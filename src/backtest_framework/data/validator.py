"""Data validation: data failing a hard check is quarantined, never passed through.

yfinance is a scraper, not an API; it breaks and serves bad prints without warning.
The validator runs at snapshot creation: hard violations quarantine the whole
snapshot (SnapshotStore.load refuses it); warnings (e.g. volume anomalies) are
recorded in the snapshot's metadata without blocking.

The bar-to-bar move check is split-aware: a raw price series legitimately jumps ~4x
on a reverse-split ex-date (XOP, 2020-03-30, in the bundled fixture). The splits table
is consulted first; after split adjustment, an unexplained move in 25-60% is a warning
and only >60% is a hard quarantine (thresholds calibrated to observed genuine data; a
25% hard threshold would have quarantined the real 2020 COVID crash days).

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
"""Calibrated against observed genuine data: XOP's 2020-03-09 oil crash day is a real
−37% simple move, and XLE's is −20%, so a 25% hard threshold would have quarantined the
genuine COVID crash. So 25–60% unexplained flags a warning (the cleaner's
spike-and-revert rule has already dropped bad prints that revert; what survives is
probably real), and only >60%, beyond anything observed for these ETFs even in 2020,
is a hard quarantine."""

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
    """True when this bar has a usable volume, for either spelling of "it does not".

    The data layer writes a gap as NaN (`csv_fixture._to_float`) and the engine layer writes
    it as None (`engine/dataview.normalise_volumes`, which converts NaN into None and whose
    docstring calls None the canonical gap). `math.isnan` alone would raise `TypeError` on
    None, so a caller who normalised first (the documented engine path) would crash. This
    check accepts both spellings, so neither layer has to convert.
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

        # Duplicate timestamps are a hard violation: downstream alignment keys bars
        # by timestamp, so a duplicate silently drops a bar last-wins; data that can
        # do that must be quarantined, not passed through.
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

            # `prev_close > 0` is required. A bar with a non-positive close is flagged above
            # and `continue`d, but the `continue` only skips that bar's own checks; the bar
            # is still the next one's predecessor, and this line divides by it. Without the
            # guard a single 0.0 close (an ordinary scraper failure) would make validate()
            # raise ZeroDivisionError instead of quarantining the data. A move measured
            # against a quarantined close is meaningless in any case, so it is not computed.
            if i > 0 and series[i - 1].bar.close > 0:
                prev_close = series[i - 1].bar.close
                move = bar.close / prev_close - 1.0
                ratio = _split_ratio_on(symbol, tb.timestamp, actions)
                if ratio is not None:
                    # Frame-robust split awareness: an as-traded series jumps by
                    # ~1/ratio on the ex-date (residual = ratio-adjusted move), while a
                    # provider-adjusted series is already continuous (residual = the
                    # raw move). The move is explained if it's small in either frame;
                    # judging only one frame would fabricate a violation on the other
                    # (e.g. quarantine clean, provider-adjusted XOP data).
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
