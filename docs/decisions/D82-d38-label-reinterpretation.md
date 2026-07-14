# D82 — D38 reinterpreted: no sector momentum exists; the label convention is enforced on what does

**Status:** Committed
**Date:** 2026-07-14
**Category:** Analytics
**Source:** Implementation session (Step 9)

## Decision

D38 requires the sector momentum strategy to carry a learning/reference label in its
docstring and README, enforced by a grep-test. **No sector momentum strategy exists
in this repository** — the original design docs were written against a pre-framework
codebase that had one; this implementation started from the doc suite alone (the
same history gap D53 hit with the "pre-refactor engine").

The gate's intent — strategies that don't belong to the market-neutral thesis carry
an explicit honest label, and a test greps for it so labels can't rot — is enforced
on the strategies that do exist (`tests/unit/test_strategy_labels.py`):
`ScheduledWeightStrategy` must self-describe as a toy/reference,
`ZScorePairsStrategy` as the honest-minimum, explicitly-not-Phase-G strategy, and a
third test fails the moment any new module appears under
`backtest_framework.strategies` without being registered — so a future directional
strategy cannot land unlabelled.

## Rationale

Writing a sector momentum strategy just to label it would be inventing a liability
to satisfy a gate about acknowledging liabilities. The enforcement mechanism (grep
the docstrings, fail on unregistered strategy modules) is the durable part of D38,
and it's now in place waiting for the strategy the original docs assumed — the label
requirement will bind the day it's needed.
