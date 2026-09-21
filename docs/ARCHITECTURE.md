# Architecture

**What the framework is, structurally.** [`CONTRIBUTING.md`](../CONTRIBUTING.md) covers how to
change it and [`TUTORIAL.md`](TUTORIAL.md) covers how to use it — `TUTORIAL.md` §1 has a
five-bullet version of this page for anyone who wants thirty seconds instead of ten minutes.

> **`STACK.md` is not this document.** Despite the name it is a *research* ledger — what each
> signal layer earns once costed honestly. Its "layers" are signal, construction, width, exit,
> overlay. No overlap with anything below.

The instrument is **63 modules across 11 packages** (`research/` is a twelfth, excluded).
`src/` holds 85 `.py` files, but 13 are `__init__.py` and 26 are
[`research/`](../src/backtest_framework/research/__init__.py), which that package calls explicitly
*not framework surface* — study code, versioned per study. Quoting 85 overstates the thing being
claimed.

---

## 1. One function, one loop

There is no engine object, no event bus, no callbacks. `run_backtest`
([`engine/backtest.py:110`](../src/backtest_framework/engine/backtest.py)) is a single function
around one `for` loop over aligned bars.

The source numbers its own steps in comments — `0, 1, 1b, 1c, 2, 3, 4, 4b, 5, 5, 6`. Note there is
no 7 (the equity append is uncommented) and **`5` appears twice**, once per fill mode. The table
below follows that numbering and adds the two steps the comments skip.

**Before the loop:** `align_bars` inner-joins the instruments, so a timestamp survives only if
every instrument has a bar there. Zero common bars **raises** rather than returning a run whose
final NAV would equal its starting cash.

**Per bar, in this order** — and the order is load-bearing, not incidental:

| | Step | Why here |
|---|---|---|
| 0 | Splits scale broker positions, every virtual book, and pending orders | before anything reads a position |
| 1 | Per-leg carry on a start-of-bar snapshot → dividends and other event flows → portfolio-level carry on `max(gross − NAV, 0)` | carry is owed on what was held *overnight*, not on what this bar does |
| 1b | **`next_open` mode only**: yesterday's decisions fill at today's **open** | |
| 1c | Intrabar stops evaluated against this bar's OHLC | **after 1b**, so a position opened this bar can be stopped this bar |
| 2 | One `DataView` per instrument, sliced to `i` → `strategy.generate_targets(views)` | the signal sees only what exists |
| 2b | *(uncommented)* Stop registry rebuilt from this bar's targets | **raises** on a stop for a split-bearing instrument — see §5 |
| 3 | `allocator.allocate(nav, strategy_ids)` from **current** NAV | D61: the book compounds into its own size |
| 4 | `sizer.size_targets(...)` → per-strategy virtual orders → `net_orders(...)` → broker orders | |
| 4b | Optional pre-trade gate rejects an order *before* it fills | off by default — see §5 |
| 5 | **`close` mode**: each netted order charged `cost_stack.trade_cost` and applied. **`next_open` mode**: the orders become `pending_virtual` and fill at 1b of the *next* bar | the two arms of one `if/else` — see below |
| 6 | Per-bar risk check, whether or not anything traded | catches exposure drifting over a limit on price alone |
| 7 | *(uncommented)* Equity and cash points appended | |

**Steps 1b and the close-fill half of 5 never both happen on a bar.** They are the arms of
`if fill_timing == "next_open": … else: …` (`backtest.py:336`), which is why the source numbers
both `5`. Read the table as one sequence with a mode switch at 5, not as eleven things that all
occur.

`BacktestResult` keeps `fills` (broker-facing, netted, costed) and `virtual_fills` (per-strategy,
un-netted) separately, and **`stop_fills` as its own stream** — "this exit was a stop" is not
recoverable afterwards, so it is recorded at the point where it is known.

---

## 2. The seams

Five sockets, all `typing.Protocol` — structural, no inheritance required.

```python
# engine/strategy.py:26
class Strategy(Protocol):
    strategy_id: str
    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]: ...

# instruments/base.py:33          (`@runtime_checkable`)
class Instrument(Protocol):
    @property
    def quote_currency(self) -> str: ...
    def notional(self, quantity: float, price: float) -> float: ...        # SIGNED
    def carry_components(self) -> tuple[str, ...]: ...
    def tradeable_quantity(self, raw_quantity: float) -> float: ...

# engine/allocator.py:16
class Allocator(Protocol):
    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]: ...

# costs/bricks.py:25-44  — three protocols, not one
class TradeCostBrick(Protocol):
    def cost(self, instrument: Instrument, quantity: float, price: float) -> float: ...
class CarryCostBrick(Protocol):
    def cost(
        self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float: ...
class EventFlowBrick(Protocol):
    def flow(
        self, instrument: Instrument, quantity: float,
        prev_timestamp: datetime, curr_timestamp: datetime,
    ) -> float: ...

# data/source.py:16
class DataSource(Protocol):
    def get_bars(
        self, instrument: Instrument, start: date, end: date, timeframe: str
    ) -> list[TimestampedBar]: ...
```

Three details that are decisions rather than accidents:

- **`Instrument.notional` is signed.** That is what lets a short fall out of NAV without the
  portfolio special-casing direction anywhere.
- **`Strategy` has an optional member the protocol deliberately does not declare** —
  `on_stop_filled(instrument_id)`, looked up with `getattr` so strategies written before stops
  existed still conform. The one place the protocol is knowingly incomplete, and
  `strategy.py:31-41` says why.
- **`DataSource` is not a seam the engine sits behind.** `run_backtest` never imports or calls
  one; it takes bars already in hand. The data layer terminates at `SnapshotStore` and the caller
  wires snapshot → engine. A real boundary, drawn as a break below.

---

## 3. Costs compose by summing, and that is the whole mechanism

`CostStack` is a frozen dataclass with four tuple slots — `trade_bricks`, `carry_bricks`,
`portfolio_carry_bricks`, `event_flow_bricks` — and every method is a `sum(...)` over its slot.

No brick ever reads another brick's output, so **ordering within a slot does not change the
total**, and `tests/unit/test_cost_stack.py` asserts it for the trade and carry slots. Two
caveats, because "provably" would be too strong: the test uses two bricks per slot, and IEEE-754
addition is commutative but **not associative** — three bricks summed in a different order can
differ in the last bit. What *is* ordered is the slots, and the engine loop fixes that: carry and
flows at step 1, trade costs at step 5. An empty stack is the zero-cost model; there is no separate
class for it.

The difference between the slots is **what the base amount is and who can compute it**:

| Slot | Charged | Base |
|---|---|---|
| trade | per fill | that order's own quantity × price |
| carry | per bar, per held leg | that leg's signed notional — `BorrowFee` uses the sign to isolate shorts |
| portfolio carry | per bar, once | `max(gross exposure − NAV, 0)` — **only the engine can compute this** |
| event flow | on the date | signed cash *to* the portfolio. Not a friction, and not scaled by the cost sweep |

`Instrument` and `CostStack` meet in one place — `_applies` (`costs/stack.py:75`). A brick
declaring `component = "borrow"` is charged only to instruments whose `carry_components()` lists
it; a brick declaring nothing is generic. That filter is the seam, not the engine.

---

## 4. Two books, two price frames

**The two most non-obvious facts in the codebase**, and until this document they existed only in
scattered docstrings.

**Two position ledgers run at all times.** `PortfolioState.positions` is broker-facing, netted, and
owns cash. `virtual_positions` is a plain `{(strategy_id, instrument_id): float}` dict the loop
owns, updated as if each strategy's own order filled in full. **Sizing reads the virtual book;
fills and NAV use the broker book.** `net_orders` is the one-way valve between them — shared legs
cancel, so two strategies wanting opposite sides of the same instrument trade once, or not at all.

The books read back from each other in exactly two places, and those are where they could diverge:
a pre-trade rejection, and a stop fill.

**Two price frames run in parallel.** Execution bars (raw) feed fills, carry and NAV. View bars
(split-adjusted) feed `DataView` and nothing else. Volumes travel in the *view* frame. They
converge nowhere except at the index `i`.

---

## 5. Guards: impossible, asserted, and merely recorded

[`PHILOSOPHY.md`](../PHILOSOPHY.md) pillar 1 says invariants should be made impossible rather than
forbidden. Most are. **Not all, and the exceptions matter more than the rule.**

### Impossible — the object was never given the data

**`DataView`** is the important one, and the mechanism is construction, not access control. A view
is *built holding only the bars up to `i`*. Bars beyond that were never handed to the object, so
there is nothing for a reflection trick, an `.iloc`, or a walk of `__dict__` to find. The
`LookAheadError` on an out-of-range index is belt-and-braces on a tuple that already contains no
future data.

`walk_forward_windows` reuses the same guard for fitting — anything that fits sees train-slice
views only. `SnapshotStore` is content-addressed and re-hashes on load, and a quarantined snapshot
**cannot reach the engine by any default path**. `TrialRegistry` is append-only by primary key.

### Asserted — raises at a boundary

Duplicate timestamps in alignment (a duplicate would silently drop a bar, last-wins, through a
dict). Zero aligned bars. A missing view bar or volume for an aligned timestamp. A stop on a
split-bearing instrument. Missing ADV or σ for the impact model — *"a loud error, not a silent zero
cost"*.

> **The example here used to be `OptionStub.margin_requirement`, and on 2026-09-17 it was
> deleted by D48 itself rather than in spite of it.** The member was required by the
> `Instrument` protocol, implemented by every instrument, and **called by nothing in
> `src/`** — while `Equity`'s implementation returned full notional where Reg T is 50%: a
> wrong number nothing could notice. A stub that raises is D48 kept. A required member
> nobody reads is D48 broken. It was both at once, and the second beat the first.
> `src/` now contains **no** `NotImplementedError` at all; the scoping claim it carried
> still stands in [`options_extension.md`](options_extension.md).

### Merely recorded — and the name overpromises

**`RiskMonitor.evaluate` returns a violation and halts nothing.** It is
`evaluate(...) -> RiskViolation | None` (`engine/risk.py:61`) — at most one per bar, since there is
one rule — and the *caller* appends it to `BacktestResult.violations` (`result.violations.append`, `engine/backtest.py:359-361`). No
corrective orders, no unwind. A caller inspecting that list is the only enforcement that exists.
`pretrade_check` *is* enforcement, but only under `enforce_pretrade=True`, which is **off by
default**.

The cleaner and validator likewise do not block: `clean()` drops and reports but **never rewrites a
price**, and `validate()` classifies into hard and warning. The blocking happens one layer up,
structurally, when the snapshot store writes `quarantined: true` and refuses to load it. Validator
classifies; snapshot store enforces.

---

## 6. The shape

```
   data/  ──▶  cleaner ──▶ validator ──▶ SnapshotStore ─┐
                                    (quarantine refuses) │
                                                         ╎  ← the engine has no DataSource
                                                         ╎     dependency; the caller wires it
                                                         ▼
   ┌──────────────────────── run_backtest, per bar i ────────────────────────┐
   │                                                                          │
   │  view bars ──▶ DataView(≤ i) ──▶ Strategy.generate_targets               │
   │                                          │                               │
   │                                          ▼                               │
   │                              ┌──▶  Allocator.allocate  ◀──┐  NAV         │
   │                              │     (float, ids) → dict    │  feedback    │
   │                              │                            │              │
   │                              ▼                            │              │
   │   virtual book ──────▶  Sizer.size_targets  ──▶ net_orders │              │
   │        ▲                                            │      │              │
   │        └──── apply_virtual_orders ◀──────┐          ▼      │              │
   │                                           │    broker book ─┘              │
   │  exec bars ──▶ stop_fill_price ──▶ on_stop_filled ──▶ Strategy            │
   │                                                                          │
   │  CostStack:  trade │ carry │ portfolio carry │ event flow  (all sum)      │
   └──────────────────────────────────────────────────────────────────────────┘
```

Three things the picture carries that prose does not:

1. **NAV feeds back into the same bar's sizing.** Not the next bar's — `current_nav` is computed
   after this bar's carry, splits and stop fills, and feeds the allocator on the next line.
2. **The two feedback arrows come from different objects.** NAV from the broker book, current
   positions from the virtual book.
3. **The allocator is a deliberately narrow pipe.** One float and a list of ids in, a dict out. It
   cannot see positions, prices, instruments or correlations — and that narrowness is precisely why
   multi-strategy allocation is an open socket rather than a design.

---

## 7. The map

| Package | Modules | What it is |
|---|---|---|
| `engine/` | 7 | the loop and its collaborators: `backtest.py` (the centre), `dataview.py` (the guard), `portfolio.py`, `risk.py`, `allocator.py`, `strategy.py`, `sweep.py` |
| `costs/` | 5 | `stack.py` composes, `bricks.py` declares, `equity_bricks.py` implements the real ones, `scaling.py` is the sweep, `calibration.py` estimates σ/ADV |
| `data/` | 11 | fetch → clean → validate → freeze. `alignment.py`, `validator.py`, `snapshot_store.py`, `corporate_actions.py` are the load-bearing four |
| `validation/` | 4 | research integrity: `walk_forward.py`, `dsr.py` (deflated Sharpe — counts trials *against* you), `pair_selection.py`, `synthetic.py` (zero-edge nulls that must earn nothing) |
| `config/` | 6 | validate a dict → live objects. The dict a study **logs** is the dict that **builds** the stack |
| `instruments/` | 3 | the protocol, `Equity`, and a stub that raises |
| `pipeline/` | 1 | `sizing.py` — the entire weight → order → netting seam |
| `simulator/` | 2 | `fills.py` (`Bar`, `stop_fill_price`), `carry.py` (ACT/365) |
| `analytics/` | 4 | metrics, tail risk, Monte Carlo, tearsheet |
| `registry/` | 1 | append-only trial log |
| `strategies/` | 2 | the two non-toy strategies |
| `research/` | 26 | **study code, not framework surface** |

`Bar` itself lives in `simulator/fills.py` — a slightly surprising home for the most central data
type in the system, and worth knowing before you go looking for it.

---

**Verification of each of these claims is in [`../CONTRIBUTING.md`](../CONTRIBUTING.md)'s gate
model**: the guards in §5 are asserted across all four tiers — `tests/integration/` for the
look-ahead guard and the risk monitor, `tests/property/` for the invariants, and `tests/unit/` for
most of the raise-sites (`test_alignment.py`, `test_snapshot_store.py`, `test_instruments.py`,
`test_sqrt_impact.py`) — the cost
composition in §3 by `tests/golden/` against hand-computed ledgers, and the whole simulator by a
penny-exact reconciliation against an independently written engine
([`verification/cross_engine_reconciliation.md`](verification/cross_engine_reconciliation.md)).
