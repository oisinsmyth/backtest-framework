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


def test_zero_overlap_alignment_raises_instead_of_empty_backtest():
    # D99 (audit F11): disjoint timestamps used to return an empty result whose
    # final NAV equalled starting cash — a silently-empty backtest.
    bars = {
        "A": [TimestampedBar(datetime(2026, 1, 5), _bar(10.0))],
        "B": [TimestampedBar(datetime(2026, 1, 6), _bar(10.0))],
    }
    with pytest.raises(ValueError, match="zero common bars"):
        run_backtest(
            bars_by_instrument=bars,
            instruments={"A": Equity(symbol="A"), "B": Equity(symbol="B")},
            strategies=[],
            cost_stack=CostStack(),
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
        )


def _dividend_split_gap_run(div_date, split_date):
    """100 shares held into a Fri->Mon gap containing a dividend and a 4:1 split
    (in either order) — returns the dividend cash actually credited (D99)."""
    from backtest_framework.costs.equity_bricks import DividendFlow

    fri, mon = datetime(2026, 1, 9, 16), datetime(2026, 1, 12, 16)
    bars = {
        "X": [
            TimestampedBar(fri, _bar(100.0)),
            TimestampedBar(mon, _bar(25.0)),  # post-split as-traded price
        ]
    }
    stack = CostStack(event_flow_bricks=(DividendFlow(dividends_by_symbol={"X": ((div_date, 1.0),)}),))
    result = run_backtest(
        bars_by_instrument=bars,
        instruments={"X": Equity(symbol="X")},
        strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"X": [0.1, 0.1]})],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        splits_by_instrument={"X": [(split_date, 4.0)]},
    )
    # Fill on Friday: 0.1 x 100k / 100 = 100 shares. Dividend cash = final cash
    # minus (cash after the Friday fill), with Monday's NAV-driven re-size fill
    # (D61) backed out so only the event flow remains.
    cash_after_friday_fill = 100_000.0 - 100 * 100.0
    monday_fill_cash = sum(-qty * price - cost for ts, _, qty, price, cost in result.fills if ts != fri)
    return result.cash_curve[-1][1] - cash_after_friday_fill - monday_fill_cash


def test_dividend_before_split_in_same_gap_pays_pre_split_shares():
    # D99 (audit F19): the old code scaled positions for the split BEFORE computing
    # flows, so a dividend earlier in the same gap paid on 4x the shares held.
    sat, sun = datetime(2026, 1, 10, 16), datetime(2026, 1, 11, 16)
    dividend_cash = _dividend_split_gap_run(div_date=sat, split_date=sun)
    assert dividend_cash == pytest.approx(100 * 1.0, rel=TOLERANCE)  # NOT 400


def test_dividend_after_split_in_same_gap_pays_post_split_shares():
    sat, sun = datetime(2026, 1, 10, 16), datetime(2026, 1, 11, 16)
    dividend_cash = _dividend_split_gap_run(div_date=sun, split_date=sat)
    assert dividend_cash == pytest.approx(400 * 1.0, rel=TOLERANCE)


def test_dividend_on_the_split_ex_date_pays_post_split_shares():
    # A dividend exactly ON the split ex-date is already post-split-frame per share
    # (as_declared_dividends scales only by splits strictly after it, D75).
    sun = datetime(2026, 1, 11, 16)
    dividend_cash = _dividend_split_gap_run(div_date=sun, split_date=sun)
    assert dividend_cash == pytest.approx(400 * 1.0, rel=TOLERANCE)
