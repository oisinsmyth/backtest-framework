# D25 — Cleaner returns data + a change report; cleaning rules are explicit, versioned, and logged per dataset

**Status:** Committed
**Date:** 2026-07-07
**Category:** Data layer
**Source:** Session 2 — full-framework review

## Decision

Cleaner returns data + a change report; cleaning rules are explicit, versioned, and logged per dataset.

## Rationale

Silent cleaning makes "strategy result" indistinguishable from "cleaning artifact." The cleaner's contract changes from `clean(df) -> df` to `clean(df) -> (df, CleaningReport)`, and the report (what was filled, dropped, patched, and why) attaches to the snapshot metadata.
