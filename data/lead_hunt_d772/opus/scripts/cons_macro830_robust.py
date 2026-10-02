"""Robustness of the CPI/EMPSIT 08:30 fade on NQ/ES (in-sample <= 2023).
Variants: sign from 08:29->08:34 (S5) or 08:29->09:29 (S60); entry 08:34 or 09:29 close; exit 11:00.
Reports CPI vs EMPSIT, halves, trimmed means, top trade, per-year.
"""
import numpy as np, pandas as pd
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
MICRO = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07)}
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & ev.event.isin(["CPI", "EMPSIT"]) & (ev.datetime_et.str[11:16] == "08:30")]
etype = dict(zip(ev.datetime_et.str[:10], ev.event))
d = pd.read_parquet(f"{OUT}\\cons_globex_0800_1230.parquet"); assert d.session.max() < SEAL
for root in ["NQ", "ES"]:
    usd, rt = MICRO[root]
    piv = d[d.root == root].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    piv = piv[piv.index.isin(list(etype))]
    for sig, ent_hm in [("S5", "08:34"), ("S5", "09:29"), ("S60", "09:29")]:
        for xhm in ["10:00", "11:00", "12:00"]:
            sh = "08:34" if sig == "S5" else "09:29"
            s = np.sign(piv[sh] - piv["08:29"])
            p = (-s * (piv[xhm] - piv[ent_hm]) * usd).dropna(); p = p[s.loc[p.index] != 0]
            n = len(p); ps = p.sort_values(); k = max(1, int(round(0.01 * n)))
            yr = pd.Series(p.values, index=pd.to_datetime(p.index).year)
            typ = pd.Series([etype[i] for i in p.index], index=p.index)
            print(f"{root} sig={sig} entry={ent_hm} exit={xhm} n={n} mean={p.mean():.2f} med={p.median():.2f} "
                  f"t={p.mean()/p.std(ddof=1)*np.sqrt(n):.2f} win={(p>0).mean():.2f} net={p.mean()-rt:.2f} "
                  f"exTop={ps.iloc[:-k].mean():.2f} exBot={ps.iloc[k:].mean():.2f} trim={ps.iloc[k:-k].mean():.2f} "
                  f"CPI={p[typ=='CPI'].mean():.2f}(n{(typ=='CPI').sum()}) NFP={p[typ=='EMPSIT'].mean():.2f} "
                  f"16-19={p[yr.index.values<2020].mean():.2f} 20-23={p[yr.index.values>=2020].mean():.2f} "
                  f"ex2022={p[yr.index.values!=2022].mean():.2f} top={p.idxmax()}:{p.max():.0f} bot={p.idxmin()}:{p.min():.0f} "
                  f"posyrs={(yr.groupby(level=0).mean()>0).sum()}/8")
