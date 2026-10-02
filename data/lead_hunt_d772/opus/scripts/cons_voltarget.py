"""Lead-5 probe (declared to the creative before running): vol-targeting deleveraging at the close.
Trigger day S: trailing 5-session realised vol of 16:00-to-16:00 returns (through S-1, so pre-entry by construction
at 15:00 of S) above the trailing-250 q80 of that series (shifted). Signal: the 15:00->16:00 move of S (close 14:59 bar
-> close 15:59 bar). Fade from 18:05 (S+1) to the 09:59 close of S+1. Compared with non-trigger days.
Also reported: the plain 'sell into the close' leg (long at 18:05 after a down 15-16 hour on trigger days).
ES/NQ/RTY/YM. Exact circular rotation null. In-sample <= 2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"; USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "YM": (0.5, 3.80), "RTY": (5.0, 3.76)}
EVE = ["18:05"]; DAY = ["14:59", "15:59", "09:59"]
parts = []
for fn, roots in {"fut_opening_globex_1m.csv.gz": ["ES", "NQ"], "fut_opening_globex_1m_ym_rty.csv.gz": ["YM", "RTY"]}.items():
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[(ch.session >= "2015-09-01") & (ch.session < SEAL) & ch.hhmm.isin(EVE + DAY)]
        sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
        ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
        parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    ret = np.log(p["15:59"]).diff()
    rv5 = ret.rolling(5).std().shift(1)                       # through S-1
    thr = rv5.rolling(250, min_periods=120).quantile(0.8).shift(1)
    trig = rv5 > thr
    c = p["15:59"] - p["14:59"]; nx = p.shift(-1)
    L = (nx["09:59"] - nx["18:05"]) * usd
    ok = c.notna() & L.notna() & (c != 0) & (p.index >= "2016-06-01") & thr.notna()
    for lab, sel in [("TRIG", ok & trig), ("NON", ok & ~trig)]:
        s = (-np.sign(c)).where(sel, 0).fillna(0); l = L.where(ok, 0).fillna(0)
        q = (s * l)[s != 0]; yy = pd.to_datetime(q.index).year
        k = (s != 0).sum(); v = np.array([np.sum(np.roll(s.values, j) * l.values) / k for j in range(1, len(s))])
        print(f"{r} {lab}: n{len(q)} mean {q.mean():.2f} med {q.median():.2f} t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} xRT {q.mean()/rt:.2f} "
              f"ex20 {q[yy!=2020].mean():.2f} ex22 {q[yy!=2022].mean():.2f} rank {(v<q.mean()).mean():.3f} yrs {q.groupby(yy).mean().round(1).to_dict()}")
