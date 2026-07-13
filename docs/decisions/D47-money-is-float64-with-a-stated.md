# D47 — Money is float64 with a stated reconciliation tolerance (default 1e-6), used by every "to the penny" test

**Status:** Committed
**Date:** 2026-07-07
**Category:** Testing
**Source:** Session 3 — final sweep

## Decision

Money is float64 with a stated reconciliation tolerance (default 1e-6), used by every "to the penny" test.

## Rationale

Penny-exact assertions on floats fail spuriously or pass falsely; the epsilon is a policy, not an accident.
