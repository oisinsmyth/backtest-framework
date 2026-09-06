"""D357 -- the out-of-sample read on the holdout fixture: one read, on the construction D355 and D356 select.

    uv run python scripts/run_d357_holdout_read.py --selftest                 [DIS] [PIPE] [NR] [6] [L] [A] [S] on the MINING fixture
    uv run python scripts/run_d357_holdout_read.py --pipe                     [PIPE] alone: the re-pointed pipeline reproduces D346 to 0.0
    uv run python scripts/run_d357_holdout_read.py --prep [--pull]            [DIS]; the EDGAR pull command (run with --pull); then the holdout counts
    uv run python scripts/run_d357_holdout_read.py --dry                      the holdout's counts and every non-return assertion; NO return is read
    uv run python scripts/run_d357_holdout_read.py --read --spend-the-holdout  ONE time, after data/d357_construction.json is committed

THE WHOLE PREP CHAIN IS RE-POINTED, NOT COPIED. Every runner since D290 reads the fixture through
module constants that memo_load makes a single object per process:

    M.B.FIXTURE / M.B.EVENTS   scripts/run_book_single_names.py   read by RP.load_ragged callers (D303 build_cache, this prep),
                                                                  R.BC.cache_key(M.B.FIXTURE), D.cache_key(), d348_prep.cache_key()
    V31.DEALS                  scripts/run_d331_deal_filter.py     the F0 filings json
    R.BC.CACHE                 scripts/d290_build_cache.py         the score npz; read by D303 build_cache, the prep, every [K]
    (d339_census OUT_JSON, d348_prep CACHE_DIR, G22.META           NOT used here: the census json is a diagnostic output, d348_prep's
                                                                   cache is bypassed -- its [F0]/[R] assert MINING constants -- and the
                                                                   delisting flag is read from the fixture's own meta.json)

`repoint(tag)` sets the three before any cache builds. D303's cache key hashes M.B.FIXTURE, M.B.EVENTS and R.BC.CACHE, so the
holdout's arrays land in their own temp/d303_cache/<key>; the holdout's score npz is temp/d290_scores_holdout.npz.

THE HOLDOUT SCORE CACHE IS A SUBSET BUILD. d290_build_cache.main() builds all 51 candidates and fans C/D/G/H over eight
subprocesses of d290_build_worker.py, which loads the MINING fixture through its own module constant and cannot be re-pointed
without editing it. Nothing D357 reads needs those families: the two cells rank `rsi` and `hist_L`, D303's build_inputs reads
`hist_L`, `macd_hist`, `rsi`, and HALF_PUB reads `cs_spread` -- all in the four serial families A (hist_L, md, price scores),
B (intrabar), E (vol level, cs_spread), F (session), which this runner builds in-process exactly as d290_build_cache.main() does,
in the same order. The npz carries the SAME key string cache_key() gives (fixture + module mtimes + the 51-name list) plus a
`built` member naming what is in it; [K] prints both.

THE PREP IS D347's prep(), INLINE, WITHOUT THE RETURN-DERIVED ARRAYS. d348_prep.prep() asserts [F0] == 1719 / 2.54% and
[R] == D343's floor share on a BUILD -- mining-fixture constants. Here `prep_counts` runs D347's statements up to the lagged
scores and percentiles and RECORDS the holdout's own counts; `prep_full` adds the D303 arrays and the open fill for the read.
The floored market, beta and the forward grid (D347's event-lens hedge) are not built: the slot cells do not read them.

[NR]: `stage_dry` and its helpers contain no code path from r1T / ocT to a statistic. The static check greps their source for
the tokens r1T, ocT, pnl, book, sharpe, net_bp, gross, trades; the stdout of the dry stage is captured and asserted to contain
none of bp, Sharpe, net, gross, pnl. Both checks must RAISE on a tainted function / line ([6]).

ASSERTIONS [DIS] [PIPE] [NR] [K] [F0] [R] [L] [A] [S] [ID] [6] -- pre-reg section 5.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import importlib.util
import inspect
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import memo_load                                   # noqa: E402  -- each chain script executes ONCE per process
memo_load.install()                                # must precede the first _load()


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


PR = _load("d348p", "d348_prep.py")                    # executes D347's whole alias chain once; its prep() is NOT used
V48 = _load("d348r", "run_d348_score_rotation_null.py")  # cell_score / build_gate / simulate_both / cell_stats / identity_worst / rotation / audits
V47 = PR.V47
W, D, Y, R, M, X = PR.W, PR.D, PR.Y, PR.R, PR.M, PR.X
G22, UF, FL, BR, V9, V38, V31, CEN, SP, EB, PA, V35 = (PR.G22, PR.UF, PR.FL, PR.BR, PR.V9, PR.V38, PR.V31, PR.CEN, PR.SP, PR.EB,
                                                       PR.PA, PR.V35)
BC = R.BC

STUDY = 357
DEPTH, CONVS = V48.DEPTH, V48.CONVS
ANN = 252.0
SIGS = ("rsi", "hist_L")
ARMS = ("target", "invalidation", "both")
CELLS_PIPE = (("rsi", 40), ("hist_L", 40))
FAST_AXES = "ABEF"
REQUIRED_SCORES = ("rsi", "hist_L", "macd_hist", "cs_spread")
N_LAG_BARS, N_NAME_SAMPLE = 200, 50
FIX = REPO / "data" / "fixtures"
FIXTURES = {
    "mining": dict(fixture=FIX / "us_shorts_daily_raw.csv.gz", events=FIX / "us_shorts_daily_raw_events.json",
                   meta=FIX / "us_shorts_daily_raw.meta.json", deals=FIX / "us_shorts_daily_raw_deals.json",
                   npz=REPO / "temp" / "d290_scores.npz"),
    "holdout": dict(fixture=FIX / "us_shorts_daily_holdout.csv.gz", events=FIX / "us_shorts_daily_holdout_events.json",
                    meta=FIX / "us_shorts_daily_holdout.meta.json", deals=FIX / "us_shorts_daily_holdout_deals.json",
                    npz=REPO / "temp" / "d290_scores_holdout.npz"),
}
CONSTRUCTION = REPO / "data" / "d357_construction.json"
RECEIPT = REPO / "data" / "d357_read_receipt.json"
OUT = REPO / "data" / "d357_holdout_read.json"
EDGAR_REPORT = REPO / "data" / "d357_edgar_coverage_holdout.txt"
PULL_CMD = "uv run python scripts/run_d357_holdout_read.py --prep --pull"
NR_TOKENS_SRC = ("r1T", "ocT", "pnl", "book", "sharpe", "net_bp", "gross", "trades")
NR_TOKENS_OUT = ("bp", "Sharpe", "sharpe", "net", "gross", "pnl")


# ------------------------------------------------------------------ re-pointing
def repoint(tag):
    """Set every fixture constant the chain reads, BEFORE any cache build. Returns the path dict."""
    F = FIXTURES[tag]
    M.B.FIXTURE, M.B.EVENTS = F["fixture"], F["events"]
    V31.DEALS = F["deals"]
    R.BC.CACHE = F["npz"]
    # one module object per file under memo_load: the constants above are the ones every consumer reads
    assert BC is R.BC and BC.B is M.B and D.M is M and W.D is D and FL.D is D and PR.M is M and V48.M is M, "alias chain is not one object"
    assert Path(M.B.FIXTURE) == F["fixture"] and Path(R.BC.CACHE) == F["npz"] and Path(V31.DEALS) == F["deals"]
    return F


def _fixture_state(tag):
    """Which fixture the chain is pointed at right now, for assertions that must not run on the wrong one."""
    return next(t for t, F in FIXTURES.items() if Path(M.B.FIXTURE) == F["fixture"])


# ------------------------------------------------------------------ [DIS]
def dis_check(verbose=True):
    ma = json.loads(FIXTURES["mining"]["meta"].read_text())["symbols"]
    mh = json.loads(FIXTURES["holdout"]["meta"].read_text())["symbols"]
    common = set(ma) & set(mh)
    assert not common, f"[DIS] {len(common)} symbols in both fixtures: {sorted(common)[:10]}"
    if verbose:
        print(f"    [DIS] DISJOINT: {len(mh):,} holdout symbols and {len(ma):,} mining symbols share none (from both .meta.json files)")
    return len(mh), len(ma)


# ------------------------------------------------------------------ the holdout score cache (subset build)
def build_score_cache_subset(tag, force=False):
    """Families A, B, E, F of d290_build_cache.main(), in-process, into R.BC.CACHE. Returns 'HIT' or 'BUILT'."""
    assert tag == "holdout", "the mining npz is the full D334 rebuild; never rebuilt here"
    assert _fixture_state(tag) == tag
    cache = Path(R.BC.CACHE)
    key = BC.cache_key(M.B.FIXTURE)
    if cache.exists() and not force:
        try:
            z = np.load(cache, allow_pickle=False)
            if str(z["key"]) == key and all(c in z.files for c in REQUIRED_SCORES):
                return "HIT"
        except Exception:
            pass
    t0 = time.time()
    panel, cleaned = BC.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    g = BC.P1.build_grids(panel, cleaned)
    md, hs, _, _, _, _, warm = BC.B.signals_ragged(panel, cleaned, 0)
    price, pwarm = BC.PS.price_scores(panel, cleaned, live=live)
    sc = {"hist_L": hs, "md": md}
    for k in BC.PS.PRICE_SCORES:
        sc[k] = np.where(pwarm[k], price[k], np.nan)
    sc.update(BC.RF.intrabar_scores(g, live))
    sc.update(BC.VS.vol_level_scores(g, live, BC.SP.corwin_schultz(g["high"], g["low"], live)))
    sc.update(BC.SS.session_scores(g, live))
    members = [c for ax in FAST_AXES for c in BC.AXES[ax]]
    missing = [c for c in members if c not in sc]
    assert not missing, f"candidates not built: {missing}"
    assert all(c in members for c in REQUIRED_SCORES), REQUIRED_SCORES
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez(cache, key=np.array(key), warm=warm, built=np.array(members), families=np.array(list(FAST_AXES)),
             **{c: sc[c] for c in members})
    print(f"    score cache BUILT {cache.relative_to(REPO)}: families {','.join(FAST_AXES)}, {len(members)} members "
          f"({cache.stat().st_size / 1e6:.0f} MB, {time.time() - t0:.0f}s); C/D/G/H not built (nothing here reads them)")
    return "BUILT"


def score_cache_check(tag):
    """[K] on the score npz: exists, newer than ragged_panel.py, key == cache_key(); reports the member set."""
    assert _fixture_state(tag) == tag
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists() and cache.stat().st_mtime > rp.stat().st_mtime, f"[K] {cache} missing or older than ragged_panel.py"
    z = np.load(cache, allow_pickle=False)
    key = BC.cache_key(M.B.FIXTURE)
    assert str(z["key"]) == key, "[K] npz key != cache_key()"
    built = [str(s) for s in z["built"]] if "built" in z.files else None
    kh = hashlib.sha1(key.encode()).hexdigest()[:16]
    what = f"subset {','.join(str(s) for s in z['families'])}: {len(built)} members" if built else f"full: {len(z.files) - 2} members"
    print(f"    [K] SCORE CACHE {cache.name}: key matches cache_key() with ragged_panel.py in the tuple (sha1 {kh}); npz newer than the builder; {what}")
    return dict(npz=str(cache), key_sha1=kh, members=built or sorted(s for s in z.files if s not in ("key", "warm")))


# ------------------------------------------------------------------ the prep: D347's statements, inline, counts recorded
def _lagged(z_sig, excl, keep, base, T, n):
    sc = UF.apply_floor_replace(np.where(excl, np.nan, z_sig), keep)
    sc = np.where(base, sc, np.nan)
    out = np.full((T, n), np.nan)
    out[1:] = sc[:, :-1].T
    return out


def prep_counts(tag, verbose=True):
    """Everything the slot cells need EXCEPT the price-return arrays; every count the dry stage prints. No statistic."""
    F = FIXTURES[tag]
    assert _fixture_state(tag) == tag, f"call repoint({tag!r}) first"
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    say = print if verbose else (lambda *a, **k: None)
    meta = json.loads(F["meta"].read_text())
    if tag == "holdout":
        ts = time.time()
        hit = build_score_cache_subset(tag)
        t_score = time.time() - ts
    else:
        hit, t_score = "HIT", 0.0
    kinfo = score_cache_check(tag)
    ts = time.time()
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    t_d303 = time.time() - ts
    d303_dir = D.build_cache(verbose=False)
    say(f"    [K] D303 ARRAYS {d303_dir.relative_to(REPO)} ({'built' if t_d303 > 5 else 'hit'}, {t_d303:.0f}s); score cache {hit} ({t_score:.0f}s); "
        f"prep is inline (d348_prep's cache is not used: its [F0]/[R] assert mining constants)")
    finT = np.asarray(A["finT"])
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
    del cleaned
    DV = X.roll_mean_T(CLOSE * VOL)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    assert finT.shape == (T, n), (finT.shape, (T, n))
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    G4 = {cv: (HALF[cv], CLOSE, DV, finT) for cv in CONVS}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    msym = meta["symbols"]
    unknown = [s for s in panel.symbols if s not in msym]
    assert not unknown, f"panel symbols missing from {F['meta'].name}: {unknown[:5]}"
    dead = np.array([bool(msym[s].get("delistingDate")) for s in panel.symbols])
    cohort_dead = int(sum(1 for s in panel.symbols if msym[s].get("cohort") == "dead"))
    # F0 -- the deal filter exactly as D331 built it; recorded, not asserted against mining counts
    deals_path = Path(V31.DEALS)
    if deals_path.exists():
        dj = json.loads(deals_path.read_text())
        fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                             lambda f: f["form"] in V31.F0_FORMS)
        excl = V31.exclusion_mask(fbars, n, T, last_live)
        f0 = dict(deals_file=str(deals_path.relative_to(REPO)), present=True, pulled_on=dj.get("pulled_on"), complete=dj.get("complete"),
                  symbols_in_file=len(dj["deals"]), symbols_with_f0=int(sum(1 for v in fbars.values() if v.size)), applied=int(n_ok), drops=drops)
    else:
        excl = np.zeros((n, T), bool)
        f0 = dict(deals_file=str(deals_path.relative_to(REPO)), present=False, pulled_on=None, complete=None, symbols_in_file=0,
                  symbols_with_f0=0, applied=0, drops={})
    pct_f0 = 100.0 * (excl & finT.T).sum() / finT.sum()
    f0["excluded_live_pct"] = float(pct_f0)
    # raw price factor and the floor (keep_v2) -- [R] is a property of code: two implementations agree on the full grid
    RAW = UF.raw_price_factor(panel, ev)
    factor_equal = bool(np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)))
    assert factor_equal, "[R] factor != census factor"
    RAW_CLOSE = CLOSE * RAW
    keep = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    keep_v1 = UF.floor_mask(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    share_v1 = UF.floor_share(keep_v1, finT)
    n_split_names = int(sum(1 for s in panel.symbols if ev["splits"].get(s)))
    # lagged floored scores and their percentiles, the two cells' signals only
    LAG = {s: _lagged(z[s], excl, keep, base, T, n) for s in SIGS}
    PCT = {s: V47.percentile_grid(LAG[s]) for s in SIGS}
    fin_per_bar = {s: np.isfinite(LAG[s]).sum(axis=1) for s in SIGS}
    coverage = {s: dict(bars_ge_50=int((fin_per_bar[s] >= 50).sum()), bars_ge_2xN_BASE=int((fin_per_bar[s] >= 2 * W.N_BASE).sum()),
                        first_bar_ge_50=(int(np.argmax(fin_per_bar[s] >= 50)) if (fin_per_bar[s] >= 50).any() else None),
                        finite_name_bars=int(fin_per_bar[s].sum())) for s in SIGS}
    sc = PR._Scores(R.BC.CACHE)
    sc._z = z
    counts = dict(tag=tag, fixture=F["fixture"].name, names=int(n), bars=int(T), first_date=panel.dates[0], last_date=panel.dates[-1],
                  live_name_bars=int(finT.sum()), warm_base_name_bars=int(base.sum()),
                  delisted=int(dead.sum()), delisted_share=float(dead.mean()), cohort_dead=cohort_dead,
                  meta_n_symbols=len(msym), names_with_splits=n_split_names, f0=f0,
                  floor=dict(v2_share_live_fail=float(share), v1_share_live_fail=float(share_v1), removed_by_relisting_clause=float(share - share_v1),
                             factor_equal=factor_equal),
                  gate_coverage=coverage, keys=dict(score_cache=kinfo, d303_dir=d303_dir.name, d303_key=D.cache_key()),
                  timing=dict(score_cache_s=t_score, d303_s=t_d303, prep_counts_s=None))
    counts["timing"]["prep_counts_s"] = time.time() - t0
    say(f"  panel {finT.shape} ({el()})")
    return dict(tag=tag, A=A, panel=panel, g=g, finT=finT, HALF=HALF, CLOSE=CLOSE, VOL=VOL, DV=DV, G4=G4, z=z, base=base, n=n, T=T,
                excl=excl, keep=keep, RAW=RAW, RAW_CLOSE=RAW_CLOSE, LAG=LAG, PCT=PCT, years=years, first_live=first_live, last_live=last_live,
                dead=dead, symbols=list(panel.symbols), dates=list(panel.dates), score=sc, counts=counts, meta=meta, t0=t0)


def open_fill_counts(Q):
    """The next-open fill's arrays (kept privately on Q for prep_full) and its COUNTS."""
    if "_A2" not in Q:
        A2, fb, rep = FL.with_open_fill(Q["A"], Q["panel"], Q["g"])
        Q["_A2"], Q["_fbmask"], Q["_FBREP"] = A2, fb, rep
    return Q["_FBREP"]


def prep_full(tag, Q=None, verbose=True):
    """prep_counts plus the D303 price-return arrays and the open fill: everything D348's cell functions read."""
    Q = Q if Q is not None else prep_counts(tag, verbose=verbose)
    assert Q["tag"] == tag and _fixture_state(tag) == tag
    open_fill_counts(Q)
    A = Q["A"]
    r1T, mkt = np.asarray(A["r1T"]), np.asarray(A["mkt"])
    A2 = Q["_A2"]
    assert np.array_equal(np.asarray(A["finT"]), Q["finT"])
    return dict(Q, r1T=r1T, mkt=mkt, ocT=A2["ocT"], mkt_oc=A2["mkt_oc"], A2=A2, fbmask=Q["_fbmask"], FBREP=Q["_FBREP"])


# ------------------------------------------------------------------ [NR]
class _Tee(io.TextIOBase):
    def __init__(self, real):
        self.real, self.buf = real, io.StringIO()

    def write(self, s):
        self.real.write(s)
        self.buf.write(s)
        return len(s)

    def flush(self):
        self.real.flush()


def nr_static(fn):
    src = inspect.getsource(fn)
    hits = [t for t in NR_TOKENS_SRC if t in src]
    assert not hits, f"[NR] {fn.__name__} contains {hits}"
    return len(src.splitlines())


def nr_stdout(text):
    hits = sorted({t for t in NR_TOKENS_OUT if t in text})
    assert not hits, f"[NR] the dry stage's stdout contains {hits}"
    return len(text.splitlines())


def _dry_tainted(P):
    """[6]: a dry function with one return appended. The static check must refuse it."""
    print("counts only")
    print(float(P["r1T"][100, 0]))


# ------------------------------------------------------------------ the dry stage (its source is grepped: no return path)
def lag_and_rotation_checks(Q, sig, rng, verbose=True):
    """[L] on the gate built from the lagged floored score; [A] on three rotations of the score. Reads scores, never prices."""
    sc = V48.cell_score(Q, sig)
    gate = V48.build_gate(Q, sig, sc)
    nonempty = np.array([t for t in range(1, Q["T"]) if V38.gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=min(N_LAG_BARS, nonempty.size), replace=False)
    n_unl = V48.lag_audit(Q, gate, sc, bars)
    assert n_unl > bars.size // 2, f"[L] {sig}: the unlagged rebuild differs on only {n_unl} of {bars.size}"
    rp = V48.plan_for(sc)
    fr = []
    for _ in range(3):
        off = V48.draw_offsets(rng, rp["lens"])
        rot = V48.rotate(sc, rp, off)
        V48.check_rotation(rot, sc, rp["fin"], range(Q["n"]))
        big = rp["lens"] >= 100
        fr.append(float((off[big] != 0).mean()) if big.any() else 1.0)
    if verbose:
        print(f"    [L] LAG AUDIT ({sig}): the long gate equals the rebuild from score[:, t-1] on all {bars.size} sampled bars "
              f"(of {nonempty.size:,} with a gate); the unlagged rebuild differs on {n_unl}")
        print(f"    [A] ROTATION ({sig}): 3 draws keep every name's finite count, every bar's finite count and every name's multiset exactly; "
              f"offsets non-zero on {100 * min(fr):.1f}-{100 * max(fr):.1f}% of names with L >= 100")
    return dict(lag_bars=int(bars.size), gate_bars=int(nonempty.size), unlagged_differs=int(n_unl), frac_nonzero=fr)


def stage_dry(tag, Q=None):
    """Counts only. The holdout's names, bars, dates, delistings, filings applied, floor share, gate coverage, cache keys; the lag
    audit and the rotation's count checks on the score. Nothing here reads a price return; the static check holds the source."""
    t0 = time.time()
    dis_check()
    F = repoint(tag)
    Q = Q if Q is not None else prep_counts(tag)
    c = Q["counts"]
    print(f"\n  {tag.upper()} FIXTURE {c['fixture']}: {c['names']:,} names x {c['bars']:,} bars, {c['first_date']} .. {c['last_date']}; "
          f"{c['live_name_bars']:,} live name-bars, {c['warm_base_name_bars']:,} warm; meta lists {c['meta_n_symbols']:,} symbols")
    print(f"  delisted (delistingDate in meta) {c['delisted']} of {c['names']} = {100 * c['delisted_share']:.1f}%; cohort dead {c['cohort_dead']}; "
          f"names with splits on file {c['names_with_splits']}")
    f0 = c["f0"]
    if f0["present"]:
        print(f"    [F0] F0 MASK: {f0['applied']:,} filings applied from {f0['deals_file']} (pulled {f0['pulled_on']}, complete {f0['complete']}, "
              f"{f0['symbols_in_file']} symbols, {f0['symbols_with_f0']} with an F0 filing); drops {f0['drops']}; "
              f"{f0['excluded_live_pct']:.2f}% of live name-bars excluded")
    else:
        print(f"    [F0] F0 MASK: 0 filings applied -- {f0['deals_file']} is ABSENT (the deal filter is empty on this run); "
              f"pull it with:  {PULL_CMD}")
    fl = c["floor"]
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor on the full grid; keep_v2 fails {100 * fl['v2_share_live_fail']:.4f}% of live "
          f"name-bars (v1 {100 * fl['v1_share_live_fail']:.4f}%; the re-listing clause removes {100 * fl['removed_by_relisting_clause']:.4f}%)")
    rep = open_fill_counts(Q)
    print(f"  open fill: {rep['fallback_cells']:,} of {rep['priced_cells']:,} priced cells fall back to the prior close "
          f"({100 * rep['fallback_frac']:.3f}%), {rep['n_fallback_names']} names; cells with an open {rep['cells_with_open']:,}")
    for s in SIGS:
        g = c["gate_coverage"][s]
        print(f"  gate coverage {s:7s}: {g['bars_ge_50']:,} of {c['bars']:,} bars with >= 50 finite lagged scores (first at bar {g['first_bar_ge_50']}); "
              f"{g['bars_ge_2xN_BASE']:,} with >= {2 * W.N_BASE}; {g['finite_name_bars']:,} finite name-bars")
    k = c["keys"]
    print(f"    [K] keys: score npz sha1 {k['score_cache']['key_sha1']}, D303 dir {k['d303_dir']}, D303 key {k['d303_key']}")
    rng = np.random.default_rng([W.SEED, STUDY, 7, 0 if tag == "mining" else 1])
    c["audits"] = {s: lag_and_rotation_checks(Q, s, rng) for s in SIGS}
    c["open_fill"] = rep
    c["timing"]["dry_stage_s"] = time.time() - t0
    print(f"  {PR.rss_line()} ({time.time() - t0:.0f}s)")
    return Q


# ------------------------------------------------------------------ [PIPE]
def stage_pipe(Q=None, verbose=True):
    """The re-pointed pipeline on the MINING fixture reproduces D346's two cells to 0.0 (D348's identity_worst)."""
    repoint("mining")
    P = prep_full("mining", Q, verbose=verbose)
    pub = V48.load_published()
    OBS, worst = {}, 0.0
    for sig, k in CELLS_PIPE:
        OBS[sig, k] = V48.observed_cell(P, sig, k, pub, verbose=verbose)
        worst = max(worst, OBS[sig, k]["worst"])
    assert worst < 1e-9, f"[PIPE] {worst:.2e}"
    print(f"    [PIPE] the re-pointed pipeline on the mining fixture reproduces D346's rsi and hist_L k=40 cells to {worst:.1e} "
          f"(every published statistic, both conventions, both lenses)")
    return P, OBS, worst


# ------------------------------------------------------------------ the EDGAR pull, re-pointed
def edgar_pull_holdout(run=False):
    H = FIXTURES["holdout"]
    print("\n  THE HOLDOUT'S DEAL FILINGS -- D331's reproducible EDGAR pull, re-pointed at the holdout (network; the principal launches it):")
    print(f"      {PULL_CMD}")
    print(f"    it sets d331_edgar_deals.FIXTURE/FIXTURE_META/EVENTS to {H['fixture'].name} / {H['meta'].name} / {H['events'].name},")
    print(f"    OUT_JSON to {H['deals'].relative_to(REPO)} and OUT_REPORT to {EDGAR_REPORT.relative_to(REPO)}, and calls its main() with the default --workers;")
    print(f"    the HTTP cache temp/edgar/ is shared with the mining pull (ticker maps are re-used); the output lands in data/ only on a complete run.")
    if not run:
        return None
    ED = _load("d331_edgar", "d331_edgar_deals.py")
    ED.FIXTURE, ED.FIXTURE_META, ED.EVENTS = str(H["fixture"]), str(H["meta"]), str(H["events"])
    ED.OUT_JSON, ED.OUT_REPORT = str(H["deals"]), str(EDGAR_REPORT)
    argv = sys.argv
    sys.argv = ["d331_edgar_deals.py", "--workers", str(ED.WORKERS)]
    t0 = time.time()
    try:
        ED.main()
    finally:
        sys.argv = argv
    print(f"  pull finished ({time.time() - t0:.0f}s); deals file {'present' if H['deals'].exists() else 'ABSENT (incomplete run stayed in temp/edgar_out)'}")
    return H["deals"].exists()


# ------------------------------------------------------------------ the read: cells, arms, nulls, groups, hurdles
def pct_of(P, sc_nT):
    """D355's exit grid for a (possibly rotated) score: the lagged floored score's cross-sectional percentile (D347's grid)."""
    return V47.percentile_grid(_lagged_from_score(sc_nT, P["base"], P["T"], P["n"]))


def _lagged_from_score(sc_nT, base, T, n):
    sc = np.where(base, sc_nT, np.nan)
    out = np.full((T, n), np.nan)
    out[1:] = sc[:, :-1].T
    return out


def _inv_supported():
    return "invalidation" in inspect.signature(W.simulate).parameters


def simulate_arm(P, gate, arm, pct, k, shift=0, lenses=("v", "i")):
    """D346's simulate pair under one of D355's arms. The target arm passes NO extra keyword -- it is D348's simulate_both."""
    assert arm in ARMS
    W.BASE_HOLD = k
    use_target = arm in ("target", "both")
    kw = dict(shift=shift, fill="open")
    if arm != "target":
        assert _inv_supported(), "run_d306_width_exits.simulate has no `invalidation=` keyword: D355's simulator edit is not on disk"
        assert pct is not None and pct.shape == P["r1T"].shape
        kw["invalidation"] = pct
    out = []
    for lens in lenses:
        out.append(W.simulate(P["A2"], gate, DEPTH, use_target, slots=(lens == "v"), **kw))
    return out


def costed_or_none(res, G4):
    try:
        return G22.costed(res, G4)
    except ZeroDivisionError:
        return None


def borrow_or_none(P, res, C):
    if any(C[cv] is None for cv in CONVS):
        return None
    BV, _ = V38.borrow_block(res, C, None, P["excl"], P["CLOSE"], P["T"])
    return BV


def slot_four_groups(P, res_v, C):
    """The four groups on the SLOT ledger (D344's construction): G22's groups per convention, the top trades named with their
    as-traded prior close and dollar-volume percentile, the price halves, per-trade by entry year."""
    r1T, ocT = P["r1T"], P["ocT"]
    contrib = FL.contributions_fill(res_v, r1T, ocT)
    G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS if C[cv]}
    G2 = G22.group2(res_v)
    G3 = {cv: G22.group3(res_v, contrib, C[cv], P["years"], P["dead"], P["CLOSE"], P["HALF"][cv]) for cv in CONVS if C[cv]}
    tr = res_v["trades"]
    pnl = np.array([t[3] for t in tr]) * 1e4
    rows = np.array([t[0] for t in tr])
    e0s = np.array([t[1] for t in tr])
    ages = np.array([t[2] for t in tr])
    sides = np.array([t[4] for t in tr])
    tot = float(pnl.sum())
    prev = np.maximum(e0s - 1, 0)
    raw_prev = P["RAW_CLOSE"][prev, rows]
    top = []
    for i in np.argsort(-pnl)[:5]:
        top.append(dict(symbol=P["symbols"][rows[i]], side="long" if sides[i] == 0 else "short", entry_date=P["dates"][e0s[i]], hold=int(ages[i]),
                        pnl_bp=float(pnl[i]), share_of_raw_pnl=(float(pnl[i] / tot) if tot > 0 else None),
                        as_traded_prior_close=(float(raw_prev[i]) if np.isfinite(raw_prev[i]) else None),
                        as_traded_entry_close=float(P["RAW_CLOSE"][e0s[i], rows[i]]), adjusted_entry_close=float(P["CLOSE"][e0s[i], rows[i]]),
                        dv_percentile_at_entry=CEN.dv_percentile(P["DV"], P["finT"], int(e0s[i]), int(rows[i])),
                        deal_excluded_at_entry=bool(P["excl"][rows[i], max(int(e0s[i]) - 1, 0)])))
    med_px = float(np.nanmedian(raw_prev))
    lo = np.isfinite(raw_prev) & (raw_prev <= med_px)
    hi = np.isfinite(raw_prev) & (raw_prev > med_px)
    csum = float(contrib.sum())
    price_halves = dict(median_as_traded_prior_close=med_px,
                        low=dict(n=int(lo.sum()), mean_bp=float(pnl[lo].mean()) if lo.any() else None, share_contrib=(float(contrib[lo].sum() / csum) if csum else None)),
                        high=dict(n=int(hi.sum()), mean_bp=float(pnl[hi].mean()) if hi.any() else None, share_contrib=(float(contrib[hi].sum() / csum) if csum else None)))
    yrs = P["years"][e0s]
    by_year_trades = {int(y): dict(n=int((yrs == y).sum()), mean_bp=float(pnl[yrs == y].mean())) for y in np.unique(yrs)}
    top_share = float(pnl.max() / tot) if tot > 0 else None
    return dict(G1=G1, G2=G2, G3=G3, top5=top, top_trade_share=top_share, total_raw_pnl_bp=tot, price_halves=price_halves,
                by_year_trades=by_year_trades, n_trades=int(pnl.size))


def rank_rotation(P, gate, arm, pct, k):
    """D348's 24-shift rank rotation of the observed gate (shifts 1..24 of the 25-name gate), every statistic, raw kept for the blend."""
    RAW, by_shift = {}, {}
    for s_ in range(1, W.N_BASE):
        rv, ri = simulate_arm(P, gate, arm, pct, k, shift=s_)
        st, full = V48.cell_stats(P, rv, ri, want_full=True)
        by_shift[s_] = st
        RAW[s_] = dict(book=rv["book"], mask=rv["mask"], C=full["C"], BV=full["borrow_variant"])
    RR = {s: np.array([by_shift[s_][s] for s_ in sorted(by_shift)], float) for s in V48.STATS}
    return RR, RAW


def time_rotation(P, sig, k, arm, sc, draws, ci, verbose=True):
    """D348's control A: each name's score rotated in time within its finite bars, re-ranked, re-simulated; the exit grid
    recomputed from the rotated score when the arm reads it. Seeds [SEED, 357, cell, arm, 0]."""
    rp = V48.plan_for(sc)
    ai = ARMS.index(arm)
    rng = np.random.default_rng([W.SEED, STUDY, ci, ai, 0])
    name_rng = np.random.default_rng([W.SEED, STUDY, 99, ci, ai])
    REC = {s: [] for s in V48.STATS}
    n_deg, ts = 0, time.time()
    for d in range(draws):
        names = name_rng.choice(P["n"], size=min(N_NAME_SAMPLE, P["n"]), replace=False)
        off = V48.draw_offsets(rng, rp["lens"])
        rot = V48.rotate(sc, rp, off)
        big = rp["lens"] >= 100
        frac_nz = float((off[big] != 0).mean()) if big.any() else 1.0
        assert frac_nz > 0.99, f"[N] offsets non-zero on only {100 * frac_nz:.2f}% of names with L >= 100"
        V48.check_rotation(rot, sc, rp["fin"], names)
        gate = V48.build_gate(P, sig, rot)
        pct = pct_of(P, rot) if arm != "target" else None
        rv, ri = simulate_arm(P, gate, arm, pct, k)
        st = V48.cell_stats(P, rv, ri)
        n_deg += int(st["degenerate"])
        for key in V48.STATS:
            REC[key].append(st[key])
        if verbose and ((d + 1) % 10 == 0 or d + 1 == draws):
            print(f"      {sig} {arm}: {d + 1}/{draws} draws ({time.time() - ts:.0f}s, {(time.time() - ts) / (d + 1):.2f} s/draw)", flush=True)
    A_ = {s: np.array([np.nan if v is None else v for v in REC[s]], float) for s in V48.STATS}
    return A_, n_deg


def hurdles(stats, FG, RR, TR):
    """H1-H6 of pre-reg section 3, each with the numbers it was decided on."""
    g = stats["gross_bp"]
    rr95 = V48.dist_of(RR["gross_bp"], g)["p95"]
    tr95 = V48.dist_of(TR["gross_bp"], g)["p95"] if TR is not None else None
    G1, G2, G3 = FG["G1"].get("PUB"), FG["G2"], FG["G3"].get("PUB")
    two_c = G1["two_c_bp"] if G1 else None
    rt_total = G1["round_trip_total"] if G1 else None
    trimmed = G2["mean_trimmed_bp"]
    H = {}
    H["H1"] = dict(value=stats["net_bp_borrow_PUB"], rule="PUB net bp/bar after GC/HTB borrow > 0", pass_=bool(np.isfinite(stats["net_bp_borrow_PUB"]) and stats["net_bp_borrow_PUB"] > 0))
    H["H2"] = dict(value=g, rank_p95=rr95, time_p95=tr95, rule="gross bp/bar above the p95 of both nulls",
                   pass_=bool(rr95 is not None and g > rr95 and (tr95 is not None and g > tr95)))
    H["H3"] = dict(value=(trimmed - two_c) if two_c is not None else None, trimmed_mean_bp=trimmed, two_c_bp=two_c, round_trip_total_bp=rt_total,
                   trimmed_minus_rt_total=(trimmed - rt_total) if rt_total is not None else None,
                   rule="symmetric 1% trimmed mean per trade (slot ledger) minus 2c (= rt_total / 2, the trade's own-notional round trip, PUB) > 0",
                   pass_=bool(two_c is not None and trimmed - two_c > 0))
    H["H4"] = dict(value=FG["top_trade_share"], rule="no trade above 10% of the ledger's raw P&L (total must be > 0)",
                   pass_=bool(FG["top_trade_share"] is not None and FG["top_trade_share"] <= 0.10))
    H["H5"] = dict(value=G3["names_to_half_pnl"] if G3 else None, raw_pnl_basis=G3["names_to_half_pnl_rawpnl"] if G3 else None,
                   rule="at least 10 names to half the P&L (contribution basis)", pass_=bool(G3 and G3["names_to_half_pnl"] >= 10))
    H["H6"] = dict(value=stats["sharpe_net_PUB"], after_borrow=(stats["net_bp_borrow_PUB"] / stats["vol_bp"] * np.sqrt(ANN) if stats["vol_bp"] > 0 else None),
                   rule="PUB net Sharpe > 0", pass_=bool(np.isfinite(stats["sharpe_net_PUB"]) and stats["sharpe_net_PUB"] > 0))
    H["all_six"] = bool(all(H[h]["pass_"] for h in ("H1", "H2", "H3", "H4", "H5", "H6")))
    return H


def print_hurdles(label, H):
    print(f"\n  HURDLES -- {label}")
    f3 = lambda v: "--" if v is None or not np.isfinite(v) else f"{v:+.3f}"
    for h in ("H1", "H2", "H3", "H4", "H5", "H6"):
        d = H[h]
        v = d["value"]
        vs = "--" if v is None else (f"{v:+.4f}" if isinstance(v, float) else str(v))
        extra = ""
        if h == "H2":
            extra = f" (rank p95 {f3(d['rank_p95'])}, time p95 {f3(d['time_p95'])})"
        elif h == "H3":
            extra = (f" (trimmed {f3(d['trimmed_mean_bp'])} - 2c {f3(d['two_c_bp'])}; vs rt_total {f3(d['round_trip_total_bp'])}: "
                     f"{f3(d['trimmed_minus_rt_total'])})")
        elif h == "H5":
            extra = f" (raw-P&L basis {d['raw_pnl_basis']})"
        elif h == "H6":
            extra = f" (after borrow {f3(d['after_borrow'])})"
        print(f"    {h} {'PASS' if d['pass_'] else 'FAIL'}  {vs}{extra}  -- {d['rule']}")
    print(f"    ALL SIX: {'PASS -- the construction enters BOOK.md' if H['all_six'] else 'FAIL -- the construction is retired'}")


def read_cell(P, spec, ci, draws):
    sig, k, arm = spec["sig"], spec["k"], spec["arm"]
    t0 = time.time()
    label = f"{sig} k={k} arm={arm}"
    print(f"\n  CELL {ci}: {label}")
    sc = V48.cell_score(P, sig)
    gate = V48.build_gate(P, sig, sc)
    pct = None
    if arm != "target":
        pct = pct_of(P, sc)
        assert np.array_equal(pct, P["PCT"][sig], equal_nan=True), "[PC] the exit grid != the prep's PCT"
        print(f"    [PC] the exit grid rebuilt from the cell score equals the prep's percentile grid bit-identically")
    res_v, res_i = simulate_arm(P, gate, arm, pct, k)
    stats, full = V48.cell_stats(P, res_v, res_i, want_full=True)
    # [L] [S] on the observed holdout cell
    rng = np.random.default_rng([W.SEED, STUDY, 7, 1, ci])
    nonempty = np.array([t for t in range(1, P["T"]) if V38.gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=min(N_LAG_BARS, nonempty.size), replace=False)
    n_unl = V48.lag_audit(P, gate, sc, bars)
    assert n_unl > bars.size // 2, f"[L] unlagged differs on only {n_unl}"
    print(f"    [L] LAG AUDIT: the long gate equals the rebuild from score[:, t-1] on all {bars.size} sampled bars; the unlagged rebuild differs on {n_unl}")
    S = {}
    for lens, res in (("variant", res_v), ("invariant", res_i)):
        worst, dL, dS, ntr = V48.sign_audit(P, res, f"{label} {lens}")
        S[lens] = dict(worst=worst, dL=dL, dS=dS, trades=ntr)
        print(f"    [S] SIGN IN MONEY ({lens}): {ntr:,} trades equal the open-fill recomputation to {worst:.1e}; favourable paths pay positively; "
              f"a +50 bp held-bar move lifts a long {dL:+.1f} bp and a short {dS:+.1f} bp")
    print(f"    observed: gross {stats['gross_bp']:+.2f}, PUB net {stats['net_bp_PUB']:+.2f} (+GC/HTB {stats['net_bp_borrow_PUB']:+.2f}), "
          f"PB net {stats['net_bp_PB']:+.2f}, PUB net Sharpe {stats['sharpe_net_PUB']:+.3f}, {stats['trades_v']:,} trades, {stats['bars']:,} bars, "
          f"entries {stats['entries']:,}; legs {stats['leg_long_bp']:+.1f} / {stats['leg_short_bp']:+.1f} bp; invariant net/trade PUB "
          f"{stats['inv_net_per_trade_PUB']:+.1f} ({time.time() - t0:.0f}s)")
    FG = slot_four_groups(P, res_v, full["C"])
    tt = FG["top5"][0]
    print(f"    top trade: {tt['symbol']} {tt['side']} entered {tt['entry_date']} held {tt['hold']} bars, {tt['pnl_bp']:+.0f} bp = "
          f"{100 * (tt['share_of_raw_pnl'] or 0):.1f}% of raw P&L; as-traded prior close ${tt['as_traded_prior_close']}, "
          f"DV percentile {tt['dv_percentile_at_entry']:.2f}, deal-excluded {tt['deal_excluded_at_entry']}")
    g2 = FG["G2"]
    print(f"    trades: n {g2['n']}, mean {g2['mean_bp']:+.1f}, median {g2['median_bp']:+.1f} ({'MEAN BELOW MEDIAN' if g2['mean_below_median'] else 'mean above median'}), "
          f"win {100 * g2['win_rate']:.1f}%, payoff {g2['payoff']:.2f}, run {g2['holding_run_mean']:.1f}, skew {g2['skew']:+.2f}, kurt {g2['kurtosis_raw']:.1f}; "
          f"ex-top {g2['mean_ex_top_bp']:+.1f}, ex-bottom {g2['mean_ex_bottom_bp']:+.1f}, trimmed {g2['mean_trimmed_bp']:+.1f} (k={g2['k_trim']})")
    if "PUB" in FG["G3"]:
        g3 = FG["G3"]["PUB"]
        print(f"    names: {g3['names']} traded, {g3['names_to_half_pnl']} to half the P&L (raw basis {g3['names_to_half_pnl_rawpnl']}), top-1/5/10 share "
              f"{100 * g3['top1_name_share']:.0f}/{100 * g3['top5_name_share']:.0f}/{100 * g3['top10_name_share']:.0f}%; years {g3['years']}, profitable gross "
              f"{g3['years_profitable_gross']} net {g3['years_profitable_net']}; dead {g3['dead']['n']} trades {g3['dead']['mean_bp']:+.1f} bp vs alive "
              f"{g3['alive']['n']} {g3['alive']['mean_bp']:+.1f}; price terciles {g3['price_low']['mean_bp']:+.1f} / {g3['price_mid']['mean_bp']:+.1f} / "
              f"{g3['price_high']['mean_bp']:+.1f}; eras {g3['era_first_half']['mean_bp']:+.1f} / {g3['era_second_half']['mean_bp']:+.1f}")
    ph = FG["price_halves"]
    print(f"    price halves at ${ph['median_as_traded_prior_close']:.2f}: low {ph['low']['n']} trades {ph['low']['mean_bp']:+.1f} bp, high {ph['high']['n']} {ph['high']['mean_bp']:+.1f} bp")
    print(f"    gross by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in sorted(FG['G3']['PUB']['gross_by_year'].items())) if "PUB" in FG["G3"] else "")
    ts = time.time()
    RR, RRraw = rank_rotation(P, gate, arm, pct, k)
    print(f"    rank rotation: {RR['gross_bp'].size} shifts ({time.time() - ts:.0f}s)")
    TR, n_deg = time_rotation(P, sig, k, arm, sc, draws, ci)
    print(f"    time rotation: {draws} draws, {n_deg} degenerate")
    H = hurdles(stats, FG, RR, TR)
    table = {}
    print(f"\n  {label}: statistic | observed | time p50 p95 max below | rank p50 p95 max above-k/24")
    for lab, key in V48.TABLE_ROWS:
        o = stats[key]
        dA, dR = V48.dist_of(TR[key], o), V48.dist_of(RR[key], o)
        above_r = int((RR[key][np.isfinite(RR[key])] < o).sum())
        table[key] = dict(observed=o, time_rotation=dA, rank_rotation=dict(dR, above_k=above_r, of=int(np.isfinite(RR[key]).sum())))
        f_ = lambda v: ("%10.3f" % v) if v is not None and np.isfinite(v) else "%10s" % "--"
        print("    %-20s %s | %s %s %s %6s | %s %s %s %s" % (lab, f_(o), f_(dA["p50"]), f_(dA["p95"]), f_(dA["max"]),
                                                            (f"{100 * dA['below']:.1f}%" if dA["below"] is not None else "--"),
                                                            f_(dR["p50"]), f_(dR["p95"]), f_(dR["max"]), f"{above_r}/{int(np.isfinite(RR[key]).sum())}"))
    print_hurdles(label, H)
    out = dict(cell=spec, label=label, observed=stats, costed={cv: full["C"][cv] for cv in CONVS}, legs={cv: full["LEGS"][cv] for cv in CONVS},
               invariant={cv: full["INV"][cv] for cv in CONVS}, borrow_variant=full["borrow_variant"], four_groups=FG, sign_audit=S,
               lag_audit=dict(bars=int(bars.size), unlagged_differs=int(n_unl)),
               nulls=dict(rank_rotation=dict(shifts=int(RR["gross_bp"].size), dist={s: V48.dist_of(RR[s], stats[s]) for s in V48.STATS}, per_shift={s: RR[s] for s in V48.STATS}),
                          time_rotation=dict(draws=draws, degenerate=n_deg, seed=[W.SEED, STUDY, ci, ARMS.index(arm), 0],
                                             dist={s: V48.dist_of(TR[s], stats[s]) for s in V48.STATS}, per_draw={s: TR[s] for s in V48.STATS})),
               table=table, hurdles=H, elapsed_s=time.time() - t0)
    raw = dict(res_v=res_v, C=full["C"], BV=full["borrow_variant"], RRraw=RRraw, sc=sc, gate=gate, pct=pct, k=k, sig=sig, arm=arm, FG=FG)
    return out, raw


# ------------------------------------------------------------------ the blend (D356's construction, 50/50 capital)
def blend_of(ra_book, ra_mask, rb_book, rb_mask, Ca, Cb, BVa, BVb):
    ma, mb = np.asarray(ra_mask, bool), np.asarray(rb_mask, bool)
    both = ma & mb
    if int(both.sum()) < 200:
        return None
    a, b_ = np.asarray(ra_book)[both], np.asarray(rb_book)[both]
    b = 0.5 * (a + b_)
    g, v = float(b.mean()) * 1e4, float(b.std(ddof=1)) * 1e4
    eq = np.cumsum(b)
    out = dict(bars=int(both.sum()), mask_mismatch_bars=int((ma ^ mb).sum()), gross_bp=g, vol_bp=v,
               sharpe_gross=(g / v * np.sqrt(ANN)) if v > 0 else np.nan, maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)) * 1e4,
               corr_gross=float(np.corrcoef(a, b_)[0, 1]) if a.std() > 0 and b_.std() > 0 else np.nan)
    for cv in CONVS:
        if Ca[cv] is None or Cb[cv] is None:
            out[f"cost_bp_{cv}"] = out[f"net_bp_{cv}"] = out[f"sharpe_net_{cv}"] = out[f"borrow_bp_{cv}"] = out[f"net_bp_borrow_{cv}"] = np.nan
            continue
        cost = 0.5 * (Ca[cv]["cost_bp"] + Cb[cv]["cost_bp"])
        net = g - cost
        borrow = 0.5 * (BVa["gc_htb"][cv]["borrow_bp_bar"] + BVb["gc_htb"][cv]["borrow_bp_bar"]) if (BVa and BVb) else np.nan
        out[f"cost_bp_{cv}"], out[f"net_bp_{cv}"] = cost, net
        out[f"sharpe_net_{cv}"] = (net / v * np.sqrt(ANN)) if v > 0 else np.nan
        out[f"borrow_bp_{cv}"], out[f"net_bp_borrow_{cv}"] = borrow, net - borrow
    return out


BLEND_STATS = ("gross_bp", "vol_bp", "sharpe_gross", "maxdd_bp", "net_bp_PUB", "net_bp_PB", "sharpe_net_PUB", "sharpe_net_PB",
               "net_bp_borrow_PUB", "net_bp_borrow_PB", "corr_gross", "bars")


def blend_null_time(P, raws, draws, verbose=True):
    """D356's paired time-rotation null: each parent rotated independently (its own seed), blended the same way; variant lens only."""
    rps = [V48.plan_for(r["sc"]) for r in raws]
    rngs = [np.random.default_rng([W.SEED, STUDY, 200 + i, 0]) for i in range(len(raws))]
    REC = {s: [] for s in BLEND_STATS}
    ts = time.time()
    for d in range(draws):
        parts = []
        for i, r in enumerate(raws):
            off = V48.draw_offsets(rngs[i], rps[i]["lens"])
            rot = V48.rotate(r["sc"], rps[i], off)
            gate = V48.build_gate(P, r["sig"], rot)
            pct = pct_of(P, rot) if r["arm"] != "target" else None
            (rv,) = simulate_arm(P, gate, r["arm"], pct, r["k"], lenses=("v",))
            C = {cv: costed_or_none(rv, P["G4"][cv]) for cv in CONVS}
            parts.append(dict(book=rv["book"], mask=rv["mask"], C=C, BV=borrow_or_none(P, rv, C)))
        bl = blend_of(parts[0]["book"], parts[0]["mask"], parts[1]["book"], parts[1]["mask"], parts[0]["C"], parts[1]["C"], parts[0]["BV"], parts[1]["BV"])
        for s in BLEND_STATS:
            REC[s].append(np.nan if bl is None else bl[s])
        if verbose and ((d + 1) % 10 == 0 or d + 1 == draws):
            print(f"      blend: {d + 1}/{draws} paired draws ({time.time() - ts:.0f}s)", flush=True)
    return {s: np.array(REC[s], float) for s in BLEND_STATS}


def blend_hurdles(P, raws, obs, RRb, TRb):
    """H1-H6 on the blend: per-bar hurdles on the blended series; per-trade hurdles on the POOLED slot ledgers, each trade charged its
    own book's 2c (a merged ledger is never re-priced), contributions at half weight (shares unchanged)."""
    pnl, cost, contrib, rows = [], [], [], []
    for r in raws:
        tr = r["res_v"]["trades"]
        p = np.array([t[3] for t in tr]) * 1e4
        two_c = r["FG"]["G1"]["PUB"]["two_c_bp"]
        pnl.append(p)
        cost.append(np.full(p.size, two_c))
        contrib.append(0.5 * FL.contributions_fill(r["res_v"], P["r1T"], P["ocT"]))
        rows.append(np.array([t[0] for t in tr]))
    pnl, cost, contrib, rows = map(np.concatenate, (pnl, cost, contrib, rows))
    net = pnl - cost
    k = max(1, net.size // 100)
    srt = np.sort(net)
    trimmed_net = float(srt[k:-k].mean())
    tot = float(pnl.sum())
    top_share = float(pnl.max() / tot) if tot > 0 else None
    per_name = np.bincount(rows, weights=contrib, minlength=P["n"])
    desc = np.sort(per_name)[::-1]
    ctot = float(contrib.sum())
    names_half = int(np.searchsorted(np.cumsum(desc), 0.5 * ctot) + 1) if ctot > 0 else None
    g = obs["gross_bp"]
    rr95 = V48.dist_of(RRb["gross_bp"], g)["p95"]
    tr95 = V48.dist_of(TRb["gross_bp"], g)["p95"]
    H = {}
    H["H1"] = dict(value=obs["net_bp_borrow_PUB"], rule="blend PUB net bp/bar after GC/HTB borrow > 0", pass_=bool(np.isfinite(obs["net_bp_borrow_PUB"]) and obs["net_bp_borrow_PUB"] > 0))
    H["H2"] = dict(value=g, rank_p95=rr95, time_p95=tr95, rule="blend gross bp/bar above the p95 of both paired nulls", pass_=bool(rr95 is not None and tr95 is not None and g > rr95 and g > tr95))
    H["H3"] = dict(value=trimmed_net, trimmed_mean_bp=float(np.sort(pnl)[k:-k].mean()), two_c_bp=float(cost.mean()), round_trip_total_bp=float(2 * cost.mean()),
                   trimmed_minus_rt_total=float(np.sort(pnl - 2 * cost)[k:-k].mean()),
                   rule="pooled ledger: symmetric 1% trimmed mean of (trade - its own book's 2c, PUB) > 0", pass_=bool(trimmed_net > 0))
    H["H4"] = dict(value=top_share, rule="no trade above 10% of the pooled ledger's raw P&L", pass_=bool(top_share is not None and top_share <= 0.10))
    H["H5"] = dict(value=names_half, raw_pnl_basis=None, rule="at least 10 names to half the pooled contribution P&L", pass_=bool(names_half is not None and names_half >= 10))
    H["H6"] = dict(value=obs["sharpe_net_PUB"], after_borrow=(obs["net_bp_borrow_PUB"] / obs["vol_bp"] * np.sqrt(ANN) if obs["vol_bp"] > 0 else None),
                   rule="blend PUB net Sharpe > 0", pass_=bool(np.isfinite(obs["sharpe_net_PUB"]) and obs["sharpe_net_PUB"] > 0))
    H["all_six"] = bool(all(H[h]["pass_"] for h in ("H1", "H2", "H3", "H4", "H5", "H6")))
    return H, dict(pooled_trades=int(pnl.size), trim_k=k)


def read_blend(P, cells_out, raws, blend_draws):
    t0 = time.time()
    a, b = raws
    print(f"\n  BLEND: 50/50 capital of [{a['sig']} {a['arm']}] and [{b['sig']} {b['arm']}] (D356's construction)")
    obs = blend_of(a["res_v"]["book"], a["res_v"]["mask"], b["res_v"]["book"], b["res_v"]["mask"], a["C"], b["C"], a["BV"], b["BV"])
    assert obs is not None, "the blend has fewer than 200 common bars"
    # [LIN] on the common bars
    if obs["mask_mismatch_bars"] == 0:
        lin = abs(obs["net_bp_PUB"] - 0.5 * (a["C"]["PUB"]["net_bp"] + b["C"]["PUB"]["net_bp"]))
        assert lin < 1e-9, f"[LIN] {lin:.2e}"
        print(f"    [LIN] the masks coincide on every bar; blend net == the mean of the parents' to {lin:.1e}")
    else:
        print(f"    [M] the two masks differ on {obs['mask_mismatch_bars']} bars: the blend is scored on the {obs['bars']:,} common bars")
    print(f"    observed: gross {obs['gross_bp']:+.2f}, PUB net {obs['net_bp_PUB']:+.2f} (+GC/HTB {obs['net_bp_borrow_PUB']:+.2f}), PB net {obs['net_bp_PB']:+.2f}, "
          f"PUB net Sharpe {obs['sharpe_net_PUB']:+.3f}, vol {obs['vol_bp']:.1f}, maxDD {obs['maxdd_bp']:.0f}, corr of gross {obs['corr_gross']:+.3f}")
    RRb = {s: [] for s in BLEND_STATS}
    for s_ in sorted(a["RRraw"]):
        ra, rb = a["RRraw"][s_], b["RRraw"][s_]
        bl = blend_of(ra["book"], ra["mask"], rb["book"], rb["mask"], ra["C"], rb["C"], ra["BV"], rb["BV"])
        for s in BLEND_STATS:
            RRb[s].append(np.nan if bl is None else bl[s])
    RRb = {s: np.array(RRb[s], float) for s in BLEND_STATS}
    TRb = blend_null_time(P, raws, blend_draws)
    H, pooled = blend_hurdles(P, raws, obs, RRb, TRb)
    print(f"\n  blend: statistic | observed | time p50 p95 | rank p50 p95")
    table = {}
    for s in ("gross_bp", "net_bp_PUB", "net_bp_borrow_PUB", "sharpe_net_PUB", "net_bp_PB", "sharpe_gross"):
        dA, dR = V48.dist_of(TRb[s], obs[s]), V48.dist_of(RRb[s], obs[s])
        table[s] = dict(observed=obs[s], time_rotation=dA, rank_rotation=dR)
        f_ = lambda v: ("%10.3f" % v) if v is not None and np.isfinite(v) else "%10s" % "--"
        print("    %-20s %s | %s %s | %s %s" % (s, f_(obs[s]), f_(dA["p50"]), f_(dA["p95"]), f_(dR["p50"]), f_(dR["p95"])))
    print_hurdles("blend", H)
    return dict(construction="0.5 * (book_a + book_b) on common bars; cost and borrow the mean of the parents' own per-bar values", parents=[a["sig"], b["sig"]],
                arms=[a["arm"], b["arm"]], observed=obs, pooled_ledger=pooled, hurdles=H, table=table,
                nulls=dict(rank_rotation=dict(shifts=int(RRb["gross_bp"].size), dist={s: V48.dist_of(RRb[s], obs[s]) for s in BLEND_STATS}, per_shift=RRb),
                           time_rotation=dict(draws=blend_draws, seeds=[[W.SEED, STUDY, 200 + i, 0] for i in range(2)],
                                              dist={s: V48.dist_of(TRb[s], obs[s]) for s in BLEND_STATS}, per_draw=TRb)),
                elapsed_s=time.time() - t0)


def load_construction():
    assert CONSTRUCTION.exists(), f"REFUSED: {CONSTRUCTION.relative_to(REPO)} is absent -- the addendum has not named the frozen construction"
    cons = json.loads(CONSTRUCTION.read_text())
    cells = cons.get("cells")
    assert isinstance(cells, list) and 1 <= len(cells) <= 2, "construction: `cells` must list one or two cells"
    for c in cells:
        assert c.get("sig") in SIGS, f"construction: sig must be one of {SIGS}"
        assert int(c.get("k", 0)) == 40, "construction: k must be 40 (pre-reg section 2)"
        assert c.get("arm") in ARMS, f"construction: arm must be one of {ARMS}"
        c["k"] = int(c["k"])
    blend = bool(cons.get("blend", False))
    if blend:
        assert len(cells) == 2 and cells[0]["sig"] != cells[1]["sig"], "construction: a blend needs two cells on different signals"
    cons["blend"] = blend
    cons.setdefault("require_deals", True)
    return cons


def git_head():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(REPO), capture_output=True, text=True, timeout=20).stdout.strip()
    except Exception:
        return None


def stage_read(a):
    t0 = time.time()
    assert a.spend_the_holdout, "REFUSED: --read needs --spend-the-holdout (this read is spent once)"
    assert not RECEIPT.exists(), (f"REFUSED: {RECEIPT.relative_to(REPO)} exists -- the holdout was read on "
                                  f"{json.loads(RECEIPT.read_text()).get('timestamp')}; a second read is not run")
    cons = load_construction()
    H = FIXTURES["holdout"]
    if cons["require_deals"]:
        assert H["deals"].exists(), f"REFUSED: {H['deals'].relative_to(REPO)} is absent -- F0 is part of the construction; run {PULL_CMD} first"
    print(f"D357  THE OUT-OF-SAMPLE READ  construction {json.dumps(cons)}  draws {a.draws} (time rotation) / {a.blend_draws} (paired blend)")
    print("\nASSERTIONS")
    dis_check()
    P_m, _OBS, pipe_worst = stage_pipe(verbose=True)
    del P_m, _OBS
    import gc
    gc.collect()
    # the receipt is written BEFORE any holdout return is read: a crash below still spends the read
    receipt = dict(timestamp=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), construction=cons, draws=a.draws, blend_draws=a.blend_draws,
                   pipe_worst=pipe_worst, git_head=git_head(), runner_sha1=hashlib.sha1(Path(__file__).read_bytes()).hexdigest()[:16],
                   deals_file_present=H["deals"].exists(), note="Holdout reads spent: 1. Not repeated for this or any derived construction.")
    RECEIPT.write_text(json.dumps(receipt, indent=1))
    print(f"\n  receipt written {RECEIPT.relative_to(REPO)} -- the read is now spent")
    repoint("holdout")
    tee = _Tee(sys.stdout)
    with contextlib.redirect_stdout(tee):
        Q = stage_dry("holdout")
    nr_stdout(tee.buf.getvalue())
    print("    [NR] the dry stage's stdout carried no return statistic")
    P = prep_full("holdout", Q)
    cells_out, blend_out, verdicts = run_construction(P, cons, a.draws, a.blend_draws)
    out = dict(note="D357: the one out-of-sample read on the holdout fixture. Variant bp/bar and invariant per trade never compared. "
                    "Holdout reads spent: 1.",
               receipt=receipt, construction=cons, holdout_counts=Q["counts"], pipe_worst=pipe_worst, cells=cells_out, blend=blend_out,
               verdicts=verdicts, statistics=list(V48.STATS), elapsed_s=time.time() - t0, rss=PR.rss_line())
    OUT.write_text(json.dumps(V48.clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s; {PR.rss_line()})")


def run_construction(P, cons, draws, blend_draws):
    """The read proper on a prepared P: every cell, its nulls, groups and hurdles; the blend if named. Fixture-agnostic."""
    print(f"    [ID] nulls as in D348: rank rotation = shifts 1..{W.N_BASE - 1} of the observed gate; time rotation = D348's rotate / draw_offsets / "
          f"check_rotation on the finite mask (imported, not re-implemented); the exit grid is recomputed from the rotated score on invalidation arms")
    cells_out, raws = [], []
    for ci, spec in enumerate(cons["cells"]):
        o, r = read_cell(P, spec, ci, draws)
        cells_out.append(o)
        raws.append(r)
    blend_out = read_blend(P, cells_out, raws, blend_draws) if cons["blend"] else None
    verdicts = {c["label"]: c["hurdles"]["all_six"] for c in cells_out}
    if blend_out:
        verdicts["blend"] = blend_out["hurdles"]["all_six"]
    print("\nVERDICT")
    for k_, v in verdicts.items():
        print(f"  {k_}: {'ALL SIX HOLD -> admission to BOOK.md (sizing and capital are separate decisions)' if v else 'a hurdle FAILS -> the construction is retired'}")
    return cells_out, blend_out, verdicts


def stage_rehearse(a):
    """The read's code path on the MINING fixture with tiny draw counts, writing only to temp/. Not a result: it proves the read
    stage executes end to end (both arms, the blend, the hurdle table, the JSON) before its one execution on the holdout."""
    t0 = time.time()
    if CONSTRUCTION.exists():                                   # the frozen construction, once the addendum names it: rehearse THAT
        cons = json.loads(CONSTRUCTION.read_text())
        cons = dict(cells=cons["cells"], blend=bool(cons.get("blend", False)), require_deals=bool(cons.get("require_deals", True)))
    else:                                                       # before it exists: an arbitrary two-arm construction that exercises every path
        cons = dict(cells=[dict(sig="rsi", k=40, arm="target"), dict(sig="hist_L", k=40, arm="invalidation")], blend=True, require_deals=True)
    print(f"D357  REHEARSAL on the mining fixture -- not a result; draws {a.draws} / {a.blend_draws}; construction {json.dumps(cons)}")
    print("\nASSERTIONS")
    P, _OBS, pipe_worst = stage_pipe(verbose=True)
    cells_out, blend_out, verdicts = run_construction(P, cons, a.draws, a.blend_draws)
    out = dict(note="D357 REHEARSAL on the MINING fixture with tiny draw counts: exercises the read stage; nothing here is a result.",
               construction=cons, pipe_worst=pipe_worst, cells=cells_out, blend=blend_out, verdicts=verdicts, elapsed_s=time.time() - t0)
    f = REPO / "temp" / "d357_rehearsal_mining.json"
    f.write_text(json.dumps(V48.clean(out), indent=1))
    print(f"\nwrote {f.relative_to(REPO)}  ({time.time() - t0:.0f}s; {PR.rss_line()})")


# ------------------------------------------------------------------ selftest
def stage_selftest():
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("\nASSERTIONS")
    dis_check()
    # [K] the re-pointing separates every key without reading either fixture's bars
    repoint("holdout")
    kh, nh, dh = D.cache_key(), Path(R.BC.CACHE), Path(V31.DEALS)
    F = repoint("mining")
    km, nm, dm = D.cache_key(), Path(R.BC.CACHE), Path(V31.DEALS)
    assert kh != km and nh != nm and dh != dm and Path(M.B.FIXTURE) == F["fixture"]
    print(f"    [K] repoint: D303 keys differ ({km} mining, {kh} holdout); npz {nm.name} vs {nh.name}; deals {dm.name} vs {dh.name}; chain aliases are one object")
    # [NR] static, on the dry stage and every helper it calls
    lines = {fn.__name__: nr_static(fn) for fn in (stage_dry, prep_counts, open_fill_counts, lag_and_rotation_checks, dis_check, score_cache_check,
                                                   build_score_cache_subset, _lagged)}
    print(f"    [NR] STATIC: none of {NR_TOKENS_SRC} in the source of {', '.join(f'{k} ({v} lines)' for k, v in lines.items())}")
    # the dry stage on the MINING fixture, stdout captured: [L] and [A] run inside it on the mining gate
    tee = _Tee(sys.stdout)
    with contextlib.redirect_stdout(tee):
        Q = stage_dry("mining")
    n_lines = nr_stdout(tee.buf.getvalue())
    print(f"    [NR] STDOUT: the dry stage's {n_lines} lines contain none of {NR_TOKENS_OUT} ({el()})")
    # [PIPE]
    P, OBS, worst = stage_pipe(Q)
    # [S] on the mining observed cell, both lenses (the read runs the same code on the holdout)
    for lens in ("res_v", "res_i"):
        w, dL, dS, ntr = V48.sign_audit(P, OBS["rsi", 40][lens], f"mining rsi {lens}")
        print(f"    [S] SIGN IN MONEY (mining rsi k=40 {'variant' if lens == 'res_v' else 'invariant'}): {ntr:,} trades equal the open-fill recomputation to {w:.1e}; "
              f"favourable paths pay positively; +50 bp lifts a long {dL:+.1f} bp and a short {dS:+.1f} bp")
    # [6] [PIPE] raises on a perturbed score cache
    rng = np.random.default_rng([W.SEED, STUDY, 6])
    pert = np.array(P["score"]("rsi"), float)
    fin = np.isfinite(pert)
    pert[fin] += rng.normal(0.0, 1.0, int(fin.sum()))
    P6 = dict(P, score=(lambda sig, _p=pert, _s=P["score"]: _p if sig == "rsi" else _s(sig)))
    broke = False
    try:
        V48.observed_cell(P6, "rsi", 40, V48.load_published(), verbose=False)
    except AssertionError:
        broke = True
    assert broke, "[6] [PIPE] passed a perturbed score cache"
    # [6] [NR] raises on a tainted dry function and on a tainted line
    broke = False
    try:
        nr_static(_dry_tainted)
    except AssertionError:
        broke = True
    assert broke, "[6] [NR] static passed a function that prints a return"
    broke = False
    try:
        nr_stdout("counts only\n    PUB net +5.14 bp\n")
    except AssertionError:
        broke = True
    assert broke, "[6] [NR] stdout passed a line carrying a return statistic"
    print(f"    [6] [PIPE] raises on rsi perturbed by N(0,1) in memory; [NR] raises on a dry function that prints float(P['r1T'][100, 0]) and on a captured "
          f"line 'PUB net +5.14 bp'")
    # the invalidation keyword, if present, is inert when absent (the target arm never passes it)
    print(f"    D355's `invalidation=` keyword on W.simulate: {'present' if _inv_supported() else 'ABSENT (invalidation/both arms would be refused at read time)'}")
    print(f"\nOK  assertions pass  ({el()}; {PR.rss_line()})")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--pipe", action="store_true")
    ap.add_argument("--prep", action="store_true")
    ap.add_argument("--pull", action="store_true", help="with --prep: run D331's EDGAR pull re-pointed at the holdout (network)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--read", action="store_true")
    ap.add_argument("--spend-the-holdout", action="store_true")
    ap.add_argument("--rehearse", action="store_true", help="the read's code path on the MINING fixture, tiny draws, output in temp/ (not a result)")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--blend-draws", type=int, default=100)
    ap.add_argument("--force-score-cache", action="store_true", help="rebuild temp/d290_scores_holdout.npz")
    a = ap.parse_args()
    t0 = time.time()
    print(f"D357  the out-of-sample read on the holdout fixture  (memo_load {memo_load.stats()['executed']} scripts executed once)")
    if a.selftest:
        stage_selftest()
    elif a.pipe:
        print("\nASSERTIONS")
        stage_pipe()
        print(f"\nOK  ({time.time() - t0:.0f}s; {PR.rss_line()})")
    elif a.prep or a.dry:
        print("\nASSERTIONS")
        if a.prep:
            dis_check()
            edgar_pull_holdout(run=a.pull)
        repoint("holdout")
        if a.force_score_cache:
            build_score_cache_subset("holdout", force=True)
        tee = _Tee(sys.stdout)
        with contextlib.redirect_stdout(tee):
            Q = stage_dry("holdout")
        n_lines = nr_stdout(tee.buf.getvalue())
        print(f"    [NR] STDOUT: the dry stage's {n_lines} lines contain none of {NR_TOKENS_OUT}")
        c = Q["counts"]
        print(f"\nOK  counts only; timing score cache {c['timing']['score_cache_s']:.0f}s, D303 {c['timing']['d303_s']:.0f}s, prep {c['timing']['prep_counts_s']:.0f}s, "
              f"dry stage {c['timing']['dry_stage_s']:.0f}s; total {time.time() - t0:.0f}s; {PR.rss_line()}")
        if not c["f0"]["present"]:
            print(f"NOTE  no deal filings applied: {PULL_CMD}")
    elif a.read:
        stage_read(a)
    elif a.rehearse:
        stage_rehearse(a)
    else:
        ap.error("one of --selftest, --pipe, --prep [--pull], --dry, --rehearse, --read --spend-the-holdout")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
