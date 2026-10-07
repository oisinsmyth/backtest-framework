"""Corporate actions: dividends and splits as data alongside raw prices.

Adjusted prices would distort cost calculations (commissions on rewritten notionals),
while raw prices without events lose dividends and make splits look like crashes. So
this module carries the events and the engine applies them (dividend cash flows via
the DividendFlow brick, split position scaling in run_backtest). split_adjusted()
builds the back-adjusted series strategies see for signal continuity; fills and
commissions use raw prices.

yfinance split-ratio convention (verified in tests): 4.0 = 4-for-1 forward split
(shares ×4, price ÷4), 0.25 = 1-for-4 reverse split (shares ×0.25, price ×4).
Back-adjustment: adjusted(t) = raw(t) / Π(ratio of every split with ex-date > t),
which maps pre-split prices onto the post-split scale and leaves the latest prices
unchanged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

from ..simulator.fills import Bar
from .bars import TimestampedBar


@dataclass(frozen=True)
class CorporateActions:
    dividends_by_symbol: Mapping[str, Sequence[tuple[datetime, float]]] = field(default_factory=dict)
    """Per symbol: (ex-date, dividend per share). Raw per-share amounts."""
    splits_by_symbol: Mapping[str, Sequence[tuple[datetime, float]]] = field(default_factory=dict)
    """Per symbol: (ex-date, ratio) in yfinance convention (see module docstring)."""


def split_adjusted(bars: Sequence[TimestampedBar], splits: Sequence[tuple[datetime, float]]) -> list[TimestampedBar]:
    """Back-adjust a raw bar series for splits only.

    Dividends are excluded; they are handled as cash flows."""
    if not splits:
        return list(bars)
    adjusted: list[TimestampedBar] = []
    for tb in bars:
        factor = 1.0
        for ex_date, ratio in splits:
            if ex_date > tb.timestamp:
                factor *= ratio
        if factor == 1.0:
            adjusted.append(tb)
        else:
            adjusted.append(
                TimestampedBar(
                    timestamp=tb.timestamp,
                    bar=Bar(
                        open=tb.bar.open / factor,
                        high=tb.bar.high / factor,
                        low=tb.bar.low / factor,
                        close=tb.bar.close / factor,
                    ),
                )
            )
    return adjusted


def _future_split_factor(timestamp: datetime, splits: Sequence[tuple[datetime, float]]) -> float:
    factor = 1.0
    for ex_date, ratio in splits:
        if ex_date > timestamp:
            factor *= ratio
    return factor


def as_traded_from_adjusted(
    bars: Sequence[TimestampedBar], splits: Sequence[tuple[datetime, float]]
) -> list[TimestampedBar]:
    """Reconstruct true as-traded prices from a split-adjusted series.

    yfinance's auto_adjust=False prices are already split-adjusted, though not
    dividend-adjusted (verified on XOP's 2020-03-30 1-for-4 reverse split in yfinance
    data: the close runs 32.12 → 32.01 across the split, while the traded price on
    2020-03-27 was ~$8.03). The adjusted series serves as the signal series, and the
    execution series used for commissions and impact is
    as_traded(t) = adjusted(t) × Π(ratio of splits with ex-date > t)."""
    if not splits:
        return list(bars)
    result: list[TimestampedBar] = []
    for tb in bars:
        factor = _future_split_factor(tb.timestamp, splits)
        if factor == 1.0:
            result.append(tb)
        else:
            result.append(
                TimestampedBar(
                    timestamp=tb.timestamp,
                    bar=Bar(
                        open=tb.bar.open * factor,
                        high=tb.bar.high * factor,
                        low=tb.bar.low * factor,
                        close=tb.bar.close * factor,
                    ),
                )
            )
    return result


def as_declared_dividends(
    dividends: Sequence[tuple[datetime, float]], splits: Sequence[tuple[datetime, float]]
) -> list[tuple[datetime, float]]:
    """Convert split-adjusted dividend amounts to as-declared per-share amounts.

    yfinance dividends are in the adjusted frame (XOP's run 0.40, 0.38, 0.311 smoothly
    across the split, where as-declared amounts would jump 4×). Cash-flow invariance
    (true_qty × true_div == adj_qty × adj_div) gives the same transform as prices:
    declared = adjusted × Π(ratio of splits with ex-date > ex_date)."""
    return [(ts, amount * _future_split_factor(ts, splits)) for ts, amount in dividends]


def save_events_json(path: str | Path, actions: CorporateActions) -> None:
    payload = {
        "dividends": {
            symbol: [[ts.isoformat(), amount] for ts, amount in events]
            for symbol, events in actions.dividends_by_symbol.items()
        },
        "splits": {
            symbol: [[ts.isoformat(), ratio] for ts, ratio in events]
            for symbol, events in actions.splits_by_symbol.items()
        },
    }
    # SnapshotStore hashes these bytes, so line endings are fixed to CRLF on every
    # platform (default text mode would vary by OS). CRLF matches the bytes existing
    # snapshot ids were computed from.
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(json.dumps(payload, indent=2, sort_keys=True))


def load_events_json(path: str | Path) -> CorporateActions:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # Strip tzinfo as for bar timestamps: events are keyed by exchange-local date and
    # are compared with naive bar timestamps.
    return CorporateActions(
        dividends_by_symbol={
            symbol: [(datetime.fromisoformat(ts).replace(tzinfo=None), float(amount)) for ts, amount in events]
            for symbol, events in payload.get("dividends", {}).items()
        },
        splits_by_symbol={
            symbol: [(datetime.fromisoformat(ts).replace(tzinfo=None), float(ratio)) for ts, ratio in events]
            for symbol, events in payload.get("splits", {}).items()
        },
    )
