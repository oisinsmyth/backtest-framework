"""Family test for Lead 3 (gold weekend reopen): every breadth root with a CME micro, hourly fixture.
Monday sessions only (and Tue-Fri placebo). m = h18_c (Sunday/evening 18:00-18:59 close) - previous session h16_c.
Fade from h18_c to h02_c (03:00 print), h09_c (10:00 print). same_front required on both sessions.
$/micro: micro spec from data/futures_costs.json where listed, else full/10 with RT = 3 + full tick/10.
In-sample: day < 2024-01-01, from 2016."""
import json, numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
COST = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\futures_costs.json"
SEAL = "2024-01-01"
ROOTS = ["ES", "NQ", "YM", "RTY", "GC", "SI", "HG", "PL", "CL", "NG", "6E", "6A", "6B", "6J", "6C", "6S", "BTC", "ZN", "ZB"]
c = json.load(open(COST, encoding="utf-8"))["roots"]
spec = {}
for r in ROOTS:
    e = c[r]
    if "micro" in e:
        m = e["micro"]; rt = m["commission_rt_usd"]["value"] + m["crossing_ticks_rt"][m["default_line"]]["value"] * m["tick_usd"]
        spec[r] = (m["usd_per_point"], rt, m["symbol"])
    else:
        f = e["full"]; spec[r] = (f["usd_per_point"] / 10, 3.0 + f["tick_usd"] / 10, r + "/10")
cols = ["root", "day", "same_front", "h18_c", "h02_c", "h09_c", "h16_c"]
parts = []
for ch in pd.read_csv(f"{FX}\\fut_breadth_hourly.csv.gz", usecols=cols, chunksize=500_000):
    parts.append(ch[ch.root.isin(ROOTS) & (ch.day >= "2015-12-01") & (ch.day < SEAL)])
d = pd.concat(parts); assert d.day.max() < SEAL
rows = []
for r, g in d.groupby("root"):
    g = g.dropna(subset=["h16_c"]).sort_values("day").copy()  # drop placeholder rows with no close
    g["prev16"] = g.h16_c.shift(1); g["prevfront"] = g.same_front.shift(1)
    g = g[(g.day >= "2016-01-01") & g.same_front]
    wd = pd.to_datetime(g.day).dt.weekday
    m = g.h18_c - g.prev16
    usd, rt, sym = spec[r]
    for x in ["h02_c", "h09_c"]:
        pnl = -np.sign(m) * (g[x] - g.h18_c) * usd
        ok = pnl.notna() & (m != 0)
        for lab, mm in [("MON", ok & (wd == 0)), ("TUE-FRI", ok & (wd > 0))]:
            q = pnl[mm]; yy = pd.to_datetime(g.day[mm]).dt.year.values
            if len(q) < 30: continue
            rows.append(dict(root=r, sym=sym, rt=round(rt, 2), exit=x[:3], grp=lab, n=len(q), mean=round(q.mean(), 2),
                             med=round(q.median(), 2), t=round(q.mean() / q.std(ddof=1) * np.sqrt(len(q)), 2),
                             x_cost=round(q.mean() / rt, 2), posyrs=int((pd.Series(q.values).groupby(yy).mean() > 0).sum()),
                             ex20=round(q[yy != 2020].mean(), 2)))
out = pd.DataFrame(rows); pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print(out.to_string(index=False))
