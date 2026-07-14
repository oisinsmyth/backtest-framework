"""Engine split handling (D75): positions (broker AND virtual books) scale by the
ratio on the ex-date; NAV is continuous across the event by construction (qty x r at
price x 1/r). As-traded series: $8 pre-split, $32 post 1-for-4 reverse split.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


def test_reverse_split_scales_position_and_preserves_nav():
    day1, day2, day3 = datetime(2020, 3, 26), datetime(2020, 3, 27), datetime(2020, 3, 30)
    bars = {
        "XOP": [
            TimestampedBar(day1, _bar(8.0)),
            TimestampedBar(day2, _bar(8.0)),
            TimestampedBar(day3, _bar(32.0)),  # post-split, as-traded
        ]
    }
    strategy = ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"XOP": [1.0, 1.0, 1.0]})

    result = run_backtest(
        bars_by_instrument=bars,
        instruments={"XOP": Equity(symbol="XOP")},
        strategies=[strategy],
        cost_stack=CostStack(),  # zero frictions: NAV change isolates the split mechanics
        allocator=ConstantSplitAllocator(),
        starting_cash=32_000.0,
        splits_by_instrument={"XOP": [(day3, 0.25)]},
    )

    navs = [nav for _, nav in result.equity_curve]
    # Bar 0: buy 32,000/8 = 4,000 shares. Bar 2: split scales 4,000 -> 1,000 @ 32.
    assert navs == pytest.approx([32_000.0, 32_000.0, 32_000.0], rel=TOLERANCE)  # continuous
    assert result.final_positions["XOP"] == pytest.approx(1_000.0, rel=TOLERANCE)


def test_view_execution_separation_feeds_strategies_the_view_series():
    # Execution series jumps 4x at the split (as-traded); view series is continuous
    # (adjusted). A strategy whose weights depend on what it SEES would break on the
    # jump — here we just assert the engine accepts both series and enforces
    # timestamp coverage.
    day1, day2 = datetime(2020, 3, 27), datetime(2020, 3, 30)
    execution = {"XOP": [TimestampedBar(day1, _bar(8.0)), TimestampedBar(day2, _bar(32.0))]}
    views = {"XOP": [TimestampedBar(day1, _bar(32.0)), TimestampedBar(day2, _bar(32.0))]}

    result = run_backtest(
        bars_by_instrument=execution,
        instruments={"XOP": Equity(symbol="XOP")},
        strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"XOP": [0.0, 0.0]})],
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=10_000.0,
        view_bars_by_instrument=views,
    )
    assert len(result.equity_curve) == 2

    # Missing a timestamp in the view series is a loud error, never a silent raw bar.
    with pytest.raises(ValueError, match="view_bars_by_instrument"):
        run_backtest(
            bars_by_instrument=execution,
            instruments={"XOP": Equity(symbol="XOP")},
            strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"XOP": [0.0]})],
            cost_stack=CostStack(),
            allocator=ConstantSplitAllocator(),
            starting_cash=10_000.0,
            view_bars_by_instrument={"XOP": [TimestampedBar(day1, _bar(32.0))]},  # day2 missing
        )
