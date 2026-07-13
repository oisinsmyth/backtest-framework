"""Unit tests for DataView (D32), per VERIFICATION_SCHEME.md Step 4.

Covers: requesting an index beyond current raises, and a reflection/attribute audit
proving no public attribute exposes future bar data. The "deliberately cheating
strategy" integration test lives in tests/integration/test_dataview_lookahead_guard.py.
"""

import pytest

from backtest_framework.engine.dataview import DataView, LookAheadError, build_data_view
from backtest_framework.simulator.fills import Bar


def _bars(n: int) -> tuple[Bar, ...]:
    return tuple(Bar(open=float(i), high=float(i), low=float(i), close=float(i)) for i in range(n))


def test_requesting_index_beyond_current_raises():
    view = build_data_view(_bars(10), up_to_index=3)
    assert view.current_index == 3
    with pytest.raises(LookAheadError):
        view[4]


def test_requesting_far_future_index_raises():
    view = build_data_view(_bars(10), up_to_index=3)
    with pytest.raises(LookAheadError):
        view[9]


def test_current_and_past_indices_are_readable():
    view = build_data_view(_bars(10), up_to_index=3)
    assert view[0].close == 0.0
    assert view[3].close == 3.0
    assert view.current_bar.close == 3.0


def test_negative_indexing_resolves_relative_to_current_bar():
    view = build_data_view(_bars(10), up_to_index=5)
    assert view[-1].close == 5.0  # current bar
    assert view[-2].close == 4.0  # one bar before

    with pytest.raises(LookAheadError):
        view[-100]  # before the start of visible history


def test_dataview_requires_at_least_one_visible_bar():
    with pytest.raises(ValueError):
        DataView(())


def test_build_data_view_rejects_out_of_range_index():
    with pytest.raises(ValueError):
        build_data_view(_bars(10), up_to_index=10)
    with pytest.raises(ValueError):
        build_data_view(_bars(10), up_to_index=-1)


# --- Reflection/attribute audit: no public attribute exposes future bar data ----------


def _visible_closes(value):
    """Recursively collect any Bar closes reachable from `value`."""
    if isinstance(value, Bar):
        return {value.close}
    if isinstance(value, (list, tuple, set, frozenset)):
        closes: set[float] = set()
        for item in value:
            closes |= _visible_closes(item)
        return closes
    return set()


def test_no_public_attribute_exposes_future_bar_data():
    all_bars = _bars(10)
    view = build_data_view(all_bars, up_to_index=3)
    future_closes = {bar.close for bar in all_bars[4:]}

    for name in dir(view):
        if name.startswith("_"):
            continue  # auditing the PUBLIC surface, per D32's own wording
        value = getattr(view, name)
        if callable(value):
            continue  # methods need args to call; not part of a passive attribute leak
        leaked = _visible_closes(value) & future_closes
        assert not leaked, f"public attribute '{name}' leaks future bar data: {leaked}"
