"""The full data pipeline end to end, offline.

Raw fixture -> clean -> validate -> snapshot -> engine (split-adjusted views for signals,
as-traded prices for execution, explicit dividend flows, split-scaled positions through BBB's
2020-03-30 1-for-4 reverse split) -> cost sweep.
"""

from pathlib import Path

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import (
    BorrowFee,
    DividendFlow,
    IBKRCommission,
    ImpactParams,
    MarginInterest,
    SqrtImpact,
)
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import (
    as_declared_dividends,
    as_traded_from_adjusted,
    load_events_json,
)
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import Snapshot, SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

TOLERANCE = 1e-6
REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "synthetic_pair_daily_raw.csv"
EVENTS = REPO / "data" / "fixtures" / "synthetic_pair_daily_raw_events.json"
STARTING_CASH = 100_000.0

# Sigma on the split-adjusted closes; ADV is the full-sample mean share volume in the
# split-adjusted volume frame. Full-sample calibration: a mild look-ahead in the cost parameters.
IMPACT_PARAMS = {
    "AAA": ImpactParams(sigma_daily=0.0158, adv_shares=42_336_935),
    "BBB": ImpactParams(sigma_daily=0.018789, adv_shares=5_310_039),
}
STRATEGY_PARAMS = dict(lookback=60, entry_z=2.0, exit_z=0.5, leg_weight=1.0)
INSTRUMENTS = {"AAA": Equity(symbol="AAA"), "BBB": Equity(symbol="BBB")}


def create_and_load_snapshot(store_root: Path) -> Snapshot:
    """Fixture -> clean -> validate -> freeze -> load. The engine only ever sees the loaded
    snapshot. Snapshots are content-addressed, so rerunning is idempotent."""
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)

    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)

    store = SnapshotStore(store_root)
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=None,
        cleaning_report=cleaning_report,
        validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    return store.load(snapshot_id)


def build_run_inputs(snapshot: Snapshot):
    execution = {
        symbol: as_traded_from_adjusted(series, snapshot.actions.splits_by_symbol.get(symbol, ()))
        for symbol, series in snapshot.bars_by_symbol.items()
    }
    views = snapshot.bars_by_symbol  # provider frame: split-adjusted, signal-continuous
    declared_dividends = {
        symbol: tuple(as_declared_dividends(divs, snapshot.actions.splits_by_symbol.get(symbol, ())))
        for symbol, divs in snapshot.actions.dividends_by_symbol.items()
    }
    splits = {symbol: list(s) for symbol, s in snapshot.actions.splits_by_symbol.items() if s}
    return execution, views, declared_dividends, splits


def build_cost_stack(declared_dividends) -> CostStack:
    return CostStack(
        trade_bricks=(
            IBKRCommission(),
            SqrtImpact(params_by_symbol=IMPACT_PARAMS),
            PercentOfNotionalSpread(bps=1.0),
        ),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol=declared_dividends),),
    )


def make_strategies():
    return [ZScorePairsStrategy(strategy_id="zscore_pairs", instrument_a="AAA", instrument_b="BBB", **STRATEGY_PARAMS)]


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    snapshot = create_and_load_snapshot(store_root=tmp_path_factory.mktemp("snapshots"))
    execution, views, declared_dividends, splits = build_run_inputs(snapshot)
    return snapshot, execution, views, declared_dividends, splits


def test_snapshot_freezes_clean_and_unquarantined(pipeline):
    snapshot, *_ = pipeline
    assert snapshot.meta["quarantined"] is False
    assert snapshot.meta["validation"]["passed"] is True
    # The 2020-03-09 crash day (BBB -37%) is recorded as a warning, not hidden.
    warnings = [v for v in snapshot.meta["validation"]["violations"] if not v["hard"]]
    assert warnings


def test_sweep_on_hardened_pipeline_is_monotonic(pipeline):
    snapshot, execution, views, declared_dividends, splits = pipeline
    sweep = run_cost_sweep(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(declared_dividends),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(0.0, 0.5, 1.0, 2.0, 4.0),
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    pnls = [pnl for _, pnl in sweep.net_pnls()]
    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))


def test_zero_multiplier_equals_frictionless_run_with_flows_retained(pipeline):
    # Event flows are not frictions and do not scale: the 0x baseline is a run with zero
    # frictions but the same dividend flows, not an empty CostStack.
    snapshot, execution, views, declared_dividends, splits = pipeline
    sweep = run_cost_sweep(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        make_strategies=make_strategies,
        base_cost_stack=build_cost_stack(declared_dividends),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        multipliers=(0.0,),
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    frictionless = run_backtest(
        bars_by_instrument=execution,
        instruments=INSTRUMENTS,
        strategies=make_strategies(),
        cost_stack=CostStack(event_flow_bricks=build_cost_stack(declared_dividends).event_flow_bricks),
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
        splits_by_instrument=splits,
        view_bars_by_instrument=views,
    )
    assert sweep.runs[0].result.final_nav == pytest.approx(frictionless.final_nav, rel=TOLERANCE)
