"""PRE-TEST for the threshold idea: does the day's SCORE GAP predict the day's return?

The rank book always holds N names. The principal's proposal is to hold them only
when they are genuinely extreme. That is a claim about TIME VARIATION: the signal
should be stronger on bars where the selected names are further apart in score.

Measured as the gap between the mean score of the short leg and the long leg, per
bar, then bars split into terciles by that gap.

CONFOUND REPORTED, NOT ASSUMED: dispersion rises with market volatility, so the
widest tercile may simply be 2020. The 2020 share of each tercile is printed.
"""
import importlib.util, json, sys
from pathlib import Path
import numpy as np
REPO=Path.cwd(); sys.path.insert(0,str(REPO/"src"))
def L(n,f):
    s=importlib.util.spec_from_file_location(n,REPO/"scripts"/f); m=importlib.util.module_from_spec(s)
    sys.modules[n]=m; s.loader.exec_module(m); return m
M=L("run_mine_neutral","run_mine_neutral.py"); BC=L("d290_build_cache","d290_build_cache.py")
B=M.B
S1=json.load(open("data/d290_stage1.json"))
CAND=["close_in_range","macd_hist","rsi","dist_52w_high","choch_dist","rev_5","price_log"]
z=np.load(BC.CACHE, allow_pickle=False)          # lazy: only requested keys load
panel,_=M.RP.load_ragged(B.FIXTURE,B.EVENTS,fee_bps=B.FEE_BPS)
live=panel.live; base=z["warm"]&live; T=live.shape[1]
fwd=M.forward_returns(panel,live)
yr=np.array([int(str(d)[:4]) for d in panel.dates])
print(f"{'candidate':16s} {'N':>3s} {'k':>3s} | {'narrow':>16s} {'mid':>16s} {'wide':>16s} | rho  2020% wide")
for c in CAND:
    N,k,_=S1["results"][c]["observed"]["spread"]
    s=z[c]; lag=M.C.lag1(s)
    order,cnt=M.rank_columns(s,base)
    ev_lo,ev_hi,_=M.legs_from_order(order,cnt,N,base.shape)
    lr,lc=np.nonzero(ev_lo); hr,hc=np.nonzero(ev_hi)
    f=fwd[k]
    slo,clo=M.bar_sums(f,lr,lc,T); shi,chi=M.bar_sums(f,hr,hc,T)
    m=(clo>0)&(chi>0)
    d=np.full(T,np.nan); d[m]=slo[m]/clo[m]-shi[m]/chi[m]
    # score gap per bar, in the score's own units
    gl,cl2=M.bar_sums(np.where(base,lag,np.nan).astype(np.float32),lr,lc,T)
    gh,ch2=M.bar_sums(np.where(base,lag,np.nan).astype(np.float32),hr,hc,T)
    gap=np.full(T,np.nan)
    ok=(cl2>0)&(ch2>0)
    gap[ok]=gh[ok]/ch2[ok]-gl[ok]/cl2[ok]
    v=m&np.isfinite(gap)&np.isfinite(d)&(yr[:T]!=2020)
    g,r=gap[v],d[v]; y=yr[:T][v]
    q=np.argsort(np.argsort(g))/max(len(g)-1,1)
    cells=[]
    for lo_,hi_ in ((0,1/3),(1/3,2/3),(2/3,0.9),(0.9,1.01)):
        sel=(q>=lo_)&(q<hi_)
        rr=r[sel]
        t=rr.mean()/(rr.std(ddof=1)/np.sqrt(rr.size)) if rr.size>2 else 0
        cells.append(f"{rr.mean()*1e4:+8.1f} t{t:+5.1f}")
    rho=np.corrcoef(np.argsort(np.argsort(g)),np.argsort(np.argsort(r)))[0,1]
    w2020=(y[(q>=2/3)]==2020).mean()
    print(f"{c:16s} {N:3d} {k:3d} | {' '.join(cells)} | {rho:+.3f} {w2020:5.1%}")
