"""Lead-5 probe: index weekend reopen (Fri 16:59 close -> Sun 18:59 close) faded from 19:00 Sunday to Monday
01:59/02:59/03:59/05:59/09:29/10:59 closes. 1-minute globex fixtures, Monday sessions, 2016..2023.
Exact circular rotation null over the Monday series (sign vs leg). $/micro."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"; USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "YM": (0.5, 3.80), "RTY": (5.0, 3.76)}
EVE = ["18:59"]; DAY = ["16:59", "01:59", "02:59", "03:59", "05:59", "09:29", "10:59"]
parts = []
for fn, roots in {"fut_opening_globex_1m.csv.gz": ["ES", "NQ"], "fut_opening_globex_1m_ym_rty.csv.gz": ["YM", "RTY"]}.items():
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[(ch.session >= "2015-10-01") & (ch.session < SEAL) & ch.hhmm.isin(EVE + DAY)]
        sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
        ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
        parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    p["prev"] = p["16:59"].shift(1)
    mon = p[(pd.to_datetime(p.index).weekday == 0) & (p.index >= "2016-01-01")]
    m = mon["18:59"] - mon["prev"]
    for x in ["01:59", "02:59", "03:59", "05:59", "09:29", "10:59"]:
        L = ((mon[x] - mon["18:59"]) * usd)
        ok = m.notna() & L.notna() & (m != 0)
        s = -np.sign(m[ok]).values; l = L[ok].values
        pnl = pd.Series(s * l, index=m[ok].index); yy = pd.to_datetime(pnl.index).year
        v = np.array([np.mean(np.roll(s, k) * l) for k in range(1, len(s))])
        print(f"{r} Mon exit {x}: n{len(pnl)} mean {pnl.mean():.2f} med {pnl.median():.2f} t {pnl.mean()/pnl.std(ddof=1)*np.sqrt(len(pnl)):.2f} "
              f"xRT {pnl.mean()/rt:.2f} ex20 {pnl[yy!=2020].mean():.2f} ex22 {pnl[yy!=2022].mean():.2f} rot p95 {np.percentile(v,95):.2f} rank {(v<pnl.mean()).mean():.3f} "
              f"posyrs {(pnl.groupby(yy).mean()>0).sum()}/8")
