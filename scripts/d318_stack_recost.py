"""D318 -- the width x exit table, costed correctly on BOTH axes, plus commission.

    uv run python scripts/d318_stack_recost.py

A RE-COSTING of published cells. It runs no new book, scores no new rule, and
closes nothing. Every gross, turnover and volatility figure is D306's unchanged.

WHY. D307 found that charging two exit rules their OWN held-name spreads confounds
the comparison -- at N=2 the no-exit book measures a round trip of 86.7 and the
target book 73.2, a 16% gap caused only by the exit changing WHEN positions open,
so four fifths of the target's apparent +4.05 advantage was the spread estimate.
D307 fixed that for two cells. **The full 28-cell table was never re-costed.**

THE TWO AXES NEED OPPOSITE TREATMENT, which no record states:

  * ACROSS WIDTHS -- per-cell. The spread difference is CAUSED by the choice under
    test: a concentrated book genuinely holds tighter, pricier names and genuinely
    pays less. D300 counted that as a real second benefit and it is one.
  * WITHIN A WIDTH, ACROSS EXITS -- common. Here the spread difference is
    incidental to what is being tested, which is D307's finding.

So each depth is charged ITS OWN no-exit book's round trip, applied to every exit
variant at that depth. That is per-cell on the width axis and common on the exit
axis simultaneously.

AND COMMISSION, WHICH THE SPREAD CHAIN NEVER CHARGED AT ALL (D317). IBKR is
`max(min($0.005/share x shares, 1% of notional), $1.00)`; in the per-share regime
that is 0.005/price in bp/side, and a paired spread position crosses four times
per round trip. Held median price comes from D300's own table at the same depths
on the same construction.

WHAT THIS IS NOT. Commission is estimated from a per-depth median price, not
derived per symbol as D264 did -- so it is a correction of the right order, not a
measurement. The min($1.00) and 1%-of-notional arms of the schedule are ignored,
which needs a position-size assumption this study does not make.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d318_stack_recost.json"
ANN = 252.0
PER_SHARE = 0.005          # IBKR per-share, the regime that binds at these sizes
CROSSINGS = 4.0            # a paired spread position: 2 legs in, 2 legs out
EXITS = ("none", "target", "none+overlay", "target+overlay")


def main() -> int:
    d306 = json.loads((REPO / "data" / "d306_width_exits.json").read_text())["cells"]
    d300 = json.loads((REPO / "data" / "d300_width.json").read_text())["depths"]
    depths = sorted({c["depth"] for c in d306.values()})

    # accounting check before anything is rebuilt on it
    for k, c in d306.items():
        lhs = c["gross_bp"] - c["cost_pos_bp"] - c["cost_overlay_bp"]
        assert abs(lhs - c["net_bp"]) < 1e-6, f"{k}: net does not reconcile"
    print("D318  the stack, re-costed on both axes")
    print("  [ok] every published cell reconciles: gross - cost_pos - cost_overlay"
          " = net\n")

    rows, out = {}, {}
    for d in depths:
        base = d306[f"N={d}/none"]
        rt_common = base["round_trip"]                  # D307: the no-exit book's
        price = d300[str(d)]["held_price_median"]
        comm_side = PER_SHARE / price * 1e4
        rt_comm = CROSSINGS * comm_side
        for e in EXITS:
            c = d306[f"N={d}/{e}"]
            # rescale the published spread cost from this cell's own round trip
            # onto the depth's common one; both cost terms scale linearly in rt.
            sc = rt_common / c["round_trip"]
            spread = (c["cost_pos_bp"] + c["cost_overlay_bp"]) * sc
            comm = c["turnover"] * rt_comm
            net = c["gross_bp"] - spread - comm
            rows[(d, e)] = dict(
                depth=d, exit=e, gross=c["gross_bp"], turnover=c["turnover"],
                rt_own=c["round_trip"], rt_common=rt_common,
                held_price=price, comm_bp_side=comm_side, rt_comm=rt_comm,
                cost_spread=spread, cost_comm=comm,
                net_published=c["net_bp"], net=net, vol=c["vol_bp"],
                # D306's published `sharpe` is a GROSS Sharpe -- gross/vol -- the
                # same convention D312 flagged in D310. It is reproduced here
                # under its right name and is UNCHANGED by any re-costing. The
                # two net Sharpes are the ones this study moves.
                sharpe_gross_pub=c["sharpe"],
                sharpe_gross=c["gross_bp"] / c["vol_bp"] * np.sqrt(ANN),
                sharpe_net_pub=c["net_bp"] / c["vol_bp"] * np.sqrt(ANN),
                sharpe_net=net / c["vol_bp"] * np.sqrt(ANN),
                exposure=c["exposure"], maxdd=c["maxdd_bp"])
            out[f"N={d}/{e}"] = rows[(d, e)]

    # the published column IS a gross Sharpe -- verified, not assumed
    w = max(abs(r["sharpe_gross"] - r["sharpe_gross_pub"]) for r in rows.values())
    assert w < 1e-3, f"D306's `sharpe` is not gross/vol (max diff {w:.2e})"
    print("  [ok] D306's published `sharpe` reproduces as GROSS/vol to %.1e --"
          " it is a gross Sharpe, and re-costing cannot move it\n" % w)

    h = "%-18s %8s %8s %7s %8s %9s %9s %9s %8s"
    print(h % ("cell", "gross", "spread", "comm", "NET", "net pub",
               "netSHRP", "netSHRP pub", "grsSHRP"))
    print("-" * 92)
    for d in depths:
        for e in EXITS:
            r = rows[(d, e)]
            print(h % (f"N={d}/{e}", "%+.2f" % r["gross"],
                       "%.2f" % r["cost_spread"], "%.2f" % r["cost_comm"],
                       "%+.2f" % r["net"], "%+.2f" % r["net_published"],
                       "%+.3f" % r["sharpe_net"], "%+.3f" % r["sharpe_net_pub"],
                       "%+.3f" % r["sharpe_gross"]))
        print("-" * 92)

    print("\nCOMMISSION, per depth (IBKR per-share on D300's held median price)")
    print("  %6s %12s %13s %11s" % ("N", "held price", "bp/side", "rt add"))
    for d in depths:
        r = rows[(d, "none")]
        print("  %6d %12s %13.2f %11.2f" % (
            d, "$%.2f" % r["held_price"], r["comm_bp_side"], r["rt_comm"]))

    best_net = max(rows.values(), key=lambda r: r["net"])
    best_shp = max(rows.values(), key=lambda r: r["sharpe_net"])
    print("\nBEST CELLS AFTER RE-COSTING")
    print("  by NET     N=%d/%-14s %+8.2f bp/bar   (published %+.2f)"
          % (best_net["depth"], best_net["exit"], best_net["net"],
             best_net["net_published"]))
    print("  by NET SHARPE  N=%d/%-14s %+8.3f      (on published cost %+.3f)"
          % (best_shp["depth"], best_shp["exit"], best_shp["sharpe_net"],
             best_shp["sharpe_net_pub"]))
    pub_net = max(rows.values(), key=lambda r: r["net_published"])
    pub_shp = max(rows.values(), key=lambda r: r["sharpe_net_pub"])
    print("  -- D306's own best-by-net was N=%d/%s and by GROSS Sharpe N=%d/%s;"
          % (pub_net["depth"], pub_net["exit"],
             max(rows.values(), key=lambda r: r["sharpe_gross"])["depth"],
             max(rows.values(), key=lambda r: r["sharpe_gross"])["exit"]))
    print("     on NET Sharpe its own numbers already pointed at N=%d/%s."
          % (pub_shp["depth"], pub_shp["exit"]))

    print("\nWHAT THE EXIT IS WORTH, charged its depth's COMMON round trip")
    print("  %6s %14s %14s %14s" % ("N", "target-none", "ovl on none", "ovl on target"))
    for d in depths:
        t = rows[(d, "target")]["net"] - rows[(d, "none")]["net"]
        o1 = rows[(d, "none+overlay")]["net"] - rows[(d, "none")]["net"]
        o2 = rows[(d, "target+overlay")]["net"] - rows[(d, "target")]["net"]
        print("  %6d %+14.2f %+14.2f %+14.2f" % (d, t, o1, o2))

    OUT.write_text(json.dumps(dict(
        note="RE-COSTING of D306's published cells. Per-cell round trip across "
             "widths, common within a width (D307), plus IBKR per-share "
             "commission estimated from D300's held median price. No new book.",
        per_share=PER_SHARE, crossings=CROSSINGS, cells=out), indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
