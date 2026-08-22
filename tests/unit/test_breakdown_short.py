"""Unit gates for the breakdown short book (D169).

The load-bearing test here is the first one. A short's loss has no ceiling, so the
per-trade stop and the position cap are the difference between a study and a fantasy —
the brief calls them non-optional and says no configuration may disable them. That is
enforced at construction, and this file is what stops a later refactor from quietly
turning the enforcement into a default.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    AtrStop,
    BreakoutStrategy,
    ChandelierStop,
    ChannelStopExit,
    Direction,
    TrailingChannelStop,
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


def test_every_short_config_the_study_builds_carries_a_stop():
    """The tail-discipline requirement is "a stop", not "the entry-channel stop" — D171
    added three more families and the sweep uses them. What must hold for every config
    the study builds is that SOME rule places a stop, which is exactly what
    `BreakoutStrategy.__post_init__` enforces."""
    for variant in ds.short_variants():
        rebuilt = build_breakout_strategy(variant.fixed_config, "s", "X")
        assert any(hasattr(r, "stop_level") for r in rebuilt.exit_rules), variant.name
        assert rebuilt.direction is Direction.SHORT
        assert rebuilt.weight_source.cap <= 1.0


def test_the_sweep_covers_every_declared_stop_family():
    """A family listed in STOP_FAMILIES but never turned into a variant would be a silent
    hole in the sweep — the table would look complete and quietly omit a row."""
    names = {v.name for v in ds.short_variants()}
    for label, _rules in ds.STOP_FAMILIES:
        expected = ds.SHORT_BASELINE if label == "entry_channel" else f"stop_{label}"
        assert expected in names, label


# ------------------------------------------------------------------- the exit rules


def test_channel_stop_provides_the_level_and_does_not_itself_exit():
    """Since D170 the rule PLACES the stop and the engine enforces it intrabar. The
    rule's own `exits()` is deliberately False — the close-based backstop lives once on
    the strategy, against the ratcheted level, rather than duplicated into every rule."""
    rule = ChannelStopExit()
    position = OpenPosition(PositionState.SHORT, entry_index=2, entry_reference=100.0,
                            stop_level=110.0)
    view = _View(bars_from([100, 100, 100, 100, 105, 115]), 5)
    assert rule.exits(view, position) is False
    assert rule.stop_level(view, position) == 110.0


def test_the_strategy_backstops_a_breached_stop_on_a_close():
    """The engine fires on a TOUCH; this fires on a CLOSE beyond the level, and exists
    for callers that drive generate_targets() without the engine."""
    strategy = BreakoutStrategy(
        "s", "X", n_entry=3, n_exit=3, direction=Direction.SHORT,
        weight_source=FixedWeight(1.0), exit_rules=(ChannelStopExit(),),
    )
    strategy._state = PositionState.SHORT
    strategy._entry_index = 0
    strategy._entry_reference = 100.0
    strategy._held_weight = 1.0
    strategy._stop_level = 110.0
    view = _View(bars_from([100, 100, 100, 115]), 3)
    assert strategy._stop_breached(view, 3) is True
    assert strategy._stop_breached(_View(bars_from([100, 100, 100, 108]), 3), 3) is False


def test_trailing_channel_stop_is_the_n_bar_extreme_against_the_trade():
    """The user-facing shape: 'lowest low of N days' for a long, highest high for a
    short."""
    bars = bars_from([100, 101, 102, 103, 104, 105])
    view = _View(bars, 5)
    short_pos = OpenPosition(PositionState.SHORT, 0, 100.0, 0.0)
    long_pos = OpenPosition(PositionState.LONG, 0, 100.0, 0.0)
    rule = TrailingChannelStop(n_bars=3)
    assert rule.stop_level(view, short_pos) == max(b.bar.high for b in bars[2:5])
    assert rule.stop_level(view, long_pos) == min(b.bar.low for b in bars[2:5])


def test_a_trailing_stop_ratchets_and_never_loosens():
    """A level allowed to retreat is not a stop: it would let a loss grow after having
    promised not to. Rising prices must not widen a short's stop."""
    strategy = BreakoutStrategy(
        "s", "X", n_entry=3, n_exit=3, direction=Direction.SHORT,
        weight_source=FixedWeight(1.0), exit_rules=(TrailingChannelStop(n_bars=2),),
    )
    strategy._state = PositionState.SHORT
    strategy._entry_index = 0
    strategy._entry_reference = 100.0
    strategy._stop_level = 0.0

    falling = bars_from([100, 99, 98, 97, 96])
    for i in (2, 3, 4):
        strategy._ratchet_stop(
            _View(falling, i),
            OpenPosition(PositionState.SHORT, 0, 100.0, strategy._stop_level),
        )
    tight = strategy._stop_level
    assert tight > 0

    # Now prices rise again; the raw 2-bar high would move UP, the stop must not.
    rising = bars_from([100, 99, 98, 130, 140])
    strategy._ratchet_stop(
        _View(rising, 4),
        OpenPosition(PositionState.SHORT, 0, 100.0, strategy._stop_level),
    )
    assert strategy._stop_level == tight, "a short's stop widened on a rally"


def test_atr_and_chandelier_place_their_stops_against_the_trade():
    bars = bars_from([100] * 40)
    view = _View(bars, 30)
    short_pos = OpenPosition(PositionState.SHORT, 25, 100.0, 0.0)
    for rule in (AtrStop(multiple=2.0, window=20), ChandelierStop(multiple=3.0, window=20)):
        level = rule.stop_level(view, short_pos)
        assert level is not None and level > 100.0, f"{rule.name} placed a short's stop below entry"

    long_pos = OpenPosition(PositionState.LONG, 25, 100.0, 0.0)
    for rule in (AtrStop(multiple=2.0, window=20), ChandelierStop(multiple=3.0, window=20)):
        level = rule.stop_level(view, long_pos)
        assert level is not None and level < 100.0, f"{rule.name} placed a long's stop above entry"


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
    so dropping the flat bars would measure the wrong thing entirely.

    `min_bars=2` keeps the fixture readable; the property under test is about which
    bars enter the correlation, not about how the weights are set."""
    long_r = [0.01, 0.01, 0.0, 0.0, 0.01, 0.01]
    short_r = [0.0, 0.0, 0.01, 0.01, 0.0, 0.0]
    out = ds.combine_books(
        long_r, short_r, rf_annual=0.0, periods_per_year=365.0, min_bars=2
    )
    assert out.n_bars == 4  # 6 returns less the 2-bar warm-up
    assert out.n_warmup_bars == 2
    assert out.correlation == pytest.approx(-1.0, abs=0.01)


def test_combining_uses_equal_vol_not_equal_capital():
    """A quiet book and a wild one at equal CAPITAL is just the wild one with noise."""
    calm = [0.001, -0.001] * 200
    wild = [0.05, -0.05] * 200
    out = ds.combine_books(calm, wild, rf_annual=0.0, periods_per_year=365.0)
    assert -1.0 <= out.correlation <= 1.0
    assert out.n_bars == 400 - ds.ENSEMBLE_MIN_BARS


# ------------------------------------------------- the ensemble weights are causal (D181)


def _noise(n: int, sd: float, seed: int) -> list[float]:
    rng = random.Random(seed)
    return [rng.gauss(0.0, sd) for _ in range(n)]


def test_ensemble_weight_at_a_bar_ignores_that_bar_and_every_later_one():
    """THE test whose absence let the look-ahead through (D181).

    The weights used to come from whole-sample volatility, so a spike in the last year
    changed the weight applied in the first. Mutating the tail must leave every earlier
    bar of the combined series untouched."""
    n, cut = 1200, 800
    calm, wild = _noise(n, 0.005, 1), _noise(n, 0.02, 2)
    mutated = wild[:cut] + [x * 25 for x in wild[cut:]]

    before = ds.combined_series(calm, wild)
    after = ds.combined_series(calm, mutated)

    shared = cut - ds.ENSEMBLE_MIN_BARS
    assert before[:shared] == after[:shared]
    assert before[shared:] != after[shared:]  # the mutation must actually reach the series


def test_a_leg_that_turns_wild_is_down_weighted_only_afterwards():
    """The weight must respond to volatility that has already happened, and not before.

    The switch is placed well past the warm-up so there are weighted bars on both sides of
    it — with an expanding window the first weight does not exist until bar
    `ENSEMBLE_MIN_BARS`, so a switch inside the warm-up would test nothing."""
    n, switch, calm_sd, wild_sd = 1200, 600, 0.005, 0.05
    long_r = _noise(n, calm_sd, 3)
    short_r = _noise(switch, calm_sd, 4) + _noise(n - switch, wild_sd, 5)

    weights, _ = ds._inverse_vol_weights(long_r, short_r, ds.ENSEMBLE_MIN_BARS)
    # index i of `weights` is bar i + ENSEMBLE_MIN_BARS; [1] is the SHORT leg's share
    at = lambda bar: weights[bar - ds.ENSEMBLE_MIN_BARS][1]

    # Both legs still calm on the last pre-switch bar, so the split is near even.
    assert 0.4 < at(switch - 1) < 0.6
    # By the end the short leg's history is half wild, and it is cut down hard.
    assert at(n - 1) < 0.2


def test_unequal_length_books_raise_rather_than_being_truncated():
    """The old code took min(len(a), len(b)) and sliced from the end, which would have
    silently shifted the pair out of alignment."""
    with pytest.raises(ValueError, match="different spans"):
        ds.combined_series(_noise(300, 0.01, 6), _noise(299, 0.01, 7))


def test_a_series_shorter_than_the_window_raises_instead_of_falling_back():
    """Falling back to whole-sample vol here is exactly the bug — quietly, on short
    inputs, in a function whose contract says the weights are trailing."""
    with pytest.raises(ValueError, match="not enough to weight"):
        ds.combined_series(_noise(20, 0.01, 8), _noise(20, 0.01, 9))


def test_a_flat_leg_falls_back_to_equal_weight_and_is_counted():
    """A book flat for its whole window has no volatility to invert. Equal weight is the
    only non-dividing-by-zero choice, and it is counted so the report can say so."""
    n = 400
    flat = [0.0] * n
    out = ds.combine_books(flat, _noise(n, 0.02, 10), rf_annual=0.0, periods_per_year=365.0)
    assert out.n_fallback_bars == out.n_bars
    assert out.n_bars == n - ds.ENSEMBLE_MIN_BARS


def test_point_estimate_and_bootstrap_series_are_the_same_book():
    """D172 split these two apart precisely so they could not diverge; D181 rewired both
    onto one helper. If they ever disagree, every published interval is on a different
    book than its point estimate."""
    calm, wild = _noise(400, 0.006, 11), _noise(400, 0.03, 12)
    out = ds.combine_books(calm, wild, rf_annual=0.0, periods_per_year=365.0)
    series = ds.combined_series(calm, wild)
    assert len(series) == out.n_bars
    assert ds.sharpe(series, 0.0, 365.0) == pytest.approx(out.combined_sharpe)


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


# ------------------------------------------------- square-root market impact (D186)


def test_every_shipped_tier_omits_the_impact_brick_entirely():
    """Impact is off by default, and "off" must mean ABSENT rather than zero-valued.

    A `sqrt_impact` entry with coefficient 0.0 would cost nothing and still change every
    config hash in both studies, orphaning every registered trial (D166's rule, fifth
    application)."""
    for tier in bs.DEFAULT_TIERS + bs.SHORT_TIERS:
        bricks = tier.cost_stack_config()["trade_bricks"]
        assert bricks == [{"type": "percent_spread", "bps": tier.fee_bps}], tier.name


def test_impact_brick_appears_only_when_switched_on():
    tier = bs.CostTier("taker_40bp", 40.0, "taker", impact_coefficient=1.0)
    bricks = tier.cost_stack_config()["trade_bricks"]
    assert bricks[0] == {"type": "percent_spread", "bps": 40.0}
    assert bricks[1] == {
        "type": "sqrt_impact",
        "coefficient": 1.0,
        "calibration": "full_sample",
    }


def test_building_an_impact_tier_without_data_raises():
    """A silently zero-cost impact brick is worse than no impact brick at all."""
    tier = bs.CostTier("taker_40bp", 40.0, "taker", impact_coefficient=1.0)
    with pytest.raises(ValueError, match="no StackDataContext"):
        tier.build()


def test_impact_cost_grows_with_size_and_grows_SUB_linearly():
    """The whole content of D66: doubling the order multiplies the cost FRACTION by
    sqrt(2), so total impact dollars scale as Q^1.5 rather than Q.

    A model that charged a flat fraction would be a spread, and capacity would be
    scale-free — which is exactly the assumption this work exists to remove."""
    from backtest_framework.costs.equity_bricks import ImpactParams, SqrtImpact

    brick = SqrtImpact(
        params_by_symbol={"X": ImpactParams(sigma_daily=0.05, adv_shares=1_000_000.0)},
        coefficient=1.0,
    )
    fracs = [
        brick.coefficient
        * brick.params_by_symbol["X"].sigma_daily
        * math.sqrt(q / brick.params_by_symbol["X"].adv_shares)
        for q in (10_000.0, 20_000.0, 40_000.0)
    ]
    assert fracs[0] < fracs[1] < fracs[2]
    assert fracs[1] / fracs[0] == pytest.approx(math.sqrt(2.0))
    assert fracs[2] / fracs[1] == pytest.approx(math.sqrt(2.0))


def test_a_symbol_with_no_volume_cannot_be_calibrated():
    """D48's rule, on the crypto path: a missing ADV is a loud error, never a default."""
    from backtest_framework.costs.calibration import calibrate_impact_params

    bars = bars_from([100.0, 101.0, 99.0, 102.0])
    with pytest.raises(ValueError, match="no volume series"):
        calibrate_impact_params({"X": bars}, {})
    with pytest.raises(ValueError, match="non-positive mean volume"):
        calibrate_impact_params({"X": bars}, {"X": [0.0, 0.0, 0.0, 0.0]})


# ------------------------------------------------------ D176: the two closed gaps


def _episode(entry_index, mfe, mae, net=1.0, exit_ts=None, bars_held=5):
    from backtest_framework.research.trade_diagnostics import TradeEpisode

    return TradeEpisode(
        entry_timestamp=EPOCH + timedelta(days=entry_index),
        exit_timestamp=exit_ts if exit_ts is not None else EPOCH + timedelta(days=entry_index + bars_held),
        entry_index=entry_index,
        exit_index=entry_index + bars_held,
        bars_held=bars_held,
        entry_price=100.0,
        exit_price=100.0,
        gross_pnl=net,
        costs=0.0,
        rebalance_costs=0.0,
        traded_notional=100.0,
        n_fills=2,
        mfe=mfe,
        mae=mae,
    )


def test_a_short_squeeze_is_measured_on_MFE_not_MAE():
    """The bug this closes. Excursions are measured in PRICE terms (D112), so a short is
    hurt when price RISES — which the diagnostics call MFE. Reading MAE instead would
    report profitable moves as squeezes, and the first cut of this function did."""
    bars = bars_from([100.0] * 60)
    # Price ran 30% UP against the short (adverse) and 2% down (favourable).
    squeezed = _episode(entry_index=40, mfe=0.30, mae=-0.02)
    report = ds.squeeze_events([squeezed], bars, direction=-1)
    assert report.n_squeezes == 1, "a 30% rise against a short is a squeeze"

    # Mirror: for a LONG the same episode is a big favourable move, not a squeeze.
    assert ds.squeeze_events([squeezed], bars, direction=+1).n_squeezes == 0


def test_a_favourable_short_move_is_never_counted_as_a_squeeze():
    bars = bars_from([100.0] * 60)
    winner = _episode(entry_index=40, mfe=0.01, mae=-0.40)  # price collapsed: short wins
    assert ds.squeeze_events([winner], bars, direction=-1).n_squeezes == 0


def test_open_episodes_are_excluded_from_the_squeeze_count():
    from backtest_framework.research.trade_diagnostics import TradeEpisode

    bars = bars_from([100.0] * 60)
    still_open = TradeEpisode(
        entry_timestamp=EPOCH, exit_timestamp=None, entry_index=40, exit_index=None,
        bars_held=5, entry_price=100.0, exit_price=None, gross_pnl=0.0, costs=0.0,
        rebalance_costs=0.0, traded_notional=100.0, n_fills=1, mfe=0.90, mae=0.0,
    )
    assert ds.squeeze_events([still_open], bars, direction=-1).n_trades == 0


def test_per_window_correlation_reports_unmeasurable_rather_than_zero():
    """A window the short book sat out has no correlation. Returning 0.0 there would
    report 'uncorrelated' for a window in which one book did not exist."""
    long_r = [0.01, -0.01, 0.02, -0.02, 0.01, -0.01]
    flat_short = [0.0] * 6
    rows = ds.correlation_by_window(long_r, flat_short, [(0, 3), (3, 6)])
    assert all(r["correlation"] is None for r in rows)
    assert all(r["short_active"] is False for r in rows)


def test_per_window_correlation_recovers_a_known_sign():
    long_r = [0.01, -0.01, 0.02, -0.02, 0.03, -0.03]
    mirrored = [-x for x in long_r]
    rows = ds.correlation_by_window(long_r, mirrored, [(0, 6)])
    assert rows[0]["correlation"] == pytest.approx(-1.0, abs=1e-9)


def test_per_window_correlation_can_disagree_with_the_full_sample():
    """The reason the brief asks for it: opposite-signed windows can average to zero."""
    long_r = [0.01, 0.02, 0.03, 0.01, 0.02, 0.03]
    short_r = [0.01, 0.02, 0.03, -0.01, -0.02, -0.03]
    rows = ds.correlation_by_window(long_r, short_r, [(0, 3), (3, 6)])
    signs = {r["correlation"] > 0 for r in rows if r["correlation"] is not None}
    assert signs == {True, False}, "expected one positive and one negative window"
