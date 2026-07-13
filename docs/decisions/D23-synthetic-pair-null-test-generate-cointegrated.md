# D23 — Synthetic-pair null test: generate cointegrated-looking series with zero true edge; strategy must earn ~nothing on them

**Status:** Committed
**Date:** 2026-07-07
**Category:** Validation & research integrity
**Source:** Session 1 — initial design review

## Decision

Synthetic-pair null test: generate cointegrated-looking series with zero true edge; strategy must earn ~nothing on them.

## Rationale

The returns-shuffle Monte Carlo destroys the autocorrelation a mean-reversion strategy trades, so it can't distinguish edge from luck. Block bootstrap retained; synthetic null added as the stronger test.
