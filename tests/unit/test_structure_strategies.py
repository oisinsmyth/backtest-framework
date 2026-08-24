"""Unit gates for the frozen wrapper (D204, WP4/WP5; amended by D207).

The wrapper is shared by every ablation arm, so a defect here does not bias one arm — it
biases all of them in the same direction and the ablation still looks internally
consistent. That is the worst kind of defect this study could have, and it is why the
pessimistic conventions get their own tests rather than being trusted to the code they
were copied from.

Three things carry real risk:

- **intra-bar ordering.** A bar covering both stop and target must resolve as a STOP. A
  bar's OHLC does not say which came first and resolving it favourably is how a backtest
  manufactures an edge (D42);
- **gap-through fills**, which must land at the bar's open and not the stop price (D10);
- **direction-signed excursions.** `feature_analysis.analyse_feature` ranks on MFE and was
  written for a long-flat book. Feeding it unsigned excursions from a two-sided book would
  rank every short by how far price rose against it — a silent, plausible wrong answer.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import Leg
from backtest_framework.research.structure_setups import Setup
from backtest_framework.research.structure_strategies import (
    COURSE_TARGET_R,
    ArmTrade,
    Wrapper,
    _excursions,
    expectancy,
    r_multiples,
    run_arm,
    to_episodes,
    trigger_features,
)
from backtest_framework.research.terrain_strategies import (
    MAX_HOLD,
    TRAIL_AFTER_R,
    TRAIL_LOOKBACK,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def ohlc(rows):
    return [
        TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c))
        for i, (o, h, lo, c) in enumerate(rows)
    ]


def flat(closes):
    return ohlc([(c, c, c, c) for c in closes])


def setup_at(ready, direction, leg, window_len=10, holds=None):
    window = tuple(range(ready, ready + window_len))
    return Setup(
        choch_index=ready - 1,
        direction=direction,
        leg=leg,
        ready_index=ready,
        window=window,
        holds=tuple(holds or (frozenset() for _ in window)),
        closed_by="max_hold",
    )


# ------------------------------------------------------------- the wrapper is a constant

def test_the_wrapper_defaults_are_the_pre_registered_values():
    """The wrapper is frozen across arms — D203's finding is that a wrapper is where a
    study goes to fool itself. These values are pinned so an arm cannot quietly hold
    different ones."""
    w = Wrapper()
    assert w.target_r == COURSE_TARGET_R == 5.0
    assert (w.trail_after_r, w.trail_lookback, w.max_hold) == (
        TRAIL_AFTER_R,
        TRAIL_LOOKBACK,
        MAX_HOLD,
    )


# ---------------------------------------------------------------- pessimistic conventions

def test_a_bar_covering_both_stop_and_target_resolves_as_a_stop():
    """D42. A bar's OHLC does not say which came first, and resolving the ambiguity in the
    strategy's favour is how a backtest manufactures an edge it will not have."""
    # Long from 100, stop at 98 (risk 2), target at 110. Bar 2 covers 97 and 111.
    bars = ohlc([
        (100, 100, 100, 100),
        (100, 100, 100, 100),
        (100, 111, 97, 105),
    ] + [(105, 105, 105, 105)] * 5)
    setup = setup_at(0, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=3)
    trades = run_arm(bars, [setup])
    assert len(trades) == 1
    assert trades[0].reason == "stop"


def test_a_gap_through_the_stop_fills_at_the_open_not_the_stop_price():
    """D10. Filling at the stop price when the bar gapped through it is free money and
    fantasy risk numbers — a bug fix, never a configurable option."""
    bars = ohlc([
        (100, 100, 100, 100),
        (100, 100, 100, 100),
        (90, 91, 89, 90),  # opens well below the 98 stop
    ] + [(90, 90, 90, 90)] * 5)
    setup = setup_at(0, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=3)
    trades = run_arm(bars, [setup])
    assert trades[0].reason == "stop"
    assert trades[0].exit_price == 90.0, "filled at the open, not at 98"


def test_a_clean_run_to_target_exits_at_the_target():
    bars = ohlc([
        (100, 100, 100, 100),
        (100, 100, 100, 100),
        (100, 104, 100, 103),
        (103, 111, 103, 110),
    ] + [(110, 110, 110, 110)] * 5)
    setup = setup_at(0, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=3)
    trades = run_arm(bars, [setup])
    assert trades[0].reason == "target"
    assert trades[0].exit_price == pytest.approx(110.0)
    assert trades[0].r_multiple == pytest.approx(COURSE_TARGET_R)


def test_a_trade_that_resolves_neither_way_exits_on_the_hold_cap():
    bars = flat([100.0] * (MAX_HOLD + 8))
    setup = setup_at(0, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=3)
    trades = run_arm(bars, [setup])
    assert trades[0].reason == "max_hold"
    assert trades[0].exit_index - trades[0].entry_index == MAX_HOLD


# ------------------------------------------------------------------ entry and sequencing

def test_the_signal_bar_never_also_pays():
    """The signal is read on bar t's close and the position fills at bar t+1's close —
    D197-D201's convention, kept identical so the numbers stay comparable."""
    bars = ohlc([(100 + i, 100 + i, 100 + i, 100 + i) for i in range(20)])
    setup = setup_at(3, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=5)
    trades = run_arm(bars, [setup])
    assert trades[0].entry_index == 4
    assert trades[0].entry_price == bars[4].bar.close


def test_only_one_position_is_held_at_a_time():
    """Overlapping positions would make the equity path depend on a sizing policy this
    study never states. A strict gap is required rather than hoped for — the shape of
    `StrategyResult.equity_curve`'s known blind spot, avoided by construction."""
    bars = flat([100.0] * 400)
    setups = [
        setup_at(ready, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=5)
        for ready in (10, 12, 14, 200)
    ]
    trades = run_arm(bars, setups)
    for a, b in zip(trades, trades[1:]):
        assert b.entry_index > a.exit_index


def test_a_stop_on_the_wrong_side_of_the_entry_is_refused():
    """An unguarded division here produces an infinite R multiple rather than an error.

    This guard is also what exposed D209's defect: with the stop read off the wrong end of
    the leg it silently rejected 93% of setups, and the surviving 7% were the ones that had
    barely pulled back."""
    bars = flat([100.0] * 50)
    # Long setup whose leg ORIGIN sits above the entry price — not a stop.
    setup = setup_at(0, direction=1, leg=Leg(0, 110.0, 0, 130.0), window_len=3)
    assert run_arm(bars, [setup]) == []


# ------------------------------------------------------------------------- excursions

def test_excursions_are_signed_by_direction_and_measured_in_r():
    """For a short, favourable is the LOW. Unsigned excursions would rank every short by
    how far price rose against it, which is exactly the kind of plausible wrong answer
    `feature_analysis` would report without complaint.

    And the unit is R, not price fraction — risk is 10 here, so a 10-point move is 1.0."""
    bars = ohlc([
        (100, 100, 100, 100),
        (100, 102, 90, 95),
        (95, 96, 94, 95),
    ])
    short = ArmTrade(0, 0, 2, -1, 100.0, 95.0, 110.0, 10.0, "target")
    mfe, mae = _excursions(bars, short)
    assert mfe == pytest.approx(1.0), "price fell 10 against a risk of 10 — 1R favourable"
    assert mae == pytest.approx(-0.2), "price rose 2 against a risk of 10"

    long = ArmTrade(0, 0, 2, 1, 100.0, 95.0, 90.0, 10.0, "stop")
    mfe, mae = _excursions(bars, long)
    assert mfe == pytest.approx(0.2)
    assert mae == pytest.approx(-1.0)


def test_excursions_are_scale_invariant():
    """The reason the unit changed, asserted directly.

    The same geometry at $100 and at $90,000 must produce the same excursion. In the
    price-fraction form it does not, which is why `stop_atr` came back a CANDIDATE at
    rho +0.56 in the first WP4 run — an artifact of a scale-dependent quantity ranked
    across eras that do not share the scale (D187's lesson)."""
    small = ohlc([(100, 100, 100, 100), (100, 102, 90, 95), (95, 96, 94, 95)])
    scale = 900.0
    large = ohlc([
        tuple(v * scale for v in row)
        for row in [(100, 100, 100, 100), (100, 102, 90, 95), (95, 96, 94, 95)]
    ])
    a = _excursions(small, ArmTrade(0, 0, 2, -1, 100.0, 95.0, 110.0, 10.0, "target"))
    b = _excursions(
        large,
        ArmTrade(0, 0, 2, -1, 100.0 * scale, 95.0 * scale, 110.0 * scale, 10.0 * scale, "target"),
    )
    assert a == pytest.approx(b)


def test_mfe_is_never_negative_and_mae_never_positive():
    """The entry bar is inside the excursion window, and its high and low bracket its own
    close, so both are bounded by construction. Asserted because a windowing off-by-one
    would break it silently."""
    bars = ohlc([(100 + i, 102 + i, 98 + i, 100 + i) for i in range(30)])
    for direction in (1, -1):
        trade = ArmTrade(0, 5, 20, direction, bars[5].bar.close, bars[20].bar.close,
                         0.0, 5.0, "max_hold")
        mfe, mae = _excursions(bars, trade)
        assert mfe >= 0.0
        assert mae <= 0.0


# ----------------------------------------------------------------- R multiples and costs

def test_the_cost_charged_in_r_matches_the_census_arithmetic():
    """WP2's friction figure and WP5's book have to be the same statement, not two numbers
    that happen to point the same way."""
    trade = ArmTrade(0, 0, 1, 1, 100.0, 100.0, 98.0, 2.0, "max_hold")
    net = r_multiples([trade], cost_bps=40.0)[0]
    expected_friction = (40.0 / 10_000.0) * (100.0 + 100.0) / 2.0
    assert net == pytest.approx(0.0 - expected_friction)


def test_zero_cost_leaves_the_raw_r_multiple():
    trade = ArmTrade(0, 0, 1, 1, 100.0, 110.0, 98.0, 2.0, "target")
    assert r_multiples([trade], cost_bps=0.0)[0] == pytest.approx(5.0)


def test_expectancy_reports_hit_rate_and_mean_r_together():
    """Either alone is misleading: 60% at 0.2R and 20% at 5R are different businesses, and
    the course's entire pitch is the second one."""
    trades = [
        ArmTrade(0, 0, 1, 1, 100.0, 110.0, 98.0, 2.0, "target"),
        ArmTrade(1, 2, 3, 1, 100.0, 98.0, 98.0, 2.0, "stop"),
        ArmTrade(2, 4, 5, 1, 100.0, 98.0, 98.0, 2.0, "stop"),
        ArmTrade(3, 6, 7, 1, 100.0, 98.0, 98.0, 2.0, "stop"),
    ]
    out = expectancy(trades, cost_bps=0.0)
    assert out["n"] == 4
    assert out["hit_rate"] == pytest.approx(0.25)
    assert out["mean_r"] == pytest.approx((5.0 - 1.0 - 1.0 - 1.0) / 4)


def test_an_empty_arm_reports_zeros_rather_than_dividing_by_nothing():
    assert expectancy([], cost_bps=40.0)["n"] == 0


# -------------------------------------------------------------------------- features

def test_features_are_continuous_and_unavailable_is_none():
    """Continuous, never boolean: WP4a's power comes from ranking on a gradient, and a
    boolean has one split where a continuous feature has four quintile boundaries.
    `None` means unavailable and is never imputed."""
    bars = ohlc([(100 + i, 101 + i, 99 + i, 100 + i) for i in range(60)])
    atr = [2.0] * len(bars)
    strength = [55.0] * len(bars)
    setup = setup_at(10, direction=-1, leg=Leg(2, 120.0, 8, 100.0), window_len=5)
    trade = ArmTrade(0, 11, 20, -1, bars[11].bar.close, bars[20].bar.close, 120.0, 5.0, "stop")

    features = trigger_features(bars, setup, trade, atr, strength, gaps=[])
    assert features["gap_distance_atr"] is None, "no gap in the leg — unavailable, not zero"
    assert isinstance(features["fib_depth"], float)
    assert features["rsi"] == 55.0
    assert features["direction"] == -1.0


def test_episodes_carry_their_features_into_the_analysis_objects():
    """`TradeEpisode` is reused rather than replaced because it carries the promotion
    criteria with it — `analyse_feature`'s three gates are thresholds this project already
    committed to, and restating them would be re-choosing them."""
    bars = ohlc([(100 + i, 101 + i, 99 + i, 100 + i) for i in range(60)])
    setup = setup_at(10, direction=1, leg=Leg(2, 90.0, 8, 120.0), window_len=5)
    trades = run_arm(bars, [setup])
    episodes = to_episodes(bars, [setup], trades, cost_bps=40.0,
                           atr=[2.0] * len(bars), strength=[55.0] * len(bars), gaps=[])
    assert len(episodes) == len(trades)
    for episode in episodes:
        assert not episode.is_open
        assert "fib_depth" in episode.features
        assert episode.costs > 0.0
        assert math.isfinite(episode.mfe) and math.isfinite(episode.mae)


# ------------------------------------------------- untradeable trades, and the overlap flag

def test_a_trade_whose_cost_exceeds_its_risk_is_counted_as_untradeable():
    """The first WP4 run reported mean R of -104. Not a bug: a stop a few basis points from
    the entry really does make a 40 bps round trip cost 10R. What it describes is a position
    size nobody can take, so the share is reported rather than left inside a mean."""
    tight = ArmTrade(0, 0, 1, 1, 100.0, 100.0, 99.99, 0.01, "max_hold")
    wide = ArmTrade(1, 2, 3, 1, 100.0, 100.0, 90.0, 10.0, "max_hold")
    other = ArmTrade(2, 4, 5, 1, 100.0, 100.0, 92.0, 8.0, "max_hold")
    out = expectancy([tight, wide, other], cost_bps=40.0)
    assert out["share_untradeable"] == pytest.approx(1 / 3)
    assert out["mean_r"] < -10.0, "the one tight stop dominates the mean"
    assert out["mean_r_tradeable"] > -1.0, "and does not dominate the takeable subset"
    assert out["median_r"] > -1.0, "nor the median"
    assert out["median_r"] > out["mean_r"]


def test_overlap_is_off_for_a_book_and_on_for_annotation():
    """WP4's feature analysis needs one outcome per setup; the one-at-a-time rule threw away
    most of them. An overlapping population is for annotation and has no equity curve."""
    bars = flat([100.0] * 400)
    setups = [
        setup_at(ready, direction=1, leg=Leg(0, 98.0, 0, 120.0), window_len=5)
        for ready in (10, 12, 14, 16)
    ]
    book = run_arm(bars, setups)
    annotated = run_arm(bars, setups, allow_overlap=True)
    assert len(book) == 1, "every later setup falls inside the first trade"
    assert len(annotated) == len(setups)
    for a, b in zip(annotated, annotated[1:]):
        assert b.entry_index > a.entry_index
