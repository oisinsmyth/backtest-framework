"""Tests that the rendered tearsheet states its caveats.

The caveats are insufficient data, the rf used, the beta expectation, and the Monte Carlo
seed."""

import numpy as np

from backtest_framework.analytics.tearsheet import render_metrics_table


def test_insufficient_data_string_actually_prints():
    # A short series prints "insufficient data" rather than a number.
    rng = np.random.default_rng(9)
    table = render_metrics_table(list(rng.normal(0, 0.01, 100)), rf_annual=0.04, periods_per_year=252)
    assert "insufficient data" in table
    assert "need >=600" in table


def test_rf_is_stated_in_the_sharpe_row():
    rng = np.random.default_rng(9)
    table = render_metrics_table(list(rng.normal(0, 0.01, 100)), rf_annual=0.04, periods_per_year=252)
    assert "rf=4.00%/yr" in table  # never an implicit rf


def test_beta_row_carries_the_market_neutral_expectation_note():
    rng = np.random.default_rng(9)
    returns = list(rng.normal(0, 0.01, 700))
    benchmark = list(rng.normal(0.0003, 0.011, 700))
    table = render_metrics_table(
        returns, rf_annual=0.04, periods_per_year=252, benchmark_returns=benchmark
    )
    assert "Realised beta" in table
    assert "≈ 0" in table and "market-neutral expectation" in table


def test_mc_table_renders_with_seed_recorded():
    rng = np.random.default_rng(9)
    table = render_metrics_table(
        list(rng.normal(0.0004, 0.01, 700)), rf_annual=0.04, periods_per_year=252, mc_seed=42
    )
    assert "seed=42" in table  # the seed appears in the table
    assert "n=10,000" in table
