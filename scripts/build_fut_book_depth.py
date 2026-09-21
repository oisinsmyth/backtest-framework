"""D604 -- the first order-book depth fixture: resting depth within +/-5 ticks of the mid at every
ET minute close of the day session, for the front contract of the eight parents held as MBO.

    python scripts/build_fut_book_depth.py --probe              # metadata, one file's message count, actions, schema
    python scripts/build_fut_book_depth.py --build [--workers 6]
    python scripts/build_fut_book_depth.py --verify 2           # serial == pool, bit-identical, on the 2 smallest session files
    python scripts/build_fut_book_depth.py --gates              # G1..G6 against the written panel; raises
    python scripts/build_fut_book_depth.py --selftest           # every gate and every refusal proved to RAISE

SYSTEM PYTHON (databento 0.86); the venv has no databento -- run with `python`, not `uv run`
(the convention `scripts/build_fut_cleared_volume_cm.py` states).

WHAT THIS IS FOR, AND WHAT IT IS NOT
------------------------------------
The settlement-flow ledger's Stage H (SETTLEMENT_FLOW_LEDGER_PREREG.md 8A.4) scales the
square-root impact by `sqrt(D_bar / D(t0))`, where `D(t0)` is resting depth within +/-5 ticks at
the t0 bar close and `D_bar` is its trailing same-time mean over PRIOR days. Required unit test 45
is that this measurement exists and is taken at the bar close; nothing in this repository had ever
read the MBO schema, so `D(t0)` could not be computed at all. This panel is that measurement.

It is a BOOK-STATE artefact. It computes no return, no signal and no trade, and the only month of
MBO on disk (2026-08-11 .. 2026-09-09) lies inside the deposit's sealed vault window
(2025-03-01 -> 2026-09-18), which the principal has not reconciled with this repository's
2024-01-01 holdout. Nothing here may be used to score anything until that reconciliation is in
writing. The panel's own meta repeats this.

THE REPLAY, AND THE ONE CONVENTION IT RESTS ON
----------------------------------------------
MBO is an order-by-order feed. `A` adds a resting order, `C` cancels (its `size` is the amount
REMOVED, not the remainder), `M` modifies it to a new price/size, `R` clears the instrument's whole
book. **`T` and `F` do not change resting depth by themselves** -- a trade is reported as its own
record and the resting order's reduction arrives as a separate `C` or `M`. `N` is a no-op.

That convention is not asserted in prose here: gate G2 is what tests it. If `F` really removed
size and this replay ignored it, traded-through orders would stay resting and the book would cross
within seconds of the open. G2 requires a strictly positive spread at every one of the emitted
minutes, on every instrument, every day. A replay with the wrong fill convention cannot pass it.

Databento delivers a full book SNAPSHOT (flag F_SNAPSHOT = 32) at the head of each daily file, so
the book is complete from the first record and not warmed up from an empty state mid-session. The
count of snapshot records is recorded per file; a file without one is refused.

WHAT A MINUTE ROW MEANS
-----------------------
`minute_et` = "HH:MM" -- the state of the book AT that instant, i.e. after every message with
`ts_recv` strictly before it. 09:30 is therefore the book as the day session opens, 16:00 the book
at the close. `ts_recv` is the feed clock and the file's own order; `ts_event` is not monotonic
across instruments and is not used for sequencing.

`n_events` counts the front instrument's own messages since the previous emitted minute. It is the
row's liveness: a frozen book (an early close, a halt) shows `n_events = 0` and keeps its previous
state, which is the truth about the book rather than a deleted row. 2026-09-07 is Labor Day and
every root's session ends at 13:00 ET; those rows are kept and are visible as `n_events = 0`.

Output data/fixtures/fut_book_depth_1m.csv.gz (gitignored by suffix; manifest-registered by the
integrator) + fut_book_depth_1m.meta.json (tracked).
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_fut_breadth_hourly import ids_of as _ids_windows  # noqa: E402
from build_fut_open_interest import rss_mb  # noqa: E402

RAW = REPO / "data" / "raw" / "databento" / "GLBX-20260911-NKFKU4AMHN"
FIX = REPO / "data" / "fixtures"
OUT = FIX / "fut_book_depth_1m.csv.gz"
META = FIX / "fut_book_depth_1m.meta.json"
SPECS = REPO / "data" / "futures_contract_specs.json"
SETTLE = REPO / "data" / "settlement_windows.csv"

ROOTS = ("ES", "NQ", "RTY", "YM", "CL", "GC", "ZN", "ZB")
"""The MBO pull's eight parent symbols. Read from the file's own metadata and CHECKED against
this tuple -- a pull that carried a ninth root would change the panel's meaning silently."""

PX = 1e-9
"""Databento fixed-point price scale."""

UNDEF = np.iinfo(np.int64).max
"""Databento's absent price. It passes a `> 0` test, which is how D507 produced a 1.8-billion-tick
spread; every price read here is compared against it before use."""

F_SNAPSHOT = 32

BAND_TICKS = 5
"""+/-5 ticks of the mid -- the ledger's own band (8A.4), not a parameter."""

SESSION_OPEN_ET = (9, 30)
SESSION_CLOSE_ET = (16, 0)
CHUNK = 2_000_000
"""Raw records per decoded chunk. Sized so one worker's Python-side lists stay a few hundred MB:
the fan-out runs six workers on a 34 GB machine shared with other sessions."""

COLUMNS = ["root", "day", "minute_et", "contract", "mid", "spread_ticks", "best_bid_lots",
           "best_ask_lots", "bid_depth_5tk", "ask_depth_5tk", "bid_orders_5tk", "ask_orders_5tk",
           "n_events"]


class DepthError(RuntimeError):
    """A depth-panel gate or door guard refused. Its own class so a caller can tell a refusal of
    this builder's invariants from an arbitrary RuntimeError raised inside pandas or databento."""


# ------------------------------------------------------------------ the minute grid


def _tick_points(roots: tuple[str, ...] = ROOTS) -> dict[str, float]:
    """Each root's tick in QUOTED price points, from the CME specification file.

    Never a literal and never a default: a wrong tick rescales every spread and every band width
    in the panel, and no downstream check could see it (D48, and `instruments/future.py`'s own
    reason for existing).
    """
    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    out = {}
    for root in roots:
        entry = specs.get(root)
        if not isinstance(entry, dict) or "tick_points" not in entry:
            raise DepthError(
                f"[SPEC] {SPECS.name} carries no tick_points for {root!r}. A guessed tick would "
                "rescale every spread and every +/-5-tick band in this panel."
            )
        out[root] = float(entry["tick_points"])
    return out


def settlement_end_et(root: str, day: str) -> tuple[tuple[int, int] | None, str]:
    """The end of `root`'s settlement window on `day` as (hour, minute) ET, with the REASON when
    there is none. Never a guess.

    Two different absences, and D586's table makes the difference visible:
      * `no_row`   -- the product is not in `data/settlement_windows.csv` at all. RTY, YM, ZN and
                      ZB are in this class: D586 sourced 17 products and carried CME's equity-index
                      notice for ES and NQ only, and the treasuries for none.
      * `not_effective` -- a row exists but its `effective_from` is after `day`. Only energy
                      (SER-4867, 2009-06-01) and equity index (SER-8591, 2020-10-26) carry a dated
                      history; every other row was stamped with the date D586 read the page,
                      2026-09-21. GC is in this class for the whole of this pull's span.
    """
    rows = pd.read_csv(SETTLE, dtype=str, encoding="utf-8").fillna("")
    same = rows[rows["root"] == root]
    if same.empty:
        return None, "no_row"
    hit = same[((same["effective_from"] == "") | (same["effective_from"] <= day))
               & ((same["effective_to"] == "") | (same["effective_to"] >= day))]
    if hit.empty:
        return None, "not_effective"
    if len(hit) > 1:
        raise DepthError(f"[SETTLE] {root} on {day} matches {len(hit)} settlement windows; the "
                         "effective-date ranges must select exactly one")
    h, m, _ = str(hit.iloc[0]["window_end_et"]).split(":")
    return (int(h), int(m)), "mapped"


def minute_grid(day: str, roots: tuple[str, ...] = ROOTS) -> tuple[list[str], dict]:
    """The emitted ET minutes for `day`: 09:30 through 16:00, EXTENDED to any mapped settlement
    window that ends later, plus the record of which roots were mapped and why not.

    The extension clause is COMPUTED rather than assumed. On this pull's eight roots every window
    effective in the span (CL 14:30, ES 16:00, NQ 16:00) ends at or before 16:00 ET, so the union
    IS the base grid -- and that is a finding, not an omission.
    """
    end_h, end_m = SESSION_CLOSE_ET
    mapped: dict[str, str] = {}
    absent: dict[str, str] = {}
    for root in roots:
        w, why = settlement_end_et(root, day)
        if w is None:
            absent[root] = why
            continue
        mapped[root] = f"{w[0]:02d}:{w[1]:02d}"
        if w > (end_h, end_m):
            end_h, end_m = w
    start = SESSION_OPEN_ET[0] * 60 + SESSION_OPEN_ET[1]
    stop = end_h * 60 + end_m
    if stop <= start:
        raise DepthError(f"[GRID] {day}: the grid would end at or before it starts "
                         f"({end_h:02d}:{end_m:02d} <= {SESSION_OPEN_ET[0]:02d}:{SESSION_OPEN_ET[1]:02d})")
    return ([f"{m // 60:02d}:{m % 60:02d}" for m in range(start, stop + 1)],
            {"settlement_window_end_et": mapped, "no_effective_window": absent,
             "grid_end_et": f"{end_h:02d}:{end_m:02d}"})


def boundaries_ns(day: str, minutes: list[str]) -> np.ndarray:
    """The UTC nanosecond instant of each ET minute on `day`. tz-aware, so DST is the library's
    problem and never a hardcoded -4. `.asi8` rather than `.view('int64')`, which is not
    nanoseconds once the index carries a non-ns unit."""
    ts = (pd.to_datetime([f"{day} {m}" for m in minutes])
          .tz_localize("US/Eastern").tz_convert("UTC").as_unit("ns"))
    out = np.asarray(ts.asi8, dtype=np.int64)
    if not (np.diff(out) == 60_000_000_000).all():
        raise DepthError(f"[GRID] {day}: the minute boundaries are not one minute apart -- a DST "
                         "transition or a bad label")
    return out


def session_days() -> list[tuple[str, Path]]:
    """(day, path) for every file in the pull whose ET date has a 09:30-16:00 day session.

    The four Sunday files cover a UTC Sunday: the CME week opens 18:00 ET that evening, which is
    22:00 UTC and inside the same UTC date, so the file is real -- but it holds no 09:30-16:00 ET
    session and contributes no row. They are dropped by the weekday test, not by their size.
    """
    out = []
    for p in sorted(RAW.glob("glbx-mdp3-*.mbo.dbn.zst")):
        day = p.name.split("-")[2].split(".")[0]
        d = f"{day[:4]}-{day[4:6]}-{day[6:]}"
        if pd.Timestamp(d).dayofweek < 5:
            out.append((d, p))
    return out


# ------------------------------------------------------------------ the replay


def _front_ids(store, w) -> dict[int, tuple[str, str]]:
    """The front contract of each root on this file's day: the root's outright with the most
    TRADE records. Returns {instrument_id: (root, contract)}.

    Trade count, not volume and not open interest, because it is the only front rule this file can
    answer for itself, and the margin is not close -- ESU6 records 254,903 trades against ESZ6's
    351 on the probe day.
    """
    counts: dict[int, int] = {}
    for arr in store.to_ndarray(count=10_000_000):
        tr = arr[arr["action"] == b"T"]
        if tr.size:
            u, c = np.unique(tr["instrument_id"], return_counts=True)
            for k, v in zip(u, c):
                counts[int(k)] = counts.get(int(k), 0) + int(v)
    tc = pd.DataFrame({"iid": list(counts), "trades": list(counts.values())})
    j = tc.merge(w, on="iid", how="inner")
    if j.empty:
        raise DepthError("[FRONT] no traded outright of the eight roots in this file")
    top = j.sort_values(["trades", "contract"], ascending=[False, True]).groupby("root").head(1)
    return {int(r.iid): (str(r.root), str(r.contract)) for r in top.itertuples()}


def replay_messages(chunks, day: str, minutes: list[str], front: dict, tick_raw: dict) -> dict:
    """The book replay itself, over an iterable of decoded MBO chunks.

    Separated from the file reading so that a known-answer case can be pushed through THIS code
    rather than through a paraphrase of it: `--selftest` feeds it a hand-built message sequence
    whose depth is worked out on paper. A self-test against a second implementation would only
    prove the two agree.

    `chunks` yields structured arrays with the MBO schema's fields; `front` is
    {instrument_id: (root, contract)}; `tick_raw` is {instrument_id: tick in 1e-9 price units}.
    """
    bnd = boundaries_ns(day, minutes)
    # per instrument: orders {oid: (px, size, is_bid)}, and price -> (size, count) on each side
    orders: dict[int, dict] = {i: {} for i in front}
    bids: dict[int, dict] = {i: {} for i in front}
    asks: dict[int, dict] = {i: {} for i in front}
    bidn: dict[int, dict] = {i: {} for i in front}
    askn: dict[int, dict] = {i: {} for i in front}
    events: dict[int, int] = {i: 0 for i in front}
    keys = np.fromiter(front, dtype=np.uint32)

    rows: list[tuple] = []
    k = 0
    n_bnd = len(bnd)
    n_in = n_kept = n_snap = 0
    unknown_ref = 0
    undef_px = 0

    def emit(idx: int) -> None:
        minute = minutes[idx]
        for iid, (root, contract) in front.items():
            b, a = bids[iid], asks[iid]
            t = tick_raw[iid]
            if not b or not a:
                raise DepthError(f"[BOOK] {root} {contract} {day} {minute}: one-sided book "
                                 f"({len(b)} bid levels, {len(a)} ask levels)")
            bb = max(b)
            ba = min(a)
            mid2 = bb + ba                      # twice the mid, exact in integers
            lo2 = mid2 - 2 * BAND_TICKS * t     # twice the lowest in-band bid price
            hi2 = mid2 + 2 * BAND_TICKS * t
            bd = bo = ad = ao = 0
            bn, an = bidn[iid], askn[iid]
            for px, sz in b.items():
                if 2 * px >= lo2:
                    bd += sz
                    bo += bn[px]
            for px, sz in a.items():
                if 2 * px <= hi2:
                    ad += sz
                    ao += an[px]
            rows.append((root, day, minute, contract, mid2 * 0.5 * PX, (ba - bb) / t,
                         b[bb], a[ba], bd, ad, bo, ao, events[iid]))
            events[iid] = 0

    for arr in chunks:
        n_in += len(arr)
        sel = np.isin(arr["instrument_id"], keys)
        if not sel.any():
            continue
        a = arr[sel]
        n_kept += len(a)
        n_snap += int((a["flags"] & F_SNAPSHOT).astype(bool).sum())
        ts_l = a["ts_recv"].astype("int64").tolist()
        iid_l = a["instrument_id"].astype("int64").tolist()
        oid_l = a["order_id"].astype("uint64").tolist()
        px_l = a["price"].astype("int64").tolist()
        sz_l = a["size"].astype("int64").tolist()
        act_l = a["action"].tolist()
        side_l = a["side"].tolist()
        for ts, iid, oid, px, sz, act, side in zip(ts_l, iid_l, oid_l, px_l, sz_l, act_l, side_l):
            while k < n_bnd and ts >= bnd[k]:
                emit(k)
                k += 1
            events[iid] += 1
            if act == b"R":
                orders[iid].clear()
                bids[iid].clear()
                asks[iid].clear()
                bidn[iid].clear()
                askn[iid].clear()
                continue
            if act == b"T" or act == b"F" or act == b"N":
                continue            # a fill does not move resting depth; see the module docstring
            if px == UNDEF:
                undef_px += 1
                continue
            book = bids[iid] if side == b"B" else asks[iid] if side == b"A" else None
            if book is None:
                continue
            cnt = bidn[iid] if side == b"B" else askn[iid]
            if act == b"A":
                o = orders[iid]
                o[oid] = (px, sz, side)
                book[px] = book.get(px, 0) + sz
                cnt[px] = cnt.get(px, 0) + 1
            elif act == b"C":
                o = orders[iid]
                prev = o.get(oid)
                if prev is None:
                    unknown_ref += 1
                    continue
                ppx, psz, pside = prev
                pbook = bids[iid] if pside == b"B" else asks[iid]
                pcnt = bidn[iid] if pside == b"B" else askn[iid]
                left = psz - sz
                if left > 0:
                    o[oid] = (ppx, left, pside)
                    pbook[ppx] -= sz
                else:
                    del o[oid]
                    rem = pbook[ppx] - psz
                    if rem <= 0:
                        del pbook[ppx]
                        del pcnt[ppx]
                    else:
                        pbook[ppx] = rem
                        pcnt[ppx] -= 1
            elif act == b"M":
                o = orders[iid]
                prev = o.get(oid)
                if prev is None:
                    unknown_ref += 1
                    continue
                ppx, psz, pside = prev
                pbook = bids[iid] if pside == b"B" else asks[iid]
                pcnt = bidn[iid] if pside == b"B" else askn[iid]
                rem = pbook[ppx] - psz
                if rem <= 0:
                    del pbook[ppx]
                    del pcnt[ppx]
                else:
                    pbook[ppx] = rem
                    pcnt[ppx] -= 1
                o[oid] = (px, sz, side)
                book[px] = book.get(px, 0) + sz
                cnt[px] = cnt.get(px, 0) + 1
    while k < n_bnd:
        emit(k)
        k += 1
    return {"day": day, "rows": rows, "n_in": n_in, "n_kept": n_kept, "n_snapshot": n_snap,
            "unknown_ref": unknown_ref, "undef_px": undef_px,
            "front": {v[0]: v[1] for v in front.values()}}


def replay(path: str, day: str, minutes: list[str], ticks: dict[str, float]) -> dict:
    """One trading day's file -> one row per (root, minute)."""
    import databento as db

    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = _ids_windows(store)
    if w is None or w.empty:
        raise DepthError(f"[IDS] {Path(path).name} carries no outright symbol mappings")
    w = w[w["root"].isin(ROOTS)].reset_index(drop=True)
    got = set(w["root"])
    if got != set(ROOTS):
        raise DepthError(f"[IDS] {Path(path).name} maps {sorted(got)}, expected {sorted(ROOTS)}")
    front = _front_ids(store, w)
    if len(front) != len(ROOTS):
        raise DepthError(f"[FRONT] {Path(path).name}: a front contract for only "
                         f"{sorted(front.values())}")
    tick_raw = {i: int(round(ticks[front[i][0]] / PX)) for i in front}
    out = replay_messages(store.to_ndarray(count=CHUNK), day, minutes, front, tick_raw)
    if out["n_snapshot"] == 0:
        raise DepthError(f"[SNAP] {Path(path).name} carries no F_SNAPSHOT record for the eight "
                         "front instruments; the book would be warmed up from empty mid-session")
    out["file"] = Path(path).name
    out["secs"] = round(time.time() - t0, 1)
    out["rss_mb"] = round(rss_mb(), 0)
    return out


def worker(item):
    day, path = item
    ticks = _tick_points()
    minutes, _ = minute_grid(day)
    return replay(str(path), day, minutes, ticks)


# ------------------------------------------------------------------ assemble, gates, write


def frame(results: list[dict]) -> pd.DataFrame:
    rows = [r for res in results for r in res["rows"]]
    d = pd.DataFrame(rows, columns=COLUMNS)
    return d.sort_values(["root", "day", "minute_et"], kind="mergesort").reset_index(drop=True)


def _usd_per_point(roots: tuple[str, ...] = ROOTS) -> dict[str, float]:
    """The dollar value of one quoted point, from the same CME specification file as the tick."""
    specs = json.loads(SPECS.read_text(encoding="utf-8"))
    out = {}
    for root in roots:
        entry = specs.get(root)
        if not isinstance(entry, dict) or "usd_per_point" not in entry:
            raise DepthError(f"[SPEC] {SPECS.name} carries no usd_per_point for {root!r}")
        out[root] = float(entry["usd_per_point"])
    return out


def depth_ranking(d: pd.DataFrame) -> pd.DataFrame:
    """Median two-sided depth within +/-5 ticks, per root, in LOTS and in DOLLARS of notional.

    Two columns because they do not agree and the disagreement is the point: a lot is a different
    object on every root. ZN quotes in tens of thousands of contracts at $108k each; ES quotes in
    hundreds at $386k. Comparing contract counts across roots is the mistake
    `a-one-contract-book-across-roots-is-a-bet-on-the-largest-dollar-sigma` names, and the dollar
    column is the one that means the same thing on all eight.
    """
    upp = _usd_per_point()
    g = d.assign(lots=d["bid_depth_5tk"] + d["ask_depth_5tk"])
    g = g.assign(usd=g["lots"] * g["mid"] * g["root"].map(upp))
    return g.groupby("root")[["lots", "usd"]].median().sort_values("usd", ascending=False)


def full_sessions(d: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Keep the days that are FULL day sessions; report the rest with their numbers.

    THE RULE, and it is a liveness rule, not a gate in disguise: a day is a full 09:30-16:00 ET
    session when every one of the eight front contracts records at least one message in every
    emitted minute (`n_events > 0` everywhere). A minute in which the front contract of ES prints
    nothing at all is not a quiet minute of a day session -- it is a session that has ended.
    Presence is the session, never a bar count.

    The criterion is deliberately INDEPENDENT of the spread and depth gates, so that "the day the
    book was crossed" and "the day the market shut early" are two findings and not one
    definition. That they coincide here is reported, not assumed.

    A day is dropped for ALL roots or for none. A half-day kept for the roots that survived it
    would make the trailing same-time window (8A.4's D_bar) ragged across roots, silently, with
    nothing downstream able to see which minute had how many prior days behind it.
    """
    per = d.groupby("day")["n_events"].min()
    keep = sorted(per[per > 0].index)
    dropped = {}
    for day in sorted(per[per <= 0].index):
        sub = d[d["day"] == day]
        dropped[day] = {
            "minutes_with_no_message": int((sub["n_events"] == 0).sum()),
            "rows": int(len(sub)),
            "crossed_or_locked_minutes": int((sub["spread_ticks"] <= 0).sum()),
            "minutes_wider_than_the_band": int((sub["spread_ticks"] > 2 * BAND_TICKS).sum()),
            "roots_affected": sorted(sub[sub["n_events"] == 0]["root"].unique()),
        }
    return d[d["day"].isin(keep)].reset_index(drop=True), dropped


def gates(d: pd.DataFrame, minutes: list[str]) -> dict:
    """G1..G6. Every one raises; `--selftest` proves each fires on a break that hits the scalar
    the gate compares."""
    if d.empty:
        raise DepthError("[G0] the panel is empty")
    if not (d["n_events"] > 0).all():
        dead = d[d["n_events"] == 0]
        raise DepthError(
            f"[G7] {len(dead)} emitted minute(s) in which the front contract printed no message "
            f"at all, first {dead.iloc[0]['root']} {dead.iloc[0]['day']} "
            f"{dead.iloc[0]['minute_et']}. A minute with no message is a session that has ended; "
            "the day belongs in excluded_days, not in the panel."
        )
    if not np.isfinite(d["mid"].to_numpy()).all():
        raise DepthError("[G1] a non-finite mid")
    sp = d["spread_ticks"].to_numpy()
    if not (sp > 0).all():
        bad = d[d["spread_ticks"] <= 0]
        raise DepthError(f"[G2] {len(bad)} minute(s) with a crossed or locked book, first: "
                         f"{bad.iloc[0].to_dict()}")
    # G3 and G4 are the band's own arithmetic, stated as identities so that neither can be tuned
    # after looking at the data. The band is +/-5 ticks of the mid, so BOTH best quotes lie inside
    # it exactly when the spread is at most 10 ticks; when it is wider, nothing at all is inside
    # the band, because nothing rests between the best bid and the best ask.
    outside = d[sp > 2 * BAND_TICKS]
    inside = d[sp <= 2 * BAND_TICKS]
    if len(outside) and not ((outside["bid_depth_5tk"] == 0)
                             & (outside["ask_depth_5tk"] == 0)).all():
        bad = outside[(outside["bid_depth_5tk"] != 0) | (outside["ask_depth_5tk"] != 0)]
        raise DepthError(
            f"[G3] {len(bad)} minute(s) whose spread exceeds {2 * BAND_TICKS} ticks -- putting "
            "both best quotes outside the band -- nevertheless report depth inside it, which "
            f"nothing can rest at. First: {bad.iloc[0].to_dict()}"
        )
    if not (inside["bid_depth_5tk"] >= inside["best_bid_lots"]).all():
        raise DepthError("[G4] bid depth within 5 ticks is below the best bid's own size, on a "
                         "minute whose best bid IS inside the band")
    if not (inside["ask_depth_5tk"] >= inside["best_ask_lots"]).all():
        raise DepthError("[G4] ask depth within 5 ticks is below the best ask's own size, on a "
                         "minute whose best ask IS inside the band")
    days = sorted(d["day"].unique())
    per = d.groupby("root").size()
    want = len(minutes) * len(days)
    off = {r: int(n) for r, n in per.items() if int(n) != want}
    if off:
        raise DepthError(f"[G5] rows != minutes x days ({want}) for {off}")
    rank = depth_ranking(d)
    index_roots = [r for r in ("ES", "NQ", "RTY", "YM") if r in rank.index]
    deepest_index = rank.loc[index_roots, "usd"].idxmax()
    if deepest_index != "ES":
        raise DepthError(f"[G6] the deepest EQUITY-INDEX root within +/-5 ticks is {deepest_index}, "
                         f"not ES -- a sanity gate, not a law: "
                         f"{rank.loc[index_roots, 'usd'].round(0).to_dict()}")
    ticks = _tick_points()
    band_bp = (d.assign(bp=BAND_TICKS * d["root"].map(ticks) / d["mid"] * 1e4)
               .groupby("root")["bp"].median().round(2).to_dict())
    return {
        "G7": "every emitted minute is LIVE -- the front contract printed at least one message "
              "in it. This is the rule that excludes an early-close day, and it is checked "
              "before the book gates so that a stale book is never read as a wide one.",
        "G1": "every emitted minute has a finite mid",
        "G2": f"every emitted minute has a strictly positive spread ({len(d):,} rows) -- this is "
              "what tests the T/F fill convention, see the module docstring",
        "G3": f"a minute whose spread exceeds {2 * BAND_TICKS} ticks -- both best quotes outside "
              f"the band -- reports EXACTLY zero depth on both sides, because nothing rests "
              f"between the best bid and the best ask. {len(outside)} of {len(d)} rows are in "
              "that state, and they are enumerated in band_empty_minutes.",
        "G4": f"depth within +/-{BAND_TICKS} ticks >= the best quote's own size on both sides, on "
              "every minute whose best quotes are inside the band",
        "band_empty_minutes": [
            {k: (float(v) if k in ("mid", "spread_ticks") else v)
             for k, v in r.items() if k in ("root", "day", "minute_et", "spread_ticks", "mid")}
            for r in outside.to_dict("records")
        ],
        "G5": f"every root has exactly {want} rows ({len(minutes)} minutes x {len(days)} days)",
        "G6": "ES is the deepest EQUITY-INDEX root within +/-5 ticks, in dollars. NOT the deepest "
              "of the eight: ZN and ZB are far deeper on both lots and notional, because a "
              "+/-5-tick band is a different economic width on every root (see band_bp).",
        "median_two_sided_lots_by_root": {k: float(v) for k, v in rank["lots"].items()},
        "median_two_sided_usd_by_root": {k: float(v) for k, v in rank["usd"].items()},
        "band_half_width_bp_by_root": band_bp,
        "rows": int(len(d)), "days": len(days), "minutes_per_day": len(minutes),
    }


def write(d: pd.DataFrame, minutes: list[str], results: list[dict], grid_note: dict,
          probe: dict, wall: float, workers: int, excluded: dict | None = None) -> dict:
    rep = gates(d, minutes)
    FIX.mkdir(parents=True, exist_ok=True)
    # A DETERMINISTIC gzip stream: the default header carries the source file name and the wall
    # clock, so two identical panels would hash differently and the meta's sha256 would check
    # nothing but "this is the file I just wrote". `mtime=0` and an empty `filename` make the
    # bytes a pure function of the rows, and LF is pinned at both layers (D550).
    csv_text = d.to_csv(index=False, lineterminator="\n", encoding="utf-8")
    raw = csv_text.encode("utf-8")
    with open(OUT, "wb") as fb, gzip.GzipFile(filename="", mode="wb", fileobj=fb, mtime=0,
                                              compresslevel=9) as gz:
        gz.write(raw)
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    plain_digest = hashlib.sha256(raw).hexdigest()
    cover = (d.groupby("root")
             .agg(rows=("day", "size"), days=("day", "nunique"),
                  first=("day", "min"), last=("day", "max"))
             .to_dict("index"))
    meta = {
        "built_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "builder": "scripts/build_fut_book_depth.py",
        "record": "D604",
        "source": str(RAW.relative_to(REPO)),
        "schema": "mbo",
        "shape": "TIDY -- one row per (root, day, minute_et): the front contract's book state AT "
                 "that ET instant, i.e. after every message with ts_recv strictly before it",
        "roots": list(ROOTS),
        "band_ticks": BAND_TICKS,
        "minutes_per_day": len(minutes),
        "minute_grid": [minutes[0], minutes[-1]],
        "grid_rule": grid_note,
        "fill_convention": "A adds, C removes its own size, M reprices, R clears; T, F and N do "
                           "not change resting depth. Gate G2 is the test of it.",
        "clock": "ts_recv (the feed's own order); ts_event is not monotonic across instruments",
        "front_rule": "the root's outright with the most TRADE records in that file",
        "front_by_day": {r["day"]: r["front"] for r in results},
        "session_rule": "a day is kept only when every front contract printed at least one "
                        "message in every emitted minute (gate G7). A day that fails is dropped "
                        "for ALL roots, so the trailing same-time window (8A.4's D_bar) is never "
                        "ragged across roots. The criterion is liveness and does NOT look at the "
                        "spread or the depth.",
        "excluded_days": excluded or {},
        "files": [r["file"] for r in results],
        "per_file": [{k: r[k] for k in ("file", "day", "n_in", "n_kept", "n_snapshot",
                                        "unknown_ref", "undef_px", "secs", "rss_mb")}
                     for r in results],
        "probe": probe,
        "rows": int(len(d)),
        "sha256": digest,
        "sha256_uncompressed_csv": plain_digest,
        "encoding": "utf-8, LF, deterministic gzip (mtime=0, no stored filename), so the digest "
                    "is a function of the rows and a rebuild reproduces it byte for byte (D550)",
        "coverage": cover,
        "gates": rep,
        "all_gates_pass": True,
        "workers": workers,
        "wall_s": round(wall, 1),
        "holdout": "BOOK STATE ONLY -- no return, no signal, no trade. The pull spans "
                   "2026-08-11..2026-09-09, inside the deposit's sealed vault window "
                   "(2025-03-01..2026-09-18), which the principal has NOT reconciled with this "
                   "repository's 2024-01-01 holdout. Nothing here may score anything until that "
                   "reconciliation is in writing (D604).",
    }
    META.write_text(json.dumps(meta, indent=1), encoding="utf-8", newline="\n")
    return meta


# ------------------------------------------------------------------ entry points


def probe() -> dict:
    """Metadata, one file's message count, its action histogram and the MBO schema fields."""
    import databento as db

    days = session_days()
    day, path = days[3]
    t0 = time.time()
    store = db.DBNStore.from_file(str(path))
    md = store.metadata
    w = _ids_windows(store)
    n = 0
    acts: dict[str, int] = {}
    snap = 0
    dtype = None
    for arr in store.to_ndarray(count=10_000_000):
        if dtype is None:
            dtype = [f for f in arr.dtype.names]
        n += len(arr)
        snap += int((arr["flags"] & F_SNAPSHOT).astype(bool).sum())
        u, c = np.unique(arr["action"], return_counts=True)
        for k, v in zip(u, c):
            acts[k.decode()] = acts.get(k.decode(), 0) + int(v)
    out = {
        "file": path.name, "day": day, "size_mb": round(path.stat().st_size / 1e6, 1),
        "schema": str(md.schema), "dataset": md.dataset,
        "span_utc": [str(pd.Timestamp(md.start, unit="ns", tz="UTC")),
                     str(pd.Timestamp(md.end, unit="ns", tz="UTC"))],
        "parent_symbols": list(md.symbols), "symbol_mappings": len(md.mappings),
        "outright_windows": 0 if w is None else int(len(w)),
        "messages": n, "actions": dict(sorted(acts.items())), "snapshot_records": snap,
        "schema_fields": dtype, "decode_secs": round(time.time() - t0, 1),
        "session_files": len(days), "total_files": len(list(RAW.glob("*.mbo.dbn.zst"))),
    }
    print(json.dumps(out, indent=1))
    return out


CACHE = REPO / "temp" / "d604_book_depth_replay.pkl"
"""The replay's own output, cached so a gate change does not cost another pass over 39 GB.

`temp/` because losing it costs one 10-minute rebuild and nothing else.
"""

REPLAY_FUNCTIONS = ("replay_messages", "replay", "_front_ids", "_tick_points", "minute_grid",
                    "boundaries_ns", "session_days", "settlement_end_et")
"""Exactly the functions whose output the cache holds. See `_cache_key`."""


def _cache_key() -> str:
    """A digest of the SOURCE of the functions that produced the cached rows.

    Keying on the file's mtime would be simpler and would be wrong in the direction that costs
    time without buying safety: every edit to a gate, a meta field or a print statement would
    discard a 10-minute replay that is still exactly correct. Keying on the fixture alone would
    be wrong in the direction that costs correctness -- CLAUDE.md's rule, and D288's -- because
    an edited estimator then reads a stale cache and the numbers look fine.

    So the key is the source text of the replay path and nothing else. Change any of it and the
    cache is discarded; change a gate and it is kept. The raw MBO files are a frozen archive and
    are covered by the day list stored beside the key.
    """
    import inspect

    src = "\n".join(inspect.getsource(globals()[name]) for name in REPLAY_FUNCTIONS)
    src += f"\nBAND_TICKS={BAND_TICKS}\nCHUNK={CHUNK}\nUNDEF={UNDEF}\nPX={PX}\nROOTS={ROOTS}"
    return hashlib.sha256(src.encode("utf-8")).hexdigest()


def build(workers: int, probe_info: dict | None = None, days=None, reuse: bool = False) -> dict:
    import pickle
    from multiprocessing import Pool

    items = days if days is not None else session_days()
    minutes, grid_note = minute_grid(items[0][0])
    cached = None
    if reuse and CACHE.exists():
        blob = pickle.loads(CACHE.read_bytes())
        if blob["key"] == _cache_key() and blob["days"] == [it[0] for it in items]:
            cached = blob
            print(f"  reusing the cached replay ({CACHE.relative_to(REPO)}, "
                  f"{blob['wall']:.0f} s of work)", flush=True)
        else:
            print("  cache is stale (the builder or the day list moved) -- replaying", flush=True)
    if cached is None:
        t0 = time.time()
        with Pool(workers) as pool:
            results = pool.map(worker, items)
        wall = time.time() - t0
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_bytes(pickle.dumps(
            {"key": _cache_key(), "days": [it[0] for it in items], "results": results,
             "wall": wall, "workers": workers}, protocol=5))
    else:
        results, wall, workers = cached["results"], cached["wall"], cached["workers"]
    item_secs = sum(r["secs"] for r in results)
    for r in results:
        print(f"  {r['file']}: {r['n_in']:,} in, {r['n_kept']:,} kept, {r['n_snapshot']:,} snapshot, "
              f"{r['unknown_ref']} unknown-ref, {r['secs']} s, RSS {r['rss_mb']} MB", flush=True)
    print(f"[SPEED] sum(item time)/wall = {item_secs:.0f}/{wall:.0f} = {item_secs / wall:.2f}x on "
          f"{workers} workers ({item_secs / wall / workers:.0%})", flush=True)
    if item_secs / wall / workers < 0.70:
        print("[SPEED] BELOW THE 70% FLOOR -- this is already processes; the loss is decode "
              "contention, not the GIL", flush=True)
    raw = frame(results)
    d, excluded = full_sessions(raw)
    for day, why in excluded.items():
        print(f"  EXCLUDED {day}: {why['minutes_with_no_message']} of {why['rows']} emitted "
              f"minutes printed no message at all -- not a full day session. On the same day, "
              f"{why['crossed_or_locked_minutes']} minutes were crossed or locked and "
              f"{why['minutes_wider_than_the_band']} were wider than the band; that coincidence "
              f"is reported, not assumed.", flush=True)
    meta = write(d, minutes, results, grid_note, probe_info or probe(), wall, workers, excluded)
    print(f"  wrote {OUT.relative_to(REPO)}: {len(d):,} rows over {d['day'].nunique()} days "
          f"(of {raw['day'].nunique()} replayed), sha256 {meta['sha256'][:16]}..., gates green",
          flush=True)
    return meta


def diagnose() -> None:
    """Describe every row the gates would reject, from the cached replay. A refusal is a finding
    before it is a bug, and this is how the finding gets looked at (memory:
    `look-at-the-object-before-reporting-it`)."""
    import pickle

    blob = pickle.loads(CACHE.read_bytes())
    d = frame(blob["results"])
    print(f"  {len(d):,} rows, {d['day'].nunique()} days")
    bad = d[d["spread_ticks"] <= 0]
    print(f"  spread <= 0: {len(bad):,} rows ({len(bad) / len(d):.2%}); "
          f"locked (==0) {int((bad['spread_ticks'] == 0).sum()):,}, "
          f"crossed (<0) {int((bad['spread_ticks'] < 0).sum()):,}")
    print("  by root:\n" + bad.groupby("root").size().to_string())
    print("  by day:\n" + bad.groupby("day").size().to_string())
    print("  by n_events == 0:\n" + bad.groupby(bad["n_events"] == 0).size().to_string())
    print("  live rows (n_events > 0) among them, by root and hour:")
    live = bad[bad["n_events"] > 0]
    if len(live):
        print(live.assign(h=live["minute_et"].str[:2]).groupby(["root", "h"]).size().to_string())
        print(live.head(12).to_string())
    wide = d[d["spread_ticks"] > 2 * BAND_TICKS]
    print(f"  spread > {2 * BAND_TICKS} ticks: {len(wide):,} rows")
    if len(wide):
        print(wide.groupby(["root", wide["n_events"] == 0]).size().to_string())
    thin = d[(d["bid_depth_5tk"] < d["best_bid_lots"]) | (d["ask_depth_5tk"] < d["best_ask_lots"])]
    print(f"  depth below the best quote: {len(thin):,} rows")
    print("  n_events == 0 overall:\n"
          + d[d["n_events"] == 0].groupby(["root", "day"]).size().to_string())


def verify(n: int) -> None:
    """Serial == pool, BIT-IDENTICALLY, on the n smallest SESSION files.

    The four smallest files in the pull are Sundays and produce no row, so "smallest" is taken
    over the files that carry a day session; comparing on a pair of empty frames would prove
    nothing (memory: zero hits means no overlap, not a new question).
    """
    from multiprocessing import Pool

    items = sorted(session_days(), key=lambda it: it[1].stat().st_size)[:n]
    minutes, _ = minute_grid(items[0][0])
    print(f"  verifying on {[it[1].name for it in items]}")
    ser = frame([worker(it) for it in items])
    with Pool(min(n, 4)) as pool:
        par = frame(pool.map(worker, items))
    a = ser.to_csv(index=False, lineterminator="\n", encoding="utf-8").encode("utf-8")
    b = par.to_csv(index=False, lineterminator="\n", encoding="utf-8").encode("utf-8")
    if a != b:
        for i, (x, y) in enumerate(zip(a.split(b"\n"), b.split(b"\n"))):
            if x != y:
                raise DepthError(f"[VERIFY] serial != pool at line {i}: {x!r} vs {y!r}")
        raise DepthError(f"[VERIFY] serial != pool: {len(a)} vs {len(b)} bytes")
    kept, dropped = full_sessions(ser)
    if len(kept):
        gates(kept, minutes)
    print(f"  serial == pool bit-identically on {len(ser):,} rows; "
          f"{len(kept):,} survive the session rule (dropped {sorted(dropped)}); gates green")
    cache = CACHE if CACHE.exists() else None
    if cache is not None:
        import pickle

        blob = pickle.loads(cache.read_bytes())
        if blob["key"] == _cache_key():
            days = {it[0] for it in items}
            want = frame([r for r in blob["results"] if r["day"] in days])
            got = ser.reset_index(drop=True)
            if want.to_csv(index=False, lineterminator="\n", encoding="utf-8") != got.to_csv(
                index=False, lineterminator="\n", encoding="utf-8"
            ):
                raise DepthError("[VERIFY] this run disagrees with the cached replay")
            print(f"  and both equal the cached replay of the same {len(days)} day(s), "
                  "bit-identically")


# ------------------------------------------------------------------ selftest


def _synthetic(minutes: list[str]) -> pd.DataFrame:
    days = ["2026-08-11", "2026-08-12"]
    rows = []
    for root in ROOTS:
        for day in days:
            for m in minutes:
                rows.append((root, day, m, root + "U6", 100.0, 1.0, 5, 6,
                             50 if root != "ES" else 500, 60 if root != "ES" else 600,
                             3, 4, 99))
    return pd.DataFrame(rows, columns=COLUMNS)


MBO_DTYPE = np.dtype([("length", "u1"), ("rtype", "u1"), ("publisher_id", "<u2"),
                      ("instrument_id", "<u4"), ("ts_event", "<u8"), ("order_id", "<u8"),
                      ("price", "<i8"), ("size", "<u4"), ("flags", "u1"), ("channel_id", "u1"),
                      ("action", "S1"), ("side", "S1"), ("ts_recv", "<u8"),
                      ("ts_in_delta", "<i4"), ("sequence", "<u4")])
"""The MBO record layout, transcribed from `--probe`'s own `schema_fields`. Written out so the
known-answer case can build messages without a databento import -- the venv has none."""


def synthetic_messages(day: str, minute: str) -> np.ndarray:
    """A hand-built message sequence for one instrument, whose depth is worked out on paper.

    Tick 0.25 points = 250,000,000 raw units. Prices in points; every order is one message.

        A  bid 100.00 x 4      A  ask 100.25 x 7
        A  bid  99.75 x 3      A  ask 100.50 x 2
        A  bid  98.50 x 9      A  ask 101.75 x 6      (6 ticks out: OUTSIDE the band)
        A  bid 100.00 x 5      (same level, second order)
        C  bid  99.75 x 3      (the whole order leaves)
        M  bid 100.00 x 4 -> bid 99.50 x 1
        T  ask 100.25 x 7      F  ask 100.25 x 7      (neither moves resting depth)

    Best bid 100.00 (5), best ask 100.25 (7); mid 100.125; band [98.875, 101.375].
    Bid side in band: 100.00 x 5 and 99.50 x 1 -> 6 lots, 2 orders (98.50 is 6.5 ticks below the
    mid and out). Ask side in band: 100.25 x 7 and 100.50 x 2 -> 9 lots, 2 orders (101.75 is 6.5
    ticks above the mid and out). Spread 1 tick.
    """
    t = int(pd.Timestamp(f"{day} {minute}", tz="US/Eastern").tz_convert("UTC").value) - 1_000
    seq = [
        (b"A", b"B", 1, 100.00, 4), (b"A", b"A", 2, 100.25, 7),
        (b"A", b"B", 3, 99.75, 3), (b"A", b"A", 4, 100.50, 2),
        (b"A", b"B", 5, 98.50, 9), (b"A", b"A", 6, 101.75, 6),
        (b"A", b"B", 7, 100.00, 5),
        (b"C", b"B", 3, 99.75, 3),
        (b"M", b"B", 1, 99.50, 1),
        (b"T", b"A", 0, 100.25, 7), (b"F", b"A", 2, 100.25, 7),
    ]
    a = np.zeros(len(seq), dtype=MBO_DTYPE)
    for i, (act, side, oid, px, sz) in enumerate(seq):
        a[i]["instrument_id"] = 7
        a[i]["order_id"] = oid
        a[i]["price"] = int(round(px / PX))
        a[i]["size"] = sz
        a[i]["action"] = act
        a[i]["side"] = side
        a[i]["ts_recv"] = t + i
        a[i]["ts_event"] = t + i
        a[i]["flags"] = F_SNAPSHOT if i == 0 else 0
    return a


def selftest() -> None:
    def expect(fn, what):
        try:
            fn()
        except DepthError as e:
            print(f"    RAISES on {what}: {str(e)[:88]}")
            return
        raise AssertionError(f"no raise on {what}")

    minutes, note = minute_grid("2026-08-11")
    print(f"  grid: {len(minutes)} minutes {minutes[0]}..{minutes[-1]}; effective settlement ends "
          f"{note['settlement_window_end_et']}; none effective for {note['no_effective_window']}")

    # ---- known answer FIRST: the hand-worked book, through the production replay
    msgs = synthetic_messages("2026-08-11", "09:29")
    out = replay_messages([msgs], "2026-08-11", ["09:30"], {7: ("ES", "ESU6")},
                          {7: int(round(0.25 / PX))})
    got = out["rows"][0]
    want = ("ES", "2026-08-11", "09:30", "ESU6", 100.125, 1.0, 5, 7, 6, 9, 2, 2, 11)
    if got != want:
        raise AssertionError(f"known-answer replay: got {got}, want {want}")
    print(f"  known-answer replay matches the hand-worked book exactly: {got}")

    base = _synthetic(minutes)
    gates(base, minutes)
    print(f"  gates pass a clean synthetic panel ({len(base):,} rows)")

    def broken(col, value, where=0):
        d = base.copy()
        d.loc[where, col] = value
        return d

    expect(lambda: gates(broken("mid", float("nan")), minutes), "a non-finite mid (G1)")
    expect(lambda: gates(broken("spread_ticks", -1.0), minutes), "a crossed book (G2)")
    expect(lambda: gates(broken("spread_ticks", 0.0), minutes), "a locked book (G2)")
    expect(lambda: gates(broken("spread_ticks", 11.0), minutes),
           "a spread outside the band still reporting depth inside it (G3)")
    expect(lambda: gates(broken("bid_depth_5tk", 1), minutes), "bid depth below the best bid (G4)")
    expect(lambda: gates(broken("ask_depth_5tk", 1), minutes), "ask depth below the best ask (G4)")
    # and the LEGITIMATE wide minute -- spread outside the band, depth exactly zero -- passes,
    # because G3 is an identity about the band and not a ceiling on the spread
    ok = base.copy()
    ok.loc[0, ["spread_ticks", "bid_depth_5tk", "ask_depth_5tk", "bid_orders_5tk",
               "ask_orders_5tk"]] = [21.0, 0, 0, 0, 0]
    gates(ok, minutes)
    print("    a spread of 21 ticks with zero in-band depth PASSES -- that is the macro-release "
          "state the panel measures, not a break")
    expect(lambda: gates(base.iloc[1:], minutes), "a missing minute (G5)")
    # G6's break must hit G6's OWN scalar: ES depth still covers its best quotes (G4 stays green)
    # and is merely no longer the deepest index root.
    d = base.copy()
    d.loc[d["root"] == "ES", ["bid_depth_5tk", "ask_depth_5tk"]] = 10
    expect(lambda: gates(d, minutes), "ES not the deepest equity-index root (G6)")
    expect(lambda: gates(base.iloc[:0], minutes), "an empty panel (G0)")
    expect(lambda: gates(broken("n_events", 0), minutes), "a minute with no message (G7)")
    expect(lambda: _tick_points(("ES", "NOSUCH")), "a root with no committed tick")
    expect(lambda: replay_messages([msgs[msgs["side"] == b"B"]], "2026-08-11", ["09:30"],
                                   {7: ("ES", "ESU6")}, {7: int(round(0.25 / PX))}),
           "a one-sided book at an emitted minute (the ask messages removed)")
    expect(lambda: boundaries_ns("2026-08-11", ["09:30", "09:32"]),
           "a minute grid whose boundaries are not one minute apart")
    print("  every gate raises on a break that hits the scalar it compares")

    # the session rule: a day with a dead minute is dropped WHOLE, and a clean panel loses nothing
    kept, dropped = full_sessions(base)
    assert len(kept) == len(base) and dropped == {}, "a clean panel lost a day"
    holey = base.copy()
    holey.loc[(holey["day"] == "2026-08-12") & (holey["root"] == "ZB")
              & (holey["minute_et"] > "14:00"), "n_events"] = 0
    kept, dropped = full_sessions(holey)
    assert list(dropped) == ["2026-08-12"], f"the session rule dropped {list(dropped)}"
    assert set(kept["day"]) == {"2026-08-11"}, "a dropped day survived for some root"
    assert dropped["2026-08-12"]["roots_affected"] == ["ZB"]
    gates(kept, minutes)
    print(f"  the session rule drops a day with a dead minute WHOLE "
          f"({dropped['2026-08-12']['minutes_with_no_message']} dead minutes on ZB took all "
          f"{len(ROOTS)} roots' rows with it) and leaves a clean panel untouched")

    for root in ("ZN", "ZB", "GC"):
        w, why = settlement_end_et(root, "2026-08-11")
        assert w is None, f"{root} unexpectedly mapped"
        print(f"    {root}: no settlement window on 2026-08-11 -- {why}, reported not guessed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--one", metavar="YYYY-MM-DD", help="replay a single day and print its timing")
    ap.add_argument("--verify", type=int, default=0)
    ap.add_argument("--gates", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--reuse", action="store_true",
                    help="reuse temp/'s cached replay when the builder has not moved")
    ap.add_argument("--diagnose", action="store_true",
                    help="load the cached replay and describe the rows the gates reject")
    args = ap.parse_args()
    if args.selftest:
        selftest()
    if args.probe:
        probe()
    if args.one:
        day, path = next(it for it in session_days() if it[0] == args.one)
        r = worker((day, path))
        n_days = len(session_days())
        print(f"  {r['file']}: {r['n_in']:,} in, {r['n_kept']:,} kept, {r['n_snapshot']:,} snapshot, "
              f"{r['unknown_ref']} unknown-ref, {r['undef_px']} undef-price, {len(r['rows']):,} rows, "
              f"{r['secs']} s, RSS {r['rss_mb']} MB")
        print(f"  front: {r['front']}")
        print(f"  PROJECTED: {n_days} session files / {args.workers} workers x {r['secs']} s = "
              f"{n_days * r['secs'] / args.workers / 60:.1f} min")
        d = frame([r])
        print(d.head(3).to_string())
        print(d.tail(3).to_string())
        print(depth_ranking(d).to_string())
    if args.verify:
        verify(args.verify)
    if args.diagnose:
        diagnose()
    if args.build:
        build(args.workers, reuse=args.reuse)
    if args.gates:
        d = pd.read_csv(OUT, dtype={"root": str, "day": str, "minute_et": str, "contract": str}, encoding="utf-8")
        minutes, _ = minute_grid(str(d["day"].iloc[0]))
        print(json.dumps(gates(d, minutes), indent=1))


if __name__ == "__main__":
    main()
