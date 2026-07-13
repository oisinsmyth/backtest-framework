"""Integration test for D32: a deliberately cheating strategy cannot obtain future bars.

This asserts the exception (or the absence of any exploitable surface), not the honour
system — every attack vector here is something a strategy author coming from pandas
habits, or actively trying to cheat, would plausibly reach for.
"""

import pytest

from backtest_framework.engine.dataview import LookAheadError, build_data_view
from backtest_framework.simulator.fills import Bar


def _bars(n: int) -> tuple[Bar, ...]:
    return tuple(Bar(open=float(i), high=float(i), low=float(i), close=float(i)) for i in range(n))


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
    # instance's own state contains a future bar.
    future_closes = {bar.close for bar in all_bars[4:]}
    for value in vars(view).values():
        if isinstance(value, tuple):
            observed_closes = {b.close for b in value if isinstance(b, Bar)}
            assert not (observed_closes & future_closes)
