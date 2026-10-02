"""C16: does the MOC-imbalance window (15:50->16:00, NYSE publishes imbalances at 15:50) revert by the next morning, as
closing-auction pressure does in single stocks (Bogousslavsky & Muravyev)? Decompose the 13:00->17:00 path into
a3 = 13:00->15:50, c = 15:50->16:00, m = 16:00->17:00; y = P(exit,S+1) - P(18:05,S+1). OLS HC1. Index roots 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0), "ES": ("fut_opening_globex_1m.csv.gz", 5.0),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0)}


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


cache = {}
need = {"12:59", "15:49", "15:59", "16:58", "16:59", "18:04", "08:29", "09:29", "09:59"}
for root, (fn, usd) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
        cache[fn] = d[d.hhmm.isin(need)]
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P["16:59"] = P["16:59"].fillna(P["16:58"])
    N = P.shift(-1)
    gap = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    ent = N["18:04"].where(gap <= 4)
    a3 = (P["15:49"] - P["12:59"]) * usd; c = (P["15:59"] - P["15:49"]) * usd; m = (P["16:59"] - P["15:59"]) * usd
    for ex in ["08:29", "09:29", "09:59"]:
        y = (N[ex] - ent) * usd
        D = pd.DataFrame({"y": y, "a3": a3, "c": c, "m": m}).dropna()
        b, t = ols(D.y.values, D[["a3", "c", "m"]].values)
        thr = c.abs().shift(1).rolling(250, min_periods=120).quantile(0.8).reindex(D.index)
        big = D[D.c.abs() >= thr]; f = -np.sign(big.c) * big.y
        print(f"{root} exit {ex}: b_a3 {b[1]:+.3f} (t {t[1]:+.2f}) b_c {b[2]:+.3f} (t {t[2]:+.2f}) b_m {b[3]:+.3f} (t {t[3]:+.2f}) n {len(D)}"
              f" | fade c q80 n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}")
