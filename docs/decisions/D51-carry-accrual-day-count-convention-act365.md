# D51 — Carry accrual day-count convention: ACT/365 as a single stated default

**Status:** Committed / Deferred
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 1 — D33 implementation)

## Decision

`accrue_carry()` computes `base_amount * annual_rate * calendar_days / 365`. ACT/365 is
the day-count convention for every carry brick (margin interest, borrow, funding) until a
per-broker/per-currency override is built.

## Rationale

D33 says carry accrues "on the calendar-day gap between consecutive bar timestamps," which
fixes the numerator (calendar days, not bar count) but never states the denominator — what
a year *is* for this purpose. That's a real, separate choice: real-world margin loan rates
are quoted under varying conventions (e.g. ACT/360 is common for USD money-market and
margin-loan rates; ACT/365 is common elsewhere), and silently picking one without saying so
would be exactly the kind of implicit default Pillar 1 of `PHILOSOPHY.md` argues against.

ACT/365 is chosen now as a single global default because: (1) it needs to be *something*
for Step 1's golden and property tests to have a concrete answer to assert against, and
(2) getting the IBKR-specific convention right is properly the equity cost bricks' job
(D4, D5), which comes later in the build order — this is a placeholder with a name, not a
researched broker-accurate figure.

**Deferred:** per-currency/per-broker day-count override, to be revisited when D4/D5
(IBKR commission + margin interest bricks) are implemented. Labelled here per R3 rather
than left as a silent gap. This is a narrower, code-level instance of D33 rather than a
reversal of it — the calendar-day-gap numerator D33 established is unchanged.
