# D39 — Golden-master tests: at least one hand-computed tiny scenario (≈5 bars, 2 trades, known costs, weekend gap included) asserted to the penny

**Status:** Committed
**Date:** 2026-07-07
**Category:** Testing
**Source:** Session 2 — full-framework review

## Decision

Golden-master tests: at least one hand-computed tiny scenario (≈5 bars, 2 trades, known costs, weekend gap included) asserted to the penny.

## Rationale

Unit tests verify the code does what the code says, not that the simulator is right; a scenario verified by hand arithmetic is ground truth. The weekend gap doubles as the regression test for D33.
