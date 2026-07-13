"""Golden-master tests for Step 3's cost bricks (D1, D2), one scenario per brick.

Hand-worked arithmetic lives in test_cost_bricks_golden.hand.txt, next to this file,
per D39. Tolerance follows D47 (money reconciliation, default 1e-6).
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity

TOLERANCE = 1e-6  # D47
AAPL = Equity(symbol="AAPL")


def test_flat_commission_ignores_inputs_returns_flat_amount():
    commission = FlatCommission(amount=1.50)
    assert commission.cost(AAPL, quantity=500, price=100.0) == 1.50


def test_percent_of_notional_spread_golden():
    spread = PercentOfNotionalSpread(bps=5.0)
    assert spread.cost(AAPL, quantity=500, price=100.0) == pytest.approx(25.0, rel=TOLERANCE)


def test_flat_rate_carry_golden():
    carry = FlatRateCarry(annual_rate=0.06)
    prev = datetime(2026, 7, 10, 16, 0)  # Friday
    curr = datetime(2026, 7, 13, 16, 0)  # Monday
    accrued = carry.cost(base_amount=50_000, prev_timestamp=prev, curr_timestamp=curr)
    assert accrued == pytest.approx(24.657534246575342, rel=TOLERANCE)


def test_combined_trade_stack_golden():
    stack = CostStack(trade_bricks=(FlatCommission(1.50), PercentOfNotionalSpread(5.0)))
    total = stack.trade_cost(AAPL, quantity=500, price=100.0)
    assert total == pytest.approx(26.50, rel=TOLERANCE)
