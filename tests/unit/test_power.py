"""Unit tests for `validation/power.py` (D588).

Six of these carry a deposit-document unit-test number in the function name
(`SETTLEMENT_FLOW_LEDGER_PREREG.md` §12, tests 51, 52, 53, 59, 62, 63), so a
reader can go from the doc's numbered requirement to the test that pins it
without a search. The rest are the guards: every raise the module promises, plus
the two checks that are not arithmetic at all — that the ANOVA ICC recovers a
known value on synthetic two-level data, and that the ported cross-series count
equals `scripts/ragged_panel.py:effective_instruments` to 1e-12.

Nothing here reads a market fixture.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.power import (
    Z80_TWO_SIDED,
    Z80_TWO_SIDED_EXACT,
    design_effect,
    forward_evaluation_days,
    icc_from_clusters,
    mde,
    mde_80,
    n_eff,
    n_eff_cross_series,
    n_eff_from_clusters,
    power_class,
    power_row,
    se_correlation,
    se_mean,
    track3_route,
    validate_track_map,
    write_power_md,
)

REPO = Path(__file__).resolve().parents[2]
TOLERANCE = 1e-12


# --------------------------------------------------------------------------- the six named tests


def test_ledger_51_design_effect_m10_rho01_gives_n_over_1p9():
    """Ledger test 51: "Design effect: m = 10 and rho = 0.1 give n_eff = n / 1.9"."""
    assert design_effect(10.0, 0.1) == pytest.approx(1.9, abs=TOLERANCE)
    for n in (100, 1_900, 5_000):
        assert n_eff(n, 10.0, 0.1) == pytest.approx(n / 1.9, abs=TOLERANCE)
    assert n_eff(1_900, 10.0, 0.1) == pytest.approx(1_000.0, abs=TOLERANCE)


def test_ledger_52_mde_calculation_at_n_eff_2500():
    """Ledger test 52: "n_eff = 2,500 gives SE = 0.02, MDE_t2 = 0.04, MDE_80 = 0.056"."""
    se = se_correlation(2_500.0)
    assert se == pytest.approx(0.02, abs=TOLERANCE)
    assert mde(se) == pytest.approx(0.04, abs=TOLERANCE)
    assert mde_80(se) == pytest.approx(0.056, abs=TOLERANCE)
    # The doc pre-registers the rounded 2.8, not z_0.975 + z_0.80; the module uses
    # 2.8 exactly and records the true sum. The gap is ~0.6%, well inside the
    # planning precision these tables are quoted to, but it is a choice, not an
    # accident, so it is asserted.
    assert Z80_TWO_SIDED == 2.8
    assert Z80_TWO_SIDED_EXACT == pytest.approx(2.801585218112969, abs=1e-15)
    assert abs(Z80_TWO_SIDED - Z80_TWO_SIDED_EXACT) < 0.002


def test_ledger_53_underpowered_stage_blocks_adoption_by_significance():
    """Ledger test 53: "A stage whose MDE exceeds its recorded plausible effect is
    labelled underpowered, and adoption by individual significance is blocked"."""
    assert power_class(0.13, 0.05) == "underpowered"
    assert power_class(0.028, 0.05) == "individually_testable"
    # Equality is NOT underpowered: §9A.2 rule 3 says "if MDE_t2 > the plausible effect".
    assert power_class(0.05, 0.05) == "individually_testable"

    row = power_row(
        stage="G: P9 non-US ETPs",
        test="Marginal flow (forward, pooled)",
        n=240,
        m=1.0,
        rho=0.0,
        track="2",
        plausible_effect=0.05,
        note="ledger 9A.1 row: n_eff ~240, SE 0.065, MDE 0.13",
    )
    assert row.mde_t2 == pytest.approx(2.0 / math.sqrt(240.0), abs=TOLERANCE)
    assert row.mde_t2 > row.plausible_effect
    assert row.power_class == "underpowered"
    assert row.adoption_by_significance_blocked is True

    testable = power_row(
        stage="A: P1 rebalance",
        test="Flow (all days, NG+CL)",
        n=5_000,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=0.05,
    )
    assert testable.power_class == "individually_testable"
    assert testable.adoption_by_significance_blocked is False


def test_ledger_59_forward_evaluation_length_and_the_cap():
    """Ledger test 59: "plausible effect 0.1 with 2 instruments gives n_needed = 400
    and 200 evaluation days; a plausible effect of 0.05 gives n_needed = 1,600,
    exceeds the cap, and routes the stage to 9B"."""
    plan = forward_evaluation_days(0.1, 2)
    assert plan.n_needed == pytest.approx(400.0, abs=TOLERANCE)
    assert plan.evaluation_days == pytest.approx(200.0, abs=TOLERANCE)
    assert plan.route == "forward"

    capped = forward_evaluation_days(0.05, 2)
    assert capped.n_needed == pytest.approx(1_600.0, abs=TOLERANCE)
    assert capped.evaluation_days is None
    assert capped.route == "9B"

    # The 120-day floor binds when the arithmetic asks for less (§13A.7(2)).
    floored = forward_evaluation_days(0.2, 2)
    assert floored.n_needed == pytest.approx(100.0, abs=TOLERANCE)
    assert floored.evaluation_days == pytest.approx(120.0, abs=TOLERANCE)
    assert floored.route == "forward"

    # Exactly at the cap is inside it, not over it (the rule says "capped at 500",
    # and a length equal to the cap has not exceeded it).
    at_cap = forward_evaluation_days(0.1, 2, cap=200.0)
    assert at_cap.evaluation_days == pytest.approx(200.0, abs=TOLERANCE)
    assert at_cap.route == "forward"
    assert forward_evaluation_days(0.1, 2, cap=199.0).route == "9B"


def test_ledger_62_track3_power_check_routes_on_the_edge_estimate():
    """Ledger test 62: "an edge estimate of 0.08 sigma selects the combined-evidence
    route; 0.15 sigma selects the N = 300 efficacy route"."""
    low = track3_route(0.08)
    assert low.se == pytest.approx(1.0 / math.sqrt(300.0), abs=TOLERANCE)
    assert low.se == pytest.approx(0.058, abs=5e-4)  # the docs' rounded 0.058 sigma
    assert low.mde == pytest.approx(0.115, abs=5e-4)  # and their 0.115 sigma
    assert low.route == "combined_evidence"

    high = track3_route(0.15)
    assert high.route == "efficacy_n300"

    # "at or above" — the boundary belongs to the efficacy route.
    assert track3_route(low.mde).route == "efficacy_n300"
    assert track3_route(math.nextafter(low.mde, 0.0)).route == "combined_evidence"


def test_ledger_63_track_map_validation_names_the_missing_statement():
    """Ledger test 63: "every stage has a track, a power class, n_eff, SE, MDE and a
    plausible-effect statement before it runs"."""
    complete = power_row(
        stage="A: P1 rebalance",
        test="Price (trade days)",
        n=1_500,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=0.06,
        sigma=1.0,
    )
    assert validate_track_map([complete]) is None

    no_statement = power_row(
        stage="E: P2 netting (COT prior)",
        test="Weekly swap-dealer fit",
        n=520,
        m=1.0,
        rho=0.0,
        track="1",
        plausible_effect=None,
    )
    with pytest.raises(ValueError, match="plausible-effect statement"):
        validate_track_map([complete, no_statement])
    # The message names the offending ROW, not just the field.
    with pytest.raises(ValueError, match="P2 netting"):
        validate_track_map([complete, no_statement])

    no_track = power_row(
        stage="F: P8a fund rolls",
        test="Flow on roll days",
        n=1_200,
        m=1.0,
        rho=0.0,
        track="   ",
        plausible_effect=0.05,
    )
    with pytest.raises(ValueError, match="a track"):
        validate_track_map([no_track])

    with pytest.raises(ValueError, match="empty TRACK_MAP"):
        validate_track_map([])


# --------------------------------------------------------------------------- guards


@pytest.mark.parametrize("m", [0.0, 0.5, -3.0])
def test_design_effect_raises_below_one_observation_per_cluster(m):
    with pytest.raises(ValueError, match="m >= 1"):
        design_effect(m, 0.1)


@pytest.mark.parametrize("rho", [1.0001, 2.0, -0.2, -1.0])
def test_design_effect_raises_on_rho_outside_its_range(rho):
    # m = 10 -> the admissible interval is [-1/9, 1].
    with pytest.raises(ValueError, match="outside"):
        design_effect(10.0, rho)


def test_design_effect_accepts_the_boundary_rho_and_gives_zero():
    assert design_effect(10.0, 1.0) == pytest.approx(10.0, abs=TOLERANCE)
    assert design_effect(10.0, -1.0 / 9.0) == pytest.approx(0.0, abs=1e-15)


def test_design_effect_at_m_one_admits_any_rho_and_is_the_identity():
    for rho in (-1.0, 0.0, 1.0, -0.37):
        assert design_effect(1.0, rho) == 1.0
    with pytest.raises(ValueError, match="finite"):
        design_effect(1.0, float("nan"))


@pytest.mark.parametrize("bad_n_eff", [1.9999, 1.0, 0.0, -5.0])
def test_se_raises_below_two_effective_observations(bad_n_eff):
    with pytest.raises(ValueError, match="n_eff >= 2"):
        se_correlation(bad_n_eff)
    with pytest.raises(ValueError, match="n_eff >= 2"):
        se_mean(0.01, bad_n_eff)


def test_n_eff_raises_on_a_zero_observation_count():
    with pytest.raises(ValueError, match="n >= 1"):
        n_eff(0, 10.0, 0.1)


def test_n_eff_raises_at_the_degenerate_floor_rather_than_dividing_by_zero():
    """rho exactly at -1/(m-1) is inside `design_effect`'s domain and gives 0. That is
    a division by zero dressed as infinite power, so `n_eff` refuses it."""
    assert design_effect(5.0, -0.25) == pytest.approx(0.0, abs=1e-15)
    with pytest.raises(ValueError, match="undefined"):
        n_eff(1_000, 5.0, -0.25)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan"), float("inf")])
def test_mde_and_mde_80_raise_on_a_non_positive_se(bad):
    with pytest.raises(ValueError):
        mde(bad)
    with pytest.raises(ValueError):
        mde_80(bad)


def test_mde_raises_on_a_non_positive_t():
    with pytest.raises(ValueError, match="positive finite t"):
        mde(0.02, t=0.0)


def test_power_class_raises_rather_than_classifying_a_zero_plausible_effect():
    with pytest.raises(ValueError, match="plausible effect"):
        power_class(0.04, 0.0)
    with pytest.raises(ValueError, match="positive finite mde"):
        power_class(0.0, 0.04)


def test_forward_evaluation_days_guards_its_inputs():
    with pytest.raises(ValueError, match="plausible effect"):
        forward_evaluation_days(0.0, 2)
    with pytest.raises(ValueError, match="at least 1 instrument"):
        forward_evaluation_days(0.1, 0)
    with pytest.raises(ValueError, match="floor <= cap"):
        forward_evaluation_days(0.1, 2, floor=600.0, cap=500.0)


def test_track3_route_guards_its_edge():
    with pytest.raises(ValueError, match="positive finite edge"):
        track3_route(0.0)
    with pytest.raises(ValueError, match="positive finite edge"):
        track3_route(float("nan"))


# --------------------------------------------------------------------------- the ICC


def test_icc_raises_on_fewer_than_two_clusters():
    with pytest.raises(ValueError, match="at least 2 clusters"):
        icc_from_clusters([1.0, 2.0, 3.0], [7, 7, 7])


def test_icc_raises_on_an_empty_cluster():
    """The empty-cluster guard has to be able to FIRE, and in the flat (values,
    cluster_ids) encoding it cannot: a label with no observations is a label that is
    simply absent from the array. So the module also accepts the grouped form, where
    losing a cluster is exactly what an empty sub-sequence means."""
    assert icc_from_clusters([[1.0, 2.0], [5.0, 6.0]]) == pytest.approx(
        icc_from_clusters([1.0, 2.0, 5.0, 6.0], [0, 0, 1, 1]), abs=TOLERANCE
    )
    with pytest.raises(ValueError, match="empty cluster at position 1"):
        icc_from_clusters([[1.0, 2.0], [], [5.0, 6.0]])
    with pytest.raises(ValueError, match="no clusters"):
        icc_from_clusters([])


def test_icc_raises_when_every_cluster_has_one_observation():
    """N == k: MSW has zero degrees of freedom, so there is no within-cluster mean
    square and the ratio is not defined."""
    with pytest.raises(ValueError, match="N > k"):
        icc_from_clusters([1.0, 2.0], ["a", "b"])
    with pytest.raises(ValueError, match="N > k"):
        icc_from_clusters([[1.0], [2.0], [3.0]])


def test_icc_raises_on_zero_total_variance():
    with pytest.raises(ValueError, match="zero total variance"):
        icc_from_clusters([4.0, 4.0, 4.0, 4.0], [0, 0, 1, 1])


def test_icc_raises_on_a_length_mismatch_and_on_a_nan():
    with pytest.raises(ValueError, match="differ in length"):
        icc_from_clusters([1.0, 2.0, 3.0], [0, 1])
    with pytest.raises(ValueError, match="non-finite"):
        icc_from_clusters([1.0, 2.0, float("nan"), 4.0], [0, 0, 1, 1])


@pytest.mark.parametrize("true_icc", [0.1, 0.5, 0.8])
def test_icc_recovers_a_known_two_level_variance_split(true_icc):
    """Synthetic two-level data: y_ij = b_i + e_ij with Var(b) = rho and Var(e) = 1 - rho,
    so the population ICC is exactly `true_icc`. 400 clusters x 15 observations is
    enough for the ANOVA estimator to land within 0.04."""
    rng = np.random.default_rng(588)
    k, per = 400, 15
    between = rng.normal(0.0, math.sqrt(true_icc), k)
    within = rng.normal(0.0, math.sqrt(1.0 - true_icc), k * per)
    values = np.repeat(between, per) + within
    ids = np.repeat(np.arange(k), per)
    assert icc_from_clusters(values, ids) == pytest.approx(true_icc, abs=0.04)


def test_icc_is_one_when_every_cluster_is_internally_identical():
    values = [1.0, 1.0, 1.0, 5.0, 5.0, 5.0, 9.0, 9.0, 9.0]
    ids = [0, 0, 0, 1, 1, 1, 2, 2, 2]
    assert icc_from_clusters(values, ids) == pytest.approx(1.0, abs=TOLERANCE)


def test_icc_can_be_negative_and_is_not_clamped():
    """Perfect anti-agreement inside each cluster: cluster means are identical, so
    MSB = 0 and the ANOVA ICC is -1/(n0 - 1) = -1. Clamping this at zero would
    understate the design effect, so the module does not clamp."""
    values = [1.0, -1.0, 1.0, -1.0, 1.0, -1.0]
    ids = [0, 0, 1, 1, 2, 2]
    assert icc_from_clusters(values, ids) == pytest.approx(-1.0, abs=1e-12)


def test_n_eff_from_clusters_uses_the_mean_cluster_size_and_the_icc():
    rng = np.random.default_rng(1588)
    k, per = 200, 12
    values = np.repeat(rng.normal(0.0, 1.0, k), per) + rng.normal(0.0, 1.0, k * per)
    ids = np.repeat(np.arange(k), per)
    rho = icc_from_clusters(values, ids)
    expected = (k * per) / (1.0 + (per - 1) * rho)
    assert n_eff_from_clusters(values, ids) == pytest.approx(expected, abs=1e-9)
    # Clustering costs sample: n_eff is well below the raw count.
    assert n_eff_from_clusters(values, ids) < 0.25 * k * per


def test_n_eff_from_clusters_handles_unequal_cluster_sizes():
    rng = np.random.default_rng(2588)
    sizes = [5, 9, 12, 3, 20, 7, 15, 11]
    values, ids = [], []
    for cluster, size in enumerate(sizes):
        values.extend(rng.normal(cluster * 2.0, 1.0, size))
        ids.extend([cluster] * size)
    total = sum(sizes)
    rho = icc_from_clusters(values, ids)
    mean_size = total / len(sizes)
    assert n_eff_from_clusters(values, ids) == pytest.approx(
        total / (1.0 + (mean_size - 1.0) * rho), abs=1e-9
    )


# --------------------------------------------------------------------------- cross-series parity


def _load_ragged_panel():
    """House pattern for reaching a research script (scripts/a1_er_stage0.py:99).
    The library may not import `scripts/`; a test may."""
    spec = importlib.util.spec_from_file_location(
        "ragged_panel_d588_test", REPO / "scripts" / "ragged_panel.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["ragged_panel_d588_test"] = module
    spec.loader.exec_module(module)
    return module


def _synthetic_panel(module, seed: int = 588, n: int = 7, T: int = 500):
    """A ragged panel: one common factor, staggered live windows so pairwise overlap
    varies and the `min_overlap` gate actually bites on at least one pair."""
    rng = np.random.default_rng(seed)
    common = rng.normal(0.0, 0.01, T)
    log_returns = np.array([0.7 * common + 0.7 * rng.normal(0.0, 0.01, T) for _ in range(n)])
    live = np.ones((n, T), dtype=bool)
    for i in range(n):
        live[i, : i * 70] = False
    log_returns[~live] = 0.0
    closes = np.where(live, 100.0 * np.exp(np.cumsum(log_returns, axis=1)), np.nan)
    symbols = [f"S{i}" for i in range(n)]
    return module.RaggedPanel(
        symbols=symbols,
        dates=[f"d{t:04d}" for t in range(T)],
        closes=closes,
        log_returns=log_returns,
        total_log_returns=log_returns.copy(),
        cost_fraction=np.zeros((n, T)),
        live=live,
        index_of={s: i for i, s in enumerate(symbols)},
    )


@pytest.mark.parametrize("min_overlap", [50, 250, 400])
@pytest.mark.parametrize("start", [0, 120])
def test_n_eff_cross_series_equals_the_script_it_was_ported_from(min_overlap, start):
    """The port is bit-for-bit, so the tolerance is the strictest one that means
    anything: 1e-12 absolute on a quantity of order 1-7."""
    module = _load_ragged_panel()
    panel = _synthetic_panel(module)
    ported = n_eff_cross_series(panel, start, min_overlap=min_overlap)
    original = module.effective_instruments(panel, start, min_overlap=min_overlap)
    assert ported == pytest.approx(original, abs=1e-12)
    assert ported == original  # in fact identical, not merely close


def test_n_eff_cross_series_is_n_on_uncorrelated_series_and_one_on_identical_ones():
    module = _load_ragged_panel()
    rng = np.random.default_rng(3588)
    n, T = 5, 600

    independent = rng.normal(0.0, 0.01, (n, T))
    live = np.ones((n, T), dtype=bool)
    panel = module.RaggedPanel(
        symbols=[f"I{i}" for i in range(n)],
        dates=[f"d{t}" for t in range(T)],
        closes=100.0 * np.exp(np.cumsum(independent, axis=1)),
        log_returns=independent,
        total_log_returns=independent.copy(),
        cost_fraction=np.zeros((n, T)),
        live=live,
        index_of={f"I{i}": i for i in range(n)},
    )
    assert n_eff_cross_series(panel, 0) == pytest.approx(n, rel=0.2)

    same = np.repeat(rng.normal(0.0, 0.01, (1, T)), n, axis=0)
    clone = module.RaggedPanel(
        symbols=[f"C{i}" for i in range(n)],
        dates=[f"d{t}" for t in range(T)],
        closes=100.0 * np.exp(np.cumsum(same, axis=1)),
        log_returns=same,
        total_log_returns=same.copy(),
        cost_fraction=np.zeros((n, T)),
        live=live,
        index_of={f"C{i}": i for i in range(n)},
    )
    assert n_eff_cross_series(clone, 0) == pytest.approx(1.0, abs=1e-9)


def test_n_eff_cross_series_guards_its_arguments():
    module = _load_ragged_panel()
    panel = _synthetic_panel(module)
    with pytest.raises(ValueError, match="start >= 0"):
        n_eff_cross_series(panel, -1)
    with pytest.raises(ValueError, match="min_overlap"):
        n_eff_cross_series(panel, 0, min_overlap=1)


# --------------------------------------------------------------------------- the row and writer


def test_power_row_carries_its_units_and_the_price_regime_scales_with_sigma():
    corr = power_row(stage="A", test="Flow", n=2_500, m=1.0, rho=0.0, track="1",
                     plausible_effect=0.05)
    assert corr.units == "correlation"
    assert corr.sigma is None
    assert corr.se == pytest.approx(0.02, abs=TOLERANCE)

    price = power_row(stage="A", test="Price", n=2_500, m=1.0, rho=0.0, track="1",
                      plausible_effect=0.05, sigma=0.011)
    assert price.units == "sigma"
    assert price.se == pytest.approx(0.011 * 0.02, abs=TOLERANCE)
    assert price.mde_t2 == pytest.approx(2.0 * 0.011 * 0.02, abs=TOLERANCE)


def test_power_row_applies_the_design_effect():
    row = power_row(stage="C3", test="Attention, day-clustered", n=4_750, m=10.0, rho=0.1,
                    track="1", plausible_effect=0.04)
    assert row.n_eff == pytest.approx(4_750 / 1.9, abs=1e-9)
    assert row.se == pytest.approx(1.0 / math.sqrt(2_500.0), abs=1e-9)
    assert row.mde_t2 == pytest.approx(0.04, abs=1e-9)
    assert row.power_class == "individually_testable"


def test_write_power_md_stamps_provenance_and_refuses_an_incomplete_table(tmp_path):
    rows = [
        power_row(stage="A: P1 rebalance", test="Flow (all days, NG+CL)", n=5_000, m=1.0,
                  rho=0.0, track="1", plausible_effect=0.05, note="ledger 9A.1"),
        power_row(stage="G: P9 non-US ETPs", test="Marginal flow", n=240, m=1.0, rho=0.0,
                  track="2", plausible_effect=0.05, note="routes to 9B"),
    ]
    out = tmp_path / "nested" / "results" / "POWER.md"
    written = write_power_md(rows, out, date="2026-09-21")
    assert written == out and out.exists()
    text = out.read_text(encoding="utf-8")
    assert "**Generated:** 2026-09-21" in text
    assert "recomputed on real data before each" in text
    assert "A: P1 rebalance" in text and "G: P9 non-US ETPs" in text
    assert "BLOCKED" in text and "permitted" in text
    # Line endings are pinned (D550): the file is LF on every OS.
    assert b"\r\n" not in out.read_bytes()

    incomplete = power_row(stage="E", test="Weekly fit", n=520, m=1.0, rho=0.0, track="1",
                           plausible_effect=None)
    with pytest.raises(ValueError, match="plausible-effect statement"):
        write_power_md([incomplete], tmp_path / "never.md")
    assert not (tmp_path / "never.md").exists()


def test_the_script_selftest_runs_clean():
    """`scripts/power_table.py --selftest` is the module's own audit: every named
    ledger test plus every guard shown raising. It must pass here too, so a change
    to the module cannot leave the script's self-test stale and unnoticed."""
    spec = importlib.util.spec_from_file_location(
        "power_table_d588_test", REPO / "scripts" / "power_table.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["power_table_d588_test"] = module
    spec.loader.exec_module(module)
    module.selftest(log=lambda *args, **kwargs: None)
