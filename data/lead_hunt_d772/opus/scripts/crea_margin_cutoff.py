"""C23 (partner's suggestion, declared before running): broker intraday-margin cut-offs force retail micro accounts flat
around 15:45-16:00 ET. If that forced flow is the transient part of the close, the 15:45->16:00 move should revert overnight
MORE on nights when the micro share of volume in 15:45-16:00 is abnormally high. Signal c = P(16:00) - P(15:45) on the mini;
z = log(micro share 15:45-16:00 / median of the prior 20 sessions' same-window share). Fade c from P(18:05,S+1)...
-- we only hold 07:00-16:15 bars of the micro decode, so the overnight leg prices come from fut_opening_globex (minis).
Reports: fade of c (q80 gate) split by z tercile; interaction OLS y ~ c + c*z; rho with Lead 4 (c 15:50->16:00, q80).
Pairs MES/ES, MNQ/NQ, M2K/RTY, MYM/YM, 2019-05-06 .. 2023-12-29 (seal)."""
import numpy as np, pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out"
FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
mm = pd.read_parquet(OUT / "crea_micro_mini_1m.parquet")
assert mm.day.max() < SEAL
PAIRS = {"ES": ("MES", "fut_opening_globex_1m.csv.gz", 5.0), "NQ": ("MNQ", "fut_opening_globex_1m.csv.gz", 2.0),
         "RTY": ("M2K", "fut_opening_globex_1m_ym_rty.csv.gz", 5.0), "YM": ("MYM", "fut_opening_globex_1m_ym_rty.csv.gz", 0.5)}


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


cache = {}
for mini, (mic, fn, usd) in PAIRS.items():
    w = mm[(mm.m >= 945) & (mm.m < 960)]
    va = w[w.root == mini].groupby("day").volume.sum(); vb = w[w.root == mic].groupby("day").volume.sum()
    share = (vb / (vb + 10 * va)).dropna()
    z = np.log(share / share.shift(1).rolling(20, min_periods=15).median())
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        cache[fn] = d[(d.session >= "2019-05-06") & (d.session < SEAL) & d.hhmm.isin({"15:44", "15:49", "15:59", "18:04", "09:59"})]
    d = cache[fn][cache[fn].root == mini]
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    N = P.shift(-1)
    ok = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values <= 4
    y = ((N["09:59"] - N["18:04"]) * usd).where(ok)
    c = (P["15:59"] - P["15:44"]) * usd
    c4 = (P["15:59"] - P["15:49"]) * usd
    D = pd.DataFrame({"y": y, "c": c, "c4": c4, "z": z}).dropna()
    D = D[D.index >= "2019-07-01"]
    g = D.c.abs() >= D.c.abs().shift(1).rolling(120, min_periods=60).quantile(0.8)
    g4 = D.c4.abs() >= D.c4.abs().shift(1).rolling(120, min_periods=60).quantile(0.8)
    D["f"] = -np.sign(D.c) * D.y
    D["zt"] = pd.qcut(D.z.rank(method="first"), 3, labels=False)
    parts = []
    for zt in (0, 1, 2):
        f = D.f[g & (D.zt == zt)]
        parts.append(f"z{zt}: n{len(f)} ${f.mean():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}")
    zc = (D.z - D.z.mean()) / D.z.std()
    b, t = ols(D.y.values, np.column_stack([D.c, D.c * zc]))
    hz = g & (D.zt == 2)
    L4 = (-np.sign(D.c4) * D.y).where(g4).fillna(0.0)
    mine = D.f.where(hz).fillna(0.0)
    rho = np.corrcoef(mine, L4)[0, 1]
    f4 = (-np.sign(D.c4) * D.y)[g4 & hz]
    print(f"{mini}/{mic}: q80 fade by micro-share tercile: " + " | ".join(parts) +
          f" || OLS b_c {b[1]:+.3f} (t {t[1]:+.2f}) b_cxz {b[2]:+.3f} (t {t[2]:+.2f}) || rho(high-z book, Lead 4) {rho:+.2f}; Lead-4 c-fade on same high-z nights ${f4.mean():+.2f} n{len(f4)}")
