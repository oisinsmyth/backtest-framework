# D40 — Property-based invariant tests on the simulator: cash never negative absent margin, every fill price within its bar's high–low range, buys+sells reconcile exactly to positions, NAV continuity across bars

**Status:** Committed
**Date:** 2026-07-07
**Category:** Testing
**Source:** Session 2 — full-framework review

## Decision

Property-based invariant tests on the simulator: cash never negative absent margin, every fill price within its bar's high–low range, buys+sells reconcile exactly to positions, NAV continuity across bars.

## Rationale

Invariants catch whole classes of bugs no example-based test anticipates, and the simulator is the component everything downstream trusts blindly.
