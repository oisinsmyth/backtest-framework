"""Data cleaner (D25, D73): explicit, versioned rules; every change reported.

Silent cleaning makes "strategy result" indistinguishable from "cleaning artifact" —
so the contract is clean(data) -> (data, CleaningReport), and the report attaches to
the snapshot's metadata (D24). Ruleset clean-v1 is DROP-AND-REPORT ONLY: the cleaner
never rewrites a price. Fabricating values is D45's sin (forward-filled prices that
fills then execute against); dropping a bar is honest, and inner-join alignment
already handles the resulting hole correctly — carry spans the gap (D33/D63).

The cleaner runs on RAW prices, before any adjustment. Rule 4's discriminator is
permanence: a >40% single-bar move that REVERTS within a bar is a bad print; one that
sticks is real (a crash — or a raw split jump, which the validator explains via the
splits table rather than either of us "fixing" it).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .bars import TimestampedBar

RULESET_VERSION = "clean-v1"

OHLC_RELATIVE_TOLERANCE = 1e-9
"""low > high beyond this relative tolerance drops the bar; within it (e.g. the
observed 1.2e-16 yfinance adjustment artifact, XOP 2018-10-24) the bar passes and the
validator's identical tolerance owns the check (D74)."""

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

    def to_meta(self) -> dict:
        return {
            "ruleset": self.ruleset,
            "changes": [
                {"symbol": c.symbol, "timestamp": c.timestamp.isoformat(), "rule": c.rule, "detail": c.detail}
                for c in self.changes
            ],
        }


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

    for symbol, series in bars_by_symbol.items():
        volumes = volumes_by_symbol.get(symbol) if volumes_by_symbol else None
        kept: list[TimestampedBar] = []
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

            if volumes is not None and i < len(volumes) and not math.isnan(volumes[i]) and volumes[i] <= 0:
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
        cleaned[symbol] = kept

    return cleaned, CleaningReport(changes=tuple(changes))
