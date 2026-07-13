"""Integration test for D30: both legs of a pairs position drift via price movement
alone (no order submitted on any bar) until gross exposure exceeds the limit — the
violation must be flagged on exactly the bar it occurs, not before or after.

Hand-worked arithmetic lives in test_risk_monitor_drift.hand.txt, next to this file.
"""

from backtest_framework.engine.risk import RiskLimits, RiskMonitor
from backtest_framework.instruments.equity import Equity

XLE = Equity(symbol="XLE")
XOP = Equity(symbol="XOP")
INSTRUMENTS = {"XLE": XLE, "XOP": XOP}

# Opened once, never touched again — every bar below evaluates the SAME positions.
POSITIONS = {"XLE": 700.0, "XOP": -700.0}

BARS = [
    {"XLE": 90.0, "XOP": 90.0},
    {"XLE": 95.0, "XOP": 95.0},
    {"XLE": 105.0, "XOP": 105.0},
    {"XLE": 110.0, "XOP": 110.0},
]


def test_violation_flagged_on_exactly_the_bar_it_occurs_with_no_order_submitted():
    monitor = RiskMonitor(RiskLimits(max_gross_exposure=150_000.0))

    violations = [
        monitor.evaluate(POSITIONS, prices, INSTRUMENTS, bar_index=i) for i, prices in enumerate(BARS)
    ]

    assert violations[0] is None
    assert violations[1] is None
    assert violations[2] is None  # 147,000 <= 150,000 — close, but not yet a violation

    violation = violations[3]
    assert violation is not None
    assert violation.rule == "max_gross_exposure"
    assert violation.limit == 150_000.0
    assert violation.observed == 154_000.0
    assert violation.bar_index == 3
