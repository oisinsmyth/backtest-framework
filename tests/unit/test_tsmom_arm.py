"""Gates for D239's time-series momentum arm.

The load-bearing one is `subset_panel`. T2 was first built by zeroing the 46
equity rows of a 57-row position matrix, which leaves `portfolio_log_returns`
dividing by 57 -- so an 11-name book at 49.8% exposure scored as a 57-name book
at 9.6%. It was caught only because D239 registered the exposure BEFORE the run.
The test below pins the property that failure violated: an N-name book is
equal-weighted over N.

The rest: the signal is what the record says it is, S1 has not moved, no
look-ahead, and the page round-trips.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "tsm", REPO / "scripts" / "run_tsmom_arm.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["tsm"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads((REPO / "data" / "tsmom_arm_summary.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------
# subset_panel -- the defect this study actually produced
# --------------------------------------------------------------------------


def test_a_subset_book_is_equal_weighted_over_the_subset():
    """Zeroing rows is NOT the same as restricting the universe, and the gap is
    exactly the factor n_subset / n_total."""
    panel, _ = R.L.load_panel()
    rows = [i for i, s in enumerate(panel.symbols) if s in R.NON_EQUITY]
    start = 1000

    sub = R.subset_panel(panel, rows)
    assert len(sub.symbols) == len(R.NON_EQUITY)
    assert sub.closes.shape[0] == len(rows)
    assert sub.dates == panel.dates

    on_subset = R.tsmom_positions(sub, start)
    zeroed = R.tsmom_positions(panel, start, rows=rows)

    exposure_right = on_subset[:, start:].mean()
    exposure_wrong = zeroed[:, start:].mean()
    assert exposure_right == pytest.approx(0.4981, abs=5e-4)
    # the wrong construction is diluted by exactly the universe ratio
    assert exposure_wrong == pytest.approx(
        exposure_right * len(rows) / len(panel.symbols), rel=1e-9
    )


def test_the_subset_panel_carries_the_right_rows():
    panel, _ = R.L.load_panel()
    rows = [3, 7, 11]
    sub = R.subset_panel(panel, rows)
    np.testing.assert_array_equal(sub.closes, panel.closes[rows])
    np.testing.assert_array_equal(sub.total_log_returns, panel.total_log_returns[rows])
    np.testing.assert_array_equal(sub.cost_fraction, panel.cost_fraction[rows])
    assert sub.symbols == tuple(panel.symbols[i] for i in rows)


# --------------------------------------------------------------------------
# The signal is what the record says
# --------------------------------------------------------------------------


def test_the_signal_is_a_twelve_month_price_comparison():
    """Built so the 252-bar sign is known by construction rather than trusted."""
    n, T = 1, 600
    closes = np.full((n, T), 100.0)
    closes[0, 300:] = 120.0  # a step up at bar 300
    panel = type("P", (), {"closes": closes})()
    pos = R.tsmom_positions(panel, start=260)

    # bar t is long iff close[t-1] > close[t-1-252]
    for t in range(261, T):
        want = float(closes[0, t - 1] > closes[0, t - 1 - R.LOOKBACK])
        assert pos[0, t] == want, f"bar {t}"
    assert np.all(pos[:, :260] == 0.0)
    assert R.LOOKBACK == 252


def test_no_look_ahead_in_the_signal():
    """position[t] must depend only on closes at t-1 and t-1-252."""
    n, T, start = 1, 700, 300
    rng = np.random.default_rng(5)
    closes = 100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, (n, T)), axis=1))
    before = R.tsmom_positions(type("P", (), {"closes": closes})(), start)

    t = 500
    bumped = closes.copy()
    bumped[:, t:] *= 1.5
    after = R.tsmom_positions(type("P", (), {"closes": bumped})(), start)
    np.testing.assert_array_equal(before[:, : t + 1], after[:, : t + 1])
    assert not np.array_equal(before[:, t + 1 :], after[:, t + 1 :])


# --------------------------------------------------------------------------
# The artifact records what the write-up claims
# --------------------------------------------------------------------------


def test_s1_did_not_move():
    """If the comparison arm shifts, the study is void. BOOK.md quotes +0.746."""
    s1 = SUMMARY["cells"]["S1"]
    assert s1["excess_sharpe"] == pytest.approx(0.746, abs=5e-4)
    assert s1["exposure_gross"] == pytest.approx(0.1887, abs=5e-4)


def test_the_registered_exposures_hold():
    """These were published in D239 BEFORE the run. A mismatch is a defect."""
    assert SUMMARY["cells"]["T1"]["exposure_gross"] == pytest.approx(0.5831, abs=5e-4)
    assert SUMMARY["cells"]["T2"]["exposure_gross"] == pytest.approx(0.4981, abs=5e-4)


def test_trend_is_an_anti_signal_not_merely_skill_free():
    """The finding, and the volatility leg is what makes it robust: T1 has a
    POSITIVE mean, so being less volatile than its rotations pushes its Sharpe UP
    -- and it still lands at the 0.7th percentile. Money confirms it independently."""
    n = SUMMARY["nulls"]["T1"]
    assert n["percentile_of_actual"] < 5.0
    assert n["money_percentile_of_actual"] < 5.0
    assert n["vol_ratio_actual_over_null"] < 1.0  # the mechanical effect favours T1
    assert SUMMARY["cells"]["T1"]["excess_sharpe"] < n["p50"]


def test_the_non_equity_subset_is_neutral_not_adverse():
    """The anti-signal is specifically an EQUITY phenomenon -- T2 sits mid-null."""
    n = SUMMARY["nulls"]["T2"]
    assert 20.0 < n["percentile_of_actual"] < 80.0


def test_every_hurdle_leg_is_present_and_every_one_failed():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    for k in ("T1", "T2"):
        p1 = SUMMARY["p1"][k]
        assert {"rho", "bar", "actual", "clears_P1"} <= set(p1)
        assert p1["clears_P1"] is False
        assert SUMMARY["nulls"][k]["clears_P3"] is False
        assert SUMMARY["cells"][k]["excess_sharpe"] < SUMMARY["buy_and_hold"]["excess_sharpe"]
    p2 = SUMMARY["p2"]
    assert "p05" in p2["bootstrap"] and "p95" in p2["bootstrap"]
    assert p2["clears_P2"] is False


def test_selection_quality_is_negative_for_both_trend_cells():
    """Worse than choosing the same number of bars at random."""
    for k in ("T1", "T2"):
        assert SUMMARY["sqrt_f"][k]["selection_quality"] < 0.0


def test_the_non_equity_partition_is_the_declared_one():
    """Fixed by asset class in D239 before the run; GDX/GDXJ are EQUITY."""
    assert set(SUMMARY["non_equity"]) == set(R.NON_EQUITY)
    assert len(R.NON_EQUITY) == 11
    assert "GDX" not in R.NON_EQUITY and "GDXJ" not in R.NON_EQUITY


def test_the_blend_weight_was_declared_not_optimised():
    assert SUMMARY["blend_weight"] == 0.5


def test_the_page_round_trips_byte_for_byte():
    """The idempotency defect appeared in D220, D222 and D229."""
    on_disk = (REPO / "TSMOM_ARM_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
