"""The five components of a discretionary price-action strategy, made mechanical (D204).

WP1 of `New Docs/STRUCTURE_MODEL.md`. This module is **detectors only** — no strategy, no
costs, no verdict. Each component is a separate function so that WP3 can test it alone and
WP4 can measure what it adds on top of the others. A module that fused them would make the
question the programme exists to answer unanswerable.

The five, and what each claims:

- **C1 market structure** (`market_structure`) — trend as a sequence of confirmed pivots,
  with a *break of structure* confirming it and a *change of character* flipping it. The
  trigger.
- **C2 the flipped level** (`StructureState.choch_level`) — the broken level becomes
  resistance where it was support.
- **C3 the Fibonacci retracement** (`retracement`) — price pulls back to 61.8% of the
  impulse leg before continuing.
- **C4 the fair value gap** (`fair_value_gaps`) — a three-bar imbalance price returns to.
- **C5 RSI** (`rsi`) — the control, not a fifth idea.

## Look-ahead is guarded HERE, not inherited

`DataView` (D32/D56) makes look-ahead structurally impossible for a strategy: the view is
constructed already sliced, so future bars are not merely forbidden but absent. **A
detector is analytics, not a strategy**, and D181 is the record of what that distinction
cost — the ensemble weighted itself with whole-sample volatility for as long as it existed,
inside a project with a look-ahead guard, because the guard does not reach analytics built
on strategy output.

So every function here is a single **causal forward pass**: the value at index `i` is
computed from bars at or before `i` and never revisited. `tests/unit/test_structure.py`
asserts the property directly — perturbing any bar after `i` must leave the output at `i`
bit-identical.

## The confirmation lag, which is where this leaks if you are careless

D173 solved this once and the reasoning is quoted because it is the whole risk:

> A pivot at bar t cannot be recognised until bar t+k, because it needs the k bars after
> it. A naive implementation that labelled pivots on the visible series without that
> offset would be reading k bars into the future — and it would leak INVISIBLY, because
> the equity curve it produced would look entirely plausible.

A pivot at `t` therefore enters the state machine at `t + k` and not before. `_pivot_at`
restates `terrain_swing._is_swing_bars` on the same footing, and the two are pinned against
each other by test rather than trusted to agree — the arrangement `terrain_swing` already
has with `strategies.breakout._is_swing`, and `terrain.mean_true_range` with
`breakout._mean_true_range`.

The one detector with NO lag is `fair_value_gaps`: a gap at `t` is defined by bars `t-2`,
`t-1` and `t`, all of which are closed. It is knowable at `t` and is stamped that way.
Giving it a lag it does not have would be as wrong as omitting one it does.

## What is deliberately absent

**No thresholds are applied here.** `retracement` returns a continuous depth, not "is it
at 61.8". `fair_value_gaps` returns every gap, not the ones that matter. Whether 0.618 is
special is the question WP3 asks against a placebo ladder, and a detector that pre-filtered
to 0.618 would have answered it by assumption.

**No parameter is chosen here.** `k` comes from D173's `SWING_K`, the touch band from
`terrain_nulls.TOUCH_ATR`, the ATR window from D194's calendar match. A value outside the
pre-registered sets is an unregistered search and `STRUCTURE_MODEL.md` counts every one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from ..data.bars import TimestampedBar
from .terrain_swing import SWING_K, _is_swing_bars

RSI_WINDOW = 14
"""Wilder's original period. Not swept — C5 is in this programme as a control, and a swept
control is not a control."""

RSI_OVERSOLD, RSI_OVERBOUGHT = 30.0, 70.0
"""The textbook thresholds, fixed. If the plain oscillator conditions outcomes as well as
the three structural components, the structural components add nothing (H6)."""

CANONICAL_RATIOS = (0.382, 0.500, 0.618, 0.786)
"""The retracement levels the course names. 0.618 is the one it calls the golden ratio."""

PLACEBO_RATIOS = (0.447, 0.553, 0.691, 0.724)
"""Non-canonical ratios at matched depths, fixed in `STRUCTURE_MODEL.md` before any run.

They bracket the canonical set without coinciding with any member, and none is derivable
from the Fibonacci sequence, from phi, or from a round fraction. **This is the whole test
of C3.** Any level partway into a retracement sits where price has recently been, so
measuring a reaction at 0.618 alone establishes nothing; measuring it against 0.447 at a
comparable depth establishes whether the NUMBER matters or only the DEPTH does."""


class Trend(Enum):
    """Structural state. `NONE` until the first break of structure — never guessed."""

    NONE = 0
    UP = 1
    DOWN = -1


class Event(Enum):
    """What happened at a bar, if anything."""

    NONE = 0
    BOS_UP = 1
    BOS_DOWN = 2
    CHOCH_UP = 3
    CHOCH_DOWN = 4


@dataclass(frozen=True)
class Pivot:
    """A fractal turn, stamped with the bar it becomes knowable on."""

    index: int
    confirmed_at: int
    """`index + k`. The state machine may not use this pivot before this bar."""
    sign: int
    """+1 for a swing high, -1 for a swing low."""
    price: float
    """The extreme itself — high for a swing high, low for a swing low."""


@dataclass(frozen=True)
class Leg:
    """The impulse leg following a change of character, in the CHoCH's direction.

    `start` is the extreme the move came from — the last confirmed pivot of the OPPOSITE
    sign to the leg's direction, known at the CHoCH. `end` is the first confirmed pivot of
    the leg's own sign after it. Until that pivot confirms, the leg does not exist and
    `StructureState.leg` is None; nothing may be measured against a leg whose end is still
    in the future, which is exactly the mistake this dataclass exists to make impossible."""

    start_index: int
    start_price: float
    end_index: int
    end_price: float

    @property
    def span(self) -> float:
        """Signed: negative for a down leg, positive for an up leg."""
        return self.end_price - self.start_price


@dataclass(frozen=True)
class StructureState:
    """C1's output at one bar. Every field derives from bars at or before that bar."""

    trend: Trend
    event: Event
    """What fired AT this bar. `NONE` on the overwhelming majority of bars."""

    last_high: float | None
    last_high_index: int | None
    last_low: float | None
    last_low_index: int | None
    """The most recently CONFIRMED pivot of each sign. `None` before the first confirms."""

    higher_low: float | None
    lower_high: float | None
    """The level a change of character must break, and the reason C1 is not simply "close
    through the last swing".

    `STRUCTURE_MODEL.md` defines `CHoCH_down` as a close below the last confirmed **higher
    low** — a swing low that was itself higher than its predecessor AND was followed by a
    `BOS_up`. In an uptrend that is usually the most recent confirmed low, but not always:
    a leg can print a pivot low beneath its predecessor without ever closing below it, and
    treating that as a higher low would fire a change of character off a structure that
    never rose. `None` means no such low exists yet and a CHoCH cannot fire."""

    choch_index: int | None
    choch_level: float | None
    """**C2.** The price of the level whose break produced the current CHoCH — the flipped
    level the course trades. `None` until the first CHoCH."""
    choch_direction: int
    """+1 if the live CHoCH turned the structure up, -1 if down, 0 if there is none."""
    level_alive: bool
    """**Broken is dead, permanently.** A close beyond `choch_level` in the pre-break
    direction invalidates it and it does not return.

    Same convention as `terrain_swing.SwingLevel`, stated explicitly so D196's result and
    this one are comparable. The distinction from S5 is that S5 built bands from repeated
    pivots and killed them on a break, while this is one specific swing traded BECAUSE it
    broke — the hypothesis `terrain_swing`'s docstring named and set aside."""

    leg: Leg | None
    """The impulse leg after the CHoCH, once its end pivot has confirmed.

    `None` between the CHoCH and that confirmation, which is a real waiting period and not
    a gap in the data: the leg's end is a pivot, and a pivot is not knowable until `k` bars
    after it. An entry rule that used a leg before this is set would be measuring a
    retracement of a leg whose extreme is still in the future."""

    bars_since_choch: int | None
    """Stored rather than derived — a `StructureState` is read in isolation and does not
    know its own index."""


def _pivot_at(bars: Sequence[TimestampedBar], index: int, k: int, sign: int) -> bool:
    """Is `index` a k-bar fractal pivot? Delegates to the existing implementation.

    This is a thin alias rather than a fourth restatement of the same five lines. D173's
    tie convention (strict and unique — equal extremes produce no pivot) therefore holds
    here by construction and not by a comment claiming it does."""
    return _is_swing_bars(bars, index, k, sign)


TIE_TOLERANT_K = tuple(range(1, 11))
"""Windows `pivots_tie_tolerant` will accept. WIDER THAN D173's `SWING_K`, deliberately and
visibly: this function is D399's and no published record was computed with it, so the window is a
parameter here. Every value outside `SWING_K` is a search step under R13. The upper bound is not
cosmetic — `k` is also the confirmation lag, and past about 10 bars a daily pivot confirms only
after the next one has already formed."""


def _pivot_at_tie_tolerant(
    bars: Sequence[TimestampedBar], index: int, k: int, sign: int
) -> bool:
    """Is `index` a k-bar fractal pivot, allowing EQUAL extremes to count?

    Deliberately not `_is_swing_bars` with a flag. That function's contract is strict-and-unique,
    it is pinned by test against `strategies.breakout._is_swing`, and D173's records were computed
    under it — so it is left exactly as it is and this is a second, separately named test.

    The only difference is the uniqueness clause. `_is_swing_bars` requires the extreme to occur
    ONCE in the window, so two bars sharing the same high produce no pivot at all; here the
    extreme is enough. The window, the sign convention, the edge handling and the price read are
    identical.

    WHY IT EXISTS, measured rather than supposed. D399's pivot ground truth — 53 swings the
    principal marked stepping forward one bar at a time, with the detector's own output hidden
    from him — disagreed with the strict rule on nine. Five of those nine were killed by the
    uniqueness clause alone, and across that 260-bar window the clause discards 11% of qualifying
    highs and 20% of qualifying lows. Relaxing it takes agreement with him from 81% to 91%; the
    remaining misses are turns tighter than the window, which is a different parameter.
    """
    if index - k < 0 or index + k >= len(bars):
        return False
    window = range(index - k, index + k + 1)
    if sign > 0:
        values = [bars[j].bar.high for j in window]
        return bars[index].bar.high == max(values)
    values = [bars[j].bar.low for j in window]
    return bars[index].bar.low == min(values)


def pivots_tie_tolerant(bars: Sequence[TimestampedBar], k: int) -> list[Pivot]:
    """`pivots`, with the strict-uniqueness tie rule relaxed. Everything else is identical.

    A bar CAN be both a swing high and a swing low here, which `pivots` documents as impossible
    under the strict rule — flat bars in a flat window satisfy both. That is a real state and it
    is returned rather than suppressed; a caller that cannot handle it should say so.

    THE WINDOW IS OPEN HERE, AND THAT IS A DISCLOSED WIDENING. `pivots` restricts `k` to D173's
    `SWING_K` = (2, 3) because its records were computed under that set and re-picking it after
    the fact is an unregistered search. This function is D399's own and was never part of those
    records, so its window is a declared parameter — but every `k` outside `SWING_K` is a search
    step and is counted as one (R13). `pivots` itself is untouched and still refuses.

    `TIE_TOLERANT_K` bounds it: below 1 there is no window, and above ~10 the confirmation lag
    (`k` bars, D173) exceeds the median gap between pivots on daily bars, so the detector would
    confirm a turn only after the next one had already happened."""
    if k not in TIE_TOLERANT_K:
        raise ValueError(
            f"k must be in {TIE_TOLERANT_K}, got {k}. Values outside D173's SWING_K={SWING_K} are "
            "a disclosed widening of the search, not a free parameter."
        )
    out: list[Pivot] = []
    for i in range(k, len(bars) - k):
        for sign in (1, -1):
            if not _pivot_at_tie_tolerant(bars, i, k, sign):
                continue
            price = bars[i].bar.high if sign > 0 else bars[i].bar.low
            out.append(Pivot(index=i, confirmed_at=i + k, sign=sign, price=price))
    out.sort(key=lambda p: (p.confirmed_at, p.index, -p.sign))
    return out


def pivots(bars: Sequence[TimestampedBar], k: int) -> list[Pivot]:
    """Every fractal pivot in the series, both signs, ordered by the bar it CONFIRMS on.

    Computed once over the whole series and consumed causally: a pivot's `confirmed_at`
    is `index + k`, and `market_structure` will not look at it before that bar. Detecting
    pivots over the full series is not look-ahead — *using* one before it confirms is, and
    that is the invariant the tests assert.

    A bar can be both a swing high and a swing low only if `k` bars either side are all
    equal, which D173's strict-and-unique rule already excludes; both signs are still
    checked so that the exclusion is a property of the detector rather than an assumption
    about the data."""
    if k not in SWING_K:
        raise ValueError(
            f"k must be one of {SWING_K}, got {k}. D173 fixed this set and "
            "STRUCTURE_MODEL.md reuses it rather than re-choosing it; a third value is an "
            "unregistered search."
        )
    out: list[Pivot] = []
    for i in range(k, len(bars) - k):
        for sign in (1, -1):
            if not _pivot_at(bars, i, k, sign):
                continue
            price = bars[i].bar.high if sign > 0 else bars[i].bar.low
            out.append(Pivot(index=i, confirmed_at=i + k, sign=sign, price=price))
    out.sort(key=lambda p: (p.confirmed_at, p.index, -p.sign))
    return out


def market_structure(bars: Sequence[TimestampedBar], k: int) -> list[StructureState]:
    """**C1.** The break-of-structure / change-of-character state machine, one state per bar.

    A single causal forward pass. At bar `t` the machine first absorbs every pivot whose
    `confirmed_at` equals `t` — that is, pivots at `t - k` — and only then evaluates
    `close_t` against the levels those pivots define. A pivot at `t - k` therefore
    influences the state at `t` and never at `t - 1`, which is D173's lag applied where it
    belongs rather than asserted in a docstring.

    The rules, from `STRUCTURE_MODEL.md`:

    - **BOS_up**: `close_t` above the most recent confirmed swing high, while trend is UP
      or NONE. Sets trend UP. Mirror for BOS_down.
    - **CHoCH_down**: trend is UP and `close_t` closes below the last confirmed HIGHER LOW.
      Sets trend DOWN and records the broken level as C2. Mirror for CHoCH_up.
    - A break of the same level fires once. It re-arms when a new pivot of that sign
      confirms — otherwise a price that sits above a swing high for a week would report a
      break of structure on every bar of it, which is the same defect
      `terrain_nulls`' touch definition exists to avoid.

    A CHoCH takes precedence over a BOS at the same bar: a bar cannot both confirm the
    trend and flip it, and the flip is the stronger statement. The precedence is stated
    here because with `k=2` on 15m bars it is not a rare tie."""
    n = len(bars)
    by_confirm: dict[int, list[Pivot]] = {}
    for p in pivots(bars, k):
        by_confirm.setdefault(p.confirmed_at, []).append(p)

    trend = Trend.NONE
    last_high = last_low = None
    last_high_index = last_low_index = None
    prev_high = prev_low = None
    higher_low = lower_high = None
    high_armed = low_armed = False
    choch_index = choch_level = None
    choch_direction = 0
    level_alive = False
    leg: Leg | None = None
    leg_start: tuple[int, float] | None = None
    """Captured AT the change of character, not when the leg's end confirms.

    By the time the end pivot arrives, `last_high` / `last_low` may already have moved on
    to newer pivots. Reading them then would measure the leg from the wrong extreme and
    every retracement built on it would be quietly wrong — the failure mode is a plausible
    number, not an exception."""

    out: list[StructureState] = []
    for t in range(n):
        for p in by_confirm.get(t, ()):
            if p.sign > 0:
                prev_high, last_high, last_high_index = last_high, p.price, p.index
                high_armed = True
            else:
                prev_low, last_low, last_low_index = last_low, p.price, p.index
                low_armed = True
        close = bars[t].bar.close
        event = Event.NONE

        # --- change of character first: a bar cannot both confirm and flip a trend ---
        if trend is Trend.UP and higher_low is not None and close < higher_low:
            event = Event.CHOCH_DOWN
            trend = Trend.DOWN
            choch_index, choch_level, choch_direction = t, higher_low, -1
            level_alive, leg = True, None
            leg_start = (
                None
                if last_high_index is None or last_high is None
                else (last_high_index, last_high)
            )
            higher_low, lower_high = None, None
            low_armed = False
        elif trend is Trend.DOWN and lower_high is not None and close > lower_high:
            event = Event.CHOCH_UP
            trend = Trend.UP
            choch_index, choch_level, choch_direction = t, lower_high, 1
            level_alive, leg = True, None
            leg_start = (
                None
                if last_low_index is None or last_low is None
                else (last_low_index, last_low)
            )
            higher_low, lower_high = None, None
            high_armed = False
        # --- break of structure ---
        elif high_armed and last_high is not None and close > last_high:
            event = Event.BOS_UP
            trend, high_armed = Trend.UP, False
            if last_low is not None and prev_low is not None and last_low > prev_low:
                higher_low = last_low
        elif low_armed and last_low is not None and close < last_low:
            event = Event.BOS_DOWN
            trend, low_armed = Trend.DOWN, False
            if last_high is not None and prev_high is not None and last_high < prev_high:
                lower_high = last_high

        # --- C2: broken is dead, permanently ---
        if level_alive and choch_level is not None:
            if (choch_direction > 0 and close < choch_level) or (
                choch_direction < 0 and close > choch_level
            ):
                level_alive = False

        # --- the impulse leg, once its end pivot has confirmed ---
        # A down leg ends at a swing LOW and an up leg at a swing HIGH, so the end pivot's
        # sign IS the CHoCH's direction. Only bar t's own confirmations are consulted:
        # this runs once per bar, so scanning forward would be the exact shape of the
        # look-ahead bug the whole module is arranged to prevent.
        if leg is None and leg_start is not None and choch_index is not None:
            for p in by_confirm.get(t, ()):
                if p.sign != choch_direction or p.index <= choch_index:
                    continue
                start_index, start_price = leg_start
                # A leg whose start is on the wrong side of its end is degenerate. It is
                # refused rather than clamped: a retracement measured against a leg of the
                # wrong sign is a number with no meaning, and clamping would produce one.
                if (choch_direction < 0 and start_price <= p.price) or (
                    choch_direction > 0 and start_price >= p.price
                ):
                    continue
                leg = Leg(start_index, start_price, p.index, p.price)
                break

        out.append(
            StructureState(
                trend=trend,
                event=event,
                last_high=last_high,
                last_high_index=last_high_index,
                last_low=last_low,
                last_low_index=last_low_index,
                higher_low=higher_low,
                lower_high=lower_high,
                choch_index=choch_index,
                choch_level=choch_level,
                choch_direction=choch_direction,
                level_alive=level_alive,
                leg=leg,
                bars_since_choch=None if choch_index is None else t - choch_index,
            )
        )
    return out


def retracement(leg: Leg, price: float) -> float | None:
    """**C3.** How far `price` has retraced `leg`, as a fraction. `None` if degenerate.

    0.0 at the leg's extreme (`end_price`), 1.0 back at its origin (`start_price`), in
    both directions. Values outside [0, 1] are returned as computed and NOT clipped: a
    reading above 1.0 means price has retraced past where the leg began, which is
    information about the structure breaking down, and clipping it would silently relabel
    a failed setup as a deep one.

    Continuous by design. Whether 0.618 is special is WP3's question, and a function that
    returned a boolean would have answered it by assumption."""
    span = leg.span
    if span == 0.0 or not math.isfinite(span):
        return None
    value = (leg.end_price - price) / span
    return value if math.isfinite(value) else None


def ratio_price(leg: Leg, ratio: float) -> float:
    """The price at `ratio` of the way back along `leg`. Inverse of `retracement`."""
    return leg.end_price - ratio * leg.span


@dataclass(frozen=True)
class Gap:
    """**C4.** A three-bar imbalance, and the bar it becomes knowable on.

    `formed_at` is the third bar's index and carries NO confirmation lag: all three bars
    are closed at that point. Giving it a lag it does not have would be as wrong as
    omitting one it does."""

    formed_at: int
    lo: float
    hi: float
    direction: int
    """+1 bullish (price pulls back DOWN into it), -1 bearish (price rallies UP into it)."""
    filled_at: int | None = None
    """The bar price traded through the far edge, after which the gap is dead. `None` if it
    survived to the end of the series — which is a statement about the sample ending, not
    about the gap, and consumers must treat it that way."""

    @property
    def midpoint(self) -> float:
        """The 50% level the course trades into."""
        return 0.5 * (self.lo + self.hi)

    @property
    def width(self) -> float:
        return self.hi - self.lo

    def alive_at(self, index: int) -> bool:
        return index >= self.formed_at and (
            self.filled_at is None or index < self.filled_at
        )


def fair_value_gaps(bars: Sequence[TimestampedBar]) -> list[Gap]:
    """**C4.** Every three-bar imbalance in the series, with the bar each is filled on.

    - **Bullish** at `t`: `low_t > high_{t-2}`. The gap is `(high_{t-2}, low_t)` and dies
      when a later bar's low trades below `high_{t-2}`.
    - **Bearish** at `t`: `high_t < low_{t-2}`. The gap is `(high_t, low_{t-2})` and dies
      when a later bar's high trades above `low_{t-2}`.

    Zero judgement: this is the one component the course states precisely enough to
    implement without interpretation, and it is implemented exactly as stated, including
    the gaps that are obviously noise. Filtering to "the ones that matter" is what the
    course does by eye and is precisely the discretion this programme exists to remove.

    Fill uses the bar's RANGE, not its close, because a gap price traded through is filled
    whether or not the bar closed beyond it.

    Cost is one pass to find and one to fill, both linear; the fill pass carries only the
    open gaps, of which there are few at any moment."""
    found: list[Gap] = []
    for t in range(2, len(bars)):
        first, third = bars[t - 2].bar, bars[t].bar
        if third.low > first.high:
            found.append(Gap(t, first.high, third.low, 1))
        elif third.high < first.low:
            found.append(Gap(t, third.high, first.low, -1))

    out: list[Gap] = []
    open_gaps: list[Gap] = []
    cursor = 0
    for t in range(len(bars)):
        while cursor < len(found) and found[cursor].formed_at == t:
            open_gaps.append(found[cursor])
            cursor += 1
        if not open_gaps:
            continue
        bar = bars[t].bar
        still_open: list[Gap] = []
        for gap in open_gaps:
            if gap.formed_at == t:
                still_open.append(gap)
                continue
            through = bar.low < gap.lo if gap.direction > 0 else bar.high > gap.hi
            if through:
                out.append(
                    Gap(gap.formed_at, gap.lo, gap.hi, gap.direction, filled_at=t)
                )
            else:
                still_open.append(gap)
        open_gaps = still_open
    out.extend(open_gaps)
    out.sort(key=lambda g: (g.formed_at, g.lo))
    return out


def rsi(bars: Sequence[TimestampedBar], window: int = RSI_WINDOW) -> list[float]:
    """**C5.** Wilder's relative strength index on closes. NaN before the first full window.

    Wilder's smoothing (an exponential mean with `alpha = 1/window`), seeded by the simple
    mean of the first `window` gains and losses — the original 1978 formulation, not the
    EMA variant some platforms ship under the same name. Which one is used changes the
    numbers, so it is stated rather than left to the reader.

    A window of all-gains returns 100.0 exactly rather than dividing by zero, which is the
    limit and not a special case.

    This is the study's CONTROL. If it conditions outcomes as well as the three structural
    components then those components add nothing over a line of code from 1978, and H6
    predicts exactly that so the finding has to survive having been predicted against."""
    if window < 2:
        raise ValueError(f"RSI window must be at least 2 bars, got {window}")
    n = len(bars)
    out = [math.nan] * n
    if n <= window:
        return out
    gains = losses = 0.0
    for i in range(1, window + 1):
        change = bars[i].bar.close - bars[i - 1].bar.close
        gains += max(change, 0.0)
        losses += max(-change, 0.0)
    avg_gain, avg_loss = gains / window, losses / window
    out[window] = _rsi_from(avg_gain, avg_loss)
    for i in range(window + 1, n):
        change = bars[i].bar.close - bars[i - 1].bar.close
        avg_gain = (avg_gain * (window - 1) + max(change, 0.0)) / window
        avg_loss = (avg_loss * (window - 1) + max(-change, 0.0)) / window
        out[i] = _rsi_from(avg_gain, avg_loss)
    return out


def _rsi_from(avg_gain: float, avg_loss: float) -> float:
    if avg_loss == 0.0:
        return 100.0 if avg_gain > 0.0 else 50.0
    return 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
