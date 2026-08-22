"""CSV fixture save/load: the pre-Step-7 stand-in for a frozen data snapshot (D70).

A fixture is a plain CSV (timestamp, symbol, open, high, low, close, volume)
committed to git — immutable the way a snapshot needs to be (D24's requirement)
because changing it is a visible diff, not a silent re-fetch. A sidecar
`<name>.meta.json` records how and when it was fetched. Step 7's SnapshotStore
(checksummed IDs, quarantine gate, cleaning reports) replaces this; until then the
fixture filename serves as the snapshot_id logged with every trial.

The volume column is stored for Step 7's future ADV work but ignored on load —
TimestampedBar carries no volume field (D59/D60), and inventing one here would be a
false affordance (D48).
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


def _open_text(path: Path, mode: str):
    """Transparent gzip (D88): a '.gz' suffix means the fixture is compressed —
    the 57-ETF universe fixture is ~17MB raw, ~2.5MB gzipped, and the repo commits
    the compressed form. Everything else about the format is identical.

    **Writes pin the gzip header's mtime to 0 and omit the embedded filename**, so the
    same content always produces the same bytes. `gzip.open` stamps the current time into
    the header, which meant re-running a fetch produced a whole-file diff even when not
    one row had changed — and a diff that always appears is a diff that stops being read.
    The whole point of committing a fixture is that changing it is visible (D70/D24), so
    the compressed form has to be a function of the content and nothing else.

    Reads are unaffected, and every fixture already committed still loads unchanged; the
    header field is metadata the decompressor ignores. Snapshot ids are also unaffected —
    `SnapshotStore` writes `bars.csv` uncompressed, so this never enters `_hash_payload`.
    """
    if path.suffix == ".gz":
        if "w" in mode:
            raw = open(path, mode + "b")
            binary = gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0)
            return io.TextIOWrapper(binary, encoding="utf-8", newline="")
        return gzip.open(path, mode + "t", encoding="utf-8", newline="")
    return open(path, mode, encoding="utf-8", newline="")


def save_fixture_csv(
    path: str | Path,
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
    extra_columns: Mapping[str, Mapping[str, Sequence[float]]] | None = None,
) -> None:
    """Write a fixture. `extra_columns` is `{column name: {symbol: series}}`.

    **`extra_columns=None` must stay byte-identical to the seven-column form.** This
    writer is also how `SnapshotStore.create` lays down `bars.csv`, and `_hash_payload`
    hashes those bytes — so a change here that touched the default path would silently
    renumber every snapshot id in the project, and snapshot ids are logged with every
    trial and printed in results docs. The extension is opt-in for exactly that reason,
    and `test_csv_fixture.py` pins the equality rather than trusting this comment.

    Extra columns exist because a provider can report more than one volume (D190: Binance
    klines carry base volume, quote volume and taker-buy volume as separate named fields).
    Deriving one from another is what D187 did wrong; carrying them side by side is the
    fix. Column order is `sorted()` so the bytes do not depend on dict insertion order.
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

    Deliberately `[:7]` rather than an exact match, which is what lets a fixture carry
    additional provider columns without every reader in the project needing to know.
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
    the bar lists after sorting). Added for the cleaner/validator (D25/D26), which
    need volumes; TimestampedBar itself still carries none (D48/D60).

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
    """Bars only — delegates to the full loader and drops volumes (audit F21: the
    two loaders used to duplicate the whole parse loop)."""
    bars_by_symbol, _ = load_fixture_csv_with_volumes(path)
    return bars_by_symbol
