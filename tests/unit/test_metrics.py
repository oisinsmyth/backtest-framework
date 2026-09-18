"""Step 9 metric gates (D37, D49, D80)."""

import math

import numpy as np
import pytest

from backtest_framework.analytics.metrics import (
    excess_sharpe,
    max_drawdown,
    max_drawdown_from_returns,
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
