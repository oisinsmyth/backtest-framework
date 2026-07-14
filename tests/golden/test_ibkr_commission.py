"""X-gate for IBKRCommission (D4, D65): the brick vs a ≥10-row worked table of the
published IBKR Fixed US-equity schedule.

The full worked table, regime labels, and the anchoring caveat (IBKR's pricing pages
403-block automated fetches; constants are the long-published schedule, manual
re-verification still owed) live in test_ibkr_commission.hand.txt, next to this file.
"""

import pytest

from backtest_framework.costs.equity_bricks import IBKRCommission
from backtest_framework.instruments.equity import Equity

TOLERANCE = 1e-6  # D47
AAPL = Equity(symbol="AAPL")
BRICK = IBKRCommission()  # defaults ARE the published schedule — that's the point


@pytest.mark.parametrize(
    ("shares", "price", "expected"),
    [
        (100, 50.00, 1.00),  # row 1: min floor
        (200, 50.00, 1.00),  # row 2: per-share == min exactly
        (1_000, 50.00, 5.00),  # row 3: per-share
        (10_000, 25.00, 50.00),  # row 4: per-share, large order
        (1_000, 0.30, 3.00),  # row 5: 1% cap (low-price stock)
        (10, 0.50, 0.05),  # row 6: cap OVERRIDES min
        (100, 2_000.00, 1.00),  # row 7: min floor on a high-price stock
        (1, 150.00, 1.00),  # row 8: single share
        (500, 1.00, 2.50),  # row 9: per-share on a $1 stock
        (500, 0.40, 2.00),  # row 10: 1% cap
        (200, 0.50, 1.00),  # row 11: per-share == min == cap, triple boundary
        (-1_000, 50.00, 5.00),  # row 12: sell side, sign-independent
        (2_000_000, 10.00, 10_000.00),  # row 13: jumbo order
    ],
)
def test_ibkr_commission_matches_published_schedule_table(shares, price, expected):
    assert BRICK.cost(AAPL, quantity=shares, price=price) == pytest.approx(expected, rel=TOLERANCE)


def test_zero_shares_costs_nothing():
    assert BRICK.cost(AAPL, quantity=0, price=50.00) == 0.0
