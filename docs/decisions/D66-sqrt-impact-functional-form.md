# D66 — Sqrt impact: fraction ∝ √Q, dollars ∝ Q^1.5; static σ/ADV params for now

**Status:** Committed / Deferred
**Date:** 2026-07-13
**Category:** Cost architecture
**Source:** Implementation session (Step 5)

## Decision

`SqrtImpact` (`costs/equity_bricks.py`) implements the square-root law as:

    impact_fraction = coefficient × σ_daily × √(|Q| / ADV)     [scales as √Q]
    dollar cost     = impact_fraction × |Q × price|             [scales as Q^1.5]

with `coefficient` defaulting to 1.0 (the order-of-magnitude Y ≈ 1 convention from
the empirical literature). σ and ADV are **static per-symbol construction
parameters** (`ImpactParams(sigma_daily, adv_shares)`), validated at construction
(σ > 0, ADV > 0 — fail at build time, not bar 3,000); an unknown symbol or an
instrument without a `symbol` attribute raises a loud `ValueError` naming the
problem. No code path returns a silent zero (D48).

**Gate clarification (deliberate, in the open — same discipline as D53):** the Step 5
U-gate says "doubling quantity multiplies impact cost by √2." Total dollar cost
scaling as √Q would require the *price concession itself* to shrink per-share as the
order grows, which is not the square-root law — the standard model has the
per-dollar impact fraction scale as √Q, making total dollars scale as Q^1.5. D3's
own rationale ("the industry-standard model reviewers/interviewers expect") is the
controlling intent, so the √2 assertion applies to `impact_fraction()` (exposed as
its own method) and the total is asserted at 2√2. Both scalings are tested, so the
distinction is checked rather than narrated.

**Deferred, per R3:** estimating σ and ADV from market data. D3 says "requires ADV
field in data layer"; that field was explicitly cut from the unhardened data source
(D59) and belongs with Step 7's snapshots, where the estimation window can obey D44's
no-same-bar-lookahead rule. Static params keep the brick honest now — the numbers are
visibly config, not silently derived.

## Rationale

The alternative reading — implement total dollars ∝ √Q because the gate's sentence
says "cost" — would produce a model no reviewer would recognize, defeating D3's
stated purpose. When the letter of a gate and the intent of its decision conflict,
the resolution gets written down and tested on both sides of the distinction, not
picked silently. Static-params-over-estimation follows Pillar 5: an estimation
pipeline built before snapshots exist would be speculative plumbing feeding a brick
whose calibration nobody can yet verify.
