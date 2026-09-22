"""Golden-master ledger for the deposit's fund model: iNAV, premium, creations, P9 (D611).

Every number here is worked by hand in `test_ledger_funds_ledger.hand.txt`, next to this file,
per D39 and CONTRIBUTING.md's rule that the ground truth comes from a calculator that never
imports this codebase. If the two disagree, the hand file is right.

There is no fixture behind any of it and there could not be: the deposit's fund panel, its ETF
quotes, its FX series and its P9 AUMs are all recorded as missing in
`docs/internal/DEPOSIT_INFRASTRUCTURE_TRACKER.md`. So the inputs are of two kinds, and the hand
file labels each -- the document's own stated figures (the leverages, 5 bp / 95%, c_AP, the 20%
restrike, the +$12m / +$24m), and round illustrative numbers chosen so the arithmetic is
checkable by eye. **`y_cash = 0.05` and `er = 0.01` below are illustrative and are not any
fund's sourced figures**; `funds.py`'s six constants carry `er=None` and `inav` raises on None.

Nothing is asserted to a tolerance except where the hand file says why.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import pytest

from backtest_framework.ledger.creations import (
    create_flow,
    creation_term,
    delta_create,
    hedged_fraction,
    split,
)
from backtest_framework.ledger.funds import (
    BOIL,
    KOLD,
    NG_MULTIPLIER,
    UNG,
    Fund,
    FundModelError,
    gate_0b,
    inav,
)
from backtest_framework.ledger.non_us import (
    BETAPRO_HNU,
    WT_3NGL,
    WT_3OIL,
    NonUsError,
    Restrike,
    RestrikeEvent,
    RestrikeLog,
    aum_usd,
    delta_h,
    index_month,
    product_value,
    q9,
    recompute_delta_h_from_restrike,
)
from backtest_framework.ledger.premium import (
    Minute,
    Quote,
    features,
    minute_feature,
    premium,
    stress,
)

# --------------------------------------------------------------------- hand file section 1
NAV_PREV = 100.0
Y_CASH = 0.05  # ILLUSTRATIVE, not sourced
ER = 0.01  # ILLUSTRATIVE, not sourced
ACCRUAL = 0.00011149162861491629
INAV_FLAT = 100.01114916286149
INAV_LONG = 102.01114916286149
INAV_SHORT = 98.01114916286149
INAV_UNLEVERED = 101.01114916286149

# --------------------------------------------------------------------- hand file section 3
INAV_MINUTE = 25.0
PREM_1 = 0.0012000000000000454
PREM_2 = -0.00039999999999992044
PREM_3 = -0.0019999999999998864
PREM_4 = -0.0035999999999999943
PREM_TWA = -0.001199999999999939
W_START = dt.datetime(2026, 9, 18, 14, 28)

# --------------------------------------------------------------------- hand file section 5
CREATE_USD = 10000000.0
P_HELD = 3.0
FLOW_BOIL = 666.6666666666666
H_AT_X1 = 0.7310585786300049
H_AT_XM1 = 0.2689414213699951
Q3_WINDOW = 179.29428091333006
Q3_INTRADAY = 487.3723857533366

# --------------------------------------------------------------------- hand file sections 6-7
DH_LONG = 12000000.0
DH_SHORT = 24000000.0
DH_TOTAL = 36000000.0
FX_PRIOR = 0.74
AUM_CAD = 175000000.0
AUM_USD_HNU = 129500000.0
RESET_LEVEL = 100.0
VALUE_AT_M67 = 79.89999999999999
DRAWDOWN_AT_M67 = -0.2010000000000001
VALUE_AT_M65 = 80.5


def _minutes() -> list[Minute]:
    """The six minutes of hand file section 3, in order."""
    day = dt.date(2026, 9, 18)

    def at(minute: int) -> dt.datetime:
        return dt.datetime(day.year, day.month, day.day, 14, minute)

    return [
        Minute(at(20), Quote(25.02, 25.04, 25.10, at(20)), INAV_MINUTE, 10.0, True, 1000.0, 800.0),
        Minute(at(21), Quote(24.98, 25.00, 24.99, at(21)), INAV_MINUTE, 10.0, True, 500.0, -200.0),
        Minute(at(22), Quote(25.00, 25.02, 25.01, at(22)), INAV_MINUTE, 90.0, True, 100.0, 0.0),
        Minute(at(23), Quote(25.00, 25.02, 25.01, at(23)), INAV_MINUTE, 10.0, False, 100.0, 0.0),
        Minute(at(24), Quote(24.94, 24.96, 24.95, at(24)), INAV_MINUTE, 10.0, True, 300.0, -300.0),
        Minute(at(25), Quote(24.90, 24.92, 24.91, at(25)), INAV_MINUTE, 10.0, True, 200.0, -200.0),
    ]


# ============================================================ 1. iNAV (hand file section 1)


def test_ledger_14_inav_zero_move_is_nav_times_one_plus_accruals():
    """Required unit test 14, all three clauses. Hand file section 1.

    The accrual is on TWO day counts, 360 for the collateral yield and 365 for the expense
    ratio, and the equality below is asserted with `==` because the hand file chose numbers
    on which `a + a*x` and `a*(1+x)` are the same double.
    """
    assert Y_CASH / 360 == 0.0001388888888888889
    assert ER / 365 == 2.7397260273972603e-05
    assert Y_CASH / 360 - ER / 365 == ACCRUAL

    # (a) zero move: NAV[t-1] x (1 + accruals), exactly, and at both leverages.
    for leverage in (2, -2):
        assert inav(NAV_PREV, leverage, 0.0, Y_CASH, ER) == INAV_FLAT
    assert NAV_PREV * (1 + ACCRUAL) == INAV_FLAT

    # (b) L = +2, r = +1% rises about 2% -- +2.011%, the extra being the accrual.
    long_inav = inav(NAV_PREV, 2, 0.01, Y_CASH, ER)
    assert long_inav == INAV_LONG
    assert NAV_PREV * (1 + 2 * 0.01) == 102.0
    assert long_inav / NAV_PREV - 1 == 0.02011149162861492
    assert math.isclose(long_inav / NAV_PREV - 1, 0.02, abs_tol=2e-4)

    # (c) L = -2 falls about 2% -- by slightly LESS than 2%, same reason.
    short_inav = inav(NAV_PREV, -2, 0.01, Y_CASH, ER)
    assert short_inav == INAV_SHORT
    assert short_inav / NAV_PREV - 1 == -0.019888508371385116
    assert math.isclose(short_inav / NAV_PREV - 1, -0.02, abs_tol=2e-4)

    # (d) the unlevered funds, whose rebalance factor is an integer zero.
    assert inav(NAV_PREV, 1, 0.01, Y_CASH, ER) == INAV_UNLEVERED
    assert UNG.rebalance_factor == 0
    assert BOIL.rebalance_factor == 2
    assert KOLD.rebalance_factor == 6


def test_the_day_counts_are_not_interchangeable():
    """Both on 365 the accrual is 1.7% smaller -- hand file section 1, stated as a warning."""
    both_365 = Y_CASH / 365 - ER / 365
    assert both_365 == 0.00010958904109589043
    assert both_365 != ACCRUAL
    assert math.isclose(both_365 / ACCRUAL, 0.983, abs_tol=5e-4)


def test_inav_refuses_an_unsourced_expense_ratio():
    """`er=None` is what all six constants carry; the formula raises rather than defaulting."""
    with pytest.raises(FundModelError, match="Section 3.2"):
        inav(NAV_PREV, 2, 0.0, Y_CASH, None)
    assert all(f.er is None for f in (BOIL, KOLD, UNG))


# =================================================== 2. Gate 0b (hand file section 2)


def test_ledger_20_gate_0b_reproduces_the_hand_calculated_error():
    """Required unit test 20. Hand file section 2: 19 of 20 within 5 bp is exactly the bar."""
    official = [1000.0] * 20
    good = [1000.2] * 19 + [1000.8]
    result = gate_0b(good, official)
    assert result.bp_errors[0] == 2.0000000000004547
    assert result.bp_errors[19] == 7.999999999999545
    assert result.n_within == 19 and result.n_days == 20
    assert result.share_within == 0.95
    assert result.passes is True
    assert result.worst_bp == 7.999999999999545

    # Two days beyond the limit and the same fund fails.
    worse = [1000.2] * 18 + [1000.8, 1000.8]
    failed = gate_0b(worse, official)
    assert failed.n_within == 18
    assert failed.share_within == 0.90
    assert failed.passes is False

    # The limit itself is inclusive, and the low side is measured on |bp|.
    boundary = gate_0b([1000.5], [1000.0])
    assert boundary.bp_errors == (5.0,)
    assert boundary.passes is True
    low = gate_0b([999.4], [1000.0])
    assert low.bp_errors == (-6.000000000000227,)
    assert low.passes is False


def test_gate_0b_refuses_the_three_shapes_that_would_pass_vacuously():
    with pytest.raises(FundModelError, match="iNAV values against"):
        gate_0b([1000.0] * 19, [1000.0] * 20)
    with pytest.raises(FundModelError, match="no days"):
        gate_0b([], [])
    with pytest.raises(FundModelError, match="official NAV"):
        gate_0b([1000.0], [0.0])


# ====================================== 3. the premium and its features (hand file section 3)


def test_the_four_premium_features_on_the_hand_worked_day():
    """Hand file section 3: four valid minutes of six, and all four features over them."""
    minutes = _minutes()
    assert minute_feature(minutes[0], INAV_MINUTE) == PREM_1
    assert minute_feature(minutes[1], INAV_MINUTE) == PREM_2
    assert minute_feature(minutes[2], INAV_MINUTE) is None
    assert minute_feature(minutes[3], INAV_MINUTE) is None
    assert minute_feature(minutes[4], INAV_MINUTE) == PREM_3
    assert minute_feature(minutes[5], INAV_MINUTE) == PREM_4

    f = features(minutes, w_start=W_START, trailing_volume_mean=4000.0)
    assert f.n_valid == 4
    assert f.prem_twa == PREM_TWA
    assert f.prem_frac == -0.25
    assert f.vol_x == 0.5
    assert f.sv_etf == 2500.0
    assert f.c_ap == 0.001


def test_stress_is_the_z_of_the_absolute_premium():
    """Hand file section 4, including the sign-insensitivity line 211 implies."""
    day = dt.date(2026, 9, 18)
    trailing = [
        (day - dt.timedelta(days=60 - i), 0.001 if i < 30 else 0.003) for i in range(60)
    ]
    assert stress(0.004, trailing, day=day) == 1.9832633040858023
    assert stress(-0.004, trailing, day=day) == 1.9832633040858023
    assert stress(0.002, trailing, day=day) == 0.0


# ============================================ 5. creations and the split (hand file section 5)


def test_the_creation_flow_and_its_split_in_contracts():
    """Hand file section 5: $10m into BOIL is +666.67 NG contracts, and the split of it."""
    assert delta_create(6000000.0, 5600000.0, 25.0) == CREATE_USD
    assert NG_MULTIPLIER * P_HELD == 30000.0
    assert create_flow(2, CREATE_USD, NG_MULTIPLIER, P_HELD) == FLOW_BOIL

    h = hedged_fraction(1.0, 0.5, 0.0)
    assert h == H_AT_X1
    window, intraday = split(h, FLOW_BOIL)
    assert window == Q3_WINDOW
    assert intraday == Q3_INTRADAY
    # Exact on THESE doubles; the hand file says why it is not exact in general.
    assert window + intraday == FLOW_BOIL
    neg_window, neg_intraday = split(h, -FLOW_BOIL)
    assert (neg_window, neg_intraday) == (-Q3_WINDOW, -Q3_INTRADAY)


def test_the_hedged_fraction_grid_is_strictly_decreasing():
    """Hand file section 5.4, the four cells and the two boundaries."""
    grid = [hedged_fraction(1.0, 0.5, s) for s in (-2.0, 0.0, 2.0, 4.0)]
    assert grid == [0.8807970779778823, H_AT_X1, 0.5, H_AT_XM1]
    assert grid == sorted(grid, reverse=True)
    assert 1.0 - H_AT_X1 == H_AT_XM1
    # h1 = 0 is flat and permitted (line 472 is h1 >= 0).
    assert {hedged_fraction(1.0, 0.0, s) for s in (-5.0, 0.0, 5.0)} == {H_AT_X1}
    # P3.7: stress + g1 x att_accel reproduces the stress = +2 cell.
    assert hedged_fraction(1.0, 0.5, 0.0, g1=2.0, att_accel=1.0) == 0.5


# ============================================================ 6-7. P9 (hand file sections 6-7)


def test_ledger_26_the_p9_rebalance_is_twelve_and_twenty_four_million():
    """Required unit test 26, quoted: +3x with AUM $50m and r = +4% gives dH = +$12m; -3x
    gives +$24m (same sign as the move). Both EXACT doubles -- hand file section 6.1."""
    aum = 50000000.0
    assert delta_h(aum, 3.0, 0.04) == DH_LONG
    assert delta_h(aum, -3.0, 0.04) == DH_SHORT
    assert DH_LONG == 12e6 and DH_SHORT == 24e6
    # the intermediate products the hand file walks through
    assert aum * 3.0 == 150000000.0
    assert 150000000.0 * (3.0 - 1) == 300000000.0
    assert 150000000.0 * (3.0 - 1) * 0.04 == DH_LONG
    # same sign as the move on both, and the -3x product's trade is twice the size
    assert DH_SHORT == 2 * DH_LONG
    # ...and the exactness is a property of these numbers, not of the expression:
    assert delta_h(aum, 1.4, 0.04) == 1119999.9999999998


def test_q9_converts_the_summed_rebalance_into_contracts():
    """Hand file section 6.2, the netting fraction across its whole permitted range."""
    assert DH_LONG + DH_SHORT == DH_TOTAL
    assert q9(DH_TOTAL, 0.0, NG_MULTIPLIER, P_HELD) == 1200.0
    assert q9(DH_TOTAL, 0.25, NG_MULTIPLIER, P_HELD) == 900.0
    assert q9(DH_TOTAL, 0.5, NG_MULTIPLIER, P_HELD) == 600.0
    assert q9(DH_TOTAL, 1.0, NG_MULTIPLIER, P_HELD) == 0.0
    with pytest.raises(NonUsError, match=r"outside \[0, 1\]"):
        q9(DH_TOTAL, 1.5, NG_MULTIPLIER, P_HELD)


def test_the_fx_conversion_uses_the_prior_settlement():
    """Hand file section 6.3: C$175m at 0.74, not at today's 0.75."""
    rates = {"2026-09-16": 0.73, "2026-09-17": 0.74, "2026-09-18": 0.75}
    assert aum_usd(AUM_CAD, rates, dt.date(2026, 9, 18)) == AUM_USD_HNU
    assert AUM_CAD * FX_PRIOR == AUM_USD_HNU
    # what using today's rate would have cost: $1.75m on one product, on one day of FX
    assert AUM_CAD * 0.75 - AUM_USD_HNU == 1750000.0


def test_the_index_month_follows_the_product_and_not_the_curve():
    """Hand file section 6.5."""
    curve = ["NGV6", "NGX6", "NGZ6"]
    assert index_month(BETAPRO_HNU, curve) == "NGV6"
    assert index_month(WT_3NGL, curve) == "NGX6"
    with pytest.raises(NonUsError, match="no index month rule"):
        index_month(WT_3OIL, curve)


def test_ledger_29_the_restrike_fires_at_six_point_seven_and_not_at_six_point_five():
    """Required unit test 29, both halves. Hand file section 7."""
    r = Restrike(threshold=0.20, L=3)
    assert r.underlying_trigger == 0.06666666666666667

    fired_value = product_value(RESET_LEVEL, 3, -0.067)
    assert fired_value == VALUE_AT_M67
    event = r.check(fired_value, RESET_LEVEL)
    assert event is not None
    assert event.drawdown == DRAWDOWN_AT_M67
    assert event.new_reset_level == VALUE_AT_M67

    quiet_value = product_value(RESET_LEVEL, 3, -0.065)
    assert quiet_value == VALUE_AT_M65
    assert (quiet_value - RESET_LEVEL) / RESET_LEVEL == -0.195
    assert r.check(quiet_value, RESET_LEVEL) is None

    # the boundary is inclusive, and the short product's adverse move is a rise
    assert r.check(80.0, RESET_LEVEL) is not None
    assert product_value(RESET_LEVEL, -3, 0.067) == VALUE_AT_M67
    assert Restrike(threshold=0.20, L=-3).check(VALUE_AT_M67, RESET_LEVEL) is not None

    # "the settlement-window flow is recomputed from the restrike level"
    assert recompute_delta_h_from_restrike(20000000.0, 3.0, -0.01) == -1200000.0
    assert recompute_delta_h_from_restrike(20000000.0, 3.0, 0.02) == 2400000.0


def test_the_restrike_log_is_line_294s_three_columns(tmp_path: Path):
    """Hand file section 7: timestamp, product, estimated dH -- and no default path."""
    log = RestrikeLog()
    log.add(
        RestrikeEvent(
            drawdown=DRAWDOWN_AT_M67,
            new_reset_level=VALUE_AT_M67,
            threshold=0.20,
            L=3,
            timestamp=dt.datetime(2026, 9, 18, 13, 47),
            product="3NGL",
            estimated_dh=-1200000.0,
        )
    )
    path = log.write(tmp_path / "restrike_events.csv")
    text = path.read_text(encoding="utf-8")
    assert text == "timestamp,product,estimated_dH\n2026-09-18T13:47:00,3NGL,-1200000.0\n"
    with pytest.raises(NonUsError, match="exists"):
        log.write(path)

    # an uncomputed dH is the empty string, never 0.0
    second = RestrikeLog()
    second.add(
        RestrikeEvent(
            drawdown=-0.25,
            new_reset_level=75.0,
            threshold=0.20,
            L=3,
            timestamp=dt.datetime(2026, 9, 18, 14, 1),
            product="3NGL",
        )
    )
    other = second.write(tmp_path / "second.csv")
    assert other.read_text(encoding="utf-8").splitlines()[1].endswith(",3NGL,")


def test_the_repository_supplies_the_multipliers_the_deposit_does_not(tmp_path: Path):
    """Hand file section 0: NG 10,000 MMBtu and CL 1,000 bbl, from the committed specs file.

    Read out of `data/futures_contract_specs.json` rather than retyped, because the claim is
    that the fund constants carry THAT file's contract size and not a number of mine.
    """
    import json

    repo = Path(__file__).resolve().parents[2]
    specs = json.loads((repo / "data" / "futures_contract_specs.json").read_text(encoding="utf-8"))
    assert specs["NG"]["usd_per_point"] == 10000.0
    assert specs["CL"]["usd_per_point"] == 1000.0
    assert BOIL.multiplier == specs["NG"]["usd_per_point"]
    assert specs["NG"]["contract_unit"] == "10,000 MMBtu"
    assert specs["CL"]["contract_unit"] == "1,000 barrels"


def test_the_creation_term_and_the_premium_kernel_are_the_documents_own():
    """Two one-liners the hand file states and nothing else in this file asserts."""
    assert creation_term(1, CREATE_USD, 99.0) == CREATE_USD
    assert creation_term(0, None, 99.0) == 99.0
    q = Quote(25.02, 25.04, 25.10, dt.datetime(2026, 9, 18, 14, 20))
    assert q.mid == 25.03
    assert premium(q, INAV_MINUTE) == PREM_1
    assert Fund("X", 3, "NG", NG_MULTIPLIER).rebalance_factor == 6
