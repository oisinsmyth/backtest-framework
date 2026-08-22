"""Offline tests for the Binance archive parser.

Gates closed here:

- The epoch unit is read per file, on BOTH sides of the 2025-01 ms -> us switch, and an
  unrecognised width raises rather than being guessed (D187's class of defect).
- Timestamps are naive-meaning-UTC regardless of the machine's local zone.
- Monthly-archive seams are de-duplicated before `align_bars` (D99) or `validate-v1`'s
  hard `duplicate_timestamp` check can see them.
- Zero-volume and zero-TRADE bars are counted separately, because their agreement is what
  distinguishes a real empty minute from D160's provider defect.
- A truncated bucket listing is detected rather than mistaken for a short history.
"""

from __future__ import annotations

from datetime import datetime

import pytest

from backtest_framework.data.binance_archive import (
    DOWNLOAD_BASE,
    ArchiveFormatError,
    assert_on_grid,
    coverage_from_listing,
    dedupe_seam,
    detect_timestamp_unit,
    gap_census,
    month_sequence,
    offgrid_census,
    parse_klines,
    parse_listing,
    resample_to_daily,
    volume_census,
)

# 2021-05-01 00:00 and 00:01 UTC, milliseconds — copied from the real archive.
_MS_ROWS = (
    "1619827200000,57697.25000000,57697.26000000,57533.75000000,57545.06000000,"
    "106.99194300,1619827259999,6165380.96980849,4248,40.81299200,2351783.49801040,0\n"
    "1619827260000,57545.06000000,57549.99000000,57421.05000000,57542.62000000,"
    "139.03474400,1619827319999,7993892.53428734,4106,62.62788400,3600659.30991260,0\n"
)

# 2025-06-01 00:00 UTC, microseconds — the same schema after the switch.
_US_ROWS = (
    "1748736000000000,104591.88000000,104647.11000000,104591.88000000,104647.11000000,"
    "10.71688000,1748736059999999,1121053.19051460,1136,9.99825000,1045871.00000000,0\n"
)

_HEADER = (
    "open_time,open,high,low,close,volume,close_time,quote_volume,count,"
    "taker_buy_volume,taker_buy_quote_volume,ignore\n"
)


def _bar_row(open_time: int, close: float = 100.0, volume: float = 1.0, trades: int = 5) -> str:
    return (
        f"{open_time},100.0,101.0,99.0,{close},{volume},{open_time + 59999},"
        f"{volume * close},{trades},0.5,50.0,0\n"
    )


# ---------------------------------------------------------------- timestamp units


def test_detect_timestamp_unit_reads_both_sides_of_the_switch():
    """2024-12 files are 13-digit ms; 2025-01 files are 16-digit us."""
    assert detect_timestamp_unit("1619827200000") == "ms"
    assert detect_timestamp_unit("1748736000000000") == "us"


def test_unrecognised_epoch_width_raises_rather_than_guessing():
    """The archive's unit changed once; a reader that guesses a third is D187 again."""
    with pytest.raises(ArchiveFormatError, match="10 digits"):
        detect_timestamp_unit("1619827200")


def test_millisecond_file_parses_to_the_right_wall_clock():
    parsed = parse_klines(_MS_ROWS)
    assert parsed.timestamp_unit == "ms"
    assert parsed.bars[0].timestamp == datetime(2021, 5, 1, 0, 0)
    assert parsed.bars[1].timestamp == datetime(2021, 5, 1, 0, 1)


def test_microsecond_file_parses_to_the_right_wall_clock():
    """The same instant read as ms would land in the year 57,400."""
    parsed = parse_klines(_US_ROWS)
    assert parsed.timestamp_unit == "us"
    assert parsed.bars[0].timestamp == datetime(2025, 6, 1, 0, 0)


def test_timestamps_are_naive_meaning_utc():
    """Naive is the layer's convention (D75); UTC is what the naivety must mean."""
    parsed = parse_klines(_MS_ROWS)
    assert parsed.bars[0].timestamp.tzinfo is None
    assert parsed.bars[0].timestamp.hour == 0


def test_a_unit_change_inside_one_file_raises():
    with pytest.raises(ArchiveFormatError, match="epoch unit changes inside"):
        parse_klines(_MS_ROWS + _US_ROWS)


# ---------------------------------------------------------------- schema


def test_header_row_is_detected_and_skipped():
    parsed = parse_klines(_HEADER + _MS_ROWS)
    assert parsed.had_header is True
    assert len(parsed.bars) == 2


def test_headerless_file_keeps_every_row():
    parsed = parse_klines(_MS_ROWS)
    assert parsed.had_header is False
    assert len(parsed.bars) == 2


def test_wrong_column_count_raises():
    with pytest.raises(ArchiveFormatError, match="expected 12 kline columns"):
        parse_klines("1619827200000,100.0,101.0,99.0,100.5\n")


def test_base_and_quote_volumes_are_kept_separately_and_never_derived():
    """The two columns D187 needed and yfinance does not provide."""
    parsed = parse_klines(_MS_ROWS)
    assert parsed.base_volumes[0] == pytest.approx(106.991943)
    assert parsed.quote_volumes[0] == pytest.approx(6165380.96980849)
    # Their ratio is a price inside the bar — the units cross-check.
    vwap = parsed.quote_volumes[0] / parsed.base_volumes[0]
    assert parsed.bars[0].bar.low <= vwap <= parsed.bars[0].bar.high


def test_taker_buy_base_is_read_from_the_right_column():
    """Column index 9. A bare row[9] is exactly how D187 happened, so this pins it."""
    parsed = parse_klines(_MS_ROWS)
    assert parsed.taker_buy_base[0] == pytest.approx(40.812992)
    assert parsed.taker_buy_base[0] < parsed.base_volumes[0]


def test_trade_counts_are_read_as_integers():
    parsed = parse_klines(_MS_ROWS)
    assert parsed.trade_counts == [4248, 4106]


def test_empty_file_raises():
    with pytest.raises(ArchiveFormatError, match="empty kline file"):
        parse_klines("")


def test_header_with_no_data_rows_raises():
    with pytest.raises(ArchiveFormatError, match="header and no data rows"):
        parse_klines(_HEADER)


# ---------------------------------------------------------------- grid and gaps


def test_bars_on_the_minute_grid_pass():
    parsed = parse_klines(_MS_ROWS)
    assert_on_grid(parsed.bars, 1)


def test_bars_off_a_five_minute_grid_raise():
    parsed = parse_klines(_MS_ROWS)
    with pytest.raises(ArchiveFormatError, match="off the 5-minute grid"):
        assert_on_grid(parsed.bars, 5)


def test_gap_census_reports_missing_minutes_and_never_patches_them():
    text = _bar_row(1619827200000) + _bar_row(1619827200000 + 5 * 60_000)
    parsed = parse_klines(text)
    assert gap_census(parsed.bars, 1) == {"5": 1}
    assert len(parsed.bars) == 2  # nothing fabricated to fill the hole


def test_gapless_series_has_an_empty_census():
    parsed = parse_klines(_MS_ROWS)
    assert gap_census(parsed.bars, 1) == {}


# ---------------------------------------------------------------- seam de-duplication


def test_seam_duplicates_are_dropped_and_counted():
    """Concatenated monthly archives are exactly D99's duplicate_timestamp failure."""
    parsed = parse_klines(_MS_ROWS + _MS_ROWS)
    bars, volumes, dropped = dedupe_seam(parsed.bars, parsed.base_volumes)
    assert dropped == 2
    assert len(bars) == len(volumes) == 2
    assert [b.timestamp for b in bars] == sorted({b.timestamp for b in parsed.bars})


def test_dedupe_keeps_the_first_occurrence_and_its_paired_volume():
    parsed = parse_klines(_bar_row(1619827200000, volume=7.0) + _bar_row(1619827200000, volume=9.0))
    _, volumes, dropped = dedupe_seam(parsed.bars, parsed.base_volumes)
    assert dropped == 1
    assert volumes == [7.0]


def test_dedupe_refuses_misaligned_inputs():
    parsed = parse_klines(_MS_ROWS)
    with pytest.raises(ArchiveFormatError, match="not aligned"):
        dedupe_seam(parsed.bars, [1.0])


def test_clean_series_is_left_untouched():
    parsed = parse_klines(_MS_ROWS)
    bars, volumes, dropped = dedupe_seam(parsed.bars, parsed.base_volumes)
    assert dropped == 0
    assert bars == parsed.bars and volumes == parsed.base_volumes


# ---------------------------------------------------------------- volume census


def test_zero_volume_agreeing_with_zero_trades_is_a_real_empty_minute():
    """22% of 2017-09's BTC minutes look like this, and they are TRUE (unlike D160's)."""
    census = volume_census([0.0, 1.0, 0.0, 2.0], [0, 5, 0, 7])
    assert census.zero_volume == 2
    assert census.zero_trades == 2
    assert census.zero_volume_and_zero_trades == 2
    assert census.agrees is True
    assert census.zero_volume_rate == pytest.approx(0.5)


def test_zero_volume_without_zero_trades_does_not_agree():
    """Volume of zero on a bar that recorded trades is a feed defect, not an empty minute."""
    census = volume_census([0.0, 1.0], [12, 5])
    assert census.zero_volume == 1
    assert census.zero_trades == 0
    assert census.agrees is False


def test_census_of_a_fully_traded_month_is_empty():
    census = volume_census([1.0, 2.0], [3, 4])
    assert census.zero_volume == 0
    assert census.agrees is True  # 0 == 0 == 0
    assert census.zero_volume_rate == 0.0


# ---------------------------------------------------------------- listing parser


_LISTING = """<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult>
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2017-08.zip</Key>
    <LastModified>2020-01-01T00:00:00.000Z</LastModified>
    <ETag>&quot;abc&quot;</ETag>
    <Size>1394854</Size>
  </Contents>
  <Contents>
    <Key>data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2017-08.zip.CHECKSUM</Key>
    <LastModified>2020-01-01T00:00:00.000Z</LastModified>
    <ETag>&quot;def&quot;</ETag>
    <Size>88</Size>
  </Contents>
  <Contents>
    <Key>data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2017-10.zip</Key>
    <LastModified>2020-01-01T00:00:00.000Z</LastModified>
    <ETag>&quot;ghi&quot;</ETag>
    <Size>2000000</Size>
  </Contents>
</ListBucketResult>
"""


def test_listing_splits_archives_from_checksum_sidecars():
    listing = parse_listing(_LISTING)
    assert len(listing.entries) == 3
    assert len(listing.archives) == 2
    assert len(listing.checksums) == 1


def test_listing_sizes_are_read_so_retention_costs_no_downloads():
    listing = parse_listing(_LISTING)
    assert sum(e.size for e in listing.archives) == 3394854


def test_truncated_listing_is_detected_and_carries_a_marker():
    """A silent stop at 1000 keys looks exactly like a symbol with 1000 months."""
    listing = parse_listing(_LISTING.replace("<IsTruncated>false", "<IsTruncated>true"))
    assert listing.is_truncated is True
    assert listing.next_marker is not None


def test_untruncated_listing_has_no_marker():
    assert parse_listing(_LISTING).is_truncated is False


def test_month_is_extracted_from_the_archive_name():
    listing = parse_listing(_LISTING)
    assert [e.month for e in listing.archives] == ["2017-08", "2017-10"]


# ---------------------------------------------------------------- coverage


def test_coverage_reports_span_size_and_checksum_rate():
    coverage = coverage_from_listing("BTCUSDT", parse_listing(_LISTING))
    assert coverage.available is True
    assert coverage.first_month == "2017-08"
    assert coverage.last_month == "2017-10"
    assert coverage.total_bytes == 3394854
    assert coverage.checksum_coverage == pytest.approx(0.5)


def test_a_month_the_provider_never_published_shows_as_a_listing_gap():
    """Distinct from a gap INSIDE a month's bars, which gap_census reports."""
    coverage = coverage_from_listing("BTCUSDT", parse_listing(_LISTING))
    assert coverage.missing_months == ["2017-09"]


def test_an_unlisted_symbol_is_unavailable_not_empty():
    coverage = coverage_from_listing("MIOTAUSDT", parse_listing("<ListBucketResult/>"))
    assert coverage.available is False
    assert coverage.first_month is None
    assert coverage.missing_months == []
    assert coverage.checksum_coverage == 0.0


def test_month_sequence_spans_a_year_boundary():
    assert month_sequence("2024-11", "2025-02") == ["2024-11", "2024-12", "2025-01", "2025-02"]


def test_month_sequence_of_a_single_month():
    assert month_sequence("2020-03", "2020-03") == ["2020-03"]


# ---------------------------------------------------------------- daily resample


def test_daily_resample_takes_first_open_last_close_and_the_extremes():
    day = 1619827200000  # 2021-05-01 00:00 UTC
    text = (
        _bar_row(day, close=100.0, volume=1.0)
        + _bar_row(day + 60_000, close=110.0, volume=2.0)
        + _bar_row(day + 120_000, close=105.0, volume=3.0)
    )
    parsed = parse_klines(text)
    daily = resample_to_daily(parsed.bars, parsed.base_volumes)
    assert len(daily) == 1
    assert daily[0].open == 100.0  # first bar's OPEN, which _bar_row fixes at 100
    assert daily[0].close == 105.0  # last bar's close
    assert daily[0].high == 101.0
    assert daily[0].low == 99.0
    assert daily[0].base_volume == pytest.approx(6.0)


def test_daily_resample_splits_on_the_utc_day_boundary():
    day = 1619827200000
    text = _bar_row(day) + _bar_row(day + 24 * 60 * 60_000)
    parsed = parse_klines(text)
    daily = resample_to_daily(parsed.bars, parsed.base_volumes)
    assert [d.day.isoformat() for d in daily] == ["2021-05-01", "2021-05-02"]


def test_daily_resample_refuses_misaligned_inputs():
    parsed = parse_klines(_MS_ROWS)
    with pytest.raises(ArchiveFormatError, match="not aligned"):
        resample_to_daily(parsed.bars, [1.0])


# ---------------------------------------------------------------- live smoke test


@pytest.mark.live_fetch
def test_real_archive_month_parses_and_verifies():
    """Shape invariants against the real provider — never specific prices (D24).

    Deliberately picks a month AFTER the microsecond switch, because the failure this
    guards is a reader that silently dates 2025 bars to the year 57,400.
    """
    import hashlib
    import io
    import urllib.request
    import zipfile

    key = "data/spot/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2025-06.zip"
    with urllib.request.urlopen(f"{DOWNLOAD_BASE}/{key}", timeout=120) as response:  # noqa: S310
        payload = response.read()
    with urllib.request.urlopen(  # noqa: S310
        f"{DOWNLOAD_BASE}/{key}.CHECKSUM", timeout=60
    ) as response:
        published = response.read().decode().split()[0]

    assert hashlib.sha256(payload).hexdigest() == published

    archive = zipfile.ZipFile(io.BytesIO(payload))
    parsed = parse_klines(archive.read(archive.namelist()[0]).decode())

    assert parsed.timestamp_unit == "us"
    assert parsed.columns == 12
    assert parsed.bars[0].timestamp.year == 2025
    assert_on_grid(parsed.bars, 1)
    assert [b.timestamp for b in parsed.bars] == sorted(b.timestamp for b in parsed.bars)
    for tb in parsed.bars:
        assert tb.bar.low <= tb.bar.open <= tb.bar.high
        assert tb.bar.low <= tb.bar.close <= tb.bar.high


# ---------------------------------------------------------------- off-grid census (D193)


def test_offgrid_census_finds_a_constant_clock_skew():
    """The real occurrence: 2017-12-04 to 2017-12-18, every BTCUSDT 1m bar stamped
    20.799s past the minute. A constant offset, not jitter, and 20,401 bars of it."""
    base = 1512345600000  # 2017-12-04 00:00 UTC
    skew = 20_799
    text = "".join(_bar_row(base + skew + m * 60_000) for m in range(5))
    parsed = parse_klines(text)
    census = offgrid_census(parsed.bars, 1)
    assert census.bars == 5
    assert census.residual_seconds == (20.799,)
    assert len(census.days) == 1


def test_offgrid_census_is_empty_on_an_aligned_series():
    parsed = parse_klines(_MS_ROWS)
    census = offgrid_census(parsed.bars, 1)
    assert census.bars == 0 and census.days == [] and census.residual_seconds == ()


def test_offgrid_census_counts_per_day_and_reports_the_span():
    base = 1512345600000
    text = "".join(
        _bar_row(base + 20_799 + d * 86_400_000 + m * 60_000)
        for d in range(3)
        for m in range(2)
    )
    census = offgrid_census(parse_klines(text).bars, 1)
    assert len(census.days) == 3
    assert census.bars == 6
    assert all(n == 2 for n in census.bars_by_day.values())


def test_a_bar_on_the_minute_but_off_a_fifteen_minute_grid_counts_as_offgrid():
    """The census is relative to the target interval, not to the minute."""
    parsed = parse_klines(_MS_ROWS)  # 00:00 and 00:01
    census = offgrid_census(parsed.bars, 15)
    assert census.bars == 1  # 00:01 is off the 15m grid, 00:00 is on it
    assert census.residual_seconds == (60.0,)
