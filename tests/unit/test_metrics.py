"""Unit tests for the performance metrics: Sharpe, Sortino, beta, drawdown, percentiles."""

import math

import numpy as np
import pytest

from backtest_framework.analytics.metrics import (
    curve_sharpe_zero_rf,
    excess_sharpe,
    max_drawdown,
    max_drawdown_from_returns,
    mid_rank_percentile,
    realised_beta,
    sharpe,
    sortino,
)

TOLERANCE = 1e-9


def test_sharpe_with_rf_4pct_on_flat_returns_is_negative():
    # A flat (constant-zero) return series at rf=4% must come out negative, which catches an
    # implementation that ignores rf. Zero variance with a negative excess mean gives -inf
    # by convention.
    result = sharpe([0.0] * 252, rf_annual=0.04, periods_per_year=252)
    assert result < 0
    assert result == -math.inf


def test_sharpe_requires_rf_and_periods_positionally():
    # rf and periods have no defaults, so omitting them is a TypeError.
    with pytest.raises(TypeError):
        sharpe([0.01, -0.02, 0.005])  # type: ignore[call-arg]


def test_sharpe_hand_value():
    # mean=0.001, sample std known; rf=0 -> excess == returns.
    r = [0.01, -0.008, 0.002, 0.0, 0.001]
    mu = np.mean(r)
    sd = np.std(r, ddof=1)
    expected = mu / sd * math.sqrt(252)
    assert sharpe(r, rf_annual=0.0, periods_per_year=252) == pytest.approx(expected, rel=TOLERANCE)


def test_sortino_flat_series_with_rf_is_negative_and_finite():
    # Flat series at rf=4%: every excess return is -rf_period (a constant loss), so
    # downside deviation is positive and sortino is negative but finite.
    result = sortino([0.0] * 252, rf_annual=0.04, periods_per_year=252)
    assert result < 0
    assert math.isfinite(result)


def test_sortino_no_downside_is_positive_infinity():
    assert sortino([0.01, 0.02, 0.015], rf_annual=0.0, periods_per_year=252) == math.inf


def test_beta_of_series_vs_itself_is_one():
    rng = np.random.default_rng(11)
    spy = rng.normal(0.0003, 0.011, 500)
    assert realised_beta(spy, spy) == pytest.approx(1.0, rel=TOLERANCE)


def test_beta_of_constant_cash_series_is_zero():
    rng = np.random.default_rng(11)
    spy = rng.normal(0.0003, 0.011, 500)
    cash = [0.0001] * 500  # constant per-period return
    assert realised_beta(cash, spy) == pytest.approx(0.0, abs=1e-12)


def test_beta_against_zero_variance_benchmark_raises():
    with pytest.raises(ValueError, match="zero variance"):
        realised_beta([0.01, -0.01, 0.02], [0.001, 0.001, 0.001])


def test_beta_length_mismatch_raises():
    with pytest.raises(ValueError, match="length mismatch"):
        realised_beta([0.01, -0.01], [0.001])


def test_max_drawdown_relocated_intact():
    curve = [(None, 100.0), (None, 110.0), (None, 99.0), (None, 105.0)]
    assert max_drawdown(curve) == pytest.approx(0.1, rel=TOLERANCE)


def test_max_drawdown_refuses_a_curve_that_was_never_above_water():
    """A curve with no positive peak raises, since drawdown is a fraction of the peak.

    Returning 0.0 instead would display as `0.00%`, the same as a run with no drawdown.
    `run_backtest` cannot produce such a curve, because every equity curve starts at a
    positive `starting_cash`.
    """
    with pytest.raises(ValueError, match="never positive"):
        max_drawdown([(None, -10.0), (None, -100.0)])

    # A non-positive first point is accepted if the curve later has a positive peak: the
    # check is on the running peak, not the opening value.
    assert max_drawdown([(None, -10.0), (None, 100.0), (None, 50.0)]) == pytest.approx(0.5, rel=TOLERANCE)

    # An empty curve returns 0.0.
    assert max_drawdown([]) == 0.0


# ------------------------------------------------- bit-exact arithmetic and rounding


def _tie_heavy_and_random_returns():
    """Yield tie-heavy and random return series for the equality tests below.

    Two implementations of the same formula are most likely to disagree on ties."""
    rng = np.random.default_rng(1)
    yield [0.1, -0.1] * 40
    yield [0.0] * 20 + [-0.3] + [0.0] * 20
    yield [0.2, -0.25, 0.3333333333333333, -0.25] * 10
    yield list(np.full(50, 0.01))
    yield list(-np.full(50, 0.01))
    for _ in range(60):
        yield list(rng.normal(0.0, 0.03, 200))
    for _ in range(60):
        yield list(rng.choice([-0.02, -0.01, 0.0, 0.01, 0.02], 200))


def test_max_drawdown_from_returns_prepends_the_opening_point():
    """The implied curve is [1.0, *cumprod]. Without the leading 1.0 an opening loss is
    invisible, because the curve would start at its own trough."""
    assert max_drawdown_from_returns([-0.2]) == pytest.approx(0.2, rel=TOLERANCE)
    assert max_drawdown_from_returns([-0.2, 0.25]) == pytest.approx(0.2, rel=TOLERANCE)
    assert max_drawdown_from_returns([]) == 0.0


def test_max_drawdown_from_returns_is_bit_identical_to_the_curve_form():
    """The returns form equals the curve form with `==`.

    The returns form delegates to the curve form, so the results should match bit for bit; a
    tolerance would not detect a second, separate implementation."""
    for returns in _tie_heavy_and_random_returns():
        curve = [1.0]
        nav = 1.0
        for r in returns:
            nav *= 1.0 + r
            curve.append(nav)
        assert max_drawdown_from_returns(returns) == max_drawdown(list(enumerate(curve)))


def test_the_reordered_drawdown_form_disagrees():
    """`1.0 - nav/peak` and `(peak - nav)/peak` (the module's form) are algebraically equal
    but not bit-equal.

    Switching from one form to the other moves drawdowns in the last bit. If a future numpy
    or CPython makes the two forms agree, this test fails and this docstring should be
    revised.
    """
    rng = np.random.default_rng(0)
    disagreements = 0
    probed = 0
    for returns in (list(rng.normal(0.0, 0.03, 200)) for _ in range(200)):
        peak, nav, worst = 1.0, 1.0, 0.0
        for r in returns:
            nav *= 1.0 + r
            peak = max(peak, nav)
            worst = max(worst, 1.0 - nav / peak)
        probed += 1
        theirs, ours = worst, max_drawdown_from_returns(returns)
        assert theirs == pytest.approx(ours, abs=1e-15), "the two must stay algebraically equal"
        disagreements += theirs != ours
    assert probed == 200
    assert disagreements > 0, (
        "the reordered form no longer disagrees at the ULP; the note in this test's "
        "docstring no longer holds and should be revised"
    )


def test_excess_sharpe_charges_rf_only_on_the_exposed_fraction():
    """Charging rf lowers every book's Sharpe, and lowers a fully exposed book the most."""
    returns = [0.01, -0.005, 0.008, 0.002, -0.001] * 20
    always_in = [1.0] * len(returns)
    half_in = [1.0, 0.0] * (len(returns) // 2)

    full = excess_sharpe(returns, always_in, 0.04, 252.0, basis="simple")
    half = excess_sharpe(returns, half_in, 0.04, 252.0, basis="simple")
    zero = excess_sharpe(returns, [0.0] * len(returns), 0.04, 252.0, basis="simple")

    # At zero exposure nothing is charged, so the result equals the rf=0 Sharpe exactly.
    assert zero == sharpe(returns, 0.0, 252.0)
    # The more exposed book is charged more, so it scores lower.
    assert full < half < zero


def test_excess_sharpe_requires_the_return_basis():
    returns = [0.01, -0.005, 0.008] * 10
    exposure = [1.0] * len(returns)
    with pytest.raises(TypeError):
        excess_sharpe(returns, exposure, 0.04, 252.0)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="basis must be"):
        excess_sharpe(returns, exposure, 0.04, 252.0, basis="geometric")
    # The two bases de-annualise rf differently and give different results.
    assert excess_sharpe(returns, exposure, 0.04, 252.0, basis="log") != excess_sharpe(
        returns, exposure, 0.04, 252.0, basis="simple"
    )


def test_excess_sharpe_reproduces_the_reference_formula_bit_for_bit():
    """The log basis matches an inline restatement of the formula with `==`.

    rf is de-annualised in log space and charged against the exposed fraction; the standard
    deviation uses ddof=1; the ratio is annualised by sqrt(ppy).
    """
    rng = np.random.default_rng(7)
    for _ in range(50):
        port = rng.normal(0.0, 0.01, 300)
        exposure = rng.random(300)
        rf_per_bar = math.log1p(0.04) / 252.0
        ex = port - exposure * rf_per_bar
        sd = float(np.std(ex, ddof=1))
        theirs = float(np.mean(ex)) / sd * math.sqrt(252.0)
        assert excess_sharpe(port, exposure, 0.04, 252.0, basis="log") == theirs


def test_excess_sharpe_length_mismatch_raises():
    with pytest.raises(ValueError, match="length mismatch"):
        excess_sharpe([0.01, -0.01], [1.0], 0.04, 252.0, basis="log")


def test_curve_sharpe_zero_rf_reproduces_the_body_it_replaced_bit_for_bit():
    """The function matches its reference formula with `==`.

    The formula is `(fmean(rets) / stdev(rets)) * sqrt(ppy)`, with `len < 3 -> 0.0` and
    `sd <= 0 -> 0.0`. The comparison is exact because any change in rounding would move every
    Sharpe computed with it.
    """
    import statistics

    rng = np.random.default_rng(9)
    cases = [
        [0.01, -0.01] * 40,
        [0.0] * 20 + [0.3] + [0.0] * 20,
        [0.002] * 3 + [-0.002] * 3,
        [0.01, 0.01],  # len < 3
        [0.01] * 10,  # sd == 0
        [],
    ]
    cases += [list(rng.normal(0.0, 0.02, 500)) for _ in range(60)]
    for rets in cases:
        if len(rets) < 3:
            want = 0.0
        else:
            sd = statistics.stdev(rets)
            want = 0.0 if sd <= 0.0 else (statistics.fmean(rets) / sd) * math.sqrt(365.0)
        assert curve_sharpe_zero_rf(rets, 365.0) == want


def test_the_two_zero_rf_kernels_are_not_the_same_float():
    """`curve_sharpe_zero_rf` and `sharpe(r, 0.0, ppy)` agree only to rounding.

    `statistics.fmean` sums exactly (`math.fsum`) while numpy sums pairwise, so the two give
    the same definition with different rounding. Both are kept because replacing one with the
    other would move results in the last bits.

    If the two ever agree on every draw, this test fails and keeping both is no longer needed.
    """
    rng = np.random.default_rng(2)
    series = [list(rng.normal(0.0, 0.02, 500)) for _ in range(200)]
    gaps = [
        abs(curve_sharpe_zero_rf(s, 365.0) - sharpe(s, 0.0, 365.0))
        for s in series
    ]
    disagreements = sum(1 for g in gaps if g > 0.0)
    assert disagreements > 0, (
        "the exact-summation and pairwise kernels no longer differ; the reason for "
        "keeping both no longer holds"
    )
    # They share a definition, so the gap stays at rounding scale.
    assert max(gaps) < 1e-12, f"the two kernels differ by {max(gaps):.3e}, which is not rounding"


def test_builtin_sum_is_compensated_and_a_manual_loop_is_not():
    """Builtin `sum()` and a manual `total += ...` loop give different floats.

    Since CPython 3.12, `sum()` uses Neumaier compensated summation for floats, while a
    manual loop accumulates plainly, so the same terms in the same order can give different
    results. Replacing `sum(xs)` with a loop, or the reverse, can change numbers anywhere in
    the codebase. The 1e16 case shows the difference without a random draw.
    """
    terms = [1e16, 1.0, -1e16, 1.0]
    total = 0.0
    for t in terms:
        total += t
    # Plain accumulation loses the first 1.0 when 1e16 absorbs it, and keeps the second.
    assert total == 1.0
    assert sum(terms) == 2.0, "builtin sum is no longer compensated; this test's note is stale"
    assert sum(terms) != total


def test_mid_rank_percentile_splits_ties_in_half():
    """Mid-rank counts half of each tie.

    On a discrete statistic, counting only draws strictly below biases the percentile
    whenever the observation equals some of the draws."""
    assert mid_rank_percentile([1.0, 2.0, 3.0, 4.0], 2.5) == 50.0
    # Four draws equal to the observation: strictly-below would say 0, this says 50.
    assert mid_rank_percentile([7.0, 7.0, 7.0, 7.0], 7.0) == 50.0
    assert mid_rank_percentile([1.0, 7.0, 7.0, 9.0], 7.0) == 50.0
    assert mid_rank_percentile([], 0.0) == 0.0
    assert mid_rank_percentile([1.0, 2.0], 99.0) == 100.0


def test_mid_rank_and_strictly_below_are_the_same_number_when_nothing_ties():
    """Without ties, the mid-rank percentile is 100 times the strictly-below fraction.

    The two conventions differ only by the tie term and the factor of 100, so any other
    difference means the draws contain ties."""
    rng = np.random.default_rng(3)
    for _ in range(50):
        draws = list(rng.normal(0.0, 1.0, 400))
        observed = float(rng.normal())
        strictly_below = float(np.mean(np.asarray(draws) < observed))
        assert mid_rank_percentile(draws, observed) == pytest.approx(
            100.0 * strictly_below, abs=1e-9
        )
