"""Gates for D230's bootstrap sweep.

The load-bearing one is the reproduction gate: if this sweep silently scored
something other than the published deltas, every conclusion in D230 would be
about arms nobody ran.
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
        "rbs", REPO / "scripts" / "run_bootstrap_sweep.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["rbs"] = module
    spec.loader.exec_module(module)
    return module


R = _load()
ARTIFACT = json.loads(
    (REPO / "data" / "bootstrap_sweep_summary.json").read_text(encoding="utf-8")
)


# --------------------------------------------------------------------------
# The audit covers what it says it covers
# --------------------------------------------------------------------------


def test_every_published_delta_field_exists_in_its_committed_artifact():
    """The field names in DELTAS are the audit. A name that does not exist in the
    committed summary means the sweep is scoring something other than what was
    reported -- silently, and with a plausible-looking number."""
    ladder = json.loads(
        (REPO / "data" / "macd_ladder_summary.json").read_text(encoding="utf-8")
    )
    impulse = json.loads(
        (REPO / "data" / "impulse_macd_summary.json").read_text(encoding="utf-8")
    )
    for study, _label, _a, _b, field in R.DELTAS:
        if field is None:
            continue
        source = ladder if study == "D217" else impulse
        for row in source["deltas"]:
            assert field in row, f"{field} missing from {study}'s committed deltas"


def test_the_sweep_covers_twenty_four_deltas():
    assert len(R.DELTAS) * len(R.BOOKS) * len(R.GATES) == 24
    assert ARTIFACT["n_deltas"] == 24


def test_all_three_studies_are_represented():
    assert {d[0] for d in R.DELTAS} == {"D217", "D218", "D229"}


def test_each_study_is_swept_at_its_own_warm_up_start():
    """A delta recomputed on a different span is not the delta that was reported.
    D217's arms start at 393 and D218's at 1,000, and mixing them would silently
    compare different spans."""
    assert ARTIFACT["starts"]["D217"] == 393
    assert ARTIFACT["starts"]["D218"] == 1000
    assert ARTIFACT["starts"]["D229"] == ARTIFACT["starts"]["D218"]


# --------------------------------------------------------------------------
# The reproduction gate -- the integrity check
# --------------------------------------------------------------------------


def test_the_committed_run_reproduced_cleanly():
    assert ARTIFACT["reproduction_clean"] is True
    assert ARTIFACT["reproduction_failures"] == []


def test_every_row_reproduced_inside_tolerance():
    for row in ARTIFACT["rows"]:
        if row["reproduction_drift"] is not None:
            assert row["reproduction_drift"] <= R.REPRO_TOL, row


def test_every_row_carries_the_published_value_it_was_checked_against():
    """A row with `published: null` would be an unchecked row wearing the same
    formatting as a checked one."""
    for row in ARTIFACT["rows"]:
        assert row["published"] is not None, row


def test_the_reproduction_tolerance_is_tight():
    assert R.REPRO_TOL == 1e-9


def test_committed_point_reads_the_real_artifacts():
    """Not a stub: the published value for a known cell must match the summary."""
    ladder = json.loads(
        (REPO / "data" / "macd_ladder_summary.json").read_text(encoding="utf-8")
    )
    expected = next(
        r["signal_minus_zero"]
        for r in ladder["deltas"]
        if r["book"] == "long_flat" and r["gate"] == "none"
    )
    got = R.committed_point("D217", "signal_minus_zero", "long_flat", "none")
    assert got == pytest.approx(expected, abs=0.0)


# --------------------------------------------------------------------------
# The two readings
# --------------------------------------------------------------------------


def test_as_claimed_is_strictly_stronger_than_as_scored():
    """The claimed hurdle adds a leg; it can never pass where the scored one fails."""
    for row in ARTIFACT["rows"]:
        if row["as_claimed"]:
            assert row["as_scored"], row


def test_as_scored_matches_the_hurdle_the_runners_applied():
    for row in ARTIFACT["rows"]:
        assert row["as_scored"] == (row["point"] >= ARTIFACT["delta_hurdle"])


def test_as_claimed_requires_both_legs():
    h = ARTIFACT["delta_hurdle"]
    for row in ARTIFACT["rows"]:
        assert row["as_claimed"] == (row["point"] >= h and row["p05"] > h)


def test_straddles_zero_is_computed_from_the_interval():
    for row in ARTIFACT["rows"]:
        assert row["straddles_zero"] == (row["p05"] < 0.0 < row["p95"])


def test_the_interval_is_ordered():
    for row in ARTIFACT["rows"]:
        assert row["p05"] <= row["p50"] <= row["p95"], row


def test_counts_agree_with_the_rows():
    rows = ARTIFACT["rows"]
    assert ARTIFACT["n_as_scored"] == sum(r["as_scored"] for r in rows)
    assert ARTIFACT["n_as_claimed"] == sum(r["as_claimed"] for r in rows)
    assert ARTIFACT["n_changed_verdict"] == ARTIFACT["n_as_scored"] - ARTIFACT["n_as_claimed"]
    assert ARTIFACT["n_straddling_zero"] == sum(r["straddles_zero"] for r in rows)


# --------------------------------------------------------------------------
# This spends no looks
# --------------------------------------------------------------------------


def test_the_sweep_evaluates_no_new_configuration():
    """Every rung swept must already belong to D217, D218 or D229. A rung that
    appears here and nowhere else would be a new look wearing an audit's clothes."""
    known = set(R.L.RUNGS) | set(R.I.RUNGS) | {"I0_jerk", "I1_signal"}
    for _study, _label, a, b, _field in R.DELTAS:
        assert a in known, a
        assert b in known, b


def test_the_sweep_reuses_d229s_bootstrap_rather_than_reimplementing_it():
    src = (REPO / "scripts" / "run_bootstrap_sweep.py").read_text(encoding="utf-8")
    assert "J.paired_block_bootstrap" in src
    assert "def paired_block_bootstrap" not in src


def test_arm_vs_benchmark_is_computed_and_carries_its_interval():
    """The comparison the 24-delta sweep did not cover, and the one the programme
    is carrying forward. It lives in the artifact so it is reproducible rather
    than a number quoted once in conversation."""
    a = ARTIFACT["arm_vs_benchmark"]
    assert a["point"] == pytest.approx(
        a["arm_excess_sharpe"] - a["bh_excess_sharpe"], rel=1e-12
    )
    assert a["p05"] <= a["p50"] <= a["p95"]
    assert a["straddles_zero"] == (a["p05"] < 0.0 < a["p95"])


def test_arm_vs_benchmark_uses_the_excess_sharpe_basis_not_the_rung_basis():
    """Rung deltas are audited price-only, rf=0, because that is how they were
    reported. This comparison was reported on excess Sharpe with rf on the
    exposed fraction, so it is audited on that. Mixing the two would compare
    numbers nobody published."""
    src = (REPO / "scripts" / "run_bootstrap_sweep.py").read_text(encoding="utf-8")
    body = src.split("def arm_vs_benchmark")[1].split("def build")[0]
    assert "total_return=True" in body
    assert "J.RF_PER_BAR" in body
    assert "exposure * J.RF_PER_BAR" in body


def test_deltas_are_audited_on_the_basis_they_were_reported_on():
    """Price-only, rf=0 -- D217's and D218's reporting basis. Auditing on a better
    basis would answer a question nobody asked."""
    src = (REPO / "scripts" / "run_bootstrap_sweep.py").read_text(encoding="utf-8")
    body = src.split("def _series")[1].split("def collect")[0]
    assert "total_return" not in body
