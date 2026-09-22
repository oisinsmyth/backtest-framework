"""D581 section 0 -- the ES option end-of-day fixture: per (usable session, option) the prior-close open interest and
settlement, the strike/expiry/right from `definition`, and for same-day-expiring options the minute-bar volume to 15:30 ET
from the archive already on disk. Design committed in the D581 commit BEFORE this file. Data layer only: no gamma, no
signal, no return.

    python scripts/build_fut_es_options_eod.py --defs  [--workers 6]   # SYSTEM interpreter: definition files -> the option table (cached)
    python scripts/build_fut_es_options_eod.py --stats [--workers 6]   # statistics files -> OI and settlement publications (cached per file)
    python scripts/build_fut_es_options_eod.py --bars  [--workers 6]   # ohlcv-1m files -> 0DTE volume to 15:30 ET per (session, option) (cached per file)
    python scripts/build_fut_es_options_eod.py --build                 # caches -> data/fixtures/fut_es_options_eod.csv.gz + meta
    python scripts/build_fut_es_options_eod.py --gates                 # G1-G7 -> meta (either interpreter)
    python scripts/build_fut_es_options_eod.py --selftest

Conventions. `stat_type` 9 = open interest in `quantity`; 3 = settlement in `price` (1e-9 units); UNDEF filtered on both, and
a settlement of exactly 0.0 is D526's second sentinel and is dropped. A publication is USABLE on the first ES session whose
10:00 ET entry is strictly after its ts_event (D497/D521's rule, imported): the OI published ~21:00 ET on T-1 describes
T-1's close and is usable on session T. Option ids are labelled from the same YEAR's definition file (both pulls split by
year) by (instrument_id, raw_symbol); the option families are ES (quarterly), EW (end of month), EW1-EW4 (Fridays),
E1A-E5A / E1B-E5B / E1C-E5C / E1D-E5D (Monday .. Thursday dailies). The ES session calendar is D462's session table.
"""
from __future__ import annotations
import argparse, importlib.util, json, pickle, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
RAW = REPO / "data" / "raw" / "databento"; FIX = REPO / "data" / "fixtures"; TEMP = REPO / "temp" / "es_options_eod"
OUT = FIX / "fut_es_options_eod.csv.gz"; META = FIX / "fut_es_options_eod.meta.json"; JOBS = REPO / "data" / "es_options_pull_jobs.json"
SESSIONS = FIX / "fut_index_sessions.csv.gz"
OPTION = re.compile(r"^(ES|EW|EW[1-4]|E[1-5][A-D])([FGHJKMNQUVXZ])(\d{1,2}) ([CP])(\d+)$")
ST_OI, ST_SETTLE = 9, 3; UNDEF = np.iinfo(np.int64).max; PX = 1e-9; CHUNK = 5_000_000; CUTOFF_HHMM = "15:30"
G3_MIN_STRIKES = 20; G6_MONEYNESS = 0.05


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


JOBS_ALL = (REPO / "data" / "es_options_pull_jobs.json", REPO / "data" / "es_options_pull_jobs_weeklies.json")   # the quarterly pull and the weekly/daily families' pull


def job_dirs():
    """Every job directory per schema across both pulls (ES.OPT resolved to the quarterly family alone; the weeklies came in a second pull)."""
    out = {"statistics": [], "definition": []}
    for f in JOBS_ALL:
        if f.exists():
            for j in json.loads(f.read_text(encoding="utf-8"))["jobs"]:
                out[j["schema"]].append(RAW / j["job"]["id"])
    return out


def year_of(path):
    m = re.search(r"glbx-mdp3-(\d{4})", path.name); return int(m.group(1))


def cache_name(kind, path):
    return f"{kind}_{path.parent.name[-10:]}_{year_of(path)}.pkl"


def load_cached(kind, year=None):
    frames = []
    for p in sorted(TEMP.glob(f"{kind}_*.pkl")):
        y = int(p.stem.split("_")[-1])
        if year is None or y == year:
            frames.append(pickle.loads(p.read_bytes()).assign(year=y))
    return pd.concat(frames, ignore_index=True) if frames else None


def es_calendar():
    s = pd.read_csv(SESSIONS, dtype={"day": str, "contract": str, "root": str}, encoding="utf-8"); s = s[(s["root"] == "ES") & (s["bars"] >= 380)]
    return np.array(sorted(s["day"].unique()))


# ------------------------------------------------------------------------------------------ --defs
def defs_worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); rows = []; n = 0
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr); cls = arr["instrument_class"]; m = (cls == b"C") | (cls == b"P")
        if not m.any():
            continue
        a = arr[m]; sym = np.char.decode(a["raw_symbol"].astype("S"), "ascii"); keep = np.array([bool(OPTION.match(s)) for s in sym])
        if not keep.any():
            continue
        a = a[keep]; sym = sym[keep]
        rows.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "raw_symbol": sym, "right": np.char.decode(a["instrument_class"].astype("S"), "ascii"),
                                  "strike": a["strike_price"].astype(np.int64) * PX, "expiration_ns": a["expiration"].astype(np.int64), "underlying": np.char.decode(a["underlying"].astype("S"), "ascii").astype(str),
                                  "ts_recv": a["ts_recv"].astype(np.int64)}))
    d = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["iid", "raw_symbol", "right", "strike", "expiration_ns", "underlying", "ts_recv"])
    # a definition record is republished every session; keep, per (id, symbol), the FIRST and LAST times it was in force -- the
    # first is the start of the id's window for that instrument (D520), the last is its expiry-day record
    d = d.sort_values(["iid", "ts_recv"]); first = d.groupby(["iid", "raw_symbol"])["ts_recv"].min().rename("ts_recv_first")
    d = d.drop_duplicates(["iid", "raw_symbol"], keep="last").merge(first, on=["iid", "raw_symbol"], how="left")
    d["family"] = d["raw_symbol"].str.extract(OPTION.pattern)[0]
    exp = pd.to_datetime(d["expiration_ns"].astype("int64"), utc=True).dt.tz_convert("US/Eastern"); d["expiry_date"] = exp.dt.strftime("%Y-%m-%d"); d["expiry_hhmm"] = exp.dt.strftime("%H:%M")
    return dict(file=Path(path).name, year=year_of(Path(path)), rows_in=n, options=int(len(d)), secs=round(time.time() - t0, 1), table=d)


def cmd_defs(workers):
    files = sorted([f for d in job_dirs()["definition"] for f in d.glob("*.definition.dbn.zst")], key=lambda p: (p.name, p.parent.name)); assert files, "no definition files"
    TEMP.mkdir(parents=True, exist_ok=True); t0 = time.time()
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(defs_worker, [str(f) for f in files], chunksize=1)
    for r, f in zip(res, files):
        (TEMP / cache_name("defs", f)).write_bytes(pickle.dumps(r["table"])); print(f"  {f.parent.name[-10:]} {r['file'][:40]:<40} {r['rows_in']:>11,} rows -> {r['options']:>8,} ES-family options  {r['secs']:>6.1f}s", flush=True)
    print(f"  defs done in {(time.time()-t0)/60:.1f} min; families: {pd.concat([r['table'] for r in res])['family'].value_counts().to_dict()}")


# ------------------------------------------------------------------------------------------ --stats
def stats_worker(path):
    import databento as db
    t0 = time.time(); p = Path(path); defs = load_cached("defs", year_of(p)); keys = np.unique(defs["iid"].to_numpy(np.uint32))
    store = db.DBNStore.from_file(path); parts = []; n = 0
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr); a = arr[np.isin(arr["instrument_id"], keys) & np.isin(arr["stat_type"], (ST_OI, ST_SETTLE))]
        if a.size:
            parts.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "stat_type": a["stat_type"].astype(np.int16), "ts_event": a["ts_event"].astype(np.int64),
                                       "ts_ref": a["ts_ref"].astype(np.int64), "quantity": a["quantity"].astype(np.int64), "price": a["price"].astype(np.int64)}))
    d = pd.concat(parts, ignore_index=True) if parts else None
    if d is not None:
        oi = d[(d["stat_type"] == ST_OI) & (d["quantity"] != UNDEF) & (d["quantity"] >= 0)]; se = d[(d["stat_type"] == ST_SETTLE) & (d["price"] != UNDEF) & (d["price"] > 0)]
        d = pd.concat([oi, se], ignore_index=True).drop_duplicates(["iid", "stat_type", "ts_event", "quantity", "price"])
        (TEMP / cache_name("stats", p)).write_bytes(pickle.dumps(d))
    return dict(file=p.name, rows_in=n, rows_kept=int(len(d)) if d is not None else 0, secs=round(time.time() - t0, 1))


def cmd_stats(workers):
    files = sorted([f for d in job_dirs()["statistics"] for f in d.glob("*.statistics.dbn.zst")], key=lambda p: (p.name, p.parent.name)); assert files, "no statistics files"
    t0 = time.time(); from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(stats_worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: r["file"]); sec = sum(r["secs"] for r in res); wall = time.time() - t0
    for r in res:
        print(f"  {r['file'][:40]:<40} {r['rows_in']:>12,} rows -> kept {r['rows_kept']:>10,}  {r['secs']:>6.1f}s", flush=True)
    print(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%); {wall/60:.1f} min")


# ------------------------------------------------------------------------------------------ --bars (0DTE volume to 15:30 ET)
def bars_worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); rows = []
    for sym, ivs in store.metadata.mappings.items():
        if OPTION.match(str(sym)):
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None); s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date"); e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
                if sid:
                    rows.append((int(sid), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return dict(file=Path(path).name, rows_in=0, rows_kept=0, secs=round(time.time() - t0, 1), table=None)
    w = pd.DataFrame(rows, columns=["iid", "raw_symbol", "w0", "w1"]); keys = np.unique(w["iid"].to_numpy(np.uint32)); parts = []; n = 0
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr); a = arr[np.isin(arr["instrument_id"], keys)]
        if not a.size:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64), "_i": np.arange(len(a))}); j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
        if j["_i"].duplicated().any():
            raise AssertionError("[IDS] an option bar claimed by two mapping windows")
        k = j["_i"].to_numpy(); ts = pd.to_datetime(a["ts_event"][k], utc=True).tz_convert("US/Eastern"); day = ts.strftime("%Y-%m-%d"); hhmm = ts.strftime("%H:%M")
        before = np.asarray(hhmm) < CUTOFF_HHMM
        parts.append(pd.DataFrame({"raw_symbol": j["raw_symbol"].to_numpy()[before], "session": np.asarray(day)[before], "volume": a["volume"][k][before].astype(np.int64)}))
    d = pd.concat(parts, ignore_index=True).groupby(["raw_symbol", "session"], sort=False)["volume"].sum().reset_index() if parts else None
    return dict(file=Path(path).name, rows_in=n, rows_kept=int(len(d)) if d is not None else 0, secs=round(time.time() - t0, 1), table=d)


def cmd_bars(workers):
    files = sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name); t0 = time.time(); from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(bars_worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: r["file"]); tabs = [r["table"] for r in res if r["table"] is not None]
    d = pd.concat(tabs, ignore_index=True).groupby(["raw_symbol", "session"], sort=False)["volume"].sum().reset_index() if tabs else pd.DataFrame(columns=["raw_symbol", "session", "volume"])
    (TEMP / "bars_pre1530.pkl").write_bytes(pickle.dumps(d)); sec = sum(r["secs"] for r in res); wall = time.time() - t0
    for r in res:
        print(f"  {r['file'][:40]:<40} {r['rows_in']:>12,} rows -> option-day rows {r['rows_kept']:>9,}  {r['secs']:>6.1f}s", flush=True)
    print(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {workers} workers ({100*sec/wall/workers:.0f}%); {len(d):,} (option, session) rows; {wall/60:.1f} min")


# ------------------------------------------------------------------------------------------ --build
def window_table(defs):
    """Per (id, year): the instruments the id carried, each with the start `w0` of its window -- its first definition time, except
    that the EARLIEST instrument of the id in the year is valid from the start of the year (the year file's first records post-date
    the first publications by hours). An id reissued within the year starts its second window at that instrument's first definition."""
    d = defs.copy(); d["w0"] = d["ts_recv_first"].astype("int64"); d = d.sort_values(["iid", "year", "w0"])
    first = d.groupby(["iid", "year"])["w0"].transform("min"); d.loc[d["w0"] == first, "w0"] = 0
    return d


def assemble(defs, stats, bars, cal, usable_session):
    """Per (usable session, option): the freshest OI and settlement publications usable that session; the expiry table; 0DTE volume."""
    # the expiry, strike and right come from the SAME YEAR's definition of the instrument id: single-digit year codes recycle, so
    # "ESZ6 C2200" is both December 2016 and December 2026, and one expiry per raw symbol across years would be wrong for one of them
    # WINDOWED labelling (D520): each publication takes the definition of its instrument id that was in force at the publication
    # time -- the last definition record for that (id, year) with ts_recv <= ts_event -- so an id reissued within the year keeps
    # both instruments, each with its own strike and expiry
    dcols = ["iid", "year", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "expiration_ns", "underlying", "w0"]
    d = window_table(defs)[dcols].sort_values("w0")
    stats = pd.merge_asof(stats.sort_values("ts_event"), d, left_on="ts_event", right_on="w0", by=["iid", "year"], direction="backward"); stats = stats[stats["raw_symbol"].notna()]
    stats["usable"] = usable_session(stats["ts_event"].to_numpy(), cal); stats = stats[pd.notna(stats["usable"])]
    keep = ["usable", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "expiration_ns", "underlying"]
    oi = stats[stats["stat_type"] == ST_OI].sort_values("ts_event").groupby(["usable", "raw_symbol"], as_index=False).last()[keep + ["quantity", "ts_event", "ts_ref"]].rename(columns={"quantity": "oi", "ts_event": "oi_ts_event", "ts_ref": "oi_ts_ref"})
    se = stats[stats["stat_type"] == ST_SETTLE].sort_values("ts_event").groupby(["usable", "raw_symbol"], as_index=False).last()[["usable", "raw_symbol", "price"]]; se["settle"] = se["price"] * PX; se = se.drop(columns="price")
    t = oi.merge(se, on=["usable", "raw_symbol"], how="left").rename(columns={"usable": "session"})
    t = t[t["expiry_date"] >= t["session"]]                                                                       # an option expired before the session carries no gamma
    t = t.merge(bars.rename(columns={"volume": "vol_to_1530"}), on=["raw_symbol", "session"], how="left")
    t["vol_to_1530"] = np.where(t["expiry_date"] == t["session"], t["vol_to_1530"].fillna(0), np.nan)             # kept only for the same-day expiry
    t["oi_pub_et"] = pd.to_datetime(t["oi_ts_event"], utc=True).dt.tz_convert("US/Eastern").dt.strftime("%Y-%m-%dT%H:%M")
    # D616: the REFERENCE session of the open interest kept -- the business date the number describes. `ts_ref` on a
    # statistics message is midnight UTC on that date (19:00 ET in winter, 20:00 in summer, never UNDEF on these rows),
    # so its UTC date is the session. `oi_pub_et` cannot do this job: a publication is usable on exactly one session, so
    # adjacent sessions' publication times are never equal, and CME's preliminary-then-final revision is invisible in it
    # (16.3 % of (option, usable session) cells carried more than one distinct reference date in 2023). A difference of
    # open interest is only a one-session position change if the two reference sessions are adjacent, and this column is
    # what makes that checkable. The publication KEPT is unchanged -- still the last by ts_event -- so `oi` does not move.
    t["oi_ref_session"] = t["oi_ts_ref"].to_numpy("int64").astype("datetime64[ns]").astype("datetime64[D]").astype(str)   # exact: ts_ref is midnight UTC, and this is ~50x strftime
    return t.sort_values(["session", "expiry_date", "strike", "right"]).reset_index(drop=True)


def cmd_build():
    OIB = _load("d497", "build_fut_open_interest.py"); cal = es_calendar(); t0 = time.time()
    defs = load_cached("defs"); bars = pickle.loads((TEMP / "bars_pre1530.pkl").read_bytes())
    # assembled one YEAR of publications at a time (the weekly families' statistics run to ~200M rows over the span; a
    # December-evening publication assembles in its own year with a January usable session, so the split is exact)
    years = sorted({int(p.stem.split("_")[-1]) for p in TEMP.glob("stats_*.pkl")}); parts = []
    for y in years:
        st = load_cached("stats", y); ty = assemble(defs[defs["year"] == y], st, bars, cal, OIB.usable_session); parts.append(ty); print(f"  {y}: {len(st):,} publications -> {len(ty):,} fixture rows", flush=True); del st
    t = pd.concat(parts, ignore_index=True).sort_values(["session", "expiry_date", "strike", "right"]).reset_index(drop=True)
    cols = ["session", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "underlying", "oi", "settle", "oi_pub_et", "vol_to_1530", "oi_ref_session"]
    t[cols].to_csv(OUT, index=False, compression="gzip", float_format="%.6g", encoding="utf-8")
    META.write_text(json.dumps(dict(spec="D581", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), rows=int(len(t)), sessions=int(t["session"].nunique()), first=str(t["session"].min()), last=str(t["session"].max()),
                                    families=t["family"].value_counts().to_dict(), usable_rule="a publication is usable on the first ES session whose 10:00 ET entry is strictly after its ts_event (D497/D521)",
                                    stat_types=dict(open_interest=ST_OI, settlement=ST_SETTLE), sentinels="UNDEF on both; settlement == 0.0 dropped (D526)", vol_to_1530="minute-bar volume before 15:30 ET on the option's expiry session only, from the archive on disk",
                                    oi_ref_session="D616: the ES session the open interest DESCRIBES, from the kept publication's ts_ref (midnight UTC on the business date). The publication kept is unchanged (last by ts_event), so `oi` is untouched. A difference of `oi` across two sessions is a one-session position change only where the two reference sessions are adjacent -- G7 measures how often that holds and what the residue is.",
                                    gates=None), indent=1), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}: {len(t):,} rows, {t['session'].nunique():,} sessions {t['session'].min()} .. {t['session'].max()}, families {t['family'].value_counts().to_dict()} in {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ --gates
def black76_iv(price, F, K, tau, right):
    """Bisection on Black-76 (rate 0) for the volatility that prices `price`; nan where no root in [1 %, 400 %]. Stdlib normal cdf so both interpreters run it."""
    import math
    def cdf(x):
        return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))
    def px(sig):
        d1 = (math.log(F / K) + 0.5 * sig * sig * tau) / (sig * math.sqrt(tau)); d2 = d1 - sig * math.sqrt(tau)
        return F * cdf(d1) - K * cdf(d2) if right == "C" else K * cdf(-d2) - F * cdf(-d1)
    lo, hi = 0.01, 4.0
    if not (px(lo) <= price <= px(hi)):
        return np.nan
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        if px(mid) < price:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def gate7_reference_session(t, cal, log=print):
    """G7 (D616) -- the open interest's reference session is recoverable, sits BEFORE the session it is used on, and one
    session back; and, per option on adjacent sessions, the two reference sessions are adjacent, which is the only
    condition under which a difference of open interest is a one-session position change.

    Reported, not enforced, because the residue is real and era-dependent: a publication whose reference date is not an
    ES session (a holiday stamp), a two-session gap after a skipped evening, and CME's preliminary-then-final revision,
    which puts two publications for the SAME reference date on adjacent sessions and so makes a delta of exactly zero
    that is not a zero position change. A study differencing this column must drop the pairs whose span is not one and
    say how many it dropped -- the fixture's job is to make that countable."""
    posn = {d: i for i, d in enumerate(list(cal))}
    ref = t["oi_ref_session"].astype(str); sess = t["session"].astype(str)
    ri = ref.map(posn).to_numpy(dtype="float64"); si = sess.map(posn).to_numpy(dtype="float64")
    gap = si - ri; fin = np.isfinite(gap)
    hist = {str(int(g)): int(n) for g, n in zip(*np.unique(gap[fin], return_counts=True))}
    at_or_after = float((ref.to_numpy() >= sess.to_numpy()).mean())
    # per option, consecutive fixture sessions that are adjacent ES sessions: is the reference span also one session?
    u = t[["raw_symbol", "session", "oi_ref_session"]].sort_values(["raw_symbol", "session"], kind="stable").reset_index(drop=True)
    sym = u["raw_symbol"].to_numpy(); same = sym[1:] == sym[:-1]
    us = u["session"].astype(str).map(posn).to_numpy(dtype="float64"); ur = u["oi_ref_session"].astype(str).map(posn).to_numpy(dtype="float64")
    ds = us[1:] - us[:-1]; dr = ur[1:] - ur[:-1]; pairs = same & (ds == 1)
    span1 = float(np.mean(dr[pairs] == 1)) if pairs.any() else None
    span0 = float(np.mean(dr[pairs] == 0)) if pairs.any() else None       # the revision: a spurious zero delta
    spannan = float(np.mean(~np.isfinite(dr[pairs]))) if pairs.any() else None
    by_year = {}
    yr = sess.str.slice(0, 4).to_numpy()
    for y in sorted(set(yr)):
        m = yr == y
        by_year[y] = dict(rows=int(m.sum()), share_gap_one=float(np.mean(gap[m & fin] == 1)) if (m & fin).any() else None,
                          share_unrecoverable=float(np.mean(~fin[m])))
    out = dict(rows=int(len(t)), share_reference_is_an_es_session=float(fin.mean()), gap_sessions_histogram=hist,
               share_gap_exactly_one=float(np.mean(gap[fin] == 1)), share_reference_at_or_after_session=at_or_after,
               adjacent_pairs=int(pairs.sum()), share_pair_reference_span_one=span1, share_pair_reference_span_zero_a_revision=span0,
               share_pair_reference_unrecoverable=spannan, by_year=by_year)
    out["passes"] = bool(out["share_reference_is_an_es_session"] >= 0.95 and at_or_after <= 0.01 and out["share_gap_exactly_one"] >= 0.95)
    return out


def cmd_gates(log=print):
    meta = json.loads(META.read_text(encoding="utf-8")); t = pd.read_csv(OUT, dtype={"session": str, "raw_symbol": str, "family": str, "right": str, "expiry_date": str, "expiry_hhmm": str, "underlying": str, "oi_pub_et": str, "oi_ref_session": str}, encoding="utf-8"); out = {}; ok = True
    # G1 OI >= 0, settlement > 0 where present
    out["G1"] = dict(negative_oi=int((t["oi"] < 0).sum()), zero_or_negative_settle=int((t["settle"] <= 0).sum()), settle_missing=int(t["settle"].isna().sum()), passes=bool((t["oi"] >= 0).all() and (t["settle"].dropna() > 0).all())); ok &= out["G1"]["passes"]
    # G2 the OI used on a session was published strictly before that session's 10:00 ET
    pub = pd.to_datetime(t["oi_pub_et"]); sess = pd.to_datetime(t["session"]); before = (pub < sess + pd.Timedelta(hours=10)); out["G2"] = dict(rows=int(len(t)), published_before_entry=float(before.mean()), passes=bool(before.all())); ok &= out["G2"]["passes"]
    # G3 the expiry calendar: a same-day-expiring family on the weekdays it should exist
    s = t[t["expiry_date"] == t["session"]].groupby("session")["family"].agg(lambda x: sorted(set(x))); days = pd.to_datetime(pd.Series(sorted(t["session"].unique()))); wd = days.dt.dayofweek.to_numpy(); ds = days.dt.strftime("%Y-%m-%d").to_numpy()
    has0 = np.array([d in s.index for d in ds]); first = {f: str(t[t["family"] == f]["expiry_date"].min()) for f in sorted(t["family"].unique())}
    by_wd = {int(w): float(has0[wd == w].mean()) for w in range(5)}; since2205 = has0[ds >= "2022-05-02"]; fri = has0[(wd == 4)]
    out["G3"] = dict(first_expiry_by_family=first, share_sessions_with_0dte_by_weekday=by_wd, share_with_0dte_since_2022_05=float(since2205.mean()), share_fridays_with_0dte=float(fri.mean()), passes=bool(fri.mean() >= 0.95 and since2205.mean() >= 0.95)); ok &= out["G3"]["passes"]
    # G4 strikes with OI per session
    ns = t[t["oi"] > 0].groupby("session")["strike"].nunique(); out["G4"] = dict(median_strikes_with_oi=float(ns.median()), sessions_under_20=[(d, int(n)) for d, n in ns[ns < G3_MIN_STRIKES].items()][:40], n_under_20=int((ns < G3_MIN_STRIKES).sum()), passes=bool((ns < G3_MIN_STRIKES).sum() <= 5)); ok &= out["G4"]["passes"]
    # G5 the OI sum by family recomputed from the raw statistics cache by a second path on ten seeded sessions
    OIB = _load("d497", "build_fut_open_interest.py"); cal = es_calendar(); rng = np.random.default_rng(581); pick = sorted(rng.choice(sorted(t["session"].unique()), 10, replace=False)); checks = []
    for d in pick:
        yr = int(d[:4]); st = load_cached("stats", yr); df = load_cached("defs", yr)
        # the same expiry rule as the fixture: an option whose expiry date is before the session carries no gamma and is not a row
        # (its final OI publication, made on its last evening, is otherwise usable the next session -- 1.49M contracts of ESM2 on 2022-06-21)
        # second path: the definition in force at each publication found by bisection on the id's own definition times (never merge_asof)
        import bisect
        st = st[st["stat_type"] == ST_OI].copy(); st["usable"] = OIB.usable_session(st["ts_event"].to_numpy(), cal); st = st[st["usable"] == d]
        dd = df.assign(year=yr); dd = window_table(dd).sort_values(["iid", "w0"]); win = {i: (g["w0"].to_list(), g[["raw_symbol", "family", "expiry_date"]].to_dict("records")) for i, g in dd.groupby("iid")}
        lab = []
        for r in st.itertuples():
            ts, recs = win.get(r.iid, ([], [])); k = bisect.bisect_right(ts, r.ts_event) - 1; lab.append(recs[k] if k >= 0 else {"raw_symbol": None, "family": None, "expiry_date": None})
        st = pd.concat([st.reset_index(drop=True), pd.DataFrame(lab)], axis=1); st = st[st["raw_symbol"].notna() & (st["expiry_date"] >= d)]
        piv = st.sort_values("ts_event").groupby("raw_symbol").last().groupby("family")["quantity"].sum().to_dict()
        mine = t[t["session"] == d].groupby("family")["oi"].sum().to_dict(); agree = all(abs(mine.get(f, 0) - piv.get(f, 0)) < 1e-9 for f in set(mine) | set(piv)); checks.append(dict(session=d, agree=bool(agree)))
        if not agree:
            log(f"    G5 {d}: fixture {mine} vs second path {piv}")
    out["G5"] = dict(sessions=checks, passes=bool(all(c["agree"] for c in checks))); ok &= out["G5"]["passes"]
    # G6 settlement-implied vol inverts near the money (uses the underlying's settlement from the strip; 5 seeded sessions)
    strip = pd.read_csv(FIX / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[strip["root"] == "ES"]
    calx = list(cal); inv = []; tried = 0
    for d in pick[:5]:
        i = calx.index(d); prev = calx[i - 1]; u = t[(t["session"] == d) & t["settle"].notna()].copy(); f = strip[strip["ref"] == prev].set_index("contract")["settle"]
        u["F"] = u["underlying"].map(f); u = u[u["F"].notna()]; u = u[(u["strike"] / u["F"] - 1).abs() < G6_MONEYNESS]
        for r in u.itertuples():
            n_ahead = max(calx.index(r.expiry_date) - i, 0) if r.expiry_date in calx else 0; tau = (n_ahead * 6.5 + 6.5) / (252 * 6.5)
            tried += 1; inv.append(np.isfinite(black76_iv(r.settle, r.F, r.strike, tau, r.right)))
    out["G6"] = dict(near_money_rows_tried=tried, share_inverting=float(np.mean(inv)) if inv else None, passes=bool(inv and np.mean(inv) >= 0.99)); ok &= out["G6"]["passes"]
    out["G7"] = gate7_reference_session(t, cal, log); ok &= out["G7"]["passes"]
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok); META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    log(f"G1 negative OI {out['G1']['negative_oi']}, non-positive settle {out['G1']['zero_or_negative_settle']}, settle missing {out['G1']['settle_missing']} {'PASS' if out['G1']['passes'] else 'FAIL'}")
    log(f"G2 OI published before the session's entry on {out['G2']['published_before_entry']:.4f} of rows {'PASS' if out['G2']['passes'] else 'FAIL'}")
    log(f"G3 first expiry by family {first}; 0DTE share by weekday {by_wd}; since 2022-05 {out['G3']['share_with_0dte_since_2022_05']:.3f}; Fridays {out['G3']['share_fridays_with_0dte']:.3f} {'PASS' if out['G3']['passes'] else 'FAIL'}")
    log(f"G4 median strikes with OI {out['G4']['median_strikes_with_oi']:.0f}; sessions under 20: {out['G4']['n_under_20']} {'PASS' if out['G4']['passes'] else 'FAIL'}")
    log(f"G5 second-path OI sums agree on {sum(c['agree'] for c in checks)}/10 sessions {'PASS' if out['G5']['passes'] else 'FAIL'}")
    log(f"G6 near-the-money settlement IV inverts on {out['G6']['share_inverting']} of {tried} {'PASS' if out['G6']['passes'] else 'FAIL'}")
    g7 = out["G7"]; log(f"G7 reference session recoverable on {g7['share_reference_is_an_es_session']:.4f} of rows, one session back on {g7['share_gap_exactly_one']:.4f}, "
                        f"at or after the session on {g7['share_reference_at_or_after_session']:.4f}; on {g7['adjacent_pairs']:,} adjacent pairs the reference span is one on "
                        f"{g7['share_pair_reference_span_one']:.4f} and zero (a revision) on {g7['share_pair_reference_span_zero_a_revision']:.4f} {'PASS' if g7['passes'] else 'FAIL'}")
    log(f"ALL GATES {'PASS' if ok else 'FAIL'}; wrote {META.relative_to(REPO)}"); return ok


def cmd_selftest():
    assert OPTION.match("EW1G6 C8200") and OPTION.match("E2BZ5 P5800") and OPTION.match("ESZ5 C6000") and OPTION.match("EWJ6 P4500") and not OPTION.match("ESZ5") and not OPTION.match("OZNZ5 C110")
    assert OPTION.match("E3DZ5 C6975").group(1) == "E3D" and OPTION.match("EW3Z5 C7035").group(1) == "EW3"
    # assemble: the OI published 21:00 ET on T-1 is usable on T; an expired option is dropped; 0DTE volume attaches only on the expiry session
    cal = np.array(["2023-03-01", "2023-03-02", "2023-03-03"])
    def ns(s):
        return int(pd.Timestamp(s, tz="US/Eastern").value)
    defs = pd.DataFrame([dict(iid=1, raw_symbol="E1CH3 C4000", family="E1C", right="C", strike=4000.0, expiry_date="2023-03-01", expiry_hhmm="16:00", expiration_ns=ns("2023-03-01T16:00"), underlying="ESH3", ts_recv=ns("2023-03-01T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023),
                         dict(iid=2, raw_symbol="EW1H3 P3900", family="EW1", right="P", strike=3900.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="ESH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023),
                         # id 1 reissued within the year to a later instrument: its window starts at that instrument's first definition
                         dict(iid=1, raw_symbol="E1CH3 C4100", family="E1C", right="C", strike=4100.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="ESH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-03-02T00:30"), year=2023),
                         # D616: a third option, used only for the preliminary-then-final revision case below
                         dict(iid=3, raw_symbol="EW1H3 P3800", family="EW1", right="P", strike=3800.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="ESH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023)])
    def refns(d):                                                        # a statistics message's ts_ref: midnight UTC on the business date
        return int(pd.Timestamp(d, tz="UTC").value)
    stats = pd.DataFrame([dict(iid=1, stat_type=ST_OI, ts_event=ns("2023-02-28T21:00"), ts_ref=refns("2023-02-28"), quantity=100, price=0, year=2023),
                          dict(iid=2, stat_type=ST_OI, ts_event=ns("2023-02-28T21:00"), ts_ref=refns("2023-02-28"), quantity=50, price=0, year=2023),
                          dict(iid=2, stat_type=ST_SETTLE, ts_event=ns("2023-02-28T17:00"), ts_ref=refns("2023-02-28"), quantity=0, price=int(12.5 / PX), year=2023),
                          dict(iid=2, stat_type=ST_OI, ts_event=ns("2023-03-01T21:00"), ts_ref=refns("2023-03-01"), quantity=70, price=0, year=2023),
                          dict(iid=1, stat_type=ST_OI, ts_event=ns("2023-03-02T21:00"), ts_ref=refns("2023-03-02"), quantity=33, price=0, year=2023),   # after the reissue: belongs to E1CH3 C4100, usable 2023-03-03
                          # the revision trap: two publications usable on 2023-03-02, the LATER one restating the OLDER business date
                          dict(iid=3, stat_type=ST_OI, ts_event=ns("2023-03-01T21:00"), ts_ref=refns("2023-03-01"), quantity=10, price=0, year=2023),
                          dict(iid=3, stat_type=ST_OI, ts_event=ns("2023-03-01T22:00"), ts_ref=refns("2023-02-28"), quantity=11, price=0, year=2023)])
    bars = pd.DataFrame([dict(raw_symbol="E1CH3 C4000", session="2023-03-01", volume=555), dict(raw_symbol="EW1H3 P3900", session="2023-03-01", volume=9)])
    OIB = _load("d497", "build_fut_open_interest.py"); t = assemble(defs, stats, bars, cal, OIB.usable_session)
    r1 = t[(t["session"] == "2023-03-01") & (t["raw_symbol"] == "E1CH3 C4000")].iloc[0]; assert r1["oi"] == 100 and r1["vol_to_1530"] == 555, r1.to_dict()
    r2 = t[(t["session"] == "2023-03-01") & (t["raw_symbol"] == "EW1H3 P3900")].iloc[0]; assert r2["oi"] == 50 and abs(r2["settle"] - 12.5) < 1e-9 and np.isnan(r2["vol_to_1530"]), r2.to_dict()
    r3 = t[(t["session"] == "2023-03-02") & (t["raw_symbol"] == "EW1H3 P3900")].iloc[0]; assert r3["oi"] == 70, "the freshest usable publication"
    assert not ((t["session"] == "2023-03-02") & (t["raw_symbol"] == "E1CH3 C4000")).any(), "an option expired before the session must be dropped"
    r4 = t[(t["session"] == "2023-03-03") & (t["iid"] == 1)] if "iid" in t else t[(t["session"] == "2023-03-03") & (t["raw_symbol"] == "E1CH3 C4100")]
    assert len(r4) == 1 and r4.iloc[0]["raw_symbol"] == "E1CH3 C4100" and r4.iloc[0]["oi"] == 33, f"the reissued id must carry its second instrument after the reissue: {r4.to_dict('records')}"
    iv = black76_iv(12.5, 4000.0, 3900.0, 2 / 252, "P"); assert np.isfinite(iv) and 0.05 < iv < 1.0, iv
    # ---- D616: the reference session, and G7 ----
    assert r1["oi_ref_session"] == "2023-02-28", f"the publication usable on 2023-03-01 describes 2023-02-28, not {r1['oi_ref_session']}"
    assert r3["oi_ref_session"] == "2023-03-01", f"the freshest publication carries ITS OWN reference date: {r3['oi_ref_session']}"
    rev = t[(t["session"] == "2023-03-02") & (t["raw_symbol"] == "EW1H3 P3800")].iloc[0]
    assert rev["oi"] == 11 and rev["oi_ref_session"] == "2023-02-28", f"last by ts_event wins and brings its reference date with it: {rev.to_dict()}"
    # the revision is INVISIBLE in oi_pub_et and VISIBLE in oi_ref_session -- the whole point of the column
    prev = t[(t["session"] == "2023-03-01") & (t["raw_symbol"] == "EW1H3 P3900")].iloc[0]
    assert rev["oi_pub_et"] != prev["oi_pub_et"], "publication times never repeat, so they cannot reveal a restated business date"
    assert rev["oi_ref_session"] == prev["oi_ref_session"], "...while the reference dates DO repeat, which is what makes the trap countable"
    good = pd.DataFrame([dict(raw_symbol="A", session="2023-03-02", oi_ref_session="2023-03-01"), dict(raw_symbol="A", session="2023-03-03", oi_ref_session="2023-03-02"),
                         dict(raw_symbol="B", session="2023-03-02", oi_ref_session="2023-03-01"), dict(raw_symbol="B", session="2023-03-03", oi_ref_session="2023-03-02")])
    g = gate7_reference_session(good, cal, log=lambda *a: None)
    assert g["passes"] and g["share_gap_exactly_one"] == 1.0 and g["adjacent_pairs"] == 2 and g["share_pair_reference_span_one"] == 1.0, g
    # RAISES on the break: a reference session at or after the session it is used on is look-ahead, and G7 must refuse it
    bad = good.copy(); bad.loc[0, "oi_ref_session"] = "2023-03-02"; b = gate7_reference_session(bad, cal, log=lambda *a: None)
    assert not b["passes"] and b["share_reference_at_or_after_session"] > 0.01, b
    # ...and on the revision break: both sessions restating one business date leaves the pair span at zero
    bad2 = good.copy(); bad2.loc[1, "oi_ref_session"] = "2023-03-01"; b2 = gate7_reference_session(bad2, cal, log=lambda *a: None)
    assert b2["share_pair_reference_span_zero_a_revision"] == 0.5, b2
    print(f"selftest: symbology, usable-session keying (21:00 ET T-1 -> T), expiry drop, 0DTE volume attachment, IV inversion (iv {iv:.3f}), "
          f"the reference session on the kept publication, the revision trap visible in oi_ref_session and invisible in oi_pub_et, "
          f"and G7 passing clean data and RAISING on both breaks (look-ahead reference, restated business date) -- all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    for f in ("defs", "stats", "bars", "build", "gates", "selftest"):
        g.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--workers", type=int, default=6); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.defs:
        cmd_defs(a.workers)
    elif a.stats:
        cmd_stats(a.workers)
    elif a.bars:
        cmd_bars(a.workers)
    elif a.build:
        cmd_build()
    else:
        sys.exit(0 if cmd_gates() else 1)
