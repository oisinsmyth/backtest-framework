# D81 — Tail gating: ≥30 tail observations; Monte Carlo: seeded block bootstrap, n=10k

**Status:** Committed
**Date:** 2026-07-14
**Category:** Analytics
**Source:** Implementation session (Step 9)

## Decision

**Tail risk (`analytics/tail_risk.py`, D36):** VaR/CVaR report only when the tail
beyond the cutoff holds **≥ 30 observations** — a tail estimated from fewer than 30
points is an anecdote, not an estimate. At 95% confidence that means n ≥ 600; at
99%, n ≥ 3,000. This is deliberately stricter than the verification gate's 100-bar
case: D36's own rationale complains that ~500 daily points at 95% "estimates the
25th-worst day," so 500 is insufficient under this policy too (tested). The result
type is never None and never a silently-wrong number — `TailRiskResult` is either
values or an explicit insufficient-data marker whose message contains the minimum-n
arithmetic, and the tearsheet prints that message verbatim.

**Monte Carlo (`analytics/monte_carlo.py`, D34/D36):** seeded **block bootstrap**
(default block 20), default **n_sims = 10,000**, `seed` a required argument. Block
bootstrap rather than returns-shuffle because D23 already demoted the shuffle for
destroying the autocorrelation a mean-reversion strategy trades; this same function
is what Step 12's validation science reuses. Same seed → byte-identical percentile
table (tested as equality, not approx); the signature default and the module
constant are asserted together so neither can drift alone.

## Rationale

The 30-observation floor is a stated policy with a defensible statistical basis (the
usual small-sample rule of thumb applied to the tail itself, which is the sample
that matters), not a threshold reverse-engineered to pass the gate. Requiring the
seed positionally rather than defaulting it is D34 applied with the same
honesty-by-signature logic as D80's rf: reproducibility that depends on remembering
an optional argument isn't reproducibility.
