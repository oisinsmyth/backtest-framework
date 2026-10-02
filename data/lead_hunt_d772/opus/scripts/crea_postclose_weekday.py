"""Lead-2 mechanism probe: is the post-close give-back the unwinding of hedges on ES-family options that expired at 16:00?
(i) Natural experiment: before 2022-05 the PM-settled ES weeklies expired Mon/Wed/Fri only; Tue/Thu had none.
(ii) Dose: same-day-expiring 16:00 ES-family open interest (contracts, from fut_es_options_eod; OI as of the prior close).
Leg A: fade m = P(16:59,S)-P(15:59,S) from P(18:05,S+1) to P(10:00,S+1). OLS of y on m interacted with expiry. ES and NQ.
2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"


def ols(y, X):
    X = np.column_stack([np.ones(len(y)), X]); b, *_ = np.linalg.lstsq(X, y, rcond=None)
    e = y - X @ b; n, k = X.shape
    XtXi = np.linalg.inv(X.T @ X); S = (X * e[:, None]).T @ (X * e[:, None]) * n / (n - k)
    return b, b / np.sqrt(np.diag(XtXi @ S @ XtXi))


o = pd.read_csv(f"{FXD}\\fut_es_options_eod.csv.gz", usecols=["session", "expiry_date", "expiry_hhmm", "oi"])
o = o[(o.session < SEAL) & (o.expiry_date == o.session) & (o.expiry_hhmm == "16:00")]
assert o.session.max() < SEAL
xoi = o.groupby("session").oi.sum()
print("sessions with a 16:00 same-day ES expiry:", len(xoi), "median OI", xoi.median())

need = {"15:59", "16:58", "16:59", "18:04", "09:59"}
d = pd.read_csv(f"{FXD}\\fut_opening_globex_1m.csv.gz", usecols=["root", "session", "hhmm", "close"])
d = d[(d.session >= "2016-01-01") & (d.session < SEAL) & d.hhmm.isin(need)]
assert d.session.max() < SEAL
for root, usd in [("ES", 5.0), ("NQ", 2.0)]:
    P = d[d.root == root].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P["16:59"] = P["16:59"].fillna(P["16:58"])
    N = P.shift(-1)
    gap = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    y = ((N["09:59"] - N["18:04"]) * usd).where(gap <= 4)
    m = (P["16:59"] - P["15:59"]) * usd
    D = pd.DataFrame({"y": y, "m": m}).dropna()
    D["xoi"] = xoi.reindex(D.index).fillna(0.0)
    D["exp"] = (D.xoi > 0).astype(float)
    dow = pd.to_datetime(D.index).dayofweek
    pre = D.index < "2022-05-01"
    print(f"\n== {root}")
    for lab, S in [("all", D), ("pre-2022-05", D[pre]), ("2022-05+", D[~pre])]:
        b, t = ols(S.y.values, np.column_stack([S.m, S.m * S.exp, S.exp]))
        print(f" [{lab}] n{len(S)} expiry share {S.exp.mean():.2f}: b_m(no expiry) {b[1]:+.3f} (t {t[1]:+.2f}), b_mxExp {b[2]:+.3f} (t {t[2]:+.2f})")
    Sp = D[pre]
    for lab, sel in [("Mon/Wed/Fri", np.isin(dow[pre], [0, 2, 4])), ("Tue/Thu", np.isin(dow[pre], [1, 3]))]:
        S = Sp[sel]
        b, t = ols(S.y.values, S[["m"]].values)
        print(f"   pre-2022-05 {lab}: n{len(S)} b_m {b[1]:+.3f} (t {t[1]:+.2f}) expiry share {S.exp.mean():.2f}")
    for wd in range(5):
        S = D[(dow == wd)]
        b, t = ols(S.y.values, S[["m"]].values)
        S2 = D[(dow == wd) & pre]
        b2, t2 = ols(S2.y.values, S2[["m"]].values)
        print(f"   weekday {wd}: all n{len(S)} b_m {b[1]:+.3f} (t {t[1]:+.2f}) | pre-2022-05 n{len(S2)} b_m {b2[1]:+.3f} (t {t2[1]:+.2f})")
    E = D[D.exp > 0].copy()
    E["oiq"] = pd.qcut(E.xoi.rank(method="first"), 3, labels=["lowOI", "midOI", "highOI"])
    for q, S in E.groupby("oiq", observed=True):
        b, t = ols(S.y.values, S[["m"]].values)
        print(f"   expiry-day OI tercile {q}: n{len(S)} median OI {S.xoi.median():.0f} b_m {b[1]:+.3f} (t {t[1]:+.2f})")
