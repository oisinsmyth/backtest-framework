"""The NQ option end-of-day fixture for the opening model's dealer-gamma agent A4 (stage S-H) and its Gate O0-H -- a mirror
of D581/D616's ES builder (`scripts/build_fut_es_options_eod.py`) on the NQ-family pull of 2026-09-27
(`data/prelapse_options_pull_jobs_nq.json`). Per (usable NQ session, option): the prior-close open interest and
settlement, the strike/expiry/right from `definition`, the OI's publication time and the session it describes. Data layer
only: no gamma, no signal, no return, no price outcome read.

    python scripts/build_fut_nq_options_eod.py --defs  [--workers 6]   # SYSTEM interpreter: definition files -> the option table (cached)
    python scripts/build_fut_nq_options_eod.py --stats [--workers 6] [--only 2017]   # statistics files -> OI and settlement publications (cached per file)
    python scripts/build_fut_nq_options_eod.py --build                 # caches -> data/fixtures/fut_nq_options_eod.csv.gz + meta
    python scripts/build_fut_nq_options_eod.py --gates                 # G1-G7, O0-H, the vault gate and the reports -> meta
    python scripts/build_fut_nq_options_eod.py --selftest

THE VAULT (hard). Sessions 2016-01-04 -> 2025-02-28 only. Three layers: (1) at READ time nothing with ts_recv or ts_event
at or after 2025-03-01 00:00 ET is kept from any file, the 2026 files are never opened, and the 2025 files are abandoned at
the first chunk wholly past the cutoff (only while the file has proven ts_recv-monotone up to there); (2) the usable-session
calendar ends at 2025-02-28, and `filter_before` drops any later session; (3) `assert_none_at_or_after` on session,
oi_ref_session and the publication date before the write and again in --gates.

Conventions, as ES. `stat_type` 9 = open interest in `quantity`; 3 = settlement in `price` (1e-9 units); UNDEF filtered on
both, and a settlement of exactly 0.0 is D526's second sentinel and is dropped. A publication is USABLE on the first NQ
session whose 10:00 ET entry is strictly after its ts_event (D497/D521): the OI published ~21:00 ET on T-1 describes T-1's
close and is usable on session T. Option ids are labelled from the same YEAR's definition file by the definition in force
at the publication (D520's windowed rule; single-digit year codes recycle). The NQ calendar is fut_index_sessions' NQ days
with >= 380 bars, exactly as ES's builder uses ES's.

What the NQ parents resolved to (probed on the 2023 definition file before this was written, and recorded per family in the
meta at --build): NQ.OPT = the quarterly family alone, expiring 09:30 ET on Fridays (AM-settled, as ES); QN1-QN4 = Friday
weeklies at 16:00 (13:00 on early-close days; a Thursday when the Friday is a holiday); QNE = end of month at 16:00, any
weekday; Q2A/Q3A = Monday dailies; Q1B-Q4B Tuesdays; Q1C-Q4C Wednesdays; Q1D-Q4D Thursdays, all 16:00. **Q1A and Q4A (and any
Q5x) were not in the pull**, so Mondays of weeks 1, 4 and 5 carry no same-day NQ expiry here -- a difference from ES, which
has E1A-E4A. `vol_to_1530` is NOT built: the NQ pull has no option bars, and A4 does not need it.

Differences from ES in the write: strike and settle are written at "%.10g" after rounding (ES wrote "%.6g", which would
round a deep-in-the-money NQ settle such as 12345.75 to 12345.8).
"""
from __future__ import annotations
import argparse, bisect, importlib.util, json, pickle, re, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts")); sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before, ReservedSliceError  # noqa: E402


def _main_checkout(repo):
    """This builder runs in a worktree; the gitignored raw pulls and input fixtures live in the MAIN checkout."""
    p = repo
    while p.parent != p:
        if p.name == "worktrees" and p.parent.name == ".claude":
            return p.parent.parent
        p = p.parent
    return repo


MAIN = _main_checkout(REPO)
RAW = MAIN / "data" / "raw" / "databento"; FIX_IN = MAIN / "data" / "fixtures"
FIX = REPO / "data" / "fixtures"; TEMP = REPO / "temp" / "nq_options_eod"
OUT = FIX / "fut_nq_options_eod.csv.gz"; META = FIX / "fut_nq_options_eod.meta.json"; JOBS = REPO / "data" / "prelapse_options_pull_jobs_nq.json"
SESSIONS = FIX_IN / "fut_index_sessions.csv.gz"; STRIP = FIX_IN / "fut_settle_strip.csv.gz"; ES_FIX = FIX_IN / "fut_es_options_eod.csv.gz"
OPTION = re.compile(r"^(NQ|QN[1-4]|QNE|Q[1-5][A-D])([FGHJKMNQUVXZ])(\d{1,2}) ([CP])(\d+)$")
ST_OI, ST_SETTLE = 9, 3; UNDEF = np.iinfo(np.int64).max; PX = 1e-9; CHUNK = 5_000_000; CHUNK_DEFS = 1_000_000   # a definition record is ~520 bytes: 5M of them OOM a worker
START, RESERVED_FROM = "2016-01-04", "2025-03-01"
CUTOFF_NS = int(pd.Timestamp(RESERVED_FROM, tz="US/Eastern").value)          # 2025-03-01 00:00 ET: nothing at or after is kept
LAST_FILE_YEAR = 2025                                                         # the 2026 files are never opened
G3_MIN_STRIKES = 20; G6_MONEYNESS = 0.05; O0H_BAR = 0.90
SPOT_SESSIONS = ("2018-06-14", "2021-11-10", "2024-05-15")                    # the ES-vs-NQ OI order-of-magnitude check (fixed before the build)
COLS = ["session", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "underlying", "oi", "settle", "oi_pub_et", "oi_ref_session"]


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s); sys.modules[name] = m; s.loader.exec_module(m); return m


def job_dirs():
    out = {"statistics": [], "definition": []}
    for j in json.loads(JOBS.read_text(encoding="utf-8"))["jobs"]:
        out[j["schema"]].append(RAW / j["job"]["id"])
    return out


def year_of(path):
    m = re.search(r"glbx-mdp3-(\d{4})", Path(path).name); return int(m.group(1))


def in_scope(files):
    """The vault's file layer: a file whose span starts after LAST_FILE_YEAR is never opened."""
    return [f for f in files if year_of(f) <= LAST_FILE_YEAR]


def cache_name(kind, path):
    return f"{kind}_{Path(path).parent.name[-10:]}_{year_of(path)}.pkl"


def load_cached(kind, year=None):
    frames = []
    for p in sorted(TEMP.glob(f"{kind}_*.pkl")):
        y = int(p.stem.split("_")[-1])
        if year is None or y == year:
            frames.append(pickle.loads(p.read_bytes()).assign(year=y))
    return pd.concat(frames, ignore_index=True) if frames else None


def nq_calendar(all_days=False):
    s = pd.read_csv(SESSIONS, dtype={"day": str, "contract": str, "root": str}, encoding="utf-8"); s = s[s["root"] == "NQ"]
    if not all_days:
        s = s[s["bars"] >= 380]
    d = np.array(sorted(s["day"].unique())); d = d[d >= START]
    return filter_before(d, None, RESERVED_FROM)


class _Monotone:
    """Tracks whether a file's ts_recv has been non-decreasing so far; only then may a chunk wholly past the cutoff end the read."""
    def __init__(self):
        self.prev = -1; self.ok = True

    def step(self, ts):
        if len(ts):
            self.ok &= bool(ts[0] >= self.prev and (np.diff(ts) >= 0).all()); self.prev = int(ts[-1])
        return self.ok and len(ts) and int(ts.min()) >= CUTOFF_NS


# ------------------------------------------------------------------------------------------ --defs
def defs_worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); rows = []; n = 0; mono = _Monotone(); stopped = False
    for arr in store.to_ndarray(count=CHUNK_DEFS):
        n += len(arr); rv = arr["ts_recv"].astype(np.int64)
        if mono.step(rv):
            stopped = True; break
        arr = arr[rv < CUTOFF_NS]                                                         # vault layer 1
        cls = arr["instrument_class"]; m = (cls == b"C") | (cls == b"P")
        if not m.any():
            continue
        a = arr[m]; sym = np.char.decode(a["raw_symbol"].astype("S"), "ascii"); keep = np.array([bool(OPTION.match(s)) for s in sym])
        if not keep.any():
            continue
        a = a[keep]; sym = sym[keep]
        rows.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "raw_symbol": sym, "right": np.char.decode(a["instrument_class"].astype("S"), "ascii"),
                                  "strike": np.round(a["strike_price"].astype(np.int64) * PX, 4), "expiration_ns": a["expiration"].astype(np.int64),
                                  "underlying": np.char.decode(a["underlying"].astype("S"), "ascii").astype(str), "ts_recv": a["ts_recv"].astype(np.int64)}))
    d = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["iid", "raw_symbol", "right", "strike", "expiration_ns", "underlying", "ts_recv"])
    # a definition record is republished every session; keep, per (id, symbol), the FIRST and LAST times it was in force (D520)
    d = d.sort_values(["iid", "ts_recv"]); first = d.groupby(["iid", "raw_symbol"])["ts_recv"].min().rename("ts_recv_first")
    d = d.drop_duplicates(["iid", "raw_symbol"], keep="last").merge(first, on=["iid", "raw_symbol"], how="left")
    d["family"] = d["raw_symbol"].str.extract(OPTION.pattern)[0]
    exp = pd.to_datetime(d["expiration_ns"].astype("int64"), utc=True).dt.tz_convert("US/Eastern"); d["expiry_date"] = exp.dt.strftime("%Y-%m-%d"); d["expiry_hhmm"] = exp.dt.strftime("%H:%M")
    return dict(file=Path(path).name, job=Path(path).parent.name, year=year_of(path), rows_in=n, options=int(len(d)), monotone=mono.ok, stopped_at_cutoff=stopped,
                max_ts_recv_kept=int(d["ts_recv"].max()) if len(d) else None, secs=round(time.time() - t0, 1), table=d)


def cmd_defs(workers):
    files = in_scope(sorted([f for d in job_dirs()["definition"] for f in d.glob("*.definition.dbn.zst")], key=lambda p: (p.name, p.parent.name))); assert files, "no definition files"
    TEMP.mkdir(parents=True, exist_ok=True); t0 = time.time()
    from multiprocessing import Pool
    with Pool(workers) as pool:
        res = pool.map(defs_worker, [str(f) for f in files], chunksize=1)
    log = []
    for r, f in zip(res, files):
        assert r["max_ts_recv_kept"] is None or r["max_ts_recv_kept"] < CUTOFF_NS, "[VAULT] a definition at or after the cutoff was kept"
        (TEMP / cache_name("defs", f)).write_bytes(pickle.dumps(r["table"]))
        log.append({k: v for k, v in r.items() if k != "table"})
        print(f"  {r['job'][-10:]} {r['file'][:40]:<40} {r['rows_in']:>11,} rows -> {r['options']:>8,} NQ-family options  monotone={r['monotone']} stop={r['stopped_at_cutoff']}  {r['secs']:>6.1f}s", flush=True)
    (TEMP / "defs_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(f"  defs done in {(time.time()-t0)/60:.1f} min; families: {pd.concat([r['table'] for r in res])['family'].value_counts().to_dict()}")


# ------------------------------------------------------------------------------------------ --stats
def stats_worker(path):
    import databento as db
    t0 = time.time(); p = Path(path); defs = load_cached("defs", year_of(p)); keys = np.unique(defs["iid"].to_numpy(np.uint32))
    store = db.DBNStore.from_file(path); parts = []; n = 0; mono = _Monotone(); stopped = False
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr); rv = arr["ts_recv"].astype(np.int64)
        if mono.step(rv):
            stopped = True; break
        m = np.isin(arr["stat_type"], (ST_OI, ST_SETTLE)) & (rv < CUTOFF_NS) & (arr["ts_event"].astype(np.int64) < CUTOFF_NS)   # vault layer 1
        a = arr[m]; a = a[np.isin(a["instrument_id"], keys)]
        if a.size:
            parts.append(pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "stat_type": a["stat_type"].astype(np.int16), "ts_event": a["ts_event"].astype(np.int64),
                                       "ts_ref": a["ts_ref"].astype(np.int64), "quantity": a["quantity"].astype(np.int64), "price": a["price"].astype(np.int64)}))
    d = pd.concat(parts, ignore_index=True) if parts else None
    if d is not None:
        oi = d[(d["stat_type"] == ST_OI) & (d["quantity"] != UNDEF) & (d["quantity"] >= 0)]; se = d[(d["stat_type"] == ST_SETTLE) & (d["price"] != UNDEF) & (d["price"] > 0)]
        d = pd.concat([oi, se], ignore_index=True).drop_duplicates(["iid", "stat_type", "ts_event", "quantity", "price"])
        assert (d["ts_event"] < CUTOFF_NS).all(), "[VAULT] a statistic at or after the cutoff was kept"
        (TEMP / cache_name("stats", p)).write_bytes(pickle.dumps(d))
    return dict(file=p.name, job=p.parent.name, rows_in=n, rows_kept=int(len(d)) if d is not None else 0, monotone=mono.ok, stopped_at_cutoff=stopped, secs=round(time.time() - t0, 1))


def cmd_stats(workers, only=None):
    files = in_scope(sorted([f for d in job_dirs()["statistics"] for f in d.glob("*.statistics.dbn.zst")], key=lambda p: (p.name, p.parent.name))); assert files, "no statistics files"
    if only:
        files = [f for f in files if year_of(f) == only]
    t0 = time.time(); from multiprocessing import Pool
    with Pool(min(workers, len(files))) as pool:
        res = pool.map(stats_worker, [str(f) for f in sorted(files, key=lambda p: -p.stat().st_size)], chunksize=1)
    res.sort(key=lambda r: (r["file"], r["job"])); sec = sum(r["secs"] for r in res); wall = time.time() - t0
    for r in res:
        print(f"  {r['job'][-10:]} {r['file'][:40]:<40} {r['rows_in']:>12,} rows -> kept {r['rows_kept']:>10,}  monotone={r['monotone']} stop={r['stopped_at_cutoff']}  {r['secs']:>6.1f}s", flush=True)
    lp = TEMP / "stats_log.json"; old = json.loads(lp.read_text(encoding="utf-8")) if lp.exists() else []
    old = [o for o in old if (o["file"], o["job"]) not in {(r["file"], r["job"]) for r in res}] + res; lp.write_text(json.dumps(old, indent=1), encoding="utf-8")
    print(f"[SPEED] sum(item time)/wall = {sec/wall:.2f}x on {min(workers, len(files))} workers ({100*sec/wall/min(workers, len(files)):.0f}%); {wall/60:.1f} min")


# ------------------------------------------------------------------------------------------ --build
def window_table(defs):
    """Per (id, year): the instruments the id carried, each with the start `w0` of its window (D520) -- as ES's builder."""
    d = defs.copy(); d["w0"] = d["ts_recv_first"].astype("int64"); d = d.sort_values(["iid", "year", "w0"])
    first = d.groupby(["iid", "year"])["w0"].transform("min"); d.loc[d["w0"] == first, "w0"] = 0
    return d


def assemble(defs, stats, cal, usable_session):
    """Per (usable session, option): the freshest OI and settlement publications usable that session -- ES's `assemble` without the bars."""
    dcols = ["iid", "year", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "expiration_ns", "underlying", "w0"]
    d = window_table(defs)[dcols].sort_values("w0")
    stats = pd.merge_asof(stats.sort_values("ts_event"), d, left_on="ts_event", right_on="w0", by=["iid", "year"], direction="backward"); stats = stats[stats["raw_symbol"].notna()]
    stats["usable"] = usable_session(stats["ts_event"].to_numpy(), cal); stats = stats[pd.notna(stats["usable"])]
    stats = filter_before(stats, "usable", RESERVED_FROM)                                   # vault layer 2
    keep = ["usable", "raw_symbol", "family", "right", "strike", "expiry_date", "expiry_hhmm", "expiration_ns", "underlying"]
    oi = stats[stats["stat_type"] == ST_OI].sort_values("ts_event").groupby(["usable", "raw_symbol"], as_index=False).last()[keep + ["quantity", "ts_event", "ts_ref"]].rename(columns={"quantity": "oi", "ts_event": "oi_ts_event", "ts_ref": "oi_ts_ref"})
    se = stats[stats["stat_type"] == ST_SETTLE].sort_values("ts_event").groupby(["usable", "raw_symbol"], as_index=False).last()[["usable", "raw_symbol", "price"]]; se["settle"] = np.round(se["price"] * PX, 6); se = se.drop(columns="price")
    t = oi.merge(se, on=["usable", "raw_symbol"], how="left").rename(columns={"usable": "session"})
    t = t[t["expiry_date"] >= t["session"]]                                                  # an option expired before the session carries no gamma
    t["oi_pub_et"] = pd.to_datetime(t["oi_ts_event"], utc=True).dt.tz_convert("US/Eastern").dt.strftime("%Y-%m-%dT%H:%M")
    t["oi_ref_session"] = t["oi_ts_ref"].to_numpy("int64").astype("datetime64[ns]").astype("datetime64[D]").astype(str)   # D616: ts_ref is midnight UTC on the business date
    return t.sort_values(["session", "expiry_date", "strike", "right"]).reset_index(drop=True)


def vault_check(t):
    """Vault layer 3: nothing at or after 2025-03-01 in any date the fixture carries. Raises ReservedSliceError."""
    assert_none_at_or_after(t, "session", RESERVED_FROM)
    assert_none_at_or_after(t, "oi_ref_session", RESERVED_FROM)
    assert_none_at_or_after(t["oi_pub_et"].astype(str).str.slice(0, 10).to_numpy(), None, RESERVED_FROM)
    return dict(last_session=str(t["session"].max()), last_oi_pub_et=str(t["oi_pub_et"].max()), reserved_from=RESERVED_FROM, passes=True)


def family_resolution(defs):
    """What each parent resolved to: expiry clock and weekday counts, first/last expiry, underlyings -- from the definitions."""
    u = defs.drop_duplicates(["iid", "raw_symbol", "year"]).copy(); wd = pd.to_datetime(u["expiry_date"]).dt.day_name().str.slice(0, 3); u["wd"] = wd
    out = {}
    for f, g in u.groupby("family"):
        out[f] = dict(options=int(len(g)), expiry_hhmm=g["expiry_hhmm"].value_counts().to_dict(), expiry_weekday=g["wd"].value_counts().to_dict(),
                      first_expiry=str(g["expiry_date"].min()), last_expiry_defined=str(g["expiry_date"].max()), underlying_roots=sorted(set(g["underlying"].str.slice(0, 2))))
    return out


def write_fixture(t):
    t = t[COLS].copy(); t["strike"] = t["strike"].round(4); t["settle"] = t["settle"].round(6)
    t.to_csv(OUT, index=False, compression={"method": "gzip", "mtime": 0}, float_format="%.10g", encoding="utf-8")


def cmd_build():
    OIB = _load("d497", "build_fut_open_interest.py"); cal = nq_calendar(); t0 = time.time()
    defs = load_cached("defs"); years = sorted({int(p.stem.split("_")[-1]) for p in TEMP.glob("stats_*.pkl")}); parts = []
    for y in years:
        st = load_cached("stats", y); ty = assemble(defs[defs["year"] == y], st, cal, OIB.usable_session); parts.append(ty); print(f"  {y}: {len(st):,} publications -> {len(ty):,} fixture rows", flush=True); del st
    t = pd.concat(parts, ignore_index=True).sort_values(["session", "expiry_date", "strike", "right"]).reset_index(drop=True)
    t = filter_before(t, "session", RESERVED_FROM); vault = vault_check(t)
    FIX.mkdir(parents=True, exist_ok=True); write_fixture(t)
    logs = {k: json.loads((TEMP / f"{k}_log.json").read_text(encoding="utf-8")) for k in ("defs", "stats") if (TEMP / f"{k}_log.json").exists()}
    META.write_text(json.dumps(dict(spec="NQ mirror of D581/D616 for the opening model's A4 (S-H) and Gate O0-H", builder="scripts/build_fut_nq_options_eod.py", built_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                                    rows=int(len(t)), sessions=int(t["session"].nunique()), first=str(t["session"].min()), last=str(t["session"].max()), columns=COLS,
                                    families=t["family"].value_counts().to_dict(), family_resolution=family_resolution(defs),
                                    inputs=dict(jobs=str(JOBS.relative_to(REPO)), raw_dir=str(RAW), statistics=[j.name for j in job_dirs()["statistics"]], definition=[j.name for j in job_dirs()["definition"]],
                                                files_read={k: [dict(job=r["job"], file=r["file"], rows_in=r["rows_in"], monotone=r["monotone"], stopped_at_cutoff=r["stopped_at_cutoff"]) for r in v] for k, v in logs.items()}),
                                    calendar="fut_index_sessions.csv.gz, root NQ, bars >= 380 (as ES's builder uses ES's), 2016-01-04 -> 2025-02-28",
                                    usable_rule="a publication is usable on the first NQ session whose 10:00 ET entry is strictly after its ts_event (D497/D521)",
                                    stat_types=dict(open_interest=ST_OI, settlement=ST_SETTLE), sentinels="UNDEF on both; settlement == 0.0 dropped (D526)",
                                    vol_to_1530="NOT BUILT: the NQ pull (statistics + definition) has no option bars, and A4 does not need it",
                                    oi_ref_session="D616: the NQ session the open interest DESCRIBES, from the kept publication's ts_ref (midnight UTC on the business date). The kept publication is the last by ts_event.",
                                    not_pulled="Q1A, Q4A and every Q5x family were not in the pull: Mondays of weeks 1, 4, 5 carry no same-day NQ expiry in this fixture (ES has E1A-E4A).",
                                    write="strike rounded to 4 dp, settle to 6 dp, written at %.10g (ES wrote %.6g, which would round a deep-ITM NQ settle); gzip mtime pinned",
                                    vault=vault, gates=None), indent=1), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}: {len(t):,} rows, {t['session'].nunique():,} sessions {t['session'].min()} .. {t['session'].max()}, families {t['family'].value_counts().to_dict()} in {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ gates (pure functions, each with a deliberate break in --selftest)
def black76_iv(price, F, K, tau, right):
    """Bisection on Black-76 (rate 0) -- ES's G6 routine, unchanged."""
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


def gate1(t):
    return dict(negative_oi=int((t["oi"] < 0).sum()), zero_or_negative_settle=int((t["settle"] <= 0).sum()), settle_missing=int(t["settle"].isna().sum()),
                share_settle_missing=float(t["settle"].isna().mean()), passes=bool((t["oi"] >= 0).all() and (t["settle"].dropna() > 0).all()))


def gate2(t):
    pub = pd.to_datetime(t["oi_pub_et"]); sess = pd.to_datetime(t["session"]); before = (pub < sess + pd.Timedelta(hours=10))
    return dict(rows=int(len(t)), published_before_entry=float(before.mean()), passes=bool(before.all()))


def gate3(t):
    """The expiry calendar: a same-day-expiring (PM, 16:00 or the early close) option on the sessions it should exist. NQ bar: Fridays
    >= 0.95 (QN1-QN4 run the whole span). Tue-Thu and the Monday share are REPORTED -- the Monday families are partial by pull (Q2A/Q3A only)."""
    z = t[(t["expiry_date"] == t["session"]) & (t["expiry_hhmm"] >= "12:00")]; s = set(z["session"])
    days = pd.to_datetime(pd.Series(sorted(t["session"].unique()))); wd = days.dt.dayofweek.to_numpy(); ds = days.dt.strftime("%Y-%m-%d").to_numpy()
    has0 = np.array([d in s for d in ds]); first = {f: str(t[t["family"] == f]["expiry_date"].min()) for f in sorted(t["family"].unique())}
    by_wd = {int(w): float(has0[wd == w].mean()) for w in range(5) if (wd == w).any()}
    by_wd_since2023 = {int(w): float(has0[(wd == w) & (ds >= "2023-01-01")].mean()) for w in range(5) if ((wd == w) & (ds >= "2023-01-01")).any()}
    fri = has0[wd == 4]
    # ES's own G3 counted ANY same-day expiry (the AM quarterly included); reported beside the PM criterion, which is the verdict.
    # The PM criterion was fixed before the first --gates run and is NOT relaxed after it: on its first run it failed at 0.947,
    # exactly on the 24 quarterly Fridays 2016-03 .. 2021-12 whose only same-day NQ expiry is the AM-settled quarterly.
    s_any = set(t.loc[t["expiry_date"] == t["session"], "session"]); any0 = np.array([d in s_any for d in ds])
    miss = [str(d) for d in ds[(wd == 4) & ~has0]]
    return dict(first_expiry_by_family=first, share_sessions_with_pm_0dte_by_weekday=by_wd, share_by_weekday_since_2023=by_wd_since2023,
                share_fridays_with_0dte=float(fri.mean()) if len(fri) else 0.0, fridays_without_pm_0dte=miss,
                es_definition_any_same_day_expiry_fridays=float(any0[wd == 4].mean()) if len(fri) else 0.0,
                passes=bool(len(fri) and fri.mean() >= 0.95))


def gate4(t):
    ns = t[t["oi"] > 0].groupby("session")["strike"].nunique()
    return dict(median_strikes_with_oi=float(ns.median()), sessions_under_20=[(d, int(n)) for d, n in ns[ns < G3_MIN_STRIKES].items()][:40], n_under_20=int((ns < G3_MIN_STRIKES).sum()),
                passes=bool((ns < G3_MIN_STRIKES).sum() <= 5))


def gate5_compare(mine, piv):
    return bool(all(abs(mine.get(f, 0) - piv.get(f, 0)) < 1e-9 for f in set(mine) | set(piv)))


def gate5_second_path(d, st, df, cal, usable_session):
    """The per-family OI sum on session `d` recomputed from the raw statistics cache by bisection on each id's own definition times (never merge_asof)."""
    yr = int(d[:4]); st = st[st["stat_type"] == ST_OI].copy(); st["usable"] = usable_session(st["ts_event"].to_numpy(), cal); st = st[st["usable"] == d]
    dd = window_table(df.assign(year=yr)).sort_values(["iid", "w0"]); win = {i: (g["w0"].to_list(), g[["raw_symbol", "family", "expiry_date"]].to_dict("records")) for i, g in dd.groupby("iid")}
    lab = []
    for r in st.itertuples():
        ts, recs = win.get(r.iid, ([], [])); k = bisect.bisect_right(ts, r.ts_event) - 1; lab.append(recs[k] if k >= 0 else {"raw_symbol": None, "family": None, "expiry_date": None})
    st = pd.concat([st.reset_index(drop=True), pd.DataFrame(lab, columns=["raw_symbol", "family", "expiry_date"])], axis=1); st = st[st["raw_symbol"].notna() & (st["expiry_date"] >= d)]
    return st.sort_values("ts_event").groupby("raw_symbol").last().groupby("family")["quantity"].sum().to_dict()


def gate6(inverts):
    return dict(near_money_rows_tried=int(len(inverts)), share_inverting=float(np.mean(inverts)) if len(inverts) else None, passes=bool(len(inverts) and np.mean(inverts) >= 0.99))


def gate7_reference_session(t, cal):
    """ES's G7 (D616) on the NQ calendar: the reference session is recoverable, before the session it is used on, and one session back."""
    posn = {d: i for i, d in enumerate(list(cal))}
    ref = t["oi_ref_session"].astype(str); sess = t["session"].astype(str)
    ri = ref.map(posn).to_numpy(dtype="float64"); si = sess.map(posn).to_numpy(dtype="float64")
    gap = si - ri; fin = np.isfinite(gap)
    hist = {str(int(g)): int(n) for g, n in zip(*np.unique(gap[fin], return_counts=True))}
    at_or_after = float((ref.to_numpy() >= sess.to_numpy()).mean())
    u = t[["raw_symbol", "session", "oi_ref_session"]].sort_values(["raw_symbol", "session"], kind="stable").reset_index(drop=True)
    sym = u["raw_symbol"].to_numpy(); same = sym[1:] == sym[:-1]
    us = u["session"].astype(str).map(posn).to_numpy(dtype="float64"); ur = u["oi_ref_session"].astype(str).map(posn).to_numpy(dtype="float64")
    ds = us[1:] - us[:-1]; dr = ur[1:] - ur[:-1]; pairs = same & (ds == 1)
    span1 = float(np.mean(dr[pairs] == 1)) if pairs.any() else None
    span0 = float(np.mean(dr[pairs] == 0)) if pairs.any() else None
    yr = sess.str.slice(0, 4).to_numpy(); by_year = {}
    for y in sorted(set(yr)):
        m = yr == y
        by_year[y] = dict(rows=int(m.sum()), share_gap_one=float(np.mean(gap[m & fin] == 1)) if (m & fin).any() else None, share_unrecoverable=float(np.mean(~fin[m])))
    out = dict(rows=int(len(t)), share_reference_is_an_nq_session=float(fin.mean()), gap_sessions_histogram=hist, share_gap_exactly_one=float(np.mean(gap[fin] == 1)) if fin.any() else 0.0,
               share_reference_at_or_after_session=at_or_after, adjacent_pairs=int(pairs.sum()), share_pair_reference_span_one=span1, share_pair_reference_span_zero_a_revision=span0, by_year=by_year)
    out["passes"] = bool(out["share_reference_is_an_nq_session"] >= 0.95 and at_or_after <= 0.01 and out["share_gap_exactly_one"] >= 0.95)
    return out


def gate_o0h(t, days, label):
    """Gate O0-H: the share of `days` with at least one option row with oi > 0 and a finite positive settle (on the same row), >= 90 %."""
    ok = t[(t["oi"] > 0) & np.isfinite(t["settle"]) & (t["settle"] > 0)]["session"].unique()
    days = pd.Index(sorted(days)); hit = days.isin(ok); yr = days.str.slice(0, 4)
    per_year = {y: dict(sessions=int((yr == y).sum()), share=float(hit[yr == y].mean())) for y in sorted(set(yr))}
    missing = list(days[~hit])
    return dict(denominator=label, sessions=int(len(days)), with_oi_and_settle=int(hit.sum()), share=float(hit.mean()) if len(days) else 0.0, per_year=per_year,
                n_missing=len(missing), missing_first_40=missing[:40], bar=O0H_BAR, passes=bool(len(days) and hit.mean() >= O0H_BAR))


def families_by_year(t):
    y = t["session"].str.slice(0, 4); return {yy: sorted(g.unique().tolist()) for yy, g in t.groupby(y)["family"]}


def spot_check_es(t, sessions=SPOT_SESSIONS):
    """Total NQ option OI against the ES fixture's ES option OI on fixed sessions -- an order-of-magnitude sanity comparison, not a gate."""
    es = []
    for ch in pd.read_csv(ES_FIX, usecols=["session", "family", "oi"], dtype={"session": str, "family": str}, encoding="utf-8", chunksize=4_000_000):
        es.append(ch[ch["session"].isin(sessions)])
    es = pd.concat(es); out = []
    for d in sessions:
        n = t[t["session"] == d]; e = es[es["session"] == d]
        out.append(dict(session=d, nq_total_oi=int(n["oi"].sum()), es_total_oi=int(e["oi"].sum()), ratio_nq_over_es=float(n["oi"].sum() / e["oi"].sum()) if e["oi"].sum() else None,
                        nq_quarterly_oi=int(n.loc[n["family"] == "NQ", "oi"].sum()), es_quarterly_oi=int(e.loc[e["family"] == "ES", "oi"].sum()), nq_rows=int(len(n)), es_rows=int(len(e))))
    return out


def opening_usable_sessions():
    """The opening model's own usable sessions (A6.9: NYSE days from SPY's daily file, minus ES half days) -- the denominator ES's 99.7 % used."""
    g0 = _load("opening_gate0", "opening_gate0.py"); use, _ = g0.usable_sessions(MAIN / "data")
    return filter_before(np.array(use), None, RESERVED_FROM)


def cmd_gates(log=print):
    meta = json.loads(META.read_text(encoding="utf-8")); t0 = time.time()
    t = pd.read_csv(OUT, dtype={"session": str, "raw_symbol": str, "family": str, "right": str, "expiry_date": str, "expiry_hhmm": str, "underlying": str, "oi_pub_et": str, "oi_ref_session": str}, encoding="utf-8")
    t = filter_before(t, "session", RESERVED_FROM); out = {}; ok = True
    out["VAULT"] = vault_check(t)
    out["G1"] = gate1(t); out["G2"] = gate2(t); out["G3"] = gate3(t); out["G4"] = gate4(t)
    OIB = _load("d497", "build_fut_open_interest.py"); cal = nq_calendar(); rng = np.random.default_rng(581); pick = sorted(rng.choice(sorted(t["session"].unique()), 10, replace=False)); checks = []; _yc = {}
    for d in pick:
        yr = int(d[:4])
        if yr not in _yc:                                                                    # one load per year, not per session (the first run reloaded ~1 GB per pick)
            _yc.clear(); _yc[yr] = (load_cached("stats", yr), load_cached("defs", yr))
        piv = gate5_second_path(d, _yc[yr][0], _yc[yr][1], cal, OIB.usable_session)
        mine = t[t["session"] == d].groupby("family")["oi"].sum().to_dict(); agree = gate5_compare(mine, piv); checks.append(dict(session=d, agree=agree))
        if not agree:
            log(f"    G5 {d}: fixture {mine} vs second path {piv}")
    out["G5"] = dict(sessions=checks, passes=bool(all(c["agree"] for c in checks)))
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8"); strip = strip[strip["root"] == "NQ"]
    calx = list(cal); inv = []
    for d in pick[:5]:
        i = calx.index(d); prev = calx[i - 1]; u = t[(t["session"] == d) & t["settle"].notna()].copy(); f = strip[strip["ref"] == prev].set_index("contract")["settle"]
        u["F"] = u["underlying"].map(f); u = u[u["F"].notna()]; u = u[(u["strike"] / u["F"] - 1).abs() < G6_MONEYNESS]
        for r in u.itertuples():
            n_ahead = max(calx.index(r.expiry_date) - i, 0) if r.expiry_date in calx else 0; tau = (n_ahead * 6.5 + 6.5) / (252 * 6.5)
            inv.append(bool(np.isfinite(black76_iv(r.settle, r.F, r.strike, tau, r.right))))
    out["G6"] = gate6(inv)
    out["G7"] = gate7_reference_session(t, cal)
    days_all = nq_calendar(all_days=True); days_380 = cal; days_open = opening_usable_sessions()
    out["O0_H"] = gate_o0h(t, days_all, "fut_index_sessions NQ days, all, 2016-01-04 -> 2025-02-28 (the brief's denominator)")
    out["O0_H_alt"] = dict(nq_calendar_bars_ge_380=gate_o0h(t, days_380, "NQ days with >= 380 bars (the build calendar)"),
                           opening_model_usable_sessions=gate_o0h(t, days_open, "opening_gate0.usable_sessions: NYSE days minus ES half days (ES's 99.7 % denominator)"))
    for k in ("G1", "G2", "G3", "G4", "G5", "G6", "G7", "O0_H"):
        ok &= out[k]["passes"]
    out["reports"] = dict(rows=int(len(t)), sessions=int(t["session"].nunique()), families_by_year=families_by_year(t), share_rows_settle_missing=float(t["settle"].isna().mean()),
                          spot_check_vs_es=spot_check_es(t))
    meta["gates"] = out; meta["all_gates_pass"] = bool(ok); meta["gates_runtime_min"] = round((time.time() - t0) / 60, 2); META.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    P = lambda b: "PASS" if b else "FAIL"
    log(f"VAULT last session {out['VAULT']['last_session']}, last publication {out['VAULT']['last_oi_pub_et']} PASS")
    log(f"G1 negative OI {out['G1']['negative_oi']}, non-positive settle {out['G1']['zero_or_negative_settle']}, settle missing {out['G1']['settle_missing']} ({out['G1']['share_settle_missing']:.4f}) {P(out['G1']['passes'])}")
    log(f"G2 OI published before the session's entry on {out['G2']['published_before_entry']:.4f} of rows {P(out['G2']['passes'])}")
    log(f"G3 first expiry by family {out['G3']['first_expiry_by_family']}; PM 0DTE share by weekday {out['G3']['share_sessions_with_pm_0dte_by_weekday']}; since 2023 {out['G3']['share_by_weekday_since_2023']}; Fridays {out['G3']['share_fridays_with_0dte']:.3f} {P(out['G3']['passes'])}")
    log(f"G4 median strikes with OI {out['G4']['median_strikes_with_oi']:.0f}; sessions under 20: {out['G4']['n_under_20']} {P(out['G4']['passes'])}")
    log(f"G5 second-path OI sums agree on {sum(c['agree'] for c in checks)}/10 sessions {P(out['G5']['passes'])}")
    log(f"G6 near-the-money settlement IV inverts on {out['G6']['share_inverting']} of {out['G6']['near_money_rows_tried']} {P(out['G6']['passes'])}")
    g7 = out["G7"]; log(f"G7 reference recoverable {g7['share_reference_is_an_nq_session']:.4f}, one back {g7['share_gap_exactly_one']:.4f}, at/after {g7['share_reference_at_or_after_session']:.4f}; pair span one {g7['share_pair_reference_span_one']}, zero {g7['share_pair_reference_span_zero_a_revision']} {P(g7['passes'])}")
    for k, g in [("O0-H", out["O0_H"])] + [(f"O0-H[{k2}]", v) for k2, v in out["O0_H_alt"].items()]:
        log(f"{k} {g['with_oi_and_settle']}/{g['sessions']} = {g['share']:.4f} (bar {O0H_BAR}) {P(g['passes'])}; per year {{{', '.join(f'{y}: {v['share']:.3f}' for y, v in g['per_year'].items())}}}")
    log(f"reports: rows {len(t):,}; settle missing {out['reports']['share_rows_settle_missing']:.4f}; spot check {out['reports']['spot_check_vs_es']}")
    log(f"ALL GATES {P(ok)}; wrote {META.relative_to(REPO)} in {(time.time()-t0)/60:.1f} min"); return ok


# ------------------------------------------------------------------------------------------ --selftest
def cmd_selftest():
    assert OPTION.match("NQZ5 C21000") and OPTION.match("QN1G6 C8200") and OPTION.match("Q2BZ5 P18500") and OPTION.match("QNEJ6 P4500") and OPTION.match("Q3AH3 C12000")
    assert not OPTION.match("NQZ5") and not OPTION.match("ESZ5 C6000") and not OPTION.match("UD:2V: 12 0103854105") and not OPTION.match("MNQZ5 C21000")
    assert OPTION.match("Q3DZ5 C6975").group(1) == "Q3D" and OPTION.match("QN3Z5 C7035").group(1) == "QN3" and OPTION.match("NQH3 C12000").group(1) == "NQ"
    assert in_scope([Path("x/glbx-mdp3-20250101-20251231.statistics.dbn.zst"), Path("x/glbx-mdp3-20260101-20260926.statistics.dbn.zst")]) == [Path("x/glbx-mdp3-20250101-20251231.statistics.dbn.zst")]
    cal = np.array(["2023-03-01", "2023-03-02", "2023-03-03"])
    def ns(s):
        return int(pd.Timestamp(s, tz="US/Eastern").value)
    def refns(d):
        return int(pd.Timestamp(d, tz="UTC").value)
    defs = pd.DataFrame([dict(iid=1, raw_symbol="Q1CH3 C12000", family="Q1C", right="C", strike=12000.0, expiry_date="2023-03-01", expiry_hhmm="16:00", expiration_ns=ns("2023-03-01T16:00"), underlying="NQH3", ts_recv=ns("2023-03-01T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023),
                         dict(iid=2, raw_symbol="QN1H3 P11900", family="QN1", right="P", strike=11900.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="NQH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023),
                         dict(iid=1, raw_symbol="Q1CH3 C12100", family="Q1C", right="C", strike=12100.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="NQH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-03-02T00:30"), year=2023),
                         dict(iid=3, raw_symbol="QN1H3 P11800", family="QN1", right="P", strike=11800.0, expiry_date="2023-03-03", expiry_hhmm="16:00", expiration_ns=ns("2023-03-03T16:00"), underlying="NQH3", ts_recv=ns("2023-03-03T23:00"), ts_recv_first=ns("2023-02-28T23:00"), year=2023)])
    stats = pd.DataFrame([dict(iid=1, stat_type=ST_OI, ts_event=ns("2023-02-28T21:00"), ts_ref=refns("2023-02-28"), quantity=100, price=0, year=2023),
                          dict(iid=2, stat_type=ST_OI, ts_event=ns("2023-02-28T21:00"), ts_ref=refns("2023-02-28"), quantity=50, price=0, year=2023),
                          dict(iid=2, stat_type=ST_SETTLE, ts_event=ns("2023-02-28T17:00"), ts_ref=refns("2023-02-28"), quantity=0, price=int(round(12345.75 / PX)), year=2023),
                          dict(iid=2, stat_type=ST_OI, ts_event=ns("2023-03-01T21:00"), ts_ref=refns("2023-03-01"), quantity=70, price=0, year=2023),
                          dict(iid=1, stat_type=ST_OI, ts_event=ns("2023-03-02T21:00"), ts_ref=refns("2023-03-02"), quantity=33, price=0, year=2023),
                          dict(iid=3, stat_type=ST_OI, ts_event=ns("2023-03-01T21:00"), ts_ref=refns("2023-03-01"), quantity=10, price=0, year=2023),
                          dict(iid=3, stat_type=ST_OI, ts_event=ns("2023-03-01T22:00"), ts_ref=refns("2023-02-28"), quantity=11, price=0, year=2023)])
    OIB = _load("d497", "build_fut_open_interest.py"); t = assemble(defs, stats, cal, OIB.usable_session)
    r1 = t[(t["session"] == "2023-03-01") & (t["raw_symbol"] == "Q1CH3 C12000")].iloc[0]; assert r1["oi"] == 100 and r1["oi_ref_session"] == "2023-02-28", r1.to_dict()
    r2 = t[(t["session"] == "2023-03-01") & (t["raw_symbol"] == "QN1H3 P11900")].iloc[0]; assert r2["oi"] == 50 and abs(r2["settle"] - 12345.75) < 1e-9, r2.to_dict()
    r3 = t[(t["session"] == "2023-03-02") & (t["raw_symbol"] == "QN1H3 P11900")].iloc[0]; assert r3["oi"] == 70 and r3["oi_ref_session"] == "2023-03-01"
    assert not ((t["session"] == "2023-03-02") & (t["raw_symbol"] == "Q1CH3 C12000")).any(), "an option expired before the session must be dropped"
    r4 = t[(t["session"] == "2023-03-03") & (t["raw_symbol"] == "Q1CH3 C12100")]; assert len(r4) == 1 and r4.iloc[0]["oi"] == 33, "the reissued id carries its second instrument"
    rev = t[(t["session"] == "2023-03-02") & (t["raw_symbol"] == "QN1H3 P11800")].iloc[0]; assert rev["oi"] == 11 and rev["oi_ref_session"] == "2023-02-28"
    # the write keeps an NQ-sized settle exactly (ES's %.6g would give 12345.8)
    import io
    buf = io.StringIO(); t[COLS].assign(strike=t["strike"].round(4), settle=t["settle"].round(6)).to_csv(buf, index=False, float_format="%.10g"); back = pd.read_csv(io.StringIO(buf.getvalue()))
    assert (back["settle"].dropna() == 12345.75).all() and len(back["settle"].dropna()) == 1, back["settle"].tolist()
    assert f"{12345.75:.6g}" == "12345.8", "the ES write format would lose this settle -- the reason for %.10g"
    # ---- the vault: layer 2 drops a later session; layer 3 RAISES on one ----
    cal2 = np.array(["2025-02-27", "2025-02-28", "2025-03-03"]); late = stats.copy().iloc[:2]; late["ts_event"] = [ns("2025-02-27T21:00"), ns("2025-02-28T21:00")]
    d2 = defs.iloc[[0, 1]].copy(); d2["year"] = 2025; d2["expiry_date"] = "2025-03-21"; late["year"] = 2025; t2 = assemble(d2, late, cal2, OIB.usable_session)
    assert set(t2["session"]) == {"2025-02-28"}, f"a publication usable on 2025-03-03 must be dropped by layer 2: {sorted(set(t2['session']))}"
    vault_check(t2)
    try:
        bad = t2.copy(); bad.loc[bad.index[0], "session"] = "2025-03-03"; vault_check(bad); raise AssertionError("vault layer 3 did not raise")
    except ReservedSliceError:
        pass
    try:
        bad = t2.copy(); bad.loc[bad.index[0], "oi_pub_et"] = "2025-03-01T00:05"; vault_check(bad); raise AssertionError("vault layer 3 did not raise on the publication date")
    except ReservedSliceError:
        pass
    mono = _Monotone(); assert not mono.step(np.array([1, 2, 3])) and mono.ok; assert mono.step(np.array([CUTOFF_NS, CUTOFF_NS + 1])); m2 = _Monotone(); m2.step(np.array([5, 4])); assert not m2.ok and not m2.step(np.array([CUTOFF_NS + 9])), "no early stop once a file is not monotone"
    # ---- every gate: passes clean, FAILS on a deliberate break of the quantity it reads ----
    g = pd.DataFrame(dict(session=["2023-03-02", "2023-03-03"], raw_symbol=["A", "A"], family=["QN1", "QN1"], right=["C", "C"], strike=[1.0, 1.0], expiry_date=["2023-03-03", "2023-03-03"],
                          expiry_hhmm=["16:00", "16:00"], underlying=["NQH3", "NQH3"], oi=[5, 6], settle=[1.0, 2.0], oi_pub_et=["2023-03-01T21:00", "2023-03-02T21:00"], oi_ref_session=["2023-03-01", "2023-03-02"]))
    assert gate1(g)["passes"]; b = g.copy(); b.loc[0, "oi"] = -1; assert not gate1(b)["passes"]; b = g.copy(); b.loc[0, "settle"] = 0.0; assert not gate1(b)["passes"]
    assert gate2(g)["passes"]; b = g.copy(); b.loc[1, "oi_pub_et"] = "2023-03-03T10:00"; assert not gate2(b)["passes"]
    assert gate3(g)["passes"]; b = g.copy(); b["expiry_date"] = "2023-03-10"; assert not gate3(b)["passes"]; b = g.copy(); b["expiry_hhmm"] = "09:30"; assert not gate3(b)["passes"], "an AM-settled quarterly is not a PM 0DTE"
    wide = pd.concat([g.assign(strike=float(k)) for k in range(25)], ignore_index=True); assert gate4(wide)["passes"]
    thin = pd.concat([wide.assign(session=f"2023-01-{d:02d}") for d in range(1, 7)] + [wide.iloc[:0]], ignore_index=True); thin = thin[thin["strike"] < 10]; assert not gate4(thin)["passes"]
    assert gate5_compare({"QN1": 11}, {"QN1": 11}) and not gate5_compare({"QN1": 11}, {"QN1": 12}) and not gate5_compare({"QN1": 11}, {"QN1": 11, "NQ": 1})
    iv = black76_iv(250.0, 12000.0, 12000.0, 5 / 252, "C"); assert np.isfinite(iv) and 0.05 < iv < 1.0, iv
    assert gate6([True] * 100)["passes"] and not gate6([True] * 98 + [False, False])["passes"] and not gate6([])["passes"]
    assert not np.isfinite(black76_iv(13000.0, 12000.0, 12000.0, 5 / 252, "C")), "a call priced above the forward cannot invert"
    cal3 = np.array(["2023-03-01", "2023-03-02", "2023-03-03"]); assert gate7_reference_session(g, cal3)["passes"]
    b = g.copy(); b.loc[0, "oi_ref_session"] = "2023-03-02"; assert not gate7_reference_session(b, cal3)["passes"]
    b = g.copy(); b.loc[1, "oi_ref_session"] = "2023-03-01"; assert gate7_reference_session(b, cal3)["share_pair_reference_span_zero_a_revision"] == 1.0
    days = [f"2023-03-{d:02d}" for d in range(1, 11)]; full = pd.concat([g.iloc[[0]].assign(session=d) for d in days], ignore_index=True)
    assert gate_o0h(full, days, "t")["share"] == 1.0 and gate_o0h(full, days, "t")["passes"]
    b = full.copy(); b.loc[b.index[:2], "settle"] = np.nan; assert gate_o0h(b, days, "t")["share"] == 0.8 and not gate_o0h(b, days, "t")["passes"], "missing settles must cost O0-H"
    b = full.copy(); b.loc[b.index[:2], "oi"] = 0; assert not gate_o0h(b, days, "t")["passes"], "zero OI must cost O0-H"
    b = full.copy(); b.loc[0, "oi"] = 0; b.loc[1, "settle"] = np.nan; b = pd.concat([b, full.iloc[[0]].assign(settle=np.nan), full.iloc[[1]].assign(oi=0)], ignore_index=True)
    assert gate_o0h(b, days, "t")["with_oi_and_settle"] == 8, "oi and settle must hold on the SAME row"
    print(f"selftest: symbology (NQ, QN1-4, QNE, Q[1-5][A-D]; ES and UD spreads refused), file-scope vault, usable-session keying (21:00 ET T-1 -> T), expiry drop, "
          f"windowed id reissue, the D616 reference session and revision trap, the %.10g write, vault layers 2 and 3 (RAISES on a late session and a late publication), "
          f"the monotone early stop, and G1-G7 + O0-H each passing clean and FAILING on its deliberate break (iv {iv:.3f}) -- all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True)
    for f in ("defs", "stats", "build", "gates", "selftest"):
        g.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--workers", type=int, default=6); ap.add_argument("--only", type=int, default=None); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    elif a.defs:
        cmd_defs(a.workers)
    elif a.stats:
        cmd_stats(a.workers, a.only)
    elif a.build:
        cmd_build()
    else:
        sys.exit(0 if cmd_gates() else 1)
