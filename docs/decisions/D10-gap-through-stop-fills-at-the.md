# D10 — Gap-through-stop fills at the bar open, not the stop price

**Status:** Committed
**Date:** 2026-07-07
**Category:** Execution / fill logic
**Source:** Session 1 — initial design review

## Decision

Gap-through-stop fills at the bar open, not the stop price.

## Rationale

Filling at stop price through a gap is free money and fantasy risk numbers. This is a bug fix, not a configurable option.
