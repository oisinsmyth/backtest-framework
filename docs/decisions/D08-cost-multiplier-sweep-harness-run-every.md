# D08 — Cost-multiplier sweep harness: run every backtest at 0.5×/1×/2×/4× the CostStack, report all four in the tearsheet

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Cost-multiplier sweep harness: run every backtest at 0.5×/1×/2×/4× the CostStack, report all four in the tearsheet.

## Rationale

For edges this thin, "does it survive 2× costs" is the single most informative output in the project — more valuable than any refinement to cost functional forms. Trivial once CostStack exists; first payoff of the refactor.
