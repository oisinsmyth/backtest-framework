# Architecture

## The run loop

There is no engine object and no event bus. `run_backtest` (`engine/backtest.py`) is one function
around one loop over aligned bars.

Before the loop, `align_bars` inner-joins the instruments: a timestamp survives only if every
instrument has a bar there. Zero common bars raises.

Per bar, in this order:

| Step | What happens |
|---|---|
| 0 | Splits scale broker positions, every strategy's virtual book, and pending orders |
| 1 | Per-leg carry on a start-of-bar snapshot, then dividends and other event flows, then portfolio-level carry on `max(gross − NAV, 0)` |
| 1b | `next_open` mode only: the previous bar's orders fill at this bar's open |
| 1c | Intrabar stops are evaluated against this bar's OHLC |
| 2 | One `DataView` per instrument, holding bars up to this one, is passed to `strategy.generate_targets` |
| 3 | `allocator.allocate` splits current NAV across strategies |
| 4 | `Sizer` turns target weights into per-strategy orders; `net_orders` nets them into broker orders. An optional pre-trade gate can reject an order here |
| 5 | `close` mode: each netted order is costed and filled at this bar's close. `next_open` mode: orders are held and fill at step 1b of the next bar |
| 6 | Risk check on the resulting book |
| 7 | Equity and cash points are appended |

`BacktestResult` keeps broker fills (netted and costed), per-strategy virtual fills (un-netted),
and stop fills as separate streams.

## Interfaces

Five `typing.Protocol` seams. Nothing needs to inherit from a base class.

```python
class Strategy(Protocol):                      # engine/strategy.py
    strategy_id: str
    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]: ...

class Instrument(Protocol):                    # instruments/base.py
    @property
    def quote_currency(self) -> str: ...
    def notional(self, quantity: float, price: float) -> float: ...   # signed
    def carry_components(self) -> tuple[str, ...]: ...
    def tradeable_quantity(self, raw_quantity: float) -> float: ...

class Allocator(Protocol):                     # engine/allocator.py
    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]: ...

class TradeCostBrick(Protocol): ...            # costs/bricks.py
class CarryCostBrick(Protocol): ...
class EventFlowBrick(Protocol): ...

class DataSource(Protocol):                    # data/source.py
    def get_bars(self, instrument, start, end, timeframe) -> list[TimestampedBar]: ...
```

`Instrument.notional` is signed, so a short reduces NAV without the portfolio special-casing
direction. `run_backtest` takes bars already in hand and never calls a `DataSource`; the caller
wires a snapshot to the engine.

## Costs

`CostStack` (`costs/stack.py`) has four slots, and every method is a sum over one slot:

| Slot | Charged | Base |
|---|---|---|
| `trade_bricks` | per fill | the order's quantity and price |
| `carry_bricks` | per bar, per held leg | that leg's signed notional (`BorrowFee` uses the sign to charge shorts only) |
| `portfolio_carry_bricks` | per bar, once | `max(gross exposure − NAV, 0)`, which only the engine can compute |
| `event_flow_bricks` | on the event date | signed cash to the portfolio (dividends). Not a friction and not scaled by the cost sweep |

No brick reads another brick's output, so order within a slot does not change the total (up to
floating-point associativity). A brick that declares a `component` such as `"borrow"` is charged
only to instruments whose `carry_components()` lists it. An empty stack is the zero-cost model.

Available bricks: flat and IBKR-style commissions, a percent-of-notional spread, square-root
market impact (equities and futures), borrow fees, margin interest, a flat-rate carry, dividend
flows, and futures commission plus tick-crossing costs read from `data/futures_costs.json`.

`engine/sweep.py` reruns one backtest with every friction scaled by a list of multipliers.
`config/` builds a cost stack from the same plain dict that is logged with each trial, so the
logged description and the objects that ran cannot drift apart.

## Two books and two price frames

Two position ledgers run at all times. `PortfolioState.positions` is the broker book: netted, and
the owner of cash. The virtual book holds each strategy's position as if its own orders had filled
in full. Sizing reads the virtual book; fills and NAV use the broker book. `net_orders` connects
them, so two strategies wanting opposite sides of one instrument trade once or not at all.

Two price frames also run in parallel. Execution bars (as traded) drive fills, carry and NAV. View
bars (split-adjusted) drive `DataView` and nothing else.

## Guards

Some invariants are impossible to break by construction:

- A `DataView` is built holding only the bars up to the current index. Later bars were never
  handed to the object, so no indexing or reflection can reach them. `walk_forward_windows`
  reuses this for fitting: a fitter sees only training-window views.
- `SnapshotStore` is content-addressed and re-hashes on load. A snapshot that failed validation is
  quarantined and cannot be loaded by default.
- `TrialRegistry` is append-only, enforced by its primary key.

Others raise at a boundary: duplicate timestamps in alignment, zero aligned bars, a missing view
bar or volume, a stop on an instrument with splits, missing ADV or volatility for the impact model.

Some are only recorded. `RiskMonitor` reports a limit breach in `BacktestResult.violations` and
does not unwind anything. The pre-trade gate enforces limits only with `enforce_pretrade=True`,
which is off by default. `clean()` drops and reports bad bars but never rewrites a price;
`validate()` classifies problems as hard or warning, and the snapshot store enforces the
quarantine.

## Data flow

```
 CSV fixture / yfinance ──▶ clean ──▶ validate ──▶ SnapshotStore ──▶ caller
                                                   (quarantine)        │
                                                                       ▼
 ┌──────────────────────────── run_backtest, per bar ─────────────────────────┐
 │  view bars ──▶ DataView (≤ i) ──▶ Strategy.generate_targets                 │
 │                                        │                                   │
 │                    NAV ──▶ Allocator ──▶ Sizer ──▶ net_orders ──▶ fills     │
 │                                                                            │
 │  CostStack: trade │ carry │ portfolio carry │ event flow   (each a sum)     │
 └────────────────────────────────────────────────────────────────────────────┘
```

## Package map

| Package | Contents |
|---|---|
| `engine/` | `run_backtest`, `DataView`, `PortfolioState`, allocator, risk monitor, strategy protocol, cost sweep |
| `costs/` | cost bricks and `CostStack`, impact calibration, cost scaling |
| `simulator/` | fill prices, intrabar stop fills, calendar carry accrual, and a standalone futures fill model (stops, targets, gap-through, passive entry) |
| `instruments/` | `Equity`, `Future` (with contract specs from `data/`), an option stub |
| `pipeline/` | target weight to order sizing and netting |
| `config/` | dict-to-object builders for cost stacks, fill and carry models |
| `data/` | bars, CSV fixtures, corporate actions, cleaner, validator, snapshot store, yfinance source |
| `analytics/` | Sharpe, Sortino, drawdown, Monte Carlo, tail risk, tearsheet |
| `validation/` | deflated Sharpe, walk-forward windows, pair selection, zero-edge synthetic pairs |
| `registry/` | append-only SQLite trial registry |
| `strategies/` | a z-score pairs strategy |
