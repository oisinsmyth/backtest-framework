"""Property-based invariants for the z-score pairs strategy and its cost stack
(D40, D78, D69, D122-D124).

The headline is the no-look-ahead property, mirroring
`tests/property/test_breakout_invariants.py`: across randomised price paths, perturbing
bars AFTER the decision bar — arbitrarily, including by orders of magnitude — must not
change a single target the strategy produced up to and including that bar. That is the
one failure that would silently invalidate every number in
`docs/results/crypto_pairs_btc_eth.md`, and an example-based test cannot cover the shapes
that would trigger it.

The rest pin the properties a PAIRS book has and a long-flat one does not: the two legs
are always exactly opposite (market neutrality by construction, before any realised-beta
measurement), borrow is charged on shorts only whichever leg happens to be short, and the
fee bill is exactly the rate times the traded notional on BOTH legs.

Conventions (D78): hypothesis with `derandomize=True`, so hypothesis owns the seeding
rather than a hand-rolled seed parameter. **It does NOT mean the same examples every run**
— since 6.156.6 hypothesis harvests its constant pool from `sys.modules` at test time, so a
full-suite run and a single-file run draw differently from the same seed (D537). A failure
here must be reproduced with the WHOLE suite before it is called a flake.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings, strategies as st

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import build_data_view
from backtest_framework.instruments.equity import Equity
from backtest_framework.research.breakout_study import CostTier
from backtest_framework.research.crypto_pairs_study import (
    build_pair_cost_stack,
    pair_cost_stack_config,
)
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)
TOLERANCE = 1e-9  # D47
EPOCH = datetime(2020, 1, 1)
INSTRUMENTS = {
    "AAA": Equity(symbol="AAA", quantity_precision=8),
    "BBB": Equity(symbol="BBB", quantity_precision=8),
}
PARAMS = [(20, 1.5, 0.5), (30, 2.0, 0.5), (60, 2.0, 0.5), (60, 2.5, 0.5), (90, 2.5, 0.5)]


@st.composite
def pair_paths(draw, min_bars=70, max_bars=200):
    """Two positively-correlated price paths, so the log spread is a plausible pairs
    spread rather than the difference of two unrelated walks."""
    n = draw(st.integers(min_bars, max_bars))
    common = draw(st.lists(st.floats(-0.08, 0.08, allow_nan=False), min_size=n, max_size=n))
    idio_a = draw(st.lists(st.floats(-0.05, 0.05, allow_nan=False), min_size=n, max_size=n))
    idio_b = draw(st.lists(st.floats(-0.05, 0.05, allow_nan=False), min_size=n, max_size=n))
    bars_a, bars_b, pa, pb = [], [], 100.0, 100.0
    for c, ia, ib in zip(common, idio_a, idio_b):
        pa = max(pa * (1.0 + c + ia), 1.0)
        pb = max(pb * (1.0 + c + ib), 1.0)
        bars_a.append(Bar(open=pa * 0.999, high=pa * 1.02, low=pa * 0.98, close=pa))
        bars_b.append(Bar(open=pb * 0.999, high=pb * 1.02, low=pb * 0.98, close=pb))
    return bars_a, bars_b


def _make(lookback: int, entry_z: float, exit_z: float, leg_weight: float = 1.0):
    return ZScorePairsStrategy(
        strategy_id="s",
        instrument_a="AAA",
        instrument_b="BBB",
        lookback=lookback,
        entry_z=entry_z,
        exit_z=exit_z,
        leg_weight=leg_weight,
    )


def _replay(strategy, bars_a, bars_b, up_to: int) -> list[tuple[float, float]]:
    out = []
    for i in range(up_to + 1):
        targets = strategy.generate_targets(
            {
                "AAA": build_data_view(tuple(bars_a), i),
                "BBB": build_data_view(tuple(bars_b), i),
            }
        )
        out.append((targets[0].weight, targets[1].weight))
    return out


def _timestamped(bars):
    return [TimestampedBar(EPOCH + timedelta(days=i), bar) for i, bar in enumerate(bars)]


def _scaled(bars, scale):
    return [
        Bar(open=b.open * scale, high=b.high * scale, low=b.low * scale, close=b.close * scale)
        for b in bars
    ]


def _run(bars_a, bars_b, strategy, fee_bps=40.0, borrow=0.10, margin=0.10, cash=100_000.0):
    return run_backtest(
        bars_by_instrument={"AAA": _timestamped(bars_a), "BBB": _timestamped(bars_b)},
        instruments=INSTRUMENTS,
        strategies=[strategy],
        cost_stack=build_pair_cost_stack(
            pair_cost_stack_config(CostTier("t", fee_bps, "taker"), borrow, margin)
        ),
        allocator=ConstantSplitAllocator(),
        starting_cash=cash,
        fill_timing="next_open",
    )


# ------------------------------------------------------------------- no look-ahead


@SETTINGS
@given(paths=pair_paths(), tail=pair_paths(min_bars=1, max_bars=40), scale=st.floats(0.01, 100.0))
def test_perturbing_future_bars_cannot_change_todays_signal(paths, tail, scale):
    """The property the whole study rests on. Replay to bar i on the original series,
    then replay to bar i on a series whose bars after i have been replaced by arbitrary,
    wildly-scaled ones. The two target sequences must be identical.

    A pairs signal has two places a leak could hide that a single-instrument signal does
    not: the spread reads BOTH legs, and the z-window is built from a range expression
    whose upper bound is easy to get wrong by one. Perturbing both legs covers both."""
    bars_a, bars_b = paths
    tail_a, tail_b = tail
    split = len(bars_a) // 2
    perturbed_a = list(bars_a[: split + 1]) + _scaled(tail_a, scale)
    perturbed_b = list(bars_b[: split + 1]) + _scaled(tail_b, scale)
    original = _replay(_make(*PARAMS[1]), bars_a, bars_b, split)
    replayed = _replay(_make(*PARAMS[1]), perturbed_a, perturbed_b, split)
    assert original == replayed


@SETTINGS
@given(paths=pair_paths(min_bars=90), scale=st.floats(0.01, 100.0))
def test_engine_equity_curve_is_unchanged_by_future_bars(paths, scale):
    """Same property one level up: through the real engine, with fees, borrow, margin
    interest and next-open fills, the equity curve up to the decision bar cannot move
    when later bars change. Catches a leak anywhere in strategy -> sizing -> fills ->
    carry, not only in the signal."""
    bars_a, bars_b = paths
    split = len(bars_a) - 20
    perturbed_a = list(bars_a[:split]) + _scaled(bars_a[split:], scale)
    perturbed_b = list(bars_b[:split]) + _scaled(bars_b[split:], scale)

    a = _run(bars_a, bars_b, _make(*PARAMS[1]))
    b = _run(perturbed_a, perturbed_b, _make(*PARAMS[1]))
    # Decisions on bar split-1 fill at bar split's OPEN, which is already perturbed —
    # so equality is asserted up to and including bar split-1's close.
    for (ts_a, nav_a), (ts_b, nav_b) in zip(a.equity_curve[:split], b.equity_curve[:split]):
        assert ts_a == ts_b
        assert nav_a == pytest.approx(nav_b, abs=TOLERANCE)


@SETTINGS
@given(paths=pair_paths())
def test_replay_is_deterministic(paths):
    bars_a, bars_b = paths
    last = len(bars_a) - 1
    assert _replay(_make(*PARAMS[1]), bars_a, bars_b, last) == _replay(
        _make(*PARAMS[1]), bars_a, bars_b, last
    )


# -------------------------------------------------------- market neutrality by design


@SETTINGS
@given(paths=pair_paths(), params=st.sampled_from(PARAMS), lw=st.sampled_from([0.25, 0.5, 1.0]))
def test_the_two_legs_are_always_exactly_opposite(paths, params, lw):
    """Neutrality *by construction*, which is a different claim from the realised-beta
    number the artifact reports. If this ever failed, that number would be measuring a
    bug rather than a design property."""
    bars_a, bars_b = paths
    weights = _replay(_make(*params, leg_weight=lw), bars_a, bars_b, len(bars_a) - 1)
    for weight_a, weight_b in weights:
        assert weight_a == -weight_b
        assert weight_a in (-lw, 0.0, lw)


@SETTINGS
@given(paths=pair_paths(), params=st.sampled_from(PARAMS))
def test_the_strategy_stands_aside_until_it_has_a_full_window(paths, params):
    """D44's rule, enforced structurally by the strategy's own guard: with fewer than
    lookback+1 visible bars there is no window ending at the PREVIOUS bar, so there must
    be no position. This is what makes a warm-up prefix of exactly `lookback` bars
    provably flat, which is what the study's leak check relies on (D123)."""
    bars_a, bars_b = paths
    lookback = params[0]
    weights = _replay(_make(*params), bars_a, bars_b, len(bars_a) - 1)
    assert all(w == (0.0, 0.0) for w in weights[:lookback])


@SETTINGS
@given(paths=pair_paths(), params=st.sampled_from(PARAMS))
def test_every_state_change_is_justified_by_its_own_threshold(paths, params):
    """The hysteresis band, stated exactly: a side may only be entered on a bar whose
    |z| exceeded entry_z in the right direction, and may only be left for flat on a bar
    whose |z| fell below exit_z. Anything else is chatter inside the band, which is the
    one thing the band exists to prevent."""
    import math
    import statistics

    lookback, entry_z, exit_z = params
    bars_a, bars_b = paths
    weights = _replay(_make(*params), bars_a, bars_b, len(bars_a) - 1)

    def z_at(index: int) -> float | None:
        if index < lookback:
            return None
        spreads = [
            math.log(bars_a[i].close) - math.log(bars_b[i].close)
            for i in range(index - lookback, index)
        ]
        std = statistics.stdev(spreads)
        if std == 0.0:
            return None
        current = math.log(bars_a[index].close) - math.log(bars_b[index].close)
        return (current - statistics.fmean(spreads)) / std

    for i in range(1, len(weights)):
        previous, current = weights[i - 1][0], weights[i][0]
        if previous == current:
            continue
        z = z_at(i)
        if z is None:
            assert current == 0.0  # degenerate window -> stand aside
            continue
        if current > 0:
            assert z < -entry_z
        elif current < 0:
            assert z > entry_z
        else:
            assert abs(z) < exit_z


# ------------------------------------------------------------------ cost application


@SETTINGS
@given(paths=pair_paths(min_bars=90), bps=st.sampled_from([0.0, 10.0, 25.0, 40.0]))
def test_trade_costs_are_exactly_the_fee_rate_times_traded_notional_on_both_legs(paths, bps):
    """Cost application asserted against arithmetic rather than against another run. The
    pairs-specific half is `both legs`: a bug that charged only the leg that happened to
    be first in the netting dict would halve the study's entire fee bill."""
    bars_a, bars_b = paths
    result = _run(bars_a, bars_b, _make(*PARAMS[1]), fee_bps=bps, borrow=0.0, margin=0.0)
    for _ts, _instrument, quantity, price, cost in result.fills:
        assert cost == pytest.approx(abs(quantity * price) * bps / 10_000.0, rel=1e-12)
    legs = {instrument for _ts, instrument, *_ in result.fills}
    if result.fills:
        assert legs == {"AAA", "BBB"} or len(result.fills) < 2
    if bps == 0.0:
        assert all(cost == 0.0 for *_, cost in result.fills)


@SETTINGS
@given(paths=pair_paths(min_bars=90))
def test_a_zero_rate_carry_stack_charges_nothing_at_all(paths):
    """The control that makes the borrow sensitivity readable: with both carry rates at
    zero, a run must be identical to one with no carry bricks at all. If it is not, some
    brick is charging on a base it should not see."""
    from backtest_framework.costs.stack import CostStack
    from backtest_framework.costs.bricks import PercentOfNotionalSpread

    bars_a, bars_b = paths
    with_zero_rates = _run(bars_a, bars_b, _make(*PARAMS[1]), borrow=0.0, margin=0.0)
    bare = run_backtest(
        bars_by_instrument={"AAA": _timestamped(bars_a), "BBB": _timestamped(bars_b)},
        instruments=INSTRUMENTS,
        strategies=[_make(*PARAMS[1])],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=40.0),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )
    assert with_zero_rates.final_nav == pytest.approx(bare.final_nav, abs=TOLERANCE)


@SETTINGS
@given(paths=pair_paths(min_bars=90), rate=st.sampled_from([0.05, 0.10, 0.25]))
def test_borrow_is_charged_on_whichever_leg_is_short(paths, rate):
    """Charged per leg on that leg's own SIGNED notional (D71), so which instrument pays
    flips with the sign of z. Asserted through the brick against the position the engine
    actually held, because "shorts only" is the property that makes the borrow
    assumption meaningful — a brick that charged both legs would double the carry and
    would look like a rate choice rather than a bug."""
    from backtest_framework.costs.equity_bricks import BorrowFee

    brick = BorrowFee(annual_rate=rate)
    day = (EPOCH, EPOCH + timedelta(days=1))
    assert brick.cost(-100_000.0, *day) == pytest.approx(100_000.0 * rate / 365.0, rel=1e-12)
    assert brick.cost(+100_000.0, *day) == 0.0

    bars_a, bars_b = paths
    result = _run(bars_a, bars_b, _make(*PARAMS[1]), borrow=rate)
    position_a = 0.0
    for _ts, instrument, quantity, _price, _cost in result.fills:
        if instrument == "AAA":
            position_a += quantity
    # Whatever the final sign, exactly one leg is short whenever the book is not flat.
    if abs(position_a) > 1e-9:
        position_b = sum(q for _ts, i, q, *_ in result.fills if i == "BBB")
        assert (position_a > 0) != (position_b > 0)
