"""Golden-master ledger for the futures cost bricks and the cost table (D591).

Every number here is worked by hand in `test_futures_costs_ledger.hand.txt`, next to this
file, per D39 and CONTRIBUTING.md's rule that the ground truth comes from a calculator that
never imports this codebase. If the two disagree, the hand file is right.

Anything touching money belongs in `tests/golden/`, and a cost line is money twice over: it
is subtracted from every trade, and it is the thing that decided D466's "there is no book".
The bars reproduced below — D469's breakeven ticks, D527's $4.2055, D556's per-root round
trips — are PUBLISHED numbers, so R16 applies: exactly, or the first mismatch named. One
mismatch exists and §4 of the hand file names it to the ULP.
"""

import importlib.util
import json
import sys
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

# Hand file §2 and §4: the measured crossing figures, to their full repr.
D527_TICKS_RT = 2.4110232735988832
D465_TICKS_RT_ES = 1.0085687251930604
D465_TICKS_RT_MES = 1.0085687251930602

PRICE = 6919.5  # D469's median ES price; every bar in §4 is quoted at it.


def _artefact(name: str) -> dict:
    return json.loads((REPO / "data" / name).read_text(encoding="utf-8"))


def _load_d469():
    """Exec `scripts/d469_scalping_feasibility.py` as a module, the `test_folds_ledger.py` way.

    Its import-time work is reading two committed JSON files; it touches no panel and no bar.
    Named by explicit path rather than by import, because `scripts/` is not a package and
    pytest imports any path you hand it.
    """
    path = REPO / "scripts" / "d469_scalping_feasibility.py"
    spec = importlib.util.spec_from_file_location("d469_scalping_feasibility", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["d469_scalping_feasibility"] = module
    spec.loader.exec_module(module)
    return module


# ------------------------------------------------------------------ §2 the D527 line


def test_mnq_on_the_d527_line_is_the_published_round_trip():
    """3.00 + 2.4110232735988832 * 0.50 = 4.205511636799441, to the bit (hand file §2)."""
    line = FuturesRoundTrip(
        commission=FuturesCommission(3.00),
        crossing=TickCrossing(D527_TICKS_RT),
        instrument=MNQ,
    )
    assert round_trip_usd(MNQ, line.bricks) == 4.205511636799441
    assert line.round_trip_usd == 4.205511636799441

    published = _artefact("d527_arm_crossing_cost.json")["reprice"]["scored"]["measured"]["rt_usd"]
    assert line.round_trip_usd == published


def test_the_two_routes_to_the_d527_round_trip_agree_bit_for_bit():
    """Per fill then doubled, against the flat sum. §0's halving argument, checked."""
    line = FuturesRoundTrip(FuturesCommission(3.00), TickCrossing(D527_TICKS_RT), instrument=MNQ)
    assert line.round_trip_usd == 3.00 + D527_TICKS_RT * MNQ.tick_usd


def test_the_artefacts_two_tick_counts_differ_by_one_ulp_and_the_dollar_does_not():
    """Hand file §2's note. The mismatch is real, immaterial here, and recorded — not hidden."""
    reprice = _artefact("d527_arm_crossing_cost.json")["reprice"]
    headline = reprice["round_trip_crossing_ticks"]
    scored = reprice["scored"]["measured"]["cross_ticks"]
    assert headline != scored
    assert abs(headline - scored) < 1e-15
    for ticks in (headline, scored):
        line = FuturesRoundTrip(FuturesCommission(3.00), TickCrossing(ticks), instrument=MNQ)
        assert line.round_trip_usd == 4.205511636799441


def test_d531_charges_the_d527_number_rounded_to_the_cent():
    """COST_USD = 4.21 in run_d531_orb_session_native.py:41 (hand file §2, ROUNDED form)."""
    measured = FuturesRoundTrip(
        FuturesCommission(3.00), TickCrossing(D527_TICKS_RT), instrument=MNQ
    ).round_trip_usd
    assert round(measured, 2) == 4.21
    assert 4.21 - measured == pytest.approx(0.004488363200559, abs=1e-15)


# ------------------------------------------------------------------ §3 the D556 rule

#: root -> (min-size symbol, tick_usd, commission, EXACT round trip). Hand file §3.
D556_ROWS = [
    ("NQ", "MNQ", 0.50, 3.00, 3.50),
    ("ES", "MES", 1.25, 3.00, 4.25),
    ("CL", "MCL", 1.00, 3.00, 4.00),
    ("SI", "SIL", 5.00, 3.00, 8.00),
    ("ZN", "ZN", 15.625, 6.00, 21.625),
    ("ZB", "ZB", 31.25, 6.00, 37.25),
    ("ZF", "ZF", 7.8125, 6.00, 13.8125),
]


@pytest.mark.parametrize(("root", "symbol", "tick_usd", "commission", "exact"), D556_ROWS)
def test_the_d556_one_tick_rule_reproduces_each_roots_round_trip(
    root, symbol, tick_usd, commission, exact
):
    """comm + one tick, from the bricks: TickCrossing(1.0) IS 0.5 tick a side (hand file §3)."""
    future = Future(
        root=symbol,
        tick_points=tick_usd / 1000.0,  # any positive tick consistent with the two below
        usd_per_point=1000.0,
        tick_usd=tick_usd,
    )
    line = FuturesRoundTrip(FuturesCommission(commission), TickCrossing(1.0), instrument=future)
    assert line.round_trip_usd == exact


@pytest.mark.parametrize(("root", "symbol", "tick_usd", "commission", "exact"), D556_ROWS)
def test_the_table_carries_each_roots_d556_line_and_it_is_the_same_number(
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


def test_zn_is_a_genuine_rounding_tie_and_the_record_prints_the_half_up_form():
    """21.625 -> 21.63 half-up, 21.62 half-even. The ledger prints 21.63 (hand file §3)."""
    exact = FuturesRoundTrip.from_table("ZN", line="d556_one_tick").round_trip_usd
    assert exact == 21.625
    assert round(exact, 2) == 21.62, "Python rounds this tie to even; the record prints 21.63"
    assert f"{exact:.2f}" == "21.62"
    # ZF is not a tie and both rules agree.
    assert round(FuturesRoundTrip.from_table("ZF", line="d556_one_tick").round_trip_usd, 2) == 13.81


def test_mnq_costs_more_on_its_own_measurement_than_on_the_convention():
    """The D527 line against the D556 rule: the difference IS the measurement (hand file §3)."""
    measured = FuturesRoundTrip(
        FuturesCommission(3.00), TickCrossing(D527_TICKS_RT), instrument=MNQ
    ).round_trip_usd
    convention = FuturesRoundTrip.from_table("NQ", line="d556_one_tick").round_trip_usd
    assert convention == 3.50
    assert measured - convention == pytest.approx(0.7055116367994, abs=1e-12)


# ------------------------------------------------------------------ §4 D469's bars


@pytest.mark.parametrize(
    ("symbol", "future", "ticks", "commission", "total", "breakeven"),
    [
        ("ES", ES, D465_TICKS_RT_ES, 4.00, 16.607109064913253, 1.3285687251930602),
        ("MES", MES, D465_TICKS_RT_MES, 3.00, 4.260710906491325, 3.40856872519306),
    ],
)
def test_d469_breakeven_bars_reproduce_exactly_from_the_bricks(
    symbol, future, ticks, commission, total, breakeven
):
    """ES 1.329 ticks, MES 3.409 ticks, at price 6919.5 (hand file §4)."""
    line = FuturesRoundTrip(FuturesCommission(commission), TickCrossing(ticks), instrument=future)
    assert line.round_trip_usd == total
    assert line.round_trip_usd / future.tick_usd == breakeven

    published = _artefact("d469_scalping_feasibility.json")["cost_bars"][symbol]
    assert published["total_usd"] == total
    assert published["breakeven_ticks"] == breakeven
    assert commission / future.tick_usd == published["commission_ticks"]


def test_d469s_own_function_agrees_with_the_bricks_exactly_on_the_bars():
    """Import D469 and compare to its function's output, not to a transcription of it.

    R16: a published number is the output of a pipeline. This runs the pipeline.
    """
    d469 = _load_d469()
    for symbol, future, ticks, commission in [
        ("ES", ES, D465_TICKS_RT_ES, 4.00),
        ("MES", MES, D465_TICKS_RT_MES, 3.00),
    ]:
        bar = d469.breakeven_ticks(symbol, PRICE)
        line = FuturesRoundTrip(
            FuturesCommission(commission), TickCrossing(ticks), instrument=future
        )
        assert line.round_trip_usd == bar["total_usd"]
        assert line.round_trip_usd / future.tick_usd == bar["breakeven_ticks"]
        assert line.crossing.ticks_per_round_trip == bar["crossing_ticks"]
        assert line.commission.per_round_trip_usd == bar["commission_usd"]


def test_the_one_mismatch_is_mes_crossing_dollars_and_it_is_one_ulp():
    """THE mismatch in this whole ledger, named rather than tolerated (hand file §4).

    D469 forms MES crossing as bp x notional; the brick forms it as ticks x tick_usd. The
    two land one ULP apart and the difference does not reach total_usd, which is asserted
    exactly above. ES has no such gap.
    """
    published = _artefact("d469_scalping_feasibility.json")["cost_bars"]

    mes_line = FuturesRoundTrip(FuturesCommission(3.00), TickCrossing(D465_TICKS_RT_MES), instrument=MES)
    mes_crossing = round_trip_usd(MES, (mes_line.crossing,))
    assert mes_crossing == 1.2607109064913251
    assert published["MES"]["crossing_usd"] == 1.2607109064913253
    assert mes_crossing != published["MES"]["crossing_usd"]
    assert abs(mes_crossing - published["MES"]["crossing_usd"]) < 3e-16

    es_line = FuturesRoundTrip(FuturesCommission(4.00), TickCrossing(D465_TICKS_RT_ES), instrument=ES)
    assert round_trip_usd(ES, (es_line.crossing,)) == published["ES"]["crossing_usd"]


def test_the_two_sizes_d465_tick_counts_differ_by_one_ulp_and_the_table_keeps_both():
    """Collapsing them would break one of the two published bars (hand file §4)."""
    es = FuturesRoundTrip.from_table("ES", "full", "d465")
    mes = FuturesRoundTrip.from_table("ES", "micro", "d465")
    assert es.crossing.ticks_per_round_trip == D465_TICKS_RT_ES
    assert mes.crossing.ticks_per_round_trip == D465_TICKS_RT_MES
    assert es.crossing.ticks_per_round_trip != mes.crossing.ticks_per_round_trip


# ------------------------------------------------------------------ §5 D533's dict

#: run_d533_story_conditions.py:36, recorded verbatim. Hand file §5.
D533_COST = {"CL": 4.00, "GC": 5.00, "SI": 8.00, "NG": 5.00, "ES": 4.25, "NQ": 4.21}


def test_d533s_dict_is_recorded_exactly_as_the_runner_charges_it():
    import ast

    tree = ast.parse((REPO / "scripts" / "run_d533_story_conditions.py").read_text(encoding="utf-8"))
    found = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "COST" for t in node.targets
        ):
            found = ast.literal_eval(node.value)
    assert found == D533_COST


@pytest.mark.parametrize(
    ("root", "charged"), [("CL", 4.00), ("SI", 8.00), ("ES", 4.25)]
)
def test_three_of_d533s_six_are_derived_by_the_one_tick_rule(root, charged):
    """CL, SI and ES equal comm 3.00 + their micro's tick exactly (hand file §5)."""
    assert FuturesRoundTrip.from_table(root, line="d556_one_tick").round_trip_usd == charged


def test_nq_is_derived_from_d527_not_from_the_one_tick_rule():
    measured = FuturesRoundTrip(
        FuturesCommission(3.00), TickCrossing(D527_TICKS_RT), instrument=MNQ
    ).round_trip_usd
    assert round(measured, 2) == D533_COST["NQ"] == 4.21
    assert FuturesRoundTrip.from_table("NQ", line="d556_one_tick").round_trip_usd != D533_COST["NQ"]


@pytest.mark.parametrize("root", ["GC", "NG"])
def test_gc_and_ng_are_charged_not_derived_and_the_table_says_so(root):
    """No line in the table produces 5.00 on either. Recorded, with what it is NOT (hand §5)."""
    rule = FuturesRoundTrip.from_table(root, line="d556_one_tick").round_trip_usd
    assert rule == 4.00
    assert D533_COST[root] == 5.00

    disagreements = load_cost_table()["disagreements"]
    assert any(root in d["what"] and "not derived" in d["resolution"].lower() for d in disagreements)


def test_mgcs_measured_crossing_is_near_five_dollars_but_is_not_the_derivation():
    """The nearest measured figure to D533's GC 5.00, and it is not equal to it (hand §5)."""
    measured = FuturesRoundTrip.from_table("GC", "micro", "d508_exec")
    assert measured.crossing.ticks_per_round_trip == 2.9334505021406643
    assert measured.round_trip_usd == 5.933450502140664
    assert measured.round_trip_usd != D533_COST["GC"]


def test_mng_is_in_no_crossing_census_on_disk():
    """D507 covers NG and not MNG; D508 covers neither. The one-tick rule is all there is."""
    table = load_cost_table()
    micro = table["roots"]["NG"]["micro"]
    assert micro["symbol"] == "MNG"
    assert set(micro["crossing_ticks_rt"]) == {"d556_one_tick"}
    assert micro["default_line"] == "d556_one_tick"
    assert set(table["roots"]["NG"]["full"]["crossing_ticks_rt"]) >= {"d507_all", "d507_exec"}


# ------------------------------------------------------------------ §6 disagreements


def test_full_size_commission_has_two_declared_values_and_both_survive():
    """$4.00 (D258/D469 on ES) against $6.00 (D468/D555 full-size). Hand file §6(i)."""
    es_full = load_cost_table()["roots"]["ES"]["full"]
    assert es_full["commission_rt_usd"]["value"] == 6.00
    assert es_full["commission_rt_usd"]["measured"] is False
    assert es_full["runner_lines"]["d469"]["commission_rt_usd"]["value"] == 4.00


def test_the_cent_quoted_roots_are_corrected_and_the_divisor_is_recorded():
    """SUPERSEDED BY D609. Hand file §6(iii) recorded ZC/ZS/ZW at 1250, HE/LE at 1000, ZL at
    600 and SR3 at 0.0625, "written unchanged" with a flag, because the builder was reading the
    definition snapshot's raw `tick_usd`. Those were CENTS (and, for SR3, hundredths of a
    dollar). The table now reads `tick_usd_full_contract`, decided by the notional test, and
    the flag records the divisor and the raw formula instead of explaining a wrong number.

    The RAW figures are pinned too, on `tick_usd_raw_formula`: the old ledger line is still
    reproducible from this table, which is what makes the correction checkable rather than a
    deletion.
    """
    table = load_cost_table()
    flags = {f["symbol"]: f for f in table["spec_flags"]}
    for symbol, dollars, raw in [("ZC", 12.5, 1250.0), ("ZS", 12.5, 1250.0),
                                 ("ZW", 12.5, 1250.0), ("HE", 10.0, 1000.0),
                                 ("LE", 10.0, 1000.0)]:
        assert flags[symbol]["tick_usd"] == dollars
        assert flags[symbol]["tick_usd_raw_formula"] == raw
        assert flags[symbol]["scaling_divisor"] == 100.0
        assert "CORRECTED (D609)" in flags[symbol]["unit"]
        assert table["roots"][symbol]["full"]["tick_usd"] == dollars
    assert flags["ZL"]["tick_usd"] == 6.000000000000001
    assert flags["ZL"]["tick_usd_raw_formula"] == 600.0000000000001
    assert "percent_of_par_note" in flags["SR3"]
    assert flags["SR3"]["tick_usd"] == 6.25
    assert flags["SR3"]["scaling_divisor"] == 1.0
    assert flags["SR3"]["tick_usd_raw_formula"] == 6.25


def test_hg_is_the_root_that_proves_the_divide_is_not_a_unit_of_measure_rule():
    """`HG` and `ZL` are both quoted per POUND and differ by a factor of 100: HG in dollars,
    ZL in cents. A `unit_of_measure`-based rule gets one of them wrong whichever way it goes,
    which is why the divisor comes from the notional and not from the units."""
    import json
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    specs = json.loads(
        (repo / "data" / "fut_specs_from_definition.json").read_text(encoding="utf-8")
    )["specs"]
    hg, zl = specs["HG"], specs["ZL"]
    assert hg["uom"] == zl["uom"] == "LBS"
    assert hg["scaling_divisor"] == 1.0 and zl["scaling_divisor"] == 100.0
    assert hg["tick_usd_full_contract"] == 12.5
    assert zl["tick_usd_full_contract"] == 6.000000000000001
    # HG is read through the CME file by the cost table (it has a verified value there), so the
    # claim is asserted on the spec file where both roots are decided by the same rule; the
    # table's own ZL entry is the one that carries the divisor.
    assert load_cost_table()["roots"]["ZL"]["full"]["scaling_divisor"] == 100.0
    assert load_cost_table()["roots"]["HG"]["full"]["tick_usd"] == 12.5


def test_every_commission_in_the_table_is_declared_and_says_so():
    """Nothing here has measured a commission. Hand file §7."""
    for root, entry in load_cost_table()["roots"].items():
        for size in ("micro", "full"):
            if size in entry:
                assert entry[size]["commission_rt_usd"]["measured"] is False, f"{root}.{size}"


# ------------------------------------------------------------------ §7 BRICK_KEYS snapshot

#: The eight rows as they stood BEFORE D591 added a ninth. Transcribed from the hand file,
#: which transcribed them from cost_stack.py before the edit.
BRICK_KEYS_BEFORE_D591 = {
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
    """176,592 stored trial configs validate against these eight rows (hand file §7).

    The row added by D591 is additive and is asserted separately. What this gates is that
    adding it did not take a key off another row — which would turn a stored, published
    config into a raise, and which nothing else in the suite would notice for four of them.
    """
    for type_name, keys in BRICK_KEYS_BEFORE_D591.items():
        assert type_name in BRICK_KEYS, f"{type_name} disappeared from BRICK_KEYS"
        assert set(BRICK_KEYS[type_name]) == keys, f"{type_name}'s allowed keys moved"
    # Additive rows after D591 are allowed (D604 added `futures_sqrt_impact` on 2026-09-21); what
    # is gated is that D591's row is present and no pre-existing row lost a key. An equality on
    # the whole difference would turn every later additive brick into a red golden.
    assert "futures_round_trip" in set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_D591)


def test_the_new_row_is_the_one_d591_declares():
    assert set(BRICK_KEYS["futures_round_trip"]) == {
        "type",
        "commission_rt_usd",
        "crossing_ticks_rt",
        "root",
        "line",
    }


# ------------------------------------------------------------------ the stack composes


def test_a_cost_stack_over_the_two_bricks_charges_the_published_round_trip():
    """The bricks in a real CostStack, entry and exit, summed as the engine sums them."""
    line = FuturesRoundTrip.from_table("NQ", "micro", "d556_one_tick")
    stack = CostStack(trade_bricks=line.bricks)
    assert stack.trade_cost(MNQ, 1.0, 20_000.0) + stack.trade_cost(MNQ, -1.0, 20_000.0) == 3.50
    assert stack.trade_cost(MNQ, 5.0, 20_000.0) == 5.0 * 0.5 * 3.50
