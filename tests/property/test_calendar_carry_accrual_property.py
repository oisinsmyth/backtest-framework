"""Property test for D33: total accrued carry over any window equals
rate * sum(calendar-day gaps), regardless of how the window is chopped into bars.

Per D34, every stochastic test takes a seed; Hypothesis's own seeding serves that role here.

**This file's own note used to point at "the fixed database-free profile in pyproject.toml /
conftest". There is no such profile and there never was** — no `[tool.hypothesis]` section, no
registered profile anywhere in the repo. It also sets no `settings(...)` of its own, so unlike its
siblings it runs at hypothesis's defaults: not derandomized, 100 examples. Left that way, now
stated rather than implied. D537 has the wider point: `derandomize=True` would not buy example
determinism anyway.
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st

from backtest_framework.simulator.carry import accrue_carry, accrue_carry_between_bars

TOLERANCE = 1e-6  # D47


@given(
    start=st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 1, 1)),
    gaps_hours=st.lists(st.floats(min_value=0.01, max_value=500, allow_nan=False, allow_infinity=False), min_size=1, max_size=30),
    annual_rate=st.floats(min_value=-0.5, max_value=0.5, allow_nan=False, allow_infinity=False),
    base_amount=st.floats(min_value=-1_000_000, max_value=1_000_000, allow_nan=False, allow_infinity=False),
)
def test_total_accrual_equals_rate_times_total_calendar_days(start, gaps_hours, annual_rate, base_amount):
    timestamps = [start]
    for hours in gaps_hours:
        timestamps.append(timestamps[-1] + timedelta(hours=hours))

    total_via_bars = sum(
        accrue_carry_between_bars(annual_rate, base_amount, prev, curr)
        for prev, curr in zip(timestamps, timestamps[1:])
    )

    total_calendar_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400.0
    total_via_span = accrue_carry(annual_rate, base_amount, total_calendar_days)

    # Relative comparison breaks down near zero (e.g. base_amount ~ 0); fall back to an
    # absolute tolerance there, consistent with D47's spirit rather than its letter.
    if abs(total_via_span) < 1e-3:
        assert abs(total_via_bars - total_via_span) < 1e-6
    else:
        assert total_via_bars == pytest.approx(total_via_span, rel=TOLERANCE)
