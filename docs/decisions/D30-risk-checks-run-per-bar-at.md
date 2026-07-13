# D30 — Risk checks run per-bar at portfolio level, not only as pre-trade gates

**Status:** Committed
**Date:** 2026-07-07
**Category:** Portfolio layer
**Source:** Session 2 — full-framework review

## Decision

Risk checks run per-bar at portfolio level, not only as pre-trade gates.

## Rationale

Positions drift into violation via price moves with no order ever firing a check (a pair whose legs both moved can silently exceed gross exposure limits). Controls-engineering framing: safety interlocks run continuously, not only on operator commands. Brick: `RiskMonitor.evaluate(portfolio_state, bar)` called every bar by the engine; violations emit corrective orders or halt flags.
