"""Unit tests for PortfolioState (engine/portfolio.py)."""

from backtest_framework.engine.portfolio import PortfolioState
from backtest_framework.instruments.equity import Equity

AAPL = Equity(symbol="AAPL")
INSTRUMENTS = {"AAPL": AAPL}


def test_apply_fill_buy_reduces_cash_and_increases_position():
    portfolio = PortfolioState(cash=100_000.0)
    portfolio.apply_fill("AAPL", delta_qty=500.0, price=100.0, trade_cost=26.0)

    assert portfolio.cash == 100_000.0 - 50_000.0 - 26.0
    assert portfolio.positions["AAPL"] == 500.0


def test_apply_fill_sell_increases_cash_and_decreases_position():
    portfolio = PortfolioState(cash=50_000.0, positions={"AAPL": 500.0})
    portfolio.apply_fill("AAPL", delta_qty=-500.0, price=100.0, trade_cost=26.0)

    assert portfolio.cash == 50_000.0 + 50_000.0 - 26.0
    assert portfolio.positions["AAPL"] == 0.0


def test_accrue_carry_reduces_cash_only():
    portfolio = PortfolioState(cash=50_000.0, positions={"AAPL": 500.0})
    portfolio.accrue_carry(24.657534246575342)

    assert portfolio.cash == 50_000.0 - 24.657534246575342
    assert portfolio.positions["AAPL"] == 500.0  # unaffected


def test_nav_is_cash_plus_positions_value():
    portfolio = PortfolioState(cash=49_974.0, positions={"AAPL": 500.0})
    nav = portfolio.nav(prices={"AAPL": 100.0}, instruments=INSTRUMENTS)
    assert nav == 49_974.0 + 50_000.0


def test_nav_with_short_position_subtracts_short_notional():
    # notional() is signed: a short (-100 shares) contributes -100*50 = -5000 here,
    # giving NAV = cash + longs - |shorts| (D43) without special-casing shorts.
    portfolio = PortfolioState(cash=10_000.0, positions={"AAPL": -100.0})
    nav = portfolio.nav(prices={"AAPL": 50.0}, instruments=INSTRUMENTS)
    assert nav == 10_000.0 - 5_000.0


def test_nav_ignores_zero_quantity_positions():
    portfolio = PortfolioState(cash=100_000.0, positions={"AAPL": 0.0})
    nav = portfolio.nav(prices={"AAPL": 100.0}, instruments=INSTRUMENTS)
    assert nav == 100_000.0
