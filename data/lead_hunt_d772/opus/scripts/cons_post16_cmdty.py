"""Independent check of the creative's post-16:00 commodity transfer (Lead-2 mechanism on NG/SI/GC/CL).
m = close(16:59) - close(15:59) of session S; gate q80 / q90 trailing-250 shifted; fade from 18:05 (S+1) to the
09:29 and 09:59 closes of S+1. Exact circular rotation null. $/micro (MNG 1000/pt RT 4.00 one-tick line;
SIL 1000/pt RT 8.00; MGC 10/pt RT 5.93; MCL 100/pt RT 5.03). In-sample sessions 2016..2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"; USD = {"NG": (1000.0, 4.00), "SI": (1000.0, 8.00), "GC": (10.0, 5.93), "CL": (100.0, 5.03)}
EVE = ["18:05"]; DAY = ["15:59", "16:59", "09:29", "09:59"]
parts = []
for ch in pd.read_csv(f"{FX}\\fut_opening_globex_1m_cl_ng_gc_si.csv.gz", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
    ch = ch[(ch.session >= "2015-09-01") & (ch.session < SEAL) & ch.hhmm.isin(EVE + DAY)]
    sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
    ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
    parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    nx = p.shift(-1); m = p["16:59"] - p["15:59"]
    for qq in [0.8, 0.9]:
        thr = m.abs().rolling(250, min_periods=120).quantile(qq).shift(1)
        for x in ["09:29", "09:59"]:
            L = (nx[x] - nx["18:05"]) * usd
            ok = m.notna() & L.notna() & (m != 0) & (p.index >= "2016-06-01") & thr.notna()
            s = (-np.sign(m) * (m.abs() >= thr)).where(ok, 0).fillna(0); l = L.where(ok, 0).fillna(0)
            q = (s * l)[s != 0]; yy = pd.to_datetime(q.index).year
            k = (s != 0).sum(); v = np.array([np.sum(np.roll(s.values, j) * l.values) / k for j in range(1, len(s))])
            ps = q.sort_values(); kk = max(1, int(round(0.01 * len(q))))
            print(f"{r} q{int(qq*100)} ->{x}: n{len(q)} mean {q.mean():.2f} med {q.median():.2f} t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} "
                  f"xRT {q.mean()/rt:.2f} exTop {ps.iloc[:-kk].mean():.2f} ex20&22 {q[(yy!=2020)&(yy!=2022)].mean():.2f} rank {(v<q.mean()).mean():.3f} "
                  f"yrs {q.groupby(yy).mean().round(1).to_dict()}")
