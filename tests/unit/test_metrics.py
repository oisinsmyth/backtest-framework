"""Step 9 metric gates (D37, D49, D80)."""

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
    # THE D49 gate: a flat (constant-zero) return series at rf=4% must come out
    # negative — this is what catches a silent rf=0 shortcut. Zero variance with
    # negative excess mean -> -inf by the stated convention (D80).
    result = sharpe([0.0] * 252, rf_annual=0.04, periods_per_year=252)
    assert result < 0
    assert result == -math.inf


def test_sharpe_requires_rf_and_periods_positionally():
    # No defaults, by design (D49/D80) — calling without them is a TypeError.
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
    assert realised_beta(spy, spy) == pytest.approx(1.0, rel=TOLERANCE)  # D37 gate


def test_beta_of_constant_cash_series_is_zero():
    rng = np.random.default_rng(11)
    spy = rng.normal(0.0003, 0.011, 500)
    cash = [0.0001] * 500  # constant per-period return
    assert realised_beta(cash, spy) == pytest.approx(0.0, abs=1e-12)  # D37 gate


def test_beta_against_zero_variance_benchmark_fails_loudly():
    with pytest.raises(ValueError, match="zero variance"):
        realised_beta([0.01, -0.01, 0.02], [0.001, 0.001, 0.001])


def test_beta_length_mismatch_fails_loudly():
    with pytest.raises(ValueError, match="length mismatch"):
        realised_beta([0.01, -0.01], [0.001])


def test_max_drawdown_relocated_intact():
    curve = [(None, 100.0), (None, 110.0), (None, 99.0), (None, 105.0)]
    assert max_drawdown(curve) == pytest.approx(0.1, rel=TOLERANCE)


def test_max_drawdown_refuses_a_curve_that_was_never_above_water():
    """A drawdown is a fraction OF a peak, and there is no peak to take a fraction of.

    The `peak > 0` gate is right to avoid the division; it used to fall through and return
    0.0, which both renderers format as `{dd:.2%}` — so the undefined case printed as a
    flat, entirely plausible `0.00%`, indistinguishable from a genuinely drawdown-free run.

    Unreachable through `run_backtest`, where every equity curve starts at a positive
    `starting_cash`, which is why changing it moves no published number.
    """
    with pytest.raises(ValueError, match="never positive"):
        max_drawdown([(None, -10.0), (None, -100.0)])

    # The first point being non-positive is fine as long as the curve recovers: the gate is
    # about the RUNNING peak, not the opening value.
    assert max_drawdown([(None, -10.0), (None, 100.0), (None, 50.0)]) == pytest.approx(0.5, rel=TOLERANCE)

    # An empty curve keeps its old answer -- there is nothing to be undefined about, and
    # tests/integration/test_cost_sweep.py pins a monotone curve at 0.0.
    assert max_drawdown([]) == 0.0


# ---------------------------------------------------------------- D542: one arithmetic


def _tie_heavy_and_random_returns():
    """Ties are where rewrites disagree, so every equality claim below is probed on them."""
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
    invisible, because the curve would start AT its own trough."""
    assert max_drawdown_from_returns([-0.2]) == pytest.approx(0.2, rel=TOLERANCE)
    assert max_drawdown_from_returns([-0.2, 0.25]) == pytest.approx(0.2, rel=TOLERANCE)
    assert max_drawdown_from_returns([]) == 0.0


def test_max_drawdown_from_returns_is_bit_identical_to_the_curve_form():
    """Not `approx`. The whole point of the delegation is that there is ONE arithmetic;
    a tolerance here would hide a second one, which is the defect D542 exists to remove."""
    for returns in _tie_heavy_and_random_returns():
        curve = [1.0]
        nav = 1.0
        for r in returns:
            nav *= 1.0 + r
            curve.append(nav)
        assert max_drawdown_from_returns(returns) == max_drawdown(list(enumerate(curve)))


def test_the_reordered_drawdown_form_really_does_disagree():
    """`1.0 - nav/peak` is what research/breakdown_study computed; `(peak - nav)/peak` is
    what this module computes. Algebraically equal, NOT bit-equal.

    This test exists because the delegation moves a published number in
    `data/breakdown_study_summary.json`, and a moved number with no test naming the reason
    is indistinguishable from a typo. It is also the anti-tautology: if some future numpy
    or CPython makes the two forms agree, this fails and the D542 record needs amending
    rather than the code silently gaining a property it never had.
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
        "the reordered form no longer disagrees at the ULP; D542's recorded reason for "
        "moving breakdown_study's numbers no longer holds and the record needs amending"
    )


def test_excess_sharpe_charges_rf_only_on_the_exposed_fraction():
    """D219: 'it lowers both, and it lowers buy-and-hold roughly twice as much'."""
    returns = [0.01, -0.005, 0.008, 0.002, -0.001] * 20
    always_in = [1.0] * len(returns)
    half_in = [1.0, 0.0] * (len(returns) // 2)

    full = excess_sharpe(returns, always_in, 0.04, 252.0, basis="simple")
    half = excess_sharpe(returns, half_in, 0.04, 252.0, basis="simple")
    zero = excess_sharpe(returns, [0.0] * len(returns), 0.04, 252.0, basis="simple")

    # At zero exposure nothing is charged, so it must equal the rf=0 Sharpe exactly.
    assert zero == sharpe(returns, 0.0, 252.0)
    # And the more exposed book is charged more, so it scores lower.
    assert full < half < zero


def test_excess_sharpe_requires_the_return_basis():
    returns = [0.01, -0.005, 0.008] * 10
    exposure = [1.0] * len(returns)
    with pytest.raises(TypeError):
        excess_sharpe(returns, exposure, 0.04, 252.0)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="basis must be"):
        excess_sharpe(returns, exposure, 0.04, 252.0, basis="geometric")
    # The two bases are genuinely different constants, not a spelling choice.
    assert excess_sharpe(returns, exposure, 0.04, 252.0, basis="log") != excess_sharpe(
        returns, exposure, 0.04, 252.0, basis="simple"
    )


def test_excess_sharpe_reproduces_the_scripts_copy_bit_for_bit():
    """The two `scripts/` bodies it replaces, restated here so adoption is provably free.

    `run_filter_search.py:279` / `run_jerk_rung.py:123`: rf de-annualised in LOG space,
    charged against the exposed fraction, ddof=1, annualised by sqrt(ppy).
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


def test_excess_sharpe_length_mismatch_fails_loudly():
    with pytest.raises(ValueError, match="length mismatch"):
        excess_sharpe([0.01, -0.01], [1.0], 0.04, 252.0, basis="log")


def test_curve_sharpe_zero_rf_reproduces_the_body_it_replaced_bit_for_bit():
    """Three inline copies became one function, and not one published Sharpe may move.

    The body, restated: `(fmean(rets) / stdev(rets)) * sqrt(ppy)`, with `len < 3 -> 0.0`
    and `sd <= 0 -> 0.0`. Exact equality, because this is the estimator behind every
    number in TERRAIN_RESULTS, STRUCTURE_RESULTS and eight committed summaries.
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
    """The measured reason `curve_sharpe_zero_rf` exists instead of `sharpe(r, 0.0, ppy)`.

    `statistics.fmean` sums exactly (`math.fsum`); numpy sums pairwise. Same definition,
    different rounding. Repointing the research call sites at `sharpe` would move every
    published terrain and structure Sharpe for no gain, and CLAUDE.md's rule is that a
    rewrite may hoist or skip but never reorder a float sum.

    The anti-tautology: if the two ever agree everywhere, this fails and D542's recorded
    reason for keeping two kernels no longer holds.
    """
    rng = np.random.default_rng(2)
    series = [list(rng.normal(0.0, 0.02, 500)) for _ in range(200)]
    gaps = [
        abs(curve_sharpe_zero_rf(s, 365.0) - sharpe(s, 0.0, 365.0))
        for s in series
    ]
    disagreements = sum(1 for g in gaps if g > 0.0)
    assert disagreements > 0, (
        "the exact-summation and pairwise kernels no longer differ; D542's reason for "
        "keeping both no longer holds and the record needs amending"
    )
    # But they are the same DEFINITION, so the gap must stay at rounding scale.
    assert max(gaps) < 1e-12, f"the two kernels differ by {max(gaps):.3e}, which is not rounding"


def test_builtin_sum_is_compensated_and_a_manual_loop_is_not():
    """Why two ATR implementations that read as identical were not the same number (D542).

    `research/trade_diagnostics._atr` used `sum(...)`; `research/breakdown_study._atr_at`
    accumulated with `total += ...`. Same terms, same order, different float — because
    **CPython 3.12 gave `sum()` Neumaier compensated summation for floats** and a manual
    loop gets plain accumulation. Neither docstring mentioned it, because neither author
    could have: the difference arrived with the interpreter.

    Pinned here because it is a REPOSITORY-WIDE class, not one function's quirk. Any
    optimisation that replaces `sum(xs)` with a loop — or the reverse — moves numbers, and
    CLAUDE.md's rule against reordering a float sum now has a second edge nobody wrote
    down. The classic 1e16 case makes it visible without depending on a random draw.
    """
    terms = [1e16, 1.0, -1e16, 1.0]
    total = 0.0
    for t in terms:
        total += t
    # Plain accumulation loses the first 1.0 when 1e16 absorbs it, and keeps the second.
    assert total == 1.0
    assert sum(terms) == 2.0, "builtin sum is no longer compensated; D542's ATR note is stale"
    assert sum(terms) != total


def test_mid_rank_percentile_splits_ties_in_half():
    """The stated reason the convention exists, from `breakout_nulls.summarise_null`: on a
    discrete statistic, counting ties as strictly-below flatters whichever side happens to
    be integer-equal."""
    assert mid_rank_percentile([1.0, 2.0, 3.0, 4.0], 2.5) == 50.0
    # Four draws equal to the observation: strictly-below would say 0, this says 50.
    assert mid_rank_percentile([7.0, 7.0, 7.0, 7.0], 7.0) == 50.0
    assert mid_rank_percentile([1.0, 7.0, 7.0, 9.0], 7.0) == 50.0
    assert mid_rank_percentile([], 0.0) == 0.0
    assert mid_rank_percentile([1.0, 2.0], 99.0) == 100.0


def test_mid_rank_and_strictly_below_are_the_same_number_when_nothing_ties():
    """D542's P3, in the small: the two conventions differ ONLY by the tie term and by a
    factor of 100. That is what makes the `breakdown_study` re-derivation checkable — a
    departure from 100x means the draws tie, which is itself a finding about a statistic
    assumed continuous."""
    rng = np.random.default_rng(3)
    for _ in range(50):
        draws = list(rng.normal(0.0, 1.0, 400))
        observed = float(rng.normal())
        strictly_below = float(np.mean(np.asarray(draws) < observed))
        assert mid_rank_percentile(draws, observed) == pytest.approx(
            100.0 * strictly_below, abs=1e-9
        )


def test_the_three_collapsed_percentile_copies_still_agree():
    """`terrain_strategies.NullComparison`, `terrain_field_nulls.FieldNullComparison` and
    the inline form in `breakout_nulls.summarise_null` all claimed in a docstring to match
    each other. Now they call one function, and this is the claim as a check."""
    from backtest_framework.research.terrain_field_nulls import FieldNullComparison
    from backtest_framework.research.terrain_strategies import NullComparison

    rng = np.random.default_rng(4)
    draws = list(rng.normal(0.0, 1.0, 200)) + [0.5, 0.5, 0.5]  # deliberate ties
    for observed in (0.5, -2.0, 0.0, 99.0):
        want = mid_rank_percentile(draws, observed)
        assert NullComparison.percentile(None, draws, observed) == want  # type: ignore[arg-type]
        assert FieldNullComparison.percentile(None, draws, observed) == want  # type: ignore[arg-type]
        # the inline form summarise_null uses, restated
        v = np.asarray(draws)
        inline = 100.0 * (float(np.sum(v < observed)) + 0.5 * float(np.sum(v == observed))) / v.size
        assert inline == want
