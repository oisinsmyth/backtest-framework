"""What happens to effective breadth as the universe grows to hundreds of names.

    uv run python scripts/project_breadth_curve.py [--json]

THE QUESTION
------------
"What would 1000 symbols look like?" Headcount is the one axis this programme has
already measured and been surprised by, so this measures the CURVE rather than
arguing about the endpoint.

`docs/FINDINGS.md` §4 states the result in one line: *"going from 57 to 486 ETFs
LOWERED effective breadth"*, and *"Effective independent instruments saturate at
1/rho regardless of n"*. This reproduces that on a named build and extends it, so the
shape of the curve is visible instead of just its two endpoints.

WHAT IS MEASURED
----------------
On `etf_wide_daily_raw` (551 symbols, daily, 2010-2026) -- the largest committed
universe here, and the closest available analogue to "a lot of instruments":

  N_eff(rho)  N / (1 + (N-1)*rho_bar)   EXACTLY the equal-weight variance reduction
  PR          (sum L)^2 / sum(L^2)      eigen-directions carrying variance

for N drawn at random from the universe, repeated, so the curve is an average over
subsets rather than one lucky draw. Both measures are carried because
`project_futures_breadth.py` found they DISAGREE about whether a weakly-correlated
block is worth adding, and that disagreement is the whole reason to look at a curve.

THE PROXY CAVEAT, AGAIN AND UNCHANGED
-------------------------------------
ETFs are not futures, and a 551-ETF universe is more internally correlated than a
1,592-product futures complex would be. What transfers is the SHAPE -- saturation,
and the sign of the marginal name -- not the level. Acquisition planning only. This
opens and closes nothing.
"""

from __future__ import annotations

import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "etf_wide_daily_raw.csv.gz"
OUT = REPO / "data" / "breadth_curve.json"

SEED = 20260910
DRAWS = 40
GRID = [2, 4, 8, 16, 32, 41, 64, 128, 256, 400]

# THE WINDOW IS CHOSEN FIRST, THEN SYMBOLS ARE ADMITTED TO IT.
# The naive version of this took the intersection of every symbol's dates and got a
# 702-day window in 2015-2017 -- no 2020, no recent era, and correlations from one
# quiet regime. Correlation is exactly the quantity that moves in a crisis, so a
# breadth curve measured on a window with no crisis in it is worthless. The grid is
# SPY's trading days over the window below, and a symbol is admitted only if it
# quotes on essentially all of them. Nothing is forward-filled.
WINDOW = ("2011-01-03", "2026-08-26")
GRID_SYMBOL = "SPY"
MIN_COVERAGE = 0.995


def load_returns() -> tuple[dict[str, np.ndarray], list[str]]:
    by_sym: dict[str, dict[str, float]] = {}
    with gzip.open(FIXTURE, "rt") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split(",")
            d = p[0][:10]
            if WINDOW[0] <= d <= WINDOW[1]:
                by_sym.setdefault(p[1], {})[d] = float(p[5])
    dates = sorted(by_sym[GRID_SYMBOL])
    need = int(len(dates) * MIN_COVERAGE)
    out = {}
    for s, v in by_sym.items():
        if len(set(v) & set(dates)) < need:
            continue
        px = np.array([v.get(d, np.nan) for d in dates])
        if np.isnan(px).any() or (px <= 0).any():
            continue
        out[s] = np.diff(np.log(px))
    return out, dates


def measures(R: np.ndarray) -> tuple[float, float, float]:
    n = R.shape[0]
    if n < 2:
        return 1.0, 1.0, float("nan")
    C = np.corrcoef(R)
    iu = np.triu_indices(n, 1)
    rho = float(np.mean(C[iu]))
    n_eff = n / (1.0 + (n - 1) * rho)
    lam = np.clip(np.linalg.eigvalsh(C), 0, None)
    pr = float(lam.sum() ** 2 / (lam ** 2).sum())
    return n_eff, pr, rho


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rets, dates = load_returns()
    syms = sorted(rets)
    M = np.vstack([rets[s] for s in syms])
    print(f"{FIXTURE.name}: {len(syms)} symbols, {dates[0]}..{dates[-1]}, "
          f"{M.shape[1]:,} common days\n")

    rng = np.random.default_rng(SEED)
    rows = []
    print(f"  {'N':>5}{'rho_bar':>10}{'N_eff':>9}{'PR':>8}{'N_eff/N':>10}{'PR/N':>8}")
    for n in GRID:
        if n > len(syms):
            continue
        ne, pr, rh = [], [], []
        for _ in range(DRAWS):
            idx = rng.choice(len(syms), size=n, replace=False)
            x, y, z = measures(M[idx])
            ne.append(x); pr.append(y); rh.append(z)
        r = {"n": n, "rho_bar": float(np.mean(rh)), "n_eff": float(np.mean(ne)),
             "pr": float(np.mean(pr)), "n_eff_sd": float(np.std(ne)), "pr_sd": float(np.std(pr))}
        rows.append(r)
        print(f"  {n:>5}{r['rho_bar']:>10.3f}{r['n_eff']:>9.2f}{r['pr']:>8.2f}"
              f"{r['n_eff']/n:>10.3f}{r['pr']/n:>8.3f}")

    full_ne, full_pr, full_rho = measures(M)
    print(f"\n  ALL {len(syms)} symbols: rho_bar {full_rho:.3f}, N_eff {full_ne:.2f}, PR {full_pr:.2f}")
    print(f"  saturation ceiling 1/rho_bar = {1/full_rho:.2f}")

    # The marginal name: what does doubling the universe actually buy?
    print(f"\n  {'from -> to':16}{'dN_eff':>9}{'dPR':>8}   per name added")
    marg = []
    for i in range(1, len(rows)):
        a0, b0 = rows[i - 1], rows[i]
        d_ne, d_pr = b0["n_eff"] - a0["n_eff"], b0["pr"] - a0["pr"]
        added = b0["n"] - a0["n"]
        marg.append({"from": a0["n"], "to": b0["n"], "d_n_eff": d_ne, "d_pr": d_pr,
                     "d_pr_per_name": d_pr / added})
        print(f"  {str(a0['n']) + ' -> ' + str(b0['n']):16}{d_ne:>9.2f}{d_pr:>8.2f}   "
              f"{d_pr / added:+.4f} PR/name")

    if a.json:
        OUT.write_text(json.dumps({
            "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "purpose": "acquisition planning: does headcount buy breadth. Not a study.",
            "fixture": FIXTURE.name, "n_symbols": len(syms),
            "window": [dates[0], dates[-1]], "n_days": int(M.shape[1]),
            "seed": SEED, "draws_per_point": DRAWS,
            "curve": rows, "marginal": marg,
            "full_universe": {"n": len(syms), "rho_bar": full_rho, "n_eff": full_ne, "pr": full_pr},
            "ceiling_1_over_rho": 1 / full_rho,
        }, indent=1) + "\n", encoding="utf-8")
        print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
