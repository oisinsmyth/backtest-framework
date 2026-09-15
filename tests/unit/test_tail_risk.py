"""Step 9 tail-risk gates (D36, D81)."""

import numpy as np

from backtest_framework.analytics.tail_risk import minimum_observations, var_cvar


def test_100_bar_series_reports_insufficient_data_not_a_number():
    # THE D36 gate, verbatim: 100 bars at 95% -> "insufficient data", never a value.
    rng = np.random.default_rng(3)
    result = var_cvar(rng.normal(0, 0.01, 100), confidence=0.95)

    assert not result.sufficient
    assert result.var is None and result.cvar is None
    assert "insufficient data" in result.insufficient_reason
    assert "need >=600" in result.insufficient_reason  # the minimum-n arithmetic is IN the message


def test_gating_threshold_is_30_tail_observations():
    assert minimum_observations(0.95) == 600  # 30 / 0.05
    assert minimum_observations(0.99) == 3000  # 30 / 0.01
    # D36's own complaint case — 500 daily points at 95% — is ALSO insufficient
    # under this policy, deliberately stricter than the gate requires (D81).
    rng = np.random.default_rng(3)
    assert not var_cvar(rng.normal(0, 0.01, 500), confidence=0.95).sufficient


def test_sufficient_sample_reports_sane_values():
    rng = np.random.default_rng(3)
    result = var_cvar(rng.normal(0.0, 0.01, 2000), confidence=0.95)

    assert result.sufficient
    # Losses reported as positive numbers; CVaR (mean beyond VaR) >= VaR by definition.
    assert result.var > 0
    assert result.cvar >= result.var
    # ~1.645 sigma for a normal at 95%: sanity band, not an exact assertion.
    assert 0.012 < result.var < 0.021
