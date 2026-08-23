"""S5 — a swing-structure supply/demand sensor, built from price turns and volume.

Conforms to the `TerrainSensor` protocol in `terrain.py`, so the null harness retained
from D189 tests it unchanged. That harness is the reason this can be evaluated at all:
D189 kept it as "the only piece of machinery in this project that can answer *does this
level mean anything* about any future sensor".

## Why this is not an S1 variant

D194 closed S1 permanently at any resolution. S1 was a **histogram of where volume
traded** — every bar contributed mass whether or not price ever turned there. S5 is
**event-based**: a level exists only where price actually reversed, more than once, and it
**dies when price closes through it**. S1 levels never died. The construction, the
inputs and the failure mode are different, so the stop does not bind.

## The definition, fixed here before any run

A level is a horizontal price band of width `cluster_atr x ATR` containing at least
`MIN_SWINGS` confirmed pivots of the same kind (highs, or lows — never mixed). Its score
multiplies three rank-normalised components:

- **volume** at the bars that formed the pivots,
- **sharpness**, the impulse away from the pivot over `SHARPNESS_BARS`, in ATR units,
- **tests**, total touches: the pivots that formed the band plus later approaches into it
  that did not break it.

Multiplicative and unweighted, deliberately. Three tunable weights would be a search
space, and any level set clearing a null could then have been found by tuning — the
failure D194's multiplicity ledger exists to price. Rank-normalisation runs in
`[1/n, 1]` rather than `[0, 1]` so no component can zero a level out entirely.

**Broken is dead, permanently.** A close beyond the band on the far side invalidates the
level and it never returns. The trader's "support becomes resistance" flip is a DIFFERENT
hypothesis and is deliberately not implemented — smuggling it in would test two ideas
while reporting one.

## The confirmation lag, which is where this design leaks if you are careless

D173 solved this once already and the reasoning is quoted because it is the whole risk:

> A pivot at bar t cannot be recognised until bar t+k, because it needs the k bars after
> it. A naive implementation that labelled pivots on the visible series without that
> offset would be reading k bars into the future — and it would leak INVISIBLY, because
> the equity curve it produced would look entirely plausible.

`_is_swing_bars` and `confirmed_pivots` restate `strategies.breakout._is_swing` and
`last_swings` on a bare bar sequence, because a sensor has no `DataView`. The two are
pinned against each other by test rather than trusted to agree — the same arrangement
`terrain.mean_true_range` has with `strategies.breakout._mean_true_range`, and for the
same reason.

Sharpness needs `SHARPNESS_BARS` bars AFTER the pivot too, so the newest pivot this will
use sits at `index - max(k, SHARPNESS_BARS)`.

## The confound this shares with S1, stated before any result

`tests` counts how often price came back to a band. A level scoring highly on tests is by
construction a price the market keeps returning to — which is D189's H2 confound, and it
bites HARDER here than it did for S1 because repetition is an explicit scoring term rather
than an emergent property. The harness's null matches level count and span but cannot
match where-price-lingered without destroying what is being tested. So a pass is not
evidence of supply and demand until that is ruled out, and ruling it out is the first task
of a passing branch.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ..data.bars import TimestampedBar
from .terrain import ATR_WINDOW, VOLUME_UNITS, PriceDensity, mean_true_range

SWING_K = (2, 3)
"""Pivot half-widths. D173's pre-registered set, reused unchanged rather than re-chosen —
re-picking a parameter set that already exists is an unregistered search wearing a
familiar name."""

CLUSTER_ATR = (0.25, 0.5)
"""Band half-width in ATR units. Same set and same reason as S1's `BUCKET_ATR`: a fixed
dollar band means something different on a $300 coin and a $90,000 one, which
`TERRAIN_MODEL.md` prohibits."""

MIN_SWINGS = 2
"""Pivots needed to form a level. Two is the double top / double bottom — the smallest
structure the concept actually names. Not swept: the touch count enters the score, so a
three-swing level already outranks a two-swing one without being a separate category."""

SHARPNESS_BARS = 5
"""Bars over which the impulse away from a pivot is measured. Fixed at the horizon the
null harness already uses (`terrain_nulls.HORIZON`, itself `breakout_study.E2_N`), rather
than chosen here — a window picked to make a verdict come out is the same failure as a
threshold picked that way."""

MIN_LEVELS = 3
"""Below this no map is emitted at all, and the reason is the NULL rather than the sensor.

`terrain_nulls.pseudo_levels` draws its random levels uniformly over
`[min(real), max(real)]`. With two real levels that span is exactly the gap between them,
so every pseudo-level lands between the two real ones and the comparison is close to
vacuous. Three is the smallest set for which the null has somewhere to put a level that
the real map did not choose."""


def _is_swing_bars(bars: Sequence[TimestampedBar], index: int, k: int, sign: int) -> bool:
    """Is `index` a k-bar fractal pivot? Restatement of `breakout._is_swing` on bars.

    Strict and unique: equal extremes produce no pivot rather than an arbitrary tiebreak,
    which is D173's stated tie convention. Pinned against the original by test."""
    if index - k < 0 or index + k >= len(bars):
        return False
    window = range(index - k, index + k + 1)
    if sign > 0:
        values = [bars[j].bar.high for j in window]
        return bars[index].bar.high == max(values) and values.count(max(values)) == 1
    values = [bars[j].bar.low for j in window]
    return bars[index].bar.low == min(values) and values.count(min(values)) == 1


def confirmed_pivots(
    bars: Sequence[TimestampedBar], index: int, k: int, sign: int, lookback: int,
    trailing_bars: int = 0,
) -> list[int]:
    """Indices of confirmed pivots in `(index - lookback, index]`, oldest first.

    The newest index considered is `index - max(k, trailing_bars)`: `k` because a pivot is
    not knowable until `k` bars after it, and `trailing_bars` because a caller measuring
    something over the bars following the pivot needs those bars to exist as well. Both
    offsets are the confirmation lag D173 identified; getting either wrong reads the
    future and does so invisibly."""
    newest = index - max(k, trailing_bars)
    oldest = max(k, index - lookback + 1)
    return [t for t in range(oldest, newest + 1) if _is_swing_bars(bars, t, k, sign)]


def _impulse(bars: Sequence[TimestampedBar], index: int, sign: int, span: int, atr: float) -> float:
    """How sharply price left the pivot, in ATR units. Zero if the bars are unavailable."""
    end = index + span
    if end >= len(bars) or atr <= 0.0:
        return 0.0
    if sign > 0:  # a swing high — the move away is downward
        trough = min(bars[j].bar.low for j in range(index + 1, end + 1))
        return max(0.0, (bars[index].bar.high - trough) / atr)
    peak = max(bars[j].bar.high for j in range(index + 1, end + 1))
    return max(0.0, (peak - bars[index].bar.low) / atr)


@dataclass(frozen=True)
class SwingLevel:
    """One clustered supply/demand band, as of the bar it was computed at."""

    price: float
    """Mean of the constituent pivot extremes."""
    sign: int
    """+1 from swing highs (supply), -1 from swing lows (demand)."""
    half_width: float
    n_swings: int
    volume: float
    sharpness: float
    tests: int
    """TOTAL touches: the pivots that formed the level PLUS later approaches that did not
    break it.

    Revised once, before any null test, after measuring the first reading. Counting only
    post-formation approaches left **65.5% of BTC levels and 69.3% of ETH levels at zero**,
    so the component was tied at the bottom rank for two thirds of the map and the score
    was effectively volume x sharpness. A level formed by five swings has been tested five
    times; treating those as not-tests was a misreading of the specification, not a
    property of the data. Recorded rather than silently corrected, in D144's manner."""
    formed_index: int
    """The index of the LAST constituent pivot — the level does not exist before this."""

    def contains(self, price: float) -> bool:
        return abs(price - self.price) <= self.half_width


def _cluster(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    pivots: Sequence[int],
    sign: int,
    half_width: float,
    atr: float,
) -> list[SwingLevel]:
    """Group pivots whose extremes fall within `half_width` of the running cluster mean.

    Single-linkage on a price-sorted list. Deterministic and order-free: sorting first
    means the result does not depend on the order pivots were discovered in."""
    if not pivots:
        return []
    extreme = (
        (lambda t: bars[t].bar.high) if sign > 0 else (lambda t: bars[t].bar.low)
    )
    ordered = sorted(pivots, key=extreme)

    groups: list[list[int]] = []
    current: list[int] = [ordered[0]]
    for t in ordered[1:]:
        centre = sum(extreme(j) for j in current) / len(current)
        if abs(extreme(t) - centre) <= half_width:
            current.append(t)
        else:
            groups.append(current)
            current = [t]
    groups.append(current)

    levels: list[SwingLevel] = []
    for group in groups:
        if len(group) < MIN_SWINGS:
            continue
        levels.append(
            SwingLevel(
                price=sum(extreme(j) for j in group) / len(group),
                sign=sign,
                half_width=half_width,
                n_swings=len(group),
                volume=sum(
                    volumes[j] for j in group if not math.isnan(volumes[j]) and volumes[j] > 0.0
                ),
                sharpness=sum(
                    _impulse(bars, j, sign, SHARPNESS_BARS, atr) for j in group
                ) / len(group),
                tests=len(group),  # the forming pivots are themselves tests
                formed_index=max(group),
            )
        )
    return levels


def _survives(
    bars: Sequence[TimestampedBar], level: SwingLevel, index: int
) -> tuple[bool, int]:
    """Walk formation → `index`. Returns (still alive, tests survived).

    **Broken is dead.** A close beyond the band on the far side invalidates the level
    permanently. Using the band edge rather than the level itself costs no new parameter
    and stops noise inside the band from killing a level on a tick.

    A test is an approach that ENTERS the band having been outside on the previous bar —
    the same "first bar of an approach" convention the null harness uses for touches, so a
    price sitting inside the band for a week counts once rather than seven times. The
    count STARTS at the number of forming pivots, which are touches too."""
    far = level.price + level.half_width if level.sign > 0 else level.price - level.half_width
    tests = level.tests  # starts at the number of forming pivots
    inside = False
    for t in range(level.formed_index + 1, index + 1):
        close = bars[t].bar.close
        if (close > far) if level.sign > 0 else (close < far):
            return False, tests
        now_inside = level.contains(close)
        if now_inside and not inside:
            tests += 1
        inside = now_inside
    return True, tests


def _rank_scores(values: Sequence[float]) -> list[float]:
    """Rank-normalise into `(0, 1]` — `(rank + 1) / n`, ties sharing the lowest rank.

    Never zero, so one weak component cannot annihilate a level that is strong on the
    other two. Ranks rather than levels because the three components have incomparable
    units and any rescaling that made them comparable would be a free parameter."""
    n = len(values)
    if n == 0:
        return []
    order = sorted(range(n), key=lambda i: values[i])
    out = [0.0] * n
    i = 0
    while i < n:
        j = i
        while j + 1 < n and values[order[j + 1]] == values[order[i]]:
            j += 1
        for m in range(i, j + 1):
            out[order[m]] = (i + 1) / n
        i = j + 1
    return out


def score_levels(levels: Sequence[SwingLevel]) -> list[float]:
    """The multiplicative, unweighted score: volume x sharpness x tests, all rank-normalised."""
    if not levels:
        return []
    v = _rank_scores([lv.volume for lv in levels])
    s = _rank_scores([lv.sharpness for lv in levels])
    t = _rank_scores([float(lv.tests) for lv in levels])
    return [a * b * c for a, b, c in zip(v, s, t)]


@dataclass(frozen=True)
class SwingSupplyDemandSensor:
    """S5 — supply and demand bands from repeated price turns, weighted by volume,
    impulse and retests, invalidated on a close through.

    Emits a `PriceDensity` whose mass sits only in the buckets holding live levels, so the
    D189 null harness consumes it unchanged. `PriceDensity.spans` is left empty on purpose:
    it censuses how many buckets a BAR's range covered, which is an S1 construction and
    has no meaning for a sensor whose levels are discrete."""

    k: int
    cluster_atr: float
    volume_units: str
    lookback_bars: int
    atr_window: int = ATR_WINDOW
    name: str = "S5_swing_supply_demand"

    def __post_init__(self) -> None:
        if self.k not in SWING_K:
            raise ValueError(
                f"k must be one of {SWING_K}, got {self.k}. D173 fixed this set; a third "
                "value is an unregistered search."
            )
        if self.cluster_atr not in CLUSTER_ATR:
            raise ValueError(
                f"cluster_atr must be one of {CLUSTER_ATR}, got {self.cluster_atr}. "
                "The spec fixes this set; a third value is an unregistered search."
            )
        if self.volume_units not in VOLUME_UNITS:
            raise ValueError(
                f"volume_units must be one of {VOLUME_UNITS}, got {self.volume_units!r}. "
                "There is no safe default: a notional column read as shares scaled every "
                "impact charge by the square root of the price once already (D187)."
            )
        if self.lookback_bars < 4 * self.k + 2 * SHARPNESS_BARS:
            raise ValueError(
                f"lookback_bars={self.lookback_bars} cannot hold two confirmed pivots plus "
                f"their impulse windows at k={self.k}"
            )

    def warm_up_bars(self) -> int:
        return self.lookback_bars + self.atr_window + 1

    def live_levels(
        self, bars: Sequence[TimestampedBar], index: int, volumes: Sequence[float]
    ) -> list[SwingLevel]:
        """Every level alive at `index`, both signs, with retest counts filled in."""
        atr = mean_true_range(bars, index - self.atr_window + 1, index + 1)
        if not math.isfinite(atr) or atr <= 0.0:
            return []
        half_width = atr * self.cluster_atr

        alive: list[SwingLevel] = []
        for sign in (1, -1):
            pivots = confirmed_pivots(
                bars, index, self.k, sign, self.lookback_bars, SHARPNESS_BARS
            )
            for level in _cluster(bars, volumes, pivots, sign, half_width, atr):
                survives, tests = _survives(bars, level, index)
                if not survives:
                    continue  # broken is dead, permanently
                alive.append(
                    SwingLevel(
                        price=level.price, sign=level.sign, half_width=level.half_width,
                        n_swings=level.n_swings, volume=level.volume,
                        sharpness=level.sharpness, tests=tests,
                        formed_index=level.formed_index,
                    )
                )
        return alive

    def levels_at(
        self,
        bars: Sequence[TimestampedBar],
        index: int,
        volumes: Sequence[float] | None = None,
    ) -> tuple[float, ...]:
        """The level prices themselves, for the null harness.

        S5's output IS a discrete level set, already selected by the MIN_SWINGS rule and
        the invalidation walk. Handing the harness a density and letting it re-extract
        high-volume nodes would discard most of them — measured at three in four — and add
        a quantile threshold this sensor does not have. So the levels are published
        directly and `density` remains available for anything that wants the map."""
        if volumes is None:
            raise ValueError(f"{self.name} weights levels by volume and was given none.")
        if index < self.warm_up_bars() - 1 or index >= len(bars):
            return ()
        levels = self.live_levels(bars, index, volumes)
        if len(levels) < MIN_LEVELS:
            return ()
        return tuple(sorted(lv.price for lv in levels))

    def density(
        self,
        bars: Sequence[TimestampedBar],
        index: int,
        volumes: Sequence[float] | None = None,
    ) -> PriceDensity | None:
        """Mass at each live level, over `bars[index - lookback + 1 : index + 1]`.

        Everything after `index` is unreachable: pivots stop at `index - max(k,
        SHARPNESS_BARS)`, the impulse window ends at or before `index`, and invalidation
        walks only to `index`. Asserted by property test, not by this sentence."""
        if volumes is None:
            raise ValueError(
                f"{self.name} weights levels by volume and was given none. A price-only "
                "version is a different sensor, not a degraded version of this one."
            )
        if len(volumes) != len(bars):
            raise ValueError(
                f"{len(bars)} bars against {len(volumes)} volumes — needs them aligned "
                "bar-for-bar (D187's second bug was exactly this)."
            )
        if index < self.warm_up_bars() - 1 or index >= len(bars):
            return None

        levels = self.live_levels(bars, index, volumes)
        if len(levels) < MIN_LEVELS:
            return None
        scores = score_levels(levels)
        total = sum(scores)
        if total <= 0.0:
            return None

        start = index - self.lookback_bars + 1
        window = bars[start : index + 1]
        low = min(b.bar.low for b in window)
        high = max(b.bar.high for b in window)
        width = levels[0].half_width
        if not (high > low) or width <= 0.0:
            return None

        n_buckets = max(1, int(math.ceil((high - low) / width)))
        edges = tuple(low + i * width for i in range(n_buckets + 1))
        raw = [0.0] * n_buckets
        for level, s in zip(levels, scores):
            if not (low <= level.price <= high):
                continue
            raw[min(n_buckets - 1, max(0, int((level.price - low) / width)))] += s

        mass_total = sum(raw)
        if mass_total <= 0.0:
            return None
        return PriceDensity(
            edges=edges,
            mass=tuple(r / mass_total for r in raw),
            bucket_width=width,
            lookback=self.lookback_bars,
            bucket_atr=self.cluster_atr,
            n_bars=len(window),
        )
