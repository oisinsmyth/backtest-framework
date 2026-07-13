# D26 — Sanity gate between data source and engine: OHLC consistency (low ≤ open/close ≤ high), bar-to-bar move thresholds, volume anomaly flags — data failing the gate is quarantined, not passed through

**Status:** Committed / Deferred
**Date:** 2026-07-07
**Category:** Data layer
**Source:** Session 2 — full-framework review

## Decision

Sanity gate between data source and engine: OHLC consistency (low ≤ open/close ≤ high), bar-to-bar move thresholds, volume anomaly flags — data failing the gate is quarantined, not passed through.

## Rationale

Yfinance is a scraper, not an API; it breaks and serves bad prints without warning, and garbage currently flows straight to fills. Brick: `DataValidator`, one class, applied at snapshot creation. Second-source cross-checking deferred as a future brick behind the same interface.
