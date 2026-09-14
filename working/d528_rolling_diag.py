"""Diagnostics on the rolling drift-aligned detector: which layer is responsible?

    python working/d528_rolling_diag.py

The main table shows gross P&L ~0 at s=1 and monotonically worse with scale, and P(target)
BELOW its own breakeven everywhere. That is consistent with two very different stories, and the
fix is opposite in each:

    a SIGNAL failure     the cell carries no reversion, and no exit geometry rescues it
    a GEOMETRY failure   the cell reverts, but the 2:1 target/stop asks for a hit rate the
                         reversion cannot deliver

Three contrasts separate them, all at fixed prices, all causal, all in sample:

  A  THE FOUR CELLS -- classifier on/off crossed with aligned / anti-aligned. If the principal's
     alignment rule is doing work, aligned must beat anti-aligned. If the classifier is doing
     work, on must beat off. Anti-aligned is reported ONLY as the control for the alignment
     rule; it is the cell the principal ruled out and is not a candidate.

  B  THE STOP LADDER. The stop fraction was not specified by the principal; 0.5 came from D471's
     "a stop must be ~half the target". It sets the breakeven hit rate in closed form,
     p_be = (f*|y| + c) / ((1+f)*|y|), so a tighter stop asks less of the signal while taking
     more stop-outs. If ANY f puts P(target) above p_be, the failure was geometry.

  C  THE ENTRY DEPTH LADDER. x sets how far the excursion must run before entry, and it is the
     one parameter the feasibility filter interacts with -- at x=2 with a 4-tick lattice floor,
     |y| >= 8 ticks always clears the 1.06-4.99 tick cost, so the filter never bound. Lower x
     is where it starts to bind, and the table reports how many trades it blocks.

Nothing admitted (R15).
"""
from __future__ import annotations

import sys

import numpy as np

sys.path.insert(0, "scripts")
sys.path.insert(0, "working")
import d528_mean_reversion_oracle as Q          # noqa: E402
import d528_rolling_aligned_detector as R       # noqa: E402

S_DIAG = 1
STOP_LADDER = (0.25, 0.5, 0.75, 1.0, 1.5)
X_LADDER = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0)


def P(*a):
    print(*a, flush=True)


def resolve_f(path, c, idx, s, tick, stop_frac):
    """R.resolve with the stop fraction as a parameter."""
    n = len(path)
    out_kind, out_pnl, out_tgt = [], [], []
    last_exit = -1
    for q in range(len(idx)):
        i = int(idx[q]); t = i + 2 * R.H
        if t <= last_exit or t >= n - 1:
            continue
        ss = float(s[q]); p0 = float(path[t]); y0 = float(c["y"][i])
        tgt = float(c["lvl"][i]); stp = p0 + ss * stop_frac * abs(y0)
        fwd = path[t + 1:min(t + R.TAU, n - 1) + 1]
        if len(fwd) == 0:
            continue
        ht = (fwd - tgt) * ss <= 0.0
        hs = (fwd - stp) * ss >= 0.0
        i_t = int(np.argmax(ht)) if ht.any() else 1 << 30
        i_s = int(np.argmax(hs)) if hs.any() else 1 << 30
        if i_s == R.BIG and i_t == R.BIG:
            k, kind, px = len(fwd), 2, float(fwd[-1])
        elif i_s <= i_t:
            k, kind, px = i_s + 1, 1, stp
        else:
            k, kind, px = i_t + 1, 0, tgt
        out_kind.append(kind); out_pnl.append((-ss) * (px - p0) / tick)
        out_tgt.append(abs(y0) / tick)
        last_exit = t + k
    return (np.array(out_kind, dtype=np.int64), np.array(out_pnl), np.array(out_tgt))


def mask(c, tick, cost, x, align, classifier):
    keep = c["ok_sd"]
    if classifier:
        keep = keep & c["mr_slope"] & c["mr_cross"] & c["a2"]
    with np.errstate(invalid="ignore"):
        keep = keep & (np.abs(c["y"]) >= x * c["sd"])
    s = np.sign(c["y"])
    if align is not None:
        keep = keep & ((s * c["slope"] < 0) if align else (s * c["slope"] > 0))
    n_pre = int(keep.sum())
    keep = keep & (np.abs(c["y"]) / tick > cost)
    return np.flatnonzero(keep), s[np.flatnonzero(keep)], n_pre, int(keep.sum())


def sweep(s_scale, x, align, classifier, stop_frac, roots, d, sp):
    KIND, PNL, TGT, CV = [], [], [], []
    blocked = 0
    for r in roots:
        g = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        cost = R.COST.get(r, R.COST_DEFAULT)
        for day, pth in Q.session_bars(g, s_scale):
            c = R.classify(pth, tick)
            if c is None:
                continue
            ix, sx, n_pre, n_post = mask(c, tick, cost, x, align, classifier)
            blocked += n_pre - n_post
            if len(ix) == 0:
                continue
            kd, pl, tg = resolve_f(pth, c, ix, sx, tick, stop_frac)
            if len(kd):
                KIND.append(kd); PNL.append(pl); TGT.append(tg)
                CV.append(np.full(len(kd), cost))
    if not KIND:
        return None
    kd = np.concatenate(KIND); pl = np.concatenate(PNL)
    tg = np.concatenate(TGT); cv = np.concatenate(CV)
    net = pl - cv
    p_be = float(np.mean((stop_frac * tg + cv) / ((1.0 + stop_frac) * tg)))
    return {"n": len(kd), "p": float((kd == 0).mean()), "p_be": p_be, "gross": pl.mean(),
            "net": net.mean(), "med": float(np.median(net)), "win": float((net > 0).mean()),
            "blocked": blocked, "tg": tg, "net_arr": net}


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
P(f"DIAGNOSTICS at s={S_DIAG} (the best scale in the main table), {len(roots)} roots, "
  f"{d['day'].min()} .. {d['day'].max()}")
P("fixed-price target and stop throughout; all causal; in sample only\n")

P("A  THE FOUR CELLS -- is the alignment rule or the classifier doing the work?")
P("   classifier  side          trades  P(target)   p_be   MARGIN    GROSS tk    NET tk   median")
base = {}
for cl in (True, False):
    for al, nm in ((True, "aligned"), (False, "anti-aligned")):
        o = sweep(S_DIAG, R.X, al, cl, R.STOP_FRAC, roots, d, sp)
        if o is None:
            continue
        base[(cl, al)] = o
        P(f"   {'on ' if cl else 'off':<11} {nm:<13} {o['n']:>6,}    {o['p']:.4f}  "
          f"{o['p_be']:.4f}  {o['p']-o['p_be']:+.4f}  {o['gross']:+9.2f} {o['net']:+9.2f} "
          f"{o['med']:+8.2f}")
P("   MARGIN is P(target) minus the hit rate this trade's own geometry needs. Positive = pays.")
P("   anti-aligned is the CONTROL for the principal's rule, not a candidate.")

P("\nB  THE STOP LADDER -- can any exit geometry rescue the aligned cell? (classifier on)")
P("   stop/target   trades  P(target)   p_be   MARGIN    GROSS tk    NET tk   median   win%")
for f in STOP_LADDER:
    o = sweep(S_DIAG, R.X, True, True, f, roots, d, sp)
    if o is None:
        continue
    P(f"   {f:>11.2f}   {o['n']:>6,}    {o['p']:.4f}  {o['p_be']:.4f}  {o['p']-o['p_be']:+.4f}  "
      f"{o['gross']:+9.2f} {o['net']:+9.2f} {o['med']:+8.2f} {o['win']:6.1%}")

P("\nC  THE ENTRY DEPTH LADDER -- and where the feasibility filter starts to bind")
P("   x (sigma)   trades   blocked by feas   median |y| tk   P(target)   p_be   MARGIN   NET tk")
for x in X_LADDER:
    o = sweep(S_DIAG, x, True, True, R.STOP_FRAC, roots, d, sp)
    if o is None:
        continue
    P(f"   {x:>9.1f}  {o['n']:>7,} {o['blocked']:>17,}   {np.median(o['tg']):>13.1f}   "
      f"{o['p']:.4f}  {o['p_be']:.4f} {o['p']-o['p_be']:+.4f} {o['net']:+9.2f}")
P("   'blocked by feas' counts extremes rejected ONLY by |y| <= cost -- the principal's test.")

P("\nD  TRADE DISTRIBUTION of the primary cell (aligned, classifier on, stop 0.5, x 2.0)")
o = base[(True, True)]
na = o["net_arr"]
lo, hi = np.quantile(na, [0.01, 0.99])
tr = na[(na >= lo) & (na <= hi)]
P(f"   n {len(na):,}   mean {na.mean():+.2f}   median {np.median(na):+.2f}   "
  f"win {o['win']:.1%}   skew {float(((na-na.mean())**3).mean()/na.std()**3):+.2f}   "
  f"kurt {float(((na-na.mean())**4).mean()/na.std()**4):.2f}")
P(f"   trimmed 1% BOTH tails  mean {tr.mean():+.2f}   ex-top {na[na <= hi].mean():+.2f}   "
  f"ex-bottom {na[na >= lo].mean():+.2f}")
P(f"   top 1% share of gross positive P&L "
  f"{na[na >= np.quantile(na, 0.99)].sum() / na[na > 0].sum():.1%}")
