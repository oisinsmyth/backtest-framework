"""Lead-2 structure for FX: is a point of EUR/AUD made after the London close (12:00->17:00 ET, NY-only liquidity) transient,
reverting when London reopens (next session 03:00-08:00 ET)? m = h16_c - h11_c of session S (h11_c = 12:00 close);
a = h11_c - h07_c (London/NY overlap morning). y = P(exit, S+1) - P(h18_c, S+1) [entry 19:00]. OLS HC1; q80 fade in $/micro.
fut_breadth_hourly, 2016-2023 (seal); same_front on both sessions."""
import numpy as np, pandas as pd

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_breadth_hourly.csv.gz"
SEAL = "2024-01-01"
R = {"6E": (12500.0, 4.38), "6A": (10000.0, 4.0), "6B": (6250.0, 4.0), "GC": (10.0, 5.93), "ES": (5.0, 4.42), "NQ": (2.0, 4.07)}
cols = ["root", "day", "same_front", "h18_c", "h02_c", "h03_c", "h07_c", "h09_c", "h11_c", "h16_c", "h15_c"]
d = pd.read_csv(FX, usecols=cols)
d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & d.root.isin(list(R))]
assert d.day.max() < SEAL


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


for root, (usd, rt) in R.items():
    g = d[d.root == root].sort_values("day").dropna(subset=["h16_c", "h11_c", "h07_c"]).reset_index(drop=True)
    N = g.shift(-1)
    ok = N.same_front.fillna(False).astype(bool) & ((pd.to_datetime(N.day) - pd.to_datetime(g.day)).dt.days <= 4)
    m = (g.h16_c - g.h11_c) * usd; a = (g.h11_c - g.h07_c) * usd
    line = []
    for ex in ["h02_c", "h07_c", "h09_c"]:
        y = ((N[ex] - N.h18_c) * usd).where(ok)
        D = pd.DataFrame({"y": y, "m": m, "a": a}).dropna()
        b, t = ols(D.y.values, D[["m", "a"]].values)
        thr = m.abs().shift(1).rolling(250, min_periods=120).quantile(0.8).reindex(D.index)
        big = D[D.m.abs() >= thr]; f = -np.sign(big.m) * big.y
        line.append(f"exit {ex[:3]}+1h: b_m {b[1]:+.3f} (t {t[1]:+.2f}) b_a {b[2]:+.3f} (t {t[2]:+.2f}) | q80 fade n{len(f)} ${f.mean():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}")
    print(f"{root} RT ${rt}:\n   " + "\n   ".join(line))
