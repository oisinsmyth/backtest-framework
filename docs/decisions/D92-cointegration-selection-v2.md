# D92 — Study v2 selection: Gatev prefilter → EG β coherence window → ADF rank; one variable per version

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (study v2)

## Decision

`research/cointegration.py::CointegrationSelector`: Gatev-score all C(n,2) pairs
(`n_pairs_tested` remains the full count, D29) → take the closest 50 → fit the
Engle-Granger step-1 regression per candidate → **discard pairs whose β falls
outside [0.7, 1.3]** → rank survivors by ADF statistic, take top-N.

The β window is a *coherence* filter, not a statistical one: the strategy trades the
1:1 spread ln A − ln B, so stationarity evidence about ln A − β·ln B with β far from
1 concerns a spread we do not trade. β is logged per selected pair (it directly
informs a future β-hedged study v3) but deliberately NOT traded.

**One variable per study version**: v2 changes selection only — trading, costs,
windows, and every parameter are byte-identical to v1 (`run_pairs_study` gained an
optional `selector` arg whose `None` default preserves v1 exactly). The v1→v2 delta
is therefore attributable to selection and nothing else.

## Rationale

Study v1 showed Gatev distance selects pairs that *tracked* without asking whether
their spread *mean-reverts* — the score literally cannot distinguish a stationary
spread from a slowly-diverging one. Cointegration filtering is the literature's
answer, and the one-variable discipline is what makes the resulting comparison
science rather than anecdote. **The outcome vindicated both choices**: gross edge
rose from +3.45% to +19.03% (selection alone), turned profitable at 0.5× costs
(+5.70%), and still failed at full retail costs (−6.43%) — the cleanest possible
evidence for the "edge exists but doesn't clear retail frictions" analysis the
Phase G writeup centers on.
