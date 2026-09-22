"""Unit tests for the D619 fund panel, the holdings parse, the fund-facts validator, and the
point-in-time options-OI join.

ONE NUMBERED DEPOSIT TEST IS CLAIMED HERE — **ledger 50**, `SETTLEMENT_FLOW_LEDGER_PREREG.md`
§12 line 756, verbatim:

    50. Options open interest by strike is joined point-in-time (the prior day's published
        values only).

`test_ledger_50_options_oi_is_joined_at_the_prior_days_publication` is the claim. **It runs on a
SYNTHETIC open-interest table, because no CL or NG options open interest exists on this disk**:
both Databento pulls on disk used `{root}.FUT` parents, and a full decode of the 2026 definition
file (9,138,836 records) shows `security_type {FUT: 9,138,835, OOF: 1}`. D619 quotes what the
real pull would cost and downloads nothing. The RULE is therefore what is tested, on data built
to make the rule's boundary visible, and the test says so rather than implying a fixture.

WHAT THE REST OF THE FILE DEFENDS
----------------------------------
Everything here has a silent failure mode, which is the only reason it is worth testing:

  * a column inserted upstream shifts `Shares Outstanding (000)` into `Assets Under Management`
    and the series stays plausible — the header assertion and the AUM identity are what notice;
  * a seed-row rule chosen from a guess rather than the data drops 62% of BOIL (`nav > 1e4`)
    while looking principled;
  * a holdings page whose table stops being server-rendered parses to an empty list, and an
    empty list divides to a clean 0.0 instead of raising;
  * a fund fact recorded with `status: "unknown"` and a value beside it is an inference wearing
    a provenance field, which is what deposit §P8a line 328 ("Do not assume.") forbids;
  * and a point-in-time join that is off by one session is look-ahead that no number reveals.

Every guard is shown to ACCEPT the good case FIRST and then to RAISE on a break aimed at the
scalar it compares. No return is computed and no fixture outside `data/` is read.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
FACTS_JSON = REPO / "data" / "fund_facts" / "fund_facts.json"


def _script(name: str) -> Any:
    """Load a D619 script as a module. Safe by inspection: none of the three has a module body
    that fetches, writes or installs anything — the work is behind `main()` and a `__main__`
    guard, which `tests/unit/test_nothing_outside_tests_is_collectable.py` also asserts."""
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def panel_mod() -> Any:
    return _script("build_fund_panel")


@pytest.fixture(scope="module")
def holdings_mod() -> Any:
    return _script("fetch_fund_holdings")


@pytest.fixture(scope="module")
def facts_mod() -> Any:
    return _script("fetch_fund_facts")


# ===================================================================== the panel's parse + gates
def _good_panel(mod: Any) -> pd.DataFrame:
    return mod._synthetic_panel()


def test_good_panel_passes_every_gate(panel_mod: Any) -> None:
    """The base case, first. A break is only evidence if the unbroken case passes."""
    report = panel_mod.run_gates(_good_panel(panel_mod))
    assert set(report) == {n for n, _ in panel_mod.GATES}
    assert report["G1_aum_identity"]["BOIL"]["share_within_rounding"] == 1.0
    assert report["G4_four_funds"]["funds"] == list(panel_mod.FUNDS)


def test_aum_identity_raises_when_a_column_is_shifted(panel_mod: Any) -> None:
    """The failure this gate exists for: shares and AUM swapped. The series still looks like a
    series; only the identity notices."""
    bad = _good_panel(panel_mod)
    bad["shares_out"], bad["aum"] = bad["aum"].copy(), bad["shares_out"].copy()
    with pytest.raises(panel_mod.PanelError, match="G1"):
        panel_mod.gate_aum_identity(bad)


def test_aum_identity_tolerance_is_half_the_published_rounding_unit(panel_mod: Any) -> None:
    """A residual of exactly five shares passes and six fails — the boundary, not a vibe.

    The source publishes shares to 0.01 thousands, so ten shares is the unit and five is half
    of it. `nav` is 1.0 here so the residual in dollars IS the residual in shares."""
    base = _good_panel(panel_mod)
    ok = base.copy()
    ok["nav"] = 1.0
    ok["shares_out"] = 1_000_000.0
    ok["aum"] = 1_000_000.0 + 5.0
    panel_mod.gate_aum_identity(ok)  # five shares: inside half a unit
    bad = ok.copy()
    bad["aum"] = 1_000_000.0 + 6.0
    with pytest.raises(panel_mod.PanelError, match="G1"):
        panel_mod.gate_aum_identity(bad)


def test_gates_raise_on_unsorted_duplicate_and_missing_fund(panel_mod: Any) -> None:
    good = _good_panel(panel_mod)
    unsorted_ = good.copy()
    unsorted_.loc[0, "date"], unsorted_.loc[1, "date"] = unsorted_.loc[1, "date"], unsorted_.loc[0, "date"]
    with pytest.raises(panel_mod.PanelError, match="G2"):
        panel_mod.gate_dates_increasing(unsorted_)
    dup = good.copy()
    dup.loc[1, "date"] = dup.loc[0, "date"]
    with pytest.raises(panel_mod.PanelError, match="G3"):
        panel_mod.gate_no_duplicates(dup)
    with pytest.raises(panel_mod.PanelError, match="G4"):
        panel_mod.gate_four_funds(good[good["fund"] != "SCO"].reset_index(drop=True))


def test_read_nav_csv_raises_on_a_changed_header(panel_mod: Any, tmp_path: Path) -> None:
    p = tmp_path / "x.csv"
    p.write_text("Date,Ticker,NAV\n09/18/2026,BOIL,20.0\n", encoding="utf-8", newline="\n")
    with pytest.raises(panel_mod.PanelError, match="header is"):
        panel_mod.read_nav_csv(p, "BOIL")


def test_read_nav_csv_raises_when_the_ticker_is_not_the_fund(panel_mod: Any, tmp_path: Path) -> None:
    """A URL template that silently returns another fund's file is the failure here. The header
    would be identical and the numbers plausible."""
    p = tmp_path / "y.csv"
    p.write_text(
        ",".join(panel_mod.SOURCE_COLUMNS) + "\n"
        "09/18/2026,ProShares UltraShort Bloomberg Natural Gas,KOLD,1,1,0,0,1,1000\n",
        encoding="utf-8", newline="\n",
    )
    with pytest.raises(panel_mod.PanelError, match="Ticker column"):
        panel_mod.read_nav_csv(p, "BOIL")


def test_seed_rule_selects_zero_share_rows_and_not_large_nav_rows(panel_mod: Any) -> None:
    """The rule the data supports, and the one it refuses, side by side.

    `nav > 1e4` would take the second row here — an ordinary row of a back-adjusted series —
    and `shares_out == 0` takes only the first."""
    frame = pd.DataFrame(
        {
            "fund": ["BOIL"] * 3,
            "nav": [8_000_000.0, 50_000.0, 20.0],
            "shares_out": [0.0, 10.0, 19_511_140.0],
        }
    )
    assert panel_mod.seed_rows(frame).tolist() == [True, False, False]


def test_split_detector_finds_a_planted_split_and_reports_the_inverse_match(panel_mod: Any) -> None:
    """A known-answer case FIRST: the detector must be able to fire, or the empty list it
    returns on the real series would mean nothing."""
    frame = pd.DataFrame(
        {
            "fund": ["X"] * 3,
            "date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
            "nav": [10.0, 100.0, 101.0],
            "prior_nav": [10.0, 100.0, 100.0],   # the split is restated INTO prior_nav on day 2
            "shares_out": [1_000_000.0, 100_000.0, 100_000.0],
            "nav_change_pct": [0.0, 0.0, 1.0],
        }
    )
    found = panel_mod.split_candidates(frame)
    assert len(found) == 1, found
    assert found[0]["date"] == "2020-01-03"
    assert found[0]["nav_ratio"] == pytest.approx(10.0), "a 1-for-10 reverse split multiplies NAV by 10"
    assert found[0]["shares_ratio"] == pytest.approx(0.1), "and divides the share count by 10"
    assert found[0]["inverse_match"] is True


def test_split_detector_is_silent_on_a_clean_chain(panel_mod: Any) -> None:
    frame = pd.DataFrame(
        {
            "fund": ["X"] * 3,
            "date": pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"]),
            "nav": [10.0, 10.1, 10.2],
            "prior_nav": [10.0, 10.0, 10.1],
            "nav_change_pct": [0.0, 1.0, 0.990099],
            "shares_out": [1e6, 1e6, 1e6],
        }
    )
    assert panel_mod.split_candidates(frame) == []
    checks = panel_mod.carry_check(frame)
    assert checks["max_carry_dev"] < 1e-9
    assert checks["max_pct_dev"] < 1e-6


# ==================================================================== the holdings parse (§3.2)
def test_live_shaped_page_parses_to_three_kinds(holdings_mod: Any) -> None:
    rows = holdings_mod.parse_holdings(holdings_mod._GOOD_PAGE, "SYN")
    assert [r.kind for r in rows] == ["futures", "swap", "cash"]
    assert rows[0].holdings_as_of == "2026-09-18"
    assert rows[0].contracts == 25_857.0
    assert rows[0].notional_usd == 786_828_510.0


def test_contract_month_parse_on_the_live_description(holdings_mod: Any) -> None:
    """`NOV26 -> 2026-11`, proved on the string the live BOIL row actually carries, and shown
    not to match a word that merely starts with a month."""
    assert holdings_mod.contract_month("NATURAL GAS FUTR NOV26") == "2026-11"
    assert holdings_mod.contract_month("WTI CRUDE FUTURE DEC27") == "2027-12"
    assert holdings_mod.contract_month("PROSHARES GENIUS MNY MKT ETF") is None
    assert holdings_mod.contract_month("NOVA26 SOMETHING") is None


def test_a_swap_line_surfaces_as_kind_swap(holdings_mod: Any) -> None:
    """Deposit §3.2 line 89 is the futures/swap split, so the swap branch must be exercised.
    BOIL and KOLD carry no swap line, and UCO carries four — this pins the classifier on both
    the synthetic row and the live UCO spelling."""
    assert holdings_mod.classify("NAT GAS SWAP NOV26") == "swap"
    assert holdings_mod.classify("BLOOMBERG WTI CRUDE OIL BALANCED SWAP - SG") == "swap"
    assert holdings_mod.classify("WTI CRUDE FUTURE DEC26") == "futures"
    assert holdings_mod.classify("PROSHARES GENIUS MNY MKT ETF") == "mmf"
    assert holdings_mod.classify("NET OTHER ASSETS / CASH") == "cash"


def test_swap_beats_futures_when_a_description_names_both(holdings_mod: Any) -> None:
    """A swap ON a future is swap notional for §3.2's purpose, so the order of the branches is
    load-bearing and is pinned here rather than left to the reading order."""
    assert holdings_mod.classify("NAT GAS FUTR SWAP NOV26") == "swap"


def test_f_fut_and_the_derivative_split_are_different_numbers(holdings_mod: Any) -> None:
    rows = holdings_mod.parse_holdings(holdings_mod._GOOD_PAGE, "SYN")
    # The synthetic page carries a swap line the live BOIL page does not, so the denominators
    # differ: f_fut divides by TOTAL exposure (futures + swap + cash) and the derivative split
    # divides by the derivative book alone.
    assert holdings_mod.f_fut(rows) == pytest.approx(
        786_828_510 / (786_828_510 + 100_000_000 + 393_480_034.95)
    )
    assert holdings_mod.f_fut_derivatives(rows) == pytest.approx(786_828_510 / 886_828_510)


def test_derivative_split_is_none_when_there_is_no_derivative(holdings_mod: Any) -> None:
    """None, not 0.0. No split is not a split of zero."""
    cash_only = [
        holdings_mod.HoldingRow("2026-09-18", "SYN", "NET OTHER ASSETS / CASH", None, None, None, 1.0, "cash")
    ]
    assert holdings_mod.f_fut_derivatives(cash_only) is None


def test_parse_raises_on_a_page_with_no_futures_row(holdings_mod: Any) -> None:
    broken = (holdings_mod._GOOD_PAGE
              .replace("NATURAL GAS FUTR NOV26", "NET OTHER ASSETS / CASH")
              .replace("NAT GAS SWAP NOV26", "NET OTHER ASSETS / CASH"))
    with pytest.raises(holdings_mod.HoldingsParseError, match="no row classifies as futures"):
        holdings_mod.parse_holdings(broken, "SYN")


def test_parse_raises_on_a_missing_as_of_date(holdings_mod: Any) -> None:
    broken = holdings_mod._GOOD_PAGE.replace("as of 9/18/2026", "as at some point")
    with pytest.raises(holdings_mod.HoldingsParseError, match="as of"):
        holdings_mod.parse_holdings(broken, "SYN")


def test_parse_raises_on_the_cms_json_response(holdings_mod: Any) -> None:
    """The real failure mode, not a hypothetical one: `www.proshares.com` content-negotiates on
    `Accept`, and the recorder's default header returns 7.8 KB of CMS JSON with no holdings."""
    with pytest.raises(holdings_mod.HoldingsParseError, match="fund-detail-table-holdings"):
        holdings_mod.parse_holdings('{"fundSymbol":"BOIL","contentType":["Page"]}', "BOIL")


def test_number_parser_reads_the_page_spellings_and_raises_on_prose(holdings_mod: Any) -> None:
    assert holdings_mod._number("786,828,510") == 786_828_510.0
    assert holdings_mod._number("$393,480,034.95") == 393_480_034.95
    assert holdings_mod._number("(1,234)") == -1234.0
    assert holdings_mod._number("--") is None
    with pytest.raises(holdings_mod.HoldingsParseError):
        holdings_mod._number("about a lot")


# ======================================================== deposit ledger test 50: the OI join
def _oi_table(stamps: list[tuple[str, float, int]]) -> pd.DataFrame:
    """(ET wall clock, strike, open interest) -> the table `usable_oi` takes."""
    return pd.DataFrame(
        {
            "ts_event": np.array(
                [pd.Timestamp(s, tz="US/Eastern").value for s, _, _ in stamps], dtype="int64"
            ),
            "strike": [k for _, k, _ in stamps],
            "oi": [v for _, _, v in stamps],
        }
    )


def test_ledger_50_options_oi_is_joined_at_the_prior_days_publication(panel_mod: Any) -> None:
    """**Deposit ledger test 50** (§12 line 756): *"Options open interest by strike is joined
    point-in-time (the prior day's published values only)."*

    SYNTHETIC TABLE, and deliberately so: no CL or NG options open interest exists on this disk
    (both pulls used `{root}.FUT` parents; the 2026 definition file decodes to 9,138,835 FUT and
    one OOF record). D619 quotes the real pull and downloads nothing, so what is tested here is
    the RULE, on four publications placed to straddle its two boundaries.

    The four, against a target session of 2026-09-18:

      A  2026-09-16 17:00 ET  strike 3.0  — two sessions back: usable, and superseded by B
      B  2026-09-17 17:00 ET  strike 3.0  — the prior evening: THE value the join must return
      C  2026-09-18 09:00 ET  strike 4.0  — D497 would allow it (before the 10:00 entry) and
                                            **test 50 does not**: it is not the prior day's
      D  2026-09-18 11:00 ET  strike 5.0  — after the entry: excluded under either rule
    """
    table = _oi_table(
        [
            ("2026-09-16 17:00", 3.0, 100),
            ("2026-09-17 17:00", 3.0, 111),
            ("2026-09-18 09:00", 4.0, 222),
            ("2026-09-18 11:00", 5.0, 333),
        ]
    )
    cal = ["2026-09-16", "2026-09-17", "2026-09-18", "2026-09-21"]
    got = panel_mod.usable_oi(table, "2026-09-18", calendar=cal)

    assert got["strike"].tolist() == [3.0], "only the prior day's strike may survive"
    assert int(got["oi"].iloc[0]) == 111, "the FRESHEST prior publication, not the first"
    # B was published at 17:00 ET on the 17th, i.e. AFTER that session's 10:00 entry, so D497
    # makes it first usable on the 18th -- which is the target session. It survives on the
    # deposit's clause because its PUBLICATION day, the 17th, is a prior day.
    assert got["first_usable_session"].tolist() == ["2026-09-18"]
    assert 4.0 not in set(got["strike"]), "a same-session 09:00 publication is not prior-day"
    assert 5.0 not in set(got["strike"]), "a publication after the entry cannot be used at all"


def test_ledger_50_join_moves_forward_with_the_session(panel_mod: Any) -> None:
    """The same table read one session later: the 09:00 and 11:00 publications of the 18th are
    now prior-day and both appear. A join that ignored the session would give one answer."""
    table = _oi_table(
        [
            ("2026-09-17 17:00", 3.0, 111),
            ("2026-09-18 09:00", 4.0, 222),
            ("2026-09-18 11:00", 5.0, 333),
        ]
    )
    cal = ["2026-09-17", "2026-09-18", "2026-09-21"]
    got = panel_mod.usable_oi(table, "2026-09-21", calendar=cal)
    assert got["strike"].tolist() == [3.0, 4.0, 5.0]


def test_ledger_50_nothing_published_yet_is_an_empty_frame_not_an_error(panel_mod: Any) -> None:
    table = _oi_table([("2026-09-18 09:00", 4.0, 222)])
    got = panel_mod.usable_oi(table, "2026-09-18", calendar=["2026-09-17", "2026-09-18"])
    assert len(got) == 0


def test_usable_oi_guards_fire(panel_mod: Any) -> None:
    ts = np.array([pd.Timestamp("2026-09-17 17:00", tz="US/Eastern").value], dtype="int64")
    with pytest.raises(panel_mod.PanelError, match="missing"):
        panel_mod.usable_oi(pd.DataFrame({"ts_event": ts, "oi": [1]}), "2026-09-18")
    with pytest.raises(panel_mod.PanelError, match="int64"):
        panel_mod.usable_oi(
            pd.DataFrame({"ts_event": ts.astype(float), "strike": [1.0], "oi": [1]}), "2026-09-18"
        )
    with pytest.raises(panel_mod.PanelError, match="not in the calendar"):
        panel_mod.usable_oi(
            pd.DataFrame({"ts_event": ts, "strike": [1.0], "oi": [1]}),
            "2026-09-18", calendar=["2026-09-17"],
        )
    with pytest.raises(panel_mod.PanelError, match="ISO date"):
        panel_mod.usable_oi(pd.DataFrame({"ts_event": ts, "strike": [1.0], "oi": [1]}), "18/09/2026")


def test_the_d497_rule_is_imported_and_not_restated(panel_mod: Any) -> None:
    """One definition of the causality rule in this repository. If `build_fut_open_interest.py`
    stops carrying `ENTRY_MIN` or `usable_session` at top level, this raises rather than the
    join quietly falling back to a local copy — because there is no local copy."""
    fn, entry_min = panel_mod._oi_rule()
    assert entry_min == 10 * 60, "D497's entry is 10:00 ET; a change there changes this join"
    cal = np.array(["2026-09-17", "2026-09-18"], dtype=object)
    ts = np.array([pd.Timestamp("2026-09-17 09:00", tz="US/Eastern").value], dtype="int64")
    assert list(fn(ts, cal)) == ["2026-09-17"]


# ================================================================= the fund-facts validator
def _minimal_facts() -> dict[str, Any]:
    fact = {
        "value": "x", "source_url": "https://example.invalid/a.htm", "accession": "0001-26-1",
        "section": "Item 1", "quote": "a short quote", "fetched_at": "2026-09-21T23:24:07Z",
        "status": "sourced",
    }
    facts = {name: dict(fact) for name in (
        "futures_swap_split", "creation_cutoff_and_lag", "rebalance_execution",
        "roll_schedule", "expense_ratio")}
    facts["creation_cutoff_and_lag"]["lag_c"] = 0
    return {
        "funds": {"BOIL": {"facts": facts}},
        "p9": [{"product": "HNU", "listing": "TSX", "issuer_site": "https://example.invalid",
                "status": "not_sourced", "question": "Q14"}],
    }


def test_minimal_facts_document_validates(facts_mod: Any) -> None:
    counts = facts_mod.validate_fund_facts(_minimal_facts())
    assert counts == {"funds": 1, "sourced": 5, "unknown": 0, "p9_not_sourced": 1}


def test_validator_raises_on_a_missing_required_fact(facts_mod: Any) -> None:
    doc = _minimal_facts()
    del doc["funds"]["BOIL"]["facts"]["roll_schedule"]
    with pytest.raises(facts_mod.FundFactsError, match="missing fact"):
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_on_a_missing_provenance_key(facts_mod: Any) -> None:
    doc = _minimal_facts()
    del doc["funds"]["BOIL"]["facts"]["expense_ratio"]["accession"]
    with pytest.raises(facts_mod.FundFactsError, match="missing key"):
        facts_mod.validate_fund_facts(doc)


@pytest.mark.parametrize("lag", [2, -1, 0.5, "0"])
def test_validator_raises_on_an_out_of_range_lag_c(facts_mod: Any, lag: Any) -> None:
    """Deposit §3.2 line 90: *"the lag parameter `lag_c` ∈ {0, 1}"*. `"0"` is included because a
    string that looks like the right number is the realistic way this breaks."""
    doc = _minimal_facts()
    doc["funds"]["BOIL"]["facts"]["creation_cutoff_and_lag"]["lag_c"] = lag
    with pytest.raises(facts_mod.FundFactsError, match="lag_c"):
        facts_mod.validate_fund_facts(doc)


def test_validator_accepts_lag_c_of_one_and_of_null(facts_mod: Any) -> None:
    for lag in (1, None):
        doc = _minimal_facts()
        doc["funds"]["BOIL"]["facts"]["creation_cutoff_and_lag"]["lag_c"] = lag
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_when_unknown_carries_a_value(facts_mod: Any) -> None:
    """The one that matters most: §P8a line 328, *"Do not assume."* A value beside
    `status: "unknown"` is an inference with a provenance field bolted on."""
    doc = _minimal_facts()
    doc["funds"]["BOIL"]["facts"]["roll_schedule"].update(status="unknown", value="four days")
    with pytest.raises(facts_mod.FundFactsError, match="Do not assume"):
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_on_sourced_with_no_source(facts_mod: Any) -> None:
    doc = _minimal_facts()
    doc["funds"]["BOIL"]["facts"]["roll_schedule"]["source_url"] = ""
    with pytest.raises(facts_mod.FundFactsError, match="empty source_url"):
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_on_a_quote_over_fifteen_words(facts_mod: Any) -> None:
    doc = _minimal_facts()
    doc["funds"]["BOIL"]["facts"]["expense_ratio"]["quote"] = " ".join(["w"] * 16)
    with pytest.raises(facts_mod.FundFactsError, match="16 words"):
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_on_lag_c_in_the_wrong_place(facts_mod: Any) -> None:
    doc = _minimal_facts()
    doc["funds"]["BOIL"]["facts"]["expense_ratio"]["lag_c"] = 0
    with pytest.raises(facts_mod.FundFactsError, match="belongs only"):
        facts_mod.validate_fund_facts(doc)


def test_validator_raises_on_a_p9_row_claiming_to_be_sourced(facts_mod: Any) -> None:
    doc = _minimal_facts()
    doc["p9"][0]["status"] = "sourced"
    with pytest.raises(facts_mod.FundFactsError, match="not_sourced"):
        facts_mod.validate_fund_facts(doc)


def test_the_committed_fund_facts_file_validates(facts_mod: Any) -> None:
    """The real document, with the counts D619 reports. A fact silently losing its provenance
    later turns this red rather than leaving `SOURCES.md` quoting a file that no longer says it."""
    counts = facts_mod.validate_fund_facts(json.loads(FACTS_JSON.read_text(encoding="utf-8")))
    assert counts == {"funds": 6, "sourced": 30, "unknown": 10, "p9_not_sourced": 8}


def test_every_lag_c_in_the_committed_file_is_zero(facts_mod: Any) -> None:
    """All six funds transact creations the same day (deposit §3.2 line 90). Recorded as a test
    because it is the INPUT to the deposit's execution-day-lag item — which another file claims —
    and a study that assumes `lag_c = 1` is off by a session on every one of the six."""
    doc = json.loads(FACTS_JSON.read_text(encoding="utf-8"))
    lags = {f: e["facts"]["creation_cutoff_and_lag"]["lag_c"] for f, e in doc["funds"].items()}
    assert lags == {"BOIL": 0, "KOLD": 0, "UCO": 0, "SCO": 0, "UNG": 0, "USO": 0}


def test_the_sec_user_agent_is_reused_and_carries_no_personal_address(facts_mod: Any) -> None:
    """The SEC edge requires an email-shaped token in the User-Agent. It must be the project
    mailbox and never the principal's own address, and the string must be the ONE this
    repository already sends — read out of `scripts/d331_edgar_deals.py` rather than retyped."""
    d331 = (REPO / "scripts" / "d331_edgar_deals.py").read_text(encoding="utf-8")
    assert f'USER_AGENT = "{facts_mod.USER_AGENT}"' in d331
    assert "@" in facts_mod.USER_AGENT
    assert "gmail" not in facts_mod.USER_AGENT.lower()
    assert facts_mod.MAX_RPS == 8.0
    assert facts_mod.MIN_INTERVAL >= 1.0 / facts_mod.MAX_RPS
