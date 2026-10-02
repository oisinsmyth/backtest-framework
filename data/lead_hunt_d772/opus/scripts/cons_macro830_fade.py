"""Premise: does the 08:30 macro-release impulse (CPI, EMPSIT) revert, $ per one micro, ES/NQ/GC/CL?
Bars are bar-START stamped (hhmm). Pre = close of 08:29 bar. Impulse = close(08:29+K) - pre. Entry close(08:29+K).
Exits at listed clocks (close of that bar). Placebo: all other weekdays at the same clock.
In-sample sessions 2016-01-01 .. 2023-12-31 only.
"""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
SEAL = "2024-01-01"
MICRO = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07), "GC": (10.0, 5.93), "CL": (100.0, 5.03)}
ev = pd.read_csv(EVT); ev = ev[ev.datetime_et < SEAL]
ev = ev[ev.event.isin(["CPI", "EMPSIT"]) & (ev.datetime_et.str[11:16] == "08:30")]
edays = set(ev.datetime_et.str[:10])

def load(fn, roots):
    parts = []
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[ch.root.isin(roots) & (ch.session >= "2016-01-01") & (ch.session < SEAL)
                & (ch.hhmm >= "08:00") & (ch.hhmm <= "12:30")]
        ch = ch[ch.et.str[:10] == ch.session]  # same-calendar-day bars only (drops stray old-dated rows)
        parts.append(ch)
    d = pd.concat(parts); assert d.session.max() < SEAL; return d

d = pd.concat([load("fut_opening_globex_1m.csv.gz", ["ES", "NQ"]),
               load("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", ["GC", "CL"])])
d.to_parquet(f"{OUT}\\cons_globex_0800_1230.parquet")
res = []
for root, g in d.groupby("root"):
    piv = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    usd, rt = MICRO[root]
    wd = pd.to_datetime(piv.index).weekday
    for K in [1, 5, 15]:
        ehm = f"08:{29+K:02d}"
        for xhm in ["09:00", "09:29", "10:00", "11:00", "12:00"]:
            if not {"08:29", ehm, xhm} <= set(piv.columns):
                continue
            pre, ent, ex = piv["08:29"], piv[ehm], piv[xhm]
            imp = ent - pre
            ok = np.isfinite(pre) & np.isfinite(ent) & np.isfinite(ex) & (imp != 0) & (wd < 5)
            pnl = -np.sign(imp) * (ex - ent) * usd
            isev = pd.Series(piv.index.isin(list(edays)), index=piv.index)
            for lab, m in [("EVENT", ok & isev), ("PLACEBO", ok & ~isev)]:
                p = pnl[m]; a = (imp.abs() * usd)[m]
                for cut, mm in [("all", a >= 0), ("top33", a >= a.quantile(2 / 3))]:
                    pp = p[mm]
                    yrs = pd.Series(pp.values, index=pd.to_datetime(pp.index).year).groupby(level=0).mean().round(1).to_dict()
                    res.append(dict(root=root, K=K, exit=xhm, set=lab, cut=cut, n=len(pp), imp=round(a[mm].mean(), 1),
                                    fade=round(pp.mean(), 2), med=round(pp.median(), 2),
                                    t=round(pp.mean() / pp.std(ddof=1) * np.sqrt(len(pp)), 2),
                                    net=round(pp.mean() - rt, 2), years=yrs if lab == "EVENT" else ""))
r = pd.DataFrame(res)
pd.set_option("display.width", 300); pd.set_option("display.max_rows", 500); pd.set_option("display.max_colwidth", 200)
print(r.to_string(index=False))
r.to_csv(f"{OUT}\\cons_macro830_fade.csv", index=False)
