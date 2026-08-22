"""BinanceDataSource: monthly flat-file archives assembled into a continuous series (D190).

The network half of `binance_archive.py`, which stays pure. Same split as
`_bars_from_dataframe` / `EquityDataSource` (D59), for the same reason: the conversion is
the part that can be wrong in a way that matters, so it must be testable offline.

## The seam this conforms to

`get_raw_history(symbol, start, end, timeframe) -> (bars, volumes, dividends, splits)` —
the method every fetch script in this project actually calls. NOT the `DataSource`
protocol in `source.py`, which returns bars without volumes, takes an `Instrument`, and is
referenced nowhere in `src`.

## Three things this class refuses to do

**It never adjusts prices.** Binance publishes a true as-traded frame: no split
adjustment, no dividend adjustment, and spot crypto has neither event to adjust for. That
is a different frame from yfinance's `auto_adjust=False` output, which is already
split-adjusted (D75). `corporate_actions.as_traded_from_adjusted` must never be applied to
anything this returns — it would rescale prices by any split ratio it was handed.

**It never derives one volume from another.** `get_raw_history` returns quote volume, the
convention every crypto fixture in this project uses. Base volume and taker-buy volume
come from `get_volume_columns` as separate series in the provider's own units. Deriving
one from the other is exactly what D187 got wrong.

**It never proceeds past a checksum mismatch.** D191's storage policy rests on the claim
that a hash the provider published is a stronger guarantee than bytes we committed. That
is only true if a mismatch stops the run, so it raises.
"""

from __future__ import annotations

import hashlib
import io
import time
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .bars import TimestampedBar
from .binance_archive import (
    DOWNLOAD_BASE,
    LISTING_BASE,
    ArchiveFormatError,
    KlineFile,
    Listing,
    OffGridCensus,
    coverage_from_listing,
    dedupe_seam,
    offgrid_census,
    month_sequence,
    parse_klines,
    parse_listing,
)

INTERVAL_MINUTES: dict[str, int] = {
    "1m": 1,
    "3m": 3,
    "5m": 5,
    "15m": 15,
    "30m": 30,
    "1h": 60,
}
"""Intervals this source will assemble. Deliberately short: the project's own resampling
contract (D161) builds coarser rungs from one base rather than fetching each natively,
so a long list here would be a second way to do the same thing."""

REQUEST_PAUSE = 0.5
DEFAULT_ATTEMPTS = 2


class ChecksumMismatch(Exception):
    """A downloaded archive does not match the SHA256 the provider published.

    Never a warning. Either the download is corrupt or the provider rewrote history, and
    both need a human before any number is computed from the bytes (D191).
    """


@dataclass(frozen=True)
class ArchiveRecord:
    """One archive as the manifest records it."""

    key: str
    month: str
    sha256: str
    size: int

    def to_json(self) -> dict:
        return {"key": self.key, "month": self.month, "sha256": self.sha256, "size": self.size}


@dataclass
class FetchReport:
    """What assembling a series cost, so none of it is silent."""

    symbol: str
    interval: str
    months: list[str] = field(default_factory=list)
    records: list[ArchiveRecord] = field(default_factory=list)
    seam_duplicates_dropped: int = 0
    bars: int = 0
    cache_hits: int = 0
    downloads: int = 0
    offgrid: OffGridCensus | None = None
    """Days whose bars are off the interval grid. Reported, never raised on here — the
    caller decides, because dropping them is a policy and this class is a fetcher."""

    def to_meta(self) -> dict:
        return {
            "symbol": self.symbol,
            "interval": self.interval,
            "months": len(self.months),
            "first_month": self.months[0] if self.months else None,
            "last_month": self.months[-1] if self.months else None,
            "bars": self.bars,
            "seam_duplicates_dropped": self.seam_duplicates_dropped,
            "cache_hits": self.cache_hits,
            "downloads": self.downloads,
            "offgrid": self.offgrid.to_meta() if self.offgrid else None,
        }


class BinanceDataSource:
    """Assembles Binance monthly kline archives into one continuous series.

    `cache_root` defaults to `data/raw/`, which is gitignored — the raw archives are the
    bytes D191 declines to commit, and caching them is what makes a re-run offline.
    """

    def __init__(
        self,
        cache_root: str | Path | None = None,
        market: str = "spot",
        opener=urllib.request.urlopen,
        pause: float = REQUEST_PAUSE,
    ) -> None:
        if market not in ("spot", "futures/um"):
            raise ValueError(f"market must be 'spot' or 'futures/um', got {market!r}")
        repo = Path(__file__).resolve().parents[3]
        self.cache_root = Path(cache_root) if cache_root else repo / "data" / "raw" / "binance"
        self.market = market
        self._opener = opener
        self._pause = pause

    # ------------------------------------------------------------------ paths

    def klines_prefix(self, symbol: str, interval: str) -> str:
        return f"data/{self.market}/monthly/klines/{symbol}/{interval}/"

    def archive_key(self, symbol: str, interval: str, month: str) -> str:
        return f"{self.klines_prefix(symbol, interval)}{symbol}-{interval}-{month}.zip"

    # ------------------------------------------------------------------ network

    def _get(self, url: str, attempts: int = DEFAULT_ATTEMPTS) -> bytes:
        last: Exception | None = None
        for attempt in range(1, attempts + 1):
            try:
                with self._opener(url, timeout=120) as response:  # noqa: S310
                    body: bytes = response.read()
                    return body
            except Exception as exc:  # noqa: BLE001 — retried, then re-raised with context
                last = exc
                if attempt < attempts:
                    time.sleep(2.0)
        raise RuntimeError(f"fetching {url} failed: {type(last).__name__}: {last}")

    def list_months(self, symbol: str, interval: str) -> list[str]:
        """Every month the archive publishes for this symbol, following pagination.

        A listing that silently stops at 1000 keys looks exactly like a symbol with 1000
        months of history, so `IsTruncated` is followed rather than assumed false.
        """
        prefix = self.klines_prefix(symbol, interval)
        entries = []
        marker: str | None = None
        while True:
            url = f"{LISTING_BASE}?delimiter=/&prefix={prefix}"
            if marker:
                url += f"&marker={marker}"
            page = parse_listing(self._get(url).decode("utf-8"))
            entries.extend(page.entries)
            if not page.is_truncated or not page.next_marker:
                break
            marker = page.next_marker
            time.sleep(self._pause)
        return coverage_from_listing(symbol, Listing(entries, False, None)).months

    def _cache_path(self, key: str) -> Path:
        return self.cache_root / key

    def fetch_archive(self, key: str) -> tuple[bytes, str, bool]:
        """Return (zip bytes, published sha256, was_cached), verifying the hash.

        The checksum is fetched from the provider even on a cache hit. That is the point:
        a cached archive whose published hash has since changed is precisely the event
        D191's manifest exists to detect, and skipping the check to save a request would
        remove the guarantee the policy is built on.
        """
        cached = self._cache_path(key)
        published = self._get(f"{DOWNLOAD_BASE}/{key}.CHECKSUM").decode().split()[0]

        if cached.is_file():
            payload = cached.read_bytes()
            was_cached = True
        else:
            payload = self._get(f"{DOWNLOAD_BASE}/{key}")
            was_cached = False

        actual = hashlib.sha256(payload).hexdigest()
        if actual != published:
            raise ChecksumMismatch(
                f"{key} hashes to {actual} but the provider publishes {published} — "
                f"{'the cached copy is stale or corrupt' if was_cached else 'the download is corrupt'}. "
                "Refusing to parse it (D191)."
            )

        if not was_cached:
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_bytes(payload)
        return payload, published, was_cached

    # ------------------------------------------------------------------ parsing

    @staticmethod
    def _unzip(key: str, payload: bytes) -> str:
        archive = zipfile.ZipFile(io.BytesIO(payload))
        names = archive.namelist()
        if len(names) != 1:
            raise ArchiveFormatError(f"{key} holds {len(names)} members, expected 1")
        return archive.read(names[0]).decode("utf-8")

    def months_for(self, symbol: str, interval: str, start: date, end: date) -> list[str]:
        """The published months that overlap [start, end].

        Partial first and last months are included whole; trimming to the exact date
        range happens after parsing, because a month is the unit the provider ships.
        """
        available = set(self.list_months(symbol, interval))
        wanted = month_sequence(f"{start:%Y-%m}", f"{end:%Y-%m}")
        return [m for m in wanted if m in available]

    def load_months(
        self, symbol: str, interval: str, months: list[str]
    ) -> tuple[list[KlineFile], FetchReport]:
        report = FetchReport(symbol=symbol, interval=interval, months=list(months))
        files: list[KlineFile] = []
        for month in months:
            key = self.archive_key(symbol, interval, month)
            payload, published, was_cached = self.fetch_archive(key)
            report.records.append(
                ArchiveRecord(key=key, month=month, sha256=published, size=len(payload))
            )
            report.cache_hits += int(was_cached)
            report.downloads += int(not was_cached)
            files.append(parse_klines(self._unzip(key, payload)))
            if not was_cached:
                time.sleep(self._pause)
        return files, report

    # ------------------------------------------------------------------ the seam

    def get_raw_history(
        self, symbol: str, start: date, end: date, timeframe: str = "1m"
    ) -> tuple[list[TimestampedBar], list[float], list[tuple], list[tuple]]:
        """The seam every fetch script calls. Volume returned is QUOTE volume.

        Quote notional is the convention every crypto fixture in this project uses, it is
        what `CostTier.volume_units` defaults to, and it is what D189's S1 sensor ran on.
        Base and taker-buy volume are available from `get_volume_columns`.

        Dividends and splits are always empty. Spot crypto has neither, and an empty
        events sidecar written from this must not be a lie (D48/D108) — it is true by
        construction here rather than by luck.
        """
        bars, columns, _ = self.get_volume_columns(symbol, start, end, timeframe)
        return bars, columns["quote_volume"], [], []

    def get_volume_columns(
        self, symbol: str, start: date, end: date, timeframe: str = "1m"
    ) -> tuple[list[TimestampedBar], dict[str, list[float]], FetchReport]:
        """Bars plus every volume column the provider states, index-aligned.

        Returns `(bars, {"quote_volume", "base_volume", "taker_buy_base", "trades"},
        report)`. The three volume columns are carried rather than derived, because
        deriving one from another by way of price is the D187 defect.

        `trades` is here because it is the only independent check on a zero-volume bar.
        D192's criterion is that zero volume is droppable only where it DISAGREES with the
        trade count — a bar with no volume and no trades is a true empty minute, a bar
        with no volume and some trades is a feed defect. Inferring trades from volume
        would make that test answer itself.
        """
        if timeframe not in INTERVAL_MINUTES:
            raise ValueError(
                f"timeframe {timeframe!r} not in {sorted(INTERVAL_MINUTES)} — coarser bars are "
                "built by resampling one base under D161's contract, not fetched natively"
            )
        if start > end:
            raise ValueError(f"start {start} is after end {end}")

        months = self.months_for(symbol, timeframe, start, end)
        if not months:
            raise ArchiveFormatError(
                f"the archive publishes no {timeframe} months for {symbol} between "
                f"{start} and {end}"
            )
        files, report = self.load_months(symbol, timeframe, months)

        bars: list[TimestampedBar] = []
        quote: list[float] = []
        base: list[float] = []
        taker: list[float] = []
        trades: list[float] = []
        for kline in files:
            bars.extend(kline.bars)
            quote.extend(kline.quote_volumes)
            base.extend(kline.base_volumes)
            taker.extend(kline.taker_buy_base)
            trades.extend(float(n) for n in kline.trade_counts)

        # Monthly archives are concatenated here, which is precisely the duplicate the
        # validator counts as a hard violation (D99) and align_bars raises on. Deduped
        # once, against the primary column, and the other two are re-indexed by the
        # positions that survived so all three stay aligned.
        keep = _first_occurrence_positions([tb.timestamp for tb in bars])
        report.seam_duplicates_dropped = len(bars) - len(keep)
        bars = [bars[i] for i in keep]
        columns = {
            "quote_volume": [quote[i] for i in keep],
            "base_volume": [base[i] for i in keep],
            "taker_buy_base": [taker[i] for i in keep],
            "trades": [trades[i] for i in keep],
        }

        # Trim to the requested calendar range; months arrive whole.
        inside = [i for i, tb in enumerate(bars) if start <= tb.timestamp.date() <= end]
        bars = [bars[i] for i in inside]
        columns = {name: [series[i] for i in inside] for name, series in columns.items()}

        report.bars = len(bars)
        report.offgrid = offgrid_census(bars, INTERVAL_MINUTES[timeframe])
        return bars, columns, report


def _first_occurrence_positions(timestamps: list) -> list[int]:
    """Indices of the first occurrence of each timestamp, order preserved.

    `dedupe_seam` in `binance_archive.py` does this for one bar/volume pair; three
    aligned columns need the surviving positions rather than one filtered pair, so this
    computes them once and the caller applies them. The two are pinned to agree by
    `test_binance_source.py`.
    """
    seen: set = set()
    keep: list[int] = []
    for i, ts in enumerate(timestamps):
        if ts in seen:
            continue
        seen.add(ts)
        keep.append(i)
    return keep


__all__ = [
    "ArchiveRecord",
    "BinanceDataSource",
    "ChecksumMismatch",
    "FetchReport",
    "INTERVAL_MINUTES",
    "dedupe_seam",
]
