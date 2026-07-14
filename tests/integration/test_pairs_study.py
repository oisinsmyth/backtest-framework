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
        assert "window_sharpe_daily" in trial.metrics  # feeds DSR's V (D90)
        assert trial.snapshot_id == "synthetic-universe"
    assert result.n_pairs_tested_per_window == 45


def test_dsr_computed_from_registry_and_finite(study):
    result, _, _ = study
    assert 0.0 <= result.dsr <= 1.0
    assert result.dsr_inputs["t"] == 5 * CONFIG.test_size


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
