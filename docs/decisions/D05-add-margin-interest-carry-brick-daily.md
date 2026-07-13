# D05 — Add margin interest carry brick: daily rate on (gross exposure − capital) when positive

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Add margin interest carry brick: daily rate on (gross exposure − capital) when positive.

## Rationale

Market-neutral pairs run ~200% gross exposure, IBKR charges ~6%/yr on small balances, and for 10–50bps/trade edges financing drag is first-order. Currently modelled as zero.
