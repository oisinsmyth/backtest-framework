"""Unit gates for the per-trade diagnostics (D112).

The golden master already pins the happy path against hand arithmetic. What is left
here is the edge behaviour that decides whether a summary table is honest: an episode
still open at the end of the run, the capture ratios' definitions, and the percentile
convention.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.backtest import BacktestResult
from backtest_framework.research.trade_diagnostics import (
    _percentile,
    extract_episodes,
    summarise,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2021, 1, 1)
SYMBOL = "X"


def bars_from(closes, highs=None, lows=None):
    highs = highs or [c * 1.05 for c in closes]
    lows = lows or [c * 0.95 for c in closes]
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=c, high=h, low=lo, close=c))
        for i, (c, h, lo) in enumerate(zip(closes, highs, lows))
    ]


def result_with(fills):
    out = BacktestResult()
    out.fills = fills
    return out


def test_an_episode_still_open_at_the_end_is_flagged_not_silently_closed():
    bars = bars_from([100, 110, 120, 130])
    result = result_with([(bars[1].timestamp, SYMBOL, 10.0, 110.0, 1.0)])
    episodes = extract_episodes(result, SYMBOL, bars)
    assert len(episodes) == 1
    e = episodes[0]
    assert e.is_open and e.exit_timestamp is None and e.exit_price is None
    # Marked at the final close: bought 10 @110, final close 130 -> +200 before costs.
    assert e.gross_pnl == pytest.approx(200.0)
    assert e.bars_held == 2  # entry at index 1, final bar index 3


def test_open_episodes_are_excluded_from_closed_trade_statistics():
    bars = bars_from([100, 110, 105, 130])
    result = result_with(
        [
            (bars[1].timestamp, SYMBOL, 10.0, 110.0, 1.0),
            (bars[2].timestamp, SYMBOL, -10.0, 105.0, 1.0),
            (bars[3].timestamp, SYMBOL, 10.0, 130.0, 1.0),
        ]
    )
    episodes = extract_episodes(result, SYMBOL, bars)
    summary = summarise(
        episodes,
        equity_curve=[(tb.timestamp, 100_000.0 + i) for i, tb in enumerate(bars)],
        instrument_bars=bars,
        n_oos_bars=len(bars),
    )
    assert summary.n_closed_trades == 1
    assert summary.n_open_at_end == 1
    # The open episode's cost still counts toward the cost totals — money left the
    # book — but not toward win rate or holding-period statistics.
    assert summary.total_costs == pytest.approx(3.0)
    assert summary.mean_bars_held == 1.0


def test_rebalancing_fills_belong_to_their_episode_and_are_not_extra_trades():
    bars = bars_from([100, 100, 100, 100, 100])
    result = result_with(
        [
            (bars[1].timestamp, SYMBOL, 10.0, 100.0, 4.0),
            (bars[2].timestamp, SYMBOL, -1.0, 100.0, 0.4),
            (bars[3].timestamp, SYMBOL, -2.0, 100.0, 0.8),
            (bars[4].timestamp, SYMBOL, -7.0, 100.0, 2.8),
        ]
    )
    episodes = extract_episodes(result, SYMBOL, bars)
    assert len(episodes) == 1
    e = episodes[0]
    assert e.n_fills == 4
    assert e.costs == pytest.approx(8.0)
    assert e.rebalance_costs == pytest.approx(1.2)  # the two interior trims only
    assert e.traded_notional == pytest.approx(2000.0)


def test_excursions_exclude_the_exit_bars_range_after_the_open():
    """The position is closed at the exit bar's OPEN, so that bar's later high and low
    must not be credited or blamed to the trade."""
    bars = bars_from(
        closes=[100, 100, 100],
        highs=[101, 120, 500],   # bar 2's 500 must not appear in MFE
        lows=[99, 80, 1],        # bar 2's 1 must not appear in MAE
    )
    result = result_with(
        [
            (bars[1].timestamp, SYMBOL, 1.0, 100.0, 0.0),
            (bars[2].timestamp, SYMBOL, -1.0, 100.0, 0.0),
        ]
    )
    e = extract_episodes(result, SYMBOL, bars)[0]
    assert e.mfe == pytest.approx(120 / 100 - 1)
    assert e.mae == pytest.approx(80 / 100 - 1)


def test_capture_ratios_are_computed_on_matched_up_and_down_days():
    instrument = bars_from([100, 110, 99, 108])  # +10%, -10%, +9.09%
    equity = [
        (instrument[0].timestamp, 1000.0),
        (instrument[1].timestamp, 1050.0),  # +5% on an instrument up day
        (instrument[2].timestamp, 1029.0),  # -2% on an instrument down day
        (instrument[3].timestamp, 1060.0),
    ]
    summary = summarise([], equity_curve=equity, instrument_bars=instrument, n_oos_bars=4)
    up_instrument = (110 / 100 - 1) + (108 / 99 - 1)
    up_strategy = (1050 / 1000 - 1) + (1060 / 1029 - 1)
    assert summary.upside_capture == pytest.approx(up_strategy / up_instrument)
    assert summary.downside_participation == pytest.approx((1029 / 1050 - 1) / (99 / 110 - 1))
    assert summary.downside_avoided == pytest.approx(1 - summary.downside_participation)


def test_mismatched_lengths_are_refused_rather_than_silently_subset():
    bars = bars_from([100, 101, 102])
    with pytest.raises(ValueError, match="compare different samples"):
        summarise([], equity_curve=[(bars[0].timestamp, 1.0)], instrument_bars=bars, n_oos_bars=3)


def test_empty_statistics_are_nan_not_zero():
    """Zero would read as "no adverse excursion"; NaN reads as "no trades". The
    difference matters in a table a reviewer is scanning."""
    bars = bars_from([100, 101, 102])
    summary = summarise(
        [], equity_curve=[(tb.timestamp, 1000.0) for tb in bars], instrument_bars=bars, n_oos_bars=3
    )
    assert summary.n_closed_trades == 0
    assert math.isnan(summary.mean_mae)
    assert math.isnan(summary.win_rate)
    assert summary.total_costs == 0.0


def test_percentile_uses_the_nearest_rank_convention():
    assert _percentile([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0.90) == 9.0
    assert _percentile([5], 0.90) == 5.0
    assert math.isnan(_percentile([], 0.90))


def test_metrics_dict_is_all_floats_for_the_registry():
    bars = bars_from([100, 110, 105])
    result = result_with(
        [
            (bars[1].timestamp, SYMBOL, 10.0, 110.0, 1.0),
            (bars[2].timestamp, SYMBOL, -10.0, 105.0, 1.0),
        ]
    )
    summary = summarise(
        extract_episodes(result, SYMBOL, bars),
        equity_curve=[(tb.timestamp, 1000.0 + i) for i, tb in enumerate(bars)],
        instrument_bars=bars,
        n_oos_bars=3,
    )
    metrics = summary.to_metrics()
    assert all(isinstance(v, float) for v in metrics.values())
    assert "whipsaw_rate" in metrics and "cost_share_of_gross" in metrics
