"""Unit gates for the swing-structure rules (D173).

The load-bearing test is `test_a_pivot_is_not_visible_until_k_bars_after_it_forms`. A
k-bar pivot needs the k bars AFTER it to be recognised, so any implementation that labels
pivots on the visible series without that offset is reading k bars into the future — and
it leaks invisibly, because the equity curve it produces looks entirely plausible. The
DataView would catch a crude version that indexed past the present; it cannot catch a
version that computes pivots from visible bars and simply forgets the lag. This file can.
"""

from __future__ import annotations

from datetime import datetime


from backtest_framework.engine.dataview import build_data_view
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    Direction,
    OpenPosition,
    PositionState,
    SwingStructureGate,
    SwingStructureStop,
    last_swings,
)

EPOCH = datetime(2021, 1, 1)


def bars(highs, lows=None):
    lows = lows if lows is not None else [h - 10 for h in highs]
    return [
        Bar(open=(h + lo) / 2, high=h, low=lo, close=(h + lo) / 2)
        for h, lo in zip(highs, lows)
    ]


# ------------------------------------------------------------ the look-ahead trap


def test_a_pivot_is_not_visible_until_k_bars_after_it_forms():
    """Bar 4 is an obvious swing high. With k=2 it cannot be KNOWN until bar 6."""
    series = bars([10, 11, 12, 13, 50, 13, 12, 11, 10])
    k = 2
    for current in (4, 5):
        view = build_data_view(series, current)
        assert 50 not in last_swings(view, current, k, +1, count=3), (
            f"the pivot at bar 4 was visible at bar {current}, {4 + k - current} bars early"
        )
    view = build_data_view(series, 6)
    assert last_swings(view, 6, k, +1, count=1) == [50]


def test_perturbing_bars_after_the_decision_cannot_change_a_pivot_already_reported():
    """The same guarantee stated the other way round: what the rule saw at bar i must not
    depend on anything after bar i."""
    base = bars([10, 11, 30, 11, 10, 11, 12, 11, 10])
    perturbed = list(base)
    perturbed[7] = Bar(open=999, high=9999, low=999, close=999)
    for current in range(5, 7):
        a = last_swings(build_data_view(base, current), current, 2, +1, count=2)
        b = last_swings(build_data_view(perturbed, current), current, 2, +1, count=2)
        assert a == b


# ---------------------------------------------------------------- pivot detection


def test_a_swing_high_is_the_strict_unique_maximum_of_its_window():
    view = build_data_view(bars([10, 11, 20, 11, 10]), 4)
    assert last_swings(view, 4, 2, +1, count=1) == [20]


def test_equal_extremes_produce_no_pivot():
    """The stated tie convention: strict and unique, so a plateau yields nothing rather
    than an arbitrary pick between two identical bars."""
    view = build_data_view(bars([10, 20, 20, 11, 10]), 4)
    assert last_swings(view, 4, 2, +1, count=3) == []


def test_swing_lows_mirror_swing_highs():
    series = bars([30, 29, 28, 29, 30], lows=[20, 19, 5, 19, 20])
    view = build_data_view(series, 4)
    assert last_swings(view, 4, 2, -1, count=1) == [5]


def test_swings_come_back_newest_first():
    # Pivots at index 2 and index 6. Note the first candidate index is k, not 0: a pivot
    # at index 1 with k=2 would need bar -1 to evaluate, so it can never be confirmed.
    series = bars([10, 11, 40, 11, 10, 11, 50, 11, 10, 11, 10])
    view = build_data_view(series, 10)
    assert last_swings(view, 10, 2, +1, count=2) == [50, 40]


def test_a_pivot_too_close_to_the_start_is_never_confirmable():
    """It needs k bars on BOTH sides, so the first k bars can never be pivots."""
    series = bars([99, 10, 11, 12, 13, 12, 11])
    view = build_data_view(series, 6)
    assert 99 not in last_swings(view, 6, 2, +1, count=5)


# --------------------------------------------------------------------- the stop


def test_the_stop_sits_at_the_last_confirmed_swing_against_the_trade():
    series = bars([10, 11, 40, 11, 10, 11, 10])
    view = build_data_view(series, 6)
    short = OpenPosition(PositionState.SHORT, entry_index=0, entry_reference=20.0, stop_level=0.0)
    assert SwingStructureStop(k=2).stop_level(view, short) == 40.0

    lows = [20, 19, 1, 19, 20, 19, 20]
    view_l = build_data_view(bars([30] * 7, lows=lows), 6)
    long = OpenPosition(PositionState.LONG, entry_index=0, entry_reference=20.0, stop_level=0.0)
    assert SwingStructureStop(k=2).stop_level(view_l, long) == 1.0


def test_the_stop_proposes_nothing_when_no_pivot_is_confirmed_yet():
    view = build_data_view(bars([10, 11, 12, 13, 14]), 4)
    position = OpenPosition(PositionState.SHORT, 0, 12.0, 0.0)
    assert SwingStructureStop(k=2).stop_level(view, position) is None


def test_the_stop_never_exits_on_its_own():
    """Like every stop rule since D170: it places a level, the engine enforces it."""
    view = build_data_view(bars([10, 11, 40, 11, 10, 11, 10]), 6)
    position = OpenPosition(PositionState.SHORT, 0, 20.0, 40.0)
    assert SwingStructureStop(k=2).exits(view, position) is False


# --------------------------------------------------------------------- the gate


def _gate_series_downtrend():
    # Two lower highs and two lower lows, with clean pivots at k=1.
    highs = [50, 40, 50, 45, 30, 45, 40, 20, 40]
    lows = [20, 10, 20, 18, 5, 18, 15, 2, 15]
    return bars(highs, lows)


def test_the_gate_admits_a_short_only_when_structure_is_a_downtrend():
    view = build_data_view(_gate_series_downtrend(), 8)
    short_gate = SwingStructureGate(k=1, direction=Direction.SHORT)
    long_gate = SwingStructureGate(k=1, direction=Direction.LONG)
    assert short_gate.accepts(view, lambda _i: True) is True
    assert long_gate.accepts(view, lambda _i: True) is False


def test_ambiguous_structure_is_a_veto_not_a_coin_flip():
    """Higher highs with lower lows is a broadening range, not a trend. Neither side may
    trade it — on this data structure was unambiguous only about half the time, so a gate
    that forced a direction would be inventing a signal."""
    highs = [30, 20, 35, 20, 40, 20, 45]
    lows = [10, 5, 8, 3, 6, 1, 4]
    view = build_data_view(bars(highs, lows), 6)
    for d in (Direction.LONG, Direction.SHORT):
        assert SwingStructureGate(k=1, direction=d).accepts(view, lambda _i: True) is False


def test_the_gate_vetoes_before_enough_structure_exists():
    view = build_data_view(bars([10, 11, 12, 13, 14]), 4)
    gate = SwingStructureGate(k=2, direction=Direction.SHORT)
    assert gate.accepts(view, lambda _i: True) is False


def test_gate_config_round_trips_and_omits_the_long_default():
    from backtest_framework.strategies.breakout import build_entry_filter

    assert SwingStructureGate(k=3).config() == {"type": "swing_structure_gate", "k": 3}
    short = SwingStructureGate(k=3, direction=Direction.SHORT).config()
    assert short["direction"] == "short"
    assert build_entry_filter(short).direction is Direction.SHORT


def test_stop_config_round_trips():
    from backtest_framework.strategies.breakout import build_exit_rule

    config = SwingStructureStop(k=2).config()
    assert config == {"type": "swing_structure_stop", "k": 2}
    assert build_exit_rule(config).k == 2
