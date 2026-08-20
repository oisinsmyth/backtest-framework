# D126 — The DSR pool is strategy configurations; convention and cost sensitivities are re-pricings, not trials

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Crypto pairs study session

## Decision

The BTC/ETH pairs study computes a DSR per cost tier whose trial pool {SRn} is every
variant in the **`grid`** and **`gross`** groups — 14 configurations (12 parameter cells ×
1, plus 2 `leg_weight` settings). The **`convention`** group (fill timing, stitching mode)
and the **`cost`** group (borrow rate, carry-free) are excluded.

Pool membership is decided on identity fields written into every logged config —
`row_kind == "variant"`, `group in ("grid", "gross")`, matching `tier`, matching trial-id
prefix — and never on the presence of a metric (D98's rule). Per-window rows carry
`row_kind == "window"` and are excluded by the same predicate. Units are per-period
(daily, non-annualised) for the logged metric, the observed SR and T alike, per D98's
contract; a regression test pins `sharpe_daily == sharpe_annual / √periods_per_year`.

The variant's own `describe()` publishes `in_dsr_pool`, so a reader of a single registry
row can tell whether it counted.

## Rationale

D116 established that for a parameter-swept study N is the number of **configurations**
tried, not the number of windows — the pairs studies v1–v3 pooled windows because they
varied no parameters, and their windows genuinely were their trials. This study sweeps 12
grid cells and 3 gross levels, so D116's pool is the right one.

The new question is what to do with the other seven variant rows, and D98 already answers
it by analogy. D98 removed cost-multiplier re-runs from the pairs studies' pool on the
grounds that *the same window re-run at scaled costs is a sensitivity point, not an
additional independent trial* — counting it inflated N with near-perfectly-correlated
entries and distorted V[{SRn}] in both directions. `fill_close`, `stitch_chained`,
`borrow_0pct`, `borrow_25pct` and `carry_free` are the same thing on different axes: the
same strategy configuration, re-priced or re-stitched. They answer "how much does this
convention matter?", not "here is another thing I tried that might have been the best".

`leg_weight`, by contrast, **is** in the pool, and the distinction is worth being explicit
about because it is the only judgement call here. Gross exposure changes what the strategy
*does* — it changes the position, the risk, and the P&L path — rather than changing what
that behaviour is charged for. D96 treated `leg_weight` as the study variable of its own
study, not as a cost sensitivity, and that reading is carried forward.

**What this pool cannot see, and why the numbers are unusable in the flattering
direction.** N counts 14 configurations. It does not count the choice of BTC/ETH — a pair
picked a priori for its fame, with no selection step for D29's correction to work on — nor
the choice of crypto, nor the choice of the two crypto assets that survived to 2025. Those
are the largest terms and the registry cannot see any of them. The standing reading,
inherited from D90 and D116 and restated once more: **DSR < 0.95 means "no demonstrated
edge"; DSR ≥ 0.95 does not mean the reverse.**

In this study every DSR comes out below 0.01, because the observed Sharpe is decisively
negative at every tier and the deflation barely has to do any work. That makes the pool
choice practically inconsequential *here* — which is precisely the reason to record it now
rather than when it matters. The instrument has to be built correctly on the day the sign
is wrong, not on the day it is convenient.
