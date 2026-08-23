"""S5b — S5's swing supply/demand sensor with ONE rule changed: a wick through decays.

A variant of `terrain_swing.SwingSupplyDemandSensor`, in its own module so that S5 stays
byte-for-byte what it was when it was written. Everything it can reuse it imports —
`_is_swing_bars`, `confirmed_pivots`, `_impulse`, `_cluster`, `_rank_scores`, `SwingLevel`,
`SWING_K`, `CLUSTER_ATR`, `MIN_SWINGS`, `SHARPNESS_BARS`, `MIN_LEVELS`. A variant that
re-implemented the shared parts would be a second sensor pretending to be a comparison:
any difference between the two readings could then come from the copy rather than from the
rule, and there would be no way to tell which afterwards.

## The one change

S5's invalidation is: **a CLOSE beyond the band's far edge kills the level permanently.**
That is kept exactly. What S5b adds is a treatment for the bar that goes through the band
and comes back:

- a DEMAND band (`sign == -1`, built from swing lows) whose lower edge is pierced by a
  bar's LOW while that bar's CLOSE finishes above the edge,
- a SUPPLY band (`sign == +1`, built from swing highs) whose upper edge is pierced by a
  bar's HIGH while that bar's CLOSE finishes below the edge,

survives with **reduced strength** rather than at full strength:
`strength_multiplier = (1 - decay) ** pierces`, multiplicative and cumulative, counted over
the same formation→index walk that already counts tests.

The hypothesis being separated out is narrow and worth stating so it can be rejected
cleanly: *a level that has been probed and rejected is not the same object as a level that
has never been touched from the wrong side, even though S5 scores them identically.* If
that is false, S5b's decay is noise multiplied into a score and it should measure no better
than S5 — which is the point of building it as a variant with one moving part.

## What S5b does NOT do, stated first because the framing invites the opposite reading

**S5b does not keep any level alive that S5 kills.** S5's kill test already reads `close`
alone; a wick that closes back was ALREADY survivable under S5. So the two sensors emit the
**same level set at every index, always** — not merely when no pierce fires. The entire
difference between them is the score attached to those levels, and therefore the mass
`density()` puts in each bucket and the order `PriceDensity.levels` would rank them in.

This is written at the top rather than discovered in a result, because "S5b rescues levels
S5 destroyed" is the natural thing to assume from the name and it is false. Anyone reading
a comparison of the two should read it as a re-weighting test, not a survival test. The
test `test_the_level_set_is_always_identical_to_s5_pierces_or_not` pins the claim rather
than leaving it as this paragraph's assertion.

**And the consequence, which is worse and is the reason this is the second paragraph of
the module rather than a footnote:** `terrain_nulls.run_null` consumes `sensor_levels`,
`sensor_levels` takes the direct `levels_at` path for this sensor, and `levels_at` returns
PRICES. The decay lives in the score, and the only thing that reads the score is
`density()`, which nothing on that path calls. **The existing null harness would therefore
return a byte-identical verdict for S5b and S5, at any decay** — measured, not reasoned:
identical maps on all 182 BTC and 132 ETH rebuild dates of the daily fixture, at both
allowed decays.

So S5b is not measurable by the harness as it stands. Running `run_null` on it would
produce S5's number and read like an independent confirmation of it. Closing that gap
means either a metric that weights touches by level score, or routing S5b through
`density()` and accepting the `HVN_QUANTILE` extraction S5's `levels_at` exists to avoid —
both of which are changes to the harness, both of which are pre-registration decisions,
and neither of which is made here. Recording it before any result rather than after is the
whole point of writing it down.

**Support-becomes-resistance is still not implemented.** Broken is still dead, still
permanently, and the flip is still a different hypothesis (S5's words, unchanged here).
Decay is not a soft version of the flip: it never revives, never changes sign, and its
multiplier only ever moves one way.

## The new parameter is a cost, and it is paid at the door

`DECAY_PER_PIERCE = (0.1, 0.25)` — two values, fixed here, before the sensor has been run
on anything. Every combination tested enters the terrain programme's multiplicity ledger,
which stood at 147 cumulative looks after D194 and is never reset. A third value added
later would be an unregistered search, and D194's own ledger discipline is that a
configuration tried and learned nothing from still costs a look.

Two rather than one because a single value would be indistinguishable from a value chosen
after seeing which one worked; two rather than four because the ledger is the constraint
and `k x cluster_atr x decay` is already 8 cells per symbol before any lookback or touch
band is varied. There is no default: the caller names the decay or the constructor raises,
the same way S5 refuses to guess `volume_units` after D187.

## Where the multiplier is applied, and why not somewhere cheaper

The multiplier hits the **final combined score**, after the rank-normalised
volume x sharpness x tests product — not any one component and not the inputs to the ranks.

Applying it to a component would launder it: `_rank_scores` only reads the ORDER of the
values it is given, so multiplying `tests` or `volume` by 0.75 before ranking changes
nothing at all unless it happens to reorder two levels, and then it changes the rank by a
full 1/n step rather than by 25%. A decay that silently did nothing on most maps and jumped
discontinuously on the rest would be a mechanism no result could be attributed to. Outside
the ranks, `(1 - decay) ** pierces` means precisely what it says and the arithmetic is
pinned by test.

The consequence, stated rather than left to be found: S5b's scores are no longer confined
to the rank grid, so a heavily-pierced level can be pushed below a level it outranks on all
three components. That is the mechanism, not a side effect.

## The three leak sites are unchanged, and so is the gate on them

D173's confirmation lag is the whole risk and it is quoted in `terrain_swing`'s docstring
for that reason. S5b inherits all three places the design could read the future — pivot
confirmation, the impulse window, and the invalidation walk — and adds nothing to them: the
decay walk runs over exactly the bars `_survives` already walked, `formed_index + 1` to
`index`, and reads `high`/`low` from bars whose `close` the S5 walk was already reading.
That is an argument, and D181 established that arguments are not what protects analytics
built on strategy output. The property test does.

## The confound carries over untouched

S5's `tests` component is D189's H2 confound in explicit form: a level scoring highly on
tests is by construction a price the market keeps returning to. Decay does not address it
and is not offered as addressing it. If anything it sharpens the question, because a pierce
is also a return to the price — a level can gain a test and a pierce on the same bar, and
both are recorded, because they are different events and collapsing them would be a
modelling choice smuggled in as bookkeeping. So a pass by S5b is not evidence of supply and
demand until H2 is ruled out, exactly as for S5 and D194.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from ..data.bars import TimestampedBar
from .terrain import ATR_WINDOW, VOLUME_UNITS, PriceDensity, mean_true_range
from .terrain_swing import (
    CLUSTER_ATR,
    MIN_LEVELS,
    SHARPNESS_BARS,
    SWING_K,
    SwingLevel,
    _cluster,
    confirmed_pivots,
)
from .terrain_swing import score_levels as _s5_score_levels

__all__ = [
    "DECAY_PER_PIERCE",
    "DecayedSwingLevel",
    "SwingSupplyDemandSensorV2",
    "score_levels",
]

DECAY_PER_PIERCE = (0.1, 0.25)
"""The ONLY decay-per-pierce values this sensor may take. A free parameter is a
multiplicity cost before it is anything else, so the set is fixed here rather than at the
call site, and membership is enforced by the constructor rather than documented.

0.1 and 0.25 are a mild and a severe reading of the same idea — after four pierces a level
retains 66% or 32% of its score respectively, which is the range over which the mechanism
is worth distinguishing from no mechanism at all. Neither is a default: `decay` has no
default value anywhere in this module."""


@dataclass(frozen=True)
class DecayedSwingLevel(SwingLevel):
    """An S5 level plus the count of wicks that went through it and closed back.

    Subclasses `SwingLevel` rather than restating its seven fields so that `contains()`,
    the field semantics and any future correction to them are shared by construction —
    S5 and S5b disagreeing about what `tests` means would make every comparison between
    them uninterpretable. `pierces` defaults to 0 because a level as `_cluster` builds it
    has not yet been walked forward, not because zero is a safe fallback."""

    pierces: int = 0
    """Bars that pierced the far edge intrabar and closed back on the live side, counted
    over `(formed_index, index]`. A bar that pierces AND closes beyond the edge is not
    counted here — it kills the level, and a dead level has no score to decay."""

    def strength_multiplier(self, decay: float) -> float:
        """`(1 - decay) ** pierces`. Separate from the score so the arithmetic can be
        pinned on its own, without a rank-normalisation standing between the test and the
        thing being asserted."""
        return (1.0 - decay) ** self.pierces


def _survives_with_decay(
    bars: Sequence[TimestampedBar], level: SwingLevel, index: int
) -> tuple[bool, int, int]:
    """Walk formation → `index`. Returns (still alive, tests survived, pierces taken).

    Deliberately a near-copy of `terrain_swing._survives` rather than a wrapper around it.
    The pierce has to be detected on the same pass as the kill and in a fixed order — the
    close test runs FIRST, so a bar that goes through the edge and stays there dies instead
    of decaying — and there is no way to get that ordering by calling a function that has
    already returned. The duplication is ~6 lines and the tests pin both walks against the
    same fixtures; a clever refactor of `_survives` would have meant editing S5.

    After the kill test has passed, `close` is known to be on the live side of `far`, so a
    pierce is exactly `low < far` for demand and `high > far` for supply. Both conditions
    are still written out in full below: the reader checking this for a look-ahead leak or
    an off-by-one should not have to reconstruct an invariant from an earlier branch.

    A bar may count as a test and a pierce simultaneously — wick through the edge, close
    back inside the band. Both are recorded. They are different events (one is interest at
    the price, the other is a failed excursion through it) and netting them would be a
    hypothesis about their relationship rather than a measurement of either."""
    far = level.price + level.half_width if level.sign > 0 else level.price - level.half_width
    tests = level.tests  # starts at the number of forming pivots, as S5 does
    pierces = 0
    inside = False
    for t in range(level.formed_index + 1, index + 1):
        bar = bars[t].bar
        if (bar.close > far) if level.sign > 0 else (bar.close < far):
            return False, tests, pierces  # broken is still dead, still permanently
        pierced = (
            (bar.high > far and bar.close <= far)
            if level.sign > 0
            else (bar.low < far and bar.close >= far)
        )
        if pierced:
            pierces += 1
        now_inside = level.contains(bar.close)
        if now_inside and not inside:
            tests += 1
        inside = now_inside
    return True, tests, pierces


def score_levels(levels: Sequence[DecayedSwingLevel], decay: float) -> list[float]:
    """S5's score, times `(1 - decay) ** pierces`.

    Built by calling `terrain_swing.score_levels` rather than re-deriving the product, so
    the base is the same arithmetic S5 uses by construction and not by inspection. With no
    pierces anywhere this returns S5's list element-for-element, which is the equivalence
    the variant has to satisfy to be a variant at all."""
    base = _s5_score_levels(levels)
    return [b * lv.strength_multiplier(decay) for b, lv in zip(base, levels)]


@dataclass(frozen=True)
class SwingSupplyDemandSensorV2:
    """S5b — S5's bands, scored down each time a wick goes through and closes back.

    Conforms to the `TerrainSensor` protocol in `terrain.py`, so D189's null harness — "the
    only piece of machinery in this project that can answer *does this level mean
    anything*" — consumes it unchanged. Frozen for the protocol's stated reason: a sensor
    whose parameters can change after construction cannot be trusted to have produced the
    densities attributed to it.

    Emits `PriceDensity` with `spans` left empty, as S5 does. The span census counts how
    many buckets a BAR's range covered; it is an S1 construction, it carried D194's
    degeneracy diagnostic, and it means nothing for a sensor whose levels are discrete. It
    is left empty rather than faked."""

    k: int
    cluster_atr: float
    volume_units: str
    lookback_bars: int
    decay: float
    atr_window: int = ATR_WINDOW
    name: str = "S5b_swing_supply_demand_decay"

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
        if self.decay not in DECAY_PER_PIERCE:
            raise ValueError(
                f"decay must be one of {DECAY_PER_PIERCE}, got {self.decay}. This is S5b's "
                "only new parameter and therefore its only new multiplicity cost; a third "
                "value is an unregistered search."
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
    ) -> list[DecayedSwingLevel]:
        """Every level alive at `index`, both signs, with retests and pierces filled in.

        The survival decision here is IDENTICAL to S5's — same clustering, same close-based
        kill — so this returns the same bands S5 returns, differing only in the `pierces`
        field. Verified by test rather than by this sentence."""
        atr = mean_true_range(bars, index - self.atr_window + 1, index + 1)
        if not math.isfinite(atr) or atr <= 0.0:
            return []
        half_width = atr * self.cluster_atr

        alive: list[DecayedSwingLevel] = []
        for sign in (1, -1):
            pivots = confirmed_pivots(
                bars, index, self.k, sign, self.lookback_bars, SHARPNESS_BARS
            )
            for level in _cluster(bars, volumes, pivots, sign, half_width, atr):
                survives, tests, pierces = _survives_with_decay(bars, level, index)
                if not survives:
                    continue  # broken is dead, permanently
                alive.append(
                    DecayedSwingLevel(
                        price=level.price, sign=level.sign, half_width=level.half_width,
                        n_swings=level.n_swings, volume=level.volume,
                        sharpness=level.sharpness, tests=tests,
                        formed_index=level.formed_index, pierces=pierces,
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

        Present for the reason S5's is: `terrain_nulls.sensor_levels` takes the direct path
        when a sensor publishes `levels_at`, and routes it through `PriceDensity.levels`
        otherwise. That fallback keeps only local maxima at or above `HVN_QUANTILE`, which
        on a sparse spike map discarded three of every four levels S5 produced and imported
        a quantile this sensor does not have. Omitting this method would silently put S5b
        on the lossy path and make every S5-vs-S5b comparison a comparison of two
        extraction rules as well as two scoring rules.

        Note what this does NOT carry: prices only, so the decay is invisible here. Two
        sensors differing only in score therefore hand the harness the same level set —
        which is the honest statement of what S5b changes, and is discussed at length in
        the module docstring."""
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
        """Decayed mass at each live level, over `bars[index - lookback + 1 : index + 1]`.

        Restates S5's bucketing rather than delegating to it, because the only line that
        differs is the score — and S5 does not expose a seam to inject one through, nor
        should it grow one to accommodate a variant that came after it.

        Everything after `index` is unreachable: pivots stop at `index - max(k,
        SHARPNESS_BARS)`, the impulse window ends at or before `index`, and the
        invalidation/decay walk runs only to `index`. Asserted by property test, not by
        this sentence — that is D181's lesson, and the pierce check reading `high` and
        `low` is a fourth field read on the same bars, so the property is re-tested here
        rather than inherited from S5's suite."""
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
        scores = score_levels(levels, self.decay)
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
