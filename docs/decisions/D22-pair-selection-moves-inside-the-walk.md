# D22 — Pair selection moves inside the walk-forward training windows, over a broad universe

**Status:** Committed
**Date:** 2026-07-07
**Category:** Validation & research integrity
**Source:** Session 1 — initial design review

## Decision

Pair selection moves inside the walk-forward training windows, over a broad universe.

## Rationale

Testing pre-known famous pairs (XLE/XOP, GLD/SLV) is meta-level in-sample selection: they're famous *because* they worked. Walk-forward interface generalises so each window's fit() can return different pairs, not just different parameters.
