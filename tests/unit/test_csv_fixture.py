"""Roundtrip tests for the CSV fixture layer (D70)."""

from datetime import datetime

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.csv_fixture import (
    load_fixture_csv,
    load_fixture_csv_with_extras,
    load_fixture_csv_with_volumes,
    save_fixture_csv,
)
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


def test_gzipped_fixture_roundtrip(tmp_path):
    # D88: a .gz suffix means transparent compression — same format, smaller repo.
    bars = {
        "XLE": [
            TimestampedBar(datetime(2026, 7, 10), Bar(open=90.0, high=91.5, low=89.5, close=91.0)),
        ]
    }
    path = tmp_path / "fixture.csv.gz"
    save_fixture_csv(path, bars, volumes_by_symbol={"XLE": [1e6]})

    assert path.read_bytes()[:2] == b"\x1f\x8b"  # actually gzip on disk
    assert load_fixture_csv(path) == bars
    loaded_bars, loaded_volumes = __import__(
        "backtest_framework.data.csv_fixture", fromlist=["load_fixture_csv_with_volumes"]
    ).load_fixture_csv_with_volumes(path)
    assert loaded_bars == bars
    assert loaded_volumes == {"XLE": [1e6]}


def test_wrong_columns_fail_loudly(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("date,ticker,price\n2026-07-10,XLE,90.0\n", encoding="utf-8")

    try:
        load_fixture_csv(path)
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "columns" in str(exc)


# ---------------------------------------------------------------- extra columns (D190)


def test_no_extra_columns_writes_the_seven_column_header(tmp_path):
    """The inertness gate. `save_fixture_csv` is also how `SnapshotStore.create` lays
    down `bars.csv`, and `_hash_payload` hashes those bytes — so if the default path
    ever gained a column, every snapshot id in the project would silently renumber."""
    bars = {"XLE": [TimestampedBar(datetime(2026, 7, 10), Bar(90.0, 91.5, 89.5, 91.0))]}
    path = tmp_path / "f.csv"
    save_fixture_csv(path, bars, volumes_by_symbol={"XLE": [1e6]})
    header = path.read_text(encoding="utf-8").splitlines()[0]
    assert header == "timestamp,symbol,open,high,low,close,volume"


def test_passing_extra_columns_none_is_byte_identical_to_omitting_it(tmp_path):
    bars = {
        "XLE": [
            TimestampedBar(datetime(2026, 7, 10), Bar(90.0, 91.5, 89.5, 91.0)),
            TimestampedBar(datetime(2026, 7, 13), Bar(91.0, 92.0, 90.0, 90.5)),
        ],
        "XOP": [TimestampedBar(datetime(2026, 7, 10), Bar(130.0, 131.0, 129.0, 130.5))],
    }
    volumes = {"XLE": [1e6, 2e6], "XOP": [5e5]}
    without, explicit = tmp_path / "a.csv", tmp_path / "b.csv"
    save_fixture_csv(without, bars, volumes)
    save_fixture_csv(explicit, bars, volumes, extra_columns=None)
    assert without.read_bytes() == explicit.read_bytes()


def test_extra_columns_roundtrip_aligned_to_the_bars(tmp_path):
    bars = {
        "BTCUSDT": [
            TimestampedBar(datetime(2021, 5, 1, 0, 0), Bar(100.0, 101.0, 99.0, 100.5)),
            TimestampedBar(datetime(2021, 5, 1, 0, 15), Bar(100.5, 102.0, 100.0, 101.5)),
        ]
    }
    path = tmp_path / "f.csv.gz"
    save_fixture_csv(
        path,
        bars,
        volumes_by_symbol={"BTCUSDT": [201.0, 203.0]},
        extra_columns={
            "base_volume": {"BTCUSDT": [2.0, 2.0]},
            "taker_buy_base": {"BTCUSDT": [1.0, 1.5]},
        },
    )
    loaded_bars, volumes, extras = load_fixture_csv_with_extras(path)
    assert loaded_bars == bars
    assert volumes == {"BTCUSDT": [201.0, 203.0]}
    assert extras["base_volume"] == {"BTCUSDT": [2.0, 2.0]}
    assert extras["taker_buy_base"] == {"BTCUSDT": [1.0, 1.5]}


def test_extra_column_order_is_sorted_not_insertion_order(tmp_path):
    """Otherwise the bytes — and any hash over them — depend on dict ordering."""
    bars = {"X": [TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 1.0, 1.0, 1.0))]}
    first, second = tmp_path / "a.csv", tmp_path / "b.csv"
    save_fixture_csv(first, bars, None, {"zzz": {"X": [1.0]}, "aaa": {"X": [2.0]}})
    save_fixture_csv(second, bars, None, {"aaa": {"X": [2.0]}, "zzz": {"X": [1.0]}})
    assert first.read_bytes() == second.read_bytes()
    assert first.read_text(encoding="utf-8").splitlines()[0].endswith(",aaa,zzz")


def test_the_volume_loader_ignores_extra_columns(tmp_path):
    """Every existing reader keeps working against a fixture that grew a column."""
    bars = {"X": [TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 1.0, 1.0, 1.0))]}
    path = tmp_path / "f.csv"
    save_fixture_csv(path, bars, {"X": [7.0]}, {"base_volume": {"X": [3.0]}})
    loaded_bars, volumes = load_fixture_csv_with_volumes(path)
    assert loaded_bars == bars and volumes == {"X": [7.0]}


def test_a_seven_column_fixture_loads_with_empty_extras(tmp_path):
    bars = {"X": [TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 1.0, 1.0, 1.0))]}
    path = tmp_path / "f.csv"
    save_fixture_csv(path, bars, {"X": [7.0]})
    _, _, extras = load_fixture_csv_with_extras(path)
    assert extras == {}


def test_a_missing_extra_value_reads_as_nan_never_zero(tmp_path):
    """An absent observation and a zero one are different facts; conflating them is
    how a volume filter silently starts rejecting or accepting everything."""
    import math

    path = tmp_path / "f.csv"
    path.write_text(
        "timestamp,symbol,open,high,low,close,volume,base_volume\n"
        "2021-05-01T00:00:00,X,1.0,1.0,1.0,1.0,7.0,\n",
        encoding="utf-8",
    )
    _, _, extras = load_fixture_csv_with_extras(path)
    assert math.isnan(extras["base_volume"]["X"][0])


def test_a_short_extra_series_writes_blanks_rather_than_misaligning(tmp_path):
    bars = {
        "X": [
            TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 1.0, 1.0, 1.0)),
            TimestampedBar(datetime(2021, 5, 2), Bar(1.0, 1.0, 1.0, 1.0)),
        ]
    }
    path = tmp_path / "f.csv"
    save_fixture_csv(path, bars, None, {"base_volume": {"X": [3.0]}})
    rows = path.read_text(encoding="utf-8").splitlines()
    assert rows[1].endswith(",3.0")
    assert rows[2].endswith(",")


def test_gzip_writes_are_reproducible_byte_for_byte(tmp_path):
    """`gzip.open` stamps the current time into the header, which made every re-fetch a
    whole-file diff even when no row changed. A diff that always appears stops being
    read, and immutable-by-diff (D70/D24) is the property fixtures exist for."""
    bars = {"X": [TimestampedBar(datetime(2021, 5, 1), Bar(1.0, 2.0, 0.5, 1.5))]}
    first, second = tmp_path / "a.csv.gz", tmp_path / "b.csv.gz"
    save_fixture_csv(first, bars, {"X": [7.0]})
    save_fixture_csv(second, bars, {"X": [7.0]})
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes()[4:8] == b"\x00\x00\x00\x00"  # mtime pinned to zero


def test_committed_gzip_fixtures_still_load(tmp_path):
    """Reads are untouched: the header field is metadata the decompressor ignores."""
    from pathlib import Path as _P

    fixtures = _P(__file__).resolve().parents[2] / "data" / "fixtures"
    bars, volumes = load_fixture_csv_with_volumes(fixtures / "crypto_intraday_1h_raw.csv.gz")
    assert bars and volumes and len(bars["BTC-USD"]) == len(volumes["BTC-USD"])
