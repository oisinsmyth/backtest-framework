"""Premise test E: the Shanghai (SHFE) day-session CLOSE at 15:00 Beijing (07:00 UTC) and night close 02:30 Beijing (18:30 UTC)
on COMEX GC / SI / HG, 2016-2023. Mechanism: SHFE day traders must flatten before the close (close-today fee structure,
no overnight for intraday accounts); the arbitrage transmits their flattening to COMEX; the move INTO the close reverts
AFTER it. Controls: the same test at placebo UTC clocks (05:00, 06:00, 09:00), Chinese exchange holidays (no SHFE
session), and the DST split (the London open sits at 07:00 UTC only in summer).

    python crea_05_shfe_close.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_clocklib import clock_test, fmt

FIX = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/fixtures")
REPO = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/.claude/worktrees/after-d674")
OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"GC": 10.0, "SI": 1000.0, "HG": 2500.0}      # $ per point, one micro (MGC 10oz, SIL 1000oz, MHG 2500lb)
COST = {"GC": 5.93, "SI": 8.00, "HG": 4.25}


def load(root):
    f = "fut_opening_globex_1m_cl_ng_gc_si.csv.gz" if root in ("GC", "SI") else "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz"
    chunks = []
    for ch in pd.read_csv(FIX / f, usecols=["root", "session", "et", "contract", "close"], chunksize=2_000_000):
        ch = ch[(ch["root"] == root) & (ch["session"] >= "2016-01-01") & (ch["session"] <= "2023-12-31")]
        chunks.append(ch)
    d = pd.concat(chunks, ignore_index=True)
    d["et"] = pd.to_datetime(d["et"])
    d = d[(d["et"] >= "2015-12-31") & (d["et"] < "2024-01-01")]
    assert d["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    d = d.rename(columns={"session": "day"})
    return d[["root", "day", "et", "contract", "close"]]


def main():
    hol = pd.read_csv(REPO / "data/calendar/china_exchange_holidays.csv")["date"].tolist()
    res = {}
    for root in ["GC", "SI", "HG"]:
        d = load(root)
        print(root, len(d), d["day"].min(), d["day"].max(), flush=True)
        R = []
        for clock, lab in [("07:00", "SHFE day close 15:00 BJ"), ("18:30", "SHFE night close 02:30 BJ"), ("01:00", "SHFE open 09:00 BJ (ref D765)"),
                           ("05:00", "placebo 05:00 UTC"), ("06:00", "placebo 06:00 UTC"), ("09:00", "placebo 09:00 UTC"), ("03:30", "SHFE lunch 11:30 BJ")]:
            for pre, post in [(30, 30), (30, 60), (15, 30)]:
                r = clock_test(d, clock, "UTC", pre, post, MULT[root], COST[root], exclude_days=hol, label=f"{root} {lab} pre{pre}/post{post}")
                R.append(r); print(fmt(r), flush=True)
            if clock == "07:00":
                # on Chinese holidays (control: no SHFE session)
                dh = d[d["day"].isin(set(hol))]
                r = clock_test(dh, clock, "UTC", 30, 30, MULT[root], COST[root], label=f"{root} {lab} CN-HOLIDAY control pre30/post30")
                R.append(r); print(fmt(r), flush=True)
                # top-half |x| only
                r = clock_test(d, clock, "UTC", 30, 30, MULT[root], COST[root], exclude_days=hol, min_abs_x=0.5, label=f"{root} {lab} top-half |x| pre30/post30")
                R.append(r); print(fmt(r), flush=True)
                # DST split: summer (EDT) vs winter (EST) -- London open coincides in summer
                summer = d[(d["et"].dt.month >= 4) & (d["et"].dt.month <= 10)]
                winter = d[(d["et"].dt.month <= 2) | (d["et"].dt.month == 12)]
                for nm, dd in [("summer(Apr-Oct)", summer), ("winter(Dec-Feb)", winter)]:
                    r = clock_test(dd, clock, "UTC", 30, 30, MULT[root], COST[root], exclude_days=hol, label=f"{root} {lab} {nm} pre30/post30")
                    R.append(r); print(fmt(r), flush=True)
        res[root] = R
    (OUT / "crea_05_shfe_close.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()
