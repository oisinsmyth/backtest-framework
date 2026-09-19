"""Corporate actions: dividends and splits as first-class data (D6, D75).

Raw prices + a separate dividends/splits table, instead of silently adjusted prices —
adjusted prices corrupt historical cost math (commissions computed on rewritten
notionals) while unadjusted-without-events breaks return dynamics (dividends vanish,
splits look like crashes). This module carries the events; the engine applies them
(dividend cash flows via the DividendFlow brick, split position scaling in
run_backtest), and split_adjusted() produces the back-adjusted series strategies see
for SIGNAL continuity — "returns from adjustments, fills/commissions from raw
prices" (D6), made literal.

yfinance split-ratio convention (verified in tests): 4.0 = 4-for-1 forward split
(shares ×4, price ÷4), 0.25 = 1-for-4 reverse split (shares ×0.25, price ×4).
Back-adjustment for a continuous signal series: adjusted(t) = raw(t) / Π(ratio of
every split with ex-date > t) — pre-split prices are mapped onto the post-split
scale, so the most recent prices are always unchanged.
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
    """Back-adjust a raw bar series for splits only (dividends deliberately excluded —
    dividend economics are handled as explicit cash flows, not price rewrites)."""
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
    """Reconstruct TRUE as-traded prices from a split-adjusted series (D75).

    Empirical finding (verified on XOP's 2020-03-30 1-for-4 reverse split in our own
    fixture): yfinance's auto_adjust=False prices are ALREADY split-adjusted — only
    dividends are excluded. The close is continuous across the split date (32.12 →
    32.01), while the true traded price on 2020-03-27 was ~$8.03. So the adjusted
    series is the correct SIGNAL series as-is, and the as-traded EXECUTION series
    (what commissions/impact must be computed on, per D6) is reconstructed as
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
    """Convert split-adjusted-frame dividend amounts to as-declared per-share amounts
    (D75). Same empirical finding as as_traded_from_adjusted: yfinance dividends are
    in the adjusted frame (the XOP series is smooth across the split — 0.40, 0.38,
    0.311 — where as-declared amounts would show a 4× discontinuity). Cash-flow
    invariance (true_qty × true_div == adj_qty × adj_div) gives the same transform as
    prices: declared = adjusted × Π(ratio of splits with ex-date > ex_date)."""
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
    # newline="\r\n", explicitly, on every platform. `Path.write_text` applies text-mode
    # translation, so this file was CRLF on Windows and LF on Linux -- and `SnapshotStore`
    # hashes these bytes, so the same fixture froze to two different snapshot ids depending on
    # who ran it (D551). CI's first week is what found it; the author's machine could not.
    #
    # CRLF rather than LF is not an aesthetic choice and is not an accident. A snapshot id is
    # logged with every trial and printed in results docs. These bytes are the ones every
    # published id was frozen under, so pinning them keeps those ids true AND makes the identity
    # reproducible anywhere. Choosing LF would be tidier and would renumber the lot.
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(json.dumps(payload, indent=2, sort_keys=True))


def load_events_json(path: str | Path) -> CorporateActions:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    # tzinfo stripped for the same reason as bar timestamps (D75): event identity is
    # the exchange-local date, and comparisons against bar timestamps must not mix
    # naive and aware datetimes.
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
