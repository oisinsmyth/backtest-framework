# backtest-framework

[![tests](https://github.com/oisinsmyth/backtest-framework/actions/workflows/tests.yml/badge.svg)](https://github.com/oisinsmyth/backtest-framework/actions/workflows/tests.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

An event-driven backtesting framework for daily and intraday strategies on equities and
futures. Costs are composed from small tested parts (commission, spread, market impact, borrow,
margin interest, dividends), and the engine is checked against hand-computed ledgers and against
an independent engine.

It was built for systematic strategy research where a reported result has to hold up under
checking: every cost is modelled explicitly, data is validated before it is used, and every trial
is logged so the best result can be judged against the number tried. It is for readers who want to
audit how a backtest reaches its numbers.

## Install

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/oisinsmyth/backtest-framework.git
cd backtest-framework
uv sync
uv run pytest -q
```

## Example

A z-score pairs strategy on ten years of bundled XLE/XOP daily bars, with commission, spread,
borrow fees and margin interest
([`examples/pairs_backtest.py`](examples/pairs_backtest.py)):

```python
bars = load_fixture_csv(FIXTURE)  # {"XLE": [...], "XOP": [...]}, daily OHLC bars

costs = CostStack(
    trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=1.0)),  # per fill
    carry_bricks=(BorrowFee(annual_rate=0.0025),),  # per short leg held overnight
    portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),  # on the book's borrowing
)

strategy = ZScorePairsStrategy(
    strategy_id="xle_xop", instrument_a="XLE", instrument_b="XOP",
    lookback=60, entry_z=2.0, exit_z=0.5, leg_weight=1.0,
)

result = run_backtest(
    bars_by_instrument=bars,
    instruments={"XLE": Equity(symbol="XLE"), "XOP": Equity(symbol="XOP")},
    strategies=[strategy],
    cost_stack=costs,
    allocator=ConstantSplitAllocator(),
    starting_cash=STARTING_CASH,
)
```

```bash
uv run python examples/pairs_backtest.py
```

```
bars            2515
fills           2231
trading costs   $5,533.54
final NAV       $80,824.43
net P&L         $-19,175.57
Sharpe (rf 0)   -0.079
Sortino (rf 0)  -0.113
max drawdown    42.61%
```

The strategy loses money after costs. Two more examples:

- [`examples/cost_sweep.py`](examples/cost_sweep.py) reruns the backtest at 0x to 4x its costs.
- [`examples/deflated_sharpe.py`](examples/deflated_sharpe.py) logs a 12-cell parameter grid to
  the trial registry and deflates the best cell's Sharpe by the number of trials.

## Packages

| Package | Contents |
|---|---|
| `engine` | `run_backtest`, look-ahead-safe `DataView`, portfolio, allocator, risk monitor, cost sweep |
| `costs` | composable cost bricks: commissions, spread, square-root impact, borrow, margin interest, dividends, futures round trips |
| `simulator` | fill prices, intrabar stops with gap-through, calendar carry accrual, a futures fill model |
| `instruments` | `Equity`, `Future` (CME contract specs in `data/`), an option stub |
| `pipeline` | target weights to orders, with netting across strategies |
| `config` | build cost stacks and models from the plain dict logged with each trial |
| `data` | CSV fixtures, corporate actions, cleaner, validator, content-addressed snapshot store, yfinance loader |
| `analytics` | Sharpe, Sortino, drawdown, Monte Carlo, tail risk, tearsheet |
| `validation` | deflated Sharpe ratio, walk-forward windows, pair selection, zero-edge synthetic pairs |
| `registry` | append-only SQLite log of every trial |
| `strategies` | a z-score pairs strategy |

[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) describes the run loop, the interfaces and the
cost model.

## How correctness is checked

701 offline tests. The golden tier asserts every fill, charge and NAV against ledgers worked by
hand without importing the package. Property tests check invariants, such as exact
reconciliation of fills to positions, over generated inputs. The engine agrees with vectorbt on
all 1,370 fills and to within $0.0000003 over a ten-year equity curve, and the metrics agree with
quantstats. A strategy only ever receives bars up to the current one. Details and limits are in
[`docs/VALIDATION.md`](docs/VALIDATION.md); [`docs/findings/`](docs/findings/) has five short
case studies from research built on the framework.

## Data

`data/fixtures/` holds XLE and XOP daily bars for 2015–2024 from Yahoo Finance via yfinance: one
file of adjusted prices, and one of raw prices with dividends and splits in a separate events
file. `data/futures_*.json` and `data/fut_specs_from_definition.json` hold CME contract
specifications and measured futures cost parameters, which the futures modules read at runtime.

## Contributing

Bug reports and pull requests are welcome; see [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Citation

If you use this in research, please cite it using [`CITATION.cff`](CITATION.cff), or the
**Cite this repository** button on GitHub.

## Licence

MIT. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
