"""D485 -- the micro-flow fixture: signed 5-minute order flow of ES/MES and NQ/MNQ from the CME tbbo tape (exchange aggressor side),
front month per session by E-mini full-session volume. Spec committed in 0651bb9 BEFORE this file. Data layer only: no study.

    python scripts/build_fut_micro_flow.py --probe            # one file, one chunk: timing, RSS, T1 on the probe (measure the worker first)
    python scripts/build_fut_micro_flow.py --build [--workers N]   # tbbo + ohlcv-1m over processes -> data/fixtures/fut_micro_flow_5m.csv.gz (+meta)
    python scripts/build_fut_micro_flow.py --gates            # T1..T5 -> meta; raises on a failed gate
    python scripts/build_fut_micro_flow.py --selftest         # synthetic trades through the aggregation; [X] a flipped aggressor sign must fail T1

Conventions: bucket_start is the 5-minute bucket START in US/Eastern (DST-aware); a bucket holds trades with ts_event in [start, start+5m).
Session = 18:00 ET day a .. 16:59 ET day b, labelled by day b. Front month per (root, session) = the E-mini contract with the highest
session volume; the micro carries the same month code. Signing = the tape's aggressor side (B buy, A sell, N unsigned).
"""
from __future__ import annotations
import argparse, json, os, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"
OUT = FIX / "fut_micro_flow_5m.csv.gz"; META = FIX / "fut_micro_flow_5m.meta.json"; ROLLS = FIX / "fut_micro_flow_rolls.csv.gz"
TBBO_DIR = RAW / "GLBX-20260911-6DA3JPNQE3"
PAIRS = {"ES": "MES", "NQ": "MNQ"}; MICRO = {v: k for k, v in PAIRS.items()}; ROOTS = ("ES", "MES", "NQ", "MNQ")
OUTRIGHT = re.compile(r"^(ES|MES|NQ|MNQ)([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 5_000_000; BUCKET_MIN = 5
SPAN = ("2025-09-11", "2026-09-10"); RTH = (9 * 60 + 30, 16 * 60)  # minutes since midnight ET, [start, end)
T1_MIN = 0.99; T2_TOL = 0.005; T3_MIN = 70; T3_OF = 78


def rss_mb():
    try:
        import ctypes, ctypes.wintypes as w
        class PMC(ctypes.Structure):
            _fields_ = [("cb", w.DWORD), ("PageFaultCount", w.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t), ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t), ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        p = PMC(); p.cb = ctypes.sizeof(PMC)
        import subprocess  # tasklist: current working set in KB (the ctypes struct read back 0.07 MB -- misaligned; not trusted)
        out = subprocess.run(["tasklist", "/FI", f"PID eq {os.getpid()}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        return float(out.strip().rsplit('","', 1)[-1].strip('"').replace(" K", "").replace(",", "")) / 1e3
    except Exception:
        return float("nan")


def ids_of(store):
    """Symbol mappings as (iid, root, contract, w0, w1) WINDOWS -- never a flat {id: symbol} dict.

    D520. A flat dict keeps only the LAST mapping written for an id and discards the validity dates,
    so one id carries one label for all time. The archive breaks that two ways: CME reuses the
    single-digit-year slot the moment a contract expires, and a live contract can be rotated to a new
    id mid-year. Across the ohlcv archive that dict ingested 229,206 bars of the WRONG INSTRUMENT.

    **Deliberately not imported from `build_fut_breadth_hourly`**, unlike `build_fut_day5m` and
    `build_fut_open_interest`, because that builder's ROOTS list has no MES or MNQ: importing its
    `ids_of` here would silently drop every micro contract, which is half of this fixture's purpose.
    One definition per root list, not one per repo.
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
    """Attach the contract from the mapping window CONTAINING each record's own timestamp.

    Returns the joined frame carrying `_i`, the positional index back into `a`. The guard is on `_i`
    rather than on (iid, ts): a tbbo file can legitimately carry several trades for one instrument at
    one nanosecond, so an (iid, ts) guard would fire on correct data, while a repeated `_i` means one
    record was claimed by two windows, which is the real ambiguity.
    """
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32),
                        "ts": a[ts_field].astype(np.uint64),
                        "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    if j["_i"].duplicated().any():
        raise AssertionError(f"[IDS] {int(j['_i'].duplicated().sum())} records claimed by MORE THAN ONE mapping window")
    return j


# ------------------------------------------------------------------------------------------ the aggregation (pure; self-tested)
def bucket_trades(ts_ns, contract, price, size, side, bid, ask):
    """Trades -> one row per (contract, bucket_start ET). ts_ns int64 UTC ns; contract str array; price/bid/ask int64 (1e-9); size uint; side bytes."""
    ts = pd.to_datetime(ts_ns, utc=True).tz_convert("US/Eastern")
    bstart = ts.floor(f"{BUCKET_MIN}min")
    side = np.asarray(side).astype("S1"); is_b = side == b"B"; is_a = side == b"A"; is_n = ~(is_b | is_a)
    at_bid = price == bid; at_ask = price == ask
    df = pd.DataFrame({"contract": contract, "bucket_start": bstart.tz_localize(None), "ts": ts_ns, "px": price * PX, "size": size.astype(np.int64),
                       "buy": np.where(is_b, size, 0).astype(np.int64), "sell": np.where(is_a, size, 0).astype(np.int64), "uns": np.where(is_n, size, 0).astype(np.int64),
                       "lot1": np.where(size == 1, size, 0).astype(np.int64), "lot_le2": np.where(size <= 2, size, 0).astype(np.int64),
                       "at_bid": at_bid.astype(np.int64), "at_ask": at_ask.astype(np.int64),
                       "agree": ((at_bid & is_a) | (at_ask & is_b)).astype(np.int64)})
    df["pxsz"] = df["px"] * df["size"]
    g = df.groupby(["contract", "bucket_start"], sort=False)
    out = g.agg(n=("size", "size"), vol=("size", "sum"), buy=("buy", "sum"), sell=("sell", "sum"), uns=("uns", "sum"), lot1=("lot1", "sum"), lot_le2=("lot_le2", "sum"),
                pxsz=("pxsz", "sum"), at_bid=("at_bid", "sum"), at_ask=("at_ask", "sum"), agree=("agree", "sum"), first_ts=("ts", "min"), last_ts=("ts", "max"),
                hi=("px", "max"), lo=("px", "min")).reset_index()
    idx_first = g["ts"].idxmin().to_numpy(); idx_last = g["ts"].idxmax().to_numpy()
    out["first_px"] = df["px"].to_numpy()[idx_first]; out["last_px"] = df["px"].to_numpy()[idx_last]
    return out


def reaggregate(parts):
    """Exact re-aggregation of partial bucket rows (chunks may split a bucket)."""
    df = pd.concat(parts, ignore_index=True)
    sums = ["n", "vol", "buy", "sell", "uns", "lot1", "lot_le2", "pxsz", "at_bid", "at_ask", "agree"]
    g = df.groupby(["contract", "bucket_start"], sort=True)
    out = g[sums].sum(); out["hi"] = g["hi"].max(); out["lo"] = g["lo"].min(); out["first_ts"] = g["first_ts"].min(); out["last_ts"] = g["last_ts"].max()
    fi = df.loc[g["first_ts"].idxmin(), ["contract", "bucket_start", "first_px"]].set_index(["contract", "bucket_start"])
    la = df.loc[g["last_ts"].idxmax(), ["contract", "bucket_start", "last_px"]].set_index(["contract", "bucket_start"])
    out["first_px"] = fi["first_px"]; out["last_px"] = la["last_px"]
    return out.reset_index()


def worker_tbbo(path, chunk=CHUNK, max_chunks=None):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store)
    if w is None:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=None)
    keys = w["iid"].to_numpy(np.uint32)
    parts = []; n_in = n_kept = 0
    for k, arr in enumerate(store.to_ndarray(count=chunk)):
        n_in += len(arr); sel = np.isin(arr["instrument_id"], keys); a = arr[sel]
        if a.size:
            j = label_rows(a, w)
            if len(j):
                i = j["_i"].to_numpy(); n_kept += len(i); contract = j["contract"].to_numpy()
                parts.append(bucket_trades(a["ts_event"][i].astype(np.int64), contract, a["price"][i].astype(np.int64), a["size"][i], a["side"][i], a["bid_px_00"][i].astype(np.int64), a["ask_px_00"][i].astype(np.int64)))
        if max_chunks and k + 1 >= max_chunks:
            break
    out = reaggregate(parts) if parts else None
    return dict(file=Path(path).name, rows_in=n_in, rows_kept=n_kept, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=out)


def worker_ohlcv(path):
    """(contract, ET minute) volume for the four roots -> per (contract, bucket_start) volume, for gate T2."""
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store)
    if w is None:
        return dict(file=Path(path).name, rows_in=0, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=None)
    keys = w["iid"].to_numpy(np.uint32); parts = []; n_in = 0
    for arr in store.to_ndarray(count=10_000_000):
        n_in += len(arr); sel = np.isin(arr["instrument_id"], keys); a = arr[sel]
        if a.size:
            j = label_rows(a, w)
            if len(j):
                i = j["_i"].to_numpy()
                ts = pd.to_datetime(a["ts_event"][i].astype(np.int64), utc=True).tz_convert("US/Eastern")
                df = pd.DataFrame({"contract": j["contract"].to_numpy(), "bucket_start": ts.floor(f"{BUCKET_MIN}min").tz_localize(None), "vol1m": a["volume"][i].astype(np.int64)})
                parts.append(df.groupby(["contract", "bucket_start"], sort=False)["vol1m"].sum().reset_index())
    out = pd.concat(parts).groupby(["contract", "bucket_start"], sort=True)["vol1m"].sum().reset_index() if parts else None
    return dict(file=Path(path).name, rows_in=n_in, secs=round(time.time() - t0, 1), rss_mb=round(rss_mb(), 0), table=out)


# ------------------------------------------------------------------------------------------ assembly
def session_of(bucket_start):
    """Session label (day b) for a bucket start in ET: >= 18:00 -> next calendar day; else same day."""
    bs = pd.DatetimeIndex(bucket_start); d = bs.normalize(); return (d + pd.Timedelta(days=1)).where(bs.hour >= 18, d)


def assemble(T, V):
    T = T.copy(); T["root"] = T["contract"].str.extract(OUTRIGHT.pattern)[0]; T["month"] = T["contract"].str[len(T["root"].iloc[0]):] if False else T["contract"].str.replace(OUTRIGHT, lambda m: m.group(2) + m.group(3), regex=True)
    T["session"] = session_of(T["bucket_start"]); T["cls"] = np.where(T["root"].isin(list(PAIRS)), "mini", "micro"); T["pair"] = T["root"].map(lambda r: r if r in PAIRS else MICRO[r])
    T = T[(T["session"] >= pd.Timestamp(SPAN[0])) & (T["session"] <= pd.Timestamp(SPAN[1]))]
    # front per (pair, session) from the mini's session volume
    mv = T[T["cls"] == "mini"].groupby(["pair", "session", "month"])["vol"].sum().reset_index()
    front = mv.sort_values(["pair", "session", "vol"], ascending=[True, True, False]).drop_duplicates(["pair", "session"])[["pair", "session", "month", "vol"]].rename(columns={"month": "front", "vol": "front_vol"})
    front = front.sort_values(["pair", "session"]); front["front_prev"] = front.groupby("pair")["front"].shift(); front["same_front"] = (front["front"] == front["front_prev"]) | front["front_prev"].isna()
    T = T.merge(front[["pair", "session", "front"]], on=["pair", "session"], how="inner"); T = T[T["month"] == T["front"]].drop(columns=["front"])
    if V is not None:
        T = T.merge(V, on=["contract", "bucket_start"], how="left")
    T["minute"] = T["bucket_start"].dt.hour * 60 + T["bucket_start"].dt.minute; T["rth"] = (T["minute"] >= RTH[0]) & (T["minute"] < RTH[1])
    T["vwap"] = T["pxsz"] / T["vol"]
    cols = ["pair", "cls", "root", "contract", "session", "bucket_start", "minute", "rth", "n", "vol", "buy", "sell", "uns", "lot1", "lot_le2", "vwap", "first_px", "last_px", "hi", "lo", "at_bid", "at_ask", "agree"] + (["vol1m"] if V is not None else [])
    T = T[cols].sort_values(["pair", "cls", "session", "bucket_start"]).reset_index(drop=True); T["session"] = T["session"].dt.strftime("%Y-%m-%d")
    return T, front


def cmd_build(workers):
    from multiprocessing import Pool
    t0 = time.time(); tb = sorted(TBBO_DIR.glob("*.tbbo.dbn.zst")); assert len(tb) == 13, f"expected 13 tbbo files, found {len(tb)}"
    oh = [f for f in sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst")) if f.name[10:18] >= "20250904"]; print(f"D485 build -- {len(tb)} tbbo files ({sum(f.stat().st_size for f in tb)/1e9:.1f} GB), {len(oh)} ohlcv-1m files, {workers} workers", flush=True)
    jobs = [("tbbo", str(f)) for f in sorted(tb, key=lambda p: -p.stat().st_size)] + [("ohlcv", str(f)) for f in oh]
    with Pool(workers) as pool:
        res = pool.map(_dispatch, jobs, chunksize=1)
    prov = [{k: v for k, v in r.items() if k != "table"} for r in res]
    for p in prov:
        print(f"  {p['file'][:44]:<44} rows_in {p['rows_in']:>13,}  kept {p.get('rows_kept', ''):>11}  {p['secs']:>7.1f}s  peakRSS {p['rss_mb']:.0f} MB", flush=True)
    T = reaggregate([r["table"] for r, j in zip(res, jobs) if j[0] == "tbbo" and r["table"] is not None])
    V = pd.concat([r["table"] for r, j in zip(res, jobs) if j[0] == "ohlcv" and r["table"] is not None]).groupby(["contract", "bucket_start"], sort=True)["vol1m"].sum().reset_index()
    T, front = assemble(T, V); FIX.mkdir(parents=True, exist_ok=True)
    T.to_csv(OUT, index=False, compression="gzip", float_format="%.4f"); front.to_csv(ROLLS, index=False, compression="gzip")
    sec = sum(p["secs"] for p in prov); wall = time.time() - t0; print(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%)", flush=True)
    for pair in PAIRS:
        for cls in ("mini", "micro"):
            b = T[(T["pair"] == pair) & (T["cls"] == cls)]; print(f"  {pair}/{cls}: {len(b):,} bucket rows, {b['session'].nunique()} sessions, {b['session'].min()} .. {b['session'].max()}, contracts {b['contract'].nunique()}")
    META.write_text(json.dumps(dict(spec="0651bb9", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), files=prov, roots=list(ROOTS), span=SPAN, bucket_min=BUCKET_MIN, session=["18:00", "16:59"],
                                    front_rule="E-mini contract with the highest session volume; micro carries the same month", signing="tape aggressor side: B buy, A sell, N unsigned", wall_min=round(wall / 60, 1), gates=None), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)} ({len(T):,} rows) in {wall/60:.1f} min; gates not yet run", flush=True)


def _dispatch(job):
    kind, path = job
    try:
        return worker_tbbo(path) if kind == "tbbo" else worker_ohlcv(path)
    except Exception as e:  # surface, never hang
        (REPO / "temp").mkdir(exist_ok=True); (REPO / "temp" / "d485_worker.err").open("a").write(f"{path}: {e!r}\n"); raise


def cmd_probe():
    f = sorted(TBBO_DIR.glob("*.tbbo.dbn.zst"))[-1]; print(f"probe: {f.name}, 2 chunks of {CHUNK:,}", flush=True)
    r = worker_tbbo(str(f), max_chunks=2); T = r["table"]; print({k: v for k, v in r.items() if k != "table"})
    T["root"] = T["contract"].str.extract(OUTRIGHT.pattern)[0]
    for root in ROOTS:
        b = T[T["root"] == root]; ab = b["at_bid"].sum() + b["at_ask"].sum(); print(f"  {root}: buckets {len(b):,} vol {b['vol'].sum():,} lot1 {b['lot1'].sum()/max(b['vol'].sum(),1):.2%} T1 agree {b['agree'].sum()/max(ab,1):.4f} (of {ab:,} at-quote trades)")
    print(f"rate: {r['rows_in']/r['secs']:,.0f} rows/s -> 13 files at ~{13*3e8:,.0f} rows projected {13*3e8/(r['rows_in']/r['secs'])/60:.0f} min single-process")


# ------------------------------------------------------------------------------------------ gates
def load_table():
    T = pd.read_csv(OUT, dtype={"pair": str, "cls": str, "root": str, "contract": str, "session": str}); T["bucket_start"] = pd.to_datetime(T["bucket_start"]); return T


def cmd_gates(log=print):
    T = load_table(); meta = json.loads(META.read_text()); g = {}
    # T1 sign agreement per class per month
    T["ym"] = T["bucket_start"].dt.strftime("%Y-%m"); a = T.groupby(["cls", "ym"])[["agree", "at_bid", "at_ask"]].sum(); a["rate"] = a["agree"] / (a["at_bid"] + a["at_ask"])
    g["T1"] = dict(min_rate=float(a["rate"].min()), threshold=T1_MIN, by={f"{c}/{m}": float(v) for (c, m), v in a["rate"].round(5).items()}); log(f"[T1] sign agreement min {a['rate'].min():.5f} (>= {T1_MIN})"); assert a["rate"].min() >= T1_MIN, "T1"
    # T2 cross-schema session volume
    # the invariant: the two schemas must agree wherever BOTH cover the session; a session the ohlcv-1m pull does not fully cover
    # (its span ends 2026-09-09 UTC, so session 2026-09-10's day leg has no bars) is excluded and LISTED, never compared
    cov = T.groupby(["contract", "session"])["vol1m"].apply(lambda x: x.notna().all()); s = T.groupby(["contract", "session"])[["vol", "vol1m"]].sum(); s = s[cov & (s["vol1m"] > 0)]; s["rel"] = (s["vol"] - s["vol1m"]).abs() / s["vol1m"]
    bad = s[s["rel"] > T2_TOL]; uncovered = cov[~cov].reset_index()[["contract", "session"]].astype(str).to_dict("records")
    g["T2"] = dict(sessions=int(len(s)), max_rel=float(s["rel"].max()), n_bad=int(len(bad)), tol=T2_TOL, worst=bad.sort_values("rel", ascending=False).head(10).reset_index().astype(str).to_dict("records"), not_covered_by_ohlcv=uncovered)
    log(f"[T2] tbbo vs ohlcv-1m session volume: {len(s):,} fully-covered contract-sessions, max rel diff {s['rel'].max():.5f}, {len(bad)} beyond {T2_TOL}; {len(uncovered)} contract-sessions not covered by the ohlcv-1m span (listed)"); assert len(bad) == 0, "T2"
    # T3 presence
    r = T[T["rth"]].groupby(["pair", "session", "cls"]).size().unstack("cls").fillna(0); present = (r["mini"] >= T3_MIN) & (r["micro"] >= T3_MIN)
    absent = r[~present].reset_index()[["pair", "session", "mini", "micro"]]; g["T3"] = dict(sessions=int(len(r)), present=int(present.sum()), absent=absent.astype(str).to_dict("records")); log(f"[T3] {int(present.sum())}/{len(r)} pair-sessions present (>= {T3_MIN} of {T3_OF} RTH buckets both classes); absent listed: {len(absent)}")
    # T5 scale
    v = T[T["rth"]].groupby(["pair", "session", "cls"])["vol"].sum().unstack("cls"); ratio = (v["micro"] / v["mini"]); g["T5"] = {p: dict(p10=float(ratio.xs(p).quantile(.1)), p50=float(ratio.xs(p).median()), p90=float(ratio.xs(p).quantile(.9))) for p in PAIRS}
    for p in PAIRS:
        log(f"[T5] {p}: micro/mini RTH volume p10/p50/p90 = {g['T5'][p]['p10']:.3f} / {g['T5'][p]['p50']:.3f} / {g['T5'][p]['p90']:.3f}")
    meta["gates"] = g; meta["gated_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()); META.write_text(json.dumps(meta, indent=1)); log("gates written to meta")


# ------------------------------------------------------------------------------------------ self-test
def cmd_selftest():
    rng = np.random.default_rng(0); n = 5000
    base = pd.Timestamp("2026-03-03 09:30", tz="US/Eastern").tz_convert("UTC").value
    ts = base + np.sort(rng.integers(0, 60 * 60 * 1e9, n)).astype(np.int64); contract = np.where(rng.random(n) < 0.5, "ESH6", "MESH6")
    bid = (5000 * 4 + rng.integers(-40, 40, n)) * 25 * 10**7; ask = bid + 25 * 10**7; is_b = rng.random(n) < 0.5
    price = np.where(is_b, ask, bid); side = np.where(is_b, b"B", b"A"); size = rng.integers(1, 6, n).astype(np.uint32)
    T = bucket_trades(ts, contract, price, size, side, bid, ask)
    assert T["vol"].sum() == size.sum() and T["buy"].sum() == size[is_b].sum() and T["sell"].sum() == size[~is_b].sum(), "sums"
    assert (T["agree"] == T["at_bid"] + T["at_ask"]).all(), "T1 must be 100% on consistent synthetic trades"
    # [T4] no-future: rebuild one bucket directly from trades with ts < end
    row = T.iloc[3]; bs = pd.Timestamp(row["bucket_start"]).tz_localize("US/Eastern"); lo, hi = bs.tz_convert("UTC").value, (bs + pd.Timedelta(minutes=BUCKET_MIN)).tz_convert("UTC").value
    m = (ts >= lo) & (ts < hi) & (contract == row["contract"]); assert size[m].sum() == row["vol"] and size[m & is_b].sum() == row["buy"], "T4 direct rebuild"
    assert abs((price[m] * PX * size[m]).sum() / size[m].sum() - row["pxsz"] / row["vol"]) < 1e-9, "vwap"
    # chunk split == whole
    k = n // 2; A = reaggregate([bucket_trades(ts[:k], contract[:k], price[:k], size[:k], side[:k], bid[:k], ask[:k]), bucket_trades(ts[k:], contract[k:], price[k:], size[k:], side[k:], bid[k:], ask[k:])])
    W = reaggregate([T]); pd.testing.assert_frame_equal(A, W, check_like=True); print("[V] chunk split == whole, bit-identical")
    # [X] a flipped aggressor sign must fail T1
    Tx = bucket_trades(ts, contract, price, size, np.where(is_b, b"A", b"B"), bid, ask); assert Tx["agree"].sum() == 0, "[X] flipped sign should give zero agreement"
    print("[X] flipped aggressor sign -> agreement 0.0000 (T1 would fail)")
    # session labelling
    s = session_of(pd.to_datetime(["2026-03-03 17:55", "2026-03-03 18:00", "2026-03-06 18:00", "2026-03-04 00:05"])); assert [x.strftime("%Y-%m-%d") for x in s] == ["2026-03-03", "2026-03-04", "2026-03-07", "2026-03-04"], "session_of"
    print("selftest OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--probe", action="store_true"); ap.add_argument("--build", action="store_true"); ap.add_argument("--gates", action="store_true"); ap.add_argument("--selftest", action="store_true"); ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.probe:
        cmd_probe()
    if a.build:
        cmd_build(a.workers)
    if a.gates:
        cmd_gates()
