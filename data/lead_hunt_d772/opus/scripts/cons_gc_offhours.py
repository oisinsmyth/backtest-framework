"""GC follow-up: which off-hours window's move reverts by the US morning? m over window [a,b] of session S
(evening bars dated S-1), fade from close(b) to close of the 09:29 / 10:59 bar of S. Gate q80 trailing-250 (shifted).
Groups: MON (session is Monday) vs TUE-FRI. $/MGC. In-sample sessions 2016..2023. Also SI (SIL $/pt 1000, RT 8)."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
SEAL = "2024-01-01"; USD = {"GC": (10.0, 5.93), "SI": (1000.0, 8.00)}
EVE = ["18:59", "19:59", "20:59", "21:59", "22:59"]; MORN = ["01:59", "02:59", "03:59", "05:59", "07:59", "09:29", "10:59", "13:29"]
HM = ["16:59"] + EVE + MORN
parts = []
for ch in pd.read_csv(f"{FX}\\fut_opening_globex_1m_cl_ng_gc_si.csv.gz", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
    ch = ch[ch.root.isin(["GC", "SI"]) & (ch.session >= "2015-10-01") & (ch.session < SEAL) & ch.hhmm.isin(HM)]
    sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
    ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
    parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
d.to_parquet(f"{OUT}\\cons_gc_si_offhours.parquet")
WIN = [("PREV16:59", "18:59"), ("18:59", "20:59"), ("20:59", "22:59"), ("22:59", "01:59"), ("01:59", "03:59"), ("03:59", "07:59"), ("PREV16:59", "22:59")]
for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    p["PREV16:59"] = p["16:59"].shift(1)
    s = pd.to_datetime(p.index); mon = pd.Series(s.weekday == 0, index=p.index)
    for a, b in WIN:
        m = p[b] - p[a]
        thr = m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
        for x in ["09:29", "10:59"]:
            pnl = -np.sign(m) * (p[x] - p[b]) * usd
            ok = pnl.notna() & (m != 0) & (p.index >= "2016-01-01")
            for G, gm in [("MON", mon), ("TUE-FRI", ~mon), ("ALL", mon | ~mon)]:
                for cut, cm in [("all", ok), ("q80", ok & (m.abs() >= thr))]:
                    q = pnl[cm & gm]
                    yy = pd.to_datetime(q.index).year
                    print(f"{r} {a}->{b} exit {x} {G:7s} {cut}: n{len(q)} mean {q.mean():.2f} med {q.median():.2f} "
                          f"t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} ex22 {q[yy!=2022].mean():.2f} "
                          f"16-19 {q[yy<2020].mean():.2f} 20-23 {q[yy>=2020].mean():.2f} posyrs {(q.groupby(yy).mean()>0).sum()}/8")
