"""Premise: does the EIA 10:30 release impulse revert (fade) on CL / NG, in $ per one micro?
In-sample <= 2023-12-31 only. fut_day1m bars: bar index = minutes since 09:00 ET, bar-start stamped.
Pre price = close of the 10:29 bar (bar 89). Impulse = close(bar 89+K) - pre. Entry at close(89+K).
Exit at close of bar X. Fade pnl = -sign(impulse)*(exit-entry)*usd_per_point_micro.
Placebo: same clock on non-report weekdays.
"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq

FIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_day1m.parquet"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
MICRO = {"CL": (100.0, 5.03), "NG": (1000.0, 4.00)}
EVNAME = {"CL": "EIA_WPSR", "NG": "EIA_NGSR"}

ev = pd.read_csv(EVT)
ev["d"] = ev["datetime_et"].str[:10]
ev["hm"] = ev["datetime_et"].str[11:16]

def bar_of(hm):
    h, m = map(int, hm.split(":")); return (h * 60 + m) - 540

out = []
for root in ["CL", "NG"]:
    t = pq.read_table(FIX, filters=[("root", "=", root), ("day", "<", SEAL), ("day", ">=", "2016-01-01")],
                      columns=["day", "bar", "close", "same_front", "present"]).to_pandas()
    assert t["day"].max() < SEAL
    t = t[t["same_front"]]
    piv = t.pivot_table(index="day", columns="bar", values="close", aggfunc="last")
    e = ev[(ev["event"] == EVNAME[root]) & (ev["d"] < SEAL)]
    edays = dict(zip(e["d"], e["hm"]))
    usd, rt = MICRO[root]
    days = pd.to_datetime(piv.index)
    for K in [1, 2, 5]:
        for xhm in ["10:45", "11:00", "11:30", "12:30", "14:15"]:
            rows = []
            for i, d in enumerate(piv.index):
                is_ev = d in edays
                hm = edays.get(d, "10:30")
                if is_ev and hm != "10:30":
                    continue  # shifted release clocks: skip for simplicity
                b0 = bar_of("10:30") - 1
                bx = bar_of(xhm)
                row = piv.iloc[i]
                pre, ent, ex = row.get(b0), row.get(b0 + K), row.get(bx)
                if not (np.isfinite(pre) and np.isfinite(ent) and np.isfinite(ex)):
                    continue
                imp = ent - pre
                if imp == 0:
                    continue
                pnl = -np.sign(imp) * (ex - ent) * usd
                rows.append((d, is_ev, abs(imp) * usd, pnl, days[i].weekday()))
            r = pd.DataFrame(rows, columns=["d", "ev", "imp", "pnl", "wd"])
            for lab, sub in [("EVENT", r[r.ev]), ("PLACEBO", r[~r.ev & r.wd.isin([0, 1, 2, 3, 4])])]:
                if len(sub) < 10:
                    continue
                q = sub["imp"].quantile([0.5, 0.8]).values
                for qlab, ss in [("all", sub), ("top50", sub[sub.imp >= q[0]]), ("top20", sub[sub.imp >= q[1]])]:
                    p = ss["pnl"]
                    out.append(dict(root=root, K=K, exit=xhm, set=lab, cut=qlab, n=len(p),
                                    imp_mean=round(ss["imp"].mean(), 2), fade_mean=round(p.mean(), 2),
                                    fade_med=round(p.median(), 2), t=round(p.mean() / p.std(ddof=1) * np.sqrt(len(p)), 2),
                                    net=round(p.mean() - rt, 2)))
res = pd.DataFrame(out)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
print(res.to_string(index=False))
res.to_csv(r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out\cons_eia_fade.csv", index=False)
