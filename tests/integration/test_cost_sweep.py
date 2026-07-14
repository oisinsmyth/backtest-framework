"""Integration tests for the cost-multiplier sweep (D8, D68) on a synthetic
scenario — fast, exact, offline. The real-fixture half of the Step 6 gates lives in
test_first_result_e2e.py.

Scenario: one round trip (in at bar 0, out at bar 2) at constant price with a flat
$10 commission as the only cost. Two fills per run, so net P&L = −2 × 10 × multiplier
exactly — monotonicity and 0×-equals-zero-cost are checkable to the penny, not just
directionally.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.engine.sweep import max_drawdown, run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


BARS = {
    "AAPL": [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 14, 16, 0), _bar(100.0)),
    ]
}
INSTRUMENTS = {"AAPL": Equity(symbol="AAPL")}
BASE_STACK = CostStack(trade_bricks=(FlatCommission(amount=10.0),))


def _make_strategies():
    return [ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5, 0.5, 0.0]})]


def _sweep(multipliers):
    return run_cost_sweep(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        make_strategies=_make_strategies,
        base_cost_stack=BASE_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        multipliers=multipliers,
    )


def test_net_pnl_is_monotonically_non_increasing_in_the_multiplier():
    sweep = _sweep((0.0, 0.5, 1.0, 2.0, 4.0))
    pnls = [pnl for _, pnl in sweep.net_pnls()]

    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))
    # And exactly: two $10 fills per run, scaled.
    assert pnls == pytest.approx([0.0, -10.0, -20.0, -40.0, -80.0], abs=TOLERANCE)


def test_zero_multiplier_run_equals_an_empty_cost_stack_run():
    sweep = _sweep((0.0,))
    zero_cost_result = run_backtest(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        strategies=_make_strategies(),
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    sweep_navs = [nav for _, nav in sweep.runs[0].result.equity_curve]
    zero_navs = [nav for _, nav in zero_cost_result.equity_curve]
    assert sweep_navs == pytest.approx(zero_navs, rel=TOLERANCE)


def test_sweep_builds_fresh_strategies_per_run():
    calls = 0

    def counting_factory():
        nonlocal calls
        calls += 1
        return _make_strategies()

    run_cost_sweep(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        make_strategies=counting_factory,
        base_cost_stack=BASE_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        multipliers=(0.0, 1.0, 2.0),
    )
    assert calls == 3  # one fresh strategy list per multiplier — no state leaks (D68)


def test_max_drawdown_arithmetic():
    curve = [(None, 100.0), (None, 110.0), (None, 99.0), (None, 105.0)]
    # Peak 110 -> trough 99: (110-99)/110 = 10%
    assert max_drawdown(curve) == pytest.approx(0.1, rel=TOLERANCE)
    assert max_drawdown([(None, 100.0), (None, 101.0)]) == 0.0
