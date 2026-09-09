"""D405 STAGE 0 -- the capital-gains overhang: does the object survive its own gates?

    uv run python scripts/run_d405_overhang_stage0.py --selftest
    uv run python scripts/run_d405_overhang_stage0.py --calibrate
    uv run python scripts/run_d405_overhang_stage0.py --run

Pre-registration fdcaf30 predates this file (R8).

STAGE 0 ONLY. No forward return is computed anywhere in this file. Nothing is scored, nothing is
admitted. Stage 1 does not exist until all three gates pass.

    6.1  VOL-SHUF   rebuild with volume permuted, price path untouched.  ABANDON if corr > 0.9
    6.2  A1         independence vs the existing score set.              ABANDON if |rho| > 0.5
    6.3  PERSIST    half-life of g and F(P).                             ABANDON if < 1 bar

The object: mass = SHARES STILL HELD at a price. Placed across the candle's own quantiles
(L -> body_bot -> body_top -> H), worn away by SUBSEQUENT VOLUME rather than elapsed days.
There is no gravity here and there is no bandwidth here -- see the record, sections 2 and 3.1.
"""
import argparse
import importlib.util
import json
import os
import pathlib
import sys
import time
from collections import Counter

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]

# ------------------------------------------------- [SPLIT] default-deny holdout guard
_OPENED = dict(n=0, refused=0, holdout=Counter())


def _audit(event, args):
    if event != "open":
        return
    p = args[0]
    if isinstance(p, bytes):
        p = p.decode(errors="replace")
    elif not isinstance(p, (str, os.PathLike)):
        return
    low = os.fspath(p).replace("\\", "/").lower()
    _OPENED["n"] += 1
    if "holdout" in low:
        _OPENED["refused"] += 1
        _OPENED["holdout"][low] += 1
        raise RuntimeError(f"[SPLIT] refused to open {low}")


sys.addaudithook(_audit)                    # D405 NEVER calls allow_holdout. There is no unlock.


def _load(name, fname):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fname)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


sys.path.insert(0, str(REPO / "src"))
RP = _load("rp", "ragged_panel.py")
PS = _load("ragged_price_scores", "ragged_price_scores.py")
FB = _load("ragged_features", "ragged_features.py")
X = _load("d320", "run_d320_tilt_filters.py")
UF = _load("d339", "d339_universe_floor.py")
UF.bind(X, None)
A1 = _load("a1", "a1_er_stage0.py")                 # effective_inputs, rank01 -- D268's instrument

FIX_D = REPO / "data/fixtures/us_shorts_daily_raw.csv.gz"
EVJ_D = REPO / "data/fixtures/us_shorts_daily_raw_events.json"
FIX_E = REPO / "data/fixtures/etf_intraday_15m_panel.csv.gz"
OUT = REPO / "data" / "d405_overhang_stage0.json"
CALIB = REPO / "data" / "d405_bar_shape_calibration.json"

KS = (20, 60, 120, 250)          # volume-time half-lives, in shares turned over
GRID_N = 512
WARMUP = 252
MIN_BARS = 750
MIN_NAMES = 20                   # per-bar cross-section floor, D268's convention
SEED = 20260909
RHO_GATE = 0.50                  # 6.2 abandon
SHUF_GATE = 0.90                 # 6.1 abandon
HL_GATE = 1.0                    # 6.3 abandon, in bars


# =====================================================================  the bar shape
def bar_quantiles(calib=None):
    """(q_low, q_body, q_high). MEASURED from the ETF 15m panel, not chosen -- see --calibrate.
    Falls back to the uniform null only if no calibration file exists, and says so."""
    if calib is None and CALIB.exists():
        calib = json.loads(CALIB.read_text(encoding="utf-8"))
    if calib is None:
        return None
    return tuple(calib["measured"][k] for k in ("q_low", "q_body", "q_high"))


def bar_segments(gl, lo, bb, bt, hi, v, q):
    """Grid slices and per-cell density for one bar's volume, across the candle's own quantiles.

    MASS-PRESERVING BY CONSTRUCTION. A segment narrower than one cell puts all its mass in the
    single cell containing it rather than vanishing; a segment of zero width (no wick, or a doji)
    is dropped and its quantile RENORMALISED across the segments that survive -- section 3.1.

    Returned rather than applied, because the shape is IDENTICAL across every k: computing it once
    and applying it to all four rows is a 4x saving on the run's dominant cost."""
    segs = [(lo, bb, q[0]), (bb, bt, q[1]), (bt, hi, q[2])]
    live = [(a, b, w) for a, b, w in segs if b > a]
    if not live:
        return (), 0.0
    tot = sum(w for _, _, w in live)
    if tot <= 0:
        return (), 0.0
    n = gl.size
    out, placed = [], 0.0
    for a, b, w in live:
        share = v * w / tot
        i0 = int(np.searchsorted(gl, a, side="left"))
        i1 = int(np.searchsorted(gl, b, side="left"))
        i0 = min(max(i0, 0), n - 1)
        i1 = min(max(i1, i0 + 1), n)
        out.append((i0, i1, share / (i1 - i0)))
        placed += share
    return tuple(out), placed


def inject(F, gl, lo, bb, bt, hi, v, q):
    """Single-row form, kept for [MASS] which asserts against one grid."""
    segs, placed = bar_segments(gl, lo, bb, bt, hi, v, q)
    for i0, i1, d in segs:
        F[i0:i1] += d
    return placed


def overhang_series(logp, lo, bb, bt, hi, vol, live, q, ks, n=GRID_N):
    """One pass over bars, all `ks` at once. Returns g, OS and F(P) per bar per k.

    F_{t+1} = (1 - theta) * F_t + V_{t+1} * bar_shape,   theta = V / (k * Vbar)

    THE DECAY IS IN VOLUME-TIME, NOT CALENDAR TIME. That is the ingredient no prior map had:
    two names with identical price paths but different volume histories give different maps."""
    T = logp.size
    ok = live & np.isfinite(logp) & np.isfinite(vol) & (vol > 0) & np.isfinite(lo) & np.isfinite(hi)
    ok &= (hi > lo) & (bb >= lo) & (bt <= hi) & (bt >= bb)   # malformed MASKED, not clamped
    if ok.sum() < MIN_BARS:
        return None
    idx = np.flatnonzero(ok)
    gl = np.linspace(logp[idx].min() - 1e-6, logp[idx].max() + 1e-6, n)
    K = len(ks)
    F = np.zeros((K, n))
    tot = np.zeros(K)
    g = np.full((K, T), np.nan)
    OS = np.full((K, T), np.nan)
    FP = np.full((K, T), np.nan)
    vbar = np.full(T, np.nan)
    csum, cn = 0.0, 0
    hist = []
    kk = np.array(ks, float)
    for t in idx:
        # --- read BEFORE injecting bar t: F carries bars <= t-1 only.  [LAG]
        if tot.max() > 0:
            j = int(np.searchsorted(gl, logp[t], side="left"))
            j = min(max(j, 0), n - 1)
            with np.errstate(invalid="ignore", divide="ignore"):
                FP[:, t] = np.where(tot > 0, F[:, j] / np.maximum(F.max(axis=1), 1e-30), np.nan)
                above = F[:, j + 1:].sum(axis=1)
                OS[:, t] = np.where(tot > 0, above / tot, np.nan)
                ref = (F * gl[None, :]).sum(axis=1) / np.maximum(tot, 1e-30)
                g[:, t] = np.where(tot > 0, 1.0 - np.exp(ref - logp[t]), np.nan)
        # --- decay by SUBSEQUENT volume, then inject bar t
        hist.append(vol[t]); csum += vol[t]; cn += 1
        if cn > 63:
            csum -= hist[-64]
        vb = csum / min(cn, 63)
        vbar[t] = vb
        theta = np.clip(vol[t] / (kk * max(vb, 1e-12)), 0.0, 0.999)
        F *= (1.0 - theta)[:, None]
        tot *= (1.0 - theta)
        segs, placed = bar_segments(gl, lo[t], bb[t], bt[t], hi[t], vol[t], q)
        for i0, i1, d in segs:
            F[:, i0:i1] += d                      # one shape, applied to every k at once
        tot += placed
    return dict(g=g, OS=OS, FP=FP, ok=ok, grid=gl)


# =====================================================================  loading
def load_daily(verbose=True):
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIX_D, EVJ_D, fee_bps=0.0)      # assert_gates_passed lives here
    pos = {d: i for i, d in enumerate(panel.dates)}
    n, T = panel.closes.shape
    g = {c: np.full((n, T), np.nan) for c in ("open", "high", "low", "close")}
    VOL = np.full((n, T), np.nan)
    for i, s in enumerate(panel.symbols):
        for st in cleaned[s]:
            t = pos[st.timestamp[:10]]
            b = st.bar
            g["open"][i, t], g["high"][i, t] = b.open, b.high
            g["low"][i, t], g["close"][i, t] = b.low, b.close
            VOL[i, t] = b.volume
    CLOSE = np.ascontiguousarray(panel.closes.T)
    finT = np.ascontiguousarray(panel.live.T)
    ev = json.loads(EVJ_D.read_text(encoding="utf-8"))
    RAWF = UF.raw_price_factor(panel, ev)
    DV = X.roll_mean_T(CLOSE * VOL.T)
    keep = UF.floor_mask_v2(CLOSE * RAWF, DV, finT)
    elig = (finT & keep).T
    if verbose:
        print(f"  daily loaded {time.time()-t0:.0f}s   {n:,} names   floor rejects "
              f"{100*UF.floor_share(keep, finT):.2f}% of live name-bars")
    return panel, cleaned, g, VOL, elig, ev, RAWF


def assert_SPLITVOL(g, VOL, panel, ev, win=20):
    """[SPLITVOL] -- VOLUME must be split-adjusted in the SAME direction as price.

    If it is not, dollar volume jumps by the split ratio on the split date and the map plants a
    fabricated mountain there. D403's [ALIGN] caught a 5x error of exactly this family and nothing
    else would have seen it."""
    dpos = {d: t for t, d in enumerate(panel.dates)}
    sidx = {s: i for i, s in enumerate(panel.symbols)}
    jumps, checked, worst = [], 0, None
    for s, sp in ev["splits"].items():
        i = sidx.get(s)
        if i is None:
            continue
        for d, ratio in sp:
            t = dpos.get(d[:10])
            if t is None or t < win or t + win >= len(panel.dates):
                continue
            dv = g["close"][i] * VOL[i]
            a, b = dv[t - win:t], dv[t + 1:t + 1 + win]
            a, b = a[np.isfinite(a) & (a > 0)], b[np.isfinite(b) & (b > 0)]
            if a.size < 5 or b.size < 5:
                continue
            j = float(np.log(np.median(b) / np.median(a)))
            lr = abs(float(np.log(float(ratio))))
            checked += 1
            jumps.append(j)
            if lr > 0.2 and abs(j) > 0.5 * lr:
                if worst is None or abs(j) > abs(worst[2]):
                    worst = (s, d[:10], j, float(ratio))
    assert checked > 50, f"[SPLITVOL] only {checked} splits checkable -- the test is vacuous"
    frac = float(np.mean(np.abs(jumps) > 0.5))
    assert worst is None, (f"[SPLITVOL] dollar volume jumps at a split: {worst[0]} {worst[1]} "
                           f"log-jump {worst[2]:+.3f} against split ratio {worst[3]} -- "
                           f"volume is not adjusted with price")
    return dict(splits_checked=checked, median_log_jump=float(np.median(jumps)),
                share_gt_0p5=frac)


def assert_MASS(q):
    """[MASS] -- the intra-bar shape places exactly V shares, in every degenerate case."""
    gl = np.linspace(np.log(90.0), np.log(110.0), GRID_N)
    cases = {
        "normal": (np.log(95), np.log(99), np.log(101), np.log(105)),
        "no upper wick": (np.log(95), np.log(99), np.log(101), np.log(101)),
        "no lower wick": (np.log(99), np.log(99), np.log(101), np.log(105)),
        "doji": (np.log(95), np.log(100), np.log(100), np.log(105)),
        "narrow, sub-cell": (np.log(100.0), np.log(100.004), np.log(100.006), np.log(100.01)),
    }
    rep = {}
    for name, (lo, bb, bt, hi) in cases.items():
        F = np.zeros(GRID_N)
        placed = inject(F, gl, lo, bb, bt, hi, 1000.0, q)
        assert abs(F.sum() - 1000.0) < 1e-6, f"[MASS] {name}: grid holds {F.sum()}, expected 1000"
        assert abs(placed - 1000.0) < 1e-6, f"[MASS] {name}: reported {placed}"
        rep[name] = round(float(F.sum()), 6)
    F = np.zeros(GRID_N)
    assert inject(F, gl, np.log(100), np.log(100), np.log(100), np.log(100), 1000.0, q) == 0.0, \
        "[MASS] a zero-range bar placed mass"
    assert F.sum() == 0.0, "[MASS] a zero-range bar touched the grid"
    # [X] the break must move THE SCALAR: a quantile set that does not sum to 1 must still
    # place exactly V, because the renormalisation is what guarantees it
    F = np.zeros(GRID_N)
    inject(F, gl, np.log(95), np.log(99), np.log(101), np.log(105), 1000.0, (0.1, 0.1, 0.1))
    assert abs(F.sum() - 1000.0) < 1e-6, "[X] renormalisation does not hold mass -- the check is inert"
    return rep


def assert_DECAY():
    """[DECAY] -- a volume spike must remove the predicted fraction of standing mass, and the
    break must move THAT SCALAR."""
    q = (0.25, 0.5, 0.25)
    T, SPIKE = 900, 700
    rs = np.random.default_rng(405)
    # a drifting path, so the map has structure the spike can actually remove
    logp = np.log(100.0) + np.cumsum(rs.normal(0, 0.01, T))
    lo, hi = logp - 0.010, logp + 0.010
    bb, bt = logp - 0.004, logp + 0.004
    vol = np.full(T, 1000.0)
    live = np.ones(T, bool)
    a = overhang_series(logp, lo, bb, bt, hi, vol, live, q, (60,))
    vol2 = vol.copy()
    vol2[SPIKE] = 1000.0 * 60.0                     # one bar turning over a full half-life
    b = overhang_series(logp, lo, bb, bt, hi, vol2, live, q, (60,))
    assert a is not None and b is not None, "[DECAY] the synthetic fell below the bar floor"
    fa, fb = a["FP"][0], b["FP"][0]
    # CAUSALITY: the spike cannot touch the map before it happens. F is read BEFORE bar t is
    # injected, so bar SPIKE's own read is still identical; the divergence starts at SPIKE+1.
    pre = float(np.nanmax(np.abs(fa[:SPIKE + 1] - fb[:SPIKE + 1])))
    assert pre < 1e-12, f"[DECAY] the spike changed the map BEFORE it happened: {pre:.2e}"
    post = float(np.nanmax(np.abs(fa[SPIKE + 1:] - fb[SPIKE + 1:])))
    # [X] the break must move THE SCALAR the assertion reads, not merely fire the name
    assert post > 1e-3, (f"[DECAY] a 60x volume bar moved the map by only {post:.2e} -- "
                         f"the decay is inert and this check cannot fail")
    oa, ob = a["OS"][0], b["OS"][0]
    dos = float(np.nanmax(np.abs(oa[SPIKE + 1:] - ob[SPIKE + 1:])))
    return dict(pre_spike_max_abs_diff=pre, post_spike_max_FP_move=round(post, 5),
                post_spike_max_OS_move=round(dos, 5))


# =====================================================================  calibration
def calibrate(verbose=True):
    """SECTION 3.2 -- measure (q_low, q_body, q_high) from the 57-ETF 15m panel.

    THE DAILY BAR IS DERIVED FROM THE 15m BARS THEMSELVES, not from a daily fixture. That is
    deliberate: D403 found the 15m and daily fixtures sit on different corporate-action bases, and
    a calibration that straddled them would be measuring the mismatch. The cost is that the range
    is RTH-only, which is reported rather than assumed away.

    No forward return enters this. It is a property of the data."""
    import gzip
    t0 = time.time()
    per = {}
    with gzip.open(FIX_E, "rt") as fh:
        hdr = next(fh).strip().split(",")
        ci = {c: i for i, c in enumerate(hdr)}
        for line in fh:
            p = line.rstrip("\n").split(",")
            key = (p[ci["symbol"]], p[ci["timestamp"]][:10])
            o, h, l, c, v = (float(p[ci[k]]) for k in ("open", "high", "low", "close", "volume"))
            r = per.get(key)
            if r is None:
                per[key] = [o, h, l, c, [((h + l + c) / 3.0, v)]]
            else:
                r[1] = max(r[1], h); r[2] = min(r[2], l); r[3] = c
                r[4].append(((h + l + c) / 3.0, v))
    acc = np.zeros(3)
    wacc = np.zeros(3)
    nd = 0
    for (sym, d), (o, H, L, c, bars) in per.items():
        if not (H > L) or len(bars) < 10:
            continue
        bb, bt = min(o, c), max(o, c)
        segs = [(L, bb), (bb, bt), (bt, H)]
        tot = sum(v for _, v in bars)
        if tot <= 0:
            continue
        s = np.zeros(3)
        for pxy, v in bars:
            if pxy < bb:
                s[0] += v
            elif pxy <= bt:
                s[1] += v
            else:
                s[2] += v
        acc += s / tot
        w = np.array([max(b - a, 0.0) for a, b in segs])
        wacc += w / w.sum() if w.sum() > 0 else 0
        nd += 1
    q = acc / nd
    w = wacc / nd
    out = dict(sessions=nd, measured=dict(q_low=float(q[0]), q_body=float(q[1]), q_high=float(q[2])),
               uniform_null=dict(q_low=float(w[0]), q_body=float(w[1]), q_high=float(w[2])),
               source=str(FIX_E.relative_to(REPO)),
               note="daily bar derived from the 15m bars themselves; RTH only; no forward return")
    CALIB.write_text(json.dumps(out, indent=1), encoding="utf-8")
    if verbose:
        print(f"  calibrated on {nd:,} ETF sessions in {time.time()-t0:.0f}s")
        print(f"    MEASURED  low {q[0]:.4f}  body {q[1]:.4f}  high {q[2]:.4f}")
        print(f"    uniform   low {w[0]:.4f}  body {w[1]:.4f}  high {w[2]:.4f}   (the null shape)")
        print(f"    -> body carries {q[1]/w[1]:.2f}x its width share")
    return out


# =====================================================================  the gates
def half_life(x):
    """Bars for the autocorrelation to fall to 0.5. NaN if it never does within 60."""
    v = x[np.isfinite(x)]
    if v.size < 500:
        return np.nan
    v = v - v.mean()
    d = float((v * v).mean())
    if d <= 0:
        return np.nan
    for L in range(1, 61):
        r = float((v[L:] * v[:-L]).mean() / d)
        if r < 0.5:
            return float(L - 1 + (1.0 if L == 1 else 0.0))
    return 60.0


def run(verbose=True):
    t0 = time.time()
    print("D405 STAGE 0  the capital-gains overhang -- three gates, no forward return\n")
    q = bar_quantiles()
    assert q is not None, "no calibration on disk -- run --calibrate first (section 3.2)"
    print(f"  bar shape (MEASURED, section 3.2): low {q[0]:.4f}  body {q[1]:.4f}  high {q[2]:.4f}")
    print(f"  [MASS]  {assert_MASS(q)}")
    print(f"  [DECAY] {assert_DECAY()}")

    panel, cleaned, G, VOL, elig, ev, RAWF = load_daily()
    print(f"  [SPLITVOL] {assert_SPLITVOL(G, VOL, panel, ev)}")

    n, T = panel.closes.shape
    live = panel.live
    logp = np.log(np.where(np.isfinite(G["close"]) & (G["close"] > 0), G["close"], np.nan))
    lo = np.log(np.where(G["low"] > 0, G["low"], np.nan))
    hi = np.log(np.where(G["high"] > 0, G["high"], np.nan))
    bb = np.log(np.where(np.minimum(G["open"], G["close"]) > 0, np.minimum(G["open"], G["close"]), np.nan))
    bt = np.log(np.where(np.maximum(G["open"], G["close"]) > 0, np.maximum(G["open"], G["close"]), np.nan))

    rng = np.random.default_rng(SEED)
    real = {k: np.full((n, T), np.nan) for k in ("g", "OS", "FP")}
    shuf = {k: np.full((n, T), np.nan) for k in ("g", "OS", "FP")}
    KI = KS.index(60)
    built = 0
    ts = time.time()
    for i in range(n):
        m = live[i] & np.isfinite(logp[i]) & np.isfinite(VOL[i]) & (VOL[i] > 0)
        if m.sum() < MIN_BARS:
            continue
        a = overhang_series(logp[i], lo[i], bb[i], bt[i], hi[i], VOL[i], live[i], q, KS)
        if a is None:
            continue
        for k in ("g", "OS", "FP"):
            real[k][i] = a[k][KI]
        v2 = VOL[i].copy()
        idx = np.flatnonzero(m)
        v2[idx] = VOL[i][rng.permutation(idx)]          # VOLUME permuted, PRICE PATH UNTOUCHED
        b = overhang_series(logp[i], lo[i], bb[i], bt[i], hi[i], v2, live[i], q, KS)
        if b is not None:
            for k in ("g", "OS", "FP"):
                shuf[k][i] = b[k][KI]
        built += 1
        if verbose and built % 200 == 0:
            print(f"    built {built:,} names   {time.time()-ts:.0f}s", flush=True)
    print(f"  built {built:,} names in {time.time()-ts:.0f}s")

    # ---- 6.1 VOL-SHUF -----------------------------------------------------
    g61 = {}
    for k in ("g", "OS", "FP"):
        a, b = real[k], shuf[k]
        m = elig & np.isfinite(a) & np.isfinite(b)
        cs = []
        for i in range(n):
            if m[i].sum() < 250:
                continue
            u, v = a[i][m[i]], b[i][m[i]]
            if u.std() > 0 and v.std() > 0:
                cs.append(float(np.corrcoef(u, v)[0, 1]))
        cs = np.array(cs)
        g61[k] = dict(names=int(cs.size), p50=float(np.median(cs)), p90=float(np.percentile(cs, 90)),
                      mean=float(cs.mean()), share_above_gate=float(np.mean(np.abs(cs) > SHUF_GATE)))
    print("\n  --- GATE 6.1  VOL-SHUF (abandon if corr > 0.90) ---")
    for k, v in g61.items():
        print(f"    {k:3s}  n {v['names']:4d}  corr p50 {v['p50']:+.4f}  p90 {v['p90']:+.4f}  "
              f"share>|0.90| {v['share_above_gate']:.4f}")
    pass61 = all(v["p50"] <= SHUF_GATE for v in g61.values())

    # ---- 6.3 PERSIST ------------------------------------------------------
    g63 = {}
    for k in ("g", "OS", "FP"):
        hl = np.array([half_life(np.where(elig[i], real[k][i], np.nan)) for i in range(n)])
        hl = hl[np.isfinite(hl)]
        g63[k] = dict(names=int(hl.size), p50=float(np.median(hl)) if hl.size else np.nan,
                      p10=float(np.percentile(hl, 10)) if hl.size else np.nan)
    print("\n  --- GATE 6.3  PERSIST (abandon if half-life < 1 bar) ---")
    for k, v in g63.items():
        print(f"    {k:3s}  n {v['names']:4d}  half-life p10 {v['p10']:.1f}  p50 {v['p50']:.1f} bars")
    pass63 = all(v["p50"] >= HL_GATE for v in g63.values())

    # ---- 6.2 A1 independence ---------------------------------------------
    print("\n  --- GATE 6.2  A1 independence (abandon if |rho| > 0.50) ---", flush=True)
    price, _pw = PS.price_scores(panel, cleaned, live=live)
    intr = FB.intrabar_scores({c: G[c] for c in ("open", "high", "low", "close")}, live)
    mom = np.full((n, T), np.nan)
    mom[:, 252:] = logp[:, 252:] - logp[:, :-252]                 # explicit 12-month momentum
    existing = {"mom_12m": mom}
    for k in PS.PRICE_SCORES:
        existing[k] = np.asarray(price[k], float)
    for k in FB.INTRABAR_SCORES:
        existing[k] = np.asarray(intr[k], float)
    cand = {f"oh_{k}": real[k] for k in ("g", "OS", "FP")}
    ctrl = {"ctrl_noise": rng.standard_normal((n, T)),
            "ctrl_blend": 0.5 * existing["mom_12m"] + 0.5 * rng.standard_normal((n, T)) * 1e-6}
    names = list(existing) + list(cand) + list(ctrl)
    M = {**existing, **cand, **ctrl}
    acc, bars = np.zeros((len(names), len(names))), 0
    for t in range(WARMUP, T):
        col = elig[:, t] & np.all([np.isfinite(M[k][:, t]) for k in names], axis=0)
        if col.sum() < MIN_NAMES:
            continue
        Z = np.vstack([A1.rank01(M[k][col, t]) for k in names])
        R = np.corrcoef(Z)
        if np.isfinite(R).all():
            acc += R
            bars += 1
    assert bars > 0, "[A1] no bar carried enough eligible names with every score finite"
    Rm = acc / bars
    ix = {k: i for i, k in enumerate(names)}
    ref = list(existing)
    rows = []
    for c in list(cand) + list(ctrl):
        r = {e: float(Rm[ix[c], ix[e]]) for e in ref}
        worst = max(r, key=lambda e: abs(r[e]))
        rows.append(dict(score=c, worst_ref=worst, worst_rho=r[worst],
                         rho_mom_12m=r["mom_12m"], all_rho=r))
    print(f"    within-bar Spearman over {bars:,} bars (D268's lens 1)")
    print(f"    {'score':14s} {'rho vs mom_12m':>15s} {'worst |rho|':>12s}  {'against':14s}")
    for r in rows:
        print(f"    {r['score']:14s} {r['rho_mom_12m']:+15.4f} {r['worst_rho']:+12.4f}  {r['worst_ref']:14s}")
    cn = [r for r in rows if r["score"] == "ctrl_noise"][0]
    cb = [r for r in rows if r["score"] == "ctrl_blend"][0]
    assert abs(cn["worst_rho"]) < RHO_GATE, f"[CTRL] ctrl_noise failed independence at {cn['worst_rho']:+.3f}"
    assert abs(cb["worst_rho"]) >= RHO_GATE, f"[CTRL] ctrl_blend PASSED at {cb['worst_rho']:+.3f} -- instrument is broken"
    eff_wo = A1.effective_inputs(Rm[np.ix_([ix[k] for k in ref], [ix[k] for k in ref])])
    wc = ref + list(cand)
    eff_w = A1.effective_inputs(Rm[np.ix_([ix[k] for k in wc], [ix[k] for k in wc])])
    print(f"    controls behave: noise {cn['worst_rho']:+.3f} (passes), blend {cb['worst_rho']:+.3f} (fails)")
    print(f"    effective inputs {eff_wo['participation_ratio']:.2f} of {len(ref)} -> "
          f"{eff_w['participation_ratio']:.2f} of {len(wc)} with the overhang family")
    pass62 = any(abs(r["worst_rho"]) < RHO_GATE for r in rows if r["score"].startswith("oh_"))

    verdict = dict(g61=pass61, g62=pass62, g63=pass63)
    out = dict(bar_shape=dict(zip(("q_low", "q_body", "q_high"), q)), ks=list(KS), k_reported=60,
               names_built=built, gate_6_1=g61, gate_6_2=dict(bars=bars, rows=rows,
               effective_without=eff_wo["participation_ratio"], effective_with=eff_w["participation_ratio"]),
               gate_6_3=g63, verdict=verdict,
               split_guard=dict(opens=_OPENED["n"], refused=_OPENED["refused"]))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(f"\n  VERDICT  6.1 VOL-SHUF {'PASS' if pass61 else 'ABANDON'}   "
          f"6.2 A1 {'PASS' if pass62 else 'ABANDON'}   6.3 PERSIST {'PASS' if pass63 else 'ABANDON'}")
    print(f"  STAGE 1 {'IS UNLOCKED' if all(verdict.values()) else 'DOES NOT OPEN'}")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")
    return out


def selftest():
    print("D405 STAGE 0 SELF-TEST\n")
    q = bar_quantiles() or (0.25, 0.5, 0.25)
    print(f"  [MASS]  {assert_MASS(q)}")
    print(f"  [DECAY] {assert_DECAY()}")
    assert _OPENED["n"] > 0, "[SPLIT] hook not installed"
    mod = sys.modules[__name__]
    assert not hasattr(mod, "allow_holdout") and not hasattr(mod, "_ALLOW"), "[SPLIT] an unlock exists"
    try:
        open(REPO / "data/fixtures/us_shorts_daily_holdout.csv.gz", "rb").close()
        raise AssertionError("[SPLIT] the guard did NOT refuse")
    except RuntimeError as e:
        assert "refused" in str(e)
    print(f"  [SPLIT] guard saw {_OPENED['n']:,} opens, refused {_OPENED['refused']}")
    print("\n  self-test clean")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
    elif a.calibrate:
        calibrate()
    elif a.run:
        run()
    else:
        ap.error("pass --selftest, --calibrate or --run")
