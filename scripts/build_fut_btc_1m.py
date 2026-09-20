"""D580 section 0 -- the one-minute CME bitcoin fixture: BTC and MBT outright bars, EVERY session, keyed in UTC,
front month per (root, CME trade date) by measured daily volume, from the CME ohlcv-1m archive. Design committed
in 382ef54 BEFORE this file. Data layer only: no study, no signal, no return.

    python scripts/build_fut_btc_1m.py --verify 3 [--workers 6]  # SYSTEM interpreter (databento): serial vs pool bit-identical on the three smallest files
    python scripts/build_fut_btc_1m.py --build [--workers 6]     # SYSTEM interpreter -> data/fixtures/fut_btc_1m.csv.gz (gitignored by pattern, in the manifest)
    python scripts/build_fut_btc_1m.py --gates                   # G1-G5 -> data/fixtures/fut_btc_1m.meta.json (either interpreter)
    python scripts/build_fut_btc_1m.py --selftest                # synthetic records through the same chunk function

Conventions: ts_event is the bar START (D462); the fixture's `ts_utc` is that start, to the minute, in UTC, because the
funding clock is UTC. CME trade date = the US/Eastern calendar date of (ts_event + 7 h): the crypto session opens 18:00 ET
and closes 17:00 ET the next day, so the evening's bars belong to the next date -- the breadth fixture's own convention
(its `day` runs h18 of the previous calendar day through h16). Front month per (root, trade date) = the outright with the
highest volume over the whole trade date (D448); every fixture bar belongs to that date's front; no stitching, no adjustment.
`ids_of` and `label_rows` are copied from build_fut_index_1m rather than imported because that module's OUTRIGHT is its
own four roots (its docstring says one definition per root list); the WINDOWED labelling is byte-for-byte the same (D520).
"""
from __future__ import annotations
import argparse, json, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"; OUT = FIX / "fut_btc_1m.csv.gz"; META = FIX / "fut_btc_1m.meta.json"
BREADTH = FIX / "fut_breadth_hourly.csv.gz"
ROOTS = ("BTC", "MBT"); OUTRIGHT = re.compile(r"^(BTC|MBT)([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 10_000_000
UNDEF = np.int64(9_223_372_036_854_775_807)
TRADE_DATE_SHIFT_H = 7
G1_MIN_AGREE = 0.98; G3_FULL = 1_200; G4_MED_MAX = 0.001


def ids_of(store):
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
            rows.append((int(sid), m.group(1), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return None
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    if w.duplicated(["iid", "w0"]).any():
        raise AssertionError("[IDS] the same (instrument_id, window start) appears twice")
    return w


def label_rows(a, w, ts_field="ts_event"):
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a[ts_field].astype(np.uint64), "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if j["_i"].duplicated().any():
        raise AssertionError(f"[IDS] {int(j['_i'].duplicated().sum())} bars claimed by MORE THAN ONE mapping window")
    return j


def process_chunk(arr, w):
    """Rows of the two roots' outrights -> (bars, day-volume). Every bar kept; ts_utc to the minute; trade date by the 7-hour shift."""
    if w is None or len(w) == 0:
        return None, None
    j = label_rows(arr, w).sort_values("_i")
    if len(j) == 0:
        return None, None
    idx = j["_i"].to_numpy(); a = arr[idx]
    ts = pd.to_datetime(a["ts_event"], utc=True); root = j["root"].to_numpy(); sym = j["contract"].to_numpy()
    trade_date = (ts.tz_convert("US/Eastern") + pd.Timedelta(hours=TRADE_DATE_SHIFT_H)).strftime("%Y-%m-%d")
    vol = a["volume"].astype(np.int64)
    dv = pd.DataFrame({"root": root, "day": trade_date, "contract": sym, "volume": vol}).groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    bars = pd.DataFrame({"root": root, "day": np.asarray(trade_date), "ts_utc": ts.strftime("%Y-%m-%dT%H:%M"), "contract": sym,
                         "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX, "volume": vol})
    return bars, dv


def assemble(bars, dv):
    """Front month per (root, trade date) by full-date volume; keep the front's bars; one row per (root, ts_utc)."""
    dv = dv.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    front = dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"], sort=True).tail(1).rename(columns={"contract": "front", "volume": "day_volume"})
    bars = bars.merge(front[["root", "day", "front"]], on=["root", "day"], how="inner"); bars = bars[bars["contract"] == bars["front"]].drop(columns="front")
    bars = bars.sort_values(["root", "ts_utc"]).drop_duplicates(["root", "ts_utc"]).reset_index(drop=True)
    return bars, front


def worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B, D = [], []; n_in = n_kept = 0
    for arr in store.to_ndarray(count=CHUNK):
        n_in += len(arr); bars, dv = process_chunk(arr, w)
        if bars is not None:
            n_kept += len(bars); B.append(bars); D.append(dv)
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=n_kept, ids=0 if w is None else int(w["iid"].nunique()), mapping_windows=0 if w is None else int(len(w)),
                secs=round(time.time() - t0, 1), bars=pd.concat(B, ignore_index=True) if B else None, dv=pd.concat(D, ignore_index=True) if D else None)


def collect(files, workers):
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
    print(f"D580 s0 build -- {len(files)} ohlcv-1m files ({sum(f.stat().st_size for f in files)/1e9:.1f} GB), chunks of {CHUNK:,} rows, {workers} workers\n", flush=True)
    res = collect(files, workers); prov = [{k: v for k, v in r.items() if k not in ("bars", "dv")} for r in res]
    for i, p in enumerate(prov, 1):
        print(f"  [{i:2d}/{len(files)}] {p['file'][:40]:<40} {p['rows_in']:>12,} rows -> BTC/MBT rows {p['rows_kept']:>9,}  {p['secs']:>6.1f}s", flush=True)
    sec = sum(p["secs"] for p in prov); wall0 = time.time() - t0
    print(f"[SPEED] sum(item time)/wall = {sec/wall0:.2f}x on {workers} workers ({100*sec/wall0/max(workers,1):.0f}%)", flush=True)
    B = [r["bars"] for r in res if r["bars"] is not None]; D = [r["dv"] for r in res if r["dv"] is not None]
    bars, front = assemble(pd.concat(B, ignore_index=True), pd.concat(D, ignore_index=True)); del B, D, res
    FIX.mkdir(parents=True, exist_ok=True)
    bars.to_csv(OUT, index=False, compression="gzip", float_format="%.2f", encoding="utf-8")
    for root in ROOTS:
        b = bars[bars["root"] == root]; print(f"  {root}: {len(b):,} bars, {b['day'].nunique():,} sessions, {b['ts_utc'].min()} .. {b['ts_utc'].max()}, contracts {b['contract'].nunique()}")
    META.write_text(json.dumps(dict(spec="382ef54", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), sessions="every session; ts_utc = bar start to the minute, UTC",
                                    trade_date=f"US/Eastern calendar date of ts_event + {TRADE_DATE_SHIFT_H} h (the 18:00 ET open belongs to the next date, as the breadth fixture's day does)",
                                    front_rule="highest full-trade-date volume per (root, trade date)", schema_note="ohlcv-1m carries no trade count; the fixture has volume only", gates=None), indent=1), encoding="utf-8")
    print(f"\nwrote {OUT.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min; gates not yet run (--gates)")


def cmd_verify(n, workers):
    t0 = time.time(); files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
    pick = sorted(sorted(files, key=lambda p: p.stat().st_size)[:n], key=lambda p: p.name)
    print(f"verify on {len(pick)} files ({sum(f.stat().st_size for f in pick)/1e9:.2f} GB): {[f.name[10:18] for f in pick]}", flush=True)
    a = collect(pick, 1); b = collect(pick, workers)
    assert [r["file"] for r in a] == [r["file"] for r in b] == [f.name for f in pick], "file order not restored"
    for x, y in zip(a, b):
        assert x["rows_in"] == y["rows_in"] and x["rows_kept"] == y["rows_kept"], x["file"]
    for k in ("bars", "dv"):
        sa = [r[k] for r in a if r[k] is not None]; sb = [r[k] for r in b if r[k] is not None]
        if sa or sb:
            pd.testing.assert_frame_equal(pd.concat(sa, ignore_index=True), pd.concat(sb, ignore_index=True), check_exact=True); print(f"  {k}: {sum(len(s) for s in sa):,} rows identical")
        else:
            print(f"  {k}: no BTC/MBT rows in these files (pre-2017 archive), counts identical")
    print(f"VERIFY PASSED in {(time.time()-t0)/60:.1f} min; per-file secs {[r['secs'] for r in a]}")


def gates(log=print):
    meta = json.loads(META.read_text(encoding="utf-8")); b = pd.read_csv(OUT, dtype={"day": str, "ts_utc": str, "contract": str, "root": str}, encoding="utf-8"); out = {}; ok = True
    # G2 no zero / UNDEF price
    px = b[["open", "high", "low", "close"]].to_numpy(float); bad = int(((px <= 0) | (px >= UNDEF * PX * 0.5)).any(axis=1).sum())
    out["G2"] = dict(bars_with_zero_or_undef_price=bad, passes=bool(bad == 0)); ok &= out["G2"]["passes"]
    # G1 front contract agrees with the breadth fixture's on common sessions (BTC)
    brf = pd.read_csv(BREADTH, usecols=["root", "day", "contract", "bars"], dtype={"root": str, "day": str, "contract": str}, encoding="utf-8"); brf = brf[brf["root"] == "BTC"]
    # the breadth fixture carries a row for every calendar day including Sundays and holidays with ZERO bars (its day = h18 of the
    # previous evening through h16, the same session convention as here); a session exists in it only where bars > 0
    br = brf[brf["bars"] > 0].set_index("day")["contract"]
    f = b[b["root"] == "BTC"].groupby("day")["contract"].first(); common = f.index.intersection(br.index); agree = float((f.loc[common] == br.loc[common]).mean()) if len(common) else float("nan")
    dis = [(d, f.loc[d], br.loc[d]) for d in common if f.loc[d] != br.loc[d]]
    out["G1"] = dict(common_sessions=int(len(common)), agreement=agree, disagreements=dis[:40], n_disagreements=len(dis), passes=bool(len(common) > 1000 and agree >= G1_MIN_AGREE)); ok &= out["G1"]["passes"]
    # G3 bars per session, by weekday of the trade date
    for root in ROOTS:
        s = b[b["root"] == root].groupby("day").size(); wd = pd.to_datetime(s.index).dayofweek
        out[f"G3_{root}"] = dict(n_sessions=int(len(s)), p50_bars=float(s.median()), share_full=float((s >= G3_FULL).mean()), p50_by_weekday={int(k): float(v) for k, v in s.groupby(wd).median().items()},
                                 first=str(s.index.min()), last=str(s.index.max()), sessions_under_600=[(d, int(n)) for d, n in s[s < 600].items()][:40])
    # G4 MBT close within 0.1 % of BTC's at common minutes
    j = b[b["root"] == "BTC"].set_index("ts_utc")["close"].to_frame("btc").join(b[b["root"] == "MBT"].set_index("ts_utc")["close"].to_frame("mbt"), how="inner"); rel = (j["mbt"] / j["btc"] - 1).abs()
    out["G4"] = dict(common_minutes=int(len(j)), median_abs_rel_diff=float(rel.median()) if len(j) else None, p99_abs_rel_diff=float(rel.quantile(0.99)) if len(j) else None, passes=bool(len(j) > 100_000 and rel.median() < G4_MED_MAX)); ok &= out["G4"]["passes"]
    # G5 sessions absent against the breadth fixture's BTC calendar
    absent = sorted(set(br.index) - set(f.index)); extra = sorted(set(f.index) - set(br.index))
    out["G5"] = dict(breadth_sessions_with_bars_absent_here=absent[:60], n_absent=len(absent), sessions_here_not_in_breadth=extra[:20], n_extra=len(extra), breadth_rows_with_zero_bars=int((brf["bars"] == 0).sum()), passes=bool(len(absent) <= 30)); ok &= out["G5"]["passes"]
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok); META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"G1 front agreement with breadth on {out['G1']['common_sessions']} sessions: {agree:.4f} ({len(dis)} disagree) {'PASS' if out['G1']['passes'] else 'FAIL'}")
    log(f"G2 zero/UNDEF prices: {bad} {'PASS' if out['G2']['passes'] else 'FAIL'}")
    for root in ROOTS:
        g = out[f"G3_{root}"]; log(f"G3 {root}: {g['n_sessions']} sessions {g['first']}..{g['last']}, p50 bars {g['p50_bars']:.0f}, share >= {G3_FULL}: {g['share_full']:.3f}, p50 by weekday {g['p50_by_weekday']}")
    log(f"G4 MBT vs BTC on {out['G4']['common_minutes']:,} common minutes: median |rel| {out['G4']['median_abs_rel_diff']} p99 {out['G4']['p99_abs_rel_diff']} {'PASS' if out['G4']['passes'] else 'FAIL'}")
    log(f"G5 breadth sessions absent here: {len(absent)} {absent[:8]}; here-not-breadth {len(extra)} {'PASS' if out['G5']['passes'] else 'FAIL'}")
    log(f"ALL GATES {'PASS' if ok else 'FAIL'}; wrote {META.relative_to(REPO)}"); return ok


def cmd_selftest():
    def wrow(iid, root, contract, s, e):
        return (iid, root, contract, np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value))
    W = pd.DataFrame([wrow(1, "BTC", "BTCF8", "2017-12-01", "2018-02-01"), wrow(2, "BTC", "BTCG8", "2017-12-01", "2018-03-01"), wrow(3, "MBT", "MBTF8", "2017-12-01", "2018-02-01"), wrow(9, "ES", "ESH8", "2017-12-01", "2018-03-01")], columns=["iid", "root", "contract", "w0", "w1"])
    W = W[W["root"].isin(ROOTS)]
    def ts(s):
        return np.uint64(pd.Timestamp(s, tz="UTC").value)
    dt = np.dtype([("ts_event", "u8"), ("instrument_id", "u4"), ("open", "i8"), ("high", "i8"), ("low", "i8"), ("close", "i8"), ("volume", "u8")])
    P = int(1e13)  # $10,000 in 1e-9 units
    arr = np.array([(ts("2018-01-10T23:30:00Z"), 1, P, P, P, P, 5),    # 18:30 ET Jan 10 -> trade date 2018-01-11
                    (ts("2018-01-11T00:00:00Z"), 1, P, P, P, P, 5),    # 19:00 ET Jan 10 -> 2018-01-11
                    (ts("2018-01-11T21:59:00Z"), 1, P, P, P, P, 5),    # 16:59 ET Jan 11 -> 2018-01-11
                    (ts("2018-01-11T20:00:00Z"), 2, P, P, P, P, 100),  # BTCG8 outvolumes BTCF8 on 2018-01-11
                    (ts("2018-01-11T20:00:00Z"), 3, P, P, P, P, 1),    # MBT
                    (ts("2018-01-11T20:00:00Z"), 9, P, P, P, P, 1)], dtype=dt)   # ES: not ours
    bars, dv = process_chunk(arr, W)
    assert set(bars["day"]) == {"2018-01-11"} and len(bars) == 5 and "ESH8" not in set(bars["contract"]), bars
    assert list(bars["ts_utc"][:3]) == ["2018-01-10T23:30", "2018-01-11T00:00", "2018-01-11T21:59"], list(bars["ts_utc"])
    b2, front = assemble(bars, dv)
    assert set(b2[b2["root"] == "BTC"]["contract"]) == {"BTCG8"} and len(b2) == 2, "front by volume: BTCG8 (100) beats BTCF8 (15)"
    assert float(b2["close"].iloc[0]) == 10_000.0
    # a summer bar: 18:00 EDT = 22:00 UTC belongs to the next trade date
    arr2 = np.array([(ts("2018-07-10T22:00:00Z"), 1, P, P, P, P, 1)], dtype=dt); W2 = pd.DataFrame([wrow(1, "BTC", "BTCN8", "2018-07-01", "2018-08-01")], columns=W.columns)
    b3, _ = process_chunk(arr2, W2); assert list(b3["day"]) == ["2018-07-11"], list(b3["day"])
    # the windowed labelling: one id, two contracts by date
    W3 = pd.DataFrame([wrow(7, "BTC", "BTCF8", "2017-12-01", "2018-02-01"), wrow(7, "BTC", "BTCZ8", "2018-11-01", "2019-01-01")], columns=W.columns)
    arr3 = np.array([(ts("2018-01-05T12:00:00Z"), 7, P, P, P, P, 1), (ts("2018-12-05T12:00:00Z"), 7, P, P, P, P, 1)], dtype=dt)
    b4, _ = process_chunk(arr3, W3); assert list(b4["contract"]) == ["BTCF8", "BTCZ8"], list(b4["contract"])
    print("selftest: trade-date shift (winter and summer), front by volume, foreign roots dropped, windowed id labelling -- all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build", action="store_true"); g.add_argument("--gates", action="store_true"); g.add_argument("--selftest", action="store_true"); g.add_argument("--verify", type=int, metavar="N")
    ap.add_argument("--workers", type=int, default=6); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.verify:
        cmd_verify(a.verify, a.workers)
    elif a.build:
        cmd_build(a.workers)
    else:
        sys.exit(0 if gates() else 1)
