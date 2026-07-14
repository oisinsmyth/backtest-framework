"""Integration tests for run_backtest (engine/backtest.py), the production loop
generalizing Step 3's test-only mini-backtest harness.

The regression-anchor test's reasoning (why it reproduces Step 3's golden numbers
despite D61's per-bar NAV-based capital) lives in test_backtest_loop.hand.txt, next to
this file.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.risk import RiskLimits
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47
AAPL = Equity(symbol="AAPL")
INSTRUMENTS = {"AAPL": AAPL}
COST_STACK = CostStack(
    trade_bricks=(FlatCommission(amount=1.00), PercentOfNotionalSpread(bps=5.0)),
    carry_bricks=(FlatRateCarry(annual_rate=0.06),),
)


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


def test_run_backtest_reproduces_step3_golden_master_exactly():
    bars = [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 14, 16, 0), _bar(100.0)),
    ]
    strategy = ScheduledWeightStrategy(strategy_id="s1", instrument_id="AAPL", weights=[0.5, 0.5, 0.0])

    result = run_backtest(
        bars=bars,
        instrument_id="AAPL",
        instruments=INSTRUMENTS,
        strategies=[strategy],
        cost_stack=COST_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    navs = [nav for _, nav in result.equity_curve]
    assert navs[0] == pytest.approx(99_974.00, rel=TOLERANCE)
    assert navs[1] == pytest.approx(99_949.342465753425, rel=TOLERANCE)
    assert navs[2] == pytest.approx(99_915.123287671244, rel=TOLERANCE)
    assert result.final_positions.get("AAPL", 0.0) == 0.0


def test_run_backtest_nets_offsetting_strategies_avoiding_double_costs():
    # Strategy A wants +100% of its capital in AAPL, strategy B wants -100% (short).
    # With an even split they cancel exactly -> zero external order, zero trade cost,
    # even though both strategies "traded" in their own virtual books.
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy_a = ScheduledWeightStrategy(strategy_id="A", instrument_id="AAPL", weights=[1.0])
    strategy_b = ScheduledWeightStrategy(strategy_id="B", instrument_id="AAPL", weights=[-1.0])

    result = run_backtest(
        bars=bars,
        instrument_id="AAPL",
        instruments=INSTRUMENTS,
        strategies=[strategy_a, strategy_b],
        cost_stack=COST_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    assert result.final_positions.get("AAPL", 0.0) == 0.0  # broker book stays flat
    assert result.final_cash == 100_000.0  # no trade cost charged - nothing was filled
    assert result.equity_curve[-1][1] == 100_000.0


def test_run_backtest_records_risk_violation_without_halting():
    # weight=1.0 against the full starting capital produces roughly 1000 shares @
    # ~100 = ~100,000 notional, comfortably over a deliberately low 50,000 limit.
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy = ScheduledWeightStrategy(strategy_id="s1", instrument_id="AAPL", weights=[1.0])

    result = run_backtest(
        bars=bars,
        instrument_id="AAPL",
        instruments=INSTRUMENTS,
        strategies=[strategy],
        cost_stack=CostStack(),  # zero-cost, isolates the risk check from cost arithmetic
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        risk_limits=RiskLimits(max_gross_exposure=50_000.0),
    )

    assert len(result.violations) == 1
    violation = result.violations[0]
    assert violation.rule == "max_gross_exposure"
    assert violation.bar_index == 0
    assert violation.observed == pytest.approx(100_000.0, rel=TOLERANCE)
    # No enforcement exists yet (D62) - the trade still went through despite the
    # violation being recorded.
    assert result.final_positions.get("AAPL", 0.0) == 1000.0


def test_run_backtest_logs_a_real_trial_to_the_registry(tmp_path):
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy = ScheduledWeightStrategy(strategy_id="s1", instrument_id="AAPL", weights=[0.5])
    registry = TrialRegistry(tmp_path / "trials.sqlite")

    result = run_backtest(
        bars=bars,
        instrument_id="AAPL",
        instruments=INSTRUMENTS,
        strategies=[strategy],
        cost_stack=COST_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        trial_registry=registry,
        trial_id="trial-001",
        config={"strategy": "scheduled_weight", "weights": [0.5]},
        snapshot_id="snap-test",
        seed=7,
    )

    record = registry.get_trial("trial-001")
    assert record.metrics["final_nav"] == pytest.approx(result.final_nav, rel=TOLERANCE)
    assert record.metrics["num_bars"] == 1
    assert record.snapshot_id == "snap-test"
    assert record.seed == 7


def test_run_backtest_requires_trial_id_and_config_when_registry_given(tmp_path):
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy = ScheduledWeightStrategy(strategy_id="s1", instrument_id="AAPL", weights=[0.5])
    registry = TrialRegistry(tmp_path / "trials.sqlite")

    with pytest.raises(ValueError, match="trial_id"):
        run_backtest(
            bars=bars,
            instrument_id="AAPL",
            instruments=INSTRUMENTS,
            strategies=[strategy],
            cost_stack=COST_STACK,
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
            trial_registry=registry,
            # trial_id and config both omitted
        )
