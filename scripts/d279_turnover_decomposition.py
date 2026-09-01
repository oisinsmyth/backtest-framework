"""D279 follow-up -- is hurdle C measuring the RANKING or the TURNOVER?

    uv run python scripts/d279_turnover_decomposition.py

THIS IS NOT A NEW HYPOTHESIS AND IT DOES NOT RE-RUN HURDLE C. D279's verdict
stands as recorded. This decomposes a confound found IN the reported numbers.

THE CONFOUND, and it is arithmetic rather than a suspicion:

  S1_short|top10   10,688 turnover units    SR +2.343
  S1_short|rnd10   59,482 turnover units    SR -1.792

`random-N` re-draws its N names EVERY BAR, so it churns 5.6x harder than the
ranked book and pays 5.6x the fees. The ranked book is persistent for free: a
name with the most negative `hist_L` today is usually still near the bottom
tomorrow. **So the pre-registered control differs from the treatment in TWO
ways, not one** -- selection AND turnover -- and hurdle C cannot separate them.

TWO MEASUREMENTS SEPARATE THEM
------------------------------
  GROSS  Re-score every cell at ZERO fees, ZERO borrow, ZERO rf. If the ranked
         book still beats random selection here, the ranking picks better
         names and the fee gap was never the story. If the gap collapses,
         hurdle C measured the trading toll and D279's N2 verdict must be
         reversed. This is a decomposition of cells already counted.

  MATCHED  A PERSISTENT random control: draw at random, then HOLD the draw
         while it still qualifies, filling only vacancies. Same N, same bars,
         random selection, and turnover in the ranked book's range. This is the
         control hurdle C should have carried.

LEDGER. The persistent controls are 6 further looks (2 arms x 3 N). D279's 14
becomes 20, and D256's 21 carried makes 41. Controls are counted like anything
else -- D228's floor does not care what a cell was built to prove.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
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


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
RP, U = B.RP, B.U

OUT = REPO / "data" / "d279_turnover_decomposition.json"
N_LEVELS, SEED = C.N_LEVELS, C.SEED
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE


def persistent_rnd(base, n, rng):
    """Random selection that PERSISTS, so turnover is not the difference.

    Draw at random from the qualifying set, then KEEP the draw for as long as
    each name still qualifies, refilling only the vacancies. This is how the
    ranked book behaves in practice -- it re-ranks every bar, but the ranking is
    stable, so names stay held. The only remaining difference from top-N is
    WHICH names, which is what hurdle C set out to test."""
    out = np.zeros_like(base)
    held: list[int] = []
    for t in range(base.shape[1]):
        q = base[:, t] != 0.0
        held = [i for i in held if q[i]]                    # drop disqualified
        need = n - len(held)
        if need > 0:
            avail = np.flatnonzero(q)
            if held:
                avail = avail[~np.isin(avail, held)]
            if avail.size:
                held = held + rng.choice(
                    avail, size=min(need, avail.size), replace=False).tolist()
        if held:
            idx = np.array(held)
            out[idx, t] = base[idx, t]
    return out


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    s2 = -B.walk_state(panel, (g_lo < 0) & (g_hi < 0) & sok, warm, U.AGE_CAP)
    arms = {"S1_short": (s1, hs), "S2_short": (s2, g_lo)}

    # THE ZERO-COST PANEL. `cost_fraction` is what `score` charges per unit
    # traded; zeroing it, borrow and rf leaves the RAW name-selection return.
    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})

    rng = np.random.default_rng(SEED)
    books = {}
    for arm, (base, score) in arms.items():
        for N in N_LEVELS:
            books[f"{arm}|top{N}"] = C.top_n(base, score, N)
            books[f"{arm}|rnd{N}"] = C.top_n(base, score, N, rng=rng)
            books[f"{arm}|per{N}"] = persistent_rnd(base, N, rng)
    print(f"built {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    net = {k: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
           for k, p in books.items()}
    gro = {k: RP.score(free, p, 0, ppy=PPY, rf_annual=0.0, borrow_annual=0.0)
           for k, p in books.items()}

    print("  GROSS is zero fees / zero borrow / zero rf -- pure name selection.\n")
    print(f"  {'arm':10s} {'N':>4s}  {'mode':>4s} {'turnover':>10s} "
          f"{'net SR':>8s} {'GROSS SR':>9s} {'gross CAGR':>11s}")
    rows = {}
    for arm in arms:
        for N in N_LEVELS:
            for mode in ("top", "rnd", "per"):
                k = f"{arm}|{mode}{N}"
                rows[k] = {"turnover": net[k]["turnover_units"],
                           "net_sharpe": net[k]["excess_sharpe"],
                           "gross_sharpe": gro[k]["excess_sharpe"],
                           "gross_cagr": gro[k]["cagr"],
                           "entries": net[k]["entries"]}
                print(f"  {arm:10s} {N:4d}  {mode:>4s} "
                      f"{net[k]['turnover_units']:10,.0f} "
                      f"{net[k]['excess_sharpe']:+8.3f} "
                      f"{gro[k]['excess_sharpe']:+9.3f} {gro[k]['cagr']:+10.2%}")
            print()

    print("  THE DECOMPOSITION -- top-N minus each control, gross and net:\n")
    print(f"  {'arm':10s} {'N':>4s}  {'vs rnd net':>11s} {'vs rnd GROSS':>13s} "
          f"{'vs per net':>11s} {'vs per GROSS':>13s}   turnover ratio")
    verdict = {}
    for arm in arms:
        for N in N_LEVELS:
            t, r, p = (rows[f"{arm}|{m}{N}"] for m in ("top", "rnd", "per"))
            v = {"vs_rnd_net": t["net_sharpe"] - r["net_sharpe"],
                 "vs_rnd_gross": t["gross_sharpe"] - r["gross_sharpe"],
                 "vs_per_net": t["net_sharpe"] - p["net_sharpe"],
                 "vs_per_gross": t["gross_sharpe"] - p["gross_sharpe"],
                 "turnover_ratio_rnd": r["turnover"] / t["turnover"],
                 "turnover_ratio_per": p["turnover"] / t["turnover"]}
            verdict[f"{arm}|{N}"] = v
            print(f"  {arm:10s} {N:4d}  {v['vs_rnd_net']:+11.3f} "
                  f"{v['vs_rnd_gross']:+13.3f} {v['vs_per_net']:+11.3f} "
                  f"{v['vs_per_gross']:+13.3f}   rnd {v['turnover_ratio_rnd']:.1f}x "
                  f"per {v['turnover_ratio_per']:.1f}x")

    json.dump({"purpose": ("separates ranking from turnover in D279's hurdle C; "
                           "does not re-run the hurdle or alter its verdict"),
               "cells": rows, "decomposition": verdict,
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
