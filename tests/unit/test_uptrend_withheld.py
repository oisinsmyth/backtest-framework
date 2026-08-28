"""Gates for D242's withheld-data verdict.

A holdout test has exactly two ways to be worthless, and both are pinned here:

  * the rule DRIFTED between the mined run and the holdout run -- so every frozen
    constant is asserted, and the runner must reproduce the mined numbers before
    it is allowed to touch the withheld fixture;
  * the two fixtures got crossed -- so the holdout's symbol set is asserted
    disjoint from the mined one.

The rest pins what the record claims: A0 grew, the stop's edge did not replicate,
and the combined book's interval still contains zero.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "uw", REPO / "scripts" / "run_uptrend_withheld.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["uw"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "uptrend_withheld_summary.json").read_text(encoding="utf-8")
)


# --------------------------------------------------------------------------
# The rule did not drift, and the fixtures are not crossed
# --------------------------------------------------------------------------


def test_every_constant_is_frozen_against_the_mined_runner():
    """If one differs, the holdout measured a different rule and the test is void.
    Importing the module already asserts this; re-assert so it is visible here."""
    for k, v in R.FROZEN.items():
        assert getattr(R.U, k) == v, f"{k} drifted"
    assert R.FROZEN == {"K": 3, "WINDOW": 252, "AGE_CAP": 63, "ATR_WINDOW": 21,
                        "STOP_ATR": 1.0, "FLOOR_ATR": 2.0, "FIXED_STOP": 0.08,
                        "TARGET_R": 2.0}


def test_the_runner_reproduces_the_mined_numbers():
    """A holdout runner that cannot reproduce the training result is measuring
    something else. D240 published +0.610 / +0.822, D237 published +0.746."""
    rep = SUMMARY["mined_reproduction"]
    assert rep["A0"] == pytest.approx(0.610, abs=5e-4)
    assert rep["A2"] == pytest.approx(0.822, abs=5e-4)
    assert rep["S1"] == pytest.approx(0.746, abs=5e-4)


def test_the_two_universes_share_no_tickers():
    """The whole point of an instrument holdout."""
    import csv
    import gzip

    def syms(path):
        out = set()
        with gzip.open(path, "rt") as f:
            for row in csv.DictReader(f):
                out.add(row["symbol"])
        return out

    mined = syms(R.FIXTURES["mined"][0])
    held = syms(R.FIXTURES["holdout"][0])
    assert len(mined) == 57 and len(held) == 60
    assert not (mined & held), f"the fixtures overlap: {sorted(mined & held)}"
    assert SUMMARY["n_symbols"] == 60


def test_the_anti_triviality_floor_is_set_the_way_d237_set_its_own():
    """25% of the mined delta over buy-and-hold."""
    assert R.H3_FLOOR == pytest.approx(0.25 * (0.822 - 0.235), abs=1e-9)
    assert SUMMARY["h3_floor"] == pytest.approx(0.147, abs=1e-3)


# --------------------------------------------------------------------------
# What the record claims
# --------------------------------------------------------------------------


def test_the_entry_rule_replicated_and_grew():
    v, c = SUMMARY["verdict"]["A0"], SUMMARY["cells"]["A0"]
    assert v["clears_all"] is True
    assert c["excess_sharpe"] > v["mined"], "A0 did not grow"
    assert v["shrinkage"] > 0
    n = SUMMARY["nulls"]["A0"]
    assert n["percentile_of_actual"] > 95.0
    assert n["money_percentile_of_actual"] > 95.0   # the leg volatility cannot inflate
    assert v["delta_vs_bh"] > 2 * SUMMARY["h3_floor"]


def test_the_stop_did_not_replicate():
    """R3, registered in advance against the result I most wanted to be true.
    99.6th on mined data, well below p95 here."""
    h4 = SUMMARY["overlay_null"]
    assert h4["clears_H4"] is False
    assert 50.0 < h4["percentile_of_actual"] < 95.0


def test_the_stop_still_reduces_drawdown_mechanically():
    """It is a risk control, not alpha -- and the record must be able to say both."""
    a0, a2 = SUMMARY["cells"]["A0"], SUMMARY["cells"]["A2"]
    assert a2["max_drawdown"] > a0["max_drawdown"]          # less negative
    assert a2["exposure_gross"] < a0["exposure_gross"]      # by holding less


def test_the_combined_book_splits_the_same_way_as_in_sample():
    cm = SUMMARY["combined"]
    assert cm["clears_H5"] is True      # beats S1 on the point estimate
    assert cm["clears_H6"] is False     # and the interval still contains zero
    assert cm["p05"] < 0.0


def test_the_combined_book_beat_buy_and_hold_on_money_and_drawdown():
    c0, bh = SUMMARY["cells"]["C0"], SUMMARY["buy_and_hold"]
    assert SUMMARY["deployable_return"]["C0"] > bh["cagr"]
    assert c0["max_drawdown"] > bh["max_drawdown"]          # far less negative


def test_the_diversification_travelled():
    """rho was predicted from CONSTRUCTION, not fitted -- so it should hold."""
    assert 0.0 < SUMMARY["rho_S1_A2"] < 0.30


def test_the_weakest_part_of_the_case_is_recorded():
    for k in ("A0", "A2"):
        assert SUMMARY["cells"][k]["clears_E"] is False
        assert SUMMARY["cells"][k]["min_entries_per_symbol"] < 30
    assert SUMMARY["arm_closed"] is False


def test_every_hurdle_leg_is_present():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    for k in ("A0", "A2"):
        assert {"clears_H1", "clears_H2", "clears_H3", "clears_all", "delta_vs_bh",
                "mined", "shrinkage"} <= set(SUMMARY["verdict"][k])
        assert {"percentile_of_actual", "money_percentile_of_actual",
                "clears_H2"} <= set(SUMMARY["nulls"][k])
    assert {"clears_H4", "n_cut", "p95"} <= set(SUMMARY["overlay_null"])
    assert {"clears_H5", "clears_H6", "p05", "p95"} <= set(SUMMARY["combined"])


def test_the_declared_reading_matches_the_outcome():
    both = (SUMMARY["verdict"]["A0"]["clears_all"], SUMMARY["verdict"]["A2"]["clears_all"])
    assert both == (True, True)
    assert "STRONGEST RESULT" in SUMMARY["reading"]


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "UPTREND_WITHHELD_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
