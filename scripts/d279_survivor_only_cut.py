"""D279 robustness cut -- the same grid with EVERY DEAD NAME REMOVED.

    uv run python scripts/d279_survivor_only_cut.py

WHY THIS IS WORTH 14 FRESH LOOKS. D279 ran on the only short-side fixture in the
programme WITHOUT a survivorship hole, and its two survivors short the
worst-accelerating names in a universe containing 596 delisted tickers. The
obvious objection is that the edge IS the delistings -- that the book is paid for
holding names on their way to zero, which a survivor-only universe would never
have offered.

D279's attribution already answered part of that: dead names carry 24.2% of
`top25`'s P&L while being 37.9% of the panel, so they are UNDER-represented. But
that is a decomposition of the dead-inclusive book. **It does not say what the
strategy would have scored if the dead names had never been available to hold**,
which is the counterfactual every survivor-biased fixture in this programme
silently assumes. This measures it.

WHAT IS HELD FIXED, so the comparison is a cut and not a re-run
---------------------------------------------------------------
SIGNALS ARE COMPUTED ON THE FULL PANEL AND THEN SUBSET. They are per-name and
independent, so a retained name's `hist_L` here is bit-identical to D279's. The
ONLY things that change are which names compete for the top-N slots, and the
population the rotation null and the effective-instrument count draw from.

Every constant is D279's, unvaried: N in {10, 25, 50}, 5 bp/side, borrow 3%/yr,
rf 4%, PPY 252, seed 0, 300 null draws.

WHAT WOULD FALSIFY THE SURVIVORS, declared before the numbers are read
----------------------------------------------------------------------
  If `S1_short|top25` loses hurdle V or hurdle C here, the edge depended on
  holding names that died, and D279's result cannot be carried to any
  survivor-only universe -- which is EVERY OTHER FIXTURE this programme owns.
  That would not make D279 wrong; it would make it unexportable, which for a
  result whose only licensed next step is an out-of-sample test is nearly the
  same thing.

  If it survives with a materially lower Sharpe, the delistings are a
  contributor and the honest headline is the survivor-only number, because that
  is the one a live book on a modern universe could have earned.

LEDGER. 14 fresh cells. D279's 41 becomes 55. NOTHING HERE MAY BE TUNED -- this
is a robustness cut on a result already recorded, not a search for a better one.
Hurdle H is reported and, per D279's RESULT, is NOT treated as decisive: a null
that a losing book clears at the 100th percentile is broken under R7's
corollary.
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
E = _load("d279e", "d279_fix_eprime.py")
RP, U = B.RP, B.U

META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
PRIOR = REPO / "data" / "d279_concentrated_summary.json"
OUT = REPO / "data" / "d279_survivor_only_summary.json"
N_SIMS, SEED = C.N_SIMS, C.SEED
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE


def subset(panel, keep):
    """A RaggedPanel over `keep` only. Row-aligned arrays are sliced; `index_of`
    is filtered by key. Nothing is recomputed, so a retained name's data is
    identical to what D279 scored."""
    syms = [panel.symbols[i] for i in keep]
    return RP.RaggedPanel(
        symbols=syms, dates=panel.dates,
        closes=panel.closes[keep], log_returns=panel.log_returns[keep],
        total_log_returns=panel.total_log_returns[keep],
        cost_fraction=panel.cost_fraction[keep], live=panel.live[keep],
        index_of={s: panel.index_of[s] for s in syms})


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    s1_full = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    s2_full = -B.walk_state(panel, (g_lo < 0) & (g_hi < 0) & sok, warm, U.AGE_CAP)
    print(f"loaded + signals on the FULL panel {time.time() - t0:.0f}s", flush=True)

    meta = json.loads(META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate")) for s in panel.symbols])
    keep = np.flatnonzero(~dead)
    sp = subset(panel, keep)
    print(f"  dead removed: {int(dead.sum())}   survivors kept: {keep.size} "
          f"of {len(panel.symbols)}\n", flush=True)

    # Signals subset, NOT recomputed -- see the module docstring.
    arms = {"S1_short": (s1_full[keep], hs[keep]),
            "S2_short": (s2_full[keep], g_lo[keep])}

    rng = np.random.default_rng(SEED)
    books = {}
    for arm, (base, score) in arms.items():
        books[f"{arm}|all"] = base
        for N in C.N_LEVELS:
            books[f"{arm}|top{N}"] = C.top_n(base, score, N)
            books[f"{arm}|rnd{N}"] = C.top_n(base, score, N, rng=rng)
    print(f"built {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    prior = json.loads(PRIOR.read_text())["cells"]
    cells = {}
    print(f"  {'cell':16s} {'expo':>6s} {'CAGR':>8s} {'SR':>8s} "
          f"{'was (dead-incl)':>16s} {'delta':>8s} {'trades':>8s} {'be borrow':>10s}")
    for k, p in books.items():
        s = RP.score(sp, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
        s["breakeven_borrow"] = C.breakeven_borrow(sp, p, 0, s)
        s["top_name_share"] = C.per_symbol_concentration(sp, p, 0)
        s["effective_instruments_book"], s["names_held_over_min_overlap"] = \
            E.eff_over_book(sp, p)
        was = prior[k]["excess_sharpe"]
        s["dead_inclusive_sharpe"] = was
        cells[k] = s
        print(f"  {k:16s} {s['exposure_gross']:5.2%} {s['cagr']:+7.2%} "
              f"{s['excess_sharpe']:+8.3f} {was:+16.3f} "
              f"{s['excess_sharpe'] - was:+8.3f} {s['entries']:8,d} "
              + (f"{s['breakeven_borrow']:9.1%}" if s["breakeven_borrow"] is not None
                 else "        —"), flush=True)

    print(f"\nrotation nulls on the SURVIVOR-ONLY panel, {N_SIMS} draws ...", flush=True)
    floor_draws = []
    for k, p in books.items():
        sh, mn = RP.rotation_null(sp, p, 0, n_sims=N_SIMS, seed=SEED, ppy=PPY,
                                  rf_annual=RF, borrow_annual=BORROW)
        c = cells[k]
        c["sharpe_pct"] = float((sh < c["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < c["total_return"]).mean() * 100)
        c["null_sharpe_p50"] = float(np.percentile(sh, 50))
        c["null_sharpe_p95"] = float(np.percentile(sh, 95))
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        c["V"] = bool(c["cagr"] > 0)
        floor_draws.append(sh)
        print(f"  {k:16s} {c['sharpe_pct']:5.1f}th / {c['money_pct']:5.1f}th   "
              f"null p50 {c['null_sharpe_p50']:+.3f}  p95 {c['null_sharpe_p95']:+.3f}   "
              f"{time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(floor_draws), axis=0), 95))

    print(f"\nbest-of-{len(books)} floor: {floor:+.3f}   "
          f"(dead-inclusive was {json.loads(PRIOR.read_text())['floor']:+.3f})\n")
    print(f"  {'cell':16s} {'SR':>8s} {'vs random':>10s} {'E-prime':>8s} "
          f"{'H':>3s} {'V':>3s} {'C':>3s} {'F':>3s} {'E':>3s}   was D279")
    surv = []
    for k in books:
        arm, mode = k.split("|")
        c = cells[k]
        if mode.startswith("top"):
            r = cells[f"{arm}|rnd{mode[3:]}"]
            c["C"] = bool(c["excess_sharpe"] > r["excess_sharpe"]
                          and c["total_return"] > r["total_return"])
            vs = f"{c['excess_sharpe'] - r['excess_sharpe']:+.3f}"
        else:
            c["C"], vs = False, "—"
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["Eprime"] = bool(c["effective_instruments_book"] >= 3.0 and c["entries"] >= 500)
        c["clears_all"] = bool(c["H"] and c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:16s} {c['excess_sharpe']:+8.3f} {vs:>10s} "
              f"{c['effective_instruments_book']:8.2f} "
              f"{y(c['H']):>3s} {y(c['V']):>3s} {y(c['C']):>3s} {y(c['F']):>3s} "
              f"{y(c['Eprime']):>3s}   "
              f"{'** SURVIVED **' if c['clears_all'] else 'no'}"
              f"{'   (was a D279 survivor)' if k in json.loads(PRIOR.read_text())['survivors'] else ''}")

    print(f"\n  SURVIVORS, survivor-only universe: {surv or 'NONE'}")
    print(f"  SURVIVORS, dead-inclusive (D279):   "
          f"{json.loads(PRIOR.read_text())['survivors']}")
    json.dump({"purpose": ("D279's grid with every delisted name removed; a "
                           "robustness cut, 14 fresh cells, nothing tuned"),
               "dead_removed": int(dead.sum()), "survivors_kept": int(keep.size),
               "floor": floor, "cells": cells, "survivors": surv,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
