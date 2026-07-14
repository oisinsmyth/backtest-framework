"""Tests for the Phase G pairs-study runner (research/pairs_study.py, D89/D90) on a
seeded synthetic universe — fast, offline, deterministic. The real-universe run is
the committed artifact (docs/results/pairs_study_v1.md); a bounded real-fixture e2e
lives at the bottom.
"""

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research.pairs_study import (
    StudyConfig,
    render_study_sweep_table,
    render_study_tearsheet,
    run_pairs_study,
)
from backtest_framework.simulator.fills import Bar

REPO = Path(__file__).resolve().parent.parent.parent
START = datetime(2026, 1, 5, 16)

CONFIG = StudyConfig(
    train_size=150,
    test_size=50,
    step=50,
    top_n=3,
    lookback=20,
    entry_z=1.5,
    exit_z=0.5,
    leg_weight=0.5,
    multipliers=(0.0, 1.0, 2.0),
    rf_annual=0.04,
    mc_seed=7,
)


def _synthetic_universe(n_symbols: int = 10, n_bars: int = 400, seed: int = 5):
    rng = np.random.default_rng(seed)
    bars, volumes = {}, {}
    common = np.cumsum(rng.normal(0.0002, 0.008, n_bars))  # a shared factor so pairs exist
    for k in range(n_symbols):
        idio = np.cumsum(rng.normal(0.0, 0.006, n_bars))
        logp = np.log(100.0) + common + idio
        prices = np.exp(logp)
        bars[f"S{k:02d}"] = [
            TimestampedBar(START + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
            for i, p in enumerate(prices.astype(float))
        ]
        volumes[f"S{k:02d}"] = [5e6] * n_bars
    return bars, volumes


@pytest.fixture(scope="module")
def study(tmp_path_factory):
    bars, volumes = _synthetic_universe()
    registry = TrialRegistry(tmp_path_factory.mktemp("study") / "trials.sqlite")
    result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe",
        config=CONFIG,
        trial_id_prefix="test-study",
    )
    return result, registry, bars


def test_stitching_and_chaining_compound_exactly(study):
    # The strong invariant (D89): stitched equity connects continuously across
    # windows (chaining) and the stitched returns compound starting cash to the
    # final NAV exactly - both properties in one identity.
    result, _, _ = study
    for m in CONFIG.multipliers:
        curve = result.curves[m]
        compounded = CONFIG.starting_cash * float(np.prod([1 + r for r in curve.returns]))
        assert curve.final_nav == pytest.approx(compounded, rel=1e-9)


def test_stitched_curve_covers_exactly_the_test_windows(study):
    # (400 - 150 - 50) / 50 + 1 = 5 windows x 50 test bars; no prefix bars leak in.
    result, _, bars = study
    assert result.n_windows == 5
    curve = result.curves[1.0]
    assert len(curve.equity) == 5 * CONFIG.test_size
    assert len(curve.returns) == 5 * CONFIG.test_size

    # First stitched timestamp is the first TEST bar of window 0 (train_size deep),
    # not a warm-up prefix bar (D89).
    all_timestamps = [tb.timestamp for tb in bars["S00"]]
    assert curve.equity[0][0] == all_timestamps[CONFIG.train_size]


def test_trials_logged_per_window_and_multiplier_with_multiplicity(study):
    result, registry, _ = study
    trials = registry.all_trials()
    assert len(trials) == 5 * len(CONFIG.multipliers)  # windows x multipliers
    for trial in trials:
        assert trial.params["n_pairs_tested"] == 45  # C(10,2) - D29's logged count
        assert "window_traded" in trial.metrics
        assert "window_sharpe_daily" in trial.metrics  # feeds DSR's V (D90/D98)
        assert trial.snapshot_id == "synthetic-universe"
    assert result.n_pairs_tested_per_window == 45


def test_dsr_computed_from_registry_and_finite(study):
    result, _, _ = study
    assert 0.0 <= result.dsr <= 1.0
    assert result.dsr_inputs["t"] == 5 * CONFIG.test_size
    # D98: the trial pool is the 1x rows only — one per window, not windows x multipliers.
    assert result.dsr_inputs["n_trials"] == 5


def test_logged_window_sharpe_is_daily_units(study):
    # D98 regression for audit F1: the logged per-window Sharpe must be in the SAME
    # per-period (daily) units as dsr_inputs["observed_sr_daily"] — i.e. equal to
    # the annualized sharpe() of that window's stitched returns divided by
    # sqrt(periods_per_year). The old code logged the annualized value, inflating
    # SR0 by sqrt(252) and forcing DSR toward 0 regardless of the strategy.
    from backtest_framework.analytics.metrics import sharpe

    result, registry, _ = study
    for w in range(result.n_windows):
        window_returns = result.curves[1.0].returns[w * CONFIG.test_size : (w + 1) * CONFIG.test_size]
        expected_daily = sharpe(
            window_returns, CONFIG.rf_annual, CONFIG.periods_per_year
        ) / np.sqrt(CONFIG.periods_per_year)
        logged = registry.get_trial(f"test-study-1.0x-w{w:02d}").metrics["window_sharpe_daily"]
        assert logged == pytest.approx(expected_daily, rel=1e-12)


def test_compute_dsr_false_skips_registry_dsr(tmp_path):
    # D98 (audit F9): capacity-style runs share a registry across levels, so the
    # per-level registry DSR is skipped entirely rather than computed over a
    # meaningless mixed pool. dsr_inputs stays (pure arithmetic on this run).
    bars, volumes = _synthetic_universe()
    result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=TrialRegistry(tmp_path / "trials.sqlite"),
        snapshot_id="synthetic-universe",
        config=CONFIG,
        trial_id_prefix="no-dsr",
        compute_dsr=False,
    )
    assert result.dsr is None
    assert "observed_sr_daily" in result.dsr_inputs
    assert "n_trials" not in result.dsr_inputs


def test_sweep_is_monotone_and_renders(study):
    result, _, _ = study
    finals = [result.curves[m].final_nav for m in sorted(CONFIG.multipliers)]
    assert all(later <= earlier + 1e-6 for earlier, later in zip(finals, finals[1:]))

    table = render_study_sweep_table(result)
    assert "Cost multiplier" in table and "0×" in table and "2×" in table


def test_tearsheet_renders_with_benchmark(study):
    result, _, bars = study
    closes = [tb.bar.close for tb in bars["S00"]]
    timestamps = [tb.timestamp for tb in bars["S00"]]
    benchmark = {ts: b / a - 1.0 for ts, a, b in zip(timestamps[1:], closes, closes[1:])}

    sheet = render_study_tearsheet(result, benchmark)
    assert "Sharpe (rf=4.00%/yr" in sheet
    assert "Realised beta" in sheet
    assert "seed=7" in sheet


def test_study_accepts_a_custom_selector_and_logs_its_details(tmp_path):
    # Study v2's hook (D92): a selector callable replaces Gatev top-N; its name and
    # per-pair details land in every trial's config. v1's default path is untouched
    # (the module-scoped `study` fixture above runs with selector=None).
    from backtest_framework.research.cointegration import CointegrationSelector

    bars, volumes = _synthetic_universe()
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    selector = CointegrationSelector(gatev_prefilter=15, beta_window=(0.7, 1.3))

    result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe-v2",
        config=CONFIG,
        trial_id_prefix="test-study-v2",
        selector=selector,
    )

    assert result.n_windows == 5
    trial = registry.get_trial("test-study-v2-1.0x-w00")
    assert trial.config["selector"] == "gatev_prefilter->engle_granger->adf_rank"
    assert trial.params["n_pairs_tested"] == 45  # still the FULL C(10,2) count
    for detail in trial.config["selection_details"]:
        assert 0.7 <= detail["beta"] <= 1.3  # the coherence filter held


def test_strategy_factory_receives_selector_details(tmp_path):
    # Study v3's hook (D94): a factory replaces the default ZScorePairsStrategy
    # construction and receives each pair's selector-details entry (carrying its
    # fitted beta) — the wiring that lets v3 trade the hedge v2 only logged.
    from backtest_framework.research.beta_zscore import BetaHedgedZScoreStrategy
    from backtest_framework.research.cointegration import CointegrationSelector

    bars, volumes = _synthetic_universe()
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    selector = CointegrationSelector(gatev_prefilter=15, beta_window=(0.7, 1.3))
    betas_seen = []

    def factory(pair, strategy_id, config, details):
        assert tuple(details["pair"]) == pair  # each pair got ITS OWN details entry
        betas_seen.append(details["beta"])
        return BetaHedgedZScoreStrategy(
            strategy_id=strategy_id,
            instrument_a=pair[0],
            instrument_b=pair[1],
            hedge_beta=details["beta"],
            lookback=config.lookback,
            entry_z=config.entry_z,
            exit_z=config.exit_z,
            leg_weight=config.leg_weight,
        )

    result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe-v3",
        config=CONFIG,
        trial_id_prefix="test-study-v3",
        selector=selector,
        strategy_factory=factory,
    )

    assert result.n_windows == 5
    assert betas_seen and all(0.7 <= b <= 1.3 for b in betas_seen)
    assert 0.0 <= result.dsr <= 1.0


def test_beta_one_factory_reproduces_the_default_path_exactly(study, tmp_path):
    # The strong regression (D94): a factory that forces beta=1 must produce a
    # stitched equity curve IDENTICAL to the default ZScorePairsStrategy path on the
    # same universe — the v3 machinery provably contains v2 as its beta=1 case.
    from backtest_framework.research.beta_zscore import BetaHedgedZScoreStrategy

    default_result, _, bars = study
    volumes = {s: [5e6] * len(series) for s, series in bars.items()}

    def beta_one_factory(pair, strategy_id, config, details):
        return BetaHedgedZScoreStrategy(
            strategy_id=strategy_id,
            instrument_a=pair[0],
            instrument_b=pair[1],
            hedge_beta=1.0,
            lookback=config.lookback,
            entry_z=config.entry_z,
            exit_z=config.exit_z,
            leg_weight=config.leg_weight,
        )

    registry = TrialRegistry(tmp_path / "trials.sqlite")
    hedged_result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=CorporateActions(),
        registry=registry,
        snapshot_id="synthetic-universe",
        config=CONFIG,
        trial_id_prefix="test-study-beta1",
        strategy_factory=beta_one_factory,
    )

    for m in CONFIG.multipliers:
        assert hedged_result.curves[m].equity == default_result.curves[m].equity


def test_bounded_run_on_the_real_universe_fixture(tmp_path):
    # The real data path, bounded to ~2 windows so the suite stays fast: slice the
    # committed fixture's first 500 bars and run one multiplier pair.
    from backtest_framework.data.corporate_actions import load_events_json
    from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes

    fixture = REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw.csv.gz"
    bars, volumes = load_fixture_csv_with_volumes(fixture)
    actions = load_events_json(REPO / "data" / "fixtures" / "universe_daily_2015_2024_raw_events.json")

    bars = {s: series[:500] for s, series in bars.items()}
    volumes = {s: v[:500] for s, v in volumes.items()}

    registry = TrialRegistry(tmp_path / "trials.sqlite")
    result = run_pairs_study(
        bars_by_symbol=bars,
        volumes_by_symbol=volumes,
        actions=actions,
        registry=registry,
        snapshot_id="bounded-real-universe",
        config=StudyConfig(
            train_size=252, test_size=63, step=63, top_n=3, lookback=30, multipliers=(0.0, 1.0)
        ),
        trial_id_prefix="bounded-real",
    )

    assert result.n_windows >= 2
    assert result.n_pairs_tested_per_window == 57 * 56 // 2  # C(57,2) = 1,596
    assert 0.0 <= result.dsr <= 1.0
    assert len(result.curves[1.0].equity) == result.n_windows * 63
