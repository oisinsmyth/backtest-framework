# D03 — Add square-root market impact brick (cost ∝ σ√(Q/ADV)); demote vol-proportional slippage to "another brick in the drawer"

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Add square-root market impact brick (cost ∝ σ√(Q/ADV)); demote vol-proportional slippage to "another brick in the drawer".

## Rationale

The vol-proportional model ranks instruments by the wrong property (volatility instead of liquidity), overcharges liquid ETFs ~20×, and uses an invented constant (k=0.1). Sqrt impact is the industry-standard model reviewers/interviewers expect. Requires ADV field in data layer.
