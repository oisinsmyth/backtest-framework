"""Unit tests for the futures square-root impact brick and its depth-scaled variant (D604).

The test names carry the required-unit-test numbers they discharge:

  * `SETTLEMENT_FLOW_LEDGER_PREREG.md` §12 required unit test **7** -- impact sign follows
    `Q_rem`; zero `Q_rem` gives zero `I`.
  * §12 required unit test **45** -- `D_bar` uses PRIOR days only. (The other half of 45, that
    the depth is measured at the t0 bar close within +/-5 ticks, is discharged against the
    fixture in `tests/unit/test_fut_book_depth.py`.)
  * §12 required unit test **46** and `INDEX_REWEIGHT_FLOW_PREREG.md` §13 required unit test
    **18** -- `I_D` equals `I` when `D(t0) = D_bar`.

The identity in 46/18 is asserted with `==`, never `approx`: `sqrt(x/x)` is exactly 1.0 and a
finite double times 1.0 is itself, so a tolerance here would hide a formula that is merely close.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from backtest_framework.config.cost_stack import (
    BRICK_KEYS,
    StackDataContext,
    build_cost_stack,
    validate_stack_config,
)
from backtest_framework.config.errors import ConfigError
from backtest_framework.costs.equity_bricks import ImpactParams, SqrtImpact
from backtest_framework.costs.futures_impact import (
    DEPTH_EXPONENT,
    LEDGER_Y,
    FuturesImpactError,
    FuturesImpactParams,
    FuturesSqrtImpact,
    depth_bar,
    depth_scaled,
    impact_params,
    load_impact_table,
)
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.instruments.equity import Equity
from backtest_framework.instruments.future import Future

SETTINGS = settings(derandomize=True, max_examples=200, deadline=None)  # D78, D537

REPO = Path(__file__).resolve().parents[2]

ES = Future(root="ES", tick_points=0.25, usd_per_point=50.0, tick_usd=12.5)
CL = Future(root="CL", tick_points=0.01, usd_per_point=1000.0, tick_usd=10.0)

WINDOW = ("2016-01-04", "2023-12-29")
PROV = ("test literal",)


def params(adv: float = 1.0e6, sigma: float = 0.012) -> FuturesImpactParams:
    return FuturesImpactParams(
        line="test", window=WINDOW, provenance=PROV,
        adv_contracts=adv, sigma_fraction=sigma,
        sigma_usd_per_contract=sigma * 400_000.0, notional_usd=400_000.0,
    )


def brick(adv: float = 1.0e6, sigma: float = 0.012, coefficient: float = LEDGER_Y):
    return FuturesSqrtImpact(params_by_root={"ES": params(adv, sigma)}, coefficient=coefficient)


# ------------------------------------------------------------------ the law itself


def test_default_coefficient_is_the_ledgers_fixed_Y():
    """5.3: `Y = 0.7, fixed` (decision D6). Not SqrtImpact's order-of-magnitude 1.0."""
    assert LEDGER_Y == 0.7
    assert FuturesSqrtImpact(params_by_root={"ES": params()}).coefficient == 0.7
    assert DEPTH_EXPONENT == 0.5


def test_impact_fraction_is_the_53_formula():
    b = brick(adv=1.0e6, sigma=0.012, coefficient=0.7)
    assert b.impact_fraction(ES, 2_500.0) == 0.7 * 0.012 * math.sqrt(2_500.0 / 1.0e6)


def test_impact_fraction_scales_as_sqrt_and_dollars_as_q_to_the_three_halves():
    """D66's shape: quadrupling the order doubles the fraction and octuples the dollars."""
    b = brick()
    f1 = b.impact_fraction(ES, 100.0)
    f4 = b.impact_fraction(ES, 400.0)
    assert f4 == pytest.approx(2.0 * f1, rel=1e-15)
    c1 = b.impact_usd(ES, 100.0, 5_000.0)
    c4 = b.impact_usd(ES, 400.0, 5_000.0)
    assert c4 == pytest.approx(8.0 * c1, rel=1e-15)


def test_impact_usd_charges_the_fraction_on_the_futures_notional():
    b = brick()
    assert b.impact_usd(ES, 50.0, 5_000.0) == b.impact_fraction(ES, 50.0) * abs(
        ES.notional(50.0, 5_000.0)
    )
    assert b.cost(ES, 50.0, 5_000.0) == b.impact_usd(ES, 50.0, 5_000.0)


def test_impact_fraction_and_cost_ignore_the_sign_of_the_quantity():
    b = brick()
    assert b.impact_fraction(ES, -300.0) == b.impact_fraction(ES, 300.0)
    assert b.cost(ES, -300.0, 5_000.0) == b.cost(ES, 300.0, 5_000.0)


def test_it_composes_in_a_CostStack_like_any_other_trade_brick():
    b = brick()
    stack = CostStack(trade_bricks=(b,))
    assert stack.trade_cost(ES, 40.0, 5_000.0) == b.cost(ES, 40.0, 5_000.0)


# --------------------------------------------- ledger required unit test 7 (sign, and zero)


def test_ledger_7_impact_sign_follows_q_rem():
    """`I = ... x sign(Q_rem)` (5.3): a buy pushes the price up, a sell down, same magnitude."""
    b = brick()
    up = b.impact_for_flow(ES, +2_500.0, 5_000.0)
    down = b.impact_for_flow(ES, -2_500.0, 5_000.0)
    assert up > 0.0
    assert down < 0.0
    assert up == -down
    assert up == b.impact_fraction(ES, 2_500.0) * 5_000.0


def test_ledger_7_zero_q_rem_gives_exactly_zero_I():
    b = brick()
    assert b.impact_for_flow(ES, 0.0, 5_000.0) == 0.0
    assert b.impact_for_flow(ES, -0.0, 5_000.0) == 0.0
    assert b.impact_usd(ES, 0.0, 5_000.0) == 0.0


def test_ledger_7_zero_q_rem_gives_zero_even_for_a_root_with_no_parameters():
    """The zero is returned BEFORE the parameter lookup, so a trade of nothing never raises on a
    parameter nothing needed. A check that could only pass by never being reached would be the
    self-test that cannot fail."""
    empty = FuturesSqrtImpact(params_by_root={})
    assert empty.impact_for_flow(ES, 0.0, 5_000.0) == 0.0
    with pytest.raises(FuturesImpactError, match="no impact params for root 'ES'"):
        empty.impact_for_flow(ES, 1.0, 5_000.0)


def test_impact_for_flow_refuses_a_non_finite_price():
    with pytest.raises(FuturesImpactError, match="finite price"):
        brick().impact_for_flow(ES, 10.0, float("nan"))


# ------------------ ledger 46 / index-reweight 18: I_D == I when D(t0) == D_bar


@pytest.mark.parametrize("impact", [0.0, 1.0, -1.0, 1e-9, 1234.5678, -9.87654321e12])
@pytest.mark.parametrize("depth", [1.0, 7.0, 1e-6, 123_456.789, 1e12])
def test_ledger_46_and_index_18_i_d_equals_i_when_depth_equals_depth_bar(impact, depth):
    assert depth_scaled(impact, depth, depth) == impact


def test_ledger_46_holds_on_the_brick_s_own_three_quantities():
    b = brick()
    d = 54_927.0
    for value in (b.impact_fraction(ES, 2_500.0),
                  b.impact_for_flow(ES, -2_500.0, 5_000.0),
                  b.impact_usd(ES, 2_500.0, 5_000.0)):
        assert depth_scaled(value, d, d) == value


@SETTINGS
@given(
    impact=st.floats(min_value=-1e9, max_value=1e9, allow_nan=False, allow_infinity=False),
    depth=st.floats(min_value=1e-6, max_value=1e9, allow_nan=False, allow_infinity=False),
)
def test_ledger_46_identity_is_exact_for_any_drawn_impact_and_depth(impact, depth):
    assert depth_scaled(impact, depth, depth) == impact


def test_depth_scaling_raises_impact_on_a_thinner_book_and_lowers_it_on_a_deeper_one():
    """`sqrt(D_bar / D(t0))`: thinner than usual costs MORE. The ratio is the easy thing to
    invert, so the direction is asserted rather than described."""
    assert depth_scaled(10.0, 25.0, 100.0) == 20.0          # a quarter of the usual depth: 2x
    assert depth_scaled(10.0, 400.0, 100.0) == 5.0          # four times the usual depth: half
    assert depth_scaled(-10.0, 25.0, 100.0) == -20.0        # the sign rides through


@pytest.mark.parametrize("bad", [0.0, -1.0, -0.0])
def test_depth_scaled_raises_on_a_non_positive_depth(bad):
    with pytest.raises(FuturesImpactError, match="must be positive"):
        depth_scaled(1.0, bad, 100.0)
    with pytest.raises(FuturesImpactError, match="must be positive"):
        depth_scaled(1.0, 100.0, bad)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_depth_scaled_raises_on_a_non_finite_argument(bad):
    with pytest.raises(FuturesImpactError, match="not finite"):
        depth_scaled(bad, 1.0, 1.0)
    with pytest.raises(FuturesImpactError, match="not finite"):
        depth_scaled(1.0, bad, 1.0)


def test_depth_scaled_raises_on_a_bool_masquerading_as_a_number():
    with pytest.raises(FuturesImpactError, match="must be numeric"):
        depth_scaled(True, 1.0, 1.0)


# ------------------------------------ ledger required unit test 45: D_bar, prior days only


def _obs(first_day: int, n: int, value=lambda i: 100.0 + i):
    return [(f"2026-08-{first_day + i:02d}", value(i)) for i in range(n)]


def test_ledger_45_depth_bar_takes_the_trailing_prior_days():
    obs = _obs(1, 20)
    assert depth_bar(obs, "2026-08-21", lookback_days=20, stat="mean") == math.fsum(
        v for _, v in obs
    ) / 20
    assert depth_bar(obs, "2026-08-21", lookback_days=20) == 0.5 * (109.0 + 110.0)


def test_ledger_45_a_same_day_row_in_the_window_raises():
    """A row AT the evaluation day is look-ahead, and it must raise rather than be filtered away:
    a silent filter leaves the caller believing a guard ran."""
    obs = _obs(1, 20) + [("2026-08-21", 999.0)]
    with pytest.raises(FuturesImpactError, match="at or after the evaluation day 2026-08-21"):
        depth_bar(obs, "2026-08-21", lookback_days=20)


def test_ledger_45_a_later_day_in_the_window_raises_too():
    obs = _obs(1, 20) + [("2026-08-25", 999.0)]
    with pytest.raises(FuturesImpactError, match="at or after the evaluation day"):
        depth_bar(obs, "2026-08-21", lookback_days=20)


def test_depth_bar_raises_when_the_window_is_short_rather_than_averaging_what_it_has():
    with pytest.raises(FuturesImpactError, match="only 5 prior day"):
        depth_bar(_obs(1, 5), "2026-08-21", lookback_days=20)


def test_depth_bar_raises_on_a_repeated_day():
    obs = _obs(1, 20) + [("2026-08-05", 500.0)]
    with pytest.raises(FuturesImpactError, match="appear twice"):
        depth_bar(obs, "2026-08-21", lookback_days=20)


def test_depth_bar_raises_on_a_non_positive_depth_it_would_later_divide_by():
    obs = _obs(1, 19) + [("2026-08-20", 0.0)]
    with pytest.raises(FuturesImpactError, match="non-positive or non-finite"):
        depth_bar(obs, "2026-08-21", lookback_days=20)


def test_depth_bar_takes_the_LAST_lookback_days_not_the_first():
    obs = _obs(1, 20)
    assert depth_bar(obs, "2026-08-21", lookback_days=3, stat="mean") == math.fsum(
        [117.0, 118.0, 119.0]
    ) / 3


def test_depth_bar_median_is_the_default_and_the_mean_is_offered_beside_it():
    """8A.4 writes MEDIAN; D604's brief said mean. Both exist, the document's is the default, and
    on a right-skewed window they differ -- which is why neither may be left unsaid."""
    obs = _obs(1, 19) + [("2026-08-20", 10_000.0)]
    assert depth_bar(obs, "2026-08-21", 20) == 0.5 * (109.0 + 110.0)
    assert depth_bar(obs, "2026-08-21", 20, stat="mean") > 500.0


def test_depth_bar_rejects_an_unknown_statistic_and_a_non_positive_lookback():
    with pytest.raises(FuturesImpactError, match="must be 'median' or 'mean'"):
        depth_bar(_obs(1, 20), "2026-08-21", 20, stat="mode")
    with pytest.raises(FuturesImpactError, match="lookback_days must be positive"):
        depth_bar(_obs(1, 20), "2026-08-21", 0)


# ------------------------------------------------ the same arithmetic as the equity brick


@SETTINGS
@given(
    sigma=st.floats(min_value=1e-6, max_value=0.4, allow_nan=False, allow_infinity=False),
    adv=st.floats(min_value=1.0, max_value=1e9, allow_nan=False, allow_infinity=False),
    quantity=st.floats(min_value=-1e7, max_value=1e7, allow_nan=False, allow_infinity=False),
    coefficient=st.floats(min_value=1e-3, max_value=5.0, allow_nan=False, allow_infinity=False),
)
def test_impact_fraction_is_bit_identical_to_equity_SqrtImpact_on_the_same_numbers(
    sigma, adv, quantity, coefficient
):
    """The futures brick must be the SAME law, not a second one that agrees to a tolerance.

    `SqrtImpact` cannot be applied to a `Future` at all -- it looks up `instrument.symbol`, which
    a Future has not got, so it raises -- which is the gap D604 closes. Here it is given an
    `Equity` carrying the identical two parameters, and the two fractions are compared as bytes.
    """
    fut = FuturesSqrtImpact(
        params_by_root={"ES": FuturesImpactParams(
            line="test", window=WINDOW, provenance=PROV,
            adv_contracts=adv, sigma_fraction=sigma,
            sigma_usd_per_contract=sigma * 400_000.0, notional_usd=400_000.0)},
        coefficient=coefficient,
    )
    eq = SqrtImpact(
        params_by_symbol={"ES": ImpactParams(sigma_daily=sigma, adv_shares=adv)},
        coefficient=coefficient,
    )
    mine = fut.impact_fraction(ES, quantity)
    theirs = eq.impact_fraction(Equity(symbol="ES"), quantity)
    assert mine == theirs, f"{mine!r} != {theirs!r}"


def test_equity_SqrtImpact_still_raises_on_a_Future_which_is_the_gap_this_module_closes():
    eq = SqrtImpact(params_by_symbol={"ES": ImpactParams(sigma_daily=0.012, adv_shares=1e6)})
    with pytest.raises(ValueError, match="needs a 'symbol' attribute"):
        eq.impact_fraction(ES, 100.0)


# ------------------------------------------------------------------ the door guards


def test_a_non_future_raises_TypeError_naming_the_equity_brick():
    with pytest.raises(TypeError, match="needs a Future"):
        brick().impact_fraction(Equity(symbol="SPY"), 100.0)
    with pytest.raises(TypeError, match="equity_bricks"):
        brick().cost(Equity(symbol="SPY"), 100.0, 400.0)


def test_an_unknown_root_raises_naming_the_root_and_the_known_roots():
    b = FuturesSqrtImpact(params_by_root={"ES": params(), "CL": params()})
    with pytest.raises(FuturesImpactError) as exc:
        b.impact_fraction(Future(root="NQ", tick_points=0.25, usd_per_point=20.0, tick_usd=5.0), 1.0)
    assert "'NQ'" in str(exc.value)
    assert "CL, ES" in str(exc.value)


@pytest.mark.parametrize("field,value", [
    ("adv_contracts", 0.0), ("adv_contracts", -1.0), ("sigma_fraction", 0.0),
    ("sigma_fraction", float("nan")), ("notional_usd", 0.0),
])
def test_params_refuse_a_zero_or_non_finite_input(field, value):
    kwargs = dict(line="t", window=WINDOW, provenance=PROV, adv_contracts=1.0,
                  sigma_fraction=0.01, sigma_usd_per_contract=1.0, notional_usd=1.0)
    kwargs[field] = value
    with pytest.raises(FuturesImpactError, match="must be finite and positive"):
        FuturesImpactParams(**kwargs)


def test_params_refuse_an_empty_provenance_or_a_backwards_window():
    with pytest.raises(FuturesImpactError, match="provenance is empty"):
        FuturesImpactParams(line="t", window=WINDOW, provenance=(), adv_contracts=1.0,
                            sigma_fraction=0.01)
    with pytest.raises(FuturesImpactError, match="ends before it starts"):
        FuturesImpactParams(line="t", window=("2023-01-01", "2016-01-01"), provenance=PROV,
                            adv_contracts=1.0, sigma_fraction=0.01)


def test_an_incomplete_line_is_refused_at_CONSTRUCTION_not_at_bar_3000():
    """`breadth_meta` measures a sigma and no volume. Storing it is right; charging with it is
    not, and the refusal happens where the brick is built."""
    sigma_only = FuturesImpactParams(line="breadth_meta", window=("2010-06-07", "2026-09-09"),
                                     provenance=PROV, sigma_fraction=0.01, notional_usd=1.0,
                                     sigma_usd_per_contract=0.01)
    assert not sigma_only.complete
    assert sigma_only.missing() == ("adv_contracts",)
    with pytest.raises(FuturesImpactError, match="carries no adv_contracts"):
        FuturesSqrtImpact(params_by_root={"ES": sigma_only})


@pytest.mark.parametrize("bad", [0.0, -0.7, float("inf")])
def test_a_zero_or_non_finite_coefficient_is_refused(bad):
    with pytest.raises(FuturesImpactError, match="must be finite and positive"):
        FuturesSqrtImpact(params_by_root={"ES": params()}, coefficient=bad)


# ------------------------------------------------------------------ the committed table


def test_the_table_carries_the_36_breadth_roots_and_three_lines():
    t = load_impact_table()
    assert len(t["roots"]) == 36
    assert t["default_line"] == "day1m_2016_2023"
    assert t["coefficient_Y"] == LEDGER_Y
    assert set(t["lines"]) == {"d511", "breadth_meta", "day1m_2016_2023"}
    assert sum(1 for e in t["roots"].values() if "d511" in e["lines"]) == 9


def test_every_stored_line_carries_its_window_and_its_provenance():
    t = load_impact_table()
    for root, entry in t["roots"].items():
        for name, line in entry["lines"].items():
            assert len(line["window"]) == 2, f"{root}/{name}"
            assert line["provenance"], f"{root}/{name}"
            for p in line["provenance"]:
                assert "#" in p or p.startswith("scripts/"), f"{root}/{name}: {p!r}"


def test_the_default_line_is_the_in_sample_one_and_ends_before_the_holdout():
    t = load_impact_table()
    for root, entry in t["roots"].items():
        window = entry["lines"]["day1m_2016_2023"]["window"]
        assert window == ["2016-01-04", "2023-12-29"], root
        assert window[1] < "2024-01-01", root


def test_the_vault_window_lines_are_labelled_as_such():
    t = load_impact_table()
    assert t["roots"]["ES"]["lines"]["d511"]["window"] == ["2025-09-11", "2026-09-10"]
    assert "vault" in t["why_default"]


def test_breadth_meta_carries_no_ADV_anywhere_because_its_source_has_no_volume():
    t = load_impact_table()
    for root, entry in t["roots"].items():
        assert "adv_contracts" not in entry["lines"]["breadth_meta"], root


def test_from_table_builds_the_default_line_and_reproduces_the_stored_numbers():
    t = load_impact_table()
    line = t["roots"]["ES"]["lines"]["day1m_2016_2023"]
    b = FuturesSqrtImpact.from_table("ES")
    assert b.coefficient == LEDGER_Y
    assert b.impact_fraction(ES, 1_000.0) == (
        LEDGER_Y * line["sigma_fraction"] * math.sqrt(1_000.0 / line["adv_contracts"])
    )


def test_from_table_raises_naming_the_known_roots_and_the_roots_own_lines():
    with pytest.raises(FuturesImpactError, match="known roots"):
        FuturesSqrtImpact.from_table("NOSUCH")
    with pytest.raises(FuturesImpactError, match="no impact line 'nosuch'"):
        FuturesSqrtImpact.from_table("ES", line="nosuch")
    # ZC is one of the 27 roots d511 never measured: naming that line for it must raise rather
    # than fall back to a neighbouring window.
    with pytest.raises(FuturesImpactError, match="no impact line 'd511'"):
        FuturesSqrtImpact.from_table("ZC", line="d511")


def test_from_table_refuses_the_volume_less_line_by_name():
    with pytest.raises(FuturesImpactError, match="carries no adv_contracts"):
        FuturesSqrtImpact.from_table("ES", line="breadth_meta")


def test_impact_params_reads_one_line_without_building_a_brick():
    p = impact_params("ES", "breadth_meta")
    assert p.adv_contracts is None
    assert p.sigma_fraction is not None and p.sigma_fraction > 0.0
    assert p.window[1] <= "2026-09-09"


def test_a_missing_table_raises_rather_than_defaulting():
    with pytest.raises(FuturesImpactError, match="is missing"):
        load_impact_table(REPO / "data" / "no_such_impact_table.json")


def test_the_multiplier_disagreements_are_recorded_in_the_artefact():
    """Seven of the 36 roots have two answers for dollars-per-point in this repository, and the
    table records all seven rather than resolving one away."""
    t = load_impact_table()
    clashes = {c["root"]: c for c in t["multiplier_disagreements"]}
    assert set(clashes) == {"SR3", "ZC", "ZS", "ZW", "ZL", "LE", "HE"}
    for root, c in clashes.items():
        expected = 0.01 if root == "SR3" else 100.0
        assert c["ratio"] == pytest.approx(expected, rel=1e-12), root


# ------------------------------------------------------------------ the config dialect


def _context() -> StackDataContext:
    return StackDataContext(bars_by_symbol={}, volumes_by_symbol={},
                            actions=CorporateActions(dividends_by_symbol={}, splits_by_symbol={}))


def _stack(*trade_bricks) -> dict:
    return {"trade_bricks": list(trade_bricks), "carry_bricks": [],
            "portfolio_carry_bricks": [], "event_flow_bricks": []}


def test_the_brick_key_row_is_additive_and_the_nine_earlier_rows_are_untouched():
    """The eight legacy rows plus D591's `futures_round_trip`. 176,592 stored trial configs
    validate against the legacy eight, and taking a key off one would turn a published config
    into a raise."""
    legacy = {
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
    for name, keys in legacy.items():
        assert set(BRICK_KEYS[name]) == keys, f"{name}'s allowed keys moved"
    assert set(BRICK_KEYS) - set(legacy) == {"futures_sqrt_impact"}
    assert set(BRICK_KEYS["futures_sqrt_impact"]) == {"type", "root", "coefficient", "line"}


def test_every_legacy_brick_config_still_validates():
    legacy = [
        {"type": "flat_commission", "amount": 1.0},
        {"type": "percent_spread", "bps": 1.0},
        {"type": "ibkr_commission"},
        {"type": "sqrt_impact", "coefficient": 1.0, "calibration": "full_sample"},
        {"type": "sqrt_impact"},
        {"type": "futures_round_trip", "root": "MES"},
        {"type": "futures_round_trip", "commission_rt_usd": 3.0, "crossing_ticks_rt": 1.0},
    ]
    for cfg in legacy:
        validate_stack_config(_stack(cfg))
    validate_stack_config({"trade_bricks": [], "carry_bricks": [{"type": "borrow_fee",
                                                                "annual_rate": 0.0025}],
                           "portfolio_carry_bricks": [{"type": "margin_interest",
                                                       "annual_rate": 0.06}],
                           "event_flow_bricks": [{"type": "dividend_flow"}]})


def test_the_declarative_config_builds_the_brick_from_the_table():
    cfg = _stack({"type": "futures_sqrt_impact", "root": "ES"})
    validate_stack_config(cfg)
    stack = build_cost_stack(cfg, _context())
    assert isinstance(stack.trade_bricks[0], FuturesSqrtImpact)
    assert stack.trade_bricks[0].coefficient == LEDGER_Y
    assert stack.trade_cost(ES, 100.0, 5_000.0) == FuturesSqrtImpact.from_table("ES").cost(
        ES, 100.0, 5_000.0
    )


def test_the_declarative_config_honours_line_and_coefficient():
    cfg = _stack({"type": "futures_sqrt_impact", "root": "ES", "line": "d511",
                  "coefficient": 1.0})
    validate_stack_config(cfg)
    built = build_cost_stack(cfg, _context()).trade_bricks[0]
    assert built.coefficient == 1.0
    assert built.params_by_root["ES"].line == "d511"


def test_a_typo_on_a_futures_sqrt_impact_key_raises_instead_of_silently_defaulting():
    """The exact drift `BRICK_KEYS` exists to close: a misspelt optional key would build at the
    default while the logged config said otherwise."""
    with pytest.raises(ConfigError, match="unknown key"):
        validate_stack_config(_stack({"type": "futures_sqrt_impact", "root": "ES",
                                      "coeficient": 1.0}))


def test_a_futures_sqrt_impact_config_without_a_root_raises():
    with pytest.raises(ConfigError, match="needs a string 'root'"):
        build_cost_stack(_stack({"type": "futures_sqrt_impact"}), _context())
    with pytest.raises(ConfigError, match="needs a string 'root'"):
        build_cost_stack(_stack({"type": "futures_sqrt_impact", "root": 3}), _context())


def test_a_table_failure_surfaces_as_a_ConfigError_at_factory_time():
    with pytest.raises(ConfigError, match="futures_sqrt_impact: .*known roots"):
        build_cost_stack(_stack({"type": "futures_sqrt_impact", "root": "NOSUCH"}), _context())
    with pytest.raises(ConfigError, match="no impact line"):
        build_cost_stack(_stack({"type": "futures_sqrt_impact", "root": "ES", "line": "zzz"}),
                         _context())


def test_the_artefact_on_disk_is_the_one_the_module_reads():
    """No second copy, no embedded default: the file the builder writes is the file the brick
    loads."""
    from backtest_framework.costs import futures_impact as mod

    assert mod.TABLE_PATH == REPO / "data" / "futures_impact_params.json"
    assert json.loads(mod.TABLE_PATH.read_text(encoding="utf-8")) == load_impact_table()
