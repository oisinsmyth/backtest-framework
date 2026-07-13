# D41 — Cross-engine validation: run one identical strategy on identical data through an established engine (backtesting.py or vectorbt) and reconcile every penny of divergence, documented in the repo

**Status:** Committed
**Date:** 2026-07-07
**Category:** Testing
**Source:** Session 2 — full-framework review

## Decision

Cross-engine validation: run one identical strategy on identical data through an established engine (backtesting.py or vectorbt) and reconcile every penny of divergence, documented in the repo.

## Rationale

One successful reconciliation buys more trust than 200 unit tests, and every divergence surfaces a design assumption — which directly serves the framework's stated purpose of understanding everything. Runs once per major simulator change, not per backtest.
