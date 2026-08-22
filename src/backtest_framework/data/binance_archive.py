"""Pure parsing for Binance's public flat-file archives (data.binance.vision).

Network access lives in `scripts/probe_binance_archive.py`; everything here is pure and
offline, mirroring the `_bars_from_dataframe` / `EquityDataSource` split in
`yfinance_source.py` (D59) so conversion is testable without touching the provider.

This module deliberately stops short of a `DataSource`. It parses; it does not fetch,
snapshot, clean or validate.

## Why a second provider at all

Every intraday result in this project is a statement about yfinance rather than about
crypto. D160 recorded that yfinance reports `Volume = 0` on roughly half of all hourly
BTC/ETH bars, so the cleaner had to be called on prices only; D163 refused any return
claim below 1h because 60 days cannot hold a 252-day training window; D165 had to splice
a cost curve onto a separately-measured gross edge because the 730 days served contain no
trend edge at all. D189 then closed the terrain programme on an S1 volume-profile sensor
built from *daily* bars for the same reason.

## Two provider facts this module exists to enforce

**The timestamp unit is not constant across the archive.** Binance switched kline
`open_time` from milliseconds to microseconds at the 2025-01 monthly file: 2024-12 is 13
digits, 2025-01 is 16. A reader that assumes milliseconds parses a mid-2025 bar as the
year 57,400. `detect_timestamp_unit` reads the unit off each file rather than assuming it
— D187's lesson, which is that the name of a field is not a contract and the parameter
that enforces it is.

**Volume is unambiguous here, and that is a change.** D187 was a units error: crypto
volume quoted in dollars was read as coins, scaling every market-impact charge by the
square root of price. Binance klines carry base volume (BTC) and quote volume (USDT) as
two separate named columns, so `parse_klines` returns both and never derives one from the
other. `taker_buy_base` arrives in the same row, which puts signed order flow within
reach without the ~400 MB-per-symbol-month `aggTrades` archives.
"""

from __future__ import annotations

import csv
import io
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from ..simulator.fills import Bar
from .bars import TimestampedBar

DOWNLOAD_BASE = "https://data.binance.vision"
"""Object download host. `{DOWNLOAD_BASE}/{key}` fetches any key from a listing."""

LISTING_BASE = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
"""S3 listing host. Returns ListBucketResult XML with a `<Size>` per key, so retention
and total bytes are measurable without downloading a single archive."""

KLINE_COLUMNS = 12
"""open_time, open, high, low, close, volume, close_time, quote_volume, trades,
taker_buy_base, taker_buy_quote, ignore."""

# 0-based column indices. Named because a bare `row[9]` is exactly how D187 happened.
COL_OPEN_TIME = 0
COL_OPEN = 1
COL_HIGH = 2
COL_LOW = 3
COL_CLOSE = 4
COL_VOLUME_BASE = 5
COL_QUOTE_VOLUME = 7
COL_TRADES = 8
COL_TAKER_BUY_BASE = 9

TIMESTAMP_DIGITS: dict[int, str] = {13: "ms", 16: "us"}
"""Epoch digit count -> unit. Milliseconds through 2024-12, microseconds from 2025-01."""

DIVISOR: dict[str, int] = {"ms": 1_000, "us": 1_000_000}

_KEY_RE = re.compile(
    r"<Key>([^<]+)</Key>.*?<Size>(\d+)</Size>",
    re.DOTALL,
)
_NEXT_MARKER_RE = re.compile(r"<NextMarker>([^<]+)</NextMarker>")
_TRUNCATED_RE = re.compile(r"<IsTruncated>([^<]+)</IsTruncated>")


class ArchiveFormatError(ValueError):
    """The archive did not have the shape this module was written against.

    Raised rather than worked around. A provider that changes its schema should stop the
    run, not have its new shape silently reinterpreted as the old one.
    """


@dataclass(frozen=True)
class ArchiveEntry:
    """One object in a bucket listing."""

    key: str
    size: int

    @property
    def filename(self) -> str:
        return self.key.rsplit("/", 1)[-1]

    @property
    def month(self) -> str | None:
        """The `YYYY-MM` stamp in a monthly archive's name, or None if absent."""
        match = re.search(r"(\d{4}-\d{2})\.zip$", self.filename)
        return match.group(1) if match else None


@dataclass(frozen=True)
class Listing:
    """A parsed `ListBucketResult`, with pagination state kept rather than discarded."""

    entries: list[ArchiveEntry]
    is_truncated: bool
    next_marker: str | None

    @property
    def archives(self) -> list[ArchiveEntry]:
        """Data objects only — the `.CHECKSUM` sidecars are metadata about them."""
        return [e for e in self.entries if e.key.endswith(".zip")]

    @property
    def checksums(self) -> list[ArchiveEntry]:
        return [e for e in self.entries if e.key.endswith(".CHECKSUM")]


@dataclass(frozen=True)
class KlineFile:
    """One parsed monthly kline archive.

    Volumes are kept in the two units the provider states, positionally aligned to
    `bars`, and never attached to a `TimestampedBar` (D48/D60).
    """

    bars: list[TimestampedBar]
    base_volumes: list[float]
    quote_volumes: list[float]
    taker_buy_base: list[float]
    trade_counts: list[int]
    timestamp_unit: str
    had_header: bool
    columns: int


@dataclass(frozen=True)
class VolumeCensus:
    """Zero-volume accounting, kept separate from zero-*trade* accounting on purpose.

    D160 found yfinance reporting `Volume = 0` on half of all hourly BTC/ETH bars whose
    prices were present and consistent — a provider defect. A 1m bar on a young or thin
    exchange listing can legitimately have no trades in it, and then zero volume is
    *true*. The two cases are distinguishable only by whether the zero-volume bars and
    the zero-trade bars are the same bars, so this counts both and their agreement.
    """

    bars: int
    zero_volume: int
    zero_trades: int
    zero_volume_and_zero_trades: int

    @property
    def zero_volume_rate(self) -> float:
        return self.zero_volume / self.bars if self.bars else 0.0

    @property
    def agrees(self) -> bool:
        """True when every zero-volume bar is also a zero-trade bar, and vice versa."""
        return (
            self.zero_volume == self.zero_trades == self.zero_volume_and_zero_trades
        )


def parse_listing(xml_text: str) -> Listing:
    """Parse an S3 `ListBucketResult` into entries plus pagination state.

    The pagination state is returned rather than dropped because a listing that silently
    stops at 1000 keys looks exactly like a symbol with 1000 months of history.
    """
    entries = [ArchiveEntry(key, int(size)) for key, size in _KEY_RE.findall(xml_text)]
    truncated_match = _TRUNCATED_RE.search(xml_text)
    is_truncated = (
        truncated_match is not None and truncated_match.group(1).strip() == "true"
    )
    marker_match = _NEXT_MARKER_RE.search(xml_text)
    next_marker = marker_match.group(1) if marker_match else None
    if is_truncated and next_marker is None and entries:
        next_marker = entries[-1].key
    return Listing(entries=entries, is_truncated=is_truncated, next_marker=next_marker)


def detect_timestamp_unit(raw_open_time: str) -> str:
    """Return `"ms"` or `"us"` from an epoch field's digit count.

    Binance switched kline timestamps from milliseconds to microseconds at 2025-01. The
    unit is read per file; assuming either one silently mis-dates half the archive.
    """
    digits = len(raw_open_time.strip())
    unit = TIMESTAMP_DIGITS.get(digits)
    if unit is None:
        raise ArchiveFormatError(
            f"open_time {raw_open_time!r} has {digits} digits; expected 13 (ms) or "
            f"16 (us). The archive's epoch unit changed once already (ms through "
            f"2024-12, us from 2025-01) and this reader refuses to guess a third."
        )
    return unit


def parse_klines(text: str) -> KlineFile:
    """Parse a monthly kline CSV into bars plus the volume columns, in stated units.

    Handles the header row Binance began emitting on some files, detects the epoch unit
    per file, and strips tzinfo so timestamps are naive-meaning-UTC — the convention the
    rest of the data layer relies on, and which D33's calendar-day carry arithmetic needs
    in order not to become DST-sensitive.
    """
    rows = list(csv.reader(io.StringIO(text)))
    rows = [r for r in rows if r]
    if not rows:
        raise ArchiveFormatError("empty kline file")

    had_header = not rows[0][COL_OPEN_TIME].strip().lstrip("-").isdigit()
    if had_header:
        rows = rows[1:]
    if not rows:
        raise ArchiveFormatError("kline file has a header and no data rows")

    columns = len(rows[0])
    if columns != KLINE_COLUMNS:
        raise ArchiveFormatError(
            f"expected {KLINE_COLUMNS} kline columns, got {columns}"
        )

    unit = detect_timestamp_unit(rows[0][COL_OPEN_TIME])
    divisor = DIVISOR[unit]

    bars: list[TimestampedBar] = []
    base_volumes: list[float] = []
    quote_volumes: list[float] = []
    taker_buy_base: list[float] = []
    trade_counts: list[int] = []

    for row in rows:
        if len(row) != columns:
            raise ArchiveFormatError(
                f"ragged kline row: expected {columns} fields, got {len(row)}"
            )
        if detect_timestamp_unit(row[COL_OPEN_TIME]) != unit:
            raise ArchiveFormatError(
                f"epoch unit changes inside a single file at {row[COL_OPEN_TIME]!r} "
                f"(file opened in {unit})"
            )
        # tz=timezone.utc then strip, NOT tz=None: the naked form reads the epoch in the
        # machine's local zone, so the same archive would parse differently in London and
        # in New York and the fixture would depend on who ran the fetch.
        timestamp = datetime.fromtimestamp(
            int(row[COL_OPEN_TIME]) / divisor, tz=timezone.utc
        ).replace(tzinfo=None)
        bars.append(
            TimestampedBar(
                timestamp=timestamp,
                bar=Bar(
                    open=float(row[COL_OPEN]),
                    high=float(row[COL_HIGH]),
                    low=float(row[COL_LOW]),
                    close=float(row[COL_CLOSE]),
                ),
            )
        )
        base_volumes.append(float(row[COL_VOLUME_BASE]))
        quote_volumes.append(float(row[COL_QUOTE_VOLUME]))
        taker_buy_base.append(float(row[COL_TAKER_BUY_BASE]))
        trade_counts.append(int(row[COL_TRADES]))

    return KlineFile(
        bars=bars,
        base_volumes=base_volumes,
        quote_volumes=quote_volumes,
        taker_buy_base=taker_buy_base,
        trade_counts=trade_counts,
        timestamp_unit=unit,
        had_header=had_header,
        columns=columns,
    )


def assert_on_grid(bars: list[TimestampedBar], minutes: int) -> None:
    """Raise unless every bar sits on the `minutes`-minute UTC grid.

    Same guard as `scripts/fetch_crypto_intraday.py`, for the same reason: D161's
    resampling contract is only exact if buckets anchor to 00:00 UTC, and a silently
    mis-bucketed bar is indistinguishable from a correct one downstream.
    """
    residuals = sorted({tb.timestamp.minute % minutes for tb in bars} - {0})
    if residuals:
        raise ArchiveFormatError(
            f"bars off the {minutes}-minute grid (residual minutes {residuals})"
        )
    if any(tb.timestamp.second or tb.timestamp.microsecond for tb in bars):
        raise ArchiveFormatError("sub-minute components in bar timestamps")


@dataclass(frozen=True)
class OffGridCensus:
    """UTC days whose bars do not sit on the interval grid, and by how much.

    Found by running this against the real archive: from **2017-12-04 06:00:20.799 to
    2017-12-18 10:00:20.799**, every `BTCUSDT` 1m bar is stamped exactly 20.799 seconds
    past the minute — 20,401 bars across 15 days, a constant offset rather than jitter.
    `ETHUSDT` carries 20.810s over the same window. Binance's kline generator was running
    on a skewed clock for a fortnight, through the December 2017 top.

    Reported as data rather than raised on, because the caller decides. Snapping the
    timestamps to the grid is not an option: the OHLC of a bar labelled 00:00:20.799
    could belong to `[00:00, 00:01)` or to `[00:00:20.8, 00:01:20.8)` and nothing in the
    archive says which. Rewriting it would be inventing the answer, which is the sin
    `clean-v1` avoids by dropping and reporting instead of correcting (D25).
    """

    minutes: int
    bars_by_day: dict[date, int] = field(default_factory=dict)
    residual_seconds: tuple[float, ...] = ()

    @property
    def days(self) -> list[date]:
        return sorted(self.bars_by_day)

    @property
    def bars(self) -> int:
        return sum(self.bars_by_day.values())

    def to_meta(self) -> dict:
        return {
            "minutes": self.minutes,
            "days": len(self.bars_by_day),
            "bars": self.bars,
            "first_day": self.days[0].isoformat() if self.bars_by_day else None,
            "last_day": self.days[-1].isoformat() if self.bars_by_day else None,
            "residual_seconds": list(self.residual_seconds),
        }


def offgrid_census(bars: list[TimestampedBar], minutes: int) -> OffGridCensus:
    """Which UTC days hold bars off the `minutes`-minute grid, and the offsets seen.

    The day is the unit because that is the unit D161's drop policy works in, and because
    the real occurrence spans whole days rather than scattered bars.
    """
    by_day: dict[date, int] = {}
    residuals: set[float] = set()
    for tb in bars:
        offset = (
            (tb.timestamp.minute % minutes) * 60
            + tb.timestamp.second
            + tb.timestamp.microsecond / 1e6
        )
        if offset:
            day = tb.timestamp.date()
            by_day[day] = by_day.get(day, 0) + 1
            residuals.add(round(offset, 6))
    return OffGridCensus(
        minutes=minutes,
        bars_by_day=by_day,
        residual_seconds=tuple(sorted(residuals)),
    )


def dedupe_seam(
    bars: list[TimestampedBar], volumes: list[float]
) -> tuple[list[TimestampedBar], list[float], int]:
    """Drop duplicate timestamps at monthly-archive seams, keeping the first occurrence.

    Concatenating monthly archives is exactly the failure mode `align_bars` raises on
    (D99) and `validate-v1` counts as a hard `duplicate_timestamp` violation. Returns the
    number dropped so the count reaches the report rather than vanishing.
    """
    if len(bars) != len(volumes):
        raise ArchiveFormatError(
            f"bars ({len(bars)}) and volumes ({len(volumes)}) are not aligned"
        )
    seen: set[datetime] = set()
    kept_bars: list[TimestampedBar] = []
    kept_volumes: list[float] = []
    for bar, volume in zip(bars, volumes):
        if bar.timestamp in seen:
            continue
        seen.add(bar.timestamp)
        kept_bars.append(bar)
        kept_volumes.append(volume)
    return kept_bars, kept_volumes, len(bars) - len(kept_bars)


def volume_census(base_volumes: list[float], trade_counts: list[int]) -> VolumeCensus:
    """Count zero-volume bars, zero-trade bars, and the overlap between them."""
    both = sum(1 for v, n in zip(base_volumes, trade_counts) if v == 0.0 and n == 0)
    return VolumeCensus(
        bars=len(base_volumes),
        zero_volume=sum(1 for v in base_volumes if v == 0.0),
        zero_trades=sum(1 for n in trade_counts if n == 0),
        zero_volume_and_zero_trades=both,
    )


@dataclass(frozen=True)
class DailyBar:
    """A UTC-day aggregate of intraday bars, for cross-provider reconciliation only."""

    day: date
    open: float
    high: float
    low: float
    close: float
    base_volume: float


def resample_to_daily(
    bars: list[TimestampedBar], base_volumes: list[float]
) -> list[DailyBar]:
    """Aggregate intraday bars into UTC calendar days.

    Deliberately simpler than `research.breakout_intraday.resample`, and not a substitute
    for it: this exists to compare a Binance day's close against the committed daily
    fixture's, not to feed a study. Partial days are aggregated as they arrive and are
    identified by `bars_by_day` in the caller rather than dropped here.
    """
    if len(bars) != len(base_volumes):
        raise ArchiveFormatError(
            f"bars ({len(bars)}) and volumes ({len(base_volumes)}) are not aligned"
        )
    buckets: dict[date, list[float]] = {}
    for tb, volume in zip(bars, base_volumes):
        day = tb.timestamp.date()
        acc = buckets.get(day)
        if acc is None:
            buckets[day] = [
                tb.bar.open,
                tb.bar.high,
                tb.bar.low,
                tb.bar.close,
                volume,
            ]
        else:
            acc[1] = max(acc[1], tb.bar.high)
            acc[2] = min(acc[2], tb.bar.low)
            acc[3] = tb.bar.close
            acc[4] += volume
    return [
        DailyBar(day=day, open=a[0], high=a[1], low=a[2], close=a[3], base_volume=a[4])
        for day, a in sorted(buckets.items())
    ]


def gap_census(bars: list[TimestampedBar], minutes: int) -> dict[str, int]:
    """Histogram of inter-bar gaps that are not exactly one step, in minutes.

    Reported, never patched — a gap is a fact about the provider (D160/D161).
    """
    step = timedelta(minutes=minutes)
    gaps: Counter[int] = Counter()
    for a, b in zip(bars, bars[1:]):
        delta = b.timestamp - a.timestamp
        if delta != step:
            gaps[int(delta.total_seconds() // 60)] += 1
    return {str(k): v for k, v in sorted(gaps.items())}


def month_sequence(first: str, last: str) -> list[str]:
    """Every `YYYY-MM` from `first` to `last` inclusive.

    Used to tell a *listing* gap (a month the provider never published, which is a
    delisting or an outage) from a gap *inside* a month's bars.
    """
    start_year, start_month = (int(p) for p in first.split("-"))
    end_year, end_month = (int(p) for p in last.split("-"))
    out: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            year, month = year + 1, 1
    return out


@dataclass(frozen=True)
class SymbolCoverage:
    """What the archive holds for one symbol at one interval."""

    symbol: str
    months: list[str] = field(default_factory=list)
    total_bytes: int = 0
    checksum_count: int = 0

    @property
    def available(self) -> bool:
        return bool(self.months)

    @property
    def first_month(self) -> str | None:
        return self.months[0] if self.months else None

    @property
    def last_month(self) -> str | None:
        return self.months[-1] if self.months else None

    @property
    def missing_months(self) -> list[str]:
        """Months inside the symbol's own span that the provider did not publish."""
        if not self.months:
            return []
        held = set(self.months)
        return [
            m
            for m in month_sequence(self.months[0], self.months[-1])
            if m not in held
        ]

    @property
    def checksum_coverage(self) -> float:
        """Fraction of archives with a published SHA256 sidecar.

        The manifest-only storage policy rests on this being 1.0: the committed record of
        the data is the provider's own hash, which is independently verifiable and cannot
        be regenerated by us.
        """
        return self.checksum_count / len(self.months) if self.months else 0.0


def coverage_from_listing(symbol: str, listing: Listing) -> SymbolCoverage:
    """Fold a listing into a per-symbol coverage record."""
    archives = listing.archives
    months = sorted(m for m in (e.month for e in archives) if m is not None)
    return SymbolCoverage(
        symbol=symbol,
        months=months,
        total_bytes=sum(e.size for e in archives),
        checksum_count=len(listing.checksums),
    )
