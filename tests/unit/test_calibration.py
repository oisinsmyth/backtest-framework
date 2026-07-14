"""Unit tests for automated impact calibration (D66, D88)."""

import math
from datetime import datetime, timedelta

import pytest

from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.simulator.fills import Bar


def _series(closes):
    start = datetime(2026, 1, 5)
    return [
        TimestampedBar(start + timedelta(days=i), Bar(open=c, high=c, low=c, close=c))
        for i, c in enumerate(closes)
    ]


def test_sigma_and_adv_hand_values():
    closes = [100.0, 102.0, 100.0, 103.0]
    returns = [math.log(b / a) for a, b in zip(closes, closes[1:])]
    import statistics

    params = calibrate_impact_params(
        {"A": _series(closes)}, {"A": [1e6, 2e6, 1.5e6, 1.5e6]}
    )["A"]

    assert params.sigma_daily == pytest.approx(statistics.stdev(returns), rel=1e-12)
    assert params.adv_shares == pytest.approx(1.5e6, rel=1e-12)


def test_nan_volumes_are_skipped_not_poisoning_the_mean():
    params = calibrate_impact_params(
        {"A": _series([100.0, 101.0, 100.5, 102.0])},
        {"A": [1e6, float("nan"), 2e6, float("nan")]},
    )["A"]
    assert params.adv_shares == pytest.approx(1.5e6, rel=1e-12)


def test_missing_volume_series_fails_loudly():
    with pytest.raises(ValueError, match="no volume series"):
        calibrate_impact_params({"A": _series([100.0, 101.0, 102.0])}, {})


def test_zero_volatility_fails_loudly():
    with pytest.raises(ValueError, match="zero return volatility"):
        calibrate_impact_params({"A": _series([100.0, 100.0, 100.0])}, {"A": [1e6] * 3})


def test_too_short_series_fails_loudly():
    with pytest.raises(ValueError, match="at least 3 bars"):
        calibrate_impact_params({"A": _series([100.0, 101.0])}, {"A": [1e6, 1e6]})
