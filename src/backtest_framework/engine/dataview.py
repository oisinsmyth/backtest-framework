"""DataView: a structural look-ahead guard for strategy code.

A DataView is constructed holding only the bars up to the current index, so later
bars cannot be reached through `.iloc`, reflection or `__dict__`; they were never
passed in. Slicing by convention (`iloc[:i+1]`) would depend on every caller
getting it right.

The engine, which holds the full series, calls build_data_view() once per bar to
construct a new DataView. Strategy code receives only that view.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..simulator.fills import Bar


class LookAheadError(IndexError):
    """Raised when a DataView is asked for a bar outside its visible range.

    Covers both an index beyond the current bar (look-ahead) and one before the start
    of visible history."""


class MissingVolumeError(LookAheadError):
    """Raised when code requires volume from a view built without a volume series.

    An instrument with no volume (spot FX, an index) returns None from `volume()`. A view
    built without any volume series raises this instead, so a missing series is reported
    as a configuration error rather than read as "no volume" by a volume filter."""


@dataclass(frozen=True)
class DataView:
    _visible_bars: tuple[Bar, ...]
    _visible_volumes: tuple[float | None, ...] | None = None
    """Aligned per-bar volume, or None when this instrument has no volume at all.

    Sliced like `_visible_bars`, so future volumes are never stored. A `None` entry is
    a gap on that bar; a `None` tuple means the instrument has no volume series. The
    accessors treat the two differently."""

    instrument_id: str | None = None
    """Optional; used only to name the instrument in a MissingVolumeError."""

    def __post_init__(self) -> None:
        if len(self._visible_bars) == 0:
            raise ValueError("DataView must be constructed with at least one visible bar")
        if self._visible_volumes is not None and len(self._visible_volumes) != len(self._visible_bars):
            raise ValueError(
                f"DataView volume series has {len(self._visible_volumes)} entries but there "
                f"are {len(self._visible_bars)} visible bar(s); the two must align bar for bar"
            )
        if self._visible_volumes is not None:
            # A NaN volume would make every volume comparison False. `normalise_volumes`
            # should already have converted NaN to None; check it here rather than
            # assume it (a caller can miss it for, e.g., np.float32).
            nan_at = [i for i, v in enumerate(self._visible_volumes) if v is not None and v != v]
            if nan_at:
                raise ValueError(
                    f"DataView was given NaN volume at index/indices {nan_at[:5]}. Mark a gap "
                    "as None; `normalise_volumes` converts NaN to None."
                )

    @property
    def current_index(self) -> int:
        return len(self._visible_bars) - 1

    @property
    def current_bar(self) -> Bar:
        return self._visible_bars[-1]

    def __len__(self) -> int:
        return len(self._visible_bars)

    def _resolve(self, index: int) -> int:
        """Return the absolute bar index for `index`.

        Negative indices count back from the current bar (-1 = current_bar). Raises
        LookAheadError if the result falls outside [0, current_index]. Shared by
        `__getitem__`, `volume` and `require_volume` so bars and volumes index alike."""
        n = len(self._visible_bars)
        resolved = index if index >= 0 else n + index
        if resolved < 0:
            raise LookAheadError(
                f"requested index {index} is before the start of visible history "
                f"(only {n} bar(s) are visible)"
            )
        if resolved >= n:
            raise LookAheadError(
                f"requested bar index {index} is beyond the current index {self.current_index}; "
                "look-ahead is not permitted"
            )
        return resolved

    def __getitem__(self, index: int) -> Bar:
        return self._visible_bars[self._resolve(index)]

    @property
    def has_volume(self) -> bool:
        """Whether this view carries a volume series. False (no volume) is not an error."""
        return self._visible_volumes is not None

    def volume(self, index: int) -> float | None:
        """Volume at `index`, or None if the view has no volume series or the bar is a gap.

        For code that can work without volume; code that cannot should call
        `require_volume()`. There is no aggregation helper such as `mean_volume()`,
        because how to treat None is the consumer's decision."""
        resolved = self._resolve(index)
        if self._visible_volumes is None:
            return None
        return self._visible_volumes[resolved]

    def require_volume(self, index: int) -> float | None:
        """Volume at `index` for code that cannot function without a volume series.

        Raises MissingVolumeError if the view carries no volume series. Returns None for
        a per-bar gap, leaving the consumer to decide how to handle it."""
        resolved = self._resolve(index)
        if self._visible_volumes is None:
            named = f" (instrument {self.instrument_id!r})" if self.instrument_id else ""
            raise MissingVolumeError(
                "volume is required but this DataView was constructed without a volume "
                f"series{named}. Pass volumes through build_data_view or run_backtest, or "
                "use volume() if the component can work without it."
            )
        return self._visible_volumes[resolved]


def normalise_volumes(volumes: Sequence[float | None]) -> tuple[float | None, ...]:
    """Convert a volume series to floats, mapping NaN to None.

    A NaN in a view would make every volume comparison False, so a volume filter would
    reject every entry without raising. This is the only place the conversion happens.

    Kept out of `build_data_view`, which runs once per bar: a Python-level pass there
    would make each view O(n) instead of a tuple slice (about 2x slower over a long
    daily series). The engine normalises once and passes
    `volumes_already_normalised=True`.

    The NaN test is `v != v`, which holds for NaN of any type. An `isinstance(v, float)`
    check would miss `np.float32`, `np.float16`, `np.longdouble` and `Decimal("NaN")`,
    which parquet reads and vendor loads produce and `list(series.values)` preserves."""
    return tuple(None if v is None or v != v else float(v) for v in volumes)


def build_data_view(
    all_bars: Sequence[Bar],
    up_to_index: int,
    volumes: Sequence[float | None] | None = None,
    instrument_id: str | None = None,
    *,
    volumes_already_normalised: bool = False,
) -> DataView:
    """Return a DataView over `all_bars[0 : up_to_index + 1]`.

    Engine-side: pass strategies the returned view, never `all_bars`. `volumes`, when
    given, must align 1:1 with `all_bars` and is sliced the same way.

    Volumes must be in the view frame, matching `view_bars_by_instrument`. Execution
    uses as-traded prices and signals use split-adjusted prices; share volume is
    split-sensitive and only strategy code reads it, so it belongs in the view frame.
    This matters for equities, not for spot crypto.

    NaN volumes become None (see `normalise_volumes`). A caller building many views
    over one series should normalise once and pass `volumes_already_normalised=True`
    so each call is a plain slice.
    """
    if up_to_index < 0 or up_to_index >= len(all_bars):
        raise ValueError(f"up_to_index {up_to_index} out of range for a series of length {len(all_bars)}")
    visible_volumes: tuple[float | None, ...] | None = None
    if volumes is not None:
        if len(volumes) != len(all_bars):
            raise ValueError(
                f"volume series has {len(volumes)} entries but there are {len(all_bars)} bar(s); "
                "the two must align bar for bar"
            )
        sliced = volumes[: up_to_index + 1]
        visible_volumes = (
            tuple(sliced) if volumes_already_normalised else normalise_volumes(sliced)
        )
    return DataView(tuple(all_bars[: up_to_index + 1]), visible_volumes, instrument_id)
