# Changelog

All notable changes are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-07

First public release.

### Added

- `run_backtest`: a single-loop, bar-by-bar engine with close or next-open fills, intrabar
  stops, split handling, per-strategy virtual books netted into one broker book, and an
  optional pre-trade risk gate.
- `DataView`, which gives strategies only the bars up to the current one.
- Cost bricks composed in a `CostStack`: flat and IBKR-style commission, percent-of-notional
  spread, square-root market impact for equities and futures, borrow fee, margin interest,
  flat-rate carry, dividend flows, and futures commission plus tick crossing from a measured
  cost table.
- `run_cost_sweep` for rerunning a backtest at scaled costs.
- Instruments: `Equity`, `Future` (CME contract specifications), and an option stub.
- Data layer: CSV fixtures, corporate actions, cleaner, validator, a content-addressed
  snapshot store, and a yfinance loader.
- Analytics: Sharpe, Sortino, drawdown, block-bootstrap Monte Carlo, tail risk, tearsheet.
- Validation: deflated Sharpe ratio from an append-only trial registry, walk-forward windows,
  pair selection, and zero-edge synthetic pairs.
- A z-score pairs strategy and three runnable examples.
- Tests: golden ledgers worked by hand, property tests, integration tests, and a
  reconciliation against vectorbt.

[0.1.0]: https://github.com/oisinsmyth/backtest-framework/releases/tag/v0.1.0
