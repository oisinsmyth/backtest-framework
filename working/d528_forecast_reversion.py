"""CAN FORWARD MEAN REVERSION BE FORECAST, rather than inferred from the fact that it just happened?

    python working/d528_forecast_reversion.py --self-test
    python working/d528_forecast_reversion.py --run

Nothing admitted (R15). Wide 5-minute fixture, 2010 -> 2026-04-10. **The reserved slice is NOT
read.** No holdout is spent by anything here.

THE PIVOT, and why it is a different question. Every construction so far conditioned on a range
having ALREADY traversed, and ADDENDUM 8 measured that premise as INVERTED: P(traverse ahead) is
0.1732, P(traverse ahead | it just traversed) is 0.1387, a lift of -0.0345 at t = -25.08. The
principal's question is whether forward reversion can instead be FORECAST from something else.

AN ORACLE READING [t, t+H) IS CONTAMINATED; A FORECASTER PREDICTING [t, t+H) FROM DATA BEFORE t IS
NOT. ADDENDUM 9 rejected the overlapping oracle as evidence that REGIME knowledge pays, because it
partly knew the trade's outcome. But as a CEILING FOR A FORECASTER it is exactly the right number:
a perfect predictor of forward traversal selects precisely those trades and earns what they earned
-- gross +23.92 against a matched p95 of +3.67, net +$19.23 per trade.

So the ceiling is measured and large, and the whole question reduces to: HOW MUCH OF FORWARD
TRAVERSAL IS PREDICTABLE FROM CAUSAL DATA?

TWO STEPS, IN THIS ORDER, because a forecaster for an unforecastable target is wasted work:

  1  IS THE TARGET FORECASTABLE? Univariate lift of each causal feature on forward traversal,
     against the 17.3% base rate, with a block bootstrap over (root, day) and an OUT-OF-TIME
     split -- quintile edges taken from 2010-2019 and applied unchanged to 2020-2026, so a
     feature that only works in the period that defined it is visible as such.
  2  DOES LIFT TRANSLATE TO MONEY? P&L of the top- and bottom-quintile cells against the
     ADDENDUM 9 matched control, scored on mean, median and trimmed mean.

EVERY FEATURE IS STRICTLY CAUSAL -- computed from bars before t. `trav_past` is carried as the
known-bad baseline: any feature that cannot beat a predictor already measured at t = -25 is noise.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view as swv

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402
import d528_wide as W                           # noqa: E402

H = Z.H
X, G, TAU = 2.0, 3.0, 20
TRAV_K = 1.5
TARGET, FRAME = "reflect", "drift"
SPLIT = "2020-01-01"          # out-of-time boundary, both halves well inside the cutoff
N_DRAW = 400
SEED = 528877
FEATS = ("trav_past", "vol_ratio", "sigma_pct", "ac1", "vratio2", "squeeze",
         "tod", "elapsed", "drift_str", "vol_fast", "vol_chg")


def P(*a):
    print(*a, flush=True)


def forward_traverse(path, c):
    """Target: does price reach BOTH -1.5 and +1.5 sigma of the [t-H,t) line over [t, t+H)?

    Vectorised. Index is t-2H, matching classify2. `ok` marks bars with a full forward window.
    """
    n = len(path)
    n_t = n - 2 * H
    out = np.zeros(n_t, bool)
    ok = np.zeros(n_t, bool)
    if n_t <= 0:
        return out, ok
    F = swv(path, H)                       # F[i] = path[i:i+H]
    t = np.arange(2 * H, n)
    valid = t + H <= n
    tv = t[valid]
    m = np.arange(H, dtype=np.float64)
    a = c["a2"][valid]
    b = c["slope"][valid]
    sd = c["line_sd"][valid]
    y = F[tv] - (a[:, None] + b[:, None] * (H + m))
    with np.errstate(invalid="ignore"):
        hit = (y.min(1) <= -TRAV_K * sd) & (y.max(1) >= TRAV_K * sd) & (sd > 0)
    out[valid] = np.nan_to_num(hit, nan=False).astype(bool)
    ok[valid] = np.isfinite(sd) & (sd > 0)
    return out, ok


def _sb_rng(path, r, t, w_long):
    """The two rolling statistics that were Python loops over every bar: the long-baseline
    return sd, and the long-window high-low range.

    WHY THIS EXISTS. At 84 bars a session those loops cost 0.83 ms of a 1.06 ms session and
    nobody noticed. At 420 bars (the 1-minute fixture) they cost 3.82 ms of 4.28 ms -- 89% --
    which is 9.4 minutes a pass over 131,289 sessions, four passes for the two legs. Profiled
    before rewriting, per CLAUDE.md; every previous guess about where the cost sat was wrong.

    EXACTNESS, NOT TOLERANCE. Both are computed over a window that is CLIPPED near the start of
    the series and CONSTANT-LENGTH after it, so:
      * the constant-length region goes through sliding_window_view, whose per-window reduction
        runs the same two-pass std and the same max/min as the slice did;
      * the clipped region keeps the original loop, because its windows are all different
        lengths and there is nothing to vectorise over.
    max and min are exactly associative so the range is safe unconditionally; the sd is the one
    that could differ in the last ULP, which is why the self-test asserts bit-equality on a
    TIE-HEAVY input as well as a smooth one (ties are where a rewrite and its reference
    disagree).
    """
    n = len(path)
    sb = np.empty(len(t))
    rng_l = np.empty(len(t))
    # sb: window r[max(tt-w_long+1, 1) : tt]; unclipped length is w_long - 1
    # rng: window path[max(tt-w_long, 0) : tt]; unclipped length is w_long
    lo_sb = w_long                      # first tt whose sb window is unclipped (tt-w_long+1 >= 1)
    lo_rg = w_long                      # first tt whose range window is unclipped
    cut = max(int(np.searchsorted(t, lo_sb)), int(np.searchsorted(t, lo_rg)))
    for k in range(cut):
        tt = int(t[k])
        a = max(tt - w_long + 1, 1)
        sb[k] = r[a:tt].std(ddof=1) if tt - a > 2 else np.nan
        rng_l[k] = np.ptp(path[max(tt - w_long, 0):tt]) if tt > 6 else np.nan
    if cut < len(t):
        tv = t[cut:]
        Ws = swv(r, w_long - 1)                  # Ws[i] = r[i : i + w_long - 1]
        sb[cut:] = Ws[tv - w_long + 1].std(axis=1, ddof=1)
        Wl = swv(path, w_long)                   # Wl[i] = path[i : i + w_long]
        blk = Wl[tv - w_long]
        rng_l[cut:] = blk.max(1) - blk.min(1)
    assert n == len(path)
    return sb, rng_l


def causal_features_ref(path, c, vm, b0):
    """REFERENCE: the original, with the two per-bar Python loops. Never called by a runner;
    kept so the fast path has something to be proved equal to."""
    return _causal(path, c, vm, b0, fast=False)


def causal_features(path, c, vm, b0):
    """Everything a forecaster may read at bar t, from bars strictly before t."""
    return _causal(path, c, vm, b0, fast=True)


def _causal(path, c, vm, b0, fast=True):
    n = len(path)
    n_t = n - 2 * H
    r = np.diff(path, prepend=path[0])
    t = np.arange(2 * H, n)
    Wr = swv(r, H)
    w = Wr[t - H + 1]                       # the H returns ending at t
    wq = w[:, :-1]                          # strictly before the trigger bar

    # past traversal -- the known-bad baseline, taken from classify2's own held-level flag
    Wp = swv(path, H)
    trav_past = c["trav"].astype(float)

    with np.errstate(invalid="ignore", divide="ignore"):
        sw = wq.std(axis=1, ddof=1)
        if fast:
            sb, rng_long = _sb_rng(path, r, t, 6 * H)
        else:
            sb = np.array([r[max(tt - 6 * H + 1, 1):tt].std(ddof=1)
                           if tt - max(tt - 6 * H + 1, 1) > 2 else np.nan for tt in t])
            rng_long = np.array([np.ptp(path[max(tt - 6 * H, 0):tt]) if tt > 6 else np.nan
                                 for tt in t])
        vol_ratio = np.where(sb > 0, sw / sb, np.nan)

        # lag-1 autocorrelation of the window's returns
        dc = wq - wq.mean(1, keepdims=True)
        num = (dc[:, :-1] * dc[:, 1:]).sum(1)
        den = (dc * dc).sum(1)
        ac1 = np.where(den > 0, num / den, np.nan)

        # variance ratio: var of 2-bar returns / (2 * var of 1-bar returns); <1 = reverting
        two = wq[:, :-1] + wq[:, 1:]
        vratio2 = np.where(den > 0, two.var(1, ddof=1) / (2 * wq.var(1, ddof=1)), np.nan)

        # range compression: recent high-low over a longer high-low
        rng_s = Wp[t - H].max(1) - Wp[t - H].min(1)
        rng_l = rng_long
        squeeze = np.where(rng_l > 0, rng_s / rng_l, np.nan)

        sigma_pct = c["line_sd"]
        drift_str = np.where(c["line_sd"] > 0,
                             np.abs(c["slope"]) * H / c["line_sd"], np.nan)

    tod = (b0 + t).astype(float)                       # absolute 5-minute bar of the session
    elapsed = (t - 2 * H) / max(n_t - 1, 1)
    vf = np.full(n_t, np.nan)
    vc = np.full(n_t, np.nan)
    if vm is not None:
        f = vm["fast"]
        idx = np.minimum(t, len(f) - 1)
        vf = f[idx]
        if vm["slow"] and vm["slow"] > 0:
            vc = vf / vm["slow"]
    return {"trav_past": trav_past, "vol_ratio": vol_ratio, "sigma_pct": sigma_pct,
            "ac1": ac1, "vratio2": vratio2, "squeeze": squeeze, "tod": tod,
            "elapsed": elapsed, "drift_str": drift_str, "vol_fast": vf, "vol_chg": vc}


def collect(roots, src, sp):
    rows = []
    for r in roots:
        if r not in sp:
            continue
        g = src[src["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            fwd, ok = forward_traverse(px, c)
            f = causal_features(px, c, vm, b0)
            n_t = len(fwd)
            # the tradeable subset, for step 2
            base = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
            with np.errstate(invalid="ignore"):
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
            base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
            base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            room = np.zeros(n_t, bool)
            room[:max(0, len(px) - 2 * H - TAU)] = True
            base = base & room
            tr = O.resolve(px, c, "flat", base, tick, tick_usd, cost_tk,
                           TARGET, FRAME, G, TAU, 0, b0, r)
            idx = [i for i in np.flatnonzero(base) if (i + 2 * H) < len(px) - 1][:len(tr)]
            # ARRAYS, NOT DICTS. This is ~6M rows across the wide fixture; one dict per row would
            # need several GB and dominate the runtime. Per-session arrays are concatenated once.
            gross = np.full(n_t, np.nan)
            cost = np.full(n_t, np.nan)
            for z, i in zip(tr, idx):
                gross[i] = z["g_real_tk"] * z["tick_usd"]
                cost[i] = z["cost_usd"]
            sel = np.flatnonzero(ok)
            if len(sel) == 0:
                continue
            block = {"root": np.full(len(sel), r, dtype=object),
                     "day": np.full(len(sel), day, dtype=object),
                     "y": fwd[sel].astype(float),
                     "gross": gross[sel], "cost": cost[sel]}
            for k in FEATS:
                v = f[k]
                block[k] = v[sel] if len(v) == n_t else np.full(len(sel), np.nan)
            rows.append(block)
    if not rows:
        return pd.DataFrame()
    cols = rows[0].keys()
    return pd.DataFrame({c: np.concatenate([b[c] for b in rows]) for c in cols})


def block_se(df, mask, col="y", n_boot=400, rng=None):
    """Block bootstrap over (root, day) of P(y | mask) - P(y)."""
    keys = (df["root"] + "|" + df["day"]).to_numpy()
    uk, inv = np.unique(keys, return_inverse=True)
    yv = df[col].to_numpy(float)
    mv = mask.to_numpy(bool) if hasattr(mask, "to_numpy") else np.asarray(mask, bool)
    out = np.empty(n_boot)
    nb = len(uk)
    for i in range(n_boot):
        pick = rng.integers(0, nb, nb)
        sel = np.isin(inv, pick)
        if sel.sum() < 100:
            out[i] = np.nan
            continue
        out[i] = yv[sel & mv].mean() - yv[sel].mean() if (sel & mv).sum() > 20 else np.nan
    return float(np.nanstd(out, ddof=1))


def self_test():
    rng = np.random.default_rng(555)
    # 1. THE TARGET MUST FIRE ON A TWO-SIDED PATH AND NOT ON A TRENDING ONE.
    #
    #    A PURE SINE CANNOT SATISFY THIS TARGET, and the fact is worth recording rather than
    #    working around: a sinusoid's peak-to-residual-sd ratio is sqrt(2) = 1.414, and TRAV_K is
    #    1.5. So `traverse` never detects smooth oscillation -- it requires SPIKY two-sided
    #    movement, which is a large part of why the classifier kept selecting the spike profile.
    #    The fixture therefore uses a quiet history followed by two-sided spikes.
    n = 2 * H + 40
    peak_over_sd = 1.0 / np.std(np.sin(np.linspace(0, 2 * np.pi, 2000)))
    assert peak_over_sd < TRAV_K, (
        f"a sine's peak/sd is {peak_over_sd:.3f}, which is NOT below TRAV_K={TRAV_K} -- the "
        f"note above is wrong")
    P(f"   [1] a pure sine's peak/sd is {peak_over_sd:.3f} < TRAV_K {TRAV_K}: smooth oscillation")
    P("       can never satisfy this target, so it selects SPIKY two-sided moves by design")
    quiet = 20000 + rng.normal(0, 0.05, 2 * H)
    spiky = 20000 + np.tile([10.0, -10.0], 20)[:40]
    trend = 20000 + np.concatenate([rng.normal(0, 0.05, 2 * H), 0.9 * np.arange(40)])
    # Asserted on the ENGINEERED bar (t = 2H, index 0), not the path average: once t moves into
    # the spiky region its OWN history is spiky, sigma inflates, and later bars stop firing --
    # so a path-wide rate measures the fixture's geometry rather than the target's behaviour.
    for nm, p, want in (("two-sided spikes", np.concatenate([quiet, spiky]), True),
                        ("trending", trend, False)):
        c = Z.classify2(p, 0.25)
        fwd, ok = forward_traverse(p, c)
        assert ok[0], f"{nm}: the engineered bar has no valid forward window"
        got = bool(fwd[0])
        P(f"   [1] {nm:<17} target at the engineered bar: {got}  (want {want})")
        assert got == want, f"{nm}: got {got}, wanted {want}"
    P("       the target discriminates two-sided movement from trend                     OK")

    # 2. EVERY FEATURE MUST BE CAUSAL: changing a bar at or after t must not change the feature
    #    at t. This is the check that matters most -- a leaked feature would forecast perfectly.
    base = 20000 + np.cumsum(rng.normal(0, 3.0, 160))
    c0 = Z.classify2(base, 0.25)
    f0 = causal_features(base, c0, None, 0)
    t_probe = 100
    i_probe = t_probe - 2 * H
    alt = base.copy()
    alt[t_probe:] += 75.0                     # rewrite everything from t onward
    c1 = Z.classify2(alt, 0.25)
    f1 = causal_features(alt, c1, None, 0)
    leaked = []
    for k in FEATS:
        if k in ("tod", "elapsed", "vol_fast", "vol_chg"):
            continue
        a, b = f0[k][i_probe], f1[k][i_probe]
        if not (np.isnan(a) and np.isnan(b)) and not np.isclose(a, b, rtol=0, atol=0):
            leaked.append((k, a, b))
    assert not leaked, f"features changed when the FUTURE changed -- leak: {leaked}"
    P(f"   [2] rewriting every bar from t onward changed none of "
      f"{len([k for k in FEATS if k not in ('tod','elapsed','vol_fast','vol_chg')])} "
      f"features   OK")

    # 3. AND THE TARGET MUST change when the future changes, or [2] proves nothing.
    fwd0, _ = forward_traverse(base, c0)
    fwd1, _ = forward_traverse(alt, c1)
    assert fwd0[i_probe] != fwd1[i_probe] or not np.array_equal(fwd0, fwd1), \
        "the target did not respond to the future -- check [2] is testing anything"
    P("   [3] the TARGET does change when the future changes (so [2] is a real check)    OK")

    # [4] THE FAST PATH MUST BE BIT-IDENTICAL TO THE LOOP IT REPLACED, on tie-heavy and flat
    #     inputs as well as smooth ones, and at the 1-minute session length as well as the
    #     5-minute one. Ties are where a vectorised reduction and a per-slice reduction disagree.
    keys = ("trav_past", "vol_ratio", "sigma_pct", "ac1", "vratio2", "squeeze", "tod",
            "elapsed", "drift_str", "vol_fast", "vol_chg")
    rg = np.random.default_rng(17)
    nbad, ncase = 0, 0
    for n in (60, 84, 121, 420, 421):
        for lab, p in (("smooth", np.cumsum(rg.normal(0, 1.0, n)) + 5000.0),
                       ("tie", 5000.0 + np.cumsum(rg.integers(-1, 2, n)) * 0.25),
                       ("flat", np.full(n, 5000.0))):
            cc = Z.classify2(np.asarray(p, float), 0.25)
            if cc is None:
                continue
            ncase += 1
            a = causal_features(np.asarray(p, float), cc, None, 0)
            b = causal_features_ref(np.asarray(p, float), cc, None, 0)
            for k in keys:
                x, y = np.asarray(a[k], float), np.asarray(b[k], float)
                if x.shape != y.shape or not ((x == y) | (np.isnan(x) & np.isnan(y))).all():
                    nbad += 1
                    P(f"   [4] MISMATCH on {lab} n={n} field {k}")
    assert nbad == 0, f"{nbad} fast/ref mismatches: the fast path must not be used"
    P(f"   [4] causal_features == causal_features_ref on all {ncase} cases (smooth, "
      f"tie-heavy, flat; n=60..421)   OK")

    # [5] AND THE CHECK MUST BE ABLE TO FAIL. Feed the reference a deliberately different
    #     baseline width and assert [4]'s comparison rejects it -- otherwise [4] only proves
    #     that two calls to the same code agree.
    p = np.cumsum(rg.normal(0, 1.0, 200)) + 5000.0
    cc = Z.classify2(p, 0.25)
    r_ = np.diff(p, prepend=p[0])
    tt_ = np.arange(2 * H, len(p))
    sb_a, rg_a = _sb_rng(p, r_, tt_, 6 * H)
    sb_b, rg_b = _sb_rng(p, r_, tt_, 6 * H - 1)          # the wrong window
    diff = not ((sb_a == sb_b) | (np.isnan(sb_a) & np.isnan(sb_b))).all()
    assert diff, "[5] the comparison cannot distinguish two different baseline widths"
    P("   [5] [X] the same comparison REJECTS a one-bar-different baseline window       OK")
    P("\n   all self-tests pass\n")


def run():
    rng = np.random.default_rng(SEED)
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    P("CAN FORWARD MEAN REVERSION BE FORECAST?")
    P(f"  wide 5-minute fixture, {len(roots)} roots, through {W.IS_END}; reserved slice NOT read")
    P(f"  target: traverse of +/-{TRAV_K} sigma over [t, t+{H}), from features strictly before t\n")
    df = collect(roots, f, sp)
    df = df.dropna(subset=["y"])
    base = df["y"].mean()
    P(f"  {len(df):,} scored bars, base rate P(traverse ahead) = {base:.4f}")
    tr = df[df["day"] < SPLIT]
    te = df[df["day"] >= SPLIT]
    P(f"  out-of-time split at {SPLIT}: {len(tr):,} early / {len(te):,} late\n")

    P("=" * 112)
    P("1  IS THE TARGET FORECASTABLE? Univariate quintile lift on P(traverse ahead).")
    P("   Quintile edges from the EARLY half only, applied unchanged to the LATE half.")
    P("")
    P("    feature        n(late)   Q1 lift    Q5 lift   |Q5-Q1|  blockSE   t   | early Q5 lift")
    res = []
    for k in FEATS:
        v_tr = tr[k].to_numpy(float)
        v_te = te[k].to_numpy(float)
        ok_tr = np.isfinite(v_tr)
        if ok_tr.sum() < 500:
            continue
        q = np.nanpercentile(v_tr[ok_tr], [20, 80])
        m1_te = te[k] <= q[0]
        m5_te = te[k] >= q[1]
        if m1_te.sum() < 200 or m5_te.sum() < 200:
            continue
        b_te = te["y"].mean()
        l1 = te.loc[m1_te, "y"].mean() - b_te
        l5 = te.loc[m5_te, "y"].mean() - b_te
        se = block_se(te, m5_te, rng=rng)
        b_tr = tr["y"].mean()
        l5e = tr.loc[tr[k] >= q[1], "y"].mean() - b_tr
        res.append((k, int(m5_te.sum()), l1, l5, abs(l5 - l1), se, l5 / se if se else np.nan, l5e))
    for k, n5, l1, l5, sp_, se, t, l5e in sorted(res, key=lambda z: -abs(z[3])):
        P(f"    {k:<14} {n5:>7,} {l1:>+9.4f} {l5:>+10.4f} {sp_:>9.4f} {se:>8.4f} "
          f"{t:>+5.1f}   | {l5e:>+8.4f}")
    P("")
    P("    'lift' is P(traverse ahead | quintile) minus the base rate on the LATE half.")
    P("    `trav_past` is the known-bad baseline (measured at t = -25 in ADDENDUM 8).")
    P("    A feature whose LATE lift has a different sign from its EARLY lift did not")
    P("    generalise and is noise regardless of its t.")

    P("")
    P("=" * 112)
    P("2  DOES LIFT TRANSLATE TO MONEY? Tradeable subset only, top/bottom quintile by feature.")
    P("")
    tdf = te.dropna(subset=["gross"]).copy()
    if len(tdf) < 200:
        P(f"    only {len(tdf)} tradeable rows in the late half -- too few")
        return
    tdf["net"] = tdf["gross"] - tdf["cost"]
    gp = tdf["gross"].to_numpy(float)
    P(f"    {len(tdf):,} tradeable rows (late half). pool gross ${gp.mean():+.2f}, "
      f"median ${np.median(gp):+.2f}")
    P("")
    P("    feature         cell     n    P(trav)  gross $   net $  | matched p5    p50    p95"
      "  | verdict")
    for k, n5, l1, l5, sp_, se, t, l5e in sorted(res, key=lambda z: -abs(z[3]))[:6]:
        v = tr[k].to_numpy(float)
        v = v[np.isfinite(v)]
        if len(v) < 500:
            continue
        q = np.nanpercentile(v, [20, 80])
        for nm, m in (("Q1 (low)", tdf[k] <= q[0]), ("Q5 (high)", tdf[k] >= q[1])):
            rows = tdf[m]
            if len(rows) < 40:
                continue
            g = rows["gross"].to_numpy(float)
            nt = rows["net"].to_numpy(float)
            dr = gp[rng.integers(0, len(gp), (N_DRAW, len(g)))]
            p5, p50, p95 = np.percentile(dr.mean(1), [5, 50, 95])
            vd = "ABOVE p95" if g.mean() > p95 else ("below p5" if g.mean() < p5 else "inside")
            P(f"    {k:<14} {nm:<10} {len(rows):>5,} {rows['y'].mean():>7.1%} "
              f"{g.mean():>+8.2f} {nt.mean():>+7.2f} | {p5:>+8.2f} {p50:>+6.2f} {p95:>+6.2f}"
              f"  | {vd}")
    P("")
    P("  If no feature moves P(traverse ahead) by more than a point or two, the target is not")
    P("  forecastable from anything here and no model over these features can help.")


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
