"""Composing the five detectors into setups — the object every later work package counts.

WP2 of `New Docs/STRUCTURE_MODEL.md` (D204). `structure.py` produces the components; this
turns them into the thing the course actually trades: *after a change of character, wait
for the pullback, and enter where the filters agree.*

## One setup population, every arm

A `Setup` records, for every bar of its pullback window, **which conditions held there** —
not whether some particular combination fired. Any subset of `{C2, C3, C4, C5}` reads its
own entry bar off the same object with `first_entry`.

That is deliberate and it is the pairing discipline this project keeps insisting on. The
16-arm ablation in WP4 must differ in the filters and in **nothing else**: same setups,
same windows, same invalidation, same bars. Recomputing per arm would let a difference in
setup construction leak into a difference attributed to a filter, which is exactly the
confound `terrain_field_nulls.compare_field_to_null` enforces away by putting the shared
parts in the signature.

## The base rule is C1 alone, and it is as loose as it can honestly be

An entry becomes possible at the bar the impulse leg **confirms** — `leg.end_index + k`.
Not before: until then the leg's extreme is still in the future, and a retracement measured
against it would be measured against a number that does not exist yet.

The C1-only arm enters at that bar. It carries **no extra parameter**, and it is the
loosest rule the structure supports, which is what WP4a needs — a large population to
annotate rather than a small one that has already been filtered by the thing under test.

## The window closes for three reasons, none of them tuned

- **Invalidation**: price closes beyond the leg's origin. The retracement is past 1.0, the
  structure that produced the setup is gone, and there is nothing left to pull back into.
- **Supersession**: a new change of character fires. The old setup is not merely stale, it
  has been contradicted.
- **`MAX_HOLD`**, an existing named constant (`terrain_strategies.MAX_HOLD`, 60 bars),
  reused rather than re-chosen. D199's convention: a window picked to make a verdict come
  out is the same failure as a threshold picked that way.

## What is NOT decided here

No stop, no target, no exit. Those are the frozen wrapper and they live in
`structure_strategies.py`, because D203's finding is that a wrapper is where a study goes
to fool itself. The census in WP2 runs on setups alone and reports counts.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Iterator, Sequence

from ..data.bars import TimestampedBar
from .structure import (
    RSI_OVERBOUGHT,
    RSI_OVERSOLD,
    Event,
    Leg,
    StructureState,
    fair_value_gaps,
    market_structure,
    ratio_price,
    retracement,
    rsi,
)
from .terrain import rolling_mean_true_range
from .terrain_nulls import TOUCH_ATR
from .terrain_strategies import MAX_HOLD

ATR_WINDOW_15M = 1_920
"""20 calendar days at 96 bars a day — D194's calendar match, reused not re-chosen.

The true range is still a 15m one, so this is 15m volatility measured over a 20-day window.
That is the intended object: on 15m bars a touch band should be scaled by 15m movement, and
the window length is what stops five hours of volatility setting the scale for a study
spanning years."""

GOLDEN_RATIO = 0.618
"""The level the course trades. Its status as anything other than one number among many is
the question WP3 asks against `structure.PLACEBO_RATIOS`, and nothing here presumes it."""

CONDITIONS = ("C2", "C3", "C4", "C5")
"""The filters that can be layered on top of C1. C1 is not in this list because it is not a
filter — it is what creates the setup at all."""


@dataclass(frozen=True)
class Setup:
    """One change of character and the pullback window that follows it."""

    choch_index: int
    direction: int
    """+1 the structure turned up and the pullback is bought, -1 turned down and sold."""
    leg: Leg
    ready_index: int
    """The bar the impulse leg confirmed — the first bar an entry is possible at all."""
    window: tuple[int, ...]
    """Bar indices in the pullback window, ascending, starting at `ready_index`."""
    holds: tuple[frozenset[str], ...]
    """Which of `CONDITIONS` held at each bar of `window`. Same length as `window`."""
    closed_by: str
    """`invalidated`, `superseded`, `max_hold` or `series_end`. Reported in the census
    because a population dominated by `series_end` would mean the window is doing nothing
    and the counts below it are about the fixture's edges."""

    def first_entry(self, required: Iterable[str] = ()) -> int | None:
        """The first bar where every condition in `required` holds SIMULTANEOUSLY.

        Simultaneity is the point. The course's claim is confluence — the filters lining
        up at one price at one time — not that each was satisfied at some point during the
        pullback. Those are very different populations and WP2 reports both, because the
        gap between them is the confluence claim measured in counts."""
        need = frozenset(required)
        for index, held in zip(self.window, self.holds):
            if need <= held:
                return index
        return None

    def ever(self, condition: str) -> bool:
        """Did `condition` hold anywhere in the window, regardless of the others?"""
        return any(condition in held for held in self.holds)


@dataclass(frozen=True)
class SetupPopulation:
    """Every setup found, and every change of character that did NOT become one.

    The drops are returned rather than left implicit because WP2's funnel starts above the
    setups, not at them: "4,366 changes of character produced 3,876 setups" is a different
    and more honest opening line than "3,876 setups". A count that only ever appears as a
    subtraction is a count nobody checks."""

    setups: tuple[Setup, ...]
    n_choch: int
    dropped_no_leg: int
    """The impulse leg never confirmed before the next change of character superseded it.
    Dropped, never imputed: a pullback with no leg has no retracement to measure."""
    dropped_dead_on_arrival: int
    """The window was empty: price had already closed beyond the leg's origin by the bar
    the leg confirmed, so the setup was invalidated before an entry was ever possible.

    A real category, not a rounding error. The impulse leg's end pivot needs `k` bars to
    confirm, and in a fast market price can retrace the whole leg inside those bars. The
    base arm would otherwise have "entered" at a bar where the structure was already gone.

    Counted rather than silently skipped: the first implementation dropped these with an
    `if window:` and the arithmetic did not add up, which is the only reason anyone
    noticed."""
    dropped_no_atr: int
    """The leg confirmed inside the ATR warm-up, so no touch band exists.

    Refused outright rather than evaluated on the bars that do have an ATR. Truncating the
    window instead was the first implementation and a test caught it: it produced
    non-contiguous windows whose first bar was not the bar an entry became possible, which
    would have silently shifted every base-arm entry forward by an unrecorded amount."""

    def __len__(self) -> int:
        return len(self.setups)

    def __iter__(self) -> Iterator[Setup]:
        return iter(self.setups)


def _gap_condition(
    gaps_in_leg: Sequence[tuple[int, float, float, int | None]], index: int, price: float
) -> bool:
    """Is `price` inside a gap that formed within the impulse leg and is still alive?

    Membership of the band, not proximity to the midpoint. The band IS the zone; adding a
    tolerance around the midpoint would introduce a second free parameter to say something
    the band already says. The midpoint distance is logged as a continuous feature in WP4
    instead, where a continuous reading is what the analysis wants."""
    for formed_at, lo, hi, filled_at in gaps_in_leg:
        if formed_at > index:
            continue
        if filled_at is not None and index >= filled_at:
            continue
        if lo <= price <= hi:
            return True
    return False


def find_setups(
    bars: Sequence[TimestampedBar],
    k: int,
    touch_atr: float,
    *,
    fib_ratio: float = GOLDEN_RATIO,
    max_wait: int = MAX_HOLD,
    atr_window: int = ATR_WINDOW_15M,
    states: Sequence[StructureState] | None = None,
) -> SetupPopulation:
    """Every change of character in `bars`, with its pullback window annotated.

    `states` may be supplied to reuse one `market_structure` pass across several parameter
    cells that share `k` — the state machine is the expensive part and it does not depend
    on `touch_atr` or `fib_ratio`. Passing states computed at a DIFFERENT `k` would be
    silently wrong, so the argument is keyword-only and the caller owns the pairing.

    Conditions at bar `t`, all evaluated on the close:

    - **C2** the flipped level is still alive and `|close - level| <= touch_atr * ATR`
    - **C3** `|close - ratio_price(leg, fib_ratio)| <= touch_atr * ATR`
    - **C4** the close sits inside a live gap formed within the leg, in the leg's direction
    - **C5** RSI is oversold for a long setup, overbought for a short one

    C2 and C3 share one tolerance. That is not a saving, it is a constraint: two tolerances
    would be a two-dimensional search dressed as two definitions, and `STRUCTURE_MODEL.md`
    fixes the band once for exactly this reason."""
    if touch_atr not in TOUCH_ATR:
        raise ValueError(
            f"touch_atr must be one of {TOUCH_ATR}, got {touch_atr}. "
            "STRUCTURE_MODEL.md fixes the set; a third value is an unregistered search."
        )
    if states is None:
        states = market_structure(bars, k)
    if len(states) != len(bars):
        raise ValueError(
            f"{len(states)} states for {len(bars)} bars — states computed on a different "
            "series say nothing about this one."
        )

    atr = rolling_mean_true_range(bars, atr_window)
    strength = rsi(bars)
    gaps = fair_value_gaps(bars)

    choch_bars = [
        t
        for t, s in enumerate(states)
        if s.event in (Event.CHOCH_UP, Event.CHOCH_DOWN)
    ]
    next_choch = {}
    for a, b in zip(choch_bars, choch_bars[1:]):
        next_choch[a] = b

    out: list[Setup] = []
    dropped_no_leg = dropped_no_atr = dropped_dead = 0
    for c in choch_bars:
        state = states[c]
        direction = state.choch_direction
        level = state.choch_level
        # The leg is None until its end pivot confirms; scan forward for the bar it
        # appears, which is the earliest an entry could be evaluated.
        ready = _first_leg_bar(states, c, next_choch.get(c, len(bars)))
        if ready is None:
            dropped_no_leg += 1
            continue
        if not math.isfinite(atr[ready]) or atr[ready] <= 0.0:
            dropped_no_atr += 1
            continue
        leg = states[ready].leg
        assert leg is not None  # _first_leg_bar returns only bars where it is set
        target_price = ratio_price(leg, fib_ratio)
        in_leg = [
            (g.formed_at, g.lo, g.hi, g.filled_at)
            for g in gaps
            if g.direction == direction and leg.start_index <= g.formed_at <= leg.end_index
        ]

        window: list[int] = []
        holds: list[frozenset[str]] = []
        closed_by = "series_end"
        limit = min(ready + max_wait, len(bars) - 1)
        supersede = next_choch.get(c)
        for t in range(ready, limit + 1):
            if supersede is not None and t >= supersede:
                closed_by = "superseded"
                break
            close = bars[t].bar.close
            depth = retracement(leg, close)
            if depth is not None and depth > 1.0:
                closed_by = "invalidated"
                break
            band = atr[t]
            if not math.isfinite(band) or band <= 0.0:
                # Cannot happen after the warm-up check above unless every true range in
                # the window is zero. Ends the window rather than skipping the bar: a
                # skipped bar makes the window non-contiguous, and its first bar stops
                # being the bar an entry became possible.
                closed_by = "atr_unavailable"
                break
            tolerance = touch_atr * band
            held: set[str] = set()
            if (
                level is not None
                and states[t].choch_index == c
                and states[t].level_alive
                and abs(close - level) <= tolerance
            ):
                held.add("C2")
            if abs(close - target_price) <= tolerance:
                held.add("C3")
            if _gap_condition(in_leg, t, close):
                held.add("C4")
            value = strength[t]
            if math.isfinite(value) and (
                (direction > 0 and value <= RSI_OVERSOLD)
                or (direction < 0 and value >= RSI_OVERBOUGHT)
            ):
                held.add("C5")
            window.append(t)
            holds.append(frozenset(held))
        else:
            closed_by = "max_hold" if limit == ready + max_wait else "series_end"

        if not window:
            dropped_dead += 1
            continue
        out.append(
            Setup(
                choch_index=c,
                direction=direction,
                leg=leg,
                ready_index=ready,
                window=tuple(window),
                holds=tuple(holds),
                closed_by=closed_by,
            )
        )
    return SetupPopulation(
        setups=tuple(out),
        n_choch=len(choch_bars),
        dropped_no_leg=dropped_no_leg,
        dropped_dead_on_arrival=dropped_dead,
        dropped_no_atr=dropped_no_atr,
    )


def _first_leg_bar(
    states: Sequence[StructureState], choch_index: int, limit: int
) -> int | None:
    """The bar this CHoCH's impulse leg becomes available on, or None if it never does.

    A leg that has not confirmed before the next change of character never confirms for
    this setup — the state machine has moved on. Those setups are dropped and counted, not
    imputed: a pullback with no leg has no retracement to measure, and inventing one would
    be the deepest kind of quiet wrong answer."""
    for t in range(choch_index, min(limit, len(states))):
        state = states[t]
        if state.choch_index != choch_index:
            return None
        if state.leg is not None:
            return t
    return None


def stop_distance(setup: Setup, entry_price: float) -> float:
    """Distance from `entry_price` to the stop, in price units.

    The course places the stop beyond the swing extreme that defined the structure — which
    is the impulse leg's end. No buffer is added: a buffer would be a free parameter, and
    the sensitivity of everything downstream to stop WIDTH is precisely what WP2's cost
    arithmetic is about to measure."""
    return abs(entry_price - setup.leg.end_price)


def friction_in_r(cost_bps: float, entry_price: float, stop: float) -> float | None:
    """A round trip of `cost_bps`, expressed as a fraction of the risked distance.

    This is the arithmetic D196/D197 already ran on daily bars — 40 bps costs **0.49R at a
    0.5-ATR stop** and **0.12R at 2 ATR** — restated so WP2 can run it on the stop widths
    this strategy actually produces, *before* any backtest. The course's entire claim is a
    hit-rate argument at 5R, made with costs omitted; this is the same argument with the
    costs put back."""
    if entry_price <= 0.0 or stop <= 0.0:
        return None
    return (cost_bps / 10_000.0) / (stop / entry_price)


def required_hit_rate(target_r: float, friction_r: float) -> float | None:
    """Break-even hit rate for a `target_r` reward against a 1R risk, after friction.

    `p * (target_r - friction) = (1 - p) * (1 + friction)`, so
    `p = (1 + friction) / (1 + target_r)`. Returns None if friction has eaten the target
    outright, which is a real outcome on a tight stop and not an error."""
    if target_r - friction_r <= 0.0:
        return None
    return (1.0 + friction_r) / (1.0 + target_r)
