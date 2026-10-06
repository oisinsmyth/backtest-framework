"""Deflated Sharpe Ratio (Bailey & López de Prado 2014).

DSR is the probability that a Sharpe ratio beats the best Sharpe expected from noise
alone, given the number of trials run. The threshold SR0 (the expected maximum Sharpe
under the null) rises with the trial count, which is read from the TrialRegistry
rather than supplied by hand.

Formulas (paper equations; Z = standard normal CDF, γ = Euler–Mascheroni):

  PSR(SR*) = Z( (SR − SR*)·√(T−1) / √(1 − γ₃·SR + (γ₄−1)/4·SR²) )
  SR0      = √V[{SRn}] · ( (1−γ)·Z⁻¹(1−1/N) + γ·Z⁻¹(1−1/(N·e)) )
  DSR      = PSR(SR0)

All Sharpe quantities are per-period (non-annualized), at the same frequency as T.
The normal CDF and its inverse come from `statistics.NormalDist`; results match the
paper to its four decimals.
"""

from __future__ import annotations

import math
import statistics as _stats
from statistics import NormalDist
from typing import Callable

from ..registry.trial_registry import TrialRecord, TrialRegistry

EULER_MASCHERONI = 0.5772156649015329
_NORMAL = NormalDist()


def probabilistic_sharpe_ratio(sr: float, sr_ref: float, t: int, skew: float, kurt: float) -> float:
    """P[true SR > sr_ref | observed sr over t periods with the given higher moments].

    `kurt` is raw (non-excess) kurtosis: 3.0 for Normal returns."""
    if t < 2:
        raise ValueError(f"PSR needs at least 2 observations, got {t}")
    denominator = math.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    z = (sr - sr_ref) * math.sqrt(t - 1.0) / denominator
    return _NORMAL.cdf(z)


def expected_max_sharpe(n_trials: int, var_trials: float) -> float:
    """SR0: the expected maximum Sharpe among n_trials trials with zero true Sharpe.

    `var_trials` is the variance of the trials' estimated Sharpes. A selected best
    result must exceed SR0."""
    if n_trials < 2:
        raise ValueError(f"expected_max_sharpe needs n_trials >= 2, got {n_trials}")
    if var_trials <= 0:
        raise ValueError(f"var_trials must be positive, got {var_trials}")
    return math.sqrt(var_trials) * (
        (1.0 - EULER_MASCHERONI) * _NORMAL.inv_cdf(1.0 - 1.0 / n_trials)
        + EULER_MASCHERONI * _NORMAL.inv_cdf(1.0 - 1.0 / (n_trials * math.e))
    )


def deflated_sharpe_ratio(
    sr: float, t: int, skew: float, kurt: float, n_trials: int, var_trials: float
) -> float:
    return probabilistic_sharpe_ratio(sr, expected_max_sharpe(n_trials, var_trials), t, skew, kurt)


def deflated_sharpe_from_trials(
    registry: TrialRegistry,
    sharpe_metric_key: str,
    sr: float,
    t: int,
    skew: float,
    kurt: float,
    include: Callable[[TrialRecord], bool] | None = None,
) -> float:
    """DSR with N and V[{SRn}] taken from the TrialRegistry.

    N is the number of trials in the registry (after the optional `include` filter) and
    V the sample variance of the named Sharpe metric across them. Raises ValueError if
    fewer than 2 trials remain or an included trial lacks the metric, since skipping it
    would understate N.

    The logged metric, `sr` and `t` must all be per-period (non-annualized). Annualized
    trial Sharpes against a per-period `sr` inflate SR0 by √periods_per_year (≈15.9× for
    daily data) and push DSR toward 0.

    `include` selects the trial pool {SRn}. For example, a study logging one row per
    (window, cost multiplier) keeps only the 1× cost rows, since a re-run at scaled cost
    is not an independent trial. Filter on config or identity fields, never on whether
    the metric is present, which would shrink N."""
    trials = [trial for trial in registry.all_trials() if include is None or include(trial)]
    if len(trials) < 2:
        raise ValueError(
            f"registry holds {len(trials)} trial(s) after filtering; DSR needs at least 2"
        )
    sharpes = []
    for trial in trials:
        if sharpe_metric_key not in trial.metrics:
            raise ValueError(
                f"trial {trial.trial_id!r} has no metric {sharpe_metric_key!r}; every trial "
                "in the pool must report it, or the trial count N would be understated"
            )
        sharpes.append(float(trial.metrics[sharpe_metric_key]))
    return deflated_sharpe_ratio(
        sr, t, skew, kurt, n_trials=len(sharpes), var_trials=_stats.variance(sharpes)
    )
