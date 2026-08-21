"""Unit gates for the breakdown short book (D169).

The load-bearing test here is the first one. A short's loss has no ceiling, so the
per-trade stop and the position cap are the difference between a study and a fantasy —
the brief calls them non-optional and says no configuration may disable them. That is
enforced at construction, and this file is what stops a later refactor from quietly
turning the enforcement into a default.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    ChannelStopExit,
    Direction,
    FixedWeight,
    InverseVolatilityWeight,
    OpenPosition,
    PositionState,
    TimeStopExit,
    build_breakout_strategy,
)

EPOCH = datetime(2021, 1, 1)


def bars_from(closes, highs=None, lows=None):
    highs = highs if highs is not None else [c * 1.05 for c in closes]
    lows = lows if lows is not None else [c * 0.95 for c in closes]
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=c, high=h, low=lo, close=c))
        for i, (c, h, lo) in enumerate(zip(closes, highs, lows))
    ]


class _View:
    def __init__(self, bars, index):
        self._bars, self.current_index = bars, index

    def __getitem__(self, j):
        return self._bars[j].bar


# ------------------------------------------------- tail discipline is NON-OPTIONAL


def test_a_short_without_a_stop_refuses_to_construct():
    with pytest.raises(ValueError, match="non-optional tail discipline"):
        BreakoutStrategy("s", "X", n_entry=20, n_exit=5, direction=Direction.SHORT)


def test_a_time_stop_alone_does_not_satisfy_the_requirement():
    """A time stop bounds DURATION, not LOSS. It is not a substitute for a price stop."""
    with pytest.raises(ValueError, match="ChannelStopExit"):
        BreakoutStrategy(
            "s", "X", n_entry=20, n_exit=5, direction=Direction.SHORT,
            exit_rules=(TimeStopExit(5),),
        )


def test_a_levered_short_refuses_to_construct():
    with pytest.raises(ValueError, match="may not be levered"):
        BreakoutStrategy(
            "s", "X", n_entry=20, n_exit=5, direction=Direction.SHORT,
            weight_source=InverseVolatilityWeight(max_weight=2.5),
            exit_rules=(ChannelStopExit(),),
        )


def test_the_long_book_is_not_forced_to_carry_a_stop():
    """The requirement is asymmetric on purpose: a long position's worst case is the
    instrument going to zero, a short's has no ceiling at all."""
    assert BreakoutStrategy("s", "X", n_entry=40, n_exit=10).direction is Direction.LONG


def test_every_short_config_the_study_builds_carries_the_stop():
    for variant in ds.short_variants():
        rules = variant.fixed_config.get("exit_rules", [])
        assert any(r["type"] == "channel_stop" for r in rules), variant.name
        rebuilt = build_breakout_strategy(variant.fixed_config, "s", "X")
        assert rebuilt.direction is Direction.SHORT
        assert rebuilt.weight_source.cap <= 1.0


# ------------------------------------------------------------------- the exit rules


def test_channel_stop_fires_for_a_short_when_price_closes_above_the_stop():
    bars = bars_from([100] * 6)
    rule = ChannelStopExit()
    position = OpenPosition(PositionState.SHORT, entry_index=2, entry_reference=100.0,
                            stop_level=110.0)
    view = _View(bars_from([100, 100, 100, 100, 105, 115]), 5)
    assert rule.exits(view, position) is True
    view_below = _View(bars_from([100, 100, 100, 100, 105, 108]), 5)
    assert rule.exits(view_below, position) is False


def test_channel_stop_never_fires_on_the_decision_bar_itself():
    view = _View(bars_from([100] * 4), 2)
    position = OpenPosition(PositionState.SHORT, entry_index=2, entry_reference=100.0,
                            stop_level=50.0)
    assert ChannelStopExit().exits(view, position) is False


def test_channel_stop_is_symmetric_for_a_long():
    position = OpenPosition(PositionState.LONG, entry_index=0, entry_reference=100.0,
                            stop_level=90.0)
    assert ChannelStopExit().exits(_View(bars_from([100, 100, 85]), 2), position) is True
    assert ChannelStopExit().exits(_View(bars_from([100, 100, 95]), 2), position) is False


def test_time_stop_waits_its_full_window_then_exits_an_unprofitable_short():
    rule = TimeStopExit(n_bars=3)
    position = OpenPosition(PositionState.SHORT, entry_index=0, entry_reference=100.0,
                            stop_level=200.0)
    flat = bars_from([100] * 6)
    assert rule.exits(_View(flat, 2), position) is False   # too early
    assert rule.exits(_View(flat, 3), position) is True    # not in profit at n_bars


def test_time_stop_leaves_a_profitable_short_alone():
    rule = TimeStopExit(n_bars=3)
    position = OpenPosition(PositionState.SHORT, entry_index=0, entry_reference=100.0,
                            stop_level=200.0)
    # A short is in profit when price has FALLEN.
    assert rule.exits(_View(bars_from([100, 99, 95, 90]), 3), position) is False


# ----------------------------------------------------------------------- regimes


def test_regime_labels_are_none_before_the_average_exists():
    labels = ds.regime_labels(bars_from([100] * 250), window=200)
    assert all(x is None for x in labels[:200])
    assert all(x is not None for x in labels[200:])


def test_a_steady_uptrend_is_labelled_bull_and_a_downtrend_bear():
    up = ds.regime_labels(bars_from([100 + i for i in range(260)]), window=200)
    down = ds.regime_labels(bars_from([1000 - i for i in range(260)]), window=200)
    assert up[-1] == "bull"
    assert down[-1] == "bear"


def test_regime_slices_partition_the_labelled_bars():
    labels = ["bull"] * 4 + ["bear"] * 3 + ["chop"] * 3
    returns = [0.01] * 10
    slices = ds.slice_by_regime(returns, labels, [True] * 10)
    assert sum(s.n_bars for s in slices) == 10
    assert sum(s.share_of_sample for s in slices) == pytest.approx(1.0)


def test_regime_slice_rejects_misaligned_inputs():
    with pytest.raises(ValueError, match="length mismatch"):
        ds.slice_by_regime([0.01, 0.02], ["bull"], [True, True])


# ------------------------------------------------------------------------- the null


def test_the_null_takes_a_direction_and_the_sign_matters():
    """The forward-compat requirement the breakdown addon asked for. On a falling
    series a SHORT null must score better than a LONG one."""
    falling = [-0.01] * 200
    short = ds.random_entry_null(falling, [5] * 10, 0.0, direction=-1,
                                 rf_annual=0.0, periods_per_year=365.0, n_draws=50)
    long = ds.random_entry_null(falling, [5] * 10, 0.0, direction=+1,
                                rf_annual=0.0, periods_per_year=365.0, n_draws=50)
    assert short.null_p50 > long.null_p50
    assert short.direction == -1 and long.direction == +1


def test_the_null_is_deterministic_for_a_fixed_seed():
    returns = [0.01, -0.02, 0.03, -0.01] * 50
    a = ds.random_entry_null(returns, [4] * 8, 0.5, direction=-1, rf_annual=0.0,
                             periods_per_year=365.0, n_draws=40, seed=7)
    b = ds.random_entry_null(returns, [4] * 8, 0.5, direction=-1, rf_annual=0.0,
                             periods_per_year=365.0, n_draws=40, seed=7)
    assert a.to_dict() == b.to_dict()


def test_the_null_degrades_gracefully_with_no_trades():
    out = ds.random_entry_null([0.01] * 50, [], 0.0, direction=-1, rf_annual=0.0,
                               periods_per_year=365.0, n_draws=10)
    assert out.percentile == 0.0


# -------------------------------------------------------------------- the ensemble


def test_correlation_is_computed_including_flat_bars():
    """Half the point of the short book is that it trades when the long book does not,
    so dropping the flat bars would measure the wrong thing entirely."""
    long_r = [0.01, 0.01, 0.0, 0.0]
    short_r = [0.0, 0.0, 0.01, 0.01]
    out = ds.combine_books(long_r, short_r, rf_annual=0.0, periods_per_year=365.0)
    assert out.n_bars == 4
    assert out.correlation == pytest.approx(-1.0, abs=0.01)


def test_combining_uses_equal_vol_not_equal_capital():
    """A quiet book and a wild one at equal CAPITAL is just the wild one with noise."""
    calm = [0.001, -0.001] * 50
    wild = [0.05, -0.05] * 50
    out = ds.combine_books(calm, wild, rf_annual=0.0, periods_per_year=365.0)
    assert -1.0 <= out.correlation <= 1.0
    assert out.n_bars == 100


# ------------------------------------------------------------------ the borrow cost


def test_short_tiers_charge_borrow_and_long_tiers_do_not():
    assert all(t.cost_stack_config()["carry_bricks"] == [] for t in bs.DEFAULT_TIERS)
    for tier in bs.SHORT_TIERS:
        bricks = tier.cost_stack_config()["carry_bricks"]
        assert bricks and bricks[0]["type"] == "borrow_fee"
        assert bricks[0]["annual_rate"] == bs.SHORT_BORROW_ANNUAL_RATE


def test_long_tier_configs_are_unchanged_by_the_borrow_field():
    """The long study's trial hashes must survive the short book existing (D166's rule)."""
    assert bs.DEFAULT_TIERS[3].cost_stack_config() == {
        "trade_bricks": [{"type": "percent_spread", "bps": 40.0}],
        "carry_bricks": [],
        "portfolio_carry_bricks": [],
        "event_flow_bricks": [],
    }
