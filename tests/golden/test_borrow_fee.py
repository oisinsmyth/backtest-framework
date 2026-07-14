"""Golden tests for BorrowFee (D71): shorts pay, longs free.

Hand arithmetic in test_borrow_fee.hand.txt, per D39.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.equity_bricks import BorrowFee

TOLERANCE = 1e-6  # D47
FRIDAY = datetime(2026, 7, 10, 16, 0)
MONDAY = datetime(2026, 7, 13, 16, 0)

BRICK = BorrowFee(annual_rate=0.0025)


def test_short_leg_pays_borrow_over_the_weekend():
    fee = BRICK.cost(base_amount=-100_000.0, prev_timestamp=FRIDAY, curr_timestamp=MONDAY)
    assert fee == pytest.approx(2.0547945205479454, rel=TOLERANCE)


def test_long_leg_pays_nothing():
    assert BRICK.cost(base_amount=100_000.0, prev_timestamp=FRIDAY, curr_timestamp=MONDAY) == 0.0


def test_flat_pays_nothing():
    assert BRICK.cost(base_amount=0.0, prev_timestamp=FRIDAY, curr_timestamp=MONDAY) == 0.0
