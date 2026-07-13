"""Unit tests for RiskMonitor's pre-trade gate (D30), per VERIFICATION_SCHEME.md Step 4.

The per-bar drift scenario (the "I" gate) lives in
tests/integration/test_risk_monitor_drift.py.
"""

from backtest_framework.engine.risk import RiskLimits, RiskMonitor, gross_exposure
from backtest_framework.instruments.equity import Equity

AAPL = Equity(symbol="AAPL")
INSTRUMENTS = {"AAPL": AAPL}


def test_gross_exposure_sums_absolute_notional_across_positions():
    positions = {"AAPL": 100.0}
    prices = {"AAPL": 150.0}
    assert gross_exposure(positions, prices, INSTRUMENTS) == 15_000.0


def test_gross_exposure_counts_short_notional_too():
    positions = {"AAPL": -100.0}  # a short
    prices = {"AAPL": 150.0}
    assert gross_exposure(positions, prices, INSTRUMENTS) == 15_000.0  # abs, not signed


def test_pretrade_check_rejects_order_that_would_breach_limit():
    monitor = RiskMonitor(RiskLimits(max_gross_exposure=150_000.0))
    violation = monitor.pretrade_check(
        positions={},
        prices={"AAPL": 100.0},
        instruments=INSTRUMENTS,
        proposed_instrument_id="AAPL",
        proposed_delta_qty=2000.0,  # 2000 * 100 = 200,000 > 150,000 limit
    )
    assert violation is not None
    assert violation.rule == "max_gross_exposure"
    assert violation.observed == 200_000.0


def test_pretrade_check_allows_order_within_limit():
    monitor = RiskMonitor(RiskLimits(max_gross_exposure=150_000.0))
    violation = monitor.pretrade_check(
        positions={},
        prices={"AAPL": 100.0},
        instruments=INSTRUMENTS,
        proposed_instrument_id="AAPL",
        proposed_delta_qty=500.0,  # 500 * 100 = 50,000 <= 150,000
    )
    assert violation is None


def test_pretrade_check_accounts_for_existing_position():
    monitor = RiskMonitor(RiskLimits(max_gross_exposure=150_000.0))
    # Already holding 1000 shares (100,000 notional); adding 600 more pushes to
    # 1600 * 100 = 160,000 > 150,000.
    violation = monitor.pretrade_check(
        positions={"AAPL": 1000.0},
        prices={"AAPL": 100.0},
        instruments=INSTRUMENTS,
        proposed_instrument_id="AAPL",
        proposed_delta_qty=600.0,
    )
    assert violation is not None
    assert violation.observed == 160_000.0
