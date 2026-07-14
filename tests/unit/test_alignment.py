"""Unit tests for multi-instrument bar alignment (D45)."""

from datetime import datetime

from backtest_framework.data.alignment import align_bars
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.simulator.fills import Bar

MON = datetime(2026, 7, 13)
TUE = datetime(2026, 7, 14)
WED = datetime(2026, 7, 15)
THU = datetime(2026, 7, 16)


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


def _series(*items: tuple[datetime, float]) -> list[TimestampedBar]:
    return [TimestampedBar(ts, _bar(price)) for ts, price in items]


def test_inner_join_keeps_only_common_timestamps():
    a = _series((MON, 10.0), (TUE, 11.0), (WED, 12.0))
    b = _series((MON, 100.0), (TUE, 101.0), (WED, 102.0))

    aligned = align_bars({"A": a, "B": b})

    assert [ab.timestamp for ab in aligned] == [MON, TUE, WED]


def test_bar_missing_from_one_leg_drops_that_timestamp_for_both():
    a = _series((MON, 10.0), (TUE, 11.0), (WED, 12.0), (THU, 13.0))
    b = _series((MON, 100.0), (WED, 102.0), (THU, 103.0))  # missing TUE

    aligned = align_bars({"A": a, "B": b})

    assert [ab.timestamp for ab in aligned] == [MON, WED, THU]  # TUE dropped for A too


def test_each_instruments_own_bar_data_is_preserved():
    a = _series((MON, 10.0), (TUE, 11.0))
    b = _series((MON, 100.0), (TUE, 101.0))

    aligned = align_bars({"A": a, "B": b})

    assert aligned[0].bars["A"].close == 10.0
    assert aligned[0].bars["B"].close == 100.0
    assert aligned[1].bars["A"].close == 11.0
    assert aligned[1].bars["B"].close == 101.0


def test_output_is_sorted_regardless_of_input_order():
    a = _series((WED, 12.0), (MON, 10.0), (TUE, 11.0))  # deliberately out of order
    b = _series((TUE, 101.0), (WED, 102.0), (MON, 100.0))

    aligned = align_bars({"A": a, "B": b})

    assert [ab.timestamp for ab in aligned] == [MON, TUE, WED]


def test_single_instrument_input_returns_the_whole_series_unchanged():
    a = _series((MON, 10.0), (TUE, 11.0), (WED, 12.0))

    aligned = align_bars({"A": a})

    assert [ab.timestamp for ab in aligned] == [MON, TUE, WED]
    assert [ab.bars["A"].close for ab in aligned] == [10.0, 11.0, 12.0]


def test_no_common_timestamps_returns_empty_list():
    a = _series((MON, 10.0))
    b = _series((TUE, 100.0))

    assert align_bars({"A": a, "B": b}) == []


def test_empty_input_returns_empty_list():
    assert align_bars({}) == []


def test_duplicate_timestamps_are_refused_loudly():
    # D99 (audit F10): keying bars by timestamp would silently collapse a duplicate
    # last-wins — a real yfinance failure mode after joins/re-fetches.
    import pytest

    a = _series((MON, 10.0), (TUE, 11.0), (TUE, 999.0))
    with pytest.raises(ValueError, match="duplicate bar timestamps"):
        align_bars({"A": a})
