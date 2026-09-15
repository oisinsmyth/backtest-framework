"""Unit gates for the era/benchmark analysis added after the first breakout run
(D118–D121).

These functions exist because the first version of the report drew conclusions the data
did not support: it compared a 37%-exposed strategy against a 100%-exposed benchmark, and
it quoted a Sharpe gap of a few hundredths as if it were evidence. The tests here pin the
arithmetic that replaced those claims.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.backtest import BacktestResult
from backtest_framework.research import breakout_study as bs
from backtest_framework.research.trade_diagnostics import extract_episodes
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def _series(closes, symbol="X"):
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=c, high=c * 1.01, low=c * 0.99, close=c))
        for i, c in enumerate(closes)
    ]


# --------------------------------------------------------------- Sharpe bootstrap


def test_bootstrap_of_a_series_against_itself_is_centred_on_zero():
    """The sanity anchor: paired against itself, every resample gives a difference of
    exactly zero, so the interval must be degenerate at zero and P(>0) must be 0. If the
    pairing were broken (independent resampling of the two series) this would fail
    immediately, which is the point of the test."""
    returns = [0.01 * math.sin(i / 3) + 0.001 for i in range(400)]
    out = bs.sharpe_difference_bootstrap(returns, returns, bs.BreakoutStudyConfig(), seed=0)
    assert out["observed"] == pytest.approx(0.0, abs=1e-12)
    assert out["p05"] == pytest.approx(0.0, abs=1e-12)
    assert out["p95"] == pytest.approx(0.0, abs=1e-12)
    assert out["prob_positive"] == 0.0


def test_bootstrap_detects_a_large_genuine_difference():
    good = [0.01] * 200 + [0.005] * 200
    bad = [-0.01] * 200 + [-0.005] * 200
    out = bs.sharpe_difference_bootstrap(good, bad, bs.BreakoutStudyConfig(), seed=0)
    assert out["observed"] > 0
    assert out["prob_positive"] > 0.95
    assert out["p05"] > 0


def test_bootstrap_is_deterministic_given_a_seed():
    returns_a = [0.01 * math.sin(i / 5) for i in range(300)]
    returns_b = [0.01 * math.cos(i / 5) for i in range(300)]
    study = bs.BreakoutStudyConfig()
    first = bs.sharpe_difference_bootstrap(returns_a, returns_b, study, seed=7)
    second = bs.sharpe_difference_bootstrap(returns_a, returns_b, study, seed=7)
    third = bs.sharpe_difference_bootstrap(returns_a, returns_b, study, seed=8)
    assert first == second
    assert first["p05"] != third["p05"]  # a different seed really does resample differently


def test_bootstrap_refuses_mismatched_lengths():
    with pytest.raises(ValueError, match="equal lengths"):
        bs.sharpe_difference_bootstrap([0.01] * 100, [0.01] * 99, bs.BreakoutStudyConfig(), seed=0)


def test_bootstrap_refuses_a_sample_shorter_than_a_block():
    with pytest.raises(ValueError, match="more than"):
        bs.sharpe_difference_bootstrap([0.01] * 10, [0.01] * 10, bs.BreakoutStudyConfig(), seed=0)


# ------------------------------------------------------------- annual breakdown


def test_annual_breakdown_compounds_within_each_calendar_year():
    """Two years, hand-checkable: +10% then +10% in year one, −50% in year two."""
    days = [datetime(2020, 6, 1), datetime(2020, 6, 2), datetime(2020, 6, 3), datetime(2021, 6, 1)]
    equity = [(days[0], 100.0), (days[1], 110.0), (days[2], 121.0), (days[3], 60.5)]
    returns = [0.10, 0.10, -0.50]

    result = bs.VariantResult(
        symbol="X", variant=bs.Variant("v", "plateau", fixed_config=bs.breakout_config()),
        tier=bs.DEFAULT_TIERS[0], schedule=(), oos_equity=equity, oos_returns=returns,
        window_sharpes_daily={}, window_final_nav={}, episodes=[],
        diagnostics=None, n_oos_bars=len(equity),  # type: ignore[arg-type]
    )
    benchmark = bs.BenchmarkResult(
        symbol="X", tier=bs.DEFAULT_TIERS[0], oos_equity=equity, oos_returns=[0.0, 0.0, 0.0]
    )
    rows = bs.annual_breakdown(result, benchmark)
    assert [int(row["year"]) for row in rows] == [2020, 2021]
    assert rows[0]["strategy"] == pytest.approx(1.10 * 1.10 - 1)  # +21%
    assert rows[1]["strategy"] == pytest.approx(-0.50)
    assert rows[0]["benchmark"] == pytest.approx(0.0)


def test_annual_breakdown_refuses_mismatched_spans():
    equity = [(EPOCH, 100.0), (EPOCH + timedelta(days=1), 110.0)]
    result = bs.VariantResult(
        symbol="X", variant=bs.Variant("v", "plateau", fixed_config=bs.breakout_config()),
        tier=bs.DEFAULT_TIERS[0], schedule=(), oos_equity=equity, oos_returns=[0.1],
        window_sharpes_daily={}, window_final_nav={}, episodes=[],
        diagnostics=None, n_oos_bars=2,  # type: ignore[arg-type]
    )
    benchmark = bs.BenchmarkResult("X", bs.DEFAULT_TIERS[0], equity, [0.1, 0.2])
    with pytest.raises(ValueError, match="different spans"):
        bs.annual_breakdown(result, benchmark)


def test_exposure_by_year_uses_timestamps_not_run_relative_indices():
    """The bug this test exists for: episode `entry_index` is relative to the RUN series,
    which begins one warm-up prefix before the OOS span. Indexing the OOS calendar with it
    silently attributes exposure to the wrong years."""
    bars = _series([100.0] * 5 + [100.0] * 5)
    timestamps = [tb.timestamp for tb in bars]
    fills = [
        (timestamps[2], "X", 1.0, 100.0, 0.0),
        (timestamps[5], "X", -1.0, 100.0, 0.0),
    ]
    engine_result = BacktestResult()
    engine_result.fills = fills
    episodes = extract_episodes(engine_result, "X", bars)

    result = bs.VariantResult(
        symbol="X", variant=bs.Variant("v", "plateau", fixed_config=bs.breakout_config()),
        tier=bs.DEFAULT_TIERS[0], schedule=(),
        oos_equity=[(ts, 100.0) for ts in timestamps], oos_returns=[0.0] * (len(bars) - 1),
        window_sharpes_daily={}, window_final_nav={}, episodes=episodes,
        diagnostics=None, n_oos_bars=len(bars),  # type: ignore[arg-type]
    )
    exposure = bs.exposure_by_year(result)
    # Held from bar 2 up to (not including) bar 5 -> 3 of 10 bars, all in 2020.
    assert exposure == {2020: pytest.approx(3 / 10)}


# --------------------------------------------------- constant-fraction benchmark


@pytest.fixture(scope="module")
def btc(requires_panel):
    from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
    from pathlib import Path

    repo = Path(__file__).resolve().parent.parent.parent
    fixture = repo / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
    requires_panel(fixture)
    bars, _ = load_fixture_csv_with_volumes(fixture)
    return bars["BTC-USD"]


def test_constant_fraction_at_one_matches_the_engine_buy_and_hold(btc):
    study = bs.BreakoutStudyConfig()
    tier = bs.DEFAULT_TIERS[-1]
    full = bs.run_constant_fraction_benchmark(btc, "BTC-USD", tier, study, 1.0)
    reference = bs.run_benchmark_via_engine(btc, "BTC-USD", tier, study)
    assert full.total_return == pytest.approx(reference.total_return, rel=1e-9)


def test_constant_fraction_sits_between_cash_and_full_exposure(btc):
    study = bs.BreakoutStudyConfig()
    tier = bs.DEFAULT_TIERS[0]  # zero fees: isolate the leverage effect
    half = bs.run_constant_fraction_benchmark(btc, "BTC-USD", tier, study, 0.5)
    full = bs.run_constant_fraction_benchmark(btc, "BTC-USD", tier, study, 1.0)
    assert 0.0 < half.total_return < full.total_return
    assert half.max_drawdown < full.max_drawdown


def test_constant_fraction_rejects_an_out_of_range_fraction(btc):
    with pytest.raises(ValueError, match="fraction must be"):
        bs.run_constant_fraction_benchmark(btc, "BTC-USD", bs.DEFAULT_TIERS[0], bs.BreakoutStudyConfig(), 0.0)
    with pytest.raises(ValueError, match="fraction must be"):
        bs.run_constant_fraction_benchmark(btc, "BTC-USD", bs.DEFAULT_TIERS[0], bs.BreakoutStudyConfig(), 1.5)


def test_constant_fraction_covers_the_same_span_as_the_strategy(btc):
    study = bs.BreakoutStudyConfig()
    tier = bs.DEFAULT_TIERS[-1]
    variant = bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10))
    strategy = bs.run_variant(btc, "BTC-USD", variant, tier, study)
    matched = bs.run_constant_fraction_benchmark(
        btc, "BTC-USD", tier, study, strategy.diagnostics.exposure
    )
    assert [ts for ts, _ in matched.oos_equity] == [ts for ts, _ in strategy.oos_equity]


# ---------------------------------------------------------- start-date sensitivity


def test_start_date_sensitivity_shortens_the_span_monotonically(btc):
    study = bs.BreakoutStudyConfig()
    variant = bs.Variant("base", "plateau", fixed_config=bs.breakout_config(40, 10))
    rows = bs.start_date_sensitivity(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[-1], study)
    assert len(rows) >= 3
    for earlier, later in zip(rows, rows[1:]):
        assert later["oos_start"] > earlier["oos_start"]
        assert later["n_oos_bars"] < earlier["n_oos_bars"]
    # The earliest cut reproduces the headline run exactly.
    headline = bs.run_variant(btc, "BTC-USD", variant, bs.DEFAULT_TIERS[-1], study)
    assert rows[0]["strategy_return"] == pytest.approx(headline.total_return, rel=1e-12)


def test_vol_target_variants_sweep_only_the_target(btc):
    """Every swept variant must differ from the baseline in exactly one config key —
    otherwise the sweep is measuring more than it claims."""
    baseline = bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT)
    for variant in bs.vol_target_variants():
        config = variant.fixed_config
        assert config["n_entry"] == baseline["n_entry"]
        assert config["n_exit"] == baseline["n_exit"]
        assert config["filters"] == baseline["filters"]
        differing = {
            key for key in config["weight_source"]
            if config["weight_source"][key] != baseline["weight_source"][key]
        }
        assert differing == {"target_annual_vol"}
    targets = {v.fixed_config["weight_source"]["target_annual_vol"] for v in bs.vol_target_variants()}
    assert targets == set(bs.VOL_TARGET_SWEEP)
    assert 0.40 not in targets, "the baseline target must not be duplicated as a swept variant"


def test_vol_target_variants_are_registered_as_trials(btc):
    names = {v.name for v in bs.default_variants("BTC-USD", bs.BreakoutStudyConfig())[0]}
    assert {v.name for v in bs.vol_target_variants()} <= names
