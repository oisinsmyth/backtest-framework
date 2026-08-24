"""Does each component beat its own matched placebo? (D204, WP3)

`terrain_nulls.py` asks whether price *behaves* differently at a sensor's levels. This asks
the same question of four components that are not level maps, so the harness is restated
rather than reused — but the definitions below are `terrain_nulls`' definitions with one
change, and the change is the whole point.

## The statistic: continuation, not reversal

`terrain_nulls` measures **reversal**, because a supply/demand level's claim is that price
bounces off it. The course's claim is different and stronger: after a change of character,
price returns to a level and then **continues in the new direction**. So:

**Touch.** Bar `t` in a setup's pullback window is a touch of level `L` if
`|close_t - L| <= k * ATR_t` and the previous bar was outside that band. Only the FIRST
touch in a window counts, so a price that sits inside the band for an hour is one touch and
not four.

**Band, fixed at the touch.** `band = k * ATR_{t0}` and it is not revisited. Same
convention as `terrain_nulls`' approach side, and for the same reason: a band that breathes
after the touch makes the outcome depend on volatility that arrived later.

**Continuation.** Within `HORIZON` bars of the touch, the close moves `band` beyond the
level **in the change of character's direction** WITHOUT first moving `band` beyond it
**against** that direction. That is the claim: it came back, it held, it went on.

The direction comes from the setup, not from the approach side. That is the one difference
from `terrain_nulls` and it is not cosmetic — a reversal statistic is agnostic about which
way price then goes, and this one is not, because the strategy is not.

## Four components, four matched placebos

Every arm below is **paired**: the real and the placebo differ in the level and in nothing
else. Same setups, same windows, same bands, same horizon, same statistic.

- **C2 the flipped level** — against levels drawn uniformly over the impulse leg's span,
  one per setup. Matched in count and in range, the way `terrain_nulls.pseudo_levels` is.
- **C3 the 61.8% retracement** — against `structure.PLACEBO_RATIOS`, which is a *paired*
  placebo needing no draws at all: the same setups, the same legs, a different number.
  **This is the cheapest decisive test in the programme.** Any level partway into a
  retracement sits where price has recently been, so a reaction at 0.618 alone establishes
  nothing. A reaction at 0.618 that 0.447 does not share establishes something.
- **C4 the fair value gap** — against a band of the SAME WIDTH displaced to a random offset
  inside the same leg. Matching the width matters: a wider band is touched more often and
  continues more often for reasons that have nothing to do with imbalance.
- **C5 RSI** — against a random bar of the same window. The control's control.

**C1 is not in this file's statistic.** A change of character has no level to touch, so it
is tested as a position series against `terrain_field_nulls.rotation_null`, which preserves
exposure, autocorrelation and net tilt exactly and isolates *when* from *how much*.
D201/D202 is the record of why nothing weaker will do.

## The confound, stated before the run

C2, C3 and C4 all sit where price has recently been, so touches cluster near price in the
real arm regardless of meaning. This is D189's H2 confound and it bites here too. Touch
counts are reported per arm so it is visible rather than absorbed — and the C3 ladder is
the one arm where it cancels exactly, because every ratio is a point on the same leg.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np

from .breakout_nulls import MetricSpec, NullDistribution, summarise_null
from .structure import Gap, ratio_price, retracement
from .structure_setups import Setup
from .terrain_nulls import HORIZON

CONTINUATION = MetricSpec(
    "p_continuation",
    "high",
    "P(continuation | touch)",
    "at least the real continuation rate",
)
"""The tail is declared here, before any run, because the direction IS the hypothesis.

The course claims price continues off these levels. So a real level is notable in the
UPPER tail — it continues MORE often than a placebo. A result in the lower tail is not a
weaker version of the same finding; it is the opposite finding, and D202 is the record of
what that looks like when it happens."""

DEFAULT_SIMS = 500
"""What every terrain null used. Reused rather than re-chosen."""


@dataclass(frozen=True)
class Reaction:
    """One arm's touch statistics over a setup population."""

    n_setups: int
    n_touches: int
    n_continued: int

    @property
    def p_continuation(self) -> float:
        """Zero touches returns 0.0 rather than NaN so a degenerate arm sorts last instead
        of propagating into a mean and silently poisoning the comparison. `n_touches` is
        always reported beside it — a rate on four touches is not a rate."""
        return self.n_continued / self.n_touches if self.n_touches else 0.0

    @property
    def touch_rate(self) -> float:
        return self.n_touches / self.n_setups if self.n_setups else 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "n_setups": self.n_setups,
            "n_touches": self.n_touches,
            "n_continued": self.n_continued,
            "p_continuation": self.p_continuation,
            "touch_rate": self.touch_rate,
        }


def touch_and_continue(
    closes: Sequence[float],
    atr: Sequence[float],
    setup: Setup,
    level: float,
    touch_atr: float,
    horizon: int = HORIZON,
) -> tuple[bool, bool]:
    """`(touched, continued)` for one level in one setup's pullback window.

    Scans the window for the first bar inside the band whose predecessor was outside, then
    looks forward `horizon` bars for a resolution. Bars before the window's start are not
    consulted for the "previous bar was outside" test at the window's first bar — the first
    bar counts as a touch if it is inside the band, because the window begins where an entry
    first became possible and there is no earlier state to be outside of.

    Unresolved within the horizon counts as **not continued**. That is the conservative
    reading and it is applied identically to both arms, so it cannot favour either."""
    window = setup.window
    n = len(closes)
    inside_prev = False
    for position, index in enumerate(window):
        band = touch_atr * atr[index]
        if not math.isfinite(band) or band <= 0.0:
            return False, False
        inside = abs(closes[index] - level) <= band
        if inside and (position == 0 or not inside_prev):
            upper, lower = level + band, level - band
            end = min(index + horizon, n - 1)
            for forward in range(index + 1, end + 1):
                close = closes[forward]
                if close >= upper:
                    return True, setup.direction > 0
                if close <= lower:
                    return True, setup.direction < 0
            return True, False
        inside_prev = inside
    return False, False


def continue_from(
    closes: Sequence[float],
    atr: Sequence[float],
    index: int,
    direction: int,
    touch_atr: float,
    horizon: int = HORIZON,
) -> bool:
    """Did price continue in `direction` from bar `index`, by the same resolution rule?

    Used where the component fires at a BAR rather than at a price — C5's RSI threshold.
    Routing that through `touch_and_continue` would search the window for the first bar
    near the trigger's close, which can land on an EARLIER bar at a similar price and quietly
    measure a different moment. The band is `touch_atr * ATR_index` around `close_index`, so
    the resolution rule is identical to the level arms' and the two remain comparable."""
    if index < 0 or index >= len(closes):
        return False
    band = touch_atr * atr[index]
    if not math.isfinite(band) or band <= 0.0:
        return False
    upper, lower = closes[index] + band, closes[index] - band
    for forward in range(index + 1, min(index + horizon, len(closes) - 1) + 1):
        close = closes[forward]
        if close >= upper:
            return direction > 0
        if close <= lower:
            return direction < 0
    return False


def reaction_at(
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Setup],
    levels: Sequence[float],
    touch_atr: float,
    horizon: int = HORIZON,
) -> Reaction:
    """Aggregate `touch_and_continue` over a population, one level per setup."""
    if len(levels) != len(setups):
        raise ValueError(
            f"{len(levels)} levels for {len(setups)} setups — the arms must be paired "
            "setup by setup or the comparison is between two different populations."
        )
    touches = continued = 0
    for setup, level in zip(setups, levels):
        hit, went_on = touch_and_continue(closes, atr, setup, level, touch_atr, horizon)
        touches += hit
        continued += went_on
    return Reaction(len(setups), touches, continued)


def leg_span_levels(setups: Sequence[Setup], rng: np.random.Generator) -> list[float]:
    """One level per setup, drawn uniformly over that setup's own impulse leg.

    Matched to the real arm in count and in range, which is what
    `terrain_nulls.pseudo_levels` matches and for the same reason: more levels or a wider
    range means more touches, and an unmatched null would be answering "does having a level
    beat having none".

    Drawn per SETUP rather than once for the series because the legs are local objects on a
    fixture spanning $3,000 to $100,000 — the scalar-band error `terrain_strategies`'
    docstring records as a 300x mistake, in a different costume."""
    out: list[float] = []
    for setup in setups:
        low = min(setup.leg.start_price, setup.leg.end_price)
        high = max(setup.leg.start_price, setup.leg.end_price)
        out.append(float(rng.uniform(low, high)) if high > low else low)
    return out


def displaced_gap_levels(
    setups: Sequence[Setup],
    gap_midpoints: Sequence[float | None],
    gap_widths: Sequence[float],
    rng: np.random.Generator,
) -> list[float]:
    """A band of the SAME WIDTH as the setup's gap, displaced to a random offset in the leg.

    Width matching is the whole design. A wider band is touched more often and resolves
    more often, so a placebo that did not match it would be measuring band width and
    reporting it as imbalance. The gap's own width is carried through and only its
    LOCATION is randomised, which is the one thing the fair-value-gap claim is about.

    Setups with no gap contribute a level of NaN, which cannot be touched — they are absent
    from both arms identically."""
    out: list[float] = []
    for setup, midpoint, width in zip(setups, gap_midpoints, gap_widths):
        if midpoint is None or not math.isfinite(width) or width <= 0.0:
            out.append(math.nan)
            continue
        low = min(setup.leg.start_price, setup.leg.end_price) + 0.5 * width
        high = max(setup.leg.start_price, setup.leg.end_price) - 0.5 * width
        out.append(float(rng.uniform(low, high)) if high > low else midpoint)
    return out


def first_gap_in_leg(
    setup: Setup, gaps: Sequence[Gap]
) -> tuple[float | None, float]:
    """The midpoint and width of the setup's first live gap, or `(None, nan)`.

    "First" rather than "best": choosing among several gaps is exactly the discretion the
    course exercises by eye ("if it aligns with my other general analysis") and exactly what
    this programme exists to remove. The earliest one is the only choice that needs no
    judgement."""
    for gap in gaps:
        if gap.direction != setup.direction:
            continue
        if not (setup.leg.start_index <= gap.formed_at <= setup.leg.end_index):
            continue
        return gap.midpoint, gap.width
    return None, math.nan


def ratio_levels(setups: Sequence[Setup], ratio: float) -> list[float]:
    """The price at `ratio` of each setup's own leg. The C3 ladder's arm constructor."""
    return [ratio_price(setup.leg, ratio) for setup in setups]


def random_window_levels(
    closes: Sequence[float], setups: Sequence[Setup], rng: np.random.Generator
) -> list[float]:
    """A close drawn from the setup's own window — C5's placebo.

    Deliberately a close that actually occurred rather than a price drawn from a range: the
    RSI condition fires at a bar, so its placebo has to be a bar too. Drawing from a range
    would compare "a moment RSI chose" against "a price", which are not the same kind of
    thing."""
    return [
        closes[setup.window[int(rng.integers(0, len(setup.window)))]] for setup in setups
    ]


def paired_bootstrap(
    real: Sequence[bool],
    placebo: Sequence[bool],
    touched_real: Sequence[bool],
    touched_placebo: Sequence[bool],
    n_sims: int,
    seed: int,
) -> dict[str, float]:
    """Resample SETUPS with replacement and recompute both arms' rates on each draw.

    One index vector is applied to BOTH arms, which is what makes it paired — the same
    arrangement `breakout_nulls.drawdown_difference_bootstrap` uses, and for the same
    reason: the arms share the setups, so resampling them independently would add a
    difference that is not there.

    Returns the difference's mean, its 5th and 95th percentiles, and the share of draws in
    which the real arm did NOT beat the placebo. A CI straddling zero is the answer, not a
    failure to reach one."""
    rng = np.random.default_rng(seed)
    n = len(real)
    r = np.asarray(real, dtype=float)
    p = np.asarray(placebo, dtype=float)
    tr = np.asarray(touched_real, dtype=float)
    tp = np.asarray(touched_placebo, dtype=float)
    diffs = np.empty(n_sims, dtype=float)
    for i in range(n_sims):
        index = rng.integers(0, n, size=n)
        real_touches, placebo_touches = tr[index].sum(), tp[index].sum()
        real_rate = r[index].sum() / real_touches if real_touches else 0.0
        placebo_rate = p[index].sum() / placebo_touches if placebo_touches else 0.0
        diffs[i] = real_rate - placebo_rate
    return {
        "mean_difference": float(diffs.mean()),
        "p05": float(np.percentile(diffs, 5)),
        "p95": float(np.percentile(diffs, 95)),
        "share_not_better": float((diffs <= 0.0).mean()),
        "n_sims": n_sims,
    }


def compare_to_placebo(
    closes: Sequence[float],
    atr: Sequence[float],
    setups: Sequence[Setup],
    real_levels: Sequence[float],
    placebo_factory: Callable[[np.random.Generator], Sequence[float]],
    touch_atr: float,
    n_sims: int = DEFAULT_SIMS,
    seed: int = 0,
    horizon: int = HORIZON,
) -> tuple[Reaction, NullDistribution, list[float]]:
    """Run the real arm once and `n_sims` placebo arms, and summarise the comparison.

    `placebo_factory(rng)` returns one level per setup. Everything else — the setups, the
    windows, the bands, the horizon, the statistic — is closed over and shared, so the two
    arms cannot differ in any respect other than the levels. The pairing is enforced by the
    signature rather than by discipline, which is the arrangement
    `terrain_field_nulls.compare_field_to_null` uses and the reason it is trustworthy."""
    real = reaction_at(closes, atr, setups, real_levels, touch_atr, horizon)
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(n_sims):
        levels = placebo_factory(rng)
        values.append(
            reaction_at(closes, atr, setups, levels, touch_atr, horizon).p_continuation
        )
    return real, summarise_null(values, real.p_continuation, CONTINUATION), values

DEPTH_BIN = 0.05
"""Width of the retracement bins the depth-matched expectation is built on.

Twenty bins over [0, 1]. Not swept, and chosen before any depth number was looked at: it is
the coarsest binning that still separates the C3 ladder's neighbouring rungs, which sit
about 0.05-0.07 apart."""


def depth_of(setup: Setup, level: float) -> float:
    """Where `level` sits on the setup's leg, as a retracement fraction."""
    value = retracement(setup.leg, level)
    return float("nan") if value is None else value


def depth_bin(depth: float) -> int | None:
    """Bin index, or None if the depth is outside [0, 1] or undefined."""
    if not math.isfinite(depth) or depth < 0.0 or depth > 1.0:
        return None
    return min(int(depth / DEPTH_BIN), int(1.0 / DEPTH_BIN) - 1)


@dataclass
class DepthTable:
    """Continuation counts by retracement bin, accumulated over the placebo draws.

    This exists because of what the C3 ladder turned out to be. The eight ratios produced a
    strictly monotone staircase in DEPTH — shallow ratios continue least, deep ones most —
    which makes depth a nuisance variable running through every other arm. A level that sits
    deep on the leg will beat a uniformly-drawn placebo whether or not it means anything,
    and a level that sits shallow will lose to one.

    So the unmatched percentile is not the verdict. The verdict is: does the real arm beat
    what a placebo AT THE SAME DEPTH would have done?"""

    touched: list[int]
    continued: list[int]

    @classmethod
    def empty(cls) -> "DepthTable":
        n = int(1.0 / DEPTH_BIN)
        return cls([0] * n, [0] * n)

    def add(self, depth: float, did_continue: bool) -> None:
        index = depth_bin(depth)
        if index is None:
            return
        self.touched[index] += 1
        self.continued[index] += did_continue

    def rate(self, index: int) -> float | None:
        return self.continued[index] / self.touched[index] if self.touched[index] else None

    def expected_for(self, depths: Sequence[float]) -> tuple[float, int]:
        """What a depth-matched placebo would have scored on this depth distribution.

        Returns `(rate, n_covered)`. Real touches whose bin the placebo never reached are
        EXCLUDED and counted, never imputed from a neighbouring bin — an unpopulated bin
        means the comparison has nothing to say there, and filling it in would be inventing
        the answer at exactly the depths where the real arm is unusual."""
        total = covered = 0.0
        n = 0
        for depth in depths:
            index = depth_bin(depth)
            if index is None:
                continue
            rate = self.rate(index)
            if rate is None:
                continue
            total += rate
            covered += 1.0
            n += 1
        return (total / covered if covered else float("nan")), n
