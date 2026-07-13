# D33 — Bars for sequencing, timestamps for accrual and annualisation. All carry costs (borrow, margin interest, funding) accrue on the calendar-day gap between consecutive bar timestamps, not per bar

**Status:** Committed
**Date:** 2026-07-07
**Category:** Backtest engine
**Source:** Session 2 — full-framework review

## Decision

Bars for sequencing, timestamps for accrual and annualisation. All carry costs (borrow, margin interest, funding) accrue on the calendar-day gap between consecutive bar timestamps, not per bar.

## Rationale

A Friday→Monday hold is one bar but three calendar days of borrow and interest; per-bar accrual with `bar_duration_days=1.0` undercharges every weekend and holiday (~40% of calendar time on daily equity data). Bug fix, not an option (same class as D10). Also resolves annualisation once instruments carry their own calendars (D17).
