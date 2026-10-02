"""C24 audit: split the DIX-contra fade into its long side (down day & high DIX) and short side (up day & low DIX); subtract the
day-leg drift (mean of all T+1 day legs, signed by the trade); year split; ex-2020/2022; trims; and an EXACT circular rotation
null of the DIX z series against (r_T, y_{T+1}) -- keeps the drift and the day-move structure, breaks only the DIX link.
Also OLS y_{T+1} ~ sgn(z) + sgn(z)*contra to separate DIX direction from the reversal interaction. 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
DIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\squeezemetrics\DIX.csv"
SEAL = "2024-01-01"
x = pd.read_csv(DIX, usecols=["date", "dix"], dtype={"date": str})
x = x[x.date < SEAL].set_index("date").dix
z = (x - x.shift(1).rolling(60, min_periods=40).mean()) / x.shift(1).rolling(60, min_periods=40).std()
R = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "RTY": (5.0, 3.76), "YM": (0.5, 3.80)}
for root, (usd, rt) in R.items():
    d = pd.read_csv(f"{FXD}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & d.hhmm.isin({"09:30", "15:59"})]
    assert d.day.max() < SEAL
    P = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last").sort_index()
    r = (P["15:59"] - P["09:30"]); N = P.shift(-1); y = (N["15:59"] - N["09:30"]) * usd
    D = pd.DataFrame({"r": r, "y": y, "z": z.reindex(P.index)}).dropna()
    D = D[D.r != 0]
    drift = D.y.mean()

    def book(zv):
        lo = (D.r.values < 0) & (zv >= 0.84); sh = (D.r.values > 0) & (zv <= -0.84)
        pos = np.where(lo, 1.0, np.where(sh, -1.0, 0.0))
        return pos
    pos = book(D.z.values)
    f = pd.Series(pos * D.y.values, index=D.index)[pos != 0]
    fl = f[pos[pos != 0] > 0]; fs = f[pos[pos != 0] < 0]
    adj = f - pos[pos != 0] * drift
    zs = D.z.values; T = len(zs)
    nulls = np.array([(lambda p: (p * D.y.values)[p != 0].mean())(book(np.roll(zs, k))) for k in range(1, T)])
    srt = f.sort_values(); k = max(1, int(round(0.01 * len(f))))
    yrs = f.groupby(f.index.str[:4]).mean().round(1).to_dict()
    ex = lambda yy: f[~f.index.str[:4].isin(yy)].mean()
    print(f"{root} (RT ${rt}, day-leg drift ${drift:+.2f}): contra n{len(f)} ({len(f) / 8:.0f}/yr) ${f.mean():+.2f} med {f.median():+.2f} "
          f"| long side n{len(fl)} ${fl.mean():+.2f} short side n{len(fs)} ${fs.mean():+.2f} | drift-adjusted ${adj.mean():+.2f} "
          f"| ex20 {ex(['2020']):+.2f} ex22 {ex(['2022']):+.2f} ex20&22 {ex(['2020', '2022']):+.2f} | trim {srt.iloc[k:-k].mean():+.2f} ex-top1% {srt.iloc[:-k].mean():+.2f}"
          f" | rotation p50 {np.median(nulls):+.2f} p95 {np.percentile(nulls, 95):+.2f} rank {(nulls < f.mean()).mean():.3f}\n     years {yrs}")
