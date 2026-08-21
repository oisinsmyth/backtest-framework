"""THE BREAKOUT GOLDEN MASTER (D39, D109): a 9-bar long-flat breakout scenario
asserted line by line against hand arithmetic.

Ground truth is test_breakout_golden.hand.txt, worked out from the stated rules
without running this codebase. It pins, in one scenario: the entry extremum excluding
the current bar, next-open fill timing, the 40 bp taker fee on every fill, the
hysteresis gap between a 3-bar-high entry and a 2-bar-low exit, and the interior
rebalancing that weight targeting causes under next-open fills.

Golden by construction (D77): if any of those five behaviours changes, this test goes
red and the hand file is the argument, not the code.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.instruments.equity import Equity
from backtest_framework.research.trade_diagnostics import extract_episodes, summarise
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import BreakoutStrategy, FixedWeight

TOLERANCE = 1e-6  # D47

SYMBOL = "BTC-TEST"
DAYS = [datetime(2021, 1, day) for day in range(1, 10)]
OHLC = [
    (100, 110, 90, 100),
    (100, 105, 95, 100),
    (100, 108, 96, 100),
    (100, 130, 99, 125),
    (125, 126, 99, 100),
    (100, 205, 98, 200),
    (200, 201, 94, 95),
    (95, 96, 89, 90),
    (90, 93, 88, 92),
]


@pytest.fixture(scope="module")
def bars():
    return [
        TimestampedBar(day, Bar(open=o, high=h, low=lo, close=c))
        for day, (o, h, lo, c) in zip(DAYS, OHLC)
    ]


@pytest.fixture(scope="module")
def result(bars):
    return run_backtest(
        bars_by_instrument={SYMBOL: bars},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[
            BreakoutStrategy(
                strategy_id="breakout",
                instrument_id=SYMBOL,
                n_entry=3,
                n_exit=2,
                weight_source=FixedWeight(1.0),
            )
        ],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=40.0),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )


def test_every_fill_line_by_line(result):
    expected = [
        (DAYS[4], 800.0, 125.0, 400.0),
        (DAYS[5], -4.0, 100.0, 1.60),
        (DAYS[6], -0.008, 200.0, 0.0064),
        (DAYS[7], -795.992, 95.0, 302.47696),
    ]
    assert len(result.fills) == len(expected)
    for (ts, instrument_id, quantity, price, cost), exp in zip(result.fills, expected):
        assert (ts, instrument_id) == (exp[0], SYMBOL)
        assert quantity == pytest.approx(exp[1], abs=TOLERANCE)
        assert price == exp[2]  # fill prices are bar opens, exact
        assert cost == pytest.approx(exp[3], rel=TOLERANCE)


def test_the_signal_bar_does_not_fill_on_itself(result):
    """The entry decision is taken at bar 3's close of 125; the fill is bar 4's open
    of 125 — the same number here by construction of the fixture, but a DIFFERENT
    bar. What proves it is the timestamp: no fill is stamped on day 4 (bar 3)."""
    assert DAYS[3] not in [ts for ts, *_ in result.fills]
    assert result.fills[0][0] == DAYS[4]


def test_equity_curve_line_by_line(result):
    expected = [
        100_000.00,
        100_000.00,
        100_000.00,
        100_000.00,
        79_600.00,
        159_198.40,
        75_619.2336,
        75_316.75664,
        75_316.75664,
    ]
    assert [ts for ts, _ in result.equity_curve] == DAYS
    for (_, nav), exp in zip(result.equity_curve, expected):
        assert nav == pytest.approx(exp, rel=TOLERANCE)


def test_final_state(result):
    assert result.final_cash == pytest.approx(75_316.75664, rel=TOLERANCE)
    assert result.final_positions.get(SYMBOL, 0.0) == pytest.approx(0.0, abs=1e-9)
    assert result.final_nav == pytest.approx(75_316.75664, rel=TOLERANCE)


def test_costs_reconcile_against_the_nav_change(result):
    total_fees = sum(cost for *_, cost in result.fills)
    assert total_fees == pytest.approx(704.08336, rel=TOLERANCE)
    gross = -sum(quantity * price for _ts, _i, quantity, price, _c in result.fills)
    assert gross == pytest.approx(-23_979.16, rel=TOLERANCE)
    assert result.final_nav - 100_000.0 == pytest.approx(gross - total_fees, rel=TOLERANCE)


def test_no_carry_was_charged(result):
    """The stack has no carry or portfolio-carry bricks, so every penny of the NAV
    change must be explained by fills alone — asserted above. This test states the
    premise explicitly so a future stack change cannot quietly reinterpret the
    reconciliation."""
    gross = -sum(quantity * price for _ts, _i, quantity, price, _c in result.fills)
    fees = sum(cost for *_, cost in result.fills)
    assert result.final_cash == pytest.approx(100_000.0 + gross - fees, rel=TOLERANCE)


def test_trade_episode_diagnostics(result, bars):
    episodes = extract_episodes(result, SYMBOL, bars)
    assert len(episodes) == 1
    e = episodes[0]
    assert (e.entry_index, e.exit_index, e.bars_held) == (4, 7, 3)
    assert (e.entry_price, e.exit_price) == (125.0, 95.0)
    assert e.n_fills == 4
    assert e.costs == pytest.approx(704.08336, rel=TOLERANCE)
    assert e.rebalance_costs == pytest.approx(1.6064, rel=TOLERANCE)
    assert e.traded_notional == pytest.approx(176_020.84, rel=TOLERANCE)
    assert e.mfe == pytest.approx(0.64, rel=TOLERANCE)
    assert e.mae == pytest.approx(-0.248, rel=TOLERANCE)
    assert e.net_pnl == pytest.approx(-24_683.24336, rel=TOLERANCE)


def test_diagnostics_summary(result, bars):
    episodes = extract_episodes(result, SYMBOL, bars)
    summary = summarise(
        episodes,
        equity_curve=result.equity_curve,
        instrument_bars=bars,
        n_oos_bars=len(bars),
        whipsaw_bars=3,
    )
    assert summary.n_closed_trades == 1
    assert summary.n_open_at_end == 0
    assert summary.win_rate == 0.0
    assert summary.whipsaw_rate == 1.0
    assert summary.mean_bars_held == 3.0
    assert summary.total_costs == pytest.approx(704.08336, rel=TOLERANCE)
    assert summary.cost_share_of_gross == pytest.approx(704.08336 / 23_979.16, rel=TOLERANCE)
    assert summary.rebalance_cost_share == pytest.approx(1.6064 / 704.08336, rel=TOLERANCE)
    assert summary.exposure == pytest.approx(3 / 9, rel=TOLERANCE)
