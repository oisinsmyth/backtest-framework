"""T10c: name the top and bottom 10 trades of the vol-gated (>= $80) SIL post-settlement fade, the monthly clustering,
and the book's daily-P&L Sharpe/Sortino (net at $8 and $13), max drawdown, worst 30-day window, exposure."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *
d = load_day1m(["SI"]); d = d[d.present & d.same_front]
g = d.pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3)
def pr(m): return g[m - 541].to_numpy()
f = pd.DataFrame({"day": list(g.index), "x": (pr(13 * 60 + 25) - pr(12 * 60 + 55)) * 1000, "y60": (pr(14 * 60 + 25) - pr(13 * 60 + 25)) * 1000}).dropna()
f["gate"] = f.y60.rolling(20).std().shift(1); f["fade"] = -np.sign(f.x) * f.y60
on = f[f.gate >= 80].copy()
print("top 10:"); print(on.nlargest(10, "fade")[["day", "x", "y60", "fade", "gate"]].to_string())
print("bottom 10:"); print(on.nsmallest(10, "fade")[["day", "x", "y60", "fade", "gate"]].to_string())
on["ym"] = on.day.str[:7]
mc = on.groupby("ym").fade.agg(["count", "sum"]).sort_values("sum", ascending=False)
print("top months:"); print(mc.head(8).to_string()); print("bottom months:"); print(mc.tail(5).to_string())
tot = on.fade.sum(); print("top month share", round(mc["sum"].max() / tot, 3), "top 3 months share", round(mc["sum"].head(3).sum() / tot, 3))
for cost in (8.0, 13.0):
    daily = pd.Series(0.0, index=f.day); daily.loc[on.day] = on.fade.to_numpy() - cost
    yrs = daily.index.str[:4]
    ann = daily.groupby(yrs).sum()
    eq = daily.cumsum(); dd = (eq - eq.cummax()).min()
    down = daily[daily < 0]
    sharpe = daily.mean() / daily.std() * np.sqrt(252) if daily.std() > 0 else np.nan
    sortino = daily.mean() / np.sqrt((down ** 2).sum() / len(daily)) * np.sqrt(252)
    worst30 = daily.rolling(30).sum().min()
    print(f"cost {cost}: net total {daily.sum():.0f}, Sharpe {sharpe:.2f}, Sortino {sortino:.2f}, maxDD {dd:.0f}, worst 30d {worst30:.0f}, exposure {len(on)/len(f):.3f}, net by year {ann.round(0).to_dict()}")
