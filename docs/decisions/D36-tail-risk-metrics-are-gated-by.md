# D36 — Tail-risk metrics are gated by sample size: VaR/CVaR and extreme percentiles only report when observations support them, otherwise the tearsheet prints "insufficient data" — and Monte Carlo default n rises from 500 to ≥10,000 (seeded per D34)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Analytics
**Source:** Session 2 — full-framework review

## Decision

Tail-risk metrics are gated by sample size: VaR/CVaR and extreme percentiles only report when observations support them, otherwise the tearsheet prints "insufficient data" — and Monte Carlo default n rises from 500 to ≥10,000 (seeded per D34).

## Rationale

95% VaR from ~500 daily points estimates the 25th-worst day, and n=500 was an arbitrary number; simulations are cheap. Reporting numbers you shouldn't trust is worse than not reporting them — reviewers probe exactly these.
