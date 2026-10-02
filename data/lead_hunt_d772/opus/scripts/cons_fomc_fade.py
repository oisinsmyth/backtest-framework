"""Premise: fade the FOMC 14:00 statement impulse on NQ/ES/YM/RTY (rth 1m), 2016..2023 scheduled meetings.
Pre = close 13:59; entry close(13:59+K); exit close X. Placebo = other days same clock. $/micro."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
MICRO = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07), "YM": (0.5, 3.80), "RTY": (5.0, 3.76)}
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & (ev.event == "FOMC") & (ev.datetime_et.str[11:16] == "14:00")]
edays = set(ev.datetime_et.str[:10])
for root in MICRO:
    usd, rt = MICRO[root]
    d = pd.read_csv(f"{FX}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & (d.hhmm >= "13:50")]; assert d.day.max() < SEAL
    piv = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last")
    for K in [1, 5, 15]:
        ehm = f"14:{K-1:02d}"
        for xhm in ["14:45", "15:15", "15:55"]:
            imp = piv[ehm] - piv["13:59"]; pnl = (-np.sign(imp) * (piv[xhm] - piv[ehm]) * usd)
            ok = pnl.notna() & (imp != 0)
            ise = pd.Series(piv.index.isin(list(edays)), index=piv.index)
            for lab, m in [("FOMC", ok & ise), ("PLACEBO", ok & ~ise)]:
                p = pnl[m]
                yrs = pd.Series(p.values, index=pd.to_datetime(p.index).year).groupby(level=0).mean().round(0).to_dict() if lab == "FOMC" else ""
                print(root, K, xhm, lab, len(p), round(p.mean(), 2), round(p.median(), 2),
                      round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2), yrs)
