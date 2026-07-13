"""Golden-master tests for D10 (gap-through-stop fills at the bar open).

Hand-worked arithmetic and reasoning for every case lives in
test_stop_fill_gap_through.hand.txt, next to this file, per D39.
"""

from backtest_framework.simulator.fills import Bar, StopSide, stop_fill_price


def test_sell_stop_gap_down_fills_at_open_not_stop():
    bar = Bar(open=38, high=39, low=37, close=38)
    assert stop_fill_price(StopSide.SELL_STOP, stop_price=45, bar=bar) == 38


def test_sell_stop_intrabar_touch_fills_at_stop():
    bar = Bar(open=46, high=47, low=44, close=44.5)
    assert stop_fill_price(StopSide.SELL_STOP, stop_price=45, bar=bar) == 45


def test_sell_stop_not_touched_returns_none():
    bar = Bar(open=50, high=51, low=48, close=49)
    assert stop_fill_price(StopSide.SELL_STOP, stop_price=45, bar=bar) is None


def test_buy_stop_gap_up_fills_at_open_not_stop():
    bar = Bar(open=52, high=53, low=51, close=52)
    assert stop_fill_price(StopSide.BUY_STOP, stop_price=45, bar=bar) == 52


def test_buy_stop_intrabar_touch_fills_at_stop():
    bar = Bar(open=44, high=46, low=43, close=45.5)
    assert stop_fill_price(StopSide.BUY_STOP, stop_price=45, bar=bar) == 45


def test_buy_stop_not_touched_returns_none():
    bar = Bar(open=40, high=42, low=39, close=41)
    assert stop_fill_price(StopSide.BUY_STOP, stop_price=45, bar=bar) is None


def test_sell_stop_open_exactly_at_stop_fills_at_stop():
    bar = Bar(open=45, high=45.5, low=44.8, close=45.2)
    assert stop_fill_price(StopSide.SELL_STOP, stop_price=45, bar=bar) == 45
