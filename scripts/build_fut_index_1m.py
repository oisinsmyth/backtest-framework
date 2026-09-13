"""D462 -- the intraday index-futures fixtures: ES, NQ, YM, RTY at one minute, regular hours (09:30-15:59 ET), front month by
measured daily volume, from the CME ohlcv-1m archive. Spec committed in de75a63 BEFORE this file. Data layer only: no study.

    python scripts/build_fut_index_1m.py --build [--workers 6]   # SYSTEM interpreter (databento lives there, as D448/D449) -> data/fixtures/fut_*.csv.gz
    python scripts/build_fut_index_1m.py --verify 3    # the pool is a SPEED change only: serial vs 6 workers, bit-identical, on the three smallest files
    python scripts/build_fut_index_1m.py --gates       # G1-G4 on the written fixtures -> data/fixtures/fut_index_1m.meta.json (either interpreter)
    python scripts/build_fut_index_1m.py --selftest    # synthetic records through the same chunk function; DST; the 15:59 bar; front-by-volume; roll logic

Conventions: ts_event is the bar START, converted US/Eastern with DST; RTH = hhmm 09:30..15:59 (390 bars; the 15:59 close is the 16:00
print); front month per (root, calendar ET day) = the outright with the highest volume over the whole day (D448); every fixture bar
belongs to that day's front contract; no stitching, no adjustment.
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"; META = FIX / "fut_index_1m.meta.json"
ROOTS = ("ES", "NQ", "YM", "RTY"); OUTRIGHT = re.compile(r"^(ES|NQ|YM|RTY)([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 10_000_000
RTH_LO, RTH_HI = "09:30", "15:59"; MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}; QUARTERLY = "HMUZ"
G1_THR = {"ES": 0.010, "NQ": 0.010, "YM": 0.010, "RTY": 0.015}; G1_MAX = 40; G3_FULL = 380; G5_PRESENT = 200; G4_OC = {"ES": 0.995, "NQ": 0.995, "YM": 0.995, "RTY": 0.99}; G4_CC = 0.99; G4_MAX_EXCLUDED = 10
ETF = {"ES": "SPY", "NQ": "QQQ", "YM": "DIA", "RTY": "IWM"}; EQ_FIX = FIX / "index_extended_15m_raw.csv.gz"


def fixture_path(root):
    return FIX / f"fut_{root}_rth_1m.csv.gz"


# ------------------------------------------------------------------------------------------ the chunk function (the whole build is this, repeated)
def ids_of(store):
    """Symbol mappings as (iid, root, contract, w0, w1) WINDOWS -- never a flat {id: (root, symbol)} dict.

    D520. A flat dict keeps only the LAST mapping written for an id and throws the validity dates
    away, so one id carries one label for all time. CME reuses the single-digit-year slot the moment
    a contract expires, and a live contract can be rotated to a new id mid-year; across the ohlcv
    archive the flat dict ingested 229,206 bars of the WRONG INSTRUMENT (0.297% of 77.2M).

    Kept local rather than imported from `build_fut_breadth_hourly` because this builder's ROOTS
    include RTY, whose day session the breadth fixture gates differently -- one definition per root
    list. `build_fut_open_interest` and `build_fut_day5m` import it; this one and the micro-flow
    builder do not, and each says why.
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
                         np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return None
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    if w.duplicated(["iid", "w0"]).any():
        raise AssertionError("[IDS] the same (instrument_id, window start) appears twice")
    return w


def label_rows(a, w, ts_field="ts_event"):
    """Attach (root, contract) from the mapping window CONTAINING each bar's own timestamp.

    Returns the joined frame carrying `_i`, the positional index back into `a`. The guard is on `_i`:
    a repeated `_i` means one bar was claimed by two windows, which is the real ambiguity and cannot
    happen on correct mappings.
    """
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                        "ts": a[ts_field].astype(np.uint64),
                        "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if j["_i"].duplicated().any():
        raise AssertionError(f"[IDS] {int(j['_i'].duplicated().sum())} bars claimed by MORE THAN ONE mapping window")
    return j


def process_chunk(arr, w):
    """Rows of the four roots' outrights -> (rth DataFrame, day-volume DataFrame). Times US/Eastern; day = calendar ET date.

    `w` is the WINDOW table from `ids_of`, not a dict: each bar is labelled from the window containing
    its own ts_event, so an id CME reissued to another contract carries the label it held that day.
    Rows are put back in archive order (`sort_values("_i")`) before anything downstream sees them --
    `assemble` de-duplicates (root, day, hhmm) after a non-stable sort, so input order is load-bearing.
    """
    if w is None or len(w) == 0:
        return None, None
    j = label_rows(arr, w).sort_values("_i")
    if len(j) == 0:
        return None, None
    idx = j["_i"].to_numpy(); a = arr[idx]
    ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern"); root = j["root"].to_numpy(); sym = j["contract"].to_numpy()
    day = ts.strftime("%Y-%m-%d"); hhmm = ts.strftime("%H:%M"); vol = a["volume"].astype(np.int64)
    dv = pd.DataFrame({"root": root, "day": day, "contract": sym, "volume": vol}).groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    rth = (hhmm >= RTH_LO) & (hhmm <= RTH_HI)
    bars = pd.DataFrame({"root": root[rth], "day": np.asarray(day)[rth], "hhmm": np.asarray(hhmm)[rth], "contract": sym[rth], "open": a["open"][rth] * PX, "high": a["high"][rth] * PX, "low": a["low"][rth] * PX, "close": a["close"][rth] * PX, "volume": vol[rth]})
    return bars, dv


def assemble(bars, dv):
    """Front month per (root, day) by full-day volume; keep the front's RTH bars; sessions and rolls tables."""
    dv = dv.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    front = dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"], sort=True).tail(1).rename(columns={"contract": "front", "volume": "day_volume"})
    bars = bars.merge(front[["root", "day", "front"]], on=["root", "day"], how="inner"); bars = bars[bars["contract"] == bars["front"]].drop(columns="front")
    bars = bars.sort_values(["root", "day", "hhmm"]).drop_duplicates(["root", "day", "hhmm"]).reset_index(drop=True)
    g = bars.groupby(["root", "day"], sort=True); first = g.first(); last = g.last()
    sess = pd.DataFrame({"contract": first["contract"], "bars": g.size(), "p0930": np.where(first["hhmm"] == RTH_LO, first["open"], np.nan), "p1600": np.where(last["hhmm"] == RTH_HI, last["close"], np.nan), "rth_volume": g["volume"].sum()}).reset_index()
    sess = sess.merge(front[["root", "day", "day_volume"]], on=["root", "day"], how="left"); sess["roll"] = sess.groupby("root")["contract"].shift(1).ne(sess["contract"]) & sess.groupby("root")["contract"].shift(1).notna()
    rolls = []
    for root, s in sess.groupby("root"):
        prev = None
        for r in s.itertuples():
            if prev is not None and r.contract != prev.contract:
                v = dv[(dv["root"] == root) & (dv["day"] == r.day)].set_index("contract")["volume"]
                rolls.append(dict(root=root, day=r.day, from_contract=prev.contract, to_contract=r.contract, from_volume=int(v.get(prev.contract, 0)), to_volume=int(v.get(r.contract, 0))))
            prev = r
    return bars, sess, pd.DataFrame(rolls)


def worker(path):
    """One archive file -> its RTH bars and day-volume rows, in archive order. The unit of the pool."""
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B, D = [], []; n_in = n_kept = 0
    for arr in store.to_ndarray(count=CHUNK):
        n_in += len(arr); bars, dv = process_chunk(arr, w)
        if bars is not None:
            n_kept += len(bars); B.append(bars); D.append(dv)
    return dict(file=Path(path).name, rows_in=n_in, rth_rows_kept=n_kept,
                ids=0 if w is None else int(w["iid"].nunique()), mapping_windows=0 if w is None else int(len(w)),
                secs=round(time.time() - t0, 1),
                bars=pd.concat(B, ignore_index=True) if B else None, dv=pd.concat(D, ignore_index=True) if D else None)


def collect(files, workers):
    """Per-file results, PUT BACK INTO ARCHIVE ORDER whatever order the pool returned them in.

    Order is load-bearing, not cosmetic: `assemble` drops duplicate (root, day, hhmm) after a
    non-stable sort, so a reshuffle could silently pick a different bar. The pool is fed
    largest-file-first for balance and the results are re-sorted by the archive's own file order, so
    the concatenated frame is bit-identical to the serial loop's. `--verify` proves that on real files.
    """
    order = {f.name: i for i, f in enumerate(files)}
    if workers > 1:
        from multiprocessing import Pool
        with Pool(workers) as pool:
            res = pool.map(worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
        res.sort(key=lambda r: order[r["file"]])
    else:
        res = [worker(str(f)) for f in files]
    return res


def cmd_build(workers):
    t0 = time.time(); files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name); assert files, "no ohlcv-1m files under data/raw/databento/"
    print(f"D462 build -- {len(files)} ohlcv-1m files ({sum(f.stat().st_size for f in files)/1e9:.1f} GB), chunks of {CHUNK:,} rows, {workers} workers\n")
    res = collect(files, workers)
    prov = [{k: v for k, v in r.items() if k not in ("bars", "dv")} for r in res]
    for i, p in enumerate(prov, 1):
        print(f"  [{i:2d}/{len(files)}] {p['file'][:40]:<40} {p['rows_in']:>12,} rows -> RTH rows {p['rth_rows_kept']:>9,}  {p['secs']:>6.1f}s", flush=True)
    sec = sum(p["secs"] for p in prov); wall0 = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec/wall0:.2f}x on {workers} workers ({100*sec/wall0/max(workers,1):.0f}%)", flush=True)
    B = [r["bars"] for r in res if r["bars"] is not None]; D = [r["dv"] for r in res if r["dv"] is not None]
    bars, sess, rolls = assemble(pd.concat(B, ignore_index=True), pd.concat(D, ignore_index=True)); del B, D, res
    FIX.mkdir(parents=True, exist_ok=True)
    for root in ROOTS:
        b = bars[bars["root"] == root].drop(columns="root"); b.to_csv(fixture_path(root), index=False, compression="gzip", float_format="%.2f"); print(f"  {root}: {len(b):,} bars, {b['day'].nunique():,} sessions, {b['day'].min()} .. {b['day'].max()}, contracts {b['contract'].nunique()}")
    sess.to_csv(FIX / "fut_index_sessions.csv.gz", index=False, compression="gzip", float_format="%.2f"); rolls.to_csv(FIX / "fut_index_rolls.csv.gz", index=False, compression="gzip")
    META.write_text(json.dumps(dict(spec="de75a63", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), rth=[RTH_LO, RTH_HI], front_rule="highest full-day volume per calendar ET day", gates=None), indent=1))
    print(f"\nwrote fixtures in {(time.time()-t0)/60:.1f} min; gates not yet run (python scripts/build_fut_index_1m.py --gates)")


def cmd_verify(n, workers):
    """Prove the pool's output is BIT-IDENTICAL to the serial loop's, on the n smallest real files.

    The parallel build is only a speed change if this holds; if it ever stops holding, the fixture
    diff that justifies a rebuild is confounded by the concurrency and means nothing.
    """
    t0 = time.time(); files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    pick = sorted(sorted(files, key=lambda p: p.stat().st_size)[:n], key=lambda p: p.name)
    print(f"verify on {len(pick)} files ({sum(f.stat().st_size for f in pick)/1e9:.2f} GB): {[f.name[10:18] for f in pick]}")
    a = collect(pick, 1); b = collect(pick, workers)
    assert [r["file"] for r in a] == [r["file"] for r in b] == [f.name for f in pick], "file order not restored"
    for x, y in zip(a, b):
        assert x["rows_in"] == y["rows_in"] and x["rth_rows_kept"] == y["rth_rows_kept"], x["file"]
    for name, k in (("bars", "bars"), ("day volume", "dv")):
        sa = pd.concat([r[k] for r in a if r[k] is not None], ignore_index=True)
        sb = pd.concat([r[k] for r in b if r[k] is not None], ignore_index=True)
        pd.testing.assert_frame_equal(sa, sb, check_exact=True)
        print(f"  {name}: {len(sa):,} rows identical row for row, column for column")
    ba, _, _ = assemble(pd.concat([r["bars"] for r in a if r["bars"] is not None], ignore_index=True),
                        pd.concat([r["dv"] for r in a if r["dv"] is not None], ignore_index=True))
    bb, _, _ = assemble(pd.concat([r["bars"] for r in b if r["bars"] is not None], ignore_index=True),
                        pd.concat([r["dv"] for r in b if r["dv"] is not None], ignore_index=True))
    pd.testing.assert_frame_equal(ba, bb, check_exact=True)
    print(f"  assembled front-month bars: {len(ba):,} rows identical")
    print(f"VERIFY PASSED in {(time.time()-t0)/60:.1f} min -- serial and {workers}-worker builds agree exactly")


# ------------------------------------------------------------------------------------------ the gates
def third_friday(y, m):
    d = pd.Timestamp(year=y, month=m, day=1); off = (4 - d.dayofweek) % 7; return d + pd.Timedelta(days=off + 14)


def expiry_of(contract, roll_day):
    m = OUTRIGHT.match(contract); mon = MONTH[m.group(2)]; yy = int(m.group(3)); y0 = int(roll_day[:4])
    cands = [y for y in range(y0 - 1, y0 + 12) if (y % 10 == yy if len(m.group(3)) == 1 else y % 100 == yy)]
    for y in cands:
        e = third_friday(y, mon)
        if e >= pd.Timestamp(roll_day) - pd.Timedelta(days=5):
            return e
    return third_friday(cands[-1], mon)


OPEN_MIN = [f"09:{m:02d}" for m in range(30, 45)]      # the span of the equity fixture's 09:30 bar, G4's open-side reference


def discontinuous_open(bars):
    """Sessions whose minute bars are NOT contiguous over 09:30-09:44 -- the open is not a market-clearing price.

    G4's open-side reference is the ETF's 09:30 FIFTEEN-MINUTE bar, so the futures must have traded
    through that same span for the two legs to measure the same interval. The window is that bar's
    own span, not a tuned parameter.

    D522: on 2020-03-16 every index root printed ONCE at 09:30 -- RTY 115 lots at a single price,
    the limit -- and nothing until 09:45, while the ETFs' 09:30 bars barely traded (QQQ 0.4% of its
    median opening volume). The futures' 09:30 print was limit-locked and the ETF's was the true
    gap-down, so the gate was comparing a pinned price against a cleared one. A halt LATER in the
    session does not do this: both markets still open at 09:30 and close at 16:00.

    Decided from the futures bars ALONE. It never sees the disagreement it is used to judge.
    """
    n = bars[bars["hhmm"].isin(OPEN_MIN)].groupby("day")["hhmm"].nunique()
    n = n.reindex(sorted(set(bars["day"]))).fillna(0)
    return set(n[n < len(OPEN_MIN)].index)


def gates(log=print):
    meta = json.loads(META.read_text()); sess = pd.read_csv(FIX / "fut_index_sessions.csv.gz", dtype={"day": str, "contract": str}); rolls = pd.read_csv(FIX / "fut_index_rolls.csv.gz", dtype={"day": str}) if (FIX / "fut_index_rolls.csv.gz").stat().st_size > 30 else pd.DataFrame()
    eq = pd.read_csv(EQ_FIX, dtype={"timestamp": str, "symbol": str}); eq["day"] = eq["timestamp"].str[:10]; eq["hhmm"] = eq["timestamp"].str[11:16]; out = {}; ok_all = True
    for root in ROOTS:
        b = pd.read_csv(fixture_path(root), dtype={"day": str, "hhmm": str, "contract": str}); s = sess[sess["root"] == root].sort_values("day").reset_index(drop=True); g = {}
        # G1 unexplained bars
        c = b["close"].to_numpy(); same = (b["day"].to_numpy()[1:] == b["day"].to_numpy()[:-1]) & (b["contract"].to_numpy()[1:] == b["contract"].to_numpy()[:-1]); r = np.abs(c[1:] / c[:-1] - 1); big = np.flatnonzero(same & (r > G1_THR[root])) + 1
        lst = [(b["day"].iat[i], b["hhmm"].iat[i], float(round(100 * (c[i] / c[i - 1] - 1), 2))) for i in big]; g["G1"] = dict(threshold=G1_THR[root], n=len(lst), bars=lst, days=sorted({d for d, _, _ in lst}), passes=bool(len(lst) <= G1_MAX))
        # G2 rolls
        rr = rolls[rolls["root"] == root].sort_values("day") if len(rolls) else pd.DataFrame(); fwd = revert = 0; dbe = []; per_q = {}
        for x in rr.itertuples():
            a, z = OUTRIGHT.match(x.from_contract), OUTRIGHT.match(x.to_contract); ea, ez = expiry_of(x.from_contract, x.day), expiry_of(x.to_contract, x.day)
            fwd += ez > ea; revert += ez < ea; dbe.append(int(np.busday_count(np.datetime64(x.day), np.datetime64(str(ea.date()))))); q = f"{ea.year}Q{(ea.month-1)//3+1}"; per_q[q] = per_q.get(q, 0) + 1
        multi = sum(v > 1 for v in per_q.values()); dbe = np.array(dbe)
        g["G2"] = dict(n_rolls=int(len(rr)), forward=int(fwd), reverting=int(revert), quarters_with_more_than_one=int(multi), days_before_expiry_p50=float(np.median(dbe)) if dbe.size else None, days_before_expiry_min=int(dbe.min()) if dbe.size else None, days_before_expiry_max=int(dbe.max()) if dbe.size else None,
                      passes=bool(len(rr) > 0 and revert == 0 and multi == 0 and dbe.min() >= 0 and dbe.max() <= 15))
        # G3 coverage
        short = s[s["bars"] < G3_FULL]; early = short[short["bars"].between(200, 220)]; hh = b.groupby("hhmm").size(); full_days = int((s["bars"] >= G3_FULL).sum()); present = float((hh >= 0.99 * full_days).mean())
        g["G3"] = dict(p50_bars=float(s["bars"].median()), n_sessions=int(len(s)), n_short=int(len(short)), n_early_close_like=int(len(early)), other_short=[(d, int(n)) for d, n in zip(short[~short.index.isin(early.index)]["day"], short[~short.index.isin(early.index)]["bars"])][:40], share_hhmm_present_on_99pct=present, passes=bool(s["bars"].median() == 390 and present >= 0.99))
        # G4 cross-check
        e = eq[eq["symbol"] == ETF[root]]; eo = e[e["hhmm"] == "09:30"].groupby("day")["open"].first(); ec = e[e["hhmm"] == "15:45"].groupby("day")["close"].last(); ed = pd.DataFrame({"eo": eo, "ec": ec}).dropna()
        f = s.set_index("day")[["p0930", "p1600", "contract"]].dropna(); j = f.join(ed, how="inner"); oc_f = j["p1600"] / j["p0930"] - 1; oc_e = j["ec"] / j["eo"] - 1; oc = float(np.corrcoef(oc_f, oc_e)[0, 1]) if len(j) > 30 else float("nan")
        # AMENDED 2026-09-13 (D522). `corr_open_to_close` stays exactly what it was and is now REPORTED, not gated;
        # the gated statistic excludes sessions whose open was not a continuous market (see discontinuous_open),
        # and the excluded sessions are NAMED with their disagreement so the exclusion cannot hide a defect.
        holed = discontinuous_open(b); keep = ~j.index.isin(holed)
        oc_c = float(np.corrcoef(oc_f[keep], oc_e[keep])[0, 1]) if int(keep.sum()) > 30 else float("nan")
        exc = [dict(day=d, futures_pct=round(100 * float(oc_f[d]), 3), etf_pct=round(100 * float(oc_e[d]), 3), gap_pct=round(100 * float(oc_f[d] - oc_e[d]), 3)) for d in j.index[~keep]]
        same_c = (j["contract"].shift(1) == j["contract"]); cc_f = (j["p1600"] / j["p1600"].shift(1) - 1)[same_c]; cc_e = (j["ec"] / j["ec"].shift(1) - 1)[same_c]; cc = float(np.corrcoef(cc_f.dropna(), cc_e.dropna())[0, 1]) if same_c.sum() > 30 else float("nan")
        g["G4"] = dict(etf=ETF[root], matched_days=int(len(j)), corr_open_to_close=oc, corr_open_to_close_continuous_open=oc_c,
                       days_continuous_open=int(keep.sum()), excluded_open_not_continuous=exc,
                       corr_close_to_close_same_contract=cc,
                       passes=bool(oc_c >= G4_OC[root] and cc >= G4_CC and len(exc) <= G4_MAX_EXCLUDED))
        # G5 (added 2026-09-12 after the build, see the D462 ADDENDUM): sessions against the equity calendar, per year. The early archive
        # carries the index futures' evening bars but not their day session on most days before 2016 -- G3 counts bars per PRESENT
        # session and could not see a missing session. usable_start = the first year from which every later year has >= 97% of the
        # equity calendar's days as full (>= G3_FULL bars) sessions.
        # a session is PRESENT when it has a day session at all (>= G5_PRESENT bars: early closes and the March-2020 halted days count);
        # G3 already scores short sessions -- G5 scores absent ones
        spy_days = sorted(set(eq[eq["symbol"] == "SPY"]["day"])); have = set(s[s["bars"] >= G5_PRESENT]["day"]); lo = min(have) if have else "9999"; cal = [d for d in spy_days if d >= lo and d <= "2026-08-26"]
        cov = {}
        for y in sorted({d[:4] for d in cal}):
            ds = [d for d in cal if d[:4] == y]; cov[y] = float(np.mean([d in have for d in ds]))
        years = sorted(cov); usable_year = next((y for y in years if all(cov[z] >= 0.97 for z in years if z >= y)), None)
        usable_start = min(d for d in have if d[:4] >= usable_year) if usable_year else None
        g["G5"] = dict(coverage_by_year={y: round(v, 3) for y, v in cov.items()}, usable_start=usable_start, passes=bool(usable_start is not None))
        log(f"     G5 coverage vs the equity calendar: " + " ".join(f"{y}:{100*v:.0f}%" for y, v in cov.items()) + f"  -> usable from {usable_start}")
        g["passes"] = all(g[k]["passes"] for k in ("G1", "G2", "G3", "G4", "G5")); ok_all &= g["passes"]; out[root] = g
        log(f"{root}: G1 {g['G1']['n']} bars > {100*G1_THR[root]:.1f}% on days {g['G1']['days'][:12]}{'...' if len(g['G1']['days']) > 12 else ''} {'PASS' if g['G1']['passes'] else 'FAIL'} | G2 rolls {g['G2']['n_rolls']} fwd {g['G2']['forward']} revert {g['G2']['reverting']} multi-per-quarter {g['G2']['quarters_with_more_than_one']} days-before-expiry p50 {g['G2']['days_before_expiry_p50']} [{g['G2']['days_before_expiry_min']},{g['G2']['days_before_expiry_max']}] {'PASS' if g['G2']['passes'] else 'FAIL'} | G3 p50 {g['G3']['p50_bars']:.0f} short {g['G3']['n_short']} (early-close-like {g['G3']['n_early_close_like']}, other {len(g['G3']['other_short'])}) {'PASS' if g['G3']['passes'] else 'FAIL'} | G4 vs {ETF[root]} n {g['G4']['matched_days']} oc {oc:.4f} (all days, reported) -> {oc_c:.4f} on {g['G4']['days_continuous_open']} with a continuous open, excluding {len(exc)} {[x['day'] for x in exc]} cc {cc:.4f} {'PASS' if g['G4']['passes'] else 'FAIL'}")
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok_all); META.write_text(json.dumps(meta, indent=1)); log(f"\nALL GATES {'PASS' if ok_all else 'FAIL'}; wrote {META.relative_to(REPO)}")
    return ok_all


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) process_chunk: DST, the RTH window, the 15:59 bar in and 16:00 out, only the four roots' outrights")
    def wrow(iid, root, contract, s, e):
        return (iid, root, contract, np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value))
    WCOLS = ["iid", "root", "contract", "w0", "w1"]
    ids = pd.DataFrame([wrow(1, "ES", "ESH5", "2015-01-01", "2015-04-01"), wrow(2, "ES", "ESM5", "2015-01-01", "2015-10-01"),
                        wrow(3, "NQ", "NQH5", "2015-01-01", "2015-10-01")], columns=WCOLS)
    def ts(s):
        return int(pd.Timestamp(s).value)
    rows = [(ts("2015-01-15 14:30:00+00:00"), 1), (ts("2015-01-15 13:30:00+00:00"), 1), (ts("2015-07-15 13:30:00+00:00"), 2), (ts("2015-07-15 19:59:00+00:00"), 2), (ts("2015-07-15 20:00:00+00:00"), 2), (ts("2015-07-15 13:30:00+00:00"), 3), (ts("2015-07-15 13:30:00+00:00"), 9)]
    arr = np.array([(t, i, 2000 * 1e9, 2001 * 1e9, 1999 * 1e9, 2000.5 * 1e9, 100) for t, i in rows], dtype=[("ts_event", "<i8"), ("instrument_id", "<u4"), ("open", "<i8"), ("high", "<i8"), ("low", "<i8"), ("close", "<i8"), ("volume", "<u8")])
    bars, dv = process_chunk(arr, ids); key = set(zip(bars["contract"], bars["day"], bars["hhmm"]))
    assert ("ESH5", "2015-01-15", "09:30") in key and ("ESH5", "2015-01-15", "08:30") not in key, "EST conversion"       # 14:30 UTC in January is 09:30 EST; 13:30 UTC is 08:30
    assert ("ESM5", "2015-07-15", "09:30") in key and ("ESM5", "2015-07-15", "15:59") in key and ("ESM5", "2015-07-15", "16:00") not in key, "EDT / 15:59 in / 16:00 out"
    assert ("NQH5", "2015-07-15", "09:30") in key and not any(c not in ("ESH5", "ESM5", "NQH5") for c in bars["contract"]) and len(bars) == 4
    assert int(dv[(dv["contract"] == "ESM5")]["volume"].sum()) == 300, "day volume counts the 16:00 bar too"
    print("  ok: 4 RTH bars kept of 7 (08:30 EST, 16:00 EDT and the unmapped instrument dropped); DST both ways; full-day volume 300 for ESM5")
    print("== (b) assemble: front by full-day volume, the roll row, p0930/p1600, bars per session")
    b = pd.DataFrame([dict(root="ES", day=d, hhmm=h, contract=c, open=1.0, high=1.0, low=1.0, close=1.0 + k, volume=1) for d in ("2015-03-12", "2015-03-13") for c in ("ESH5", "ESM5") for k, h in enumerate(("09:30", "12:00", "15:59"))])
    dvx = pd.DataFrame([dict(root="ES", day="2015-03-12", contract="ESH5", volume=900), dict(root="ES", day="2015-03-12", contract="ESM5", volume=100), dict(root="ES", day="2015-03-13", contract="ESH5", volume=400), dict(root="ES", day="2015-03-13", contract="ESM5", volume=600)])
    bars2, sess, rolls = assemble(b, dvx); assert list(sess["contract"]) == ["ESH5", "ESM5"] and len(rolls) == 1 and rolls.iloc[0]["to_contract"] == "ESM5" and rolls.iloc[0]["from_volume"] == 400 and list(sess["bars"]) == [3, 3]
    assert sess.iloc[0]["p0930"] == 1.0 and sess.iloc[0]["p1600"] == 3.0 and bool(sess.iloc[1]["roll"]) and not bool(sess.iloc[0]["roll"]) and len(bars2) == 6 and (bars2[bars2["day"] == "2015-03-13"]["contract"] == "ESM5").all()
    print("  ok: front flips to ESM5 on the higher-volume day, one roll row with both volumes, p0930/p1600 from the 09:30 open and 15:59 close")
    print("== (c) expiry arithmetic: third Fridays; single-digit years resolved by the roll year; ESH5 -> 2015-03-20; ESZ9 rolled in 2019 -> 2019-12-20; NQU0 rolled 2020-09 -> 2020-09-18")
    assert str(third_friday(2015, 3).date()) == "2015-03-20" and str(expiry_of("ESH5", "2015-03-12").date()) == "2015-03-20" and str(expiry_of("ESZ9", "2019-12-13").date()) == "2019-12-20" and str(expiry_of("NQU0", "2020-09-11").date()) == "2020-09-18"
    assert str(expiry_of("ESM0", "2010-06-07").date()) == "2010-06-18" and str(expiry_of("ESH1", "2020-12-11").date()) == "2021-03-19", "year wrap"
    print("== (d) D520: a REUSED instrument_id is labelled from the window holding each bar's own timestamp, and the ambiguity guard fires")
    reuse = pd.DataFrame([wrow(7, "ES", "ESH5", "2015-01-01", "2015-04-01"), wrow(7, "NQ", "NQZ5", "2015-09-01", "2016-01-01")], columns=WCOLS)
    rr = [(ts("2015-02-11 14:30:00+00:00"), 7), (ts("2015-10-14 13:30:00+00:00"), 7), (ts("2015-06-10 13:30:00+00:00"), 7)]   # window A, window B, the gap between them
    ra = np.array([(t, i, 2000 * 1e9, 2001 * 1e9, 1999 * 1e9, 2000.5 * 1e9, 100) for t, i in rr], dtype=arr.dtype)
    lab = label_rows(ra, reuse); got = dict(zip(lab["_i"], zip(lab["root"], lab["contract"])))
    assert got == {0: ("ES", "ESH5"), 1: ("NQ", "NQZ5")}, f"windowed labelling wrong: {got}"
    flat = {int(r.iid): (r.root, r.contract) for r in reuse.itertuples()}                                                     # what a flat dict keeps: the LAST window only
    assert flat[7] == ("NQ", "NQZ5") and got[0] != flat[7], "the check cannot fire -- the flat dict must disagree on row 0"
    b_re, _ = process_chunk(ra, reuse)                                                                                        # both labelled bars are 09:30 ET (EST then EDT); the gap bar is gone
    assert list(b_re["contract"]) == ["ESH5", "NQZ5"] and list(b_re["root"]) == ["ES", "NQ"] and len(b_re) == 2, f"one id, two labels, archive order: {list(b_re['contract'])}"
    bad = pd.DataFrame([wrow(7, "ES", "ESH5", "2015-01-01", "2015-12-01"), wrow(7, "NQ", "NQZ5", "2015-09-01", "2016-01-01")], columns=WCOLS)
    try:
        label_rows(ra, bad); raise SystemExit("[X] the overlap guard did NOT fire on two windows claiming one bar")
    except AssertionError as e:
        assert "MORE THAN ONE" in str(e), e
    print("  ok: id 7 reads ESH5 in February and NQZ5 in October, the gap bar is dropped, the flat dict would have called both NQZ5, and overlapping windows raise")
    print("== (e) D522: G4's halted-open exclusion fires on a hole in 09:30-09:44, and NOT on a full open, an early close or a later halt")
    def sess_bars(day, minutes):
        return pd.DataFrame([dict(day=day, hhmm=m, contract="RTYM0", open=1.0, high=1.0, low=1.0, close=1.0, volume=1) for m in minutes])
    ALLDAY = [f"{h:02d}:{m:02d}" for h in range(9, 16) for m in range(60) if f"{h:02d}:{m:02d}" >= "09:30" and f"{h:02d}:{m:02d}" <= "15:59"]
    halt_open = [m for m in ALLDAY if not ("09:31" <= m <= "09:44")]                 # the 2020-03-16 shape: one print at 09:30, then nothing until 09:45
    halt_late = [m for m in ALLDAY if not ("13:00" <= m <= "13:14")]                 # a halt after the open leaves both legs measuring 09:30->16:00
    early = [m for m in ALLDAY if m <= "12:59"]                                      # a half session: full open, short tail
    no_open = [m for m in ALLDAY if m >= "10:00"]                                    # no open at all
    bb = pd.concat([sess_bars("2020-03-16", halt_open), sess_bars("2020-03-17", ALLDAY),
                    sess_bars("2020-03-18", halt_late), sess_bars("2019-07-03", early), sess_bars("2019-07-05", no_open)], ignore_index=True)
    got = discontinuous_open(bb)
    assert got == {"2020-03-16", "2019-07-05"}, f"halted-open detector wrong: {sorted(got)}"
    assert "2020-03-17" not in got and "2020-03-18" not in got and "2019-07-03" not in got, "a full open, a LATER halt and an early close must all survive"
    full_only = discontinuous_open(sess_bars("2020-03-17", ALLDAY)); assert full_only == set(), "[X] the detector fires on a clean session"
    hole_1min = discontinuous_open(sess_bars("2020-03-17", [m for m in ALLDAY if m != "09:38"])); assert hole_1min == {"2020-03-17"}, "[X] a single missing minute inside the window must be caught"
    print(f"  ok: flags the 09:30-then-nothing session and a session with no open; passes a full open, a 13:00 halt and an early close; one missing minute is enough")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--build", action="store_true"); g.add_argument("--gates", action="store_true"); g.add_argument("--selftest", action="store_true"); g.add_argument("--verify", type=int, metavar="N", help="serial vs pool on the N smallest files, bit-identical")
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.build:
        cmd_build(a.workers)
    elif a.verify:
        cmd_verify(a.verify, a.workers)
    elif a.gates:
        sys.exit(0 if gates() else 1)
    else:
        cmd_selftest()
