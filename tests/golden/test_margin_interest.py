"""G-gate for MarginInterest (D5, D67), brick level. Hand arithmetic in
test_margin_interest.hand.txt; the engine-wiring half of the gate lives in
tests/integration/test_margin_interest_in_backtest.py.

The brick itself only knows the accrual math — the max(gross − capital, 0) base is
the CALLER's contract (the engine's portfolio-carry step, D67). These tests exercise
both: the brick against the golden weekend number, and the base formula the engine
applies, so the only-when-positive branch is pinned at the same level the arithmetic
is.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.equity_bricks import MarginInterest
from backtest_framework.costs.stack import CostStack

TOLERANCE = 1e-6  # D47
FRIDAY = datetime(2026, 7, 10, 16, 0)
MONDAY = datetime(2026, 7, 13, 16, 0)

BRICK = MarginInterest(annual_rate=0.06)


def test_weekend_accrual_on_borrowed_portion_matches_d33_golden_arithmetic():
    # Case 1: 200% gross on 100k capital -> base 100k; Fri->Mon = 3 calendar days.
    base = max(200_000.0 - 100_000.0, 0.0)
    accrued = BRICK.cost(base, FRIDAY, MONDAY)
    assert accrued == pytest.approx(49.315068493150684, rel=TOLERANCE)


def test_underleveraged_book_is_charged_nothing():
    # Case 2: gross 80k < capital 100k -> base clamps to 0, not a negative rebate.
    base = max(80_000.0 - 100_000.0, 0.0)
    assert base == 0.0
    assert BRICK.cost(base, FRIDAY, MONDAY) == 0.0


def test_gross_exactly_at_capital_is_charged_nothing():
    # Case 3: boundary.
    base = max(100_000.0 - 100_000.0, 0.0)
    assert BRICK.cost(base, FRIDAY, MONDAY) == 0.0


def test_portfolio_carry_slot_sums_bricks_and_defaults_empty():
    empty = CostStack()
    assert empty.portfolio_carry_cost(100_000.0, FRIDAY, MONDAY) == 0.0

    stack = CostStack(portfolio_carry_bricks=(BRICK, MarginInterest(annual_rate=0.01)))
    total = stack.portfolio_carry_cost(100_000.0, FRIDAY, MONDAY)
    manual = BRICK.cost(100_000.0, FRIDAY, MONDAY) + MarginInterest(0.01).cost(100_000.0, FRIDAY, MONDAY)
    assert total == pytest.approx(manual, rel=TOLERANCE)
