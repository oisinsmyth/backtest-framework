# D90 — Study DSR methodology: registry-fed N and V; pair-level multiplicity as an explicit optimism caveat

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Phase G kickoff)

## Decision

The study's DSR uses `deflated_sharpe_from_trials` (D86) against the study's own
TrialRegistry: N = logged backtests (windows × multipliers = 175 for study v1), V =
variance of per-window daily Sharpes across those trials; the observed Sharpe,
skew, and kurtosis come from the stitched 1× OOS returns. Each study run uses a
dedicated registry file so N is deterministic and the artifact reproducible.

**The caveat is part of the method, not a footnote**: registry-N counts backtests
run, but each window *scored 1,596 candidate pairs* to choose its top 5 — selection
breadth the registry-N does not capture. The study doc states this directly: the
reported DSR is therefore optimistic, so DSR < 0.95 read as "no demonstrated edge"
is conservative in the safe direction, while a hypothetical DSR ≥ 0.95 could NOT be
taken at face value without accounting for pair-level multiplicity. (Study v1's
actual DSR = 0.0000, so the safe direction is the operative one.)

## Rationale

Folding pair-level multiplicity into N would require a defensible model of the
dependence between 1,596 overlapping pair-scores — genuine research methodology work
that belongs in the Phase G writeup, not a silent parameter choice inside a runner
script. Stating the direction of the bias (optimistic) and the safe interpretation
rule is the honest interim position: it makes the number unusable for overclaiming
while keeping it usable for what study v1 actually concluded — the naive
Gatev/z-score approach on this universe has no edge that survives costs, a
conclusion the bias direction only strengthens.
