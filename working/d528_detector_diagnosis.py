"""IS THE DETECTOR FINDING RANGES, OR FINDING VOLATILITY EXPANSION?

    python working/d528_detector_diagnosis.py --self-test
    python working/d528_detector_diagnosis.py --run

Nothing admitted (R15). Micro universe, in sample only; reserved slice UNREAD. No holdout is
spent by anything in this file -- it is a diagnosis of the instrument.

THE PRINCIPAL'S OBSERVATION, from the ten decile charts: "on every trade bar the top one, the
price has consolidated, triggered the detector, and then had a move that seems a bit sudden."

THE HYPOTHESIS THAT WOULD EXPLAIN IT. Sigma is estimated ON THE TRAILING WINDOW, which is the
consolidation itself. So:

    price goes quiet  ->  sigma collapses  ->  the |y| >= 2*sigma bar becomes trivially low in
    ABSOLUTE terms  ->  the first real move clears it  ->  we sell the breakout

If that is what is happening, the detector is a VOLATILITY-EXPANSION detector wearing a
mean-reversion costume, and it is systematically positioned against the expansion. It would
predict precisely what has been measured all session: 83.5% stop-outs, a median hold of 2 bars,
and stops hit almost immediately.

It would also explain ADDENDUM 8's inverted premise (lift -0.0345, t -25.08): "quiet window then
active window" traverses its band easily, and that is an expansion signature, not a ranging one.

FOUR CAUSAL FEATURES, ALL AVAILABLE AT THE ENTRY BAR, measure it:

    vol_ratio     sd of bar returns over [t-H, t)  /  sd over [t-6H, t)
                  below 1 means the window is QUIETER than its own recent baseline
    jump          |r_t| / median |r| over [t-H, t)      how outsized the triggering bar is
    frac_last     |P[t] - P[t-1]| / |y|                 how much of the excursion ONE bar built
    sig_ratio     sd(first half) / sd(second half) of the trailing window -- the sigma-agreement
                  test from the ORIGINAL D528 A1, which this classifier dropped and which is the
                  one filter that directly rejects "quiet then active"

Section 1 asks whether admitted trades differ from the pool on these. Section 2 asks whether
OUTCOMES vary with them. Section 3 tests four repairs against the RANDOM-MATCHED control (real
data, randomised selection, count matched) established in ADDENDUM 9 as the correct one.
"""
from __future__ import annotations

import argparse
import sys

import numpy as np

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_book_and_sides as B                 # noqa: E402
import d528_opposite_extreme_and_drift_stops as O   # noqa: E402

H = Z.H
X, G, TAU = 2.0, 3.0, 40
TARGET, FRAME = "reflect", "drift"
BASE_W = 6 * H                # the longer volatility baseline, 60 bars
N_DRAW = 400
SEED = 528613


def P(*a):
    print(*a, flush=True)


def features(path, tick, c):
    """The four suddenness/quietness features, per bar t in [2H, n). All causal."""
    n = len(path)
    n_t = n - 2 * H
    r = np.diff(path, prepend=path[0])
    out = {k: np.full(n_t, np.nan) for k in
           ("vol_ratio", "jump", "frac_last", "sig_ratio")}
    for i in range(n_t):
        t = i + 2 * H
        w = r[t - H + 1:t + 1]                       # the H returns ending at t (incl. trigger)
        if len(w) < 4:
            continue
        # vol_ratio must describe the CONSOLIDATION, so it excludes the triggering bar from both
        # the window and the baseline. Including r[t] inflated the window's own sd and made a
        # quiet-then-jump path read vol_ratio 1.26 -- the feature measured the jump, not the calm.
        wq = r[t - H + 1:t]                          # the H-1 returns BEFORE the trigger
        wbq = r[max(t - BASE_W + 1, 1):t]
        sw = wq.std(ddof=1) if len(wq) > 2 else np.nan
        sb = wbq.std(ddof=1) if len(wbq) > 2 else np.nan
        out["vol_ratio"][i] = sw / sb if (sb and sb > 0 and np.isfinite(sw)) else np.nan
        med = np.median(np.abs(w[:-1])) if len(w) > 1 else np.nan
        out["jump"][i] = abs(r[t]) / med if (med and med > 0) else np.nan
        y = c["flat_y"][i]
        out["frac_last"][i] = abs(r[t]) / abs(y) if abs(y) > 0 else np.nan
        h = H // 2
        s1 = w[:h].std(ddof=1) if h > 2 else np.nan
        s2 = w[h:].std(ddof=1) if (len(w) - h) > 2 else np.nan
        out["sig_ratio"][i] = (s1 / s2) if (s2 and s2 > 0) else np.nan
    return out


def collect(d, sp, roots, day_index):
    """The candidate pool with features attached, plus the causal classifier's own selection."""
    pool = []
    for r in roots:
        gg = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        tick_usd = sp[r]["tick_usd"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        for day, pth, b0 in B.sessions_with_bars(gg, 1):
            c = Z.classify2(pth, tick)
            if c is None:
                continue
            f = features(pth, tick, c)
            base = (c["flat_sd"] > 0) & c["slope_ok"] & c["a2ok"]
            with np.errstate(invalid="ignore"):
                base = base & (np.abs(c["flat_y"]) >= X * c["flat_sd"])
            base = base & (np.sign(c["flat_y"]) * c["slope"] < 0)
            base = base & (np.abs(c["flat_y"]) / tick > cost_tk)
            base = np.nan_to_num(base, nan=False).astype(bool)
            if not base.any():
                continue
            tr = O.resolve(pth, c, "flat", base, tick, tick_usd, cost_tk,
                           TARGET, FRAME, G, TAU, day_index[day], b0, r)
            idx = [i for i in np.flatnonzero(base) if (i + 2 * H) < len(pth) - 1][:len(tr)]
            for z, i in zip(tr, idx):
                for k in f:
                    z[k] = float(f[k][i])
                z["trav"] = bool(c["trav"][i])
                z["net"] = z["g_real_tk"] * z["tick_usd"] - z["cost_usd"]
                z["gross"] = z["g_real_tk"] * z["tick_usd"]
                pool.append(z)
    return pool


def summ(rows):
    if not rows:
        return None
    g = np.array([z["gross"] for z in rows])
    nt = np.array([z["net"] for z in rows])
    kd = np.array([z["kind"] for z in rows])
    bars = np.array([z["bars"] for z in rows])
    return {"n": len(rows), "p_tgt": float((kd == 0).mean()), "win": float((nt > 0).mean()),
            "gross": float(g.mean()), "net": float(nt.mean()), "bars": float(bars.mean())}


def matched(pool, k, rng, n_draw=N_DRAW):
    g = np.array([z["gross"] for z in pool])
    if k >= len(g) or k < 5:
        return (np.nan, np.nan, np.nan)
    dr = np.array([g[rng.choice(len(g), k, replace=False)].mean() for _ in range(n_draw)])
    return tuple(np.percentile(dr, [5, 50, 95]))


def self_test():
    rng = np.random.default_rng(91)
    # 1. THE FEATURES MUST MOVE THE RIGHT WAY ON ENGINEERED PATHS. A quiet stretch followed by a
    #    jump must give vol_ratio < 1, a large `jump`, and frac_last near 1. If they do not, the
    #    diagnosis reads noise.
    n = 2 * H + BASE_W + 5
    pth = 20000 + np.cumsum(np.concatenate([
        rng.normal(0, 3.0, BASE_W),          # noisy baseline
        rng.normal(0, 0.05, H - 1),          # quiet window
        [12.0]]))                            # then one big bar
    pth = np.concatenate([pth, pth[-1] + np.zeros(2 * H)])
    c = Z.classify2(pth, 0.25)
    f = features(pth, 0.25, c)
    # the cumsum runs over BASE_W + (H-1) + 1 elements, so the jump is the LAST of them:
    # bar index BASE_W + H - 1, and the feature arrays are indexed by t - 2H.
    jump_bar = BASE_W + H - 1
    i = jump_bar - 2 * H
    P(f"   [1] engineered quiet-then-jump bar: vol_ratio {f['vol_ratio'][i]:.3f}  "
      f"jump {f['jump'][i]:.1f}x  frac_last {f['frac_last'][i]:.2f}")
    assert f["vol_ratio"][i] < 1.0, f"vol_ratio {f['vol_ratio'][i]:.3f} should be < 1 after a quiet stretch"
    assert f["jump"][i] > 3.0, f"jump {f['jump'][i]:.1f} should be large on a one-bar move"
    P("       quiet stretch -> vol_ratio below 1, and the jump bar is an outlier          OK")

    # 2. AND THE OPPOSITE PATH MUST INVERT THEM, or the features cannot discriminate.
    pth2 = 20000 + np.cumsum(np.concatenate([
        rng.normal(0, 0.05, BASE_W),          # quiet baseline
        rng.normal(0, 3.0, H)]))              # then a NOISY window, no single jump
    pth2 = np.concatenate([pth2, pth2[-1] + np.zeros(2 * H)])
    c2 = Z.classify2(pth2, 0.25)
    f2 = features(pth2, 0.25, c2)
    # the noisy window occupies bars BASE_W .. BASE_W+H-1, so its last bar is the
    # one whose trailing window is entirely noisy.
    j = (BASE_W + H - 1) - 2 * H
    assert f2["vol_ratio"][j] > 1.0, \
        f"vol_ratio {f2['vol_ratio'][j]:.3f} should exceed 1 when the window is noisier than base"
    P(f"   [2] engineered noisy-window bar: vol_ratio {f2['vol_ratio'][j]:.3f} > 1          OK")

    # 3. THE MATCHED CONTROL MUST BE UNBIASED against the pool it draws from.
    fake = [{"gross": v} for v in rng.normal(-1.2, 25.0, 3000)]
    p5, p50, p95 = matched(fake, 120, rng, n_draw=1500)
    pm = np.mean([z["gross"] for z in fake])
    assert abs(p50 - pm) < 0.15 * 25.0 / np.sqrt(120), f"matched median {p50:.3f} vs pool {pm:.3f}"
    assert p5 < p50 < p95
    P(f"   [3] matched control unbiased: p50 {p50:+.3f} vs pool mean {pm:+.3f}             OK")
    P("\n   all self-tests pass\n")


def run():
    d = Q.load()
    sp = Q.specs()
    roots = [r for r in sorted(set(d["root"]) & set(sp)) if sp[r].get("has_micro")]
    udays = sorted(set(d["day"]))
    day_index = {u: i for i, u in enumerate(udays)}
    rng = np.random.default_rng(SEED)

    pool = collect(d, sp, roots, day_index)
    trav = [z for z in pool if z["trav"]]
    P("IS THE DETECTOR FINDING RANGES, OR FINDING VOLATILITY EXPANSION?")
    P(f"  micro universe, {len(roots)} roots, {len(udays)} sessions, s=1")
    P(f"  pool {len(pool):,} candidates; the causal `traverse` classifier selects "
      f"{len(trav):,}\n")

    # ------------------------------------------------------------------ 1 the diagnosis
    P("=" * 110)
    P("1  WHAT THE DETECTOR IS ACTUALLY SELECTING  (median of each feature)")
    P("")
    P("    feature       meaning                                    pool    traverse-selected")
    for k, why in (("vol_ratio", "window sd / 60-bar baseline sd; <1 = quiet"),
                   ("jump", "entry bar |r| / window median |r|"),
                   ("frac_last", "share of |y| built by the LAST bar"),
                   ("sig_ratio", "sd(first half) / sd(second half)")):
        a = np.array([z[k] for z in pool], dtype=float)
        b = np.array([z[k] for z in trav], dtype=float)
        P(f"    {k:<13} {why:<42} {np.nanmedian(a):>6.3f} {np.nanmedian(b):>18.3f}")
    P("")
    fl = np.array([z["frac_last"] for z in pool], dtype=float)
    P(f"    share of pool entries where ONE bar built >50% of the excursion: "
      f"{np.nanmean(fl > 0.5):.1%}")
    P(f"    ... and >80%: {np.nanmean(fl > 0.8):.1%}")
    jj = np.array([z["jump"] for z in pool], dtype=float)
    P(f"    share where the entry bar is >3x the window's median bar: {np.nanmean(jj > 3):.1%}")
    vr = np.array([z["vol_ratio"] for z in pool], dtype=float)
    P(f"    share where the window is QUIETER than its 60-bar baseline: {np.nanmean(vr < 1):.1%}")

    # ------------------------------------------------------------------ 2 outcomes by feature
    P("")
    P("=" * 110)
    P("2  DO OUTCOMES VARY WITH THEM? Pool split into quartiles of each feature.")
    P("")
    for k in ("vol_ratio", "jump", "frac_last", "sig_ratio"):
        v = np.array([z[k] for z in pool], dtype=float)
        ok = np.isfinite(v)
        qs = np.nanpercentile(v[ok], [25, 50, 75])
        P(f"    {k}   quartile cuts at {qs[0]:.3f} / {qs[1]:.3f} / {qs[2]:.3f}")
        P("      quartile      n    P(tgt)   win%    gross $    net $   mean bars")
        edges = [-np.inf, qs[0], qs[1], qs[2], np.inf]
        for qi in range(4):
            rows = [z for z, vv in zip(pool, v)
                    if np.isfinite(vv) and edges[qi] <= vv < edges[qi + 1]]
            s = summ(rows)
            if s is None or s["n"] < 20:
                continue
            P(f"      Q{qi+1}       {s['n']:>6,} {s['p_tgt']:>7.1%} {s['win']:>6.1%} "
              f"{s['gross']:>+9.2f} {s['net']:>+8.2f} {s['bars']:>10.1f}")
        P("")

    # ------------------------------------------------------------------ 3 repairs
    P("=" * 110)
    P("3  FOUR REPAIRS, each against the RANDOM-MATCHED control (real data, randomised selection)")
    P("")

    def f_sigagree(z):     # the dropped A1-sigma test
        return np.isfinite(z["sig_ratio"]) and 0.5 <= z["sig_ratio"] <= 2.0

    def f_notquiet(z):     # reject windows quieter than their own baseline
        return np.isfinite(z["vol_ratio"]) and z["vol_ratio"] >= 1.0

    def f_nojump(z):       # reject an outsized triggering bar
        return np.isfinite(z["jump"]) and z["jump"] <= 3.0

    def f_gradual(z):      # reject an excursion built mostly by one bar
        return np.isfinite(z["frac_last"]) and z["frac_last"] <= 0.5

    REPAIRS = {
        "baseline (no repair)": lambda z: True,
        "traverse only": lambda z: z["trav"],
        "R1 sigma-agreement": f_sigagree,
        "R2 not-quiet": f_notquiet,
        "R3 no-jump": f_nojump,
        "R4 gradual excursion": f_gradual,
        "R2+R3": lambda z: f_notquiet(z) and f_nojump(z),
        "R3+R4": lambda z: f_nojump(z) and f_gradual(z),
        "R1+R2+R3+R4": lambda z: (f_sigagree(z) and f_notquiet(z)
                                  and f_nojump(z) and f_gradual(z)),
        "traverse + R3+R4": lambda z: z["trav"] and f_nojump(z) and f_gradual(z),
    }
    P("    repair                  n    P(tgt)   win%    gross $    net $  | matched p5    p50"
      "    p95  | verdict")
    for nm, fn in REPAIRS.items():
        rows = [z for z in pool if fn(z)]
        s = summ(rows)
        if s is None or s["n"] < 20:
            P(f"    {nm:<22} {0 if s is None else s['n']:>5}  too few")
            continue
        p5, p50, p95 = matched(pool, s["n"], rng)
        vd = "ABOVE p95" if s["gross"] > p95 else ("below p5" if s["gross"] < p5 else "inside")
        P(f"    {nm:<22} {s['n']:>5,} {s['p_tgt']:>7.1%} {s['win']:>6.1%} "
          f"{s['gross']:>+9.2f} {s['net']:>+8.2f} | {p5:>+8.2f} {p50:>+6.2f} {p95:>+6.2f}"
          f"  | {vd}")
    P("")
    P("  The control is the ADDENDUM 9 one: real data, random count-matched selection from the")
    P("  same pool. Exploratory -- ten filters were tried, so a single p95 crossing here is one")
    P("  look among ten and settles nothing on its own.")


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
