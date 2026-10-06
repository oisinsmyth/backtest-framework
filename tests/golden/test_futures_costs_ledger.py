"""Golden-master ledger for the futures cost bricks and the cost table.

Every number here is worked by hand in `test_futures_costs_ledger.hand.txt`, next to this
file, with a calculator that never imports this codebase. If the two disagree, the hand file
is right.

The table's cost lines are keyed by the measurement that produced them ("d556_one_tick",
"d465", "d508_exec"). Those strings are data keys in data/futures_costs.json.
"""

import json
from pathlib import Path

import pytest

from backtest_framework.config.cost_stack import BRICK_KEYS
from backtest_framework.costs.futures_bricks import (
    FuturesCommission,
    FuturesRoundTrip,
    TickCrossing,
    load_cost_table,
    round_trip_usd,
)
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.future import Future

REPO = Path(__file__).resolve().parents[2]

# Hand file §1. Written out rather than read from the specs file, because a golden test that
# reads its inputs from the same place as the code under test gates nothing.
MNQ = Future(root="MNQ", tick_points=0.25, usd_per_point=2.0, tick_usd=0.50)
MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)
ES = Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=12.50)

# Hand file §2 and §4: measured crossing figures, to their full repr.
MNQ_MEASURED_TICKS_RT = 2.4110232735988832
ES_TICKS_RT = 1.0085687251930604
MES_TICKS_RT = 1.0085687251930602


# ------------------------------------------------------------------ §2 measured crossing


def test_mnq_with_a_measured_crossing_is_the_hand_round_trip():
    """3.00 + 2.4110232735988832 * 0.50 = 4.205511636799441, to the bit (hand file §2)."""
    line = FuturesRoundTrip(
        commission=FuturesCommission(3.00),
        crossing=TickCrossing(MNQ_MEASURED_TICKS_RT),
        instrument=MNQ,
    )
    assert round_trip_usd(MNQ, line.bricks) == 4.205511636799441
    assert line.round_trip_usd == 4.205511636799441


def test_the_two_routes_to_the_round_trip_agree_bit_for_bit():
    """Per fill then doubled, against the flat sum. §0's halving argument, checked."""
    line = FuturesRoundTrip(FuturesCommission(3.00), TickCrossing(MNQ_MEASURED_TICKS_RT), instrument=MNQ)
    assert line.round_trip_usd == 3.00 + MNQ_MEASURED_TICKS_RT * MNQ.tick_usd


def test_the_measured_round_trip_rounds_to_4_21():
    measured = FuturesRoundTrip(
        FuturesCommission(3.00), TickCrossing(MNQ_MEASURED_TICKS_RT), instrument=MNQ
    ).round_trip_usd
    assert round(measured, 2) == 4.21
    assert 4.21 - measured == pytest.approx(0.004488363200559, abs=1e-15)


# ------------------------------------------------------------------ §3 the one-tick rule

#: root -> (min-size symbol, tick_usd, commission, EXACT round trip). Hand file §3.
ONE_TICK_ROWS = [
    ("NQ", "MNQ", 0.50, 3.00, 3.50),
    ("ES", "MES", 1.25, 3.00, 4.25),
    ("CL", "MCL", 1.00, 3.00, 4.00),
    ("SI", "SIL", 5.00, 3.00, 8.00),
    ("ZN", "ZN", 15.625, 6.00, 21.625),
    ("ZB", "ZB", 31.25, 6.00, 37.25),
    ("ZF", "ZF", 7.8125, 6.00, 13.8125),
]


@pytest.mark.parametrize(("root", "symbol", "tick_usd", "commission", "exact"), ONE_TICK_ROWS)
def test_the_one_tick_rule_reproduces_each_roots_round_trip(
    root, symbol, tick_usd, commission, exact
):
    """comm + one tick, from the bricks: TickCrossing(1.0) is 0.5 tick a side (hand file §3)."""
    future = Future(
        root=symbol,
        tick_points=tick_usd / 1000.0,  # any positive tick consistent with the two below
        usd_per_point=1000.0,
        tick_usd=tick_usd,
    )
    line = FuturesRoundTrip(FuturesCommission(commission), TickCrossing(1.0), instrument=future)
    assert line.round_trip_usd == exact


@pytest.mark.parametrize(("root", "symbol", "tick_usd", "commission", "exact"), ONE_TICK_ROWS)
def test_the_table_carries_each_roots_one_tick_line_and_it_is_the_same_number(
    root, symbol, tick_usd, commission, exact
):
    table = load_cost_table()
    entry = table["roots"][root][table["roots"][root]["min_size"]]
    assert entry["symbol"] == symbol
    assert entry["tick_usd"] == tick_usd
    assert entry["commission_rt_usd"]["value"] == commission
    assert entry["runner_lines"]["d556_min_size"]["value"] == exact

    line = FuturesRoundTrip.from_table(root, line="d556_one_tick")
    assert line.round_trip_usd == exact


def test_zn_is_a_genuine_rounding_tie():
    """21.625 -> 21.63 half-up, 21.62 half-even (hand file §3)."""
    exact = FuturesRoundTrip.from_table("ZN", line="d556_one_tick").round_trip_usd
    assert exact == 21.625
    assert round(exact, 2) == 21.62, "Python rounds this tie to even"
    assert f"{exact:.2f}" == "21.62"
    # ZF is not a tie and both rules agree.
    assert round(FuturesRoundTrip.from_table("ZF", line="d556_one_tick").round_trip_usd, 2) == 13.81


def test_mnq_costs_more_on_its_measured_crossing_than_on_the_convention():
    """The measured line against the one-tick rule (hand file §3)."""
    measured = FuturesRoundTrip(
        FuturesCommission(3.00), TickCrossing(MNQ_MEASURED_TICKS_RT), instrument=MNQ
    ).round_trip_usd
    convention = FuturesRoundTrip.from_table("NQ", line="d556_one_tick").round_trip_usd
    assert convention == 3.50
    assert measured - convention == pytest.approx(0.7055116367994, abs=1e-12)


# ------------------------------------------------------------------ §4 breakeven bars


@pytest.mark.parametrize(
    ("future", "ticks", "commission", "total", "breakeven"),
    [
        (ES, ES_TICKS_RT, 4.00, 16.607109064913253, 1.3285687251930602),
        (MES, MES_TICKS_RT, 3.00, 4.260710906491325, 3.40856872519306),
    ],
)
def test_breakeven_bars_reproduce_exactly_from_the_bricks(future, ticks, commission, total, breakeven):
    """ES 1.329 ticks, MES 3.409 ticks (hand file §4)."""
    line = FuturesRoundTrip(FuturesCommission(commission), TickCrossing(ticks), instrument=future)
    assert line.round_trip_usd == total
    assert line.round_trip_usd / future.tick_usd == breakeven


def test_mes_crossing_dollars_are_exact_from_the_bricks():
    mes_line = FuturesRoundTrip(FuturesCommission(3.00), TickCrossing(MES_TICKS_RT), instrument=MES)
    assert round_trip_usd(MES, (mes_line.crossing,)) == 1.2607109064913251


def test_the_two_sizes_tick_counts_differ_by_one_ulp_and_the_table_keeps_both():
    """Collapsing them would break one of the two bars (hand file §4)."""
    es = FuturesRoundTrip.from_table("ES", "full", "d465")
    mes = FuturesRoundTrip.from_table("ES", "micro", "d465")
    assert es.crossing.ticks_per_round_trip == ES_TICKS_RT
    assert mes.crossing.ticks_per_round_trip == MES_TICKS_RT
    assert es.crossing.ticks_per_round_trip != mes.crossing.ticks_per_round_trip


def test_mgc_measured_execution_hours_crossing():
    measured = FuturesRoundTrip.from_table("GC", "micro", "d508_exec")
    assert measured.crossing.ticks_per_round_trip == 2.9334505021406643
    assert measured.round_trip_usd == 5.933450502140664


def test_mng_has_only_the_one_tick_line():
    """No crossing measurement covers MNG; the one-tick rule is its only line."""
    table = load_cost_table()
    micro = table["roots"]["NG"]["micro"]
    assert micro["symbol"] == "MNG"
    assert set(micro["crossing_ticks_rt"]) == {"d556_one_tick"}
    assert micro["default_line"] == "d556_one_tick"
    assert set(table["roots"]["NG"]["full"]["crossing_ticks_rt"]) >= {"d507_all", "d507_exec"}


# ------------------------------------------------------------------ §5 and §6


def test_full_size_commission_has_two_declared_values_and_both_survive():
    """$4.00 kept on ES's older cost line against $6.00 full-size. Hand file §5."""
    es_full = load_cost_table()["roots"]["ES"]["full"]
    assert es_full["commission_rt_usd"]["value"] == 6.00
    assert es_full["commission_rt_usd"]["measured"] is False
    assert es_full["runner_lines"]["d469"]["commission_rt_usd"]["value"] == 4.00


def test_the_cent_quoted_roots_are_corrected_and_the_divisor_is_recorded():
    """Hand file §6. The raw figures are pinned too, on `tick_usd_raw_formula`, so the
    correction is checkable rather than a deletion."""
    table = load_cost_table()
    flags = {f["symbol"]: f for f in table["spec_flags"]}
    for symbol, dollars, raw in [("ZC", 12.5, 1250.0), ("ZS", 12.5, 1250.0),
                                 ("ZW", 12.5, 1250.0), ("HE", 10.0, 1000.0),
                                 ("LE", 10.0, 1000.0)]:
        assert flags[symbol]["tick_usd"] == dollars
        assert flags[symbol]["tick_usd_raw_formula"] == raw
        assert flags[symbol]["scaling_divisor"] == 100.0
        assert "CORRECTED" in flags[symbol]["unit"]
        assert table["roots"][symbol]["full"]["tick_usd"] == dollars
    assert flags["ZL"]["tick_usd"] == 6.000000000000001
    assert flags["ZL"]["tick_usd_raw_formula"] == 600.0000000000001
    assert "percent_of_par_note" in flags["SR3"]
    assert flags["SR3"]["tick_usd"] == 6.25
    assert flags["SR3"]["scaling_divisor"] == 1.0
    assert flags["SR3"]["tick_usd_raw_formula"] == 6.25


def test_hg_is_the_root_that_proves_the_divide_is_not_a_unit_of_measure_rule():
    """`HG` and `ZL` are both quoted per pound and differ by a factor of 100: HG in dollars,
    ZL in cents. A `unit_of_measure`-based rule gets one of them wrong whichever way it goes,
    which is why the divisor comes from the notional and not from the units."""
    specs = json.loads(
        (REPO / "data" / "fut_specs_from_definition.json").read_text(encoding="utf-8")
    )["specs"]
    hg, zl = specs["HG"], specs["ZL"]
    assert hg["uom"] == zl["uom"] == "LBS"
    assert hg["scaling_divisor"] == 1.0 and zl["scaling_divisor"] == 100.0
    assert hg["tick_usd_full_contract"] == 12.5
    assert zl["tick_usd_full_contract"] == 6.000000000000001
    assert load_cost_table()["roots"]["ZL"]["full"]["scaling_divisor"] == 100.0
    assert load_cost_table()["roots"]["HG"]["full"]["tick_usd"] == 12.5


def test_every_commission_in_the_table_is_declared_and_says_so():
    """Nothing here has measured a commission. Hand file §8."""
    for root, entry in load_cost_table()["roots"].items():
        for size in ("micro", "full"):
            if size in entry:
                assert entry[size]["commission_rt_usd"]["measured"] is False, f"{root}.{size}"


# ------------------------------------------------------------------ §7 BRICK_KEYS snapshot

#: The eight rows as they stood before the futures row was added. Hand file §7.
BRICK_KEYS_BEFORE_FUTURES = {
    "flat_commission": {"type", "amount"},
    "percent_spread": {"type", "bps"},
    "ibkr_commission": {"type", "per_share", "min_per_order", "max_pct_of_trade_value"},
    "borrow_fee": {"type", "annual_rate"},
    "margin_interest": {"type", "annual_rate"},
    "flat_rate_carry": {"type", "annual_rate"},
    "sqrt_impact": {"type", "coefficient", "calibration", "volume_units"},
    "dividend_flow": {"type", "source"},
}


def test_no_pre_existing_brick_key_row_moved():
    """Stored trial configs validate against these eight rows (hand file §7). Adding a row
    must not take a key off another row, which would turn a stored config into a raise."""
    for type_name, keys in BRICK_KEYS_BEFORE_FUTURES.items():
        assert type_name in BRICK_KEYS, f"{type_name} disappeared from BRICK_KEYS"
        assert set(BRICK_KEYS[type_name]) == keys, f"{type_name}'s allowed keys moved"
    # Later additive rows are allowed; what is gated is that the futures row is present.
    assert "futures_round_trip" in set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_FUTURES)


def test_the_futures_row_has_its_declared_keys():
    assert set(BRICK_KEYS["futures_round_trip"]) == {
        "type",
        "commission_rt_usd",
        "crossing_ticks_rt",
        "root",
        "line",
    }


# ------------------------------------------------------------------ the stack composes


def test_a_cost_stack_over_the_two_bricks_charges_the_round_trip():
    """The bricks in a real CostStack, entry and exit, summed as the engine sums them."""
    line = FuturesRoundTrip.from_table("NQ", "micro", "d556_one_tick")
    stack = CostStack(trade_bricks=line.bricks)
    assert stack.trade_cost(MNQ, 1.0, 20_000.0) + stack.trade_cost(MNQ, -1.0, 20_000.0) == 3.50
    assert stack.trade_cost(MNQ, 5.0, 20_000.0) == 5.0 * 0.5 * 3.50
