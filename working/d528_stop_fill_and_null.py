"""THE STOP LADDER, WITH A REALISED STOP FILL AND ITS OWN SIGN-SHUFFLE NULL.

    python working/d528_stop_fill_and_null.py

Diagnostic B reported that the TIGHTEST stop (0.25 x target) is the only geometry that clears:
gross +3.66, net +1.13 ticks, P(target) 0.2910 against a breakeven of 0.2728. Two reasons not to
believe that number as it stands, and both are checked here rather than argued.

1  THE STOP FILL WAS IDEALISED, AND IN THE DIRECTION THAT MANUFACTURES THIS EXACT PATTERN.
   A resting LIMIT order does fill at its own price, so taking the target at `tgt` is right. A
   STOP order becomes a market order: it fills AT OR BEYOND the stop, never better. Filling at
   exactly `stp` therefore hands back whatever the price gapped past it, and the tighter the stop
   the more often that happens -- which would produce a monotone decay of "excess" with stop
   width out of nothing at all. Since only 1-minute mid samples are observed, the truth is
   bracketed rather than known, so both ends are computed:

       IDEAL  fill at stp          the optimistic bound (what diagnostic B used)
       REAL   fill at the observed mid on the bar the stop was breached (pessimistic bound)

   The truth lies between. REAL leads, because an optimistic fill is what overstated the previous
   version of this construction by ~24 ticks.

2  THE BENCHMARK MUST BE SIMULATED, NOT CLOSED FORM. f/(1+f) is the hitting probability for a
   driftless walk with no time limit and Gaussian steps; none of those three holds here (tau=20
   truncates, steps are fat-tailed, and D471 measured the analogous closed-form constant at
   1.17-1.21 rather than 1). The main runner's sign-shuffle null read 0.3538 at f=0.5 where the
   closed form says 0.3333 -- so the closed form is ~2pp too generous and the whole apparent
   excess at f=0.5 was benchmark error. Every rung here carries its own null.

The null holds |r| in place and randomises only signs, so it preserves the return distribution,
the fat tails and the volatility clustering, and destroys exactly the claim under test: that the
ARRANGEMENT of signs after an extreme is reverting.

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
STOP_LADDER = (0.25, 0.5, 0.75, 1.0)
N_SHUF = 20
SEED = 528777


def P(*a):
    print(*a, flush=True)


def resolve2(path, c, idx, s, tick, f):
    """Both stop-fill conventions in one pass. Returns (kind, pnl_real, pnl_ideal, tgt_ticks)."""
    n = len(path)
    kd, pr, pi, tg = [], [], [], []
    last_exit = -1
    for q in range(len(idx)):
        i = int(idx[q]); t = i + 2 * R.H
        if t <= last_exit or t >= n - 1:
            continue
        ss = float(s[q]); p0 = float(path[t]); y0 = float(c["y"][i])
        tgt = float(c["lvl"][i]); stp = p0 + ss * f * abs(y0)
        fwd = path[t + 1:min(t + R.TAU, n - 1) + 1]
        if len(fwd) == 0:
            continue
        ht = (fwd - tgt) * ss <= 0.0
        hs = (fwd - stp) * ss >= 0.0
        i_t = int(np.argmax(ht)) if ht.any() else 1 << 30
        i_s = int(np.argmax(hs)) if hs.any() else 1 << 30
        if i_s == R.BIG and i_t == R.BIG:
            k, kind = len(fwd), 2
            px_real = px_ideal = float(fwd[-1])
        elif i_s <= i_t:
            k, kind = i_s + 1, 1
            px_real, px_ideal = float(fwd[i_s]), stp      # <-- the only difference
        else:
            k, kind = i_t + 1, 0
            px_real = px_ideal = tgt                      # a resting limit fills at its price
        kd.append(kind)
        pr.append((-ss) * (px_real - p0) / tick)
        pi.append((-ss) * (px_ideal - p0) / tick)
        tg.append(abs(y0) / tick)
        last_exit = t + k
    return (np.array(kd, dtype=np.int64), np.array(pr), np.array(pi), np.array(tg))


d = Q.load()
sp = Q.specs()
roots = sorted(set(d["root"]) & set(sp))
rng = np.random.default_rng(SEED)

P(f"THE STOP LADDER with a REALISED stop fill and a per-rung sign-shuffle null")
P(f"  s={S_DIAG}, x={R.X} sigma, tau={R.TAU}, classifier on, drift-aligned, {len(roots)} roots")
P(f"  in sample {d['day'].min()} .. {d['day'].max()}, {N_SHUF} shuffles\n")
P("  stop/  trades  P(target)   null    EXCESS   SE     p_be  | NET ticks REAL  IDEAL   "
  "GAP   median")
P("  target                                                   | (the honest one)  (slip)")

for f in STOP_LADDER:
    KD, PR, PI, TG, CV = [], [], [], [], []
    n_hit = n_all = 0
    for r in roots:
        g = d[d["root"] == r]
        tick = sp[r]["tick_price_units"]
        cost = R.COST.get(r, R.COST_DEFAULT)
        for day, pth in Q.session_bars(g, S_DIAG):
            c = R.classify(pth, tick)
            if c is None:
                continue
            ix, sx, _ = R.entries(c, tick, cost)
            if len(ix):
                kd, pr_, pi_, tg = resolve2(pth, c, ix, sx, tick, f)
                if len(kd):
                    KD.append(kd); PR.append(pr_); PI.append(pi_); TG.append(tg)
                    CV.append(np.full(len(kd), cost))
            rr = np.diff(pth)
            sg = np.where(rng.integers(0, 2, (N_SHUF, len(rr))) == 1, 1.0, -1.0)
            Pn = pth[0] + np.concatenate(
                [np.zeros((N_SHUF, 1)), np.cumsum(np.abs(rr) * sg, axis=1)], axis=1)
            cn = R.classify(Pn, tick)
            if cn is None:
                continue
            for j in range(N_SHUF):
                cj = {kk: (vv[j] if np.ndim(vv) else vv) for kk, vv in cn.items()}
                ij, sj, _ = R.entries(cj, tick, cost)
                if len(ij) == 0:
                    continue
                kj, _, _, _ = resolve2(Pn[j], cj, ij, sj, tick, f)
                if len(kj):
                    n_hit += int((kj == 0).sum()); n_all += len(kj)
    if not KD:
        continue
    kd = np.concatenate(KD); pr_ = np.concatenate(PR)
    pi_ = np.concatenate(PI); tg = np.concatenate(TG); cv = np.concatenate(CV)
    po = float((kd == 0).mean()); pn = n_hit / max(n_all, 1)
    se = float(np.sqrt(po * (1 - po) / len(kd) + pn * (1 - pn) / max(n_all, 1)))
    p_be = float(np.mean((f * tg + cv) / ((1.0 + f) * tg)))
    nr, ni = (pr_ - cv).mean(), (pi_ - cv).mean()
    P(f"  {f:>5.2f}  {len(kd):>6,}    {po:.4f} {pn:.4f}  {po-pn:+.4f} {se:.4f} "
      f"{p_be:.4f} |    {nr:+8.2f} {ni:+7.2f} {ni-nr:+6.2f} "
      f"{np.median(pr_-cv):+8.2f}")

P("\n  EXCESS is against the sign shuffle, which is the only admissible benchmark here.")
P("  GAP is what the idealised stop fill was worth per trade -- pure slippage, not signal.")
P("  Both fills use the SAME trade list and the SAME entries, so GAP isolates the fill.")
