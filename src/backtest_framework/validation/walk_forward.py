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
from ..engine.dataview import DataView, build_data_view, normalise_volumes


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
    volumes_by_instrument: Mapping[str, Sequence[float | None]] | None = None,
) -> Iterator[WalkForwardWindow]:
    """`volumes_by_instrument` is optional and exists so that fitters wanting volume — a
    liquidity-aware selector, a dollar-volume screen — get it under the SAME structural
    guard as the bars (D168). Train views are built by the same `build_data_view` call,
    so the slicing guarantee is identical and does not need re-arguing: the test
    window's volumes were never handed to the object either."""
    if train_size < 2 or test_size < 1:
        raise ValueError(f"need train_size >= 2 and test_size >= 1, got {train_size}/{test_size}")
    step = step if step is not None else test_size

    aligned = align_bars(bars_by_instrument)
    n = len(aligned)
    instruments = list(bars_by_instrument)

    # Volume is matched to aligned timestamps before any window is cut, so a window's
    # volumes cannot drift out of step with its bars.
    volume_lookup: dict[str, tuple[float | None, ...] | None] = {}
    if volumes_by_instrument is not None:
        for symbol in instruments:
            supplied = volumes_by_instrument.get(symbol)
            if supplied is None:
                volume_lookup[symbol] = None
                continue
            series = bars_by_instrument[symbol]
            if len(supplied) != len(series):
                raise ValueError(
                    f"volumes_by_instrument[{symbol!r}] has {len(supplied)} entries but its bar "
                    f"series has {len(series)} — the two must align exactly"
                )
            by_timestamp = {tb.timestamp: v for tb, v in zip(series, normalise_volumes(supplied))}
            try:
                volume_lookup[symbol] = tuple(by_timestamp[ab.timestamp] for ab in aligned)
            except KeyError as exc:
                raise ValueError(
                    f"volumes_by_instrument is missing a volume for an aligned timestamp on "
                    f"{symbol!r}: {exc}"
                ) from exc

    window_index = 0
    start = 0
    while start + train_size + test_size <= n:
        train = aligned[start : start + train_size]
        test = aligned[start + train_size : start + train_size + test_size]

        train_volumes: dict[str, tuple[float | None, ...] | None] = {}
        for symbol in instruments:
            aligned_volumes = volume_lookup.get(symbol)
            train_volumes[symbol] = (
                None if aligned_volumes is None else aligned_volumes[start : start + train_size]
            )
        train_views = {
            symbol: build_data_view(
                tuple(ab.bars[symbol] for ab in train),
                train_size - 1,
                volumes=train_volumes[symbol],
                instrument_id=symbol,
                volumes_already_normalised=True,
            )
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
