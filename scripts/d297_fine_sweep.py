import importlib.util, sys
from pathlib import Path
import numpy as np
REPO = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(REPO/'src'))
sp = importlib.util.spec_from_file_location('d297', REPO/'scripts'/'run_d297_overlay.py')
D = importlib.util.module_from_spec(sp); sys.modules['d297'] = D; sp.loader.exec_module(D)
E, R, M = D.E, D.R, D.M
panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
live = panel.live; T = live.shape[1]
z = np.load(R.BC.CACHE, allow_pickle=False); bm = z['warm'] & live; n = bm.shape[0]
ctx, r1, vol, plan = E.build_inputs(z, bm, panel, live, T)
lo, hi, ent, tr, fired, clo, chi, resid = E.simulate(ctx, r1, vol, 'none', None, None, None, n, T)
m = np.isfinite(lo) & np.isfinite(hi); base = (lo[m]-hi[m]).astype(np.float64)
print('IS X=12 A PLATEAU OR A SPIKE?  fine sweep, s=0.0, 300 null draws each\n')
print(f"  {'X':>4s} {'expo':>7s} {'mean':>7s} {'SHARPE':>7s} {'ret/exp':>8s} "
      f"{'null95':>7s} {'p':>7s}")
best=[]
for X in range(6, 31):
    on,_,_ = D.schedule(base, float(X))
    st = D.stats(base, np.where(on,1.0,0.0), 105.4)
    rng = np.random.default_rng(4242+X)
    nl = np.array([D.stats(base, np.where(D.matched_schedule(on,rng),1.0,0.0),105.4)['sharpe']
                   for _ in range(300)])
    p = float((nl>=st['sharpe']).sum()+1)/(nl.size+1)
    star = '  <-- the D297 cell' if X==12 else ''
    print(f"  {X:4d} {on.mean():7.1%} {st['mean_bp']:+7.2f} {st['sharpe']:+7.3f} "
          f"{st['ret_per_exposure']:+8.2f} {np.percentile(nl,95):+7.3f} {p:7.4f}{star}")
    best.append((X, st['sharpe'], p))
s=[b[1] for b in best]
print(f"\n  Sharpe across X in [6,30]: min {min(s):+.3f} max {max(s):+.3f} "
      f"p50 {np.median(s):+.3f}  | control +0.512")
print(f"  cells at p<0.05: {sum(1 for b in best if b[2]<0.05)} of {len(best)}")
