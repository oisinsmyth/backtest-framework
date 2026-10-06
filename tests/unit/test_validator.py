"""Tests for the data validator.

The validator separates hard violations from warnings, uses thresholds calibrated against
observed real data, and accounts for splits so that a reverse-split jump in an as-traded
series is not quarantined.
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
    # XOP 2018-10-24: close < low by 1.2e-16 relative, within the 1e-9 tolerance.
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


def test_a_zero_close_is_quarantined_rather_than_raising():
    """A 0.0 close is flagged as a hard violation without raising.

    A zero close is a common scraper failure. The next bar does not divide by it as
    `prev_close`, which would raise ZeroDivisionError instead of returning a result that
    quarantines the data.
    """
    result = validate({"A": _series([10.0, 0.0, 10.0])})

    assert not result.passed
    assert [v.check for v in result.hard_violations] == ["non_positive_price"]
    # No unexplained_move is computed from the bad previous close.
    assert not any(v.check == "unexplained_move" for v in result.violations)


def test_a_negative_close_does_not_fabricate_a_move_on_the_next_bar():
    """A negative close does not produce a spurious move on the next bar.

    Dividing by -5.0 does not raise but would produce a -21% move and a second
    `unexplained_move` hard violation. `not passed` alone would not detect that, so the full
    list of hard violations is checked.
    """
    result = validate({"A": _series([100.0, -5.0, 100.0])})

    assert not result.passed
    assert [v.check for v in result.hard_violations] == ["non_positive_price"]


def test_genuine_crash_day_is_a_warning_not_quarantine():
    # Calibration point: XOP 2020-03-09 was a real -37% simple move. An unexplained move
    # of 25-60% is a warning, so a real crash does not quarantine the dataset.
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
    # A provider-frame (split-adjusted) series is already continuous across the ex-date
    # (XOP: 32.12 -> 32.01). The split adjustment must not turn that small move into a
    # -75% move.
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


def test_duplicate_timestamps_are_a_hard_violation():
    # Alignment would collapse duplicates without reporting them, so the validator
    # quarantines them before they reach the engine.
    from datetime import datetime

    from backtest_framework.data.bars import TimestampedBar
    from backtest_framework.simulator.fills import Bar

    ts = datetime(2026, 7, 13)
    bar = Bar(open=10.0, high=10.0, low=10.0, close=10.0)
    result = validate({"DUP": [TimestampedBar(ts, bar), TimestampedBar(ts, bar)]})

    assert not result.passed
    assert any(v.check == "duplicate_timestamp" and v.hard for v in result.violations)
