# D11 — Rename "VWAP" fill assumption to TYPICAL_PRICE_OPTIMISTIC

**Status:** Committed
**Date:** 2026-07-07
**Category:** Execution / fill logic
**Source:** Session 1 — initial design review

## Decision

Rename "VWAP" fill assumption to TYPICAL_PRICE_OPTIMISTIC.

## Rationale

(H+L+C)/3 is typical price, not VWAP, is unknowable intra-bar (mild look-ahead), and labelling it "realistic" is dishonest. Keep as sensitivity bound only.
