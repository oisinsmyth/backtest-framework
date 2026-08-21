"""Unit gates for the long-flat breakout strategy (D109).

Covers the three things that decide whether any downstream number means anything:
the extremum windows exclude the current bar, the hysteresis band cannot chatter,
and every filter/sizing brick is separable and toggleable rather than welded into
the entry logic.
"""

from __future__ import annotations

import math

import pytest

from backtest_framework.config.errors import ConfigError
from backtest_framework.engine.dataview import DataView, build_data_view
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    ConsecutiveCloseFilter,
    FixedWeight,
    InverseVolatilityWeight,
    TrendGateFilter,
    VolatilityContractionFilter,
    build_breakout_strategy,
    build_entry_filter,
    build_weight_source,
)

TOLERANCE = 1e-9


def flat_bars(closes, spread=0.5):
    return [Bar(open=c, high=c + spread, low=c - spread, close=c) for c in closes]


def weights(strategy: BreakoutStrategy, bars) -> list[float]:
    out = []
    for i in range(len(bars)):
        targets = strategy.generate_targets({strategy.instrument_id: build_data_view(bars, i)})
        assert len(targets) == 1  # long-flat, single instrument: exactly one target
        out.append(targets[0].weight)
    return out


# ------------------------------------------------------- extremum windows / no self-trigger


def test_entry_level_excludes_the_current_bar():
    bars = flat_bars([10, 11, 12, 13, 14])
    s = BreakoutStrategy("s", "X", n_entry=4, n_exit=2)
    view = build_data_view(bars, 4)
    # highs of bars 0..3 are 10.5, 11.5, 12.5, 13.5 — bar 4's own 14.5 is NOT in there.
    assert s.entry_level(view, 4) == pytest.approx(13.5)


def test_exit_level_excludes_the_current_bar():
    bars = flat_bars([10, 9, 8, 7, 6])
    s = BreakoutStrategy("s", "X", n_entry=4, n_exit=2)
    view = build_data_view(bars, 4)
    # lows of bars 2..3 are 7.5, 6.5; bar 4's own 5.5 is excluded.
    assert s.exit_level(view, 4) == pytest.approx(6.5)


def test_a_bar_cannot_trigger_on_its_own_high():
    """A single enormous bar whose high dwarfs everything before it must not enter on
    itself — the entry compares its CLOSE to the prior bars' highs."""
    bars = flat_bars([10, 10, 10, 10]) + [Bar(open=10, high=1000.0, low=9.0, close=10.4)]
    s = BreakoutStrategy("s", "X", n_entry=4, n_exit=2)
    assert weights(s, bars)[-1] == 0.0  # close 10.4 < prior highs' max 10.5


def test_entry_and_exit_are_mutually_exclusive_on_every_bar():
    """The structural reason the strategy cannot chatter: with n_exit <= n_entry the
    exit window nests inside the entry window, so max(high) over the entry window is
    at least min(low) over the exit window and no close can be strictly outside
    both."""
    import random

    rng = random.Random(20260818)
    closes = [100.0]
    for _ in range(400):
        closes.append(max(closes[-1] * (1 + rng.uniform(-0.2, 0.2)), 1.0))
    bars = [
        Bar(open=c, high=c * (1 + abs(rng.gauss(0, 0.02))), low=c * (1 - abs(rng.gauss(0, 0.02))), close=c)
        for c in closes
    ]
    for n_entry, n_exit in ((20, 5), (30, 10), (40, 10), (55, 20), (20, 20)):
        s = BreakoutStrategy("s", "X", n_entry=n_entry, n_exit=n_exit)
        for i in range(n_entry, len(bars)):
            view = build_data_view(bars, i)
            assert not (s.entry_condition(view, i) and s.exit_condition(view, i))


def test_n_exit_above_n_entry_is_refused():
    with pytest.raises(ValueError, match="hysteresis band"):
        BreakoutStrategy("s", "X", n_entry=10, n_exit=20)


# ------------------------------------------------------------------------ hysteresis


def test_no_chatter_on_an_oscillating_series():
    """A series oscillating hard around a level crosses the entry threshold many
    times; the strategy must not flip state on it. The exit level sits an entire
    n_exit-bar low below the entry level, so an oscillation smaller than the band
    produces at most ONE entry and no exit."""
    closes = [100.0 + (2.0 if i % 2 else -2.0) for i in range(120)]
    closes[60:] = [c + 6.0 for c in closes[60:]]  # one genuine step up, then oscillate again
    bars = flat_bars(closes, spread=0.25)
    s = BreakoutStrategy("s", "X", n_entry=20, n_exit=5)

    w = weights(s, bars)
    flips = sum(1 for a, b in zip(w, w[1:]) if (a > 0) != (b > 0))
    assert flips <= 1, f"state flipped {flips} times on a bounded oscillation — that is chatter"
    # And it never round-trips within the oscillation half-period.
    assert not any(w[i] > 0 and w[i + 1] == 0 for i in range(len(w) - 1))


def test_hysteresis_holds_through_a_pullback_smaller_than_the_exit_window():
    """Entered on a breakout, a pullback that does not breach the n_exit-bar low
    must not close the position — that gap IS the hysteresis."""
    closes = [100 + i for i in range(30)] + [129, 128, 127, 128, 130]
    bars = flat_bars(closes, spread=0.5)
    s = BreakoutStrategy("s", "X", n_entry=20, n_exit=10)
    w = weights(s, bars)
    assert w[-1] > 0 and min(w[20:]) > 0


def test_exit_fires_once_the_faster_low_is_breached():
    closes = [100 + i for i in range(30)] + [120, 110, 100]
    bars = flat_bars(closes, spread=0.5)
    s = BreakoutStrategy("s", "X", n_entry=20, n_exit=5)
    w = weights(s, bars)
    assert w[-1] == 0.0 and w[29] > 0.0


def test_flat_is_the_default_state_and_shorting_never_happens():
    closes = [100 - i for i in range(60)]  # relentless downtrend
    bars = flat_bars(closes)
    s = BreakoutStrategy("s", "X", n_entry=20, n_exit=10)
    assert set(weights(s, bars)) == {0.0}


# --------------------------------------------------------------------------- filters


def test_debounce_m1_is_the_identity_filter():
    closes = [100 + math.sin(i / 3) * 5 + i * 0.4 for i in range(120)]
    bars = flat_bars(closes)
    plain = weights(BreakoutStrategy("s", "X", n_entry=20, n_exit=5), bars)
    debounced = weights(
        BreakoutStrategy("s", "X", n_entry=20, n_exit=5, filters=(ConsecutiveCloseFilter(1),)), bars
    )
    assert plain == debounced


def test_debounce_m2_requires_two_consecutive_triggering_closes():
    # Bar 20 breaks out, bar 21 falls back inside — m=2 must reject the single-close
    # trigger, while the unfiltered strategy takes it.
    closes = [100.0] * 20 + [110.0, 99.0, 99.0]
    bars = flat_bars(closes, spread=0.5)
    plain = weights(BreakoutStrategy("s", "X", n_entry=20, n_exit=5), bars)
    debounced = weights(
        BreakoutStrategy("s", "X", n_entry=20, n_exit=5, filters=(ConsecutiveCloseFilter(2),)), bars
    )
    assert plain[20] > 0.0
    assert debounced[20] == 0.0
    assert all(w == 0.0 for w in debounced)


def test_trend_gate_blocks_entries_below_the_moving_average():
    # A breakout of the 5-bar high that still sits below the 20-bar SMA.
    closes = [200.0] * 15 + [100.0] * 5 + [104.0]
    bars = flat_bars(closes, spread=0.5)
    plain = weights(BreakoutStrategy("s", "X", n_entry=5, n_exit=3), bars)
    gated = weights(
        BreakoutStrategy("s", "X", n_entry=5, n_exit=3, filters=(TrendGateFilter(sma_window=20),)), bars
    )
    assert plain[-1] > 0.0
    assert gated[-1] == 0.0


def test_volatility_contraction_admits_a_quiet_run_up_and_rejects_a_noisy_one():
    quiet = [Bar(open=100, high=100.2, low=99.8, close=100.0) for _ in range(120)]
    noisy = [Bar(open=100, high=110.0, low=90.0, close=100.0) for _ in range(120)]
    trigger = Bar(open=100, high=200.0, low=100.0, close=150.0)

    f = VolatilityContractionFilter(threshold=1.0, short_window=20, long_window=100)
    # Contracting: the last 20 bars are quiet, the 100-bar window contains noise.
    contracting = noisy[:80] + quiet[:20] + [trigger]
    expanding = quiet[:80] + noisy[:20] + [trigger]
    i = len(contracting) - 1
    assert f.accepts(build_data_view(contracting, i), lambda _j: True)
    assert not f.accepts(build_data_view(expanding, i), lambda _j: True)


def test_filters_are_a_pure_veto_on_the_raw_breakout_condition():
    """Separability, stated as the property that actually holds. A filter cannot be
    compared entry-set to entry-set against the baseline — vetoing one entry shifts
    the whole state trajectory, so the filtered strategy can legitimately enter on a
    bar where the baseline was already long. What must hold on every bar is that the
    filtered strategy never opens a position unless (a) the RAW breakout condition
    was true on that bar and (b) the filter accepted it. Anything else would mean the
    filter had reached into the entry logic instead of sitting beside it."""
    import random

    rng = random.Random(7)
    closes, p = [], 100.0
    for _ in range(500):
        p = max(p * (1 + rng.gauss(0, 0.03)), 1.0)
        closes.append(p)
    bars = flat_bars(closes, spread=0.3)

    for f in (
        ConsecutiveCloseFilter(2),
        VolatilityContractionFilter(threshold=0.8),
        VolatilityContractionFilter(threshold=1.0),
        TrendGateFilter(sma_window=200),
    ):
        s = BreakoutStrategy("s", "X", n_entry=20, n_exit=10, filters=(f,))
        w = weights(s, bars)
        entries = [i for i in range(1, len(w)) if w[i] > 0 and w[i - 1] == 0]
        assert entries, f"{f.name} admitted nothing at all — the test would be vacuous"
        for i in entries:
            view = build_data_view(bars, i)
            assert s.entry_condition(view, i), f"{f.name} entered without a raw breakout at bar {i}"
            assert f.accepts(view, lambda j: s.entry_condition(view, j)), (
                f"{f.name} entered on a bar it does not accept"
            )
        # A filter is never consulted on exits: it can keep you out, never trap you in.
        exits = [i for i in range(1, len(w)) if w[i] == 0 and w[i - 1] > 0]
        for i in exits:
            assert s.exit_condition(build_data_view(bars, i), i)


def test_duplicate_filters_are_refused():
    with pytest.raises(ValueError, match="duplicate filter names"):
        BreakoutStrategy("s", "X", filters=(TrendGateFilter(), TrendGateFilter(50)))


# --------------------------------------------------------------------------- sizing


def test_inverse_vol_weight_is_target_over_realized_vol():
    # A series whose last 20 log returns are all exactly +1% has zero dispersion, so
    # use an alternating pattern with a known stdev instead.
    closes = [100.0]
    for i in range(40):
        closes.append(closes[-1] * (1.01 if i % 2 == 0 else 1 / 1.01))
    bars = flat_bars(closes)
    ws = InverseVolatilityWeight(target_annual_vol=0.40, vol_window=20, periods_per_year=365.0)
    view = build_data_view(bars, len(bars) - 1)

    import statistics

    window = closes[len(closes) - 22 : len(closes) - 1]
    returns = [math.log(b / a) for a, b in zip(window, window[1:])]
    expected = 0.40 / (statistics.stdev(returns) * math.sqrt(365.0))
    assert ws.weight(view) == pytest.approx(min(expected, 1.0), rel=1e-12)


def test_inverse_vol_weight_is_capped_at_one():
    bars = flat_bars([100.0 + i * 1e-6 for i in range(40)])  # near-zero vol
    ws = InverseVolatilityWeight(target_annual_vol=0.40, vol_window=20)
    assert ws.weight(build_data_view(bars, len(bars) - 1)) == 1.0


def test_inverse_vol_weight_uses_only_bars_before_the_current_one():
    """D44: the vol estimate must not see today's return. Changing only the CURRENT
    bar's close must leave the weight unchanged."""
    closes = [100.0 * (1.0 + 0.01 * math.sin(i)) for i in range(40)]
    ws = InverseVolatilityWeight(vol_window=20)
    a = flat_bars(closes)
    b = flat_bars(closes[:-1] + [closes[-1] * 3.0])
    i = len(a) - 1
    assert ws.weight(build_data_view(a, i)) == ws.weight(build_data_view(b, i))


def test_degenerate_vol_window_stands_aside_rather_than_sizing_infinitely():
    bars = flat_bars([100.0] * 40)
    assert InverseVolatilityWeight(vol_window=20).weight(build_data_view(bars, 39)) is None


def _volatile_uptrend(n: int = 90) -> list[Bar]:
    """Daily moves large enough that a 40% annual vol target actually binds
    (0.40/√365 ≈ 2.09% per day), on a path that still breaks out and stays up."""
    closes, p = [], 100.0
    for i in range(n):
        p *= 1.0 + (0.06 if i % 3 == 0 else -0.03) + 0.004
        closes.append(p)
    return flat_bars(closes, spread=0.1)


def test_at_entry_sizing_holds_its_weight_for_the_life_of_the_trade():
    bars = _volatile_uptrend()
    s = BreakoutStrategy(
        "s", "X", n_entry=20, n_exit=10,
        weight_source=InverseVolatilityWeight(vol_window=20, rebalance="at_entry"),
    )
    w = weights(s, bars)
    trade = [x for x in w if x > 0]
    assert trade and max(trade) < 1.0, "vol target never bound — the test would be vacuous"
    # One trade in this path; every bar of it carries the entry weight unchanged.
    assert len(set(trade)) == 1, "at_entry sizing changed weight mid-trade"


def test_every_bar_sizing_updates_the_weight_while_long():
    bars = _volatile_uptrend()
    s = BreakoutStrategy(
        "s", "X", n_entry=20, n_exit=10,
        weight_source=InverseVolatilityWeight(vol_window=20, rebalance="every_bar"),
    )
    trade = [x for x in weights(s, bars) if x > 0]
    assert trade and max(trade) < 1.0
    assert len(set(trade)) > 1


def test_fixed_weight_is_constant():
    assert FixedWeight(0.5).weight(build_data_view(flat_bars([1, 2, 3]), 2)) == 0.5


# ------------------------------------------------------------------- config round trip


def test_strategy_config_round_trips_through_the_factory():
    original = BreakoutStrategy(
        "s", "X", n_entry=30, n_exit=5,
        weight_source=InverseVolatilityWeight(target_annual_vol=0.3, vol_window=15, rebalance="every_bar"),
        filters=(ConsecutiveCloseFilter(2), TrendGateFilter(100)),
    )
    rebuilt = build_breakout_strategy(original.config(), "s", "X")
    assert rebuilt.config() == original.config()
    assert rebuilt.warm_up_bars() == original.warm_up_bars()

    closes = [100 + math.sin(i / 5) * 10 + i * 0.2 for i in range(300)]
    bars = flat_bars(closes)
    assert weights(rebuilt, bars) == weights(build_breakout_strategy(original.config(), "s", "X"), bars)


def test_unknown_component_type_fails_loudly_naming_the_key():
    # This used "volume_confirmation" as its unknown-filter example, because D111 had
    # it recorded as blocked and no such filter existed. D168 built it, so the example
    # had to move to a type that is genuinely unregistered — the test failing when the
    # filter landed is the registry behaving correctly, not a regression.
    with pytest.raises(ConfigError, match="unknown type"):
        build_entry_filter({"type": "open_interest_confirmation", "multiple": 1.5})
    with pytest.raises(ConfigError, match="unknown type"):
        build_weight_source({"type": "kelly"})
    with pytest.raises(ConfigError, match="breakout_long_flat"):
        build_breakout_strategy({"type": "mean_reversion"}, "s", "X")


def test_warm_up_is_the_max_across_every_component():
    s = BreakoutStrategy(
        "s", "X", n_entry=20, n_exit=10,
        weight_source=InverseVolatilityWeight(vol_window=30),
        filters=(TrendGateFilter(200), VolatilityContractionFilter(long_window=100)),
    )
    assert s.warm_up_bars() == 200  # SMA gate dominates
    # And every component is evaluable at exactly that index, with none reachable one
    # bar earlier — the guard is tight, not padded.
    bars = flat_bars([100 + math.sin(i / 4) for i in range(400)])
    view = build_data_view(bars, s.warm_up_bars())
    s.entry_condition(view, s.warm_up_bars())
    for f in s.filters:
        f.accepts(view, lambda j: s.entry_condition(view, j))
    assert s.weight_source.weight(view) is not None


def test_no_targets_before_warm_up():
    s = BreakoutStrategy("s", "X", n_entry=20, n_exit=10, filters=(TrendGateFilter(200),))
    bars = flat_bars([100 + i for i in range(260)])
    w = weights(s, bars)
    assert all(x == 0.0 for x in w[:200])
    assert w[200] > 0.0  # a relentless ramp enters on the first bar it is allowed to


def test_dataview_out_of_range_is_a_look_ahead_error_not_a_silent_wrap():
    """Guards the primitive the whole strategy is built on: negative indices resolve
    relative to the current bar, so an off-by-one in a window would wrap rather than
    raise if DataView allowed it. It does not."""
    from backtest_framework.engine.dataview import LookAheadError

    view: DataView = build_data_view(flat_bars([1, 2, 3]), 1)
    with pytest.raises(LookAheadError):
        view[2]
    with pytest.raises(LookAheadError):
        view[-5]
