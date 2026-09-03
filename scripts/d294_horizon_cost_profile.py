"""D294 -- the horizon profile, read COST-ADJUSTED instead of by t.

    uv run python scripts/d294_horizon_cost_profile.py

NOT A NEW SEARCH. This re-reads the grid D293 already built, with a different
summary statistic. No cell is added and no parameter is swept that D290 did not
sweep for all 51 of its candidates.

WHY IT MATTERS. D290 picked each candidate's horizon by MAXIMUM t, and t is
cost-blind. The round trip is paid ONCE PER ENTRY whichever k you hold for, so
gross grows with k while cost does not. `hist_L` and the confluence both peak at
k=5 on t and that says nothing about where they peak on cost coverage.

CLAUDE.md, in as many words: "A longer hold lifts breakeven by amortising one
round trip; per-bar edge usually FALLS, so Sharpe can drop as cost coverage
rises. Say which moved: edge per unit exposure, or cost per trade."

So both are reported, and neither alone:

    x cost      gross(k) / round trip      -- does the trade pay for itself
    t           the same statistic D290 ranked on   -- is the edge there
    bp per bar  gross(k) / k               -- edge per unit exposure, which is
                                              what a longer hold gives away

A horizon that improves `x cost` while collapsing `bp per bar` has bought cost
coverage with edge, and that is a real trade rather than a free lunch. Reported
under BOTH aggregations of Corwin-Schultz, because the correction to D293 showed
the mean and the robust estimates straddle R14's line.
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


C = _load("d293", "run_d293_candidate.py")
SP = _load("d285sp", "d285_spread_estimate.py")
R, M, D, ET = C.R, C.M, C.D, C.ET
OUT = REPO / "data" / "d294_horizon_cost_profile.json"
N_FIXED = 25


def main() -> int:
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    live = panel.live
    T = live.shape[1]
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & live
    fwd = M.forward_returns(panel, live)
    g = M.P1.build_grids(panel, cleaned)
    on, idr = ET.segments(g, live, panel)
    fwd_o = ET.open_entry(on, idr, live, C.HORIZONS)
    half = SP.corwin_schultz(g["high"], g["low"], live) / 2.0 * 1e4
    sa, s1, s2 = z[C.PRIMARY], z[C.PAIR[0]], z[C.PAIR[1]]

    out = {}
    for nm, comp in (("confluence", True), (C.PRIMARY, False)):
        ranks = C.rank_all(sa, s1, s2, base, comp)
        b = C.book(ranks, N_FIXED, T, comp)
        plan, klo, khi = b[2], b[3], b[4]
        bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
        cost = {}
        for side, rows, mask in (("long", plan.lo, klo), ("short", plan.hi, khi)):
            v = half[rows[mask], bc[mask]]
            v = v[np.isfinite(v)]
            cost[side] = (float(v.mean()), float(np.median(v)))
        rt_mean = 2 * cost["long"][0] + 2 * cost["short"][0]
        rt_med = 2 * cost["long"][1] + 2 * cost["short"][1]
        cs_c = C.cell_stats(fwd, b[0], b[1], T)
        cs_o = C.cell_stats(fwd_o, b[0], b[1], T)

        print(f"\n{'=' * 88}")
        print(f"  {nm}   N={N_FIXED}   round trip: mean {rt_mean:.1f} bp, "
              f"robust(median) {rt_med:.1f} bp")
        print(f"{'=' * 88}")
        print(f"  {'k':>3s} | {'gross bp':>9s} {'t':>6s} | {'bp/bar':>7s} | "
              f"{'x mean':>7s} {'x robust':>9s} | {'open bp':>9s} {'open t':>7s} "
              f"{'x open':>7s}")
        rows = []
        for k in C.HORIZONS:
            rc = cs_c.get(k, {}).get("spread")
            ro = cs_o.get(k, {}).get("spread")
            if rc is None:
                continue
            xm, xr = rc[0] / rt_mean, rc[0] / rt_med
            xo = (ro[0] / rt_mean) if ro else None
            star = "  <- D290/D293 cell" if k == 5 else ""
            print(f"  {k:3d} | {rc[0]:+9.2f} {rc[1]:+6.2f} | {rc[0] / k:+7.2f} | "
                  f"{xm:7.3f} {xr:9.3f} | "
                  f"{(f'{ro[0]:+9.2f}' if ro else '       --')} "
                  f"{(f'{ro[1]:+7.2f}' if ro else '     --')} "
                  f"{(f'{xo:7.3f}' if xo is not None else '     --')}{star}")
            rows.append(dict(k=k, bp=rc[0], t=rc[1], bp_per_bar=rc[0] / k,
                             x_mean=xm, x_robust=xr,
                             open_bp=ro[0] if ro else None,
                             open_t=ro[1] if ro else None, x_open=xo))
        best_t = max(rows, key=lambda r: r["t"])
        best_x = max(rows, key=lambda r: r["x_robust"])
        print(f"\n    peak on t          : k={best_t['k']:<3d} t {best_t['t']:+.2f}"
              f"   x robust {best_t['x_robust']:.3f}   bp/bar "
              f"{best_t['bp_per_bar']:+.2f}")
        print(f"    peak on COST       : k={best_x['k']:<3d} t {best_x['t']:+.2f}"
              f"   x robust {best_x['x_robust']:.3f}   bp/bar "
              f"{best_x['bp_per_bar']:+.2f}")
        print(f"    -> cost coverage {best_x['x_robust'] / best_t['x_robust']:.2f}x "
              f"better, edge per unit exposure "
              f"{best_x['bp_per_bar'] / best_t['bp_per_bar']:.2f}x")
        out[nm] = dict(round_trip_mean=rt_mean, round_trip_robust=rt_med,
                       rows=rows, peak_t=best_t, peak_cost=best_x)

    json.dump({"purpose": "D294: D293's own grid re-read cost-adjusted. k was "
                          "chosen on t, which is cost-blind, and the round trip "
                          "is paid once per entry whatever k is held.",
               "N": N_FIXED, "results": out}, open(OUT, "w"), indent=1)
    print(f"\n  wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
