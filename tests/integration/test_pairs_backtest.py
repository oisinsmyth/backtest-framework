"""Integration tests for multi-instrument (pairs) backtests through run_backtest,
proving D45's alignment policy end to end.

The golden scenario's hand-worked arithmetic lives in test_pairs_backtest.hand.txt,
next to this file, per D39. One test hits real yfinance for XLE/XOP and is marked
live_fetch (excluded from the default run, same convention as test_yfinance_source.py).
"""

from datetime import date, datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.yfinance_source import EquityDataSource
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


def test_dropped_bar_on_one_leg_drops_it_for_both_and_carry_spans_the_real_gap():
    a = Equity(symbol="A")
    b = Equity(symbol="B")
    instruments = {"A": a, "B": b}
    cost_stack = CostStack(
        trade_bricks=(FlatCommission(amount=1.00), PercentOfNotionalSpread(bps=5.0)),
        carry_bricks=(FlatRateCarry(annual_rate=0.06),),
    )

    monday = datetime(2026, 7, 13)
    tuesday = datetime(2026, 7, 14)
    wednesday = datetime(2026, 7, 15)

    bars_a = [
        TimestampedBar(monday, _bar(100.0)),
        TimestampedBar(tuesday, _bar(100.0)),  # exists for A...
        TimestampedBar(wednesday, _bar(100.0)),
    ]
    bars_b = [
        TimestampedBar(monday, _bar(50.0)),
        # ...but B has no Tuesday bar (e.g. a halt) — Tuesday must be dropped for A too.
        TimestampedBar(wednesday, _bar(50.0)),
    ]

    strategy = ScheduledWeightStrategy(
        strategy_id="pairs", weights_by_instrument={"A": [0.4, 0.4], "B": [-0.2, -0.2]}
    )

    result = run_backtest(
        bars_by_instrument={"A": bars_a, "B": bars_b},
        instruments=instruments,
        strategies=[strategy],
        cost_stack=cost_stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    # Only 2 aligned bars ran (Tuesday dropped), not 3.
    assert len(result.equity_curve) == 2
    assert result.equity_curve[0][0] == monday
    assert result.equity_curve[1][0] == wednesday  # not tuesday

    navs = [nav for _, nav in result.equity_curve]
    assert navs[0] == pytest.approx(99_968.00, rel=TOLERANCE)
    assert navs[1] == pytest.approx(99_961.424657534253, rel=TOLERANCE)

    assert result.final_positions == {"A": 400.0, "B": -400.0}


@pytest.mark.live_fetch
def test_real_xle_xop_pair_runs_end_to_end():
    source = EquityDataSource()
    xle = Equity(symbol="XLE")
    xop = Equity(symbol="XOP")
    instruments = {"XLE": xle, "XOP": xop}

    start, end = date(2024, 1, 2), date(2024, 2, 1)
    bars_xle = source.get_bars(xle, start=start, end=end, timeframe="1d")
    bars_xop = source.get_bars(xop, start=start, end=end, timeframe="1d")

    n = min(len(bars_xle), len(bars_xop))
    strategy = ScheduledWeightStrategy(
        strategy_id="pairs", weights_by_instrument={"XLE": [0.5] * n, "XOP": [-0.5] * n}
    )
    cost_stack = CostStack(
        trade_bricks=(FlatCommission(amount=1.00), PercentOfNotionalSpread(bps=5.0)),
        carry_bricks=(FlatRateCarry(annual_rate=0.06),),
    )

    result = run_backtest(
        bars_by_instrument={"XLE": bars_xle, "XOP": bars_xop},
        instruments=instruments,
        strategies=[strategy],
        cost_stack=cost_stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    assert len(result.equity_curve) > 0
    assert "XLE" in result.final_positions
    assert "XOP" in result.final_positions
    assert result.final_positions["XLE"] > 0  # long leg
    assert result.final_positions["XOP"] < 0  # short leg
