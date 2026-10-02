"""Audit of the creative's C5 (post-cash-close overshoot). In-sample sessions 2016..2023.
m = close(16:59 bar of session S) - close(15:59 bar of S)  [16:00 print -> 17:00]
Legs on session S+1 signed against m: A 18:05(S+1 open bars, i.e. prior evening) -> 10:00 ; B 09:29 -> 11:00 ; C 18:05 -> 09:29.
Gate |m| >= trailing-250 q80 of |m| (shifted, pre-entry). Earnings season = Jan15-Feb10, Apr15-May10, Jul15-Aug10, Oct15-Nov10.
Also: residual r = m_NQ - beta*m_ES (beta from trailing 250 sessions, shifted) and the day return 09:30-16:00 of S.
"""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
SEAL = "2024-01-01"; USD = {"NQ": 2.0, "ES": 5.0}
HM = ["09:29", "10:00", "11:00", "15:59", "16:14", "16:59", "18:05"]
parts = []
for ch in pd.read_csv(f"{FX}\\fut_opening_globex_1m.csv.gz", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
    ch = ch[(ch.session >= "2015-12-01") & (ch.session < SEAL) & ch.hhmm.isin(HM)]
    parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
# keep only bars belonging to the session's own window: evening bars dated session-1, day bars dated session
sd = pd.to_datetime(d.session); bd = pd.to_datetime(d.et.str[:10])
d = d[((d.hhmm >= "18:00") & ((sd - bd).dt.days.between(1, 4))) | ((d.hhmm < "18:00") & (bd == sd))]
P = {r: g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last") for r, g in d.groupby("root")}
idx = P["NQ"].index.intersection(P["ES"].index)
def season(s):
    m, dd = s.month, s.day
    return (m in (1, 4, 7, 10) and dd >= 15) or (m in (2, 5, 8, 11) and dd <= 10)
rows = {}
for r in ["NQ", "ES"]:
    p = P[r].reindex(idx)
    m = p["16:59"] - p["15:59"]; day = p["15:59"] - p["09:29"]
    nxt = p.shift(-1)  # session S+1 (next trading session in the index)
    rows[r] = pd.DataFrame({"m": m, "day": day, "A": -(nxt["10:00"] - nxt["18:05"]), "B": -(nxt["11:00"] - nxt["09:29"]),
                            "C": -(nxt["09:29"] - nxt["18:05"])}, index=idx)
mNQ, mES = rows["NQ"].m, rows["ES"].m
cov = (mNQ * mES).rolling(250, min_periods=120).mean().shift(1); var = (mES * mES).rolling(250, min_periods=120).mean().shift(1)
resid = mNQ - (cov / var) * mES
for r in ["NQ", "ES"]:
    df = rows[r].copy(); df["resid"] = resid
    df = df[(df.index >= "2016-01-01")].dropna()
    thr = df.m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
    g = df[df.m.abs() >= thr]; print(r, "df", len(df), "g", len(g), P[r].notna().sum().to_dict())
    ins = pd.Series([season(pd.Timestamp(s)) for s in g.index], index=g.index)
    for leg in ["A", "B", "C"]:
        pnl = np.sign(g.m) * g[leg] * USD[r]
        def st(x): return f"n{len(x)} {x.mean():.2f} med {x.median():.2f} t {x.mean()/x.std(ddof=1)*np.sqrt(len(x)):.2f}"
        a, b = pnl[ins], pnl[~ins]
        wt = (a.mean() - b.mean()) / np.sqrt(a.var() / len(a) + b.var() / len(b))
        yrs = pnl.groupby(pd.to_datetime(pnl.index).year).mean().round(1).to_dict()
        yy = pd.to_datetime(pnl.index).year; print(f"   {r} {leg} ex2022 {pnl[yy!=2022].mean():.2f} 16-19 {pnl[yy<2020].mean():.2f} 20-23 {pnl[yy>=2020].mean():.2f} ex2020+2022 {pnl[(yy!=2022)&(yy!=2020)].mean():.2f} nyr {pnl.groupby(yy).size().to_dict()}")
        print(f"{r} leg {leg}: all {st(pnl)} | season {st(a)} | off {st(b)} | diff t {wt:.2f} | {yrs}")
    # regression of leg A pnl (unsigned: future return of fade-direction) : y = -(next move) on m, day, resid
    y = g["A"] * USD[r]
    X = np.column_stack([np.ones(len(g)), g.m, g.day] + ([g.resid] if r == "NQ" else []))
    beta, *_ = np.linalg.lstsq(X, y.values, rcond=None)
    res = y.values - X @ beta; s2 = res @ res / (len(y) - X.shape[1]); se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    print(r, "OLS leg A (y=-next 18:05->10:00 move, $) on [1, m, day" + (", resid]" if r == "NQ" else "]"),
          "t:", np.round(beta / se, 2))
    yB = g["B"] * USD[r]; beta, *_ = np.linalg.lstsq(X, yB.values, rcond=None)
    res = yB.values - X @ beta; s2 = res @ res / (len(yB) - X.shape[1]); se = np.sqrt(np.diag(s2 * np.linalg.inv(X.T @ X)))
    print(r, "OLS leg B (09:29->11:00) t:", np.round(beta / se, 2))
    if r == "NQ":
        for lab, sel in [("resid-dominated |resid|>|m-resid|", g.resid.abs() > (g.m - g.resid).abs()), ("common-dominated", g.resid.abs() <= (g.m - g.resid).abs())]:
            pnl = (np.sign(g.m) * g["A"] * USD[r])[sel]
            print("NQ", lab, f"n{len(pnl)} {pnl.mean():.2f} t {pnl.mean()/pnl.std(ddof=1)*np.sqrt(len(pnl)):.2f}")
