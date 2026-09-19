# Tutorial — from empty terminal to research output

This walks the whole pipeline: setup → data → costs → a strategy → a backtest → the
cost sweep → trial logging → analytics → validation science → a full study. It
assumes you can read Python; it does not assume you've read the 764 decision records
(they're linked where they matter — [`decisions/`](decisions/README.md)).

**Every code block below whose first line is `# runnable` is executed verbatim, in
order, by `tests/integration/test_tutorial.py`** — the blocks share one namespace
(later blocks use earlier variables), and `WORKDIR` is an injected temp directory.
If the framework's API drifts, this tutorial fails CI rather than silently lying —
the same doc-rot discipline as everything else here (D91).

---

## 0. Setup

```bash
git clone <this repo> && cd "Backtest Framework"
uv sync                 # installs everything incl. dev deps (pytest, vectorbt, quantstats)
uv run pytest -q tests/golden   # 101 ledger-anchored tests, no market data
uv run pytest                   # the whole suite, ~4m here; 53 tests skip (2026-09-17)
                                # without the bulk panels, each naming the file it wanted
```

The one-line philosophy ([PHILOSOPHY.md](../PHILOSOPHY.md)): **build something you
can't lie to yourself with.** Every API choice below that feels strict — required
arguments, loud errors, structural guards — is that sentence enforced in code.

## 1. The mental model, in five bullets

- **Instruments** (`instruments/`) — what you trade. `Equity("XLE")` knows its
  notional, rounding, and carry types. Everything is a swappable object, never a
  bare ticker string (D12).
- **Costs** (`costs/`) — a `CostStack` of independent bricks in four slots: per-trade
  (commission, impact, spread), per-leg carry (borrow), portfolio-level carry
  (margin interest on `max(gross − NAV, 0)`), and event flows (dividends: longs
  credited, shorts debited). Empty stack ≡ zero costs (D1/D2/D67/D75).
- **Strategies** (`engine/strategy.py`) — emit *target weights*, never share counts
  (D27). They see the market only through `DataView`s that physically do not contain
  future bars (D32/D56) — there is nothing to peek at.
- **The engine** (`engine/backtest.py::run_backtest`) — per bar: apply splits →
  accrue carry and dividend flows → hand strategies their views → size targets
  against current NAV (D61) → net orders across strategies (shared legs cancel) →
  fill at close → risk check → record. Multi-strategy and multi-instrument natively.
- **Research integrity** (`registry/`, `validation/`) — every run can log a trial
  (config hash, snapshot id, seed) to an append-only `TrialRegistry` (D20); the
  Deflated Sharpe Ratio later *counts those trials against you* (D21/D86).

## 2. Hello world: a backtest in one screen

```python
# runnable
from datetime import datetime, timedelta

from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

START = datetime(2026, 1, 5, 16)

def make_bars(prices, start=START):
    """OHLC pinned to one price per bar - fine for examples."""
    return [
        TimestampedBar(start + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
        for i, p in enumerate(prices)
    ]

bars = {"ACME": make_bars([100.0, 102.0, 101.0, 105.0, 103.0])}

result = run_backtest(
    bars_by_instrument=bars,
    instruments={"ACME": Equity(symbol="ACME")},
    strategies=[ScheduledWeightStrategy(strategy_id="demo",
                                        weights_by_instrument={"ACME": [0.5, 0.5, 0.5, 0.0, 0.0]})],
    cost_stack=CostStack(),                # empty stack == zero costs
    allocator=ConstantSplitAllocator(),    # one strategy -> 100% of capital
    starting_cash=100_000.0,
)

print("final NAV:", result.final_nav)
assert result.final_nav > 100_000        # bought at 100, rode to 105, exited
assert result.final_positions.get("ACME", 0.0) == 0.0
```

What you get back (`BacktestResult`): `equity_curve` and `cash_curve` (per-bar
`(timestamp, value)`), `fills` (every broker-facing fill with its trade cost),
`violations` (risk breaches — recorded, not enforced, D62), `final_positions`,
`final_nav`. Weights are sized against *current NAV each bar* (D61) and rounded to
whole shares by default (`Equity(quantity_precision=8)` for fractional).

## 3. Real costs: the CostStack

Toy bricks (`costs/bricks.py`) exist for tests; the real ones live in
`costs/equity_bricks.py`. The full stack used by the published studies:

```python
# runnable
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.costs.equity_bricks import (
    BorrowFee, DividendFlow, IBKRCommission, MarginInterest, SqrtImpact,
)

# SqrtImpact needs per-symbol sigma/ADV. calibrate_impact_params automates it from
# bars + volumes (full-sample: a documented look-ahead in COST params only, D66).
volumes = {"ACME": [1_000_000.0] * 5}
impact_params = calibrate_impact_params(bars, volumes)

real_stack = CostStack(
    trade_bricks=(
        IBKRCommission(),                        # $0.005/sh, $1 min, 1% cap (D65)
        SqrtImpact(params_by_symbol=impact_params),  # sqrt market impact (D66)
        PercentOfNotionalSpread(bps=1.0),        # half-spread stand-in
    ),
    carry_bricks=(BorrowFee(annual_rate=0.0025),),          # shorts pay, longs free (D71)
    portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),  # on max(gross-NAV, 0) (D67)
    event_flow_bricks=(DividendFlow(dividends_by_symbol={}),),   # ex-date cash flows (D75)
)
```

Carry accrues on **calendar days** between bars — a Friday→Monday hold is three days
of borrow and margin, not one (D33). Everything is per-brick swappable; write your
own by matching the `TradeCostBrick` / `CarryCostBrick` / `EventFlowBrick` protocols
in `costs/bricks.py`.

## 4. Writing a strategy

Implement the `Strategy` protocol: a `strategy_id` and
`generate_targets(views) -> list[TargetWeight]`. You receive one `DataView` per
instrument — index into history freely (`view[i]`, `view[-2]`, `view.current_bar`),
but an index past the current bar raises `LookAheadError`, and the future bars are
not merely hidden, they were never given to the object (D56).

```python
# runnable
from dataclasses import dataclass
from typing import Mapping

from backtest_framework.engine.dataview import DataView
from backtest_framework.pipeline.sizing import TargetWeight

@dataclass
class MovingAverageStrategy:
    """Long when price > its trailing MA, flat otherwise. Tutorial toy."""
    strategy_id: str
    instrument_id: str
    window: int = 10
    weight: float = 0.6

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view = views[self.instrument_id]
        if len(view) < self.window + 1:                      # warm-up: stand aside
            return [TargetWeight(self.strategy_id, self.instrument_id, 0.0)]
        closes = [view[i].close for i in range(len(view) - self.window, len(view))]
        ma = sum(closes) / len(closes)
        w = self.weight if view.current_bar.close > ma else 0.0
        return [TargetWeight(self.strategy_id, self.instrument_id, w)]

import numpy as np
rng = np.random.default_rng(42)
trend = make_bars(list(100.0 * np.cumprod(1 + rng.normal(0.001, 0.01, 120))))

ma_result = run_backtest(
    bars_by_instrument={"ACME": trend},
    instruments={"ACME": Equity(symbol="ACME")},
    strategies=[MovingAverageStrategy(strategy_id="ma", instrument_id="ACME")],
    cost_stack=real_stack,
    allocator=ConstantSplitAllocator(),
    starting_cash=100_000.0,
)
print(f"MA strategy: {ma_result.final_nav:,.2f} over {len(ma_result.equity_curve)} bars, "
      f"{len(ma_result.fills)} fills")
```

Rules of the road: emit a weight-0 target to exit (don't just omit it); if your
strategy holds state (like `ZScorePairsStrategy`'s current side), construct a fresh
instance per run — the sweep enforces this by taking factories (D68). New strategy
modules must carry an honest thesis label in their docstring or
`tests/unit/test_strategy_labels.py` fails (D38/D82).

## 5. Real data: fetch → clean → validate → snapshot

The engine should only ever read **frozen snapshots**, never live fetches — yfinance
restates history, and a restated history is a different dataset (D24). The pipeline:

```python
# not runnable in CI (network) - this is scripts/fetch_fixture_v2.py's job
from datetime import date
from backtest_framework.data.yfinance_source import EquityDataSource

source = EquityDataSource()
bars_xle, volumes_xle, dividends_xle, splits_xle = source.get_raw_history(
    "XLE", date(2015, 1, 1), date(2024, 12, 31)
)
```

Two facts about what comes back (D75, learned from the data, not the docs):
yfinance's `auto_adjust=False` prices **and dividends are already split-adjusted**
— the provider frame is your *signal* series as-is; true as-traded prices for
*execution* are reconstructed (`as_traded_from_adjusted`), and dividends converted
(`as_declared_dividends`). Timestamps are normalized to naive exchange-local time.

Then freeze it — cleaner and validator run at snapshot creation:

```python
# runnable
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate

messy = {"ACME": make_bars([100.0, 101.0, float("nan"), 102.0, 101.5, 103.0])}

cleaned, report = clean(messy)                      # drop-and-report, never rewrites (D73)
print("cleaning changes:", [(c.rule, str(c.timestamp.date())) for c in report.changes])
assert report.changes[0].rule == "non_finite_ohlc"

validation = validate(cleaned, CorporateActions())  # hard violations vs warnings (D74)
assert validation.passed

store = SnapshotStore(WORKDIR / "snapshots")
snapshot_id = store.create(cleaned, CorporateActions(),
                           cleaning_report=report, validation=validation)
snapshot = store.load(snapshot_id)                  # checksum-verified on load
print("snapshot:", snapshot_id[:16], "...")
```

Snapshot ids are content hashes: identical data → same id; restated data → new id.
A snapshot whose validation had **hard** violations is quarantined — `load()`
refuses it, structurally:

```python
# runnable
import pytest
from backtest_framework.data.snapshot_store import QuarantinedSnapshotError

garbage = {"BAD": make_bars([100.0, -5.0, 100.0])}   # non-positive price: hard violation
bad_validation = validate(garbage, CorporateActions())
assert not bad_validation.passed

bad_id = store.create(garbage, CorporateActions(), validation=bad_validation)
with pytest.raises(QuarantinedSnapshotError):
    store.load(bad_id)                               # garbage cannot reach the engine (D26)
```

For corporate actions on real data, pass the splits to the engine and give
`DividendFlow` the declared-frame amounts; strategies see the continuous provider
frame while execution uses as-traded prices:

```python
# not runnable in CI - the pattern from scripts/run_first_result_v2.py
execution = {s: as_traded_from_adjusted(series, actions.splits_by_symbol.get(s, ()))
             for s, series in snapshot.bars_by_symbol.items()}
result = run_backtest(
    bars_by_instrument=execution,                 # as-traded: fills, costs, NAV
    view_bars_by_instrument=snapshot.bars_by_symbol,  # provider frame: signals
    splits_by_instrument=dict(snapshot.actions.splits_by_symbol),
    ...,
)
```

## 6. The cost sweep — the most informative output

"Does it survive 2× costs" beats any single number (D8). The sweep runs the same
scenario at 0×/0.5×/1×/2×/4× frictions (dividend flows don't scale — they're
transfers, not frictions):

```python
# runnable
from backtest_framework.engine.sweep import render_sweep_table, run_cost_sweep

def make_strategies():   # a FACTORY: fresh instances per run, no state leaks (D68)
    return [MovingAverageStrategy(strategy_id="ma", instrument_id="ACME")]

sweep = run_cost_sweep(
    bars_by_instrument={"ACME": trend},
    instruments={"ACME": Equity(symbol="ACME")},
    make_strategies=make_strategies,
    base_cost_stack=real_stack,
    allocator=ConstantSplitAllocator(),
    starting_cash=100_000.0,
)
print(render_sweep_table(sweep))
pnls = [pnl for _, pnl in sweep.net_pnls()]
assert all(b <= a + 1e-6 for a, b in zip(pnls, pnls[1:]))   # monotone in costs
```

## 7. Logging trials — the reproducibility loop

Log every run you might ever cite. The registry is append-only (overwrites are
refused by the primary key) and stores config + snapshot id + seed, so a logged
trial can be reloaded and re-run identically — and the DSR later uses the *count*:

```python
# runnable
from backtest_framework.registry.trial_registry import TrialRegistry

registry = TrialRegistry(WORKDIR / "trials.sqlite")
run_backtest(
    bars_by_instrument={"ACME": trend},
    instruments={"ACME": Equity(symbol="ACME")},
    strategies=make_strategies(),
    cost_stack=real_stack,
    allocator=ConstantSplitAllocator(),
    starting_cash=100_000.0,
    trial_registry=registry,
    trial_id="tutorial-001",
    config={"strategy": "ma_cross", "window": 10, "weight": 0.6},
    snapshot_id=snapshot_id,      # ties the result to frozen data
    seed=0,
)
trial = registry.get_trial("tutorial-001")
print("logged:", trial.trial_id, "->", round(trial.metrics["final_nav"], 2))
```

## 8. Analytics — honest by signature

`rf_annual` and `periods_per_year` are **required** (a silent rf=0 flatters every
market-neutral book — D49/D80). VaR/CVaR refuse small samples instead of printing a
number you shouldn't trust (D36/D81). Monte Carlo requires a seed (D34).

```python
# runnable
from backtest_framework.analytics.metrics import max_drawdown, sharpe
from backtest_framework.analytics.tearsheet import render_metrics_table

navs = [nav for _, nav in ma_result.equity_curve]
returns = [b / a - 1.0 for a, b in zip(navs, navs[1:])]

print("Sharpe (rf=4%):", round(sharpe(returns, rf_annual=0.04, periods_per_year=252), 3))
print("max drawdown:", f"{max_drawdown(ma_result.equity_curve):.2%}")

sheet = render_metrics_table(returns, rf_annual=0.04, periods_per_year=252,
                             equity_curve=ma_result.equity_curve, mc_seed=7)
print(sheet)
assert "insufficient data" in sheet    # ~120 bars can't support a 95% VaR (needs >=600)
```

## 9. Validation science — before you believe any result

**Walk-forward with structurally-guarded fitting**: anything that fits (pair
selection, future regime models) receives training data as DataViews only — the test
window is physically absent (D85). **Selection logs its multiplicity** (D29), and
the **Deflated Sharpe Ratio** pulls the trial count from the registry, never from
your memory (D86):

```python
# runnable
from backtest_framework.validation.dsr import deflated_sharpe_from_trials, deflated_sharpe_ratio
from backtest_framework.validation.pair_selection import select_pairs
from backtest_framework.validation.walk_forward import walk_forward_windows

# A small synthetic universe with a shared factor, so plausible pairs exist.
universe = {}
common = np.cumsum(rng.normal(0.0002, 0.008, 200))
for k in range(6):
    idio = np.cumsum(rng.normal(0.0, 0.006, 200))
    universe[f"S{k}"] = make_bars(list(np.exp(np.log(100) + common + idio)))

window = next(iter(walk_forward_windows(universe, train_size=100, test_size=50)))
selection = select_pairs(window.train_views, top_n=2)
print("selected:", selection.ranked_pairs, "of", selection.n_pairs_tested, "tested")
assert selection.n_pairs_tested == 15    # C(6,2) - log this number with your trial!

# The famous DSR example (Bailey & Lopez de Prado): an annualized Sharpe of 2.5,
# after 100 trials, is NOT significant at 95%:
import math
dsr = deflated_sharpe_ratio(sr=2.5 / math.sqrt(250), t=1250, skew=-3, kurt=10,
                            n_trials=100, var_trials=0.002)
print("DSR:", round(dsr, 4))
assert dsr < 0.95
```

There are also zero-edge synthetic pairs (`validation/synthetic.py`) for null tests
— if your strategy profits on those, you have a look-ahead bug, not an edge (D23/D87).

## 10. The full study — everything at once

`research/pairs_study.py` composes all of the above into the Phase G loop: snapshot
→ walk-forward windows → top-N Gatev selection per window → the selected pairs
traded as N strategies in ONE portfolio (shared legs net internally) → cost sweep →
per-window trials logged → registry-fed DSR → markdown artifact.

```bash
# the real thing, offline and deterministic from committed fixtures:
uv run python scripts/run_pairs_study.py     # -> docs/results/pairs_study_v1.md
# to build a new universe first (network, one-time):
uv run python scripts/fetch_universe.py
```

Programmatic use follows `tests/integration/test_pairs_study.py`:

```python
# runnable
from backtest_framework.research.pairs_study import StudyConfig, run_pairs_study

study_registry = TrialRegistry(WORKDIR / "study_trials.sqlite")
study = run_pairs_study(
    bars_by_symbol=universe,
    volumes_by_symbol={s: [5e6] * 200 for s in universe},
    actions=CorporateActions(),
    registry=study_registry,
    snapshot_id="tutorial-universe",
    config=StudyConfig(train_size=100, test_size=50, step=50, top_n=2, lookback=20,
                       entry_z=1.5, exit_z=0.5, leg_weight=0.5, multipliers=(0.0, 1.0)),
)
print(f"windows: {study.n_windows}, pairs tested/window: {study.n_pairs_tested_per_window}, "
      f"DSR: {study.dsr:.4f}")
assert len(study_registry) == study.n_windows * 2      # every run logged
```

## 11. Reading the outputs

- `docs/results/first_real_number.md` / `_v2.md` — the single-pair XLE/XOP runs
  (v1 unhardened data path; v2 through the full pipeline). Both preserved; every
  number regenerable by the scripts.
- `docs/results/pairs_study_v1.md` — the walk-forward study over 57 ETFs. Its
  verdict (gross ≈ nothing, −13% at real costs, DSR = 0.0000) is the framework
  working as intended: an honest "no edge," with the caveats printed beside the
  numbers.
- `docs/verification/cross_engine_reconciliation.md` — why you can trust the
  engine's arithmetic (penny-exact vs vectorbt over 2,515 bars / 1,370 trades).

## 12. Extending it — the house rules

1. **Record the decision** — anything non-obvious gets a `docs/decisions/D<n>` file
   ("decision — because rationale", R4). For the next number ask the directory —
   `ls docs/decisions | grep -oE '^D[0-9]+' | sort -V | tail -1` — rather than the index, which
   lists every number but is regenerated rather than appended to.
   [`CONTRIBUTING.md`](../CONTRIBUTING.md) has the record template.
2. **A step is done when its gate passes** — new components ship with tests; golden
   tests ship with a `.hand.txt` showing the arithmetic (D39/D47).
3. **No false affordances** — a knob no code reads, or a method returning a wrong
   number instead of raising, is a bug (D48).
4. **The framework is frozen** (post-Step-12) except bug fixes; study code goes in
   `research/`, versioned per study (D89).
5. When in doubt, [PHILOSOPHY.md](../PHILOSOPHY.md) is the tie-breaker.

## Gotchas worth knowing before they bite

- `sharpe()`/`sortino()` without `rf_annual`/`periods_per_year` is a `TypeError` —
  deliberate (D80). Same for the Monte Carlo `seed` (D81).
- Whole-share rounding means tiny NAV drifts re-trade ±1 shares at high weights;
  use `Equity(quantity_precision=8)` for fractional sizing.
- Stateful strategies must be fresh per run — hand the sweep a factory (D68).
- vectorbt convention boundary: at target weight ≈ 1.0 it reserves fees from the
  purchase while this engine charges cash (D79) — relevant only if you reconcile.
- σ/ADV calibration is full-sample (D66) and the data is single-source yfinance
  (D26) — both documented caveats, restated in every results artifact.
- Risk violations are **recorded, not enforced** (D62): check
  `result.violations`, don't assume breaches were blocked.
