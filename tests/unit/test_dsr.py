"""Tests that the DSR implementation reproduces the worked example in Bailey & López de
Prado, "The Deflated Sharpe Ratio" (JPM 2014), with the trial count read from the
TrialRegistry.

Paper example: annualized SR 2.5 over 5 years of daily data, so non-annualized
SR = 2.5/√250, T = 1250, skewness −3, kurtosis 10. The paper does not state V[{SRn}]
directly; 0.002 is back-solved from checkpoint 1 and confirmed by checkpoint 2:

  1. at N = 46 trials, DSR "would have been 0.9505"
  2. with Normal returns the strategy survives until N = 88 (DSR ≈ 0.95)
  3. at N = 100 actual trials, DSR ≈ 0.9004, below the 95% level despite the 2.5 Sharpe.
"""

import math

import pytest

from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.validation.dsr import (
    deflated_sharpe_from_trials,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    probabilistic_sharpe_ratio,
)

SR = 2.5 / math.sqrt(250)  # 0.158114 non-annualized
T = 1250
SKEW, KURT = -3.0, 10.0
V_TRIALS = 0.002


def test_paper_headline_n100_dsr_is_0_9004():
    dsr = deflated_sharpe_ratio(SR, T, SKEW, KURT, n_trials=100, var_trials=V_TRIALS)
    assert dsr == pytest.approx(0.9004, abs=1e-4)
    assert dsr < 0.95  # the paper's conclusion: rejected at 95% despite SR 2.5


def test_paper_checkpoint_n46_dsr_is_0_9505():
    # The paper's text gives DSR 0.9505 for a discovery made after N = 46 trials.
    dsr = deflated_sharpe_ratio(SR, T, SKEW, KURT, n_trials=46, var_trials=V_TRIALS)
    assert dsr == pytest.approx(0.9505, abs=1e-4)


def test_paper_checkpoint_normal_returns_survive_to_n88():
    # The paper's text: with Normal returns (kurt = 3) the 95% boundary is at N = 88
    # independent trials.
    dsr_88 = deflated_sharpe_ratio(SR, T, skew=0.0, kurt=3.0, n_trials=88, var_trials=V_TRIALS)
    dsr_89 = deflated_sharpe_ratio(SR, T, skew=0.0, kurt=3.0, n_trials=89, var_trials=V_TRIALS)
    assert dsr_88 == pytest.approx(0.9505, abs=1e-4)
    assert dsr_88 >= 0.95 > dsr_89  # the boundary lies between 88 and 89


def test_sr0_rises_with_trials_and_annualizes_to_paper_value():
    sr0_100 = expected_max_sharpe(100, V_TRIALS)
    assert sr0_100 * math.sqrt(250) == pytest.approx(1.789, abs=1e-3)  # paper's SR0
    assert expected_max_sharpe(10, V_TRIALS) < sr0_100 < expected_max_sharpe(1000, V_TRIALS)


def test_psr_basics():
    # PSR against a zero benchmark with a healthy SR and normal returns is high...
    assert probabilistic_sharpe_ratio(0.1, 0.0, 1250, 0.0, 3.0) > 0.99
    # ...and negative skew / fat tails reduce confidence at the same SR.
    assert probabilistic_sharpe_ratio(0.1, 0.0, 1250, -3.0, 10.0) < probabilistic_sharpe_ratio(
        0.1, 0.0, 1250, 0.0, 3.0
    )


def test_dsr_from_registry_pulls_n_and_variance_never_typed_in(tmp_path):
    # N and V come from the TrialRegistry: 100 trials whose sharpe metrics are ±d
    # around 0 with sample variance 0.002, i.e. var = 100·d²/99 = 0.002, d = √0.00198.
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    d = math.sqrt(0.00198)
    for i in range(100):
        registry.add_trial(
            trial_id=f"trial-{i:03d}",
            config={"variant": i},
            params={},
            metrics={"sharpe_daily": d if i % 2 == 0 else -d},
            snapshot_id="snap-x",
            seed=i,
        )

    dsr = deflated_sharpe_from_trials(registry, "sharpe_daily", sr=SR, t=T, skew=SKEW, kurt=KURT)

    assert dsr == pytest.approx(0.9004, abs=1e-4)  # the paper's number, registry-fed


def test_trial_missing_the_sharpe_metric_raises(tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    registry.add_trial("a", {"v": 1}, {}, {"sharpe_daily": 0.1}, "s", 0)
    registry.add_trial("b", {"v": 2}, {}, {"final_nav": 1.0}, "s", 1)  # no sharpe

    with pytest.raises(ValueError, match="no metric"):
        deflated_sharpe_from_trials(registry, "sharpe_daily", sr=SR, t=T, skew=SKEW, kurt=KURT)


def test_include_predicate_scopes_the_trial_pool(tmp_path):
    # A study logging one row per (window, multiplier) passes a config-based predicate
    # so that N counts trials and excludes cost-sensitivity re-runs. 100 matching trials
    # reproduce the paper's N=100 result with 200 non-matching rows (other multipliers)
    # interleaved, some of which lack the metric; excluded rows without the metric do
    # not raise.
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    d = math.sqrt(0.00198)
    for i in range(100):
        registry.add_trial(
            f"study-1.0x-{i:03d}",
            {"cost_multiplier": 1.0},
            {},
            {"sharpe_daily": d if i % 2 == 0 else -d},
            "snap-x",
            i,
        )
        registry.add_trial(
            f"study-2.0x-{i:03d}", {"cost_multiplier": 2.0}, {}, {"sharpe_daily": 99.0}, "snap-x", i
        )
        registry.add_trial(
            f"study-0.0x-{i:03d}", {"cost_multiplier": 0.0}, {}, {}, "snap-x", i  # metric absent
        )

    dsr = deflated_sharpe_from_trials(
        registry,
        "sharpe_daily",
        sr=SR,
        t=T,
        skew=SKEW,
        kurt=KURT,
        include=lambda trial: trial.config.get("cost_multiplier") == 1.0,
    )
    assert dsr == pytest.approx(0.9004, abs=1e-4)

    # A predicate-matching trial without the metric raises.
    registry.add_trial("study-1.0x-100", {"cost_multiplier": 1.0}, {}, {}, "snap-x", 100)
    with pytest.raises(ValueError, match="no metric"):
        deflated_sharpe_from_trials(
            registry,
            "sharpe_daily",
            sr=SR,
            t=T,
            skew=SKEW,
            kurt=KURT,
            include=lambda trial: trial.config.get("cost_multiplier") == 1.0,
        )
