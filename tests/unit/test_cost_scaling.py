"""Unit tests for scaled_cost_stack (D8, D68)."""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import MarginInterest
from backtest_framework.costs.scaling import scaled_cost_stack
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity

AAPL = Equity(symbol="AAPL")
FRIDAY, MONDAY = datetime(2026, 7, 10, 16, 0), datetime(2026, 7, 13, 16, 0)

STACK = CostStack(
    trade_bricks=(FlatCommission(amount=1.00), PercentOfNotionalSpread(bps=5.0)),
    carry_bricks=(FlatRateCarry(annual_rate=0.06),),
    portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
)


@pytest.mark.parametrize("multiplier", [0.0, 0.5, 1.0, 2.0, 4.0])
def test_all_three_slots_scale_by_the_multiplier(multiplier):
    scaled = scaled_cost_stack(STACK, multiplier)

    assert scaled.trade_cost(AAPL, 500, 100.0) == pytest.approx(
        multiplier * STACK.trade_cost(AAPL, 500, 100.0)
    )
    assert scaled.carry_cost(50_000, FRIDAY, MONDAY) == pytest.approx(
        multiplier * STACK.carry_cost(50_000, FRIDAY, MONDAY)
    )
    assert scaled.portfolio_carry_cost(100_000, FRIDAY, MONDAY) == pytest.approx(
        multiplier * STACK.portfolio_carry_cost(100_000, FRIDAY, MONDAY)
    )


def test_zero_multiplier_zeroes_everything():
    scaled = scaled_cost_stack(STACK, 0.0)
    assert scaled.trade_cost(AAPL, 500, 100.0) == 0.0
    assert scaled.carry_cost(50_000, FRIDAY, MONDAY) == 0.0
    assert scaled.portfolio_carry_cost(100_000, FRIDAY, MONDAY) == 0.0


def test_one_multiplier_is_identity_on_outputs():
    scaled = scaled_cost_stack(STACK, 1.0)
    assert scaled.trade_cost(AAPL, 500, 100.0) == STACK.trade_cost(AAPL, 500, 100.0)


def test_brick_structure_is_preserved_not_collapsed():
    scaled = scaled_cost_stack(STACK, 2.0)
    assert len(scaled.trade_bricks) == len(STACK.trade_bricks)
    assert len(scaled.carry_bricks) == len(STACK.carry_bricks)
    assert len(scaled.portfolio_carry_bricks) == len(STACK.portfolio_carry_bricks)


def test_negative_multiplier_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        scaled_cost_stack(STACK, -1.0)
