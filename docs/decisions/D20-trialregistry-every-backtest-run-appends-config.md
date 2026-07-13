# D20 — TrialRegistry: every backtest run appends config hash + params + headline metrics to local SQLite/CSV. Build before any real experimentation

**Status:** Committed (urgent)
**Date:** 2026-07-07
**Category:** Validation & research integrity
**Source:** Session 1 — initial design review

## Decision

TrialRegistry: every backtest run appends config hash + params + headline metrics to local SQLite/CSV. Build before any real experimentation.

## Rationale

Deflated Sharpe requires the number of trials attempted, and that count cannot be reconstructed retroactively. The one component that can't be retrofitted.
