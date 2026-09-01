"""D277 -- the mine. Every base signal from this session crossed with every filter.

    uv run python scripts/d277_mine.py

THIS IS A SEARCH AND IT IS LABELLED AS ONE. No hypothesis is pre-registered, no
hurdle is claimed, nothing may enter any book from it. The output is a RANKED
CANDIDATE LIST WITH A MULTIPLICITY PRICE, which is a different object from a
result and is reported as such.

WHY IT IS STILL WORTH RUNNING. A mine returns a maximum, and the maximum of N
noise draws is large -- so the only honest way to read one is against a
best-of-N floor computed over THE WHOLE SEARCH rather than the winner (D228).
That floor is computed here. If nothing clears it, the mine has priced its own
output at zero, which is a real answer obtained cheaply.

THE LEDGER, AND THE PRINCIPAL CORRECTED ME ON IT. Earlier drafts carried 46,278
looks into this search. That is over-correction and the repo says so in its own
words: D218 states its floor as "+1.42 Sharpe at 45,803 looks -- no arm anyone
runs on THIS FIXTURE can clear it", scoped to the 57-ETF DAILY fixture. That
count accumulates pairs studies, breakouts, the MACD ladder and structure work --
hypotheses this search is not testing, on universes this search does not use.
Summing them here is the same error the principal rejected for the terrain
programme's 259, and it would make any finding unfalsifiable by construction.

WHAT DOES CARRY IS ~118 -- D264 through D276, on THIS fixture -- because those
studies BUILT the bases and the scores mined here, so the search space was not
chosen independently of them. Total ~433, not 46,278.

AND THE LEDGER DECIDES NOTHING EITHER WAY. It is bookkeeping. What prices a mine
is the EMPIRICAL best-of-315 floor below, computed from the data.

WHAT IS CROSSED
  bases    S1_short_intra, S2_short_intra, choch_short          (3)
  filters  17 scores x {top quintile, bottom quintile}, + none  (35)
  strata   ALL, LOW, HIGH                                        (3)
                                                       = 315 cells

  The 17 scores are the whole session's inventory: 9 price (D267), 4 volume
  (D270) and 4 profile (D272).

STAGE 2 pairs the ten best single filters with a second filter, +340 cells,
because "cross-pollinate" is the request and a single filter is not a crossing.
"""

from __future__ import annotations

import importlib.util
import json
import math
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


S = _load("d275", "run_choch_short.py")
P = _load("d272", "run_volume_profile.py")
A, R, M, D, X = S.A, S.R, S.M, S.D, S.X
C, V, I = P.C, P.V, P.I

OUT = REPO / "data" / "d277_mine_summary.json"
N_SIMS, SEED = 200, 0
TOP_PAIRS = 10


def build_all(panel, cleaned, first, start, vol, px, bod):
    price = C.build_scores(panel, cleaned)
    volu = V.build_volume_scores(panel, vol, px, bod, panel.total_log_returns)
    prof = P.build_profile_scores(panel, cleaned, vol, start)
    scores = {**price, **{k: volu[k] for k in ("rel_vol", "vol_z", "dollar_vol", "vol_trend")},
              **prof}
    books = R.build_books(panel, cleaned, start, first)
    ch, _ = S.choch_books(panel, cleaned, first, start)
    bases = {"S1_short_intra": books["S1_short_intra"],
             "S2_short_intra": books["S2_short_intra"],
             "choch_short": ch["choch_short"]}
    return bases, scores


def quintile_mask(score, start, which):
    """True where the LAGGED score sits in its top (or bottom) quintile, per symbol."""
    n, T = score.shape
    m = np.zeros((n, T), dtype=bool)
    for i in range(n):
        s = score[i, start - 1:T - 1]
        ok = np.isfinite(s)
        if ok.sum() < 100:
            continue
        lo, hi = np.quantile(s[ok], [0.2, 0.8])
        sel = (s >= hi) if which == "top" else (s <= lo)
        m[i, start:] = sel & ok
    return m


def main() -> int:
    rp, rc = R.load_full()
    panel, cleaned = R.subset(rp, rc, R.STRATA["ALL"])
    first, gap = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    T = panel.closes.shape[1]
    ppy = (T / int(first.sum())) * 252.0
    sess_end, _ = A.session_maps(first, T)
    vol, px, stamps = V.load_volume(panel)
    bod = V.bar_of_day(stamps)

    print("building 17 scores and 3 base books ...", flush=True)
    bases_all, scores_all = build_all(panel, cleaned, first, start, vol, px, bod)
    names = list(scores_all)
    masks = {(nm, w): quintile_mask(scores_all[nm], start, w)
             for nm in names for w in ("top", "bot")}
    filters = [("none", None)] + [(f"{nm}|{w}", (nm, w)) for nm in names
                                 for w in ("top", "bot")]
    print(f"  {len(names)} scores -> {len(filters)} filters "
          f"x {len(bases_all)} bases x 3 strata = "
          f"{len(filters) * len(bases_all) * 3} cells\n", flush=True)

    cells = {}
    for st in ("ALL", "LOW", "HIGH"):
        p, cl = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        keep = [panel.symbols.index(s) for s in p.symbols]
        borrow = R.borrow_vector(p.symbols)
        c2 = 2.0 * float(np.mean(p.cost_fraction) * 1e4)
        for bn, bbook in bases_all.items():
            base = bbook[keep]
            for fname, f in filters:
                pos = base if f is None else base * masks[f][keep]
                if not (pos != 0).any():
                    continue
                sc = R.score(p, pos, start, first, gap, ppy, borrow)
                tr = S.per_trade(pos, p.total_log_returns, start, sess_end)
                mv = float(tr.mean()) if tr.size else 0.0
                cells[f"{st}|{bn}|{fname}"] = {
                    "stratum": st, "base": bn, "filter": fname, "cost_bp": c2,
                    "exposure": sc["exposure"], "cagr": sc["cagr"],
                    "sharpe": sc["excess_sharpe"], "turnover": sc["turnover_per_year"],
                    "n_trades": int(tr.size), "move_bp": mv, "move_vs_cost": mv / c2,
                    "entries": sc["entries"], "min_per_sym": sc["min_entries_per_symbol"]}
        print(f"  {st} done ({len(cells)} cells so far)", flush=True)

    ranked = sorted(cells.items(), key=lambda kv: -kv[1]["sharpe"])
    print(f"\n{'=' * 100}\nSTAGE 1 -- {len(cells)} cells. Top 15 by excess Sharpe.\n{'=' * 100}")
    print(f"  {'cell':52s} {'Sharpe':>7s} {'CAGR':>8s} {'move':>8s} {'x cost':>7s} "
          f"{'expo':>6s} {'turn':>5s}")
    for k, c in ranked[:15]:
        print(f"  {k:52s} {c['sharpe']:+7.3f} {c['cagr']:+7.2%} {c['move_bp']:+7.2f}b "
              f"{c['move_vs_cost']:6.2f}x {c['exposure']:5.1%} {c['turnover']:5.0f}")

    by_move = sorted(cells.items(), key=lambda kv: -kv[1]["move_vs_cost"])
    print(f"\n  Top 10 by MOVE PER TRADE vs the cost bar -- the quantity that decides "
          f"viability:")
    for k, c in by_move[:10]:
        print(f"  {k:52s} {c['move_bp']:+7.2f}b {c['move_vs_cost']:6.2f}x  "
              f"CAGR {c['cagr']:+7.2%}  {c['n_trades']:,} trades")

    # ---- the best-of-N floor over the WHOLE search (D228) ----
    print(f"\ncomputing the best-of-{len(cells)} floor, {N_SIMS} shared-offset draws ...",
          flush=True)
    rng = np.random.default_rng(SEED)
    panels = {}
    for st in ("ALL", "LOW", "HIGH"):
        p, _ = ((panel, cleaned) if st == "ALL" else R.subset(rp, rc, R.STRATA[st]))
        panels[st] = (p, [panel.symbols.index(s) for s in p.symbols],
                      R.borrow_vector(p.symbols))
    keys = list(cells)
    best = np.empty(N_SIMS)
    for s in range(N_SIMS):
        off = rng.integers(1, T - start, size=len(panel.symbols))
        mx = -9e9
        for k in keys:
            c = cells[k]
            p, keep, borrow = panels[c["stratum"]]
            base = bases_all[c["base"]][keep]
            pos = base if c["filter"] == "none" else base * masks[
                tuple(c["filter"].split("|"))][keep]
            rot = np.zeros_like(pos)
            for i, j in enumerate(keep):
                rot[i, start:] = np.roll(pos[i, start:], int(off[j]))
            tot = X.signed_log_returns(p, rot, total_return=True)[start:]
            ex, _ = R.excess_vec(tot, rot, start, first, gap, ppy, borrow)
            mx = max(mx, R._sharpe(ex, ppy))
        best[s] = mx
        if (s + 1) % 50 == 0:
            print(f"  {s + 1}/{N_SIMS}", flush=True)
    floor = float(np.percentile(best, 95))

    top = ranked[0][1]
    print(f"\n{'=' * 100}")
    print(f"  BEST-OF-{len(cells)} FLOOR (p95): {floor:+.3f}")
    print(f"  best cell in the mine:           {top['sharpe']:+.3f}   ({ranked[0][0]})")
    print(f"  clears the floor: {'YES' if top['sharpe'] > floor else 'NO'}")
    print(f"  cells clearing the floor: "
          f"{sum(1 for _, c in cells.items() if c['sharpe'] > floor)} of {len(cells)}")
    print(f"  cells with move >= cost bar AND positive CAGR: "
          f"{sum(1 for _, c in cells.items() if c['move_vs_cost'] >= 1 and c['cagr'] > 0)}")
    print("=" * 100)

    json.dump({"n_cells": len(cells), "floor": floor, "n_sims": N_SIMS,
               "cells": cells,
               "top_by_sharpe": [k for k, _ in ranked[:25]],
               "top_by_move": [k for k, _ in by_move[:25]]},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
