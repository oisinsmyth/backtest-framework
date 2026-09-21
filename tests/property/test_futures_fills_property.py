"""Invariants of the shared futures fill model (D587), over random sessions and instruments.

Gate P. The unit and golden files pin the fill model at chosen inputs; the failures feared
here have a SHAPE that no finite set of examples covers — "some price comes back between
ticks", "some bar lets a target through when the stop was also inside". Those quantify over
the path and the instrument, which is what this tier is for (CONTRIBUTING.md, and the
statement of the distinction in `tests/property/test_macd_invariants.py`).

**D78 conventions, amended by D537.** `SETTINGS` is module-level with `derandomize=True`,
40 examples and no deadline. D537 is the reason `derandomize` is not claimed to give
byte-determinism: since hypothesis 6.156.6 the constant pool fed into generation is
harvested from `sys.modules` at test time, so a full-suite run and a single-file run draw
DIFFERENT values from the same seed. A failure here that does not reproduce when the file
is run alone is therefore not a flake — reproduce it with the whole suite.

**Tie-heavy by construction.** `spread` is drawn from {2, 8, 200} ticks, and at 2 a
four-price bar collides constantly: equal high and low, stop exactly on the low, limit
exactly on the close. Ties are where two conventions that agree everywhere else disagree,
so a generator that never produces them tests the easy half of every rule.
"""

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest_framework.instruments.future import Future
from backtest_framework.simulator.futures_fills import (
    ExitKind,
    FillAssumption,
    SessionOHLC,
    Side,
    adverse_price,
    bar_at,
    entry_fill,
    passive_limit,
    resolve_exit,
    running_peak_drawdown,
    stress_fill,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

INSTRUMENTS = [Future.from_specs(r) for r in ("MES", "ES", "NQ", "CL", "GC", "ZN", "YM")]
SIDES = st.sampled_from([Side.LONG, Side.SHORT])
RULES = st.sampled_from(list(FillAssumption))


@st.composite
def sessions(draw, min_bars: int = 3, max_bars: int = 14):
    """A session of grid-aligned bars on a randomly chosen contract.

    Prices are INTEGER MULTIPLES OF THE TICK by construction — `m * tick_points` — which is
    the only way to generate a valid futures price without asserting the very grid rule the
    tests are checking.
    """
    fut = draw(st.sampled_from(INSTRUMENTS))
    n = draw(st.integers(min_value=min_bars, max_value=max_bars))
    base = draw(st.integers(min_value=2_000, max_value=40_000))
    spread = draw(st.sampled_from([2, 8, 200]))
    o, h, lo, c = [], [], [], []
    for _ in range(n):
        ks = sorted(draw(st.lists(st.integers(min_value=-spread, max_value=spread), min_size=4, max_size=4)))
        lo.append((base + ks[0]) * fut.tick_points)
        o.append((base + ks[1]) * fut.tick_points)
        c.append((base + ks[2]) * fut.tick_points)
        h.append((base + ks[3]) * fut.tick_points)
    ohlc = SessionOHLC(np.array(o), np.array(h), np.array(lo), np.array(c))
    return fut, ohlc


@st.composite
def sessions_with_t0(draw, min_bars: int = 3, max_bars: int = 14):
    fut, ohlc = draw(sessions(min_bars=min_bars, max_bars=max_bars))
    n = ohlc.close.size
    t0 = draw(st.integers(min_value=0, max_value=n - 2))
    return fut, ohlc, t0


# ----------------------------------------------------------- every price is tradeable


@given(data=sessions_with_t0(), side=SIDES, ticks=st.integers(min_value=0, max_value=4), rule=RULES)
@SETTINGS
def test_every_price_the_model_returns_sits_on_the_tick_grid(data, side, ticks, rule):
    fut, ohlc, t0 = data
    n = ohlc.close.size
    fut.assert_on_grid(entry_fill(ohlc.close, t0, side, fut, ticks).price)
    fut.assert_on_grid(entry_fill(ohlc.close, t0, side, fut, ticks, at="open", open=ohlc.open).price)
    fut.assert_on_grid(stress_fill(ohlc.close, t0, side, fut, k=n - 1 - t0, ticks_adverse=ticks).price)
    passive = passive_limit(
        ohlc.open, ohlc.high, ohlc.low, ohlc.close, t0, side, fut, n - 1 - t0, rule
    )
    if passive.filled:
        fut.assert_on_grid(passive.price)


@given(data=sessions(), side=SIDES, rule=RULES, which=st.integers(0, 3), frac=st.integers(0, 8))
@SETTINGS
def test_resolve_exit_returns_a_price_on_the_grid(data, side, rule, which, frac):
    fut, ohlc = data
    j = which % ohlc.close.size
    bar = bar_at(ohlc, j)
    span = round((bar.high - bar.low) / fut.tick_points)
    stop_level = fut.round_to_tick(bar.low + (span * frac / 8) * fut.tick_points, "nearest")
    target_level = fut.round_to_tick(bar.high - (span * frac / 8) * fut.tick_points, "nearest")
    if side is Side.SHORT:
        stop_level, target_level = target_level, stop_level
    r = resolve_exit(bar, stop_level, target_level, side, fut, stop_rule=rule, target_rule=rule)
    if r.price is not None:
        fut.assert_on_grid(r.price)
    assert (r.price is None) == (r.kind is ExitKind.NONE)


# ------------------------------------------------------------- the concession's sign


@given(data=sessions_with_t0(), side=SIDES, ticks=st.integers(min_value=0, max_value=6))
@SETTINGS
def test_entry_fill_is_never_better_than_the_anchor_close(data, side, ticks):
    fut, ohlc, t0 = data
    anchor = float(ohlc.close[t0 + 1])
    price = entry_fill(ohlc.close, t0, side, fut, ticks).price
    if side is Side.LONG:
        assert price >= anchor
    else:
        assert price <= anchor
    assert abs(fut.ticks(abs(price - anchor)) - ticks) < 1e-6
    assert entry_fill(ohlc.close, t0, side, fut, 0).price == anchor


@given(data=sessions_with_t0(), side=SIDES, ticks=st.integers(min_value=0, max_value=6))
@SETTINGS
def test_stress_fill_is_never_better_than_the_primary_fill(data, side, ticks):
    fut, ohlc, t0 = data
    k = ohlc.close.size - 1 - t0
    primary = entry_fill(ohlc.close, t0, side, fut, ticks)
    stressed = stress_fill(ohlc.close, t0, side, fut, k=k, ticks_adverse=ticks)
    if side is Side.LONG:
        assert stressed.price >= primary.price
    else:
        assert stressed.price <= primary.price
    assert stress_fill(ohlc.close, t0, side, fut, k=1, ticks_adverse=ticks) == primary


@given(price=st.integers(2_000, 40_000), side=SIDES, a=st.integers(0, 20), b=st.integers(0, 20),
       fut=st.sampled_from(INSTRUMENTS), closing=st.booleans())
@SETTINGS
def test_adverse_price_is_monotone_in_the_concession(price, side, a, b, fut, closing):
    px = price * fut.tick_points
    lo_t, hi_t = (a, b) if a <= b else (b, a)
    near = adverse_price(px, side, lo_t, fut, closing=closing)
    far = adverse_price(px, side, hi_t, fut, closing=closing)
    worse_is_up = (side is Side.LONG) != closing
    assert (far >= near) if worse_is_up else (far <= near)
    assert adverse_price(px, side, 0, fut, closing=closing) == px


# ----------------------------------------------------------------- the pessimism rule


@given(data=sessions(), side=SIDES, stop_rule=RULES, target_rule=RULES,
       which=st.integers(0, 3), s=st.integers(0, 8), t=st.integers(0, 8))
@SETTINGS
def test_a_target_is_never_returned_from_a_bar_whose_stop_was_also_reached(
    data, side, stop_rule, target_rule, which, s, t
):
    """All three deposit documents' intra-bar rule, quantified over bars and instruments."""
    fut, ohlc = data
    bar = bar_at(ohlc, which % ohlc.close.size)
    span = (bar.high - bar.low) / fut.tick_points
    a = fut.round_to_tick(bar.low + (span * s / 8) * fut.tick_points, "nearest")
    b = fut.round_to_tick(bar.low + (span * t / 8) * fut.tick_points, "nearest")
    stop_level, target_level = (a, b) if side is Side.LONG else (b, a)

    if side is Side.LONG:
        reach = stop_level if stop_rule is FillAssumption.TOUCH else stop_level - fut.tick_points
        stop_reached = bar.low <= reach
    else:
        reach = stop_level if stop_rule is FillAssumption.TOUCH else stop_level + fut.tick_points
        stop_reached = bar.high >= reach

    r = resolve_exit(bar, stop_level, target_level, side, fut,
                     stop_rule=stop_rule, target_rule=target_rule)
    if stop_reached:
        assert r.kind is ExitKind.STOP
    else:
        assert r.kind is not ExitKind.STOP


@given(data=sessions(), side=SIDES, which=st.integers(0, 3), s=st.integers(0, 8))
@SETTINGS
def test_a_stop_fill_is_never_better_than_the_stop_level(data, side, which, s):
    """The gap rule (D10) may only make the fill WORSE. Free money is the bug it exists to kill."""
    fut, ohlc = data
    bar = bar_at(ohlc, which % ohlc.close.size)
    span = (bar.high - bar.low) / fut.tick_points
    stop_level = fut.round_to_tick(bar.low + (span * s / 8) * fut.tick_points, "nearest")
    r = resolve_exit(bar, stop_level, None, side, fut)
    if r.kind is ExitKind.STOP:
        assert (r.price <= stop_level) if side is Side.LONG else (r.price >= stop_level)
        assert r.gapped == (r.price != stop_level or bar.open == stop_level)


# ------------------------------------------------------------------- passive orders


@given(data=sessions_with_t0(), side=SIDES)
@SETTINGS
def test_trade_through_is_strictly_more_demanding_than_touch(data, side):
    fut, ohlc, t0 = data
    k = ohlc.close.size - 1 - t0
    args = (ohlc.open, ohlc.high, ohlc.low, ohlc.close, t0, side, fut, k)
    touch = passive_limit(*args, FillAssumption.TOUCH)
    through = passive_limit(*args, FillAssumption.TRADE_THROUGH)
    if through.filled:
        assert touch.filled, "a bar that traded through the limit necessarily reached it"
        assert touch.bar <= through.bar
    if touch.filled and through.filled:
        assert touch.price == through.price == float(ohlc.close[t0])


@given(data=sessions_with_t0(), side=SIDES, noise=st.integers(-50, 50).filter(lambda k: k != 0))
@SETTINGS
def test_a_fill_does_not_depend_on_bars_after_the_one_it_filled_on(data, side, noise):
    """The look-ahead shape: perturbing bars AFTER the decision must change nothing before it.

    `noise` is never 0 — a perturbation that perturbs nothing would make this pass on an
    implementation that reads the whole session.
    """
    fut, ohlc, t0 = data
    primary = entry_fill(ohlc.close, t0, side, fut)
    stressed = stress_fill(ohlc.close, t0, side, fut, k=1)
    moved = SessionOHLC(
        ohlc.open.copy(), ohlc.high.copy(), ohlc.low.copy(), ohlc.close.copy()
    )
    for arr in (moved.open, moved.high, moved.low, moved.close):
        arr[t0 + 2 :] += noise * fut.tick_points
    assert not np.array_equal(moved.close, ohlc.close) or t0 + 2 >= ohlc.close.size
    assert entry_fill(moved.close, t0, side, fut) == primary
    assert stress_fill(moved.close, t0, side, fut, k=1) == stressed


# ---------------------------------------------------------- running-peak drawdown


@given(data=sessions(), side=SIDES)
@SETTINGS
def test_running_peak_drawdown_dominates_every_single_bar_range(data, side):
    fut, ohlc = data
    dd = running_peak_drawdown(ohlc.high, ohlc.low, side, fut)
    assert dd >= 0.0
    assert dd >= float(np.max(ohlc.high - ohlc.low)) - 1e-9
    prefix = running_peak_drawdown(ohlc.high[:-1], ohlc.low[:-1], side, fut) if ohlc.high.size > 1 else 0.0
    assert dd >= prefix - 1e-9, "a longer path can only deepen the worst drawdown"


# ------------------------------------------------------------------- the tick grid


@given(fut=st.sampled_from(INSTRUMENTS), m=st.integers(-40_000, 40_000), frac=st.floats(0, 1))
@SETTINGS
def test_round_to_tick_brackets_and_is_idempotent(fut, m, frac):
    price = (m + frac) * fut.tick_points
    down = fut.round_to_tick(price, "down")
    nearest = fut.round_to_tick(price, "nearest")
    up = fut.round_to_tick(price, "up")
    assert down <= nearest <= up
    assert up - down <= fut.tick_points * (1 + 1e-9)
    for p in (down, nearest, up):
        fut.assert_on_grid(p)
        for direction in ("down", "nearest", "up"):
            assert fut.round_to_tick(p, direction) == p
