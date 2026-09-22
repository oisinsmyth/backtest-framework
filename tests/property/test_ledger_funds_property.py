"""Property tests for the deposit's fund model -- `ledger/funds`, `premium`, `creations`,
`non_us` (D611).

Conventions per D78 (derandomized hypothesis, seeding owned by the library) as amended by
D537 (`derandomize=True` fixes the seed but NOT the examples drawn, so a failure here is
reproducible within a run and the example set is not byte-stable between a single-file run
and a full-suite one). `max_examples=40` and `deadline=None` keep the file inside the gate.

The exact numbers are pinned by `tests/golden/test_ledger_funds_ledger.py`, which was worked
by hand. What is worth a property here is the set of RELATIONS the pre-registration reasons
with and never writes down as a formula:

  * the iNAV is linear in the held return with slope `L x NAV[t-1]` -- which is what "L times
    exposure" means, and it is asserted on returns nobody chose rather than at +1%;
  * `h` stays inside (0, 1) and never rises with stress while `h1 >= 0` -- required unit test
    18 on a grid is four points, and the monotonicity is the mechanism;
  * `Create_flow` is odd in the creation and takes its sign from `L`, on every pair of signs;
  * the `-3x` product's forced rebalance is exactly twice the `+3x` one's -- the deposit's own
    +$12m / +$24m, as an identity rather than at one AUM;
  * the split conserves the flow to within four ulp, which the golden explains is not the same
    as exactly;
  * the restrike fires below its trigger and not above it, at leverages and thresholds other
    than the document's 3 and 20%.

No fixture is read, no file is written and no return is computed.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.ledger.creations import (
    CreationError,
    create_flow,
    hedged_fraction,
    split,
)
from backtest_framework.ledger.funds import Fund, gate_0b, inav
from backtest_framework.ledger.non_us import Restrike, delta_h, product_value
from backtest_framework.ledger.premium import Quote, premium

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

navs = st.floats(min_value=1.0, max_value=1e4, allow_nan=False, allow_infinity=False)
returns = st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False)
rates = st.floats(min_value=0.0, max_value=0.2, allow_nan=False, allow_infinity=False)
expense = st.floats(min_value=0.0, max_value=0.05, allow_nan=False, allow_infinity=False)
aums = st.floats(min_value=1e3, max_value=1e12, allow_nan=False, allow_infinity=False)
leverages = st.sampled_from([-3, -2, -1, 1, 2, 3])
flows = st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False)


@SETTINGS
@given(nav=navs, L=leverages, r1=returns, r2=returns, y=rates, er=expense)
def test_inav_is_linear_in_the_held_return_with_slope_l_times_nav(nav, L, r1, r2, y, er):
    """P3.1 line 184: the leverage multiplies the return and the accrual is additive."""
    assume(abs(r2 - r1) > 1e-9)
    lhs = inav(nav, L, r2, y, er) - inav(nav, L, r1, y, er)
    assert math.isclose(lhs, nav * L * (r2 - r1), rel_tol=1e-9, abs_tol=1e-12)
    # and the accrual term does not depend on the return at all
    no_accrual = inav(nav, L, r1, 0.0, 0.0)
    assert math.isclose(
        inav(nav, L, r1, y, er) - no_accrual,
        nav * (y / 360 - er / 365),
        rel_tol=1e-9,
        abs_tol=1e-12,
    )


@SETTINGS
@given(nav=navs, L=leverages, y=rates, er=expense)
def test_a_zero_held_return_leaves_only_the_accrual(nav, L, y, er):
    """Required unit test 14's first clause, at leverages and rates nobody chose."""
    assert inav(nav, L, 0.0, y, er) == nav + nav * (y / 360 - er / 365)


@SETTINGS
@given(
    h0=st.floats(min_value=-5.0, max_value=5.0),
    h1=st.floats(min_value=0.0, max_value=3.0),
    s1=st.floats(min_value=-4.0, max_value=4.0),
    s2=st.floats(min_value=-4.0, max_value=4.0),
)
def test_h_is_inside_the_open_interval_and_never_rises_with_stress(h0, h1, s1, s2):
    """Required unit test 18's relation. `h1 >= 0: more stress -> less hedged` (line 232).

    The stress range is bounded because a double logistic SATURATES near |x| = 37 and the
    module raises there rather than returning 1.0; the saturation boundary has its own test in
    `tests/unit/test_ledger_funds.py`.
    """
    assume(s1 <= s2)
    a = hedged_fraction(h0, h1, s1)
    b = hedged_fraction(h0, h1, s2)
    assert 0.0 < a < 1.0 and 0.0 < b < 1.0
    assert b <= a
    if h1 == 0.0:
        assert a == b  # flat, and line 472 permits h1 = 0


@SETTINGS
@given(h0=st.floats(min_value=-5.0, max_value=5.0), s=st.floats(min_value=-4.0, max_value=4.0))
def test_a_negative_h1_or_g1_always_raises(h0, s):
    """Section 8 line 472's two constraints, enforced at every point rather than at one."""
    with pytest.raises(CreationError):
        hedged_fraction(h0, -1e-12, s)
    with pytest.raises(CreationError):
        hedged_fraction(h0, 0.5, s, g1=-1e-12)


@SETTINGS
@given(L=leverages, usd=flows, price=st.floats(min_value=0.01, max_value=500.0))
def test_create_flow_is_odd_in_the_creation_and_signed_by_the_leverage(L, usd, price):
    """Required unit test 19's relation on every pair of signs, not on the two easy ones."""
    multiplier = 10000.0
    flow = create_flow(L, usd, multiplier, price)
    assert create_flow(L, -usd, multiplier, price) == -flow
    if usd != 0.0 and flow != 0.0:
        assert math.copysign(1.0, flow) == math.copysign(1.0, L) * math.copysign(1.0, usd)
    # doubling the money doubles the contracts; the conversion is linear, not a step
    assert create_flow(L, 2 * usd, multiplier, price) == 2 * flow


@SETTINGS
@given(h0=st.floats(min_value=-4.0, max_value=4.0), flow=flows)
def test_the_split_conserves_the_flow_to_within_four_ulp(h0, flow):
    """Lines 233-234 as the document writes them: two roundings, not one and a residual."""
    h = hedged_fraction(h0, 0.0, 0.0)
    window, intraday = split(h, flow)
    assert abs((window + intraday) - flow) <= 4 * math.ulp(abs(flow) + 1e-300)
    if flow != 0.0:
        assert math.copysign(1.0, window) == math.copysign(1.0, flow)
        assert math.copysign(1.0, intraday) == math.copysign(1.0, flow)


@SETTINGS
@given(aum=aums, r=returns)
def test_the_inverse_products_rebalance_is_exactly_twice_the_long_ones(aum, r):
    """Line 297: L(L-1) is 6 at +3x and 12 at -3x, which is required unit test 26's 12 and 24.

    Asserted with `==`: the two differ by a factor of two and scaling a double by a power of
    two is exact, so this is an identity of the formula rather than of the numbers the
    document happened to pick.
    """
    assume(r == 0.0 or abs(r) >= 1e-9)
    long_side = delta_h(aum, 3.0, r)
    short_side = delta_h(aum, -3.0, r)
    assert short_side == 2 * long_side
    # "same sign as the move" -- both, for both products
    if r != 0.0:
        assert math.copysign(1.0, long_side) == math.copysign(1.0, r)
        assert math.copysign(1.0, short_side) == math.copysign(1.0, r)
    # the unleveraged case is the L(L-1) = 0 of the two creation-only US funds
    assert delta_h(aum, 1.0, r) == 0.0


@SETTINGS
@given(
    threshold=st.floats(min_value=0.05, max_value=0.5),
    L=st.sampled_from([-3, -2, 2, 3]),
    r=st.floats(min_value=-0.4, max_value=0.4),
    level=st.floats(min_value=1.0, max_value=1000.0),
)
def test_the_restrike_fires_below_its_trigger_and_not_above_it(threshold, L, r, level):
    """Line 292, at leverages and thresholds other than the document's 3 and 20%.

    Stated with a 1e-9 margin around the trigger: the product value is a rounded double, so a
    move within an ulp of the boundary can land either side of it and neither answer is wrong.
    The exact boundary case -- a product value of exactly 80.0 against a reset of 100.0 -- is
    pinned in the golden instead.
    """
    rest = Restrike(threshold=threshold, L=L)
    assume(abs(abs(r) - rest.underlying_trigger) > 1e-9)
    value = product_value(level, L, r)
    assume(value > 0.0)
    event = rest.check(value, level)
    adverse = r if L < 0 else -r  # an adverse move is a rise for an inverse product
    if adverse > rest.underlying_trigger:
        assert event is not None
        assert event.new_reset_level == value
        assert event.drawdown <= -threshold
    else:
        assert event is None


@SETTINGS
@given(
    bid=st.floats(min_value=1.0, max_value=100.0),
    spread=st.floats(min_value=1e-3, max_value=1.0),
    last=st.floats(min_value=0.01, max_value=1000.0),
    fair=st.floats(min_value=1.0, max_value=100.0),
)
def test_the_premium_never_depends_on_the_last_trade(bid, spread, last, fair):
    """Line 199, as a property over quotes rather than the golden's one series."""
    ts = dt.datetime(2026, 9, 18, 14, 20)
    q1 = Quote(bid, bid + spread, last, ts)
    q2 = Quote(bid, bid + spread, last / 2 + 0.01, ts)
    assert premium(q1, fair) == premium(q2, fair)
    assert q1.mid == (bid + (bid + spread)) / 2


@SETTINGS
@given(
    navs_list=st.lists(navs, min_size=1, max_size=30),
    errors=st.lists(st.floats(min_value=-50.0, max_value=50.0), min_size=1, max_size=30),
)
def test_gate_0b_reports_a_share_that_matches_its_own_error_list(navs_list, errors):
    """The verdict is a function of the reported errors and of nothing else (line 191)."""
    n = min(len(navs_list), len(errors))
    official = navs_list[:n]
    inavs = [nav * (1 + bp / 1e4) for nav, bp in zip(official, errors[:n])]
    result = gate_0b(inavs, official)
    assert 0.0 <= result.share_within <= 1.0
    assert result.n_within == sum(1 for bp in result.bp_errors if abs(bp) <= 5.0)
    assert result.share_within == result.n_within / result.n_days
    assert result.passes == (result.share_within >= 0.95)
    assert result.worst_bp == max(abs(bp) for bp in result.bp_errors)


@SETTINGS
@given(L=leverages, multiplier=st.floats(min_value=1.0, max_value=1e5))
def test_a_fund_always_knows_its_rebalance_factor(L, multiplier):
    """`L(L-1)`: an integer, zero exactly at L = 1, and never negative."""
    fund = Fund(name="X", L=L, underlying_root="NG", multiplier=multiplier)
    assert fund.rebalance_factor == L * (L - 1)
    assert isinstance(fund.rebalance_factor, int)
    assert fund.rebalance_factor >= 0
    assert (fund.rebalance_factor == 0) == (L == 1)
