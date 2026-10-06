"""Data validation: data failing a hard check is quarantined.

yfinance is a scraper and can serve bad prints without warning. The validator runs
at snapshot creation: a hard violation quarantines the whole snapshot (so
SnapshotStore.load raises), while warnings (e.g. volume anomalies) are recorded in the
snapshot's metadata without blocking.

The bar-to-bar move check accounts for splits: a raw series jumps ~4x on a
reverse-split ex-date (XOP, 2020-03-30, in the bundled fixture). After split
adjustment, an unexplained move of 25-60% is a warning and only >60% is hard (see
MOVE_HARD_THRESHOLD).

Cross-checking against a second data source is not implemented.
"""

from __future__ import annotations

import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from .bars import TimestampedBar
from .corporate_actions import CorporateActions

VALIDATOR_VERSION = "validate-v1"

OHLC_RELATIVE_TOLERANCE = 1e-9  # same tolerance the cleaner uses

MOVE_WARNING_THRESHOLD = 0.25
MOVE_HARD_THRESHOLD = 0.60
"""Calibrated on real data: on 2020-03-09 XOP moved −37% and XLE −20%, so a 25% hard
threshold would quarantine the COVID crash. Unexplained moves of 25–60% are warnings
(the cleaner has already dropped spikes that revert, so what remains is probably
real); only moves above 60%, beyond anything these ETFs showed even in 2020, are
hard."""

VOLUME_SPIKE_MULTIPLE = 10.0
VOLUME_MEDIAN_WINDOW = 20


@dataclass(frozen=True)
class Violation:
    symbol: str
    timestamp: datetime
    check: str
    detail: str
    hard: bool


@dataclass(frozen=True)
class ValidationResult:
    version: str = VALIDATOR_VERSION
    violations: tuple[Violation, ...] = ()

    @property
    def hard_violations(self) -> tuple[Violation, ...]:
        return tuple(v for v in self.violations if v.hard)

    @property
    def warnings(self) -> tuple[Violation, ...]:
        return tuple(v for v in self.violations if not v.hard)

    @property
    def passed(self) -> bool:
        return not self.hard_violations

    def to_meta(self) -> dict:
        return {
            "version": self.version,
            "passed": self.passed,
            "violations": [
                {
                    "symbol": v.symbol,
                    "timestamp": v.timestamp.isoformat(),
                    "check": v.check,
                    "detail": v.detail,
                    "hard": v.hard,
                }
                for v in self.violations
            ],
        }


def _is_present(volume: float | None) -> bool:
    """True when this bar has a usable volume.

    Treats both gap representations as missing: NaN from the data layer
    (`csv_fixture._to_float`) and None from the engine layer
    (`engine/dataview.normalise_volumes`). `math.isnan` would raise TypeError on None.
    """
    return volume is not None and volume == volume


def _split_ratio_on(symbol: str, timestamp: datetime, actions: CorporateActions) -> float | None:
    for ex_date, ratio in actions.splits_by_symbol.get(symbol, ()):
        if ex_date == timestamp:
            return ratio
    return None


def validate(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    actions: CorporateActions | None = None,
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
) -> ValidationResult:
    actions = actions or CorporateActions()
    violations: list[Violation] = []

    for symbol, series in bars_by_symbol.items():
        volumes = volumes_by_symbol.get(symbol) if volumes_by_symbol else None

        # Duplicate timestamps are hard: alignment keys bars by timestamp and would keep
        # only the last of them.
        timestamp_counts = Counter(tb.timestamp for tb in series)
        for ts, count in sorted(timestamp_counts.items()):
            if count > 1:
                violations.append(
                    Violation(symbol, ts, "duplicate_timestamp", f"{count} bars share this timestamp", hard=True)
                )

        for i, tb in enumerate(series):
            bar = tb.bar
            tol = OHLC_RELATIVE_TOLERANCE * abs(bar.high)

            if min(bar.open, bar.high, bar.low, bar.close) <= 0:
                violations.append(
                    Violation(symbol, tb.timestamp, "non_positive_price", f"OHLC={(bar.open, bar.high, bar.low, bar.close)}", hard=True)
                )
                continue

            if bar.low - tol > min(bar.open, bar.close) or max(bar.open, bar.close) > bar.high + tol:
                violations.append(
                    Violation(
                        symbol,
                        tb.timestamp,
                        "ohlc_inconsistent",
                        f"open/close outside [low, high] beyond tolerance: O={bar.open} H={bar.high} L={bar.low} C={bar.close}",
                        hard=True,
                    )
                )

            # A non-positive close is flagged above but is still the next bar's
            # predecessor; skip the move check rather than divide by it.
            if i > 0 and series[i - 1].bar.close > 0:
                prev_close = series[i - 1].bar.close
                move = bar.close / prev_close - 1.0
                ratio = _split_ratio_on(symbol, tb.timestamp, actions)
                if ratio is not None:
                    # An as-traded series jumps by ~1/ratio on the ex-date, while a
                    # provider-adjusted one is continuous. Take the smaller of the raw
                    # and ratio-adjusted moves so either frame passes (e.g. clean,
                    # provider-adjusted XOP data).
                    ratio_adjusted = (bar.close * ratio) / prev_close - 1.0
                    move = min((move, ratio_adjusted), key=abs)
                if abs(move) > MOVE_WARNING_THRESHOLD:
                    violations.append(
                        Violation(
                            symbol,
                            tb.timestamp,
                            "unexplained_move",
                            f"close {prev_close} -> {bar.close} ({move:+.1%} after split adjustment)",
                            hard=abs(move) > MOVE_HARD_THRESHOLD,
                        )
                    )

            if volumes is not None and i < len(volumes) and _is_present(volumes[i]):
                if volumes[i] == 0:
                    violations.append(
                        Violation(symbol, tb.timestamp, "zero_volume", "volume=0", hard=False)
                    )
                elif i >= VOLUME_MEDIAN_WINDOW:
                    window = [v for v in volumes[i - VOLUME_MEDIAN_WINDOW : i] if _is_present(v)]
                    if window:
                        median = statistics.median(window)
                        if median > 0 and volumes[i] > VOLUME_SPIKE_MULTIPLE * median:
                            violations.append(
                                Violation(
                                    symbol,
                                    tb.timestamp,
                                    "volume_spike",
                                    f"volume {volumes[i]:,.0f} > {VOLUME_SPIKE_MULTIPLE}x trailing median {median:,.0f}",
                                    hard=False,
                                )
                            )

    return ValidationResult(violations=tuple(violations))
