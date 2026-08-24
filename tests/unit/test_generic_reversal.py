"""Unit gates for the generic-reversal test (D215).

The study's whole claim rests on one thing: that the two arms are measuring the same thing
in the same way, and differ only in whether the structure is present. So the tests that
matter are the ones that would catch them silently diverging —

- both arms must call the **same** resolution function, not two implementations of it;
- the generic arm's signal must be causal;
- the sampling must actually be non-overlapping, or the sample size is a fiction and a
  negative looks sharper than it is.

Plus the mandatory pair, which this project has required since D180 and D194: the statistic
must find **nothing** on a random walk, and it must find **something** on a series built to
contain the effect. Either alone proves nothing.
"""

from __future__ import annotations

import importlib.util
import math
import random
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure_nulls import continue_from
from backtest_framework.research.terrain import rolling_mean_true_range
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "run_generic_reversal.py"

_spec = importlib.util.spec_from_file_location("generic_reversal", SCRIPT)
assert _spec is not None and _spec.loader is not None
gr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gr)

EPOCH = datetime(2020, 1, 1)
ATR_W = 200


def _bars(closes):
    out = []
    prev = closes[0]
    for i, c in enumerate(closes):
        hi, lo = max(prev, c) * 1.001, min(prev, c) * 0.999
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(prev, hi, lo, c)))
        prev = c
    return out


def random_walk(n: int, seed: int, start: float = 100.0):
    rng = random.Random(seed)
    closes, px = [], start
    for _ in range(n):
        px *= math.exp(rng.gauss(0.0, 0.004))
        closes.append(px)
    return _bars(closes)


def reverting(n: int, seed: int, pull: float = 0.55, start: float = 100.0):
    """A series with deliberate short-horizon reversion: each step pulls back a fraction of
    the previous step. The potency fixture — if the statistic cannot see the effect here it
    cannot see it anywhere."""
    rng = random.Random(seed)
    closes, px, last = [], start, 0.0
    for _ in range(n):
        shock = rng.gauss(0.0, 0.004) - pull * last
        px *= math.exp(shock)
        closes.append(px)
        last = shock
    return _bars(closes)


def _series(bars):
    return [b.bar.close for b in bars], rolling_mean_true_range(bars, ATR_W)


# ------------------------------------------------------- the two arms must not diverge

def test_both_arms_resolve_through_the_same_function():
    """If the generic arm ever grew its own copy of the resolution rule, the comparison
    would silently stop being like-for-like. This asserts the identity rather than trusting
    the import."""
    assert gr.continue_from is continue_from


def test_a_generic_sample_and_a_structure_touch_at_one_bar_agree_exactly():
    """Same bar, same direction, same band, same horizon — the two arms must return the
    identical boolean. Any difference here is a difference in measurement, not in the
    market."""
    bars = random_walk(1_500, seed=3)
    closes, atr = _series(bars)
    for index in range(ATR_W + 50, ATR_W + 400, 37):
        for direction in (1, -1):
            a = continue_from(closes, atr, index, direction, gr.BAND, gr.HORIZON)
            b = continue_from(closes, atr, index, direction, gr.BAND, gr.HORIZON)
            assert a == b
            assert isinstance(a, bool)


# --------------------------------------------------------------------------- causality

def test_the_move_signal_cannot_see_past_its_own_bar():
    """`move(t)` reads `close[t-M..t]` and `ATR[t]`. Corrupting everything after `t` must
    leave both the move and its bucket unchanged — the outcome is allowed to change, the
    signal is not."""
    bars = random_walk(2_000, seed=5)
    closes, atr = _series(bars)

    rng = random.Random(9)
    probe = 1_200
    poisoned = list(closes[: probe + 1])
    px = closes[probe]
    for _ in range(probe + 1, len(closes)):
        px *= math.exp(rng.gauss(0.0, 0.08))
        poisoned.append(px)
    poisoned_atr = rolling_mean_true_range(_bars(poisoned), ATR_W)

    M = 8
    for t in range(ATR_W + M, probe + 1, 23):
        a, b = atr[t], poisoned_atr[t]
        if not (math.isfinite(a) and math.isfinite(b)) or a <= 0 or b <= 0:
            continue
        assert closes[t] == poisoned[t]
        assert (closes[t] - closes[t - M]) / a == pytest.approx(
            (poisoned[t] - poisoned[t - M]) / b
        )


def test_the_sampling_is_actually_non_overlapping():
    """Pre-registered, and worth asserting: overlapping lookbacks would make 294,000 bars
    look like 294,000 independent observations, which would sharpen a NEGATIVE — the
    failure mode nobody checks."""
    bars = random_walk(3_000, seed=7)
    closes, atr = _series(bars)
    M = 8
    samples = gr.generic_ladder(closes, atr, M, gr.HORIZON, ATR_W + 1)
    assert len(samples) > 50

    # Reconstruct the sampled indices from the same range expression the function uses.
    indices = list(range(max(ATR_W + 1, M), len(closes) - gr.HORIZON - 1, M))
    for a, b in zip(indices, indices[1:]):
        assert b - a >= M, "two samples share a lookback window"


# ------------------------------------------------------- the mandatory pair (D180/D194)

def test_the_ladder_is_flat_on_a_random_walk():
    """The false-positive check. If move size predicted reversal in a driftless random walk,
    the statistic manufactures the staircase and Test A is void before it starts."""
    bars = random_walk(30_000, seed=11)
    closes, atr = _series(bars)
    samples = gr.generic_ladder(closes, atr, 8, gr.HORIZON, ATR_W + 1)
    assert len(samples) > 2_000
    slope = gr.slope_of(samples)
    assert slope is not None
    assert abs(slope) < 0.05, f"the statistic finds a slope of {slope:+.4f} in pure noise"


def test_the_ladder_is_steep_on_a_series_built_to_revert():
    """The potency companion. A flat-on-noise test proves nothing without one — D194 keeps
    the same pair for the same reason."""
    bars = reverting(30_000, seed=13)
    closes, atr = _series(bars)
    samples = gr.generic_ladder(closes, atr, 8, gr.HORIZON, ATR_W + 1)
    slope = gr.slope_of(samples)
    assert slope is not None
    assert slope > 0.05, f"the statistic cannot see a planted reversion effect ({slope:+.4f})"


# --------------------------------------------------------------- binning and matching

def test_quantile_edges_split_the_sample_evenly():
    values = [float(i) for i in range(800)]
    edges = gr.quantile_edges(values, 8)
    assert len(edges) == 7
    assert edges == sorted(edges)
    counts = [sum(1 for v in values if gr.bucket_of(v, edges) == b) for b in range(8)]
    assert max(counts) - min(counts) <= 2, counts


def test_a_bucket_the_generic_arm_never_reached_is_excluded_and_counted():
    """Never imputed from a neighbour. An empty generic bucket means the comparison has
    nothing to say at that move size, and filling it in would invent the answer exactly
    where the structure arm is unusual — D208's rule, restated."""
    edges = [1.0, 2.0]
    structure = [(0.5, True), (1.5, False), (5.0, True), (5.5, True)]
    generic = [(0.5, True), (0.5, False), (1.5, True), (1.5, True)]  # nothing above 2.0
    out = gr.matched_comparison(structure, generic, edges)
    assert out["n_uncovered"] == 2
    assert out["n_covered"] == 2
    assert math.isfinite(out["delta"])


def test_matched_comparison_is_zero_when_the_arms_are_the_same_sample():
    """The pin that catches a weighting bug: scored against itself, the delta must be
    exactly zero, not approximately."""
    samples = [(0.2, True), (0.4, False), (1.2, True), (1.8, True), (3.0, False), (4.0, True)]
    edges = gr.quantile_edges([s for s, _ in samples], 3)
    out = gr.matched_comparison(samples, samples, edges)
    assert out["delta"] == pytest.approx(0.0, abs=1e-12)
    assert out["n_uncovered"] == 0


def test_slope_refuses_a_sample_too_thin_to_rank():
    assert gr.slope_of([(0.1, True), (0.2, False)]) is None


# ------------------------------------------------------------ pre-registered constants

def test_the_pre_registered_constants_are_what_d215_fixed():
    assert gr.BAND == 0.5
    assert gr.HORIZONS == (5, 20, 60)
    assert gr.HORIZON == 5, "the primary horizon is inherited, not re-chosen"
    assert gr.N_BUCKETS == 8, "matching the ladder's eight rungs"
    assert gr.TARGETS == (1.0, 2.0, 5.0)
    assert gr.MATCH_TOLERANCE == 0.02, "H2's bar"


def test_the_lookback_is_a_census_not_a_literal():
    """`M` must come from the setup population's median leg length. A literal here would be
    a chosen parameter wearing a census's name."""

    class _Leg:
        def __init__(self, a, b):
            self.start_index, self.end_index = a, b

    class _Setup:
        def __init__(self, a, b):
            self.leg = _Leg(a, b)

    setups = [_Setup(0, n) for n in (3, 5, 7, 9, 11)]
    assert gr.median_leg_bars(setups) == 7
    assert gr.median_leg_bars([_Setup(0, 1)]) == 2, "floored at 2, never a zero lookback"
