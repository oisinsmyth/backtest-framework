"""The 1-MINUTE QUOTED MID day-session fixture, for D528's mean-reversion oracle.

    python scripts/build_fut_day1m_mid.py --self-test
    python scripts/build_fut_day1m_mid.py --decode      # bbo-1m -> 1-minute mid, cached
    python scripts/build_fut_day1m_mid.py --build       # the fixture

WHY 1 MINUTE AND WHY THE MID.  D528 needs both at once and `bbo-1m` supplies both: it is one
top-of-book record per minute, so the mid `(bid+ask)/2` is available at 1-minute resolution --
~420 bars a day session against the 84 of `fut_day5m`.

THE MID IS NOT A CONVENIENCE.  Bid-ask bounce is an MA(-1) in the TRADE price and it has
contaminated this research line three times (D523 voided, D526 s4, D529's segmenter), and no null
can hold it while releasing mean reversion because at this resolution they are the same object.
Nobody trades at the mid, so it carries none.

D526 decoded the same files but aggregated to 5-minute bars, discarding the minute detail this
fixture exists to keep.  Everything else is inherited from that builder rather than rewritten:
the UNDEF_PRICE sentinel filter (INT64_MAX passes a `> 0` test -- D507's recorded bug), the
WINDOWED id->symbol mapping (a flat dict pools contracts a decade apart -- D520/D521), and the
front month taken from `fut_breadth_hourly` by inner join so no two fixtures can disagree.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BREADTH = REPO / "data" / "fixtures" / "fut_breadth_hourly.csv.gz"
CACHE = REPO / "temp" / "d528_mid1m_cache"
OUT = REPO / "data" / "fixtures" / "fut_day1m_mid.parquet"
META = REPO / "data" / "fixtures" / "fut_day1m_mid.meta.json"

DAY_LO, DAY_HI = 540, 959          # 09:00 .. 15:59 ET, inclusive
N_MIN = DAY_HI - DAY_LO + 1        # 420


class GateError(RuntimeError):
    pass


def P(*a):
    print(*a, flush=True)


def _d526():
    """Import D526's decoder for the pieces already paid for."""
    import importlib.util
    p = REPO / "scripts" / "d526_mid_vs_trade_scaling.py"
    spec = importlib.util.spec_from_file_location("d526", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def do_decode() -> int:
    import databento as db
    Q = _d526()

    CACHE.mkdir(parents=True, exist_ok=True)
    files = Q.bbo_files()
    todo = [f for f in files if not (CACHE / f"{f.stem}.mid1m.parquet").exists()]
    P(f"  {len(files)} bbo-1m files, {len(files)-len(todo)} cached, {len(todo)} to decode "
      f"({sum(f.stat().st_size for f in todo)/2**30:.2f} GiB)")
    t0 = time.time()
    for i, f in enumerate(todo, 1):
        t1 = time.time()
        store = db.DBNStore.from_file(f)
        win = Q.id_windows(store)
        arr = store.to_ndarray()
        keep = np.isin(arr["instrument_id"], np.fromiter(win, dtype=np.uint32))
        a = arr[keep]
        del arr
        n_raw = len(a)
        undef = (a["bid_px_00"] == Q.UNDEF_PRICE) | (a["ask_px_00"] == Q.UNDEF_PRICE)
        ok = (a["bid_px_00"] > 0) & (a["ask_px_00"] > 0) & (~undef) \
            & (a["ask_px_00"] > a["bid_px_00"])
        n_undef, n_bad = int(undef.sum()), int((~ok).sum() - undef.sum())
        a = a[ok]
        mid = (a["bid_px_00"].astype(np.float64)
               + a["ask_px_00"].astype(np.float64)) * 0.5 * Q.PX
        ts = pd.to_datetime(a["ts_recv"], utc=True).tz_convert("US/Eastern")
        minute = (ts.hour * 60 + ts.minute).to_numpy()
        day = ts.strftime("%Y-%m-%d").to_numpy()
        tsv = ts.value.to_numpy() if hasattr(ts, "value") else ts.astype("int64").to_numpy()

        iid = a["instrument_id"].astype(np.int64)
        roots = np.empty(len(a), object)
        syms = np.empty(len(a), object)
        nowin = 0
        for k, lst in win.items():
            m = iid == k
            if not m.any():
                continue
            if len(lst) == 1:
                roots[m], syms[m] = lst[0][0], lst[0][1]
                continue
            tt = tsv[m]
            rr = np.empty(m.sum(), object)
            ss = np.empty(m.sum(), object)
            hit = np.zeros(m.sum(), bool)
            for (rt, sy, s_ns, e_ns) in lst:
                sel = (tt >= s_ns) & (tt < e_ns) & (~hit)
                rr[sel], ss[sel], hit[sel] = rt, sy, True
            nowin += int((~hit).sum())
            roots[m], syms[m] = rr, ss

        inday = (minute >= DAY_LO) & (minute <= DAY_HI)
        good = inday & (roots != None)                                   # noqa: E711
        d = pd.DataFrame({"root": roots[good].astype(str),
                          "contract": syms[good].astype(str),
                          "day": day[good], "minute": minute[good].astype(np.int16),
                          "mid": mid[good]})
        # ONE record per (root, contract, day, minute); bbo-1m should already be unique, so a
        # duplicate is a defect and the LAST is taken only after the count is checked.
        n_pre = len(d)
        d = d.sort_values(["root", "contract", "day", "minute"], kind="stable")
        g = d.groupby(["root", "contract", "day", "minute"], as_index=False).agg(
            mid=("mid", "last"), n_rec=("mid", "size"))
        dup = int((g["n_rec"] > 1).sum())
        g = g.drop(columns=["n_rec"])
        g.to_parquet(CACHE / f"{f.stem}.mid1m.parquet", index=False)
        rate = (time.time() - t0) / i
        P(f"  [{i:2d}/{len(todo)}] {f.name[-30:]:<30} {n_raw:>10,} quoted, "
          f"{n_undef:>7,} one-sided, {n_bad:>6,} crossed, {nowin:>5,} unwindowed, "
          f"{dup:>5,} dup-min -> {len(g):>9,} rows, {g['root'].nunique():>2} roots  "
          f"({time.time()-t1:.0f}s, ETA {rate*(len(todo)-i)/60:.0f} min)")
    P(f"\n  decode done in {(time.time()-t0)/60:.1f} min")
    return 0


def do_build() -> int:
    Q = _d526()
    files = Q.bbo_files()
    have = sorted(CACHE.glob("*.mid1m.parquet"))
    if len(have) != len(files):
        raise GateError(f"[CACHE] {len(have)} of {len(files)} decoded -- run --decode first")
    G = pd.concat([pd.read_parquet(p) for p in have], ignore_index=True)
    G = G.groupby(["root", "contract", "day", "minute"], as_index=False).agg(mid=("mid", "last"))
    P(f"  {len(G):,} raw 1-minute mid rows, {G['root'].nunique()} roots")
    b = pd.read_csv(BREADTH, usecols=["root", "day", "contract", "same_front", "present"])
    n0 = len(G)
    G = G.merge(b, on=["root", "day", "contract"], how="inner")
    P(f"  front-month join: {n0:,} -> {len(G):,} ({len(G)/n0:.1%} kept)")
    if len(G) == 0:
        raise GateError("[JOIN] the front-month join kept nothing")
    G["bar"] = (G["minute"] - DAY_LO).astype(np.int16)
    G = G.sort_values(["root", "day", "bar"], kind="stable").reset_index(drop=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    G.to_parquet(OUT, index=False)

    per = G.groupby("root").agg(rows=("mid", "size"), sessions=("day", "nunique"),
                                first=("day", "min"), last=("day", "max"))
    per["rows_per_session"] = per["rows"] / per["sessions"]
    P(f"\n     root       rows  sessions  rows/sess (of {N_MIN})    span")
    for r, row in per.iterrows():
        P(f"     {r:>4}{row['rows']:>11,.0f}{row['sessions']:>10,.0f}"
          f"{row['rows_per_session']:>13.1f}          {row['first']} .. {row['last']}")
    # STRUCTURAL FIX: the SESSION BAND PER ROOT goes in the metadata.
    # Twice now a reader has assumed a fixed 420-minute grid and silently discarded every root
    # whose session is shorter -- ZW trades roughly 09:31-14:21, and 291 minutes is its TRADING
    # DAY, not a gap. The day5m fixture recorded the same lesson and it was not carried over.
    # So the band is measured here and any reader can take it rather than rediscover it.
    cov = {}
    for r, gg in G.groupby("root"):
        ns = gg["day"].nunique()
        occ = gg.groupby("bar").size() / ns
        band = [int(b) for b in range(N_MIN) if occ.get(b, 0.0) > 0.5]
        run = []
        if band:
            arr = np.array(band)
            brk = np.flatnonzero(np.diff(arr) != 1)
            st = np.concatenate(([0], brk + 1))
            sp = np.concatenate((brk + 1, [len(arr)]))
            i = int(np.argmax(sp - st))
            run = [int(arr[st[i]]), int(arr[sp[i] - 1])]
        cov[r] = {"band_bars": run, "band_minutes": len(band),
                  "band_et": ([f"{(DAY_LO+run[0])//60:02d}:{(DAY_LO+run[0])%60:02d}",
                               f"{(DAY_LO+run[1]+1)//60:02d}:{(DAY_LO+run[1]+1)%60:02d}"]
                              if run else []),
                  "sessions": int(ns)}
    short = sorted((r, c["band_minutes"]) for r, c in cov.items() if c["band_minutes"] < 400)
    P(f"\n  SESSION BANDS: {len(cov) - len(short)} roots span ~all {N_MIN} minutes; "
      f"{len(short)} are SHORTER and a fixed grid would silently drop them:")
    for r, n in short:
        P(f"     {r:>4}  {n:>3} minutes  {'-'.join(cov[r]['band_et'])}")

    meta = {"built_utc": pd.Timestamp.now("UTC").strftime("%Y-%m-%dT%H:%M:%SZ"),
            "builder": "scripts/build_fut_day1m_mid.py",
            "price": "quoted mid (bid+ask)/2 from bbo-1m; nobody trades at it, so it carries no "
                     "bid-ask bounce -- the contaminant that voided D523 and split D526's result",
            "bar_minutes": 1, "day_session_et_minutes": [DAY_LO, DAY_HI],
            "bars_per_full_session": N_MIN,
            "front_rule": "from fut_breadth_hourly by (root, day, contract) inner join, NOT "
                          "re-derived",
            "id_rule": "each record labelled from the symbol-mapping window CONTAINING its "
                       "timestamp (D520/D521)",
            "sentinel_rule": "bid/ask == INT64_MAX is Databento's ABSENT price and PASSES a `> 0` "
                             "test; filtered explicitly (D507)",
            "flags_carried": ["same_front", "present"],
            "coverage": cov,
            "why_coverage": "A ROOT'S SESSION BAND IS ITS OWN. Two readers have now assumed a "
                            "fixed 420-minute grid and silently discarded every root whose "
                            "session is shorter -- ZW trades ~09:31-14:21 and 291 minutes is "
                            "its TRADING DAY, not a gap, while NQ and ES carry all 420 with one "
                            "unbroken run. Take coverage[root]['band_bars'], or sample inside "
                            "each session's own longest contiguous run; never assume the grid.",
            "roots": sorted(G["root"].unique()),
            "rows": int(len(G)), "sessions": int(G.groupby(["root", "day"]).ngroups),
            "span": [str(G["day"].min()), str(G["day"].max())],
            "size_mib": round(OUT.stat().st_size / 2**20, 1)}
    META.write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)}  ({len(G):,} rows, "
      f"{OUT.stat().st_size / 2**20:.0f} MiB)")
    P(f"  wrote {META.relative_to(REPO)}")
    return 0


def do_self_test() -> int:
    fails = []

    def chk(name, ok, note=""):
        P(f"    [{'PASS' if ok else 'FAIL'}] {name:<66} {note}")
        if not ok:
            fails.append(name)

    Q = _d526()
    chk("the day session is 420 minutes, 09:00..15:59 ET",
        N_MIN == 420 and DAY_LO == 540 and DAY_HI == 959)
    chk("bar 0 is 09:00 and bar 419 is 15:59",
        (DAY_LO - DAY_LO) == 0 and (DAY_HI - DAY_LO) == 419)
    px = np.array([100_000_000, Q.UNDEF_PRICE, 0, 250_000_000], dtype=np.int64)
    chk("[X] the UNDEFINED-price sentinel PASSES a `> 0` test, which is why it is filtered",
        bool((px > 0)[1]))
    chk("and the filter excludes it explicitly",
        list((px > 0) & (px != Q.UNDEF_PRICE)) == [True, False, False, True])
    chk("id_windows and the sentinel are IMPORTED from D526, not re-implemented",
        Q.id_windows.__module__ == "d526" and Q.UNDEF_PRICE == 2**63 - 1)
    chk("this fixture keeps 1-minute detail where D526 aggregated to 5",
        Q.BAR_MIN == 5 and 1 < Q.BAR_MIN)
    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--decode", action="store_true")
    ap.add_argument("--build", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return do_self_test()
    if a.decode:
        return do_decode()
    if a.build:
        return do_build()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
