"""C24 audit for the conservative: (1) P&L share by year, ex-2020; (2) bp-of-notional edge per year (NQ, ES);
(3) neighbouring cuts z 0.5/0.84/1.28 x z-windows 20/60/120; (4) one extra day of lag (DIX_{T-1} for the T+1 trade) as a
publication-time robustness check; (5) contra vs agree vs unconditional next-day fade on the same days, and contra minus
the unconditional fade restricted to the contra days' move-size. Day leg 09:30->16:00, 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
DIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\squeezemetrics\DIX.csv"
SEAL = "2024-01-01"
x = pd.read_csv(DIX, usecols=["date", "dix"], dtype={"date": str})
x = x[x.date < SEAL].set_index("date").dix


def zser(w, lag=0):
    z = (x - x.shift(1).rolling(w, min_periods=int(0.67 * w)).mean()) / x.shift(1).rolling(w, min_periods=int(0.67 * w)).std()
    return z.shift(lag)


for root, usd in [("NQ", 2.0), ("ES", 5.0), ("RTY", 5.0), ("YM", 0.5)]:
    d = pd.read_csv(f"{FXD}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & d.hhmm.isin({"09:30", "15:59"})]
    assert d.day.max() < SEAL
    P = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last").sort_index()
    r = P["15:59"] - P["09:30"]; N = P.shift(-1); y = (N["15:59"] - N["09:30"]) * usd
    notional = N["09:30"] * usd
    print(f"\n==== {root}")
    for w in (20, 60, 120):
        for lag in (0, 1):
            z = zser(w, lag).reindex(P.index)
            line = []
            for cut in (0.5, 0.84, 1.28):
                con = ((r < 0) & (z >= cut)) | ((r > 0) & (z <= -cut))
                agr = ((r < 0) & (z <= -cut)) | ((r > 0) & (z >= cut))
                fc = (-np.sign(r) * y)[con].dropna(); fa = (-np.sign(r) * y)[agr].dropna()
                line.append(f"z{cut}: con n{len(fc)} ${fc.mean():+.2f} (t {fc.mean() / fc.std() * np.sqrt(len(fc)):+.2f}) agr ${fa.mean():+.2f}")
            print(f" w{w} lag{lag}: " + " | ".join(line))
    z = zser(60).reindex(P.index)
    con = ((r < 0) & (z >= 0.84)) | ((r > 0) & (z <= -0.84))
    f = (-np.sign(r) * y)[con].dropna()
    bp = (f / notional.reindex(f.index) * 1e4)
    allf = (-np.sign(r) * y).dropna()
    allbp = allf / notional.reindex(allf.index) * 1e4
    yr = pd.DataFrame({"n": f.groupby(f.index.str[:4]).size(), "sum$": f.groupby(f.index.str[:4]).sum().round(0),
                       "share%": (100 * f.groupby(f.index.str[:4]).sum() / f.sum()).round(1),
                       "mean$": f.groupby(f.index.str[:4]).mean().round(2), "mean_bp": bp.groupby(bp.index.str[:4]).mean().round(2),
                       "uncond_fade_bp": allbp.groupby(allbp.index.str[:4]).mean().round(2)})
    print(yr.to_string())
    print(f" contra mean ${f.mean():+.2f} ({bp.mean():+.2f} bp); ex-2020 ${f[~f.index.str.startswith('2020')].mean():+.2f} "
          f"({bp[~bp.index.str.startswith('2020')].mean():+.2f} bp); 2016-19 {bp[bp.index < '2020'].mean():+.2f} bp vs 2020-23 {bp[bp.index >= '2020'].mean():+.2f} bp; "
          f"unconditional next-day fade all days ${allf.mean():+.2f} ({allbp.mean():+.2f} bp), on the contra days' |r| tercile-matched set: see below")
    # size-matched unconditional baseline: non-contra days with |r| in the same deciles as contra days
    dec = pd.qcut(r.abs().rank(method="first"), 10, labels=False)
    w_ = dec[con].value_counts(normalize=True)
    base = []
    for k, wt in w_.items():
        s = (-np.sign(r) * y)[(dec == k) & ~con].dropna()
        base.append(wt * s.mean())
    print(f" |r|-decile-matched unconditional fade (non-contra days): ${sum(base):+.2f}  -> DIX margin ${f.mean() - sum(base):+.2f}")
