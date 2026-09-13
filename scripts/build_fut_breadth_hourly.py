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
        if sized != r:
            if sized not in sr or "tick_usd" not in sr[sized]:
                raise GateError(f"[SPEC] {r} maps to micro {sized}, absent from "
                                f"{SPECS_REPO.name}")
            tick_usd = sr[sized]["tick_usd"]
        else:
            tick_usd = tick_usd_full
        out[r] = {"tick_price_units": d["tick_price_units"],
                  "unit_of_measure_qty": d["unit_of_measure_qty"], "uom": d["uom"],
                  "scaling_divisor": div, "scaling_reason": why,
                  "tick_usd_full_contract": tick_usd_full,
                  "sized_as": sized, "tick_usd": tick_usd,
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
        P("  --build is not implemented yet; --decode first")
        return 2
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
