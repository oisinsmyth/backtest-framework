# D31 — Allocator is a bare-bones stand-in: constant capital split across strategies, behind a stable `Allocator` interface

**Status:** Committed
**Date:** 2026-07-07
**Category:** Portfolio layer
**Source:** Session 2 — full-framework review

## Decision

Allocator is a bare-bones stand-in: constant capital split across strategies, behind a stable `Allocator` interface.

## Rationale

Multi-strategy allocation (correlation, capacity, sleeve rebalancing) is a hard problem with zero validated strategies to inform it; any interface designed now from speculation will be wrong. Constant-split keeps the Lego socket real and testable while committing nothing. Same pattern as the options stub: shape committed, cleverness deferred.
