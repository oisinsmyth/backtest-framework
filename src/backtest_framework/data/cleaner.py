"""Data cleaner with explicit, versioned rules; every change is reported.

`clean(data)` returns `(data, CleaningReport)`, and the report is attached to the
snapshot's metadata so cleaning effects can be told apart from strategy results.
Ruleset clean-v1 only drops bars and never rewrites a price, since fills would execute
against a fabricated (e.g. forward-filled) price. Inner-join alignment handles the
resulting hole, and carry spans the gap.

The cleaner runs on raw prices, before any adjustment. A single-bar move of more than
40% that reverts on the next bar is a bad print; one that persists is kept (a crash,
or a raw split jump, which the validator explains from the splits table).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

from .bars import TimestampedBar

RULESET_VERSION = "clean-v1"

OHLC_RELATIVE_TOLERANCE = 1e-9
"""A bar with low > high beyond this relative tolerance is dropped. Within it (e.g. the
1.2e-16 yfinance adjustment artifact on XOP 2018-10-24) the bar is kept, and the
validator applies the same tolerance."""

SPIKE_THRESHOLD = 0.40
REVERT_THRESHOLD = 0.10


@dataclass(frozen=True)
class CleaningChange:
    symbol: str
    timestamp: datetime
    rule: str
    detail: str


@dataclass(frozen=True)
class CleaningReport:
    ruleset: str = RULESET_VERSION
    changes: tuple[CleaningChange, ...] = ()
    kept_indices: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    """Per symbol, the indices of the input series that survived cleaning.

    `clean()` returns bars only, so the caller's volume list no longer lines up with them
    after the first drop. Passed unchanged to `validate()` or `calibrate_impact_params()`,
    the misaligned volumes would feed ADV, `SqrtImpact` charges and P&L. Realign with

        volumes = [volumes[i] for i in report.kept_indices[symbol]]

    or with `realign()`.
    """

    def to_meta(self) -> dict:
        return {
            "ruleset": self.ruleset,
            "changes": [
                {"symbol": c.symbol, "timestamp": c.timestamp.isoformat(), "rule": c.rule, "detail": c.detail}
                for c in self.changes
            ],
        }

    def realign(self, symbol: str, values: Sequence[Any]) -> list[Any]:
        """Drop the same entries from a per-bar series that cleaning dropped from the bars.

        Raises KeyError if `symbol` has no cleaning record, and ValueError if the series is
        shorter than the cleaned input (it cannot be the series that was cleaned).
        """
        kept = self.kept_indices.get(symbol)
        if kept is None:
            raise KeyError(f"no cleaning record for {symbol!r}; realign needs the report that dropped its bars")
        if kept and max(kept) >= len(values):
            raise ValueError(
                f"{symbol!r}: series has {len(values)} entries but cleaning kept index "
                f"{max(kept)} of a longer input, so this is not the series that was cleaned"
            )
        return [values[i] for i in kept]


def _is_present(volume: float | None) -> bool:
    """True when this bar has a usable volume.

    Treats both gap representations as missing: NaN from the data layer
    (`csv_fixture._to_float`) and None from the engine layer
    (`engine/dataview.normalise_volumes`). `math.isnan` would raise TypeError on None.
    """
    return volume is not None and volume == volume


def _is_bad_print(prev_close: float, close: float, next_close: float) -> bool:
    spike = abs(close / prev_close - 1.0)
    revert = abs(next_close / prev_close - 1.0)
    return spike > SPIKE_THRESHOLD and revert < REVERT_THRESHOLD


def clean(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
) -> tuple[dict[str, list[TimestampedBar]], CleaningReport]:
    cleaned: dict[str, list[TimestampedBar]] = {}
    changes: list[CleaningChange] = []
    kept_indices: dict[str, tuple[int, ...]] = {}

    for symbol, series in bars_by_symbol.items():
        volumes = volumes_by_symbol.get(symbol) if volumes_by_symbol else None
        kept: list[TimestampedBar] = []
        kept_at: list[int] = []
        for i, tb in enumerate(series):
            bar = tb.bar
            values = (bar.open, bar.high, bar.low, bar.close)

            if any(not math.isfinite(v) for v in values):
                changes.append(CleaningChange(symbol, tb.timestamp, "non_finite_ohlc", f"OHLC={values}"))
                continue

            if bar.low - bar.high > OHLC_RELATIVE_TOLERANCE * abs(bar.high):
                changes.append(
                    CleaningChange(symbol, tb.timestamp, "low_above_high", f"low={bar.low} > high={bar.high}")
                )
                continue

            if volumes is not None and i < len(volumes) and _is_present(volumes[i]) and volumes[i] <= 0:
                changes.append(
                    CleaningChange(symbol, tb.timestamp, "non_positive_volume", f"volume={volumes[i]}")
                )
                continue

            if 0 < i < len(series) - 1:
                prev_close, next_close = series[i - 1].bar.close, series[i + 1].bar.close
                if prev_close > 0 and _is_bad_print(prev_close, bar.close, next_close):
                    changes.append(
                        CleaningChange(
                            symbol,
                            tb.timestamp,
                            "spike_and_revert",
                            f"close {prev_close} -> {bar.close} -> {next_close}",
                        )
                    )
                    continue

            kept.append(tb)
            kept_at.append(i)
        cleaned[symbol] = kept
        kept_indices[symbol] = tuple(kept_at)

    return cleaned, CleaningReport(changes=tuple(changes), kept_indices=kept_indices)
