"""DataView: a structural look-ahead guard for strategy code (D32).

Slicing-by-convention (`iloc[:i+1]`) is an honour system — one careless reference to the
underlying frame silently invalidates every result downstream. The approach here isn't
access control on top of the full data (hiding it behind a leading underscore and hoping
nobody looks); it's that a DataView is *constructed* holding only the bars visible up to
the current index. Bars beyond that were never handed to the object in the first place,
so there is nothing for a reflection trick, a `.iloc`, or a walk of `__dict__` to find —
"physically cannot" rather than "asked nicely not to" (see PHILOSOPHY.md, Pillar 1).

The engine (which does have the full series) calls build_data_view() once per bar to
construct a fresh, growing DataView; strategy code only ever receives the result of that
call, never the underlying sequence itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ..simulator.fills import Bar


class LookAheadError(IndexError):
    """Raised when code holding a DataView asks for a bar outside the range it was
    constructed with — whether beyond the current index (look-ahead) or before the
    start of visible history (out of range)."""


class MissingVolumeError(LookAheadError):
    """Raised when code that REQUIRES volume holds a view constructed without one.

    This is the third of the three volume states, and the only loud one (D168). "This
    instrument has no volume" (spot FX, an index, a synthetic path) and "somebody
    forgot to wire the volume through" must never be the same observation: the first is
    a permanent property of the world and is correctly silent, the second is a
    configuration error that would otherwise turn a volume filter into a filter that
    rejects every entry and returns a clean-looking, wrong result."""


@dataclass(frozen=True)
class DataView:
    _visible_bars: tuple[Bar, ...]
    _visible_volumes: tuple[float | None, ...] | None = None
    """Aligned per-bar volume, or None when this instrument has no volume at all.

    Constructed SLICED, exactly as `_visible_bars` is: future volumes are never handed
    to the object, so the look-ahead guarantee is inherited from the existing
    construction rather than re-argued for a second channel (D32/D56). A `None` ENTRY
    inside the tuple is a real gap on that bar; a `None` TUPLE is an instrument with no
    volume series. Those are different states and the accessors keep them different."""

    instrument_id: str | None = None
    """Only used to name the instrument in a MissingVolumeError. A view that does not
    know its own id still works; the error message is just less helpful."""

    def __post_init__(self) -> None:
        if len(self._visible_bars) == 0:
            raise ValueError("DataView must be constructed with at least one visible bar")
        if self._visible_volumes is not None and len(self._visible_volumes) != len(self._visible_bars):
            raise ValueError(
                f"DataView volume series has {len(self._visible_volumes)} entries but there "
                f"are {len(self._visible_bars)} visible bar(s) — the two must align exactly"
            )
        if self._visible_volumes is not None:
            # A NaN here is the D168 failure in its finished form: every comparison against
            # it is False, so a volume filter rejects every entry and the run returns a
            # plausible wrong answer with no error anywhere. `normalise_volumes` is meant to
            # have converted it to None already; this refuses to hold one either way, so the
            # conversion is CHECKED at the boundary rather than assumed to have happened.
            # It exists because the conversion silently did not happen for np.float32.
            nan_at = [i for i, v in enumerate(self._visible_volumes) if v is not None and v != v]
            if nan_at:
                raise ValueError(
                    f"DataView was given NaN volume at index/indices {nan_at[:5]} — a gap must "
                    "be None, not NaN (D168). Pass the series through "
                    "`normalise_volumes` rather than constructing the view from raw values."
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
        """Absolute bar index, with Python-style negative indexing relative to the
        current bar (-1 = current_bar, -2 = one bar before that, ...). Any index that
        resolves outside [0, current_index] raises LookAheadError — there is no index
        that could resolve to a future bar, because none is stored here.

        Factored out and shared by `__getitem__`, `volume` and `require_volume` so a
        future change cannot make the bar accessor and the volume accessor disagree
        about what index -3 means."""
        n = len(self._visible_bars)
        resolved = index if index >= 0 else n + index
        if resolved < 0:
            raise LookAheadError(
                f"requested index {index} is before the start of visible history "
                f"(only {n} bar(s) are visible)"
            )
        if resolved >= n:
            raise LookAheadError(
                f"requested bar index {index} is beyond the current index {self.current_index} "
                "— look-ahead is not permitted (D32)"
            )
        return resolved

    def __getitem__(self, index: int) -> Bar:
        return self._visible_bars[self._resolve(index)]

    @property
    def has_volume(self) -> bool:
        """Whether this view carries a volume series at all. False is state 1 — the
        instrument has no volume — and is not an error."""
        return self._visible_volumes is not None

    def volume(self, index: int) -> float | None:
        """Volume at `index`, or None if unavailable — either because this instrument
        has no volume series, or because this particular bar has a gap.

        The accessor IS the contract: calling `volume()` says "I can work without it".
        Code that cannot work without it calls `require_volume()` instead. There is
        deliberately no `mean_volume()` helper — aggregation embeds a policy about
        None, and policy belongs in the consumer, not in the guard object."""
        resolved = self._resolve(index)
        if self._visible_volumes is None:
            return None
        return self._visible_volumes[resolved]

    def require_volume(self, index: int) -> float | None:
        """Volume at `index` for code that cannot function without a volume series.

        Raises MissingVolumeError if the view carries no series at all (state 3, a
        configuration error). Still returns None for a per-bar gap (state 2) — a gap is
        a fact about the data, and the consumer states its own policy on it."""
        resolved = self._resolve(index)
        if self._visible_volumes is None:
            named = f" (instrument {self.instrument_id!r})" if self.instrument_id else ""
            raise MissingVolumeError(
                "volume is required but this DataView was constructed without a volume "
                f"series{named} — pass volumes through build_data_view/run_backtest, or "
                "use volume() if the component can work without it (D168)"
            )
        return self._visible_volumes[resolved]


def normalise_volumes(volumes: Sequence[float | None]) -> tuple[float | None, ...]:
    """NaN -> None, once, for a whole series.

    Every comparison against NaN is False, so a NaN that survived into a view would make
    a volume filter reject every entry and return a plausible, wrong result with no error
    anywhere. This is the one place that conversion happens (D168).

    Split out from `build_data_view` for a measured reason: `build_data_view` is called
    once PER BAR, so doing this Python-level pass inside it made view construction O(n)
    per bar where it had been a C-level tuple slice. Measured on the breakout study that
    was a 2x whole-run slowdown (109s -> 227s) for work whose answer never changes. Engine
    callers own the full series, so they normalise once here and pass
    `volumes_already_normalised=True`.

    NOT gated on `isinstance(v, float)`, and that is the whole point. `v != v` is true for
    every NaN of every type; the `isinstance` check that used to guard it admitted
    `np.float64` (which subclasses `float`) and silently let through `np.float32`,
    `np.float16`, `np.longdouble` and `Decimal("NaN")` — the types a parquet read or a
    vendor load produces by default, and the ones `list(series.values)` preserves where
    `.tolist()` would not. For those the NaN reached the view and made a volume filter
    reject every entry: the exact failure this function exists to prevent, arriving through
    the function itself. `DataView.__post_init__` now refuses a NaN as well, so the
    conversion is checked at the boundary rather than trusted here."""
    return tuple(None if v is None or v != v else float(v) for v in volumes)


def build_data_view(
    all_bars: Sequence[Bar],
    up_to_index: int,
    volumes: Sequence[float | None] | None = None,
    instrument_id: str | None = None,
    *,
    volumes_already_normalised: bool = False,
) -> DataView:
    """Engine-side helper: this function has access to the full bar series (it's engine
    code, not strategy code) and slices it down to a DataView exposing only
    all_bars[0 : up_to_index + 1]. Strategy code should only ever receive what this
    function returns — never `all_bars` itself.

    `volumes`, when supplied, must align 1:1 with `all_bars` and is sliced identically —
    that slicing is the whole point, and it is why the volume channel inherits the
    look-ahead guarantee instead of needing its own argument (D168).

    **Volumes are in the VIEW frame**, matching `view_bars_by_instrument`. Share volume
    is split-sensitive, and this framework runs two price frames (D75): as-traded raw
    prices for execution, split-adjusted prices for signal continuity. Volume is only
    ever consumed by strategy code, which sees the view frame, so that is the frame it
    must be supplied in. Moot for spot crypto, live for any equity use.

    `NaN` is normalised to `None` and never enters a view — see `normalise_volumes`.
    Callers that build many views over the SAME series (the engine, once per bar) should
    call `normalise_volumes` once themselves and pass `volumes_already_normalised=True`,
    which leaves the per-bar path a pure slice. Everyone else can ignore the flag and get
    the conversion for free.
    """
    if up_to_index < 0 or up_to_index >= len(all_bars):
        raise ValueError(f"up_to_index {up_to_index} out of range for a series of length {len(all_bars)}")
    visible_volumes: tuple[float | None, ...] | None = None
    if volumes is not None:
        if len(volumes) != len(all_bars):
            raise ValueError(
                f"volume series has {len(volumes)} entries but there are {len(all_bars)} bar(s) "
                "— the two must align exactly"
            )
        sliced = volumes[: up_to_index + 1]
        visible_volumes = (
            tuple(sliced) if volumes_already_normalised else normalise_volumes(sliced)
        )
    return DataView(tuple(all_bars[: up_to_index + 1]), visible_volumes, instrument_id)
