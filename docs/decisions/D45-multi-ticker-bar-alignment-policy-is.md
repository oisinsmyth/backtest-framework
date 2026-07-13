# D45 — Multi-ticker bar alignment policy is explicit: pairs/multi-leg strategies use inner-join alignment; a missing bar on one leg means no trading that bar (carry still accrues)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Data layer
**Source:** Session 3 — final sweep

## Decision

Multi-ticker bar alignment policy is explicit: pairs/multi-leg strategies use inner-join alignment; a missing bar on one leg means no trading that bar (carry still accrues).

## Rationale

Forward-filling fabricates prices that fills then execute against, and unstated alignment is where pairs backtests quietly diverge from reality.
