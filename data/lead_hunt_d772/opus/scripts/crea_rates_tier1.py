"""C18: does Lead 1 transfer to Treasury futures, where the CASH market is OPEN at 08:30? CPI/EMPSIT (events.csv) impulse
x = P(08:30+K) - P(08:30) [P(T) = close of bar T-1]; enter P(08:30+K) against it; exit 09:29 / 10:00 / 11:00 / 12:00.
Placebo: all other weekdays, same clock. $ per MICRO YIELD contract ($10/bp) via a rough points->bp map
(ZT 50 bp/pt, ZF 19, ZN 14, ZB 3.9: duration x price, 2016-23 typical) -- order of magnitude only. Cost ~$4 (unmeasured).
Front = highest-volume contract per (root, day) in the window. 2016-2023 (seal)."""
import numpy as np, pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
df = pd.read_parquet(OUT / "crea_rates_1m.parquet")
assert df.day.max() < "2024-01-01"
ev = pd.read_csv(EVT); ev["d"] = ev.datetime_et.str[:10]; ev["hm"] = ev.datetime_et.str[11:16]
cpi = set(ev[(ev.event == "CPI") & (ev.hm == "08:30")].d); nfp = set(ev[(ev.event == "EMPSIT") & (ev.hm == "08:30")].d)
BPPT = {"ZT": 50.0, "ZF": 19.0, "ZN": 14.0, "ZB": 3.9}
for root, bp in BPPT.items():
    a = df[df.root == root]
    v = a.groupby(["day", "contract"]).volume.sum().reset_index()
    f = v.sort_values(["day", "volume"]).groupby("day").tail(1)[["day", "contract"]]
    a = a.merge(f, on=["day", "contract"])
    P = a.pivot(index="day", columns="m", values="close").reindex(columns=range(480, 726)).ffill(axis=1)
    usd = bp * 10.0
    wd = pd.to_datetime(P.index).dayofweek
    grp = np.where(P.index.isin(cpi), "CPI", np.where(P.index.isin(nfp), "NFP", np.where(wd < 5, "OTHER", "x")))
    print(f"\n== {root} (~${usd:.0f}/pt per micro yield) days {len(P)}")
    t0 = 510
    for K in (1, 3, 5):
        line = []
        for X, lab in [(569, "09:29"), (600, "10:00"), (660, "11:00"), (720, "12:00")]:
            x = P[t0 + K - 1] - P[t0 - 1]; y = P[X - 1] - P[t0 + K - 1]
            fade = -np.sign(x) * y * usd
            ok = np.isfinite(fade) & (x != 0)
            parts = []
            for g in ("CPI", "NFP", "OTHER"):
                s = fade[ok & (grp == g)]
                parts.append(f"{g} n{len(s)} ${s.mean():+.2f} t{s.mean() / s.std() * np.sqrt(len(s)):+.2f}")
            line.append(f"->{lab}: " + ", ".join(parts))
        print(f" K{K}: " + " | ".join(line))
    # year split, K5 -> 11:00, CPI+NFP pooled
    x = P[t0 + 4] - P[t0 - 1]; y = P[659] - P[t0 + 4]
    fade = pd.Series(-np.sign(x) * y * usd, index=P.index)
    s = fade[np.isin(grp, ["CPI", "NFP"]) & np.isfinite(fade) & (x != 0).values]
    print("  K5->11:00 CPI+NFP by year:", s.groupby(s.index.str[:4]).mean().round(1).to_dict(), f"pooled ${s.mean():+.2f} med {s.median():+.2f} n{len(s)}")
