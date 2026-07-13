# D35 — Configuration becomes declarative: SimConfig and strategy configs are plain data (dicts/strings — e.g. `{"cost_model": "ibkr_v1"}`), with factories constructing live objects from them

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 2 — full-framework review

## Decision

Configuration becomes declarative: SimConfig and strategy configs are plain data (dicts/strings — e.g. `{"cost_model": "ibkr_v1"}`), with factories constructing live objects from them.

## Rationale

The TrialRegistry's "config hash" is impossible while configs hold live objects (cost model instances, timedeltas, CostStacks) that don't serialise or hash stably. Declarative config makes trials hashable, diffable, comparable, and re-runnable — load-bearing for D20, D21, and D34.
