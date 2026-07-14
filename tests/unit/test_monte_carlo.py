"""Step 9 Monte Carlo gates (D34, D36, D81)."""

import inspect

import numpy as np
import pytest

from backtest_framework.analytics.monte_carlo import (
    DEFAULT_N_SIMS,
    block_bootstrap_percentiles,
)

RETURNS = list(np.random.default_rng(5).normal(0.0004, 0.012, 300))


def test_default_n_sims_is_at_least_10000():
    # THE D36 gate: the default rose from 500 to >= 10,000. Assert both the constant
    # and the actual signature default, so neither can drift alone.
    assert DEFAULT_N_SIMS >= 10_000
    signature_default = inspect.signature(block_bootstrap_percentiles).parameters["n_sims"].default
    assert signature_default == DEFAULT_N_SIMS


def test_seed_is_required():
    with pytest.raises(TypeError):
        block_bootstrap_percentiles(RETURNS)  # type: ignore[call-arg]


def test_same_seed_identical_percentile_table():
    # THE D34 gate: byte-identical, not approximately equal.
    a = block_bootstrap_percentiles(RETURNS, seed=42, n_sims=2000)
    b = block_bootstrap_percentiles(RETURNS, seed=42, n_sims=2000)
    assert a.terminal_return == b.terminal_return
    assert a.max_drawdown == b.max_drawdown


def test_different_seed_different_table():
    a = block_bootstrap_percentiles(RETURNS, seed=42, n_sims=2000)
    b = block_bootstrap_percentiles(RETURNS, seed=43, n_sims=2000)
    assert a.terminal_return != b.terminal_return


def test_percentiles_are_ordered_and_drawdowns_positive():
    result = block_bootstrap_percentiles(RETURNS, seed=42, n_sims=2000)
    values = [result.terminal_return[p] for p in sorted(result.terminal_return)]
    assert values == sorted(values)  # p5 <= p25 <= ... <= p95
    assert all(dd >= 0 for dd in result.max_drawdown.values())


def test_too_short_series_fails_loudly():
    with pytest.raises(ValueError, match="block_size"):
        block_bootstrap_percentiles(RETURNS[:10], seed=1)
