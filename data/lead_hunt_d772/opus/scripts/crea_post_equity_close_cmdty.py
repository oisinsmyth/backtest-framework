"""VARIANT: post-EQUITY-close hour 16:00->17:00 on commodities. C5 family test: on commodity roots, is a point made AFTER the root's own settlement (Globex-only, post price-setting)
more transient than a point made in the hours before it? m = P(16:59,S) - P(settle_end,S); a = P(settle_end) - P(settle_end-3h);
y = P(exit, S+1) - P(18:05 entry, S+1). OLS y ~ m + a (HC1 t), and the q80 fade of m in $ per micro.
Also the index roots with settle_end = 16:00 for comparison. Fixtures fut_opening_globex_1m*; sessions 2016..2023 (seal).
"""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
CASES = {"GC": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "15:59", 10.0, 5.93),
         "SI": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "15:59", 1000.0, 8.00),
         "CL": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "15:59", 100.0, 5.03),
         "NG": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "15:59", 1000.0, 4.00),
         "HG": ("fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "15:59", 2500.0, 4.25),
         "NQ": ("fut_opening_globex_1m.csv.gz", "15:59", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", "15:59", 5.0, 4.42),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", "15:59", 0.5, 3.80), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", "15:59", 5.0, 3.76)}
EXITS = ["08:29", "09:59", "11:59"]


def hm_minus(hm, mins):
    h, m = map(int, hm.split(":")); t = h * 60 + m - mins; return f"{t // 60:02d}:{t % 60:02d}"


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


cache = {}
for root, (fn, se, usd, rt) in CASES.items():
    pre = hm_minus(se, 180)
    need = {se, pre, "16:58", "16:59", "18:04", *EXITS}
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        cache[fn] = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
    d = cache[fn]
    d = d[(d.root == root) & d.hhmm.isin(need)]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P["16:59"] = P["16:59"].fillna(P["16:58"])
    N = P.shift(-1)
    gap = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    ent = N["18:04"].where(gap <= 4)
    m = (P["16:59"] - P[se]) * usd
    a = (P[se] - P[pre]) * usd
    line = []
    for ex in EXITS:
        y = (N[ex] - ent) * usd
        D = pd.DataFrame({"y": y, "m": m, "a": a}).dropna()
        b, t = ols(D.y.values, D[["m", "a"]].values)
        thr = m.abs().shift(1).rolling(250, min_periods=120).quantile(0.8).reindex(D.index)
        big = D[D.m.abs() >= thr]
        f = -np.sign(big.m) * big.y
        line.append(f"exit {ex}: b_m {b[1]:+.3f} (t {t[1]:+.2f}) b_a {b[2]:+.3f} (t {t[2]:+.2f}) | q80 fade n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}")
    print(f"{root} settle_end {se} RT ${rt} mean|m| ${m.abs().mean():.1f}\n   " + "\n   ".join(line))
