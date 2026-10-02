"""Main session's independent check of the Opus pair's Lead 1 (CPI/NFP 08:30 fade on MNQ), written without reading
their code beyond its data sources. Impulse = close(08:34 bar) - close(08:29 bar); fade from close(08:34) to
close(11:00); $2 per NQ point (MNQ). One contract per session window, asserted. In-sample sessions < 2024-01-01."""
import math

import numpy as np
import pandas as pd

ROOT = "C:/Users/O/Desktop/Projects/Backtest Framework"
EVT = ROOT + "/.claude/worktrees/after-d674/data/calendar/events.csv"
SEAL = "2024-01-01"
USD, RT = 2.0, 4.07

ev = pd.read_csv(EVT, encoding="utf-8")
ev = ev[(ev["datetime_et"] < SEAL) & ev["event"].isin(["CPI", "EMPSIT"]) & (ev["datetime_et"].str[11:16] == "08:30")]
kind = dict(zip(ev["datetime_et"].str[:10], ev["event"]))

need = {"08:29", "08:34", "11:00"}
rows = []
for ch in pd.read_csv(ROOT + "/data/fixtures/fut_opening_globex_1m.csv.gz", chunksize=2_000_000,
                      usecols=["root", "session", "et", "hhmm", "contract", "close"]):
    ch = ch[(ch["root"] == "NQ") & (ch["session"] >= "2016-01-01") & (ch["session"] < SEAL) & ch["hhmm"].isin(need)]
    ch = ch[ch["et"].str[:10] == ch["session"]]
    rows.append(ch)
d = pd.concat(rows)
assert d["session"].max() < SEAL
px = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
ct = d.groupby("session")["contract"].nunique()
px = px[(ct.reindex(px.index) == 1).to_numpy()].dropna()
imp = px["08:34"] - px["08:29"]
pnl = -np.sign(imp) * (px["11:00"] - px["08:34"]) * USD
pnl = pnl[imp != 0]
wd = pd.to_datetime(pnl.index).weekday < 5
isev = pnl.index.isin(list(kind))

def stats(p: pd.Series) -> str:
    return (f"n {len(p)}, mean {p.mean():+.2f}, median {p.median():+.2f}, t {p.mean() / p.std(ddof=1) * math.sqrt(len(p)):.2f}, "
            f"net {p.mean() - RT:+.2f}, trimmed1% {p.sort_values().iloc[int(len(p)*.01):len(p)-int(len(p)*.01)].mean():+.2f}")

e = pnl[isev & wd]
print("EVENTS  ", stats(e))
print("PLACEBO ", stats(pnl[~isev & wd]))
print("by year ", e.groupby(pd.to_datetime(e.index).year).mean().round(2).to_dict())
print("CPI     ", stats(e[[kind[s] == "CPI" for s in e.index]]))
print("EMPSIT  ", stats(e[[kind[s] == "EMPSIT" for s in e.index]]))
print("top trade", e.idxmax(), round(e.max(), 2), "| worst", e.idxmin(), round(e.min(), 2))

# data cross-check: the 11:00 close against the separate RTH file, same day and contract
rth = pd.read_csv(ROOT + "/data/fixtures/fut_NQ_rth_1m.csv.gz", usecols=["day", "hhmm", "contract", "close"])
rth = rth[(rth["hhmm"] == "11:00") & rth["day"].isin(e.index)].set_index("day")["close"]
both = px.loc[e.index, "11:00"].to_frame("g").join(rth.rename("r"), how="inner")
print("11:00 close agreement with fut_NQ_rth_1m:", int((both["g"] == both["r"]).sum()), "of", len(both))
