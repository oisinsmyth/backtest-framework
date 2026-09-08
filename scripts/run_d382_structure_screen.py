"""D382 -- the market-structure screen on the liquid ETF universe.

    uv run python scripts/run_d382_structure_screen.py --selftest
    uv run python scripts/run_d382_structure_screen.py --scores          build and cache the 19 score grids
    uv run python scripts/run_d382_structure_screen.py --observed        the 76 cells, no nulls
    uv run python scripts/run_d382_structure_screen.py --nulls --draws 200
    uv run python scripts/run_d382_structure_screen.py --report
    --out-dir DIR   (default data/)

Pre-registration: docs/decisions/D382-the-market-structure-screen-on-the-liquid-universe.md (committed e4a36b0, BEFORE this file -- R8)
Fixture: data/fixtures/etf_wide_daily_raw.csv.gz, built and gated by scripts/fetch_etf_universe.py (commit e22350a).

WHY THIS UNIVERSE. Axes B (intrabar shape), D (volume profile) and H (harvested structure) have only ever run on single names, where
the held names measure 37.72 bp/side and D373's book netted -0.063 bp/bar against +3.859 gross. S1's universe charges ~1.5-1.8 bp/side.
The features are unchanged; the cost structure is 20x kinder.

[SPLIT] IS THE ASSERTION THIS STUDY LIVES ON. Mining ends 2019-12-31; 2020-01-01 onward is RESERVED and this runner has no path to
it. The truncation cuts the `cleaned` BAR LISTS as well as the grids -- ragged_structure_scores' own selftest documents why: "the
structure machine and the gap scan read `cleaned`, so slicing the grid alone would hand them the future the audit is testing for."

DIRECTION IS DECLARED LONG (gate 1h). The reversed book is scored and reported separately; a feature that works only reversed is
DIRECTION-INVERTED and counts against its stated mechanism, as D290's wick_asym did.

THE HURDLE THAT MATTERS FOR A DIRECTIONAL BOOK is not the null -- it is BUY-AND-HOLD AT MATCHED EXPOSURE. D290: fifty of fifty-one
long-only books are market drift. [BH] refuses to report an excess without it.

AND THE FAILURE MODE THIS FAMILY HAS is gate 1e, capturability. On single names D290's two strongest intrabar candidates died there:
close_in_range cleared its nulls at CV t +6.19 and min z +12.08 and retained 19% at open entry; wick_asym cleared all three at
t +10.51 with open-entry t -1.77 and 115% of the effect overnight. That is a property of the family, not the universe, so it is
computed here at stage 1 and not deferred.

ASSERTIONS [SPLIT][GATE][LAG][FEAT][DIR][BH][X] -- pre-reg s6.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


RP = _load("ragged_panel", "ragged_panel.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
FB = _load("ragged_features", "ragged_features.py")
PR = _load("ragged_profile", "ragged_profile.py")
ST = _load("ragged_structure_scores", "ragged_structure_scores.py")

STUDY = 382
DATA = REPO / "data"
FIX = DATA / "fixtures" / "etf_wide_daily_raw.csv.gz"
EV = DATA / "fixtures" / "etf_wide_daily_raw_events.json"

MINING_END = "2019-12-31"          # pre-reg s1. 2020-01-01 onward is RESERVED and unreachable from here.
HOLDS = (5, 10, 20, 40)            # reported, never picked (R14 2026-09-03)
PRIMARY_HOLD = 20                  # nominated in advance so one number can be quoted without selection
DECILE = 10.0                      # the extreme decile, as D290 defined an event
WARMUP = 252                       # the screen's own warm-up; no book before it
PPY, RF, BORROW = 252.0, 0.04, 0.0
SEED = 20260908


def out_paths(d):
    d = Path(d)
    return dict(dir=d, scores=d / "d382_scores.npz", observed=d / "d382_observed.json",
                nulls=d / "d382_nulls.json", report=d / "d382_structure_screen.json")


# ------------------------------------------------------------------ [SPLIT]
class _Trunc:
    """A RaggedPanel truncated to the mining window. Every (n, T) array is sliced and `index_of` rebuilt, so nothing downstream can
    reach a reserved bar even by indexing past the end."""

    def __init__(self, p, cut):
        self.symbols, self.dates = p.symbols, list(p.dates)[:cut]
        self.closes, self.live = p.closes[:, :cut], p.live[:, :cut]
        self.log_returns = p.log_returns[:, :cut]
        self.total_log_returns = p.total_log_returns[:, :cut]
        self.cost_fraction = p.cost_fraction
        self.index_of = {s: (a, min(b, cut - 1)) for s, (a, b) in p.index_of.items() if a < cut}

    @property
    def shape(self):
        return self.closes.shape

    def n_live(self):
        return self.live.sum(axis=0)


def split_index(dates):
    return next((i for i, d in enumerate(dates) if str(d) > MINING_END), len(dates))


def assert_SPLIT(panel, cleaned, cut, full_dates):
    """[SPLIT] no reserved bar reaches any grid, score, null or book. Default-deny; there is no override in this file."""
    assert panel.shape[1] == cut, f"[SPLIT] the panel carries {panel.shape[1]} bars, not the mining {cut}"
    assert str(panel.dates[-1]) <= MINING_END, f"[SPLIT] the last mined bar is {panel.dates[-1]}, past {MINING_END}"
    for s, bars in cleaned.items():
        if bars and str(bars[-1].timestamp)[:10] > MINING_END:
            raise AssertionError(f"[SPLIT] {s}'s bar list runs to {bars[-1].timestamp[:10]}, past {MINING_END}")
    return dict(mining_bars=cut, reserved_bars=len(full_dates) - cut, boundary=MINING_END,
                first=str(panel.dates[0]), last=str(panel.dates[-1]))


def truncate(panel, cleaned, cut):
    """Cut the BAR LISTS as well as the grids. ragged_structure_scores' selftest documents why: the structure machine and the gap
    scan read `cleaned`, so slicing the grid alone would hand them the future."""
    keep = {}
    for i, s in enumerate(panel.symbols):
        n_ok = int(panel.live[i, :cut].sum())
        keep[s] = cleaned[s][:n_ok]
    return _Trunc(panel, cut), keep


# ------------------------------------------------------------------ the 19 features
def build_all_scores(panel, cleaned):
    g = P1.build_grids(panel, cleaned)
    live = panel.live
    vol = np.full(panel.shape, np.nan)
    pos = {d: i for i, d in enumerate(panel.dates)}
    for i, s in enumerate(panel.symbols):
        for st in cleaned[s]:
            t = pos.get(str(st.timestamp)[:10])
            if t is not None:
                vol[i, t] = st.bar.volume
    out = {}
    b = FB.intrabar_scores(g, live)
    for k in FB.INTRABAR_SCORES:
        out[k] = np.asarray(b[k], float)
    h = ST.structure_scores(g, cleaned, panel, live)
    for k in ST.STRUCTURE_SCORES:
        out[k] = np.asarray(h[k], float)
    try:
        d, _census = PR.build_profile_scores(panel, cleaned, vol, WARMUP, live=live)
        for k in getattr(PR, "PROFILE_SCORES", tuple(d)):
            if k in d:
                out[k] = np.asarray(d[k], float)
    except Exception as e:                                   # reported, never silently dropped
        out["_profile_error"] = str(e)[:200]
    return out, g, vol


# ------------------------------------------------------------------ events -> positions
def pct_rank(s, live):
    """Cross-sectional percentile within each bar, over LIVE names with a finite score. NaN elsewhere."""
    out = np.full(s.shape, np.nan)
    ok = live & np.isfinite(s)
    for t in range(s.shape[1]):
        m = ok[:, t]
        k = int(m.sum())
        if k < 20:
            continue
        v = s[m, t]
        r = v.argsort().argsort().astype(float)
        out[m, t] = 100.0 * (r + 0.5) / k
    return out


def positions_from(p, live, hold, low_tail=True):
    """A LONG-FLAT book. An event is the percentile CROSSING into the extreme decile, as D290 defined one; the position is held
    `hold` bars from the NEXT bar -- lag = 1, so exposure through bar t is decided on t-1."""
    prev = np.full_like(p, np.nan)
    prev[:, 1:] = p[:, :-1]
    with np.errstate(invalid="ignore"):
        ev = ((p <= DECILE) & (prev > DECILE)) if low_tail else ((p >= 100 - DECILE) & (prev < 100 - DECILE))
    ev &= live
    n, T = p.shape
    pos = np.zeros((n, T))
    idx = np.argwhere(ev)
    for i, t in idx:
        a = t + 1                                            # lag = 1
        pos[i, a:min(a + hold, T)] = 1.0
    pos[:, :WARMUP] = 0.0
    return np.minimum(pos, 1.0), int(ev.sum())


def positions_fast(p, live, hold, low_tail=True):
    """[POS] the same book as `positions_from`, built by a difference array instead of a per-event loop.

    A null pass rebuilds 152 books per draw, so the loop version is unaffordable. `assert_POS` proves the two agree bit-for-bit
    before any draw is taken -- the speed is only allowed because the equality is checked, not assumed.
    """
    prev = np.full_like(p, np.nan)
    prev[:, 1:] = p[:, :-1]
    with np.errstate(invalid="ignore"):
        ev = ((p <= DECILE) & (prev > DECILE)) if low_tail else ((p >= 100 - DECILE) & (prev < 100 - DECILE))
    ev &= live
    n, T = p.shape
    i, t = np.nonzero(ev)
    d = np.zeros((n, T + 1))
    a = np.minimum(t + 1, T)
    b = np.minimum(t + 1 + hold, T)
    np.add.at(d, (i, a), 1.0)
    np.add.at(d, (i, b), -1.0)
    pos = (np.cumsum(d[:, :T], axis=1) > 0).astype(float)
    pos[:, :WARMUP] = 0.0
    return pos, int(ev.sum())


def assert_POS(p, live, hold):
    """[POS] the fast builder equals the loop builder. Checked on a TIE-HEAVY input is not possible here (percentiles are
    distinct by construction), so it is checked on the real grid, which is the input the study actually uses."""
    a, na = positions_from(p, live, hold)
    b, nb = positions_fast(p, live, hold)
    assert na == nb, f"[POS] event counts differ: {na} vs {nb}"
    assert np.array_equal(a > 0, b > 0), "[POS] the fast builder disagrees with the loop builder"
    return True


def trade_cumsum(panel):
    """One cumulative sum of each name's total log return, reused by every draw. A trade [s, e) is C[i, e-1] - C[i, s-1]."""
    tl = np.where(np.isfinite(panel.total_log_returns), panel.total_log_returns, 0.0) * panel.live
    return np.cumsum(tl, axis=1)


def trades_fast(pos, C):
    """Per-trade gross return in bp AND each trade's length in bars, from the precomputed cumulative sum.

    THE LENGTH IS RETURNED BECAUSE THE PER-TRADE MEAN IS NOT SAFE ALONE HERE. Overlapping events merge into ONE run -- a name that
    keeps firing while already held produces a single long trade, not several -- so a "trade" at nominal hold 40 can run far past 40
    bars and its mean is inflated by event DENSITY as well as by hold. That is D374's segmentation confound one level deeper.

    The within-hold null comparison stays fair because both sides merge identically. What is NOT safe is reading the per-trade number
    as an economic per-trade quantity, or comparing it across holds. `bp per BAR HELD` is the segmentation-stable companion and is
    reported beside it everywhere.
    """
    a = pos > 0
    d = np.diff(a.astype(np.int8), axis=1, prepend=0, append=0)
    si, st = np.nonzero(d == 1)
    ei, et = np.nonzero(d == -1)
    if si.size == 0:
        return np.zeros(0), np.zeros(0)
    lo = np.where(st > 0, C[si, np.maximum(st - 1, 0)], 0.0)
    hi = C[ei, np.minimum(et - 1, C.shape[1] - 1)]
    return np.expm1(hi - lo) * 1e4, (et - st).astype(float)


def rate_bp(pnl, ln):
    """bp per BAR HELD -- total P&L over total bars. Stable under the merging `trades_fast` documents."""
    tot = ln.sum()
    return float(pnl.sum() / tot) if tot > 0 else float("nan")


def trades_from(pos, panel):
    """Per-TRADE gross return in bp: each contiguous run of exposure, compounded on that name's own total log returns."""
    tl = panel.total_log_returns
    live = panel.live
    out = []
    a = (pos > 0) & live
    for i in range(a.shape[0]):
        row = a[i]
        if not row.any():
            continue
        d = np.diff(row.astype(np.int8), prepend=0, append=0)
        for s, e in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
            v = tl[i, s:e]
            v = v[np.isfinite(v)]
            if v.size:
                out.append(np.expm1(v.sum()) * 1e4)
    return np.asarray(out, float)


# ------------------------------------------------------------------ audits
def assert_LAG(p, live, hold):
    """[LAG] exposure through bar t is decided on t-1, re-derived by a SECOND implementation that never calls positions_from."""
    pos, _ = positions_from(p, live, hold)
    n, T = p.shape
    ref = np.zeros((n, T))
    for i in range(n):
        for t in range(1, T):
            if live[i, t] and np.isfinite(p[i, t]) and np.isfinite(p[i, t - 1]) and p[i, t] <= DECILE < p[i, t - 1]:
                ref[i, t + 1:min(t + 1 + hold, T)] = 1.0
    ref[:, :WARMUP] = 0.0
    assert np.array_equal(pos > 0, ref > 0), "[LAG] the second implementation disagrees -- the book may read bar t"
    return True


def assert_BH(panel, start):
    """[BH] buy-and-hold at MATCHED exposure. Refuses to produce an excess without an exposure to match."""
    ones = np.ones(panel.shape)
    s = RP.score(panel, ones, start, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
    assert s["exposure_gross"] > 0.9, f"[BH] the comparator's exposure is {s['exposure_gross']:.3f}, not ~1"
    return s


def bh_matched(panel, start, exposure):
    """Buy-and-hold scaled to the candidate's own exposure -- the only fair comparator for a flat-by-default book."""
    return RP.score(panel, np.full(panel.shape, float(exposure)), start, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)


# ------------------------------------------------------------------ stages
def load_mined():
    panel, cleaned = RP.load_ragged(FIX, EV, fee_bps=0.0)     # [GATE] load_ragged runs assert_gates_passed
    full_dates = [str(d) for d in panel.dates]
    cut = split_index(full_dates)
    tp, tc = truncate(panel, cleaned, cut)
    sp = assert_SPLIT(tp, tc, cut, full_dates)
    return tp, tc, sp


def stage_scores(paths):
    print("\nSCORES -- the 19 features on the mined window only")
    t0 = time.time()
    panel, cleaned, sp = load_mined()
    print(f"  [GATE] fixture accepted. [SPLIT] {sp['mining_bars']:,} mined bars {sp['first']} -> {sp['last']}, "
          f"{sp['reserved_bars']:,} reserved and unreachable")
    sc, g, vol = build_all_scores(panel, cleaned)
    err = sc.pop("_profile_error", None)
    names = sorted(sc)
    print(f"  built {len(names)} score grids in {time.time() - t0:.0f}s")
    if err:
        print(f"  [FEAT] axis D (volume profile) did NOT build: {err}")
    for k in names:
        cov = float((np.isfinite(sc[k]) & panel.live).sum() / max(panel.live.sum(), 1))
        print(f"    {k:<18} coverage {cov:6.1%}")
    paths["dir"].mkdir(parents=True, exist_ok=True)
    np.savez_compressed(paths["scores"], **{k: sc[k] for k in names},
                        _live=panel.live, _dates=np.array([str(d) for d in panel.dates]),
                        _symbols=np.array(panel.symbols), _names=np.array(names),
                        _profile_error=np.array([err or ""]))
    print(f"  wrote {paths['scores']} ({time.time() - t0:.0f}s)")
    return names


def cell_stats(panel, p, hold, low_tail=True):
    pos, n_ev = positions_from(p, panel.live, hold, low_tail)
    if n_ev < 50:
        return None
    tr, ln = trades_fast(pos, trade_cumsum(panel))
    if tr.size < 30:
        return None
    s = RP.score(panel, pos, WARMUP, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
    bh = bh_matched(panel, WARMUP, s["exposure_gross"])
    return dict(events=n_ev, trades=int(tr.size), mean_bp=float(tr.mean()), median_bp=float(np.median(tr)),
                bp_per_bar=rate_bp(tr, ln), mean_run_bars=float(ln.mean()),
                excess_sharpe=s["excess_sharpe"], cagr=s["cagr"], exposure=s["exposure_gross"],
                max_drawdown=s["max_drawdown"], entries=s["entries"], clears_E=s["clears_E"],
                bh_matched_cagr=bh["cagr"], bh_matched_sharpe=bh["excess_sharpe"],
                excess_over_bh_cagr=s["cagr"] - bh["cagr"])


def stage_observed(paths):
    print(f"\nOBSERVED -- {len(HOLDS)} holds x the features, LONG declared (gate 1h). No nulls.")
    t0 = time.time()
    panel, cleaned, sp = load_mined()
    z = np.load(paths["scores"], allow_pickle=False)
    names = [str(x) for x in z["_names"]]
    bh1 = assert_BH(panel, WARMUP)
    print(f"  [BH] unit-exposure buy-and-hold: CAGR {bh1['cagr']:+.2%}  Sharpe {bh1['excess_sharpe']:+.3f}")
    out = {}
    for k in names:
        p = pct_rank(z[k], panel.live)
        assert_LAG(p, panel.live, HOLDS[0]) if k == names[0] else None
        for h in HOLDS:
            for tail, tag in ((True, "lo"), (False, "hi")):
                c = cell_stats(panel, p, h, tail)
                if c:
                    out[f"{k}|{h}|{tag}"] = c
        done = [v for kk, v in out.items() if kk.startswith(k + "|")]
        if done:
            best = max(done, key=lambda v: v["mean_bp"])
            print(f"    {k:<18} cells {len(done)}  best mean {best['mean_bp']:+8.2f} bp  "
                  f"excess vs B&H {best['excess_over_bh_cagr']:+.2%}", flush=True)
    paths["observed"].write_text(json.dumps(dict(study=STUDY, split=sp, bh_unit=bh1, cells=out), indent=1))
    print(f"  wrote {paths['observed']}  ({len(out)} cells, {time.time() - t0:.0f}s)")
    return out


def stage_selftest(paths):
    print("\nSELFTEST")
    t0 = time.time()
    panel, cleaned, sp = load_mined()
    print(f"  [GATE][SPLIT] {sp['mining_bars']:,} mined bars {sp['first']} -> {sp['last']}, {sp['reserved_bars']:,} reserved")
    print(f"  [BH] {assert_BH(panel, WARMUP)['cagr']:+.2%} CAGR at unit exposure")
    z = np.load(paths["scores"], allow_pickle=False) if paths["scores"].exists() else None
    if z is not None:
        k = str(z["_names"][0])
        p = pct_rank(z[k], panel.live)
        print(f"  [LAG] re-deriving {k}'s book by a second implementation")
        assert_LAG(p, panel.live, 5)
        print("       agree")

    print("\n  [X] the audits RAISE on a deliberately broken input")
    broken = {}

    def must_raise(name, fn):
        try:
            fn()
        except AssertionError:
            broken[name] = "RAISED"
            return
        broken[name] = "*** DID NOT RAISE ***"
        raise AssertionError(f"[X] {name} did not raise -- a self-test that cannot fail is worse than none")

    full, fullc = RP.load_ragged(FIX, EV, fee_bps=0.0)
    cut = split_index([str(d) for d in full.dates])
    must_raise("split_untruncated_panel", lambda: assert_SPLIT(full, fullc, cut, full.dates))
    tp, tc = truncate(full, fullc, cut)
    bad = dict(tc)
    bad[full.symbols[0]] = fullc[full.symbols[0]]            # one name's bar list left un-cut
    must_raise("split_bar_list_not_cut", lambda: assert_SPLIT(tp, bad, cut, full.dates))

    class _NoExp:
        shape = panel.shape
    must_raise("bh_zero_exposure",
               lambda: assert_BH(_Zero(panel), WARMUP))
    for k, v in broken.items():
        print(f"       {k}: {v}")
    print(f"\n  selftest OK ({time.time() - t0:.0f}s)")
    return True


class _Zero:
    """A panel whose names are never live -- [BH]'s comparator must refuse it rather than divide by nothing."""

    def __init__(self, p):
        self.symbols, self.dates = p.symbols, p.dates
        self.closes, self.log_returns = p.closes, p.log_returns
        self.total_log_returns = p.total_log_returns
        self.cost_fraction = p.cost_fraction
        self.live = np.zeros_like(p.live)
        self.index_of = p.index_of

    @property
    def shape(self):
        return self.closes.shape

    def n_live(self):
        return self.live.sum(axis=0)


# ------------------------------------------------------------------ the three nulls, best-of-152 under a shared draw
def null_rotation(pos, live, off):
    """Per-name timing rolled WITHIN each name's own live window. Rolling across the whole grid would place exposure on bars the
    name did not trade (ragged_panel.rotation_null's own reasoning, and D351's)."""
    out = np.zeros_like(pos)
    n, T = pos.shape
    for i in range(n):
        w = np.flatnonzero(live[i])
        if w.size < 2:
            continue
        s = pos[i, w]
        out[i, w] = np.roll(s, int(off[i]) % w.size)
    return out


def null_permute_bar(p, ok, order, liveorder):
    """The percentile permuted ACROSS NAMES inside each bar, vectorised.

    `order` puts live rows first in RANDOM order (the key is +inf off-mask), `liveorder` puts them first in ROW order. Gathering by
    the second and scattering by the first is a within-column permutation of exactly the live values, with NaN left everywhere else.
    """
    src = np.take_along_axis(np.where(ok, p, np.nan), liveorder, axis=0)
    out = np.full_like(p, np.nan)
    np.put_along_axis(out, order, src, axis=0)
    return out


def perm_indices(ok, rng):
    """One shared permutation per bar, reused by every feature in the draw."""
    n = ok.shape[0]
    key = rng.random(ok.shape)
    key[~ok] = np.inf
    order = np.argsort(key, axis=0)
    liveorder = np.argsort(np.where(ok, np.arange(n)[:, None], n + 1), axis=0)
    return order, liveorder


def stage_nulls(paths, draws):
    print(f"\nNULLS -- {draws} draws x 3 families, best-of-152 floor under a SHARED draw (pre-reg s5 as amended 886c9fe)")
    t0 = time.time()
    panel, cleaned, sp = load_mined()
    z = np.load(paths["scores"], allow_pickle=False)
    names = [str(x) for x in z["_names"]]
    live = panel.live
    C = trade_cumsum(panel)
    obs = json.loads(paths["observed"].read_text())["cells"]

    P = {k: pct_rank(z[k], live) for k in names}
    assert_POS(P[names[0]], live, HOLDS[0])
    print(f"  [POS] the fast builder equals the loop builder on {names[0]}")

    cells = [(k, h, tail) for k in names for h in HOLDS for tail in (True, False)]
    cells = [c for c in cells if f"{c[0]}|{c[1]}|{'lo' if c[2] else 'hi'}" in obs]
    print(f"  {len(cells)} cells carried forward from the observed pass")

    base = {}
    for k, h, tail in cells:
        pos, _ = positions_fast(P[k], live, h, tail)
        base[(k, h, tail)] = pos
    print(f"  base books built ({time.time() - t0:.0f}s)")

    n, T = live.shape
    ok = live & np.isfinite(P[names[0]])
    rng = np.random.default_rng([SEED, STUDY])

    # THE FLOOR IS TAKEN WITHIN A HOLD, not across all 152 cells. A 40-bar hold earns roughly four times a 10-bar hold PER TRADE by
    # construction, so a max over cells spanning four holds is always set by the longest one and is not like-for-like -- D374's
    # segmentation lesson, which cost that study a retracted claim. Each hold gets its own best-of-38 floor (19 features x 2 tails)
    # and is compared only to observed cells at the SAME hold.
    by_hold = {h: [c for c in cells if c[1] == h] for h in HOLDS}
    floors = {f"{fam}|{h}": [] for fam in ("rotation", "permutation") for h in HOLDS}
    rates = {k: [] for k in floors}
    for d in range(draws):
        off = rng.integers(0, T, size=n)                       # ONE offset vector, shared by every cell in the draw
        for h in HOLDS:
            m = r = -np.inf
            for key in by_hold[h]:
                tr, ln = trades_fast(null_rotation(base[key], live, off), C)
                if tr.size >= 30:
                    m = max(m, float(tr.mean()))
                    r = max(r, rate_bp(tr, ln))
            floors[f"rotation|{h}"].append(m)
            rates[f"rotation|{h}"].append(r)

        order, liveorder = perm_indices(ok, rng)               # ONE permutation set, shared by every feature in the draw
        permuted = {k: null_permute_bar(P[k], ok, order, liveorder) for k in names}
        for h in HOLDS:
            m = r = -np.inf
            for k, hh, tail in by_hold[h]:
                pos, _ = positions_fast(permuted[k], live, hh, tail)
                tr, ln = trades_fast(pos, C)
                if tr.size >= 30:
                    m = max(m, float(tr.mean()))
                    r = max(r, rate_bp(tr, ln))
            floors[f"permutation|{h}"].append(m)
            rates[f"permutation|{h}"].append(r)
        if (d + 1) % 10 == 0 or d + 1 == draws:
            print(f"    {d + 1}/{draws} ({time.time() - t0:.0f}s, {(time.time() - t0) / (d + 1):.1f} s/draw)", flush=True)

    out = dict(study=STUDY, draws=draws, cells=len(cells), split=sp,
               floors={k: dict(n=len(v), p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)),
                               max=float(np.max(v))) for k, v in floors.items() if v},
               rate_floors={k: dict(p50=float(np.percentile(v, 50)), p95=float(np.percentile(v, 95)))
                            for k, v in rates.items() if v},
               note=("best-of-38 WITHIN EACH HOLD, under one shared offset / permutation per draw. The floor is NOT taken across "
                     "holds: a 40-bar hold earns ~4x a 10-bar hold per trade by construction, so a cross-hold max is always set by "
                     "the longest hold and is not like-for-like (D374)."))
    paths["nulls"].write_text(json.dumps(out, indent=1))
    print(f"  wrote {paths['nulls']} ({time.time() - t0:.0f}s)")
    for k, v in out["floors"].items():
        print(f"    {k:<12} p50 {v['p50']:+9.2f}  p95 {v['p95']:+9.2f}  max {v['max']:+9.2f} bp")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    for f in ("selftest", "scores", "observed", "nulls", "report"):
        ap.add_argument(f"--{f}", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--out-dir", default=str(DATA))
    a = ap.parse_args()
    print("D382  the market-structure screen on the liquid ETF universe")
    paths = out_paths(a.out_dir)
    if a.scores:
        stage_scores(paths)
    elif a.observed:
        stage_observed(paths)
    elif a.nulls:
        stage_nulls(paths, a.draws)
    elif a.selftest:
        stage_selftest(paths)
    else:
        ap.error("one of --selftest, --scores, --observed, --nulls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
