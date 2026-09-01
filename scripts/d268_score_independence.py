"""D268 STEP 1 -- are the nine scores actually independent families?

    uv run python scripts/d268_score_independence.py

DESCRIPTIVE. No cell is scored, no book built, no forward return read. This
measures the correlation structure of the SCORES ONLY, and it exists to kill a
proposal cheaply if the premise is false.

THE PROPOSAL IT GATES
----------------------
The principal's: bucket strategies by type -- breakout, momentum, mean reversion,
trend -- and use AGREEMENT BETWEEN FAMILIES as the selectivity mechanism, rather
than the strength of any single signal. That is a genuinely different quantity
from D267's: it counts independent confirmations instead of grading magnitude, so
D267's failure does not carry over.

WHY IT MIGHT BE FALSE BEFORE IT IS TESTED
------------------------------------------
D218 measured Impulse MACD's acceleration rung against classic MACD's on
identical bars and found them to agree WITHIN 0.04 SHARPE -- "the whole apparatus
buys nothing over EMA(12) - EMA(26)". Two constructions sharing no arithmetic
produced the same signal.

**If the nine scores are three things wearing nine hats, then "three families
agree" is one family agreeing with itself, and a consensus rule built on it would
manufacture confidence from nothing.** That is the failure mode this file is for.

THE FAMILIES, DECLARED BEFORE THE CORRELATIONS ARE READ
--------------------------------------------------------
  ACCELERATION   impulse_hist, macd_hist
  LEVEL          impulse_md, impulse_nodz, macd_line
  MOMENTUM       trailing_return
  OSCILLATOR     rsi
  SLOPE          g_lo, g_min

Assigned by CONSTRUCTION -- what the arithmetic does -- not by how they behave,
so the measurement can contradict the taxonomy rather than confirm it.

THE BAR, STATED BEFORE THE RUN
-------------------------------
Scores are compared as RANKS within symbol, because a consensus rule would use
their ordering rather than their units, and Spearman is invariant to the
monotone rescalings that separate e.g. `md` from `mi - smma(close)`.

  * WITHIN a declared family, |rho| is EXPECTED to be high. That is not a defect.
  * BETWEEN families, |rho| >= 0.7 means the two are not distinct inputs, however
    different their arithmetic looks.
  * EFFECTIVE INDEPENDENT FAMILIES, by the participation ratio of the correlation
    matrix's eigenvalues. **If that comes in below 3, the consensus proposal is
    dead on arrival** -- there are not enough distinct opinions to take a vote.
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


C = _load("d267", "run_magnitude_calibration.py")
R, M, D = C.R, C.M, C.D

OUT = REPO / "data" / "d268_score_independence.json"

FAMILY = {
    "impulse_hist": "ACCELERATION", "macd_hist": "ACCELERATION",
    "impulse_md": "LEVEL", "impulse_nodz": "LEVEL", "macd_line": "LEVEL",
    "trailing_return": "MOMENTUM",
    "rsi": "OSCILLATOR",
    "g_lo": "SLOPE", "g_min": "SLOPE",
}
BETWEEN_FAMILY_LIMIT = 0.70
MIN_EFFECTIVE_FAMILIES = 3.0


def rankify(x):
    """Ranks within the finite entries, scaled to [0,1]. NaN preserved."""
    out = np.full(x.shape, np.nan)
    ok = np.isfinite(x)
    if ok.sum() < 2:
        return out
    v = x[ok]
    order = np.argsort(np.argsort(v))
    out[ok] = order / (len(v) - 1)
    return out


def main() -> int:
    raw_panel, raw_cleaned = R.load_full()
    panel, cleaned = R.subset(raw_panel, raw_cleaned, R.STRATA["ALL"])
    first, _ = D.session_structure(panel.dates)
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    sc = C.build_scores(panel, cleaned)
    names = list(C.SCORES)

    # Rank within symbol, then pool -- a consensus rule ranks per name.
    cols = []
    for n in names:
        per = [rankify(sc[n][i, start:]) for i in range(len(panel.symbols))]
        cols.append(np.concatenate(per))
    X = np.vstack(cols)
    ok = np.all(np.isfinite(X), axis=0)
    X = X[:, ok]
    print(f"{X.shape[1]:,} bars with all nine scores finite, "
          f"{len(panel.symbols)} symbols\n")

    Rm = np.corrcoef(X)          # Spearman, since the inputs are ranks
    print("SPEARMAN RANK CORRELATION between scores")
    print("        " + " ".join(f"{n[:7]:>8s}" for n in names))
    for i, n in enumerate(names):
        print(f"{n[:7]:>7s} " + " ".join(f"{Rm[i, j]:8.2f}" for j in range(len(names))))

    within, between = [], []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            same = FAMILY[names[i]] == FAMILY[names[j]]
            (within if same else between).append(
                {"a": names[i], "b": names[j], "rho": float(Rm[i, j]),
                 "family_a": FAMILY[names[i]], "family_b": FAMILY[names[j]]})

    print(f"\nWITHIN-family pairs:  n={len(within)}  "
          f"mean |rho| {np.mean([abs(p['rho']) for p in within]):.3f}")
    print(f"BETWEEN-family pairs: n={len(between)} "
          f"mean |rho| {np.mean([abs(p['rho']) for p in between]):.3f}")

    viol = sorted([p for p in between if abs(p["rho"]) >= BETWEEN_FAMILY_LIMIT],
                  key=lambda p: -abs(p["rho"]))
    print(f"\nBETWEEN-family pairs at |rho| >= {BETWEEN_FAMILY_LIMIT} "
          f"-- these are NOT distinct inputs: {len(viol)}")
    for p in viol:
        print(f"   {p['a']:16s} ({p['family_a']:12s}) vs {p['b']:16s} "
              f"({p['family_b']:12s})  rho {p['rho']:+.3f}")
    if not viol:
        print("   none")

    lam = np.maximum(np.linalg.eigvalsh(Rm), 0.0)
    eff = float(lam.sum() ** 2 / (lam ** 2).sum())
    print(f"\nEFFECTIVE INDEPENDENT SCORES (participation ratio): "
          f"{eff:.2f} of {len(names)}")
    print(f"  eigenvalues: " + " ".join(f"{v:.2f}" for v in sorted(lam)[::-1]))
    print(f"  variance in the first component: {max(lam) / lam.sum():.1%}")

    verdict = ("PROPOSAL IS VIABLE -- there are enough distinct opinions to take a vote"
               if eff >= MIN_EFFECTIVE_FAMILIES else
               "PROPOSAL IS DEAD ON ARRIVAL -- these are not independent families, "
               "and a consensus among them would be one signal agreeing with itself")
    print(f"\n  bar: effective >= {MIN_EFFECTIVE_FAMILIES:.1f}")
    print(f"  VERDICT: {verdict}")

    OUT.write_text(json.dumps(
        {"purpose": "gates the consensus proposal; scores nothing",
         "families": FAMILY, "names": names,
         "spearman": Rm.tolist(), "within": within, "between": between,
         "between_family_violations": viol,
         "effective_independent_scores": eff,
         "first_component_share": float(max(lam) / lam.sum()),
         "bar_effective": MIN_EFFECTIVE_FAMILIES, "verdict": verdict}, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
