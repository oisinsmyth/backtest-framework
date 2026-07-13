# D48 — No false affordances: enum values and flags for unimplemented behaviour are removed or implemented. Immediate case: FillStatus.PARTIAL either gains a volume-cap fill brick or is deleted

**Status:** Committed
**Date:** 2026-07-07
**Category:** Testing
**Source:** Session 3 — final sweep

## Decision

No false affordances: enum values and flags for unimplemented behaviour are removed or implemented. Immediate case: FillStatus.PARTIAL either gains a volume-cap fill brick or is deleted.

## Rationale

Dead options imply capabilities that don't exist, and a reviewer (or future you) will trust them. Same rule applies to any config knob that no code path reads.
