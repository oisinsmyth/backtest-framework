"""CSV fixture save/load: a lightweight frozen data set.

A fixture is a plain CSV (timestamp, symbol, open, high, low, close, volume)
committed to git, so any change to it shows up as a diff. A sidecar
`<name>.meta.json` records how and when it was fetched. SnapshotStore (checksummed
IDs, quarantine gate, cleaning reports) is the fuller mechanism and uses this writer
for its `bars.csv`; a bare fixture's filename can serve as the snapshot_id logged
with a trial.

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

    The gzip write path stacks a raw file, a GzipFile and a text wrapper. GzipFile does
    not close a file object it was handed, so this wrapper closes the raw file itself.
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
    """Open a fixture as text, gzip-compressed if the path ends in '.gz'.

    A large multi-symbol fixture compresses roughly 7x; the format is otherwise the same.
    Writes set the gzip header mtime to 0 and omit the embedded filename, so identical
    content gives identical bytes (`gzip.open` would stamp the current time). Reads
    ignore the header. Snapshot ids are unaffected: `SnapshotStore` writes `bars.csv`
    uncompressed, so this never reaches `_hash_payload`.
    """
    if path.suffix == ".gz":
        if "w" in mode:
            raw = open(path, mode + "b")
            # An explicit `fileobj=raw` is needed to set mtime=0, and GzipFile does not
            # close a fileobj it was given; `_ClosingTextIOWrapper` closes `raw` when the
            # caller's `with` block exits.
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

    With `extra_columns=None` the output must stay byte-identical to the seven-column
    form: `SnapshotStore.create` writes `bars.csv` with this function and `_hash_payload`
    hashes those bytes, so any change would alter every snapshot id.
    `tests/unit/test_csv_fixture.py` checks this.

    Extra columns hold additional provider fields, e.g. Binance klines report base,
    quote and taker-buy volume separately. They are written in `sorted()` order so the
    bytes do not depend on dict insertion order.

    Raises ValueError if a symbol's volumes and bars differ in length.
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
                # Truncating to len(series) would hide a misalignment. The usual cause is
                # passing raw volumes after `clean()` has dropped bars.
                raise ValueError(
                    f"{symbol!r} has {len(volumes)} volumes against {len(series)} bars. If the "
                    "bars were cleaned, realign the volumes with "
                    "`CleaningReport.realign(symbol, volumes)` first."
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
    """Raise ValueError unless the first seven columns are the standard ones.

    Further columns are allowed, so a fixture can carry extra provider fields.
    """
    if fieldnames is None or list(fieldnames[: len(_COLUMNS)]) != _COLUMNS:
        raise ValueError(
            f"fixture {path} does not have the expected columns {_COLUMNS}, got {fieldnames}"
        )


def _to_float(cell: str | None) -> float:
    """Parse a cell as float; an empty or missing cell is NaN, not zero.

    `engine/dataview.py` later maps NaN to None, so a missing volume is never read as a
    real zero.
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
    """Like load_fixture_csv, but also return per-symbol volumes aligned with the sorted bars.

    Used by the cleaner and validator; TimestampedBar has no volume field. Columns
    beyond the standard seven are ignored (see `load_fixture_csv_with_extras`)."""
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
    index-aligned to the bar lists after sorting. A fixture with no extra columns gives
    an empty `extras` dict.
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
    """Load a fixture's bars per symbol, sorted by timestamp, without volumes."""
    bars_by_symbol, _ = load_fixture_csv_with_volumes(path)
    return bars_by_symbol
