"""Offline tests for the terrain strategy harness (D196).

A strategy harness with an untested exit path is how a backtest lies quietly, so the
gates here are ordered by how much damage each failure would do:

- **Intrabar ordering is pessimistic.** When one bar's range covers both the stop and the
  target, the STOP is taken. OHLC does not say which came first and resolving that in the
  strategy's favour is how a backtest manufactures an edge.
- **The band is a per-bar series.** The scalar version risked >100% of capital on early
  BTC and produced a -105% short. That is pinned so it cannot come back.
- **The two fill assumptions actually differ** (D9), and the pessimistic one is the one
  that refuses fills the optimistic one grants.
- **The null is paired**: only the levels differ between arms.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain_strategies import (
    TRAIL_AFTER_R,
    FillAssumption,
    band_half_widths,
    buy_and_hold,
    compare_to_null,
    run_bounce_rr,
    run_touch_horizon,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2021, 1, 1)


def mk(rows):
    """rows: (open, high, low, close)."""
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=o, high=h, low=lo, close=c))
        for i, (o, h, lo, c) in enumerate(rows)
    ]


def flat(price, n):
    return [(price, price, price, price)] * n


WIDE = [1.0] * 400
"""A constant band, so tests exercise the strategy rather than the ATR."""


# ---------------------------------------------------------------- touch entries


def test_an_approach_from_above_is_a_long_and_from_below_a_short():
    """The bounce hypothesis and nothing else: buy demand, sell supply."""
    rows = flat(105.0, 3) + [(100.0, 100.0, 100.0, 100.0)] + flat(105.0, 3)
    rows += [(95.0, 95.0, 95.0, 95.0)] + flat(90.0, 3)
    bars = mk(rows)
    r = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, horizon=1)
    assert r.n_trades >= 1
    assert r.trades[0].direction == 1  # came from 105, above the level


def test_sitting_inside_the_band_counts_once_not_once_per_bar():
    rows = flat(105.0, 2) + flat(100.0, 5) + flat(105.0, 2)
    bars = mk(rows)
    r = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, horizon=1)
    assert r.n_trades == 1


def test_a_nan_band_before_warm_up_produces_no_trades():
    """NaN fails every comparison, so the guard is explicit rather than incidental."""
    bars = mk(flat(105.0, 3) + flat(100.0, 3))
    half = [float("nan")] * len(bars)
    assert run_touch_horizon(bars, {0: (100.0,)}, half, 0.0, 365.0).n_trades == 0


# ---------------------------------------------------------------- the per-bar band


def test_the_band_is_a_series_derived_from_the_rolling_atr():
    bars = mk([(100.0 + i, 101.0 + i, 99.0 + i, 100.0 + i) for i in range(60)])
    half = band_half_widths(bars, 20, 0.5)
    assert len(half) == len(bars)
    assert all(h != h for h in half[:20])  # NaN before the window fills
    assert half[-1] > 0.0


def test_a_band_wider_than_the_price_produces_no_trade():
    """The guard on the bug that produced a -105% short: a stop further away than the
    price itself is not a stop, it is a licence to lose more than the account."""
    rows = flat(12.0, 3) + [(10.0, 10.0, 10.0, 10.0)] + flat(12.0, 3)
    bars = mk(rows)
    huge = [50.0] * len(bars)  # band far wider than the $10 price
    r = run_bounce_rr(bars, {0: (10.0,)}, huge, 0.0, 365.0, 2.0, FillAssumption.TOUCH)
    assert r.n_trades == 0


def test_no_trade_can_lose_more_than_the_account():
    bars = mk([(100.0 + i % 7, 102.0 + i % 7, 98.0 + i % 7, 100.0 + i % 7) for i in range(300)])
    half = band_half_widths(bars, 20, 0.5)
    for fill in FillAssumption:
        r = run_bounce_rr(bars, {0: (100.0,), 100: (101.0,)}, half, 40.0, 365.0, 2.0, fill)
        assert all(x > -1.0 for x in r.net_returns), fill


# ---------------------------------------------------------------- intrabar ordering


def test_when_one_bar_covers_both_stop_and_target_the_stop_wins():
    """The single most important test here. OHLC cannot say which came first, so the
    pessimistic reading is taken — anything else invents an edge."""
    # Long entered at 100, stop 99, target 102. One bar spans 98..103.
    rows = flat(101.0, 2) + [(100.0, 100.0, 100.0, 100.0)] + [(100.0, 100.0, 100.0, 100.0)]
    rows += [(100.0, 103.0, 98.0, 100.0)] + flat(100.0, 5)
    bars = mk(rows)
    r = run_bounce_rr(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0,
                      FillAssumption.TOUCH)
    assert r.n_trades == 1
    assert r.trades[0].reason == "stop"
    assert r.trades[0].gross_return < 0.0


def test_a_target_alone_is_taken_when_the_stop_is_untouched():
    rows = flat(101.0, 2) + [(100.0, 100.0, 100.0, 100.0)] + [(100.0, 100.0, 100.0, 100.0)]
    rows += [(100.0, 103.0, 99.6, 102.5)] + flat(102.0, 5)
    bars = mk(rows)
    r = run_bounce_rr(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0,
                      FillAssumption.TOUCH)
    assert r.n_trades == 1 and r.trades[0].reason == "target"
    assert r.trades[0].gross_return == pytest.approx(0.02)


# ---------------------------------------------------------------- fill assumptions


def test_trade_through_refuses_a_fill_that_touch_grants():
    """D9's whole point: touch != fill, and bar-level limit fills are adversely selected."""
    rows = flat(101.0, 2) + [(100.5, 100.5, 100.0, 100.5)] + flat(101.0, 6)
    bars = mk(rows)
    args = ({0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0)
    touched = run_bounce_rr(bars, *args, FillAssumption.TOUCH)
    through = run_bounce_rr(bars, *args, FillAssumption.TRADE_THROUGH)
    assert touched.n_trades == 1  # the low exactly reaches 100.0
    assert through.n_trades == 0  # but never trades strictly through it


def test_trade_through_fills_when_price_goes_past_the_level():
    rows = flat(101.0, 2) + [(100.5, 100.5, 99.0, 100.0)] + flat(101.0, 6)
    bars = mk(rows)
    r = run_bounce_rr(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0,
                      FillAssumption.TRADE_THROUGH)
    assert r.n_trades == 1


# ---------------------------------------------------------------- trailing stop


def test_the_trail_does_not_engage_before_one_r():
    """Below 1R the trail would just be the entry stop under another name."""
    assert TRAIL_AFTER_R == 1.0
    # Rises to +0.5R then falls back to the original stop at 99.
    rows = flat(101.0, 2) + [(100.0, 100.0, 100.0, 100.0)] + [(100.0, 100.0, 100.0, 100.0)]
    rows += [(100.0, 100.5, 100.0, 100.5), (100.0, 100.0, 98.9, 99.0)] + flat(99.0, 4)
    bars = mk(rows)
    r = run_bounce_rr(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0,
                      FillAssumption.TOUCH)
    assert r.n_trades == 1 and r.trades[0].reason == "stop"
    assert r.trades[0].exit_price == pytest.approx(99.0)  # the ORIGINAL stop, not trailed


def test_one_position_at_a_time():
    bars = mk(flat(105.0, 2) + flat(100.0, 1) + flat(105.0, 1) + flat(100.0, 1) + flat(105.0, 20))
    r = run_bounce_rr(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, 2.0,
                      FillAssumption.TOUCH)
    for a, b in zip(r.trades, r.trades[1:]):
        assert b.entry_index > a.exit_index


# ---------------------------------------------------------------- equity and B&H


def test_the_equity_curve_marks_to_market_while_a_position_is_open():
    """Stepping only at exits would hide an open drawdown between entry and stop."""
    rows = flat(101.0, 2) + [(100.0, 100.0, 100.0, 100.0)]
    rows += [(100.0, 100.0, 99.5, 99.5), (99.5, 99.5, 99.5, 99.5)] + flat(99.5, 6)
    bars = mk(rows)
    r = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, horizon=5)
    curve = r.equity_curve(bars)
    assert len(curve) == len(bars)
    assert min(curve) < 1.0  # the open loss is visible before the exit


def test_max_drawdown_is_negative_or_zero():
    bars = mk(flat(105.0, 2) + flat(100.0, 1) + flat(90.0, 10))
    r = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0, horizon=5)
    assert r.max_drawdown(bars) <= 0.0


def test_buy_and_hold_measures_the_span_the_strategy_trades():
    bars = mk([(100.0 * 1.01**i,) * 4 for i in range(100)])
    bh = buy_and_hold(bars, 50, 365.0)
    assert bh["bars"] == 50
    assert bh["total_return"] == pytest.approx(1.01**49 - 1, rel=1e-9)
    assert bh["max_drawdown"] == pytest.approx(0.0)


# ---------------------------------------------------------------- the paired null


def test_the_null_changes_only_the_levels():
    """Pairing is enforced by the signature: `run` closes over everything but the levels."""
    bars = mk([(100.0 + 5 * math.sin(i / 3), 100.0 + 5 * math.sin(i / 3) + 1,
                100.0 + 5 * math.sin(i / 3) - 1, 100.0 + 5 * math.sin(i / 3))
               for i in range(400)])
    half = [1.0] * len(bars)
    seen = []

    def run(levels):
        seen.append(levels)
        return run_touch_horizon(bars, levels, half, 40.0, 365.0)

    levels = {0: (99.0, 101.0, 103.0)}
    cmp = compare_to_null(bars, levels, run, n_sims=5, seed=0)
    assert len(cmp.null_sharpes) == 5
    assert seen[0] is levels                       # the real arm gets the real levels
    assert all(len(x[0]) == 3 for x in seen[1:])   # the null arms get matched counts


def test_the_null_summary_reports_both_arms_trade_counts():
    """The H2 confound is visible rather than absorbed: real levels sit where price has
    been, so the arms can differ in trade count for reasons unrelated to skill."""
    bars = mk([(100.0 + 5 * math.sin(i / 3), 100.0 + 5 * math.sin(i / 3) + 1,
                100.0 + 5 * math.sin(i / 3) - 1, 100.0 + 5 * math.sin(i / 3))
               for i in range(400)])
    half = [1.0] * len(bars)
    cmp = compare_to_null(
        bars, {0: (99.0, 101.0, 103.0)},
        lambda lv: run_touch_horizon(bars, lv, half, 40.0, 365.0),
        n_sims=5, seed=0,
    )
    d = cmp.to_dict(bars, 365.0)
    assert "n_trades_real" in d and "n_trades_null_mean" in d
    assert 0.0 <= d["sharpe_percentile"] <= 100.0


def test_costs_reduce_every_trade():
    bars = mk(flat(105.0, 2) + flat(100.0, 1) + flat(105.0, 10))
    free = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 0.0, 365.0)
    paid = run_touch_horizon(bars, {0: (100.0,)}, [1.0] * len(bars), 40.0, 365.0)
    assert free.n_trades == paid.n_trades > 0
    for a, b in zip(free.net_returns, paid.net_returns):
        assert b == pytest.approx(a - 0.008)
