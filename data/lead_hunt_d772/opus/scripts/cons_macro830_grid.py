"""K x exit grid for CPI and EMPSIT separately, NQ and ES; plus the 09:29->11:00 leg signed by the 08:29->08:34 move
(the 'cash open re-prices the release' object) for events and non-event weekdays. In-sample <= 2023."""
import numpy as np, pandas as pd
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"; MICRO = {"NQ": 2.0, "ES": 5.0}
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & ev.event.isin(["CPI", "EMPSIT"]) & (ev.datetime_et.str[11:16] == "08:30")]
et = dict(zip(ev.datetime_et.str[:10], ev.event))
d = pd.read_parquet(f"{OUT}\\cons_globex_0800_1230.parquet"); assert d.session.max() < SEAL
pd.set_option("display.width", 250)
for root, usd in MICRO.items():
    piv = d[d.root == root].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    piv = piv[pd.to_datetime(piv.index).weekday < 5]
    typ = pd.Series([et.get(i, "NONE") for i in piv.index], index=piv.index)
    for grp in ["CPI", "EMPSIT"]:
        tab_m, tab_t = {}, {}
        for K in [1, 3, 5, 10, 15, 30]:
            ehm = f"{8 + (29 + K) // 60:02d}:{(29 + K) % 60:02d}"
            for x in ["09:29", "10:00", "10:30", "11:00", "11:30", "12:00"]:
                imp = piv[ehm] - piv["08:29"]; p = (-np.sign(imp) * (piv[x] - piv[ehm]) * usd)
                p = p[(typ == grp) & p.notna() & (imp != 0)]
                tab_m[(K, x)] = round(p.mean(), 1); tab_t[(K, x)] = round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2)
        print(f"\n{root} {grp} mean $/micro (rows K, cols exit)"); print(pd.Series(tab_m).unstack())
        print(f"{root} {grp} t"); print(pd.Series(tab_t).unstack())
    # decomposition: 08:34->09:29 and 09:29->11:00 legs signed by the 08:29->08:34 impulse
    s = np.sign(piv["08:34"] - piv["08:29"])
    for lab, m in [("EVENT", typ != "NONE"), ("NONEVENT", typ == "NONE")]:
        for a, b in [("08:34", "09:29"), ("09:29", "11:00")]:
            p = (-s * (piv[b] - piv[a]) * usd)[m & (s != 0)].dropna()
            print(root, lab, f"{a}->{b}", len(p), round(p.mean(), 2), round(p.median(), 2), round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2))
