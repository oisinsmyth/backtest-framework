"""The shared futures fill model (D587): guards, the adapter, and the self-test's own gate.

Gate U. The hand-computed ledger for every fill is in `tests/golden/test_futures_fills_ledger.py`;
this file is about what happens when the inputs are WRONG — which is most of what a fill model
has to get right, because a study that silently truncates a stress window or transposes a side
produces a number rather than an error.

**No panel is read here.** The equality guards against `run_d490_range_reversion.py` and
`d465_es_spread_and_mae_bias.py` run on the ES fixture and live in D587's record, not in the
suite: they are R16 identity checks on a build, not invariants of this module.
"""

import math
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from backtest_framework.instruments.future import Future
from backtest_framework.simulator.fills import Bar
from backtest_framework.simulator.futures_fills import (
    ExitKind,
    FillAssumption,
    PassiveSession,
    SessionOHLC,
    Side,
    _expect_raise,
    adverse_price,
    assert_entry_before,
    bar_at,
    entry_fill,
    passive_diagnostic,
    passive_limit,
    resolve_exit,
    running_peak_drawdown,
    selftest,
    session_ohlc,
    stress_fill,
)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)

OPEN = np.array([5000.00, 5000.50, 5001.75, 5000.25, 4997.50])
HIGH = np.array([5001.00, 5002.00, 5003.00, 5000.50, 4999.00])
LOW = np.array([4999.00, 5000.50, 5000.00, 4997.00, 4996.50])
CLOSE = np.array([5000.50, 5001.75, 5002.25, 4997.50, 4998.75])
OHLC = SessionOHLC(OPEN, HIGH, LOW, CLOSE)


# ------------------------------------------------------------------ the self-test


def test_module_selftest_passes():
    assert selftest(log=lambda *_: None) == 0


def test_the_selftest_helper_can_itself_fail():
    """A self-test that cannot fail is worse than none.

    `_expect_raise` is the only thing standing between "every audit fires" and "every audit
    was written down", so it gets its own known-answer case: handed a function that does NOT
    raise, it must complain rather than pass.
    """
    with pytest.raises(AssertionError, match="did not raise"):
        _expect_raise(lambda: None, ValueError, "a function that cannot fail", log=lambda *_: None)
    with pytest.raises(TypeError):
        # the WRONG exception type must propagate, not be swallowed as "it raised, good enough"
        _expect_raise(lambda: (_ for _ in ()).throw(TypeError("x")), ValueError, "x", log=lambda *_: None)


# ------------------------------------------------------------------- the adapter


def test_session_ohlc_reads_a_dataframe_by_column_name():
    frame = pd.DataFrame({"low": LOW, "close": CLOSE, "open": OPEN, "high": HIGH, "volume": np.arange(5)})
    s = session_ohlc(frame)
    assert np.array_equal(s.open, OPEN) and np.array_equal(s.close, CLOSE)
    assert np.array_equal(s.high, HIGH) and np.array_equal(s.low, LOW)


def test_session_ohlc_names_the_missing_column():
    frame = pd.DataFrame({"open": OPEN, "high": HIGH, "low": LOW})
    with pytest.raises(KeyError, match="close"):
        session_ohlc(frame)


def test_bar_at_hands_back_the_shape_the_gap_rule_speaks():
    assert bar_at(OHLC, 3) == Bar(open=5000.25, high=5000.50, low=4997.00, close=4997.50)
    with pytest.raises(ValueError, match="past the session end"):
        bar_at(OHLC, 5)


# -------------------------------------------------------------- the concession sign


@pytest.mark.parametrize(
    "side, closing, expected",
    [
        (Side.LONG, False, 5000.25),   # opening a long: pay up
        (Side.SHORT, False, 4999.75),  # opening a short: sell down
        (Side.LONG, True, 4999.75),    # closing a long: sell down
        (Side.SHORT, True, 5000.25),   # closing a short: buy up
    ],
)
def test_adverse_price_signs(side, closing, expected):
    """All four cells, in money. A sign asserted in prose inverted D280."""
    assert adverse_price(5000.00, side, 1, MES, closing=closing) == expected


def test_adverse_price_rejects_a_negative_concession():
    with pytest.raises(ValueError, match="non-negative"):
        adverse_price(5000.00, Side.LONG, -1, MES)


# ------------------------------------------------------------------- side guards


@pytest.mark.parametrize(
    "call",
    [
        lambda s: entry_fill(CLOSE, 0, s, MES),
        lambda s: stress_fill(CLOSE, 0, s, MES, k=2),
        lambda s: resolve_exit(bar_at(OHLC, 3), 4998.0, 5010.0, s, MES),
        lambda s: passive_limit(OPEN, HIGH, LOW, CLOSE, 0, s, MES, 2),
        lambda s: adverse_price(5000.0, s, 1, MES),
        lambda s: running_peak_drawdown(HIGH, LOW, s, MES),
    ],
)
@pytest.mark.parametrize("bad_side", ["long", 1, -1, None])
def test_every_entry_point_rejects_a_side_that_is_not_a_Side(call, bad_side):
    with pytest.raises(TypeError, match="Side"):
        call(bad_side)


# --------------------------------------------------------------- window guards


def test_entry_fill_rejects_a_fill_bar_past_the_session_end():
    with pytest.raises(ValueError, match="past the session end"):
        entry_fill(CLOSE, 4, Side.LONG, MES)


def test_stress_fill_rejects_a_window_past_the_session_end_rather_than_truncating():
    stress_fill(CLOSE, 0, Side.LONG, MES, k=4)
    with pytest.raises(ValueError, match="not silently truncated"):
        stress_fill(CLOSE, 1, Side.LONG, MES, k=4)


def test_stress_fill_rejects_a_zero_length_window():
    with pytest.raises(ValueError, match="at least 1"):
        stress_fill(CLOSE, 0, Side.LONG, MES, k=0)


def test_passive_limit_rejects_a_cancel_window_past_the_session_end():
    passive_limit(OPEN, HIGH, LOW, CLOSE, 0, Side.LONG, MES, 4)
    with pytest.raises(ValueError, match="past the session end"):
        passive_limit(OPEN, HIGH, LOW, CLOSE, 0, Side.LONG, MES, 5)


def test_entry_fill_at_open_needs_the_open_array_and_will_not_substitute_the_close():
    with pytest.raises(ValueError, match="different fill convention"):
        entry_fill(CLOSE, 0, Side.LONG, MES, at="open")
    with pytest.raises(ValueError, match="different lengths"):
        entry_fill(CLOSE, 0, Side.LONG, MES, at="open", open=OPEN[:3])
    with pytest.raises(ValueError, match="'close' or 'open'"):
        entry_fill(CLOSE, 0, Side.LONG, MES, at="settle")


# ------------------------------------------------------------------- data guards


def test_an_off_grid_anchor_is_rejected():
    dirty = CLOSE.copy()
    dirty[1] = 5001.80
    with pytest.raises(ValueError, match="off the 0.25 grid"):
        entry_fill(dirty, 0, Side.LONG, MES)


def test_a_missing_bar_is_not_a_price():
    dirty = CLOSE.copy()
    dirty[1] = np.nan
    with pytest.raises(ValueError, match="not finite"):
        entry_fill(dirty, 0, Side.LONG, MES)
    with pytest.raises(ValueError, match="non-finite"):
        stress_fill(dirty, 0, Side.LONG, MES, k=3)


@pytest.mark.parametrize(
    "bar, why",
    [
        (Bar(open=5000.0, high=4999.0, low=5001.0, close=5000.0), "high"),
        (Bar(open=5010.0, high=5001.0, low=4999.0, close=5000.0), "open"),
        (Bar(open=5000.0, high=5001.0, low=4999.0, close=5010.0), "close"),
    ],
)
def test_resolve_exit_rejects_a_bar_that_is_not_a_bar(bar, why):
    with pytest.raises(ValueError, match=why):
        resolve_exit(bar, 4990.0, 5010.0, Side.LONG, MES)


def test_resolve_exit_rejects_off_grid_levels_unless_told_they_are_not_on_the_grid():
    bar = bar_at(OHLC, 3)
    with pytest.raises(ValueError, match="stop level"):
        resolve_exit(bar, 4998.10, 5010.0, Side.LONG, MES)
    with pytest.raises(ValueError, match="target level"):
        resolve_exit(bar, 4990.0, 5000.30, Side.LONG, MES)
    loose = resolve_exit(bar, 4998.10, 5010.0, Side.LONG, MES, levels_on_grid=False)
    assert (loose.kind, loose.price) == (ExitKind.STOP, 4998.10)


def test_resolve_exit_with_no_levels_at_all_is_a_no_op():
    assert resolve_exit(bar_at(OHLC, 3), None, None, Side.LONG, MES).kind is ExitKind.NONE


def test_running_peak_drawdown_rejects_a_ragged_or_off_grid_path():
    with pytest.raises(ValueError, match="different lengths"):
        running_peak_drawdown(HIGH, LOW[:3], Side.LONG, MES)
    dirty = HIGH.copy()
    dirty[2] = 5003.10
    with pytest.raises(ValueError, match="off the 0.25 grid"):
        running_peak_drawdown(dirty, LOW, Side.LONG, MES)


# -------------------------------------------------------------- passive diagnostic


def test_passive_diagnostic_reports_counts_beside_an_empty_group_mean():
    out = passive_diagnostic([PassiveSession(OHLC, 0, Side.LONG)], MES, horizon=4, cancel_after=4)
    assert out["n"] == 1.0 and out["n_filled"] == 1.0 and out["n_unfilled"] == 0.0
    assert out["unfilled_rate"] == 0.0
    assert math.isnan(out["mean_outcome_unfilled"])


def test_passive_diagnostic_guards_its_inputs():
    with pytest.raises(ValueError, match="no sessions"):
        passive_diagnostic([], MES, horizon=1)
    with pytest.raises(ValueError, match="at least 1 bar"):
        passive_diagnostic([PassiveSession(OHLC, 0, Side.LONG)], MES, horizon=0)
    with pytest.raises(ValueError, match="past the session end"):
        passive_diagnostic([PassiveSession(OHLC, 2, Side.LONG)], MES, horizon=4, cancel_after=2)
    with pytest.raises(TypeError, match="PassiveSession"):
        passive_diagnostic([OHLC], MES, horizon=1)


def test_the_diagnostic_outcome_is_signed_by_the_side():
    long_out = passive_diagnostic([PassiveSession(OHLC, 0, Side.LONG)], MES, horizon=4, cancel_after=4)
    short_out = passive_diagnostic([PassiveSession(OHLC, 0, Side.SHORT)], MES, horizon=4, cancel_after=4)
    assert long_out["mean_outcome_filled"] == -short_out["mean_outcome_filled"]


# ------------------------------------------------------------------ timing guard


def test_assert_entry_before_needs_timestamps():
    with pytest.raises(TypeError, match="subtractable"):
        assert_entry_before("14:25", datetime(2019, 6, 3, 14, 28))
    with pytest.raises(ValueError, match="non-negative"):
        assert_entry_before(datetime(2019, 6, 3, 14, 20), datetime(2019, 6, 3, 14, 28), min_minutes=-1)


def test_assert_entry_before_accepts_pandas_timestamps():
    assert_entry_before(pd.Timestamp("2019-06-03 14:25"), pd.Timestamp("2019-06-03 14:28"))
    with pytest.raises(ValueError, match="No trade"):
        assert_entry_before(pd.Timestamp("2019-06-03 14:27"), pd.Timestamp("2019-06-03 14:28"))


# ------------------------------------------- the epsilon, which is the whole point


OFF_GRID_BAR = Bar(open=4998.00, high=4998.50, low=4997.00, close=4997.25)
"""Reached 4997.10 and 4998.40, but traded through neither by a tick. Both levels are off
the 0.25 grid, which is the only way the two epsilons can be told apart: on the grid,
`low <= stop - tick` and `low < stop` are the same statement."""


@pytest.mark.parametrize(
    "side, stop, target",
    [
        (Side.LONG, 4997.10, 5010.00),
        (Side.SHORT, 4998.40, 4990.00),
    ],
)
def test_stop_trade_through_epsilon_is_one_tick_not_an_absolute_1e_9(side, stop, target):
    """The disagreement with `research/terrain_strategies.py:TRADE_THROUGH_EPS = 1e-9`.

    An absolute 1e-9 would fill both of these, because the bar reached the level; a
    one-tick epsilon does not, because the bar never traded a tick beyond it. This test
    is the only thing in the suite that can tell the two rules apart, and it exists
    because a deliberate 1e-9 mutation survived every other gate.
    """
    through = resolve_exit(OFF_GRID_BAR, stop, target, side, MES,
                           stop_rule=FillAssumption.TRADE_THROUGH, levels_on_grid=False)
    assert through.kind is ExitKind.NONE, "an absolute 1e-9 epsilon would have filled this"
    touch = resolve_exit(OFF_GRID_BAR, stop, target, side, MES,
                         stop_rule=FillAssumption.TOUCH, levels_on_grid=False)
    assert (touch.kind, touch.price) == (ExitKind.STOP, stop)


@pytest.mark.parametrize(
    "side, target, touch_price",
    [
        (Side.LONG, 4998.40, 4998.40),
        (Side.SHORT, 4997.10, 4997.10),
    ],
)
def test_target_trade_through_epsilon_is_one_tick_too(side, target, touch_price):
    through = resolve_exit(OFF_GRID_BAR, None, target, side, MES,
                           target_rule=FillAssumption.TRADE_THROUGH, levels_on_grid=False)
    assert through.kind is ExitKind.NONE
    touch = resolve_exit(OFF_GRID_BAR, None, target, side, MES,
                         target_rule=FillAssumption.TOUCH, levels_on_grid=False)
    assert (touch.kind, touch.price) == (ExitKind.TARGET, touch_price)


# ------------------------------------------------------ the pessimism, once more


def test_nothing_can_return_a_target_from_a_bar_whose_stop_was_also_inside():
    """The rule all three deposit documents state, checked on both sides and both rules."""
    bar = bar_at(OHLC, 3)  # low 4997.00, high 5000.50
    for stop_rule in FillAssumption:
        for target_rule in FillAssumption:
            long_r = resolve_exit(bar, 4998.0, 5000.0, Side.LONG, MES,
                                  stop_rule=stop_rule, target_rule=target_rule)
            assert long_r.kind is ExitKind.STOP, (stop_rule, target_rule)
            short_r = resolve_exit(bar, 5000.0, 4998.0, Side.SHORT, MES,
                                   stop_rule=stop_rule, target_rule=target_rule)
            assert short_r.kind is ExitKind.STOP, (stop_rule, target_rule)
