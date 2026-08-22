"""Offline tests for `BinanceDataSource`, against a stub opener serving built archives.

Gates closed here:

- Seam de-duplication actually runs when monthly archives are concatenated — the gap
  `dedupe_seam` was committed with tests and no caller for (D190/a470e8f).
- All three volume columns stay index-aligned to the bars through de-duplication and
  calendar trimming, because deriving one from another is the D187 defect.
- A checksum mismatch RAISES, on a fresh download and on a stale cache alike. D191's
  argument is that a published hash beats committed bytes, which is only true if a
  mismatch stops the run.
- The four-tuple's dividends and splits are empty, so an events sidecar written from it
  is true by construction rather than by luck (D48/D108).
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from datetime import date, datetime

import pytest

from backtest_framework.data.binance_archive import ArchiveFormatError, dedupe_seam
from backtest_framework.data.binance_source import (
    BinanceDataSource,
    ChecksumMismatch,
    _first_occurrence_positions,
)

MINUTE_MS = 60_000
# 2021-05-01 00:00:00 UTC in milliseconds.
MAY_2021 = 1619827200000
JUN_2021 = 1622505600000  # 2021-06-01 00:00:00 UTC


def _row(open_time: int, close: float = 100.0, base: float = 2.0, trades: int = 5) -> str:
    quote = base * close
    taker = base / 2
    return (
        f"{open_time},100.0,101.0,99.0,{close},{base},{open_time + 59_999},"
        f"{quote},{trades},{taker},{taker * close},0\n"
    )


def _zip_bytes(name: str, text: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(name, text)
    return buffer.getvalue()


class _Response:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        return None


class StubArchive:
    """Serves listings, archives and checksums from an in-memory month map."""

    def __init__(self, months: dict[str, str], symbol: str = "BTCUSDT", interval: str = "1m"):
        self.symbol, self.interval = symbol, interval
        self.zips = {m: _zip_bytes(f"{symbol}-{interval}-{m}.csv", t) for m, t in months.items()}
        self.checksums = {m: hashlib.sha256(z).hexdigest() for m, z in self.zips.items()}
        self.requests: list[str] = []

    def prefix(self) -> str:
        return f"data/spot/monthly/klines/{self.symbol}/{self.interval}/"

    def listing_xml(self) -> str:
        entries = "".join(
            "<Contents>"
            f"<Key>{self.prefix()}{self.symbol}-{self.interval}-{m}.zip</Key>"
            "<LastModified>2024-01-01T00:00:00.000Z</LastModified><ETag>&quot;e&quot;</ETag>"
            f"<Size>{len(z)}</Size></Contents>"
            for m, z in sorted(self.zips.items())
        )
        return f"<ListBucketResult><IsTruncated>false</IsTruncated>{entries}</ListBucketResult>"

    def __call__(self, url: str, timeout: int = 0):
        self.requests.append(url)
        if "ListBucketResult" not in url and "?delimiter=" in url:
            return _Response(self.listing_xml().encode())
        for month in self.zips:
            stem = f"{self.symbol}-{self.interval}-{month}.zip"
            if url.endswith(stem + ".CHECKSUM"):
                return _Response(f"{self.checksums[month]}  {stem}\n".encode())
            if url.endswith(stem):
                return _Response(self.zips[month])
        raise AssertionError(f"stub has no object for {url}")


def _source(stub: StubArchive, tmp_path) -> BinanceDataSource:
    # pause=0: the politeness delay is for the provider, not for the test suite.
    return BinanceDataSource(cache_root=tmp_path / "cache", opener=stub, pause=0.0)


def _two_clean_months() -> dict[str, str]:
    may = "".join(_row(MAY_2021 + i * MINUTE_MS, close=100.0 + i) for i in range(3))
    jun = "".join(_row(JUN_2021 + i * MINUTE_MS, close=200.0 + i) for i in range(3))
    return {"2021-05": may, "2021-06": jun}


# ---------------------------------------------------------------- month resolution


def test_months_are_resolved_from_the_listing(tmp_path):
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    assert source.list_months("BTCUSDT", "1m") == ["2021-05", "2021-06"]


def test_only_months_overlapping_the_range_are_fetched(tmp_path):
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    months = source.months_for("BTCUSDT", "1m", date(2021, 6, 1), date(2021, 6, 30))
    assert months == ["2021-06"]


def test_a_requested_month_the_provider_lacks_is_simply_absent(tmp_path):
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    months = source.months_for("BTCUSDT", "1m", date(2021, 4, 1), date(2021, 6, 30))
    assert months == ["2021-05", "2021-06"]


def test_a_range_the_archive_does_not_cover_raises(tmp_path):
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    with pytest.raises(ArchiveFormatError, match="publishes no 1m months"):
        source.get_raw_history("BTCUSDT", date(2019, 1, 1), date(2019, 12, 31))


def test_an_unsupported_timeframe_raises_rather_than_being_fetched(tmp_path):
    """Coarser rungs come from D161's resampling contract, not from a native fetch."""
    stub = StubArchive(_two_clean_months())
    with pytest.raises(ValueError, match="not in"):
        _source(stub, tmp_path).get_raw_history("BTCUSDT", date(2021, 5, 1), date(2021, 5, 2), "4h")


def test_start_after_end_raises(tmp_path):
    stub = StubArchive(_two_clean_months())
    with pytest.raises(ValueError, match="is after end"):
        _source(stub, tmp_path).get_raw_history("BTCUSDT", date(2021, 6, 1), date(2021, 5, 1))


# ---------------------------------------------------------------- the seam


def test_two_months_assemble_into_one_continuous_series(tmp_path):
    stub = StubArchive(_two_clean_months())
    bars, volumes, dividends, splits = _source(stub, tmp_path).get_raw_history(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    assert len(bars) == 6
    assert bars[0].timestamp == datetime(2021, 5, 1, 0, 0)
    assert bars[-1].timestamp == datetime(2021, 6, 1, 0, 2)
    assert len(volumes) == 6


def test_dividends_and_splits_are_always_empty(tmp_path):
    """So an events sidecar written from this is true by construction (D48/D108)."""
    stub = StubArchive(_two_clean_months())
    _, _, dividends, splits = _source(stub, tmp_path).get_raw_history(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    assert dividends == [] and splits == []


def test_get_raw_history_returns_quote_volume_not_base(tmp_path):
    """Quote notional is the crypto convention here and what D189's S1 sensor used."""
    stub = StubArchive({"2021-05": _row(MAY_2021, close=100.0, base=2.0)})
    bars, volumes, _, _ = _source(stub, tmp_path).get_raw_history(
        "BTCUSDT", date(2021, 5, 1), date(2021, 5, 31)
    )
    assert volumes == [200.0]  # base 2.0 x close 100.0, as the provider states it


def test_all_three_volume_columns_are_carried_and_never_derived(tmp_path):
    stub = StubArchive({"2021-05": _row(MAY_2021, close=100.0, base=2.0)})
    _, columns, _ = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 5, 1), date(2021, 5, 31)
    )
    assert columns["base_volume"] == [2.0]
    assert columns["quote_volume"] == [200.0]
    assert columns["taker_buy_base"] == [1.0]


# ---------------------------------------------------------------- seam de-duplication


def test_a_duplicated_bar_across_the_seam_is_dropped_and_counted(tmp_path):
    """Concatenated archives are exactly D99's duplicate_timestamp hard violation."""
    overlap = _row(MAY_2021 + 2 * MINUTE_MS, close=102.0)
    months = _two_clean_months()
    months["2021-06"] = overlap + months["2021-06"]
    stub = StubArchive(months)
    bars, columns, report = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    assert report.seam_duplicates_dropped == 1
    timestamps = [tb.timestamp for tb in bars]
    assert len(timestamps) == len(set(timestamps)) == 6


def test_deduplication_keeps_every_column_aligned_to_the_bars(tmp_path):
    months = _two_clean_months()
    months["2021-06"] = _row(MAY_2021 + 2 * MINUTE_MS, close=102.0) + months["2021-06"]
    stub = StubArchive(months)
    bars, columns, _ = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    for name, series in columns.items():
        assert len(series) == len(bars), name
    # quote = base x close for every surviving row, which only holds if the drop applied
    # the same positions to all three columns.
    for tb, base, quote in zip(bars, columns["base_volume"], columns["quote_volume"]):
        assert quote == pytest.approx(base * tb.bar.close)


def test_the_position_helper_agrees_with_dedupe_seam(tmp_path):
    """Two implementations of one rule is a drift risk, so they are pinned together."""
    stamps = [datetime(2021, 5, 1, 0, m) for m in (0, 1, 1, 2, 0, 3)]
    from backtest_framework.simulator.fills import Bar

    from backtest_framework.data.bars import TimestampedBar as TB

    bars = [TB(timestamp=s, bar=Bar(1.0, 1.0, 1.0, 1.0)) for s in stamps]
    volumes = [float(i) for i in range(len(stamps))]
    kept_bars, kept_volumes, dropped = dedupe_seam(bars, volumes)
    keep = _first_occurrence_positions(stamps)
    assert [bars[i] for i in keep] == kept_bars
    assert [volumes[i] for i in keep] == kept_volumes
    assert len(stamps) - len(keep) == dropped == 2


def test_a_clean_series_loses_nothing(tmp_path):
    stub = StubArchive(_two_clean_months())
    _, _, report = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    assert report.seam_duplicates_dropped == 0


# ---------------------------------------------------------------- calendar trimming


def test_months_arrive_whole_and_are_trimmed_to_the_requested_range(tmp_path):
    stub = StubArchive(_two_clean_months())
    bars, columns, _ = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 6, 1), date(2021, 6, 30)
    )
    assert len(bars) == 3
    assert all(tb.timestamp.month == 6 for tb in bars)
    assert all(len(series) == 3 for series in columns.values())


# ---------------------------------------------------------------- checksums


def test_a_corrupt_download_raises_and_names_the_key(tmp_path):
    stub = StubArchive(_two_clean_months())
    stub.checksums["2021-05"] = "0" * 64
    with pytest.raises(ChecksumMismatch, match="2021-05"):
        _source(stub, tmp_path).get_raw_history("BTCUSDT", date(2021, 5, 1), date(2021, 6, 30))


def test_a_stale_cache_raises_rather_than_being_used(tmp_path):
    """The whole point of D191: a cached archive whose published hash has since changed
    is the event the manifest exists to detect, so the checksum is re-fetched every time."""
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    source.get_raw_history("BTCUSDT", date(2021, 5, 1), date(2021, 6, 30))

    cached = source._cache_path(source.archive_key("BTCUSDT", "1m", "2021-05"))
    assert cached.is_file()
    cached.write_bytes(b"not the archive you cached")

    with pytest.raises(ChecksumMismatch, match="stale or corrupt"):
        source.get_raw_history("BTCUSDT", date(2021, 5, 1), date(2021, 6, 30))


def test_a_second_run_hits_the_cache_and_does_not_redownload(tmp_path):
    stub = StubArchive(_two_clean_months())
    source = _source(stub, tmp_path)
    _, _, first = source.get_volume_columns("BTCUSDT", date(2021, 5, 1), date(2021, 6, 30))
    _, _, second = source.get_volume_columns("BTCUSDT", date(2021, 5, 1), date(2021, 6, 30))
    assert first.downloads == 2 and first.cache_hits == 0
    assert second.downloads == 0 and second.cache_hits == 2


def test_the_report_records_the_published_hash_for_every_archive(tmp_path):
    """These records are what the manifest is written from."""
    stub = StubArchive(_two_clean_months())
    _, _, report = _source(stub, tmp_path).get_volume_columns(
        "BTCUSDT", date(2021, 5, 1), date(2021, 6, 30)
    )
    assert [r.month for r in report.records] == ["2021-05", "2021-06"]
    assert all(len(r.sha256) == 64 for r in report.records)
    assert report.records[0].sha256 == stub.checksums["2021-05"]


def test_an_archive_with_two_members_raises(tmp_path):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("a.csv", _row(MAY_2021))
        archive.writestr("b.csv", _row(MAY_2021))
    stub = StubArchive({"2021-05": _row(MAY_2021)})
    stub.zips["2021-05"] = buffer.getvalue()
    stub.checksums["2021-05"] = hashlib.sha256(buffer.getvalue()).hexdigest()
    with pytest.raises(ArchiveFormatError, match="holds 2 members"):
        _source(stub, tmp_path).get_raw_history("BTCUSDT", date(2021, 5, 1), date(2021, 5, 31))


# ---------------------------------------------------------------- construction


def test_an_unknown_market_raises():
    with pytest.raises(ValueError, match="market must be"):
        BinanceDataSource(market="coinbase")
