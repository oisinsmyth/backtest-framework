# D24 — Immutable data snapshots: fetch once, freeze with a fetch-date stamp; every trial logs its snapshot ID

**Status:** Committed
**Date:** 2026-07-07
**Category:** Data layer
**Source:** Session 2 — full-framework review

## Decision

Immutable data snapshots: fetch once, freeze with a fetch-date stamp; every trial logs its snapshot ID.

## Rationale

Yfinance restates history (dividends re-adjust all past prices, corporate action fixes rewrite old bars), so identical code produces different results months apart, silently making TrialRegistry entries incomparable. Data versioning is as fundamental to research integrity as trial counting. Brick: `SnapshotStore` sitting between fetcher and engine; engine only ever reads snapshots, never live fetches.
