"""Unit gates for the Phase 1.1 additions: the sign-parameterized breakout brick
(D166) and the at-trigger feature layer (D167).

The load-bearing tests here are the two that would silently corrupt conclusions rather
than fail loudly:

- **the trigger bar is `entry_index - 1`**, not the entry bar. Getting this wrong is a
  one-bar look-ahead that lives entirely inside the diagnostics, so no engine property
  test would catch it and every P&L number would stay correct while every statement
  about which triggers were good became false.
- **a long-flat config still hashes as it did in v1.** The sign parameterization is
  supposed to be invisible to a long-only run; if `direction` leaked into `config()` at
  its default, all 184 v1 trial hashes would change while nothing about the runs did.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.backtest import BacktestResult
from backtest_framework.research.feature_analysis import analyse_feature, spearman
from backtest_framework.research.trade_diagnostics import (
    FEATURE_NAMES,
    FEATURE_UNAVAILABLE,
    breadth_series,
    extract_episodes,
    hours_to_next_expiry,
    last_friday,
    trigger_features,
)
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    ChannelStopExit,
    Direction,
    PositionState,
    TrendGateFilter,
    build_breakout_strategy,
)

EPOCH = datetime(2021, 1, 1)
SYMBOL = "X"


def bars_from(closes, highs=None, lows=None):
    highs = highs if highs is not None else [c * 1.05 for c in closes]
    lows = lows if lows is not None else [c * 0.95 for c in closes]
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=c, high=h, low=lo, close=c))
        for i, (c, h, lo) in enumerate(zip(closes, highs, lows))
    ]


# --------------------------------------------------------------- D166: sign parameterization


def test_long_flat_config_is_byte_identical_to_v1():
    """`direction` must not appear at its default, or every v1 trial hash changes."""
    config = BreakoutStrategy(
        "s", SYMBOL, n_entry=40, n_exit=10, filters=(TrendGateFilter(200),)
    ).config()
    assert "direction" not in config
    assert "direction" not in config["filters"][0]


def test_short_config_is_explicit_and_round_trips():
    original = BreakoutStrategy(
        "s",
        SYMBOL,
        n_entry=40,
        n_exit=10,
        direction=Direction.SHORT,
        filters=(TrendGateFilter(200, direction=Direction.SHORT),),
        # D169 made the per-trade stop non-optional on the short side, so a short
        # strategy no longer constructs without one. This test predates that rule.
        exit_rules=(ChannelStopExit(),),
    )
    config = original.config()
    assert config["direction"] == "short"
    rebuilt = build_breakout_strategy(config, "s", SYMBOL)
    assert rebuilt.direction is Direction.SHORT
    assert rebuilt.filters[0].direction is Direction.SHORT


def test_an_unknown_direction_is_rejected_rather_than_defaulted():
    """A typo must not silently produce a long book."""
    config = BreakoutStrategy("s", SYMBOL, n_entry=4, n_exit=2).config()
    config["direction"] = "lnog"
    with pytest.raises(Exception, match="direction"):
        build_breakout_strategy(config, "s", SYMBOL)


class _View:
    def __init__(self, bars, index):
        self._bars, self.current_index = bars, index

    def __getitem__(self, j):
        return self._bars[j].bar


def test_short_channel_logic_mirrors_long_exactly():
    bars = bars_from([10, 11, 12, 13, 14, 15])
    long_side = BreakoutStrategy("s", SYMBOL, n_entry=5, n_exit=3)
    short_side = BreakoutStrategy(
        "s", SYMBOL, n_entry=5, n_exit=3, direction=Direction.SHORT,
        exit_rules=(ChannelStopExit(),),
    )
    view = _View(bars, 5)

    assert long_side.entry_level(view, 5) == max(b.bar.high for b in bars[0:5])
    assert short_side.entry_level(view, 5) == min(b.bar.low for b in bars[0:5])
    # The exit channel is taken AGAINST the trade direction on both sides.
    assert long_side.exit_level(view, 5) == min(b.bar.low for b in bars[2:5])
    assert short_side.exit_level(view, 5) == max(b.bar.high for b in bars[2:5])


def test_position_state_carries_the_sign_so_a_short_emits_a_negative_weight():
    assert PositionState.LONG * 0.4 == pytest.approx(0.4)
    assert PositionState.SHORT * 0.4 == pytest.approx(-0.4)
    assert PositionState.FLAT * 0.4 == 0.0


# ------------------------------------------------------------------ D167: feature layer


def test_features_are_read_off_the_trigger_bar_not_the_entry_bar():
    """The decision bar is the one BEFORE the entry fill (D103 next-open fills).

    Constructed so the two bars disagree: the trigger bar closes at its low (CLV 0) and
    the entry bar closes at its high (CLV 1). Reading the wrong bar flips F3 from 0 to 1.
    """
    bars = [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=100, high=110, low=90, close=100))
        for i in range(5)
    ]
    bars[2] = TimestampedBar(bars[2].timestamp, Bar(open=100, high=110, low=90, close=90))
    bars[3] = TimestampedBar(bars[3].timestamp, Bar(open=100, high=110, low=90, close=110))

    result = BacktestResult()
    result.fills = [
        (bars[3].timestamp, SYMBOL, 1.0, 100.0, 0.0),
        (bars[4].timestamp, SYMBOL, -1.0, 100.0, 0.0),
    ]
    episodes = extract_episodes(
        result, SYMBOL, bars, features_at=lambda i: trigger_features(bars, i)
    )
    assert episodes[0].entry_index == 3
    # Trigger bar is index 2, which closed on its low.
    assert episodes[0].features["F3"] == pytest.approx(0.0)


def test_blocked_features_are_present_and_none_never_absent():
    bars = bars_from([100] * 60)
    features = trigger_features(bars, 55)
    assert set(features) == set(FEATURE_NAMES)
    # F5 is still blocked: no derivatives plumbing exists.
    assert features["F5"] is None
    assert "F5" in FEATURE_UNAVAILABLE
    # F2 is NOT blocked any more (D168 closed the D111 gap). It is None here only
    # because this call supplied no volumes, which is a different statement — the
    # distinction is exactly what FEATURE_UNAVAILABLE encodes.
    assert "F2" not in FEATURE_UNAVAILABLE
    assert features["F2"] is None


def test_f2_is_computed_when_volumes_are_supplied():
    bars = bars_from([100] * 60)
    volumes = [100.0] * 60
    volumes[55] = 250.0
    features = trigger_features(bars, 55, volumes=volumes)
    # Baseline is bars 35..54, all 100.0 -> mean 100.0; the trigger bar is 250.0.
    assert features["F2"] == pytest.approx(2.5)


def test_f2_baseline_excludes_the_trigger_bar():
    """If the trigger bar's own volume entered the average it has to beat, a large bar
    would inflate its own threshold and the ratio would be understated."""
    bars = bars_from([100] * 60)
    volumes = [100.0] * 60
    volumes[55] = 2100.0
    ratio = trigger_features(bars, 55, volumes=volumes)["F2"]
    # Excluding the trigger bar: 2100 / 100 = 21.0.
    # Including it, the mean would be (19*100 + 2100)/20 = 200 -> ratio 10.5.
    assert ratio == pytest.approx(21.0)


def test_f2_is_none_when_a_volume_is_missing_in_the_window():
    bars = bars_from([100] * 60)
    volumes: list = [100.0] * 60
    volumes[40] = None
    assert trigger_features(bars, 55, volumes=volumes)["F2"] is None


def test_close_location_value_is_none_on_a_zero_range_bar_rather_than_a_divide_by_zero():
    bars = [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=100, high=100, low=100, close=100))
        for i in range(5)
    ]
    assert trigger_features(bars, 3)["F3"] is None


def test_extension_is_none_before_its_own_warm_up_and_a_number_after():
    bars = bars_from([100 + i for i in range(80)])
    assert trigger_features(bars, 10)["F1"] is None
    assert trigger_features(bars, 70)["F1"] is not None


def test_breadth_uses_only_completed_bars():
    """Perturbing a bar AFTER timestamp t must not change breadth at t."""
    a = bars_from([100 + i for i in range(80)])
    b = bars_from([100 + i for i in range(80)])
    before = breadth_series({"A": a, "B": b})
    target = a[60].timestamp

    a_perturbed = list(a)
    a_perturbed[70] = TimestampedBar(a[70].timestamp, Bar(open=1e6, high=1e6, low=1e6, close=1e6))
    after = breadth_series({"A": a_perturbed, "B": b})
    assert before[target] == after[target]


def test_breadth_on_a_two_instrument_universe_can_only_take_three_values():
    """Recorded because it is the mechanical reason F4 is underpowered here."""
    rising = bars_from([100 + i for i in range(80)])
    falling = bars_from([200 - i for i in range(80)])
    values = set(breadth_series({"A": rising, "B": falling}).values())
    assert values <= {0.0, 0.5, 1.0}


def test_deribit_expiry_is_the_last_friday_at_0800_utc():
    for year, month in ((2026, 1), (2026, 2), (2026, 8), (2026, 12)):
        assert last_friday(year, month).weekday() == 4
    # 2026-08-28 is the last Friday of August; 08:00 on that day is 200h from the 20th.
    assert hours_to_next_expiry(datetime(2026, 8, 20)) == pytest.approx(200.0)
    # Past August's expiry, the next one is September's.
    assert hours_to_next_expiry(datetime(2026, 8, 29)) == pytest.approx(656.0)


def test_expiry_distance_is_never_negative():
    for day in range(1, 29):
        assert hours_to_next_expiry(datetime(2026, 2, day)) >= 0.0


# ------------------------------------------------------------- D167: analysis verdicts


def test_spearman_handles_ties_and_constants():
    assert spearman([1, 2, 3], [1, 2, 3]) == pytest.approx(1.0)
    assert spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert spearman([1, 1, 1], [1, 2, 3]) is None
    assert spearman([1, 1, 2, 2], [1, 1, 2, 2]) == pytest.approx(1.0)


def _episode(value, mfe, bars_held=10, net=1.0):
    from backtest_framework.research.trade_diagnostics import TradeEpisode

    return TradeEpisode(
        entry_timestamp=EPOCH + timedelta(days=int(value * 1000) % 4000),
        exit_timestamp=EPOCH + timedelta(days=4100),
        entry_index=1,
        exit_index=2,
        bars_held=bars_held,
        entry_price=100.0,
        exit_price=100.0 + net,
        gross_pnl=net,
        costs=0.0,
        rebalance_costs=0.0,
        traded_notional=100.0,
        n_fills=2,
        mfe=mfe,
        mae=-0.05,
        features={"F1": value},
    )


def test_a_feature_below_the_trade_floor_is_underpowered_not_verdicted():
    episodes = [_episode(i, i / 10) for i in range(5)]
    verdict = analyse_feature(episodes, "F1")
    assert verdict.verdict == "UNDERPOWERED"
    assert verdict.buckets == ()


def test_a_blocked_feature_reports_its_reason():
    episodes = [_episode(i, i / 10) for i in range(40)]
    verdict = analyse_feature(episodes, "F5")
    assert verdict.verdict == "UNAVAILABLE"
    assert verdict.unavailable_reason and "open-interest" in verdict.unavailable_reason


def test_a_clean_monotone_relationship_is_a_candidate():
    episodes = [_episode(i, i / 100) for i in range(40)]
    verdict = analyse_feature(episodes, "F1")
    assert verdict.verdict == "CANDIDATE"
    assert verdict.rho_mfe > 0.9


def test_open_episodes_are_excluded_from_the_outcome_tables():
    from backtest_framework.research.trade_diagnostics import TradeEpisode

    closed = [_episode(i, i / 100) for i in range(40)]
    still_open = TradeEpisode(
        entry_timestamp=EPOCH,
        exit_timestamp=None,
        entry_index=1,
        exit_index=None,
        bars_held=5,
        entry_price=100.0,
        exit_price=None,
        gross_pnl=999.0,
        costs=0.0,
        rebalance_costs=0.0,
        traded_notional=100.0,
        n_fills=1,
        mfe=99.0,
        mae=0.0,
        features={"F1": 0.0},
    )
    assert analyse_feature(closed + [still_open], "F1").n_total == len(closed)
