"""Property invariants for the breakout null generator (D40/D78/D130).

The unit suite checks the invariants on a handful of fixed series. These check them on
whatever hypothesis can construct: arbitrary lengths, arbitrary block sizes, arbitrary
segmentations, arbitrary (coherent) price paths. The two load-bearing claims —
"same multiset of bar shapes" and "buy-and-hold is invariant" — are what every p-value
in `docs/results/breakout_monte_carlo.md` rests on, so they get the stronger test.

`derandomize=True` per D78: a property suite that fails only on some seeds trains people
to re-run until green.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import breakout_nulls as bn
from backtest_framework.simulator.fills import Bar

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)
START = datetime(2021, 3, 1)


@st.composite
def coherent_bars(draw, min_bars: int = 12, max_bars: int = 220):
    """OHLC paths that satisfy the only structural constraint real bars have:
    low <= min(open, close) <= max(open, close) <= high, all strictly positive."""
    n = draw(st.integers(min_value=min_bars, max_value=max_bars))
    seed = draw(st.integers(min_value=0, max_value=2**32 - 1))
    drift = draw(st.floats(min_value=-0.004, max_value=0.004))
    vol = draw(st.floats(min_value=0.002, max_value=0.08))
    rng = np.random.default_rng(seed)

    bars = []
    close = 100.0
    for i in range(n):
        open_ = close * float(np.exp(rng.normal(0.0, vol / 3)))
        close = open_ * float(np.exp(rng.normal(drift, vol)))
        high = max(open_, close) * (1.0 + abs(float(rng.normal(0.0, vol / 2))))
        low = min(open_, close) * (1.0 - abs(float(rng.normal(0.0, vol / 2))))
        bars.append(TimestampedBar(START + timedelta(days=i), Bar(open_, high, low, close)))
    return bars


def _sorted_shapes(bars, lo: int = 0, hi: int | None = None) -> np.ndarray:
    ratios = bn.bar_shapes(bars).ratios[lo:hi]
    return ratios[np.lexsort(ratios.T[::-1])]


@SETTINGS
@given(bars=coherent_bars(), block_size=st.integers(min_value=1, max_value=64), seed=st.integers(0, 10_000))
def test_resampling_preserves_the_multiset_and_the_terminal_growth(bars, block_size, seed):
    shapes = bn.bar_shapes(bars)
    assume(block_size < shapes.n_shapes)
    path = bn.resample_bars(shapes, seed=seed, block_size=block_size)

    assert len(path) == len(bars)
    np.testing.assert_allclose(_sorted_shapes(path), _sorted_shapes(bars), rtol=1e-9)
    # Buy-and-hold cannot tell the difference — the product of a permuted multiset of
    # close ratios is the product of the multiset (D47's tolerance, relative).
    np.testing.assert_allclose(
        path[-1].bar.close / path[0].bar.close,
        bars[-1].bar.close / bars[0].bar.close,
        rtol=1e-9,
    )


@SETTINGS
@given(bars=coherent_bars(), block_size=st.integers(min_value=1, max_value=64), seed=st.integers(0, 10_000))
def test_resampled_bars_stay_coherent(bars, block_size, seed):
    shapes = bn.bar_shapes(bars)
    assume(block_size < shapes.n_shapes)
    for tb in bn.resample_bars(shapes, seed=seed, block_size=block_size):
        assert tb.bar.low > 0.0
        assert tb.bar.low <= min(tb.bar.open, tb.bar.close)
        assert tb.bar.high >= max(tb.bar.open, tb.bar.close)


@SETTINGS
@given(
    bars=coherent_bars(min_bars=40),
    split=st.floats(min_value=0.2, max_value=0.8),
    block_size=st.integers(min_value=1, max_value=8),
    seed=st.integers(0, 10_000),
)
def test_every_segment_boundary_close_is_invariant(bars, split, block_size, seed):
    """Segmentation's whole purpose (D130): the price at each boundary is a product over
    a segment's own shapes, so permuting inside segments cannot move it."""
    boundary = max(2, min(len(bars) - 3, int(split * len(bars))))
    shapes = bn.bar_shapes(bars, segment_starts=(boundary,))
    assume(all(block_size < end - start for start, end in shapes.segments()))
    path = bn.resample_bars(shapes, seed=seed, block_size=block_size)
    np.testing.assert_allclose(path[boundary].bar.close, bars[boundary].bar.close, rtol=1e-9)
    np.testing.assert_allclose(path[-1].bar.close, bars[-1].bar.close, rtol=1e-9)
    np.testing.assert_allclose(
        _sorted_shapes(path, boundary, None), _sorted_shapes(bars, boundary, None), rtol=1e-9
    )


@SETTINGS
@given(bars=coherent_bars(), block_size=st.integers(min_value=1, max_value=64), seed=st.integers(0, 10_000))
def test_the_same_seed_always_produces_the_same_path(bars, block_size, seed):
    shapes = bn.bar_shapes(bars)
    assume(block_size < shapes.n_shapes)
    a = bn.resample_bars(shapes, seed=seed, block_size=block_size)
    b = bn.resample_bars(shapes, seed=seed, block_size=block_size)
    assert [tb.bar for tb in a] == [tb.bar for tb in b]


@SETTINGS
@given(n=st.integers(min_value=2, max_value=500), block_size=st.integers(min_value=1, max_value=250), seed=st.integers(0, 10_000))
def test_block_permutation_is_always_a_bijection(n, block_size, seed):
    assume(block_size < n)
    index = bn.block_permutation(n, block_size, np.random.default_rng(seed))
    assert sorted(index.tolist()) == list(range(n))


@SETTINGS
@given(
    values=st.lists(st.floats(-50, 50, allow_nan=False), min_size=5, max_size=400),
    a=st.floats(-60, 60, allow_nan=False),
    b=st.floats(-60, 60, allow_nan=False),
)
def test_upper_tail_p_values_are_monotone_in_the_observed_result(values, a, b):
    """A better real result can never earn a worse p-value in the 'high' direction —
    the property that makes the reported number readable as evidence at all."""
    assume(a <= b)
    spec = bn.MetricSpec("m", "high", "M", "")
    assert bn.summarise_null(values, a, spec).p_value >= bn.summarise_null(values, b, spec).p_value


@SETTINGS
@given(
    values=st.lists(st.floats(-50, 50, allow_nan=False), min_size=5, max_size=400),
    real=st.floats(-60, 60, allow_nan=False),
)
def test_p_values_and_percentiles_stay_inside_their_ranges(values, real):
    for direction in ("high", "low"):
        d = bn.summarise_null(values, real, bn.MetricSpec("m", direction, "M", ""))
        assert 1.0 / (len(values) + 1.0) <= d.p_value <= 1.0
        assert 0.0 <= d.percentile <= 100.0
        assert d.p_value_se >= 0.0
