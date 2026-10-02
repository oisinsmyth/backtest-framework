"""C5 attack (a): is the post-close fade just the daily reversal (K8)? y = P(10:00, S+1) - P(18:05, S+1).
Regress y on m = P(16:15 or 16:59,S)-P(16:00,S), on the day-session return d = P(16:00,S)-P(09:30,S), and on a = P(16:00)-P(13:00).
Also: Welch t of the earnings-season vs off-season difference (b), top-5 trades (d). NQ and ES. 2016-2023, seal asserted."""
import numpy as np, pandas as pd

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_opening_globex_1m.csv.gz"
SEAL = "2024-01-01"
d = pd.read_csv(FX, usecols=["root", "session", "hhmm", "close"])
d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
assert d.session.max() < SEAL
need = ["09:29", "12:59", "15:59", "16:14", "16:58", "16:59", "18:04", "09:59"]
d = d[d.hhmm.isin(need)]


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    # HC1 robust SE
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    se = np.sqrt(np.diag(XtXi @ S @ XtXi)); return b, b / se


for root, usd in [("NQ", 2.0), ("ES", 5.0)]:
    P = d[d.root == root].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P["16:59"] = P["16:59"].fillna(P["16:58"])
    N = P.shift(-1)
    gap = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    ent = N["18:04"].where(gap <= 4)
    y = (N["09:59"] - ent) * usd
    for wname, a in [("16:00-16:15", "16:14"), ("16:00-17:00", "16:59")]:
        m = (P[a] - P["15:59"]) * usd
        dd = (P["15:59"] - P["09:29"]) * usd
        aa = (P["15:59"] - P["12:59"]) * usd
        D = pd.DataFrame({"y": y, "m": m, "d": dd, "a": aa}).dropna()
        thr = m.abs().shift(1).rolling(250, min_periods=120).quantile(0.8).reindex(D.index)
        big = D[D.m.abs() >= thr]
        print(f"\n{root} {wname}: n all {len(D)}, q80 n {len(big)}")
        for lab, S in [("all", D), ("q80", big)]:
            b, tt = ols(S.y.values, S[["m"]].values)
            b2, t2 = ols(S.y.values, S[["m", "d", "a"]].values)
            print(f"  [{lab}] y~m: b_m {b[1]:+.4f} (t {tt[1]:+.2f}) | y~m+d+a: b_m {b2[1]:+.4f} (t {t2[1]:+.2f}), b_d {b2[2]:+.4f} (t {t2[2]:+.2f}), b_a {b2[3]:+.4f} (t {t2[3]:+.2f})")
        # season split on q80 fade
        f = -np.sign(big.m) * big.y
        md = pd.Series(big.index.str[5:10], index=big.index)
        ins = ((md >= "01-15") & (md <= "02-10")) | ((md >= "04-15") & (md <= "05-10")) | ((md >= "07-15") & (md <= "08-10")) | ((md >= "10-15") & (md <= "11-10"))
        fi, fo = f[ins], f[~ins]
        tw = (fi.mean() - fo.mean()) / np.sqrt(fi.var() / len(fi) + fo.var() / len(fo))
        print(f"  season: in ${fi.mean():+.2f} (n {len(fi)}) off ${fo.mean():+.2f} (n {len(fo)}), Welch t of diff {tw:+.2f}")
        print("   in-season n by year", fi.groupby(fi.index.str[:4]).size().to_dict())
        top = f.sort_values()
        print("   top5:", [(i, round(v, 1)) for i, v in top.iloc[-5:].items()], " bottom5:", [(i, round(v, 1)) for i, v in top.iloc[:5].items()])
        k = max(1, int(round(0.01 * len(f))))
        print(f"   ex-top1% ${top.iloc[:-k].mean():+.2f} ex-bot1% ${top.iloc[k:].mean():+.2f} trimmed ${top.iloc[k:-k].mean():+.2f}")
