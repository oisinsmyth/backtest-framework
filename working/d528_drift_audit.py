"""DOES THE FORECAST SURVIVE THE DRIFT FILTER? The audit the principal asked for.

    python working/d528_drift_audit.py --run

Nothing admitted (R15). Wide 5-minute fixture through 2026-04-10; reserved slice NOT read.

THE QUESTION, and it is load-bearing for everything downstream. The forecastability result --
`vol_ratio` moving P(traverse ahead) from a 14.95% base to 22.1%, t = -155 -- was measured on ALL
4,884,589 SCORED BARS: no drift filter, no excursion filter, nothing. The P&L was measured only on
the 2,834 bars that survive the full entry chain:

    slope_ok            the slope-STABILITY test, |b1-b2|*H <= 0.5*sigma_pooled
    |y| >= 2 sigma      the excursion
    sign(y)*slope < 0   THE DRIFT ALIGNMENT -- the principal's rule
    |y|/tick > cost     feasibility

So the forecast was validated on one population and applied to a different, far smaller one. And
the two already differ on the TARGET: P(traverse) is 14.95% over all bars and 11.1% over the
tradeable subset, so the entry chain removes about a quarter of the traversal probability in
relative terms BEFORE the forecast is applied.

WHAT THIS FILE MEASURES, stage by stage:

  1  THE FUNNEL. How many bars each filter removes, and what P(traverse ahead) is at each stage.
     A filter that lowers P(traverse) is removing the very regime the forecast exists to find.
  2  THE FORECAST'S LIFT WITHIN EACH STAGE. If vol_ratio separates traversal strongly over all
     bars but weakly among drift-ALIGNED bars, the t = -155 does not transfer and every number
     built on it is unsupported.
  3  ALIGNED vs ANTI-ALIGNED, side by side, so "is the drift filter throwing away too much" is
     answered with the forecast's own lift in each half rather than by argument.

The two drift-related filters are reported SEPARATELY, because they do different jobs and only one
of them is the principal's rule:
     slope_ok           rejects regime change  (my addition, never justified against the forecast)
     sign(y)*slope < 0  trades with the drift   (the principal's rule)
"""
from __future__ import annotations

import argparse
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402
import d528_why_zero as Z                       # noqa: E402
import d528_wide as W                           # noqa: E402
import d528_forecast_reversion as FR            # noqa: E402

H = Z.H
X = 2.0
FEATS4 = ("vol_ratio", "squeeze", "vratio2", "ac1")
SEED = 528661


def P(*a):
    print(*a, flush=True)


def collect(roots, src, sp):
    """Every scored bar with the target, the four forecast features, and each filter's flag."""
    out = []
    for r in roots:
        if r not in sp:
            continue
        g = src[src["root"] == r]
        if r in W.GATE_2016:
            g = g[g["day"] >= "2016-01-04"]
        if len(g) == 0:
            continue
        tick = sp[r]["tick_price_units"]
        cost_tk = R.COST.get(r, R.COST_DEFAULT)
        sess = W.sessions_of(g, "close")
        vols = W.tod_and_vol(sess)
        for (day, px, vol, b0), vm in zip(sess, vols):
            c = Z.classify2(px, tick)
            if c is None:
                continue
            fwd, ok = FR.forward_traverse(px, c)
            ft = FR.causal_features(px, c, vm, b0)
            n_t = len(fwd)
            with np.errstate(invalid="ignore"):
                f_sd = np.nan_to_num(c["flat_sd"] > 0, nan=False).astype(bool)
                f_slope = np.nan_to_num(c["slope_ok"], nan=False).astype(bool)
                f_a2 = np.asarray(c["a2ok"])
                f_exc = np.nan_to_num(np.abs(c["flat_y"]) >= X * c["flat_sd"],
                                      nan=False).astype(bool)
                f_align = np.nan_to_num(np.sign(c["flat_y"]) * c["slope"] < 0,
                                        nan=False).astype(bool)
                f_feas = np.nan_to_num(np.abs(c["flat_y"]) / tick > cost_tk,
                                       nan=False).astype(bool)
            sel = np.flatnonzero(ok)
            if len(sel) == 0:
                continue
            blk = {"root": np.full(len(sel), r, dtype=object),
                   "day": np.full(len(sel), day, dtype=object),
                   "y": fwd[sel].astype(float),
                   "f_sd": f_sd[sel], "f_slope": f_slope[sel], "f_a2": f_a2[sel],
                   "f_exc": f_exc[sel], "f_align": f_align[sel], "f_feas": f_feas[sel]}
            for k in FEATS4:
                v = ft[k]
                blk[k] = v[sel] if len(v) == n_t else np.full(len(sel), np.nan)
            out.append(blk)
    cols = out[0].keys()
    return pd.DataFrame({c: np.concatenate([b[c] for b in out]) for c in cols})


def lift(df, feat, rng, n_boot=200):
    """Q1-minus-base lift of `feat` on the target, with a block bootstrap over (root, day)."""
    v = df[feat].to_numpy(float)
    ok = np.isfinite(v)
    if ok.sum() < 400:
        return (np.nan, np.nan, 0)
    q = np.nanpercentile(v[ok], 20)
    m = ok & (v <= q)
    if m.sum() < 200:
        return (np.nan, np.nan, 0)
    yv = df["y"].to_numpy(float)
    base = yv.mean()
    val = yv[m].mean() - base
    keys = (df["root"].astype(str) + "|" + df["day"].astype(str)).to_numpy()
    uk, inv = np.unique(keys, return_inverse=True)
    nb = len(uk)
    bs = np.empty(n_boot)
    for i in range(n_boot):
        pick = np.isin(inv, rng.integers(0, nb, nb))
        if pick.sum() < 200 or (pick & m).sum() < 50:
            bs[i] = np.nan
            continue
        bs[i] = yv[pick & m].mean() - yv[pick].mean()
    return (val, float(np.nanstd(bs, ddof=1)), int(m.sum()))


def run():
    rng = np.random.default_rng(SEED)
    sp = Q.specs()
    f = W.load("close")
    roots = sorted(set(f["root"]) & set(sp))
    P("DOES THE FORECAST SURVIVE THE DRIFT FILTER?")
    P(f"  wide 5-minute fixture, {len(roots)} roots, through {W.IS_END}\n")
    d = collect(roots, f, sp)
    P(f"  {len(d):,} scored bars, base P(traverse ahead) = {d['y'].mean():.4f}\n")

    P("=" * 104)
    P("1  THE FUNNEL -- what each filter removes, and what it does to P(traverse ahead)")
    P("")
    P("    stage                              bars      kept    P(traverse)   vs all bars")
    base_all = d["y"].mean()
    stages = [("all scored bars", np.ones(len(d), bool))]
    m = d["f_sd"].to_numpy(bool)
    stages.append(("+ sigma > 0", m.copy()))
    m = m & d["f_slope"].to_numpy(bool)
    stages.append(("+ slope_ok (stability)", m.copy()))
    m = m & d["f_a2"].to_numpy(bool)
    stages.append(("+ a2 (4-tick lattice)", m.copy()))
    m = m & d["f_exc"].to_numpy(bool)
    stages.append(("+ |y| >= 2 sigma (excursion)", m.copy()))
    m_pre_align = m.copy()
    m = m & d["f_align"].to_numpy(bool)
    stages.append(("+ DRIFT ALIGNMENT", m.copy()))
    m = m & d["f_feas"].to_numpy(bool)
    stages.append(("+ feasibility", m.copy()))
    for nm, mm in stages:
        p = d.loc[mm, "y"].mean() if mm.sum() else np.nan
        P(f"    {nm:<32} {int(mm.sum()):>9,} {mm.mean():>8.2%} {p:>13.4f} "
          f"{p - base_all:>+13.4f}")
    P("")
    P("    A stage that LOWERS P(traverse) is removing the regime the forecast exists to find.")

    P("")
    P("=" * 104)
    P("2  DOES THE FORECAST'S LIFT SURVIVE EACH STAGE? Q1 lift on P(traverse ahead).")
    P("")
    P("    population                    n(Q1)   vol_ratio    squeeze    vratio2       ac1")
    pops = [("all scored bars", np.ones(len(d), bool)),
            ("slope_ok only", d["f_slope"].to_numpy(bool)),
            ("excursion only", m_pre_align),
            ("+ ALIGNED (tradeable)", stages[-1][1]),
            ("ANTI-aligned excursions",
             m_pre_align & ~d["f_align"].to_numpy(bool) & d["f_feas"].to_numpy(bool))]
    for nm, mm in pops:
        if mm.sum() < 1000:
            P(f"    {nm:<28} {int(mm.sum()):>7,}  too few")
            continue
        sub = d[mm]
        cells = []
        n1 = 0
        for k in FEATS4:
            v, se, n = lift(sub, k, rng)
            n1 = max(n1, n)
            cells.append(f"{v:+.4f}" + ("*" if (np.isfinite(se) and se > 0
                                                and abs(v) > 2 * se) else " "))
        P(f"    {nm:<28} {n1:>7,}  " + "  ".join(f"{c:>9}" for c in cells))
    P("    * = |lift| exceeds 2 block-bootstrap SE.")
    P("")
    P("    If the lift collapses at '+ ALIGNED', the t = -155 measured on all bars does NOT")
    P("    transfer to the tradeable population, and every P&L number built on it is")
    P("    unsupported. If it survives, the forecast is intact and the drift filter is")
    P("    costing candidates rather than costing signal.")

    P("")
    P("=" * 104)
    P("3  IS THE DRIFT FILTER THROWING AWAY TOO MUCH?")
    P("")
    exc = m_pre_align & d["f_feas"].to_numpy(bool)
    al = exc & d["f_align"].to_numpy(bool)
    an = exc & ~d["f_align"].to_numpy(bool)
    P(f"    feasible excursions          {int(exc.sum()):>9,}")
    P(f"      drift-ALIGNED              {int(al.sum()):>9,} ({al.sum()/max(exc.sum(),1):.1%})"
      f"   P(traverse) {d.loc[al,'y'].mean():.4f}")
    P(f"      ANTI-aligned               {int(an.sum()):>9,} ({an.sum()/max(exc.sum(),1):.1%})"
      f"   P(traverse) {d.loc[an,'y'].mean():.4f}")
    P("")
    P(f"    slope_ok alone removes       {1 - d['f_slope'].mean():.1%} of all bars")
    P(f"      P(traverse | slope_ok)     {d.loc[d['f_slope'].to_numpy(bool),'y'].mean():.4f}")
    P(f"      P(traverse | NOT slope_ok) "
      f"{d.loc[~d['f_slope'].to_numpy(bool),'y'].mean():.4f}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.run:
        run()
    else:
        ap.error("choose --run")
