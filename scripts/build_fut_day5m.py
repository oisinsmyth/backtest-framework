"""The 5-minute day-session fixture: 84 bars a session, for the intraday reversion label.

    python scripts/build_fut_day5m.py --self-test
    python scripts/build_fut_day5m.py --decode      # SYSTEM python (databento); one pass, cached
    python scripts/build_fut_day5m.py --build
    python scripts/build_fut_day5m.py --status

**Data layer only. No study, no signal, no label.** If a function here computes an efficiency or a
return, it is a bug -- this file produces bars and nothing else.

WHY 5 MINUTES AND NOT THE HOURLY FIXTURE
----------------------------------------
The intraday mean-reversion label is `efficiency = |sum r| / sum |r|` over a forward window of H
bars, with a NON-OVERLAPPING causal twin over the preceding H. The day session is **7 hourly
bars**, so on `fut_breadth_hourly` that pins H at 3 and yields ONE observation per session -- which
forecloses the H sweep, and H is exactly the parameter that must not be fixed by accident.

    09:00-15:59 ET = 420 minutes
      5-min  ->  84 bars/session    H sweep 3, 4, 6, 8, 12, 16, 20
     15-min  ->  28 bars/session    H sweep 3, 4, 6, 8, 12
     hourly  ->   7 bars/session    H = 3, one observation per session

WHAT THIS INHERITS RATHER THAN RE-DERIVING
------------------------------------------
Every trap already paid for:

  * **`ids_of` with VALIDITY WINDOWS**, imported from the breadth builder. A flat
    `{instrument_id: symbol}` dict pools two contracts a decade apart (`CLN9` is July-2019 then
    July-2029) and also ingests foreign instruments -- 229,206 bars of the wrong product across
    the archive (D520).
  * **The front month comes from `fut_breadth_hourly` itself**, not re-derived. That GUARANTEES
    the two fixtures agree on which contract is front on every session, which is the
    cross-consistency property a study reading both needs.
  * **`present` and `same_front` are carried through**, because D506 found that leaving absent
    rows in a panel poisons a recursive indicator: NaN propagates through EMA/ZLEMA/SMMA and cost
    20% of the signal. A study must drop them BEFORE flattening, and it can only do that if the
    flags travel with the bars.
  * **The duplicate-minute guard**, which is what caught the expiry pooling in the first place.

Parquet, not csv.gz: ~13M rows x 7 columns is roughly 10x smaller and far faster to read as
parquet, and the hourly fixture stays the committed CSV for anything that wants one.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from build_fut_breadth_hourly import (  # noqa: E402
    GateError, OUTRIGHT, PX, ROOTS, ids_of, ohlcv_files)

BREADTH = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
CACHE = REPO / "temp" / "day5m_decode"
OUT = REPO / "data" / "fixtures" / "fut_day5m.parquet"
META = REPO / "data" / "fixtures" / "fut_day5m.meta.json"

BAR_MIN = 5
DAY_LO, DAY_HI = 540, 959          # 09:00:00 .. 15:59:59 ET, inclusive
N_BARS = (DAY_HI - DAY_LO + 1) // BAR_MIN
CHUNK = 10_000_000
KEY = ["root", "contract", "day", "bar"]


def P(*a, **k):
    print(*a, **k, flush=True)


def bar_of(minute):
    """ET minute-of-day -> 5-minute bar index within the day session, or -1 outside it."""
    m = np.asarray(minute)
    b = (m - DAY_LO) // BAR_MIN
    return np.where((m >= DAY_LO) & (m <= DAY_HI), b, -1)


def reaggregate_ref(df):
    """REFERENCE: one Python lambda per group. Slow, correct, never called by the decode."""
    g = df.groupby(KEY, sort=False)
    return pd.DataFrame({
        "high": g["high"].max(), "low": g["low"].min(), "volume": g["volume"].sum(),
        "n": g["close"].size(),
        "open": g.apply(lambda x: x.loc[x["minute"].idxmin(), "open"], include_groups=False),
        "close": g.apply(lambda x: x.loc[x["minute"].idxmax(), "close"], include_groups=False),
    }).reset_index()


def reaggregate(df):
    """Minute rows -> 5-minute bars. A stable sort on (key, minute) then first/last replaces the
    reference's per-group lambdas, and is equal to it ONLY when (key, minute) is unique -- the
    same invariant the hourly builder asserts, for the same reason: on ties `idxmax` takes the
    FIRST row at the maximum minute and `.last()` takes the LAST."""
    dup = int(df.duplicated(KEY + ["minute"]).sum())
    if dup:
        raise GateError(f"[BARS] {dup} duplicate (root, contract, day, bar, minute) rows -- a "
                        f"minute archive holds one bar per instrument-minute")
    d = df.sort_values(KEY + ["minute"], kind="stable")
    g = d.groupby(KEY, sort=False)
    return pd.DataFrame({
        "high": g["high"].max(), "low": g["low"].min(), "volume": g["volume"].sum(),
        "n": g["close"].size(), "open": g["open"].first(), "close": g["close"].last(),
    }).reset_index()


def process_chunk(arr, w):
    """Rows -> 5-minute day-session bars. Labels come from the mapping window CONTAINING the
    bar's timestamp, never from a flat id lookup."""
    if w is None or len(w) == 0:
        return None
    sel = np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32))
    a = arr[sel]
    if a.size == 0:
        return None
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                        "ts": a["ts_event"].astype(np.uint64),
                        "open": a["open"] * PX, "high": a["high"] * PX,
                        "low": a["low"] * PX, "close": a["close"] * PX,
                        "volume": a["volume"].astype(np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if len(j) == 0:
        return None
    if j.duplicated(["iid", "ts"]).any():
        n = int(j.duplicated(["iid", "ts"]).sum())
        raise GateError(f"[IDS] {n} bars claimed by more than one mapping window")
    ts = pd.to_datetime(j["ts"].to_numpy(), utc=True).tz_convert("US/Eastern")
    minute = (ts.hour * 60 + ts.minute).to_numpy()
    b = bar_of(minute)
    keep = b >= 0                       # DAY SESSION ONLY -- the overnight is closed for prop
    if not keep.any():
        return None
    df = pd.DataFrame({"root": j["root"].to_numpy()[keep],
                       "contract": j["contract"].to_numpy()[keep],
                       "day": np.asarray(ts.strftime("%Y-%m-%d"))[keep],
                       "bar": b[keep].astype(np.int16),
                       "minute": minute[keep].astype(np.int16),
                       "open": j["open"].to_numpy()[keep], "high": j["high"].to_numpy()[keep],
                       "low": j["low"].to_numpy()[keep], "close": j["close"].to_numpy()[keep],
                       "volume": j["volume"].to_numpy()[keep]})
    return reaggregate(df)


def do_decode(limit) -> int:
    import databento as db
    CACHE.mkdir(parents=True, exist_ok=True)
    files = ohlcv_files()
    todo = [f for f in files if not (CACHE / f"{f.stem}.5m.parquet").exists()]
    P(f"  {len(files)} ohlcv-1m files, {len(files) - len(todo)} cached, {len(todo)} to decode")
    if limit:
        todo = todo[:limit]
    t0 = time.perf_counter()
    for i, f in enumerate(todo, 1):
        t1 = time.perf_counter()
        store = db.DBNStore.from_file(f)
        w = ids_of(store)
        parts = []
        for arr in store.to_ndarray(count=CHUNK):
            g = process_chunk(arr, w)
            if g is not None:
                parts.append(g)
        if parts:
            G = (pd.concat(parts, ignore_index=True).groupby(KEY, as_index=False)
                 .agg(high=("high", "max"), low=("low", "min"), volume=("volume", "sum"),
                      n=("n", "sum"), open=("open", "first"), close=("close", "last")))
            G.to_parquet(CACHE / f"{f.stem}.5m.parquet", index=False)
            nr, nrow = G["root"].nunique(), len(G)
        else:
            nr, nrow = 0, 0
        el = time.perf_counter() - t1
        rate = (time.perf_counter() - t0) / i
        P(f"  [{i}/{len(todo)}] {f.name[:42]:<42} {el / 60:5.1f} min  {nr:>2} roots  "
          f"{nrow:>9,} bars  ETA {rate * (len(todo) - i) / 60:6.1f} min")
    P(f"\n  decode done in {(time.perf_counter() - t0) / 60:.1f} min")
    return 0


def _et(bar: int) -> str:
    m = DAY_LO + BAR_MIN * bar
    return f"{m // 60:02d}:{m % 60:02d}"


def coverage(G: pd.DataFrame) -> dict:
    """Per-root SESSION BAND and FIRST CLEAN YEAR.

    A root's span is not its usable span.  ES's rows begin 2010-06-07 and its 2011 holds
    73 of ~252 sessions; SR3 has 257 sessions in 2020 and NO five-minute slot present in
    more than 38% of them.  A study that reads the span and trusts it silently mixes a
    13%-populated year with a full one, so the fixture carries the answer rather than
    leaving it to be rediscovered.

    TWO INDEPENDENT AXES, kept separate on purpose.  A year can hold few sessions whose
    bars are complete (ES 2015: 232 sessions at full fill -- usable) or many sessions whose
    bars are absent (SR3 2020: 257 sessions, no slot above 0.38 -- not usable).  Collapsing
    them into one flag makes those two identical, which they are not.

    band            slots present in >50% of the reference year's sessions -- the root's own
                    trading hours (84 for the 23-hour markets, 58 for grains, 55 for
                    livestock).  Taken from a RECENT year because hours have widened.
    sessions        sessions per year.  ~258 is a full calendar.
    slot_fill       fraction of the band's slots populated in >=90% of that year's sessions,
                    for every year holding >=60 sessions.
    first_full_bars earliest year with slot_fill >= 0.90.  None means never.
    first_clean     earliest year with slot_fill >= 0.90 AND >=240 sessions, i.e. a whole
                    calendar of complete sessions.  Between the two, the bars are complete
                    and the calendar is not.
    """
    G = G.copy()
    G["yr"] = pd.to_datetime(G["day"].astype(str)).dt.year
    ref = int(G.loc[G["yr"] < G["yr"].max(), "yr"].max())   # last year not part-complete
    out = {}
    for r, g in G.groupby("root"):
        last = g[g["yr"] == ref]
        occ = last.groupby("bar").size() / last["day"].nunique()
        band = [b for b in range(N_BARS) if occ.get(b, 0.0) > 0.5]
        sess = {int(y): int(gy["day"].nunique()) for y, gy in g.groupby("yr")}
        if not band:
            out[r] = {"band_slots": 0, "band_et": [], "band_gaps": [],
                      "first_full_bars_year": None, "first_clean_year": None,
                      "sessions_by_year": sess, "slot_fill_by_year": {},
                      "note": f"no slot present in >50% of {ref} sessions"}
            continue
        full, clean, fill = None, None, {}
        for y, gy in g.groupby("yr"):
            ny = gy["day"].nunique()
            if ny < 60:                      # too few sessions to measure a fill on
                continue
            o = gy.groupby("bar").size() / ny
            frac = sum(1 for b in band if o.get(b, 0.0) >= 0.90) / len(band)
            fill[int(y)] = round(frac, 3)
            if full is None and frac >= 0.90:
                full = int(y)
            if clean is None and frac >= 0.90 and ny >= 240:
                clean = int(y)
        out[r] = {"band_slots": len(band),
                  "band_et": [_et(min(band)), _et(max(band) + 1)],
                  "band_bars": [int(min(band)), int(max(band))],
                  "band_gaps": [b for b in range(min(band), max(band) + 1) if b not in band],
                  "first_full_bars_year": full, "first_clean_year": clean,
                  "sessions_by_year": sess, "slot_fill_by_year": fill}
    return {"reference_year": ref, "per_root": out}


def do_build() -> int:
    files = ohlcv_files()
    have = sorted(CACHE.glob("*.5m.parquet"))
    if len(have) != len(files):
        raise GateError(f"[CACHE] {len(have)} of {len(files)} decoded -- run --decode first")
    P(f"  loading {len(have)} cached slices ...")
    G = pd.concat([pd.read_parquet(p) for p in have], ignore_index=True)
    G = G.groupby(KEY, as_index=False).agg(
        high=("high", "max"), low=("low", "min"), volume=("volume", "sum"), n=("n", "sum"),
        open=("open", "first"), close=("close", "last"))
    P(f"  {len(G):,} raw 5-minute bars, {G['root'].nunique()} roots")

    # THE FRONT MONTH AND THE FLAGS COME FROM THE HOURLY FIXTURE, not re-derived
    b = pd.read_csv(BREADTH, usecols=["root", "day", "contract", "same_front", "present"])
    n_before = len(G)
    G = G.merge(b, on=["root", "day", "contract"], how="inner")
    P(f"  front-month join: {n_before:,} -> {len(G):,} bars "
      f"({len(G) / n_before:.1%} kept; the rest are back months)")
    if len(G) == 0:
        raise GateError("[JOIN] the front-month join kept nothing -- the contract labels differ")

    G = G.sort_values(["root", "day", "bar"], kind="stable").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    G.to_parquet(OUT, index=False)
    per = G.groupby("root").agg(bars=("close", "size"), sessions=("day", "nunique"),
                                first=("day", "min"), last=("day", "max"))
    per["bars_per_session"] = per["bars"] / per["sessions"]
    P("\n     root      bars  sessions  bars/sess       span")
    for r, row in per.iterrows():
        P(f"     {r:>4}{row['bars']:>10,.0f}{row['sessions']:>10,.0f}"
          f"{row['bars_per_session']:>11.1f}   {row['first']} .. {row['last']}")
    # WHAT THE INHERITED FLAGS ACTUALLY MARK, measured rather than asserted.  present=False
    # does NOT mean the bar is missing -- these rows carry real OHLC and real volume.
    pf = G[~G["present"]]
    flg = {"sessions": int(G.groupby(["root", "day"]).ngroups),
           "present_false_rows": int(len(pf)),
           "present_false_sessions": int(pf.groupby(["root", "day"]).ngroups),
           "present_false_nan_close": int(pf["close"].isna().sum()),
           "present_false_zero_volume": int((pf["volume"] == 0).sum()),
           "present_false_top_roots": list(
               pf.groupby("root").size().sort_values(ascending=False).head(4).index),
           "roll_sessions": int(G[~G["same_front"]].groupby(["root", "day"]).ngroups)}
    P(f"\n  FLAGS -- present=False on {flg['present_false_sessions']:,} of {flg['sessions']:,} "
      f"root-sessions, and {flg['present_false_nan_close']} of those rows have a NaN close: "
      f"the flag marks an incomplete HOURLY row, not an absent 5-minute bar")
    P(f"          same_front=False on {flg['roll_sessions']:,} root-sessions (the rolls)")

    cov = coverage(G)
    P(f"\n  COVERAGE -- band measured on {cov['reference_year']}; a span is not a usable span")
    P("     root  slots  session band       bars full  whole calendar")
    for r in sorted(cov["per_root"],
                    key=lambda k: (str(cov["per_root"][k]["first_clean_year"]), k)):
        c = cov["per_root"][r]
        band = "-".join(c["band_et"]) if c["band_slots"] else "(none)"
        P(f"     {r:>4}{c['band_slots']:>7}  {band:<17}  "
          f"{c['first_full_bars_year'] or 'NEVER':>9}  "
          f"{c['first_clean_year'] or 'NEVER':>14}"
          + (f"   intermittent slots {c['band_gaps']}" if c.get("band_gaps") else ""))

    meta = {"built_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "builder": "scripts/build_fut_day5m.py",
            "bar_minutes": BAR_MIN, "day_session_et_minutes": [DAY_LO, DAY_HI],
            "bars_per_full_session": N_BARS,
            "front_rule": "taken from fut_breadth_hourly by (root, day, contract) inner join, "
                          "NOT re-derived, so the two fixtures cannot disagree on the front",
            "id_rule": "each bar labelled from the symbol-mapping window CONTAINING its "
                       "timestamp; a flat id->symbol dict pools reused expiry slots and ingests "
                       "foreign instruments (D520)",
            "flags_carried": ["same_front", "present"],
            "why_flags": "D506: leaving absent rows in a panel poisons a recursive indicator -- "
                         "NaN propagates through EMA/ZLEMA/SMMA and cost 20% of the signal. A "
                         "study must drop them BEFORE flattening.",
            "what_present_means": f"present is the BREADTH fixture's session-level flag, "
                                  f"isfinite(hourly_open * hourly_close) over the root's own "
                                  f"h09..h15 window -- i.e. the HOURLY panel could form a "
                                  f"complete row. It is NOT 'this 5-minute bar is missing': of "
                                  f"the {flg['present_false_rows']:,} present=False rows here, "
                                  f"{flg['present_false_nan_close']} have a NaN close and "
                                  f"{flg['present_false_zero_volume']} have zero volume. They "
                                  f"are holidays, half-days and thin sessions. "
                                  f"{flg['present_false_sessions']:,} of "
                                  f"{flg['sessions']:,} root-sessions "
                                  f"({flg['present_false_sessions'] / flg['sessions']:.1%}), "
                                  f"heaviest on {', '.join(flg['present_false_top_roots'])}.",
            "what_same_front_means": f"the front contract changed at or during the session: "
                                     f"{flg['roll_sessions']:,} of {flg['sessions']:,} "
                                     f"root-sessions "
                                     f"({flg['roll_sessions'] / flg['sessions']:.1%}). A return "
                                     f"computed across such a boundary is a roll, not a move.",
            "flag_counts": flg,
            "roots": sorted(G["root"].unique()),
            "per_root": {r: {k: (int(v) if k in ("bars", "sessions") else v)
                             for k, v in row.items()} for r, row in per.iterrows()},
            "coverage": cov,
            "why_coverage": "a root's SPAN is not its usable span: ES's rows start "
                            "2010-06-07 but 2011 holds 73 of ~252 sessions, and SR3 has "
                            "257 sessions in 2020 with no slot present in >38% of them. "
                            "Read coverage.per_root[root]['first_clean_year'], not 'first'.",
            "rows": int(len(G)), "size_mib": round(OUT.stat().st_size / 2**20, 1)}
    META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}  ({len(G):,} rows, "
      f"{OUT.stat().st_size / 2**20:.0f} MiB)")
    P(f"  wrote {META.relative_to(REPO)}")
    return 0


def do_status() -> int:
    files = ohlcv_files()
    have = sorted(CACHE.glob("*.5m.parquet"))
    P(f"  ohlcv-1m files: {len(files)}   cached: {len(have)}")
    if have:
        P(f"  cache: {sum(p.stat().st_size for p in have) / 2**20:.0f} MiB")
    P(f"  fixture: {'present' if OUT.exists() else 'ABSENT'}")
    return 0


def do_self_test() -> int:
    fails = []

    def chk(label, cond, detail=""):
        P(f"    [{'PASS' if cond else 'FAIL'}] {label:60} {detail}")
        if not cond:
            fails.append(label)

    chk("09:00 is bar 0 and 15:55 is the last bar",
        bar_of(540) == 0 and bar_of(955) == N_BARS - 1 and N_BARS == 84,
        f"540->{bar_of(540)}, 955->{bar_of(955)}, {N_BARS} bars")
    chk("every minute inside a 5-minute bar maps to the same bar",
        all(bar_of(540 + k) == 0 for k in range(5)) and bar_of(545) == 1)
    chk("[X] minutes OUTSIDE the day session map to -1, not to bar 0",
        bar_of(539) == -1 and bar_of(960) == -1 and bar_of(0) == -1,
        f"08:59->{bar_of(539)}, 16:00->{bar_of(960)}, midnight->{bar_of(0)}")
    chk("the bar count divides the session exactly",
        N_BARS * BAR_MIN == DAY_HI - DAY_LO + 1)

    # --- re-aggregation: equal to the reference, and the guard fires on ties ---------------
    rng = np.random.default_rng(509)
    m = 600
    df = pd.DataFrame({"root": rng.choice(["ES", "ZN"], m),
                       "contract": "X", "day": rng.choice(["d1", "d2"], m),
                       "minute": rng.integers(540, 560, m).astype(np.int16),
                       "open": rng.normal(100, 1, m), "high": rng.normal(101, 1, m),
                       "low": rng.normal(99, 1, m), "close": rng.normal(100, 1, m),
                       "volume": rng.integers(1, 50, m)})
    df["bar"] = bar_of(df["minute"].to_numpy()).astype(np.int16)
    try:
        reaggregate(df)
        fired = False
    except GateError:
        fired = True
    chk("[X] the duplicate-minute guard FIRES on tie-heavy input", fired,
        f"{int(df.duplicated(KEY + ['minute']).sum())} duplicates")
    u = df.drop_duplicates(KEY + ["minute"]).copy()
    ref = reaggregate_ref(u).sort_values(KEY).reset_index(drop=True)
    fast = reaggregate(u).sort_values(KEY).reset_index(drop=True)
    cols = ("high", "low", "volume", "n", "open", "close")
    chk("[OPT] the vectorised reaggregate equals the reference EXACTLY when minutes are unique",
        len(ref) == len(fast) and all(
            np.allclose(ref[c].to_numpy(float), fast[c].to_numpy(float)) for c in cols),
        f"{len(ref)} bars, {len(u)} rows")
    chk("the open is the earliest minute's open and the close the latest minute's close",
        bool(np.isclose(
            fast.iloc[0]["open"],
            u[(u["root"] == fast.iloc[0]["root"]) & (u["day"] == fast.iloc[0]["day"])
              & (u["bar"] == fast.iloc[0]["bar"])].sort_values("minute").iloc[0]["open"])))

    chk("ids_of is imported from the breadth builder, not re-implemented",
        ids_of.__module__ == "build_fut_breadth_hourly", ids_of.__module__)
    chk(f"{len(ROOTS)} roots, inherited from the breadth builder", len(ROOTS) == 36)

    # --- coverage, on a constructed case whose answer is known by hand -----------------------
    # GOOD trades 84 slots every year.  SHORT trades slots 6..63 only (a grain's hours).
    # LATE is 20% populated in 2023 and full from 2024.  THIN never fills any slot.
    days = {y: [f"{y}-{1 + i // 21:02d}-{1 + i % 21:02d}" for i in range(250)]
            for y in (2023, 2024, 2025)}
    rows = []
    rng = np.random.default_rng(0)
    for y, ds in days.items():
        for di, d in enumerate(ds):
            for b in range(N_BARS):
                rows.append(("GOOD", d, b))
                if 6 <= b <= 63:
                    rows.append(("SHORT", d, b))
                if y >= 2024 or di % 3 == 0:
                    rows.append(("LATE", d, b))
                if rng.random() < 0.30:
                    rows.append(("THIN", d, b))
    CV = pd.DataFrame(rows, columns=["root", "day", "bar"])
    cv = coverage(CV)["per_root"]
    chk("coverage: the reference year is the last year that is not part-complete",
        coverage(CV)["reference_year"] == 2024, str(coverage(CV)["reference_year"]))
    chk("coverage: a full root reads 84 slots, 09:00-16:00, clean from its first year",
        (cv["GOOD"]["band_slots"], cv["GOOD"]["band_et"], cv["GOOD"]["first_clean_year"])
        == (84, ["09:00", "16:00"], 2023), str(cv["GOOD"]))
    chk("coverage: a short-session root reads ITS OWN band, not the 84-slot window",
        (cv["SHORT"]["band_slots"], cv["SHORT"]["band_et"]) == (58, ["09:30", "14:20"]),
        str(cv["SHORT"]))
    chk("coverage: a root with 50 complete-bar sessions in 2023 is not CLEAN until 2024 "
        "but its bars were already full -- the two axes separate",
        cv["LATE"]["first_clean_year"] == 2024
        and cv["LATE"]["first_full_bars_year"] == 2023
        and cv["LATE"]["sessions_by_year"][2023] == 84
        and cv["LATE"]["slot_fill_by_year"][2023] == 1.0, str(cv["LATE"]))
    chk("coverage: a root no slot fills reads first_clean_year None -- the SR3 case",
        cv["THIN"]["first_clean_year"] is None and cv["THIN"]["band_slots"] == 0,
        str(cv["THIN"]))
    broken = CV[~((CV["root"] == "GOOD") & (CV["bar"].isin((40, 41))))]
    bb = coverage(broken)["per_root"]["GOOD"]
    chk("[X] coverage FIRES on a root with a hole punched mid-session",
        bb["band_slots"] == 82 and bb["band_gaps"] == [40, 41], str(bb))

    # --- the H-sweep room this fixture exists to create --------------------------------------
    room = [h for h in (3, 4, 6, 8, 12, 16, 20) if 2 * h <= N_BARS]
    chk("84 bars leaves room for a NON-OVERLAPPING past/future pair at every H up to 20",
        room == [3, 4, 6, 8, 12, 16, 20], f"{room}")
    chk("[X] and 7 hourly bars leaves room only at H=3, which is why this fixture exists",
        [h for h in (3, 4, 6, 8, 12, 16, 20) if 2 * h <= 7] == [3])

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
    if a.build:
        return do_build()
    if a.status:
        return do_status()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
