"""Gates for D240's uptrend-onset arm.

The load-bearing ones are the two the whole result rests on:

  * `rolling_fit` is a prefix-sum fast path, so it is pinned against a brute-force
    `np.polyfit` on the same windows. A fast path nobody checks against the slow
    one is a defect waiting to happen.
  * the causal window. A pivot at index i is knowable only at i + k (D173). If the
    fit could see it earlier the arm would leak k bars of future, invisibly.

Then: the overlay null preserves exit COUNT exactly (the single property that makes
it the right control under R7), no look-ahead in the walk, and the page round-trips.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "uo", REPO / "scripts" / "run_uptrend_onset.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["uo"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "uptrend_onset_summary.json").read_text(encoding="utf-8")
)


# --------------------------------------------------------------------------
# The fast path is pinned against the slow one
# --------------------------------------------------------------------------


def test_prefix_sum_regression_matches_brute_force_polyfit():
    rng = np.random.default_rng(3)
    T, k = 1200, 3
    idx = np.sort(rng.choice(np.arange(5, T - 5), size=90, replace=False))
    y = np.cumsum(rng.normal(0, 0.05, len(idx))) + 4.0

    slope, inter = R.rolling_fit(T, idx, y, k)
    checked = 0
    for t in range(400, T, 37):
        sel = (idx >= t - R.WINDOW) & (idx <= t - k)
        if sel.sum() < R.MIN_PIVOTS:
            assert math.isnan(slope[t])
            continue
        m, b = np.polyfit(idx[sel].astype(float), y[sel], 1)
        assert slope[t] == pytest.approx(m, rel=1e-9, abs=1e-12)
        assert inter[t] == pytest.approx(b, rel=1e-9, abs=1e-9)
        checked += 1
    assert checked > 15, "the test barely exercised the fast path"


def test_a_pivot_is_invisible_for_exactly_k_bars():
    """D173's confirmation lag, asserted directly rather than trusted."""
    T, k = 600, 3
    base = np.array([100, 200, 300], dtype=int)
    y = np.array([1.0, 1.1, 1.2])
    late = 400
    s_without, _ = R.rolling_fit(T, base, y, k)
    s_with, _ = R.rolling_fit(T, np.append(base, late), np.append(y, 1.35), k)

    # invisible up to and including late + k - 1, visible from late + k
    np.testing.assert_allclose(
        s_without[: late + k], s_with[: late + k], rtol=0, atol=0, equal_nan=True
    )
    assert s_without[late + k] != s_with[late + k]


def test_an_old_pivot_drops_out_of_the_window():
    """The window is TRAILING and finite, so a pivot older than WINDOW bars must
    leave the fit — and its departure must visibly change the slope."""
    T, k = 900, 3
    idx = np.array([200, 300, 320, 340], dtype=int)
    y = np.array([9.0, 1.0, 1.01, 1.02])
    slope, _ = R.rolling_fit(T, idx, y, k)

    # t = 400: window is [148, 397] -- all four in, dragged down hard by the 9.0
    assert slope[400] < -0.05
    # t = 500: window is [248, 497] -- the 200 has aged out, leaving three flat ones
    assert slope[500] == pytest.approx(0.0005, abs=1e-6)
    # t = 700: window is [448, 697] -- nothing left, and NaN is the right answer
    assert math.isnan(slope[700])


# --------------------------------------------------------------------------
# R7's null -- the property that makes it the right control
# --------------------------------------------------------------------------


def test_the_overlay_null_preserves_exit_count_exactly():
    class P:
        closes = np.ones((4, 500))
    trades = [(i % 4, 100 + 20 * i, 160 + 20 * i, 0.05) for i in range(12)]
    rng = np.random.default_rng(0)
    pool = np.array([0.2, 0.5, 0.8])
    base = R.null_book(P, trades, 0, pool, rng, 50)
    for n_cut in (1, 5, 12):
        got = R.null_book(P, trades, n_cut, pool, rng, 50)
        shortened = sum(
            1 for (i, a, b, _r) in trades if got[i, a : b + 1].sum() < (b - a + 1)
        )
        assert shortened == n_cut, f"asked for {n_cut} cuts, made {shortened}"
        assert got.sum() < base.sum()


def test_the_null_never_lengthens_a_trade():
    class P:
        closes = np.ones((2, 400))
    trades = [(0, 100, 200, 0.05), (1, 150, 250, 0.05)]
    rng = np.random.default_rng(1)
    for _ in range(20):
        got = R.null_book(P, trades, 2, np.array([0.1, 0.9]), rng, 50)
        for i, a, b, _r in trades:
            assert got[i, a : b + 1].sum() <= (b - a + 1)
            assert got[i, b + 1 :].sum() == 0.0


# --------------------------------------------------------------------------
# The artifact records what the write-up claims
# --------------------------------------------------------------------------


def test_s1_did_not_move():
    s1 = SUMMARY["cells"]["S1"]
    assert s1["excess_sharpe"] == pytest.approx(0.746, abs=5e-4)
    assert s1["exposure_gross"] == pytest.approx(0.1887, abs=5e-4)


def test_the_declared_constants_are_what_the_record_says():
    assert (R.K, R.WINDOW, R.AGE_CAP, R.ATR_WINDOW) == (3, 252, 63, 21)
    assert (R.STOP_ATR, R.FLOOR_ATR, R.FIXED_STOP, R.TARGET_R) == (1.0, 2.0, 0.08, 2.0)
    assert SUMMARY["age_cap"] == 63 and SUMMARY["k"] == 3


def test_every_hurdle_leg_is_present():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    assert {"percentile_of_actual", "money_percentile_of_actual", "clears_B"} <= set(
        SUMMARY["rotation_null_A0"]
    )
    for k in R.OVERLAYS:
        assert {"n_cut", "p95", "percentile_of_actual", "clears_A"} <= set(
            SUMMARY["overlay_nulls"][k]
        )
    for k in R.CELL_ORDER:
        assert {"rho", "bar", "clears_C"} <= set(SUMMARY["p1"][k])
        assert {"sharpe_p05", "delta_p05", "delta_excludes_zero"} <= set(
            SUMMARY["bootstrap"][k]
        )


def test_the_verdict_the_record_reports():
    assert SUMMARY["rotation_null_A0"]["clears_B"] is True
    assert SUMMARY["rotation_null_A0"]["percentile_of_actual"] > 95.0
    assert all(SUMMARY["p1"][k]["clears_C"] for k in R.CELL_ORDER)
    # the fixed stop clears its overlay null; the structural one does not
    assert SUMMARY["overlay_nulls"]["A2"]["clears_A"] is True
    assert SUMMARY["overlay_nulls"]["A1"]["clears_A"] is False
    # the target is actively harmful, not merely neutral
    assert SUMMARY["overlay_nulls"]["A3"]["percentile_of_actual"] < 10.0


def test_the_weakest_part_of_the_case_is_recorded():
    """E fails at 2 entries per symbol -- worse than S1's 9. If this ever silently
    passes, the fixture or the rule changed and the record is stale."""
    assert SUMMARY["cells"]["A0"]["min_entries_per_symbol"] < 30
    assert SUMMARY["cells"]["A0"]["clears_E"] is False
    assert SUMMARY["diagnostics"]["n_onsets"] == 245


def test_no_arm_beats_buy_and_hold_with_an_interval_excluding_zero():
    """Including S1. The write-up must not claim otherwise."""
    for k in list(R.CELL_ORDER) + ["S1"]:
        assert SUMMARY["bootstrap"][k]["delta_excludes_zero"] is False


def test_the_combination_arithmetic_is_the_closed_form():
    c, p1 = SUMMARY["cells"], SUMMARY["p1"]
    s1 = c["S1"]["excess_sharpe"]
    for k in R.CELL_ORDER:
        sb, rho = c[k]["excess_sharpe"], p1[k]["rho"]
        want = math.sqrt((s1 ** 2 + sb ** 2 - 2 * rho * s1 * sb) / (1 - rho ** 2))
        assert SUMMARY["combined"][f"S1_plus_{k}"]["sharpe"] == pytest.approx(want, rel=1e-12)


def test_no_look_ahead_in_the_walk(loading_a_panel):
    """A close moved from bar t onward may not change any position at index <= t."""
    with loading_a_panel():
        panel, cleaned = R.L.load_panel()
    start = max(R.M.impulse_warm_up_bars(), R.M.warm_up_bars(),
                R.M.MATCHED_MOMENTUM_LOOKBACK)
    up, gl, il, atr = R.signals(panel, cleaned, start)
    before, _, _ = R.walk(panel, up, gl, il, atr, start, stop_mode="fixed")

    t = start + 300
    bumped = type(panel)(
        symbols=panel.symbols, closes=panel.closes.copy(), log_returns=panel.log_returns,
        cost_fraction=panel.cost_fraction, dates=panel.dates,
        total_log_returns=panel.total_log_returns,
    )
    bumped.closes[:, t:] *= 1.3
    after, _, _ = R.walk(bumped, up, gl, il, atr, start, stop_mode="fixed")
    np.testing.assert_array_equal(before[:, : t + 1], after[:, : t + 1])


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "docs" / "results" / "UPTREND_ONSET_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
