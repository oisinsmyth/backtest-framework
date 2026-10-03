"""The forward recorder: one-minute NQ / YM / ES / RTY day-session bars from Sierra Chart's tick files, from 2026-09-21 only,
and D737's line (D735's YM k1.0 1 sigma_rem, frozen in programme slot 1) computed on them, day by day.

    uv run python scripts/record_forward_nq_lines.py --selftest
    uv run python scripts/record_forward_nq_lines.py --validate --data-root D   # in-sample 2023 only, against Databento
    uv run python scripts/record_forward_nq_lines.py --record [--refresh]      # daily, from now

WHY. After the joint vault run every confirmation (D737's follow-up, the post-vault allocation work, any new NQ line)
can only be scored on sessions after 2026-09-18. Sierra's intraday downloads reach about five months back, so a session
not recorded within that window is lost. This records the bars and the line's trades while they can still be had.

THE SEAL. Nothing dated before FORWARD_FROM (2026-09-21, the first session after the vault's last) is read from any
Sierra file in --record: every file is cut by binary search at FORWARD_FROM 00:00 ET and the decode raises if a record
before it survives. NQ and YM 2024-01-01 -> 2026-09-18 are D716's and D737's vault; they are never read here.
--validate reads only 2023-04-03 -> 2023-12-29 (in-sample), cut at 2024-01-01 00:00 ET.

THE BARS. Sierra's NQ/ES/YM files are tick records (D695): `c` is the trade price, `h`/`l` the ask/bid. A minute bar is
open = first trade, high/low = max/min trade, close = last trade, volume = sum, over 09:30 <= t < 16:00 ET; minutes
without a trade are absent (as in fut_{R}_rth_1m). The front contract is the listed quarterly with the most 09:30-16:00
volume that session; a day whose front differs from the day before is a roll day, which D727's panel rules drop.

THE LINE. D737's own functions (`vault_d737_nq_leads_the_dow.cell` over D727's `panel_from_raw`), on the forward bars:
sigma_oc needs 20 prior forward sessions and sigma_s 15 of the next 20, so the first scoreable day is about the 36th
forward session (early November 2026). Earlier days are recorded as burn-in.

THE GLOBEX SESSIONS (2026-10-01, the principal: "yes add F2 and C1 to the recorder"). Each session's full Globex
minutes, [the evening before 18:00, 17:00) ET, on the day session's front, in fut_opening_globex_1m's layout. With the
day-session bars they are everything the two other NQ lines in the joint vault read: NQ F2 (D716, slot 7: NQ's
15:30 day-session bars, ES's for the agreement book) and C1 (D680, slot 9: the day session plus D671's overnight high
and low, 18:00 -> 09:29). Their LEDGERS are not computed here, and cannot be before the joint run: both rank each day
among the previous 250 days three times over (D671's `tiers`), so their first forward tier reads the vault window
(2024-01 -> 2026-09-18), which no one may read before the joint run. After it, each line's forward trades are its frozen
code over the vault-built history followed by these bars. A session whose Globex open precedes FORWARD_FROM
(2026-09-21's, opening 09-20) is skipped whole, never cut. Validated in-sample (2023-04 -> 2023-12) against D644's
fixture: the overnight high and low are equal on all 192 NQ and ES sessions.

RTY (2026-10-03, the principal, on D779: base L4 kept open and recorded forward). RTY's day-session and Globex bars
are recorded under the same seal; they are everything base L4 (D778's base book: the 15:50 -> 16:00 closing move, faded
from the next 18:05 to 10:00) reads. Its LEDGER is not computed here: its q80 gate ranks |c| among the 250 prior sessions
(at least 120), so its first forward gate reads the vault window unless it waits ~120 forward sessions. It is owed after
the joint run (over vault-built history), or on forward history alone from about April 2027. Validated in-sample like
the others (day bars against fut_RTY_rth_1m; Globex against fut_opening_globex_1m_ym_rty).

OUTPUTS. data/raw/forward/fut_{NQ,YM,ES,RTY}_fwd_1m.csv.gz (the day-session bars) and fut_{NQ,YM,ES}_fwd_globex_1m.csv.gz
(the Globex sessions); both gitignored caches, NOT disposable: a lost session cannot be re-fetched after ~5 months;
data/forward/d737_forward.csv (one row a session; tracked); data/forward/d737_forward_revisions.csv (a recorded row
that later changed is never overwritten silently).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

SC_DATA = Path(r"C:\SierraChart\Data")
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")
ET = "America/New_York"
EXCH = {"NQ": "CME", "ES": "CME", "YM": "CBOT", "RTY": "CME"}     # RTY: 2026-10-03, base L4's inputs (D779)
PRICE_DECIMALS = {"RTY": 1}                                          # a tick that float32 cannot hold exactly (to_tick)
MONTHS = {3: "H", 6: "M", 9: "U", 12: "Z"}
FORWARD_FROM = "2026-09-21"
VAL_LO, VAL_HI, VAL_CUT = "2023-04-03", "2023-12-29", "2024-01-01"
VAL_SCORED_FROM = "2023-07-01"
MINUTES = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
RAW_DIR = REPO / "data" / "raw" / "forward"
OUT_DIR = REPO / "data" / "forward"
LEDGER = OUT_DIR / "d737_forward.csv"
REVISIONS = OUT_DIR / "d737_forward_revisions.csv"
VALIDATION = OUT_DIR / "sierra_bar_validation.json"
LEDGER_COLS = ["day", "nq_contract", "ym_contract", "sigma_oc_usd", "status", "m0", "side", "entry", "exit", "stopped", "gross_usd",
               "net_usd"]


class RecorderError(RuntimeError):
    pass


# ================================================================================ Sierra decoding
def us(ts: pd.Timestamp) -> int:
    return int((ts.tz_convert("UTC") - ORIGIN) / pd.Timedelta(microseconds=1))


def sym(root: str, y: int, m: int) -> str:
    return f"{root}{MONTHS[m]}{y % 100:02d}-{EXCH[root]}"


def third_friday(y: int, m: int) -> dt.date:
    d = dt.date(y, m, 15)
    return d + dt.timedelta(days=(4 - d.weekday()) % 7)


def candidates(root: str, day: str) -> list[str]:
    """The two listed quarterlies whose expiry is on or after the day."""
    d = dt.date.fromisoformat(day)
    out, y, m = [], d.year, ((d.month - 1) // 3 + 1) * 3
    while len(out) < 2:
        if third_friday(y, m) >= d:
            out.append(sym(root, y, m))
        m += 3
        if m > 12:
            m, y = 3, y + 1
    return out


def open_scid(name: str) -> np.memmap | None:
    p = SC_DATA / f"{name}.scid"
    if not p.exists() or p.stat().st_size <= 56:
        return None
    with open(p, "rb") as fh:
        head = fh.read(12)
    if head[:4] != b"SCID":
        raise RecorderError(f"{p.name}: not an SCID file")
    hdr, rs = int.from_bytes(head[4:8], "little"), int.from_bytes(head[8:12], "little")
    if rs != REC.itemsize:
        raise RecorderError(f"{p.name}: record size {rs} != {REC.itemsize}")
    return np.memmap(p, dtype=REC, mode="r", offset=hdr)


def window_minutes(mm: np.memmap, t0: int, t1: int, floor_us: int, cut_us: int, what: str
                   ) -> tuple[np.ndarray, dict[str, np.ndarray]] | None:
    """Trade-price minute OHLCV over [t0, t1) from one file: (minute offsets from t0 that traded, their columns).
    Reads only records in [floor, cut)."""
    if t0 < floor_us or t1 > cut_us:
        raise RecorderError(f"seal: {what} lies outside the permitted span")
    i0, i1 = (int(x) for x in np.searchsorted(mm["dt"], [t0, t1]))
    if i1 <= i0:
        return None
    rec = np.asarray(mm[i0:i1])
    if rec["dt"].min() < floor_us or rec["dt"].max() >= cut_us:
        raise RecorderError(f"seal: a record outside [{floor_us}, {cut_us}) was decoded")
    rec = rec[rec["v"] > 0]
    if len(rec) == 0:
        return None
    n = (t1 - t0) // 60_000_000
    k = ((rec["dt"] - t0) // 60_000_000).astype(np.int64)
    if k.min() < 0 or k.max() > n - 1:
        raise RecorderError(f"{what}: a trade falls outside the window")
    c = rec["c"].astype(np.float64)
    first = np.full(n, len(k), np.int64)
    last = np.full(n, -1, np.int64)
    idx = np.arange(len(k))
    np.minimum.at(first, k, idx)
    np.maximum.at(last, k, idx)
    hi = np.full(n, -np.inf)
    lo = np.full(n, np.inf)
    np.maximum.at(hi, k, c)
    np.minimum.at(lo, k, c)
    vol = np.bincount(k, weights=rec["v"].astype(np.float64), minlength=n)
    live = np.flatnonzero(last >= 0)
    return live, {"open": c[first[live]], "high": hi[live], "low": lo[live], "close": c[last[live]],
                  "volume": vol[live].astype(np.int64)}


def day_bars(mm: np.memmap, day: str, floor_us: int, cut_us: int) -> pd.DataFrame | None:
    """09:30-16:00 ET minute bars of one session from one file. Reads only records in [floor, cut)."""
    t0 = us(pd.Timestamp(f"{day} 09:30", tz=ET))
    t1 = us(pd.Timestamp(f"{day} 16:00", tz=ET))
    w = window_minutes(mm, t0, t1, floor_us, cut_us, day)
    if w is None:
        return None
    live, col = w
    return pd.DataFrame({"day": day, "hhmm": [MINUTES[x] for x in live], **col})


def globex_start(day: str) -> pd.Timestamp:
    """A session's Globex open: 18:00 ET on the calendar day before (Sunday's for a Monday)."""
    return pd.Timestamp(f"{(dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()} 18:00", tz=ET)


def globex_bars(mm: np.memmap, root: str, day: str, floor_us: int, cut_us: int) -> pd.DataFrame | None:
    """One session's Globex minute bars, [day-1 18:00, day 17:00) ET, in fut_opening_globex_1m's layout (root,
    session, et, hhmm, OHLCV): the overnight that D671's `overnight` reads (18:00 -> 09:29) and the day session."""
    s0 = globex_start(day)
    w = window_minutes(mm, us(s0), us(pd.Timestamp(f"{day} 17:00", tz=ET)), floor_us, cut_us, f"{day} Globex")
    if w is None:
        return None
    live, col = w
    et = s0 + pd.to_timedelta(live, unit="min")
    return pd.DataFrame({"root": root, "session": day, "et": et.strftime("%Y-%m-%d %H:%M"), "hhmm": et.strftime("%H:%M"),
                         **col})


def build_bars(root: str, days: list[str], floor: str, cut: str, contract_of: dict[str, str] | None = None) -> pd.DataFrame:
    """One root's bars over the days. The front is the candidate with the most volume (or contract_of[day] if given)."""
    floor_us, cut_us = us(pd.Timestamp(floor, tz=ET)), us(pd.Timestamp(cut, tz=ET))
    cache: dict[str, np.memmap | None] = {}
    out = []
    for day in days:
        names = [contract_of[day]] if contract_of is not None else candidates(root, day)
        best, bv = None, -1.0
        for nm in names:
            if nm not in cache:
                cache[nm] = open_scid(nm)
            if cache[nm] is None:
                continue
            b = day_bars(cache[nm], day, floor_us, cut_us)
            if b is not None and b["volume"].sum() > bv:
                best, bv = b.assign(contract=nm), float(b["volume"].sum())
        if best is not None:
            out.append(best)
    if not out:
        return pd.DataFrame(columns=["day", "hhmm", "open", "high", "low", "close", "volume", "contract"])
    return to_tick(pd.concat(out, ignore_index=True), root)


def to_tick(b: pd.DataFrame, root: str) -> pd.DataFrame:
    """Sierra stores prices as float32. A tick that is a binary fraction (NQ/ES 0.25, YM 1) survives exactly. RTY's 0.1
    does not: unrounded, 80% of 2023's minutes differ from Databento's by ~1e-4 (the validation, 2026-10-03). Rounding to
    the tick's decimals gives the same double as parsing the price's text. Monotone, so it commutes with high/low."""
    if root in PRICE_DECIMALS:
        b = b.copy()
        for c in ("open", "high", "low", "close"):
            b[c] = b[c].astype(float).round(PRICE_DECIMALS[root])
    return b


def build_globex(root: str, contract_of: dict[str, str], floor: str, cut: str) -> pd.DataFrame:
    """One root's Globex sessions, each on the contract given for it (the day session's front), so the overnight and
    the day are the same contract. A session whose Globex open falls before `floor` is skipped whole, never cut: a
    partial overnight would understate its range (2026-09-21's opens on 09-20, before the forward seal)."""
    floor_us, cut_us = us(pd.Timestamp(floor, tz=ET)), us(pd.Timestamp(cut, tz=ET))
    cache: dict[str, np.memmap | None] = {}
    out = []
    for day, nm in sorted(contract_of.items()):
        if us(globex_start(day)) < floor_us:
            continue
        if nm not in cache:
            cache[nm] = open_scid(nm)
        if cache[nm] is None:
            continue
        b = globex_bars(cache[nm], root, day, floor_us, cut_us)
        if b is not None:
            out.append(b.assign(contract=nm))
    cols = ["root", "session", "et", "hhmm", "contract", "open", "high", "low", "close", "volume"]
    return to_tick(pd.concat(out, ignore_index=True)[cols], root) if out else pd.DataFrame(columns=cols)


# ================================================================================ the line
def d737_rows(nq: pd.DataFrame, ym: pd.DataFrame, scored_from: str) -> tuple[pd.DataFrame, dict[str, Any]]:
    import stage0_d727_trend_curve as T
    import vault_d737_nq_leads_the_dow as V
    c = V.cell(T.panel_from_raw("NQ", nq), T.panel_from_raw("YM", ym))
    cst = V.cost()
    pp, days = c["pp"], c["days"]
    trade_of = {int(d): i for i, d in enumerate(c["d"])}
    nqc = nq.groupby("day")["contract"].first()
    ymc = ym.groupby("day")["contract"].first()
    sig_ok = np.isfinite(c["sp"]["sig"])
    rows = []
    all_days = sorted(set(nq["day"]))
    pos = {d: i for i, d in enumerate(days)}
    for day in all_days:
        if day < scored_from:
            continue
        r = {"day": day, "nq_contract": nqc.get(day, ""), "ym_contract": ymc.get(day, ""), "m0": "", "side": "",
             "entry": "", "exit": "", "stopped": "", "gross_usd": "", "net_usd": ""}
        i = pos.get(day)
        # informational, never a gate: NQ's sigma_oc in $ at one MNQ (D742's floor note reads the split from it)
        r["sigma_oc_usd"] = round(float(pp["soc"][i]) * 2.0, 6) if i is not None else ""
        if i is None:
            r["status"] = "excluded (roll day, short session or no sigma_oc yet)"
        elif not sig_ok[i] or not np.isfinite(c["XL"][i, 30]):
            r["status"] = "burn-in (sigma_s needs 15 of the prior 20 sessions)" if np.isfinite(c["XL"][i, 30]) else "no YM session"
        elif i in trade_of:
            j = trade_of[i]
            m0, D = int(c["m0"][i]), float(c["D"][i])
            entry = float(pp["Op"][i, m0])
            g = float(c["g"][j])
            st = bool(c["G"]["stop_up"][i, m0] if D > 0 else c["G"]["stop_dn"][i, m0])
            r.update({"status": "trade", "m0": m0, "side": int(D), "entry": entry,
                      "exit": entry + D * g / 2.0, "stopped": st, "gross_usd": round(g, 6), "net_usd": round(g - cst, 6)})
        else:
            r["status"] = "no trigger"
        rows.append(r)
    info = {"sessions": len(all_days), "panel_days": int(len(days)), "trades": int(len(c["d"])), "cost": cst}
    return pd.DataFrame(rows, columns=LEDGER_COLS), info


# ================================================================================ modes
def validate(data_root: Path) -> int:
    """In-sample only: Sierra-derived bars against Databento's fut_{R}_rth_1m (its own contract per day), 2023-04 ->
    2023-12, and D737's trades on each, 2023-07 -> 2023-12."""
    import stage0_d727_trend_curve as T
    out: dict[str, Any] = {"window": [VAL_LO, VAL_HI], "cut": VAL_CUT, "roots": {}}
    bars = {}
    for root in ("NQ", "YM", "ES", "RTY"):
        b = pd.read_csv(data_root / "fixtures" / f"fut_{root}_rth_1m.csv.gz", dtype={"day": str, "hhmm": str, "contract": str},
                        encoding="utf-8")
        b = b[(b["day"] >= VAL_LO) & (b["day"] <= VAL_HI)]
        if (b["day"] >= VAL_CUT).any():
            raise RecorderError("seal: a Databento row on or after 2024-01-01 in the validation")
        days = sorted(b["day"].unique())
        con = b.groupby("day")["contract"].agg(lambda s: s.value_counts().index[0])
        own = {d: sierra_name(root, con[d], d) for d in days}
        s_own = build_bars(root, days, VAL_LO, VAL_CUT, contract_of=own)
        s_rule = build_bars(root, days, VAL_LO, VAL_CUT)
        front_agree = float((s_rule.groupby("day")["contract"].first().reindex(days) ==
                             pd.Series(own).reindex(days)).mean())
        j = s_own.merge(b, on=["day", "hhmm"], suffixes=("_s", "_d"))
        ratio = j["volume_s"] / j["volume_d"].where(j["volume_d"] > 0)
        out["roots"][root] = {
            "days": len(days), "minutes_databento": int(len(b)), "minutes_sierra": int(len(s_own)), "matched": int(len(j)),
            "close_equal": float((j["close_s"] == j["close_d"]).mean()), "open_equal": float((j["open_s"] == j["open_d"]).mean()),
            "high_equal": float((j["high_s"] == j["high_d"]).mean()), "low_equal": float((j["low_s"] == j["low_d"]).mean()),
            "volume_ratio_median": float(ratio.median()), "front_rule_agrees_with_databento": front_agree}
        bars[root] = (s_own.drop(columns=["contract"]).assign(contract=s_own["contract"]), b)
    # D737 on Sierra bars against D737 on Databento bars (each from 2023-04, scored from 2023-07)
    s_rows, _ = d737_rows(bars["NQ"][0], bars["YM"][0], VAL_SCORED_FROM)
    d_rows, _ = d737_rows(bars["NQ"][1], bars["YM"][1], VAL_SCORED_FROM)
    m = s_rows.merge(d_rows, on="day", suffixes=("_s", "_d"))
    both = m[(m["status_s"] == "trade") & (m["status_d"] == "trade")]
    out["d737"] = {"days_compared": int(len(m)), "status_agree": float((m["status_s"] == m["status_d"]).mean()),
                   "trades_sierra": int((m["status_s"] == "trade").sum()), "trades_databento": int((m["status_d"] == "trade").sum()),
                   "same_m0_and_side": float(((both["m0_s"] == both["m0_d"]) & (both["side_s"] == both["side_d"])).mean()) if len(both) else None,
                   "gross_abs_diff_median": float((both["gross_usd_s"].astype(float) - both["gross_usd_d"].astype(float)).abs().median()) if len(both) else None,
                   "net_sum_sierra": float(both["net_usd_s"].astype(float).sum()), "net_sum_databento": float(both["net_usd_d"].astype(float).sum())}
    out["globex"] = validate_globex(data_root)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


def validate_globex(data_root: Path) -> dict[str, Any]:
    """In-sample only: Sierra Globex sessions against fut_opening_globex_1m (D644's fixture, ES and NQ) and
    fut_opening_globex_1m_ym_rty (RTY; added 2026-10-03), the fixture's contract per session, 2023-04 -> 2023-12,
    minute by minute and on what C1 reads from them: D671's `overnight` high and low over 18:00 -> 09:29."""
    import stage0_d671_break_construction as C
    parts = []
    for fn, roots in (("fut_opening_globex_1m.csv.gz", ("NQ", "ES")), ("fut_opening_globex_1m_ym_rty.csv.gz", ("RTY",))):
        for ch in pd.read_csv(data_root / "fixtures" / fn, encoding="utf-8", chunksize=2_000_000,
                              dtype={"session": str, "et": str, "hhmm": str, "contract": str}):
            parts.append(ch[ch["root"].isin(roots) & (ch["session"] > VAL_LO) & (ch["session"] <= VAL_HI)])
    fx = pd.concat(parts, ignore_index=True)                       # VAL_LO's own Globex opens the day before
    if (fx["et"] >= VAL_CUT).any():
        raise RecorderError("seal: a Databento Globex row on or after 2024-01-01 in the validation")
    res: dict[str, Any] = {}
    for root in ("NQ", "ES", "RTY"):
        d = fx[fx["root"] == root]
        con = d.groupby("session")["contract"].agg(lambda s: s.value_counts().index[0])
        s = build_globex(root, {x: sierra_name(root, con[x], x) for x in con.index}, VAL_LO, VAL_CUT)
        j = s.merge(d, on=["session", "et"], suffixes=("_s", "_d"))
        on_s, on_d = C.overnight(s.assign(root=root), root), C.overnight(d, root)
        C.overnight_audit(on_s)
        o = on_s.join(on_d, lsuffix="_s", rsuffix="_d", how="inner")
        res[root] = {"sessions_databento": int(d["session"].nunique()), "sessions_sierra": int(s["session"].nunique()),
                     "minutes_databento": int(len(d)), "minutes_sierra": int(len(s)), "matched": int(len(j)),
                     "single_contract_sessions_databento": float((d.groupby("session")["contract"].nunique() == 1).mean()),
                     **{f"{c}_equal": float((j[f"{c}_s"] == j[f"{c}_d"]).mean()) for c in ("open", "high", "low", "close")},
                     "overnight_sessions_compared": int(len(o)),
                     "on_high_equal": float((o["on_high_s"] == o["on_high_d"]).mean()),
                     "on_low_equal": float((o["on_low_s"] == o["on_low_d"]).mean()),
                     "on_range_abs_diff_points_p99": float(((o["on_high_s"] - o["on_low_s"]) - (o["on_high_d"] - o["on_low_d"]))
                                                           .abs().quantile(0.99))}
    return res


def sierra_name(root: str, contract: str, day: str) -> str:
    """Databento's contract code (e.g. NQZ3) to Sierra's file name (NQZ23-CME), the decade taken from the day."""
    mon, digit = contract[len(root)], int(contract[len(root) + 1:])
    y = int(day[:4])
    yy = y - (y % 10) + digit
    if yy < y - 1:
        yy += 10
    return f"{root}{mon}{yy % 100:02d}-{EXCH[root]}"


def merge_saved(b: pd.DataFrame, path: Path, key: str = "day", order: tuple[str, str] = ("day", "hhmm")) -> pd.DataFrame:
    """Saved bars are never lost: a day the new build lacks, or holds with fewer minutes, keeps its saved bars."""
    if not path.exists():
        return b
    old = pd.read_csv(path, dtype={key: str, "et": str, "hhmm": str, "contract": str}, encoding="utf-8")
    n_old, n_new = old.groupby(key).size(), b.groupby(key).size()
    keep_old = [d for d in n_old.index if n_new.get(d, 0) < n_old[d]]
    out = pd.concat([b[~b[key].isin(keep_old)], old[old[key].isin(keep_old)]], ignore_index=True)
    return out.sort_values(list(order)).reset_index(drop=True)


def record(refresh: bool) -> int:
    today = dt.date.today()
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range(FORWARD_FROM, today - dt.timedelta(days=1))]
    if refresh:
        import importlib.util
        s = importlib.util.spec_from_file_location("sierra_dl", REPO / "scripts" / "sierra_index_reweight_download.py")
        SD = importlib.util.module_from_spec(s)
        s.loader.exec_module(SD)
        names = sorted({n for r in EXCH for d in days[-5:] or [FORWARD_FROM] for n in candidates(r, d)})
        SD.queue(names, "scid", refresh=True)
        SD.wait_drained(names, quiet_s=120, cap_s=1800)
    cut = (today + dt.timedelta(days=1)).isoformat()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    bars, globex = {}, {}
    for root in EXCH:
        b = build_bars(root, days, FORWARD_FROM, cut)
        if len(b) and b["day"].min() < FORWARD_FROM:
            raise RecorderError("seal: a forward bar before 2026-09-21")
        b = merge_saved(b, RAW_DIR / f"fut_{root}_fwd_1m.csv.gz")
        b.to_csv(RAW_DIR / f"fut_{root}_fwd_1m.csv.gz", index=False, encoding="utf-8")
        bars[root] = b
        # the full Globex session on the day session's front: C1's overnight range (D680) and anything later
        g = build_globex(root, b.groupby("day")["contract"].first().to_dict(), FORWARD_FROM, cut)
        if len(g) and g["et"].min() < FORWARD_FROM:
            raise RecorderError("seal: a forward Globex bar before 2026-09-21")
        g = merge_saved(g, RAW_DIR / f"fut_{root}_fwd_globex_1m.csv.gz", key="session", order=("session", "et"))
        g.to_csv(RAW_DIR / f"fut_{root}_fwd_globex_1m.csv.gz", index=False, encoding="utf-8")
        globex[root] = g
    rows, info = d737_rows(bars["NQ"], bars["YM"], FORWARD_FROM)
    revised = 0
    new = rows.astype(str)
    if LEDGER.exists():
        old = pd.read_csv(LEDGER, dtype=str, keep_default_na=False, encoding="utf-8")
        added = [col for col in LEDGER_COLS if col not in old.columns]
        for col in added:                                    # a column added later is back-filled, not a revision
            old[col] = ""
        old = old[LEDGER_COLS]
        mm = old.merge(new, on="day", how="inner", suffixes=("_old", "_new"))
        ch = []
        for _, r in mm.iterrows():
            diff = [c for c in LEDGER_COLS[1:] if r[f"{c}_old"] != r[f"{c}_new"] and c not in added]
            if diff:
                ch.append({"day": r["day"], "changed": ";".join(diff),
                           "recorded_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                           "old": json.dumps({c: r[f"{c}_old"] for c in diff}), "new": json.dumps({c: r[f"{c}_new"] for c in diff})})
        if ch:                                               # the recomputation wins; the old values are kept here
            revised = len(ch)
            pd.DataFrame(ch).to_csv(REVISIONS, mode="a", header=not REVISIONS.exists(), index=False, encoding="utf-8")
        lost = old[~old["day"].isin(new["day"])]             # a day the bars no longer reach keeps its recorded row
        new = pd.concat([new, lost], ignore_index=True).sort_values("day")
    new.to_csv(LEDGER, index=False, encoding="utf-8", lineterminator="\n")
    led = pd.read_csv(LEDGER, dtype=str, keep_default_na=False, encoding="utf-8")
    tr = led[led["status"] == "trade"]
    burn = int(led["status"].str.startswith("burn-in").sum())
    nxt = [c for r in EXCH for c in candidates(r, today.isoformat())]
    missing = [n for n in nxt if open_scid(n) is None]
    print(f"[forward] sessions {len(led)} (from {FORWARD_FROM}); bars NQ/YM/ES/RTY "
          f"{'/'.join(str(bars[r]['day'].nunique()) for r in ('NQ', 'YM', 'ES', 'RTY'))}; "
          f"Globex sessions NQ/YM/ES/RTY {'/'.join(str(globex[r]['session'].nunique()) for r in ('NQ', 'YM', 'ES', 'RTY'))}"
          f"; burn-in {burn}; D737 trades {len(tr)}, net ${tr['net_usd'].astype(float).sum():.2f}; revisions {revised}"
          + (f"; MISSING Sierra files for the current/next contracts: {missing}" if missing else ""))
    return 0


# ================================================================================ self-test (synthetic and the seal)
def selftest() -> int:
    fails: list[str] = []
    if candidates("NQ", "2026-09-21") != ["NQZ26-CME", "NQH27-CME"]:
        fails.append(f"candidates for 2026-09-21: {candidates('NQ', '2026-09-21')}")
    if candidates("YM", "2026-12-18") != ["YMZ26-CBOT", "YMH27-CBOT"] or candidates("YM", "2026-12-19") != ["YMH27-CBOT", "YMM27-CBOT"]:
        fails.append("candidates around the December expiry")
    if sierra_name("NQ", "NQZ3", "2023-11-15") != "NQZ23-CME" or sierra_name("YM", "YMH4", "2023-12-20") != "YMH24-CBOT":
        fails.append("Databento-to-Sierra contract names")
    if (sierra_name("RTY", "RTYZ3", "2023-11-15") != "RTYZ23-CME"
            or candidates("RTY", "2026-09-21") != ["RTYZ26-CME", "RTYH27-CME"]):
        fails.append("RTY's contract names and candidates")
    f32 = pd.DataFrame({c: [float(np.float32(2412.3))] for c in ("open", "high", "low", "close")})
    if f32["close"].iloc[0] == 2412.3 or to_tick(f32, "RTY")["close"].iloc[0] != 2412.3 or \
            to_tick(f32, "NQ")["close"].iloc[0] != f32["close"].iloc[0]:
        fails.append("RTY's float32 prices are not rounded to the tick (or another root's are touched)")
    # a synthetic tick array: bars from trade prices, the seal raises outside the span
    t0 = us(pd.Timestamp("2026-10-05 09:30", tz=ET))
    rec = np.zeros(6, REC)
    rec["dt"] = [t0 + 1_000_000, t0 + 30_000_000, t0 + 59_000_000, t0 + 61_000_000, t0 + 125_000_000, t0 + 389 * 60_000_000 + 5]
    rec["c"] = [100.0, 101.0, 99.5, 100.25, 100.5, 102.0]
    rec["h"], rec["l"] = rec["c"] + 0.25, rec["c"] - 0.25
    rec["v"] = [1, 2, 1, 3, 1, 1]

    class MM(np.ndarray):
        pass
    mm = rec.view(MM)
    b = day_bars(mm, "2026-10-05", us(pd.Timestamp(FORWARD_FROM, tz=ET)), us(pd.Timestamp("2026-10-06", tz=ET)))
    want = [("09:30", 100.0, 101.0, 99.5, 99.5, 4), ("09:31", 100.25, 100.25, 100.25, 100.25, 3), ("09:32", 100.5, 100.5, 100.5, 100.5, 1),
            ("15:59", 102.0, 102.0, 102.0, 102.0, 1)]
    got = list(b[["hhmm", "open", "high", "low", "close", "volume"]].itertuples(index=False, name=None))
    if got != want:
        fails.append(f"day_bars: {got}")
    try:
        day_bars(mm, "2026-09-18", us(pd.Timestamp(FORWARD_FROM, tz=ET)), us(pd.Timestamp("2026-10-06", tz=ET)))
        fails.append("the seal did not raise for a vault-window day")
    except RecorderError:
        pass
    # Globex: a Monday's session opens Sunday 18:00; labels in ET; the overnight and the day in one session
    if globex_start("2026-10-05") != pd.Timestamp("2026-10-04 18:00", tz=ET):
        fails.append(f"globex_start: {globex_start('2026-10-05')}")
    s0 = us(pd.Timestamp("2026-10-04 18:00", tz=ET))
    g = np.zeros(5, REC)
    g["dt"] = [s0 - 1, s0 + 30_000_000, s0 + 359 * 60_000_000 + 999_999, us(pd.Timestamp("2026-10-05 09:29:59", tz=ET)),
               us(pd.Timestamp("2026-10-05 16:59:59", tz=ET))]
    g["c"], g["v"] = [99.0, 100.0, 101.0, 102.0, 103.0], [5, 1, 1, 1, 1]
    gb = globex_bars(g[1:].view(MM), "NQ", "2026-10-05", us(pd.Timestamp(FORWARD_FROM, tz=ET)), us(pd.Timestamp("2026-10-06", tz=ET)))
    got = list(gb[["session", "et", "hhmm", "close"]].itertuples(index=False, name=None))
    want = [("2026-10-05", "2026-10-04 18:00", "18:00", 100.0), ("2026-10-05", "2026-10-04 23:59", "23:59", 101.0),
            ("2026-10-05", "2026-10-05 09:29", "09:29", 102.0), ("2026-10-05", "2026-10-05 16:59", "16:59", 103.0)]
    if got != want:
        fails.append(f"globex_bars: {got}")
    try:
        globex_bars(g.view(MM), "NQ", "2026-09-21", us(pd.Timestamp(FORWARD_FROM, tz=ET)), us(pd.Timestamp("2026-10-06", tz=ET)))
        fails.append("the seal did not raise for 2026-09-21's Globex session (it opens 09-20)")
    except RecorderError:
        pass
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: contract candidates and the December roll; Databento-to-Sierra names; minute bars from trade "
          "prices (open/high/low/close/volume) on a synthetic tick array; the seal raises for a day before 2026-09-21; "
          "Globex sessions open the evening before, labelled in ET, and 2026-09-21's (opening 09-20) raises")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.validate:
        return validate(a.data_root)
    if a.record:
        return record(a.refresh)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
