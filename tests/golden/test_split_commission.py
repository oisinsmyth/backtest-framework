"""G-gate: commission on the pre-split XOP bar computed on TRUE as-traded prices vs
the adjusted-price calculation — difference nonzero and equal to hand arithmetic
(test_split_commission.hand.txt). Uses the committed raw fixture's actual bar.
"""

from datetime import datetime
from pathlib import Path

import pytest

from backtest_framework.costs.equity_bricks import IBKRCommission
from backtest_framework.data.corporate_actions import as_traded_from_adjusted, load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.instruments.equity import Equity

TOLERANCE = 1e-6  # D47
REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = REPO / "data" / "fixtures"

XOP = Equity(symbol="XOP")
PRE_SPLIT_DAY = datetime(2020, 3, 27)


def _closes():
    bars = load_fixture_csv(FIXTURE_DIR / "xle_xop_daily_2015_2024_raw.csv")["XOP"]
    events = load_events_json(FIXTURE_DIR / "xle_xop_daily_2015_2024_raw_events.json")
    splits = events.splits_by_symbol["XOP"]
    true_bars = as_traded_from_adjusted(bars, splits)

    adjusted_close = next(tb.bar.close for tb in bars if tb.timestamp == PRE_SPLIT_DAY)
    true_close = next(tb.bar.close for tb in true_bars if tb.timestamp == PRE_SPLIT_DAY)
    return adjusted_close, true_close


def test_pre_split_bar_frames_differ_by_the_split_ratio():
    adjusted_close, true_close = _closes()
    assert adjusted_close == pytest.approx(32.12, abs=0.01)
    assert true_close == pytest.approx(adjusted_close * 0.25, rel=TOLERANCE)


def test_commission_on_true_vs_adjusted_notional_differs_by_hand_amount():
    adjusted_close, true_close = _closes()
    brick = IBKRCommission()
    notional = 1_000 * adjusted_close  # $32,120 deployed either way

    true_shares = notional / true_close  # 4,000 real shares
    adjusted_shares = notional / adjusted_close  # 1,000 phantom shares

    commission_true = brick.cost(XOP, quantity=true_shares, price=true_close)
    commission_adjusted = brick.cost(XOP, quantity=adjusted_shares, price=adjusted_close)

    assert commission_true == pytest.approx(20.00, rel=TOLERANCE)
    assert commission_adjusted == pytest.approx(5.00, rel=TOLERANCE)
    assert commission_true - commission_adjusted == pytest.approx(15.00, rel=TOLERANCE)  # nonzero, exact
