"""Premise: the reopen move after the weekend (Sunday 18:00) - priced in the thinnest book of the week - reverts by
the Monday cash open. m = close(18:59 bar, evening of session S) - close(16:59 bar of previous session).
Fade from the 18:59 close to the close of the 09:29 / 10:59 bar of session S. $/micro.
Groups: MON (session S is a Monday, i.e. weekend reopen), POSTHOL (gap of >1 weekday between sessions, non-Monday),
WEEKDAY (ordinary daily reopen, placebo). Gate: |m| >= trailing-q80 of |m| within the group's own history (shifted).
In-sample sessions 2016..2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
SEAL = "2024-01-01"
USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "YM": (0.5, 3.80), "RTY": (5.0, 3.76), "GC": (10.0, 5.93), "CL": (100.0, 5.03)}
HM = ["16:59", "18:59", "09:29", "10:59"]
FILES = {"fut_opening_globex_1m.csv.gz": ["ES", "NQ"], "fut_opening_globex_1m_ym_rty.csv.gz": ["YM", "RTY"],
         "fut_opening_globex_1m_cl_ng_gc_si.csv.gz": ["GC", "CL"]}
parts = []
for fn, roots in FILES.items():
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[ch.root.isin(roots) & (ch.session >= "2015-10-01") & (ch.session < SEAL) & ch.hhmm.isin(HM)]
        sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
        ch = ch[((ch.hhmm == "18:59") & (sd - bd).dt.days.between(1, 4)) | ((ch.hhmm != "18:59") & (bd == sd))]
        parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
pd.set_option("display.width", 250)
out = []
for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    s = pd.to_datetime(p.index)
    prev_close = p["16:59"].shift(1)
    gapdays = pd.Series(s, index=p.index).diff().dt.days
    m = p["18:59"] - prev_close
    grp = np.where(s.weekday == 0, "MON", np.where(gapdays > 1, "POSTHOL", "WEEKDAY"))
    df = pd.DataFrame({"m": m, "grp": grp, "x0929": p["09:29"], "x1059": p["10:59"], "e": p["18:59"]}, index=p.index).dropna()
    df = df[df.index >= "2016-01-01"]
    for G in ["MON", "POSTHOL", "WEEKDAY"]:
        sub = df[df.grp == G]
        thr = sub.m.abs().rolling(60 if G == "MON" else 250, min_periods=30).quantile(0.8).shift(1)
        for cut, sel in [("all", sub.m != 0), ("q80", sub.m.abs() >= thr)]:
            ss = sub[sel]
            for x in ["x0929", "x1059"]:
                pnl = -np.sign(ss.m) * (ss[x] - ss.e) * usd
                if len(pnl) < 15: continue
                yy = pd.to_datetime(pnl.index).year
                out.append(dict(root=r, grp=G, cut=cut, exit=x, n=len(pnl), mabs=round((ss.m.abs() * usd).mean(), 1),
                                mean=round(pnl.mean(), 2), med=round(pnl.median(), 2),
                                t=round(pnl.mean() / pnl.std(ddof=1) * np.sqrt(len(pnl)), 2), net=round(pnl.mean() - rt, 2),
                                ex22=round(pnl[yy != 2022].mean(), 2), h1=round(pnl[yy < 2020].mean(), 2), h2=round(pnl[yy >= 2020].mean(), 2)))
r = pd.DataFrame(out); print(r.to_string(index=False)); r.to_csv(f"{OUT}\\cons_reopen_gap.csv", index=False)
