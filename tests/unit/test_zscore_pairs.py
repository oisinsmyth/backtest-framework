"""Unit tests for ZScorePairsStrategy, on constructed series.

The spread is ln(A) − ln(B). B is fixed at 100.0, so the spread is ln(A/100) and z is
controlled entirely by A's price path. A steady oscillation keeps the rolling std defined
and nonzero; the final bar's price then sets z where each scenario needs it.
"""

import pytest

from backtest_framework.engine.dataview import build_data_view
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy


def _views(prices_a: list[float], prices_b: list[float]):
    bars_a = tuple(Bar(open=p, high=p, low=p, close=p) for p in prices_a)
    bars_b = tuple(Bar(open=p, high=p, low=p, close=p) for p in prices_b)
    i = len(bars_a) - 1
    return {"A": build_data_view(bars_a, i), "B": build_data_view(bars_b, i)}


def _strategy(**overrides):
    defaults = dict(
        strategy_id="s", instrument_a="A", instrument_b="B", lookback=10, entry_z=2.0, exit_z=0.5, leg_weight=1.0
    )
    return ZScorePairsStrategy(**{**defaults, **overrides})


def _weights(targets):
    return {t.instrument_id: t.weight for t in targets}


def _oscillation(n: int) -> list[float]:
    """A prices alternating 99/101 around 100: nonzero spread std, mean near zero."""
    return [99.0 if i % 2 == 0 else 101.0 for i in range(n)]


def test_flat_during_warmup():
    strategy = _strategy()
    # lookback=10 needs 11 visible bars; with 10 it is still warming up.
    views = _views(_oscillation(10), [100.0] * 10)
    assert _weights(strategy.generate_targets(views)) == {"A": 0.0, "B": 0.0}


def test_enters_short_spread_when_z_breaches_entry():
    strategy = _strategy()
    # 11 bars: 10-bar oscillating window (std ~ ln(1.01ish)), final bar A=120 -> huge +z.
    prices_a = _oscillation(10) + [120.0]
    views = _views(prices_a, [100.0] * 11)
    weights = _weights(strategy.generate_targets(views))
    assert weights == {"A": -1.0, "B": 1.0}  # spread rich: short A, long B


def test_enters_long_spread_on_negative_breach():
    strategy = _strategy()
    prices_a = _oscillation(10) + [80.0]  # huge -z
    views = _views(prices_a, [100.0] * 11)
    weights = _weights(strategy.generate_targets(views))
    assert weights == {"A": 1.0, "B": -1.0}


def test_holds_side_inside_hysteresis_band():
    strategy = _strategy()
    # Bar 11: breach -> short spread.
    views = _views(_oscillation(10) + [120.0], [100.0] * 11)
    strategy.generate_targets(views)
    assert strategy._side == -1

    # Next bar: A at a level where |z| sits between exit (0.5) and entry (2.0).
    # The window now includes the 120 print (mean 0.0192, std 0.0582, computed directly);
    # A=108 gives z=+0.99, inside the band.
    views2 = _views(_oscillation(10) + [120.0, 108.0], [100.0] * 12)
    weights = _weights(strategy.generate_targets(views2))
    assert weights == {"A": -1.0, "B": 1.0}  # held, not exited


def test_exits_when_z_returns_inside_exit_threshold():
    strategy = _strategy()
    views = _views(_oscillation(10) + [120.0], [100.0] * 11)
    strategy.generate_targets(views)

    # A back to 100 -> spread ~0, z near the (small) window mean -> |z| < 0.5 -> flat.
    views2 = _views(_oscillation(10) + [120.0, 100.0], [100.0] * 12)
    weights = _weights(strategy.generate_targets(views2))
    assert weights == {"A": 0.0, "B": 0.0}
    assert strategy._side == 0


def test_zero_std_window_stands_aside():
    strategy = _strategy()
    # Constant prices -> every spread identical -> std 0 -> flat, no ZeroDivisionError.
    views = _views([100.0] * 12, [100.0] * 12)
    assert _weights(strategy.generate_targets(views)) == {"A": 0.0, "B": 0.0}


def test_standing_aside_on_a_degenerate_window_clears_the_side_it_stood_aside_from():
    """Emitting flat targets on a degenerate window resets `_side` to 0.

    The previous test starts with `_side` already 0, so this one starts in a trade.

    If `_side` were left at ±1, the engine would close the position and pay a round trip;
    on the next bar `std > 0` again and `|z|` falls in the hysteresis band, so no branch
    fires, the stale side is re-emitted, and the book re-enters. That is a second round trip
    on a bar with no entry crossing.
    """
    strategy = _strategy(lookback=3, entry_z=2.0, exit_z=0.5)
    strategy._side = -1  # the state a live entry leaves behind

    flat = _weights(strategy.generate_targets(_views([100.0] * 12, [100.0] * 12)))

    assert flat == {"A": 0.0, "B": 0.0}, "a degenerate window must stand aside"
    assert strategy._side == 0, (
        "the strategy emitted flat targets but _side is still nonzero; the next "
        "in-band bar will re-emit it and re-enter with no entry crossing"
    )


def test_invalid_thresholds_rejected_at_construction():
    with pytest.raises(ValueError, match="exit_z"):
        _strategy(entry_z=1.0, exit_z=1.0)
    with pytest.raises(ValueError, match="lookback"):
        _strategy(lookback=1)
