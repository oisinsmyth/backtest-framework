"""Step 12 X-gate (D20, D21, D86): the DSR implementation reproduces the worked
example from Bailey & López de Prado, "The Deflated Sharpe Ratio" (JPM 2014), with
the trials count pulled from the TrialRegistry — never typed in.

Paper example (recovery method in D86 — the PDF's equation glyphs don't survive text
extraction, but its plain text anchors two checkpoints that overdetermine the one
missing parameter): annualized SR 2.5 over 5 years of daily data → non-annualized
SR = 2.5/√250, T = 1250, skewness −3, kurtosis 10, V[{SRn}] = 0.002 (back-solved
from checkpoint 1 and independently confirmed by checkpoint 2):

  1. paper text: at N = 46 trials, DSR "would have been 0.9505"
  2. paper text: with Normal returns the strategy survives until N = 88 (DSR ≈ 0.95)
  3. the headline: at N = 100 actual trials, DSR ≈ 0.9004 — "not a legitimate
     empirical discovery at a 95% confidence level" despite the 2.5 Sharpe.
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
    # Plain-text anchor: "Should the strategist have made his discovery after
    # running only N = 46 independent trials ... would have been 0.9505".
    dsr = deflated_sharpe_ratio(SR, T, SKEW, KURT, n_trials=46, var_trials=V_TRIALS)
    assert dsr == pytest.approx(0.9505, abs=1e-4)


def test_paper_checkpoint_normal_returns_survive_to_n88():
    # Plain-text anchor: "If the strategy had exhibited Normal returns ... after
    # N = 88 independent trials" — the 95% boundary under normality (kurt = 3).
    dsr_88 = deflated_sharpe_ratio(SR, T, skew=0.0, kurt=3.0, n_trials=88, var_trials=V_TRIALS)
    dsr_89 = deflated_sharpe_ratio(SR, T, skew=0.0, kurt=3.0, n_trials=89, var_trials=V_TRIALS)
    assert dsr_88 == pytest.approx(0.9505, abs=1e-4)
    assert dsr_88 >= 0.95 > dsr_89  # the boundary sits exactly between 88 and 89


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
    # THE D20/D21 gate: N and V come from the TrialRegistry. 100 trials whose sharpe
    # metrics are ±d around 0 with sample variance exactly 0.002:
    # var = 100·d²/99 = 0.002 → d = √0.00198.
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


def test_trial_missing_the_sharpe_metric_fails_loudly(tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    registry.add_trial("a", {"v": 1}, {}, {"sharpe_daily": 0.1}, "s", 0)
    registry.add_trial("b", {"v": 2}, {}, {"final_nav": 1.0}, "s", 1)  # no sharpe

    with pytest.raises(ValueError, match="no metric"):
        deflated_sharpe_from_trials(registry, "sharpe_daily", sr=SR, t=T, skew=SKEW, kurt=KURT)


def test_include_predicate_scopes_the_trial_pool(tmp_path):
    # D98 (audit F8): a study logging one row per (window, multiplier) passes a
    # config-based predicate so N counts real trials, not cost-sensitivity re-runs.
    # 100 predicate-matching trials reproduce the paper's N=100 headline even with
    # 300 non-matching rows (different multipliers) interleaved in the registry —
    # including rows that lack the metric entirely, which must NOT fail as long as
    # the predicate excludes them.
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

    # A predicate-matching trial missing the metric still fails loudly (D20).
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
