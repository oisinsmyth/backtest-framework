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


@dataclass(frozen=True)
class DataView:
    _visible_bars: tuple[Bar, ...]

    def __post_init__(self) -> None:
        if len(self._visible_bars) == 0:
            raise ValueError("DataView must be constructed with at least one visible bar")

    @property
    def current_index(self) -> int:
        return len(self._visible_bars) - 1

    @property
    def current_bar(self) -> Bar:
        return self._visible_bars[-1]

    def __len__(self) -> int:
        return len(self._visible_bars)

    def __getitem__(self, index: int) -> Bar:
        """Absolute bar index, with Python-style negative indexing relative to the
        current bar (-1 = current_bar, -2 = one bar before that, ...). Any index that
        resolves outside [0, current_index] raises LookAheadError — there is no index
        that could resolve to a future bar, because none is stored here."""
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
        return self._visible_bars[resolved]


def build_data_view(all_bars: Sequence[Bar], up_to_index: int) -> DataView:
    """Engine-side helper: this function has access to the full bar series (it's engine
    code, not strategy code) and slices it down to a DataView exposing only
    all_bars[0 : up_to_index + 1]. Strategy code should only ever receive what this
    function returns — never `all_bars` itself.
    """
    if up_to_index < 0 or up_to_index >= len(all_bars):
        raise ValueError(f"up_to_index {up_to_index} out of range for a series of length {len(all_bars)}")
    return DataView(tuple(all_bars[: up_to_index + 1]))
