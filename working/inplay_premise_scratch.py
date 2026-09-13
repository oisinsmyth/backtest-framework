"""Premise check for an in-play lever on the PROP book. Conditioner-side only: no signed P&L, no edge, no signal.
Measures, per root and per causal in-play decile: E|day-session move| in dollars and ticks, sigma, the fixed fee as a share of
E|M|, the break-even accuracy it implies, and the share of days whose |move| exceeds the P3 bar ($1,000 = 2% of $50k).
The in-play measure is known before 09:30: the OVERNIGHT leg's range and volume relative to their own trailing medians.
"""
import numpy as np, pandas as pd, json

FIX = 'data/fixtures/fut_sessions_hourly.csv.gz'
ROOTS = ['ES', 'NQ', 'YM', 'ZN', 'ZB', 'GC', 'CL', '6E']
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "GC": 10.0, "CL": 100.0, "6E": 12_500.0, "ZN": 1_000.0, "ZB": 1_000.0}
TICK = {"ES": 0.25, "NQ": 0.25, "YM": 1.0, "GC": 0.1, "CL": 0.01, "6E": 0.0001, "ZN": 1 / 64, "ZB": 1 / 32}
FEE = {r: (6.0 if r in ("ZN", "ZB") else 3.0) for r in ROOTS}
NIGHT = ['h18', 'h19', 'h20', 'h21', 'h22', 'h23', 'h00', 'h01', 'h02', 'h03', 'h04', 'h05', 'h06', 'h07', 'h08']
DAY = ['h09', 'h10', 'h11', 'h12', 'h13', 'h14', 'h15']
WARM = 20
START, END = '2016-01-04', '2023-12-29'

T = pd.read_csv(FIX, dtype={'root': str, 'day': str})
T = T[T.same_front.astype(bool)]
T = T[(T.day >= START) & (T.day <= END)]
rows = []
persist = {}
for r in ROOTS:
    t = T[T.root == r].sort_values('day').reset_index(drop=True)
    mult, tick, fee = MULT[r], TICK[r], FEE[r]
    day_o = t['h09_o'].to_numpy(float); day_c = t['h15_c'].to_numpy(float)
    dh = t[[f'{s}_h' for s in DAY]].to_numpy(float); dl = t[[f'{s}_l' for s in DAY]].to_numpy(float)
    nh = t[[f'{s}_h' for s in NIGHT]].to_numpy(float); nl = t[[f'{s}_l' for s in NIGHT]].to_numpy(float)
    nv = t[[f'{s}_v' for s in NIGHT]].to_numpy(float)
    M = (day_c - day_o) * mult                                     # signed day move in $ (only |M| and sigma are used)
    day_rng = (np.nanmax(dh, axis=1) - np.nanmin(dl, axis=1)) * mult
    night_rng = (np.nanmax(nh, axis=1) - np.nanmin(nl, axis=1)) * mult
    night_vol = np.nansum(nv, axis=1)
    ok = np.isfinite(M) & np.isfinite(night_rng) & np.isfinite(night_vol) & (night_vol > 0)
    # causal in-play: the overnight leg's range and volume against their trailing WARM-session medians (shifted, so day d is excluded)
    med_r = pd.Series(night_rng).rolling(WARM, min_periods=WARM).median().shift(1).to_numpy()
    med_v = pd.Series(night_vol).rolling(WARM, min_periods=WARM).median().shift(1).to_numpy()
    rel_r = night_rng / med_r; rel_v = night_vol / med_v
    score = np.sqrt(np.clip(rel_r, 0, None) * np.clip(rel_v, 0, None))        # the declared in-play score: geometric mean of the two
    m = ok & np.isfinite(score)
    # premise 1: does the conditioner predict the size of the move it precedes?
    persist[r] = dict(n=int(m.sum()),
                      rho_score_absM=float(np.corrcoef(score[m], np.abs(M[m]))[0, 1]),
                      rho_relr_absM=float(np.corrcoef(rel_r[m], np.abs(M[m]))[0, 1]),
                      rho_relv_absM=float(np.corrcoef(rel_v[m], np.abs(M[m]))[0, 1]),
                      rho_score_next=float(np.corrcoef(score[m][:-1], score[m][1:])[0, 1]))
    q = pd.qcut(score[m], 10, labels=False, duplicates='drop')
    aM = np.abs(M[m]); Mm = M[m]
    for d in range(10):
        s = q == d
        if s.sum() < 10:
            continue
        e = float(aM[s].mean())
        rows.append(dict(root=r, decile=d + 1, n=int(s.sum()), e_absM_usd=e, e_absM_ticks=e / (tick * mult),
                         sigma_usd=float(Mm[s].std(ddof=1)), fee_share=fee / e, breakeven_acc=0.5 + fee / (2 * e),
                         beyond_1000=float((np.abs(Mm[s]) > 1000).mean()), beyond_500=float((np.abs(Mm[s]) > 500).mean()),
                         med_absM=float(np.median(aM[s]))))
D = pd.DataFrame(rows)
pd.set_option('display.width', 200)
print('PERSISTENCE of the conditioner, and whether it predicts the size of the move it precedes (2016-2023):')
print(pd.DataFrame(persist).T.round(3).to_string())
print('\nE|day move| and the fee against it, by in-play decile (1 = quietest overnight, 10 = most in play):')
for r in ROOTS:
    d = D[D.root == r]
    if d.empty:
        continue
    print(f"\n{r} (one micro, fee ${FEE[r]:.0f}):")
    print('  decile:        ' + ' '.join(f'{int(x):>7d}' for x in d.decile))
    print('  E|M| $:        ' + ' '.join(f'{x:>7.0f}' for x in d.e_absM_usd))
    print('  E|M| ticks:    ' + ' '.join(f'{x:>7.0f}' for x in d.e_absM_ticks))
    print('  sigma $:       ' + ' '.join(f'{x:>7.0f}' for x in d.sigma_usd))
    print('  fee/E|M| %:    ' + ' '.join(f'{100*x:>7.1f}' for x in d.fee_share))
    print('  breakeven %:   ' + ' '.join(f'{100*x:>7.1f}' for x in d.breakeven_acc))
    print('  |M|>$1000 %:   ' + ' '.join(f'{100*x:>7.1f}' for x in d.beyond_1000))
print('\nRATIO of decile 10 to decile 1, per root:')
for r in ROOTS:
    d = D[D.root == r]
    if len(d) < 10:
        continue
    a, b = d.iloc[0], d.iloc[-1]
    print(f"  {r}: E|M| x{b.e_absM_usd/a.e_absM_usd:.2f}  sigma x{b.sigma_usd/a.sigma_usd:.2f}  fee share {100*a.fee_share:.1f}% -> {100*b.fee_share:.1f}%  "
          f"breakeven {100*a.breakeven_acc:.1f}% -> {100*b.breakeven_acc:.1f}%  P3 breach rate {100*a.beyond_1000:.1f}% -> {100*b.beyond_1000:.1f}%")
D.to_csv('temp/inplay_premise.csv', index=False, float_format='%.4f')
json.dump(persist, open('temp/inplay_premise_persistence.json', 'w'), indent=1)
print('\nwrote temp/inplay_premise.csv and temp/inplay_premise_persistence.json')
