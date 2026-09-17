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
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

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
    kept_indices: Mapping[str, tuple[int, ...]] = field(default_factory=dict)
    """Per symbol, the indices of the INPUT series that survived cleaning.

    `clean()` takes a volume series, uses it to decide what to drop, and returns only bars.
    The caller is left holding a volume list that is now longer than the bars it belongs to
    and misaligned from the first drop onward — every subsequent volume attributed to the
    wrong bar. That is not hypothetical: roughly half the runners in `scripts/` pass the raw
    list straight on to `validate()` and `calibrate_impact_params()`, and the misalignment
    reaches ADV, therefore `SqrtImpact` charges, therefore P&L (D541).

    This is the additive half of the fix: a caller can realign exactly, with

        volumes = [volumes[i] for i in report.kept_indices[symbol]]

    without `clean()`'s signature changing and without any existing caller breaking.
    `research/breakout_universe.align_volumes` solves the same problem by re-matching on
    timestamps, and its docstring records that it exists only because this interface did not
    offer the information. Now it does.
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
        """Take a per-bar series indexed against the INPUT bars and drop what the bars did.

        Raises rather than truncating when the series does not match the input length: a
        series of the wrong length is not a series that can be realigned, and quietly
        returning a shorter one is how this defect stayed invisible in the first place.
        """
        kept = self.kept_indices.get(symbol)
        if kept is None:
            raise KeyError(f"no cleaning record for {symbol!r} — realign needs the report that dropped its bars")
        if kept and max(kept) >= len(values):
            raise ValueError(
                f"{symbol!r}: series has {len(values)} entries but cleaning kept index "
                f"{max(kept)} of a longer input — this series is not the one that was cleaned"
            )
        return [values[i] for i in kept]


def _is_present(volume: float | None) -> bool:
    """True when this bar has a usable volume, for either spelling of "it does not".

    The data layer writes a gap as NaN (`csv_fixture._to_float`) and the engine layer writes
    it as None (`engine/dataview.normalise_volumes`, which converts NaN INTO None and whose
    docstring calls None the canonical gap). Both are correct in their own half; the bug was
    that these call sites used `math.isnan`, which does not raise on a gap it understands and
    DOES raise `TypeError: must be real number, not NoneType` on the other spelling. So a
    caller who normalised first -- the documented engine path -- crashed the validator.

    Cheaper than making one half convert: neither half has to win, and the declared types
    (`Sequence[float]`) that hid the contradiction from mypy stop mattering.
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
