# D34 — Explicit RNG seed policy: every stochastic component (Monte Carlo shuffle, block bootstrap, synthetic nulls) takes a seed parameter; seeds are logged in the TrialRegistry

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 2 — full-framework review

## Decision

Explicit RNG seed policy: every stochastic component (Monte Carlo shuffle, block bootstrap, synthetic nulls) takes a seed parameter; seeds are logged in the TrialRegistry.

## Rationale

"deterministic simulator" means nothing for reproducibility if the analytics layer is silently nondeterministic. Re-running a logged trial must reproduce it to the penny, randomness included.
