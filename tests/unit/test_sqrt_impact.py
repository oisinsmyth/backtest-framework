"""Unit tests for SqrtImpact.

Doubling quantity multiplies the impact fraction (the per-dollar price concession,
`cost ∝ σ√(Q/ADV)`) by √2. Total dollar cost is fraction × trade notional, so it scales as
Q^1.5 (2√2 on doubling), as in the standard square-root impact model. Both scalings are
tested.
"""

import math

import pytest

from backtest_framework.costs.equity_bricks import ImpactParams, SqrtImpact
from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.option_stub import OptionStub

TOLERANCE = 1e-9
AAPL = Equity(symbol="AAPL")

BRICK = SqrtImpact(params_by_symbol={"AAPL": ImpactParams(sigma_daily=0.02, adv_shares=1_000_000)})


def test_impact_fraction_hand_value():
    # 0.02 * sqrt(10,000 / 1,000,000) = 0.02 * 0.1 = 0.002 (20 bps)
    assert BRICK.impact_fraction(AAPL, quantity=10_000) == pytest.approx(0.002, rel=TOLERANCE)


def test_doubling_quantity_scales_impact_fraction_by_sqrt2():
    single = BRICK.impact_fraction(AAPL, quantity=10_000)
    double = BRICK.impact_fraction(AAPL, quantity=20_000)
    assert double / single == pytest.approx(math.sqrt(2), rel=TOLERANCE)


def test_doubling_quantity_scales_dollar_cost_by_two_sqrt2():
    # fraction scales by sqrt(2), notional by 2 -> dollars by 2*sqrt(2).
    single = BRICK.cost(AAPL, quantity=10_000, price=50.0)
    double = BRICK.cost(AAPL, quantity=20_000, price=50.0)
    assert single == pytest.approx(1_000.0, rel=TOLERANCE)  # 0.002 * 500,000
    assert double / single == pytest.approx(2 * math.sqrt(2), rel=TOLERANCE)


def test_cost_is_sign_independent():
    assert BRICK.cost(AAPL, quantity=-10_000, price=50.0) == BRICK.cost(AAPL, quantity=10_000, price=50.0)


def test_zero_quantity_costs_nothing():
    assert BRICK.cost(AAPL, quantity=0, price=50.0) == 0.0


# --- Invalid inputs raise instead of returning zero cost ------------------------------


def test_zero_adv_raises_at_construction():
    with pytest.raises(ValueError, match="adv_shares"):
        SqrtImpact(params_by_symbol={"AAPL": ImpactParams(sigma_daily=0.02, adv_shares=0.0)})


def test_negative_adv_raises_at_construction():
    with pytest.raises(ValueError, match="adv_shares"):
        SqrtImpact(params_by_symbol={"AAPL": ImpactParams(sigma_daily=0.02, adv_shares=-5.0)})


def test_zero_sigma_raises_at_construction():
    # sigma=0 would make every cost from the brick zero, so it is rejected like ADV=0.
    with pytest.raises(ValueError, match="sigma_daily"):
        SqrtImpact(params_by_symbol={"AAPL": ImpactParams(sigma_daily=0.0, adv_shares=1_000_000)})


def test_unknown_symbol_raises_naming_it():
    xle = Equity(symbol="XLE")
    with pytest.raises(ValueError, match="XLE") as excinfo:
        BRICK.cost(xle, quantity=100, price=80.0)
    assert "AAPL" in str(excinfo.value)  # the message lists the known symbols


def test_instrument_without_symbol_attribute_raises():
    option = OptionStub(underlying_symbol="AAPL", strike=150.0, expiry="2026-09-18", option_type="call")
    with pytest.raises(ValueError, match="symbol"):
        BRICK.cost(option, quantity=1, price=3.50)
