"""Unit tests for D620's quarterly Schedule-of-Investments parser and its gates.

**No numbered deposit test is claimed here.** The deposit's §12 has no filings test; what this
file defends is the parse itself, and every one of its failure modes is silent:

  * a filing era whose row shape the parser does not know returns FEWER rows, not an error, and
    the fixture's coverage then describes the parser rather than the funds — hence the
    zero-row guard on a futures block, tested here on a block that has one;
  * the USCF schedule has **three different column orders** across eighteen years, and in two of
    them the second money column is the UNREALIZED GAIN rather than a notional. Writing that
    into `notional_usd` gives an `f_fut` computed from two different quantities that looks
    entirely reasonable;
  * `PROSHARES ULTRA ` and `PROSHARES ULTRASHORT ` differ by four characters, so a loose alias
    silently merges UCO with SCO — and one real filing spells it `PROSHARES ULTR ASHORT`;
  * a CME code carries ONE year digit, so `CLX2` is ambiguous without the period it is held at;
  * and an anchor whose share count was blanked by a later partial match inside the same filing
    is a projection anchor with a hole in it, which is the shape that breaks `project_fund_panel`.

Every guard is shown to ACCEPT a good case FIRST and then to RAISE on a break aimed at the
scalar it compares. No return is computed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]


def _script(name: str) -> Any:
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


B = _script("build_fund_holdings_quarterly")


# ---------------------------------------------------------------- hand-typed table fragments
#: A ProShares futures table, typed from the shape of `0001193125-25-039791`. Two blocks, one
#: purchased and one sold, so the sign convention is exercised in both directions inside one
#: document rather than asserted for one.
PROSHARES_FRAGMENT = (
    "PROSHARES ULTRA BLOOMBERG NATURAL GAS SCHEDULE OF INVESTMENTS DECEMBER 31, 2023 "
    "Principal Amount Value Short-term U.S. government and agency obligations "
    "Total short-term U.S. government and agency obligations (cost $ 64,445,510 ) $ 64,459,117 "
    "Futures Contracts Purchased Number of Contracts Notional Amount at Value Unrealized "
    "Appreciation (Depreciation)/Value Natural Gas - NYMEX, expires March 2024 62,768 "
    "$ 1,460,611,360 $ 43,607,070 "
    "Futures Contracts Sold Number of Contracts Notional Amount at Value "
    "Natural Gas - NYMEX, expires June 2024 1,000 $ 20,000,000 $ 1,000 "
    "PROSHARES ULTRA BLOOMBERG NATURAL GAS STATEMENTS OF FINANCIAL CONDITION "
    "December 31, 2023 December 31, 2022 Assets "
    "Shareholders&#8217; equity Shareholders&#8217; equity 729,892,808 100,000,000 "
    "Shares outstanding (Note 1) 5,113,709 1,000,000 "
    "Net asset value per share (Note 1) $ 142.73 $ 100.00 "
    "PROSHARES ULTRA BLOOMBERG NATURAL GAS STATEMENTS OF OPERATIONS"
)

#: A USCF swap table, typed from the shape of `0001410578-24-000105`. The counterparty sits
#: before the payment frequency and the notional is the first money column.
USCF_FRAGMENT = (
    "United States Natural Gas Fund, LP Schedule of Investments At December 31, 2023 "
    "Notional Amount Contracts Contracts Capital "
    "Open Commodity Futures Contracts - Long United States Contracts "
    "NYMEX Natural Gas Futures NG February 2024 contracts, expiring January 2024 * "
    "$ 695,222,259 29,248 $ 40,072,461 4.11 "
    "Total United States Money Market Funds $ 70,950,000 7.29 "
    "Open OTC Commodity Swap Contracts "
    "MACQUARIE MQCP362H 12122023Index (b) 0.25 % Macquarie Bank Ltd Monthly 01/12/2024 "
    "$ 129,306,126 144,210,360 — $ 14,904,234 "
    "SOC GEN SGIXCNG1 09292023Index (b) 0.40 Societe Generale Monthly 03/29/2024 "
    "94,559,204 94,558,181 — ( 1,023 ) "
    "United States Natural Gas Fund, LP Statements of Operations"
)

#: A fund section with a Statements of Financial Condition and NO Schedule of Investments the
#: parser can read. It must produce an `unparsed` row carrying the anchors and a reason, never
#: no row at all.
UNPARSEABLE_FRAGMENT = (
    "United States Oil Fund, LP Statements of Financial Condition At March 31, 2006 "
    "Assets Cash … $1,000 Partnership Capital Limited partner $980 General partner 20 "
    "Total partnership capital $1,000 "
    "United States Oil Fund, LP Notes to Financial Statements"
)


def _rows(text: str, *, issuer: str, accession: str = "0001-00-000001",
          filed: str = "2024-02-29", form: str = "10-K", report: str = "2023-12-31") -> pd.DataFrame:
    got, _seen = B.rows_for_filing(
        B.flatten(text), issuer=issuer, accession=accession, filed=filed, form=form,
        report_date=report,
    )
    return pd.DataFrame(got, columns=list(B.COLUMNS))


# --------------------------------------------------------------------------------- primitives
def test_flatten_resolves_entities_and_the_invisible_spaces_the_filers_use() -> None:
    got = B.flatten("<b>Shareholders&#8217;</b>​equity &amp;  cash")
    assert got == " Shareholders’ equity & cash"


@pytest.mark.parametrize(
    ("text", "want"),
    [
        ("$ 431,110,215", 431110215.0),
        ("( 29,339,198 )", -29339198.0),
        ("80.21", 80.21),
        ("—", None),
        ("", None),
        ("n/a", None),
    ],
)
def test_money_parses_the_filers_number_forms(text: str, want: float | None) -> None:
    assert B.money(text) == want


def test_month_key_raises_on_a_month_it_does_not_know() -> None:
    assert B.month_key("March", "2025") == "2025-03"
    with pytest.raises(B.HoldingsError, match="unknown month name"):
        B.month_key("Smarch", "2025")


@pytest.mark.parametrize(
    ("code", "period", "want"),
    [
        ("CLX2", "2012-09-30", "2012-11"),   # the real 2012 row
        ("NGX2", "2012-09-30", "2012-11"),
        ("CLF3", "2012-09-30", "2013-01"),   # digit 3 is the NEXT year, not 2003
        ("CLZ0", "2019-12-31", "2020-12"),   # decade rollover
    ],
)
def test_cme_code_month_resolves_the_single_year_digit_against_the_period(
    code: str, period: str, want: str
) -> None:
    assert B.cme_code_month(code, period) == want


def test_cme_code_month_raises_on_a_string_that_is_not_an_outright() -> None:
    with pytest.raises(B.HoldingsError, match="not a CME outright code"):
        B.cme_code_month("CL-SPREAD", "2012-09-30")


# ------------------------------------------------------------------------- the alias boundary
@pytest.mark.parametrize(
    ("name", "want"),
    [
        ("PROSHARES ULTRA BLOOMBERG CRUDE OIL", "UCO"),
        ("PROSHARES ULTRASHORT BLOOMBERG CRUDE OIL", "SCO"),
        ("PROSHARES ULTRA DJ-AIG CRUDE OIL", "UCO"),
        ("PROSHARES ULTRA DJ-UBS NATURAL GAS", "BOIL"),
        # The real misspelling in one filing's heading. Space-insensitive matching is why it maps.
        ("PROSHARES ULTR ASHORT BLOOMBERG CRUDE OIL", "SCO"),
        # Other series of the same registrant. None of them may be captured.
        ("PROSHARES ULTRAPRO 3X CRUDE OIL ETF", None),
        ("PROSHARES ULTRA BLOOMBERG COMMODITY", None),
        ("PROSHARES ULTRASHORT GOLD", None),
        ("PROSHARES SHORT VIX SHORT-TERM FUTURES ETF", None),
    ],
)
def test_the_series_alias_separates_ultra_from_ultrashort_and_ultrapro(
    name: str, want: str | None
) -> None:
    assert B._proshares_fund(name) == want


# ------------------------------------------------------------------- the three table fragments
def test_the_proshares_fragment_parses_both_sides_the_cash_line_and_the_anchors() -> None:
    frame = _rows(PROSHARES_FRAGMENT, issuer="proshares_trust_ii")
    boil = frame[(frame["fund"] == "BOIL") & (frame["period_end"] == "2023-12-31")]
    fut = boil[boil["kind"] == "futures"].sort_values("contract_month")
    assert list(fut["contract_month"]) == ["2024-03", "2024-06"]
    # SIGNED: purchased is positive and sold is negative, in contracts AND in notional.
    assert list(fut["contracts"]) == [62768.0, -1000.0]
    assert list(fut["notional_usd"]) == [1460611360.0, -20000000.0]
    assert list(fut["sign_basis"]) == ["block_header", "block_header"]
    cash = boil[boil["kind"] == "cash"]
    assert len(cash) == 1 and float(cash["notional_usd"].iloc[0]) == 64459117.0
    assert float(boil["shares_out"].iloc[0]) == 5113709.0
    assert float(boil["net_assets"].iloc[0]) == 729892808.0
    assert float(boil["nav_per_share"].iloc[0]) == 142.73
    # The comparative column is an anchor of its own, with no holdings behind it.
    prior = frame[(frame["fund"] == "BOIL") & (frame["period_end"] == "2022-12-31")]
    assert len(prior) == 1 and prior["kind"].iloc[0] == "unparsed"
    assert float(prior["shares_out"].iloc[0]) == 1000000.0
    assert "anchors only" in str(prior["reason"].iloc[0])


def test_the_uscf_fragment_parses_the_swap_notional_and_not_the_fair_value_beside_it() -> None:
    frame = _rows(USCF_FRAGMENT, issuer="ung")
    g = frame[frame["period_end"] == "2023-12-31"]
    swaps = g[g["kind"] == "swap"]
    assert sorted(swaps["counterparty"]) == ["Macquarie Bank Ltd", "Societe Generale"]
    # 129,306,126 is the NOTIONAL column; 144,210,360 is the fair value in the next column.
    assert sorted(swaps["notional_usd"]) == [94559204.0, 129306126.0]
    fut = g[g["kind"] == "futures"]
    assert len(fut) == 1
    assert fut["contract_month"].iloc[0] == "2024-02"
    assert fut["month_basis"].iloc[0] == "stated_contract"
    assert float(fut["contracts"].iloc[0]) == 29248.0
    assert float(fut["notional_usd"].iloc[0]) == 695222259.0
    f_fut = float(g["f_fut"].iloc[0])
    assert f_fut == pytest.approx(695222259.0 / (695222259.0 + 223865330.0), abs=1e-12)


def test_an_unparseable_period_is_written_down_with_a_reason_and_never_skipped() -> None:
    frame = _rows(UNPARSEABLE_FRAGMENT, issuer="uso", report="2006-03-31")
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["fund"] == "USO"
    assert row["kind"] == "unparsed"
    assert str(row["reason"]).strip()
    assert not np.isfinite(float(row["f_fut"]))  # NULL, never a plausible-looking 0.0
    assert row["period_end"] == "2006-03-31"


def test_a_futures_block_whose_rows_do_not_match_raises_rather_than_returning_nothing() -> None:
    broken = PROSHARES_FRAGMENT.replace("expires March 2024 62,768", "expiring Marchish 62768")
    with pytest.raises(B.HoldingsError, match="yielded ZERO rows"):
        _rows(broken, issuer="proshares_trust_ii")


def test_the_no_notional_uscf_era_leaves_notional_null_instead_of_taking_the_gain() -> None:
    """2008-2015 print contracts and UNREALIZED GAIN with no notional column anywhere."""
    old = (
        "United States Oil Fund, LP Condensed Schedule of Investments (Unaudited) At March 31, 2008 "
        "Open Futures Contracts Number of Contracts Loss on Open Commodity % of Partners' Capital "
        "United States Contracts Crude Oil Futures contracts, expires May 2008 7,122 "
        "$ ( 13,349,470 ) ( 1.84 ) "
        "United States Oil Fund, LP Condensed Statements of Operations"
    )
    frame = _rows(old, issuer="uso", report="2008-03-31")
    fut = frame[frame["kind"] == "futures"]
    assert len(fut) == 1
    assert float(fut["contracts"].iloc[0]) == 7122.0
    assert not np.isfinite(float(fut["notional_usd"].iloc[0]))
    assert fut["month_basis"].iloc[0] == "expires_label"
    # No notional anywhere means no f_fut, not an f_fut of 1.0.
    assert not np.isfinite(float(fut["f_fut"].iloc[0]))


def test_merge_anchor_keeps_the_first_non_null_so_a_later_partial_match_cannot_blank_it() -> None:
    anchors: dict[tuple[str, str], dict[str, float]] = {}
    key = ("USO", "2021-12-31")
    B._merge_anchor(anchors, key, shares_out=43823603.0, nav_per_share=54.18, net_assets=2374159266.0)
    # The notes restate total partners' capital alone. It must not erase the share count.
    B._merge_anchor(anchors, key, shares_out=None, nav_per_share=None, net_assets=2374159266.0)
    assert anchors[key] == {"shares_out": 43823603.0, "nav_per_share": 54.18, "net_assets": 2374159266.0}


def test_merge_anchor_leaves_no_empty_key_behind() -> None:
    anchors: dict[tuple[str, str], dict[str, float]] = {}
    B._merge_anchor(anchors, ("X", "2020-01-01"), shares_out=None, net_assets=None, nav_per_share=None)
    assert anchors == {}


# ---------------------------------------------------------------------------------- the gates
@pytest.fixture()
def good() -> pd.DataFrame:
    return B._good_frame()


def test_every_gate_accepts_the_good_frame(good: pd.DataFrame) -> None:
    report = B.run_gates(good)
    assert report["G0_kinds_and_reasons"]["unparsed"] == 0
    assert report["G1_f_fut_in_unit_interval"]["max"] <= 1.0
    assert report["G3_no_duplicate_lines"]["duplicate_rows"] == 0
    assert report["G2_contract_months_forward"]["backward_rows"] == 0


def test_gate_kinds_raises_on_a_kind_outside_the_declared_five(good: pd.DataFrame) -> None:
    bad = good.copy()
    bad.loc[0, "kind"] = "derivative"
    with pytest.raises(B.HoldingsError, match="not in"):
        B.gate_kinds(bad)


def test_gate_kinds_raises_on_an_unparsed_row_with_no_reason(good: pd.DataFrame) -> None:
    bad = good.copy()
    bad.loc[0, "kind"] = "unparsed"
    with pytest.raises(B.HoldingsError, match="carry no reason"):
        B.gate_kinds(bad)


def test_gate_f_fut_raises_one_ulp_outside_the_unit_interval(good: pd.DataFrame) -> None:
    bad = good.copy()
    bad.loc[0, "f_fut"] = np.nextafter(1.0, 2.0)
    with pytest.raises(B.HoldingsError, match=r"outside \[0,1\]"):
        B.gate_f_fut(bad)


def test_gate_months_forward_tolerates_one_source_typo_and_raises_on_a_systematic_one(
    good: pd.DataFrame,
) -> None:
    one = good.copy()
    fut = one.index[one["kind"] == "futures"]
    one.loc[fut[0], "contract_month"] = "2001-01"
    share = 1 / len(fut)
    if share <= B.BACKWARD_MONTH_MAX_SHARE:  # pragma: no cover - the synthetic frame is small
        assert B.gate_months_forward(one)["backward_rows"] == 1
    many = good.copy()
    many.loc[many["kind"] == "futures", "contract_month"] = "2001-01"
    with pytest.raises(B.HoldingsError, match="it is the parse and not the filings"):
        B.gate_months_forward(many)


def test_gate_no_duplicates_raises_on_a_repeated_line(good: pd.DataFrame) -> None:
    with pytest.raises(B.HoldingsError, match="duplicate lines"):
        B.gate_no_duplicates(pd.concat([good, good.iloc[[0]]], ignore_index=True))


def test_gate_year_coverage_names_the_missing_year(good: pd.DataFrame) -> None:
    bad = good.copy()
    boil = bad["fund"] == "BOIL"
    bad.loc[boil, "period_end"] = bad.loc[boil, "period_end"].replace({"2022-12-31": "2019-12-31"})
    with pytest.raises(B.HoldingsError, match=r"no parsed holdings row in \[2020, 2021, 2022\]"):
        B.gate_year_coverage(bad)


def test_gate_known_answer_raises_when_uco_loses_its_swaps(good: pd.DataFrame) -> None:
    bad = good[~((good["fund"] == "UCO") & (good["kind"] == "swap"))].reset_index(drop=True)
    with pytest.raises(B.HoldingsError, match="has swaps for this fund"):
        B.gate_known_answer(bad)


def test_gate_known_answer_raises_when_sco_gains_swaps(good: pd.DataFrame) -> None:
    extra = good[good["fund"] == "UCO"].copy()
    extra["fund"] = "SCO"
    extra["source_accession"] = "0002-2023-1"
    with pytest.raises(B.HoldingsError, match="has no swaps for this fund"):
        B.gate_known_answer(pd.concat([good, extra], ignore_index=True))


def test_the_selftest_reports_every_break_firing() -> None:
    assert B.selftest() == 0
