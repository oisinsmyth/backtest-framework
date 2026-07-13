# D09 — Add LIMIT_TRADE_THROUGH fill assumption (fill only if price exceeds limit by ε) alongside optimistic touch-fill

**Status:** Committed
**Date:** 2026-07-07
**Category:** Execution / fill logic
**Source:** Session 1 — initial design review

## Decision

Add LIMIT_TRADE_THROUGH fill assumption (fill only if price exceeds limit by ε) alongside optimistic touch-fill.

## Rationale

Touch ≠ fill (queue position) and bar-level limit fills are adversely selected. Keep both; compare sensitivity.
