# D21 — Deflated Sharpe Ratio added as a sibling to the IS/OOS overfitting ratio, not a replacement

**Status:** Committed
**Date:** 2026-07-07
**Category:** Validation & research integrity
**Source:** Session 1 — initial design review

## Decision

Deflated Sharpe Ratio added as a sibling to the IS/OOS overfitting ratio, not a replacement.

## Rationale

The ratio is a quick smoke alarm but statistically noisy at ~8–12 OOS windows; DSR is the proper instrument and punishes for number of trials (fed by D20).
