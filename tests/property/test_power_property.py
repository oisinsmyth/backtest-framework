"""Property tests for `validation/power.py` (D588).

Conventions per D78 (derandomized hypothesis, seeding owned by the library rather
than a hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the
seed but NOT the examples drawn, because since hypothesis 6.156.6 the constant pool
is harvested from `sys.modules` at test time — so a failure here is reproducible
within a run but the example set is not byte-stable across a full-suite run and a
single-file run). `max_examples=40` and `deadline=None` keep the file cheap enough
to sit in the default gate.

What is worth a property and what is not. The closed forms are pinned by the golden
and unit tests; these check the RELATIONS the deposit docs reason with but never
write down — that the design effect is monotone, that clustering can only cost
sample, that the two MDEs keep their ratio, that routing is a step function with the
boundary on the documented side, and that the ANOVA ICC is invariant to the things
it must be invariant to (relabelling clusters, shifting and scaling the values).
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.validation.power import (
    Z80_TWO_SIDED,
    design_effect,
    forward_evaluation_days,
    icc_from_clusters,
    mde,
    mde_80,
    n_eff,
    power_class,
    power_row,
    se_correlation,
    se_mean,
    track3_route,
    validate_track_map,
)

# D78 / D537: derandomized, bounded, no deadline.
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

TOLERANCE = 1e-9

_m = st.floats(min_value=1.0, max_value=500.0, allow_nan=False, allow_infinity=False)
_unit = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
_positive = st.floats(
    min_value=1e-4, max_value=1.0, allow_nan=False, allow_infinity=False, exclude_min=False
)
_n = st.integers(min_value=2, max_value=200_000)


# --------------------------------------------------------------------------- design effect


@SETTINGS
@given(m=_m, rho=_unit)
def test_clustering_never_increases_the_effective_sample(m, rho):
    """With rho >= 0 the design effect is at least 1, so n_eff <= n: clustering can
    only cost sample. The whole reason §9A.2 rule 1 demands the real rho before a
    stage runs is that assuming rho = 0 always OVERSTATES power."""
    assert design_effect(m, rho) >= 1.0 - TOLERANCE
    assert n_eff(10_000, m, rho) <= 10_000.0 + TOLERANCE


@SETTINGS
@given(m=_m, a=_unit, b=_unit)
def test_design_effect_is_monotone_in_rho(m, a, b):
    lo, hi = sorted((a, b))
    assert design_effect(m, lo) <= design_effect(m, hi) + TOLERANCE


@SETTINGS
@given(rho=_unit)
def test_singleton_clusters_are_a_no_op(rho):
    """m = 1 means one observation per cluster, i.e. no clustering at all, and no rho
    can change that."""
    assert design_effect(1.0, rho) == 1.0
    assert n_eff(5_000, 1.0, rho) == 5_000.0


# --------------------------------------------------------------------------- SE and MDE


@SETTINGS
@given(n_eff_value=st.floats(min_value=2.0, max_value=1e7, allow_nan=False,
                             allow_infinity=False))
def test_the_two_mdes_keep_their_documented_ratio(n_eff_value):
    """MDE_80 / MDE_t2 = 2.8 / 2 = 1.4 for every sample size: the 80%-power figure is
    always 40% larger than the bare-significance one. Reporting MDE_t2 as if it were
    a powered number understates the required effect by that factor."""
    se = se_correlation(n_eff_value)
    assert mde_80(se) / mde(se) == pytest.approx(Z80_TWO_SIDED / 2.0, abs=1e-12)
    assert mde_80(se) > mde(se)


@SETTINGS
@given(
    sigma=st.floats(min_value=1e-6, max_value=10.0, allow_nan=False, allow_infinity=False),
    n_eff_value=st.floats(min_value=2.0, max_value=1e7, allow_nan=False, allow_infinity=False),
)
def test_price_se_is_the_correlation_se_scaled_by_sigma(sigma, n_eff_value):
    """The only difference between the two unit regimes is the factor sigma. Anything
    else would mean the module had two different notions of a standard error."""
    assert se_mean(sigma, n_eff_value) == pytest.approx(
        sigma * se_correlation(n_eff_value), rel=1e-12
    )


@SETTINGS
@given(a=st.floats(min_value=2.0, max_value=1e6), b=st.floats(min_value=2.0, max_value=1e6))
def test_more_effective_sample_never_raises_the_mde(a, b):
    lo, hi = sorted((a, b))
    assert mde(se_correlation(hi)) <= mde(se_correlation(lo)) + 1e-12


@SETTINGS
@given(n_eff_value=st.floats(min_value=2.0, max_value=1e7))
def test_quadrupling_the_effective_sample_halves_the_mde(n_eff_value):
    """The square-root law, as the docs use it to size forward windows: 4x the sample
    for 2x the resolution. This is why §13A.7(2)'s n_needed is a SQUARE."""
    assert mde(se_correlation(4.0 * n_eff_value)) == pytest.approx(
        0.5 * mde(se_correlation(n_eff_value)), rel=1e-12
    )


# --------------------------------------------------------------------------- routing


@SETTINGS
@given(mde_value=_positive, plausible=_positive)
def test_power_class_is_exactly_the_comparison_rule_3_states(mde_value, plausible):
    label = power_class(mde_value, plausible)
    assert label == ("underpowered" if mde_value > plausible else "individually_testable")
    assert label in ("underpowered", "individually_testable")


@SETTINGS
@given(
    n=_n,
    m=_m,
    rho=_unit,
    plausible=_positive,
    sigma=st.one_of(st.none(), st.floats(min_value=1e-4, max_value=5.0)),
)
def test_a_row_is_blocked_exactly_when_it_is_not_individually_testable(n, m, rho, plausible, sigma):
    assume(n / design_effect(m, rho) >= 2.0)  # below 2, se_correlation refuses by design
    row = power_row(
        stage="S", test="T", n=n, m=m, rho=rho, track="1",
        plausible_effect=plausible, sigma=sigma,
    )
    assert row.adoption_by_significance_blocked == (row.mde_t2 > plausible)
    assert row.units == ("correlation" if sigma is None else "sigma")
    # A complete row always validates; it is the missing statement that raises.
    assert validate_track_map([row]) is None


@SETTINGS
@given(n=_n, m=_m, rho=_unit, sigma=st.one_of(st.none(), st.floats(min_value=1e-4, max_value=5.0)))
def test_a_row_without_a_plausible_effect_statement_is_always_refused(n, m, rho, sigma):
    """§13A.2 (v1.8) requires the statement before the stage runs, so there is no
    combination of inputs that lets an unstated row through."""
    assume(n / design_effect(m, rho) >= 2.0)
    row = power_row(stage="S", test="T", n=n, m=m, rho=rho, track="1",
                    plausible_effect=None, sigma=sigma)
    assert row.power_class is None
    assert row.adoption_by_significance_blocked is True
    with pytest.raises(ValueError, match="plausible-effect statement"):
        validate_track_map([row])


@SETTINGS
@given(plausible=_positive, instruments=st.integers(min_value=1, max_value=40))
def test_forward_plan_respects_its_floor_cap_and_square_law(plausible, instruments):
    plan = forward_evaluation_days(plausible, instruments)
    assert plan.n_needed == pytest.approx((2.0 / plausible) ** 2, rel=1e-12)
    if plan.route == "forward":
        assert plan.evaluation_days is not None
        assert 120.0 <= plan.evaluation_days <= 500.0
        assert plan.evaluation_days == pytest.approx(
            max(120.0, plan.n_needed / instruments), rel=1e-12
        )
    else:
        assert plan.route == "9B"
        assert plan.evaluation_days is None
        assert plan.n_needed / instruments > 500.0


@SETTINGS
@given(plausible=_positive, instruments=st.integers(min_value=1, max_value=20))
def test_more_instruments_never_lengthen_the_forward_window(plausible, instruments):
    """Doubling the instruments halves the calendar, never the reverse — the reason
    §13A.7(2) divides by an instrument count at all."""
    fewer = forward_evaluation_days(plausible, instruments)
    more = forward_evaluation_days(plausible, 2 * instruments)
    if fewer.route == "forward":
        assert more.route == "forward"
        assert more.evaluation_days <= fewer.evaluation_days + 1e-9


@SETTINGS
@given(edge=st.floats(min_value=1e-6, max_value=2.0, allow_nan=False, allow_infinity=False))
def test_track3_routing_is_a_step_function_with_the_boundary_on_efficacy(edge):
    route = track3_route(edge)
    assert route.mde == pytest.approx(2.0 / math.sqrt(300.0), rel=1e-12)
    assert route.route == ("efficacy_n300" if edge >= route.mde else "combined_evidence")
    # Monotone: a larger edge never routes to the weaker evidence path.
    bigger = track3_route(edge * 2.0)
    assert not (route.route == "efficacy_n300" and bigger.route == "combined_evidence")


# --------------------------------------------------------------------------- the ICC


_values = st.lists(
    st.floats(min_value=-1e3, max_value=1e3, allow_nan=False, allow_infinity=False),
    min_size=6,
    max_size=60,
)


def _grouped(values: list[float], k: int) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(values, dtype=float)
    ids = np.arange(y.size) % k
    return y, ids


@SETTINGS
@given(values=_values, k=st.integers(min_value=2, max_value=5))
def test_icc_is_invariant_to_shifting_and_scaling_the_values(values, k):
    """The ICC is a variance RATIO, so adding a constant or multiplying by one cannot
    move it. If it did, the estimate would depend on the units the flow happened to
    be recorded in."""
    y, ids = _grouped(values, k)
    assume(y.size > k)
    assume(float(np.var(y)) > 1e-9)
    base = icc_from_clusters(y, ids)
    assert icc_from_clusters(y + 137.5, ids) == pytest.approx(base, abs=1e-8)
    assert icc_from_clusters(y * -3.25, ids) == pytest.approx(base, abs=1e-8)


@SETTINGS
@given(values=_values, k=st.integers(min_value=2, max_value=5))
def test_icc_is_invariant_to_relabelling_the_clusters(values, k):
    """Cluster ids are labels, not an ordering. A day id, a year and an instrument
    name must all give the same answer for the same partition."""
    y, ids = _grouped(values, k)
    assume(y.size > k)
    assume(float(np.var(y)) > 1e-9)
    base = icc_from_clusters(y, ids)
    renamed = np.array([f"cluster-{(7 * int(i) + 3) % k}" for i in ids])
    assert icc_from_clusters(y, renamed) == pytest.approx(base, abs=1e-9)


@SETTINGS
@given(values=_values, k=st.integers(min_value=2, max_value=5))
def test_icc_lies_in_its_theoretical_range(values, k):
    """(MSB - MSW) / (MSB + (n0 - 1) MSW) is at most 1 (MSW = 0) and at least
    -1/(n0 - 1) (MSB = 0). n0 >= 1, so -1 is a safe lower bound for k >= 2 designs
    with at least two observations in some cluster."""
    y, ids = _grouped(values, k)
    assume(y.size > k)
    assume(float(np.var(y)) > 1e-9)
    icc = icc_from_clusters(y, ids)
    assert -1.0 - 1e-9 <= icc <= 1.0 + 1e-9


@SETTINGS
@given(
    k=st.integers(min_value=3, max_value=12),
    per=st.integers(min_value=2, max_value=8),
    offset=st.floats(min_value=1.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
def test_a_pure_between_cluster_split_gives_an_icc_of_one(k, per, offset):
    """Every observation equals its cluster's own constant: all the variance is
    between clusters, so MSW = 0 and the ICC is exactly 1 — the maximum clustering
    penalty, n_eff = n / m."""
    y = np.repeat(np.arange(k, dtype=float) * offset, per)
    ids = np.repeat(np.arange(k), per)
    assert icc_from_clusters(y, ids) == pytest.approx(1.0, abs=1e-12)
    assert n_eff(int(y.size), float(per), 1.0) == pytest.approx(y.size / per, rel=1e-12)


@SETTINGS
@given(values=_values, k=st.integers(min_value=2, max_value=5))
def test_the_grouped_and_flat_input_forms_agree(values, k):
    """The grouped form exists so the empty-cluster guard can fire; it must not be a
    second, subtly different estimator."""
    y, ids = _grouped(values, k)
    assume(y.size > k)
    assume(float(np.var(y)) > 1e-9)
    groups = [y[ids == cluster] for cluster in range(k)]
    assume(all(group.size > 0 for group in groups))
    assert icc_from_clusters(groups) == pytest.approx(icc_from_clusters(y, ids), abs=1e-12)
