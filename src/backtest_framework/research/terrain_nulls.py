"""Does a terrain sensor's map beat randomly placed levels? (D189, WP2)

This is the make-or-break work package of the terrain programme, and its verdict is a stop
condition:

    If S1 fails its null, STOP the terrain programme and report — do not proceed to WP3+
    on the theory that other sensors will save it.   — TERRAIN_IMPLEMENTATION_PLAN.md

A volume profile will always produce levels. The only question that matters is whether
price behaves differently at *those* levels than at the same number of levels scattered at
random over the same range. Everything downstream — fusion, F7/F8/F9, gates — is built on
the assumption that it does, and that assumption has never been tested here.

## The definitions are fixed HERE, before any run

`TERRAIN_MODEL.md` requires the touch and reversal definitions to be mechanical and written
down before the harness runs, so they cannot be adjusted once a verdict is unwelcome. They
are:

**Touch.** Bar `t` is a touch of level `L` if `|close_t - L| <= k * ATR_t` and the previous
bar was outside that band. Only the FIRST bar of an approach counts, so a price that sits
inside the band for a week is one touch rather than five.

**Approach side.** Below if `close_{t-1} < L`, above otherwise. Fixed at the touch and not
revisited.

**Reversal.** Within `HORIZON` bars of the touch, the close returns to `k * ATR` beyond the
band on the side it approached from, WITHOUT first reaching `k * ATR` beyond the band on the
far side. That is a bounce: it came, it did not get through, it went back.

**Traversal.** Bars from touch until the close is `k * ATR` beyond the band on the FAR side,
censored at `HORIZON`. A level that absorbs impulse should be slower to cross.

**Volatility response.** Realized volatility over the `HORIZON` bars after the touch divided
by realized volatility over the `HORIZON` bars before it. Dense inventory absorbs impulse,
so a real level should DECELERATE price — a ratio below 1, and below the random one.

`k` is swept only over the spec's `{0.5, 1.0}`. `HORIZON` is fixed at 5 bars, matching the
E2 window already in use (`breakout_study.E2_N`), rather than chosen here — a horizon picked
to make a verdict come out is the same failure as a threshold picked that way.

## The null

Pseudo-levels are matched to the real map's level DENSITY: the same count, drawn uniformly
over the same price range the real levels span. Matching the count matters — more levels
mean more touches mean more reversals, so an unmatched null would be answering "does having
levels beat having none", which is not the question.

## The false-positive check is mandatory

`tests/unit/test_terrain_nulls.py` runs this harness on a pure random walk and requires it
to find NOTHING. After D180 — five passes on a sample that turned out to be the rule's best
case — a harness that finds structure in noise would invalidate every result downstream of
it before any of them are written.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

import numpy as np

from ..data.bars import TimestampedBar
from .breakout_nulls import MetricSpec, NullDistribution, summarise_null
from .terrain import (
    ATR_WINDOW,
    TerrainSensor,
    mean_true_range,
    realized_volatility,
    rolling_mean_true_range,
    rolling_realized_volatility,
)

HORIZON = 5
"""Bars a reaction is measured over. Fixed at the E2 window already in the project
(`breakout_study.E2_N` starts at 5) rather than chosen here."""

TOUCH_ATR = (0.5, 1.0)
"""The only k values, per `TERRAIN_MODEL.md`."""

REBUILD_EVERY = 20
"""Bars between profile rebuilds — roughly monthly on daily bars.

Not a tuning knob: a trader does not redraw a volume profile every bar, and rebuilding at
every index would multiply the runtime by twenty to produce levels that barely move. The
levels between rebuilds are held, which is also what using them would look like."""

HVN_QUANTILE = 0.7
"""A high-volume node is a local maximum at or above the 70th percentile of occupied
bucket mass. Stated before the run; not swept."""

TERRAIN_METRICS: tuple[MetricSpec, ...] = (
    MetricSpec(
        "p_reversal",
        "high",
        "P(reversal | touch)",
        "at least the real reversal rate — real levels should turn price back more often "
        "than random ones",
    ),
    MetricSpec(
        "traversal_bars",
        "high",
        "Bars to traverse",
        "at least the real traversal time — dense inventory should be SLOWER to cross",
    ),
    MetricSpec(
        "vol_ratio",
        "low",
        "Realized vol after / before",
        "a deceleration at least as strong as the real one — absorbing impulse means "
        "volatility falls approaching the level",
    ),
)
"""Each metric declares its own tail. `MetricSpec` exists precisely so the direction is the
hypothesis rather than something chosen once the numbers are in (D130's note)."""


@dataclass(frozen=True)
class ReactionStats:
    n_touches: int
    p_reversal: float
    traversal_bars: float
    vol_ratio: float

    def to_dict(self) -> dict[str, float]:
        return {
            "n_touches": float(self.n_touches),
            "p_reversal": self.p_reversal,
            "traversal_bars": self.traversal_bars,
            "vol_ratio": self.vol_ratio,
        }

    def get(self, metric: str) -> float:
        return {
            "p_reversal": self.p_reversal,
            "traversal_bars": self.traversal_bars,
            "vol_ratio": self.vol_ratio,
        }[metric]


def level_reactions(
    bars: Sequence[TimestampedBar],
    levels_by_index: Mapping[int, Sequence[float]],
    k: float,
    horizon: int = HORIZON,
    atr_window: int = ATR_WINDOW,
    atr_series: Sequence[float] | None = None,
    vol_series: Sequence[float] | None = None,
) -> ReactionStats:
    """Reaction statistics at a set of levels, under the definitions fixed in this module.

    `levels_by_index` maps a bar index to the levels in force from that bar until the next
    entry — the profile is rebuilt periodically and held between rebuilds."""
    if k not in TOUCH_ATR:
        raise ValueError(f"k must be one of {TOUCH_ATR}, got {k}")

    schedule = sorted(levels_by_index)
    if not schedule:
        return ReactionStats(0, 0.0, 0.0, 0.0)

    reversals, traversals, vol_ratios = [], [], []
    active: tuple[float, ...] = ()
    next_change = 0
    inside: dict[float, bool] = {}

    for t in range(schedule[0], len(bars) - horizon):
        if next_change < len(schedule) and t >= schedule[next_change]:
            active = tuple(levels_by_index[schedule[next_change]])
            inside = {lv: False for lv in active}
            next_change += 1
        if not active or t < atr_window + 1:
            continue

        # Precomputed series when the caller supplies them, per-call otherwise. The
        # fallback is not dead code: it keeps the daily path (D189) byte-identical, and
        # the two are pinned to agree by test rather than by inspection.
        atr = atr_series[t] if atr_series is not None else mean_true_range(
            bars, t - atr_window + 1, t + 1
        )
        if not math.isfinite(atr) or atr <= 0.0:
            continue
        band = k * atr
        close = bars[t].bar.close
        prev = bars[t - 1].bar.close

        for level in active:
            in_band = abs(close - level) <= band
            was_inside = inside.get(level, False)
            inside[level] = in_band
            if not in_band or was_inside:
                continue  # not a touch: outside, or already inside from a previous bar

            from_below = prev < level
            near, far = (level - band, level + band) if from_below else (level + band, level - band)

            reversed_ = False
            crossed = False
            traversal = float(horizon)
            for j in range(t + 1, min(t + 1 + horizon, len(bars))):
                c = bars[j].bar.close
                beyond_far = c > far + band if from_below else c < far - band
                back_near = c < near - band if from_below else c > near + band
                if beyond_far:
                    crossed = True
                    traversal = float(j - t)
                    break
                if back_near:
                    reversed_ = True
                    break

            reversals.append(1.0 if reversed_ and not crossed else 0.0)
            traversals.append(traversal)
            if vol_series is not None:
                before = vol_series[t]
                after = vol_series[t + horizon] if t + horizon < len(vol_series) else 0.0
            else:
                before = realized_volatility(bars, t - horizon, t + 1)
                after = realized_volatility(bars, t, t + horizon + 1)
            if before > 0.0:
                vol_ratios.append(after / before)

    if not reversals:
        return ReactionStats(0, 0.0, 0.0, 0.0)
    return ReactionStats(
        n_touches=len(reversals),
        p_reversal=float(np.mean(reversals)),
        traversal_bars=float(np.mean(traversals)),
        vol_ratio=float(np.mean(vol_ratios)) if vol_ratios else 0.0,
    )


def sensor_levels(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    sensor: TerrainSensor,
    rebuild_every: int = REBUILD_EVERY,
) -> dict[int, tuple[float, ...]]:
    """Levels the sensor would have had, rebuilt every `rebuild_every` bars.

    **Two ways a sensor may supply levels, and the choice is the sensor's.** A histogram
    sensor (S1) emits a density and its levels are the high-volume nodes extracted from
    it. A sensor whose output is already a discrete set of levels (S5) publishes
    `levels_at` and that set is used directly.

    Forcing the second kind through the first path is not neutral: `PriceDensity.levels`
    keeps only local maxima at or above `HVN_QUANTILE`, which on a sparse spike map
    discarded three of every four levels S5 produced and imported a quantile the sensor
    never needed. The fallback is unchanged, so S1's path is byte-identical."""
    explicit = getattr(sensor, "levels_at", None)
    out: dict[int, tuple[float, ...]] = {}
    for t in range(0, len(bars), rebuild_every):
        if explicit is not None:
            levels = explicit(bars, t, volumes)
            if levels:
                out[t] = tuple(levels)
            continue
        density = sensor.density(bars, t, volumes)
        if density is None:
            continue
        levels = density.levels(HVN_QUANTILE, "hvn")
        if levels:
            out[t] = levels
    return out


def pseudo_levels(
    real: Mapping[int, Sequence[float]], rng: np.random.Generator
) -> dict[int, tuple[float, ...]]:
    """Random levels matched to the real map's density: same count, same span, same dates.

    Matching the COUNT is what makes this the right null. More levels mean more touches
    mean more reversals, so an unmatched comparison would answer "does having levels beat
    having none" — a question with an obvious and uninteresting answer."""
    out: dict[int, tuple[float, ...]] = {}
    for t, levels in real.items():
        if not levels:
            continue
        low, high = min(levels), max(levels)
        if high <= low:
            out[t] = tuple(levels)
            continue
        out[t] = tuple(float(x) for x in rng.uniform(low, high, size=len(levels)))
    return out


def run_null(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    sensor: TerrainSensor,
    k: float,
    n_sims: int = 500,
    seed: int = 0,
    rebuild_every: int = REBUILD_EVERY,
    horizon: int = HORIZON,
    atr_window: int = ATR_WINDOW,
    precompute: bool = False,
) -> dict[str, Any]:
    """The sensor's levels against `n_sims` matched random level sets.

    Returns the real statistics, the null distributions per metric, and the touch counts —
    the last of which is not decoration: a verdict on twelve touches is not a verdict, and
    the report must be able to say so."""
    real_levels = sensor_levels(bars, volumes, sensor, rebuild_every)
    if not real_levels:
        return {"available": False, "reason": "sensor produced no levels over this series"}

    # The ATR and realized-volatility series depend only on the BARS, never on the levels,
    # so they are identical across the real run and all `n_sims` null draws. Computing
    # them once turns the reaction scan from quadratic in the window into linear: measured
    # at 173 hours for D194's grid the per-call way, 0.5 hours this way. Off by default so
    # the daily path (D189) runs the exact code it ran before.
    atr_series = rolling_mean_true_range(bars, atr_window) if precompute else None
    vol_series = rolling_realized_volatility(bars, horizon) if precompute else None

    real = level_reactions(bars, real_levels, k, horizon, atr_window, atr_series, vol_series)
    if real.n_touches == 0:
        return {"available": False, "reason": "no touches of the sensor's levels"}

    rng = np.random.default_rng(seed)
    draws: dict[str, list[float]] = {m.name: [] for m in TERRAIN_METRICS}
    null_touches: list[int] = []
    for _ in range(n_sims):
        stats = level_reactions(
            bars, pseudo_levels(real_levels, rng), k, horizon, atr_window,
            atr_series, vol_series,
        )
        if stats.n_touches == 0:
            continue
        null_touches.append(stats.n_touches)
        for spec in TERRAIN_METRICS:
            draws[spec.name].append(stats.get(spec.name))

    distributions: dict[str, NullDistribution] = {}
    for spec in TERRAIN_METRICS:
        if len(draws[spec.name]) < 2:
            continue
        distributions[spec.name] = summarise_null(draws[spec.name], real.get(spec.name), spec)

    return {
        "available": True,
        "k": k,
        "n_sims": len(null_touches),
        "seed": seed,
        "rebuild_every": rebuild_every,
        "horizon": HORIZON,
        "hvn_quantile": HVN_QUANTILE,
        "n_rebuilds": len(real_levels),
        "mean_levels_per_rebuild": float(
            np.mean([len(v) for v in real_levels.values()])
        ),
        "real": real.to_dict(),
        "mean_null_touches": float(np.mean(null_touches)) if null_touches else 0.0,
        "distributions": {m: d.to_dict() for m, d in distributions.items()},
    }


def verdict(result: Mapping[str, Any], alpha: float = 0.05) -> dict[str, Any]:
    """Pass/fail on the stated rule: a sensor passes if it beats random placement on at
    least one metric at `alpha`, one-sided in the direction that metric declared.

    "At least one of three" is a deliberately GENEROUS bar, and it is stated as such. The
    stop condition it feeds is severe — a failure here ends the programme — so the test
    should not be the thing that ends it on a technicality. The multiplicity it costs is
    recorded in TERRAIN_RESULTS.md rather than corrected away: three metrics x two k values
    is six looks, and a 5% test taken six times is not a 5% test."""
    if not result.get("available"):
        return {"passed": False, "reason": result.get("reason", "unavailable"), "beaten": []}
    beaten = [
        name
        for name, d in result["distributions"].items()
        if float(d["p_value"]) <= alpha
    ]
    return {
        "passed": bool(beaten),
        "alpha": alpha,
        "beaten": sorted(beaten),
        "n_metrics": len(result["distributions"]),
        "n_touches": int(result["real"]["n_touches"]),
    }
