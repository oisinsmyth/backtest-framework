# D04 — Model IBKR's actual commission schedule (per-share, exchange fees, minimums) instead of flat bps + £1 min

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Model IBKR's actual commission schedule (per-share, exchange fees, minimums) instead of flat bps + £1 min.

## Rationale

The target broker is known and per-share pricing diverges from bps pricing by up to ~70× depending on share price. Free accuracy.
