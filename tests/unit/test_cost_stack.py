"""Unit tests for CostStack (D1, D2), per VERIFICATION_SCHEME.md Step 3.

Per-brick golden-master hand arithmetic lives in test_cost_bricks_golden.py /
test_cost_bricks_golden.hand.txt. This file covers the stack-composition behaviour:
empty-stack-is-zero-cost, total-equals-sum-of-bricks, and ordering invariance.
"""

from datetime import datetime

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity

AAPL = Equity(symbol="AAPL")
PREV, CURR = datetime(2026, 7, 10, 16, 0), datetime(2026, 7, 13, 16, 0)


def test_empty_stack_trade_cost_is_zero():
    stack = CostStack()
    assert stack.trade_cost(AAPL, quantity=100, price=150.0) == 0.0


def test_empty_stack_carry_cost_is_zero():
    stack = CostStack()
    assert stack.carry_cost(base_amount=50_000, prev_timestamp=PREV, curr_timestamp=CURR) == 0.0


def test_stack_trade_total_equals_sum_of_individual_bricks():
    commission = FlatCommission(amount=1.0)
    spread = PercentOfNotionalSpread(bps=5.0)
    stack = CostStack(trade_bricks=(commission, spread))

    total = stack.trade_cost(AAPL, quantity=500, price=100.0)
    manual_sum = commission.cost(AAPL, 500, 100.0) + spread.cost(AAPL, 500, 100.0)
    assert total == manual_sum


def test_stack_carry_total_equals_sum_of_individual_bricks():
    carry_a = FlatRateCarry(annual_rate=0.06)
    carry_b = FlatRateCarry(annual_rate=0.01)  # e.g. a second, independent carry layer
    stack = CostStack(carry_bricks=(carry_a, carry_b))

    total = stack.carry_cost(base_amount=50_000, prev_timestamp=PREV, curr_timestamp=CURR)
    manual_sum = carry_a.cost(50_000, PREV, CURR) + carry_b.cost(50_000, PREV, CURR)
    assert total == manual_sum


def test_trade_brick_ordering_has_no_effect_on_total():
    # Every trade brick computes its cost independently from (instrument, quantity,
    # price) alone — never from another brick's output — so summation is commutative
    # by construction. Asserted here rather than left as an assumption.
    commission = FlatCommission(amount=1.0)
    spread = PercentOfNotionalSpread(bps=5.0)

    forward = CostStack(trade_bricks=(commission, spread))
    reversed_ = CostStack(trade_bricks=(spread, commission))

    assert forward.trade_cost(AAPL, 500, 100.0) == reversed_.trade_cost(AAPL, 500, 100.0)


def test_carry_brick_ordering_has_no_effect_on_total():
    carry_a = FlatRateCarry(annual_rate=0.06)
    carry_b = FlatRateCarry(annual_rate=0.01)

    forward = CostStack(carry_bricks=(carry_a, carry_b))
    reversed_ = CostStack(carry_bricks=(carry_b, carry_a))

    assert forward.carry_cost(50_000, PREV, CURR) == reversed_.carry_cost(50_000, PREV, CURR)
