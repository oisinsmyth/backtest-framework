"""Unit gates for setup composition (D204, WP2).

Two groups matter here.

The first is causality again, one level up. `structure.py`'s detectors are individually
guarded, but composition is where a leak can be *reintroduced* — a window that reads one
bar past its own end, an invalidation checked after the fact. The detectors being clean
does not make the composition clean.

The second is the monotonicity of `first_entry`. The whole ablation in WP4 rests on it:
adding a filter must only ever delay an entry or remove it, never move it earlier. If that
fails, the 16 arms are not nested and comparing them says nothing.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from itertools import combinations

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import Event, market_structure
from backtest_framework.research.structure_setups import (
    ATR_WINDOW_15M,
    CONDITIONS,
    find_setups,
    friction_in_r,
    required_hit_rate,
    stop_distance,
)
from backtest_framework.research.terrain_nulls import TOUCH_ATR
from backtest_framework.research.terrain_strategies import MAX_HOLD
from backtest_framework.research.terrain_swing import SWING_K
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)
ATR_WINDOW = 200
"""A short ATR window for the tests, so a few thousand synthetic bars are enough to warm it
up. The study itself uses `ATR_WINDOW_15M`; what is being tested here is the composition,
not the calendar match."""


def wandering(n: int, seed: int, start: float = 100.0) -> list[TimestampedBar]:
    rng = random.Random(seed)
    out, px = [], start
    for i in range(n):
        o = px
        px *= math.exp(rng.gauss(0.0, 0.004))
        c = px
        h = max(o, c) * (1.0 + abs(rng.gauss(0.0, 0.001)))
        lo = min(o, c) * (1.0 - abs(rng.gauss(0.0, 0.001)))
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c)))
    return out


def setups_on(bars, k=2, touch=0.5):
    return find_setups(bars, k, touch, atr_window=ATR_WINDOW).setups


BARS = wandering(4_000, seed=41)
SETUPS = setups_on(BARS)
POPULATION = find_setups(BARS, 2, 0.5, atr_window=ATR_WINDOW)


def test_the_fixture_produces_a_population_worth_asserting_on():
    """A guard on the tests themselves. Every assertion below quantifies over setups, and
    a fixture that produced none would make all of them pass vacuously — the same failure
    mode D205 recorded for the leg-direction test."""
    assert len(SETUPS) > 50
    assert {s.direction for s in SETUPS} == {1, -1}
    assert any(s.holds and any(held for held in s.holds) for s in SETUPS)


# ----------------------------------------------------------------- causality, one level up

@pytest.mark.parametrize("index", (1_500, 2_500, 3_200))
def test_setups_that_closed_before_an_index_are_unaffected_by_bars_after_it(index):
    rng = random.Random(5)
    corrupted = list(BARS[: index + 1])
    px = BARS[index].bar.close
    for i in range(index + 1, len(BARS)):
        px *= math.exp(rng.gauss(0.0, 0.05))
        o, c = px, px * 1.01
        corrupted.append(
            TimestampedBar(BARS[i].timestamp, Bar(o, max(o, c) * 1.03, min(o, c) * 0.97, c))
        )

    def closed_before(series):
        return [s for s in setups_on(series) if s.window[-1] < index]

    real, fake = closed_before(BARS), closed_before(corrupted)
    assert len(real) > 10, "the probe index must leave a population behind it"
    assert real == fake


def test_a_window_never_extends_past_the_next_change_of_character():
    """A superseded setup is not merely stale, it has been contradicted. Letting its
    window run through the next CHoCH would count entries the structure had already
    disowned, and would double-count bars across two setups."""
    states = market_structure(BARS, 2)
    chochs = [
        t for t, s in enumerate(states) if s.event in (Event.CHOCH_UP, Event.CHOCH_DOWN)
    ]
    for setup in SETUPS:
        later = [c for c in chochs if c > setup.choch_index]
        if later:
            assert setup.window[-1] < later[0]


def test_a_window_is_contiguous_and_starts_where_the_leg_confirms():
    for setup in SETUPS:
        assert setup.window[0] == setup.ready_index
        assert list(setup.window) == list(range(setup.window[0], setup.window[-1] + 1))
        assert len(setup.window) == len(setup.holds)
        assert len(setup.window) <= MAX_HOLD + 1


def test_a_window_never_outlives_its_own_invalidation():
    """Invalidation is a close beyond the leg's origin: the retracement is past 1.0 and
    the structure the setup was built on is gone."""
    for setup in SETUPS:
        leg = setup.leg
        for index in setup.window:
            close = BARS[index].bar.close
            if setup.direction > 0:  # up leg, invalidated by a close below its origin
                assert close >= leg.start_price or index == setup.window[-1]
            else:
                assert close <= leg.start_price or index == setup.window[-1]


# ------------------------------------------------------- the nesting the ablation needs

def test_the_base_arm_enters_at_the_bar_the_leg_confirms():
    """C1 alone carries no extra parameter. It is the loosest rule the structure supports,
    which is what WP4a needs: a large population to annotate rather than one already
    filtered by the thing under test."""
    for setup in SETUPS:
        assert setup.first_entry(()) == setup.ready_index


def test_adding_a_filter_only_ever_delays_an_entry_or_removes_it():
    """The property the 16-arm ablation rests on. If a superset could enter EARLIER the
    arms would not be nested and comparing them would say nothing about what a filter
    adds."""
    for setup in SETUPS:
        for size in range(len(CONDITIONS)):
            for base in combinations(CONDITIONS, size):
                base_entry = setup.first_entry(base)
                if base_entry is None:
                    # A superset of an unsatisfiable set is unsatisfiable.
                    for extra in CONDITIONS:
                        if extra not in base:
                            assert setup.first_entry(base + (extra,)) is None
                    continue
                for extra in CONDITIONS:
                    if extra in base:
                        continue
                    wider = setup.first_entry(base + (extra,))
                    assert wider is None or wider >= base_entry


def test_ever_and_first_entry_agree_on_a_single_condition():
    for setup in SETUPS:
        for condition in CONDITIONS:
            assert setup.ever(condition) == (setup.first_entry((condition,)) is not None)


def test_conditions_are_drawn_only_from_the_registered_set():
    for setup in SETUPS:
        for held in setup.holds:
            assert held <= set(CONDITIONS)


# ------------------------------------------------------------------- the cost arithmetic

def test_friction_reproduces_the_numbers_d196_already_published():
    """D196/D197 measured a 40 bps round trip at **0.49R on a 0.5-ATR stop** and **0.12R
    at 2 ATR**. Reproduced here from the implied daily ATR rather than retyped as a
    constant, so the formula is pinned against a number this project already stands
    behind — the same discipline as anchoring to a reference you did not write."""
    price = 10_000.0
    atr = 0.016_33 * price  # the ATR/price the published pair implies
    assert friction_in_r(40.0, price, 0.5 * atr) == pytest.approx(0.49, abs=0.005)
    assert friction_in_r(40.0, price, 2.0 * atr) == pytest.approx(0.12, abs=0.005)


def test_friction_scales_inversely_with_the_stop_width():
    price = 100.0
    wide = friction_in_r(40.0, price, 2.0)
    tight = friction_in_r(40.0, price, 0.5)
    assert wide is not None and tight is not None
    assert tight == pytest.approx(4.0 * wide)


def test_required_hit_rate_is_the_break_even_algebra():
    # Frictionless 5R: p * 5 = (1 - p) * 1  ->  p = 1/6.
    assert required_hit_rate(5.0, 0.0) == pytest.approx(1.0 / 6.0)
    # With friction f: p = (1 + f) / (1 + target).
    assert required_hit_rate(5.0, 0.49) == pytest.approx(1.49 / 6.0)


def test_a_target_the_friction_has_already_eaten_returns_none():
    """A real outcome on a tight stop, not an error. The course's whole claim is a
    hit-rate argument at 5R made with costs omitted; this is the case where putting them
    back leaves no target at all."""
    assert required_hit_rate(0.4, 0.5) is None


def test_stop_distance_is_measured_to_the_swing_extreme():
    setup = SETUPS[0]
    entry = BARS[setup.ready_index].bar.close
    assert stop_distance(setup, entry) == abs(entry - setup.leg.end_price)


def test_degenerate_inputs_return_none_rather_than_a_number():
    assert friction_in_r(40.0, 0.0, 1.0) is None
    assert friction_in_r(40.0, 100.0, 0.0) is None


# ------------------------------------------------------------- pre-registered parameters

def test_an_unregistered_touch_band_is_refused():
    with pytest.raises(ValueError, match="unregistered search"):
        find_setups(BARS[:500], 2, 0.75, atr_window=ATR_WINDOW)


def test_states_from_a_different_series_are_refused():
    """Passing states is an optimisation — the state machine does not depend on the touch
    band. Passing states computed on OTHER bars would be silently wrong, so it is refused
    at the door rather than trusted to the caller."""
    with pytest.raises(ValueError, match="say nothing about this one"):
        find_setups(BARS[:500], 2, 0.5, states=market_structure(BARS, 2))


@pytest.mark.parametrize("k", SWING_K)
@pytest.mark.parametrize("touch", TOUCH_ATR)
def test_every_registered_cell_produces_setups(k, touch):
    """A cell that produced nothing would silently drop out of the sensitivity table and
    look like agreement."""
    assert len(setups_on(BARS, k, touch)) > 20


def test_the_calendar_matched_atr_window_is_twenty_days_of_15m_bars():
    assert ATR_WINDOW_15M == 20 * 96


# --------------------------------------------------------------- the drops are reported

def test_every_change_of_character_is_accounted_for():
    """The funnel starts above the setups, not at them. A count that only ever appears as
    a subtraction is a count nobody checks, so the drops are returned explicitly and this
    asserts they add up."""
    assert (
        len(POPULATION.setups)
        + POPULATION.dropped_no_leg
        + POPULATION.dropped_dead_on_arrival
        + POPULATION.dropped_no_atr
        == POPULATION.n_choch
    )
    assert POPULATION.n_choch > len(POPULATION.setups), "some drops must actually occur"


def test_a_setup_inside_the_atr_warm_up_is_refused_not_truncated():
    """Refusing is the honest option and truncating was the first implementation. The
    truncated form produced non-contiguous windows whose first bar was not the bar an entry
    became possible, silently shifting every base-arm entry forward — caught by
    `test_a_window_is_contiguous_and_starts_where_the_leg_confirms`, which is why that test
    is worth more than it looks."""
    population = find_setups(BARS, 2, 0.5, atr_window=1_500)
    assert population.dropped_no_atr > 0
    for setup in population.setups:
        assert list(setup.window) == list(range(setup.window[0], setup.window[-1] + 1))
        assert setup.window[0] == setup.ready_index
