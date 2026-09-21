"""Golden-master ledger for the futures square-root impact brick and its table (D604).

Every number here is worked by hand in `test_futures_impact_ledger.hand.txt`, next to this file,
per D39 and CONTRIBUTING.md's rule that the ground truth comes from a calculator that never
imports this codebase. If the two disagree, the hand file is right.

Anything touching money belongs in `tests/golden/`, and an impact term is money at the one place
a futures study here has never charged any: size. `costs/equity_bricks.py:SqrtImpact` raises on a
`Future`, so every futures result on disk was computed with commission and crossing alone, which
is sound at one contract and silently optimistic above it. The bars reproduced below are the
committed artefact's own measured parameters, so R16 applies: exactly, or the first mismatch
named. Nothing here is asserted to a tolerance.
"""

import json
import math
from pathlib import Path

import pytest

from backtest_framework.config.cost_stack import BRICK_KEYS
from backtest_framework.costs.equity_bricks import ImpactParams, SqrtImpact
from backtest_framework.costs.futures_impact import (
    DEPTH_EXPONENT,
    LEDGER_Y,
    FuturesSqrtImpact,
    depth_scaled,
    impact_params,
    load_impact_table,
)
from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.future import Future

REPO = Path(__file__).resolve().parents[2]

# Hand file §1. Written out rather than read from the specs file, because a golden test that
# reads its inputs from the same place as the code under test gates nothing.
ES = Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=12.5)
MES = Future(root="MES", tick_points=0.25, usd_per_point=5.0, tick_usd=1.25)

# Hand file §1: the measured ES line, to its full repr.
ES_ADV = 1253830.165063291
ES_SIGMA_FRACTION = 0.00932119101946498
ES_SIGMA_USD = 1519.9726384933488
ES_NOTIONAL_USD = 163066.35443037972
ES_SESSIONS = 1975

# Hand file §5: the second root.
CL_ADV = 265938.80699008866
CL_SIGMA_FRACTION = 0.019012768995616155

# Hand file §2 and §3.
RATIO_Q1000 = 0.0007975561825389021
SQRT_Q1000 = 0.02824103720720792
FRACTION_Q1000 = 0.00018426807167734195
RATIO_Q1 = 7.975561825389021e-07
SQRT_Q1 = 0.000893060010603376
FRACTION_Q1 = 5.827068065475641e-06
RATIO_Q4000 = 0.0031902247301556085
SQRT_Q4000 = 0.05648207441441584
FRACTION_Q4000 = 0.0003685361433546839

PRICE = 4000.0          # hand file §3
NOTIONAL_Q1000 = 200000000.0
IMPACT_USD_Q1000 = 36853.61433546839
IMPACT_POINTS_Q1000 = 0.7370722867093678

# Hand file §5.
CL_RATIO_Q500 = 0.0018801317703836832
CL_SQRT_Q500 = 0.043360486279372876
CL_FRACTION_Q500 = 0.0005770820364171101


def _artefact() -> dict:
    return json.loads((REPO / "data" / "futures_impact_params.json").read_text(encoding="utf-8"))


def _es_line() -> dict:
    return _artefact()["roots"]["ES"]["lines"]["day1m_2016_2023"]


# ------------------------------------------------------------------ §0/§1 the declared constants


def test_the_declared_constants_are_the_ledgers_own():
    """Hand file §0 and §1: Y = 0.7 fixed (5.3, decision D6), exponent 0.5 fixed (8A.4)."""
    assert LEDGER_Y == 0.7
    assert DEPTH_EXPONENT == 0.5
    assert _artefact()["coefficient_Y"] == 0.7


def test_the_measured_es_line_is_the_artefacts_own_numbers_to_the_bit():
    line = _es_line()
    assert line["adv_contracts"] == ES_ADV
    assert line["sigma_fraction"] == ES_SIGMA_FRACTION
    assert line["sigma_usd_per_contract"] == ES_SIGMA_USD
    assert line["notional_usd"] == ES_NOTIONAL_USD
    assert line["sessions"] == ES_SESSIONS
    assert line["window"] == ["2016-01-04", "2023-12-29"]


def test_the_stored_sigma_fraction_is_the_stored_division_exactly():
    """Hand file §1: 1519.9726384933488 / 163066.35443037972 = 0.00932119101946498, to the bit.
    Carrying all three lets a reader check the division instead of taking it."""
    assert ES_SIGMA_USD / ES_NOTIONAL_USD == ES_SIGMA_FRACTION


def test_the_parameters_the_library_reads_are_the_ones_on_disk():
    p = impact_params("ES")
    assert p.line == "day1m_2016_2023"
    assert p.adv_contracts == ES_ADV
    assert p.sigma_fraction == ES_SIGMA_FRACTION
    assert p.window == ("2016-01-04", "2023-12-29")


# ------------------------------------------------------------------ §2 the fraction


@pytest.mark.parametrize("quantity,ratio,root,fraction", [
    (1.0, RATIO_Q1, SQRT_Q1, FRACTION_Q1),
    (1000.0, RATIO_Q1000, SQRT_Q1000, FRACTION_Q1000),
    (4000.0, RATIO_Q4000, SQRT_Q4000, FRACTION_Q4000),
])
def test_impact_fraction_reproduces_the_hand_worked_arithmetic(quantity, ratio, root, fraction):
    """Hand file §2, every intermediate: the divide, the square root and the product."""
    assert quantity / ES_ADV == ratio
    assert math.sqrt(ratio) == root
    assert LEDGER_Y * ES_SIGMA_FRACTION * root == fraction
    assert FuturesSqrtImpact.from_table("ES").impact_fraction(ES, quantity) == fraction


def test_quadrupling_the_order_doubles_the_fraction_exactly_on_these_doubles():
    """Hand file §2: 2 * 0.00018426807167734195 == 0.0003685361433546839. Exact here as a
    property of these particular doubles, not of the law -- which the hand file says."""
    assert 2.0 * FRACTION_Q1000 == FRACTION_Q4000


def test_the_fraction_in_basis_points():
    assert FRACTION_Q1000 * 1e4 == 1.8426807167734196


def test_the_second_root_is_gated_too():
    """Hand file §5: one root is one point; the table is not gated at one point."""
    line = _artefact()["roots"]["CL"]["lines"]["day1m_2016_2023"]
    assert line["adv_contracts"] == CL_ADV
    assert line["sigma_fraction"] == CL_SIGMA_FRACTION
    assert 500.0 / CL_ADV == CL_RATIO_Q500
    assert math.sqrt(CL_RATIO_Q500) == CL_SQRT_Q500
    assert LEDGER_Y * CL_SIGMA_FRACTION * CL_SQRT_Q500 == CL_FRACTION_Q500
    cl = Future(root="CL", tick_points=0.01, usd_per_point=1000.0, tick_usd=10.0)
    assert FuturesSqrtImpact.from_table("CL").impact_fraction(cl, 500.0) == CL_FRACTION_Q500


# ------------------------------------------------------------------ §3 dollars and signed points


def test_the_notional_and_the_dollar_impact():
    """Hand file §3: 1,000 ES at 4,000 is $200,000,000 of index, and the impact is $36,853.61."""
    assert ES.notional(1000.0, PRICE) == NOTIONAL_Q1000
    brick = FuturesSqrtImpact.from_table("ES")
    assert FRACTION_Q1000 * NOTIONAL_Q1000 == IMPACT_USD_Q1000
    assert brick.impact_usd(ES, 1000.0, PRICE) == IMPACT_USD_Q1000
    assert brick.cost(ES, 1000.0, PRICE) == IMPACT_USD_Q1000


def test_ledger_7_the_signed_move_in_price_points():
    """Hand file §3, required unit test 7(a): equal and opposite, and the buy is positive."""
    brick = FuturesSqrtImpact.from_table("ES")
    assert FRACTION_Q1000 * PRICE == IMPACT_POINTS_Q1000
    assert brick.impact_for_flow(ES, 1000.0, PRICE) == IMPACT_POINTS_Q1000
    assert brick.impact_for_flow(ES, -1000.0, PRICE) == -IMPACT_POINTS_Q1000


def test_ledger_7_zero_flow_is_exactly_zero():
    """Hand file §3, required unit test 7(b) -- including the negative zero."""
    brick = FuturesSqrtImpact.from_table("ES")
    assert brick.impact_for_flow(ES, 0.0, PRICE) == 0.0
    assert brick.impact_for_flow(ES, -0.0, PRICE) == 0.0
    assert brick.impact_usd(ES, 0.0, PRICE) == 0.0


def test_the_fraction_is_size_invariant_and_the_notional_is_not():
    """Hand file §3: one ES is $200,000 of index at 4,000 and one MES is $20,000. The fraction is
    the same number; what changes is what it is charged on."""
    brick = FuturesSqrtImpact(
        params_by_root={"ES": impact_params("ES"), "MES": impact_params("ES")}
    )
    assert brick.impact_fraction(ES, 1000.0) == brick.impact_fraction(MES, 1000.0)
    assert ES.notional(1.0, PRICE) == 200000.0
    assert MES.notional(1.0, PRICE) == 20000.0
    size = _artefact()["roots"]["ES"]["size"]
    assert size["size_ratio_full_over_sized"] == 10.0
    assert size["usd_per_point_sized"] == 5.0
    assert size["sized_as"] == "MES"


# ------------------------------------------------------------------ §4 the depth identity


@pytest.mark.parametrize("value", [FRACTION_Q1000, IMPACT_POINTS_Q1000, IMPACT_USD_Q1000,
                                   -IMPACT_POINTS_Q1000, 0.0])
@pytest.mark.parametrize("depth", [54927.0, 1.0, 1e12])
def test_ledger_46_and_index_18_the_depth_identity_is_exact(value, depth):
    """Hand file §4. Ledger required unit test 46 and INDEX_REWEIGHT_FLOW_PREREG.md required unit
    test 18: `I_D` equals `I` when `D(t0) = D_bar`. Asserted with `==`."""
    assert depth_scaled(value, depth, depth) == value


def test_the_depth_scaling_direction_is_the_one_8A4_intends():
    """Hand file §4: a book at a quarter of its usual depth doubles the impact."""
    assert depth_scaled(10.0, 25.0, 100.0) == 20.0
    assert depth_scaled(10.0, 400.0, 100.0) == 5.0
    assert depth_scaled(-10.0, 25.0, 100.0) == -20.0
    assert depth_scaled(FRACTION_Q1000, 25.0, 100.0) == FRACTION_Q4000  # the §4 coincidence


# ------------------------------------------------------------------ §6 the same law


def test_it_is_the_same_law_as_the_equity_brick_to_the_bit():
    """Hand file §6: identical expression, identical doubles, identical result."""
    fut = FuturesSqrtImpact.from_table("ES")
    eq = SqrtImpact(
        params_by_symbol={"ES": ImpactParams(sigma_daily=ES_SIGMA_FRACTION, adv_shares=ES_ADV)},
        coefficient=LEDGER_Y,
    )
    assert fut.impact_fraction(ES, 1000.0) == eq.impact_fraction(Equity(symbol="ES"), 1000.0)
    assert fut.impact_fraction(ES, 1000.0) == FRACTION_Q1000


def test_the_equity_brick_still_cannot_price_a_future_which_is_the_gap_closed():
    """Hand file §6. A suite that did not pin this could not tell the gap had been closed from
    the gap never having existed."""
    eq = SqrtImpact(params_by_symbol={"ES": ImpactParams(sigma_daily=0.01, adv_shares=1e6)})
    with pytest.raises(ValueError, match="needs a 'symbol' attribute"):
        eq.cost(ES, 1000.0, PRICE)


# ------------------------------------------------------------------ §7 the BRICK_KEYS row


#: The nine rows as they stood BEFORE D604 added a tenth: the eight legacy rows plus D591's.
#: Transcribed from the hand file, which transcribed them from cost_stack.py before the edit.
BRICK_KEYS_BEFORE_D604 = {
    "flat_commission": {"type", "amount"},
    "percent_spread": {"type", "bps"},
    "ibkr_commission": {"type", "per_share", "min_per_order", "max_pct_of_trade_value"},
    "borrow_fee": {"type", "annual_rate"},
    "margin_interest": {"type", "annual_rate"},
    "flat_rate_carry": {"type", "annual_rate"},
    "sqrt_impact": {"type", "coefficient", "calibration", "volume_units"},
    "dividend_flow": {"type", "source"},
    "futures_round_trip": {"type", "commission_rt_usd", "crossing_ticks_rt", "root", "line"},
}


def test_no_pre_existing_brick_key_row_moved():
    """Hand file §7. 176,592 stored trial configs validate against the legacy eight, and D591's
    row is published too. What this gates is that adding a tenth took no key off any of the nine
    -- which would turn a stored, published config into a raise."""
    for type_name, keys in BRICK_KEYS_BEFORE_D604.items():
        assert type_name in BRICK_KEYS, f"{type_name} disappeared from BRICK_KEYS"
        assert set(BRICK_KEYS[type_name]) == keys, f"{type_name}'s allowed keys moved"
    assert set(BRICK_KEYS) - set(BRICK_KEYS_BEFORE_D604) == {"futures_sqrt_impact"}


def test_the_new_row_is_exactly_the_four_keys_the_factory_reads():
    assert set(BRICK_KEYS["futures_sqrt_impact"]) == {"type", "root", "coefficient", "line"}


# ------------------------------------------------------------------ §8 the artefact's shape


def test_the_artefacts_shape_is_the_one_the_hand_file_describes():
    t = load_impact_table()
    assert t["default_line"] == "day1m_2016_2023"
    assert len(t["roots"]) == 36
    assert set(t["lines"]) == {"d511", "breadth_meta", "day1m_2016_2023"}
    assert t["complete_lines"] == ["d511", "day1m_2016_2023"]
    assert sum(1 for e in t["roots"].values() if "d511" in e["lines"]) == 9


def test_breadth_meta_carries_a_sigma_and_no_volume_on_every_root():
    t = load_impact_table()
    for root, entry in t["roots"].items():
        line = entry["lines"]["breadth_meta"]
        assert line["sigma_fraction"] > 0.0, root
        assert "adv_contracts" not in line, root


def test_the_default_line_is_the_only_in_sample_one():
    t = load_impact_table()
    assert t["roots"]["ES"]["lines"]["day1m_2016_2023"]["window"][1] == "2023-12-29"
    assert t["roots"]["ES"]["lines"]["d511"]["window"] == ["2025-09-11", "2026-09-10"]
    assert t["roots"]["ES"]["lines"]["breadth_meta"]["window"][1] == "2026-09-09"
