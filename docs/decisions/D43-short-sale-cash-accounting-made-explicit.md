# D43 — Short-sale cash accounting made explicit: short proceeds credit cash but the margin requirement locks equivalent buying power; NAV = cash + longs − |shorts|, defined in one place and tested

**Status:** Committed
**Date:** 2026-07-07
**Category:** Portfolio layer
**Source:** Session 3 — final sweep

## Decision

Short-sale cash accounting made explicit: short proceeds credit cash but the margin requirement locks equivalent buying power; NAV = cash + longs − |shorts|, defined in one place and tested.

## Rationale

"free" short proceeds funding new longs is the single most common silent simulator bug, and the current PortfolioState design never states its policy.
