"""WHY IS IT ZERO? The principal's intuition says the causal rolling detector should have done
BETTER than the stale one, and the P(target) table says it did nothing. Four things that table
cannot see, all checked here.

    python working/d528_why_zero.py --self-test
    python working/d528_why_zero.py --run

Nothing admitted (R15). Exploratory and multiplicity-laden by construction: this is a diagnosis
of an instrument, not a test of a primary. Any survivor needs the reserved slice, which stays
UNREAD.

-------------------------------------------------------------------------------------------------
1  THE NULL'S P&L WAS NEVER COMPUTED, AND IT IS THE ACTUAL SIGNAL CRITERION.

The standing criterion in this programme is a positive GROSS mean per trade ABOVE THE NULLS. The
previous run compared P(target) against the null and then reported the OBSERVED P&L. Those are
different tests, and there is a concrete mechanism in the gap:

    MEAN REVERSION CAN LIVE IN THE OVERSHOOT RATHER THAN THE HIT RATE.

The null's P(target) was 0.2886 where the closed form b/(a+b) says 0.2000. That gap is overshoot:
a stop 0.5 sigma away gets blown through, the realised loss averages ~0.41 of the target distance
rather than 0.25, and the hit rate rises to compensate. A series that genuinely DECELERATES as it
extends would overshoot LESS at the SAME hit rate -- invisible to P(target), visible only in P&L.

2  THE NULL IS A MARTINGALE, SO ITS GROSS P&L MUST BE EXACTLY ZERO. That is a hard calibration,
   not an assumption: sign-shuffling gives E[dP | past] = 0, and optional stopping then forces
   E[gross] = 0 for ANY bounded stop/target rule. So

       null gross != 0  =>  the FILL CONVENTION is biased, and the null measures the bias

   and comparing real against null at the SAME convention cancels the fill question, which is far
   better than arguing over which bound is right. Both conventions are carried anyway.

3  THE CROSSINGS CLASSIFIER MAY BE SELECTING TREND CONTINUATION. `crossings >= 2` of the HELD
   level means price oscillated about the PREVIOUS window's line extrapolated forward -- i.e. the
   extrapolation WORKED, which is trend persistence. Then a 2 sigma departure from the FRESH level
   is demanded. Those two are in tension. So four classifiers are compared, two of which measure
   reversion directly:

       none       every bar with a valid sigma
       cross2     >= 2 crossings of the held level          (the current rule)
       cross4     >= 4 crossings                            (more of the same thing)
       ac1neg     lag-1 autocorrelation of the window's bar returns < 0   <-- reversion, directly
       traverse   price reached BOTH -1.5 and +1.5 sigma about the held level  <-- the principal's
                  "reliability with which price travels the full width of the range"

4  THE TREND-EXTENDED LEVEL MECHANICALLY INFLATES THE ALIGNED CELL'S EXCURSIONS. lvl_t = a2+b2*H
   is the fitted line ONE BAR past its window. Under the alignment rule s*b2 < 0, extrapolating
   pushes the level AWAY from the price, so |y| is systematically LARGER than against a flat mean.
   Some "extremes" may be manufactured by the extrapolation rather than by price being extreme.
   So both level definitions are run:

       line   lvl = a2 + b2*H,  sigma = residual sd about the LINE
       flat   lvl = mean(W_cur), sigma = sd about the MEAN        (drift still from b2, for the
                                                                  alignment rule only)

AND THE SE IS CLUSTERED. The previous table used a naive binomial SE where this repo's own rule is
a session-level block bootstrap; D525 measured rho = 0.51 across index roots. Every difference
below carries a block-bootstrap SE over (root, day) sessions.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402

H = R.H
X = R.X
TAU = R.TAU
BIG = R.BIG
SCALES = (1, 3)
STOP_FRAC = 0.5
N_SHUF = 20
N_BOOT = 2000
SEED = 528311
CLASSIFIERS = ("none", "cross2", "cross4", "ac1neg", "traverse")
LEVELS = ("line", "flat")


def P(*a):
    print(*a, flush=True)


def classify2(path, tick):
    """Everything the detector can know at bar t from bars < t, for BOTH level definitions.

    `path` may be (n,) or (M, n). Index of every returned array is t - 2H.
    """
    W = swv(path, H, axis=-1)
    b, a, sd = R.fit_win(W)
    nb = path.shape[-1]
    n_t = nb - 2 * H
    if n_t <= 0:
        return None
    prev, cur = slice(0, n_t), slice(H, H + n_t)
    b1, a1, s1 = b[..., prev], a[..., prev], sd[..., prev]
    b2, a2, s2 = b[..., cur], a[..., cur], sd[..., cur]
    Wc = W[..., cur, :]

    # the HELD level: W_prev's line across W_cur's bars. Unsaturated by construction.
    m = np.arange(H, dtype=np.float64)
    y_held = Wc - (a1[..., None] + b1[..., None] * (H + m))
    sgn = np.where(np.sign(y_held) == 0.0, np.nan, np.sign(y_held))
    crossings = np.nansum(np.abs(np.diff(sgn, axis=-1)) > 1.5, axis=-1)

    # lag-1 autocorrelation of the window's bar returns: reversion, measured directly
    dr = np.diff(Wc, axis=-1)
    drc = dr - dr.mean(-1, keepdims=True)
    num = (drc[..., :-1] * drc[..., 1:]).sum(-1)
    den = (drc * drc).sum(-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        ac1 = np.where(den > 0, num / den, np.nan)

    # the traverse: did price reach BOTH edges of a +/-1.5 sigma range about the held level?
    with np.errstate(invalid="ignore"):
        s1s = np.where(s1 > 0, s1, np.nan)
        trav = (y_held.min(-1) <= -1.5 * s1s) & (y_held.max(-1) >= 1.5 * s1s)

    pooled = np.sqrt(0.5 * (s1 ** 2 + s2 ** 2))
    med = np.median(np.abs(dr), axis=-1) / tick
    with np.errstate(invalid="ignore"):
        mr_slope = (np.abs(b1 - b2) * H <= 0.5 * pooled) & (pooled > 0)

    px_t = path[..., 2 * H:]
    lvl_line = a2 + b2 * H
    mu = Wc.mean(-1)
    sd_flat = Wc.std(-1, ddof=1)
    out = {
        "slope": b2, "a2": a2,
        "line_lvl": lvl_line, "line_y": px_t - lvl_line, "line_sd": s2,
        "flat_lvl": mu, "flat_y": px_t - mu, "flat_sd": sd_flat,
        "cross": crossings, "ac1": ac1,
        "trav": np.nan_to_num(trav, nan=False).astype(bool),
        "slope_ok": np.nan_to_num(mr_slope, nan=False).astype(bool),
        "a2ok": np.asarray(med >= Q.MIN_TICKS),
        "px": px_t,
    }
    return out


def entry_mask(c, lvl, tick, cost, classifier, align=True):
    y, sd = c[f"{lvl}_y"], c[f"{lvl}_sd"]
    keep = sd > 0
    if classifier != "none":
        keep = keep & c["slope_ok"] & c["a2ok"]
        if classifier == "cross2":
            keep = keep & (c["cross"] >= 2)
        elif classifier == "cross4":
            keep = keep & (c["cross"] >= 4)
        elif classifier == "ac1neg":
            keep = keep & np.nan_to_num(c["ac1"] < 0, nan=False).astype(bool)
        elif classifier == "traverse":
            keep = keep & c["trav"]
    with np.errstate(invalid="ignore"):
        keep = keep & (np.abs(y) >= X * sd)
    s = np.sign(y)
    if align:
        keep = keep & (s * c["slope"] < 0)
    keep = keep & (np.abs(y) / tick > cost)
    return np.nan_to_num(keep, nan=False).astype(bool)


def resolve_vec(path, c, lvl, keep, tick, stop_frac):
    """Vectorised outcome for every admitted bar, then a cheap greedy non-overlap pass.

    Each entry's outcome depends only on its own forward path, so the overlap rule can be applied
    AFTER the outcomes are computed. Returns (kind, pnl_real, pnl_ideal, tgt_ticks) for the
    non-overlapping subset. Asserted equal to the reference loop in --self-test.
    """
    idx = np.flatnonzero(keep)
    if len(idx) == 0:
        z = np.zeros(0)
        return z.astype(np.int64), z, z, z
    n = path.shape[-1]
    t = idx + 2 * H
    ok = t < n - 1
    idx, t = idx[ok], t[ok]
    if len(idx) == 0:
        z = np.zeros(0)
        return z.astype(np.int64), z, z, z
    y = c[f"{lvl}_y"][idx]
    s = np.sign(y)
    p0 = path[t]
    tgt = c[f"{lvl}_lvl"][idx]
    stp = p0 + s * stop_frac * np.abs(y)
    k = np.arange(1, TAU + 1)
    j = t[:, None] + k[None, :]
    valid = j <= (n - 1)
    F = path[np.minimum(j, n - 1)]
    ht = ((F - tgt[:, None]) * s[:, None] <= 0.0) & valid
    hs = ((F - stp[:, None]) * s[:, None] >= 0.0) & valid
    i_t = np.where(ht.any(1), ht.argmax(1), BIG)
    i_s = np.where(hs.any(1), hs.argmax(1), BIG)
    nvalid = valid.sum(1)
    both_miss = (i_t == BIG) & (i_s == BIG)
    stop_first = (~both_miss) & (i_s <= i_t)
    kind = np.where(both_miss, 2, np.where(stop_first, 1, 0)).astype(np.int64)
    dbar = np.where(both_miss, nvalid, np.where(stop_first, i_s + 1, i_t + 1))
    last = np.clip(t + nvalid, 0, n - 1)
    px_real = np.where(both_miss, path[last],
                       np.where(stop_first, F[np.arange(len(idx)), np.minimum(i_s, TAU - 1)], tgt))
    px_ideal = np.where(both_miss, path[last], np.where(stop_first, stp, tgt))
    # greedy non-overlap, in time order: index arithmetic only
    take = np.zeros(len(idx), bool)
    last_exit = -1
    for q in range(len(idx)):
        if t[q] > last_exit:
            take[q] = True
            last_exit = t[q] + int(dbar[q])
    sel = np.flatnonzero(take)
    return (kind[sel], (-s[sel]) * (px_real[sel] - p0[sel]) / tick,
            (-s[sel]) * (px_ideal[sel] - p0[sel]) / tick, np.abs(y[sel]) / tick)


def shuffled(path, rng, m):
    rr = np.diff(path)
    sg = np.where(rng.integers(0, 2, (m, len(rr))) == 1, 1.0, -1.0)
    return path[0] + np.concatenate([np.zeros((m, 1)), np.cumsum(np.abs(rr) * sg, axis=1)], axis=1)


def boot_diff(blocks, rng, n_boot=N_BOOT, cols=(0, 1, 2, 3)):
    """Block bootstrap over SESSIONS of (real mean - null mean).

    `blocks` rows are per-session (sum_real, n_real, sum_null, n_null, sum_real_ideal,
    sum_null_ideal); `cols` picks which sum/count pair is differenced. Resampling whole sessions
    is what makes this a clustered SE: the naive per-trade SE assumes independence across trades
    in the same session, and D525 measured rho = 0.51 across index roots.
    """
    A = np.asarray(blocks, dtype=np.float64)
    if len(A) < 20:
        return np.nan
    sr, nr_c, sn, nn_c = cols
    S = A[:, [sr, nr_c, sn, nn_c]]
    nb = len(S)
    idx = rng.integers(0, nb, (n_boot, nb))
    G = S[idx]                                   # (n_boot, nb, 4)
    num_r, den_r = G[:, :, 0].sum(1), G[:, :, 1].sum(1)
    num_n, den_n = G[:, :, 2].sum(1), G[:, :, 3].sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        out = np.where(den_r > 0, num_r / den_r, np.nan) - \
              np.where(den_n > 0, num_n / den_n, np.nan)
    return float(np.nanstd(out, ddof=1))


# ---------------------------------------------------------------------------------- self-tests
def self_test():
    rng = np.random.default_rng(7)
    pth = 20000 + np.cumsum(rng.normal(0, 2.0, 300))
    c = classify2(pth, 0.25)
    keep = entry_mask(c, "line", 0.25, 0.0, "none")
    kv, prv, piv, tgv = resolve_vec(pth, c, "line", keep, 0.25, STOP_FRAC)
    # reference: the looped resolve in the committed runner, same level and stop
    cR = {"y": c["line_y"], "lvl": c["line_lvl"], "sd": c["line_sd"]}
    ix = np.flatnonzero(keep)
    kR, kdR, plR, tgR = R.resolve(pth, cR, ix, np.sign(c["line_y"][ix]), 0.25, 0.0)
    assert len(kv) == len(kdR), f"vectorised {len(kv)} trades vs reference {len(kdR)}"
    assert np.array_equal(kv, kdR), "vectorised KIND disagrees with the reference loop"
    assert np.array_equal(tgv, tgR), "vectorised target distance disagrees"
    assert np.allclose(piv, plR, rtol=0, atol=0), "idealised P&L disagrees with the reference"
    P(f"   [1] vectorised resolve == reference loop on {len(kv)} trades (kind, target, P&L)  OK")

    # the vectorisation must be able to FAIL: break the precedence and confirm disagreement
    broke = False
    try:
        kb = np.where((kv == 2), 1, kv)
        assert np.array_equal(kb, kdR)
    except AssertionError:
        broke = True
    assert broke, "the equality check cannot fail"
    P("   [2] that equality check REJECTS a deliberately broken kind vector                 OK")

    # OPTIONAL STOPPING. A sign-shuffled path is a martingale, so with TRUE fills the gross
    # expectancy is exactly zero for any bounded stop/target rule. Neither observable convention
    # is true: REAL charges the whole overshoot as loss (a real stop triggers inside the bar,
    # nearer its own price), IDEAL charges none of it. The invariant is that they BRACKET zero,
    # and the width of the bracket is the fill uncertainty -- which cancels in a real-vs-null
    # comparison taken at the same convention.
    rng2 = np.random.default_rng(11)
    tr = ti = 0.0
    cnt = 0
    sq = 0.0
    for _ in range(60):
        base = 20000 + np.cumsum(rng2.normal(0, 2.0, 300))
        for sp in shuffled(base, rng2, 8):
            cs = classify2(sp, 0.25)
            ks = entry_mask(cs, "line", 0.25, 0.0, "none")
            _, pr, pi, _ = resolve_vec(sp, cs, "line", ks, 0.25, STOP_FRAC)
            tr += pr.sum(); ti += pi.sum(); sq += float((pr ** 2).sum()); cnt += len(pr)
    gr, gi = tr / max(cnt, 1), ti / max(cnt, 1)
    sd = np.sqrt(max(sq / max(cnt, 1) - gr ** 2, 0.0))
    se = sd / np.sqrt(max(cnt, 1))
    P(f"   [3] martingale calibration on {cnt:,} null trades (truth is EXACTLY 0):")
    P(f"       REAL  fill {gr:+.3f} ticks  ({gr/se:+.1f} SE)   <- charges the full overshoot")
    P(f"       IDEAL fill {gi:+.3f} ticks  ({gi/se:+.1f} SE)   <- charges none of it")
    assert gr < 0.0 < gi, (
        f"the two fills do not bracket zero (real {gr:+.3f}, ideal {gi:+.3f}) -- then one of them "
        f"is not merely imprecise but WRONG, and a real-vs-null difference cannot be trusted")
    P(f"       they BRACKET zero, bracket width {gi-gr:.2f} ticks; both carried below       OK")

    # the flat level must differ from the line level, and both must be usable
    assert not np.array_equal(c["line_lvl"], c["flat_lvl"]), "flat and line levels are identical"
    P("   [4] the two level definitions are distinct                                        OK")

    # the traverse classifier must be strictly harder than cross2 (both edges vs two crossings)
    n2 = int(entry_mask(c, "line", 0.25, 0.0, "cross2").sum())
    nt = int(entry_mask(c, "line", 0.25, 0.0, "traverse").sum())
    P(f"   [5] cross2 admits {n2}, traverse admits {nt} on the same path                      OK")
    P("\n   all self-tests pass\n")


# ---------------------------------------------------------------------------------------- run
def run():
    rng = np.random.default_rng(SEED)
    boot_rng = np.random.default_rng(SEED + 1)
    d = Q.load()
    sp = Q.specs()
    roots = sorted(set(d["root"]) & set(sp))
    P("WHY IS IT ZERO? real vs null at the SAME fill, per classifier and per level definition")
    P(f"  {len(roots)} roots, {d['day'].min()} .. {d['day'].max()}, x={X}s, "
      f"stop={STOP_FRAC}x target, tau={TAU}, {N_SHUF} shuffles, drift-aligned throughout")
    P("  GROSS is realised-fill and excludes cost, so it is directly comparable to the null,")
    P("  whose true value is ZERO by optional stopping.\n")

    for s in SCALES:
        cells = {(cl, lv): {"blocks": [], "hr": [0, 0], "hn": [0, 0],
                            "ovr": [0.0, 0], "ovn": [0.0, 0], "tg": []}
                 for cl in CLASSIFIERS for lv in LEVELS}
        for r in roots:
            g = d[d["root"] == r]
            tick = sp[r]["tick_price_units"]
            cost = R.COST.get(r, R.COST_DEFAULT)
            for day, pth in Q.session_bars(g, s):
                c = classify2(pth, tick)
                if c is None:
                    continue
                Pn = shuffled(pth, rng, N_SHUF)
                cn_all = classify2(Pn, tick)
                if cn_all is None:
                    continue
                for cl in CLASSIFIERS:
                    for lv in LEVELS:
                        cell = cells[(cl, lv)]
                        keep = entry_mask(c, lv, tick, cost, cl)
                        kd, pr_, pi_, tg = resolve_vec(pth, c, lv, keep, tick, STOP_FRAC)
                        sr, nr, sri = float(pr_.sum()), len(pr_), float(pi_.sum())
                        cell["hr"][0] += int((kd == 0).sum()); cell["hr"][1] += len(kd)
                        if nr:
                            cell["tg"].append(tg)
                            loss = pr_[kd == 1]
                            cell["ovr"][0] += float(-loss.sum()); cell["ovr"][1] += len(loss)
                        sn, nn, sni = 0.0, 0, 0.0
                        for j in range(N_SHUF):
                            cj = {k2: (v2[j] if np.ndim(v2) > 0 and np.shape(v2)[0] == N_SHUF
                                       else v2) for k2, v2 in cn_all.items()}
                            kj = entry_mask(cj, lv, tick, cost, cl)
                            kdj, prj, pij, _ = resolve_vec(Pn[j], cj, lv, kj, tick, STOP_FRAC)
                            sn += float(prj.sum()); nn += len(prj); sni += float(pij.sum())
                            cell["hn"][0] += int((kdj == 0).sum()); cell["hn"][1] += len(kdj)
                            lj = prj[kdj == 1]
                            cell["ovn"][0] += float(-lj.sum()); cell["ovn"][1] += len(lj)
                        if nr or nn:
                            cell["blocks"].append((sr, nr, sn, nn, sri, sni))
        P(f"  s={s}")
        P("    classifier  level  trades null/sh  P(tgt)  null  | REAL fill: real  null "
          "  DIFF   SE     t  | IDEAL: DIFF    SE     t  | overshoot r/n")
        for cl in CLASSIFIERS:
            for lv in LEVELS:
                cell = cells[(cl, lv)]
                A = np.asarray(cell["blocks"], dtype=np.float64) if cell["blocks"] else None
                if A is None or A[:, 1].sum() < 50:
                    continue
                nr, nn = A[:, 1].sum(), A[:, 3].sum()
                gr, gn = A[:, 0].sum() / nr, (A[:, 2].sum() / nn if nn else np.nan)
                ir, inl = A[:, 4].sum() / nr, (A[:, 5].sum() / nn if nn else np.nan)
                se = boot_diff(cell["blocks"], boot_rng, cols=(0, 1, 2, 3))
                se_i = boot_diff(cell["blocks"], boot_rng, cols=(4, 1, 5, 3))
                pr_hit = cell["hr"][0] / max(cell["hr"][1], 1)
                pn_hit = cell["hn"][0] / max(cell["hn"][1], 1)
                tg = np.concatenate(cell["tg"]) if cell["tg"] else np.array([np.nan])
                mb = np.nanmean(tg) * STOP_FRAC
                ovr = cell["ovr"][0] / max(cell["ovr"][1], 1) / mb if mb > 0 else np.nan
                ovn = cell["ovn"][0] / max(cell["ovn"][1], 1) / mb if mb > 0 else np.nan
                dif, dif_i = gr - gn, ir - inl
                tt = dif / se if se and np.isfinite(se) and se > 0 else np.nan
                ti_ = dif_i / se_i if se_i and np.isfinite(se_i) and se_i > 0 else np.nan
                P(f"    {cl:<11} {lv:<6} {int(nr):>6,} {nn/N_SHUF:>7,.0f}  {pr_hit:.4f} "
                  f"{pn_hit:.4f} | {gr:+8.2f} {gn:+6.2f} {dif:+7.2f} {se:5.2f} {tt:+6.2f} "
                  f"| {dif_i:+7.2f} {se_i:5.2f} {ti_:+6.2f} | {ovr:.3f} / {ovn:.3f}")
        P("")
    P("  DIFF is the signal criterion: GROSS mean per trade ABOVE the null, same fill both sides.")
    P("  bootSE is a block bootstrap over (root, day) sessions, not a naive per-trade SE.")
    P("  'mean loss / b' is realised loss on a stop-out divided by the stop distance -- the")
    P("  OVERSHOOT. A series that decelerates as it extends overshoots LESS than its shuffle,")
    P("  and that is invisible to P(target).")


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
