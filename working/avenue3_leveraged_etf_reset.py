"""AVENUE 3, STAGE 0 -- is the close-continuation effect LEVERAGED-ETF REBALANCING, or generic momentum?

THE MECHANISM. A leveraged ETF must reset exposure to a fixed multiple of that day's CLOSING NAV.
For leverage L and assets A, after an index move r the required rebalance trade is

        trade = A x L x (L - 1) x r

which is POSITIVE for L = +3 (6Ar) and ALSO positive for L = -3 (12Ar): both the long and the
inverse fund BUY after an up day and SELL after a down day. The participant is forced by its own
prospectus, cannot decline, cannot wait, and its size is a deterministic function of a number
everyone can observe in real time. The hedge lands in index futures.

WHY THIS IS NOT JUST D463. D463 tested the trade UNCONDITIONALLY -- sign of return-of-day, 15:30
open -> 16:00 print -- and the ledger scored it dead on cost (K2/K3/K4: NQ gross +$0.66, ES +$0.62,
YM +$0.08 against $3.50). The mechanism makes two predictions that test were not built to see:

  P1  DOSE-RESPONSE IN MAGNITUDE. Flow is LINEAR in r, so continuation should strengthen with
      |return-of-day|. Generic momentum has no such requirement.
  P2  DOSE-RESPONSE ACROSS ROOTS. The flow exists only where a leveraged ETF complex trades that
      future. If continuation is just as strong in soybeans and the euro as in the S&P, the
      mechanism is NOT the explanation.

GROUPS ARE DECLARED HERE, BEFORE THE RUN, and not revised afterwards:
  HIGH  ES NQ RTY YM            US equity index: the largest leveraged-ETP complexes exist here
  MED   CL NG GC SI HG ZN ZB    known leveraged ETPs (UCO/SCO, BOIL/KOLD, UGL/GLL, AGQ/ZSL, TMF/TMV)
  ZERO  the six FX, five grains, livestock, SR3 TN UB ZF ZT PA PL BZ HO RB NKD
  (BTC excluded from the grouping: 2x bitcoin ETPs are recent and the root's history is short.)

A NAMED CONFOUND. "Concentrated in equity index" does NOT uniquely identify this mechanism -- the
equity close also carries MOC imbalance and index-tracking flow. P1 is the sharper discriminator,
because leveraged-ETF flow is linear in r with a known constant and MOC imbalance is not.

Reported in HIT RATE terms, because D529 established this book is paid for accuracy, not shape.
NO P&L is claimed; gross per trade is shown against the D527-corrected cost for scale only (R15).
In sample 2016-01-04..2023-12-29; the 2024+ slice is NOT read.

    python working/avenue3_leveraged_etf_reset.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
SPECS = json.loads((REPO / "data" / "futures_contract_specs.json").read_text())
LO, HI = "2016-01-04", "2023-12-29"
BAR_MIN = 5
OPEN_BAR = {"equity": 6}          # 09:30 ET = bar 6 (bars start 09:00); commodities trade from 09:00
HIGH = ["ES", "NQ", "RTY", "YM"]
MED = ["CL", "NG", "GC", "SI", "HG", "ZN", "ZB"]
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K", "6E": "M6E", "CL": "MCL", "GC": "MGC"}


def group_of(r):
    return "HIGH" if r in HIGH else ("MED" if r in MED else ("BTC" if r == "BTC" else "ZERO"))


def main():
    G = pd.read_parquet(FIX / "fut_day5m.parquet")
    G = G[(G["day"] >= LO) & (G["day"] <= HI)]
    G = G[G["present"].astype(str).str.lower().isin(("true", "1")) &
          G["same_front"].astype(str).str.lower().isin(("true", "1"))]
    print(f"day5m: {len(G):,} bars, {G['root'].nunique()} roots, {G['day'].nunique():,} sessions "
          f"in {LO}..{HI}\n")

    rows = []
    for T_bar, label in ((72, "15:00"), (78, "15:30")):
        piv_o = G.pivot_table(index=["root", "day"], columns="bar", values="open", aggfunc="first")
        piv_c = G.pivot_table(index=["root", "day"], columns="bar", values="close", aggfunc="last")
        need = [b for b in (6, T_bar, T_bar + 1, 83) if b in piv_o.columns and b in piv_c.columns]
        if len(need) < 4:
            print(f"  {label}: missing bars, skipped")
            continue
        o_open = piv_o[6].to_numpy(float)          # 09:30 open (equity RTH open; commodities already trading)
        c_T = piv_c[T_bar].to_numpy(float)         # the close of bar T -- the decision point
        o_next = piv_o[T_bar + 1].to_numpy(float)  # fill at the NEXT bar's open: no look-ahead
        c_end = piv_c[83].to_numpy(float)          # the 15:55 bar's close = the session's last print
        idx = piv_o.index
        ok = np.isfinite(o_open) & np.isfinite(c_T) & np.isfinite(o_next) & np.isfinite(c_end) & \
             (o_open > 0) & (c_T > 0) & (o_next > 0) & (c_end > 0)
        rod = np.where(ok, np.log(c_T / o_open), np.nan)           # return of day to T
        fwd = np.where(ok, np.log(c_end / o_next), np.nan)         # T -> close, entered at the next open
        d = pd.DataFrame({"root": idx.get_level_values(0), "day": idx.get_level_values(1),
                          "rod": rod, "fwd": fwd})[ok]
        d["grp"] = d["root"].map(group_of)
        d["dir"] = np.sign(d["rod"])
        d = d[d["dir"] != 0]
        d["hit"] = (np.sign(d["fwd"]) == d["dir"]).astype(float)
        d["T"] = label
        rows.append(d)
    D = pd.concat(rows, ignore_index=True)

    for label, dd in D.groupby("T"):
        print("=" * 92)
        print(f"T = {label}: trade the sign of the day's move so far, entered at the next bar's open, "
              f"held to the session's last print")
        print(f"\n  [P2] BY GROUP -- the identification. If ZERO matches HIGH, this is not ETF rebalancing.")
        print(f"  {'group':<7}{'roots':>7}{'n':>10}{'hit %':>9}{'SE':>7}{'z vs 50%':>10}")
        for g in ("HIGH", "MED", "ZERO"):
            x = dd[dd.grp == g]
            if not len(x):
                continue
            h = x["hit"].mean(); n = len(x); se = np.sqrt(0.25 / n)
            print(f"  {g:<7}{x['root'].nunique():>7}{n:>10,}{100*h:>8.2f}%{100*se:>7.2f}{(h-0.5)/se:>10.1f}")

        print(f"\n  [P1] DOSE-RESPONSE IN |return of day|, within each group. Flow is LINEAR in r,")
        print(f"       so the hit rate should RISE with the quintile if the mechanism is real.")
        print(f"  {'group':<7}" + "".join(f"{('Q'+str(q)):>9}" for q in range(1, 6)) + f"{'Q5-Q1':>9}")
        for g in ("HIGH", "MED", "ZERO"):
            x = dd[dd.grp == g].copy()
            if len(x) < 500:
                continue
            x["q"] = x.groupby("root")["rod"].transform(lambda s: pd.qcut(s.abs(), 5, labels=False, duplicates="drop"))
            hs = [x[x.q == q]["hit"].mean() for q in range(5)]
            print(f"  {g:<7}" + "".join(f"{100*h:>8.2f}%" for h in hs) + f"{100*(hs[4]-hs[0]):>8.2f}%")

        print(f"\n  BY ROOT within HIGH and the top of ZERO (hit %, n):")
        per = dd.groupby("root").agg(n=("hit", "size"), hit=("hit", "mean"), grp=("grp", "first"))
        per["z"] = (per["hit"] - 0.5) / np.sqrt(0.25 / per["n"])
        show = pd.concat([per[per.grp == "HIGH"].sort_values("z", ascending=False),
                          per[per.grp == "ZERO"].sort_values("z", ascending=False).head(6)])
        for r, v in show.iterrows():
            print(f"    {r:<5} {v.grp:<5} n {int(v.n):>6,}  hit {100*v.hit:>6.2f}%  z {v.z:>+6.2f}")
    print("=" * 92)


if __name__ == "__main__":
    main()
