"""THE GOLDEN MASTER (D39, D77): the whole simulator against an independently
hand-computed 5-bar short-side scenario — every fill, every commission, every carry
accrual, the dividend debit, cash and NAV per bar, asserted line by line.

Ground truth in test_the_golden_master.hand.txt, produced by a standalone calculator
that never imports this codebase. If this test and the production engine ever
disagree, one of them is wrong about what a backtest IS — that argument happens here,
not at bar 3,000 of a research run.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47

THU, FRI = datetime(2026, 1, 8, 16), datetime(2026, 1, 9, 16)
MON, TUE, WED = datetime(2026, 1, 12, 16), datetime(2026, 1, 13, 16), datetime(2026, 1, 14, 16)


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


@pytest.fixture(scope="module")
def result():
    bars = {
        "TEST": [
            TimestampedBar(THU, _bar(100.0)),
            TimestampedBar(FRI, _bar(98.0)),
            TimestampedBar(MON, _bar(101.0)),
            TimestampedBar(TUE, _bar(99.0)),
            TimestampedBar(WED, _bar(99.0)),
        ]
    }
    stack = CostStack(
        trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=5.0)),
        carry_bricks=(BorrowFee(annual_rate=0.02),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol={"TEST": ((MON, 0.50),)}),),
    )
    strategy = ScheduledWeightStrategy(
        strategy_id="s", weights_by_instrument={"TEST": [-1.2, -1.2, -1.2, 0.0, 0.0]}
    )
    return run_backtest(
        bars_by_instrument=bars,
        instruments={"TEST": Equity(symbol="TEST")},
        strategies=[strategy],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )


def test_every_fill_line_by_line(result):
    expected = [
        (THU, "TEST", -1200.0, 100.0, 66.0),
        (FRI, "TEST", -53.0, 98.0, 3.597),  # the $1 IBKR minimum fires here
        (MON, "TEST", 90.0, 101.0, 5.545),
        (TUE, "TEST", 1163.0, 99.0, 63.3835),
    ]
    assert len(result.fills) == len(expected)
    for actual, exp in zip(result.fills, expected):
        ts, instrument_id, qty, price, cost = actual
        assert (ts, instrument_id) == (exp[0], exp[1])
        assert qty == exp[2]  # share counts are exact integers
        assert price == exp[3]
        assert cost == pytest.approx(exp[4], rel=TOLERANCE)


def test_cash_curve_line_by_line(result):
    expected = [
        (THU, 219_934.0),
        (FRI, 225_115.4496849315),
        (MON, 215_358.7978929953),  # includes the -626.50 dividend debit on the short
        (TUE, 100_149.6537022380),
        (WED, 100_149.6537022380),
    ]
    assert [ts for ts, _ in result.cash_curve] == [ts for ts, _ in expected]
    for (_, actual), (_, exp) in zip(result.cash_curve, expected):
        assert actual == pytest.approx(exp, rel=TOLERANCE)


def test_equity_curve_line_by_line(result):
    expected = [
        (THU, 99_934.0),
        (FRI, 102_321.4496849315),
        (MON, 97_895.7978929953),
        (TUE, 100_149.6537022380),
        (WED, 100_149.6537022380),
    ]
    for (_, actual), (_, exp) in zip(result.equity_curve, expected):
        assert actual == pytest.approx(exp, rel=TOLERANCE)


def test_final_state(result):
    assert result.final_positions.get("TEST", 0.0) == 0.0
    assert result.final_nav == pytest.approx(100_149.6537022380, rel=TOLERANCE)
    # Cross-check independent of the bar-by-bar bookkeeping: final NAV - start ==
    # short price P&L - all frictions - dividend debit. Price P&L on the varying
    # position: computed in the hand file's trace; the identity that MUST hold here
    # is NAV == cash (flat book).
    assert result.final_cash == pytest.approx(result.final_nav, rel=TOLERANCE)
