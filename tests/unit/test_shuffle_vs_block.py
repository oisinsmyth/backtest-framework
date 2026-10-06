"""Tests that the block bootstrap keeps autocorrelation that a returns shuffle removes.

On an autocorrelated series, shuffling removes the autocorrelation a mean-reversion
strategy trades, while the block bootstrap keeps most of it, so Monte Carlo uses blocks.
"""

import numpy as np

from backtest_framework.analytics.monte_carlo import block_bootstrap_paths


def _acf1(x: np.ndarray) -> float:
    a, b = x[:-1], x[1:]
    return float(np.corrcoef(a, b)[0, 1])


def test_shuffle_destroys_autocorrelation_block_bootstrap_preserves_it():
    rng = np.random.default_rng(77)
    # AR(1) with rho = 0.6: strong, known autocorrelation.
    n = 500
    eps = rng.normal(0.0, 0.01, n)
    r = np.empty(n)
    r[0] = eps[0]
    for i in range(1, n):
        r[i] = 0.6 * r[i - 1] + eps[i]

    original_acf = _acf1(r)
    assert original_acf > 0.5  # the generated series is autocorrelated

    block_paths = block_bootstrap_paths(r, seed=7, n_sims=200, block_size=25)
    block_acf = float(np.mean([_acf1(p) for p in block_paths]))

    shuffle_rng = np.random.default_rng(7)
    shuffle_acf = float(np.mean([_acf1(shuffle_rng.permutation(r)) for _ in range(200)]))

    assert abs(shuffle_acf) < 0.05  # shuffling removes the autocorrelation
    assert block_acf > 0.35  # blocks keep most of it (boundary losses only)
    assert block_acf > shuffle_acf + 0.3
