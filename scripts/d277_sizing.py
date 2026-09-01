"""D277 addendum: what the five cells do under different sizing.

Sharpe is INVARIANT to constant leverage (D201/D202), so nothing about quality
changes. What changes is the return, the volatility, the drawdown, and whether
the book survives its worst bar."""
import importlib.util, sys, json, math
from pathlib import Path
import numpy as np
REPO = Path.cwd(); sys.path.insert(0, "src")
def _load(n,f):
    s=importlib.util.spec_from_file_location(n,REPO/"scripts"/f); m=importlib.util.module_from_spec(s); sys.modules[n]=m; s.loader.exec_module(m); return m
Q = _load("d277","d277_mine.py"); S,P,R,M,D,A = Q.S,Q.P,Q.R,Q.M,Q.D,Q.A
rp,rc = R.load_full(); panel,cleaned = R.subset(rp,rc,R.STRATA["ALL"])
first,gap = D.session_structure(panel.dates)
start = max(M.impulse_warm_up_bars(),M.warm_up_bars(),M.MATCHED_MOMENTUM_LOOKBACK)
T = panel.closes.shape[1]; ppy = (T/int(first.sum()))*252.0
vol,px,stamps = Q.V.load_volume(panel); bod = Q.V.bar_of_day(stamps)
bases, scores = Q.build_all(panel,cleaned,first,start,vol,px,bod)
masks = {(nm,w): Q.quintile_mask(scores[nm],start,w) for nm in scores for w in ("top","bot")}

FIVE = [("LOW","S2_short_intra","impulse_hist","bot"),
        ("LOW","S2_short_intra","macd_line","bot"),
        ("HIGH","S2_short_intra","mass_imbalance","bot"),
        ("ALL","S2_short_intra","mass_imbalance","bot"),
        ("LOW","S2_short_intra","mass_imbalance","bot")]

print(f"{'cell':40s} {'n':>2s} {'expo':>6s} | {'CAGR':>8s} {'vol':>7s} {'maxDD':>8s} {'SR':>7s}")
print("-"*100)
rows=[]
for st,base,sc,w in FIVE:
    p,cl = ((panel,cleaned) if st=="ALL" else R.subset(rp,rc,R.STRATA[st]))
    keep=[panel.symbols.index(x) for x in p.symbols]; borrow=R.borrow_vector(p.symbols)
    pos = bases[base][keep]*masks[(sc,w)][keep]
    n = len(p.symbols)
    base_sc = R.score(p,pos,start,first,gap,ppy,borrow)
    # worst adverse bar while in position -> Model-A ruin
    held = pos[:,start:]!=0.0
    r = p.total_log_returns[:,start:]
    adverse = float(np.max(np.expm1(r[held]))) if held.any() else 0.0
    max_notional = 1.0/adverse if adverse>0 else float("inf")
    rows.append((st,base,sc,n,base_sc,adverse,max_notional))
    print(f"{st+'|'+base+'|'+sc+'|'+w:40s} {n:2d} {base_sc['exposure']:5.2%} | "
          f"{base_sc['cagr']:+7.2%} {base_sc['vol']:6.2%} {base_sc['max_drawdown']:7.2%} "
          f"{base_sc['excess_sharpe']:+7.3f}")
print()
print("READING (a) -- FULL DEPLOYMENT PER TRADE: when the signal fires, 100% of capital")
print("             in that name instead of 1/n. Scale = n.")
print(f"{'cell':40s} {'scale':>6s} {'CAGR':>9s} {'vol':>8s} {'maxDD':>9s} {'SR':>7s}")
print("-"*100)
for st,base,sc,n,b,adv,mn in rows:
    k=float(n)
    print(f"{st+'|'+base+'|'+sc:40s} {k:5.0f}x {np.expm1(math.log1p(b['cagr'])*k):+8.2%} "
          f"{b['vol']*k:7.2%} {max(-1.0,b['max_drawdown']*k):8.2%} {b['excess_sharpe']:+7.3f}")
print()
print("READING (b) -- 100% AVERAGE EXPOSURE: lever until mean|position| = 1.0.")
print(f"{'cell':40s} {'scale':>7s} {'implied vol':>12s} {'worst bar':>10s} {'max survivable':>15s}")
print("-"*100)
for st,base,sc,n,b,adv,mn in rows:
    k=1.0/b['exposure']
    print(f"{st+'|'+base+'|'+sc:40s} {k:6.0f}x {b['vol']*k:11.1%} {adv:+9.2%} "
          f"{mn:14.2f}x")
print()
print("  'max survivable' = the largest notional that survives the worst ADVERSE bar")
print("  the cell actually held. Above it, one bar takes the account to zero.")
