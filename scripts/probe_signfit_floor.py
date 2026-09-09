"""A best-of-N permutation floor prices SELECTION. It is blind to SIGN-FITTING.

    uv run python scripts/probe_signfit_floor.py

NOTHING HERE TOUCHES A FIXTURE. No cell is scored, no book is built, no data is read. It is a
pure sampling-theory check of a claim that arrived in an external-evidence brief
(working/leads/C1-combination.md) and that, if true, scopes a method this repo uses everywhere.

THE CLAIM, AND WHY IT COULD NOT BE LEFT AS A QUOTE. CLAUDE.md records the exact permutation
floor built in run_d395_chop.py -- best-of-N for a cell picked from a grid, no independence
assumption -- and says it "should replace normal-approximation floors programme-wide". The brief
says that floor has a blind spot: it prices the bias from CHOOSING among candidates, and not the
bias from ORIENTING each candidate in-sample. The second exists even when nothing is selected.

THE ARITHMETIC. For k uncorrelated equal-volatility signals combined equal-weight,
t_combo = sqrt(k) * mean(t_i). Signing each signal by its own in-sample t replaces t_i with
|t_i|, so under the null of k WORTHLESS signals:

    E[t_combo] = sqrt(2/pi) * sqrt(k)        sd[t_combo] = sqrt(1 - 2/pi)     -- free of k

The sd is k-free because the sqrt(k) multiplier and the 1/sqrt(k) of the mean cancel exactly.
That is the whole mechanism: ORTHOGONALITY MULTIPLIES DETECTABILITY BY sqrt(k), and sign-fitting
hands you the same sqrt(k) for nothing.

WHAT THIS FILE ESTABLISHES, by closed form AND by 200,000-draw simulation which must agree:

  1. The brief's three quoted critical values reproduce: 3.94 at k=13.5, 4.20 at k=16,
     6.75 at k=52 (this file gets 3.92 / 4.18 / 6.75 from the closed form and 3.91 / 4.22 /
     6.77 from simulation).
  2. THE POINT. At k=16 a best-of-N selection floor sits at p95 = 2.95 while the sign-fitted
     composite's own null sits at p95 = 4.23. A COMPOSITE OF SIXTEEN PURE-NOISE SIGNALS WOULD
     CLEAR THE SELECTION FLOOR COMFORTABLY. Selection and sign-fitting are different biases and
     a floor for one is not a floor for the other.
  3. Pre-declaring every sign in writing removes the absolute value and returns the null to
     standard normal: p95 = 1.64. That is worth a factor of ~2 in the hurdle, and it is a
     writing discipline rather than a computation.

SCOPE, STATED SO THIS IS NOT OVER-READ. This does not say the D395 floor is wrong -- it is
correct for what it prices, and it remains the right instrument for a cell picked from a grid.
It says the floor must be EXTENDED whenever a construction orients its own components in
sample: the null must draw synthetic components and sign them the same way the treatment does.
The assumptions here are the brief's own -- uncorrelated, equal-volatility components -- and
real signals are neither, so the numbers are a calibration, not a verdict on any actual study.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "signfit_floor_probe.json"

E_ABS = float(np.sqrt(2 / np.pi))          # E|Z|
SD_ABS = float(np.sqrt(1 - 2 / np.pi))     # sd|Z|
DRAWS = 200_000
SEED = 20260909
BRIEF = {13.5: 3.94, 16: 4.20, 52: 6.75}   # the values to reproduce


def closed_form(k: float) -> dict:
    mean = E_ABS * np.sqrt(k)
    return {"k": k, "null_mean": mean, "null_sd": SD_ABS, "crit_5pct": mean + 1.645 * SD_ABS}


def main() -> None:
    rng = np.random.default_rng(SEED)
    print(f"E|Z| = {E_ABS:.5f}   sd|Z| = {SD_ABS:.5f}   ({DRAWS:,} draws, seed {SEED})\n")

    print(f"{'k':>6}{'null mean':>12}{'null sd':>10}{'5% crit':>10}{'brief':>8}{'sim p95':>10}")
    rows = {}
    for k, claimed in BRIEF.items():
        cf = closed_form(k)
        ki = int(round(k))
        sim = np.sqrt(ki) * np.abs(rng.standard_normal((DRAWS, ki))).mean(axis=1)
        p95 = float(np.quantile(sim, 0.95))
        # [X] closed form and simulation must agree, or one of them is wrong
        assert abs(sim.mean() - E_ABS * np.sqrt(ki)) < 0.02, "closed form and simulation disagree"
        rows[str(k)] = {**cf, "brief_claim": claimed, "sim_p95": p95,
                        "sim_mean": float(sim.mean()), "sim_k_used": ki}
        print(f"{k:>6}{cf['null_mean']:>12.3f}{cf['null_sd']:>10.3f}"
              f"{cf['crit_5pct']:>10.2f}{claimed:>8.2f}{p95:>10.2f}")

    print("\nTHE POINT -- what a SELECTION-only floor sees, at k = 16:")
    k = 16
    t = rng.standard_normal((DRAWS, k))
    best = float(np.quantile(np.abs(t).max(axis=1), 0.95))
    combo = float(np.quantile(np.sqrt(k) * np.abs(t).mean(axis=1), 0.95))
    pre = float(np.quantile(np.sqrt(k) * rng.standard_normal((DRAWS, k)).mean(axis=1), 0.95))
    print(f"  best-of-{k} |t|, i.e. what a best-of-N floor prices : p95 = {best:.2f}")
    print(f"  sign-fitted equal-weight composite, same k noise    : p95 = {combo:.2f}")
    print(f"  -> the composite's null is {combo - best:+.2f} ABOVE the selection floor, so a")
    print(f"     composite of {k} PURE-NOISE signals clears that floor comfortably.")
    print(f"  signs PRE-DECLARED in writing (null returns to normal): p95 = {pre:.2f}")

    # [X] the finding itself, asserted so a future change to this file cannot quietly lose it
    assert combo > best + 0.5, "the whole finding is that the composite null EXCEEDS best-of-N"

    OUT.write_text(json.dumps({
        "claim_source": "working/leads/C1-combination.md (external brief), verified here",
        "E_abs_Z": E_ABS, "sd_abs_Z": SD_ABS, "draws": DRAWS, "seed": SEED,
        "reproduction_of_brief": rows,
        "k16": {"best_of_N_p95": best, "signfit_composite_p95": combo,
                "signs_predeclared_p95": pre},
        "scope": "assumes uncorrelated equal-volatility components, the brief's own assumptions; "
                 "real signals are neither, so these are calibration values, not a verdict",
    }, indent=2))
    print(f"\nwritten {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
