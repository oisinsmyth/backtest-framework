"""D266 CROSS-SCREEN -- R12 applied: does anything from D247/D264/D265 reach the
prop track?

    uv run python scripts/d266_prop_cross_screen.py

R12 REQUIRES THIS, and it requires it in a specific form: "a candidate that fails
one track's standards is screened against the other's BEFORE it is closed", and
"a cross-screen must RE-COST, not merely re-threshold." So the cells are re-priced
at futures commission and then measured against hurdle P, rather than having the
personal track's verdict restated at a different threshold.

NO NEW BOOK IS BUILT AND NO CELL IS RE-RUN. Every input is read from a committed
artifact -- D247's `intraday_shorts_summary.json`. Re-costing is arithmetic on
`breakeven_bps`, which is a cost-free statistic by construction.

=========================================================================
WHAT CANNOT BE SCREENED AT ALL, AND WHY IT IS NOT A COST QUESTION
=========================================================================

**D264 and D265's single-name work is structurally unportable.** Its edge is
single-name idiosyncratic variance -- FINDINGS 2 -- and there is no retail
futures contract on PG, LMT, PM, MO, CLF, SM, YELP or RH. Single stock futures
exist in name only at retail. R12's escape hatch assumes the same exposure can be
bought more cheaply elsewhere; here it cannot be bought at all.

**So the screen runs on D247's 57-ETF intraday cells instead**, because those are
index and sector exposure, and ES/NQ/RTY/YM are the contracts they proxy.

=========================================================================
THE BASIS LIMITATION, STATED BEFORE THE NUMBERS
=========================================================================

The cells were measured on ETFs, not futures. D263 recorded the same caveat for
the COT panel: "they are the same underlying exposure but not the same
instrument." A pass here is a FEASIBILITY BOUND, not a result. Three specific
gaps:

  * SPY tracks ES closely; XLE, XOP, GDXJ and most of the 57 have NO futures
    contract, so a real futures book is a SUBSET of this universe and would have
    lower breadth than the 2.23 effective instruments D247 ran at.
  * Futures trade nearly 24 hours. "Intraday-flat" on an equity session is not
    the same construction on a contract that never really closes.
  * P1 is measured on OPEN equity and our max drawdown is CLOSED equity. R11 says
    in terms that ours is "a different and gentler statistic." Every P1 number
    below is therefore OPTIMISTIC by an unmeasured amount.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d266_prop_cross_screen.json"

# R12's table: personal ~3.8 bp round trip, prop ~0.2 bp. Per side.
COST_ETF_PER_SIDE = 1.60      # what D247 charged
COST_FUT_PER_SIDE = 0.10      # R12's ~0.2 bp round trip

P1_TRAILING_DD = 0.04         # hurdle P1, on OPEN equity
P3_WORST_DAY = 0.02


def main() -> int:
    src = json.loads((REPO / "data" / "intraday_shorts_summary.json").read_text())
    cells, be = src["cells"], src["breakeven_bps"]

    print("=" * 100)
    print("R12 CROSS-SCREEN -- D247's ETF intraday cells, RE-COSTED at futures commission")
    print("=" * 100)
    print(f"  charged: ETF {COST_ETF_PER_SIDE:.2f} bp/side  ->  futures "
          f"{COST_FUT_PER_SIDE:.2f} bp/side  ({COST_ETF_PER_SIDE / COST_FUT_PER_SIDE:.0f}x cheaper)\n")
    print(f"  {'cell':16s} {'turn':>5s} {'breakeven':>10s} | {'gross/yr':>9s} "
          f"{'ETF net':>9s} {'FUT net':>9s} | {'SR etf':>6s} {'SR fut':>7s} | "
          f"{'K':>4s} {'P2':>4s} {'P1 size':>10s} {'P1 return':>10s}")
    rows = []
    for k, c in cells.items():
        b = be[k]
        turn = c["turnover_per_year"]
        gross = b / 1e4 * turn                      # cost-free, by construction
        etf_net = gross - COST_ETF_PER_SIDE / 1e4 * turn
        fut_net = gross - COST_FUT_PER_SIDE / 1e4 * turn
        clears_k = b >= COST_FUT_PER_SIDE
        # P2: an intraday-flat cell holds no position across ANY flatten time, so
        # it is natively compliant at every venue -- including Topstep, which
        # R11's amendment treats as BLOCKED for the personal book.
        p2 = "PASS" if k.endswith("_intra") else "fail"
        dd = abs(c["max_drawdown"])
        # P1 is a SIZING constraint: scale until the drawdown reaches 4%. Return
        # scales with it, which is the whole point of computing it.
        size = P1_TRAILING_DD / dd if dd > 0 else 0.0
        p1_ret = fut_net * size
        # THE SHARPE MUST BE RE-COSTED TOO. D247's figure is at 1.60 bp/side, and
        # quoting it beside a futures-cost RETURN would understate the cell in one
        # column while P1 overstates it in another. Cost reduction adds a constant
        # to the mean and leaves the volatility essentially unchanged, so
        # `dSharpe = d_return / vol` to first order.
        vol = c["vol"]
        sharpe_fut = c["excess_sharpe"] + ((fut_net - etf_net) / vol if vol > 0 else 0.0)
        rows.append({"cell": k, "turnover": turn, "breakeven_bps": b,
                     "vol": vol, "excess_sharpe_futures": sharpe_fut,
                     "gross_pa": gross, "etf_net_pa": etf_net, "fut_net_pa": fut_net,
                     "clears_K_at_futures": clears_k, "p2": p2 == "PASS",
                     "max_dd": dd, "p1_size": size, "p1_scaled_return_pa": p1_ret,
                     "excess_sharpe_etf": c["excess_sharpe"]})
        print(f"  {k:16s} {turn:5.0f} {b:9.2f}b | {gross:+8.2%} {etf_net:+8.2%} "
              f"{fut_net:+8.2%} | {c['excess_sharpe']:+6.3f} {sharpe_fut:+7.3f} | "
              f"{'YES' if clears_k else 'no':>4s} {p2:>4s} {size:9.3f}x {p1_ret:+9.3%}")

    print("\n" + "=" * 100)
    print("VERDICT AGAINST HURDLE P")
    print("=" * 100)
    surv = [r for r in rows if r["clears_K_at_futures"] and r["fut_net_pa"] > 0]
    print(f"\n  Cells clearing the COST hurdle at futures pricing AND making money: "
          f"{len(surv)} of {len(rows)}")
    for r in surv:
        print(f"    {r['cell']:16s} futures net {r['fut_net_pa']:+.2%}/yr, "
              f"Sharpe {r['excess_sharpe_etf']:+.3f} -> {r['excess_sharpe_futures']:+.3f}, "
              f"P2 {'PASS' if r['p2'] else 'fail'}, "
              f"at P1 size {r['p1_size']:.3f}x -> {r['p1_scaled_return_pa']:+.3%}/yr")

    best = max(rows, key=lambda r: r["p1_scaled_return_pa"])
    print(f"\n  Best cell after P1 SIZING: {best['cell']} at "
          f"{best['p1_scaled_return_pa']:+.3%}/yr")
    print(f"  R11's clarification: at k uncorrelated arms each runs 1/sqrt(k) of solo")
    print(f"  size, so a k-arm book earns sqrt(k) x this. BOOK_PROP.md records k = 1.")
    for k_arms in (1, 4, 9):
        print(f"    k={k_arms}: {best['p1_scaled_return_pa'] * (k_arms ** 0.5):+.3%}/yr")

    print("""
  P4 (expected time-to-breach > 3 years) is NOT computed here and cannot be from
  these artifacts: it needs the OPEN-equity path against a ratcheting barrier, and
  every number above is closed-equity.  R11 states the difference is material and
  in the optimistic direction.  P5 and P6 are venue facts, not properties of these
  cells -- P6 restricts the venue to Topstep or MyFundedFutures.
""")
    OUT.write_text(json.dumps({"cost_etf_per_side": COST_ETF_PER_SIDE,
                               "cost_fut_per_side": COST_FUT_PER_SIDE,
                               "cells": rows, "survivors": [r["cell"] for r in surv]},
                              indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
