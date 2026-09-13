"""STAGE 0 for component #2: at minimum tradable size, what fraction of the day-session move does a
round trip cost — on every root whose contract spec is CME-verified?

WHY THIS FIRST. The story on the table is "stop paying the queue rent on ZN and join instead". That
story is only NECESSARY if no root is affordable as a TAKER. D473/D493 fixed the arithmetic that
decides a prop component -- gross per session must be several ticks against the round trip -- and
D515 found NQ wins on TWO counts at once: the largest day-session edge AND the cheapest cost
relative to its move (3.2% against 6.3% for the next best). That 3.2% has never been tabulated
across the wider root list. If several roots sit near NQ's ratio, a PORTABLE TAKER component is
available and the maker route is a luxury. If none do, the maker route is forced.

NO RETURN IS READ AS A P&L. This computes the average size of the day-session move and the cost of
trading it. It takes no position, applies no signal and scores no strategy (R15).

  cost_rt   = commission_rt + crossing_ticks * tick_usd        the repo's convention, D504's arm
  E|move|   = mean | h15_c - h09_o | * usd_per_point           the day session the arm trades
  ratio     = cost_rt / E|move|                                 NQ reads 3.2% via MNQ

WINDOW: 2016-01-04 .. 2023-12-29, the D462 usable in-sample window. 2024-01 onward is RESERVED and
is NOT READ here.

    python working/stage0_taker_affordability.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures"
SPECS = json.loads((REPO / "data" / "futures_contract_specs.json").read_text())

LO, HI = "2016-01-04", "2023-12-29"          # in sample; 2024+ reserved and not read
COMMISSION_RT = 3.00                          # the repo's convention (D504: $3 + 1.009 ticks = $3.50 on MNQ)
CROSS_TICKS = 1.009                           # measured, scale-free (D485/D504)
CD_BAR = 500.0                                # C-d: daily sigma at minimum size <= 1% of a $50k account
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K", "6E": "M6E", "CL": "MCL", "GC": "MGC"}


def spec(root):
    d = SPECS.get(root)
    if not isinstance(d, dict) or "tick_usd" not in d or "usd_per_point" not in d:
        return None
    return float(d["tick_usd"]), float(d["usd_per_point"])


def main():
    B = pd.read_csv(FIX / "fut_breadth_hourly.csv.gz",
                    usecols=["root", "day", "contract", "same_front", "present", "h09_o", "h15_c"],
                    dtype={"root": str, "day": str, "contract": str})
    n0 = len(B)
    B = B[(B["day"] >= LO) & (B["day"] <= HI)]
    B = B[B["present"].astype(str).str.lower().isin(("true", "1")) &
          B["same_front"].astype(str).str.lower().isin(("true", "1"))]
    B = B.dropna(subset=["h09_o", "h15_c"])
    B = B[(B["h09_o"] > 0) & (B["h15_c"] > 0)]
    print(f"breadth fixture {n0:,} rows -> {len(B):,} in-sample present same-front sessions, "
          f"{B['root'].nunique()} roots, {B['day'].min()} .. {B['day'].max()}\n")
    assert B["day"].max() <= HI, "[WINDOW] the reserved slice was read"

    rows = []
    for root, g in B.groupby("root", sort=True):
        sp = spec(root)
        if sp is None:
            rows.append(dict(root=root, sessions=len(g), status="spec not CME-verified"))
            continue
        # minimum tradable size: the micro where one exists in the verified file, else the full contract
        m = MICRO.get(root)
        traded, tick_usd, mult = (m, *spec(m)) if (m and spec(m)) else (root, *sp)
        move_pts = (g["h15_c"].to_numpy(float) - g["h09_o"].to_numpy(float))
        e_move_usd = float(np.mean(np.abs(move_pts)) * mult)
        sigma_usd = float(np.std(move_pts, ddof=1) * mult)          # C-d is a sigma bar, not a mean bar
        e_move_ticks = e_move_usd / tick_usd
        cost = COMMISSION_RT + CROSS_TICKS * tick_usd
        rows.append(dict(root=root, traded=traded, sessions=len(g), tick_usd=tick_usd,
                         e_move_usd=e_move_usd, e_move_ticks=e_move_ticks, sigma_usd=sigma_usd,
                         cost_rt=cost, ratio=cost / e_move_usd, cd_pass=bool(sigma_usd <= CD_BAR),
                         status="ok"))
    d = pd.DataFrame(rows)
    ok = d[d.status == "ok"].sort_values("ratio").reset_index(drop=True)
    # the mixed frame makes cd_pass an object column, and `~` on object bools returns -1/-2, both truthy
    ok["cd_pass"] = ok["cd_pass"].astype(bool)
    bad = d[d.status != "ok"]

    print(f"{'root':<5}{'traded':<8}{'tick $':>8}{'E|move| $':>11}{'ticks':>8}{'cost $':>8}{'cost/move':>10}{'sigma $':>10}  C-d")
    for r in ok.itertuples():
        flag = "  <-- the admitted arm" if r.root == "NQ" else ""
        print(f"{r.root:<5}{r.traded:<8}{r.tick_usd:>8.2f}{r.e_move_usd:>11,.2f}"
              f"{r.e_move_ticks:>8.1f}{r.cost_rt:>8.2f}{100*r.ratio:>9.1f}%{r.sigma_usd:>10,.0f}"
              f"  {'PASS' if r.cd_pass else 'FAIL'}{flag}")
    if len(bad):
        print(f"\nno CME-verified spec, not scored ({len(bad)}): {sorted(bad['root'])}")

    nq = float(ok.loc[ok.root == "NQ", "ratio"].iloc[0]) if (ok.root == "NQ").any() else np.nan
    print(f"\nNQ reads {100*nq:.1f}% (D515 quotes 3.2% on a slightly different window/definition)")
    within2 = ok[ok.ratio <= 2 * nq]
    print(f"roots within 2x of NQ's ratio: {len(within2)} -> {list(within2.root)}")
    both = ok[(ok.ratio <= 0.10) & ok.cd_pass]
    print(f"\nBOTH cheap (cost/move <= 10%) AND expressible (C-d): {len(both)} -> {list(both.root)}")
    print(f"cheap but NOT expressible at any size we hold:        {list(ok[(ok.ratio <= 0.10) & ~ok.cd_pass].root)}")
    print("\nthe fee-and-barrier identity, restated: a root is cheap BECAUSE it moves,")
    print("and it fails C-d for the same reason. The micro is what breaks the tie.")
    print(f"  corr(log cost ratio, log sigma) = {np.corrcoef(np.log(ok.ratio), np.log(ok.sigma_usd))[0,1]:+.3f}")
    ok.to_csv(REPO / "working" / "stage0_taker_affordability.csv", index=False)


if __name__ == "__main__":
    main()
