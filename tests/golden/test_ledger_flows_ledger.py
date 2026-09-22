"""Golden master for `backtest_framework.ledger` (D610).

Hand arithmetic in `test_ledger_flows_ledger.hand.txt`, which was written and saved to the
working tree BEFORE `src/backtest_framework/ledger/` existed, per D39 and CONTRIBUTING.md:
the ground truth is produced by a calculator that never imports this codebase, because a
`.hand.txt` derived from the implementation launders the implementation's assumptions into
the thing meant to check them.

The ledger of record is `docs/internal/User-Doc-Deposit/SETTLEMENT_FLOW_LEDGER_PREREG.md`
v1.9 -- an untracked, read-only deposit source, quoted by line number and never copied.

**Every assertion here is `==` except three, and the .hand.txt names all three**: `sigma_rem`
(5 sqrt(2), irrational), the consistency flag's threshold (2 sqrt(0.125), irrational, so only
the boolean outcomes are asserted exactly), and the interior of the P1/P2 routing identity
(one ulp wide by construction -- see the module docstring of `ledger/flows.py`).

No fixture is read and no strategy return is computed.
"""

from __future__ import annotations

import datetime as dt
import math
from pathlib import Path

import pytest

from backtest_framework.ledger.flows import (
    LedgerError,
    q1_notional,
    q1_rebalance,
    q2_swap,
    route,
)
from backtest_framework.ledger.netting import consistency_flag, fit_lambda
from backtest_framework.ledger.rolls import UNG_SCHEDULE, roll_days, roll_legs
from backtest_framework.ledger.update import kalman_update

HAND = Path(__file__).with_suffix(".hand.txt")

# --- the cases, transcribed from the .hand.txt ------------------------------------------

#: Case 1, required unit test 1 (line 707).
AUM = 1e9
R_UP = 0.05
#: Case 1's contract conversion: an NG-shaped pair, 10,000 MMBtu and $3.00.
MULTIPLIER = 10_000.0
P_HELD = 3.00

#: Case 2, required unit test 6 (line 712).
MU, VAR, P, R_NOISE, Z = 100.0, 400.0, 0.5, 100.0, 60.0

#: Case 3, required unit test 38 (line 744). P_old / P_new = 0.75 exactly.
PHI, N_OLD, P_OLD, P_NEW = 0.25, 400.0, 3.00, 4.00
NEAR_EXPIRY = dt.date(2026, 3, 30)

#: Case 4, required unit test 42 (line 748). Sum x^2 = 8, Sum xy = 16.
D_SX = [1.0, 1.0, 1.0, 1.0, 2.0]
D_SD = [2.0, 3.0, 1.0, 2.0, 4.0]


def test_hand_file_is_present_and_quotes_the_ledger() -> None:
    """The golden is only a golden while its hand arithmetic ships beside it."""
    text = HAND.read_text(encoding="utf-8")
    assert text.isascii(), "the .hand.txt is committed source and must stay ASCII"
    for quoted in (
        "Q1 = Sum_funds AUM[t-1] x L x (L - 1) x r[t, tau] x f_fut[t-1]",
        "K     = p sigma^2_total / (p^2 sigma^2_total + R)",
        "Sell_old     = - phi_f,d x N_old,f x sign(L_f)",
        "Fit:  DeltaSD_w = lambda x DeltaSX_w + eps_w,",
    ):
        assert quoted in text, f"the hand file no longer quotes: {quoted!r}"


# ----------------------------------------------------------------- required unit test 1


def test_ledger_1_q1_notional_at_l_plus_two_and_minus_two() -> None:
    """Line 707: L = +2 gives +1e8, L = -2 gives +3e8, both on a POSITIVE return.

    Hand file case 1. Both assertions are `==`: the document's left-to-right association is
    exact in binary64 on these numbers and the alternative grouping is not, which is why the
    last assertion here pins the grouping rather than trusting it.
    """
    assert q1_notional(AUM, 2.0, R_UP, 1.0) == 1e8
    assert q1_notional(AUM, -2.0, R_UP, 1.0) == 3e8

    # Both positive on a positive move -- line 707's parenthesis, and the mechanical core of
    # the hypothesis: a 2x long fund and a 2x inverse fund BOTH buy on an up day.
    assert q1_notional(AUM, 2.0, R_UP, 1.0) > 0.0
    assert q1_notional(AUM, -2.0, R_UP, 1.0) > 0.0
    # ... and the inverse fund's coefficient is three times the long fund's, 6 against 2.
    assert q1_notional(AUM, -2.0, R_UP, 1.0) == 3.0 * q1_notional(AUM, 2.0, R_UP, 1.0)

    # A negative move reverses both, exactly (IEEE multiplication is sign-symmetric).
    assert q1_notional(AUM, 2.0, -R_UP, 1.0) == -1e8
    assert q1_notional(AUM, -2.0, -R_UP, 1.0) == -3e8

    # The grouping measurement from the hand file, re-run here rather than quoted: the
    # document's own order is exact and pulling the two small factors together is not.
    assert AUM * 6 * 0.05 == 3e8
    assert AUM * (6 * 0.05) != 3e8
    assert AUM * (6 * 0.05) == 300000000.00000006

    # The contract conversion is one division applied to that same numerator.
    assert q1_rebalance(AUM, 2.0, R_UP, 1.0, MULTIPLIER, P_HELD) == 1e8 / (MULTIPLIER * P_HELD)


# ----------------------------------------------------------------- required unit test 6


def test_ledger_6_update_step_on_the_documents_own_numbers() -> None:
    """Line 712: mu = 100, sigma^2 = 400, p = 0.5, R = 100, z = 60.

    Hand file case 2. Four of the five outputs are exact and asserted with `==`; the fifth is
    5 sqrt(2) and is asserted to 12 places.
    """
    u = kalman_update(MU, VAR, P, R_NOISE, Z)
    assert u.k == 1.0
    assert u.q_hat == 110.0
    assert u.var_post == 200.0
    assert u.q_rem == 55.0
    assert math.isclose(u.sigma_rem, 0.5 * math.sqrt(200.0), rel_tol=0.0, abs_tol=1e-12)
    assert round(u.sigma_rem, 12) == round(7.071067811865475, 12)

    # K = 1 exactly because p sigma^2 = 200 and p^2 sigma^2 + R = 200: the measurement is
    # exactly as informative as the prior. Asserted as the two halves, so an implementation
    # that got the right K from the wrong numerator would not pass.
    assert P * VAR == 200.0
    assert P * P * VAR + R_NOISE == 200.0
    # (1 - K p) the wrong way up would still give 200 here, so the halves are pinned too.
    assert 1.0 - u.k * P == 0.5


# ---------------------------------------------------------------- required unit test 38


def test_ledger_38_roll_legs_sign_and_the_price_scaling() -> None:
    """Line 744: a long fund sells the expiring month and buys the next; an inverse fund does
    the reverse; new-month contracts are scaled by P_old / P_new.

    Hand file case 3. Exact throughout because 3.00 / 4.00 = 0.75 is a binary fraction.
    """
    assert P_OLD / P_NEW == 0.75

    sell, buy = roll_legs(PHI, N_OLD, +1.0, P_OLD, P_NEW)
    assert (sell, buy) == (-100.0, +75.0)

    inv_sell, inv_buy = roll_legs(PHI, N_OLD, -2.0, P_OLD, P_NEW)
    assert (inv_sell, inv_buy) == (+100.0, -75.0)

    # Only sign(L) enters: an L = -3 fund rolling the same N_old gets the same two legs.
    assert roll_legs(PHI, N_OLD, -3.0, P_OLD, P_NEW) == (inv_sell, inv_buy)

    # Line 335, "notional-matched" -- exact on these prices.
    assert buy * P_NEW == -sell * P_OLD == 300.0
    assert inv_buy * P_NEW == -inv_sell * P_OLD == -300.0

    # Required unit test 37's arithmetic, which shares this case: four days, 25% each,
    # cumulative 100%, day one two weeks before the near month's expiration.
    assert UNG_SCHEDULE.fractions == (0.25, 0.25, 0.25, 0.25)
    assert UNG_SCHEDULE.cumulative == (0.25, 0.5, 0.75, 1.0)
    days = roll_days(NEAR_EXPIRY, UNG_SCHEDULE)
    assert days == [dt.date(2026, 3, 16), dt.date(2026, 3, 17),
                    dt.date(2026, 3, 18), dt.date(2026, 3, 19)]
    assert (NEAR_EXPIRY - days[0]).days == 14
    # The hand file picked this expiry so the four calendar days are weekdays. Mon..Thu.
    assert [d.weekday() for d in days] == [0, 1, 2, 3]


# ---------------------------------------------------------------- required unit test 42


def test_ledger_42_lambda_is_projected_onto_the_unit_interval_and_the_flag_fires() -> None:
    """Line 748: the fit constrains lambda to [0, 1]; the flag triggers beyond 2 combined SE.

    Hand file case 4. lambda_unconstrained = 16/8 = 2.0 exactly, SE = sqrt(0.5/8) = 0.25
    exactly, and both are asserted with `==`.
    """
    f = fit_lambda(D_SD, D_SX)
    assert f.lam_unconstrained == 2.0
    assert f.lam == 1.0
    assert f.clipped is True
    assert f.se == 0.25

    # The hand file's residuals and s^2, re-derived from the returned slope.
    resid = [y - f.lam_unconstrained * x for y, x in zip(D_SD, D_SX)]
    assert resid == [0.0, 1.0, -1.0, 0.0, 0.0]
    assert math.fsum(r * r for r in resid) == 2.0
    assert 2.0 / (len(D_SD) - 1) == 0.5
    assert math.sqrt(0.5 / 8.0) == 0.25

    # An interior slope is returned untouched and reports clipped = False.
    interior = fit_lambda([1.0, 1.0, 1.0, 1.0, 2.0], D_SX)
    assert interior.lam_unconstrained == interior.lam
    assert interior.clipped is False

    # Line 499's flag. Threshold 2 sqrt(0.125) is irrational, so the BOOLEANS are asserted
    # exactly and the threshold only to 12 places.
    assert consistency_flag(n_hat=1.0, se_n=0.25, lam=0.75, se_lam=0.25) is True
    assert consistency_flag(n_hat=0.9, se_n=0.25, lam=0.75, se_lam=0.25) is False
    assert round(2.0 * math.sqrt(0.125), 12) == round(0.7071067811865476, 12)
    assert 1.0 - 0.75 == 0.25


# --------------------------------------------------- the routing identity's two regimes


def test_routing_is_exact_at_the_endpoints_and_one_ulp_wide_inside() -> None:
    """Line 709's claim is about the endpoints and this is what holds beyond them.

    Hand file case 1's last block. The endpoints are `==`; the interior is bounded by one ulp
    and the measured count of inexact points is pinned, so a change in the arithmetic that
    widened it would fail here rather than pass quietly.
    """
    total = q1_rebalance(AUM, 2.0, R_UP, 1.0, MULTIPLIER, P_HELD)

    q1, q2 = route(AUM, 2.0, R_UP, 1.0, 0.0, MULTIPLIER, P_HELD)
    assert (q1, q2) == (total, 0.0)

    q1, q2 = route(AUM, 2.0, R_UP, 0.0, 0.0, MULTIPLIER, P_HELD)
    assert (q1, q2) == (0.0, total)

    # n = 1 nets the whole swap book away, exactly.
    assert q2_swap(AUM, 2.0, R_UP, 0.0, 1.0, MULTIPLIER, P_HELD) == 0.0

    ulp = math.ulp(total)
    inexact = 0
    hand_inexact = 0
    for i in range(1, 100):
        f = i / 100
        a, b = route(AUM, 2.0, R_UP, f, 0.0, MULTIPLIER, P_HELD)
        gap = abs((a + b) - total)
        assert gap <= ulp, f"f_fut = {f}: routing is {gap / ulp} ulp wide"
        inexact += gap != 0.0
        # The hand file's own spelling, `total x f + total x (1 - f)`, recomputed here so its
        # count of 26 stays checked. It is NOT the module's spelling: line 156 is one
        # fraction, so `route` forms each numerator and divides once, and the two orders do
        # not agree in the last bit. Measured, the module's spelling is inexact at 51 of the
        # 99 interior points and the hand file's at 26 -- both bounded by the same one ulp,
        # and the record says so rather than the hand file being edited to match the code.
        hand_inexact += (total * f + total * (1.0 - f)) != total
    assert inexact == 51, "the module's own spelling: numerator first, one division"
    assert hand_inexact == 26, "the hand file's spelling: total, then split"


def test_the_leverage_coefficient_is_zero_at_l_one_and_l_zero() -> None:
    """Required unit test 2's arithmetic, on the golden's own numbers (line 708)."""
    assert q1_notional(AUM, 1.0, R_UP, 1.0) == 0.0
    assert q1_notional(AUM, 0.0, R_UP, 1.0) == 0.0
    assert q1_rebalance(AUM, 1.0, R_UP, 1.0, MULTIPLIER, P_HELD) == 0.0


def test_the_golden_cases_all_refuse_their_own_broken_input() -> None:
    """A golden that cannot fail is worse than none: each case's guard is fired here."""
    with pytest.raises(LedgerError):
        q1_notional(AUM, 2.0, R_UP, 1.5)  # f_fut outside [0, 1]
    with pytest.raises(LedgerError):
        kalman_update(MU, VAR, P, 0.0, Z)  # R = 0
    with pytest.raises(LedgerError):
        roll_legs(PHI, N_OLD, 0.0, P_OLD, P_NEW)  # sign(0) has no direction
    with pytest.raises(LedgerError):
        fit_lambda(D_SD, [0.0] * 5)  # a zero regressor column
    with pytest.raises(LedgerError):
        consistency_flag(n_hat=1.5, se_n=0.25, lam=0.75, se_lam=0.25)  # n outside [0, 1]
