"""Premise: the 10:00 ISM release (manufacturing: 1st business day; services: 3rd business day) impulse fade,
NQ/ES rth 1m, sessions 2016..2023. Pre = close(09:59); entry close(09:59+K); exit close(X). $/micro.
Placebo = all other days at the same clock. Business day proxied by trading day of month (fixture days).
"""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
SEAL = "2024-01-01"
MICRO = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07)}
res = []
for root in ["NQ", "ES"]:
    d = pd.read_csv(f"{FX}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL)]; assert d.day.max() < SEAL
    piv = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last")
    days = pd.Series(pd.to_datetime(piv.index), index=piv.index)
    tdom = days.groupby(days.dt.to_period("M")).rank(method="first").astype(int)
    usd, rt = MICRO[root]
    for K in [1, 5, 15]:
        ehm = f"10:{K-1:02d}" if K > 0 else "09:59"
        ehm = f"{10 + (K - 1) // 60}:{(K - 1) % 60:02d}"
        for xhm in ["11:00", "12:00", "13:00", "15:00"]:
            pre, ent, ex = piv["09:59"], piv[ehm], piv[xhm]
            imp = ent - pre
            ok = np.isfinite(pre) & np.isfinite(ent) & np.isfinite(ex) & (imp != 0)
            pnl = -np.sign(imp) * (ex - ent) * usd
            for lab, m in [("ISM_MFG_BD1", ok & (tdom == 1)), ("ISM_SVC_BD3", ok & (tdom == 3)),
                           ("PLACEBO", ok & ~tdom.isin([1, 3]))]:
                p = pnl[m]
                yrs = pd.Series(p.values, index=pd.to_datetime(p.index).year).groupby(level=0).mean().round(1).to_dict()
                res.append(dict(root=root, K=K, exit=xhm, set=lab, n=len(p), imp=round((imp.abs() * usd)[m].mean(), 1),
                                fade=round(p.mean(), 2), med=round(p.median(), 2),
                                t=round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2), years=yrs if lab != "PLACEBO" else ""))
r = pd.DataFrame(res)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 200)
print(r.to_string(index=False)); r.to_csv(f"{OUT}\\cons_ism1000_fade.csv", index=False)
