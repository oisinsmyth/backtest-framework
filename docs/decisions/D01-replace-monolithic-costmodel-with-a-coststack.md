# D01 — Replace monolithic CostModel with a CostStack (ordered list of composable cost bricks)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Replace monolithic CostModel with a CostStack (ordered list of composable cost bricks).

## Rationale

Real trading frictions (spread, impact, commission, financing, borrow, FX) are independent layers, not one number. Composing small bricks per backtest makes every friction individually swappable, testable, and comparable.
