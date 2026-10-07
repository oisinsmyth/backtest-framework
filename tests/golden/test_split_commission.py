"""Golden test: commission on the pre-split XOP bar on as-traded vs adjusted prices.

The difference is nonzero and equals the hand arithmetic in test_split_commission.hand.txt.
The bar is XOP's last close before its 1-for-4 reverse split of 2020-03-30, $32.12 in the
split-adjusted frame.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.equity_bricks import IBKRCommission
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import as_traded_from_adjusted
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # relative tolerance for golden comparisons

XOP = Equity(symbol="XOP")
PRE_SPLIT_DAY = datetime(2020, 3, 27)
SPLITS = [(datetime(2020, 3, 30), 0.25)]  # 1-for-4 reverse split


def _closes():
    bars = [TimestampedBar(PRE_SPLIT_DAY, Bar(open=32.12, high=32.12, low=32.12, close=32.12))]
    true_bars = as_traded_from_adjusted(bars, SPLITS)

    adjusted_close = next(tb.bar.close for tb in bars if tb.timestamp == PRE_SPLIT_DAY)
    true_close = next(tb.bar.close for tb in true_bars if tb.timestamp == PRE_SPLIT_DAY)
    return adjusted_close, true_close


def test_pre_split_bar_frames_differ_by_the_split_ratio():
    adjusted_close, true_close = _closes()
    assert adjusted_close == pytest.approx(32.12, abs=0.01)
    assert true_close == pytest.approx(adjusted_close * 0.25, rel=TOLERANCE)


def test_commission_on_true_vs_adjusted_notional_differs_by_hand_amount():
    adjusted_close, true_close = _closes()
    brick = IBKRCommission()
    notional = 1_000 * adjusted_close  # $32,120 deployed either way

    true_shares = notional / true_close  # 4,000 real shares
    adjusted_shares = notional / adjusted_close  # 1,000 phantom shares

    commission_true = brick.cost(XOP, quantity=true_shares, price=true_close)
    commission_adjusted = brick.cost(XOP, quantity=adjusted_shares, price=adjusted_close)

    assert commission_true == pytest.approx(20.00, rel=TOLERANCE)
    assert commission_adjusted == pytest.approx(5.00, rel=TOLERANCE)
    assert commission_true - commission_adjusted == pytest.approx(15.00, rel=TOLERANCE)  # nonzero, exact
