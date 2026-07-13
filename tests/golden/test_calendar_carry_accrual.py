"""Golden-master tests for D33 (calendar-day carry accrual) and D51 (ACT/365 day count).

Hand-worked arithmetic for every case lives in test_calendar_carry_accrual.hand.txt,
next to this file, per D39. Tolerance follows D47 (money reconciliation, default 1e-6).
"""

from datetime import datetime

import pytest

from backtest_framework.simulator.carry import (
    accrue_carry,
    accrue_carry_between_bars,
    calendar_days_between,
)

TOLERANCE = 1e-6  # D47


def test_friday_close_to_monday_close_accrues_three_days():
    prev = datetime(2026, 7, 10, 16, 0)  # Friday
    curr = datetime(2026, 7, 13, 16, 0)  # Monday
    assert calendar_days_between(prev, curr) == pytest.approx(3.0, rel=TOLERANCE)

    accrued = accrue_carry_between_bars(annual_rate=0.06, base_amount=100_000, prev_timestamp=prev, curr_timestamp=curr)
    assert accrued == pytest.approx(49.31506849315068, rel=TOLERANCE)


def test_holiday_gap_accrues_four_days():
    prev = datetime(2026, 7, 2, 16, 0)  # Thursday
    curr = datetime(2026, 7, 6, 16, 0)  # Monday (Fri holiday + weekend in between)
    assert calendar_days_between(prev, curr) == pytest.approx(4.0, rel=TOLERANCE)

    accrued = accrue_carry_between_bars(annual_rate=0.05, base_amount=80_000, prev_timestamp=prev, curr_timestamp=curr)
    assert accrued == pytest.approx(43.83561643835616, rel=TOLERANCE)


def test_hourly_bars_over_weekend_accrue_full_gap_not_one_bar_duration():
    prev = datetime(2026, 7, 10, 21, 0)  # Friday, last hourly bar of the week
    curr = datetime(2026, 7, 13, 9, 0)  # Monday, first hourly bar of the next week
    assert calendar_days_between(prev, curr) == pytest.approx(2.5, rel=TOLERANCE)

    accrued = accrue_carry_between_bars(annual_rate=0.06, base_amount=100_000, prev_timestamp=prev, curr_timestamp=curr)
    assert accrued == pytest.approx(41.0958904109589, rel=TOLERANCE)

    # The bug D33 kills: charging one bar-duration (1 hour = 1/24 day) instead of the gap.
    naive_buggy_accrual = accrue_carry(annual_rate=0.06, base_amount=100_000, calendar_days=1 / 24)
    assert accrued != pytest.approx(naive_buggy_accrual, rel=TOLERANCE)


def test_zero_gap_accrues_nothing():
    t = datetime(2026, 7, 13, 16, 0)
    assert accrue_carry_between_bars(annual_rate=0.06, base_amount=100_000, prev_timestamp=t, curr_timestamp=t) == 0.0
