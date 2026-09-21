"""Golden tests for the deposit docs' power tables (D588).

The ledger of record is `LETF_CLOSE_FLOW_PREREG.md` §6A and §6B, with one clustered
row from `SETTLEMENT_FLOW_LEDGER_PREREG.md` §9A.1. Hand arithmetic in
test_power_ledger.hand.txt, per D39: every constant below was worked out there
before the module was run, and the docs' own rounded quotes ("~0.045 sigma",
"~0.09 sigma", "0.020", "0.040 corr", "~0.058 sigma", "~0.115 sigma") are asserted
alongside the exact values, so a change that keeps the code self-consistent but
drifts from the published tables still fails.

No market fixture is read; these are planning numbers.
"""

from __future__ import annotations

import pytest

from backtest_framework.validation.power import (
    forward_evaluation_days,
    power_row,
    track3_route,
    write_power_md,
)

TOLERANCE = 1e-12  # the arithmetic is closed-form; nothing here needs slack

# LETF §6A, H1 primary cell. The doc's default plausible-effect statement is "MDE at
# or below round-trip cost"; 0.06 sigma is the value declared for this golden, and it
# is what splits the cell's own planned range (see the .hand.txt).
H1_PLAUSIBLE_SIGMA = 0.06


def _h1_row(n: int):
    return power_row(
        stage="LETF close flow / H1",
        test="Primary cell, active days at k = 3, per instrument",
        n=n,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=H1_PLAUSIBLE_SIGMA,
        sigma=1.0,
        note="LETF 6A planning row; plausible effect = round-trip cost, 0.06 sigma",
    )


def test_case_1_h1_at_the_low_end_of_its_planned_range_is_underpowered():
    row = _h1_row(500)
    assert row.n_eff == pytest.approx(500.0, abs=TOLERANCE)
    assert row.units == "sigma"
    assert row.se == pytest.approx(0.044721359549995794, abs=TOLERANCE)
    assert row.mde_t2 == pytest.approx(0.08944271909999159, abs=TOLERANCE)
    assert row.mde_80 == pytest.approx(0.12521980673998823, abs=TOLERANCE)
    # the doc's own rounding: "~0.045 sigma" and "~0.09 sigma"
    assert row.se == pytest.approx(0.045, abs=5e-4)
    assert row.mde_t2 == pytest.approx(0.09, abs=1e-3)
    assert row.power_class == "underpowered"
    assert row.adoption_by_significance_blocked is True


def test_case_2_the_same_cell_at_the_high_end_is_individually_testable():
    row = _h1_row(1_500)
    assert row.n_eff == pytest.approx(1_500.0, abs=TOLERANCE)
    assert row.se == pytest.approx(0.025819888974716113, abs=TOLERANCE)
    assert row.mde_t2 == pytest.approx(0.051639777949432225, abs=TOLERANCE)
    assert row.mde_80 == pytest.approx(0.07229568912920512, abs=TOLERANCE)
    # the doc's own rounding: "~0.026 sigma" and "~0.05 sigma"
    assert row.se == pytest.approx(0.026, abs=5e-4)
    assert row.mde_t2 == pytest.approx(0.05, abs=2e-3)
    assert row.power_class == "individually_testable"
    assert row.adoption_by_significance_blocked is False


def test_case_2b_one_planned_range_straddles_the_adoption_rule():
    """The doc quotes H1's n_eff as "~500-1,500" as if it were one cell. Against the
    declared 0.06 sigma it is two: §9A.2 rule 3 blocks adoption at one end and permits
    it at the other. That is the finding this golden pair exists to hold."""
    low, high = _h1_row(500), _h1_row(1_500)
    assert low.adoption_by_significance_blocked != high.adoption_by_significance_blocked
    assert low.mde_t2 > H1_PLAUSIBLE_SIGMA >= high.mde_t2


def test_case_3_clustered_row_joins_ledger_tests_51_and_52():
    """Ledger §9A.1's C3 attention row, reached through the design effect: m = 10 and
    rho = 0.1 (test 51) take n = 4,750 to n_eff = 2,500, whose SE is 0.020 and MDE
    0.040 corr (test 52) — exactly the doc's planned figures."""
    row = power_row(
        stage="Ledger C3 / attention (continuous, H11a)",
        test="Attention vs ETF signed volume, day-clustered",
        n=4_750,
        m=10.0,
        rho=0.1,
        track="1",
        plausible_effect=0.04,
        note="ledger 9A.1; design effect 1.9 from tests 51/52",
    )
    assert row.units == "correlation"
    assert row.n_eff == pytest.approx(2_500.0, abs=TOLERANCE)
    assert row.se == pytest.approx(0.02, abs=TOLERANCE)
    assert row.mde_t2 == pytest.approx(0.04, abs=TOLERANCE)
    assert row.mde_80 == pytest.approx(0.056, abs=TOLERANCE)
    # §9A.2 rule 3 is strict: MDE == plausible effect is testable, not underpowered.
    assert row.mde_t2 == pytest.approx(row.plausible_effect, abs=TOLERANCE)
    assert row.power_class == "individually_testable"


def test_case_4_track3_target_matches_the_doc_and_routes_on_the_boundary():
    """LETF §6B / ledger §13A.7(4): "at N = 300 trades, SE ~= 0.058 sigma and the MDE
    (t = 2) ~= 0.115 sigma"."""
    route = track3_route(0.08)
    assert route.se == pytest.approx(0.05773502691896257, abs=TOLERANCE)
    assert route.mde == pytest.approx(0.11547005383792514, abs=TOLERANCE)
    assert route.se == pytest.approx(0.058, abs=5e-4)
    assert route.mde == pytest.approx(0.115, abs=5e-4)
    assert route.route == "combined_evidence"
    assert track3_route(0.15).route == "efficacy_n300"
    assert track3_route(0.11547005383792514).route == "efficacy_n300"


def test_case_5_forward_evaluation_length_ledger_unit_test_59():
    forward = forward_evaluation_days(0.1, 2)
    assert (forward.n_needed, forward.evaluation_days, forward.route) == (400.0, 200.0, "forward")
    routed = forward_evaluation_days(0.05, 2)
    assert (routed.n_needed, routed.evaluation_days, routed.route) == (1_600.0, None, "9B")


def test_the_rendered_table_carries_its_provenance_and_the_row_values(tmp_path):
    """A power table without the "recomputed on real data" line is a set of numbers
    that looks measured and is not, so the header is part of the golden."""
    rows = [
        _h1_row(500),
        _h1_row(1_500),
        power_row(
            stage="Ledger C3 / attention (continuous, H11a)",
            test="Attention vs ETF signed volume, day-clustered",
            n=4_750,
            m=10.0,
            rho=0.1,
            track="1",
            plausible_effect=0.04,
        ),
    ]
    path = write_power_md(rows, tmp_path / "letf" / "POWER.md", date="2026-09-21", title="POWER")
    text = path.read_text(encoding="utf-8")

    assert text.startswith("# POWER\n")
    assert "**Generated:** 2026-09-21" in text
    assert "backtest_framework.validation.power` (D588)" in text
    assert "recomputed on real data before each stage runs" in text.replace("**", "")
    assert "Ledger" in text and "9A.1" in text

    header = [line for line in text.splitlines() if line.startswith("| Stage |")]
    assert len(header) == 1
    for column in ("n_eff", "SE", "MDE (t = 2)", "MDE (80%)", "Plausible effect", "Power class"):
        assert column in header[0]

    body = [line for line in text.splitlines() if line.startswith("| LETF close flow")]
    assert len(body) == 2
    assert "0.0447" in body[0] and "0.0894" in body[0] and "underpowered" in body[0]
    assert "BLOCKED" in body[0]
    assert "0.0258" in body[1] and "0.0516" in body[1] and "individually_testable" in body[1]
    assert "permitted" in body[1]

    clustered = [line for line in text.splitlines() if line.startswith("| Ledger C3")]
    assert len(clustered) == 1
    assert "2,500.0" in clustered[0] and "correlation" in clustered[0]
    assert "0.0200" in clustered[0] and "0.0400" in clustered[0] and "0.0560" in clustered[0]

    # D550: the newline is pinned, so the bytes are the same on every OS.
    assert b"\r\n" not in path.read_bytes()
