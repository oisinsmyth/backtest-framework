# D42 — Intra-bar ambiguity convention: when two exits are touchable in the same bar (e.g. stop and limit/target both within the bar's range), assume the adverse one fills first

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 3 — final sweep

## Decision

Intra-bar ambiguity convention: when two exits are touchable in the same bar (e.g. stop and limit/target both within the bar's range), assume the adverse one fills first.

## Rationale

OHLC bars cannot tell you whether the high or low came first; without a stated convention the simulator silently picks the optimistic path. Conservative-path assumption is documented and tested, not implied.
