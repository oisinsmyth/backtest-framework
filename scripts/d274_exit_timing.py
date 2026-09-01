"""D274 -- can a TIME-based exit rescue the intraday short? Descriptive anatomy.

    uv run python scripts/d274_exit_timing.py

NO RULE IS PROPOSED AND NO CELL IS PROMOTED. The full k-curve is reported rather
than a chosen k: selecting one from a 12-point sweep is a search and would need
its own pre-registration.

WHY TIME AND NOT A TAKE-PROFIT. Take-profits are closed three times over -- D235
(seven overlays; against the correct matched-count random-exit null the best sat
at the 63rd percentile and the trigger carried no information), D255 (best level
of 600 with perfect hindsight worth +0.017 Sharpe, because 97.2% of trades never
travel far enough to be cut), and D256 (every take-profit cell hurt). But those
levels were 10-30% against an intraday MFE of 30-122 bp, so they were 10 to 100
times larger than the entire excursion and were never testing this book.

TIME IS THE UNTESTED LEVER AND IT IS STRUCTURALLY DIFFERENT: turnover is
sum|dpos|, so one entry plus one exit is 2 whether the hold is 3 bars or 30.
Exiting earlier costs NOTHING extra and lowers the variance tax. It is the only
lever in this programme that improves the numerator without touching the
denominator.

R7's NULL IS THE ONLY ONE THAT DISCRIMINATES and is computed at every k: a
RANDOM exit bar drawn from the same truncated hold. D235 exists because seven
overlays beat their baseline and none beat this.

CORRECTED. A fixed-k exit applies to EVERY trade -- exit at min(k, natural end),
so the sample never shrinks and there is no survivorship in k. The first version
averaged only over trades that LASTED k bars, which selects trades whose signal
stayed on, and that is not a rule anyone can trade."""
import importlib.util, sys
from pathlib import Path
import numpy as np
REPO = Path.cwd(); sys.path.insert(0, "src")
def _load(n, f):
    s = importlib.util.spec_from_file_location(n, REPO/"scripts"/f)
    m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m
A = _load("d271", "d271_trade_anatomy.py"); R, M, D = A.R, A.M, A.D
rp, rc = R.load_full(); pa, ca = R.subset(rp, rc, R.STRATA["ALL"])
first, _ = D.session_structure(pa.dates)
start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
sess_end, _ = A.session_maps(first, pa.closes.shape[1])
rng = np.random.default_rng(0)
for st, arm in (("LOW","S2_short_intra"), ("HIGH","S1_short_intra")):
    p, cl = R.subset(rp, rc, R.STRATA[st]); books = R.build_books(p, cl, start, first)
    pos, rets = books[arm], p.total_log_returns
    c2 = 2.0*float(np.mean(p.cost_fraction)*1e4); paths = []
    for i in range(pos.shape[0]):
        s = pos[i]; ent = np.flatnonzero((s[start:]!=0.0)&(s[start-1:-1]==0.0))+start
        for t in ent:
            close = int(sess_end[t]); z = np.flatnonzero(s[t:close]==0.0)
            ex = t+int(z[0]) if z.size else close
            pth = -np.cumsum(rets[i, t:ex])
            if pth.size: paths.append(pth)
    n = len(paths)
    print("="*76); print(f"{st}:{arm}   {n:,} trades (ALL of them, every k)   cost bar {c2:.2f} bp")
    print("="*76)
    print(f"  {'exit at bar k':>13s} {'mean P&L':>10s} {'R7 random':>10s} {'excess':>8s}  vs cost")
    for k in (1,2,3,4,6,8,10,12,16,20,26,40):
        real = np.mean([x[min(k, len(x))-1] for x in paths])*1e4
        null = np.mean([x[rng.integers(0, min(k, len(x)))] for x in paths])*1e4
        print(f"  {k:13d} {real:9.2f}b {null:9.2f}b {real-null:+7.2f}b   {real/c2:5.2f}x")
    full = np.mean([x[-1] for x in paths])*1e4
    print(f"  {'signal exit':>13s} {full:9.2f}b {'--':>9s} {'--':>8s}   {full/c2:5.2f}x")
    print()
