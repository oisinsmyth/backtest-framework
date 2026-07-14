"""D25 gate: cleaner given injected defects -> CleaningReport lists every change;
clean input -> empty report. Ruleset clean-v1 (D73): drop-and-report, never rewrite.
"""

from datetime import datetime, timedelta

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.cleaner import RULESET_VERSION, clean
from backtest_framework.simulator.fills import Bar


def _series(closes: list[float]) -> list[TimestampedBar]:
    start = datetime(2026, 1, 1)
    return [
        TimestampedBar(start + timedelta(days=i), Bar(open=c, high=c * 1.01, low=c * 0.99, close=c))
        for i, c in enumerate(closes)
    ]


def test_clean_input_produces_empty_report():
    bars = {"A": _series([100.0, 101.0, 102.0, 101.5])}
    cleaned, report = clean(bars)

    assert cleaned == bars
    assert report.changes == ()
    assert report.ruleset == RULESET_VERSION


def test_nan_close_dropped_and_reported():
    series = _series([100.0, 101.0, 102.0])
    series[1] = TimestampedBar(series[1].timestamp, Bar(open=101.0, high=102.0, low=100.0, close=float("nan")))

    cleaned, report = clean({"A": series})

    assert len(cleaned["A"]) == 2
    assert len(report.changes) == 1
    assert report.changes[0].rule == "non_finite_ohlc"
    assert report.changes[0].timestamp == series[1].timestamp


def test_low_above_high_dropped_and_reported():
    series = _series([100.0, 101.0, 102.0])
    series[1] = TimestampedBar(series[1].timestamp, Bar(open=101.0, high=100.0, low=103.0, close=101.0))

    cleaned, report = clean({"A": series})

    assert len(cleaned["A"]) == 2
    assert report.changes[0].rule == "low_above_high"


def test_epsilon_low_high_artifact_passes_untouched():
    # The observed XOP 2018-10-24 case: low > high by ~1e-16 relative - within
    # tolerance, NOT the cleaner's business (the validator's tolerance owns it).
    series = _series([100.0])
    high = 119.87006378173828
    series[0] = TimestampedBar(series[0].timestamp, Bar(open=119.0, high=high, low=high + 1e-14, close=119.5))

    cleaned, report = clean({"A": series})

    assert len(cleaned["A"]) == 1
    assert report.changes == ()


def test_zero_volume_day_dropped_and_reported():
    bars = {"A": _series([100.0, 101.0, 102.0])}
    volumes = {"A": [1e6, 0.0, 1.2e6]}

    cleaned, report = clean(bars, volumes)

    assert len(cleaned["A"]) == 2
    assert report.changes[0].rule == "non_positive_volume"


def test_spike_and_revert_dropped_but_permanent_move_kept():
    # 100 -> 150 (+50% spike) -> 101 (reverts): bad print, dropped.
    spiky = _series([100.0, 150.0, 101.0, 102.0])
    cleaned, report = clean({"A": spiky})
    assert len(cleaned["A"]) == 3
    assert report.changes[0].rule == "spike_and_revert"

    # 100 -> 55 (-45%) -> 54 (sticks): a real crash, kept - permanence discriminates (D73).
    crash = _series([100.0, 55.0, 54.0, 56.0])
    cleaned, report = clean({"A": crash})
    assert len(cleaned["A"]) == 4
    assert report.changes == ()


def test_every_injected_defect_is_individually_reported():
    # The D25 gate wording: the report lists EVERY change.
    series = _series([100.0, 101.0, 102.0, 103.0, 104.0])
    series[1] = TimestampedBar(series[1].timestamp, Bar(open=101.0, high=102.0, low=100.0, close=float("nan")))
    series[3] = TimestampedBar(series[3].timestamp, Bar(open=103.0, high=100.0, low=104.0, close=103.0))

    cleaned, report = clean({"A": series})

    assert len(cleaned["A"]) == 3
    assert {c.rule for c in report.changes} == {"non_finite_ohlc", "low_above_high"}
    assert len(report.changes) == 2
