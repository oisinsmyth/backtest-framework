# D44 — Engine enforces a warm-up period: no trading until the longest indicator lookback (incl. the cost model's vol_window) is satisfied; vol estimates use data up to the *previous* bar only

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 3 — final sweep

## Decision

Engine enforces a warm-up period: no trading until the longest indicator lookback (incl. the cost model's vol_window) is satisfied; vol estimates use data up to the *previous* bar only.

## Rationale

Right now the first 21 bars silently use the fallback cost regime (a mid-backtest cost shift), indicators computed on partial windows are noise, and same-bar vol estimation is a small look-ahead.
