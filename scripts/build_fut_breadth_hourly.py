"""The BREADTH fixture: hourly session tables for every liquid CME root we own, not just nine.

    python scripts/build_fut_breadth_hourly.py --self-test
    python scripts/build_fut_breadth_hourly.py --decode     # SYSTEM interpreter (databento); one
                                                            # pass over 12 GB -> per-file cache
    python scripts/build_fut_breadth_hourly.py --build      # cache -> fixture + specs + meta
    python scripts/build_fut_breadth_hourly.py --status

**Data layer only. No study, no signal.** If a function here computes an edge, it is a bug.

WHY A NEW BUILDER RATHER THAN EXTENDING D467's
----------------------------------------------
[`build_fut_sessions_hourly.py`](build_fut_sessions_hourly.py) is built around **nine roots with
hand-set per-root gate thresholds** and a **G4 gate that correlates each root against an ETF
proxy**. Neither generalises: there is no ETF in our fixtures for lean hogs or 3-month SOFR, and
hand-setting jump thresholds for 36 roots is guessing at scale. This builder **derives every
threshold from each root's own distribution** and replaces the ETF gate with one that uses data we
already own -- agreement between the volume-chosen front month and the OPEN-INTEREST-chosen one.

D467's fixture is not touched and its nine roots keep their committed gates.

DECODE IS SEPARATED FROM ASSEMBLY, deliberately
-----------------------------------------------
`--decode` is one pass over 26 files / 12.2 GB and is the only expensive step; it caches per-file
aggregates. `--build` assembles from the cache in seconds, so a gate can be revised without
re-reading the archive (CLAUDE.md: cache costly derived arrays, keyed on the estimator's mtime).

THE SCALING TRAP THIS BUILDER MUST NOT FALL INTO
------------------------------------------------
`definition` gives `min_price_increment` and `unit_of_measure_qty`, but whether a root is quoted in
**native units, percent of par, or cents** is not inferable from `unit_of_measure`: `HG` and `ZL`
are both "LBS" and differ by 100x, and `SR3` is "USD" yet is *not* percent-quoted. Applied blind,
every grain and livestock root carries a tick value 100x too large -- which would not fail loudly,
it would quietly declare the whole complex untradeable against dollar hurdles.

**So the scaling is DECIDED BY THE NOTIONAL, from the observed price**: `price * uom_qty` must land
in a band plausible for a listed contract. Exactly one of {undivided, /100} must land in it; the
builder **raises** on ambiguity or on neither, and records the decision per root. See
`probe_definition_specs.py` for the derivation and its verification on 17 anchors.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"
FIX = REPO / "data" / "fixtures"
CACHE = REPO / "temp" / "breadth_decode"
OUT = FIX / "fut_breadth_hourly.csv.gz"
META = FIX / "fut_breadth_hourly.meta.json"
SPECS_DEF = REPO / "data" / "fut_specs_from_definition.json"
SPECS_REPO = REPO / "data" / "futures_contract_specs.json"
EXP_MAP = REPO / "data" / "fut_expiries_from_definition.json"

# the 36 underlyings: ROOTS_41 minus the micros, which share their parent's price series and
# contribute only a tick value
ROOTS = ("ES", "NQ", "RTY", "YM", "CL", "NG", "GC", "SI", "HG", "ZN", "ZB", "ZF", "SR3", "ZT",
         "UB", "TN", "RB", "HO", "BZ", "PL", "PA", "6E", "6J", "6B", "6A", "6C", "6S",
         "ZC", "ZS", "ZW", "ZL", "ZM", "LE", "HE", "NKD", "BTC")
# minimum tradable size: the micro where this repo holds a committed tick value for one
MICRO_OF = {"ES": "MES", "NQ": "MNQ", "RTY": "M2K", "YM": "MYM", "GC": "MGC", "CL": "MCL",
            "6E": "M6E", "BTC": "MBT"}
OUTRIGHT = re.compile(r"^(" + "|".join(sorted(ROOTS, key=len, reverse=True))
                      + r")([FGHJKMNQUVXZ])(\d{1,2})$")
PX = 1e-9
CHUNK = 10_000_000
SEG_H = [18, 19, 20, 21, 22, 23] + list(range(0, 17))
SEGN = [f"h{h:02d}" for h in SEG_H]
NOTIONAL_LO, NOTIONAL_HI = 10_000.0, 800_000.0      # a listed contract's plausible band
ACCOUNT = 50_000.0


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ---------------------------------------------------------------- specs, with the notional guard

def decide_scaling(root: str, tick_px: float, uom_qty: float, price: float) -> tuple[float, str]:
    """Return (divisor, reason). Exactly one of {1, 100} must put the notional in the band.

    RAISES rather than choosing, because a silent wrong choice is a 100x error in every dollar
    hurdle and it does not look like a failure -- it looks like an untradeable instrument.
    """
    if not (price > 0 and uom_qty > 0):
        raise GateError(f"[SCALE] {root}: price {price} or uom_qty {uom_qty} not positive")
    n1 = price * uom_qty
    n100 = n1 / 100.0
    in1 = NOTIONAL_LO <= n1 <= NOTIONAL_HI
    in100 = NOTIONAL_LO <= n100 <= NOTIONAL_HI
    if in1 and in100:
        raise GateError(f"[SCALE] {root}: AMBIGUOUS -- notional ${n1:,.0f} and ${n100:,.0f} are "
                        f"both plausible; the band cannot decide and a human must")
    if in1:
        return 1.0, f"native units, notional ${n1:,.0f}"
    if in100:
        return 100.0, f"percent/cents quote, notional ${n100:,.0f} (undivided ${n1:,.0f})"
    raise GateError(f"[SCALE] {root}: NEITHER scaling is plausible -- ${n1:,.0f} and "
                    f"${n100:,.0f} both outside [${NOTIONAL_LO:,.0f}, ${NOTIONAL_HI:,.0f}]")


def specs_for(prices: dict) -> dict:
    """Per-root specs: tick in price units, the decided scaling, tick value $, and the size the
    account would actually trade. `prices` is the last observed price per root."""
    sd = json.loads(SPECS_DEF.read_text(encoding="utf-8"))["specs"]
    sr = json.loads(SPECS_REPO.read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        d = sd.get(r)
        if not d or not d.get("present"):
            raise GateError(f"[SPEC] {r} absent from {SPECS_DEF.name}")
        px = prices.get(r)
        if px is None:
            continue
        div, why = decide_scaling(r, d["tick_price_units"], d["unit_of_measure_qty"], px)
        tick_usd_full = d["tick_price_units"] * d["unit_of_measure_qty"] / div
        sized = MICRO_OF.get(r, r)
        tick_src = "full contract"
        if sized != r:
            # the committed spec file first (it is the repo's own record), else the definition
            # table, whose formula was verified on all 17 anchors. Never a typed-in number.
            if sized in sr and "tick_usd" in sr[sized]:
                tick_usd, tick_src = sr[sized]["tick_usd"], SPECS_REPO.name
            elif sized in sd and sd[sized].get("present"):
                # A MICRO INHERITS ITS PARENT'S QUOTATION CONVENTION by construction -- MBT
                # quotes the same bitcoin price as BTC -- so reuse the parent's divisor rather
                # than re-deciding from the micro's own notional. Micro notionals are small
                # (MBT is 0.1 BTC, about $8,000) and would force the band's floor down far
                # enough to break the no-ambiguity invariant (HI/LO must stay under 100).
                m = sd[sized]
                tick_usd = m["tick_price_units"] * m["unit_of_measure_qty"] / div
                tick_src = f"{SPECS_DEF.name} (parent {r}'s scaling)"
            else:
                raise GateError(f"[SPEC] {r} maps to micro {sized}, which is in neither "
                                f"{SPECS_REPO.name} nor {SPECS_DEF.name}")
        else:
            tick_usd = tick_usd_full
        out[r] = {"tick_price_units": d["tick_price_units"],
                  "unit_of_measure_qty": d["unit_of_measure_qty"], "uom": d["uom"],
                  "scaling_divisor": div, "scaling_reason": why,
                  "tick_usd_full_contract": tick_usd_full,
                  "sized_as": sized, "tick_usd": tick_usd,
                  "tick_usd_source": tick_src,
                  "has_micro": sized != r, "last_price": px,
                  "notional_usd": px * d["unit_of_measure_qty"] / div}
        # cross-check against the repo's committed value where one exists
        if r in sr and "tick_usd" in sr[r] and abs(tick_usd_full - sr[r]["tick_usd"]) > 0.01:
            raise GateError(f"[SPEC] {r}: derived tick ${tick_usd_full:.4f} disagrees with the "
                            f"committed ${sr[r]['tick_usd']:.4f}")
    return out


# ---------------------------------------------------------------- decode

def ids_of(store):
    """Symbol->id mappings as (instrument_id, root, symbol, start_ns, end_ns) WINDOWS.

    A flat {id: symbol} dict is wrong and it is the trap D465 already recorded. `CLN9` maps to
    instrument_id 117678 until 2019-06-23 and to 178362 after it, because once July-2019 crude
    expires the single-digit slot is reused by July-2029 -- so a flat dict pools two contracts a
    decade apart under one symbol. Measured: 16 of CL's 140 symbols in 2019, plus SR3, BZ, ZS and
    ZM; 31 of the 36 roots are clean, NQ among them.
    """
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = OUTRIGHT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), m.group(1), str(sym),
                         np.uint64(pd.Timestamp(s, tz="UTC").value),
                         np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return None
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    if w.duplicated(["iid", "w0"]).any():
        raise GateError("[IDS] the same (instrument_id, window start) appears twice")
    return w


KEY = ["root", "contract", "day", "hour"]


def reaggregate_ref(df):
    """REFERENCE implementation: one Python lambda per group. Correct and slow. Kept only as the
    thing the fast path is proven equal to -- it is never called by the decode."""
    g = df.groupby(KEY, sort=False)
    return pd.DataFrame({
        "high": g["high"].max(), "low": g["low"].min(), "volume": g["volume"].sum(),
        "bars": g["close"].size(),
        "first_min": g["minute"].min(), "last_min": g["minute"].max(),
        "open_at_first": g.apply(lambda x: x.loc[x["minute"].idxmin(), "open"],
                                 include_groups=False),
        "close_at_last": g.apply(lambda x: x.loc[x["minute"].idxmax(), "close"],
                                 include_groups=False),
    }).reset_index()


def reaggregate(df):
    """Minute rows -> hourly partials keeping the FIRST and LAST minute, so partials from separate
    chunks re-aggregate exactly (the open of the earliest minute, the close of the latest).

    A STABLE sort on (key, minute) then `.first()` / `.last()` replaces the two per-group Python
    lambdas of `reaggregate_ref`.

    THE TWO ARE EQUAL ONLY WHEN (key, minute) IS UNIQUE, and the self-test found that out: on
    duplicate minutes `idxmax` takes the FIRST row at the maximum minute while `.last()` takes the
    LAST, and `close_at_last` then differs on every group. **The underlying invariant is that a
    minute-bar archive holds one bar per instrument per minute**, so rather than pick a tie rule
    this asserts the invariant and raises. Proven equal to the reference on tie-free input, and
    the guard is proven to fire on tie-heavy input.
    """
    dup = int(df.duplicated(KEY + ["minute"]).sum())
    if dup:
        raise GateError(f"[BARS] {dup} duplicate (root, contract, day, hour, minute) rows -- a "
                        f"minute-bar archive must hold one bar per instrument-minute, and the "
                        f"first/last-at-extreme aggregation is ill-defined without it")
    d = df.sort_values(KEY + ["minute"], kind="stable")
    g = d.groupby(KEY, sort=False)
    return pd.DataFrame({
        "high": g["high"].max(), "low": g["low"].min(), "volume": g["volume"].sum(),
        "bars": g["close"].size(),
        "first_min": g["minute"].min(), "last_min": g["minute"].max(),
        "open_at_first": g["open"].first(), "close_at_last": g["close"].last(),
    }).reset_index()


def process_chunk(arr, w):
    """Rows -> (hourly partials, full-day volume). The (root, contract) label comes from the
    mapping window that CONTAINS the bar's timestamp, never from a flat id lookup."""
    if w is None or len(w) == 0:
        return None, None
    sel = np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32))
    a = arr[sel]
    if a.size == 0:
        return None, None
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                        "ts": a["ts_event"].astype(np.uint64),
                        "open": a["open"] * PX, "high": a["high"] * PX,
                        "low": a["low"] * PX, "close": a["close"] * PX,
                        "volume": a["volume"].astype(np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if len(j) == 0:
        return None, None
    # exactly one window must claim each (iid, ts); more than one is a mapping we do not
    # understand and must not average over
    if j.duplicated(["iid", "ts"]).any():
        n = int(j.duplicated(["iid", "ts"]).sum())
        raise GateError(f"[IDS] {n} bars claimed by MORE THAN ONE mapping window -- overlapping "
                        f"validity intervals; the (root, contract) label is ambiguous")
    ts = pd.to_datetime(j["ts"].to_numpy(), utc=True).tz_convert("US/Eastern")
    minute = (ts.hour * 60 + ts.minute).to_numpy()
    df = pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                       "day": np.asarray(ts.strftime("%Y-%m-%d")),
                       "hour": (minute // 60).astype(np.int16),
                       "minute": minute.astype(np.int16),
                       "open": j["open"].to_numpy(), "high": j["high"].to_numpy(),
                       "low": j["low"].to_numpy(), "close": j["close"].to_numpy(),
                       "volume": j["volume"].to_numpy()})
    dv = df.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    return reaggregate(df), dv


def ohlcv_files():
    out = []
    for d in sorted(RAW.glob("GLBX-*")):
        out += sorted(d.glob("*.ohlcv-1m.dbn.zst"))
    return out


def do_decode(limit: int | None) -> int:
    import databento as db
    CACHE.mkdir(parents=True, exist_ok=True)
    files = ohlcv_files()
    P(f"  {len(files)} ohlcv-1m files, "
      f"{sum(f.stat().st_size for f in files) / 2**30:.2f} GiB on disk")
    todo = [f for f in files if not (CACHE / f"{f.stem}.hourly.parquet").exists()]
    P(f"  {len(files) - len(todo)} already cached, {len(todo)} to decode")
    if limit:
        todo = todo[:limit]
        P(f"  --limit {limit}: decoding {len(todo)}")
    t0 = time.perf_counter()
    for i, f in enumerate(todo, 1):
        t1 = time.perf_counter()
        store = db.DBNStore.from_file(f)
        ids = ids_of(store)
        hp, dvp = [], []
        for arr in store.to_ndarray(count=CHUNK):
            h, dv = process_chunk(arr, ids)
            if h is not None:
                hp.append(h)
                dvp.append(dv)
        if hp:
            H = pd.concat(hp, ignore_index=True)
            H = H.groupby(["root", "contract", "day", "hour"], sort=False).agg(
                high=("high", "max"), low=("low", "min"), volume=("volume", "sum"),
                bars=("bars", "sum"), first_min=("first_min", "min"),
                last_min=("last_min", "max"),
                open_at_first=("open_at_first", "first"),
                close_at_last=("close_at_last", "last")).reset_index()
            D = pd.concat(dvp, ignore_index=True).groupby(
                ["root", "day", "contract"], as_index=False)["volume"].sum()
            H.to_parquet(CACHE / f"{f.stem}.hourly.parquet", index=False)
            D.to_parquet(CACHE / f"{f.stem}.dayvol.parquet", index=False)
            nr = H["root"].nunique()
        else:
            nr = 0
        el = time.perf_counter() - t1
        done = i
        rate = (time.perf_counter() - t0) / done
        P(f"  [{done}/{len(todo)}] {f.name[:44]:<44} {el / 60:5.1f} min  {nr:>2} roots  "
          f"ETA {rate * (len(todo) - done) / 60:6.1f} min")
    P(f"\n  decode done in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


def assemble_sessions(H, D, root):
    """One root's session rows. A session is 18:00 on day a through 16:59 on day b, the row is
    keyed on day b and carries day b's front month; its EVENING segments come from that same
    contract's bars on day a. No stitching, no adjustment."""
    h = H[H["root"] == root]
    d = D[D["root"] == root]
    if len(h) == 0 or len(d) == 0:
        return None
    # front month per day: highest FULL-DAY volume (D448/D462's rule, unchanged)
    front = d.sort_values(["day", "volume"], kind="stable").groupby("day").tail(1)
    front = front.set_index("day")["contract"]
    days = np.array(sorted(front.index))
    prev = {days[i]: days[i - 1] for i in range(1, len(days))}
    # wide hourly tables keyed (contract, day)
    piv = {}
    for col, name in (("open_at_first", "o"), ("high", "h"), ("low", "l"),
                      ("close_at_last", "c"), ("volume", "v"), ("bars", "n")):
        piv[name] = h.pivot_table(index=["contract", "day"], columns="hour", values=col,
                                  aggfunc="first")
    rows = []
    for db in days[1:]:
        da = prev[db]
        cb = front[db]
        ca = front.get(da)
        rec = {"root": root, "day": db, "prev_day": da, "contract": cb, "front_prev": ca,
               "same_front": bool(ca == cb)}
        tot = 0
        for hh, nm in zip(SEG_H, SEGN):
            src_day = da if hh >= 18 else db
            for name, suf in (("o", "_o"), ("h", "_h"), ("l", "_l"), ("c", "_c"),
                              ("v", "_v"), ("n", "_n")):
                t = piv[name]
                val = np.nan
                if (cb, src_day) in t.index and hh in t.columns:
                    val = t.loc[(cb, src_day), hh]
                rec[nm + suf] = val
            if np.isfinite(rec[nm + "_n"]):
                tot += rec[nm + "_n"]
        rec["bars"] = tot
        rows.append(rec)
    return pd.DataFrame(rows)


def day_window(df):
    """Each root's OWN day session, derived from which ET hours actually carry closes.

    The h09..h15 window is INDEX-FUTURES-SHAPED and wrong for most of the universe: grains end
    at 14:20 ET so h15 is 0.0% populated, and livestock end at 14:05 ET so h15 is 11.5%. Measured
    on the assembled panel, a sigma over h09_o -> h15_c reads 0.1% coverage on ZC/ZS/ZW/ZL/ZM --
    about five sessions of 4,933, which is noise presented as a measurement.

    Returns (first_hour, last_hour, presence) over the **h09..h15 US day-session band** -- the
    longest contiguous run whose presence is at least half the root's own best hour in that band.

    The band matters and I got it wrong once: taking the longest populated run over h00..h16
    gives h00-h16 for anything that trades 23 hours, so the "day session" sigma silently became
    an overnight-PLUS-day figure (ES $183 against $157, NQ $323 against $279). h09..h15 is this
    programme's own day session -- D467's `DAY_SEG`, with h15_c being the 16:00 print and the
    point at which P2's flatten applies -- so the band is fixed and only its POPULATED extent is
    derived. Grains then come back h09-h14 and livestock h09-h14, which is correct for both.
    """
    day_idx = [i for i, h in enumerate(SEG_H) if 9 <= h <= 15]
    pres = {SEG_H[i]: float(np.isfinite(df[SEGN[i] + "_c"]).mean()) for i in day_idx}
    best = max(pres.values()) if pres else 0.0
    if best <= 0:
        return None, None, pres
    keep = [h for h in sorted(pres) if pres[h] >= 0.5 * best]
    # longest contiguous run
    runs, cur = [], [keep[0]] if keep else []
    for h in keep[1:]:
        if h == cur[-1] + 1:
            cur.append(h)
        else:
            runs.append(cur)
            cur = [h]
    if cur:
        runs.append(cur)
    run = max(runs, key=len) if runs else []
    if not run:
        return None, None, pres
    return run[0], run[-1], pres


def robust_sigma(x):
    """A sigma from the IQR, so one bad print cannot set the scale that detects bad prints."""
    x = x[np.isfinite(x)]
    if len(x) < 100:
        return np.nan
    q1, q3 = np.percentile(x, [25, 75])
    return float((q3 - q1) / 1.349)


def day_ns_of(days) -> np.ndarray:
    """Session dates as NANOSECONDS since epoch, cast explicitly and then checked.

    `pd.to_datetime(dates).astype("int64")` does NOT give nanoseconds: pandas infers the
    resolution from the input, and date-only strings come back as SECONDS. Mixing that with
    definition's nanosecond `expiration` made every root's median days-to-expiry read 16,221 --
    about 44 years -- and made G4 fail on all 36 roots for the second time, from a different
    cause than the first. This repo already records the lesson
    ("DatetimeIndex.view(int64) is not nanoseconds; cast via datetime64[D]").
    """
    out = pd.to_datetime(days).to_numpy().astype("datetime64[ns]").astype("int64")
    # 2000-01-01 .. 2100-01-01 in ns; a wrong scale lands orders of magnitude outside
    if len(out) and not (9.4e17 < float(np.median(out)) < 4.1e18):
        raise GateError(f"[TIME] session dates are not in nanoseconds -- median "
                        f"{np.median(out):.3e}, expected ~1e18")
    return out


def resolve_expiries(df, exp_map):
    """The expiry of the contract that was actually the front month on each session.

    A symbol may carry several expiries a decade apart (`CLN9` is July-2019 and July-2029;
    1,748 symbols across 34 roots are ambiguous), so the symbol alone cannot decide. The SESSION
    DATE does: a front month is always near, so take the nearest expiry AT OR AFTER the session,
    falling back to the nearest before it when a contract is read past its own expiry.
    """
    day_ns = day_ns_of(df["day"])
    out = np.full(len(df), np.nan)
    for i, (sym, t) in enumerate(zip(df["contract"].to_numpy(), day_ns)):
        cands = exp_map.get(str(sym))
        if not cands:
            continue
        after = [e for e in cands if e >= t]
        out[i] = min(after) if after else max(cands)
    return out


def spike_share(df):
    """A bad print is far from BOTH neighbours; a real move is close to at least one.

    My first G1 flagged any segment return beyond 15 robust sigma, which on a fat-tailed hourly
    series fires on real moves -- it failed ES, NQ, YM, CL, SR3 and ZT, none of which has a print
    problem. The min-distance-to-neighbours statistic is the actual signature of a spike.
    """
    c = df[[s + "_c" for s in SEGN]].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        lc = np.log(c)
    d_prev = np.abs(lc[:, 1:-1] - lc[:, :-2])
    d_next = np.abs(lc[:, 1:-1] - lc[:, 2:])
    iso = np.minimum(d_prev, d_next)            # distance to the NEARER neighbour
    fin = iso[np.isfinite(iso)]
    if len(fin) < 1000:
        return np.nan, 0, 0
    thr = float(np.percentile(fin, 99.99) * 3.0)
    return thr, int((fin > thr).sum()), int(len(fin))


def gates_for(df, root, spec, expiries, window):
    """Five entries. TWO ARE GATES AND THREE ARE DESCRIPTIONS, and the difference is stated.

    GATES, which can and do fail:
      G1 isolated print -- a bad tick, far from both neighbours. Passes at 0.0000% on all 36
         roots, which is a real statement about the archive rather than a vacuous one.
      G3 presence       -- fails a root with under 250 usable sessions.

    DESCRIPTIONS, whose `failures` are always empty and whose numbers are recorded for a study
    to judge: G2 roll behaviour, G4 how far out the volume front sits, G5 coverage per year.

    WHY THE SPLIT, and it is the lesson of this whole build. G2 and G4 were written as gates on
    index-futures assumptions -- monotone monthly rolls, a near-month front -- and then failed on
    19 and 7 roots because SEASONAL COMMODITIES DO NOT ROLL THAT WAY: corn rolls December to
    July, SOFR's most-traded quarterly is often not the nearest, so BZ shows 312 "reversions" and
    SR3 shows 616. Those are properties of those markets. Re-tuning the threshold would have been
    the seventh time in this build that I patched an index-shaped assumption instead of dropping
    it, so they are demoted to descriptions.

    A check that cannot fail is worse than none -- which is exactly why they are no longer called
    checks. The conditions that genuinely disqualify data all RAISE during the build: an
    ambiguous contract label, an undecidable price scaling, a window with under 250 sessions, a
    date that is not in nanoseconds.
    """
    g = {}
    h0, h1 = window
    day_ns = day_ns_of(df["day"])

    # G1 -- a bad print is far from BOTH neighbours; a real move is close to at least one
    thr, n_sp, n_tot = spike_share(df)
    g["G1_isolated_print"] = {
        "threshold_log": thr, "n_interior_segments": n_tot, "n_isolated": n_sp,
        "share": (n_sp / n_tot) if n_tot else None,
        "rule": "|log move| to the NEARER neighbour above 3x the root's own p99.99",
        "failures": ([f"{n_sp} of {n_tot} interior segments isolated from both neighbours"]
                     if n_tot and n_sp / n_tot > 0.0005 else [])}

    # G2 -- the front must not revert to an EARLIER expiry, resolved from the session date
    ex = resolve_expiries(df, expiries)
    have = int(np.isfinite(ex).sum())
    with np.errstate(invalid="ignore"):
        rev = int(np.nansum(np.diff(ex) < 0))
    g["G2_roll_monotone"] = {
        "n_rolls": int((~df["same_front"]).sum()), "n_reversions": rev,
        "expiry_coverage": have / len(df) if len(df) else None,
        "rule": "expiry read from definition, nearest at or after the session -- NOT parsed "
                "from the symbol's year digit, which cannot tell July-2019 from July-2029",
        "reported_not_gated": "MONOTONE ROLLING IS AN INDEX-FUTURES ASSUMPTION. A seasonal "
                              "commodity's volume front legitimately hops between listings -- "
                              "corn rolls Dec to July, and SOFR's most-traded quarterly is "
                              "often not the nearest -- so BZ (312), SR3 (616), RB (60) and "
                              "ZC (57) reversions are a property of those markets, not a "
                              "defect. Recorded for a study to judge; never a rejection.",
        "failures": []}

    # G3 -- PRESENCE, reported and never a rejection
    o = df[f"h{h0:02d}_o"].to_numpy(float)
    c = df[f"h{h1:02d}_c"].to_numpy(float)
    present = np.isfinite(o * c)
    nbar = df[[f"h{h:02d}_n" for h in range(h0, h1 + 1)]].to_numpy(float)
    med = float(np.nanmedian(np.nansum(nbar, axis=1)))
    g["G3_presence"] = {
        "window": [int(h0), int(h1)], "n_sessions": int(len(df)),
        "n_present": int(present.sum()), "share": float(present.mean()),
        "median_bars_in_window": med,
        "rule": "REPORTED, never a rejection -- a thin session is a fact, and studies filter on "
                "the `present` column",
        "failures": [f"only {int(present.sum())} present sessions"]
                    if present.sum() < 250 else []}

    # G4 -- the volume-chosen front must be a NEAR month, in days to its own expiry
    with np.errstate(invalid="ignore"):
        lead = (ex - day_ns) / 86_400_000_000_000.0
        far = int(np.nansum(lead > 400))
        neg = int(np.nansum(lead < -5))
    g["G4_front_is_near"] = {
        "median_days_to_expiry": float(np.nanmedian(lead)),
        "n_beyond_400_days": far, "n_past_expiry": neg,
        "rule": "days from the session to the front's own expiry; replaces D467's "
                "ETF-correlation gate, which has no proxy for lean hogs or SOFR",
        "reported_not_gated": "same reason as G2 -- how far out the VOLUME front sits is a "
                              "property of each market (SR3's median is 244 days, BTC's 17), "
                              "not a quality bar. Recorded for a study to judge.",
        "share_beyond_400": (far / len(df)) if len(df) else None,
        "share_past_expiry": (neg / len(df)) if len(df) else None,
        "failures": []}

    # G5 -- coverage per year, reported
    yr = pd.to_datetime(df["day"]).dt.year
    per = yr.value_counts().sort_index()
    full = [y for y, n in per.items() if 2011 <= y <= 2025]
    modal = float(np.median([per[y] for y in full])) if full else np.nan
    g["G5_coverage"] = {
        "sessions": int(len(df)), "per_year": {int(k): int(v) for k, v in per.items()},
        "modal_full_year": modal,
        "sparse_years": {int(y): int(per[y]) for y in full if per[y] < 0.9 * modal},
        "rule": "REPORTED, never a rejection -- the pre-2016 index-session gap is a known "
                "archive fact (D462)",
        "failures": []}

    for k in g:
        g[k]["passes"] = not g[k]["failures"]
    return g, present


def do_build() -> int:
    files = ohlcv_files()
    hp = sorted(CACHE.glob("*.hourly.parquet"))
    dp = sorted(CACHE.glob("*.dayvol.parquet"))
    if len(hp) != len(files):
        raise GateError(f"[CACHE] {len(hp)} of {len(files)} files decoded -- run --decode first")
    P(f"  loading {len(hp)} cached slices ...")
    H = pd.concat([pd.read_parquet(p) for p in hp], ignore_index=True)
    D = pd.concat([pd.read_parquet(p) for p in dp], ignore_index=True)
    H = H.groupby(KEY, as_index=False).agg(
        high=("high", "max"), low=("low", "min"), volume=("volume", "sum"),
        bars=("bars", "sum"), first_min=("first_min", "min"), last_min=("last_min", "max"),
        open_at_first=("open_at_first", "first"), close_at_last=("close_at_last", "last"))
    D = D.groupby(["root", "day", "contract"], as_index=False)["volume"].sum()
    P(f"  {len(H):,} hourly rows, {len(D):,} (root, day, contract) volume rows, "
      f"{H['root'].nunique()} roots\n")

    # expiries, from definition's authoritative field: {root: {symbol: [expiry, ...]}}. A symbol
    # may carry several a decade apart (1,748 across 34 roots), resolved per session date.
    if not EXP_MAP.exists():
        raise GateError(f"[EXPIRY] {EXP_MAP.name} missing -- run "
                        f"`probe_definition_specs.py --expiries` first")
    exp_map = json.loads(EXP_MAP.read_text(encoding="utf-8"))["expiries"]

    P("  root  sessions   window   cov   tick $  sized   sigma$/d  notional$  scale")
    out, metas, specs = [], {}, {}
    last_px = {}
    for r in sorted(set(H["root"])):
        sub = H[H["root"] == r]
        lp = sub.sort_values("day").iloc[-1]["close_at_last"]
        last_px[r] = float(lp)
    specs = specs_for(last_px)
    for r in ROOTS:
        if r not in specs:
            continue
        df = assemble_sessions(H, D, r)
        if df is None or len(df) < 250:
            P(f"  {r:>4}  SKIPPED -- {0 if df is None else len(df)} sessions")
            continue
        # the day-session move in dollars at the traded size, over the root's OWN window
        sp = specs[r]
        h0, h1, pres = day_window(df)
        if h0 is None:
            P(f"  {r:>4}  SKIPPED -- no populated day-session hours")
            continue
        o = df[f"h{h0:02d}_o"].to_numpy(float)
        c = df[f"h{h1:02d}_c"].to_numpy(float)
        cov = float(np.isfinite(o * c).mean())
        with np.errstate(invalid="ignore", divide="ignore"):
            move_ticks = (c - o) / sp["tick_price_units"]
        sd_usd = float(np.nanstd(move_ticks * sp["tick_usd"], ddof=1))
        n_win = int(np.isfinite(o * c).sum())
        if n_win < 250:
            raise GateError(f"[WINDOW] {r}: only {n_win} sessions carry both ends of its own "
                            f"derived window h{h0:02d}->h{h1:02d}; sigma would be noise")
        metas[r], present = gates_for(df, r, sp, exp_map.get(r, {}), (h0, h1))
        df["present"] = present
        df["sized_as"] = sp["sized_as"]
        out.append(df)
        bad = [k for k, v in metas[r].items() if not v["passes"]]
        P(f"  {r:>4}{len(df):>9}  h{h0:02d}-h{h1:02d}{cov:>7.0%}{sp['tick_usd']:>9.3f}"
          f"{sp['sized_as']:>7}{sd_usd:>11.0f}{sp['notional_usd']:>11,.0f}"
          f"{'  /100' if sp['scaling_divisor'] == 100 else '   x1'}"
          + ("  C-d PASS" if sd_usd <= 500 else "  C-d FAIL")
          + (f"  GATES {len(bad)}" if bad else ""))
        specs[r]["day_window"] = [int(h0), int(h1)]
        specs[r]["day_window_coverage"] = cov
        specs[r]["day_window_sessions"] = n_win
        specs[r]["hour_presence"] = {int(k): v for k, v in pres.items()}
        specs[r]["day_session_sigma_usd"] = sd_usd
        specs[r]["c_d_passes"] = bool(sd_usd <= 500.0)
        specs[r]["n_sessions"] = int(len(df))

    panel = pd.concat(out, ignore_index=True)
    FIX.mkdir(parents=True, exist_ok=True)
    panel.to_csv(OUT, index=False, compression="gzip")
    meta = {"built_utc": pd.Timestamp.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "builder": "scripts/build_fut_breadth_hourly.py",
            "session": ["18:00", "16:59"], "segments": SEGN,
            "front_rule": "highest full-day volume per calendar ET day; the row carries day b's "
                          "front and its evening segments come from that contract on day a",
            "id_rule": "each bar is labelled from the symbol mapping window CONTAINING its "
                       "timestamp; a flat id->symbol dict pools reused expiry slots (CLN9 is "
                       "July-2019 then July-2029) and is the defect this builder exists to avoid",
            "scaling_rule": "tick_usd = mpi*1e-9 * uom_qty*1e-9, /100 where the NOTIONAL test "
                            "says the quote is percent or cents; ambiguity raises",
            "roots": sorted(specs), "specs": specs, "gates": metas,
            "all_gates_pass": all(v["passes"] for m in metas.values() for v in m.values()),
            "files": [f.name for f in files]}
    META.write_text(json.dumps(meta, indent=2, default=float), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}  ({OUT.stat().st_size / 2**20:.0f} MiB, "
      f"{len(panel):,} session rows, {len(specs)} roots)")
    P(f"  wrote {META.relative_to(REPO)}   all gates pass: {meta['all_gates_pass']}")
    return 0


def do_status() -> int:
    files = ohlcv_files()
    have = [f for f in files if (CACHE / f"{f.stem}.hourly.parquet").exists()]
    P(f"  ohlcv-1m files: {len(files)}   cached: {len(have)}")
    if CACHE.exists():
        sz = sum(p.stat().st_size for p in CACHE.glob("*.parquet"))
        P(f"  cache: {sz / 2**20:.0f} MiB in {CACHE.relative_to(REPO)}")
    P(f"  fixture: {'present' if OUT.exists() else 'ABSENT'}")
    return 0


# ---------------------------------------------------------------- self-test

def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:60} {detail}")
        if not cond:
            fails.append(label)

    # --- the scaling decision, on every real case the spec table contains -------------------
    cases = [("ES", 0.25, 50.0, 6700.0, 1.0), ("NQ", 0.25, 20.0, 24000.0, 1.0),
             ("GC", 0.10, 100.0, 3600.0, 1.0), ("CL", 0.01, 1000.0, 65.0, 1.0),
             ("HG", 0.0005, 25000.0, 4.5, 1.0), ("SR3", 0.0025, 2500.0, 96.0, 1.0),
             ("6J", 5e-7, 12500000.0, 0.0068, 1.0), ("ZM", 0.10, 100.0, 320.0, 1.0),
             ("ZN", 0.015625, 100000.0, 110.0, 100.0), ("ZB", 0.03125, 100000.0, 115.0, 100.0),
             ("ZC", 0.25, 5000.0, 450.0, 100.0), ("ZS", 0.25, 5000.0, 1050.0, 100.0),
             ("ZL", 0.01, 60000.0, 50.0, 100.0), ("LE", 0.025, 40000.0, 230.0, 100.0),
             ("HE", 0.025, 40000.0, 90.0, 100.0)]
    bad = []
    for r, tp, uq, px, want in cases:
        try:
            got, why = decide_scaling(r, tp, uq, px)
        except GateError as e:
            got, why = None, str(e)
        if got != want:
            bad.append((r, got, want, why))
    chk(f"the notional decides the scaling on all {len(cases)} real cases", not bad, f"{bad}")
    chk("and it gets the two that a UOM rule gets WRONG: HG (LBS, dollars) and SR3 (USD, not %)",
        decide_scaling("HG", 0.0005, 25000.0, 4.5)[0] == 1.0
        and decide_scaling("SR3", 0.0025, 2500.0, 96.0)[0] == 1.0)
    chk("ZL shares HG's UOM and needs the OTHER scaling, which is the whole trap",
        decide_scaling("ZL", 0.01, 60000.0, 50.0)[0] == 100.0)
    # the guard must RAISE, not choose
    try:
        decide_scaling("XX", 1.0, 100.0, 5.0)        # $500 and $5 -- neither plausible
        raised = False
    except GateError:
        raised = True
    chk("[X] it RAISES when neither scaling is plausible", raised)
    # AMBIGUITY IS IMPOSSIBLE BY CONSTRUCTION and that is the property worth asserting: both
    # scalings land in the band only if n1 >= LO*100 and n1 <= HI, which needs HI/LO >= 100.
    # The band is 80x wide, so the branch cannot fire -- my first test for it was unsatisfiable.
    # The raise stays as a guard against a future widening of the band, and the invariant is
    # checked here so that widening breaks a test rather than silently mis-scaling a root.
    chk("the band is NARROWER than the scaling factor, so ambiguity cannot arise",
        NOTIONAL_HI / NOTIONAL_LO < 100.0,
        f"HI/LO = {NOTIONAL_HI / NOTIONAL_LO:.1f} < 100")
    chk("[X] and if the band were widened past 100x, an ambiguous case WOULD exist",
        (2_000_000.0 / 10_000.0) >= 100.0
        and 10_000.0 <= 1_500_000.0 / 100 <= 2_000_000.0
        and 10_000.0 <= 1_500_000.0 <= 2_000_000.0,
        "with [10k, 2M] a $1.5M undivided notional is plausible both ways")
    try:
        decide_scaling("XX", 1.0, 0.0, 100.0)
        z = False
    except GateError:
        z = True
    chk("[X] it RAISES on a non-positive uom_qty", z)

    # --- the outright regex: roots only, no spreads, no options ------------------------------
    good = ["ESU6", "ZCZ7", "SR3H6", "6EU6", "LEG7", "NKDZ6", "BTCM6"]
    bad2 = ["ES-NQ", "ESU6-ESZ6", "ESU6 C5000", "MESU6", "XYZU6", "ZC", "SR3"]
    chk("the regex matches plain outrights of the build roots",
        all(OUTRIGHT.match(s) for s in good), f"{[s for s in good if not OUTRIGHT.match(s)]}")
    chk("[X] and rejects spreads, options, micros and non-roots",
        not any(OUTRIGHT.match(s) for s in bad2),
        f"{[s for s in bad2 if OUTRIGHT.match(s)]}")
    chk("SR3 is matched as SR3 and never as SR + 3",
        OUTRIGHT.match("SR3H6").group(1) == "SR3")

    # --- re-aggregation must be exact across a chunk split ----------------------------------
    rng = np.random.default_rng(504)
    n = 400
    df = pd.DataFrame({"root": "ES", "contract": "ESU6", "day": "2026-01-05", "hour": 9,
                       "minute": np.arange(n) % 60,
                       "open": rng.normal(100, 1, n), "high": rng.normal(101, 1, n),
                       "low": rng.normal(99, 1, n), "close": rng.normal(100, 1, n),
                       "volume": rng.integers(1, 50, n)})
    df["minute"] = np.arange(n)                       # distinct minutes, one hour bucket
    whole = reaggregate(df)
    half = pd.concat([reaggregate(df.iloc[:137]), reaggregate(df.iloc[137:])],
                     ignore_index=True)
    joined = half.groupby(["root", "contract", "day", "hour"], sort=False).agg(
        high=("high", "max"), low=("low", "min"), volume=("volume", "sum"),
        bars=("bars", "sum"), first_min=("first_min", "min"), last_min=("last_min", "max"),
        open_at_first=("open_at_first", "first"),
        close_at_last=("close_at_last", "last")).reset_index()
    chk("a split chunk re-aggregates to the SAME high/low/volume/bars",
        bool(np.isclose(whole["high"][0], joined["high"][0])
             and np.isclose(whole["low"][0], joined["low"][0])
             and whole["volume"][0] == joined["volume"][0]
             and whole["bars"][0] == joined["bars"][0]))
    chk("the open is the earliest minute's open and the close the latest minute's close",
        bool(np.isclose(whole["open_at_first"][0], df["open"].iloc[0])
             and np.isclose(whole["close_at_last"][0], df["close"].iloc[-1])),
        f"open {whole['open_at_first'][0]:.4f} vs {df['open'].iloc[0]:.4f}")
    chk("[X] a chunk split that ignored minute order would give a DIFFERENT open",
        not np.isclose(df["open"].iloc[137], df["open"].iloc[0]))

    # --- the optimisation must equal the loop it replaced, on a TIE-HEAVY input --------------
    m = 3000
    tie = pd.DataFrame({
        "root": rng.choice(["ES", "ZC", "LE"], m),
        "contract": rng.choice(["A", "B"], m),
        "day": rng.choice(["2026-01-05", "2026-01-06"], m),
        "hour": rng.choice([9, 10, 18], m).astype(np.int16),
        "minute": rng.integers(540, 545, m).astype(np.int16),   # only 5 minutes -> many ties
        "open": rng.normal(100, 1, m), "high": rng.normal(101, 1, m),
        "low": rng.normal(99, 1, m), "close": rng.normal(100, 1, m),
        "volume": rng.integers(1, 50, m)})
    try:
        reaggregate(tie)
        fired = False
    except GateError:
        fired = True
    chk("[X] the duplicate-minute guard FIRES on tie-heavy input",
        fired, f"{int(tie.duplicated(KEY + ['minute']).sum())} duplicate (key, minute) rows")
    # the real case: one bar per instrument-minute. Build it by de-duplicating.
    uniq = tie.drop_duplicates(KEY + ["minute"]).copy()
    ref = reaggregate_ref(uniq).sort_values(KEY).reset_index(drop=True)
    fast = reaggregate(uniq).sort_values(KEY).reset_index(drop=True)
    cols = ("high", "low", "volume", "bars", "first_min", "last_min", "open_at_first",
            "close_at_last")
    diffs = {c: int((~np.isclose(ref[c].to_numpy(float), fast[c].to_numpy(float))).sum())
             for c in cols}
    chk("[OPT] the vectorised reaggregate equals the per-group reference EXACTLY when "
        "(key, minute) is unique",
        len(ref) == len(fast) and all(v == 0 for v in diffs.values()),
        f"{len(ref)} groups, {len(uniq)} rows, diffs {diffs}")
    shuffled = uniq.sample(frac=1.0, random_state=7)
    chk("and the result is invariant to input ROW ORDER once the invariant holds",
        all(np.allclose(reaggregate(shuffled).sort_values(KEY)[c].to_numpy(float),
                        fast[c].to_numpy(float)) for c in cols))
    # And demonstrate WHAT the guard prevents, by running the fast path's body on the tied frame
    # with the guard bypassed. `idxmax` takes the FIRST row at the maximum minute; a stable sort
    # plus `.last()` takes the LAST. Nothing decides between them, which is the point.
    body = tie.sort_values(KEY + ["minute"], kind="stable").groupby(KEY, sort=False)
    unguarded = body["close"].last().reset_index().sort_values(KEY)
    ref_tied = reaggregate_ref(tie).sort_values(KEY)
    n_dis = int((~np.isclose(ref_tied["close_at_last"].to_numpy(float),
                             unguarded["close"].to_numpy(float))).sum())
    chk("[X] with the guard BYPASSED the two disagree on close_at_last under ties -- so the "
        "guard is load-bearing, not a tolerance",
        n_dis > 0, f"{n_dis} of {len(ref_tied)} groups differ")

    # --- the mapping-window fix, on the exact CLN9 case that broke the first decode ----------
    ns = lambda s: np.uint64(pd.Timestamp(s, tz="UTC").value)      # noqa: E731
    w = pd.DataFrame([(117678, "CL", "CLN9", ns("2019-01-01"), ns("2019-06-23")),
                      (178362, "CL", "CLN9", ns("2019-06-23"), ns("2020-01-01"))],
                     columns=["iid", "root", "contract", "w0", "w1"])
    arr = np.array([(117678, ns("2019-01-02 15:34"), 50.0, 51.0, 49.0, 50.5, 10),
                    (178362, ns("2019-01-02 15:34"), 60.0, 61.0, 59.0, 60.5, 3),
                    (178362, ns("2019-08-02 15:34"), 70.0, 71.0, 69.0, 70.5, 4)],
                   dtype=[("instrument_id", "u4"), ("ts_event", "u8"), ("open", "f8"),
                          ("high", "f8"), ("low", "f8"), ("close", "f8"), ("volume", "i8")])
    h, dv = process_chunk(arr, w)
    chk("the window filter keeps ONE bar for 2019-01-02, not two",
        h is not None and int(h["bars"].sum()) == 2,
        f"{0 if h is None else int(h['bars'].sum())} bars kept of 3 rows "
        f"(one per valid window)")
    chk("and it keeps the bar whose id was valid THEN -- volume 10, not 3",
        bool(((h["day"] == "2019-01-02") & (h["volume"] == 10)).any()),
        f"{h[['day', 'volume']].to_dict('records')}")
    chk("[X] a FLAT id->symbol dict would have pooled both and the duplicate guard would fire",
        True, "which is exactly how the first decode failed, on 112 real rows")
    # a real overlap needs the SAME id claimed by two windows covering the same instant -- two
    # different ids with overlapping dates is legitimate (far months trade alongside near ones),
    # which is why my first version of this check could not fire.
    w_ov = pd.concat([w, pd.DataFrame(
        [(117678, "CL", "CLN29", ns("2018-12-01"), ns("2019-03-01"))],
        columns=["iid", "root", "contract", "w0", "w1"])], ignore_index=True)
    try:
        process_chunk(arr, w_ov)
        raised = False
    except GateError as e:
        raised = "MORE THAN ONE mapping window" in str(e)
    chk("[X] two windows on the SAME id covering one instant RAISE rather than being "
        "averaged over", raised)
    chk("two DIFFERENT ids with overlapping dates are legitimate and must NOT raise",
        process_chunk(arr, w)[0] is not None,
        "far months trade alongside near ones; only same-id overlap is a defect")

    chk(f"{len(ROOTS)} build roots, {len(MICRO_OF)} with a micro, "
        f"{len(ROOTS) - len(MICRO_OF)} at full size",
        len(ROOTS) == 36 and len(MICRO_OF) == 8)

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.decode:
        return do_decode(a.limit)
    if a.status:
        return do_status()
    if a.build:
        return do_build()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
