"""CSV fixture save/load: a lightweight frozen data set.

A fixture is a plain CSV (timestamp, symbol, open, high, low, close, volume)
committed to git, immutable the way a snapshot needs to be because changing it is a
visible diff, not a silent re-fetch. A sidecar `<name>.meta.json` records how and when
it was fetched. SnapshotStore (checksummed IDs, quarantine gate, cleaning reports) is
the fuller mechanism and uses this writer for its `bars.csv`; a bare fixture's filename
can serve as the snapshot_id logged with a trial.

`load_fixture_csv` ignores the volume column, since TimestampedBar carries no volume
field; `load_fixture_csv_with_volumes` returns it separately.
"""

from __future__ import annotations

import csv
import gzip
import io
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

from ..simulator.fills import Bar
from .bars import TimestampedBar

_COLUMNS = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]


class _ClosingTextIOWrapper(io.TextIOWrapper):
    """A TextIOWrapper that also closes a file object it did not open.

    The gzip write path is a three-layer stack — raw file, GzipFile, text wrapper — and only
    the middle layer is owned by the one above it. Without this, `with _open_text(...)`
    would close two of the three and leave the raw handle to the garbage collector.
    """

    def __init__(self, buffer, raw, **kwargs):
        super().__init__(buffer, **kwargs)
        self._raw_file = raw

    def close(self) -> None:
        try:
            super().close()
        finally:
            self._raw_file.close()


def _open_text(path: Path, mode: str):
    """Transparent gzip: a '.gz' suffix means the fixture is compressed (a large
    multi-symbol fixture compresses roughly 7x). Everything else about the format is
    identical.

    Writes pin the gzip header's mtime to 0 and omit the embedded filename, so the same
    content always produces the same bytes. `gzip.open` stamps the current time into the
    header, so re-running a fetch would produce a whole-file diff even when no row had
    changed. Committing a fixture is meant to make changes visible, so the compressed
    form has to be a function of the content and nothing else.

    Reads are unaffected; the header field is metadata the decompressor ignores. Snapshot
    ids are also unaffected: `SnapshotStore` writes `bars.csv` uncompressed, so this never
    enters `_hash_payload`.
    """
    if path.suffix == ".gz":
        if "w" in mode:
            raw = open(path, mode + "b")
            # `GzipFile` closes the underlying file only when it opened it itself. Here it
            # does not (an explicit `fileobj=raw` is what lets `mtime=0` be pinned), so a
            # plain wrapper would close the GzipFile and leave `raw` open until garbage
            # collection. `_ClosingTextIOWrapper` closes `raw` too, so the handle's lifetime
            # matches the caller's `with` block on every interpreter and platform.
            try:
                binary = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
                return _ClosingTextIOWrapper(binary, raw, encoding="utf-8", newline="")
            except Exception:
                raw.close()
                raise
        return gzip.open(path, mode + "t", encoding="utf-8", newline="")
    return open(path, mode, encoding="utf-8", newline="")


def save_fixture_csv(
    path: str | Path,
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
    extra_columns: Mapping[str, Mapping[str, Sequence[float]]] | None = None,
) -> None:
    """Write a fixture. `extra_columns` is `{column name: {symbol: series}}`.

    `extra_columns=None` must stay byte-identical to the seven-column form. This writer
    is also how `SnapshotStore.create` lays down `bars.csv`, and `_hash_payload` hashes
    those bytes, so a change to the default path would silently change every snapshot id,
    and snapshot ids are logged with every trial. The extension is opt-in for that reason,
    and `tests/unit/test_csv_fixture.py` checks the equality.

    Extra columns exist because a provider can report more than one volume (Binance klines
    carry base volume, quote volume and taker-buy volume as separate named fields).
    Carrying them side by side avoids deriving one from another with the wrong units.
    Column order is `sorted()` so the bytes do not depend on dict insertion order.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    extra_names = sorted(extra_columns) if extra_columns else []
    with _open_text(path, "w") as f:
        writer = csv.writer(f)
        writer.writerow(_COLUMNS + extra_names)
        for symbol in sorted(bars_by_symbol):
            series = bars_by_symbol[symbol]
            volumes = volumes_by_symbol.get(symbol) if volumes_by_symbol else None
            if volumes is not None and len(volumes) != len(series):
                # Refuse rather than truncate. The loop below reads `volumes[i]` for each
                # bar, so a longer volume series would be silently cut to len(series) with
                # its first N entries kept, preserving the wrong alignment when the extra
                # entries are at the front or middle while making the lengths agree.
                #
                # The common cause: `clean()` drops bars and does not re-index volumes, so a
                # caller who passes the raw list onward is misaligned from the first drop.
                raise ValueError(
                    f"{symbol!r} has {len(volumes)} volumes against {len(series)} bars. This "
                    "writer used to truncate to the bar count, which hides a misalignment "
                    "instead of reporting one. If the bars were cleaned, realign with "
                    "`CleaningReport.realign(symbol, volumes)` rather than passing the "
                    "original series (see D541)."
                )
            extras = [
                (extra_columns or {}).get(name, {}).get(symbol) for name in extra_names
            ]
            for i, tb in enumerate(series):
                volume = volumes[i] if volumes is not None else ""
                row = [
                    tb.timestamp.isoformat(),
                    symbol,
                    tb.bar.open,
                    tb.bar.high,
                    tb.bar.low,
                    tb.bar.close,
                    volume,
                ]
                row.extend(
                    series_i[i] if series_i is not None and i < len(series_i) else ""
                    for series_i in extras
                )
                writer.writerow(row)


def _check_columns(path: Path, fieldnames: Sequence[str] | None) -> None:
    """The first seven columns are the contract; anything after them is optional extra.

    Deliberately `[:7]` rather than an exact match, which lets a fixture carry additional
    provider columns without every reader needing to know.
    """
    if fieldnames is None or list(fieldnames[: len(_COLUMNS)]) != _COLUMNS:
        raise ValueError(
            f"fixture {path} does not have the expected columns {_COLUMNS}, got {fieldnames}"
        )


def _to_float(cell: str | None) -> float:
    """An empty cell means "no value here", which is NaN — never zero.

    `engine/dataview.py` turns NaN into None precisely so a missing volume cannot be
    compared against; a zero would be a real observation and a false one.
    """
    return float(cell) if cell not in (None, "") else float("nan")


def _row_to_bar(row: Mapping[str, str]) -> tuple[TimestampedBar, float]:
    return (
        TimestampedBar(
            timestamp=datetime.fromisoformat(row["timestamp"]).replace(tzinfo=None),
            bar=Bar(
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
            ),
        ),
        _to_float(row.get("volume")),
    )


def load_fixture_csv_with_volumes(
    path: str | Path,
) -> tuple[dict[str, list[TimestampedBar]], dict[str, list[float]]]:
    """Like load_fixture_csv, but also returns per-symbol volume series (aligned with
    the bar lists after sorting), for the cleaner and validator, which need volumes;
    TimestampedBar itself carries none.

    Any columns beyond the standard seven are ignored here; `load_fixture_csv_with_extras`
    returns them."""
    bars_by_symbol, volumes_by_symbol, _ = load_fixture_csv_with_extras(path)
    return bars_by_symbol, volumes_by_symbol


def load_fixture_csv_with_extras(
    path: str | Path,
) -> tuple[
    dict[str, list[TimestampedBar]],
    dict[str, list[float]],
    dict[str, dict[str, list[float]]],
]:
    """Like `load_fixture_csv_with_volumes`, plus any columns beyond the standard seven.

    Returns `(bars, volumes, extras)` where `extras` is `{column: {symbol: series}}`, all
    index-aligned to the bar lists after sorting. A fixture with no extra columns returns
    an empty `extras` dict, so this is safe to call on any fixture in the repo.
    """
    path = Path(path)
    extra_names: list[str] = []
    rows_by_symbol: dict[str, list[tuple[TimestampedBar, float, list[float]]]] = {}
    with _open_text(path, "r") as f:
        reader = csv.DictReader(f)
        _check_columns(path, reader.fieldnames)
        extra_names = list((reader.fieldnames or [])[len(_COLUMNS) :])
        for row in reader:
            tb, volume = _row_to_bar(row)
            rows_by_symbol.setdefault(row["symbol"], []).append(
                (tb, volume, [_to_float(row.get(name)) for name in extra_names])
            )
    bars_by_symbol: dict[str, list[TimestampedBar]] = {}
    volumes_by_symbol: dict[str, list[float]] = {}
    extras: dict[str, dict[str, list[float]]] = {name: {} for name in extra_names}
    for symbol, rows in rows_by_symbol.items():
        rows.sort(key=lambda triple: triple[0].timestamp)
        bars_by_symbol[symbol] = [tb for tb, _, _ in rows]
        volumes_by_symbol[symbol] = [volume for _, volume, _ in rows]
        for j, name in enumerate(extra_names):
            extras[name][symbol] = [values[j] for _, _, values in rows]
    return bars_by_symbol, volumes_by_symbol, extras


def load_fixture_csv(path: str | Path) -> dict[str, list[TimestampedBar]]:
    """Bars only: delegates to the full loader and drops volumes."""
    bars_by_symbol, _ = load_fixture_csv_with_volumes(path)
    return bars_by_symbol
