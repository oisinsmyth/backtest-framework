"""Data sanity gate (D26, D74): data failing it is quarantined, never passed through.

yfinance is a scraper, not an API — it breaks and serves bad prints without warning.
The validator runs at snapshot creation (D24): HARD violations quarantine the whole
snapshot (SnapshotStore.load refuses it — structurally, not by convention);
WARNINGS (D26 calls them "volume anomaly flags") are recorded in the snapshot's
metadata without blocking.

The bar-to-bar move check is split-aware: a raw price series legitimately jumps ~4x
on a reverse-split ex-date (XOP, 2020-06-22, in our own data). The splits table is
consulted before crying foul — an unexplained >25% close-to-close move is a hard
violation; the same move on a split date, scaled by the split ratio, is expected.

Second-source cross-checking stays deferred, per D26's own scoping.
"""

from __future__ import annotations

import math
import statistics
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

from .bars import TimestampedBar
from .corporate_actions import CorporateActions

VALIDATOR_VERSION = "validate-v1"

OHLC_RELATIVE_TOLERANCE = 1e-9  # same tolerance the cleaner uses; D47's spirit (D74)

MOVE_WARNING_THRESHOLD = 0.25
MOVE_HARD_THRESHOLD = 0.60
"""Calibrated against observed genuine data, not guessed (D74): XOP's 2020-03-09 oil
crash day is a real −37% simple move, and XLE's is −20% — a 25% hard threshold would
have quarantined the genuine COVID crash. So 25–60% unexplained flags a WARNING (the
cleaner's spike-and-revert rule has already dropped bad prints that revert; what
survives is probably real), and only >60% — beyond anything observed for these ETFs
even in 2020 — is a hard quarantine."""

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

        # Duplicate timestamps are a hard violation (D99): downstream alignment
        # keys bars by timestamp, so a duplicate silently drops a bar last-wins —
        # data that can do that must be quarantined, not passed through.
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

            if i > 0:
                prev_close = series[i - 1].bar.close
                move = bar.close / prev_close - 1.0
                ratio = _split_ratio_on(symbol, tb.timestamp, actions)
                if ratio is not None:
                    # Frame-robust split awareness (D74): an AS-TRADED series jumps by
                    # ~1/ratio on the ex-date (residual = ratio-adjusted move), while a
                    # provider-adjusted series is already continuous (residual = the
                    # raw move). The move is explained if it's small in EITHER frame —
                    # judging only one frame fabricates a violation on the other, which
                    # is exactly how this check's first version quarantined our own
                    # clean XOP data.
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

            if volumes is not None and i < len(volumes) and not math.isnan(volumes[i]):
                if volumes[i] == 0:
                    violations.append(
                        Violation(symbol, tb.timestamp, "zero_volume", "volume=0", hard=False)
                    )
                elif i >= VOLUME_MEDIAN_WINDOW:
                    window = [v for v in volumes[i - VOLUME_MEDIAN_WINDOW : i] if not math.isnan(v)]
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
