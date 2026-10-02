"""Premise C14: CTA trend-signal flips force predictable execution; does the price give it back afterwards?
Daily closes = last bar of each root's day session in fut_day1m (own-contract returns; roll days carry 0).
CTA position proxy p_t = mean over L in {20,60,120,250} of sign(sum of last L daily returns) (known at close t).
Event: |p_t - p_{t-1}| >= 0.5 (two lookbacks flip the same way, or one flips from 0). Direction D = sign(dp).
Report the day-session-close returns on t+1 (execution day: should follow D), t+2, t+3 (should revert), in $ per micro.
The tradeable reversion: enter at the t+1 close (proxy for the 18:00 reopen), fade D, exit at the t+2 close.
2010-2023 where the root is clean; seal asserted.
"""
import numpy as np, pandas as pd, pyarrow.parquet as pq

FIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_day1m.parquet"
SEAL = "2024-01-01"
R = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07), "YM": (0.5, 3.80), "RTY": (5.0, 3.76), "GC": (10.0, 5.93), "SI": (1000.0, 8.0),
     "HG": (2500.0, 4.25), "CL": (100.0, 5.03), "NG": (1000.0, 4.0), "6E": (12500.0, 4.38)}
t = pq.read_table(FIX, filters=[("root", "in", list(R)), ("day", "<", SEAL)],
                  columns=["root", "day", "bar", "close", "contract", "present"]).to_pandas()
assert t.day.max() < SEAL
t = t[t.present]
last = t.sort_values("bar").groupby(["root", "day"]).tail(1).sort_values(["root", "day"])
rows = []
for root, g in last.groupby("root"):
    usd, rt = R[root]
    g = g.reset_index(drop=True)
    same = g.contract.eq(g.contract.shift(1))
    dpx = (g.close - g.close.shift(1)).where(same)  # points, own contract
    ret = np.log(g.close / g.close.shift(1)).where(same).fillna(0.0)
    p = sum(np.sign(ret.rolling(L, min_periods=L).sum()) for L in (20, 60, 120, 250)) / 4.0
    dp = p.diff()
    ev = (dp.abs() >= 0.5) & p.notna() & p.shift(1).notna()
    D = np.sign(dp)
    for k in (1, 2, 3):
        g[f"d{k}"] = dpx.shift(-k)
    g["D"] = D; g["ev"] = ev; g["root"] = root; g["usd"] = usd
    g["sd20"] = dpx.rolling(20).std()
    rows.append(g[g.ev & (g.day >= "2011-01-01")])
E = pd.concat(rows)
print("events per root:", E.groupby("root").size().to_dict(), "span", E.day.min(), E.day.max())
for root, g in E.groupby("root"):
    out = []
    for k in (1, 2, 3):
        pnl = (g.D * g[f"d{k}"] * g.usd).dropna()
        out.append(f"t+{k} follow ${pnl.mean():+7.2f} (t {pnl.mean() / pnl.std() * np.sqrt(len(pnl)):+.2f})")
    fade2 = (-g.D * g.d2 * g.usd).dropna()
    print(f"{root:4s} n={len(g):3d} ({len(g) / 13:.0f}/yr) " + " | ".join(out) + f" || FADE t+2 ${fade2.mean():+.2f} med {fade2.median():+.2f}")
E["fade2"] = -E.D * E.d2 * E.usd
E["f1"] = E.D * E.d1 * E.usd
print("pooled fade t+2 by year:", E.groupby(E.day.str[:4]).fade2.mean().round(2).to_dict())
print("pooled follow t+1 by year:", E.groupby(E.day.str[:4]).f1.mean().round(2).to_dict())
# placebo: random days, same roots: the unconditional mean of -sign(ret_t) * ret_{t+2}? report the D-signed t+2 on non-event days
