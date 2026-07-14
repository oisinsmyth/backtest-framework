"""Roundtrip tests for the CSV fixture layer (D70)."""

from datetime import datetime

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.csv_fixture import load_fixture_csv, save_fixture_csv
from backtest_framework.simulator.fills import Bar


def test_save_load_roundtrip_preserves_bars(tmp_path):
    bars = {
        "XLE": [
            TimestampedBar(datetime(2026, 7, 10), Bar(open=90.0, high=91.5, low=89.5, close=91.0)),
            TimestampedBar(datetime(2026, 7, 13), Bar(open=91.0, high=92.0, low=90.0, close=90.5)),
        ],
        "XOP": [
            TimestampedBar(datetime(2026, 7, 10), Bar(open=130.0, high=131.0, low=129.0, close=130.5)),
        ],
    }
    path = tmp_path / "fixture.csv"
    save_fixture_csv(path, bars, volumes_by_symbol={"XLE": [1e6, 2e6], "XOP": [5e5]})

    loaded = load_fixture_csv(path)

    assert loaded == bars  # volumes stored but not loaded (D48 — no false volume field)


def test_load_sorts_by_timestamp(tmp_path):
    bars = {
        "XLE": [
            TimestampedBar(datetime(2026, 7, 13), Bar(open=91.0, high=92.0, low=90.0, close=90.5)),
            TimestampedBar(datetime(2026, 7, 10), Bar(open=90.0, high=91.5, low=89.5, close=91.0)),
        ]
    }
    path = tmp_path / "fixture.csv"
    save_fixture_csv(path, bars)

    loaded = load_fixture_csv(path)
    timestamps = [tb.timestamp for tb in loaded["XLE"]]
    assert timestamps == sorted(timestamps)


def test_wrong_columns_fail_loudly(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,ticker,price\n2026-07-10,XLE,90.0\n", encoding="utf-8")

    try:
        load_fixture_csv(path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "columns" in str(exc)
