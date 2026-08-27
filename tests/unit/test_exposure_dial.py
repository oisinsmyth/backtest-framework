"""Gates for D231's exposure dial.

The load-bearing ones are the look-ahead test on the rolling quantile and the
rotation-matching test: a rotation that changed exposure or turnover would stop
being a control for "you just traded less", which is the entire confound.
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
        "red", REPO / "scripts" / "run_exposure_dial.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["red"] = module
    spec.loader.exec_module(module)
    return module


R = _load()
SCREEN = json.loads(
    (REPO / "data" / "exposure_dial_screen.json").read_text(encoding="utf-8")
)


# --------------------------------------------------------------------------
# The dials do what the record says
# --------------------------------------------------------------------------


def test_every_dial_landed_within_the_declared_tolerance():
    """Amendment 2's gate. If a dial misses its target, exposure is an outcome
    rather than a control and the study is not measuring what it claims."""
    for c in SCREEN["cells"]:
        assert c["exposure_drift_pp"] <= R.EXPOSURE_TOLERANCE_PP, c["cell"]
    assert SCREEN["exposure_failures"] == []


def test_the_declared_targets_and_fractions_are_unchanged():
    assert R.TARGETS == (0.40, 0.30, 0.20, 0.10)
    assert R.UNIVERSE_FRACTIONS == {0.40: 0.544, 0.30: 0.351, 0.20: 0.228, 0.10: 0.105}
    assert R.NORM_WINDOW == 252
    assert R.SELECTION_FLOOR == -0.25
    assert R.EXPOSURE_TOLERANCE_PP == 3.0


def test_both_families_and_all_four_levels_are_present():
    cells = {c["cell"] for c in SCREEN["cells"]}
    assert cells == {f"{f}@{t:.0%}" for f in ("T", "N") for t in R.TARGETS}


def test_threshold_dial_hits_its_target_on_synthetic_data():
    rng = np.random.default_rng(1)
    z = rng.normal(size=(8, 1500))
    for target in (0.40, 0.20):
        hold = R.dial_threshold(z, target)[:, R.NORM_WINDOW :]
        assert abs(hold.mean() - target) < 0.03


def test_top_n_dial_never_holds_more_than_its_fraction():
    rng = np.random.default_rng(2)
    z = rng.normal(size=(57, 400))
    for target in R.TARGETS:
        hold = R.dial_top_n(z, target)
        k = max(1, round(R.UNIVERSE_FRACTIONS[target] * 57))
        assert hold.sum(axis=0).max() <= k


def test_top_n_never_holds_a_negative_signal():
    """The dial raises the bar; it must not lower it. A cell that held the least
    bad of a universe of negatives would be a different rule."""
    z = np.full((10, 50), -1.0)
    assert R.dial_top_n(z, 0.40).sum() == 0.0


# --------------------------------------------------------------------------
# No look-ahead
# --------------------------------------------------------------------------


def test_the_rolling_threshold_excludes_its_own_bar():
    """`c[t]` is the quantile of `z[t-252 .. t-1]`. If bar t were inside its own
    threshold window the rule would be comparing a value against a set containing
    it, which is a mild but real look-ahead."""
    z = np.zeros((1, 600))
    z[0, 400] = 100.0
    a = R.dial_threshold(z, 0.30)
    assert a[0, 400] == 1.0  # the spike clears a threshold it did not help set


def test_perturbing_from_bar_t_moves_no_decision_at_or_before_t():
    rng = np.random.default_rng(4)
    z = rng.normal(size=(4, 900))
    t = 700
    a = R.dial_threshold(z.copy(), 0.30)
    z2 = z.copy()
    z2[:, t:] += 40.0
    b = R.dial_threshold(z2, 0.30)
    assert np.array_equal(a[:, :t], b[:, :t])


def test_positions_are_lag_shifted_before_scoring():
    src = (REPO / "scripts" / "run_exposure_dial.py").read_text(encoding="utf-8")
    assert "F.shift(fn(z, target), LAG)" in src
    assert R.LAG == 1


# --------------------------------------------------------------------------
# The rotation null is a MATCHED control
# --------------------------------------------------------------------------


def test_rotation_preserves_exposure_and_turnover_exactly():
    """This is what makes the null a control for "you just traded less". If
    rotation changed either quantity the comparison would be meaningless."""
    rng = np.random.default_rng(5)
    pos = (rng.random((6, 500)) > 0.7).astype(float)
    rot = np.array([np.roll(pos[i], int(rng.integers(1, 500))) for i in range(6)])
    assert rot.sum() == pos.sum()
    for i in range(6):
        a = int(np.sum(np.diff(pos[i]) != 0))
        b = int(np.sum(np.diff(rot[i]) != 0))
        assert abs(a - b) <= 2  # only the wrap seam can differ


def test_one_offset_vector_is_shared_across_cells():
    """Rotating each cell independently would make them artificially independent,
    inflating the max and giving a floor wrong in the conservative direction."""
    src = (REPO / "scripts" / "run_exposure_dial.py").read_text(encoding="utf-8")
    body = src.split("def rotation_nulls")[1].split("def build")[0]
    draw = body.index("offsets = rng.integers")
    loop = body.index("for k in names:")  # the loop, not the `for k in names}` comprehension
    assert draw < loop
    assert body.count("offsets = rng.integers") == 1


def test_the_null_ran_and_covers_every_cell():
    nl = SCREEN["nulls"]
    assert nl["n_sims"] == R.N_SIMS == 1000
    assert set(nl["per_cell_p95"]) == {c["cell"] for c in SCREEN["cells"]}


def test_best_of_search_p95_is_at_least_every_single_cell_p95():
    """A maximum over cells cannot be below any of its members."""
    nl = SCREEN["nulls"]
    assert nl["best_p95"] >= max(nl["per_cell_p95"].values()) - 1e-9


# --------------------------------------------------------------------------
# Stage 1 carries no verdict
# --------------------------------------------------------------------------


def test_the_screen_stage_is_flagged_as_carrying_no_verdict():
    assert SCREEN["stage"] == "screen"
    assert SCREEN["is_verdict"] is False


def test_the_screen_used_the_mined_fixture_not_the_holdout():
    """Spending the holdout on stage 1 would be the one unrecoverable mistake
    available here."""
    assert "holdout" not in SCREEN["fixture"]
    assert SCREEN["n_symbols"] == 57


def test_survivors_are_exactly_the_cells_above_the_declared_floor():
    s = SCREEN["screen"]
    expected = [c["cell"] for c in SCREEN["cells"] if c["selection_quality"] >= R.SELECTION_FLOOR]
    assert s["survivors"] == expected
    assert set(s["survivors"]) | set(s["dropped"]) == {c["cell"] for c in SCREEN["cells"]}


def test_selection_quality_is_measured_against_the_sqrt_f_prediction():
    par = SCREEN["parent"]
    for c in SCREEN["cells"]:
        pred = par["excess_sharpe"] * (c["exposure"] / par["exposure"]) ** 0.5
        assert c["sqrt_f_predicted"] == pytest.approx(pred, rel=1e-9)
        assert c["selection_quality"] == pytest.approx(
            c["excess_sharpe"] / pred - 1.0, rel=1e-9
        )


def test_buy_and_hold_is_computed_and_fully_exposed():
    bh = SCREEN["buy_and_hold"]
    assert bh["exposure"] == pytest.approx(1.0, abs=1e-9)
    assert bh["excess_sharpe"] < SCREEN["parent"]["excess_sharpe"]


def test_levered_column_is_the_declared_monotone_transform():
    """Disclosed in the record as a presentation of excess Sharpe, not independent
    evidence. If it ever stopped ranking cells identically, the disclosure would
    be wrong."""
    bh_vol = SCREEN["buy_and_hold"]["vol"]
    for c in SCREEN["cells"]:
        assert c["levered_return_at_bh_vol"] == pytest.approx(
            R.RF_ANNUAL + c["excess_sharpe"] * bh_vol, rel=1e-9
        )
    by_sharpe = [c["cell"] for c in sorted(SCREEN["cells"], key=lambda c: -c["excess_sharpe"])]
    by_levered = [c["cell"] for c in sorted(SCREEN["cells"], key=lambda c: -c["levered_return_at_bh_vol"])]
    assert by_sharpe == by_levered
