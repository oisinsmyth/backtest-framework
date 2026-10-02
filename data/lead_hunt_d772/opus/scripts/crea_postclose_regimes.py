"""Lead-2 mechanism probe: retail forced flattening? Prop-firm/intraday-margin rules force retail day traders flat at
~16:10 ET (Topstep 15:10 CT) and ~16:45-16:59 ET (broker intraday-margin cutoffs, Apex 16:59). If that flow is the transient
part, the give-back should load on those sub-windows and be larger after the micro E-mini launch (2019-05-06).
Sub-windows of the post-close hour: w1 16:00-16:10, w2 16:10-16:15, w3 16:15-16:40, w4 16:40-17:00 (prices = closes of
the bar before each clock). y = P(10:00,S+1) - P(18:05,S+1). Joint OLS, HC1. Also the 15:15->15:30 CT halt era: the equity
daily settlement moved from 16:15 ET to 16:00 ET on 2020-10-26 (SER-8591). 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


need = {"15:59", "16:09", "16:14", "16:39", "16:58", "16:59", "18:04", "09:59"}
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0), "ES": ("fut_opening_globex_1m.csv.gz", 5.0),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0)}
cache = {}
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
    y = ((N["09:59"] - N["18:04"]) * usd).where(gap <= 4)
    W = pd.DataFrame({"w1": P["16:09"] - P["15:59"], "w2": P["16:14"] - P["16:09"], "w3": P["16:39"] - P["16:14"],
                      "w4": P["16:59"] - P["16:39"]}) * usd
    D = pd.concat([y.rename("y"), W], axis=1).dropna()
    print(f"\n== {root}  mean|w| " + " ".join(f"{c} ${D[c].abs().mean():.1f}" for c in W.columns))
    for lab, S in [("all", D), 
                   ("R1 settle16:15+halt ..2020-10-23", D[D.index < "2020-10-26"]), ("R3 settle16:00 no halt 2021-06-28..", D[D.index >= "2021-06-28"])]:
        b, t = ols(S.y.values, S[["w1", "w2", "w3", "w4"]].values)
        print(f"  [{lab}] n{len(S)}: " + " ".join(f"b_{c} {b[i + 1]:+.3f} (t {t[i + 1]:+.2f})" for i, c in enumerate(W.columns)))
