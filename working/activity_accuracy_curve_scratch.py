"""Does directional accuracy on the day session fall as the prior night gets busier, or rise?
The "no man's land" video says quiet, contracting conditions are where expected value is negative.
D506 compared only the top activity decile against the other 90%. This resolves the whole curve.
Outcome-side but wholly inside D506's window and cells -- a measurement, nothing new is spent.
"""
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path('.').resolve()
spec = importlib.util.spec_from_file_location('af', REPO / 'scripts' / 'activity_filter.py')
af = importlib.util.module_from_spec(spec); sys.modules['af'] = af; spec.loader.exec_module(af)
spec2 = importlib.util.spec_from_file_location('d506', REPO / 'scripts' / 'run_d506_inplay_accuracy.py')
d506 = importlib.util.module_from_spec(spec2); sys.modules['d506'] = d506; spec2.loader.exec_module(d506)

T = pd.read_csv(REPO / 'data/fixtures/fut_sessions_hourly.csv.gz', dtype={'root': str, 'day': str})
rows = []
for root in d506.ROOTS:
    d = d506.load_root(T, root); b = d506.build(d)
    M = d['M']; fee = d506.FEE[root]
    s = b['score']
    for sg in ('S1', 'S2'):
        sig = b['sig'][sg]
        ok = np.isfinite(M) & np.isfinite(sig) & (sig != 0) & np.isfinite(s) & (M != 0)
        q = pd.qcut(s[ok], 10, labels=False, duplicates='drop')
        x = (sig * M)[ok]; aM = np.abs(M)[ok]
        for i in range(10):
            m = q == i
            if m.sum() < 20:
                continue
            rows.append(dict(root=root, sig=sg, decile=i + 1, n=int(m.sum()), p=float((x[m] > 0).mean()),
                             gross=float(x[m].mean()), e_absM=float(aM[m].mean()), fee_share=fee / float(aM[m].mean())))
D = pd.DataFrame(rows)
print('DIRECTIONAL ACCURACY BY ACTIVITY DECILE (1 = quietest prior night, 10 = busiest), 2016-2023\n')
for sg, name in (('S1', 'the long day drift'), ('S2', 'the log MACD')):
    sub = D[D.sig == sg]
    print(f'{name}:')
    print('  root   ' + ' '.join(f'{i:>6d}' for i in range(1, 11)) + '   q1-q10   slope/decile')
    for root in d506.ROOTS:
        r = sub[sub.root == root].sort_values('decile')
        if len(r) < 10:
            continue
        p = r.p.to_numpy() * 100
        sl = np.polyfit(np.arange(1, 11), p, 1)[0]
        print(f'  {root:5s}  ' + ' '.join(f'{v:6.1f}' for v in p) + f'   {p[0]-p[-1]:+6.1f}   {sl:+.2f}')
    piv = sub.pivot_table(index='decile', values='p', aggfunc='mean') * 100
    pm = piv.p.to_numpy()
    print(f'  POOLED ' + ' '.join(f'{v:6.1f}' for v in pm) + f'   {pm[0]-pm[-1]:+6.1f}   {np.polyfit(np.arange(1,11), pm, 1)[0]:+.2f}\n')
g = D.pivot_table(index='decile', columns='sig', values='gross', aggfunc='mean')
print('mean gross $ per trade by decile (equal weight across roots):')
print(g.round(2).to_string())
q1 = D[D.decile == 1]; q10 = D[D.decile == 10]
print(f'\nquietest decile: mean accuracy {100*q1.p.mean():.2f}%, mean gross ${q1.gross.mean():+.2f}, n {int(q1.n.sum()):,}')
print(f'busiest  decile: mean accuracy {100*q10.p.mean():.2f}%, mean gross ${q10.gross.mean():+.2f}, n {int(q10.n.sum()):,}')
print(f'cells where the quietest decile beats the busiest on accuracy: {int((q1.p.to_numpy() > q10.p.to_numpy()).sum())} of {len(q1)}')
