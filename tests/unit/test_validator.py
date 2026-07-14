"""D26 gate: the sanity gate flags what it should — hard violations vs warnings
(D74), with thresholds calibrated against observed genuine data, and split-awareness
so a real reverse-split jump in an as-traded series isn't quarantined.
"""

from datetime import datetime, timedelta

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.data.validator import validate
from backtest_framework.simulator.fills import Bar


def _series(closes: list[float]) -> list[TimestampedBar]:
    start = datetime(2026, 1, 1)
    return [
        TimestampedBar(start + timedelta(days=i), Bar(open=c, high=c * 1.01, low=c * 0.99, close=c))
        for i, c in enumerate(closes)
    ]


def test_clean_series_passes():
    result = validate({"A": _series([100.0, 101.0, 99.5, 100.5])})
    assert result.passed
    assert result.violations == ()


def test_ohlc_inconsistency_is_hard():
    series = _series([100.0, 101.0])
    series[1] = TimestampedBar(series[1].timestamp, Bar(open=101.0, high=100.0, low=99.0, close=101.0))
    result = validate({"A": series})
    assert not result.passed
    assert result.hard_violations[0].check == "ohlc_inconsistent"


def test_observed_epsilon_artifact_passes_tolerance():
    # XOP 2018-10-24: close < low by 1.2e-16 relative — within the 1e-9 tolerance.
    high = 128.9409511386912
    low = 119.8700637817383
    close = 119.87006378173828  # < low, by float noise
    series = [TimestampedBar(datetime(2026, 1, 1), Bar(open=125.0, high=high, low=low, close=close))]
    assert validate({"A": series}).passed


def test_non_positive_price_is_hard():
    series = _series([100.0])
    series[0] = TimestampedBar(series[0].timestamp, Bar(open=100.0, high=101.0, low=-1.0, close=100.0))
    result = validate({"A": series})
    assert not result.passed
    assert result.hard_violations[0].check == "non_positive_price"


def test_genuine_crash_day_is_a_warning_not_quarantine():
    # Calibration anchor (D74): XOP 2020-03-09 was a REAL -37% simple move. 25-60%
    # unexplained => warning; the dataset must not be quarantined for a real crash.
    result = validate({"A": _series([100.0, 63.0, 61.0])})
    assert result.passed  # no hard violations
    warnings = result.warnings
    assert warnings and warnings[0].check == "unexplained_move"


def test_extreme_unexplained_move_is_hard():
    result = validate({"A": _series([100.0, 30.0, 31.0])})  # -70%, beyond anything observed
    assert not result.passed
    assert result.hard_violations[0].check == "unexplained_move"


def test_split_explains_the_jump_on_its_ex_date():
    # As-traded series through a 1-for-4 reverse split: ~8 -> ~32 (a +300% raw move).
    start = datetime(2026, 1, 1)
    series = [
        TimestampedBar(start, Bar(open=8.0, high=8.1, low=7.9, close=8.03)),
        TimestampedBar(start + timedelta(days=1), Bar(open=32.0, high=32.5, low=31.5, close=32.01)),
    ]
    actions = CorporateActions(splits_by_symbol={"A": [(start + timedelta(days=1), 0.25)]})

    result = validate({"A": series}, actions)

    assert result.passed
    assert not any(v.check == "unexplained_move" for v in result.violations)


def test_already_adjusted_series_is_not_flagged_on_the_split_date():
    # Regression for the bug the gate caught on our own data (D74): a PROVIDER-frame
    # series is already continuous across the ex-date (XOP: 32.12 -> 32.01). The
    # frame-robust check must not "correct" that smooth move into a fabricated -75%.
    start = datetime(2026, 1, 1)
    series = [
        TimestampedBar(start, Bar(open=32.0, high=32.5, low=31.5, close=32.12)),
        TimestampedBar(start + timedelta(days=1), Bar(open=32.0, high=32.5, low=31.5, close=32.01)),
    ]
    actions = CorporateActions(splits_by_symbol={"A": [(start + timedelta(days=1), 0.25)]})

    result = validate({"A": series}, actions)

    assert result.passed
    assert not any(v.check == "unexplained_move" for v in result.violations)


def test_volume_anomalies_are_warnings():
    closes = [100.0 + 0.1 * i for i in range(25)]
    volumes = [1e6] * 25
    volumes[22] = 0.0  # zero-volume day
    volumes[24] = 2e7  # 20x median spike

    result = validate({"A": _series(closes)}, volumes_by_symbol={"A": volumes})

    assert result.passed  # warnings never quarantine
    checks = {v.check for v in result.warnings}
    assert checks == {"zero_volume", "volume_spike"}
