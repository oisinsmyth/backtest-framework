"""D264 addendum -- is the verdict an artefact of the capital size it was run at?

    uv run python scripts/d264_cost_vs_size.py

THIS SCORES NO NEW CELL. It varies only the COST SCHEDULE against the ALREADY
MEASURED breakeven, which is a re-costing of the kind R12 explicitly contemplates
("a cross-screen must RE-COST, not merely re-threshold"). No book is rebuilt, no
hurdle is re-run, no stratum is added, no window is re-cut.

WHY THE BREAKEVEN IS THE RIGHT THING TO HOLD FIXED
---------------------------------------------------
`breakeven_bps` reconstructs the arm's COST-FREE excess return -- it adds the
charged cost back before dividing by turnover -- so it is a property of the
signal and the turnover, NOT of the cost schedule. Changing account size cannot
move it. So the whole question reduces to: at what size does the CHARGED cost
fall below the breakeven the study already measured?

THE ARITHMETIC, before the table confirms it
---------------------------------------------
IBKR Fixed is `max(min(per_share * shares, 1% of notional), $1.00)`, and in the
per-share regime the bps figure is

    1e4 * (c * N/p) / N  =  1e4 * c / p

-- INDEPENDENT OF NOTIONAL, and a function of PRICE alone. So there is no size at
which commission gets cheaper. Below `shares = min_order/c` the $1.00 minimum
binds and it gets WORSE. Above, it is flat, and the thing that actually grows is
market impact, which THIS MODEL DOES NOT CHARGE.

So the cost curve is flat-then-rising as size falls, and flat-but-optimistic as
size rises. The study sits in the flat region.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


R = _load("d264", "run_single_name_intraday.py")
L = R.L

SUMMARY = json.loads((REPO / "data" / "single_name_intraday_summary.json").read_text())

# The two real IBKR US-equity schedules. The repo's committed model is FIXED;
# R12's prose quotes PRO TIERED. Both are priced here because the difference is
# 30% and the verdict should not depend on which one the reader assumes.
SCHEDULES = {
    "IBKR Fixed (the repo's committed model)": dict(per_share=0.005, min_order=1.00, cap=0.01),
    "IBKR Pro tiered (R12's prose)": dict(per_share=0.0035, min_order=0.35, cap=0.01),
}

SIZES = (1_000, 2_500, 5_000, 10_000, 25_000, 50_000, 100_000,
         175_439, 500_000, 1_000_000, 10_000_000)


def commission_bps(price, notional, per_share, min_order, cap):
    shares = notional / price
    c = min(per_share * shares, cap * notional)
    return 1e4 * max(c, min_order) / notional


def main() -> int:
    prices = {}
    saved = (L.FIXTURE, L.EVENTS)
    try:
        L.FIXTURE, L.EVENTS = R.FIXTURE, R.EVENTS
        panel, _ = L.load_panel()
    finally:
        L.FIXTURE, L.EVENTS = saved
    for i, s in enumerate(panel.symbols):
        prices[s] = float(np.median(panel.closes[i]))

    print("MEDIAN PRICE PER NAME, and why it is the variable that matters\n")
    print(f"  {'symbol':7s} {'stratum':8s} {'median px':>10s} {'50/px bp':>9s} {'35/px bp':>9s}")
    for s in R.STRATA["ALL"]:
        print(f"  {s:7s} {R.STRATUM[s]:8s} {prices[s]:10.2f} "
              f"{50.0 / prices[s]:9.2f} {35.0 / prices[s]:9.2f}")
    print("\n  Commission in bps is `1e4 * per_share / price` in the per-share regime.")
    print("  NOTIONAL DOES NOT APPEAR. Size cannot make it cheaper.\n")

    cells = ("S1_short_intra", "S2_short_intra")
    for label, sch in SCHEDULES.items():
        print("=" * 78)
        print(f"{label}: ${sch['per_share']}/share, min ${sch['min_order']:.2f}, "
              f"cap {sch['cap']:.0%}")
        print("=" * 78)
        for st in ("LOW", "HIGH"):
            syms = R.STRATA[st]
            hs = R.HALF_SPREAD_BPS[R.STRATUM[syms[0]]]
            be = {c: SUMMARY["breakeven_bps"][f"{st}:{c}"] for c in cells}
            print(f"\n  {st} stratum  (half-spread assumed {hs} bp)")
            print(f"    measured breakeven, size-invariant: "
                  + "  ".join(f"{c} {be[c]:.2f} bp" for c in cells))
            print(f"    {'notional/posn':>14s} {'commission':>11s} {'+spread':>9s} "
                  f"{'= charged':>10s} | clears breakeven?")
            for n in SIZES:
                comm = float(np.mean([commission_bps(prices[s], n, **sch) for s in syms]))
                charged = comm + hs
                ok = [c for c in cells if be[c] is not None and be[c] >= charged]
                zero_spread_ok = [c for c in cells if be[c] is not None and be[c] >= comm]
                mark = ("YES: " + ",".join(ok)) if ok else "no"
                if not ok and zero_spread_ok:
                    mark += f"   (would clear at ZERO spread: {','.join(zero_spread_ok)})"
                print(f"    {n:14,d} {comm:10.2f}b {hs:8.2f}b {charged:9.2f}b | {mark}")

    print("\n" + "=" * 78)
    print("THE UNMODELLED COST THAT RUNS THE OTHER WAY")
    print("=" * 78)
    print("""
  Market impact is NOT charged anywhere in this study, and it is the only cost
  that GROWS with size. The high-vol names ran $60-85M median daily dollar
  volume in the selection window, and the arm turns over ~324x/yr.

  So the table above is OPTIMISTIC at large size and the optimism is unbounded:
  every row at $1M+ per position understates the true cost by an amount nobody
  here has measured. The honest reading of the large-size rows is 'not cheaper',
  not 'this is what it would cost'.
""")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
