"""R17 (2026-09-19): every reported Sharpe carries a Sortino beside it, under the same convention.

The rule lives in three places a runner cannot avoid: `stats_block` in the shared futures runner
(D555, imported by every later one), the terrain summary dict, and `sortino_annual` beside
`sharpe_annual` on the study-result classes. Each is checked here against
`analytics.metrics.sortino` so the number is one number, not several.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.analytics.metrics import sharpe, sortino

REPO = Path(__file__).resolve().parents[2]


def _load_d555():
    spec = importlib.util.spec_from_file_location("d555_for_test", REPO / "scripts" / "run_d555_tsmom_replication.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["d555_for_test"] = mod
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _series(seed: int = 7, n: int = 600) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.standard_t(4, n) * 0.008 + 0.0003


def test_the_shared_runner_stats_block_reports_sortino_beside_sharpe_under_the_library_convention():
    R = _load_d555()
    x = _series()
    days = np.array([f"2020-{1 + (i // 21) % 12:02d}-{1 + i % 21:02d}" for i in range(len(x))])
    block = R.stats_block(x, days, "t")
    assert "sharpe" in block and "sortino" in block
    assert block["sharpe"] == pytest.approx(sharpe(x, 0.0, 252.0))
    assert block["sortino"] == pytest.approx(sortino(x, 0.0, 252.0))
    assert block["sortino"] != block["sharpe"]


def test_the_runner_sortino_uses_downside_over_all_observations_and_handles_no_downside():
    R = _load_d555()
    x = np.array([0.01, -0.02, 0.03, 0.0, -0.01])
    dd = math.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    assert R.sortino(x) == pytest.approx(x.mean() / dd * math.sqrt(252))
    assert R.sortino(np.array([0.01, 0.02, 0.03])) == math.inf
    assert R.sortino(np.array([0.0, 0.0, 0.0])) == 0.0
    assert math.isnan(R.sortino(np.array([0.01])))


def test_the_null_enumeration_can_carry_a_sortino_column_of_the_same_shape():
    R = _load_d555()
    x = _series(3, 300)
    keep = np.ones(299, dtype=bool)
    col = np.array([R.sortino(np.roll(x, k)) for k in range(1, 300)])
    block = R.sortino_null_block(x, col, keep)
    assert set(block) == {"observed", "p05", "p50", "p95", "n_finite"}
    assert block["observed"] == pytest.approx(R.sortino(x))
    assert block["n_finite"] == 299 and block["p05"] <= block["p50"] <= block["p95"]


def test_the_study_result_classes_expose_sortino_beside_sharpe():
    from backtest_framework.research import breakout_study, crypto_pairs_study

    for cls in (breakout_study.VariantResult, breakout_study.BenchmarkResult, crypto_pairs_study.VariantResult):
        assert hasattr(cls, "sharpe_annual") and hasattr(cls, "sortino_annual"), cls.__name__


def test_the_terrain_summary_carries_sortino_next_to_sharpe():
    src = (REPO / "src" / "backtest_framework" / "research" / "terrain_strategies.py").read_text(encoding="utf-8")
    i = src.index('"sharpe": curve_sharpe_zero_rf(rets, periods_per_year)')
    assert '"sortino": sortino(rets, 0.0, periods_per_year)' in src[i : i + 400]
