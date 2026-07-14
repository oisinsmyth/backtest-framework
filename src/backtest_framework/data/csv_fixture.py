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
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

from ..simulator.fills import Bar
from .bars import TimestampedBar

_COLUMNS = ["timestamp", "symbol", "open", "high", "low", "close", "volume"]


def save_fixture_csv(
    path: str | Path,
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(_COLUMNS)
        for symbol in sorted(bars_by_symbol):
            series = bars_by_symbol[symbol]
            volumes = volumes_by_symbol.get(symbol) if volumes_by_symbol else None
            for i, tb in enumerate(series):
                volume = volumes[i] if volumes is not None else ""
                writer.writerow(
                    [tb.timestamp.isoformat(), symbol, tb.bar.open, tb.bar.high, tb.bar.low, tb.bar.close, volume]
                )


def load_fixture_csv_with_volumes(
    path: str | Path,
) -> tuple[dict[str, list[TimestampedBar]], dict[str, list[float]]]:
    """Like load_fixture_csv, but also returns per-symbol volume series (aligned with
    the bar lists after sorting). Added for the cleaner/validator (D25/D26), which
    need volumes; TimestampedBar itself still carries none (D48/D60)."""
    rows_by_symbol: dict[str, list[tuple[TimestampedBar, float]]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or reader.fieldnames[: len(_COLUMNS)] != _COLUMNS:
            raise ValueError(
                f"fixture {path} does not have the expected columns {_COLUMNS}, got {reader.fieldnames}"
            )
        for row in reader:
            tb = TimestampedBar(
                timestamp=datetime.fromisoformat(row["timestamp"]).replace(tzinfo=None),
                bar=Bar(
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                ),
            )
            volume = float(row["volume"]) if row.get("volume") not in (None, "") else float("nan")
            rows_by_symbol.setdefault(row["symbol"], []).append((tb, volume))
    bars_by_symbol: dict[str, list[TimestampedBar]] = {}
    volumes_by_symbol: dict[str, list[float]] = {}
    for symbol, rows in rows_by_symbol.items():
        rows.sort(key=lambda pair: pair[0].timestamp)
        bars_by_symbol[symbol] = [tb for tb, _ in rows]
        volumes_by_symbol[symbol] = [volume for _, volume in rows]
    return bars_by_symbol, volumes_by_symbol


def load_fixture_csv(path: str | Path) -> dict[str, list[TimestampedBar]]:
    bars_by_symbol: dict[str, list[TimestampedBar]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or reader.fieldnames[: len(_COLUMNS)] != _COLUMNS:
            raise ValueError(
                f"fixture {path} does not have the expected columns {_COLUMNS}, got {reader.fieldnames}"
            )
        for row in reader:
            tb = TimestampedBar(
                timestamp=datetime.fromisoformat(row["timestamp"]).replace(tzinfo=None),
                bar=Bar(
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                ),
            )
            bars_by_symbol.setdefault(row["symbol"], []).append(tb)
    for series in bars_by_symbol.values():
        series.sort(key=lambda tb: tb.timestamp)
    return bars_by_symbol
