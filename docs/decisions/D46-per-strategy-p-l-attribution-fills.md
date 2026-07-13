# D46 — Per-strategy P&L attribution: fills are already strategy-tagged; add per-strategy virtual books so sleeve-level returns exist

**Status:** Committed
**Date:** 2026-07-07
**Category:** Portfolio layer
**Source:** Session 3 — final sweep

## Decision

Per-strategy P&L attribution: fills are already strategy-tagged; add per-strategy virtual books so sleeve-level returns exist.

## Rationale

Order netting (D27) makes portfolio positions non-attributable, and the future allocator brick (D31) is blind without per-sleeve return streams. Cheap now, painful to reconstruct later.
