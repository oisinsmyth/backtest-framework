# D13 — CostStacks are per-instrument-class

**Status:** Committed
**Date:** 2026-07-07
**Category:** Instruments
**Source:** Session 1 — initial design review

## Decision

CostStacks are per-instrument-class.

## Rationale

Frictions genuinely differ: equity (tight spread, per-share commission, borrow/dividends), options (huge %-of-premium spread, per-contract commission, theta), crypto (%maker/taker fee, funding rate), FX (spread-only, rollover). Each cell of that matrix is a brick the instrument class declares.
