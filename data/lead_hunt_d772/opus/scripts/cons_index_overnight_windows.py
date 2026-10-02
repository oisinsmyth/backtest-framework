"""Which overnight window's move (cash equities shut) reverts by the US morning on the index roots?
Windows over session S (evening bars dated S-1): 18:05->19:59 (Asia pre), 19:59->21:59 (Tokyo/China open),
21:59->02:59, 02:59->03:59 (Europe open), 03:59->08:29 (Europe morning), plus the full 18:05->08:29.
Fade from the window-end close to the close of the 10:59 bar of S (and 09:29). Gate q80 trailing-250 shifted.
Excludes CPI/EMPSIT days (Lead 1). $/micro. In-sample sessions 2016..2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
USD = {"NQ": 2.0, "ES": 5.0, "YM": 0.5, "RTY": 5.0}
EVE = ["18:05", "19:59", "21:59"]; MORN = ["02:59", "03:59", "08:29", "09:29", "10:59"]
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & ev.event.isin(["CPI", "EMPSIT"])]
edays = set(ev.datetime_et.str[:10])
parts = []
for fn, roots in {"fut_opening_globex_1m.csv.gz": ["ES", "NQ"], "fut_opening_globex_1m_ym_rty.csv.gz": ["YM", "RTY"]}.items():
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[(ch.session >= "2015-10-01") & (ch.session < SEAL) & ch.hhmm.isin(EVE + MORN)]
        sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
        ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
        parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
WIN = [("18:05", "19:59"), ("19:59", "21:59"), ("21:59", "02:59"), ("02:59", "03:59"), ("03:59", "08:29"), ("18:05", "08:29")]
for r, g in d.groupby("root"):
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    p = p[~p.index.isin(list(edays))]
    for a, b in WIN:
        m = p[b] - p[a]; thr = m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
        for x in ["09:29", "10:59"]:
            pnl = -np.sign(m) * (p[x] - p[b]) * USD[r]
            ok = pnl.notna() & (m != 0) & (p.index >= "2016-01-01")
            for cut, cm in [("all", ok), ("q80", ok & (m.abs() >= thr))]:
                q = pnl[cm]; yy = pd.to_datetime(q.index).year
                print(f"{r} {a}->{b} x{x} {cut}: n{len(q)} mean {q.mean():.2f} med {q.median():.2f} t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} "
                      f"ex22 {q[yy!=2022].mean():.2f} 16-19 {q[yy<2020].mean():.2f} 20-23 {q[yy>=2020].mean():.2f} posyrs {(q.groupby(yy).mean()>0).sum()}/8")
