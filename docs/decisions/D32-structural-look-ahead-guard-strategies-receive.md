# D32 — Structural look-ahead guard: strategies receive a `DataView` accessor that physically cannot return bars beyond the current index and raises if asked — the full DataFrame is never reachable from strategy code

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 2 — full-framework review

## Decision

Structural look-ahead guard: strategies receive a `DataView` accessor that physically cannot return bars beyond the current index and raises if asked — the full DataFrame is never reachable from strategy code.

## Rationale

Slicing-by-convention (`iloc[:i+1]`) is an honor system; one careless reference to the underlying frame (or one 6:50am mistake) silently invalidates every result. The framework's entire value proposition is trustworthy answers; trust must be enforced by structure, not agreement.
