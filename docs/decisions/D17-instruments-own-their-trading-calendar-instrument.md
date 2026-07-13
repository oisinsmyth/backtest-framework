# D17 — Instruments own their trading calendar: instrument.periods_per_year(bar_duration); audit every annualisation constant in the codebase

**Status:** Committed
**Date:** 2026-07-07
**Category:** Instruments
**Source:** Session 1 — initial design review

## Decision

Instruments own their trading calendar: instrument.periods_per_year(bar_duration); audit every annualisation constant in the codebase.

## Rationale

Equities ≈252 days, crypto = 365, FX ≈260, and hard-coded /365 or /252 constants become a subtle bug farm across asset classes.
