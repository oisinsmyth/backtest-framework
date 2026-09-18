"""Monte Carlo null suite for the breakout study (D130-D133).

The first two tests here are the ones that make the whole study valid: if the resampled
paths do not carry the same multiset of bar shapes, or if a block-1 shuffle does not
reproduce buy-and-hold's terminal wealth exactly, then the "same marginal distribution,
ordering destroyed" claim is false and every p-value in
`docs/results/breakout_monte_carlo.md` means nothing.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.analytics.metrics import max_drawdown
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import breakout_nulls as bn
from backtest_framework.research import breakout_study as bs
from backtest_framework.simulator.fills import Bar

START = datetime(2020, 1, 1)


def _random_bars(
    n: int, seed: int = 11, start_price: float = 100.0, drift: float = 0.0008
) -> list[TimestampedBar]:
    """Random OHLC bars with coherent geometry: high above both ends, low below both."""
    rng = np.random.default_rng(seed)
    bars = []
    close = start_price
    for i in range(n):
        open_ = close * float(np.exp(rng.normal(0.0, 0.005)))
        close = open_ * float(np.exp(rng.normal(drift, 0.02)))
        high = max(open_, close) * (1.0 + abs(float(rng.normal(0.0, 0.01))))
        low = min(open_, close) * (1.0 - abs(float(rng.normal(0.0, 0.01))))
        bars.append(TimestampedBar(START + timedelta(days=i), Bar(open_, high, low, close)))
    return bars


def _sorted_shapes(bars, lo: int = 0, hi: int | None = None) -> np.ndarray:
    """The multiset of bar shapes over shape indices [lo, hi), as a canonically-ordered
    array so two multisets can be compared elementwise."""
    ratios = bn.bar_shapes(bars).ratios[lo:hi]
    return ratios[np.lexsort(ratios.T[::-1])]


# ------------------------------------------------ the two claims the study rests on


def test_resampled_path_has_the_same_multiset_of_bar_shapes_at_every_block_size():
    bars = _random_bars(400)
    source = _sorted_shapes(bars)
    for block_size in (1, 5, 20, 60, 137):
        path = bn.resample_bars(bn.bar_shapes(bars), seed=3, block_size=block_size)
        assert len(path) == len(bars)
        # Same shapes, and NOT (except by astronomical accident) the same order.
        assert _sorted_shapes(path) == pytest.approx(source, rel=1e-12)
        if block_size < len(bars) // 2:
            assert [tb.bar.close for tb in path] != [tb.bar.close for tb in bars]


def test_segmented_resampling_keeps_each_segment_multiset_intact():
    """The stronger claim segmentation buys (D130): the measured span's OWN marginal
    distribution is identical on every null path, not just the whole fixture's."""
    bars = _random_bars(400, seed=44)
    shapes = bn.bar_shapes(bars, segment_starts=(120, 260))
    before, middle, after = (
        _sorted_shapes(bars, 0, 120),
        _sorted_shapes(bars, 120, 260),
        _sorted_shapes(bars, 260, None),
    )
    for block_size in (1, 5, 20):
        path = bn.resample_bars(shapes, seed=9, block_size=block_size)
        assert _sorted_shapes(path, 0, 120) == pytest.approx(before, rel=1e-12)
        assert _sorted_shapes(path, 120, 260) == pytest.approx(middle, rel=1e-12)
        assert _sorted_shapes(path, 260, None) == pytest.approx(after, rel=1e-12)
        # ...and therefore every segment boundary close is invariant.
        for boundary in (120, 260):
            assert path[boundary].bar.close == pytest.approx(bars[boundary].bar.close, rel=1e-9)


def test_segment_starts_are_validated():
    bars = _random_bars(100, seed=45)
    with pytest.raises(ValueError, match="strictly increasing"):
        bn.bar_shapes(bars, segment_starts=(50, 20))
    with pytest.raises(ValueError, match="strictly inside"):
        bn.bar_shapes(bars, segment_starts=(0,))
    with pytest.raises(ValueError, match="strictly inside"):
        bn.bar_shapes(bars, segment_starts=(99,))


def test_block_one_shuffle_preserves_buy_and_hold_terminal_wealth_exactly():
    """The controlled-comparison claim (D130): a shuffle changes the sequence and
    nothing else, so close-to-close buy-and-hold earns exactly the same. Asserted to
    floating-point tolerance per D47 — relative, because the quantity is a growth
    factor rather than a cash amount."""
    bars = _random_bars(1200, seed=5)
    original = bars[-1].bar.close / bars[0].bar.close
    for seed in (0, 1, 2, 99):
        path = bn.resample_bars(bn.bar_shapes(bars), seed=seed, block_size=1)
        shuffled = path[-1].bar.close / path[0].bar.close
        assert shuffled == pytest.approx(original, rel=1e-9)
        assert path[0].bar == bars[0].bar  # the anchor bar is never resampled


def test_buy_and_hold_invariance_holds_at_every_block_size_too():
    bars = _random_bars(600, seed=8)
    original = bars[-1].bar.close / bars[0].bar.close
    for block_size in (1, 5, 20, 60):
        path = bn.resample_bars(bn.bar_shapes(bars), seed=17, block_size=block_size)
        assert path[-1].bar.close / path[0].bar.close == pytest.approx(original, rel=1e-9)


def test_intrabar_geometry_survives_resampling():
    """A bar's high must remain its own high. If the resampler scaled o/h/l/c by
    anything other than one common factor, a resampled 'high' could fall below its own
    close — and the strategy's entry level is a rolling max of highs."""
    bars = _random_bars(300, seed=13)
    path = bn.resample_bars(bn.bar_shapes(bars), seed=4, block_size=5)
    for tb in path:
        assert tb.bar.high >= max(tb.bar.open, tb.bar.close)
        assert tb.bar.low <= min(tb.bar.open, tb.bar.close)
        assert tb.bar.low > 0.0


def test_timestamps_and_length_are_untouched():
    bars = _random_bars(250, seed=21)
    path = bn.resample_bars(bn.bar_shapes(bars), seed=6, block_size=20)
    assert [tb.timestamp for tb in path] == [tb.timestamp for tb in bars]


# ------------------------------------------------------------ the block permutation


def test_block_permutation_is_a_bijection_for_every_block_size():
    rng = np.random.default_rng(0)
    for n in (10, 97, 1000):
        for block_size in (1, 3, 7, n - 1):
            index = bn.block_permutation(n, block_size, rng)
            assert index.shape == (n,)
            assert sorted(index.tolist()) == list(range(n))


def test_block_permutation_keeps_blocks_contiguous():
    """The ladder means nothing if the blocks are not runs of consecutive source bars."""
    index = bn.block_permutation(100, 10, np.random.default_rng(2))
    for start in range(0, 100, 10):
        block = index[start : start + 10].tolist()
        assert block == list(range(block[0], block[0] + 10))


def test_block_permutation_at_or_beyond_full_length_is_refused():
    for block_size in (50, 51):
        with pytest.raises(ValueError, match="only one block"):
            bn.block_permutation(50, block_size, np.random.default_rng(0))


# ---------------------------------------------------------- determinism under seed


def test_same_seed_reproduces_the_path_byte_for_byte():
    shapes = bn.bar_shapes(_random_bars(300, seed=31))
    a = bn.resample_bars(shapes, seed=42, block_size=5)
    b = bn.resample_bars(shapes, seed=42, block_size=5)
    assert [tb.bar for tb in a] == [tb.bar for tb in b]


def test_different_seeds_give_genuinely_different_paths():
    shapes = bn.bar_shapes(_random_bars(300, seed=31))
    a = bn.resample_bars(shapes, seed=1, block_size=5)
    b = bn.resample_bars(shapes, seed=2, block_size=5)
    differing = sum(1 for x, y in zip(a, b) if x.bar != y.bar)
    assert differing > len(a) // 2


def test_simulation_seeds_are_deterministic_distinct_and_block_independent():
    seeds = bn.simulation_seeds(7, 500)
    assert seeds == bn.simulation_seeds(7, 500)
    assert len(set(seeds)) == 500
    assert seeds != bn.simulation_seeds(8, 500)
    # The first n seeds of a longer draw are the same seeds — which is what makes a
    # cell reproducible on its own and every cell of the grid paired on identical paths.
    assert bn.simulation_seeds(7, 50) == seeds[:50]


# --------------------------------------------------- degenerate inputs fail loudly


def test_constant_price_is_refused():
    bars = [
        TimestampedBar(START + timedelta(days=i), Bar(100.0, 100.0, 100.0, 100.0)) for i in range(50)
    ]
    with pytest.raises(ValueError, match="single point masquerading"):
        bn.bar_shapes(bars)


def test_perfectly_geometric_price_is_refused():
    """Every bar the same shape means every permutation is the identity — the same
    failure as a constant price, without the constant price."""
    bars = []
    close = 100.0
    for i in range(60):
        bars.append(TimestampedBar(START + timedelta(days=i), Bar(close, close * 1.02, close * 0.99, close * 1.01)))
        close *= 1.01
    with pytest.raises(ValueError, match="single point masquerading"):
        bn.bar_shapes(bars)


def test_too_short_series_is_refused():
    with pytest.raises(ValueError, match="at least 3 bars"):
        bn.bar_shapes(_random_bars(2))


def test_non_positive_price_is_refused():
    bars = _random_bars(20)
    bars[5] = TimestampedBar(bars[5].timestamp, Bar(1.0, 1.0, 0.0, 1.0))
    with pytest.raises(ValueError, match="non-positive"):
        bn.bar_shapes(bars)


def test_non_finite_price_is_refused():
    bars = _random_bars(20)
    bars[5] = TimestampedBar(bars[5].timestamp, Bar(1.0, float("nan"), 1.0, 1.0))
    with pytest.raises(ValueError, match="non-finite"):
        bn.bar_shapes(bars)


# ------------------------------------------------------------ p-values and tails


def _spec(direction: str) -> bn.MetricSpec:
    return bn.MetricSpec("m", direction, "M", "note")


def test_p_value_uses_the_add_one_form_and_never_reports_zero():
    values = np.zeros(99)
    d = bn.summarise_null(values, real=10.0, spec=_spec("high"))
    assert d.p_value == pytest.approx(1.0 / 100.0)
    assert d.percentile == pytest.approx(100.0)


def test_lower_tail_direction_is_not_the_upper_tail_reversed_by_accident():
    values = np.arange(100, dtype=float)
    high = bn.summarise_null(values, real=90.0, spec=_spec("high"))
    low = bn.summarise_null(values, real=90.0, spec=_spec("low"))
    assert high.p_value == pytest.approx(11.0 / 101.0)  # 90..99 are >= 90, plus the +1
    assert low.p_value == pytest.approx(92.0 / 101.0)  # 0..90 are <= 90, plus the +1
    assert high.percentile == pytest.approx(90.5)


def test_monte_carlo_standard_error_is_the_binomial_one_and_shrinks_with_n():
    small = bn.summarise_null(np.arange(200, dtype=float), 190.0, _spec("high"))
    large = bn.summarise_null(np.arange(20_000, dtype=float), 19_000.0, _spec("high"))
    for d in (small, large):
        assert d.p_value_se == pytest.approx(
            math.sqrt(d.p_value * (1 - d.p_value) / d.n_sims), rel=1e-12
        )
    assert small.p_value == pytest.approx(large.p_value, abs=0.01)
    assert large.p_value_se < small.p_value_se / 5


def test_ties_are_counted_at_half_weight_in_the_percentile():
    values = np.array([1.0, 2.0, 2.0, 2.0, 3.0])
    d = bn.summarise_null(values, real=2.0, spec=_spec("high"))
    assert d.percentile == pytest.approx(100.0 * (1 + 1.5) / 5)


def test_unknown_direction_is_refused():
    with pytest.raises(ValueError, match="unknown direction"):
        bn.summarise_null(np.arange(10, dtype=float), 1.0, _spec("sideways"))


def test_every_declared_metric_exists_on_a_null_sample():
    """No false affordances (D48): a MetricSpec naming a field NullSample does not have
    would fail only at report time, on the full grid, after an hour of compute."""
    fields = bn.NullSample.__dataclass_fields__
    for spec in bn.NULL_METRICS:
        assert spec.name in fields
        assert spec.direction in ("high", "low")


# ------------------------------------------------- trade-level bootstrap (test 3)


def test_trade_bootstrap_is_deterministic_under_seed_and_varies_across_seeds():
    returns = [0.4, -0.1, 1.2, -0.05, 0.3, -0.2, 0.9]
    a = bn.trade_bootstrap(returns, seed=0, n_sims=2000)
    assert a == bn.trade_bootstrap(returns, seed=0, n_sims=2000)
    assert a["median"] != bn.trade_bootstrap(returns, seed=1, n_sims=2000)["median"]


def test_trade_bootstrap_actual_terminal_wealth_is_the_product_of_the_returns():
    returns = [0.4, -0.1, 1.2, -0.05]
    out = bn.trade_bootstrap(returns, seed=0, n_sims=500)
    assert out["actual_terminal_wealth"] == pytest.approx(1.4 * 0.9 * 2.2 * 0.95)


def test_trade_bootstrap_refuses_too_few_trades_and_total_wipeouts():
    with pytest.raises(ValueError, match="at least 2 closed trades"):
        bn.trade_bootstrap([0.5], seed=0)
    with pytest.raises(ValueError, match="wipe the account"):
        bn.trade_bootstrap([0.5, -1.0, 0.2], seed=0)


def test_a_single_dominant_trade_shows_up_as_a_wide_bootstrap():
    """The property the concentration numbers are meant to expose: when one trade
    carries the result, resampling drops it often and the terminal wealth distribution
    becomes enormous relative to its median."""
    concentrated = [10.0] + [0.01] * 19
    spread = [0.13] * 20
    a = bn.trade_bootstrap(concentrated, seed=0, n_sims=5000)
    b = bn.trade_bootstrap(spread, seed=0, n_sims=5000)
    assert a["p95"] / a["p05"] > 50 * (b["p95"] / b["p05"])


# ------------------------------------- paired drawdown bootstrap (test 4)


def test_drawdown_from_returns_matches_the_analytics_max_drawdown():
    rng = np.random.default_rng(3)
    returns = rng.normal(0.0005, 0.02, 500)
    navs = 100_000.0 * np.cumprod(1.0 + returns)
    curve = [(START, 100_000.0)] + [
        (START + timedelta(days=i + 1), float(v)) for i, v in enumerate(navs)
    ]
    # Scaled by 100,000, so this one stays a tolerance -- the multiplication is a real
    # float operation the unscaled form does not perform.
    assert bn.returns_max_drawdown(returns) == pytest.approx(max_drawdown(curve), abs=1e-12)


def test_the_vectorised_drawdown_is_bit_identical_to_the_scalar_one():
    """D542: the hot path keeps its own loop, so something has to prove it is the same
    number and not merely a close one.

    `approx` would let a second arithmetic live here indefinitely, which is the defect
    D542 removes everywhere else. Probed on TIE-HEAVY inputs as well as random ones --
    repeated equal moves and runs of zeros are where a rewrite disagrees, and a drawdown
    is a running maximum, so ties are exactly what decides which bar wins.
    """
    rng = np.random.default_rng(11)
    cases = [
        [0.1, -0.1] * 40,
        [0.0] * 20 + [-0.3] + [0.0] * 20,
        [0.2, -0.25, 0.3333333333333333, -0.25] * 10,
        list(np.full(50, 0.01)),
        list(-np.full(50, 0.01)),
    ]
    cases += [list(rng.normal(0.0, 0.03, 200)) for _ in range(40)]
    cases += [list(rng.choice([-0.02, -0.01, 0.0, 0.01, 0.02], 200)) for _ in range(40)]

    for returns in cases:
        vectorised = float(
            bn._max_drawdown_from_returns(np.asarray(returns, dtype=float)[None, :])[0]
        )
        assert bn.returns_max_drawdown(returns) == vectorised


def test_paired_drawdown_bootstrap_against_itself_is_degenerate_at_zero():
    """The pairing check, in the same shape D120 used for the Sharpe version: a series
    bootstrapped against ITSELF must give exactly zero every time. It only does if one
    index vector is applied to both series."""
    rng = np.random.default_rng(9)
    returns = rng.normal(0.0004, 0.02, 800).tolist()
    out = bn.drawdown_difference_bootstrap(returns, returns, seed=0, n_sims=400, block_size=20)
    assert out["p05"] == 0.0 and out["p95"] == 0.0 and out["mean_difference"] == 0.0
    assert out["prob_strategy_shallower"] == 0.0
    assert out["observed_difference"] == 0.0


def test_paired_drawdown_bootstrap_is_deterministic_under_seed():
    rng = np.random.default_rng(10)
    s = rng.normal(0.0006, 0.012, 600).tolist()
    b = rng.normal(0.0009, 0.030, 600).tolist()
    a1 = bn.drawdown_difference_bootstrap(s, b, seed=4, n_sims=500)
    a2 = bn.drawdown_difference_bootstrap(s, b, seed=4, n_sims=500)
    assert a1 == a2
    assert a1["prob_strategy_shallower"] != bn.drawdown_difference_bootstrap(
        s, b, seed=5, n_sims=500
    )["prob_strategy_shallower"]


def test_paired_drawdown_bootstrap_chunking_cannot_change_the_answer():
    rng = np.random.default_rng(12)
    s = rng.normal(0.0006, 0.012, 400).tolist()
    b = rng.normal(0.0009, 0.030, 400).tolist()
    whole = bn.drawdown_difference_bootstrap(s, b, seed=1, n_sims=600, chunk_size=600)
    chunked = bn.drawdown_difference_bootstrap(s, b, seed=1, n_sims=600, chunk_size=97)
    assert whole["observed_difference"] == chunked["observed_difference"]
    # Different chunking draws the same numbers in a different grouping, so the
    # distribution — not the individual draw — is what must agree.
    assert whole["prob_strategy_shallower"] == pytest.approx(
        chunked["prob_strategy_shallower"], abs=0.06
    )


def test_paired_drawdown_bootstrap_detects_a_genuinely_calmer_series():
    rng = np.random.default_rng(14)
    calm = (rng.normal(0.0005, 0.006, 900)).tolist()
    wild = (rng.normal(0.0005, 0.040, 900)).tolist()
    out = bn.drawdown_difference_bootstrap(calm, wild, seed=0, n_sims=1000)
    assert out["prob_strategy_shallower"] > 0.99
    assert out["prob_se"] < 0.01


def test_paired_drawdown_bootstrap_refuses_mismatched_and_short_inputs():
    with pytest.raises(ValueError, match="equal lengths"):
        bn.drawdown_difference_bootstrap([0.1] * 50, [0.1] * 51, seed=0)
    with pytest.raises(ValueError, match="more than 20 observations"):
        bn.drawdown_difference_bootstrap([0.01] * 20, [0.01] * 20, seed=0)


# ------------------------------------------ end to end on a small synthetic series


def _small_study() -> bs.BreakoutStudyConfig:
    return bs.BreakoutStudyConfig(train_size=80, test_size=20, step=20)


def _small_variant() -> bs.Variant:
    return bs.Variant(
        "null_test",
        "plateau",
        fixed_config=bs.breakout_config(
            n_entry=10, n_exit=5, weight_source={"type": "fixed_weight", "fraction": 1.0}
        ),
    )


def _trending_bars(n: int = 600, seed: int = 77, rho: float = 0.45) -> list[TimestampedBar]:
    """A series with genuine momentum — AR(1) log returns — so the trend follower
    actually makes money on it. A pure random walk with drift does not reliably reward
    a breakout rule, which is the whole point of the study this module tests; the
    concentration statistics are undefined on a losing run and say so."""
    rng = np.random.default_rng(seed)
    shocks = rng.normal(0.0006, 0.018, n)
    log_returns = np.empty(n)
    log_returns[0] = shocks[0]
    for i in range(1, n):
        log_returns[i] = rho * log_returns[i - 1] + shocks[i]
    closes = 100.0 * np.exp(np.cumsum(log_returns))
    bars = []
    previous = 100.0
    for i, close in enumerate(map(float, closes)):
        open_ = previous * float(np.exp(rng.normal(0.0, 0.004)))
        high = max(open_, close) * (1.0 + abs(float(rng.normal(0.0, 0.008))))
        low = min(open_, close) * (1.0 - abs(float(rng.normal(0.0, 0.008))))
        bars.append(TimestampedBar(START + timedelta(days=i), Bar(open_, high, low, close)))
        previous = close
    return bars


TEST_TIER = bs.CostTier("test_25bp", 25.0, "taker")


def test_trade_nav_returns_telescope_into_the_reported_total_return():
    """The identity that makes the trade bootstrap a bootstrap over terminal wealth:
    the strategy is flat between episodes and idle cash earns nothing, so the product
    of the per-episode NAV multiples IS the total return factor."""
    result = bs.run_variant(_trending_bars(), "SYN", _small_variant(), TEST_TIER, _small_study())
    returns = bn.trade_nav_returns(result)
    assert len(returns) == len(result.episodes) >= 2
    product = math.prod(1.0 + r for r in returns)
    assert product == pytest.approx(1.0 + result.total_return, rel=1e-12)


def test_trade_concentration_shares_are_consistent_and_ordered():
    result = bs.run_variant(_trending_bars(), "SYN", _small_variant(), TEST_TIER, _small_study())
    c = bn.trade_concentration(result)
    assert c.n_closed >= 5
    assert c.total_net_pnl > 0
    # Shares are monotone in N but NOT bounded by 1: when the losing trades subtract
    # from the total, the winners' share of the net exceeds 100%, and saying so is the
    # finding rather than a bug to clamp away.
    assert 0 < c.top_pnl_shares[1] <= c.top_pnl_shares[3] <= c.top_pnl_shares[5]
    assert 0 < c.top_log_shares[1] <= c.top_log_shares[3] <= c.top_log_shares[5]
    assert c.n_winners < c.n_closed  # this fixture really does contain losers
    assert c.best_trade_return >= c.worst_trade_return


def test_trade_concentration_reports_not_a_number_rather_than_a_wrong_number():
    """A losing run has no meaningful "share of total P&L" — the denominator is
    negative, and a share of a negative total is a sign trap, not information (D36's
    report-only-what-the-sample-supports rule applied to a ratio)."""
    result = bs.run_variant(
        _random_bars(600, seed=3, drift=-0.003), "SYN", _small_variant(), TEST_TIER, _small_study()
    )
    c = bn.trade_concentration(result)
    assert c.total_net_pnl < 0
    assert all(math.isnan(v) for v in c.top_pnl_shares.values())


def test_study_bar_shapes_segments_at_the_oos_start_and_trims_the_unused_tail():
    bars = _trending_bars(700)
    study = _small_study()
    oos_start, oos_end = bn.study_span(bars, study)
    trimmed, shapes = bn.study_bar_shapes(bars, study)
    assert len(trimmed) == oos_end
    assert shapes.segment_starts == (oos_start,)
    # Trimming must be a no-op for the strategy: the study never reads past oos_end.
    full = bs.run_variant(bars, "SYN", _small_variant(), TEST_TIER, study)
    cut = bs.run_variant(trimmed, "SYN", _small_variant(), TEST_TIER, study)
    assert cut.total_return == full.total_return
    assert cut.oos_equity == full.oos_equity


def test_null_paths_leave_the_measured_span_buy_and_hold_exactly_unchanged():
    """The controlled-comparison claim as the study actually uses it: over the OOS span
    itself, close-to-close buy-and-hold is identical on every null path (D47's
    tolerance, relative)."""
    bars, study = _trending_bars(700), _small_study()
    oos_start, oos_end = bn.study_span(bars, study)
    trimmed, shapes = bn.study_bar_shapes(bars, study)
    real = trimmed[oos_end - 1].bar.close / trimmed[oos_start].bar.close
    for block_size in (1, 5, 20):
        for seed in (0, 1, 2):
            path = bn.resample_bars(shapes, seed=seed, block_size=block_size)
            assert path[oos_end - 1].bar.close / path[oos_start].bar.close == pytest.approx(
                real, rel=1e-9
            )


def test_path_null_runs_the_real_strategy_and_is_reproducible():
    bars, study, variant = _trending_bars(), _small_study(), _small_variant()
    a = bn.path_null(bars, "SYN", variant, TEST_TIER, study, seed=0, n_sims=6, block_size=1)
    b = bn.path_null(bars, "SYN", variant, TEST_TIER, study, seed=0, n_sims=6, block_size=1)
    assert a.samples == b.samples
    assert a.real == b.real
    c = bn.path_null(bars, "SYN", variant, TEST_TIER, study, seed=1, n_sims=6, block_size=1)
    assert c.samples != a.samples
    for spec in bn.NULL_METRICS:
        d = a.distribution(spec)
        assert 0.0 <= d.percentile <= 100.0
        assert 0.0 < d.p_value <= 1.0


def test_path_null_real_reference_matches_a_direct_study_run():
    """The null is only a null OF the published result if its reference IS the
    published result — same call, same numbers."""
    bars, study, variant = _trending_bars(), _small_study(), _small_variant()
    result = bn.path_null(bars, "SYN", variant, TEST_TIER, study, seed=0, n_sims=2)
    direct = bs.run_variant(bars, "SYN", variant, TEST_TIER, study)
    assert result.real.total_return == direct.total_return
    assert result.real.sharpe_annual == direct.sharpe_annual(study)
    assert result.real.max_drawdown == direct.max_drawdown
    assert result.real.n_trades == float(direct.diagnostics.n_closed_trades)


def test_the_study_benchmark_barely_moves_across_null_paths():
    """D115's benchmark buys at the second OOS bar's OPEN, so it is not EXACTLY
    invariant — that bar's open ratio is resampled. This pins the honest version the
    report states: its dispersion is a rounding error next to the strategy's."""
    bars, study, variant = _trending_bars(), _small_study(), _small_variant()
    result = bn.path_null(bars, "SYN", variant, TEST_TIER, study, seed=0, n_sims=25, block_size=1)
    benchmark = result.values("benchmark_total_return")
    strategy = result.values("total_return")
    relative_spread = float(np.std(benchmark)) / abs(1.0 + result.real.benchmark_total_return)
    assert relative_spread < 0.03
    assert float(np.std(benchmark)) < float(np.std(strategy))
