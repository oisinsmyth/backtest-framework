"""Walk-forward windows with structurally-guarded training data (D22, D28, D85).

Anything that FITS — pair selection today, regime models when they exist (D28), any
future parameter estimation — receives training data as `Mapping[str, DataView]`
built from the training slice ONLY. The test window is physically absent from what a
fitter can reach (D56's construction guarantee, reused): there is no index, attribute
or reflection path from a train view to a test bar, because the object was never
given one. This is D22's "selection inside the training window" enforced by
structure rather than reviewer discipline.

Windows are aligned across instruments first (D45/D63), so every fitter sees the
same timestamps per leg and OOS test slices line up 1:1 with training slices.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Mapping, Sequence

from ..data.alignment import align_bars
from ..data.bars import TimestampedBar
from ..engine.dataview import DataView, build_data_view


@dataclass(frozen=True)
class WalkForwardWindow:
    index: int
    train_views: Mapping[str, DataView]
    """What fitters get: training bars only, per instrument, structurally guarded."""
    test_bars_by_instrument: Mapping[str, list[TimestampedBar]]
    """What run_backtest gets for the OOS leg of this window."""


def walk_forward_windows(
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    train_size: int,
    test_size: int,
    step: int | None = None,
) -> Iterator[WalkForwardWindow]:
    if train_size < 2 or test_size < 1:
        raise ValueError(f"need train_size >= 2 and test_size >= 1, got {train_size}/{test_size}")
    step = step if step is not None else test_size

    aligned = align_bars(bars_by_instrument)
    n = len(aligned)
    instruments = list(bars_by_instrument)

    window_index = 0
    start = 0
    while start + train_size + test_size <= n:
        train = aligned[start : start + train_size]
        test = aligned[start + train_size : start + train_size + test_size]

        train_views = {
            symbol: build_data_view(tuple(ab.bars[symbol] for ab in train), train_size - 1)
            for symbol in instruments
        }
        test_bars = {
            symbol: [TimestampedBar(ab.timestamp, ab.bars[symbol]) for ab in test]
            for symbol in instruments
        }
        yield WalkForwardWindow(
            index=window_index, train_views=train_views, test_bars_by_instrument=test_bars
        )
        window_index += 1
        start += step
