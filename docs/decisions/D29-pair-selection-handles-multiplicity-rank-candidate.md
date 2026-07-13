# D29 — Pair selection handles multiplicity: rank candidate pairs and take top-N rather than thresholding p-values; the number of pairs tested is logged to the TrialRegistry

**Status:** Committed
**Date:** 2026-07-07
**Category:** Signals & strategy interface
**Source:** Session 2 — full-framework review

## Decision

Pair selection handles multiplicity: rank candidate pairs and take top-N rather than thresholding p-values; the number of pairs tested is logged to the TrialRegistry.

## Rationale

Testing 200 pairs at p<0.05 yields ~10 false positives from pure noise. D22 fixed look-ahead; this fixes multiple testing. Both are needed for the selection step to be honest.
