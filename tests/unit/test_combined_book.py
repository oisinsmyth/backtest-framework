"""Gates for D241's combined book and capital allocator.

The load-bearing ones are the two invariants the build broke before the
assertions caught them:

  * a name is held ONCE and charged ONCE, even when both arms want it (1,000
    cells, 3.63% of demand -- the first draft summed the books and double-funded);
  * TOTAL is a HARD cap enforced globally, because ownership can transfer between
    arms without a capital event, after which per-arm reserve checks no longer
    bound the sum.

Plus incumbency (an open position is never evicted for a newcomer), inertness at
100% capital, and the page round-trip.
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
        "cb", REPO / "scripts" / "run_combined_book.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["cb"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "combined_book_summary.json").read_text(encoding="utf-8")
)


def _demand(n=4, T=40, start=5):
    return {"S1": np.zeros((n, T)), "A2": np.zeros((n, T))}


# --------------------------------------------------------------------------
# Amendment 1 -- a name is held once
# --------------------------------------------------------------------------


def test_a_name_wanted_by_both_arms_is_funded_once():
    d = _demand()
    d["S1"][0, 10:20] = 1.0
    d["A2"][0, 10:20] = 1.0          # the same name, the same bars
    g, _ = R.allocate(d, 5, 1.0, {"S1": 0.0, "A2": 0.0})
    book = g["S1"] + g["A2"]
    assert book.max() <= 1.0, "the name was double-funded"
    assert book[0, 15] == 1.0
    # exactly one arm owns it at any bar
    assert (g["S1"][0, 15] + g["A2"][0, 15]) == 1.0


def test_ownership_transfers_without_a_capital_event():
    """S1 opens it; S1 leaves; A2 still wants it -> the position CONTINUES."""
    d = _demand()
    d["S1"][0, 10:15] = 1.0
    d["A2"][0, 12:20] = 1.0
    g, _ = R.allocate(d, 5, 1.0, {"S1": 0.0, "A2": 0.0})
    book = g["S1"] + g["A2"]
    assert book[0, 12] == 1.0 and book[0, 16] == 1.0, "the position was dropped on handover"
    assert g["S1"][0, 11] == 1.0          # S1 owns it early
    assert g["A2"][0, 18] == 1.0          # A2 owns it late
    assert np.all(book[0, 10:20] == 1.0)  # unbroken throughout


# --------------------------------------------------------------------------
# Amendment 2 -- TOTAL binds globally
# --------------------------------------------------------------------------


def test_total_capital_is_never_over_committed():
    rng = np.random.default_rng(4)
    n, T, start = 8, 200, 10
    d = {a: (rng.random((n, T)) > 0.4).astype(float) for a in ("S1", "A2")}
    for total, r1, r2 in ((1.0, 0.0, 0.0), (0.5, 0.25, 0.25), (0.5, 0.0, 0.0),
                          (0.25, 0.10, 0.10), (0.75, 0.0, 0.0)):
        g, _ = R.allocate(d, start, total, {"S1": r1, "A2": r2})
        book = g["S1"] + g["A2"]
        assert book.max() <= 1.0
        deployed = book[:, start:].mean(axis=0)
        assert deployed.max() <= total + 1e-9, f"over-committed at total={total}"


def test_reserves_exceeding_total_are_rejected():
    d = _demand()
    with pytest.raises(AssertionError):
        R.allocate(d, 5, 0.5, {"S1": 0.4, "A2": 0.4})


# --------------------------------------------------------------------------
# The allocator's declared behaviour
# --------------------------------------------------------------------------


def test_an_incumbent_is_never_evicted_for_a_newcomer():
    """FCFS on daily bars means incumbency. Capital is tight; the arm already
    holding keeps it, and the newcomer is denied."""
    n, T, start = 4, 30, 2
    d = _demand(n, T, start)
    d["S1"][0, 5:25] = 1.0                    # holds one name throughout
    d["A2"][1:4, 10:25] = 1.0                 # three newcomers arrive later
    g, info = R.allocate(d, start, 1.0 / n, {"S1": 0.0, "A2": 0.0})   # room for ONE
    assert np.all(g["S1"][0, 6:24] == 1.0), "the incumbent was evicted"
    assert g["A2"][:, 10:24].sum() == 0.0, "a newcomer was funded over an incumbent"
    assert info["denied"]["A2"] > 0


def test_rationing_denies_entries_rather_than_shrinking_positions():
    """Every granted position is full size. D236 scaled; D241 denies."""
    rng = np.random.default_rng(7)
    n, T, start = 10, 120, 5
    d = {a: (rng.random((n, T)) > 0.5).astype(float) for a in ("S1", "A2")}
    g, _ = R.allocate(d, start, 0.3, {"S1": 0.0, "A2": 0.0})
    vals = np.unique(np.concatenate([g["S1"].ravel(), g["A2"].ravel()]))
    assert set(vals.tolist()) <= {0.0, 1.0}, f"a fractional position appeared: {vals}"


def test_the_allocator_is_inert_at_full_capital():
    """C0 must be the plain union -- nothing to ration, so nothing rationed."""
    rng = np.random.default_rng(11)
    n, T, start = 6, 150, 8
    d = {a: (rng.random((n, T)) > 0.6).astype(float) for a in ("S1", "A2")}
    d = {a: v for a, v in d.items()}
    for a in d:
        d[a][:, :start] = 0.0
    g, info = R.allocate(d, start, 1.0, {"S1": 0.0, "A2": 0.0})
    np.testing.assert_array_equal(g["S1"] + g["A2"], np.maximum(d["S1"], d["A2"]))
    assert info["binds_fraction"] == 0.0
    assert info["denied"]["S1"] == 0 and info["denied"]["A2"] == 0


# --------------------------------------------------------------------------
# The artifact records what the write-up claims
# --------------------------------------------------------------------------


def test_the_arms_did_not_move():
    assert SUMMARY["solo"]["S1"]["excess_sharpe"] == pytest.approx(0.746, abs=5e-4)
    assert SUMMARY["solo"]["A2"]["excess_sharpe"] == pytest.approx(0.822, abs=5e-4)


def test_c0_never_rationed():
    assert SUMMARY["allocation"]["C0"]["binds_fraction"] == 0.0
    assert SUMMARY["allocation"]["C0"]["denied_rate_S1"] == 0.0
    assert SUMMARY["allocation"]["C0"]["denied_rate_A2"] == 0.0


def test_the_closed_form_overstated_the_built_book():
    """D240 reported 1.032; the book delivers less, because the closed form
    assumes OPTIMAL weights and the union holds each arm at natural exposure."""
    assert SUMMARY["closed_form_prediction"] > SUMMARY["cells"]["C0"]["excess_sharpe"]
    assert SUMMARY["closed_form_prediction"] == pytest.approx(1.032, abs=5e-3)


def test_the_verdict_the_record_reports():
    assert SUMMARY["m1"]["clears_M1"] is False        # beats S1, interval contains zero
    assert SUMMARY["m1"]["delta_vs_S1"] > 0.0
    assert -0.05 < SUMMARY["m1"]["p05"] < 0.0         # fails by a hair
    assert SUMMARY["m2"]["clears_M2"] is False
    assert SUMMARY["m3"]["clears_M3"] is True         # sharing beats partitioning


def test_m3_survives_both_symbol_orderings():
    """The magnitude is order-dependent; the DIRECTION must not be."""
    f, r = SUMMARY["cells"], SUMMARY["reverse_order_sharpe"]
    assert f["C1"]["excess_sharpe"] - f["C2"]["excess_sharpe"] > 0.0
    assert r["C1"] - r["C2"] > 0.0


def test_every_hurdle_leg_is_present():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    for k in R.CELL_ORDER:
        for a in R.ARMS:
            assert {"delta", "p05", "p95", "excludes_zero"} <= set(SUMMARY["bootstrap"][k][a])
        assert {"binds_fraction", "denied_rate_S1", "max_deployed"} <= set(
            SUMMARY["allocation"][k]
        )
    assert set(SUMMARY["m4"]) == {"C1", "C2", "C3", "C4"}


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "docs" / "results" / "COMBINED_BOOK_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
