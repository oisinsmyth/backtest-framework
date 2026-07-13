"""Unit tests for the Instrument abstraction (D12, D16), per VERIFICATION_SCHEME.md Step 3."""

import pytest

from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.option_stub import OptionStub


def test_equity_notional_is_quantity_times_price():
    equity = Equity(symbol="AAPL")
    assert equity.notional(quantity=100, price=150.0) == 15_000.0


def test_equity_tradeable_quantity_whole_shares_rounds_to_int():
    equity = Equity(symbol="AAPL")  # quantity_precision=None -> whole shares only
    assert equity.tradeable_quantity(99.6) == 100.0
    assert equity.tradeable_quantity(99.4) == 99.0


def test_equity_tradeable_quantity_fractional_shares_rounds_to_precision():
    equity = Equity(symbol="AAPL", quantity_precision=4)
    assert equity.tradeable_quantity(12.345678) == 12.3457


def test_equity_tradeable_quantity_eight_decimal_crypto_precision_stub():
    # Proves the rounding mechanism generalizes to crypto-like precision; this is not a
    # real crypto instrument (no funding carry component, no 365-day calendar override —
    # that's D14/Step 10's job).
    equity = Equity(symbol="BTC-STUB", quantity_precision=8)
    assert equity.tradeable_quantity(0.123456789) == 0.12345679


def test_equity_carry_components_lists_applicable_types():
    equity = Equity(symbol="AAPL")
    assert equity.carry_components() == ("margin_interest", "borrow", "dividend")


def test_equity_margin_requirement_is_full_notional_stand_in():
    equity = Equity(symbol="AAPL")
    assert equity.margin_requirement(quantity=100, price=150.0) == 15_000.0


# --- Option stub (D16, D48) -------------------------------------------------------


def _sample_option() -> OptionStub:
    return OptionStub(underlying_symbol="AAPL", strike=150.0, expiry="2026-09-18", option_type="call")


def test_option_stub_notional_multiplier_math_correct():
    option = _sample_option()
    # 2 contracts, $3.50 premium/share, 100 shares/contract -> 2 * 3.50 * 100
    assert option.notional(quantity=2, price=3.50) == 700.0


def test_option_stub_tradeable_quantity_whole_contracts_only():
    option = _sample_option()
    assert option.tradeable_quantity(2.6) == 3.0


def test_option_stub_carry_components_is_correctly_empty_not_unimplemented():
    option = _sample_option()
    assert option.carry_components() == ()


def test_option_stub_margin_requirement_raises_pointing_at_design_doc():
    option = _sample_option()
    with pytest.raises(NotImplementedError, match="docs/options_extension.md"):
        option.margin_requirement(quantity=2, price=3.50)
