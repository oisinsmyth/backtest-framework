"""Deflated Sharpe Ratio (Bailey & López de Prado 2014) — D20, D21, D86.

DSR answers the only honest version of "is this Sharpe real?": given how many trials
you ran, what is the probability that the BEST of them beats the Sharpe you'd expect
from pure noise? The rejection threshold SR0 (the expected maximum Sharpe under the
null) rises with the number of trials — which is why the TrialRegistry exists (D20):
that count cannot be reconstructed retroactively, so it's logged live and pulled from
the registry here, never typed in.

Formulas (paper equations; Z = standard normal CDF, γ = Euler–Mascheroni):

  PSR(SR*) = Z( (SR − SR*)·√(T−1) / √(1 − γ₃·SR + (γ₄−1)/4·SR²) )
  SR0      = √V[{SRn}] · ( (1−γ)·Z⁻¹(1−1/N) + γ·Z⁻¹(1−1/(N·e)) )
  DSR      = PSR(SR0)

All Sharpe quantities are NON-annualized (per-period), same frequency as T. Normal
CDF/inverse via the stdlib (`math.erf`, `statistics.NormalDist.inv_cdf`) — no scipy
for two functions; accuracy verified to the paper's four decimals (D86).
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
    """SR0: the expected maximum Sharpe among n_trials zero-true-Sharpe trials whose
    estimated Sharpes have variance var_trials — the noise floor a selected best
    result must clear."""
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
    """DSR with N and V[{SRn}] pulled from the TrialRegistry (D20/D21's whole point:
    the trial count is logged evidence, not a self-reported number). N = trials in
    the registry (after the optional `include` filter); V = sample variance of the
    named Sharpe metric across them. Included trials missing the metric fail loudly
    — silently skipping them would understate N.

    UNITS CONTRACT (D98 — this is where the audit's F1 bug lived): the logged metric,
    `sr`, and `t` must all be in the SAME per-period (non-annualized) units. Feeding
    annualized trial Sharpes against a per-period `sr` inflates SR0 by √periods_per_year
    (≈15.9× for daily data) and forces DSR toward 0 regardless of the strategy.

    `include` selects which registry rows constitute the trial pool {SRn} — e.g. a
    study that logs one row per (window, cost multiplier) passes a predicate keeping
    only the real-cost (1×) rows, because the same window re-run at scaled costs is
    not an additional independent trial (D98). The predicate must select on
    config/identity fields, never on presence of the metric itself — that would
    silently shrink N, which the loud failure below exists to prevent."""
    trials = [trial for trial in registry.all_trials() if include is None or include(trial)]
    if len(trials) < 2:
        raise ValueError(
            f"registry holds {len(trials)} trial(s) after filtering; DSR needs at least 2"
        )
    sharpes = []
    for trial in trials:
        if sharpe_metric_key not in trial.metrics:
            raise ValueError(
                f"trial {trial.trial_id!r} has no metric {sharpe_metric_key!r} — every trial "
                "in the pool must report it, or the trial count N would silently exclude it (D20)"
            )
        sharpes.append(float(trial.metrics[sharpe_metric_key]))
    return deflated_sharpe_ratio(
        sr, t, skew, kurt, n_trials=len(sharpes), var_trials=_stats.variance(sharpes)
    )
