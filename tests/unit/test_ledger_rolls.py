"""`backtest_framework.ledger.rolls` -- P8a fund rolls and P8b's scaled flag (D610).

Covers the settlement flow ledger's required unit tests 37 (line 743), 39 (line 745) and 40
(line 746). The hand-worked case for number 38 is in
`tests/golden/test_ledger_flows_ledger.py`.

Offline: no fixture, no network, no strategy return. No expiry calendar is read -- see the
module docstring of `ledger/rolls.py` for why "two weeks" is 14 calendar days here and what
the alternative reading would give.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from backtest_framework.ledger.flows import LedgerError
from backtest_framework.ledger.rolls import (
    ROLL_SCHEDULES,
    RollSchedule,
    TWO_WEEKS_DAYS,
    UNG_SCHEDULE,
    q8b,
    roll_days,
    roll_legs,
    validate_roll,
)

#: A SYNTHETIC expiry, chosen so the four calendar days are Mon..Thu and the case is legible.
#: It is not sourced as any contract's real expiry and this module reads no expiry calendar.
NEAR_EXPIRY = dt.date(2026, 3, 30)


# ------------------------------------------------------------------ required unit test 37


def test_ledger_37_ung_rolls_four_days_at_25_percent_from_two_weeks_before_expiry() -> None:
    """Line 743: "UNG roll fractions: four days at 25% each; cumulative 100%; day 1 starts
    two weeks before near-month expiration per the rule."

    Line 327 is the source and it is carried on the schedule object, so a reader can see
    which filing sentence the four numbers came from.
    """
    s = UNG_SCHEDULE
    assert s.fractions == (0.25, 0.25, 0.25, 0.25)
    assert s.days == 4
    assert math.fsum(s.fractions) == 1.0  # exact: four binary fractions at one exponent
    assert s.cumulative == (0.25, 0.5, 0.75, 1.0)
    assert s.start_rule == "two_weeks_before_near_expiry"
    assert "four-day period beginning two weeks before" in s.source
    assert "75/25, 50/50, 25/75" in s.source

    # The benchmark weights line 327 states are the complements of the cumulative fractions.
    assert [(1.0 - c, c) for c in s.cumulative] == [(0.75, 0.25), (0.5, 0.5), (0.25, 0.75), (0.0, 1.0)]

    days = roll_days(NEAR_EXPIRY)
    assert len(days) == 4
    assert (NEAR_EXPIRY - days[0]).days == TWO_WEEKS_DAYS == 14
    assert days == [dt.date(2026, 3, 16), dt.date(2026, 3, 17),
                    dt.date(2026, 3, 18), dt.date(2026, 3, 19)]
    assert all((b - a).days == 1 for a, b in zip(days, days[1:]))

    # THE AMBIGUITY, MADE VISIBLE RATHER THAN HIDDEN. Fourteen calendar days is a choice; the
    # four days are not adjusted for weekends or holidays, and on most expiries two of them
    # are a Saturday and a Sunday. A study reconciles against the issuer's published CSV
    # (line 327's last sentence) before using these dates.
    weekend_case = roll_days(dt.date(2026, 3, 27))
    assert [d.weekday() for d in weekend_case] == [4, 5, 6, 0]
    assert any(d.weekday() >= 5 for d in weekend_case)


def test_for_fund_refuses_every_fund_whose_schedule_is_not_sourced() -> None:
    """Line 328: "USO, BOIL, KOLD, UCO, SCO, P9 products: to source from each prospectus or
    index methodology (Q19). Do not assume."

    UNG's schedule is the only one line 327 states, and USO is the trap: same issuer, same
    family, different prospectus.
    """
    assert RollSchedule.for_fund("UNG") is UNG_SCHEDULE
    assert RollSchedule.for_fund("ung") is UNG_SCHEDULE
    assert sorted(ROLL_SCHEDULES) == ["UNG"]
    for fund in ("USO", "BOIL", "KOLD", "UCO", "SCO", "HNU", "3NGL"):
        with pytest.raises(LedgerError, match="Do not assume"):
            RollSchedule.for_fund(fund)
    with pytest.raises(LedgerError, match="non-empty string"):
        RollSchedule.for_fund("")


def test_a_schedule_must_be_sourced_and_must_roll_the_whole_position() -> None:
    with pytest.raises(LedgerError, match="sum to"):
        RollSchedule((0.25, 0.25, 0.25), "two_weeks_before_near_expiry", "synthetic")
    with pytest.raises(LedgerError, match="must lie in"):
        RollSchedule((0.5, 0.5, 0.0), "two_weeks_before_near_expiry", "synthetic")
    with pytest.raises(LedgerError, match="Do not assume"):
        RollSchedule((1.0,), "two_weeks_before_near_expiry", "")
    # A second start rule is a second sourced fact, not a branch.
    other = RollSchedule((1.0,), "five_business_days_before_expiry", "synthetic, for this test")
    with pytest.raises(LedgerError, match="only the 'two_weeks_before_near_expiry' rule"):
        roll_days(NEAR_EXPIRY, other)
    with pytest.raises(LedgerError, match="must be a datetime.date"):
        roll_days(dt.datetime(2026, 3, 30, 14, 28))  # type: ignore[arg-type]


# ------------------------------------------------------------------ required unit test 39


def test_ledger_39_holdings_at_25_percent_a_day_pass_and_one_big_day_falls_back_to_p8b() -> None:
    """Line 745: "synthetic holdings changing by 25% per day across the window pass; holdings
    that change all on one day fail and trigger the P8b fallback."

    Line 340 is the consequence and it is a FIELD on the result, not an inference: "Any fund
    whose reconstruction fails validation falls back to P8b treatment."
    """
    ok = validate_roll([0.25, 0.25, 0.25, 0.25])
    assert ok.passes is True
    assert ok.fallback_to_p8b is False
    assert ok.max_abs_deviation == 0.0

    bad = validate_roll([1.0, 0.0, 0.0, 0.0])
    assert bad.passes is False
    assert bad.fallback_to_p8b is True
    assert bad.max_abs_deviation == 0.75
    assert "P8b" in bad.reason and "day 1 of 4" in bad.reason

    # Inside the declared tolerance -- a published holdings file rounds.
    assert validate_roll([0.26, 0.24, 0.25, 0.25]).passes is True
    # Outside it, and the failing DAY is named.
    off = validate_roll([0.30, 0.20, 0.25, 0.25])
    assert off.passes is False and "day 1 of 4" in off.reason

    # The second clause, isolated: EVERY day is within tolerance of its phi and the roll
    # still never completed. A per-day check alone would pass this and leave 4% of the
    # position sitting in the expiring month with nothing saying so.
    partial = validate_roll([0.24, 0.24, 0.24, 0.24])
    assert max(abs(v - 0.25) for v in (0.24,) * 4) < 0.02
    assert partial.passes is False and "sum to" in partial.reason
    assert partial.fallback_to_p8b is True

    # A length mismatch is not a tolerance question.
    with pytest.raises(LedgerError, match="3 observed day"):
        validate_roll([0.33, 0.33, 0.34])
    with pytest.raises(LedgerError, match="tol must be positive"):
        validate_roll([0.25] * 4, tol=0.0)


# ------------------------------------------------------------------ required unit test 40


def test_ledger_40_a_fund_counted_in_p8a_contributes_exactly_zero_to_p8b() -> None:
    """Line 746: "No double counting: a fund in P8a contributes zero to P8b."

    Line 352: "P8b must exclude any fund already counted in P8a." The term is not computed at
    all, so no beta8 can make it non-zero -- that is what turns "must exclude" into a
    guarantee.
    """
    p8a = ("UNG", "USO", "BOIL", "KOLD", "UCO", "SCO")
    for fund in p8a:
        for beta8 in (0.0, 1e9, -1e9, 12345.678):
            out = q8b(1, 1.0, beta8, fund=fund, p8a_funds=p8a)
            assert out == 0.0
            assert not math.copysign(1.0, out) < 0.0  # a clean +0.0, not a signed zero
    assert q8b(1, 1.0, 5000.0, fund="ung", p8a_funds=p8a) == 0.0  # case-insensitive

    # A tracker NOT in P8a gets line 348's product.
    assert q8b(1, 0.25, 4000.0, fund="GSCI-TRACKER", p8a_funds=p8a) == 1000.0
    assert q8b(0, 0.25, 4000.0, fund="GSCI-TRACKER", p8a_funds=p8a) == 0.0
    assert q8b(True, 0.5, -4000.0, fund="GSCI-TRACKER", p8a_funds=p8a) == -2000.0

    with pytest.raises(LedgerError, match="roll_flag must be 0 or 1"):
        q8b(2, 0.25, 4000.0, fund="GSCI-TRACKER", p8a_funds=p8a)
    with pytest.raises(LedgerError, match="roll_fraction must lie"):
        q8b(1, 1.5, 4000.0, fund="GSCI-TRACKER", p8a_funds=p8a)
    # A bare string would test membership character by character.
    with pytest.raises(LedgerError, match="collection of fund names"):
        q8b(1, 0.25, 4000.0, fund="UNG", p8a_funds="UNG,USO")  # type: ignore[arg-type]


# --------------------------------------------------------------------------- the two legs


def test_roll_legs_refuses_the_inputs_that_would_double_count_the_short_side() -> None:
    """`n_old` is a COUNT and the short side is carried by sign(L); carrying it twice halves
    nothing and doubles the sign."""
    with pytest.raises(LedgerError, match="non-negative"):
        roll_legs(0.25, -400.0, -2.0, 3.0, 4.0)
    with pytest.raises(LedgerError, match="L = 0 has no sign"):
        roll_legs(0.25, 400.0, 0.0, 3.0, 4.0)
    with pytest.raises(LedgerError, match="phi must lie in"):
        roll_legs(0.0, 400.0, 1.0, 3.0, 4.0)
    with pytest.raises(LedgerError, match="must be positive"):
        roll_legs(0.25, 400.0, 1.0, 0.0, 4.0)
    # A zero position rolls nothing, in both legs, for either sign of L.
    assert roll_legs(0.25, 0.0, 1.0, 3.0, 4.0) == (0.0, 0.0)
