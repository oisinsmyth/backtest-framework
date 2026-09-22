"""Property tests for `backtest_framework.ledger` (D610).

Conventions per D78 (derandomized hypothesis, seeding owned by the library) as amended by
D537 (`derandomize=True` fixes the seed but NOT the examples drawn, so a failure here is
reproducible within a run and the example set is not byte-stable across a full-suite run and
a single-file run). `max_examples=40` and `deadline=None` keep the file inside the default
gate.

What is worth a property here and what is not. The exact numbers are pinned by
`tests/golden/test_ledger_flows_ledger.py`, which was hand-worked before the code existed;
these check the RELATIONS the deposit document reasons with but never writes down:

  * ``Q1`` is ODD in the day's return -- the fund buys on the way up exactly as hard as it
    sells on the way down, which is what makes the rebalance a *mechanical* flow rather than
    a directional view, and is exact in binary64 because IEEE multiplication is sign
    symmetric;
  * ``Q1`` is exactly zero at L in {0, 1}, on inputs nobody chose;
  * the Kalman gain can only ever shrink the variance: ``0 <= K p <= 1`` and
    ``var_post <= var``, for every admissible ``(mu, var, p, R, z)``;
  * ``route`` conserves the unrouted total to within one ulp at ``n = 0``, and EXACTLY at the
    two endpoints line 709 names;
  * a roll's two legs have opposite signs and match in notional;
  * ``fit_lambda`` never returns a slope outside [0, 1], whatever the weeks look like.

No fixture is read and no strategy return is computed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.ledger.flows import (
    LedgerError,
    aggregate,
    FlowTerm,
    held_months,
    is_large,
    large_lot_threshold,
    q1_notional,
    q1_rebalance,
    route,
)
from backtest_framework.ledger.netting import fit_lambda
from backtest_framework.ledger.rolls import roll_legs
from backtest_framework.ledger.update import kalman_update

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

aum = st.floats(min_value=0.0, max_value=1e12, allow_nan=False, allow_infinity=False)
lev = st.sampled_from([-3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0])
ret = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)
frac = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
price = st.floats(min_value=0.01, max_value=5000.0, allow_nan=False, allow_infinity=False)
mult = st.sampled_from([1.0, 100.0, 1000.0, 10_000.0, 2500.0])


# --------------------------------------------------------------------------- P1


@SETTINGS
@given(a=aum, L=lev, r=ret, f=frac)
def test_q1_is_odd_in_the_return(a: float, L: float, r: float, f: float) -> None:
    """``Q1(-r) == -Q1(r)``, exactly.

    The rebalance is a MECHANICAL flow: the same AUM buys on an up day exactly as hard as it
    sells on an equal down day. The exactness is IEEE-754's, not the arithmetic's -- negating
    one factor of a product negates the product and never changes a bit of the significand --
    and it is asserted with `==` for that reason.
    """
    assert q1_notional(a, L, -r, f) == -q1_notional(a, L, r, f)


@SETTINGS
@given(a=aum, r=ret, f=frac, m=mult, p=price)
def test_q1_is_exactly_zero_where_the_leverage_coefficient_vanishes(
    a: float, r: float, f: float, m: float, p: float
) -> None:
    """Required unit test 2's claim, on inputs nobody picked: L(L-1) is 0 at L = 0 and L = 1."""
    for L in (0.0, 1.0):
        assert q1_notional(a, L, r, f) == 0.0
        assert q1_rebalance(a, L, r, f, m, p) == 0.0


@SETTINGS
@given(a=aum, L=lev, r=ret, f=frac, m=mult, p=price)
def test_route_conserves_the_total_to_one_ulp_and_exactly_at_the_endpoints(
    a: float, L: float, r: float, f: float, m: float, p: float
) -> None:
    """Line 709's identity, and the honest statement of what holds beyond its two endpoints.

    The endpoints are exact because a product with a 1.0 or a 0.0 factor is lossless. The
    interior is one ulp wide because line 156 and line 165 are two independent products, and
    a version of `route` that conserved exactly would no longer be the registered formulas.
    """
    total = q1_rebalance(a, L, r, 1.0, m, p)
    assume(math.isfinite(total))

    q1, q2 = route(a, L, r, 1.0, 0.0, m, p)
    assert (q1, q2) == (total, 0.0)
    q1, q2 = route(a, L, r, 0.0, 0.0, m, p)
    assert (q1, q2) == (0.0, total)

    q1, q2 = route(a, L, r, f, 0.0, m, p)
    assert abs((q1 + q2) - total) <= math.ulp(abs(total)) or total == 0.0
    # Netting only ever shrinks the swap leg, and never touches the futures leg.
    q1n, q2n = route(a, L, r, f, 1.0, m, p)
    assert q1n == q1 and q2n == 0.0


@SETTINGS
@given(
    qs=st.lists(st.floats(min_value=-1e7, max_value=1e7, allow_nan=False), min_size=1, max_size=6),
    vs=st.lists(st.floats(min_value=0.0, max_value=1e9, allow_nan=False), min_size=6, max_size=6),
)
def test_aggregate_is_independent_of_the_order_the_participants_were_declared_in(
    qs: list[float], vs: list[float]
) -> None:
    """Section 5.1's ``Sum active Q_i`` says nothing about an order, so neither may the code.

    `math.fsum` is correctly rounded and therefore permutation invariant; a naive loop is not,
    and two studies enabling the same stages in a different sequence would print different
    last bits.
    """
    terms = [FlowTerm(f"P{i}", q, vs[i]) for i, q in enumerate(qs)]
    mu, var = aggregate(terms)
    assert aggregate(list(reversed(terms))) == (mu, var)
    assert aggregate(terms[1:] + terms[:1]) == (mu, var)
    assert var >= 0.0


# --------------------------------------------------------------------------- the update


@SETTINGS
@given(
    mu=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    var=st.floats(min_value=0.0, max_value=1e9, allow_nan=False),
    p=frac,
    R=st.floats(min_value=1e-6, max_value=1e9, allow_nan=False),
    z=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
)
def test_the_update_can_only_ever_shrink_the_variance(
    mu: float, var: float, p: float, R: float, z: float
) -> None:
    """``0 <= K p <= 1`` and ``var_post <= var``, and ``q_rem`` is exactly ``(1 - p) q_hat``.

    This is the property that makes lines 380-384 a Kalman update rather than four
    expressions that happen to sit together: the observation cannot make the ledger LESS
    certain than its prior, and the remaining flow is the posterior mean scaled by the share
    that has not traded yet.
    """
    u = kalman_update(mu, var, p, R, z)
    assert 0.0 <= u.k * p <= 1.0
    assert 0.0 <= u.var_post <= var
    assert u.q_rem == (1.0 - p) * u.q_hat
    assert u.sigma_rem >= 0.0
    assert math.isfinite(u.k) and math.isfinite(u.q_hat)
    # An infinite R is the no-information limit and returns the prior untouched, exactly.
    inf = kalman_update(mu, var, p, math.inf, z)
    assert inf.k == 0.0 and inf.q_hat == mu and inf.var_post == var


# --------------------------------------------------------------------------- the roll


@SETTINGS
@given(
    phi=st.floats(min_value=1e-6, max_value=1.0, allow_nan=False),
    n_old=st.floats(min_value=1e-6, max_value=1e7, allow_nan=False),
    L=st.sampled_from([-3.0, -2.0, -1.0, 1.0, 2.0, 3.0]),
    p_old=price,
    p_new=price,
)
def test_roll_legs_are_opposite_in_sign_and_matched_in_notional(
    phi: float, n_old: float, L: float, p_old: float, p_new: float
) -> None:
    """Lines 334-335. The two legs always point opposite ways, and their notionals match.

    The notional match is asserted with a relative tolerance and not with `==`: ``Buy_new``
    carries the factor ``P_old / P_new``, and ``(x * (a / b)) * b`` is not bit-identical to
    ``x * a`` unless the ratio is a binary fraction. The golden's case is one where it is.
    """
    sell, buy = roll_legs(phi, n_old, L, p_old, p_new)
    assert math.copysign(1.0, sell) != math.copysign(1.0, buy)
    assert (L > 0) == (sell < 0), "a long fund SELLS the expiring month (line 744)"
    assert (L < 0) == (sell > 0), "an inverse fund BUYS it (line 338)"
    assume(math.isfinite(buy * p_new) and math.isfinite(sell * p_old))
    assert math.isclose(buy * p_new, -sell * p_old, rel_tol=1e-12, abs_tol=0.0)
    # Magnitude is set by phi and N_old alone; L's size never enters.
    assert abs(sell) == phi * n_old


# --------------------------------------------------------------------------- the fit


@SETTINGS
@given(
    xs=st.lists(st.floats(min_value=-1e6, max_value=1e6, allow_nan=False), min_size=2, max_size=25),
    noise=st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    slope=st.floats(min_value=-50.0, max_value=50.0, allow_nan=False),
)
def test_fit_lambda_never_leaves_the_unit_interval(
    xs: list[float], noise: float, slope: float
) -> None:
    """Line 496 constrains lambda to [0, 1] and the projection is the exact minimiser there.

    The unconstrained slope is reported beside it, always, so a clipped fit is visible rather
    than silently indistinguishable from a slope that genuinely landed on the boundary.
    """
    # A design whose Sum x^2 underflows towards zero makes the standard error overflow; that
    # is refused by `fit_lambda` and is tested there, not drowned in warnings here.
    assume(math.fsum(x * x for x in xs) > 1e-6)
    ys = [slope * x for x in xs]
    ys[0] += noise
    try:
        f = fit_lambda(ys, xs)
    except LedgerError:
        return  # a degenerate design is refused, which is the other half of the contract
    assert 0.0 <= f.lam <= 1.0
    assert f.clipped == (f.lam != f.lam_unconstrained)
    if not f.clipped:
        assert f.lam == f.lam_unconstrained
    assert f.se >= 0.0
    # The projection really is the constrained argmin: no point in [0, 1] beats it.
    x = np.asarray(xs)
    y = np.asarray(ys)

    def sse(lam: float) -> float:
        return float(np.sum((y - lam * x) ** 2))

    best = min((sse(g / 50.0), g / 50.0) for g in range(51))
    assert sse(f.lam) <= best[0] * (1.0 + 1e-9) + 1e-9


# --------------------------------------------------------------------------- large lots


@SETTINGS
@given(
    sizes=st.lists(st.floats(min_value=0.5, max_value=1e5, allow_nan=False), min_size=1, max_size=8),
    n_days=st.integers(min_value=20, max_value=26),
)
def test_l_min_is_an_observed_size_and_the_tie_counts_as_large(
    sizes: list[float], n_days: int
) -> None:
    """8A.5's threshold under the nearest-rank convention, on pools nobody chose.

    Two claims: ``L_min`` is a size some trade actually had (which is what makes line 753's
    tie clause meaningful), and a trade exactly at it counts as large.
    """
    pool = {f"2026-01-{i + 1:02d}": list(sizes) for i in range(n_days)}
    l_min = large_lot_threshold(pool, "2026-02-01")
    assert l_min in set(sizes)
    assert is_large(l_min, l_min) is True
    assert all(is_large(s, l_min) == (s >= l_min) for s in sizes)
    # At least one trade is at or above the threshold -- a percentile of a non-empty pool is
    # never above its own maximum.
    assert l_min <= max(sizes)
    with pytest.raises(LedgerError):
        large_lot_threshold({**pool, "2026-02-01": list(sizes)}, "2026-02-01")


@SETTINGS
@given(
    holdings=st.lists(st.floats(min_value=0.0, max_value=1e6, allow_nan=False),
                      min_size=1, max_size=5),
)
def test_held_month_weights_are_non_negative_and_sum_to_one(holdings: list[float]) -> None:
    """Line 718's mapping is a probability vector over the months the fund actually holds."""
    assume(any(h > 0.0 for h in holdings))
    book = {f"2026-{i + 1:02d}": h for i, h in enumerate(holdings)}
    w = held_months(book)
    assert set(w) == set(book)
    assert all(v >= 0.0 for v in w.values())
    assert abs(math.fsum(w.values()) - 1.0) <= 1e-12
    # The short side of the same book weights identically: direction is not in the holdings.
    assert held_months({k: -v for k, v in book.items()}) == w
