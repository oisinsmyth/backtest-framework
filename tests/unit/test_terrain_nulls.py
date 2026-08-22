"""Unit gates for the terrain null-test harness (D189, WP2).

Two checks matter here and the second matters most.

**Planted levels must be found.** A harness that cannot detect structure that is definitely
there would return "fail" for every sensor and end the programme for the wrong reason.

**A pure random walk must produce NOTHING.** `TERRAIN_IMPLEMENTATION_PLAN.md` calls this
mandatory, and after D180 the reason is concrete: E1 cleared its bar five times on a sample
that turned out to be its best case, and every one of those passes looked like evidence. A
harness that finds levels in noise would invalidate every terrain result downstream of it
before any of them are written — and it would do so invisibly, because the output would look
exactly like a discovery.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain_nulls import (
    HORIZON,
    TERRAIN_METRICS,
    level_reactions,
    pseudo_levels,
    run_null,
    verdict,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def _bars(closes: list[float]) -> list[TimestampedBar]:
    return [
        TimestampedBar(
            EPOCH + timedelta(days=i),
            Bar(open=c, high=c * 1.01, low=c * 0.99, close=c),
        )
        for i, c in enumerate(closes)
    ]


def random_walk(n: int, seed: int, sigma: float = 0.02, start: float = 100.0) -> list[float]:
    rng = random.Random(seed)
    out, px = [], start
    for _ in range(n):
        px *= math.exp(rng.gauss(0.0, sigma))
        out.append(px)
    return out


def bouncing(
    n: int, seed: int, low: float = 90.0, high: float = 100.0, period: int = 20
) -> list[float]:
    """A triangular oscillation between `low` and `high`, so both bounds are REAL levels:
    price arrives at them repeatedly and turns around every time.

    Two earlier attempts at this fixture were wrong in opposite directions, and both were
    caught by the harness rather than by inspection. A drift term of `-0.9 * gap` pushes
    price TOWARD the level — a magnet, which produces FEWER reversals than random. Flipping
    it to `+1.2 * gap` made a wall price could not return to, giving one touch in 1,500
    bars. A level has to be somewhere price keeps coming back to AND keeps turning at, and
    an oscillation is the simplest thing that is both.

    A level at either bound reverses on every touch. A level in the middle of the range is
    crossed four times a period and reverses at none of them, which is what makes this a
    test rather than a tautology."""
    rng = random.Random(seed)
    out = []
    for i in range(n):
        phase = (i % period) / period
        base = low + (high - low) * (2 * phase if phase < 0.5 else 2 * (1.0 - phase))
        out.append(base * math.exp(rng.gauss(0.0, 0.002)))
    return out


# ------------------------------------------------------------------ it detects structure


def test_planted_levels_are_detected():
    """A level price genuinely reverses at must beat random placement."""
    bars = _bars(bouncing(1500, seed=3))
    n = len(bars)
    real = {t: (100.0,) for t in range(200, n - HORIZON, 20)}

    rng = np.random.default_rng(0)
    truth = level_reactions(bars, real, k=0.5)
    assert truth.n_touches > 20, "the planted level was never touched — fixture is wrong"

    beaten = 0
    for _ in range(200):
        fake = level_reactions(bars, pseudo_levels_wide(real, rng), k=0.5)
        if fake.n_touches and fake.p_reversal >= truth.p_reversal:
            beaten += 1
    assert beaten / 200 <= 0.05, (
        f"a planted level was beaten by random placement {beaten / 200:.0%} of the time — "
        "the harness cannot see structure that is definitely there"
    )


def pseudo_levels_wide(real, rng):
    """Random levels over a WIDE band around the planted one.

    `pseudo_levels` matches the real map's span, and a map with a single level has zero
    span — so for the single-level fixture the null has to be widened by hand or it would
    place its random level exactly on the real one."""
    return {t: (float(rng.uniform(85.0, 115.0)),) for t in real}


# ------------------------------------------- and it does NOT invent structure (mandatory)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_a_pure_random_walk_yields_no_levels(seed: int):
    """THE mandatory false-positive check.

    A geometric random walk has no support or resistance — there is nothing at any price.
    If the harness reports a sensor beating its null here, every downstream terrain result
    is uninterpretable."""
    from backtest_framework.research.terrain import VolumeProfileSensor

    n = 1200
    bars = _bars(random_walk(n, seed=seed))
    rng = random.Random(seed + 100)
    volumes = [rng.uniform(500.0, 1500.0) for _ in range(n)]

    sensor = VolumeProfileSensor(90, 0.5, "shares")
    result = run_null(bars, volumes, sensor, k=0.5, n_sims=200, seed=seed)
    if not result["available"]:
        return  # no levels at all is also "found nothing"

    v = verdict(result)
    assert not v["passed"], (
        f"the harness found structure in a random walk (beat: {v['beaten']}) — it would "
        "report noise as a sensor verdict"
    )


def test_random_levels_do_not_beat_themselves():
    """Sanity on the null itself: two independent random level sets on the same series
    should be indistinguishable, so neither should systematically beat the other."""
    bars = _bars(random_walk(1000, seed=9))
    real = {t: (bars[t].bar.close,) for t in range(200, 950, 20)}
    rng = np.random.default_rng(5)
    a = level_reactions(bars, pseudo_levels(real, rng), k=1.0)
    b = level_reactions(bars, pseudo_levels(real, rng), k=1.0)
    if a.n_touches and b.n_touches:
        assert abs(a.p_reversal - b.p_reversal) < 0.5


# ------------------------------------------------------------------ definitions and guards


def test_a_price_sitting_inside_the_band_counts_as_one_touch():
    """The touch definition takes only the FIRST bar of an approach. Without that, a price
    that drifts along a level for a week reports as five touches and the reversal rate is
    measured on a denominator of loitering."""
    closes = [90.0] + [100.0] * 10 + [90.0]
    bars = _bars(closes * 30)
    levels = {0: (100.0,)}
    stats = level_reactions(bars, levels, k=1.0)
    approaches = sum(
        1
        for i in range(1, len(bars))
        if abs(bars[i].bar.close - 100.0) < 1e-9 and abs(bars[i - 1].bar.close - 100.0) > 1e-9
    )
    assert stats.n_touches <= approaches


def test_k_outside_the_specs_set_raises():
    bars = _bars(random_walk(300, seed=4))
    with pytest.raises(ValueError, match="k must be one of"):
        level_reactions(bars, {0: (100.0,)}, k=0.75)


def test_every_metric_declares_its_tail():
    """`MetricSpec.direction` is the hypothesis. A silently-chosen tail turns a two-sided
    question into a one-sided p-value (D130)."""
    for spec in TERRAIN_METRICS:
        assert spec.direction in ("high", "low"), spec.name
    by_name = {m.name: m for m in TERRAIN_METRICS}
    # Absorbing impulse means volatility FALLS at a real level, so this one is lower-tail.
    assert by_name["vol_ratio"].direction == "low"
    # Real levels should turn price back more often and be slower to cross.
    assert by_name["p_reversal"].direction == "high"
    assert by_name["traversal_bars"].direction == "high"


def test_a_sensor_with_no_levels_reports_unavailable_not_a_pass():
    from backtest_framework.research.terrain import VolumeProfileSensor

    bars = _bars([100.0] * 300)  # flat: no ATR, so no density and no levels
    sensor = VolumeProfileSensor(90, 0.5, "shares")
    result = run_null(bars, [100.0] * 300, sensor, k=0.5, n_sims=10, seed=0)
    assert result["available"] is False
    assert verdict(result)["passed"] is False
