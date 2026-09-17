"""THE WEDGE'S LAST QUESTION.

Two studies asked "which way?" and got nothing. Neither asked the textbook claim:
DOES COMPRESSION FORECAST EXPANSION?

The bar is not "is there a relationship" -- compression IS low volatility and low
volatility is autocorrelated, so a naive test passes trivially. The bar is:

    does channel width in ATRs beat TRAILING REALISED VOLATILITY at forecasting
    forward realised volatility?

If not, the wedge is a laggy proxy for `std(returns, 21)` and the line is closed.

R9: w_atr and trail_vol are read at t-1; fwd_vol is measured from t+1 onward.
Arming thresholds swept 2..6 ATR, because the principal's point is that a real
wedge is generally wider than 2 ATR and the tight threshold may be what starves
hurdle E.
"""
import importlib.util, math, sys
from pathlib import Path
import numpy as np

# Resolved from this file, not hardcoded: the literal absolute path this line used to
# hold was the author's own checkout, so the script could not run on any other machine.
REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
def _load(nm, fn):
    sp = importlib.util.spec_from_file_location(nm, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(sp); sys.modules[nm] = m; sp.loader.exec_module(m); return m
from backtest_framework.research import macd as M
W = _load("d249_wedge", "run_wedge_inverse.py")
E = _load("d243_extended", "run_book_extended.py")
L = E.L

H = 21          # forward and trailing volatility window
FIX = REPO / "data" / "fixtures"


def run(label, fixture, events, ppy):
    sf, se, sp = L.FIXTURE, L.EVENTS, L.PPY
    try:
        L.FIXTURE, L.EVENTS, L.PPY = fixture, events, ppy
        panel, cleaned = L.load_panel()
    finally:
        L.FIXTURE, L.EVENTS, L.PPY = sf, se, sp

    n, T = panel.closes.shape
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    sig = W.wedge_signals(panel, cleaned, start)
    r = panel.log_returns

    # trailing and forward realised volatility, annualised
    r2 = r * r
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(r2, axis=1)], axis=1)
    trail = np.full((n, T), np.nan)
    fwd = np.full((n, T), np.nan)
    trail[:, H:] = np.sqrt((cs[:, H:T] - cs[:, :T-H]) / H * ppy)          # bars t-H .. t-1
    fwd[:, :T-H-1] = np.sqrt((cs[:, H+1:T] - cs[:, 1:T-H]) / H * ppy)     # bars t+1 .. t+H

    w = np.full((n, T), np.nan)
    w[:, 1:] = sig["w_atr"][:, :-1]                     # R9: read at t-1
    cv = np.zeros((n, T), dtype=bool)
    cv[:, 1:] = sig["conv"][:, :-1]

    ok = np.isfinite(w) & np.isfinite(trail) & np.isfinite(fwd) & cv
    ok[:, :start] = False
    wv, tv, fv = w[ok], trail[ok], fwd[ok]
    print(f"\n{'='*78}\n{label}: {n} names x {T:,} bars, {ok.sum():,} usable converging cells\n{'='*78}")

    def q5(x, y, lab):
        e = np.quantile(x, [.2, .4, .6, .8])
        out = [y[x < e[0]].mean()]
        for i in range(3):
            out.append(y[(x >= e[i]) & (x < e[i+1])].mean())
        out.append(y[x >= e[3]].mean())
        print(f"  {lab:34} " + "  ".join(f"{v:6.1%}" for v in out) +
              f"   spread {out[-1]-out[0]:+6.1%}")
        return out

    print(f"\nFORWARD {H}-BAR REALISED VOL, by quintile of each predictor (Q1 low -> Q5 high)")
    print(f"  {'':34} {'Q1':>6}  {'Q2':>6}  {'Q3':>6}  {'Q4':>6}  {'Q5':>6}")
    q5(wv, fv, "channel width in ATRs (the wedge)")
    q5(tv, fv, "trailing realised vol (CONTROL)")

    pw = np.corrcoef(wv, fv)[0, 1]
    pt = np.corrcoef(tv, fv)[0, 1]
    # partial correlation of width with forward vol, controlling for trailing vol
    rwt = np.corrcoef(wv, tv)[0, 1]
    part = (pw - pt * rwt) / math.sqrt(max((1 - pt*pt) * (1 - rwt*rwt), 1e-12))
    print(f"\n  corr(width, fwd vol)               {pw:+.3f}")
    print(f"  corr(trailing vol, fwd vol)        {pt:+.3f}   <- the control")
    print(f"  corr(width, trailing vol)          {rwt:+.3f}")
    print(f"  PARTIAL corr(width, fwd | trail)   {part:+.3f}   <- what the wedge ADDS")

    print(f"\nDOUBLE SORT -- does width still sort forward vol INSIDE a trailing-vol bucket?")
    te = np.quantile(tv, [1/3, 2/3])
    print(f"  {'trailing-vol tercile':24} {'width Q1':>10} {'width Q5':>10} {'spread':>9}")
    adds = []
    for b, lab in enumerate(("LOW trailing vol", "MID", "HIGH trailing vol")):
        m = (tv < te[0]) if b == 0 else ((tv >= te[1]) if b == 2 else ((tv >= te[0]) & (tv < te[1])))
        x, y = wv[m], fv[m]
        e = np.quantile(x, [.2, .8])
        a, z = y[x < e[0]].mean(), y[x >= e[1]].mean()
        adds.append(z - a)
        print(f"  {lab:24} {a:9.1%} {z:9.1%} {z-a:+8.1%}   n={m.sum():,}")
    print(f"  mean within-bucket spread {np.mean(adds):+.2%}   "
          f"(raw width spread was {q5.__name__ and ''}"
          f"{fv[wv>=np.quantile(wv,.8)].mean()-fv[wv<np.quantile(wv,.2)].mean():+.2%})")

    print(f"\nARMING THRESHOLD SWEEP -- setups and hurdle E, as the threshold widens")
    print(f"  {'arm <= k ATR':14} {'% cells':>9} {'episodes':>10} {'names':>7} {'per name':>9} "
          f"{'median gap':>11}")
    live = np.zeros((n, T), dtype=bool); live[:, start:] = True
    for k in (2.0, 3.0, 4.0, 5.0, 6.0):
        armed = sig["conv"] & (sig["w_atr"] <= k) & live
        prev = np.zeros_like(armed); prev[:, 1:] = armed[:, :-1]
        eps = armed & ~prev
        per = eps.sum(axis=1)
        gaps = []
        for i in range(n):
            idx = np.flatnonzero(eps[i])
            if len(idx) > 1: gaps.extend(np.diff(idx))
        print(f"  {k:13.1f} {armed[:, start:].mean():8.2%} {eps.sum():10,} "
              f"{int((per>0).sum()):7d} {per.mean():9.1f} "
              f"{(np.median(gaps) if gaps else float('nan')):10.0f}b")
    print(f"  hurdle E needs >= 30 ENTRIES per symbol, and entries are a fraction of episodes")


run("US ETFs (extended, 16.8 yr)", FIX / "universe_daily_extended_raw.csv.gz",
    FIX / "universe_daily_extended_raw_events.json", 252.0)
run("CRYPTO (D244's 34 coins)", FIX / "crypto_book_2018_raw.csv.gz",
    FIX / "crypto_book_2018_raw_events.json", 365.0)
