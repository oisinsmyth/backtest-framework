"""`ledger/non_us.py`: the eight P9 products, FX, the index month, the restrike (D611).

Three numbered required unit tests live here -- 27 (FX at the prior settlement, never the
current day's), 28 (flow is mapped to each product's own index contract month), 30 (a missing
published notional falls back to stated leverage AND flags the day) -- plus the property that
makes the other two honest: every figure Section 3.1b marks indicative, "to source" or "verify"
is `None` on the constant rather than a plausible number, and the functions that would need it
raise.

The restrike's numbers are hand-worked in `tests/golden/test_ledger_funds_ledger.hand.txt`
section 7 and asserted in the golden file; what is here is the surrounding behaviour.
"""

from __future__ import annotations

import datetime as dt
import math

import pytest

from backtest_framework.ledger.non_us import (
    BETAPRO_HND,
    BETAPRO_HNU,
    BETAPRO_HOD,
    BETAPRO_HOU,
    INDICATIVE,
    NON_US_PRODUCTS,
    NonUsError,
    Product,
    Restrike,
    RestrikeEvent,
    RestrikeLog,
    WT_3NGL,
    WT_3NGS,
    WT_3OIL,
    WT_3OIS,
    aum_usd,
    delta_h,
    effective_leverage,
    fx_rate_prior,
    index_month,
    product_value,
    q9,
    recompute_delta_h_from_restrike,
)

CURVE = ["NGV6", "NGX6", "NGZ6"]
DAY = dt.date(2026, 9, 18)
RATES = {"2026-09-16": 0.73, "2026-09-17": 0.74, "2026-09-18": 0.75}


# ------------------------------------------------------------------ the table itself


def test_the_eight_products_are_section_3_1bs_table():
    """Lines 76-84. NGXL is 3NGL's second share line, not a ninth product."""
    assert list(NON_US_PRODUCTS) == ["HNU", "HND", "HOU", "HOD", "3NGL", "3NGS", "3OIL", "3OIS"]
    assert [(p.name, p.issuer, p.stated_L, p.currency, p.underlying) for p in NON_US_PRODUCTS.values()] == [
        ("HNU", "BetaPro", 2, "CAD", "NG"),
        ("HND", "BetaPro", -2, "CAD", "NG"),
        ("HOU", "BetaPro", 2, "CAD", "CL"),
        ("HOD", "BetaPro", -2, "CAD", "CL"),
        ("3NGL", "WisdomTree", 3, "EUR", "NG"),
        ("3NGS", "WisdomTree", -3, "EUR", "NG"),
        ("3OIL", "WisdomTree", 3, "EUR", "CL"),
        ("3OIS", "WisdomTree", -3, "EUR", "CL"),
    ]
    assert all(p.listing == "TSX" for p in (BETAPRO_HNU, BETAPRO_HND, BETAPRO_HOU, BETAPRO_HOD))
    assert all("Borsa" in p.listing for p in (WT_3NGL, WT_3NGS, WT_3OIL, WT_3OIS))


def test_every_product_carries_line_74s_warning_and_no_unsourced_number():
    """Line 74: "All figures are indicative and must be re-sourced point-in-time"."""
    for p in NON_US_PRODUCTS.values():
        assert p.status.startswith(INDICATIVE), p
    # Line 80 states the 20% restrike for one line only; 81 and 82 say "verify ... restrike terms".
    assert WT_3NGL.restrike_threshold == 0.20
    assert [p.restrike_threshold for p in (WT_3NGS, WT_3OIL, WT_3OIS)] == [None, None, None]
    assert all(p.restrike_threshold is None for p in (BETAPRO_HNU, BETAPRO_HOD))
    # Line 289 gives an index month rule for BetaPro and for WisdomTree NG and for nothing else.
    assert BETAPRO_HNU.index_month_rule == "front"
    assert WT_3NGL.index_month_rule == WT_3NGS.index_month_rule == "second_front"
    assert WT_3OIL.index_month_rule is WT_3OIS.index_month_rule is None
    # The "up to 2x at manager discretion" caveat travels with the four BetaPro products.
    assert all("discretion" in p.status for p in (BETAPRO_HNU, BETAPRO_HND, BETAPRO_HOU, BETAPRO_HOD))


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("issuer", "ProShares", "issuer"),
        ("stated_L", 0, "stated_L = 0"),
        ("stated_L", 3.0, "must be an int"),
        ("index_month_rule", "back", "index_month_rule"),
        ("restrike_threshold", 20.0, "fraction"),
        ("restrike_threshold", 0.0, "fraction"),
        ("status", "", "status is empty"),
        ("currency", "", "required"),
    ],
)
def test_the_product_constructor_refuses_each_impossible_field(field, value, message):
    kwargs = dict(
        name="X",
        issuer="WisdomTree",
        stated_L=3,
        currency="EUR",
        listing="LSE",
        index_month_rule="second_front",
        restrike_threshold=0.20,
        status=INDICATIVE,
        underlying="NG",
    )
    kwargs[field] = value
    with pytest.raises(NonUsError, match=message):
        Product(**kwargs)


# ------------------------------------------------------------------ the numbered claims


def test_ledger_27_fx_uses_the_prior_settlement_and_never_the_current_day():
    """Required unit test 27, line 288."""
    rate_day, rate = fx_rate_prior(RATES, DAY)
    assert (rate_day, rate) == (dt.date(2026, 9, 17), 0.74)
    assert aum_usd(175000000.0, RATES, DAY) == 129500000.0

    # a gap in the series falls back to the last rate BEFORE the day, not forward to the next
    gapped = {"2026-09-16": 0.73, "2026-09-18": 0.75}
    assert fx_rate_prior(gapped, DAY) == (dt.date(2026, 9, 16), 0.73)

    # and when the only rates are for the day itself or later, there is no fallback at all
    for only in ({"2026-09-18": 0.75}, {"2026-09-18": 0.75, "2026-09-19": 0.76}):
        with pytest.raises(NonUsError, match="no FX rate dated before"):
            fx_rate_prior(only, DAY)
        with pytest.raises(NonUsError, match="no FX rate dated before"):
            aum_usd(175000000.0, only, DAY)

    with pytest.raises(NonUsError, match="no FX rates"):
        fx_rate_prior({}, DAY)
    with pytest.raises(NonUsError, match="ISO date"):
        fx_rate_prior({"18/09/2026": 0.74}, DAY)
    with pytest.raises(NonUsError, match="must be positive"):
        fx_rate_prior({"2026-09-17": 0.0}, DAY)
    with pytest.raises(NonUsError, match="must be a date"):
        fx_rate_prior(RATES, dt.datetime(2026, 9, 18))  # type: ignore[arg-type]


def test_ledger_28_flow_maps_to_each_products_own_index_contract_month():
    """Required unit test 28, line 289: 2nd-front for WisdomTree NG, front for BetaPro."""
    assert index_month(BETAPRO_HNU, CURVE) == "NGV6"
    assert index_month(BETAPRO_HND, CURVE) == "NGV6"
    assert index_month(WT_3NGL, CURVE) == "NGX6"
    assert index_month(WT_3NGS, CURVE) == "NGX6"
    # the two products the document gives no rule for
    for product in (WT_3OIL, WT_3OIS):
        with pytest.raises(NonUsError, match="no index month rule"):
            index_month(product, CURVE)
    # a curve too short for the rule the product names
    assert index_month(BETAPRO_HNU, ["NGV6"]) == "NGV6"
    with pytest.raises(NonUsError, match="needs the second_front month"):
        index_month(WT_3NGL, ["NGV6"])
    with pytest.raises(NonUsError, match="needs the front month"):
        index_month(BETAPRO_HNU, [])
    with pytest.raises(NonUsError, match="empty contract code"):
        index_month(WT_3NGL, ["NGV6", ""])


def test_ledger_30_a_missing_published_notional_uses_stated_l_and_flags_the_day():
    """Required unit test 30, line 282 / decision D19."""
    assert effective_leverage(140000000.0, 100000000.0, 2) == (1.4, False)
    assert effective_leverage(None, 100000000.0, 2) == (2.0, True)
    assert effective_leverage(None, 100000000.0, -2) == (-2.0, True)

    # the flag is the content: a day actually run at 1.4x is modelled at 2.0x without it
    flagged_leverage, flagged = effective_leverage(None, 100000000.0, 2)
    measured_leverage, measured = effective_leverage(140000000.0, 100000000.0, 2)
    assert flagged is True and measured is False
    aum = 50000000.0
    assert delta_h(aum, flagged_leverage, 0.04) == 4000000.0
    assert delta_h(aum, measured_leverage, 0.04) == 1119999.9999999998

    with pytest.raises(NonUsError, match="NAV"):
        effective_leverage(140000000.0, 0.0, 2)
    with pytest.raises(NonUsError, match="NAV"):
        effective_leverage(None, -1.0, 2)
    with pytest.raises(NonUsError, match="finite or None"):
        effective_leverage(math.nan, 100000000.0, 2)
    with pytest.raises(NonUsError, match="stated_L = 0"):
        effective_leverage(None, 100000000.0, 0)


# ------------------------------------------------------------------ the rest of the guards


def test_delta_h_and_q9_refuse_their_impossible_inputs():
    with pytest.raises(NonUsError, match="finite"):
        delta_h(math.inf, 3.0, 0.04)
    with pytest.raises(NonUsError, match="cannot be negative"):
        delta_h(-1.0, 3.0, 0.04)
    with pytest.raises(NonUsError, match=r"outside \[0, 1\]"):
        q9(1.0, -0.1, 10000.0, 3.0)
    with pytest.raises(NonUsError, match="multiplier"):
        q9(1.0, 0.0, 0.0, 3.0)
    with pytest.raises(NonUsError, match="p_held"):
        q9(1.0, 0.0, 10000.0, 0.0)


def test_the_restrike_threshold_is_on_the_product_and_the_trigger_is_derived():
    """Line 292's two quantities, which are one sentence apart and different."""
    r = Restrike(threshold=0.20, L=3)
    assert r.underlying_trigger == 0.2 / 3
    assert Restrike(threshold=0.20, L=-3).underlying_trigger == 0.2 / 3
    assert Restrike(threshold=0.20, L=2).underlying_trigger == 0.1
    # the check reads the product value, not the underlying move
    assert r.check(85.0, 100.0) is None
    assert r.check(79.0, 100.0) is not None
    # and it is measured from the LAST RESET, so a second 20% fall from the new level fires
    first = r.check(product_value(100.0, 3, -0.07), 100.0)
    assert first is not None
    assert r.check(first.new_reset_level * 0.85, first.new_reset_level) is None
    assert r.check(first.new_reset_level * 0.79, first.new_reset_level) is not None
    with pytest.raises(NonUsError, match="last_reset_level"):
        r.check(80.0, 0.0)
    with pytest.raises(NonUsError, match="threshold"):
        Restrike(threshold=20.0, L=3)
    with pytest.raises(NonUsError, match="L = 0"):
        Restrike(threshold=0.2, L=0)
    with pytest.raises(NonUsError, match="must be an int"):
        product_value(100.0, 3.0, -0.07)  # type: ignore[arg-type]


def test_recompute_from_the_restrike_is_the_same_formula_on_new_inputs():
    assert recompute_delta_h_from_restrike(20000000.0, 3.0, -0.01) == delta_h(
        20000000.0, 3.0, -0.01
    )


def test_the_restrike_log_refuses_a_row_it_cannot_write(tmp_path):
    log = RestrikeLog()
    bare = RestrikeEvent(drawdown=-0.21, new_reset_level=79.0, threshold=0.2, L=3)
    with pytest.raises(NonUsError, match="timestamp, product and estimated"):
        log.add(bare)
    with pytest.raises(NonUsError, match="RestrikeEvent"):
        log.add("2026-09-18,3NGL,-1")  # type: ignore[arg-type]
    log.add(
        RestrikeEvent(
            drawdown=-0.21,
            new_reset_level=79.0,
            threshold=0.2,
            L=3,
            timestamp=dt.datetime(2026, 9, 18, 13, 47),
            product="3NGL",
            estimated_dh=-1200000.0,
        )
    )
    written = log.write(tmp_path / "events.csv")
    assert written.read_text(encoding="utf-8").startswith("timestamp,product,estimated_dH\n")
    # an empty log is a written file with a header and no rows -- a run that found nothing
    empty = RestrikeLog().write(tmp_path / "empty.csv")
    assert empty.read_text(encoding="utf-8") == "timestamp,product,estimated_dH\n"
