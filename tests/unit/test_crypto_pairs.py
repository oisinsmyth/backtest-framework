"""Unit gates for the BTC/ETH pairs study harness (D122-D127).

Synthetic data throughout — the real-fixture behaviour lives in
`tests/integration/test_crypto_pairs_study.py`. What is asserted here is that each piece
means what its name says: the cointegration critical values are the library's and not a
remembered approximation, the declarative cost stack builds the bricks it claims, a
variant's overrides land in exactly one field, and the basket benchmark really is a
50/50 hold.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.config.errors import ConfigError
from backtest_framework.costs.equity_bricks import BorrowFee, MarginInterest
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research import crypto_pairs_study as cp
from backtest_framework.research.breakout_study import CostTier
from backtest_framework.research.cointegration import adf_stat
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2018, 1, 1)
TIER = CostTier("test_40bp", 40.0, "taker")


def _series(closes, opens=None):
    opens = opens if opens is not None else closes
    return [
        TimestampedBar(
            EPOCH + timedelta(days=i),
            Bar(open=o, high=max(o, c) * 1.01, low=min(o, c) * 0.99, close=c),
        )
        for i, (o, c) in enumerate(zip(opens, closes))
    ]


# ------------------------------------------------------- cointegration critical values


def test_dickey_fuller_critical_values_match_statsmodels():
    """D125/Pillar 3: the τ_μ table is anchored against a library we did not write,
    not typed in from memory. `adfuller`'s critical values are sample-size dependent, so
    this pins them at the study's own train_size."""
    from statsmodels.tsa.stattools import adfuller

    rng = np.random.default_rng(0)
    series = np.cumsum(rng.normal(size=cp.CryptoPairsConfig().train_size))
    _stat, _p, _lag, _nobs, critical, *_ = adfuller(series, maxlag=1, regression="c", autolag=None)
    for level, expected in cp.DF_TAU_MU_CRITICAL.items():
        assert critical[level] == pytest.approx(expected, abs=5e-4), level


def test_engle_granger_critical_values_are_stricter_than_the_plain_df_table():
    """Not an anchor but an ordering invariant: estimating β from the same sample must
    raise the bar. If these two tables ever crossed, one of them was mistyped."""
    for level in ("1%", "5%", "10%"):
        assert cp.ENGLE_GRANGER_CRITICAL[level] < cp.DF_TAU_MU_CRITICAL[level], level


def test_demeaned_no_constant_adf_tracks_the_constant_included_regression():
    """The study compares `adf_stat(spread − mean)` against the τ_μ table. That is a
    stated approximation — demeaning then regressing without a constant is not
    algebraically identical to including one — so the size of the approximation is
    measured here rather than assumed away."""
    from statsmodels.tsa.stattools import adfuller

    rng = np.random.default_rng(7)
    worst = 0.0
    for _ in range(20):
        series = np.cumsum(rng.normal(size=252)) + 5.0
        mine = adf_stat(series - series.mean(), lags=1)
        theirs = adfuller(series, maxlag=1, regression="c", autolag=None)[0]
        worst = max(worst, abs(mine - theirs))
    assert worst < 0.25, f"demeaned ADF drifted {worst:.3f} from the constant-included one"


# ------------------------------------------------------------- cointegration reporting


def _pair_config(**kwargs):
    return cp.CryptoPairsConfig(
        symbol_a="AAA", symbol_b="BBB", train_size=252, test_size=63, step=63, **kwargs
    )


def _cointegrated_pair(n, seed):
    """B is a random walk; A is B plus a mean-reverting (AR(1), φ=0.5) log spread. The
    log spread is stationary by construction, so a working test must find it."""
    rng = np.random.default_rng(seed)
    log_b = np.cumsum(rng.normal(0.0, 0.02, size=n)) + math.log(100.0)
    spread, value = [], 0.0
    for shock in rng.normal(0.0, 0.02, size=n):
        value = 0.5 * value + shock
        spread.append(value)
    log_a = log_b + np.asarray(spread)
    return {"AAA": _series(list(np.exp(log_a))), "BBB": _series(list(np.exp(log_b)))}


def _independent_walks(n, seed):
    rng = np.random.default_rng(seed)
    log_a = np.cumsum(rng.normal(0.0, 0.02, size=n)) + math.log(100.0)
    log_b = np.cumsum(rng.normal(0.0, 0.02, size=n)) + math.log(100.0)
    return {"AAA": _series(list(np.exp(log_a))), "BBB": _series(list(np.exp(log_b)))}


def test_a_genuinely_stationary_spread_is_detected_in_every_window():
    """The positive control. Without it, a 14% detection rate on real data could just as
    easily mean the test is broken as that the pair is not cointegrated."""
    config = _pair_config()
    series = cp.aligned_series(_cointegrated_pair(700, seed=1), config)
    report = cp.cointegration_report(series, config)
    assert len(report.windows) >= 5
    assert report.rate("5%") == 1.0


def test_two_independent_random_walks_are_rejected_almost_always():
    """The negative control, and the reason the real-data result is readable: on data
    with no cointegrating relationship the 5% test must fire at roughly its nominal
    rate, not at 100%."""
    config = _pair_config()
    series = cp.aligned_series(_independent_walks(700, seed=2), config)
    report = cp.cointegration_report(series, config)
    assert report.rate("5%") <= 0.2


def test_cointegration_rates_are_monotone_in_the_significance_level():
    config = _pair_config()
    series = cp.aligned_series(_independent_walks(700, seed=3), config)
    report = cp.cointegration_report(series, config)
    for test in ("traded", "engle_granger"):
        assert report.rate("1%", test) <= report.rate("5%", test) <= report.rate("10%", test)
        assert report.count("5%", test) == round(report.rate("5%", test) * len(report.windows))


def test_cointegration_uses_training_bars_only():
    """D22's structural rule applied to a diagnostic: every window's report must be
    identical when the bars AFTER that window's training slice are replaced by garbage.
    `walk_forward_windows` guarantees this by construction; this proves the guarantee is
    actually being relied on rather than merely present."""
    config = _pair_config()
    series = cp.aligned_series(_independent_walks(700, seed=4), config)
    reference = cp.cointegration_report(series, config)

    # Wreck everything from the end of window 0's TRAINING slice onward.
    cutoff = config.train_size
    wrecked = {
        symbol: list(bars[:cutoff])
        + [
            TimestampedBar(
                tb.timestamp,
                Bar(open=tb.bar.open * 50, high=tb.bar.high * 50, low=tb.bar.low * 50,
                    close=tb.bar.close * 50),
            )
            for tb in bars[cutoff:]
        ]
        for symbol, bars in series.items()
    }
    perturbed = cp.cointegration_report(wrecked, config)
    assert perturbed.windows[0].adf_traded_spread == reference.windows[0].adf_traded_spread
    assert perturbed.windows[0].engle_granger_beta == reference.windows[0].engle_granger_beta


# -------------------------------------------------------------------------- cost stack


def test_pair_cost_stack_config_builds_exactly_the_three_bricks_it_names():
    config = cp.pair_cost_stack_config(TIER, 0.10, 0.06)
    stack = cp.build_pair_cost_stack(config)
    assert [type(b) for b in stack.trade_bricks] == [PercentOfNotionalSpread]
    assert [type(b) for b in stack.carry_bricks] == [BorrowFee]
    assert [type(b) for b in stack.portfolio_carry_bricks] == [MarginInterest]
    assert stack.event_flow_bricks == ()
    assert stack.trade_bricks[0].bps == 40.0
    assert stack.carry_bricks[0].annual_rate == 0.10
    assert stack.portfolio_carry_bricks[0].annual_rate == 0.06


def test_the_fee_slot_is_byte_identical_to_the_breakout_studys_tier_config():
    """D124's comparability claim, asserted rather than described: the two studies price
    fees with the same brick config, so a fee-tier difference between the reports can
    never be a modelling difference."""
    assert (
        cp.pair_cost_stack_config(TIER, 0.10, 0.06)["trade_bricks"]
        == TIER.cost_stack_config()["trade_bricks"]
    )


def test_a_malformed_stack_config_fails_loudly_at_build_time():
    config = cp.pair_cost_stack_config(TIER, 0.10, 0.06)
    del config["carry_bricks"]
    with pytest.raises(ConfigError, match="carry_bricks"):
        cp.build_pair_cost_stack(config)


# ---------------------------------------------------------------------- config/variants


def test_config_round_trips_through_its_logged_dict():
    config = cp.CryptoPairsConfig(borrow_annual_rate=0.25, stitch="chained", fill_timing="close")
    assert cp.CryptoPairsConfig.from_dict(config.to_dict()) == config


def test_config_dict_carries_every_field_that_changes_a_result():
    """D102's finding, applied here: two experiments that differ must not hash
    identically. Every dataclass field must appear in the logged dict."""
    import dataclasses

    logged = cp.CryptoPairsConfig().to_dict()
    for field in dataclasses.fields(cp.CryptoPairsConfig):
        assert field.name in logged, field.name


def test_config_refuses_an_unknown_stitch_or_fill_mode():
    with pytest.raises(ValueError, match="stitch"):
        cp.CryptoPairsConfig(stitch="rolling")
    with pytest.raises(ValueError, match="fill_timing"):
        cp.CryptoPairsConfig(fill_timing="vwap")


def test_a_variant_override_changes_exactly_one_field():
    base = cp.CryptoPairsConfig()
    resolved = cp.PairsVariant("v", "cost", borrow_annual_rate=0.25).resolve(base)
    assert resolved.borrow_annual_rate == 0.25
    assert resolved.to_dict() | {"borrow_annual_rate": base.borrow_annual_rate} == base.to_dict()


def test_a_variant_with_no_overrides_resolves_to_the_study_config_itself():
    base = cp.CryptoPairsConfig()
    assert cp.PairsVariant("v", "grid").resolve(base) is base


def test_variant_names_are_unique_and_the_baseline_is_in_the_grid():
    names = [v.name for v in cp.default_variants()]
    assert len(names) == len(set(names))
    assert cp.baseline_name() in [v.name for v in cp.grid_variants()]


def test_only_grid_and_gross_variants_enter_the_dsr_pool():
    """D116/D98: convention and cost sensitivities are the same configuration re-priced,
    so they are sensitivity points and not additional independent trials."""
    for variant in cp.default_variants():
        assert variant.describe()["in_dsr_pool"] == (variant.group in ("grid", "gross"))
    assert {v.group for v in cp.convention_variants() + cp.cost_variants()} == {
        "convention",
        "cost",
    }


def test_variant_rebuilds_from_its_logged_description():
    for variant in cp.default_variants():
        rebuilt = cp.PairsVariant.from_config(variant.describe())
        assert rebuilt.strategy_config() == variant.strategy_config()
        assert (rebuilt.name, rebuilt.group) == (variant.name, variant.group)


def test_variant_rebuild_refuses_a_foreign_strategy_config():
    with pytest.raises(ValueError, match="zscore_pairs"):
        cp.PairsVariant.from_config(
            {"variant": "x", "group": "grid", "strategy_config": {"type": "breakout_long_flat"}}
        )


def test_build_strategy_returns_a_fresh_instance_every_call():
    """`ZScorePairsStrategy._side` is per-run mutable state (D69). A shared instance
    would carry one run's position into the next."""
    variant = cp.PairsVariant("v", "grid")
    config = cp.CryptoPairsConfig()
    a, b = variant.build_strategy(config), variant.build_strategy(config)
    assert a is not b
    a._side = -1
    assert b._side == 0


# -------------------------------------------------------------------------- alignment


def test_aligned_series_inner_joins_and_says_so_when_there_is_nothing_left():
    config = _pair_config()
    long_leg = _series([100.0 + i for i in range(10)])
    short_leg = _series([100.0 + i for i in range(4)])
    aligned = cp.aligned_series({"AAA": long_leg, "BBB": short_leg}, config)
    assert len(aligned["AAA"]) == len(aligned["BBB"]) == 4

    disjoint = [
        TimestampedBar(EPOCH + timedelta(days=100 + i), tb.bar) for i, tb in enumerate(short_leg)
    ]
    with pytest.raises(ValueError, match="share no timestamps"):
        cp.aligned_series({"AAA": long_leg, "BBB": disjoint}, config)


def test_aligned_series_names_a_missing_symbol():
    with pytest.raises(ValueError, match="missing required symbol"):
        cp.aligned_series({"AAA": _series([100.0] * 10)}, _pair_config())


# -------------------------------------------------------------------------- benchmarks


def test_the_basket_benchmark_is_the_mean_of_the_two_leg_curves():
    """The 50/50 basket is built by averaging two full-capital `run_benchmark` curves
    rather than by reimplementing buy-and-hold (D115). That is only valid because
    `run_benchmark` is linear in starting cash — asserted here, not assumed."""
    config = _pair_config(starting_cash=100_000.0)
    rng = np.random.default_rng(11)
    n = 400
    bars = {
        "AAA": _series(list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))),
        "BBB": _series(list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))),
    }
    series = cp.aligned_series(bars, config)
    benchmarks = cp.run_benchmarks(series, TIER, config)
    basket = benchmarks["basket_5050"]
    for i, (_ts, nav) in enumerate(basket.oos_equity):
        expected = 0.5 * benchmarks["AAA"].oos_equity[i][1] + 0.5 * benchmarks["BBB"].oos_equity[i][1]
        assert nav == pytest.approx(expected, rel=1e-12)


def test_realised_beta_against_a_benchmark_is_the_metrics_definition():
    from backtest_framework.analytics.metrics import realised_beta

    config = _pair_config()
    rng = np.random.default_rng(13)
    n = 400
    bars = {
        "AAA": _series(list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))),
        "BBB": _series(list(100 * np.exp(np.cumsum(rng.normal(0, 0.02, n))))),
    }
    series = cp.aligned_series(bars, config)
    benchmarks = cp.run_benchmarks(series, TIER, config)
    result = cp.run_variant(series, cp.PairsVariant("v", "grid", lookback=20), TIER, config)
    betas = cp.realised_betas(result, benchmarks)
    assert set(betas) == {"vs_AAA", "vs_BBB", "vs_basket_5050"}
    assert betas["vs_AAA"] == pytest.approx(
        realised_beta(result.oos_returns, benchmarks["AAA"].oos_returns)
    )
