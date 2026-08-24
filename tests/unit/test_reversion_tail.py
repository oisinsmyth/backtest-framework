"""Unit gates for the tail/frequency/fill study (D216).

D216 asks whether the reversion effect can ever clear a real cost. Everything in its answer
routes through three quantities, and each has a specific way of being silently wrong:

- **the break-even solver.** It is a fixed point, not a constant, and it decides every
  verdict in the study. Pinned against the closed form it must collapse to.
- **the maker arm.** It exists to model adverse selection, so an inverted fill convention
  would not crash — it would quietly report that adverse selection is *good for you*. Pinned
  by subset, by strictness, and by a constructed momentum series where the sign is known.
- **the rate.** This is not a hypothetical. The first version of `rate()` was
  `sum(1 for _, ok in rows)` with no `if ok`: it counted every row, returned 1.0 identically,
  made every cell read 100.00%, and drove the reading function to announce a positive. No
  test caught it — what caught it was the halves function, which sums bools correctly, and
  therefore disagreed with the headline. Two views of one quantity diverging is the same tell
  as D209. The pin below is the one that should have existed first.

Plus the pair this project has required since D180: the statistic must find nothing on a
random walk and something on a series built to contain the effect. Either alone proves
nothing.
"""

from __future__ import annotations

import importlib.util
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run_reversion_tail.py"

_spec = importlib.util.spec_from_file_location("reversion_tail", SCRIPT)
assert _spec is not None and _spec.loader is not None
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)

EPOCH = datetime(2020, 1, 1)


def _bars(closes, pad: float = 0.0):
    """Bars whose range is exactly the close-to-close move, unless `pad` says otherwise.

    **`pad` defaults to zero deliberately.** The first version of this helper padded every
    bar with a 0.1% wick on both sides, which meant a limit resting at the previous close
    was always traded through — the maker arm filled 434 of 434 events and the fill
    convention could not be tested at all. A fixture generous enough to fill everything
    cannot demonstrate selective filling."""
    out = []
    prev = closes[0]
    for i, c in enumerate(closes):
        hi, lo = max(prev, c) * (1 + pad), min(prev, c) * (1 - pad)
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(prev, hi, lo, c)))
        prev = c
    return out


def random_walk(n: int, seed: int, start: float = 100.0):
    rng = random.Random(seed)
    closes, px = [], start
    for _ in range(n):
        px *= math.exp(rng.gauss(0.0, 0.004))
        closes.append(px)
    return closes


def trending(n: int, seed: int, drift: float = 0.6, start: float = 100.0):
    """Momentum by construction: each step continues a fraction of the previous one.

    The potency fixture for the *maker* claim. On a path that keeps going, a limit that only
    fills on trade-through fills precisely into the continuations, so its outcomes must be
    worse than the taker arm's. If they are not, the fill convention is inverted."""
    rng = random.Random(seed)
    closes, px, last = [], start, 0.0
    for _ in range(n):
        shock = rng.gauss(0.0, 0.004) + drift * last
        px *= math.exp(shock)
        closes.append(px)
        last = shock
    return closes


# --------------------------------------------------------------------------------------
# The break-even solver. Every verdict in the study moves if this is subtly wrong.
# --------------------------------------------------------------------------------------


@pytest.mark.parametrize("atr_bp", [10.0, 38.3, 51.9, 381.6, 527.6])
@pytest.mark.parametrize("cost", [0.0, 1.0, 5.0, 40.0])
def test_the_solver_collapses_to_the_symmetric_closed_form(atr_bp, cost):
    """With `c_tp == c_stop` the fixed point must be exactly `0.5 + RT/ATR`.

    This is the identity the pre-registration quotes and the one a reader will check by
    hand. A solver that drifts from it here is wrong everywhere."""
    got = rt.break_even_p(atr_bp, cost, cost, cost)
    want = 0.5 + (cost + cost) / atr_bp
    assert got == pytest.approx(want, rel=1e-12)


def test_a_free_trade_breaks_even_at_a_coin_flip():
    assert rt.break_even_p(50.0, 0.0, 0.0, 0.0) == pytest.approx(0.5)


def test_the_asymmetric_fixed_point_is_harsher_than_the_symmetric_reading():
    """The take-profit rests and the stop crosses, so the round trip depends on `p`.

    Pricing it symmetrically at the cheaper leg — the "2 bp maker round trip" the
    pre-registration retracts — understates the hurdle. That understatement must be
    visible here, or the correction D216 makes to its own arithmetic is cosmetic."""
    atr = 38.3
    honest = rt.break_even_p(atr, 1.0, 1.0, 10.0)
    too_generous = rt.break_even_p(atr, 1.0, 1.0, 1.0)
    assert honest > too_generous
    assert honest == pytest.approx(0.6377, abs=5e-4)
    assert too_generous == pytest.approx(0.5522, abs=5e-4)


def test_an_unreachable_break_even_is_infinite_rather_than_a_plausible_number():
    """When the stop's cost swamps the bracket the denominator goes non-positive. Returning
    a wrapped-around finite `p*` would let an impossible cell read as a cleared one."""
    assert rt.break_even_p(10.0, 40.0, 40.0, 5.0) == float("inf")
    assert rt.break_even_p(10.0, 40.0, 40.0, 0.0) == float("inf")


# --------------------------------------------------------------------------------------
# The sampler.
# --------------------------------------------------------------------------------------


def test_selected_events_respect_the_spacing_rule_and_are_a_subset_of_the_qualifying_bars():
    closes = random_walk(3_000, seed=11)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    lookback, warmup, horizon = rt.LOOKBACK, 200, rt.HORIZON

    events = rt.tail_events(closes, atr, lookback, warmup, horizon, 1.0)
    assert events, "the fixture must produce some events or the test is vacuous"

    assert all(b - a >= lookback for a, b in zip(events, events[1:])), "spacing violated"

    for t in events:
        assert abs(rt.move_at(closes, atr, t, lookback)) >= 1.0
        assert t >= max(warmup, lookback)
        assert t < len(closes) - horizon - 1


def test_a_higher_cutoff_selects_strictly_fewer_events():
    closes = random_walk(3_000, seed=12)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    counts = [
        len(rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, c))
        for c in (0.5, 1.0, 2.0, 3.0)
    ]
    assert counts == sorted(counts, reverse=True)
    assert counts[0] > counts[-1]


# --------------------------------------------------------------------------------------
# The fill convention. An inverted maker arm would report adverse selection as a benefit.
# --------------------------------------------------------------------------------------


def test_a_resting_bid_fills_only_when_the_next_bar_trades_through_it():
    """Constructed by hand so the convention is readable rather than inferred."""
    limit = 100.0
    below = TimestampedBar(EPOCH, Bar(limit, limit, limit, limit))
    trades_through = TimestampedBar(EPOCH, Bar(limit, limit, 99.0, 99.5))
    touches_only = TimestampedBar(EPOCH, Bar(limit, limit + 1, limit, limit + 0.5))

    assert rt.maker_filled([below, trades_through], 0, +1) is True
    assert rt.maker_filled([below, touches_only], 0, +1) is False
    # The mirror: a resting offer needs the next bar to trade above it.
    assert rt.maker_filled([below, touches_only], 0, -1) is True
    assert rt.maker_filled([below, trades_through], 0, -1) is False


def test_a_touch_exactly_at_the_limit_does_not_fill():
    """D9's pessimistic convention, reused. A touch-fills implementation would inflate the
    maker sample with exactly the events that did not continue — the favourable half."""
    limit = 100.0
    a = TimestampedBar(EPOCH, Bar(limit, limit, limit, limit))
    touch = TimestampedBar(EPOCH, Bar(limit, limit, limit, limit))
    assert rt.maker_filled([a, touch], 0, +1) is False
    assert rt.maker_filled([a, touch], 0, -1) is False


def test_the_last_bar_cannot_fill_because_there_is_no_next_bar():
    limit = 100.0
    only = TimestampedBar(EPOCH, Bar(limit, limit, limit, limit))
    assert rt.maker_filled([only], 0, +1) is False


def test_maker_fills_are_a_strict_subset_of_taker_fills():
    """The taker arm always fills; the maker arm fills sometimes. If maker ever fills where
    taker does not, the convention is inverted and every adverse-selection number in the
    study flips sign."""
    closes = random_walk(4_000, seed=13)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    events = rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, 1.0)
    assert len(events) > 50

    cell = rt.measure(bars, closes, atr, events, rt.LOOKBACK, rt.HORIZON)
    assert cell["taker"]["n"] == len(events)
    assert cell["maker"]["n"] < cell["taker"]["n"], "maker must fill strictly less often"
    assert 0.0 < cell["maker"]["fill_rate"] < 1.0

    filled = {
        t for t in events
        if rt.maker_filled(bars, t, -1 if rt.move_at(closes, atr, t, rt.LOOKBACK) > 0 else 1)
    }
    assert filled.issubset(set(events))


def test_adverse_selection_is_visible_on_a_series_built_with_momentum():
    """The potency companion to the measurement.

    On a path that continues, the maker arm fills into the continuations by construction, so
    it must score worse than the taker arm. A study that reports adverse selection needs to
    demonstrate its instrument can see it where it is known to be."""
    closes = trending(6_000, seed=14, drift=0.6)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    events = rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, 1.0)
    assert len(events) > 100

    cell = rt.measure(bars, closes, atr, events, rt.LOOKBACK, rt.HORIZON)
    assert cell["adverse_selection"] is not None
    assert cell["adverse_selection"] > 0.0, (
        "maker must score worse than taker on a momentum path; a non-positive value here "
        "means the fill convention is inverted"
    )


# --------------------------------------------------------------------------------------
# The rate. This is the regression pin for the bug that shipped.
# --------------------------------------------------------------------------------------


def test_the_reversion_rate_counts_only_the_reversions():
    """`sum(1 for _, ok in rows)` — the shipped bug — returns 1.0 for every input below.

    Hand-counted, so the expected value does not come from the same expression under test.
    That was the flaw in D212's cost pin, which compared a function to itself."""
    assert rt._rate([(0, True), (1, False), (2, True), (3, False)]) == pytest.approx(0.5)
    assert rt._rate([(0, True), (1, True), (2, True), (3, False)]) == pytest.approx(0.75)
    assert rt._rate([(0, False), (1, False)]) == pytest.approx(0.0)
    assert rt._rate([(0, True)]) == pytest.approx(1.0)
    assert rt._rate([]) is None


def test_the_rate_is_not_identically_one_on_a_real_measurement():
    """The bug's signature, pinned directly: every cell read exactly 100.00%.

    A random walk cannot revert 100% of the time. Asserting the *shape* of the failure and
    not only the arithmetic means a different implementation of the same mistake is still
    caught."""
    closes = random_walk(4_000, seed=15)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    events = rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, 1.0)
    cell = rt.measure(bars, closes, atr, events, rt.LOOKBACK, rt.HORIZON)
    assert 0.2 < cell["taker"]["p"] < 0.8, cell["taker"]["p"]


def test_the_headline_rate_and_the_halves_agree():
    """The two views that disagreed and exposed the bug, now required to agree.

    The headline must be the sample-weighted blend of the two halves. This is the general
    form of both D209 and the `rate()` bug: one quantity computed two ways, checked against
    each other rather than each against itself."""
    closes = random_walk(6_000, seed=16)
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    events = rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, 0.8)
    cell = rt.measure(bars, closes, atr, events, rt.LOOKBACK, rt.HORIZON)

    blk = cell["taker"]
    assert blk["p_first_half"] is not None and blk["p_second_half"] is not None
    cut = len(bars) // 2
    n_early = sum(1 for t in events if t <= cut)
    n_late = blk["n"] - n_early
    blended = (
        blk["p_first_half"] * n_early + blk["p_second_half"] * n_late
    ) / blk["n"]
    assert blended == pytest.approx(blk["p"], abs=1e-12)


# --------------------------------------------------------------------------------------
# The verdict, and the arm/fee pairing that this study's first draft got wrong.
# --------------------------------------------------------------------------------------


def test_an_underpowered_bucket_carries_no_verdict():
    """Asserted rather than left to the reader. A cell with nine events can post a 100% rate
    and clear any hurdle; `powered` is what stops that being read as a result."""
    cell = {
        "maker": {"n": rt.MIN_N - 1, "p": 0.99, "p_first_half": 0.99, "p_second_half": 0.99}
    }
    v = rt.verdict_for(cell, 0.55, "maker")
    assert v["powered"] is False
    assert v["clears_break_even"] is False, "an underpowered cell must not clear"


def test_the_powered_boundary_is_inclusive_at_min_n():
    cell = {"maker": {"n": rt.MIN_N, "p": 0.99, "p_first_half": 0.99, "p_second_half": 0.99}}
    assert rt.verdict_for(cell, 0.55, "maker")["powered"] is True


def test_one_good_half_is_not_enough_to_be_stable():
    """D213 is the reason this hurdle exists: a mined rule that inverted out of sample."""
    cell = {"maker": {"n": 500, "p": 0.60, "p_first_half": 0.70, "p_second_half": 0.50}}
    v = rt.verdict_for(cell, 0.55, "maker")
    assert v["clears_break_even"] is True
    assert v["stable_across_halves"] is False


def test_an_infinite_break_even_clears_nothing():
    cell = {"maker": {"n": 500, "p": 1.0, "p_first_half": 1.0, "p_second_half": 1.0}}
    v = rt.verdict_for(cell, float("inf"), "maker")
    assert v["clears_break_even"] is False
    assert v["stable_across_halves"] is False


def test_every_fee_tier_declares_the_fill_arm_it_is_coherent_with():
    """The regression pin for this study's second defect.

    The first draft scored both arms against every tier, which paired a TAKER fill with
    MAKER costs and produced a pass: it took `p` from the population that crossed the spread
    and the cost from the population that rested. Each tier now names its arm, and a maker
    tier may not be scored on taker fills."""
    assert {f["name"] for f in rt.FEES}, "fee tiers must exist"
    for f in rt.FEES:
        assert f["arm"] in ("maker", "taker"), f
        # A tier whose entry is priced at the maker fee must be scored on maker fills.
        if f["c_in"] <= 5.0:
            assert f["arm"] == "maker", f["name"]
        else:
            assert f["arm"] == "taker", f["name"]
    assert rt.VERDICT_FEE in {f["name"] for f in rt.FEES}
    verdict_tier = next(f for f in rt.FEES if f["name"] == rt.VERDICT_FEE)
    assert verdict_tier["arm"] == "maker"
    assert verdict_tier["c_stop"] > verdict_tier["c_tp"], (
        "the verdict tier's whole point is that a stop cannot rest and a take-profit can"
    )


# --------------------------------------------------------------------------------------
# The mandatory pair: nothing on noise, something on a planted effect.
# --------------------------------------------------------------------------------------


def _tail_rate(closes, cutoff: float) -> tuple[float, int]:
    bars = _bars(closes)
    atr = rt.rolling_mean_true_range(bars, 200)
    events = rt.tail_events(closes, atr, rt.LOOKBACK, 200, rt.HORIZON, cutoff)
    cell = rt.measure(bars, closes, atr, events, rt.LOOKBACK, rt.HORIZON)
    return cell["taker"]["p"], cell["taker"]["n"]


def test_the_tail_statistic_finds_nothing_on_a_random_walk():
    """At a tail cutoff, not just at the median — a cutoff is exactly where a statistic can
    manufacture a staircase out of noise, and the study reads its answer off the tail."""
    rates = []
    for seed in range(6):
        p, n = _tail_rate(random_walk(6_000, seed=200 + seed), cutoff=1.5)
        assert n > 40, n
        rates.append(p)
    mean = sum(rates) / len(rates)
    assert 0.45 < mean < 0.55, rates


def test_the_tail_statistic_finds_the_effect_on_a_planted_reverting_series():
    rng_rates = []
    for seed in range(4):
        closes, px, last = [], 100.0, 0.0
        rng = random.Random(300 + seed)
        for _ in range(6_000):
            shock = rng.gauss(0.0, 0.004) - 0.55 * last
            px *= math.exp(shock)
            closes.append(px)
            last = shock
        p, n = _tail_rate(closes, cutoff=1.5)
        assert n > 40, n
        rng_rates.append(p)
    assert min(rng_rates) > 0.55, rng_rates
