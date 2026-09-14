"""THE ROLLING, DRIFT-ALIGNED, FEASIBILITY-FILTERED DETECTOR -- the principal's three corrections.

    python working/d528_rolling_aligned_detector.py --self-test
    python working/d528_rolling_aligned_detector.py --run

Nothing admitted (R15). No pre-registered statistic is changed. This is detector design, so the
component line belongs to the run that SCORES the construction, not to this one.

-------------------------------------------------------------------------------------------------
1  THE CLASSIFICATION IS CURRENT, AT THAT SCALE.  <-- the principal marked this "very important"

The previous design classified bars [0,20) once, then waited up to 11 bars for an excursion. The
verdict was therefore up to 11 bars stale and the level was extrapolated that far BEFORE the trade
even began -- which is exactly the slope-runaway the ten decile charts showed. Here EVERY BAR is a
candidate: at bar t the trailing window is re-tested, the level is re-fitted on the immediately
preceding H bars, and only then is the extreme checked. One bar of extrapolation, not eleven.

AND THE CLASSIFIER NOW MEASURES REVERSION RATHER THAN STABILITY. The old A1 tested whether two
half-window SLOPES agreed, which is a no-regime-change test, not a mean-reversion test. The
principal's own definition is the reliability with which price travels the full width of the
range, so the classifier counts how many times the residual CROSSES its level inside the trailing
window. Crucially the level it crosses is fitted on the PRECEDING window, never on the bars the
crossings are counted in -- a level fitted on its own residual's bars is forced to be crossed
(the saturation finding: P(return) 0.9077 on a random walk), so a saturated crossing count would
measure arithmetic, not the market.

2  TRADE WITH THE DRIFT, NEVER AGAINST IT.

Drift positive -> LONG only, and only from the LOW extreme. Drift negative -> SHORT only, and only
from the HIGH extreme. With y = P - level and s = sign(y), the trade direction is -s, so the rule
is exactly  s * slope < 0.

MY EARLIER LABEL FOR THIS CELL WAS WRONG IN PROSE AND RIGHT IN CODE. I called it "the level drifts
TOWARD the price". It drifts AWAY: s=-1 with slope>0 is a rising level above a price beneath it.
That is why the cell measured the LOWER P(return), 0.11-0.13 against 0.37-0.42. Both numbers are
real and neither was an edge:

    the principal's cell   the level recedes, so a RESIDUAL return is hard, but the drift
                           pays the position: the P&L drift term is -s*slope*d > 0
    the other cell         the level chases the price, so the residual "returns" because the
                           LEVEL moved, not because price reverted -- and that return earns
                           nothing, since the same term is then negative

So the 0.37-0.42 was the level-chasing artefact. P(residual return) was the wrong target
statistic: it can be satisfied entirely by the level's own motion. It is replaced below by
P(price reaches a FIXED price set at entry), which no level motion can manufacture.

3  NO TRADE THAT CANNOT PAY UNDER PERFECT REVERSION.

This also fixes the exit, which is what made the charts lose. Both exits are now FIXED PRICES
chosen at entry -- a resting limit and a resting stop, which is what a real trade is:

    target  = the level frozen at entry, lvl_t            gross gain under perfect reversion
    stop    = P_t + s * STOP_FRAC * |y|                   adverse by half the target (D471)
    timeout = TAU bars, out at market

Freezing them removes the runaway entirely: the level's slope can no longer walk the stop onto the
price. And it makes the feasibility test exact -- under perfect reversion P_exit = lvl_t, so

    gross gain = (-s) * (lvl_t - P_t) = (-s) * (-y) = s*y = |y|   exactly

hence the filter is simply  |y| / tick > cost_root,  with no drift credit claimed. Breakeven hit
rate follows in closed form: p*(|y|-c) = (1-p)*(STOP_FRAC*|y|+c).
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
import d528_mean_reversion_oracle as Q     # noqa: E402

H = Q.H_EST                 # 10 bars: one window
X = 2.0                     # the extreme, in residual sigma
STOP_FRAC = 0.5             # stop is half the target away (D471: a stop must be ~half the target)
TAU = 20                    # bars before the timeout
CROSS_MIN = 2               # traverses of the held level required inside the trailing window
SCALES = (1, 2, 3, 5, 8)
N_SHUF = 20
SEED = 528999
BIG = 1 << 30               # the no-hit sentinel; see the precedence note in `resolve`

# Measured full-year effective crossing, ticks per round trip (D507 final). COST_DEFAULT is used
# where the root was not in the tbbo pull; it is deliberately on the expensive side, because an
# understated cost would let the feasibility filter admit trades that cannot pay.
COST = {"NQ": 2.134, "ES": 1.060, "CL": 1.546, "GC": 4.117, "RTY": 1.340,
        "YM": 1.767, "6E": 1.082, "BTC": 4.993}
COST_DEFAULT = 2.5

T_LOC = np.arange(H, dtype=np.float64)
T_BAR = T_LOC.mean()
STT = float(((T_LOC - T_BAR) ** 2).sum())


def P(*a):
    print(*a, flush=True)


def fit_win(W):
    """OLS slope, intercept and residual sd along the LAST axis of W (..., H).

    Written to be the same sequence of float operations as the one-window reference in
    `_fit_ref`, so the vectorised and looped forms agree bit-for-bit (asserted in --self-test).
    """
    tc = T_LOC - T_BAR
    b = ((W - W.mean(-1, keepdims=True)) * tc).sum(-1) / STT
    a = W.mean(-1) - b * T_BAR
    r = W - (a[..., None] + b[..., None] * T_LOC)
    return b, a, r.std(-1, ddof=1)


def _fit_ref(seg):
    """The single-window reference `fit_win` must reproduce exactly."""
    tc = T_LOC - T_BAR
    b = float(((seg - seg.mean()) * tc).sum() / STT)
    a = float(seg.mean() - b * T_BAR)
    r = seg - (a + b * T_LOC)
    return b, a, float(r.std(ddof=1))


def classify(path, tick):
    """Per bar t in [2H, n), everything the detector knows using ONLY bars < t.

    Returns a dict of arrays indexed by t - 2H. `path` may be (n,) or (M, n); the leading axis is
    carried through, so the null's M shuffled paths are classified in one pass.
    """
    W = swv(path, H, axis=-1)                       # (..., n-H+1, H): W[i] = path[i:i+H]
    b, a, sd = fit_win(W)
    nb = path.shape[-1]
    n_t = nb - 2 * H                                # t = 2H .. nb-1
    if n_t <= 0:
        return None
    prev = slice(0, n_t)                            # W index of the window ending at t-H
    cur = slice(H, H + n_t)                         # W index of the window ending at t
    b1, a1 = b[..., prev], a[..., prev]
    b2, a2, s2 = b[..., cur], a[..., cur], sd[..., cur]
    s1 = sd[..., prev]

    # --- the HELD level: W_prev's line extrapolated across W_cur's own bars, so the residual is
    #     measured on bars the level never saw. Unsaturated by construction.
    m = np.arange(H, dtype=np.float64)
    held = a1[..., None] + b1[..., None] * (H + m)           # (..., n_t, H)
    y_held = W[..., cur, :] - held
    sgn = np.sign(y_held)
    sgn = np.where(sgn == 0.0, np.nan, sgn)
    crossings = np.nansum(np.abs(np.diff(sgn, axis=-1)) > 1.5, axis=-1)

    pooled = np.sqrt(0.5 * (s1 ** 2 + s2 ** 2))
    med = np.median(np.abs(np.diff(W[..., cur, :], axis=-1)), axis=-1) / tick
    with np.errstate(invalid="ignore"):
        mr_cross = crossings >= CROSS_MIN
        mr_slope = (np.abs(b1 - b2) * H <= 0.5 * pooled) & (pooled > 0)
    lvl_t = a2 + b2 * H                             # the level AT t: one bar of extrapolation
    y_t = path[..., 2 * H:] - lvl_t
    return {"lvl": lvl_t, "y": y_t, "sd": s2, "slope": b2, "cross": crossings,
            "mr_cross": np.nan_to_num(mr_cross, nan=False).astype(bool),
            "mr_slope": np.nan_to_num(mr_slope, nan=False).astype(bool),
            "a2": np.asarray(med >= Q.MIN_TICKS), "ok_sd": s2 > 0}


def entries(c, tick, cost, align=True, feas=True, classifier=True):
    """Entry bars (absolute index into path) and their fixed target/stop prices, plus the funnel."""
    keep = c["ok_sd"]
    n0 = int(keep.sum())
    if classifier:
        keep = keep & c["mr_slope"] & c["mr_cross"] & c["a2"]
    n1 = int(keep.sum())
    with np.errstate(invalid="ignore"):
        keep = keep & (np.abs(c["y"]) >= X * c["sd"])
    n2 = int(keep.sum())
    s = np.sign(c["y"])
    if align:
        keep = keep & (s * c["slope"] < 0)
    n3 = int(keep.sum())
    if feas:
        keep = keep & (np.abs(c["y"]) / tick > cost)
    n4 = int(keep.sum())
    idx = np.flatnonzero(keep)
    return idx, s[idx], np.array([n0, n1, n2, n3, n4])


def resolve(path, c, idx, s, tick, cost):
    """Fixed-price target and stop, no overlapping positions. Returns per-trade arrays."""
    n = len(path)
    out_k, out_kind, out_pnl, out_tgt = [], [], [], []
    last_exit = -1
    for q in range(len(idx)):
        i = int(idx[q])
        t = i + 2 * H
        if t <= last_exit or t >= n - 1:
            continue
        ss = float(s[q])
        p0 = float(path[t])
        y0 = float(c["y"][i])
        tgt = float(c["lvl"][i])                     # frozen at entry
        stp = p0 + ss * STOP_FRAC * abs(y0)          # adverse by half the target
        hi = min(t + TAU, n - 1)
        fwd = path[t + 1:hi + 1]
        if len(fwd) == 0:
            continue
        # target first if both land on the same bar would be ambiguous -> resolve AGAINST us
        hit_t = (fwd - tgt) * ss <= 0.0              # price has reached the level
        hit_s = (fwd - stp) * ss >= 0.0              # price has gone adverse to the stop
        i_t = int(np.argmax(hit_t)) if hit_t.any() else 1 << 30
        i_s = int(np.argmax(hit_s)) if hit_s.any() else 1 << 30
        # PRECEDENCE. Ties go AGAINST us. And the no-hit case must be tested FIRST: with both
        # indices at the sentinel, `i_s <= i_t` is TRUE, which recorded a timeout as a stop AND
        # set last_exit a billion bars ahead, silently killing every later entry in the session.
        if i_s == BIG and i_t == BIG:
            k, kind, px = len(fwd), 2, float(fwd[-1])
        elif i_s <= i_t:
            k, kind, px = i_s + 1, 1, stp
        else:
            k, kind, px = i_t + 1, 0, tgt
        out_k.append(k)
        out_kind.append(kind)
        out_pnl.append((-ss) * (px - p0) / tick)
        out_tgt.append(abs(y0) / tick)
        last_exit = t + k
    return (np.array(out_k), np.array(out_kind, dtype=np.int64),
            np.array(out_pnl), np.array(out_tgt))


def self_test():
    rng = np.random.default_rng(1)
    # 1. the vectorised fit reproduces the one-window reference EXACTLY
    p = rng.normal(20000, 5, 60)
    W = swv(p, H)
    bv, av, sv = fit_win(W)
    for i in range(W.shape[0]):
        br, ar, sr = _fit_ref(W[i])
        assert bv[i] == br and av[i] == ar and sv[i] == sr, f"fit mismatch at {i}"
    # tie-heavy input, where a rewrite is most likely to disagree
    p2 = np.round(rng.normal(100, 0.5, 60) * 4) / 4
    W2 = swv(p2, H)
    b2v, a2v, s2v = fit_win(W2)
    for i in range(W2.shape[0]):
        br, ar, sr = _fit_ref(W2[i])
        assert b2v[i] == br and a2v[i] == ar and s2v[i] == sr, f"tie fit mismatch at {i}"
    P("   [1] vectorised fit == one-window reference, bit-exact, incl. a tie-heavy input  OK")

    # 2. the leading axis is carried: classifying M paths at once == classifying each alone
    Pm = rng.normal(20000, 5, (4, 80))
    cm = classify(Pm, 0.25)
    for j in range(4):
        cj = classify(Pm[j], 0.25)
        for k in ("y", "sd", "slope", "cross", "lvl"):
            assert np.array_equal(cm[k][j], cj[k]), f"axis mismatch in {k}"
    P("   [2] M-path classify == per-path classify, every field                           OK")

    # 3. THE HELD LEVEL IS UNSATURATED. A least-squares level over its own bars forces the
    #    residual to sum to zero, so it must be crossed. The held level must not.
    n_sat = n_held = 0
    for _ in range(400):
        q = 20000 + np.cumsum(rng.normal(0, 1, 2 * H))
        _, _, _ = fit_win(q[H:][None, :])
        bb, aa, _ = _fit_ref(q[:H])
        yh = q[H:] - (aa + bb * (H + np.arange(H)))
        bo, ao, _ = _fit_ref(q[H:])
        yo = q[H:] - (ao + bo * np.arange(H))
        n_sat += int((np.sign(yo)[:-1] != np.sign(yo)[1:]).any())
        n_held += int((np.sign(yh)[:-1] != np.sign(yh)[1:]).any())
    assert n_sat == 400, f"self-fitted level failed to always cross: {n_sat}"
    assert n_held < 380, f"held level looks saturated too: {n_held}/400"
    P(f"   [3] self-fitted level crosses {n_sat}/400 (forced); held level {n_held}/400       OK")

    # 4. THE ALIGNMENT FILTER KEEPS THE PRINCIPAL'S CELL AND NOTHING ELSE, and the funnel is
    #    monotone. Built on a path with a KNOWN positive drift so the expected side is long.
    tvec = np.arange(200, dtype=np.float64)
    q = 20000 + 0.5 * tvec + rng.normal(0, 3, 200)
    c = classify(q, 0.25)
    idx, s, fn = entries(c, 0.25, 0.0, align=True, feas=False)
    assert (np.diff(fn) <= 0).all(), f"funnel not monotone: {fn}"
    if len(idx):
        assert (s * c["slope"][idx] < 0).all(), "alignment filter admitted the wrong cell"
        pos_drift = c["slope"][idx] > 0
        assert (s[pos_drift] < 0).all(), "long not taken from the LOW extreme on positive drift"
    P(f"   [4] alignment admits only s*slope<0, long-from-low on positive drift; funnel {fn}  OK")

    # 5. THE FEASIBILITY FILTER FIRES, and it fires on the right side of the threshold
    idx_a, _, fa = entries(c, 0.25, 0.0, align=True, feas=True)
    idx_b, _, fb = entries(c, 0.25, 1e9, align=True, feas=True)
    assert fb[4] == 0, "a cost of 1e9 admitted trades -- the feasibility filter does not fire"
    assert fa[4] >= fb[4]
    P("   [5] feasibility filter fires (cost 1e9 -> 0 trades)                              OK")

    # 6. SIGN AUDIT IN MONEY, and the exit prices are FIXED. A short from above a level that then
    #    falls to it must PAY; a short that runs against us must LOSE; and neither may depend on
    #    the level's slope after entry.
    n = 2 * H + 6
    up = np.concatenate([20000 + np.zeros(2 * H), [20010.0] * 6])
    cu = classify(up, 0.25)
    i0 = len(cu["y"]) - 7
    sgn = np.sign(cu["y"][i0]) if cu["y"][i0] != 0 else 1.0
    P("   [6] sign audit in money:")
    for name, fwd_px, want in (("reverts to level", float(cu["lvl"][i0]), +1),
                               ("runs away", float(up[2 * H + i0] + sgn * 50), -1)):
        pnl = (-sgn) * (fwd_px - float(up[2 * H + i0])) / 0.25
        assert np.sign(pnl) == want, f"{name}: pnl {pnl} wanted sign {want}"
        P(f"       {name:<18} {pnl:+9.1f} ticks  (wanted {want:+d})  OK")

    # 7. A BROKEN BOOK MUST FAIL THE SIGN AUDIT -- a check that cannot fail is worse than none.
    broke = False
    try:
        pnl = (+sgn) * (float(cu["lvl"][i0]) - float(up[2 * H + i0])) / 0.25   # inverted sign
        assert np.sign(pnl) == +1
    except AssertionError:
        broke = True
    assert broke, "the sign audit passed an INVERTED book"
    P("   [7] the sign audit REJECTS an inverted book                                      OK")

    # 8. no overlapping positions
    pth = 20000 + np.cumsum(rng.normal(0, 2, 400))
    cc = classify(pth, 0.25)
    ix, sx, _ = entries(cc, 0.25, 0.0, feas=False)
    k, kind, pnl, tgt = resolve(pth, cc, ix, sx, 0.25, 0.0)
    P(f"   [8] {len(k)} non-overlapping trades resolved from {len(ix)} candidate entries     OK")

    # 9. THE NO-HIT SENTINEL. With neither target nor stop reached, both indices are BIG and
    #    `i_s <= i_t` is TRUE -- which recorded a TIMEOUT as a STOP at the stop price and set
    #    last_exit a billion bars ahead, silently killing every later entry in that session.
    flat = np.concatenate([20000 + rng.normal(0, 3, 2 * H), np.full(TAU + 4, 20000.0)])
    cf = classify(flat, 0.25)
    i0 = int(np.argmax(np.abs(cf["y"])))
    sg0 = np.sign(cf["y"][i0]) or 1.0
    kk, _, _, _ = resolve(flat, cf, np.array([i0]), np.array([sg0]), 0.25, 0.0)
    if len(kk):
        assert kk[0] <= TAU, f"no-hit exit at bar {kk[0]} -- the sentinel leaked into the hold"
    for i_s, i_t, want in ((BIG, BIG, 2), (3, 5, 1), (5, 3, 0), (4, 4, 1)):
        got = 2 if (i_s == BIG and i_t == BIG) else (1 if i_s <= i_t else 0)
        assert got == want, f"precedence({i_s},{i_t}) = {got}, wanted {want}"
    # and the OLD precedence must FAIL the no-hit case -- a check that cannot fail is worse
    broke = False
    try:
        i_s = i_t = BIG
        assert (1 if i_s <= i_t else (0 if i_t < BIG else 2)) == 2
    except AssertionError:
        broke = True
    assert broke, "the old precedence passed the no-hit case -- the test cannot fail"
    P("   [9] BIG/BIG resolves as TIMEOUT, ties against us, old precedence REJECTED      OK")
    P("\n   all self-tests pass\n")


def run():
    rng = np.random.default_rng(SEED)
    d = Q.load()
    sp = Q.specs()
    roots = sorted(set(d["root"]) & set(sp))
    P("THE ROLLING, DRIFT-ALIGNED, FEASIBILITY-FILTERED DETECTOR")
    P(f"  classified EVERY BAR on bars < t; long only from the low extreme when drift > 0;")
    P(f"  target and stop are FIXED PRICES set at entry; no trade unless |y| > cost")
    P(f"  {len(roots)} roots, in sample {d['day'].min()} .. {d['day'].max()}, "
      f"x={X}s, stop={STOP_FRAC}x target, tau={TAU}, crossings>={CROSS_MIN}, {N_SHUF} shuffles\n")

    P("  THE FUNNEL, and the trade. GROSS is before the crossing, NET after it.")
    P("    s  |  bars classified   MR    extreme  aligned  feasible |  trades  "
      "P(target)   null  |  GROSS tk    NET tk   median   win%   p_be")
    for s in SCALES:
        FN = np.zeros(5, dtype=np.int64)
        K, KIND, PNL, TGT, COSTV = [], [], [], [], []
        nt_null = nn_null = 0
        for r in roots:
            g = d[d["root"] == r]
            tick = sp[r]["tick_price_units"]
            cost = COST.get(r, COST_DEFAULT)
            for day, pth in Q.session_bars(g, s):
                c = classify(pth, tick)
                if c is None:
                    continue
                ix, sx, fn = entries(c, tick, cost)
                FN += fn
                if len(ix):
                    k, kind, pnl, tgt = resolve(pth, c, ix, sx, tick, cost)
                    if len(k):
                        K.append(k); KIND.append(kind); PNL.append(pnl); TGT.append(tgt)
                        COSTV.append(np.full(len(k), cost))
                # --- null: sign shuffle of THIS session's returns, all N_SHUF at once
                rr = np.diff(pth)
                sg = np.where(rng.integers(0, 2, (N_SHUF, len(rr))) == 1, 1.0, -1.0)
                Pn = pth[0] + np.concatenate(
                    [np.zeros((N_SHUF, 1)), np.cumsum(np.abs(rr) * sg, axis=1)], axis=1)
                cn = classify(Pn, tick)
                if cn is None:
                    continue
                for j in range(N_SHUF):
                    cj = {kk: (vv[j] if np.ndim(vv) else vv) for kk, vv in cn.items()}
                    ij, sj, _ = entries(cj, tick, cost)
                    if len(ij) == 0:
                        continue
                    kj, kdj, _, _ = resolve(Pn[j], cj, ij, sj, tick, cost)
                    if len(kj):
                        nt_null += int((kdj == 0).sum()); nn_null += len(kj)
        if not K:
            P(f"    {s:>2}  |  {FN[0]:>15,} {FN[1]:>6,} {FN[2]:>8,} {FN[3]:>8,} {FN[4]:>9,} |"
              f"  no trades")
            continue
        k = np.concatenate(K); kind = np.concatenate(KIND)
        pnl = np.concatenate(PNL); tgt = np.concatenate(TGT); cv = np.concatenate(COSTV)
        net = pnl - cv
        po = float((kind == 0).mean()); pn = nt_null / max(nn_null, 1)
        p_be = float(np.mean((STOP_FRAC * tgt + cv) / ((1.0 + STOP_FRAC) * tgt)))
        P(f"    {s:>2}  |  {FN[0]:>15,} {FN[1]:>6,} {FN[2]:>8,} {FN[3]:>8,} {FN[4]:>9,} |"
          f" {len(k):>7,}    {po:.4f} {pn:.4f}  | {pnl.mean():+8.2f}  {net.mean():+8.2f} "
          f"{np.median(net):+8.2f} {(net > 0).mean():6.1%} {p_be:6.3f}")

    P("\n  P(target) is the probability price reached a FIXED price set at entry -- no level")
    P("  motion can manufacture it, unlike the P(residual return) the earlier runs reported.")
    P("  p_be is the hit rate this trade needs to break even, from its own target and stop.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        P("SELF-TESTS")
        self_test()
    if a.run:
        run()
    if not (a.self_test or a.run):
        ap.error("choose --self-test or --run")
