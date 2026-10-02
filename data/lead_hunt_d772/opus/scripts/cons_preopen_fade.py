"""Lead-5 probe: the pre-open futures-only move on NON-CPI/NFP days (ES/NQ), faded after the cash open.
m windows: 08:00->09:29 (close of 07:59.. use 08:00 bar close as start), 08:59->09:29, 08:29->08:34 already Lead 1.
Entry at the 09:29 close (the 09:30 print), exit 10:00 / 11:00 / 12:00. Gate q80 trailing-250 shifted.
Exact circular rotation null. In-sample <= 2023."""
import numpy as np, pandas as pd
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"; USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42)}
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & ev.event.isin(["CPI", "EMPSIT"])]
edays = set(ev.datetime_et.str[:10])
d = pd.read_parquet(f"{OUT}\\cons_globex_0800_1230.parquet"); assert d.session.max() < SEAL
def rot(sig, leg):
    s, l = sig.values, leg.values; k = (s != 0).sum(); obs = np.nansum(s * l) / k
    v = np.array([np.nansum(np.roll(s, j) * l) / k for j in range(1, len(s))]); return obs, np.percentile(v, 95), (v < obs).mean()
for r, (usd, rt) in USD.items():
    p = d[d.root == r].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    p = p[(pd.to_datetime(p.index).weekday < 5) & ~p.index.isin(list(edays))]
    for a in ["08:00", "08:59", "09:14"]:
        m = p["09:29"] - p[a]
        thr = m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
        for x in ["10:00", "11:00", "12:00"]:
            L = (p[x] - p["09:29"]) * usd
            ok = m.notna() & L.notna() & (p.index >= "2016-06-01")
            sig = (-np.sign(m) * (m.abs() >= thr)).where(ok, 0).fillna(0)
            q = (sig * L)[sig != 0]; yy = pd.to_datetime(q.index).year
            obs, p95, rk = rot(sig[ok], L[ok].fillna(0))
            print(f"{r} m {a}->09:29 exit {x}: n{len(q)} mean {q.mean():.2f} med {q.median():.2f} t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} "
                  f"ex22 {q[yy!=2022].mean():.2f} rot p95 {p95:.2f} rank {rk:.3f} yrs {q.groupby(yy).mean().round(1).to_dict()}")
