# How correctness is checked

```bash
uv run pytest -q                # 693 tests, offline
uv run pytest -q tests/golden   # hand-computed ledgers only
uv run pytest -m live_fetch     # the two tests that call yfinance
```

## Test tiers

| Tier | Tests | What it pins |
|---|---:|---|
| `tests/golden/` | 159 | Hand-computed ledgers. Each test has a `.hand.txt` file beside it with the arithmetic worked out by a calculator that never imports this package. If the code and the hand file disagree, the hand file is right. |
| `tests/property/` | 28 | Invariants checked with Hypothesis over generated inputs: fills reconcile exactly with final positions, NAV does not leak at zero cost, fill prices lie inside their bar, identical runs are identical, carry totals rate × calendar days, futures fills sit on the tick grid and never beat a stop, and zero-edge inputs earn nothing. |
| `tests/integration/` | 44 | Whole runs: the backtest loop, the cost sweep, splits and dividends through the engine, walk-forward pair selection, the look-ahead guard, the risk monitor, the full data pipeline from raw fixture to snapshot to sweep, and the cross-engine reconciliation. |
| `tests/unit/` | 462 | One behaviour per test, including the guards: every check that is meant to raise is shown to raise. |

## The golden master

`tests/golden/test_the_golden_master.py` runs a five-bar short position through every cost brick
at once: IBKR-style commission, a 5 bp spread, a 2% borrow fee, 6% margin interest on borrowing
above NAV, and a $0.50 dividend debited to the short on its ex-date, across a weekend so carry
accrues for three calendar days. Every fill, every charge and the final NAV of 100,149.6537 are
asserted against the hand ledger.

## Agreement with an independent engine

`tests/integration/test_cross_engine.py` runs the same strategy through this engine and through
vectorbt 1.1.0. Both consume one precomputed MA(10)/MA(30) crossover weight schedule on the
bundled XLE daily fixture, so signal code is out of the comparison and any difference is a
disagreement about sizing, fills, fees or accounting.

| | this engine | vectorbt `from_orders` |
|---|---|---|
| Bars | 2,515 | 2,515 |
| Fills | 1,370 | 1,370 |
| Final value | $159,233.023491 | $159,233.023491 |

The largest divergence over the ten-year equity curve is $2.2e-7 in absolute terms and 1.3e-12 in
relative terms, both floating-point noise. The test asserts a relative tolerance of 1e-6 on every
bar and an identical fill count.

Conventions matched on purpose:

| Convention | This engine | vectorbt |
|---|---|---|
| Re-sizing | target weight × current NAV, every bar | `size_type="targetpercent"`, every bar |
| Fill price | close of the signal bar | `price=close` |
| Shares | fractional (`quantity_precision=8`) | fractional |
| Fees | `PercentOfNotionalSpread(bps=5)` on order notional | `fees=0.0005` on order value |
| Target weight | 0.6 | 0.6 |

The weight is 0.6 rather than 1.0 because near full investment vectorbt reserves fees out of the
purchase while this engine pays them from cash. Below that boundary the conventions coincide.

Scope: one instrument, long or flat, proportional fees only. Carry, dividends, splits, margin and
multi-leg netting are not in vectorbt's comparable feature set; they are anchored by the golden
ledgers instead.

## Agreement with quantstats

`tests/unit/test_quantstats_crosscheck.py` computes Sharpe (at zero and 4% risk-free), Sortino and
maximum drawdown on the same return series with this package and with quantstats. Sharpe at
zero risk-free and drawdown agree to a relative 1e-9; Sharpe at 4% and Sortino to 1e-6.

## Look-ahead

A strategy receives one `DataView` per instrument, built holding only the bars up to the current
index. Later bars were never passed to the object, so no indexing, slicing or attribute walk can
reach them. `tests/integration/test_dataview_lookahead_guard.py` runs strategies written to
cheat, and checks that none of them can obtain a future bar or a future volume. Walk-forward
fitting (`validation/walk_forward.py`) uses the same construction: a fitter only ever receives
training-window views.

This guards strategies built on the engine. It does not guard analysis written outside it, such
as a vectorised research script. [`findings/lag-audit.md`](findings/lag-audit.md) is an example
of a look-ahead error made in exactly that layer.

## Multiple testing

`registry/trial_registry.py` is an append-only SQLite log of every trial, keyed so a trial id
cannot be written twice. `validation/dsr.py` computes the deflated Sharpe ratio (Bailey and López
de Prado, 2014) with the trial count and the variance of Sharpe across trials read from the
registry. `tests/property/test_multiplicity_null.py` checks that selecting the best of many
pure-noise configurations shows no out-of-sample edge, and that synthetic pairs built to look
cointegrated but with a random-walk spread (`validation/synthetic.py`) earn nothing.

## What is not covered

- The cross-engine check covers one instrument, long or flat, with proportional fees only.
- Data quality depends on the provider. The validator classifies problems and the snapshot store
  quarantines failures, but a corporate-actions file that misreports an event as a dividend is
  applied as given. See [`findings/fabricated-dividend-days.md`](findings/fabricated-dividend-days.md).
- The crossing costs in `data/futures_costs.json` were measured over 2025-09 to 2026-09. A tick
  is fixed in price terms, so on older, lower-priced data it is a larger fraction of price and
  those costs are optimistic for earlier years.
- The futures impact coefficient Y = 0.7 is taken from the 0.5-1 range reported in the
  literature, not calibrated on these contracts; no metaorder data for them is available here.
- `RiskMonitor` records limit breaches and does not act on them. The pre-trade gate is off unless
  `enforce_pretrade=True`.

## Case studies

From research built on this framework:

- [Cross-engine reconciliation](findings/cross-engine-reconciliation.md)
- [The deflated-Sharpe hurdle rises with the trial count](findings/deflated-sharpe-hurdle.md)
- [A lag audit removed 93% of an apparent edge](findings/lag-audit.md)
- [A same-close fill credited the overnight gap](findings/same-close-fill.md)
- [Corporate actions booked as dividends](findings/fabricated-dividend-days.md)
