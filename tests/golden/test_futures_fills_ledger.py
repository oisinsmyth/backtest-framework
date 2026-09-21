"""Golden-master ledger for the shared futures fill model (D587).

Every case's arithmetic is worked by hand in `test_futures_fills_ledger.hand.txt`, next to
this file, per D39 and CONTRIBUTING.md's rule that the ground truth is produced by a
calculator that never imports this codebase. The five-bar session is defined once there and
transcribed here; if the two ever disagree, the hand file is right and this file is wrong.

Anything touching money belongs in `tests/golden/`, and a fill price is money: it is the
single number that separates a study's gross from its net.
"""

from datetime import datetime

import numpy as np
import pytest

from backtest_framework.instruments.future import Future
from backtest_framework.simulator.fills import Bar
from backtest_framework.simulator.futures_fills import (
    ExitKind,
    Fill,
    FillAssumption,
    PassiveResult,
    PassiveSession,
    SessionOHLC,
    Side,
    assert_entry_before,
    entry_fill,
    passive_diagnostic,
    passive_limit,
    resolve_exit,
    running_peak_drawdown,
    stress_fill,
)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)

# Session A, hand file §"THE SESSION".
A_OPEN = np.array([5000.00, 5000.50, 5001.75, 5000.25, 4997.50])
A_HIGH = np.array([5001.00, 5002.00, 5003.00, 5000.50, 4999.00])
A_LOW = np.array([4999.00, 5000.50, 5000.00, 4997.00, 4996.50])
A_CLOSE = np.array([5000.50, 5001.75, 5002.25, 4997.50, 4998.75])
A = SessionOHLC(A_OPEN, A_HIGH, A_LOW, A_CLOSE)

# Session B, hand file §5.
B = SessionOHLC(
    np.array([5000.00, 5000.00, 5000.25, 5000.25, 5000.50]),
    np.array([5000.25, 5000.25, 5000.50, 5000.50, 5000.75]),
    np.array([4999.75, 5000.00, 5000.00, 5000.00, 5000.25]),
    np.array([5000.00, 5000.25, 5000.25, 5000.50, 5000.75]),
)

BAR0 = Bar(open=5000.00, high=5001.00, low=4999.00, close=5000.50)
BAR1 = Bar(open=5000.50, high=5002.00, low=5000.50, close=5001.75)
BAR3 = Bar(open=5000.25, high=5000.50, low=4997.00, close=4997.50)


# ------------------------------------------------------------------ §1 entry fill


def test_entry_fill_at_close_is_the_deposit_documents_convention():
    assert entry_fill(A_CLOSE, 0, Side.LONG, MES) == Fill(bar=1, price=5002.00)
    assert entry_fill(A_CLOSE, 0, Side.SHORT, MES) == Fill(bar=1, price=5001.50)


def test_entry_fill_at_open_is_d490s_convention():
    assert entry_fill(A_CLOSE, 0, Side.LONG, MES, at="open", open=A_OPEN) == Fill(1, 5000.75)
    assert entry_fill(A_CLOSE, 0, Side.SHORT, MES, at="open", open=A_OPEN) == Fill(1, 5000.25)


def test_entry_fill_concession_scales_with_ticks_adverse():
    assert entry_fill(A_CLOSE, 0, Side.LONG, MES, 0).price == 5001.75
    assert entry_fill(A_CLOSE, 0, Side.LONG, MES, 2).price == 5002.25


# ----------------------------------------------------------------- §2 stress fill


def test_stress_fill_picks_the_worst_close_for_the_direction():
    """Shock document's required unit test 10."""
    assert stress_fill(A_CLOSE, 0, Side.LONG, MES, k=4) == Fill(bar=2, price=5002.50)
    assert stress_fill(A_CLOSE, 0, Side.SHORT, MES, k=4) == Fill(bar=3, price=4997.25)


def test_stress_fill_window_shrinks_to_the_primary_fill_at_k_equals_one():
    assert stress_fill(A_CLOSE, 0, Side.LONG, MES, k=2) == Fill(bar=2, price=5002.50)
    assert stress_fill(A_CLOSE, 0, Side.LONG, MES, k=1) == entry_fill(A_CLOSE, 0, Side.LONG, MES)


def test_stress_fill_is_not_better_than_the_primary_fill():
    assert stress_fill(A_CLOSE, 0, Side.LONG, MES, k=4).price >= entry_fill(A_CLOSE, 0, Side.LONG, MES).price
    assert stress_fill(A_CLOSE, 0, Side.SHORT, MES, k=4).price <= entry_fill(A_CLOSE, 0, Side.SHORT, MES).price


# ------------------------------------------------------------- §3 exit resolution


def test_bar_spanning_stop_and_target_records_the_stop_long():
    """Ledger unit test 11 and shock unit test 9, long side."""
    r = resolve_exit(BAR3, stop=4998.00, target=5000.50, side=Side.LONG, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.STOP, 4998.00, False)


def test_bar_spanning_stop_and_target_records_the_stop_short():
    r = resolve_exit(BAR3, stop=5000.50, target=4997.00, side=Side.SHORT, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.STOP, 5000.50, False)


def test_target_alone_fills_at_the_level():
    r = resolve_exit(BAR3, stop=4990.00, target=5000.50, side=Side.LONG, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.TARGET, 5000.50, False)


def test_stop_gapped_through_fills_at_the_open():
    """D10, reached through `simulator.fills.stop_fill_price` rather than reimplemented."""
    r = resolve_exit(BAR3, stop=5000.75, target=5010.00, side=Side.LONG, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.STOP, 5000.25, True)


def test_target_gapped_past_in_our_favour_fills_at_the_open():
    r = resolve_exit(BAR1, stop=4990.00, target=5000.25, side=Side.LONG, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.TARGET, 5000.50, True)


def test_neither_level_reached():
    r = resolve_exit(BAR0, stop=4990.00, target=5010.00, side=Side.LONG, fut=MES)
    assert (r.kind, r.price, r.gapped) == (ExitKind.NONE, None, False)


def test_d490_trailing_stop_conventions_reproduce():
    knobs = dict(
        stop_rule=FillAssumption.TRADE_THROUGH, stop_slippage_ticks=1,
        gap_through=False, levels_on_grid=True,
    )
    through = resolve_exit(BAR3, 4997.25, 5010.00, Side.LONG, MES, **knobs)
    assert (through.kind, through.price) == (ExitKind.STOP, 4997.00)
    touched = resolve_exit(BAR3, 4997.00, 5010.00, Side.LONG, MES, **knobs)
    assert touched.kind is ExitKind.NONE


# --------------------------------------------------------------- §4 passive limit


def test_touch_and_trade_through_disagree_on_the_same_bar():
    touch = passive_limit(A_OPEN, A_HIGH, A_LOW, A_CLOSE, 0, Side.LONG, MES, 1, FillAssumption.TOUCH)
    assert touch == PassiveResult(filled=True, bar=1, price=5000.50)
    through = passive_limit(A_OPEN, A_HIGH, A_LOW, A_CLOSE, 0, Side.LONG, MES, 1)
    assert through == PassiveResult(filled=False, bar=None, price=None)


def test_trade_through_fills_at_the_limit_not_at_the_bars_open():
    r = passive_limit(A_OPEN, A_HIGH, A_LOW, A_CLOSE, 0, Side.LONG, MES, 4)
    assert r == PassiveResult(filled=True, bar=2, price=5000.50)
    assert r.price != A_OPEN[2], "a passive order is not credited with price improvement"


def test_short_limit_needs_the_bar_to_trade_up_through_it():
    r = passive_limit(A_OPEN, A_HIGH, A_LOW, A_CLOSE, 0, Side.SHORT, MES, 1)
    assert r == PassiveResult(filled=True, bar=1, price=5000.50)


# ----------------------------------------------------------- §5 passive diagnostic


def test_passive_diagnostic_ledger():
    out = passive_diagnostic(
        [PassiveSession(A, 0, Side.LONG), PassiveSession(B, 0, Side.LONG)],
        MES, horizon=4, cancel_after=4,
    )
    assert out["n"] == 2.0
    assert out["n_filled"] == 1.0
    assert out["n_unfilled"] == 1.0
    assert out["unfilled_rate"] == 0.5
    assert out["mean_outcome_filled"] == -7.0
    assert out["mean_outcome_unfilled"] == 3.0


# ----------------------------------------------------- §6 running-peak drawdown


def test_running_peak_drawdown_pessimistic_ledger():
    assert running_peak_drawdown(A_HIGH, A_LOW, Side.LONG, MES) == 6.50
    assert running_peak_drawdown(A_HIGH, A_LOW, Side.SHORT, MES) == 4.00


def test_running_peak_drawdown_in_ticks_and_dollars():
    points = running_peak_drawdown(A_HIGH, A_LOW, Side.LONG, MES)
    assert MES.ticks(points) == 26.0
    assert MES.usd(points, 1) == 32.50


# --------------------------------------------------------- §7 entry timing rule


@pytest.mark.parametrize(
    "hour, minute, second, accepted",
    [(14, 25, 0, True), (14, 25, 30, False), (14, 26, 0, False), (14, 29, 0, False), (13, 50, 0, True)],
)
def test_entry_must_complete_three_minutes_before_the_window(hour, minute, second, accepted):
    """Ledger's required unit test 10."""
    start = datetime(2019, 6, 3, 14, 28)
    ts = datetime(2019, 6, 3, hour, minute, second)
    if accepted:
        assert_entry_before(ts, start) is None
    else:
        with pytest.raises(ValueError, match="No trade"):
            assert_entry_before(ts, start)


def test_min_minutes_zero_still_rejects_an_entry_after_the_window_opens():
    start = datetime(2019, 6, 3, 14, 28)
    assert_entry_before(start, start, min_minutes=0) is None
    with pytest.raises(ValueError):
        assert_entry_before(datetime(2019, 6, 3, 14, 29), start, min_minutes=0)
