# D115 — The buy-and-hold benchmark holds a fixed quantity, not a fixed weight

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout study session

## Decision

`run_benchmark` computes buy-and-hold directly: buy at the **second** OOS bar's open (the
earliest any decision made on the first OOS bar could fill), paying the tier's fee on the
entry notional, hold a fixed quantity to the end, and mark at the final close with no
forced liquidation — exactly how a strategy variant that ends long is marked.

`run_benchmark_via_engine` keeps the alternative — the same thing expressed as a constant
100% target weight through `run_backtest` — as a **cross-check only**, asserted in
`tests/integration/test_breakout_study.py` to agree within 2e-4 relative.

## Rationale

Under next-open fills (D103) the sizing pipeline targets a *weight*, sized on the decision
bar's close and filled at the next bar's open. Whenever those two prices differ — a ~0.06%
mean gap on daily crypto bars — a constant 100% weight arrives slightly off target and is
corrected on the following bar. That is correct behaviour for a weight-targeting strategy
and wrong behaviour for a benchmark: buy-and-hold buys once and does nothing else. A
benchmark that quietly rebalances daily is not the thing the report claims to be comparing
against.

In practice the two agree closely on this data (the cross-check tolerance is 2e-4), so the
choice changes no conclusion. It is made anyway because "the benchmark is exactly what its
name says" should not depend on a gap statistic happening to be small — and keeping both
implementations, with a test tying them together, means a future data set where the gap is
*not* small will produce a failing test rather than a quietly wrong benchmark column.

**Benchmark frame (D37, inverted).** D37 says a market-neutral book benchmarks against the
risk-free rate. This strategy is directional (D117), so the same rule points the other way:
its honest benchmark is holding the instrument. Sharpe against rf=4% is still reported, but
the buy-and-hold column is the one the verdict is read from.
