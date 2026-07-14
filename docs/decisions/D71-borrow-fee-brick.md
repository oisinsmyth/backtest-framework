# D71 — BorrowFee brick: shorts pay, longs free

**Status:** Committed
**Date:** 2026-07-14
**Category:** Cost architecture
**Source:** Implementation session (Step 6)

## Decision

`BorrowFee(annual_rate=0.0025)` in `costs/equity_bricks.py`: a per-leg carry brick
charging `annual_rate × max(−base_amount, 0)` over the calendar-day gap (D33,
ACT/365 per D51) — the engine hands per-leg bricks each leg's *signed* notional, so
`max(−base, 0)` isolates short exposure exactly: shorts pay, longs pay nothing, flat
pays nothing. Default 0.25%/yr is general-collateral territory for liquid ETFs;
hard-to-borrow rates are a config change, and per-symbol borrow rates are a future
refinement if a strategy ever shorts anything less liquid than a sector ETF.

## Rationale

The pairs strategy's short leg pays stock borrow continuously, and no existing brick
had the right shape: `FlatRateCarry` charges on *signed* notional (a long leg would
absurdly earn the borrow rate), and `MarginInterest` is portfolio-level (D67).
Borrow is genuinely per-leg and one-sided — D1's own brick list names it as its own
friction. Ten lines against the existing `CarryCostBrick` interface, golden-tested on
both signs; the shape (shorts-only) matters more than the rate for the cost sweep's
purpose.
