"""D348 prep -- a cached, drop-in replacement for D347's prep() in scripts/run_d347_long_signal_controls.py.

    uv run python scripts/d348_prep.py --build [--force] [--rss]     populate temp/d348_prep/<key>/
    uv run python scripts/d348_prep.py --verify [--rss]              D347's own prep() vs this module's cached prep(): every key bit-identical
    uv run python scripts/d348_prep.py --time [--rss]                time a cache HIT

In a runner:

    PREP = _load("d348p", "d348_prep.py")     # executes D347's whole alias chain ONCE -- do NOT _load run_d347_* again in the
    V47 = PREP.V47                            # same process; take D347 and every alias from here: PREP.V45 .EB .W .Y .UF .FL .D .M .R ...
    P = PREP.prep(need_grids=True)            # HIT: the dict below in ~2 s of load; BUILD: D347's prep re-derived and written

What prep() returns -- EVERY key D347's prep() returns, with the same value (bit-identical arrays, == scalars):

    A, A3, r1T, finT, ocT, m_f, m_f_oc, keep, elig, base, z, n, T, panel, HALF, CLOSE, RAW_CLOSE, DV, years, down_years,
    yr_ret, LAG, PCT, EVENTS, beta, F, bucket_rsi, excl, t0, m_start

plus what D346-style slot runners need:

    A2        FL.with_open_fill(A, panel, g)'s dict == dict(A, ocT=ocT, mkt_oc=mkt_oc) with the PANEL-WIDE mkt_oc (D345/D346's
              kernel input). D347's A3 is NOT this: A3 = dict(A2, r1T, finT, vxT, mkt=m_f, mkt_oc=m_f_oc) carries the FLOORED
              hedge. Both are returned under their own names.
    G4        {cv: (HALF[cv], CLOSE, DV, finT) for cv in ("PB", "PUB")} as run_d346_legs_floor_open.py builds it
    mkt       np.asarray(A["mkt"]), the panel-wide close-to-close market (D347 computes it and does not return it)
    mkt_oc    the panel-wide open-to-close market from FL.with_open_fill
    VOL, RAW, live, first_live, last_live, fbmask, FBREP, symbols, dates
    z_path    Path of the D290 score cache;  score(sig) -> z[sig] read lazily from that npz (per-array; nothing else is held)
    cache_key, cache_hit

What is cached (temp/d348_prep/<key>/<name>.npy, one file per array; scalars/lists/dicts in meta.json):
    ocT mkt_oc m_f m_f_oc keep elig base live HALF_PB HALF_PUB CLOSE VOL RAW RAW_CLOSE DV years first_live last_live excl
    LAG_{hist_L,rev_21,rsi} PCT_{hist_L,rev_21,rsi} EV_{sig}_lo EV_{sig}_hi (4 signals) beta F bucket_rsi fbmask
What is re-derived on a HIT (already a cache, or a handle):
    A        D.build_cache(verbose=False); D.load_cache(mmap=True)       -- the D303 cache, mmapped
    r1T finT mkt vxT   np.asarray(A[...]) exactly as D347 does
    A2 A3    rebuilt as dicts from A and the cached ocT / mkt_oc / m_f / m_f_oc
    z        np.load(R.BC.CACHE) -- an NpzFile handle (reads the zip directory only); score(sig) reads one member
    EVENTS   (EV_lo, EV_hi, score_T) with score_T the SAME object as LAG["rsi"] / PCT[...] as in D347
    panel    None on a HIT.  The RaggedPanel is not cacheable; on a BUILD it is the live object.  D347 reads P["panel"] in ONE
             place: stage_selftest uses P["panel"].live.T to rebuild the panel-wide mkt_oc -- use P["live"] (cached, (n, T) bool)
             or P["mkt_oc"] (the FL value itself) instead.  P["symbols"] and P["dates"] replace panel.symbols / panel.dates.
    t0       time.time() at the start of THIS prep() call (a timestamp; never compared)

Cache key: sha1[:16] over fixture and events file (path:size:int(mtime)), R.BC.cache_key(M.B.FIXTURE), D.cache_key(), and
name:size:int(mtime) of ragged_panel.py d280_forecast_precheck.py d285_spread_estimate.py run_d320_tilt_filters.py
run_d331_deal_filter.py d339_census.py d339_universe_floor.py d340_fill.py d337_borrow.py run_d347_long_signal_controls.py
and this file.  Prints `[K] d348_prep cache HIT <key>` or `BUILD <key>`.

Assertions: [K] runs live on both paths (it reads one small member of the npz).  [F0] [R] [H] run on a BUILD as part of
building; on a HIT their asserted quantities (n_ok, pct_f0, floor share, factor==census, m_start) are re-read from meta.json and
re-asserted against V35.EXPECT_*, the D343 json and the cached hedge, so the runner still prints all four lines.

Arrays >= MMAP_MIN bytes are loaded with mmap_mode="r" on a HIT (read-only: an in-place write raises, which is the loud
failure; pass mmap=False to prep() for writable copies).  Smaller ones are loaded fully.

Measured (Windows 11, 16 cores, 31.7 GB; panel (T, n) = (4187, 1573); cache 943 MB in 38 files):
    import of the D347 alias chain      WITHOUT memo_load: 164 s alone, 460 s with six processes competing, 5-7.5 GB resident --
                                        the chain's own `_load`s re-executing leaf modules (d285_spread_estimate.py 151x,
                                        d290_build_cache.py and run_mine_neutral.py 54x).  This is what exhausted a 32 GB
                                        machine on the first launch of D348-D350.
                                        WITH memo_load (installed above, before the first _load): 0.2 s, 59 scripts executed
                                        once, 63 re-executions skipped; a HIT process is ~1.4-2.0 GB resident.
    BUILD                               43 s after the import (D347's prep is 71 s in the same process); peak working set 4.3 GB
                                        under memo_load (12.4 GB without).
    HIT                                 0.2 s warm; ~7 s when the 2.7 GB npz is cold -- 6.85 s is the first open of the score
                                        cache for [K] (D347's prep pays the same).
    --verify                            124 s after the import (D347 prep 71 s + HIT 0.2 s + one panel reload for the A2 check).
                                        Exit 0 on 2026-09-06 without memo_load: 30/30 keys OK, 11/11 extras OK.  The cache
                                        built WITH memo_load was then compared file by file to the one built without it:
                                        38/38 bit-identical (temp/cmp_caches.py), and D348's [ID] reproduces D346/D343 to 0.0
                                        under it.
    NOTE the key includes this file's mtime: editing it (even the docstring) forces one rebuild.  Run --build once before
    launching concurrent stages so that no two processes build the same key at once.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np

_T_IMPORT = time.time()
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import memo_load                                   # noqa: E402  -- each chain script executes ONCE per process
memo_load.install()                                # must precede the first _load(); see memo_load.py


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V47 = _load("d347r", "run_d347_long_signal_controls.py")       # main guarded; every alias
V45, V35, V31, PA, V9 = V47.V45, V47.V35, V47.V31, V47.PA, V47.V9
V6, Y, W, D, M, SP, R, X = V47.V6, V47.Y, V47.W, V47.D, V47.M, V47.SP, V47.R, V47.X
G22, BR, V38, CEN, UF, FL, EB = V47.G22, V47.BR, V47.V38, V47.CEN, V47.UF, V47.FL, V47.EB
IMPORT_S = time.time() - _T_IMPORT

CACHE_DIR = REPO / "temp" / "d348_prep"
KEYED_SCRIPTS = ("ragged_panel.py", "d280_forecast_precheck.py", "d285_spread_estimate.py", "run_d320_tilt_filters.py",
                 "run_d331_deal_filter.py", "d339_census.py", "d339_universe_floor.py", "d340_fill.py", "d337_borrow.py",
                 "run_d347_long_signal_controls.py", "d348_prep.py")
SIGNALS, SCORE_OF, CONVS = V47.SIGNALS, V47.SCORE_OF, V47.CONVS
LAG_SIGS = ("hist_L", "rev_21", "rsi")
MMAP_MIN = 1 << 20
ARRAY_KEYS = (("ocT", "mkt_oc", "m_f", "m_f_oc", "keep", "elig", "base", "live", "HALF_PB", "HALF_PUB", "CLOSE", "VOL", "RAW",
               "RAW_CLOSE", "DV", "years", "first_live", "last_live", "excl", "beta", "F", "bucket_rsi", "fbmask")
              + tuple(f"LAG_{s}" for s in LAG_SIGS) + tuple(f"PCT_{s}" for s in LAG_SIGS)
              + tuple(f"EV_{s}_{w}" for s in SIGNALS for w in ("lo", "hi")))


# ------------------------------------------------------------------ key / memory
def cache_key() -> str:
    h = hashlib.sha1()
    for p in (M.B.FIXTURE, M.B.EVENTS):
        p = Path(p)
        st = p.stat()
        h.update(f"{p}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(R.BC.cache_key(M.B.FIXTURE).encode())
    h.update(D.cache_key().encode())
    for f in KEYED_SCRIPTS:
        st = (REPO / "scripts" / f).stat()
        h.update(f"{f}:{st.st_size}:{int(st.st_mtime)}".encode())
    return h.hexdigest()[:16]


def rss_line() -> str:
    try:
        import psutil
        mi = psutil.Process().memory_info()
        peak = getattr(mi, "peak_wset", None)
        s = f"rss {mi.rss / 2**20:,.0f} MB"
        return s + (f", peak working set {peak / 2**20:,.0f} MB" if peak else "")
    except ImportError:
        try:
            import resource
            return f"peak rss {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024:,.0f} MB"
        except ImportError:
            return "rss unavailable (no psutil, no resource)"


# ------------------------------------------------------------------ the shared assertions
def _assert_K():
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists() and cache.stat().st_mtime > rp.stat().st_mtime, "[K]"
    assert str(np.load(cache, allow_pickle=False)["key"]) == R.BC.cache_key(M.B.FIXTURE), "[K] key"
    print("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")


# Fixture-aware expectations. None => the MINING constants, cross-checked against D335's filing count and D343's
# stored floor share -- independent prior records, so on the mining fixture these are real checks.
#
# A caller re-pointed at another fixture sets EXPECT to that fixture's own universe constants. Those come from
# the counts-only --dry stage, which reads no return, so they are facts about how the UNIVERSE was built, never
# about how the strategy performed. But there is no prior record to cross-check them against, so on another
# fixture these assertions are a REGRESSION LOCK -- they pin the numbers so a later change is caught -- and NOT
# an independent verification. Stated here rather than left for a reader to assume.
EXPECT = None


def _assert_F0(n_ok, pct_f0):
    want_n = V35.EXPECT_APPLIED if EXPECT is None else EXPECT["f0_applied"]
    want_p = V35.EXPECT_PCT if EXPECT is None else EXPECT["f0_pct"]
    assert n_ok == want_n and abs(pct_f0 - want_p) < 0.02, f"[F0] {n_ok} / {pct_f0:.3f}% (want {want_n} / {want_p})"
    print(f"    [F0] F0 MASK: {n_ok:,} filings applied, {pct_f0:.2f}% of live name-bars excluded"
          + ("" if EXPECT is None else f"  [{EXPECT['tag']}: regression lock, not an independent check]"))


def _assert_R(factor_equal, share, el):
    # Mining compares to D343's STORED full-precision share, so 1e-9 is the right bar. A re-pointed fixture's
    # expectation is transcribed from its own --dry printout at six decimals, so the lock is held to the
    # precision actually recorded -- demanding 1e-9 of a 6-dp constant fails on the digits it never had.
    want = (float(json.loads(V47.D343_JSON.read_text())["floor"]["v2_share_live_fail"])
            if EXPECT is None else EXPECT["floor_share"])
    tol = 1e-9 if EXPECT is None else 1e-6
    assert factor_equal, "[R] factor"
    assert abs(share - want) < tol, f"[R] keep_v2 share {share} != {want} (tol {tol:g})"
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor; keep_v2 fails {100 * share:.4f}%"
          + (" == D343" if EXPECT is None else f" == {EXPECT['tag']}'s own --dry count") + f" ({el()})")


def _m_start_of(m_f, m_f_oc, T):
    m_ok = np.isfinite(m_f) & np.isfinite(m_f_oc)
    m_start = int(T - np.argmax(~m_ok[::-1])) if (~m_ok).any() else 0
    assert m_ok[m_start:].all(), "[H] hedge undefined after m_start"
    return m_start, int((~m_ok[:m_start]).sum())


# ------------------------------------------------------------------ BUILD: D347's prep(), line for line, with the extras kept
def _build(el):
    """Same statements in the same order as run_d347_long_signal_controls.prep(); returns (arrays, meta, live objects)."""
    _assert_K()
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    DV = X.roll_mean_T(CLOSE * VOL)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct_f0 = 100.0 * (excl & finT.T).sum() / finT.sum()
    _assert_F0(n_ok, pct_f0)
    RAW = UF.raw_price_factor(panel, ev)
    factor_equal = bool(np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)))
    RAW_CLOSE = CLOSE * RAW
    keep = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    _assert_R(factor_equal, share, el)
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    m_f, m_f_oc = V47.floored_market(r1T, ocT, keep, finT)
    m_start, n_undef = _m_start_of(m_f, m_f_oc, T)
    print(f"  hedge defined from bar {m_start} ({panel.dates[m_start]}) onward; {n_undef} earlier bars undefined")

    def lagged(sig):
        sc = UF.apply_floor_replace(np.where(excl, np.nan, z[sig]), keep)
        sc = np.where(base, sc, np.nan)
        out = np.full((T, n), np.nan)
        out[1:] = sc[:, :-1].T
        return out
    LAG = {s: lagged(s) for s in LAG_SIGS}
    PCT = {s: V47.percentile_grid(LAG[s]) for s in LAG}
    print(f"  lagged scores and percentiles built ({el()})")
    elig = finT & keep
    elig[:m_start] = False

    def events_for(sig):
        if sig == "rsi_turn":
            r = LAG["rsi"]
            prev = np.full_like(r, np.nan)
            prev[1:] = r[:-1]
            with np.errstate(invalid="ignore"):
                lo = (r > V47.RSI_LO) & (prev <= V47.RSI_LO) & elig
                hi = (r < V47.RSI_HI) & (prev >= V47.RSI_HI) & elig
            return lo, hi
        p = PCT[SCORE_OF[sig]]
        prev = np.full_like(p, np.nan)
        prev[1:] = p[:-1]
        with np.errstate(invalid="ignore"):
            lo = (p <= V47.DECILE) & (prev > V47.DECILE) & elig
            hi = (p >= 100.0 - V47.DECILE) & (prev < 100.0 - V47.DECILE) & elig
        return lo, hi

    EV = {s: events_for(s) for s in SIGNALS}
    counts = {s: (int(EV[s][0].sum()), int(EV[s][1].sum())) for s in SIGNALS}
    for s in SIGNALS:
        print(f"  events {s:10s}: long {counts[s][0]:,}, mirror {counts[s][1]:,}")
    beta = V47.roll_beta(r1T, m_f)
    F = V47.forward_excess_grid(r1T, ocT, m_f, m_f_oc, finT)
    bucket_rsi = V47.bucket_of(PCT["rsi"])
    yr_ret = {int(y): float(np.nansum(m_f[years == y])) for y in np.unique(years)}
    down_years = sorted(y for y, v in yr_ret.items() if v < 0)
    print(f"  floored market by year: " + " ".join(f"{y}:{100 * v:+.0f}%" for y, v in sorted(yr_ret.items())) + f"; down-years {down_years} ({el()})")

    arrays = dict(ocT=ocT, mkt_oc=mkt_oc, m_f=m_f, m_f_oc=m_f_oc, keep=keep, elig=elig, base=base, live=panel.live,
                  HALF_PB=HALF_PB, HALF_PUB=HALF_PUB, CLOSE=CLOSE, VOL=VOL, RAW=RAW, RAW_CLOSE=RAW_CLOSE, DV=DV, years=years,
                  first_live=first_live, last_live=last_live, excl=excl, beta=beta, F=F, bucket_rsi=bucket_rsi, fbmask=fbmask)
    for s in LAG_SIGS:
        arrays[f"LAG_{s}"], arrays[f"PCT_{s}"] = LAG[s], PCT[s]
    for s in SIGNALS:
        arrays[f"EV_{s}_lo"], arrays[f"EV_{s}_hi"] = EV[s]
    assert set(arrays) == set(ARRAY_KEYS), sorted(set(arrays) ^ set(ARRAY_KEYS))
    meta = dict(n=int(n), T=int(T), m_start=m_start, n_hedge_undefined=n_undef, m_start_date=panel.dates[m_start],
                down_years=[int(y) for y in down_years], yr_ret={str(k): v for k, v in yr_ret.items()},
                f0_n_ok=int(n_ok), f0_pct=float(pct_f0), r_factor_equal=factor_equal, r_share=float(share),
                event_counts={s: list(c) for s, c in counts.items()}, FBREP=FBREP,
                symbols=list(panel.symbols), dates=list(panel.dates), z_path=str(R.BC.CACHE))
    return arrays, meta, dict(A=A, z=z, panel=panel)


def _write_cache(key, arrays, meta, build_seconds):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = CACHE_DIR / f"{key}.tmp"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir()
    for k, a in arrays.items():
        np.save(tmp / f"{k}.npy", a)
    meta = dict(meta, key=key, build_seconds=build_seconds, import_seconds=IMPORT_S)
    (tmp / "meta.json").write_text(json.dumps(meta))
    final = CACHE_DIR / key
    if final.exists():
        shutil.rmtree(final)
    os.replace(tmp, final)
    return final


def _is_hit(d: Path) -> bool:
    return (d / "meta.json").exists() and all((d / f"{k}.npy").exists() for k in ARRAY_KEYS)


def _load_cache(d: Path, mmap: bool):
    meta = json.loads((d / "meta.json").read_text())
    arrays = {}
    for k in ARRAY_KEYS:
        p = d / f"{k}.npy"
        mode = "r" if (mmap and p.stat().st_size >= MMAP_MIN) else None
        arrays[k] = np.load(p, mmap_mode=mode)
    return arrays, meta


class _Scores:
    """score(sig) -> z[sig]; the NpzFile is opened on first use and only the requested member is read."""

    def __init__(self, path):
        self.path, self._z = Path(path), None

    @property
    def z(self):
        if self._z is None:
            self._z = np.load(self.path, allow_pickle=False)
        return self._z

    def __call__(self, sig):
        return self.z[sig]


# ------------------------------------------------------------------ prep
def prep(need_grids=True, mmap=True, verbose=True, force_build=False):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    key = cache_key()
    d = CACHE_DIR / key
    hit = _is_hit(d) and not force_build
    print(f"    [K] d348_prep cache {'HIT' if hit else 'BUILD'} {key}")
    if hit:
        _assert_K()
        D.build_cache(verbose=False)
        A = D.load_cache(mmap=True)
        arrays, meta = _load_cache(d, mmap)
        _assert_F0(meta["f0_n_ok"], meta["f0_pct"])
        _assert_R(meta["r_factor_equal"], meta["r_share"], el)
        m_start, n_undef = _m_start_of(arrays["m_f"], arrays["m_f_oc"], meta["T"])
        assert m_start == meta["m_start"] and n_undef == meta["n_hedge_undefined"], "[H] cached hedge != meta"
        print(f"  hedge defined from bar {m_start} ({meta['m_start_date']}) onward; {n_undef} earlier bars undefined")
        for s in SIGNALS:
            c = meta["event_counts"][s]
            assert (int(arrays[f"EV_{s}_lo"].sum()), int(arrays[f"EV_{s}_hi"].sum())) == tuple(c), f"[E] cached events {s} != meta"
            print(f"  events {s:10s}: long {c[0]:,}, mirror {c[1]:,}")
        panel = None
        sc = _Scores(meta["z_path"])
        z = sc.z
    else:
        arrays, meta, live = _build(el)
        A, z, panel = live["A"], live["z"], live["panel"]
        _write_cache(key, arrays, meta, time.time() - t0)
        sc = _Scores(meta["z_path"])
        sc._z = z
        print(f"  cache written {d} ({el()})")

    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    n, T, m_start = meta["n"], meta["T"], meta["m_start"]
    ocT, mkt_oc, m_f, m_f_oc = arrays["ocT"], arrays["mkt_oc"], arrays["m_f"], arrays["m_f_oc"]
    A2 = dict(A, ocT=ocT, mkt_oc=mkt_oc)
    A3 = dict(A2, r1T=r1T, finT=finT, vxT=np.asarray(A["vxT"]), mkt=m_f, mkt_oc=m_f_oc)
    HALF = {"PB": arrays["HALF_PB"], "PUB": arrays["HALF_PUB"]}
    CLOSE, DV = arrays["CLOSE"], arrays["DV"]
    G4 = {cv: (HALF[cv], CLOSE, DV, finT) for cv in CONVS}
    LAG = {s: arrays[f"LAG_{s}"] for s in LAG_SIGS}
    PCT = {s: arrays[f"PCT_{s}"] for s in LAG_SIGS}
    EVENTS = {s: (arrays[f"EV_{s}_lo"], arrays[f"EV_{s}_hi"], LAG["rsi"] if s == "rsi_turn" else PCT[SCORE_OF[s]])
              for s in SIGNALS}
    yr_ret = {int(k): float(v) for k, v in meta["yr_ret"].items()}
    if verbose and hit:
        print(f"  floored market by year: " + " ".join(f"{y}:{100 * v:+.0f}%" for y, v in sorted(yr_ret.items()))
              + f"; down-years {meta['down_years']} ({el()})")
    return dict(A=A, A3=A3, r1T=r1T, finT=finT, ocT=ocT, m_f=m_f, m_f_oc=m_f_oc, keep=arrays["keep"], elig=arrays["elig"],
                base=arrays["base"], z=z, n=n, T=T, panel=panel, HALF=HALF, CLOSE=CLOSE, RAW_CLOSE=arrays["RAW_CLOSE"], DV=DV,
                years=arrays["years"], down_years=list(meta["down_years"]), yr_ret=yr_ret, LAG=LAG, PCT=PCT, EVENTS=EVENTS,
                beta=arrays["beta"], F=arrays["F"] if need_grids else None, bucket_rsi=arrays["bucket_rsi"], excl=arrays["excl"],
                t0=t0, m_start=m_start,
                # extras
                A2=A2, G4=G4, mkt=mkt, mkt_oc=mkt_oc, VOL=arrays["VOL"], RAW=arrays["RAW"], live=arrays["live"],
                first_live=arrays["first_live"], last_live=arrays["last_live"], fbmask=arrays["fbmask"], FBREP=meta["FBREP"],
                symbols=list(meta["symbols"]), dates=list(meta["dates"]), z_path=Path(meta["z_path"]), score=sc,
                cache_key=key, cache_hit=hit)


# ------------------------------------------------------------------ verify
def _desc(v):
    if isinstance(v, np.ndarray):
        return f"ndarray {v.shape} {v.dtype}" + (" mmap" if isinstance(v, np.memmap) else "")
    if isinstance(v, dict):
        return f"dict[{len(v)}]"
    if isinstance(v, (tuple, list)):
        return f"{type(v).__name__}[{len(v)}]"
    if isinstance(v, np.lib.npyio.NpzFile):
        return f"NpzFile[{len(v.files)}]"
    return type(v).__name__


def _eq(a, b):
    """True if bit-identical: arrays by array_equal (equal_nan on floats), containers recursively, scalars by ==."""
    if isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        if not (isinstance(a, np.ndarray) and isinstance(b, np.ndarray)):
            return False
        if a.shape != b.shape or a.dtype != b.dtype:
            return False
        return bool(np.array_equal(a, b, equal_nan=(a.dtype.kind in "fc")))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(_eq(a[k], b[k]) for k in a)
    if isinstance(a, (tuple, list)) and isinstance(b, (tuple, list)):
        return len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    if isinstance(a, np.lib.npyio.NpzFile) and isinstance(b, np.lib.npyio.NpzFile):
        return sorted(a.files) == sorted(b.files)
    if a is None or b is None:
        return a is b
    return bool(a == b)


def verify(rss=False) -> int:
    t0 = time.time()
    print("VERIFY  D347's own prep(need_grids=True) ...")
    t = time.time()
    P1 = V47.prep(need_grids=True)
    t_d347 = time.time() - t
    print(f"  D347 prep: {t_d347:.1f}s\nVERIFY  d348_prep.prep(need_grids=True) ...")
    t = time.time()
    P2 = prep(need_grids=True)
    t_hit = time.time() - t
    print(f"  d348 prep: {t_hit:.1f}s ({'HIT' if P2['cache_hit'] else 'BUILD -- run --build first; a verify must hit'})")
    bad = []
    if not P2["cache_hit"]:
        bad.append("cache_hit")
    print(f"\n  {'key':12s} {'D347 value':34s} {'d348 value':40s} status")
    for k in P1:
        a, b = P1[k], P2.get(k, KeyError)
        if b is KeyError:
            status = "MISSING"
            bad.append(k)
        elif k == "t0":
            status = "note: timestamp, not compared"
        elif k == "panel":
            live_ok = _eq(np.asarray(a.live), np.asarray(P2["live"])) and list(a.symbols) == P2["symbols"] and list(a.dates) == P2["dates"]
            status = "note: None on HIT; live/symbols/dates match" if (b is None and live_ok) else "OK" if _eq(a, b) else "MISMATCH"
            if "MISMATCH" in status:
                bad.append(k)
        else:
            ok = _eq(a, b)
            status = "OK" if ok else "MISMATCH"
            if not ok:
                bad.append(k)
        print(f"  {k:12s} {_desc(a):34s} {_desc(b) if b is not KeyError else '-':40s} {status}")

    print("\n  extras")
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    A2_ref, fb_ref, rep_ref = FL.with_open_fill(P1["A"], panel, g)
    checks = {
        "A2 == FL.with_open_fill(A, panel, g)[0]": _eq(A2_ref, P2["A2"]),
        "fbmask == with_open_fill[1]": _eq(fb_ref, P2["fbmask"]),
        "FBREP == with_open_fill[2]": _eq(rep_ref, P2["FBREP"]),
        "A3 == dict(A2, r1T, finT, vxT, mkt=m_f, mkt_oc=m_f_oc)": _eq(dict(P2["A2"], r1T=P1["r1T"], finT=P1["finT"], vxT=np.asarray(P1["A"]["vxT"]),
                                                                          mkt=P1["m_f"], mkt_oc=P1["m_f_oc"]), P2["A3"]),
        "G4 == {cv: (HALF[cv], CLOSE, DV, finT)}": _eq({cv: (P1["HALF"][cv], P1["CLOSE"], P1["DV"], P1["finT"]) for cv in CONVS}, P2["G4"]),
        "mkt == np.asarray(A['mkt'])": _eq(np.asarray(P1["A"]["mkt"]), P2["mkt"]),
        "live == panel.live": _eq(np.asarray(P1["panel"].live), P2["live"]),
        "score('rsi') == z['rsi']": _eq(P1["z"]["rsi"], P2["score"]("rsi")),
        "z_path == R.BC.CACHE": Path(P2["z_path"]) == Path(R.BC.CACHE),
        "EVENTS score objects are LAG/PCT objects": all(P2["EVENTS"][s][2] is (P2["LAG"]["rsi"] if s == "rsi_turn" else P2["PCT"][SCORE_OF[s]]) for s in SIGNALS),
        "need_grids=False -> F is None": prep(need_grids=False, verbose=False)["F"] is None,
    }
    for name, ok in checks.items():
        print(f"  {name:60s} {'OK' if ok else 'MISMATCH'}")
        if not ok:
            bad.append(name)
    print(f"\n  timings: D347 prep {t_d347:.1f}s | d348 HIT {t_hit:.1f}s | verify total {time.time() - t0:.1f}s | import chain {IMPORT_S:.1f}s")
    if rss:
        print(f"  {rss_line()}")
    if bad:
        print(f"\nVERIFY FAILED: {bad}")
        return 1
    print("\nVERIFY OK: every D347 key present and bit-identical; extras consistent")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--force", action="store_true", help="with --build: rebuild even on a HIT")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--time", action="store_true")
    ap.add_argument("--rss", action="store_true")
    a = ap.parse_args()
    print(f"d348_prep  import chain {IMPORT_S:.1f}s  key {cache_key()}  memo_load {memo_load.stats()}")
    rc = 0
    if a.build:
        t = time.time()
        P = prep(need_grids=True, force_build=a.force)
        print(f"BUILD done in {time.time() - t:.1f}s ({'was a HIT; pass --force to rebuild' if P['cache_hit'] else 'built'})")
    if a.verify:
        rc = verify(rss=a.rss)
    if a.time:
        t = time.time()
        P = prep(need_grids=True)
        print(f"TIME  prep() {'HIT' if P['cache_hit'] else 'BUILD'} in {time.time() - t:.1f}s (+ {IMPORT_S:.1f}s import chain)")
        for k in ("F", "beta", "PCT", "LAG", "ocT", "elig"):
            v = P[k]
            print(f"      {k:8s} {_desc(v) if not isinstance(v, dict) else {s: _desc(x) for s, x in v.items()}}")
    if a.rss and not a.verify:
        print(f"RSS   {rss_line()}")
    if not (a.build or a.verify or a.time):
        ap.print_help()
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
