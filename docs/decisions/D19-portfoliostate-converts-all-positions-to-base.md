# D19 — PortfolioState converts all positions to base currency for NAV

**Status:** Committed
**Date:** 2026-07-07
**Category:** Data & portfolio layers
**Source:** Session 1 — initial design review

## Decision

PortfolioState converts all positions to base currency for NAV.

## Rationale

A multi-currency book has no meaningful single NAV otherwise. Depends on D7 FX plumbing.
