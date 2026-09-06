"""D363 -- the cost lines on the two-sink fade: the ledger is D362's A2 arm reproduced to 1e-9 and NOTHING about it changes; this record
re-COSTS it (four spread lines from the record's own Corwin-Schultz estimator, three execution bounds, participation) and re-SIZES it
(INV, U) with a within-name weight permutation as U's null. Within-sample measurement; no holdout; nothing promoted (R15).

    uv run python scripts/run_d363_cost_lines.py --selftest
    uv run python scripts/run_d363_cost_lines.py --perm --draws 200 --part 0
    uv run python scripts/run_d363_cost_lines.py --report
    --out-dir DIR    (every stage; default data/ -- the smoke runs pass temp/... so that nothing under data/ is touched)

Pre-registration: docs/decisions/D363-the-cost-lines-on-the-two-sink-fade-entry-window-spread-execution-bounds-and-cost-aware-sizing.md (44292b4)

THE LEDGER: run_d362's A2 arm, built by run_d362's own functions (base -> features -> hit_grids -> arm_signal('A2') -> run_short at cap 10) and
asserted [ID] against data/d362_sink_filter.json: 3,079 trades, mean +61.71, and D362's ledger-median 2c PUB / PB (88.77 / 38.70) to 1e-9.
A trade is (row, e0, age, pnl, side): entry bar t = e0 (the fill is the OPEN of e0), gap day g = e0 - 1, exit bar e = e0 + age - 1 (the close print).

THE ESTIMATOR (the record's: d285_spread_estimate.corwin_schultz, the ONE implementation the score cache and d348_prep use):
    the two-day pair (d, d+1) gives ONE round-trip proportional spread s; s < 0 is set to 0 (the authors' clamp); NaN unless both days are live
    with finite highs and positive lows. corwin_schultz stores the pair at the FIRST day's index; HALF_PB[t] = s(t, t+1) / 2 x 1e4 (so the "per-bar"
    convention at the entry bar reads the entry day and the day AFTER it); HALF_PUB[t] = cs_spread[t-1] / 2 x 1e4 where cs_spread at own bar k is the
    nanmean over the name's own live bars k-20..k of the pair ENDING at each bar (ragged_vol_scores E2: lagged = raw shifted by one own bar), NaN
    unless >= ceil(0.8 x 21) = 17 of the 21 are finite and the name has >= 21 own bars.
    THIS RUNNER'S PER-BAR ESTIMATE hs_bar[t, i] IS THE PAIR (t-1, t) ASSIGNED TO ITS SECOND DAY t (half-spread, bp/side, clamped per pair), so
    that PUB at entry bar t == the 21-own-bar trailing mean of hs_bar ENDING AT t-1 ([CS], 300 samples to 1e-9) and PB at t == hs_bar[t+1].
    The windows follow: EW entry = nanmean of hs_bar over the three bars g-1, g, t (pairs (g-2,g-1), (g-1,g), (g,t)); EW exit = nanmean over
    e-1, e, e+1 (pairs (e-2,e-1), (e-1,e), (e,e+1)); EW1 entry = hs_bar[t] (the pair (g, t)); EW1 exit = hs_bar[e] (the pair (e-1, e)).
    THE CLAMP: every pair is clamped at zero BEFORE averaging (exactly as cs_spread averages clamped pairs); EW is "zero-clamped" when its mean
    is exactly 0 (every finite pair in the window was clamped); EW1 when its single pair was clamped. A window with no finite pair falls back to
    PUB (counted). The high/low grids come from the fixture streamed by this runner (cached in temp/d363_prep/, close and volume asserted equal
    to the prep's CLOSE / VOL bit-identically on the build); the second, independent read behind [EW] and [PART] is d361_export_trades.stream_bars
    (a dict by symbol and date strings) with the formula in plain Python.

TWO 2c CONVENTIONS, both reported and labelled:
    ledger-median (D362's, V47.two_c): 2 x median over the ledger of HALF[e0, row] + 2 x 0.005 / median CLOSE x 1e4 -- used for [ID] only and
    printed beside as "D362";
    per-trade (this record's): each trade charged its own name's half-spread at its own entry and exit bars + 2 x 0.005 / its own AS-TRADED close
    (RAW_CLOSE[e0, row]) x 1e4; net = gross - 2c - borrow (D337's gc_htb). Every cost-line, quintile, bound and sizing table is per-trade.

EXECUTION BOUNDS: full crossing = 2c; half crossing = (entry + exit) / 2 + commission; auction = commission only; borrow always. Participation =
position / (close x volume) at the entry bar and at the exit bar in the fixture's frame -- prices are DIVIDED and volumes MULTIPLIED by the split
factor (the fixture meta), so close x volume == as-traded close x as-traded shares bit-for-bit up to rounding; [PART] recomputes it from the raw bars.

SIZING (weights per trade, mean 1; the statistic is sum w x / sum w, its t = m / se with se = sqrt(sum w^2 (x - m)^2) / sum w, D362's W):
    INV  w = 1 / 2c_PUB(per-trade), normalised to mean 1, capped at INV_CAP = 5 and re-normalised to a fixed point (the cap binds on a few
         near-zero-spread names; the count is reported);
    U    w = 1 on PUB quintiles 0 and 4, 0.5 on 1-3, normalised to mean 1; quintiles are rank-based equal-count bins of the trade's own PUB
         half-spread at entry over the 3,079 trades (ties broken by ledger order).
    PERM (200 draws, seed [SEED, 363, 1, part]): within each name its trades' U-weights are permuted; a name with one trade keeps its weight
    (counted); a permutation equal to the observed vector on a name with >= 2 distinct weights is redrawn (counted); the statistic is net per
    unit capital under PUB (per-trade convention); the weighted deployed net PUB (costed_w) is carried beside.

ASSERTIONS [K][F0][R][HOLDOUT-GUARD][ID][CS][EW][PART][W][PERM][6] -- pre-reg section 7. The holdout guard is run_d362's audit hook, installed
when run_d362 is the FIRST module this file loads (before anything else in the chain executes).
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


D62 = _load("d362r", "run_d362_sink_filter.py")        # FIRST: installs the holdout audit hook and memo_load before any other module of the chain runs
V61, EXP, PREP = D62.V61, D62.EXP, D62.PREP
V60, V59, V58, V53, V49, V47, V50 = D62.V60, D62.V59, D62.V58, D62.V53, D62.V49, D62.V47, D62.V50
EB, G22, BR = D62.EB, D62.G22, D62.BR
SP, VS = PREP.SP, PREP.M.VS                            # the record's Corwin-Schultz (d285_spread_estimate) and the E-score module that windows it
SEED, CONVS = D62.SEED, D62.CONVS
STUDY = 363
ARM, CAP = "A2", D62.CAP
PER_SHARE, BORROW_SCHEME = D62.PER_SHARE, D62.BORROW_SCHEME
run_short, clean = D62.run_short, D62.clean
DATA = REPO / "data"
D362_REPORT = DATA / "d362_sink_filter.json"
FIXTURE = V60.FIXTURE
GRID_CACHE = REPO / "temp" / "d363_prep"
GRID_VERSION = "d363-hl-v1"
SELFTEST_TMP = REPO / "temp" / "d363_selftest"
LINES = ("PUB", "PB", "EW", "EW1")
POSITIONS = (10_000, 25_000, 50_000)
INV_CAP = 5.0
U_SHAPE = (1.0, 0.5, 0.5, 0.5, 1.0)
CS_BARS, MIN_CNT = VS.CS_BARS, int(np.ceil(VS.MIN_FRAC * VS.CS_BARS))
NULL = dict(PERM=1)
PREREG = dict(trades=3_079, mean_bp=61.71, two_c_PUB=88.77, two_c_PB=38.7, q1_ratio=0.75, q3_tol=0.10, q4_share=0.90, q4_position=25_000,
              q8_ew1=0.30, q8_ew=0.15, perm_draws=200)


def out_paths(out_dir):
    d = Path(out_dir)
    return dict(dir=d, perm=str(d / "d363_perm_p{part}.json"), report=d / "d363_cost_lines.json")


def fq(x, nd=2):
    return "-" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:+.{nd}f}"


# ------------------------------------------------------------------ the ledger: D362's A2, by D362's functions
_LEDGER = {}


def ledger(P):
    """D362's A2 arm exactly: base (gated G2 x T2) -> the five features -> the hit grids -> the signal less S1|S2 hits -> run_short at cap 10.
    D362's own [ID] on the base ledger is run on the way. Memoised."""
    if _LEDGER:
        return _LEDGER
    B = D62.base(P)
    T, n = P["T"], P["n"]
    res0 = run_short(P, B["gated"], B["sc"], "cap", CAP)
    idd0 = D62.assert_ID(P, res0)
    F = D62.features(P)
    H, hits = D62.hit_grids(F, T, n)
    sig = D62.arm_signal(ARM, B["gated"], H, hits)
    res = run_short(P, sig, B["sc"], "cap", CAP)
    V53.assert_series_defs(res)
    _LEDGER.update(B=B, res0=res0, base_id=idd0, sig=sig, res=res, trades=res["trades"], events=int(sig.sum()), removed=int(B["gated"].sum() - sig.sum()))
    return _LEDGER


def stored_A2():
    return json.loads(D362_REPORT.read_text())["results"][ARM]["per_trade"]


def assert_ID(P, res, tol=1e-9, tag="[ID]"):
    """The A2 ledger == D362's stored A2: trade count, mean, median, and the ledger-median 2c PUB / PB (V47.two_c, D362's convention) with the
    held half-spreads and price, each to tol; the pre-registration's rounded figures (3,079, +61.71, 88.77 / 38.7) within rounding."""
    s = stored_A2()
    tr = res["trades"]
    pnl = V47.pnl_bp(res)
    m = float(pnl.mean())
    assert all(t[4] == 1 for t in tr), f"{tag} a long in the short ledger"
    assert len(tr) == s["trades"] == PREREG["trades"], f"{tag} {len(tr):,} trades != D362's stored {s['trades']:,}"
    assert abs(m - s["mean_bp"]) < tol, f"{tag} mean {m:.10f} != D362's stored {s['mean_bp']:.10f}"
    assert abs(float(np.median(pnl)) - s["median_bp"]) < tol, f"{tag} median"
    c2 = {cv: V47.two_c(tr, P["HALF"][cv], P["CLOSE"]) for cv in CONVS}
    for cv in CONVS:
        assert abs(c2[cv][0] - s["two_c"][cv]) < tol, f"{tag} 2c {cv} {c2[cv][0]:.10f} != D362's stored {s['two_c'][cv]:.10f}"
        assert abs(c2[cv][1] - s["held_half"][cv]) < tol, f"{tag} held half-spread {cv}"
    assert abs(c2["PUB"][2] - s["held_price"]) < tol, f"{tag} held price"
    assert abs(m - PREREG["mean_bp"]) < 5e-3 and abs(c2["PUB"][0] - PREREG["two_c_PUB"]) < 5e-3 and abs(c2["PB"][0] - PREREG["two_c_PB"]) < 5e-2, \
        f"{tag} the pre-registration's rounded figures differ from the stored values"
    return dict(trades=len(tr), mean_bp=m, stored_mean_bp=s["mean_bp"], median_bp=float(np.median(pnl)), two_c_ledger_median={cv: c2[cv][0] for cv in CONVS},
                stored_two_c=s["two_c"], held_half={cv: c2[cv][1] for cv in CONVS}, held_price=c2["PUB"][2], stored_commission_bp=s["commission_bp"],
                stored_borrow_mean_bp=s["borrow"]["mean_bp"], stored_net_borrow=s["net_per_trade_borrow"])


# ------------------------------------------------------------------ the raw high / low grids (this runner's own stream of the fixture; cached)
def grid_cache_key(P):
    h = hashlib.sha1()
    st = FIXTURE.stat()
    h.update(f"{FIXTURE}:{st.st_size}:{int(st.st_mtime)}".encode())
    h.update(str(P["cache_key"]).encode())
    h.update(GRID_VERSION.encode())
    return h.hexdigest()[:16]


def stream_hl(symbols, dates):
    """HIGH, LOW, CLOSE, VOL (T, n) from the fixture's rows placed by symbol and date exactly as ragged_panel.load_ragged places them."""
    import csv
    import gzip
    sym = {s: i for i, s in enumerate(symbols)}
    pos = {d: t for t, d in enumerate(dates)}
    T, n = len(dates), len(symbols)
    H, L, C, V = (np.full((T, n), np.nan) for _ in range(4))
    seen = 0
    with gzip.open(FIXTURE, "rt") as f:
        r = csv.reader(f)
        head = next(r)
        c = {k: head.index(k) for k in ("timestamp", "symbol", "high", "low", "close", "volume")}
        for row in r:
            i, t = sym.get(row[c["symbol"]]), pos.get(row[c["timestamp"]][:10])
            if i is None or t is None:
                continue
            assert not np.isfinite(C[t, i]), f"duplicate bar {row[c['symbol']]} {row[c['timestamp']][:10]}"
            H[t, i], L[t, i], C[t, i], V[t, i] = float(row[c["high"]]), float(row[c["low"]]), float(row[c["close"]]), float(row[c["volume"]])
            seen += 1
    return H, L, C, V, seen


def hl_grids(P):
    """(HIGH, LOW) (T, n), NaN off live; cached in temp/d363_prep/ keyed on the fixture, the d348 cache key and GRID_VERSION. On a miss the streamed
    CLOSE and VOL must equal the prep's CLOSE / VOL bit-identically and the finite pattern must be exactly the live cells."""
    f = GRID_CACHE / f"hl_{grid_cache_key(P)}.npz"
    if f.exists():
        z = np.load(f)
        H, L = z["high"], z["low"]
        print(f"    [K] d363 high/low grid cache HIT {f.name}")
    else:
        t0 = time.time()
        H, L, C, V, seen = stream_hl(P["symbols"], P["dates"])
        live = np.asarray(P["live"]).T
        assert np.array_equal(C, np.asarray(P["CLOSE"]), equal_nan=True), "[K] the streamed close grid != the prep's CLOSE"
        assert np.array_equal(V, np.asarray(P["VOL"]), equal_nan=True), "[K] the streamed volume grid != the prep's VOL"
        assert seen == int(live.sum()) and np.array_equal(np.isfinite(H), live) and np.array_equal(np.isfinite(L), live), "[K] the streamed bars are not exactly the live cells"
        GRID_CACHE.mkdir(parents=True, exist_ok=True)
        np.savez(f, high=H, low=L)
        print(f"    [K] d363 high/low grid BUILT from {FIXTURE.name} ({seen:,} bars, {time.time() - t0:.0f}s): streamed CLOSE == prep CLOSE and VOL == prep VOL "
              f"bit-identically, high/low finite on exactly the live cells; cached {f.name}")
    assert H.shape == (P["T"], P["n"])
    return H, L


# ------------------------------------------------------------------ the per-bar Corwin-Schultz estimate, assigned to the SECOND day of its pair
def cs_pair_direct(h1, l1, h2, l2):
    """One pair in plain Python: the round-trip proportional spread, clamped at zero; NaN where unusable (the record's rule, corwin_schultz)."""
    if not (math.isfinite(h1) and math.isfinite(h2) and l1 > 0 and l2 > 0 and h1 > 0 and h2 > 0):     # h <= 0 is NaN through numpy's log too
        return math.nan, False
    b = math.log(h1 / l1) ** 2 + math.log(h2 / l2) ** 2
    g = math.log(max(h1, h2) / min(l1, l2)) ** 2
    a = (math.sqrt(2.0 * b) - math.sqrt(b)) / SP.SQ2 - math.sqrt(g / SP.SQ2)
    s = 2.0 * math.expm1(a) / (1.0 + math.exp(a))
    if not math.isfinite(s):
        return math.nan, False
    return max(s, 0.0), s < 0.0


def hs_bar_grid(H, L, live_Tn):
    """hs_bar (T, n): the pair (t-1, t) half-spread in bp/side at index t (its SECOND day), clamped per pair; clamped (T, n) bool marks a pair whose
    raw estimate was negative. Vectorised in the (T, n) orientation, independent of corwin_schultz's (n, T) code path."""
    T, n = H.shape
    ok = live_Tn[:-1] & live_Tn[1:] & np.isfinite(H[:-1]) & np.isfinite(H[1:]) & (L[:-1] > 0) & (L[1:] > 0)
    h1, l1, h2, l2 = H[:-1], L[:-1], H[1:], L[1:]
    with np.errstate(invalid="ignore", divide="ignore"):
        b = np.log(h1 / l1) ** 2 + np.log(h2 / l2) ** 2
        g = np.log(np.maximum(h1, h2) / np.minimum(l1, l2)) ** 2
        a = (np.sqrt(2.0 * b) - np.sqrt(b)) / SP.SQ2 - np.sqrt(g / SP.SQ2)
        s = 2.0 * np.expm1(a) / (1.0 + np.exp(a))
    s = np.where(ok & np.isfinite(s), s, np.nan)
    neg = np.isfinite(s) & (s < 0.0)
    s = np.where(np.isfinite(s), np.maximum(s, 0.0), np.nan)
    hs = np.full((T, n), np.nan)
    hs[1:] = s / 2.0 * 1e4
    cl = np.zeros((T, n), bool)
    cl[1:] = neg
    return hs, cl


def pub_direct(hs_bar, own, t, i, end_shift=1):
    """The record's PUB rule at (t, i) from hs_bar: the 21 own live bars ending at t - end_shift (own[i] = the name's live bar indices), NaN unless the
    name has >= 21 own bars up to there and >= 17 of the 21 are finite; the nanmean of the clamped pairs."""
    at = own[i]
    k = np.searchsorted(at, t - end_shift)
    if k >= at.size or at[k] != t - end_shift or k < CS_BARS - 1:
        return math.nan
    w = hs_bar[at[k - CS_BARS + 1:k + 1], i]
    if int(np.isfinite(w).sum()) < MIN_CNT:
        return math.nan
    return float(np.nanmean(w))


def own_bars(live_Tn):
    return [np.flatnonzero(live_Tn[:, i]) for i in range(live_Tn.shape[1])]


def assert_CS(P, hs_bar, own, rng, k=300, tol=1e-9, end_shift=1, tag="[CS]"):
    """PUB: at k sampled live name-bars with finite HALF_PUB, the 21-own-bar trailing nanmean of hs_bar ending at t-1 == P['HALF']['PUB'][t, i] to
    tol, and at k sampled live name-bars (finite or not) the NaN pattern agrees (the clamp and count rules identical); PB: at k sampled name-bars
    P['HALF']['PB'][t, i] == hs_bar[t+1, i] (the pair (t, t+1)) to tol with the same NaN pattern; the clamp: hs_bar >= 0 everywhere finite and
    exactly 0 where the pair was clamped."""
    PUB, PB = np.asarray(P["HALF"]["PUB"]), np.asarray(P["HALF"]["PB"])
    live = np.asarray(P["live"]).T
    T, n = PUB.shape
    ft, fi = np.nonzero(np.isfinite(PUB))
    pick = rng.choice(ft.size, size=k, replace=False)
    worst = 0.0
    for j in pick:
        t, i = int(ft[j]), int(fi[j])
        mine = pub_direct(hs_bar, own, t, i, end_shift)
        assert math.isfinite(mine), f"{tag} PUB finite at ({P['dates'][t]}, {P['symbols'][i]}) but the direct window is NaN"
        worst = max(worst, abs(mine - float(PUB[t, i])))
        assert worst < tol, f"{tag} PUB at ({P['dates'][t]}, {P['symbols'][i]}): window {mine:.12f} != HALF_PUB {float(PUB[t, i]):.12f}"
    lt, li = np.nonzero(live[1:])
    lt = lt + 1
    pick2 = rng.choice(lt.size, size=k, replace=False)
    n_nan = 0
    for j in pick2:
        t, i = int(lt[j]), int(li[j])
        mine, ref = pub_direct(hs_bar, own, t, i, end_shift), float(PUB[t, i])
        assert math.isnan(mine) == math.isnan(ref), f"{tag} PUB NaN pattern differs at ({P['dates'][t]}, {P['symbols'][i]}): window {mine} vs HALF_PUB {ref}"
        if math.isnan(ref):
            n_nan += 1
        else:
            assert abs(mine - ref) < tol, f"{tag} PUB at ({P['dates'][t]}, {P['symbols'][i]})"
    pt, pi = np.nonzero(live[:-1])
    pick3 = rng.choice(pt.size, size=k, replace=False)
    worst_pb, n_pb_nan = 0.0, 0
    for j in pick3:
        t, i = int(pt[j]), int(pi[j])
        mine, ref = float(hs_bar[t + 1, i]), float(PB[t, i])
        assert math.isnan(mine) == math.isnan(ref), f"{tag} PB NaN pattern differs at ({P['dates'][t]}, {P['symbols'][i]})"
        if math.isnan(ref):
            n_pb_nan += 1
            continue
        worst_pb = max(worst_pb, abs(mine - ref))
        assert worst_pb < tol, f"{tag} PB at ({P['dates'][t]}, {P['symbols'][i]}): hs_bar[t+1] {mine:.12f} != HALF_PB {ref:.12f}"
    fin = np.isfinite(hs_bar)
    assert (hs_bar[fin] >= 0.0).all(), f"{tag} a negative per-bar estimate survived the clamp"
    zero_share = float((hs_bar[fin] == 0.0).mean())
    return dict(sampled=int(k), worst_pub=worst, nan_sampled=n_nan, worst_pb=worst_pb, pb_nan_sampled=n_pb_nan, finite_cells=int(fin.sum()), zero_share=zero_share,
                universe_median_bp=float(np.median(hs_bar[fin])), pub_universe_median_bp=float(np.nanmedian(PUB)), pb_universe_median_bp=float(np.nanmedian(PB)))


# ------------------------------------------------------------------ the windows and the cost lines, per trade
def trade_bars(trades):
    tr = np.array([(r, e0, a) for r, e0, a, _p, _s in trades], dtype=np.int64)
    rows, e0s, ages = tr[:, 0], tr[:, 1], tr[:, 2]
    return rows, e0s, e0s - 1, e0s + ages - 1


def window_mean(hs_bar, clamped, bars, row, T):
    """nanmean of hs_bar over the given global bars for one name (bars outside [0, T) are skipped); returns (value, n_finite, n_clamped)."""
    vals, ncl = [], 0
    for b in bars:
        if 0 <= b < T:
            v = hs_bar[b, row]
            if np.isfinite(v):
                vals.append(float(v))
                ncl += int(clamped[b, row])
    if not vals:
        return math.nan, 0, 0
    return float(np.mean(vals)), len(vals), ncl


def windows(P, trades, hs_bar, clamped):
    """Per trade: EW entry (g-1, g, t), EW exit (e-1, e, e+1), EW1 entry (the pair (g, t) = hs_bar[t]), EW1 exit (the pair (e-1, e) = hs_bar[e]);
    the fallback to PUB where a window has no finite pair; the zero flags."""
    T = P["T"]
    PUB = np.asarray(P["HALF"]["PUB"])
    rows, e0s, gs, es = trade_bars(trades)
    N = rows.size
    out = {k: np.full(N, np.nan) for k in ("EW_in", "EW_out", "EW1_in", "EW1_out", "PUB")}
    cnt = {k: np.zeros(N, np.int64) for k in ("EW_in_n", "EW_out_n", "EW_in_clamped", "EW_out_clamped")}
    fb = {k: np.zeros(N, bool) for k in ("EW_in", "EW_out", "EW1_in", "EW1_out")}
    zero = {k: np.zeros(N, bool) for k in ("EW_in", "EW_out", "EW1_in", "EW1_out")}
    for j in range(N):
        r, t, g, e = int(rows[j]), int(e0s[j]), int(gs[j]), int(es[j])
        pub = float(PUB[t, r])
        out["PUB"][j] = pub
        v, nf, ncl = window_mean(hs_bar, clamped, (g - 1, g, t), r, T)
        cnt["EW_in_n"][j], cnt["EW_in_clamped"][j] = nf, ncl
        if nf == 0:
            fb["EW_in"][j], v = True, pub
        else:
            zero["EW_in"][j] = v == 0.0
        out["EW_in"][j] = v
        v, nf, ncl = window_mean(hs_bar, clamped, (e - 1, e, e + 1), r, T)
        cnt["EW_out_n"][j], cnt["EW_out_clamped"][j] = nf, ncl
        if nf == 0:
            fb["EW_out"][j], v = True, pub
        else:
            zero["EW_out"][j] = v == 0.0
        out["EW_out"][j] = v
        v = float(hs_bar[t, r])
        if not np.isfinite(v):
            fb["EW1_in"][j], v = True, pub
        else:
            zero["EW1_in"][j] = v == 0.0                              # zero-clamped: exactly 0 (the clamp is the only way there; `clamped` counts the pairs)
        out["EW1_in"][j] = v
        v = float(hs_bar[e, r])
        if not np.isfinite(v):
            fb["EW1_out"][j], v = True, pub
        else:
            zero["EW1_out"][j] = v == 0.0
        out["EW1_out"][j] = v
    assert np.isfinite(out["PUB"]).all(), "a trade with no PUB half-spread at entry"
    return dict(values=out, counts=cnt, fallback=fb, zero=zero, rows=rows, e0=e0s, g=gs, e=es)


def cost_lines(P, trades, Wd):
    """Per-trade arrays: gross, commission (2 x 0.005 / AS-TRADED close at e0 x 1e4), borrow (D337 gc_htb), and for each line its entry and exit
    half-spread, 2c = entry + exit + commission, net = gross - 2c - borrow, plus the three execution bounds."""
    v = Wd["values"]
    rows, e0s = Wd["rows"], Wd["e0"]
    gross = np.array([t[3] for t in trades]) * 1e4
    px = np.asarray(P["RAW_CLOSE"])[e0s, rows].astype(float)
    assert np.isfinite(px).all() and (px > 0).all(), "a non-positive as-traded close at entry"
    comm = 2.0 * PER_SHARE / px * 1e4
    borrow, htb, _rate = V49.borrow_of(P, trades)
    borrow = np.asarray(borrow, float)
    PB = np.asarray(P["HALF"]["PB"])[e0s, rows].astype(float)
    pb_fb = ~np.isfinite(PB)                                          # the pair (t, t+1) has no day after (a delisting at t+1, or the panel's last bar):
    PB = np.where(pb_fb, v["PUB"], PB)                                # D362's V47.two_c nanmedian-ed these away; here they fall back to PUB and are counted
    Wd["fallback"]["PB"] = pb_fb
    side = dict(PUB=(v["PUB"], v["PUB"]), PB=(PB, PB), EW=(v["EW_in"], v["EW_out"]), EW1=(v["EW1_in"], v["EW1_out"]))
    L = {}
    for ln in LINES:
        ent, ex = side[ln]
        spread = ent + ex
        two_c = spread + comm
        L[ln] = dict(entry=ent, exit=ex, spread=spread, two_c=two_c, net=gross - two_c - borrow, net_half=gross - spread / 2.0 - comm - borrow)
    return dict(gross=gross, comm=comm, borrow=borrow, htb=np.asarray(htb, bool), px=px, net_auction=gross - comm - borrow, lines=L)


def raw_bars_for(P, trades, idx):
    """The second, independent read of the fixture for the sampled trades: d361_export_trades.stream_bars on the bars g-2..t and e-2..e+1 of each."""
    symbols, dates, T = P["symbols"], P["dates"], P["T"]
    rows, e0s, gs, es = trade_bars(trades)
    want = set()
    for j in idx:
        s = symbols[int(rows[j])]
        for b in list(range(int(gs[j]) - 2, int(e0s[j]) + 1)) + list(range(int(es[j]) - 2, int(es[j]) + 2)):
            if 0 <= b < T:
                want.add((s, dates[b]))
    return EXP.stream_bars(want)


def assert_EW(P, trades, Wd, bars, idx, tol=1e-9, tag="[EW]"):
    """On the sampled trades every window value (EW entry / exit, EW1 entry / exit) equals a plain-Python recomputation from the raw high / low read by
    symbol and date strings (a missing bar is a NaN pair; each pair clamped; the mean of the finite pairs; the fallback to PUB where none), and the
    fallback / zero flags agree."""
    symbols, dates, T = P["symbols"], P["dates"], P["T"]
    v, fb, zero = Wd["values"], Wd["fallback"], Wd["zero"]
    worst, n_fb, n_zero = 0.0, 0, 0

    def pair(s, b):
        k1, k2 = (s, dates[b - 1]) if b - 1 >= 0 else None, (s, dates[b]) if 0 <= b < T else None
        if k1 is None or k2 is None or k1 not in bars or k2 not in bars:
            return math.nan, False
        h1, l1 = bars[k1][1], bars[k1][2]
        h2, l2 = bars[k2][1], bars[k2][2]
        return cs_pair_direct(h1, l1, h2, l2)

    for j in idx:
        r, t, g, e = int(Wd["rows"][j]), int(Wd["e0"][j]), int(Wd["g"][j]), int(Wd["e"][j])
        s = symbols[r]
        pub = float(v["PUB"][j])
        for key, wbars in (("EW_in", (g - 1, g, t)), ("EW_out", (e - 1, e, e + 1))):
            ps = [pair(s, b) for b in wbars]
            fin = [p for p, _c in ps if math.isfinite(p)]
            if not fin:
                direct, dfb, dz = pub, True, False
            else:
                direct = sum(x / 2.0 * 1e4 for x in fin) / len(fin)
                dfb, dz = False, direct == 0.0
            assert dfb == bool(fb[key][j]) and dz == bool(zero[key][j]), f"{tag} {key} flags differ on trade {j} ({s} {dates[t]}): direct fb {dfb} zero {dz}"
            worst = max(worst, abs(direct - float(v[key][j])))
            assert worst < tol, f"{tag} {key} on trade {j} ({s} {dates[t]}): direct {direct:.10f} != grid {float(v[key][j]):.10f}"
            n_fb += dfb
            n_zero += dz
        for key, b in (("EW1_in", t), ("EW1_out", e)):
            p, _c = pair(s, b)
            if math.isfinite(p):
                direct, dfb, dz = p / 2.0 * 1e4, False, p == 0.0
            else:
                direct, dfb, dz = pub, True, False
            assert dfb == bool(fb[key][j]) and dz == bool(zero[key][j]), f"{tag} {key} flags differ on trade {j} ({s} {dates[t]})"
            worst = max(worst, abs(direct - float(v[key][j])))
            assert worst < tol, f"{tag} {key} on trade {j} ({s} {dates[t]}): direct {direct:.10f} != grid {float(v[key][j]):.10f}"
    return dict(sampled=len(idx), worst=worst, fallbacks_in_sample=n_fb, zeros_in_sample=n_zero, bars=len(bars))


# ------------------------------------------------------------------ participation
def participation(P, trades, Wd):
    """position / (close x volume) at the entry bar e0 and the exit bar e, in the fixture's frame (== as-traded close x as-traded shares); NaN where
    the dollar volume is not finite or is zero (counted)."""
    CLOSE, VOL = np.asarray(P["CLOSE"]), np.asarray(P["VOL"])
    rows, e0s, es = Wd["rows"], Wd["e0"], Wd["e"]
    out = dict(dv_entry=CLOSE[e0s, rows] * VOL[e0s, rows], dv_exit=CLOSE[es, rows] * VOL[es, rows])
    for k in ("dv_entry", "dv_exit"):
        dv = out[k]
        bad = ~np.isfinite(dv) | (dv <= 0)
        out[k + "_bad"] = int(bad.sum())
        for pos in POSITIONS:
            with np.errstate(divide="ignore", invalid="ignore"):
                out[f"part_{k[3:]}_{pos}"] = np.where(bad, np.nan, pos / dv)
    return out


def part_summary(PT):
    out = {}
    for bar in ("entry", "exit"):
        out[bar] = dict(dollar_volume_bad=PT[f"dv_{bar}_bad"], dollar_volume_median=float(np.nanmedian(PT[f"dv_{bar}"])))
        for pos in POSITIONS:
            x = PT[f"part_{bar}_{pos}"]
            f = x[np.isfinite(x)]
            out[bar][str(pos)] = dict(median=float(np.median(f)), p90=float(np.quantile(f, .9)), p99=float(np.quantile(f, .99)),
                                      share_under_1pct=float((f < 0.01).mean()), share_under_5pct=float((f < 0.05).mean()), n=int(f.size))
    return out


def assert_PART(P, trades, Wd, PT, bars, idx, rtol=1e-12, tag="[PART]"):
    """On the sampled trades participation == position / (raw close x raw volume) at the entry and the exit bar from the raw bars read by strings."""
    symbols, dates = P["symbols"], P["dates"]
    worst = 0.0
    for j in idx:
        r, t, e = int(Wd["rows"][j]), int(Wd["e0"][j]), int(Wd["e"][j])
        s = symbols[r]
        for bar, b in (("entry", t), ("exit", e)):
            k = (s, dates[b])
            assert k in bars, f"{tag} the raw bar {k} is missing (the name is not live on its {bar} bar?)"
            cl, vo = bars[k][3], bars[k][4]
            dv = cl * vo
            for pos in POSITIONS:
                mine = float(PT[f"part_{bar}_{pos}"][j])
                if not (math.isfinite(dv) and dv > 0):
                    assert math.isnan(mine), f"{tag} {s} {dates[b]}: zero dollar volume but participation {mine}"
                    continue
                direct = pos / dv
                err = abs(mine - direct) / direct
                worst = max(worst, err)
                assert err < rtol, f"{tag} {s} {dates[b]} ${pos:,}: {mine!r} != {direct!r}"
    return dict(sampled=len(idx), worst_rel=worst)


# ------------------------------------------------------------------ quintiles and the sizing arms
def quintiles(pub):
    """Rank-based equal-count bins (0 tightest .. 4 widest) of the trade's own PUB half-spread at entry; ties broken by ledger order (stable sort)."""
    N = pub.size
    order = np.argsort(pub, kind="stable")
    q = np.empty(N, np.int64)
    q[order] = np.arange(N) * 5 // N
    return q


def weights_INV(two_c_pub, cap=INV_CAP, max_iter=100):
    """w = 1 / 2c_PUB (per trade), normalised to mean 1, capped at `cap`, re-normalised -- iterated to the fixed point (mean 1, max <= cap)."""
    assert (two_c_pub > 0).all(), "a non-positive per-trade 2c PUB (commission alone is positive)"
    w0 = 1.0 / two_c_pub
    w = w0 / w0.mean()
    raw_max = float(w.max())
    for _ in range(max_iter):
        w2 = np.minimum(w / w.mean(), cap)
        if np.abs(w2 - w).max() < 1e-13:
            w = w2
            break
        w = w2
    w = w / w.mean()
    assert abs(w.mean() - 1.0) < 1e-12 and w.max() <= cap * (1 + 1e-9), "INV did not converge"
    return w, dict(cap=cap, binding=int((w >= cap * (1 - 1e-9)).sum()), uncapped_max=raw_max, min=float(w.min()), max=float(w.max()))


def weights_U(q):
    w = np.array([U_SHAPE[int(x)] for x in q], float)
    return w / w.mean()


def wstats(x, w):
    W = float(w.sum())
    m = float((w * x).sum() / W)
    se = float(np.sqrt(((w ** 2) * (x - m) ** 2).sum()) / W)
    return dict(mean=m, se=se, t=m / se if se > 0 else None)


def arm_block(CL, w, label):
    """Gross and net per unit capital under every line and bound (sum w x / sum w), the t on the weighted mean, capital used = sum w / n."""
    g = wstats(CL["gross"], w)
    out = dict(arm=label, n=int(w.size), capital_used=float(w.sum() / w.size), sum_w=float(w.sum()), gross=g, comm=wstats(CL["comm"], w)["mean"],
               borrow=wstats(CL["borrow"], w)["mean"], net_auction=wstats(CL["net_auction"], w), lines={}, weight_min=float(w.min()), weight_max=float(w.max()))
    for ln in LINES:
        L = CL["lines"][ln]
        out["lines"][ln] = dict(two_c=wstats(L["two_c"], w)["mean"], spread=wstats(L["spread"], w)["mean"], net=wstats(L["net"], w), net_half=wstats(L["net_half"], w))
    return out


def wgrid_of(trades, w, T, n):
    """(T, n) grid holding each trade's weight at its (e0, row) -- one trade per cell (a name is entered at most once per bar), NaN elsewhere."""
    g = np.full((T, n), np.nan)
    for j, (row, e0, _a, _p, _s) in enumerate(trades):
        assert np.isnan(g[e0, row]), "two trades on one (e0, row)"
        g[e0, row] = w[j]
    return g


def assert_W(P, res, w, tol=1e-12, tag="[W]"):
    """D362's [W] with this record's weights: every trade's weight read off the grid at its (e0, row) == the vector; with every weight 1 the weighted
    rebuild == V58.rebuild exactly and == the kernel's book_dep_x to tol, and costed_w == G22.costed key for key on both conventions; with the arm's
    weights the series x sum w == the bar-loop second implementation to tol and sums to sum w pnl to 1e-9; sum w pnl / sum w == a plain loop;
    capital used == sum w / n."""
    tr = res["trades"]
    T, n = P["T"], P["n"]
    wgrid = wgrid_of(tr, w, T, n)
    wv = D62.weights_of(tr, wgrid)
    assert np.array_equal(wv, w), f"{tag} the grid weights differ from the vector"
    ones = np.ones_like(wgrid)
    reb1, cw1, ew1 = D62.rebuild_w(tr, P, ones)
    reb0, cnt0, ent0 = V58.rebuild(tr, P, hedged=True)
    assert np.array_equal(reb1, reb0) and np.array_equal(cw1, cnt0.astype(float)) and np.array_equal(ew1, ent0.astype(float)), f"{tag} unit weights != V58.rebuild"
    held = res["held"].astype(np.int64)
    covered = cnt0 == held
    S1 = D62.series_w(tr, P, ones)
    bd = np.asarray(res["book_dep_x"], float)
    worst1 = float(np.abs(np.nan_to_num(S1["book"][covered]) - np.nan_to_num(bd[covered])).max())
    assert worst1 < tol, f"{tag} the unit-weight series differs from the kernel's book_dep_x ({worst1:.2e})"
    for cv in CONVS:
        mine = D62.costed_w(tr, S1, P, cv)
        ref = G22.costed(dict(trades=tr, book=S1["book"], mask=S1["mask"], ent=ent0, held=cnt0), P["G4"][cv])
        for k in ref:
            assert mine[k] == ref[k], f"{tag} costed_w[{k}] != G22.costed with unit weights ({cv})"
    S = D62.series_w(tr, P, wgrid)
    sx, cw = D62.weighted_loop(tr, P, wgrid)
    worst2 = float(np.abs(np.nan_to_num(S["book"] * S["held_w"]) - sx).max())
    assert worst2 < tol and float(np.abs(S["held_w"] - cw).max()) < tol, f"{tag} the weighted series x sum w differs from the bar loop ({worst2:.2e})"
    pnl = D62.pnl_bp_of(tr)
    assert abs(float(S["signed"].sum()) * 1e4 - float((w * pnl).sum())) < 1e-9, f"{tag} the weighted rebuild does not sum to sum w pnl"
    num = den = 0.0
    for j, (_r, _e, _a, p, _s) in enumerate(tr):
        num += w[j] * p * 1e4
        den += w[j]
    m = float((w * pnl).sum() / w.sum())
    assert abs(m - num / den) < 1e-9, f"{tag} sum w pnl / sum w != the direct loop"
    cap = float(w.sum() / len(tr))
    assert abs(cap - float(w.mean())) < 1e-15 and abs(cap - den / len(tr)) < 1e-12, f"{tag} capital used != sum w / n"
    return dict(worst_unit=worst1, worst_loop=worst2, mean_w_bp=m, capital=cap, sum_w=float(w.sum()), n=len(tr), wgrid=wgrid)


def deployed_w(res, P, wgrid):
    d = D62.deployed_block_w(res, P, wgrid)
    d.pop("_series", None)
    return d


# ------------------------------------------------------------------ the within-name permutation null for U
def name_groups(trades):
    g = {}
    for j, (row, _e, _a, _p, _s) in enumerate(trades):
        g.setdefault(int(row), []).append(j)
    return {i: np.array(v) for i, v in sorted(g.items())}


def perm_draw(w, groups, rng, max_redraw=64):
    """Within each name the U-weights of its trades permuted; a name with one trade (or one distinct weight) keeps its vector; a permutation equal to
    the observed vector on a name with >= 2 distinct weights is redrawn. Returns (permuted weights, redraws)."""
    wp = w.copy()
    redraw = 0
    for _i, idx in groups.items():
        if idx.size < 2:
            continue
        blk = w[idx]
        if np.unique(blk).size < 2:
            continue
        for _ in range(max_redraw):
            perm = rng.permutation(idx.size)
            cand = blk[perm]
            if not np.array_equal(cand, blk):
                break
            redraw += 1
        else:
            raise AssertionError("[PERM] no changing permutation found")
        wp[idx] = cand
    return wp, redraw


def assert_PERM(w, wp, groups, tag="[PERM]"):
    """Every name's weight multiset kept (sorted equality); single-trade names and constant-weight names keep their vector exactly; on every name with
    >= 2 distinct weights the permuted vector differs from the observed; the whole vector differs from the observed; sum w unchanged."""
    n_single = n_const = n_var = 0
    for _i, idx in groups.items():
        assert np.array_equal(np.sort(w[idx]), np.sort(wp[idx])), f"{tag} name {_i}: the weight multiset changed"
        if idx.size < 2:
            n_single += 1
            assert np.array_equal(w[idx], wp[idx]), f"{tag} a single-trade name's weight changed"
        elif np.unique(w[idx]).size < 2:
            n_const += 1
            assert np.array_equal(w[idx], wp[idx]), f"{tag} a constant-weight name's vector changed"
        else:
            n_var += 1
            assert not np.array_equal(w[idx], wp[idx]), f"{tag} name {_i}: the permuted vector is the observed one"
    assert not np.array_equal(w, wp), f"{tag} the permuted vector equals the observed"
    assert abs(float(w.sum()) - float(wp.sum())) < 1e-9, f"{tag} sum w changed"
    return dict(names=len(groups), single=n_single, constant=n_const, variable=n_var)


def perm_stat(CL, wp, res, P):
    """The statistic per draw: net per unit capital under PUB (per-trade convention); gross, net PB / EW and the weighted deployed net PUB beside."""
    out = dict(net_PUB=wstats(CL["lines"]["PUB"]["net"], wp)["mean"], net_PB=wstats(CL["lines"]["PB"]["net"], wp)["mean"],
               net_EW=wstats(CL["lines"]["EW"]["net"], wp)["mean"], gross=wstats(CL["gross"], wp)["mean"])
    S = D62.series_w(res["trades"], P, wgrid_of(res["trades"], wp, P["T"], P["n"]))
    out["deployed_net_PUB"] = D62.costed_w(res["trades"], S, P, "PUB")["net_bp"]
    return out


# ------------------------------------------------------------------ the shared build
def build(P, with_fixture=True, sample_seed=97):
    """Everything the stages share: the ledger, [ID], the grids, hs_bar, [CS], the windows, the cost lines, participation, the sampled raw-bar
    checks ([EW], [PART]; with_fixture=False skips the fixture read), the quintiles and the arms."""
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    LG = ledger(P)
    res, tr = LG["res"], LG["trades"]
    idd = assert_ID(P, res)
    print(f"    [ID] the A2 ledger == D362's stored A2: {idd['trades']:,} trades, mean {idd['mean_bp']:+.6f} == stored {idd['stored_mean_bp']:+.6f}; ledger-median 2c PUB "
          f"{idd['two_c_ledger_median']['PUB']:.6f} / PB {idd['two_c_ledger_median']['PB']:.6f} == stored {idd['stored_two_c']['PUB']:.6f} / {idd['stored_two_c']['PB']:.6f}; held "
          f"half-spread and price also to 1e-9; D362's own [ID] on the base ledger ({LG['base_id']['trades']:,}, {LG['base_id']['mean_bp']:+.4f}) passed on the way ({el()})")
    H, L = hl_grids(P)
    live = np.asarray(P["live"]).T
    hs_bar, clamped = hs_bar_grid(H, L, live)
    own = own_bars(live)
    cs = assert_CS(P, hs_bar, own, np.random.default_rng([SEED, STUDY, sample_seed]))
    print(f"    [CS] hs_bar = the pair (t-1, t) at its SECOND day t, clamped per pair: its 21-own-bar trailing nanmean ending at t-1 (>= 17 finite, >= 21 own bars) == "
          f"HALF_PUB at {cs['sampled']} sampled finite name-bars to {cs['worst_pub']:.0e} and the NaN pattern agrees on {cs['sampled']} sampled live name-bars ({cs['nan_sampled']} NaN); "
          f"HALF_PB[t] == hs_bar[t+1] (the pair (t, t+1)) at {cs['sampled']} samples to {cs['worst_pb']:.0e} ({cs['pb_nan_sampled']} NaN); hs_bar >= 0 on all {cs['finite_cells']:,} "
          f"finite cells, exactly 0 on {100 * cs['zero_share']:.1f}% (the clamp); universe medians hs_bar {cs['universe_median_bp']:.1f} / PB {cs['pb_universe_median_bp']:.1f} / "
          f"PUB {cs['pub_universe_median_bp']:.1f} bp/side ({el()})")
    Wd = windows(P, tr, hs_bar, clamped)
    CL = cost_lines(P, tr, Wd)
    PT = participation(P, tr, Wd)
    out = dict(LG=LG, res=res, trades=tr, ID=idd, hs_bar=hs_bar, clamped=clamped, own=own, H=H, L=L, CS=cs, Wd=Wd, CL=CL, PT=PT)
    if with_fixture:
        rng = np.random.default_rng([SEED, STUDY, sample_seed + 1])
        idx = np.sort(rng.choice(len(tr), size=300, replace=False))
        bars = raw_bars_for(P, tr, idx)
        ew = assert_EW(P, tr, Wd, bars, idx)
        pt = assert_PART(P, tr, Wd, PT, bars, idx)
        fb, z = Wd["fallback"], Wd["zero"]
        print(f"    [EW] {ew['sampled']} sampled trades: EW entry / exit and EW1 entry / exit == a plain-Python recomputation from {ew['bars']:,} raw bars read independently by "
              f"symbol and date strings (each pair clamped, the mean of the finite pairs, PUB where none) to {ew['worst']:.0e}; fallback and zero flags agree "
              f"({ew['fallbacks_in_sample']} fallbacks, {ew['zeros_in_sample']} zero windows in the sample); ledger fallbacks EW in {int(fb['EW_in'].sum())} out "
              f"{int(fb['EW_out'].sum())}, EW1 in {int(fb['EW1_in'].sum())} out {int(fb['EW1_out'].sum())} ({el()})")
        print(f"    [PART] {pt['sampled']} sampled trades: participation at $10k / $25k / $50k == position / (raw close x raw volume) at the entry and the exit bar "
              f"from the same raw bars (rel {pt['worst_rel']:.0e}; the fixture divides prices and multiplies volumes by the split factor, so close x volume is the "
              f"as-traded dollar volume); zero dollar volume on {PT['dv_entry_bad']} entry / {PT['dv_exit_bad']} exit bars ({el()})")
        out.update(EW=ew, PART=pt, sample_idx=idx, bars=bars)
    q = quintiles(Wd["values"]["PUB"])
    wI, invinfo = weights_INV(CL["lines"]["PUB"]["two_c"])
    wU = weights_U(q)
    out.update(q=q, wI=wI, wU=wU, inv_info=invinfo, wE=np.ones(len(tr)))
    return out


# ------------------------------------------------------------------ report pieces
def line_table(CL, Wd):
    v, fb, z = Wd["values"], Wd["fallback"], Wd["zero"]
    g = CL["gross"]
    budget = float(g.mean() - CL["borrow"].mean() - CL["comm"].mean())
    out = dict(gross_mean=float(g.mean()), commission_mean=float(CL["comm"].mean()), borrow_mean=float(CL["borrow"].mean()), htb_n=int(CL["htb"].sum()),
               breakeven_half_spread_bp_side=budget / 2.0, price_median=float(np.median(CL["px"])), lines={})
    for ln in LINES:
        L = CL["lines"][ln]
        d = dict(entry_median=float(np.median(L["entry"])), exit_median=float(np.median(L["exit"])), entry_mean=float(L["entry"].mean()), exit_mean=float(L["exit"].mean()),
                 two_c_mean=float(L["two_c"].mean()), net_mean=float(L["net"].mean()), net_median=float(np.median(L["net"])), net_t=wstats(L["net"], np.ones(g.size))["t"],
                 spread_coverage=budget / float(L["spread"].mean()) if L["spread"].mean() > 0 else None,
                 net_half_mean=float(L["net_half"].mean()), share_net_pos=float((L["net"] > 0).mean()))
        if ln == "PB":
            d["fallback_to_PUB"] = int(fb["PB"].sum())
        if ln in ("EW", "EW1"):
            d.update(fallback_in=int(fb[ln + "_in"].sum()), fallback_out=int(fb[ln + "_out"].sum()), zero_in=int(z[ln + "_in"].sum()), zero_out=int(z[ln + "_out"].sum()),
                     zero_in_share=float(z[ln + "_in"].mean()), zero_out_share=float(z[ln + "_out"].mean()))
            if ln == "EW":
                cnt = Wd["counts"]
                d.update(entry_pairs_finite_mean=float(cnt["EW_in_n"].mean()), exit_pairs_finite_mean=float(cnt["EW_out_n"].mean()),
                         entry_pairs_clamped_share=float(cnt["EW_in_clamped"].sum() / max(cnt["EW_in_n"].sum(), 1)),
                         exit_pairs_clamped_share=float(cnt["EW_out_clamped"].sum() / max(cnt["EW_out_n"].sum(), 1)))
                nf = ~fb["EW_in"]
                d["entry_median_ex_fallback"] = float(np.median(L["entry"][nf]))
                d["exit_median_ex_fallback"] = float(np.median(L["exit"][~fb["EW_out"]]))
        out["lines"][ln] = d
    out["net_auction_mean"] = float(CL["net_auction"].mean())
    return out


def quintile_table(CL, Wd, q):
    v = Wd["values"]
    g = CL["gross"]
    out = []
    for k in range(5):
        m = q == k
        d = dict(q=k, n=int(m.sum()), pub_median=float(np.median(v["PUB"][m])), pub_min=float(v["PUB"][m].min()), pub_max=float(v["PUB"][m].max()),
                 ew_in_median=float(np.median(v["EW_in"][m])), ew_out_median=float(np.median(v["EW_out"][m])), pb_median=float(np.median(CL["lines"]["PB"]["entry"][m])),
                 price_median=float(np.median(CL["px"][m])), gross_mean=float(g[m].mean()), gross_median=float(np.median(g[m])), borrow_mean=float(CL["borrow"][m].mean()),
                 comm_mean=float(CL["comm"][m].mean()), lines={})
        for ln in LINES:
            L = CL["lines"][ln]
            d["lines"][ln] = dict(two_c_mean=float(L["two_c"][m].mean()), net_mean=float(L["net"][m].mean()), net_t=wstats(L["net"][m], np.ones(int(m.sum())))["t"])
        out.append(d)
    mid = (q >= 1) & (q <= 3)
    pooled = dict(n=int(mid.sum()), gross_mean=float(g[mid].mean()), lines={ln: dict(net_mean=float(CL["lines"][ln]["net"][mid].mean())) for ln in LINES})
    return dict(by_q=out, middle_pooled=pooled)


def load_perm(paths, obs_net):
    fs = sorted(paths["dir"].glob("d363_perm_p*.json"))
    if not fs:
        return None
    parts, stats = [], {}
    for f in fs:
        d = json.loads(f.read_text())
        assert d["draws"] == len(d["draws_stat"]["net_PUB"]), f"[P] {f.name}"
        assert abs(d["observed"]["net_PUB"] - obs_net) < 1e-9, f"[P] {f.name}: observed {d['observed']['net_PUB']} differs from the rebuilt {obs_net}"
        for k, v in d["draws_stat"].items():
            stats.setdefault(k, []).extend(v)
        parts.append(dict(file=f.name, part=d["part"], draws=d["draws"], seed=d["seed"], seconds_per_draw=d["seconds_per_draw"], rss=d.get("rss"), redraws=d["redraws_total"]))
    assert len({p["part"] for p in parts}) == len(parts), "[P] a part repeated"
    out = dict(parts=parts, draws=len(stats["net_PUB"]), groups=d["groups"], notes=d["notes"])
    for k in stats:
        out[k] = V53._dist(stats[k], d["observed"][k])
    out["net_PUB"]["above"] = bool(obs_net > np.quantile(stats["net_PUB"], .95))
    return out


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    SELFTEST_TMP.mkdir(parents=True, exist_ok=True)
    print(f"    [K] [F0] [R] via d348_prep (cache {'HIT' if P['cache_hit'] else 'BUILD'} {P['cache_key']}); the kernel is D345's (EB.simulate_event), the fill the next open")
    print(f"    [HOLDOUT-GUARD] {D62.assert_HOLDOUT_GUARD()}; a non-existent 'holdout' probe path was refused by the hook before the filesystem was touched (run_d362's hook, "
          f"installed before any other module of the chain executed) ({el()})")
    Bd = build(P)
    res, tr, CL, Wd = Bd["res"], Bd["trades"], Bd["CL"], Bd["Wd"]
    # [W] on both arms
    wv = {}
    for nm, w in (("INV", Bd["wI"]), ("U", Bd["wU"])):
        wv[nm] = assert_W(P, res, w)
    print(f"    [W] on INV and U: every trade's weight read off the (e0, row) grid == the vector; with every weight 1 the weighted rebuild == V58.rebuild exactly and == the "
          f"kernel's book_dep_x to {wv['U']['worst_unit']:.0e}, and costed_w == G22.costed key for key on both conventions; with the arm's weights the series x sum w == a "
          f"bar-loop second implementation to {max(wv['INV']['worst_loop'], wv['U']['worst_loop']):.0e} and sums to sum w pnl; sum w pnl / sum w INV {wv['INV']['mean_w_bp']:+.4f} "
          f"U {wv['U']['mean_w_bp']:+.4f} == a plain loop to 1e-9; capital used {wv['INV']['capital']:.6f} / {wv['U']['capital']:.6f} == sum w / n; INV cap {INV_CAP} binds on "
          f"{Bd['inv_info']['binding']} trades (uncapped max {Bd['inv_info']['uncapped_max']:.1f}) ({el()})")
    # [PERM] 5 draws
    groups = name_groups(tr)
    rng = np.random.default_rng([SEED, STUDY, NULL["PERM"], 0])
    obs = perm_stat(CL, Bd["wU"], res, P)
    pv, info = [], None
    for _ in range(5):
        wp, redraw = perm_draw(Bd["wU"], groups, rng)
        info = assert_PERM(Bd["wU"], wp, groups)
        info["redraws"] = redraw
        pv.append(perm_stat(CL, wp, res, P)["net_PUB"])
    print(f"    [PERM] 5 draws: every name's U-weight multiset kept, the vector never the observed on the {info['variable']} names with >= 2 distinct weights (of {info['names']}; "
          f"{info['single']} single-trade names and {info['constant']} constant-weight names keep theirs); redraws {info['redraws']}; net per unit capital under PUB "
          + ", ".join(f"{x:+.2f}" for x in pv) + f" vs U {obs['net_PUB']:+.2f} ({el()})")
    # [6]
    broke = []
    try:                                                              # [ID] on a perturbed ledger (+1 bp on one trade)
        r6 = dict(res, trades=[(r, e, a, p + (1e-4 if j == 0 else 0.0), sd) for j, (r, e, a, p, sd) in enumerate(tr)])
        assert_ID(P, r6)
    except AssertionError as e:
        assert "[ID]" in str(e)
        broke.append("ID")
    try:                                                              # [CS] on a shifted window (ending at t instead of t-1)
        assert_CS(P, Bd["hs_bar"], Bd["own"], np.random.default_rng(6), end_shift=0)
    except AssertionError as e:
        assert "[CS]" in str(e)
        broke.append("CS")
    try:                                                              # [EW] on a perturbed high (a sampled trade whose entry pair is finite and non-zero: its gap-day high x 1.01 in the grid)
        j = next(int(j) for j in Bd["sample_idx"] if not Wd["fallback"]["EW1_in"][j] and not Wd["zero"]["EW1_in"][j])
        r, g = int(Wd["rows"][j]), int(Wd["g"][j])
        H6 = Bd["H"].copy()
        H6[g, r] *= 1.01
        hs6, cl6 = hs_bar_grid(H6, Bd["L"], np.asarray(P["live"]).T)
        W6 = windows(P, tr, hs6, cl6)
        assert_EW(P, tr, W6, Bd["bars"], [j])
    except AssertionError as e:
        assert "[EW]" in str(e)
        broke.append("EW")
    try:                                                              # [PERM] on a wrong multiset (one trade's weight doubled)
        wp6 = Bd["wU"].copy()
        j = next(j for j, idx in groups.items() if idx.size >= 2)
        wp6[groups[j][0]] *= 2.0
        assert_PERM(Bd["wU"], wp6, groups)
    except AssertionError as e:
        assert "[PERM]" in str(e)
        broke.append("PERM")
    assert broke == ["ID", "CS", "EW", "PERM"], f"[6] raised: {broke}"
    print("    [6] [ID] raises on a perturbed ledger (+1 bp on one trade); [CS] raises on a shifted window (ending at t, not t-1); [EW] raises on a perturbed high "
          "(one sampled trade's gap-day high x 1.01); [PERM] raises on a wrong multiset (one weight doubled)")
    LT = line_table(CL, Wd)
    summ = dict(ID=Bd["ID"], CS=Bd["CS"], EW=Bd["EW"], PART=Bd["PART"], W={k: {kk: vv for kk, vv in v.items() if kk != "wgrid"} for k, v in wv.items()}, perm5=pv, perm_info=info,
                lines=LT, guard=D62.guard_line())
    (SELFTEST_TMP / "selftest_summary.json").write_text(json.dumps(clean(summ), indent=1))
    print(f"    check: {len(tr):,} trades gross {LT['gross_mean']:+.2f}; per-trade 2c PUB {LT['lines']['PUB']['two_c_mean']:.2f} PB {LT['lines']['PB']['two_c_mean']:.2f} EW "
          f"{LT['lines']['EW']['two_c_mean']:.2f} EW1 {LT['lines']['EW1']['two_c_mean']:.2f}; net PUB {LT['lines']['PUB']['net_mean']:+.2f} EW {LT['lines']['EW']['net_mean']:+.2f}")
    print(f"    [HOLDOUT-GUARD] at exit: {D62.guard_line()}")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_perm(P, draws, part, paths):
    Bd = build(P, with_fixture=False)
    res, tr, CL = Bd["res"], Bd["trades"], Bd["CL"]
    w = Bd["wU"]
    assert_W(P, res, w)
    groups = name_groups(tr)
    seed = [SEED, STUDY, NULL["PERM"], part]
    rng = np.random.default_rng(seed)
    obs = perm_stat(CL, w, res, P)
    print(f"\n  PERM part {part}: {len(tr):,} trades, {len(groups):,} names; U net per unit capital under PUB {obs['net_PUB']:+.2f} (gross {obs['gross']:+.2f}); "
          f"{draws} within-name weight permutations, seed {seed}")
    D_, redraws, info = {k: [] for k in obs}, [], None
    ts = time.time()
    for d in range(draws):
        wp, rd = perm_draw(w, groups, rng)
        info = assert_PERM(w, wp, groups)
        redraws.append(rd)
        st = perm_stat(CL, wp, res, P)
        for k in st:
            D_[k].append(st[k])
        if (d + 1) % 50 == 0 or d + 1 == draws:
            print(f"    PERM {d + 1}/{draws} ({time.time() - ts:.0f}s; {(time.time() - ts) / (d + 1):.3f} s/draw)", flush=True)
    spd = (time.time() - ts) / max(draws, 1)
    out = dict(study=STUDY, arm="U", null="PERM", part=part, draws=draws, seed=seed, observed=obs, draws_stat=D_, redraws=redraws, redraws_total=int(sum(redraws)), groups=info,
               notes=dict(statistic="net per unit capital under PUB, per-trade convention (own PUB at entry x 2 + own commission at the as-traded close + own borrow)",
                          PERM="within each name its trades' U-weights permuted; single-trade and constant-weight names keep theirs; a permutation equal to the observed on a name with >= 2 distinct weights is redrawn",
                          deployed="deployed_net_PUB = D362's costed_w on the weighted hedged series (ledger-median PUB, 4 crossings)"),
               seconds_per_draw=spd, rss=PREP.rss_line(), guard=D62.guard_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    f = Path(paths["perm"].format(part=part))
    f.write_text(json.dumps(clean(out)))
    r = np.array(D_["net_PUB"])
    print(f"  wrote {f}: PERM net PUB p50 {np.median(r):+.2f} p95 {np.quantile(r, .95):+.2f} max {r.max():+.2f} vs U {obs['net_PUB']:+.2f}; {spd:.3f} s/draw "
          f"({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def stage_report(P, paths):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print(f"    [HOLDOUT-GUARD] {D62.assert_HOLDOUT_GUARD()}")
    Bd = build(P)
    res, tr, CL, Wd, PT, q = Bd["res"], Bd["trades"], Bd["CL"], Bd["Wd"], Bd["PT"], Bd["q"]
    v = Wd["values"]
    LT = line_table(CL, Wd)
    QT = quintile_table(CL, Wd, q)
    PS = part_summary(PT)
    arms = {}
    for nm, w in (("EQ", Bd["wE"]), ("INV", Bd["wI"]), ("U", Bd["wU"])):
        wv = assert_W(P, res, w)
        a = arm_block(CL, w, nm)
        a["deployed"] = deployed_w(res, P, wv["wgrid"])
        a["D362_W"] = D62.trade_block_w(P, tr, w)
        a["W_check"] = {k: vv for k, vv in wv.items() if k != "wgrid"}
        arms[nm] = a
    obs_perm = perm_stat(CL, Bd["wU"], res, P)
    PM = load_perm(paths, obs_perm["net_PUB"])
    print(f"    [W] EQ / INV / U pass; PERM {'loaded (' + str(PM['draws']) + ' draws)' if PM else 'NOT RUN'} ({el()})")
    stored = stored_A2()

    # ---- print ----
    print("\n" + "=" * 170)
    print(f"THE COST LINES on D362's A2 (the two-sink gated gap-up fade, short at the next open, cap 10, hedged): {len(tr):,} trades, gross {LT['gross_mean']:+.2f} bp per TRADE. "
          f"Every line is an OHLC estimator (the record's Corwin-Schultz); nothing here is a quoted spread (D336 pending)")
    print("=" * 170)
    print(f"  conventions: PER-TRADE (this record: own half-spread at own entry / exit bars + 2 x $0.005 / own as-traded close) in every table below; D362's LEDGER-MEDIAN "
          f"2c PUB {stored['two_c']['PUB']:.2f} / PB {stored['two_c']['PB']:.2f} (median half-spread x 2 + commission at the median panel close ${stored['held_price']:.2f}) "
          f"reproduced to 1e-9 for [ID] and printed here only")
    print(f"  commission per trade mean {LT['commission_mean']:.2f} bp (median as-traded close ${LT['price_median']:.2f}); borrow mean {LT['borrow_mean']:.2f} bp ({LT['htb_n']} HTB); "
          f"breakeven half-spread (gross - borrow - commission) / 2 = {LT['breakeven_half_spread_bp_side']:.2f} bp/side under any line")
    print("\n  THE COST LINES per trade (bp): median half-spread entry / exit, mean 2c, mean net (= gross - 2c - borrow), coverage = (gross - borrow - comm) / mean(entry + exit)")
    print("  %-4s %8s %8s | %8s %8s | %8s %8s | %7s %6s %6s | %s" % ("line", "entry50", "exit50", "entry_mu", "exit_mu", "2c", "net", "net t", "cover", "net>0", "fallbacks / zero-clamped"))
    for ln in LINES:
        d = LT["lines"][ln]
        extra = f"fallback to PUB on {d['fallback_to_PUB']} (no day after the entry)" if ln == "PB" else ""
        if ln in ("EW", "EW1"):
            extra = (f"fallback to PUB in {d['fallback_in']} / out {d['fallback_out']}; zero-clamped in {d['zero_in']} ({100 * d['zero_in_share']:.1f}%) / out {d['zero_out']} "
                     f"({100 * d['zero_out_share']:.1f}%)")
            if ln == "EW":
                extra += (f"; pairs finite per window in {d['entry_pairs_finite_mean']:.2f} out {d['exit_pairs_finite_mean']:.2f}, pairs clamped {100 * d['entry_pairs_clamped_share']:.0f}% / "
                          f"{100 * d['exit_pairs_clamped_share']:.0f}%; medians ex-fallback {d['entry_median_ex_fallback']:.2f} / {d['exit_median_ex_fallback']:.2f}")
        print("  %-4s %8.2f %8.2f | %8.2f %8.2f | %8.2f %+8.2f | %+7.2f %6.2f %5.1f%% | %s" % (ln, d["entry_median"], d["exit_median"], d["entry_mean"], d["exit_mean"], d["two_c_mean"],
                                                                                          d["net_mean"], d["net_t"] or 0, d["spread_coverage"] or 0, 100 * d["share_net_pos"], extra))
    print("\n  EXECUTION BOUNDS per trade (mean net bp): full crossing = gross - 2c - borrow; half crossing = gross - (entry + exit) / 2 - commission - borrow; auction = gross - commission - borrow")
    print("  %-4s %10s %10s %10s" % ("line", "full", "half", "auction"))
    for ln in LINES:
        d = LT["lines"][ln]
        print("  %-4s %+10.2f %+10.2f %+10.2f" % (ln, d["net_mean"], d["net_half_mean"], LT["net_auction_mean"]))
    print("\n  PARTICIPATION: position / (close x volume) in the fixture's frame (== as-traded close x as-traded shares); median / p90 / p99 / share under 1% / under 5%")
    for bar in ("entry", "exit"):
        s = PS[bar]
        print(f"  {bar:5s} (dollar volume median ${s['dollar_volume_median'] / 1e6:.2f}M; {s['dollar_volume_bad']} bars with zero dollar volume): "
              + "; ".join(f"${int(p) // 1000}k {100 * s[p]['median']:.3f}% / {100 * s[p]['p90']:.2f}% / {100 * s[p]['p99']:.1f}% / {100 * s[p]['share_under_1pct']:.1f}% / "
                          f"{100 * s[p]['share_under_5pct']:.1f}%" for p in map(str, POSITIONS)))
    print("\n  BY PUB QUINTILE (rank-based equal-count bins of the trade's own PUB half-spread at entry; q0 tightest): n, PUB range, medians of PUB / EW in / EW out / PB, price, "
          "gross, and net under every line (mean bp per trade, t)")
    print("  %2s %4s %14s | %6s %6s %6s %6s %6s | %7s | %8s %8s %8s %8s | %s" % ("q", "n", "PUB range", "PUB50", "EWin50", "EWout50", "PB50", "px50", "gross", "netPUB", "netPB", "netEW", "netEW1", "t: PUB / EW"))
    for d in QT["by_q"]:
        L = d["lines"]
        print("  %2d %4d %6.1f - %6.1f | %6.1f %6.1f %6.1f %6.1f %6.2f | %+7.1f | %+8.1f %+8.1f %+8.1f %+8.1f | %+.2f / %+.2f" % (
            d["q"], d["n"], d["pub_min"], d["pub_max"], d["pub_median"], d["ew_in_median"], d["ew_out_median"], d["pb_median"], d["price_median"], d["gross_mean"],
            L["PUB"]["net_mean"], L["PB"]["net_mean"], L["EW"]["net_mean"], L["EW1"]["net_mean"], L["PUB"]["net_t"] or 0, L["EW"]["net_t"] or 0))
    mp = QT["middle_pooled"]
    print(f"  middle three pooled (n {mp['n']:,}): gross {mp['gross_mean']:+.1f}; net PUB {mp['lines']['PUB']['net_mean']:+.1f} PB {mp['lines']['PB']['net_mean']:+.1f} "
          f"EW {mp['lines']['EW']['net_mean']:+.1f} EW1 {mp['lines']['EW1']['net_mean']:+.1f}")
    print("\n  SIZING ARMS: per unit of capital (sum w x / sum w), t = m / se (se = sqrt(sum w^2 (x - m)^2) / sum w), capital used = sum w / n; deployed = D362's W arithmetic "
          "(weighted hedged series, ledger-median PUB, 4 crossings)")
    print("  %-4s %6s %6s %6s | %8s %6s | %8s %8s %8s %8s | %7s %7s %7s | %8s %8s %8s" % ("arm", "cap", "wmin", "wmax", "gross", "t", "netPUB", "netPB", "netEW", "netEW1", "tPUB", "tPB", "tEW",
                                                                                         "dep gr", "dep net4", "dep net2"))
    for nm, a in arms.items():
        L, dep = a["lines"], a["deployed"]["PUB"]
        print("  %-4s %6.3f %6.3f %6.3f | %+8.2f %+6.2f | %+8.2f %+8.2f %+8.2f %+8.2f | %+7.2f %+7.2f %+7.2f | %+8.2f %+8.2f %+8.2f" % (
            nm, a["capital_used"], a["weight_min"], a["weight_max"], a["gross"]["mean"], a["gross"]["t"] or 0, L["PUB"]["net"]["mean"], L["PB"]["net"]["mean"], L["EW"]["net"]["mean"],
            L["EW1"]["net"]["mean"], L["PUB"]["net"]["t"] or 0, L["PB"]["net"]["t"] or 0, L["EW"]["net"]["t"] or 0, dep["hedged"]["gross_bp"], dep["hedged"]["net_bp"], dep["hedged_2x"]["net_bp"]))
    ii = Bd["inv_info"]
    print(f"  INV: w = 1 / 2c_PUB (per trade) normalised to mean 1, capped at {ii['cap']} (binds on {ii['binding']} trades; uncapped max {ii['uncapped_max']:.2f}); "
          f"U: {U_SHAPE} on q0..q4 normalised to mean 1 (weights {Bd['wU'].min():.4f} / {Bd['wU'].max():.4f})")
    if PM:
        d = PM["net_PUB"]
        print(f"  PERM ({PM['draws']} draws over {len(PM['parts'])} part(s)): net per unit capital under PUB p50 {d['p50']:+.2f} p95 {d['p95']:+.2f} max {d['max']:+.2f} vs U "
              f"{obs_perm['net_PUB']:+.2f} ({'above' if d['above'] else 'NOT above'} p95); gross p50 {PM['gross']['p50']:+.2f} p95 {PM['gross']['p95']:+.2f} vs {obs_perm['gross']:+.2f}; "
              f"deployed net PUB p50 {PM['deployed_net_PUB']['p50']:+.2f} p95 {PM['deployed_net_PUB']['p95']:+.2f} vs {obs_perm['deployed_net_PUB']:+.2f}; names {PM['groups']['names']:,} "
              f"({PM['groups']['single']} single-trade, {PM['groups']['constant']} constant-weight, {PM['groups']['variable']} permuted); redraws {sum(p['redraws'] for p in PM['parts'])}")

    # ---- predictions ----
    v_ = lambda b: "CONFIRMED" if b else "FALSIFIED"
    Lt = LT["lines"]
    pub50, ewin50, ewout50 = Lt["PUB"]["entry_median"], Lt["EW"]["entry_median"], Lt["EW"]["exit_median"]
    s25 = PS["entry"][str(PREREG["q4_position"])]["share_under_1pct"]
    mids = [QT["by_q"][k]["lines"]["EW"]["net_mean"] for k in (1, 2, 3)]
    qd = {}
    qd["Q1"] = bool(ewin50 <= PREREG["q1_ratio"] * pub50)
    qd["Q2"] = bool(Lt["EW"]["net_mean"] > 0)
    qd["Q3"] = bool(abs(ewout50 - pub50) <= PREREG["q3_tol"] * pub50)
    qd["Q4"] = bool(s25 >= PREREG["q4_share"])
    qd["Q5"] = bool(mp["lines"]["EW"]["net_mean"] > 0)
    qd["Q6"] = bool(arms["INV"]["lines"]["PUB"]["net"]["mean"] < arms["EQ"]["lines"]["PUB"]["net"]["mean"] and arms["INV"]["lines"]["PB"]["net"]["mean"] < arms["EQ"]["lines"]["PB"]["net"]["mean"])
    qd["Q7"] = bool(PM is not None and PM["net_PUB"]["above"])
    qd["Q8"] = bool(Lt["EW1"]["zero_in_share"] > PREREG["q8_ew1"] and Lt["EW"]["zero_in_share"] < PREREG["q8_ew"])
    qd["check"] = bool(Bd["ID"]["trades"] == PREREG["trades"] and Bd["CS"]["worst_pub"] < 1e-9 and Bd["CS"]["sampled"] == 300)
    print(f"\nPREDICTIONS (D362's A2, {len(tr):,} trades, bp per trade, per-trade cost convention unless stated; cost decides nothing about the signal, R15)")
    print(f"  Q1 (LOAD-BEARING) entry-side EW half-spread <= {PREREG['q1_ratio']} x PUB at the median: {v_(qd['Q1'])} -- EW entry median {ewin50:.2f} vs PUB {pub50:.2f} "
          f"(ratio {ewin50 / pub50:.3f}; ex-fallback {Lt['EW']['entry_median_ex_fallback']:.2f}; EW1 entry median {Lt['EW1']['entry_median']:.2f}; PB {Lt['PB']['entry_median']:.2f})")
    print(f"  Q2 the ledger nets > 0 per trade under EW after commission and borrow: {v_(qd['Q2'])} -- gross {LT['gross_mean']:+.2f} - 2c EW {Lt['EW']['two_c_mean']:.2f} - borrow "
          f"{LT['borrow_mean']:.2f} = {Lt['EW']['net_mean']:+.2f} (t {Lt['EW']['net_t']:+.2f}; PUB {Lt['PUB']['net_mean']:+.2f}, PB {Lt['PB']['net_mean']:+.2f}, EW1 {Lt['EW1']['net_mean']:+.2f})")
    print(f"  Q3 exit-side EW within {100 * PREREG['q3_tol']:.0f}% of PUB at the median: {v_(qd['Q3'])} -- EW exit median {ewout50:.2f} vs PUB {pub50:.2f} ({100 * (ewout50 / pub50 - 1):+.1f}%)")
    print(f"  Q4 at ${PREREG['q4_position'] // 1000}k the entry-day participation is under 1% for >= {100 * PREREG['q4_share']:.0f}% of trades: {v_(qd['Q4'])} -- {100 * s25:.1f}% "
          f"(median {100 * PS['entry']['25000']['median']:.3f}%, p90 {100 * PS['entry']['25000']['p90']:.2f}%); exit bar {100 * PS['exit']['25000']['share_under_1pct']:.1f}%")
    print(f"  Q5 (against) the middle three PUB quintiles net > 0 under EW (read as the pooled group; each printed): {v_(qd['Q5'])} -- pooled {mp['lines']['EW']['net_mean']:+.2f} "
          f"[{mp['n']:,}]; q1 {mids[0]:+.1f} q2 {mids[1]:+.1f} q3 {mids[2]:+.1f} (under PUB pooled {mp['lines']['PUB']['net_mean']:+.2f})")
    print(f"  Q6 INV lowers net per unit capital under both PUB and PB relative to equal weight: {v_(qd['Q6'])} -- PUB INV {arms['INV']['lines']['PUB']['net']['mean']:+.2f} vs EQ "
          f"{arms['EQ']['lines']['PUB']['net']['mean']:+.2f}; PB INV {arms['INV']['lines']['PB']['net']['mean']:+.2f} vs EQ {arms['EQ']['lines']['PB']['net']['mean']:+.2f} "
          f"(gross INV {arms['INV']['gross']['mean']:+.2f} vs {arms['EQ']['gross']['mean']:+.2f})")
    print(f"  Q7 U's net per unit capital under PUB above the p95 of {PREREG['perm_draws']} within-name weight permutations: {v_(qd['Q7'])} -- U {obs_perm['net_PUB']:+.2f}"
          + (f" vs PERM p95 {PM['net_PUB']['p95']:+.2f} (p50 {PM['net_PUB']['p50']:+.2f}) at {PM['draws']} draws" if PM else "; PERM NOT RUN (falsified by absence)")
          + f"; EQ {arms['EQ']['lines']['PUB']['net']['mean']:+.2f}")
    print(f"  Q8 EW1 zero-clamped on > {100 * PREREG['q8_ew1']:.0f}% of entries and EW on < {100 * PREREG['q8_ew']:.0f}%: {v_(qd['Q8'])} -- EW1 {100 * Lt['EW1']['zero_in_share']:.1f}% "
          f"({Lt['EW1']['zero_in']}), EW {100 * Lt['EW']['zero_in_share']:.1f}% ({Lt['EW']['zero_in']}); exits EW1 {100 * Lt['EW1']['zero_out_share']:.1f}% EW {100 * Lt['EW']['zero_out_share']:.1f}%")
    print(f"  check: the ledger reproduces D362's A2 ({Bd['ID']['trades']:,}, {Bd['ID']['mean_bp']:+.4f}) and its ledger-median 2c PUB / PB "
          f"({Bd['ID']['two_c_ledger_median']['PUB']:.2f} / {Bd['ID']['two_c_ledger_median']['PB']:.2f}) to 1e-9; the per-bar estimator averaged over 21 own bars reproduces HALF_PUB "
          f"at {Bd['CS']['sampled']} sampled name-bars to {Bd['CS']['worst_pub']:.0e}: {v_(qd['check'])}")
    for a in arms.values():
        a["deployed"].pop("_series", None)
    out = dict(note="D363: the cost lines on D362's A2 (unchanged, [ID] to 1e-9) -- PUB / PB as D362, EW (three-bar windows around the gap and the exit) and EW1 (the single "
                    "pair) from the record's own Corwin-Schultz per-bar estimate ([CS] to 1e-9 against HALF_PUB / HALF_PB); the execution bounds and participation; INV and U "
                    "sizing with a within-name weight permutation null. Every line is an OHLC estimator; D336 (quoted spreads) is not pre-empted. Nothing is a book; nothing promoted.",
               study=STUDY, ledger=dict(arm=ARM, cap=CAP, events=Bd["LG"]["events"], events_removed=Bd["LG"]["removed"], trades=len(tr), source="run_d362 A2 (base -> features -> hit_grids -> arm_signal -> run_short)"),
               conventions=dict(per_bar_estimate="hs_bar[t, i] = the Corwin-Schultz pair (t-1, t) assigned to its SECOND day t, half-spread bp/side, clamped at 0 per pair; NaN where either day is not live",
                                PUB="HALF_PUB[t] = nanmean of hs_bar over the name's 21 own live bars ending at t-1, >= 17 finite (asserted [CS]); both sides of the trade",
                                PB="HALF_PB[t] = hs_bar[t+1] = the pair (t, t+1): the entry day and the day after (asserted [CS]); both sides; PUB where NaN (no day after; counted)",
                                EW="entry = nanmean of hs_bar over g-1, g, t (pairs (g-2,g-1), (g-1,g), (g,t)); exit = nanmean over e-1, e, e+1; PUB where no pair is finite (counted)",
                                EW1="entry = hs_bar[t] (the pair (g, t)); exit = hs_bar[e] (the pair (e-1, e)); PUB where NaN (counted)",
                                clamp="every pair clamped at 0 before averaging (as cs_spread); EW zero-clamped = the window mean is exactly 0; EW1 zero-clamped = its pair was negative",
                                two_c_per_trade="entry + exit + 2 x 0.005 / RAW_CLOSE[e0, row] x 1e4 (the as-traded close); net = gross - 2c - borrow (D337 gc_htb)",
                                two_c_ledger_median="D362's V47.two_c: 2 x median half-spread + commission at the median panel CLOSE; reproduced for [ID], not used in the tables",
                                participation="position / (CLOSE x VOL) in the fixture's frame; prices divided and volumes multiplied by the split factor, so this equals as-traded close x as-traded shares",
                                quintiles="rank-based equal-count bins of PUB at entry over the ledger, ties by ledger order",
                                INV=f"1 / 2c_PUB per trade, mean 1, capped at {INV_CAP} and re-normalised to a fixed point", U=f"{U_SHAPE} on q0..q4, mean 1",
                                weighted_stat="sum w x / sum w; t = m / se, se = sqrt(sum w^2 (x - m)^2) / sum w; capital used = sum w / n"),
               ID=Bd["ID"], CS=Bd["CS"], EW=Bd["EW"], PART=Bd["PART"], inv=Bd["inv_info"], lines=LT, quintiles=QT, participation=PS, arms=arms, perm_observed=obs_perm, perm=PM,
               d362_stored_per_trade=stored, predictions=qd, prereg=PREREG, seeds=dict(PERM=[SEED, STUDY, NULL["PERM"], "part"], samples=[SEED, STUDY, 97], raw_sample=[SEED, STUDY, 98]),
               borrow=dict(scheme=BORROW_SCHEME, gc_bps=BR.GC_BPS, htb_bps=BR.HTB_BPS, px_htb=BR.PX_HTB), guard=D62.guard_line(), rss=PREP.rss_line())
    paths["dir"].mkdir(parents=True, exist_ok=True)
    paths["report"].write_text(json.dumps(clean(out), indent=1))
    print(f"    [HOLDOUT-GUARD] at exit: {out['guard']}")
    print(f"\nwrote {paths['report']}  ({time.time() - P['t0']:.0f}s)  {PREP.rss_line()}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--perm", action="store_true", help="the within-name weight permutation null for U")
    ap.add_argument("--draws", type=int, default=200)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--out-dir", default=str(DATA), help="where the stage files go (default data/; the smoke runs pass a temp/ directory)")
    a = ap.parse_args()
    print("D363  the cost lines on the two-sink fade -- the entry-window spread, the execution bounds and cost-aware sizing on D362's A2 ledger (unchanged)")
    paths = out_paths(a.out_dir)
    P = PREP.prep(need_grids=False)
    P["rsi_pct_ok"] = np.isfinite(np.asarray(P["PCT"]["rsi"]))
    P["elig_b"] = np.asarray(P["elig"]) & P["rsi_pct_ok"]
    if a.selftest:
        stage_selftest(P)
    elif a.perm:
        stage_perm(P, a.draws, a.part, paths)
    elif a.report:
        stage_report(P, paths)
    else:
        ap.error("one of --selftest, --perm, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
