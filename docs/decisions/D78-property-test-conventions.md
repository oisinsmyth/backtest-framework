# D78 — Property-test conventions: derandomized hypothesis, shadow accountant, reset-guarantee reinterpretation

**Status:** Committed
**Date:** 2026-07-14
**Category:** Testing
**Source:** Implementation session (Step 8)

## Decision

`tests/property/test_simulator_invariants.py` (D40) runs hypothesis with
`derandomize=True`: the suite is byte-deterministic in CI, satisfying D34's
reproducibility intent with hypothesis owning the seeding rather than a hand-rolled
seed parameter. Eight invariants across random price paths and weight schedules:
cash ≥ 0 absent margin; fills at the bar's close (and `stop_fill_price` ∈ [low, high]
for random bars — the one component that chooses prices); Σ(fill quantities) ==
final position *exactly*; the shadow-accountant leak tests (zero costs → NAV change
== position × Δprice exactly; flat commission → total NAV gap == $10 × fill count);
identical-runs-identical; equity-curve sha256 stable across reruns.

**Reset reinterpretation (per the plan, D53 discipline):** the gate's
"broker.reset() → state identical to fresh construction" names a class that doesn't
exist — `run_backtest` constructs fresh `PortfolioState`/virtual books per call and
the sweep takes strategy factories (D68). The guarantee the gate protects (no state
leakage between walk-forward runs) is asserted directly: two identical calls produce
identical equity curves and fills.

## Rationale

Derandomize-over-seed-parameter: a flaky property suite that fails only on some seeds
trains people to re-run until green — determinism keeps every failure reproducible
and every pass meaningful. The shadow accountant is the strongest leak detector
available without duplicating the engine: with costs at zero the *only* legal source
of NAV change is price movement on held positions, so any drift is a leak by
definition, on every random path tried.
