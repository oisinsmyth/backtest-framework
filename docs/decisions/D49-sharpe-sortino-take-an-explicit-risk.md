# D49 — Sharpe/Sortino take an explicit risk-free rate input, consistent with the D37 benchmark frame

**Status:** Committed
**Date:** 2026-07-07
**Category:** Analytics
**Source:** Session 3 — final sweep

## Decision

Sharpe/Sortino take an explicit risk-free rate input, consistent with the D37 benchmark frame.

## Rationale

Rf≈0 shortcuts are wrong in a 4–5% rate era and materially flatter a market-neutral book whose honest hurdle *is* the risk-free rate.
