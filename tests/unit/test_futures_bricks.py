"""Unit and property gates for the futures cost bricks (D591).

`tests/golden/test_futures_costs_ledger.py` pins the published dollars; this file pins the
BEHAVIOUR that produces them — that the charge is per fill and per contract, that a futures
brick refuses an instrument with no tick, that `round_trip_usd` refuses to invent a price,
and that a stack over the bricks and the helper agree for every input rather than at the four
points a golden test names.

VERIFICATION_SCHEME.md Step 3 (the CostStack seam) and D48 (no false affordances) are the
gates here. The property at the foot is the one that matters: the golden ledger and the
helper are two routes to the same number, and a golden test only ever checks the routes at
the places someone thought to look.

Conventions (D78): hypothesis with `derandomize=True`, which fixes hypothesis's seed and NOT
the values it draws (D537) — a failure here is reproduced with the whole suite before it is
called a flake.
"""

import math
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest_framework.costs.futures_bricks import (
    FuturesCommission,
    FuturesCostError,
    FuturesRoundTrip,
    TickCrossing,
    build_trade_bricks,
    crossing_lines_for,
    line_names,
    load_cost_table,
    round_trip_usd,
    table_roots,
)
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.future import Future

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
ES = Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=12.50)
ZN = Future(root="ZN", tick_points=0.015625, usd_per_point=1000.0, tick_usd=15.625)
XLE = Equity(symbol="XLE")


# ------------------------------------------------------------------ the two rules


def test_commission_charges_half_a_round_trip_on_each_fill():
    brick = FuturesCommission(3.00)
    assert brick.cost(MES, 1.0, 5000.0) == 1.50
    assert brick.cost(MES, -1.0, 5000.0) == 1.50
    assert brick.cost(MES, 1.0, 5000.0) + brick.cost(MES, -1.0, 5000.0) == 3.00


def test_commission_is_per_contract_and_that_is_what_binds_at_micro_size():
    """$3 is 2.4 MES ticks and 0.24 ES ticks — the same fee, an order of magnitude apart."""
    brick = FuturesCommission(3.00)
    assert brick.cost(MES, 4.0, 5000.0) == 4.0 * 1.50
    assert round_trip_usd(MES, (brick,)) / MES.tick_usd == 2.4
    assert round_trip_usd(ES, (brick,)) / ES.tick_usd == 0.24


def test_commission_ignores_the_price_entirely():
    brick = FuturesCommission(6.00)
    assert brick.cost(ZN, 1.0, 95.0) == brick.cost(ZN, 1.0, 130.0) == 3.00


def test_crossing_charges_half_a_tick_a_side_for_a_one_tick_round_trip():
    brick = TickCrossing(1.0)
    assert brick.cost(MES, 1.0, 5000.0) == 0.625
    assert round_trip_usd(MES, (brick,)) == 1.25


def test_crossing_prices_the_same_tick_count_off_each_contracts_own_tick():
    """The ratio IS the micro argument: one tick is $12.50 on ES and $1.25 on MES.

    Exact on a dyadic tick count, and only to a relative 1e-15 on D465's measured one: 12.5
    and 1.25 are ten apart exactly, but `x*12.5` and `x*1.25` round independently, so the
    ratio of the two products is 10.000000000000002 for this x. That is a property of the
    double, not of the brick — which is why the golden ledger compares each contract against
    its OWN published bar rather than against the other contract's scaled by ten.
    """
    assert round_trip_usd(ES, (TickCrossing(1.0),)) / round_trip_usd(MES, (TickCrossing(1.0),)) == 10.0
    measured = TickCrossing(1.0085687251930602)
    assert round_trip_usd(ES, (measured,)) / round_trip_usd(MES, (measured,)) == pytest.approx(
        10.0, rel=1e-15
    )


def test_crossing_scales_with_quantity_and_not_with_price():
    brick = TickCrossing(2.0)
    assert brick.cost(ZN, 3.0, 110.0) == 3.0 * 15.625
    assert brick.cost(ZN, 3.0, 110.0) == brick.cost(ZN, 3.0, 132.5)


@pytest.mark.parametrize("quantity", [0.0, -0.0])
def test_a_zero_quantity_fill_costs_nothing(quantity):
    assert FuturesCommission(3.0).cost(MES, quantity, 5000.0) == 0.0
    assert TickCrossing(1.0).cost(MES, quantity, 5000.0) == 0.0


def test_both_bricks_charge_a_short_exactly_what_they_charge_a_long():
    """Sign audit, in money: cost is a cost on both sides and never a rebate on one."""
    for brick in (FuturesCommission(4.25), TickCrossing(1.7)):
        assert brick.cost(ES, -7.0, 5000.0) == brick.cost(ES, 7.0, 5000.0) > 0.0


# ------------------------------------------------------------------ the door guards


@pytest.mark.parametrize("brick", [FuturesCommission(3.0), TickCrossing(1.0)])
def test_a_futures_brick_refuses_an_equity(brick):
    """D48: charging a per-contract fee on a share would be a number, not an answer."""
    with pytest.raises(TypeError, match="needs a Future"):
        brick.cost(XLE, 100.0, 50.0)


@pytest.mark.parametrize("brick", [FuturesCommission(3.0), TickCrossing(1.0)])
def test_a_futures_brick_refuses_anything_without_a_tick(brick):
    with pytest.raises(TypeError, match="needs a Future"):
        brick.cost(object(), 1.0, 50.0)  # type: ignore[arg-type]


def test_the_guard_names_the_symbol_it_was_handed():
    with pytest.raises(TypeError, match="XLE"):
        TickCrossing(1.0).cost(XLE, 1.0, 50.0)


@pytest.mark.parametrize(
    ("ctor", "value"), [(FuturesCommission, -0.01), (TickCrossing, -1.0)]
)
def test_a_negative_cost_is_refused_at_construction(ctor, value):
    """A rebate would flatter every study downstream and nothing there could see it."""
    with pytest.raises(ValueError):
        ctor(value)


def test_round_trip_usd_refuses_to_invent_a_price_for_a_brick_that_reads_one():
    """A zero price silently zeroes PercentOfNotionalSpread — exactly D48's failure."""
    with pytest.raises(FuturesCostError, match="PercentOfNotionalSpread"):
        round_trip_usd(ES, (FuturesCommission(3.0), PercentOfNotionalSpread(bps=1.0)))
    # With a price it is fine, and the spread really charges something.
    charged = round_trip_usd(ES, (PercentOfNotionalSpread(bps=1.0),), price=5000.0)
    assert charged == pytest.approx(2 * 250_000.0 * 1e-4, rel=1e-12)


def test_a_line_with_no_instrument_has_no_round_trip_of_its_own():
    line = FuturesRoundTrip(FuturesCommission(3.0), TickCrossing(1.0))
    with pytest.raises(FuturesCostError, match="no instrument"):
        _ = line.round_trip_usd
    # It is still a perfectly good brick — the caller supplies the contract at fill time.
    assert round_trip_usd(MES, line.bricks) == 4.25


# ------------------------------------------------------------------ the table


def test_from_table_resolves_a_parent_root_to_its_minimum_tradable_size():
    """COMPONENTS_PROP.md scores a component at minimum size; that is the default here."""
    line = FuturesRoundTrip.from_table("ES")
    assert line.instrument is not None and line.instrument.root == "MES"
    assert line.size == "micro"
    assert line.commission.per_round_trip_usd == 3.00


def test_from_table_resolves_a_traded_symbol_directly():
    line = FuturesRoundTrip.from_table("MES")
    assert line.root == "ES" and line.size == "micro"
    assert line.instrument is not None and line.instrument.tick_usd == 1.25


def test_from_table_takes_the_full_contract_when_asked():
    line = FuturesRoundTrip.from_table("ES", "full")
    assert line.instrument is not None and line.instrument.usd_per_point == 50.0
    assert line.commission.per_round_trip_usd == 6.00


def test_the_default_line_is_d508_exec_where_it_was_measured():
    line = FuturesRoundTrip.from_table("NQ", "micro")
    assert line.line == "d508_exec"
    assert line.crossing.ticks_per_round_trip == 2.1342422122227602
    assert line.window == ("2025-09-11", "2026-09-11")


def test_the_default_line_falls_back_to_the_one_tick_convention_and_not_to_a_quoted_spread():
    """D507 is a FLOOR. Falling back to it would serve two statistics under one name."""
    line = FuturesRoundTrip.from_table("ZN")
    assert line.line == "d556_one_tick"
    assert line.crossing.ticks_per_round_trip == 1.0
    assert line.window == ()
    assert "d507_all" in crossing_lines_for("ZN"), "the quoted line exists and is NOT the default"


@pytest.mark.parametrize(
    ("root", "match"),
    [
        ("NOPE", "no futures cost line"),
        ("MES", "Pass the parent root"),
    ],
)
def test_an_unknown_or_mis_sized_root_raises_and_names_what_is_known(root, match):
    with pytest.raises(FuturesCostError, match=match):
        FuturesRoundTrip.from_table(root, "full")


def test_a_root_with_no_micro_says_so_rather_than_inventing_one():
    with pytest.raises(FuturesCostError, match="no 'micro' entry"):
        FuturesRoundTrip.from_table("ZN", "micro")


def test_a_line_that_root_was_never_measured_on_raises_rather_than_borrowing_one():
    """The nuisance a wrong fallback creates is silent, so the failure must not be."""
    with pytest.raises(FuturesCostError, match="no crossing line 'd465'"):
        FuturesRoundTrip.from_table("ZN", "full", "d465")
    with pytest.raises(FuturesCostError, match="no crossing line 'invented'"):
        FuturesRoundTrip.from_table("ES", "micro", "invented")


def test_a_missing_table_raises_and_says_how_to_build_it():
    with pytest.raises(FuturesCostError, match="--build"):
        FuturesRoundTrip.from_table("ES", table_path=Path("no/such/futures_costs.json"))


def test_crossing_lines_for_shows_the_spread_of_the_estimates():
    """Looking at every line before picking one is the habit; the default hides it."""
    lines = crossing_lines_for("MNQ")
    assert set(lines) >= {"d508_exec", "d508_all", "d507_all", "d507_exec", "d556_one_tick"}
    assert min(lines.values()) == 1.0  # the convention is the cheapest on MNQ
    assert max(lines.values()) == pytest.approx(2.482738115465196)


def test_build_trade_bricks_returns_the_pair_a_cost_stack_takes():
    commission, crossing = build_trade_bricks("ES", "micro", "d556_one_tick")
    assert isinstance(commission, FuturesCommission) and isinstance(crossing, TickCrossing)
    assert CostStack(trade_bricks=(commission, crossing)).trade_cost(MES, 1.0, 5000.0) == 2.125


def test_the_table_covers_the_breadth_set_and_declares_its_lines():
    roots = table_roots()
    assert len(roots) == 36
    assert {"ES", "NQ", "CL", "GC", "ZN", "ZB", "SR3", "BZ"} <= set(roots)
    assert set(line_names()) == {
        "d465",
        "d507_all",
        "d507_exec",
        "d508_all",
        "d508_exec",
        "d510",
        "d556_one_tick",
    }


def test_the_table_is_read_once_per_path():
    assert load_cost_table() is load_cost_table()


# ------------------------------------------------------------------ properties


@given(
    commission=st.floats(min_value=0.0, max_value=1e4, allow_nan=False, allow_infinity=False),
    ticks=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
    tick_usd=st.sampled_from([0.5, 1.0, 1.25, 5.0, 6.25, 12.5, 15.625, 31.25, 1250.0]),
    price=st.floats(min_value=0.01, max_value=1e5, allow_nan=False, allow_infinity=False),
    long_first=st.booleans(),
)
@SETTINGS
def test_an_entry_and_an_exit_cost_exactly_one_round_trip(
    commission, ticks, tick_usd, price, long_first
):
    """THE property: the stack's two fills and the helper are the same double, always.

    Not approximately, and not at the four points the golden ledger names. Both sides are
    built from the same bricks in the same order, and halving by 0.5 is exact in binary, so
    equality is the right assertion and a tolerance here would hide a real regression.
    """
    future = Future(
        root="TEST", tick_points=tick_usd / 100.0, usd_per_point=100.0, tick_usd=tick_usd
    )
    bricks = (FuturesCommission(commission), TickCrossing(ticks))
    stack = CostStack(trade_bricks=bricks)

    first, second = (1.0, -1.0) if long_first else (-1.0, 1.0)
    walked = stack.trade_cost(future, first, price) + stack.trade_cost(future, second, price)
    assert walked == round_trip_usd(future, bricks)
    assert walked == round_trip_usd(future, bricks, price=price)


@given(
    commission=st.floats(min_value=0.0, max_value=1e3, allow_nan=False, allow_infinity=False),
    ticks=st.floats(min_value=0.0, max_value=1e2, allow_nan=False, allow_infinity=False),
    tick_usd=st.sampled_from([0.5, 1.25, 12.5, 15.625]),
)
@SETTINGS
def test_the_round_trip_is_commission_plus_one_tick_count(commission, ticks, tick_usd):
    """`comm + ticks * tick_usd`, the identity the whole table is written in."""
    future = Future(root="T", tick_points=tick_usd / 100.0, usd_per_point=100.0, tick_usd=tick_usd)
    bricks = (FuturesCommission(commission), TickCrossing(ticks))
    assert round_trip_usd(future, bricks) == commission + ticks * tick_usd


@given(
    quantity=st.integers(min_value=-500, max_value=500),
    commission=st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
    ticks=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@SETTINGS
def test_a_fill_costs_the_same_whichever_way_it_is_signed_and_never_less_than_nothing(
    quantity, commission, ticks
):
    stack = CostStack(trade_bricks=(FuturesCommission(commission), TickCrossing(ticks)))
    charged = stack.trade_cost(MES, float(quantity), 5000.0)
    assert charged == stack.trade_cost(MES, float(-quantity), 5000.0)
    assert charged >= 0.0
    assert math.isfinite(charged)


@given(
    a=st.integers(min_value=0, max_value=400),
    b=st.integers(min_value=0, max_value=400),
    commission=st.floats(min_value=0.0, max_value=50.0, allow_nan=False, allow_infinity=False),
    ticks=st.floats(min_value=0.0, max_value=8.0, allow_nan=False, allow_infinity=False),
)
@SETTINGS
def test_cost_is_linear_in_contracts_so_size_never_buys_a_discount(a, b, commission, ticks):
    """D493: size cannot fix a prop edge. That is only true if the model says so."""
    stack = CostStack(trade_bricks=(FuturesCommission(commission), TickCrossing(ticks)))
    one = stack.trade_cost(MES, 1.0, 5000.0)
    assert stack.trade_cost(MES, float(a), 5000.0) == pytest.approx(a * one, rel=1e-12, abs=1e-12)
    assert stack.trade_cost(MES, float(a + b), 5000.0) == pytest.approx(
        stack.trade_cost(MES, float(a), 5000.0) + stack.trade_cost(MES, float(b), 5000.0),
        rel=1e-12,
        abs=1e-12,
    )
