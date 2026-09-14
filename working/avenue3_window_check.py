"""Is the ZERO group's huge "close reversion" an effect, or is the window outside its session?

The avenue-3 test found hit 46.3% (z = -12.6) in the 19 roots with no leveraged-ETF complex, i.e.
strong REVERSION into 15:59 -- and nothing at all (50.03%, z = +0.1) in the US equity index where the
mechanism predicts the effect. Before reading that as a finding, note LE returned n = 20 and HE
n = 13 against ~1,900 for the equity roots. That is not a thin root; that is a root whose SESSION
ENDS BEFORE THE WINDOW. Grains close 14:20 ET, livestock 14:05, COMEX metals 13:30.

A "close" measured in a root's illiquid tail bounces on the spread, and bid-ask bounce looks exactly
like reversion. This measures whether the 15:00-15:59 window is liquid for each root, so the earlier
table can be read correctly.

    python working/avenue3_window_check.py
"""
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
LO, HI = "2016-01-04", "2023-12-29"
HIGH = ["ES", "NQ", "RTY", "YM"]
MED = ["CL", "NG", "GC", "SI", "HG", "ZN", "ZB"]

G = pd.read_parquet(REPO / "data" / "fixtures" / "fut_day5m.parquet")
G = G[(G["day"] >= LO) & (G["day"] <= HI)]
G = G[G["present"].astype(str).str.lower().isin(("true", "1")) &
      G["same_front"].astype(str).str.lower().isin(("true", "1"))]
G["grp"] = np.where(G["root"].isin(HIGH), "HIGH", np.where(G["root"].isin(MED), "MED", "ZERO"))
G["late"] = G["bar"] >= 72          # 15:00 ET onward

vol = G.groupby(["root", "grp", "late"])["volume"].sum().unstack(fill_value=0)
n = G.groupby(["root", "grp", "late"]).size().unstack(fill_value=0)
d = pd.DataFrame({"vol_early": vol.get(False, 0), "vol_late": vol.get(True, 0),
                  "bars_early": n.get(False, 0), "bars_late": n.get(True, 0)}).reset_index()
d["late_vol_share"] = d["vol_late"] / (d["vol_early"] + d["vol_late"]).replace(0, np.nan)
# 12 of 84 bars are 15:00-15:59, so a root trading evenly would show 12/84 = 14.3%
d["vs_even"] = d["late_vol_share"] / (12 / 84)
d = d.sort_values(["grp", "late_vol_share"])

print("Share of the session's VOLUME that trades in 15:00-15:59 ET.")
print("12 of 84 bars are in that window, so an evenly-traded root reads 14.3% and vs_even = 1.00.\n")
print(f"  {'root':<6}{'grp':<6}{'late vol share':>16}{'vs even':>10}{'bars late':>11}{'sessions':>10}")
for r in d.itertuples():
    flag = "   <-- window is OUTSIDE this root's session" if r.late_vol_share < 0.05 else ""
    print(f"  {r.root:<6}{r.grp:<6}{100*r.late_vol_share:>15.2f}%{r.vs_even:>10.2f}{r.bars_late:>11,}"
          f"{r.bars_late//12:>10,}{flag}")

print("\nby group:")
for g, x in d.groupby("grp"):
    bad = int((x["late_vol_share"] < 0.05).sum())
    print(f"  {g:<6} {len(x):>2} roots, median late-volume share {100*x['late_vol_share'].median():>6.2f}%, "
          f"{bad} of {len(x)} with the window essentially OUTSIDE their session")
