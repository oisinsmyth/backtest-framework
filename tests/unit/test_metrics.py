"""Step 9 metric gates (D37, D49, D80)."""

import math

import numpy as np
import pytest

from backtest_framework.analytics.metrics import max_drawdown, realised_beta, sharpe, sortino

TOLERANCE = 1e-9


def test_sharpe_with_rf_4pct_on_flat_returns_is_negative():
    # THE D49 gate: a flat (constant-zero) return series at rf=4% must come out
    # negative — this is what catches a silent rf=0 shortcut. Zero variance with
    # negative excess mean -> -inf by the stated convention (D80).
    result = sharpe([0.0] * 252, rf_annual=0.04, periods_per_year=252)
    assert result < 0
    assert result == -math.inf


def test_sharpe_requires_rf_and_periods_positionally():
    # No defaults, by design (D49/D80) — calling without them is a TypeError.
    with pytest.raises(TypeError):
        sharpe([0.01, -0.02, 0.005])  # type: ignore[call-arg]


def test_sharpe_hand_value():
    # mean=0.001, sample std known; rf=0 -> excess == returns.
    r = [0.01, -0.008, 0.002, 0.0, 0.001]
    mu = np.mean(r)
    sd = np.std(r, ddof=1)
    expected = mu / sd * math.sqrt(252)
    assert sharpe(r, rf_annual=0.0, periods_per_year=252) == pytest.approx(expected, rel=TOLERANCE)


def test_sortino_flat_series_with_rf_is_negative_and_finite():
    # Flat series at rf=4%: every excess return is -rf_period (a constant loss), so
    # downside deviation is positive and sortino is negative but finite.
    result = sortino([0.0] * 252, rf_annual=0.04, periods_per_year=252)
    assert result < 0
    assert math.isfinite(result)


def test_sortino_no_downside_is_positive_infinity():
    assert sortino([0.01, 0.02, 0.015], rf_annual=0.0, periods_per_year=252) == math.inf


def test_beta_of_series_vs_itself_is_one():
    rng = np.random.default_rng(11)
    spy = rng.normal(0.0003, 0.011, 500)
    assert realised_beta(spy, spy) == pytest.approx(1.0, rel=TOLERANCE)  # D37 gate


def test_beta_of_constant_cash_series_is_zero():
    rng = np.random.default_rng(11)
    spy = rng.normal(0.0003, 0.011, 500)
    cash = [0.0001] * 500  # constant per-period return
    assert realised_beta(cash, spy) == pytest.approx(0.0, abs=1e-12)  # D37 gate


def test_beta_against_zero_variance_benchmark_fails_loudly():
    with pytest.raises(ValueError, match="zero variance"):
        realised_beta([0.01, -0.01, 0.02], [0.001, 0.001, 0.001])


def test_beta_length_mismatch_fails_loudly():
    with pytest.raises(ValueError, match="length mismatch"):
        realised_beta([0.01, -0.01], [0.001])


def test_max_drawdown_relocated_intact():
    curve = [(None, 100.0), (None, 110.0), (None, 99.0), (None, 105.0)]
    assert max_drawdown(curve) == pytest.approx(0.1, rel=TOLERANCE)
