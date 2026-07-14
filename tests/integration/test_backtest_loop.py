"""Integration tests for run_backtest (engine/backtest.py), the production loop
generalizing Step 3's test-only mini-backtest harness.

The regression-anchor test's reasoning (why it reproduces Step 3's golden numbers
despite D61's per-bar NAV-based capital) lives in test_backtest_loop.hand.txt, next to
this file. These tests are all single-instrument (a one-entry bars_by_instrument
mapping, D64's N=1 case) — multi-instrument/pairs scenarios live in
tests/integration/test_pairs_backtest.py.
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
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5, 0.5, 0.0]})

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
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
    strategy_a = ScheduledWeightStrategy(strategy_id="A", weights_by_instrument={"AAPL": [1.0]})
    strategy_b = ScheduledWeightStrategy(strategy_id="B", weights_by_instrument={"AAPL": [-1.0]})

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
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
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [1.0]})

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
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
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5]})
    registry = TrialRegistry(tmp_path / "trials.sqlite")

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
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
    assert record.metrics["num_instruments"] == 1
    assert record.snapshot_id == "snap-test"
    assert record.seed == 7


def test_run_backtest_requires_trial_id_and_config_when_registry_given(tmp_path):
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5]})
    registry = TrialRegistry(tmp_path / "trials.sqlite")

    with pytest.raises(ValueError, match="trial_id"):
        run_backtest(
            bars_by_instrument={"AAPL": bars},
            instruments=INSTRUMENTS,
            strategies=[strategy],
            cost_stack=COST_STACK,
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
            trial_registry=registry,
            # trial_id and config both omitted
        )


def test_enforce_pretrade_rejects_breaching_order_and_keeps_books_reconciled():
    # D101 (audit F12): with enforcement on, the same breaching order is REJECTED —
    # never fills, virtual books drop it too (broker and sleeves stay reconciled),
    # and the violation is recorded with its bar index.
    bars = [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(100.0)),
    ]
    strategy = ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [1.0, 1.0]})

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
        instruments=INSTRUMENTS,
        strategies=[strategy],
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        risk_limits=RiskLimits(max_gross_exposure=50_000.0),
        enforce_pretrade=True,
    )

    assert result.final_positions.get("AAPL", 0.0) == 0.0  # nothing filled
    assert result.final_cash == 100_000.0
    assert result.fills == [] and result.virtual_fills == []
    assert result.final_virtual_positions == {}  # sleeves reconciled with broker
    # Rejected on BOTH bars — the strategy re-attempts and is re-rejected.
    assert [v.bar_index for v in result.violations] == [0, 1]
    assert all(v.rule == "max_gross_exposure" for v in result.violations)


def test_enforce_pretrade_requires_risk_limits():
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    with pytest.raises(ValueError, match="requires risk_limits"):
        run_backtest(
            bars_by_instrument={"AAPL": bars},
            instruments=INSTRUMENTS,
            strategies=[],
            cost_stack=CostStack(),
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
            enforce_pretrade=True,
        )


def test_virtual_fills_are_strategy_tagged_even_when_netting_cancels():
    # D101 (audit F5): the netting scenario keeps the broker book flat, but the
    # sleeve-level record must show both strategies' orders — this is the
    # strategy-tagged fill stream D46 promised.
    bars = [TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0))]
    strategy_a = ScheduledWeightStrategy(strategy_id="A", weights_by_instrument={"AAPL": [1.0]})
    strategy_b = ScheduledWeightStrategy(strategy_id="B", weights_by_instrument={"AAPL": [-1.0]})

    result = run_backtest(
        bars_by_instrument={"AAPL": bars},
        instruments=INSTRUMENTS,
        strategies=[strategy_a, strategy_b],
        cost_stack=COST_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    assert result.fills == []  # broker saw nothing (netted away)
    assert len(result.virtual_fills) == 2
    by_strategy = {sid: qty for _, sid, _, qty, _ in result.virtual_fills}
    assert by_strategy["A"] == 500.0 and by_strategy["B"] == -500.0  # 50k each @ 100
    assert result.final_virtual_positions == {("A", "AAPL"): 500.0, ("B", "AAPL"): -500.0}
    # Sleeve books sum to the broker book exactly.
    assert sum(result.final_virtual_positions.values()) == result.final_positions.get("AAPL", 0.0)
