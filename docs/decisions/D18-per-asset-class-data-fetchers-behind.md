# D18 — Per-asset-class data fetchers behind one DataSource interface: get_bars(instrument, timeframe). Existing yfinance fetcher becomes EquityDataSource

**Status:** Committed
**Date:** 2026-07-07
**Category:** Data & portfolio layers
**Source:** Session 1 — initial design review

## Decision

Per-asset-class data fetchers behind one DataSource interface: get_bars(instrument, timeframe). Existing yfinance fetcher becomes EquityDataSource.

## Rationale

Each asset class has different sources but the engine should not care. Options data source stays unwritten.
