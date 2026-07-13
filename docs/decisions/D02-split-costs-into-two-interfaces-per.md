# D02 — Split costs into two interfaces: per-trade costs (charged on fills) vs carry costs (charged per bar on open positions)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Split costs into two interfaces: per-trade costs (charged on fills) vs carry costs (charged per bar on open positions).

## Rationale

They are mechanically different things with different hook points in the simulator. Per-trade: spread, impact, commission, FX conversion. Carry: margin interest, borrow fees, dividend flows, funding rates. This distinction is itself an important trading mental model.
