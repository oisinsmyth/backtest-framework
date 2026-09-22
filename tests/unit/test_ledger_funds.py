"""`ledger/funds.py` and `ledger/creations.py`: the constants, the guards, and three claims (D611).

The hand-worked arithmetic lives in `tests/golden/test_ledger_funds_ledger.py`. What is here is
the other half: that the six fund constants are the deposit's Section 3.1 table and carry NO
invented facts, that every refusal in the two modules actually fires, and the three numbered
required unit tests whose substance is a sign or a branch rather than a number -- 4 (the
execution-day lag), 18 (the hedged fraction) and 19 (the creation sign).

The creations module is tested here rather than in a file of its own because `create_flow` and
`split` are the fund table's arithmetic one step on: the leverage and the multiplier that decide
both are `Fund` fields.
"""

from __future__ import annotations

import math

import pytest

from backtest_framework.ledger.creations import (
    CreationError,
    create_flow,
    creation_term,
    delta_create,
    hedged_fraction,
    split,
)
from backtest_framework.ledger.funds import (
    BOIL,
    CL_MULTIPLIER,
    KOLD,
    NG_MULTIPLIER,
    SCO,
    UCO,
    UNG,
    US_FUNDS,
    USO,
    Fund,
    FundModelError,
    gate_0b,
    inav,
)

CREATE_USD = 10000000.0
P_HELD = 3.0


# ----------------------------------------------------------------- the fund table itself


def test_the_six_funds_are_section_3_1s_table():
    """Lines 60-65: name, leverage, underlying, and the role each leverage implies."""
    assert list(US_FUNDS) == ["BOIL", "KOLD", "UCO", "SCO", "UNG", "USO"]
    assert [(f.name, f.L, f.underlying_root) for f in US_FUNDS.values()] == [
        ("BOIL", 2, "NG"),
        ("KOLD", -2, "NG"),
        ("UCO", 2, "CL"),
        ("SCO", -2, "CL"),
        ("UNG", 1, "NG"),
        ("USO", 1, "CL"),
    ]
    # "Creations only (L(L-1) = 0)" is an integer zero, not a small float.
    assert UNG.rebalance_factor == 0 and USO.rebalance_factor == 0
    assert isinstance(UNG.rebalance_factor, int)
    assert [f.rebalance_factor for f in (BOIL, KOLD, UCO, SCO)] == [2, 6, 2, 6]
    assert {f.currency for f in US_FUNDS.values()} == {"USD"}


def test_no_fund_carries_an_invented_fact():
    """Section 3.2 is a list of facts to SOURCE, and Section 0 instruction 3 forbids inventing them.

    The expense ratio and the index month rule are both on it, so both are None on all six, and
    `inav` refuses the first of them at the point of use rather than substituting anything.
    """
    for fund in US_FUNDS.values():
        assert fund.er is None, fund
        assert fund.index_month_rule is None, fund
    with pytest.raises(FundModelError, match="Section 3.2"):
        inav(100.0, 2, 0.0, 0.05, None)


def test_the_multipliers_are_the_contract_sizes():
    assert NG_MULTIPLIER == 10000.0 and CL_MULTIPLIER == 1000.0
    assert BOIL.multiplier == KOLD.multiplier == UNG.multiplier == NG_MULTIPLIER
    assert UCO.multiplier == SCO.multiplier == USO.multiplier == CL_MULTIPLIER


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"name": "", "L": 2, "underlying_root": "NG", "multiplier": 1.0}, "needs a name"),
        ({"name": "X", "L": 0, "underlying_root": "NG", "multiplier": 1.0}, "L = 0"),
        ({"name": "X", "L": 2, "underlying_root": "", "multiplier": 1.0}, "underlying root"),
        ({"name": "X", "L": 2, "underlying_root": "NG", "multiplier": 0.0}, "multiplier"),
        ({"name": "X", "L": 2, "underlying_root": "NG", "multiplier": -1.0}, "multiplier"),
        (
            {"name": "X", "L": 2, "underlying_root": "NG", "multiplier": 1.0, "er": 0.95},
            "expense ratio",
        ),
        (
            {"name": "X", "L": 2, "underlying_root": "NG", "multiplier": 1.0, "er": -0.01},
            "expense ratio",
        ),
        ({"name": "X", "L": 2.0, "underlying_root": "NG", "multiplier": 1.0}, "must be an int"),
    ],
)
def test_the_fund_constructor_refuses_each_impossible_field(kwargs, message):
    with pytest.raises(FundModelError, match=message):
        Fund(**kwargs)


def test_a_percentage_typed_as_a_fraction_is_the_expense_ratio_guard():
    """0.95 is not 0.95%, and the two are a factor of 100 apart in the accrual."""
    assert Fund("X", 2, "NG", NG_MULTIPLIER, er=0.0095).er == 0.0095
    with pytest.raises(FundModelError, match="0.95"):
        Fund("X", 2, "NG", NG_MULTIPLIER, er=0.95)


def test_inav_refuses_a_non_positive_or_non_finite_input():
    with pytest.raises(FundModelError, match="nav_prev"):
        inav(0.0, 2, 0.0, 0.05, 0.01)
    with pytest.raises(FundModelError, match="nav_prev"):
        inav(-100.0, 2, 0.0, 0.05, 0.01)
    with pytest.raises(FundModelError, match="r_held"):
        inav(100.0, 2, math.nan, 0.05, 0.01)
    with pytest.raises(FundModelError, match="y_cash"):
        inav(100.0, 2, 0.0, math.inf, 0.01)
    with pytest.raises(FundModelError, match="must be an int"):
        inav(100.0, 2.0, 0.0, 0.05, 0.01)  # type: ignore[arg-type]


def test_gate_0b_thresholds_are_arguments_and_both_comparisons_are_inclusive():
    result = gate_0b([1000.5], [1000.0], bp_limit=5.0)
    assert result.passes is True and result.bp_errors == (5.0,)
    assert gate_0b([1000.5], [1000.0], bp_limit=4.999).passes is False
    # 19 of 20 is exactly 0.95 and passes; asking for 0.96 fails the same sample.
    official = [1000.0] * 20
    good = [1000.2] * 19 + [1000.8]
    assert gate_0b(good, official, share=0.95).passes is True
    assert gate_0b(good, official, share=0.96).passes is False
    with pytest.raises(FundModelError, match="share"):
        gate_0b(good, official, share=1.5)
    with pytest.raises(FundModelError, match="bp_limit"):
        gate_0b(good, official, bp_limit=0.0)


# ------------------------------------------------------------------ the numbered claims


def test_ledger_4_the_execution_day_lag_picks_one_term_and_never_both():
    """Required unit test 4, line 226.

    `lag_c = 1`: Q3_known uses the realised change from t-1 and no forecast term.
    `lag_c = 0`: the forecast term only.
    """
    realised = CREATE_USD
    forecast = 99.0
    assert creation_term(1, realised, forecast) == realised
    assert creation_term(1, realised, None) == realised
    assert creation_term(0, realised, forecast) == forecast
    assert creation_term(0, None, forecast) == forecast

    # At lag 1 the forecast cannot influence the answer at all: C2 is forecasting TOMORROW's.
    assert creation_term(1, realised, 1e12) == creation_term(1, realised, -1e12)

    # Neither branch falls back to the other.
    with pytest.raises(CreationError, match="Q3_known"):
        creation_term(1, None, forecast)
    with pytest.raises(CreationError, match="forecast is None"):
        creation_term(0, realised, None)
    # Section 3.2 defines lag_c in {0, 1}; nothing else is a described execution timing.
    for bad in (2, -1, 7):
        with pytest.raises(CreationError, match="lag_c"):
            creation_term(bad, realised, forecast)
    with pytest.raises(CreationError, match="must be an int"):
        creation_term(0.5, realised, forecast)  # type: ignore[arg-type]


def test_ledger_18_h_is_in_the_open_interval_and_non_increasing_in_stress():
    """Required unit test 18, on a grid rather than at a point, plus its two constraints."""
    grid = [-4.0, -2.0, -1.0, 0.0, 0.5, 1.0, 2.0, 4.0, 8.0]
    for h1 in (0.0, 0.25, 0.5, 2.0):
        values = [hedged_fraction(1.0, h1, s) for s in grid]
        assert all(0.0 < v < 1.0 for v in values), (h1, values)
        assert values == sorted(values, reverse=True), (h1, values)
        if h1 == 0.0:
            assert len(set(values)) == 1  # flat, and flat is permitted
        else:
            assert len(set(values)) == len(values)  # strictly decreasing

    # Section 8 line 472: h1 >= 0 and g1 >= 0, enforced rather than assumed.
    with pytest.raises(CreationError, match="h1 >= 0"):
        hedged_fraction(1.0, -0.1, 0.0)
    with pytest.raises(CreationError, match="g1 >= 0"):
        hedged_fraction(1.0, 0.5, 0.0, g1=-0.1)
    # P3.7 line 271: the attention term enters in place of stress and is also non-increasing.
    accel = [hedged_fraction(1.0, 0.5, 0.0, g1=2.0, att_accel=a) for a in (0.0, 1.0, 2.0)]
    assert accel == sorted(accel, reverse=True)
    # A saturated logistic is refused rather than returned as 1.0.
    with pytest.raises(CreationError, match="saturated"):
        hedged_fraction(40.0, 0.0, 0.0)
    with pytest.raises(CreationError, match="finite"):
        hedged_fraction(math.nan, 0.5, 0.0)


def test_ledger_19_the_creation_sign_comes_from_the_leverage():
    """Required unit test 19: a KOLD creation gives negative Create_flow, a BOIL creation positive.

    All four cases, because the two that read naturally would pass on a formula with the sign
    taken from dCreate instead of from L.
    """
    creation = delta_create(6000000.0, 5600000.0, 25.0)
    redemption = delta_create(5600000.0, 6000000.0, 25.0)
    assert creation == CREATE_USD and redemption == -CREATE_USD

    boil_create = create_flow(BOIL.L, creation, BOIL.multiplier, P_HELD)
    kold_create = create_flow(KOLD.L, creation, KOLD.multiplier, P_HELD)
    boil_redeem = create_flow(BOIL.L, redemption, BOIL.multiplier, P_HELD)
    kold_redeem = create_flow(KOLD.L, redemption, KOLD.multiplier, P_HELD)

    assert boil_create > 0 and kold_create < 0
    assert boil_redeem < 0 and kold_redeem > 0
    assert boil_create == -kold_create == -boil_redeem == kold_redeem == 666.6666666666666

    # The unlevered funds still create: L(L-1) = 0 kills the REBALANCE, not the creation.
    assert create_flow(UNG.L, creation, UNG.multiplier, P_HELD) == 333.3333333333333
    assert UNG.rebalance_factor == 0

    # And the split never changes a sign, only divides one.
    h = hedged_fraction(1.0, 0.5, 0.0)
    for flow in (boil_create, kold_create):
        window, intraday = split(h, flow)
        assert math.copysign(1.0, window) == math.copysign(1.0, flow)
        assert math.copysign(1.0, intraday) == math.copysign(1.0, flow)


# ------------------------------------------------------------- the rest of the refusals


def test_delta_create_refuses_a_broken_panel_row():
    with pytest.raises(CreationError, match="NAV must be positive"):
        delta_create(1.0, 0.0, 0.0)
    with pytest.raises(CreationError, match="non-negative"):
        delta_create(-1.0, 0.0, 25.0)
    with pytest.raises(CreationError, match="finite"):
        delta_create(math.nan, 0.0, 25.0)


def test_create_flow_refuses_a_non_positive_price():
    """CL settled at -$37.63 on 2020-04-20 and the contract conversion is undefined there."""
    with pytest.raises(CreationError, match="p_held"):
        create_flow(2, CREATE_USD, NG_MULTIPLIER, -37.63)
    with pytest.raises(CreationError, match="multiplier"):
        create_flow(2, CREATE_USD, 0.0, P_HELD)
    with pytest.raises(CreationError, match="L = 0"):
        create_flow(0, CREATE_USD, NG_MULTIPLIER, P_HELD)


def test_split_refuses_an_h_outside_the_open_interval():
    for bad in (0.0, 1.0, -0.5, 1.5, math.nan):
        with pytest.raises(CreationError, match="open interval"):
            split(bad, 100.0)
    with pytest.raises(CreationError, match="finite"):
        split(0.5, math.inf)
