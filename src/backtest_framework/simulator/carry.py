"""Calendar-day carry accrual.

Implements D33: carry costs (margin interest, borrow fees, funding) accrue on the
calendar-day gap between consecutive bar timestamps, never on bar count. A Friday-close
to Monday-close hold is one bar but three calendar days of carry; per-bar accrual
undercharges every weekend and holiday.

Day-count convention is ACT/365 (see D51) — a single stated default, not per-broker or
per-currency yet. That refinement is deferred to the equity cost bricks step (D4, D5).
"""

from datetime import datetime

DEFAULT_DAY_COUNT = 365.0


def calendar_days_between(start: datetime, end: datetime) -> float:
    """Calendar-day gap between two timestamps, as a float (fractional for intraday bars)."""
    return (end - start).total_seconds() / 86400.0


def accrue_carry(
    annual_rate: float,
    base_amount: float,
    calendar_days: float,
    *,
    day_count: float = DEFAULT_DAY_COUNT,
) -> float:
    """Carry accrued on `base_amount` at `annual_rate` over `calendar_days` calendar days.

    `base_amount` is whatever the calling cost brick has already determined is the
    carry-bearing quantity (e.g. gross exposure minus capital for margin interest, or
    short notional for a borrow fee) — this function only knows about the accrual math,
    not position semantics.
    """
    return base_amount * annual_rate * calendar_days / day_count


def accrue_carry_between_bars(
    annual_rate: float,
    base_amount: float,
    prev_timestamp: datetime,
    curr_timestamp: datetime,
    *,
    day_count: float = DEFAULT_DAY_COUNT,
) -> float:
    """Convenience wrapper: accrue carry over the calendar-day gap between two bar timestamps."""
    days = calendar_days_between(prev_timestamp, curr_timestamp)
    return accrue_carry(annual_rate, base_amount, days, day_count=day_count)
