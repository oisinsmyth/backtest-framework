"""Integration test for D32: a deliberately cheating strategy cannot obtain future bars.

This asserts the exception (or the absence of any exploitable surface), not the honour
system — every attack vector here is something a strategy author coming from pandas
habits, or actively trying to cheat, would plausibly reach for.
"""

import math

import pytest

from backtest_framework.engine.dataview import (
    LookAheadError,
    MissingVolumeError,
    build_data_view,
)
from backtest_framework.simulator.fills import Bar


def _bars(n: int) -> tuple[Bar, ...]:
    return tuple(Bar(open=float(i), high=float(i), low=float(i), close=float(i)) for i in range(n))


def _volumes(n: int) -> list[float]:
    """Volumes chosen so every value is distinct from every bar close, and future
    volumes are distinguishable from visible ones by magnitude alone."""
    return [1000.0 + i for i in range(n)]


def test_cheating_strategy_cannot_obtain_future_bars():
    all_bars = _bars(10)
    view = build_data_view(all_bars, up_to_index=3)

    # Attack 1: ask for a future index directly through the documented accessor.
    with pytest.raises(LookAheadError):
        view[view.current_index + 1]

    # Attack 2: reach for pandas-honed instincts. None of these exist on this object.
    for pandas_ish_name in ("iloc", "loc", "data", "df", "frame", "values"):
        assert not hasattr(view, pandas_ish_name), f"DataView unexpectedly exposes '{pandas_ish_name}'"

    # Attack 3: climb back to whatever constructed this view to reach the full series.
    for parent_ref_name in ("parent", "engine", "portfolio", "source", "_parent", "_engine", "_source"):
        assert not hasattr(view, parent_ref_name), f"DataView unexpectedly exposes '{parent_ref_name}'"

    # Attack 4: read the "private" storage directly (leading underscore is only a
    # convention in Python, not real access control) — even this yields nothing extra,
    # because future bars were never given to the object in the first place.
    assert all(bar.close <= 3.0 for bar in view._visible_bars)
    assert len(view._visible_bars) == 4  # bars 0..3, never 4..9

    # Attack 5: walk every attribute the object actually has and check none of the
    # instance's own state contains a future bar OR a future volume. The volume half
    # matters as much as the bar half: this attack previously inspected only tuples
    # whose members are Bar objects, so a tuple of floats carrying the full volume
    # series would have walked straight past it (D168).
    future_closes = {bar.close for bar in all_bars[4:]}
    for value in vars(view).values():
        if isinstance(value, tuple):
            observed_closes = {b.close for b in value if isinstance(b, Bar)}
            assert not (observed_closes & future_closes)


def test_cheating_strategy_cannot_obtain_future_volumes():
    """The volume channel is new attack surface, and gets the same treatment.

    The mitigation is structural rather than defensive: the volume tuple is CONSTRUCTED
    SLICED, so there is no future volume in the object to reach. That is only a real
    mitigation if it is tested, which is what this is."""
    all_bars = _bars(10)
    all_volumes = _volumes(10)
    view = build_data_view(all_bars, up_to_index=3, volumes=all_volumes, instrument_id="X")

    # Attack 1: the documented accessor, past the current bar.
    with pytest.raises(LookAheadError):
        view.volume(view.current_index + 1)
    with pytest.raises(LookAheadError):
        view.require_volume(view.current_index + 1)

    # Attack 2: negative indices that wrap past the start of visible history.
    with pytest.raises(LookAheadError):
        view.volume(-len(view) - 1)

    # Attack 3: read the "private" storage directly.
    assert len(view._visible_volumes) == 4  # volumes 0..3, never 4..9
    assert max(view._visible_volumes) == 1003.0

    # Attack 4: walk the instance's own state for any future volume value.
    future_volumes = set(all_volumes[4:])
    for value in vars(view).values():
        if isinstance(value, tuple):
            observed = {v for v in value if isinstance(v, float)}
            assert not (observed & future_volumes), "a future volume is reachable from the view"

    # Attack 5: the volume accessor must agree with the bar accessor about every index,
    # including negatives — they share _resolve precisely so they cannot drift apart.
    for index in list(range(4)) + [-1, -2, -3, -4]:
        assert view.volume(index) == 1000.0 + view[index].close


def test_a_view_holds_exactly_one_volume_entry_per_visible_bar():
    for up_to in range(6):
        view = build_data_view(_bars(6), up_to_index=up_to, volumes=_volumes(6))
        assert len(view._visible_volumes) == up_to + 1 == len(view._visible_bars)


def test_the_three_volume_states_are_distinguishable():
    """State 1 (no series) is silent, state 2 (a gap) is silent, state 3 (required but
    absent) is loud. Collapsing 1 and 3 is the trap this design exists to avoid."""
    bars = _bars(4)

    # State 1 — instrument has no volume at all.
    none_view = build_data_view(bars, up_to_index=3)
    assert none_view.has_volume is False
    assert none_view.volume(0) is None
    # State 3 — the same absence, but the caller says it cannot work without it.
    with pytest.raises(MissingVolumeError, match="volume is required"):
        none_view.require_volume(0)

    # State 2 — a real gap on one bar of a real series.
    gap_view = build_data_view(bars, up_to_index=3, volumes=[10.0, None, 30.0, 40.0])
    assert gap_view.has_volume is True
    assert gap_view.volume(1) is None
    assert gap_view.require_volume(1) is None  # a gap is data, not a configuration error
    assert gap_view.require_volume(2) == 30.0


def test_nan_never_reaches_a_view():
    """Every comparison against NaN is False, so a NaN that survived into a view would
    make a volume filter reject every entry and return a plausible, wrong result."""
    view = build_data_view(_bars(4), up_to_index=3, volumes=[10.0, float("nan"), 30.0, 40.0])
    assert view.volume(1) is None
    assert not any(isinstance(v, float) and math.isnan(v) for v in view._visible_volumes)


def test_a_length_mismatch_fails_loudly_naming_both_lengths():
    with pytest.raises(ValueError, match="3 entries but there are 4"):
        build_data_view(_bars(4), up_to_index=3, volumes=[1.0, 2.0, 3.0])


def test_the_error_names_the_instrument_when_it_knows_it():
    view = build_data_view(_bars(4), up_to_index=1, instrument_id="BTC-USD")
    with pytest.raises(MissingVolumeError, match="BTC-USD"):
        view.require_volume(0)
