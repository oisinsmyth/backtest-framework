"""D279 integrity check on the two surviving cells -- WHERE does the money come from?

    uv run python scripts/d279_survivor_attribution.py

NO NEW CELL, NO NEW HURDLE, NO NULL RE-RUN. This attributes P&L that D279 has
already reported. The ledger is unchanged.

THREE QUESTIONS, and each one could sink the survivors on its own.

  1. IS IT THE DEAD NAMES? The fixture carries 562 delisted names (35.7%) and
     122 more that collapsed while listed. A short book that makes its money on
     terminal decliners is making a REAL claim, but a fragile one: D252 records
     that provider coverage logs 40-76 delistings a year for 2009-2012 against
     700-1,000 after 2016, so the dead cohort is MATERIALLY UNDER-SAMPLED EARLY.
     If the P&L is concentrated in dead names it is also concentrated in the
     back half of the span, and the early years are not evidence for it.

  2. IS IT ONE ERA? A short book in a rising market that earns its whole result
     in 2020 or 2022 has found two drawdowns, not an edge. Reported by calendar
     year, no smoothing.

  3. IS IT A HANDFUL OF NAMES? D279 declared this in advance as what E-prime
     does NOT guard against, and promised per-symbol concentration beside every
     cell. That was reported as a single top-name share; this gives the full
     shape -- the share carried by the top 1, 5 and 10 names, and how many names
     it takes to reach half the P&L.

WHAT WOULD BE DISQUALIFYING, stated before the numbers are read: a result whose
money is majority-dead AND majority-post-2016 is a result the fixture cannot
support, because the early span then has no comparable population.
"""

from __future__ import annotations

import csv
import gzip
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

META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
OUT = REPO / "data" / "d279_survivor_attribution.json"
CELLS = ("S1_short|top25", "S1_short|top50", "S1_short|top10")


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=C.FEE)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    books = {f"S1_short|top{N}": C.top_n(s1, hs, N) for N in C.N_LEVELS}
    print(f"rebuilt {time.time() - t0:.0f}s", flush=True)

    meta = json.loads(META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate")) for s in panel.symbols])
    years = np.array([int(d[:4]) for d in panel.dates])
    print(f"delisted names in the panel: {int(dead.sum())} of {len(panel.symbols)}\n")

    out = {}
    for k in CELLS:
        pos = books[k]
        # Per-name, per-bar P&L in log units. This is the SAME quantity D279
        # scored, sliced rather than recomputed.
        pnl = pos * panel.total_log_returns
        by_sym = pnl.sum(axis=1)
        tot = by_sym.sum()

        d_share = by_sym[dead].sum() / tot
        order = np.argsort(-by_sym)
        cum = np.cumsum(by_sym[order]) / tot
        n_half = int(np.searchsorted(cum, 0.5) + 1)
        top1, top5, top10 = (by_sym[order[:m]].sum() / tot for m in (1, 5, 10))
        winners = int((by_sym > 0).sum())
        traded = int((np.abs(pos).sum(axis=1) > 0).sum())

        by_year = {}
        for y in sorted(set(years.tolist())):
            by_year[y] = float(pnl[:, years == y].sum())
        post16 = sum(v for y, v in by_year.items() if y >= 2016) / tot

        out[k] = {"total_log_pnl": float(tot), "dead_share": float(d_share),
                  "post2016_share": float(post16), "names_traded": traded,
                  "names_profitable": winners, "names_to_half_pnl": n_half,
                  "top1_share": float(top1), "top5_share": float(top5),
                  "top10_share": float(top10),
                  "by_year": {str(y): v for y, v in by_year.items()}}

        print(f"  {k}")
        print(f"    dead-name share of P&L      {d_share:+7.1%}   "
              f"(dead names are {dead.sum() / len(dead):.1%} of the panel)")
        print(f"    post-2016 share of P&L      {post16:+7.1%}")
        print(f"    names traded / profitable   {traded:,} / {winners:,}")
        print(f"    names to reach half the P&L {n_half}")
        print(f"    top 1 / 5 / 10 name share   {top1:+.1%} / {top5:+.1%} / {top10:+.1%}")
        print("    by year:", "  ".join(
            f"{y}:{v:+.3f}" for y, v in sorted(by_year.items())), flush=True)
        pos_years = sum(1 for v in by_year.values() if v > 0)
        print(f"    profitable years            {pos_years}/{len(by_year)}\n")

    json.dump({"purpose": ("attributes P&L already reported by D279; adds no "
                           "cell, no hurdle and no null"),
               "delisted_in_panel": int(dead.sum()),
               "panel_names": len(panel.symbols), "cells": out,
               "elapsed_s": round(time.time() - t0, 1)}, open(OUT, "w"), indent=1)
    print(f"wrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
