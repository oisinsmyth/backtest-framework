"""Gates on the CFTC Commitments of Traders fixture.

Offline and deterministic: every test reads the committed artifacts, none touches
the network. The live-API checks live in `fetch_cftc_cot.py --probe`.

WHAT THESE TESTS ARE ACTUALLY DEFENDING

The COT fetcher's failure modes are all SILENT. A wrong contract code returns a
full, plausible, well-formed series for the wrong market. A renamed field yields
empty columns rather than an error. A study keyed on `report_date` instead of
`release_date_nominal` is look-ahead by three days and looks fine. So the tests
below pin the specific things that would otherwise go wrong quietly.
"""

from __future__ import annotations

import csv
import gzip
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
META = REPO / "data" / "fixtures" / "cftc_cot_raw.meta.json"
MAP = REPO / "data" / "fixtures" / "cftc_cot_map.json"


def _load_fetcher():
    path = REPO / "scripts" / "fetch_cftc_cot.py"
    spec = importlib.util.spec_from_file_location("fetch_cftc_cot", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fetch_cftc_cot"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load_fetcher()


@pytest.fixture(scope="module")
def meta():
    if not META.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("fixture not built")
    return json.loads(META.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def mapping():
    if not MAP.exists():  # pragma: no cover
        pytest.skip("map not built")
    return json.loads(MAP.read_text(encoding="utf-8"))["symbols"]


@pytest.fixture(scope="module")
def rows():
    if not FIXTURE.exists():  # pragma: no cover
        pytest.skip("fixture not built")
    with gzip.open(FIXTURE, "rt", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------- the provider


def test_the_providers_own_typos_are_pinned_verbatim(mod):
    """`swap__positions_short_all` has a DOUBLE underscore and
    `noncomm_postions_spread_all` says "postions". Both are real, both were read
    off a live record, and both look like defects somebody will helpfully fix.
    If the CFTC ever corrects them our columns go silently empty, so the exact
    spellings are asserted here rather than trusted."""
    flat = {f for fam in mod.CATEGORIES.values() for c in fam for f in c[1:] if f}
    assert "swap__positions_short_all" in flat
    assert "swap__positions_spread_all" in flat
    assert "noncomm_postions_spread_all" in flat
    # And the plausible "corrected" spellings must NOT be what we ask for.
    assert "swap_positions_short_all" not in flat
    assert "noncomm_positions_spread_all" not in flat


def test_only_futures_only_datasets_are_used(mod):
    """The futures-and-options COMBINED datasets exist and would silently change
    what `open_interest` means. Named here so a future edit has to be deliberate."""
    assert set(mod.DATASETS.values()) == {"6dca-aqww", "72hh-3qpy", "gpe5-46if"}
    for combined in ("jun7-fc8e", "kh3c-gbw2", "yw9f-hn96"):
        assert combined not in mod.DATASETS.values()


# ------------------------------------------------------------ the symbol map


def test_every_requested_symbol_resolved_to_exactly_one_code(mod, mapping, meta):
    assert set(mapping) == set(mod.SYMBOLS)
    assert meta["gates"]["every_symbol_resolved"] is True
    assert meta["gates"]["unresolved_symbols"]["failures"] == []
    codes = [v["code"] for v in mapping.values()]
    assert len(codes) == len(set(codes)), "two symbols share a contract code"


def test_crude_oil_resolved_to_wti_light_sweet_and_not_one_of_the_other_six(mapping):
    """`%CRUDE OIL%` matches SEVEN contracts. Six of them are the wrong market and
    every one would have returned a full, plausible, entirely misleading series."""
    assert mapping["CL"]["code"] == "067411"
    assert mapping["CL"]["contract_name"] == "CRUDE OIL, LIGHT SWEET-WTI"
    for wrong in ("06741Q", "067655", "06765A", "06765I", "06765G", "067DU1"):
        assert mapping["CL"]["code"] != wrong


def test_natural_gas_resolved_despite_the_abbreviation_trap(mapping, mod):
    """The nastier of the two traps: the CFTC abbreviates, so `%NATURAL GAS%`
    does not match the main Henry Hub contract AT ALL. It returns only
    'E-MINI NATURAL GAS' and a San Juan index -- two plausible wrong answers and
    no right one. The liquid NYMEX contract is 'NAT GAS NYME'."""
    assert mapping["NG"]["code"] == "023651"
    assert mapping["NG"]["contract_name"] == "NAT GAS NYME"
    assert "NAT GAS" in mod.SYMBOLS["NG"][1]


def test_the_micro_contracts_are_present_with_their_own_codes(mapping):
    """The finding that makes this fixture worth more than rung 1: the CFTC
    reports micros separately, so the retail/institutional split the proposal
    costs at $14.28 of minute bars is directly observable here for nothing."""
    for sym, code in [("MES", "13874U"), ("MNQ", "209747"), ("M2K", "239747"),
                      ("MYM", "124608"), ("MGC", "088695"), ("MSI", "084694"),
                      ("MHG", "085699")]:
        assert mapping[sym]["code"] == code, sym
        assert "MICRO" in mapping[sym]["contract_name"].upper()
    # Each micro must differ from its full-size sibling, or the pair is degenerate.
    for micro, full in [("MES", "ES"), ("MNQ", "NQ"), ("M2K", "RTY"),
                        ("MYM", "YM"), ("MGC", "GC"), ("MSI", "SI"), ("MHG", "HG")]:
        assert mapping[micro]["code"] != mapping[full]["code"]


# ---------------------------------------------------------------- the fixture


def test_the_open_interest_identity_holds_on_every_checked_row(meta):
    """OI == sum(long) + sum(spread) == sum(short) + sum(spread). A spread
    position is one long AND one short held by the same trader, so it is inside
    open interest and outside the directional columns -- checking `sum(long)`
    alone fails on 94% of rows, which is how this gate was found to be wrong the
    first time. Requiring BOTH sides is what proves no column was transposed."""
    ident = meta["gates"]["open_interest_identity"]
    assert ident["failures"] == []
    assert ident["checked"] > 50_000
    assert ident["rate"] == 1.0, (
        f"identity held on {ident['passed']}/{ident['checked']}"
    )


def test_no_duplicate_reports(meta):
    assert meta["gates"]["no_duplicate_report_rows"] is True
    assert meta["gates"]["duplicate_rows_dropped"] == 0


def test_every_row_carries_its_family_so_taxonomies_cannot_be_pooled(rows, mod):
    """The three reports use DIFFERENT trader taxonomies. A financial contract has
    no producer-merchant and a physical has no asset-manager; pooling them would
    average categories that do not mean the same thing."""
    families = {r["family"] for r in rows}
    assert families == set(mod.DATASETS)
    by_family = {}
    for r in rows:
        by_family.setdefault(r["family"], set()).add(r["category"])
    for family, cats in by_family.items():
        expected = {c[0] for c in mod.CATEGORIES[family]}
        assert cats == expected, family
    # And the taxonomies genuinely differ, or the guard would be pointless.
    assert by_family["tff"] != by_family["disaggregated"]
    assert "asset_manager" in by_family["tff"]
    assert "producer_merchant" in by_family["disaggregated"]


def test_release_date_is_the_friday_of_the_reports_week(rows, mod):
    """Keying a study on `report_date` reads Tuesday's positions on Tuesday and is
    three days of look-ahead -- exactly what R9 forbids of a conditioning
    variable. The fixture carries the release date so a study can key on it.

    It is the FRIDAY OF THE WEEK, not a flat +3 days. That distinction is load
    bearing: the survey day shifts on holidays, and a flat +3 from the Wednesday
    report of 2007-01-03 would land the release on a Saturday."""
    checked = 0
    for r in rows:
        if not r["release_date_nominal"]:
            continue
        rd = date.fromisoformat(r["report_date"])
        rel = date.fromisoformat(r["release_date_nominal"])
        assert rel.weekday() == 4, f"{r['report_date']} -> {rel} is not a Friday"
        # STRICTLY after: a report cannot be published before it is surveyed, and
        # a Friday-dated report would otherwise release on itself -- zero lag,
        # which is look-ahead by construction.
        assert timedelta(days=1) <= rel - rd <= timedelta(days=7)
        checked += 1
    assert checked > 100_000


def test_report_dates_are_tuesdays_once_the_schedule_existed(rows, mod):
    """MEASURED, and it is why the release convention is week-based. From 1993 the
    survey day is Tuesday on 98-100% of weeks; the rest are holiday shifts to
    Monday or Wednesday. BEFORE 1993 there was no weekly Tuesday schedule at all
    -- 1986 is 46.8% Friday -- which is why those rows carry no release date."""
    # Four Friday reports survive after 1993, all year-end or holiday schedule
    # anomalies in the CFTC's own history. Pinned by name rather than tolerated by
    # loosening the assertion, so a FIFTH one fails loudly.
    KNOWN_FRIDAY_REPORTS = {"1997-12-19", "2001-12-21", "2001-12-28", "2003-02-14"}
    odd = {r["report_date"] for r in rows
           if r["report_date"] >= mod.TUESDAY_CONVENTION_FROM
           and date.fromisoformat(r["report_date"]).weekday() not in (0, 1, 2)}
    assert odd == KNOWN_FRIDAY_REPORTS, f"unexpected report weekday: {odd}"

    modern = {date.fromisoformat(r["report_date"]).weekday()
              for r in rows if r["report_date"] >= mod.TUESDAY_CONVENTION_FROM}
    assert modern <= {0, 1, 2, 4}
    assert 1 in modern

    early = {date.fromisoformat(r["report_date"]).weekday()
             for r in rows if r["report_date"] < mod.TUESDAY_CONVENTION_FROM}
    assert early - {0, 1, 2}, "pre-1993 should NOT be Tuesday-only"


def test_pre_convention_rows_carry_no_fabricated_release_date(rows, mod, meta):
    """A fabricated release date would look usable. An empty one forces a study to
    decide what to do with data whose publication convention nobody here knows."""
    for r in rows:
        if r["report_date"] < mod.TUESDAY_CONVENTION_FROM:
            assert r["release_date_nominal"] == "", r["report_date"]
        else:
            assert r["release_date_nominal"] != "", r["report_date"]
    assert meta["release_convention_measured"]["rows_without_a_release_date"] > 0
    assert meta["release_convention_measured"]["tuesday_schedule_from"] == \
        mod.TUESDAY_CONVENTION_FROM


def test_the_release_convention_records_where_it_fails(meta):
    """Publication is suspended during government shutdowns and released in
    batches afterwards, so +3 days is OPTIMISTIC across those windows. Stated,
    not silently ignored."""
    fails = meta["release_convention_fails_here"]
    assert any("2018-12" in f["from"] for f in fails)
    assert any("shutdown" in f["why"] for f in fails)


# ------------------------------------------------------------- the provenance


def test_the_euro_predates_itself_and_that_is_recorded(meta):
    """Legacy rows run from 1986 under the name 'EURO FX'. The euro did not exist
    until 1999-01-01, and continuous coverage begins exactly 1999-01-05 after a
    644-week gap. Code 099741 carries a back-labelled predecessor, and a study
    reading the full series would splice two different currencies."""
    warn = meta["provenance_warnings"]
    assert "6E" in warn
    assert "1999" in warn["6E"]
    assert meta["first_report_per_symbol_family"]["6E|legacy"] < "1999-01-01"


def test_the_russell_venue_change_is_recorded(meta):
    """Not pre-inception, but the Russell 2000 E-mini traded on ICE from 2008 to
    2017. Pre-2017 rows describe a contract on a different exchange from the one
    the prop track would trade."""
    assert "RTY" in meta["provenance_warnings"]
    assert "ICE" in meta["provenance_warnings"]["RTY"]


def test_micro_cot_inception_bounds_the_free_rung_two_test(meta):
    """A contract enters COT only once it has enough REPORTABLE traders, which is
    far later than its listing date. The micros launched 2019-05-06; MES first
    reports 2020-07-28 and MYM not until 2022-07-26. MSI and MHG have under a
    year. This BOUNDS what the free weekly micro/mini test can cover, so it is
    recorded rather than discovered by a study."""
    inc = meta["micro_cot_inception"]
    assert inc["MES"] > "2019-05-06", "COT entry lags contract launch"
    assert inc["MSI"] >= "2026-01-01"
    assert inc["MHG"] >= "2026-01-01"
    # The two pairs with real history, which is what a study may actually use.
    assert inc["MES"] < "2021-01-01"
    assert inc["MNQ"] < "2021-01-01"


def test_the_measured_family_start_disagrees_with_the_published_one(meta):
    """The CFTC publishes 2009-09 for disaggregated and 2010-07-20 for TFF; both
    datasets carry back-history to 2006-06-13. More history than documented is
    still a discrepancy, and taking the better number silently is how a provider
    fact stops being checkable."""
    assert meta["family_first_report_measured"]["tff"] < \
        meta["family_first_report_published"]["tff"]
    assert meta["family_first_report_measured"]["disaggregated"] < \
        meta["family_first_report_published"]["disaggregated"]


# ------------------------------------------------------------- reproducibility


def test_the_fixture_is_byte_reproducible(meta):
    """D252 found `--build` producing 1,580 / 1,573 / 1,574 symbols across three
    runs of unchanged code. Here the content was stable but the FILE was not:
    gzip stamps an mtime into header bytes 4-7, so two identical builds hashed
    differently. Written with mtime=0, which this asserts directly."""
    header = FIXTURE.read_bytes()[:10]
    assert header[:2] == b"\x1f\x8b", "not a gzip file"
    assert header[4:8] == b"\x00\x00\x00\x00", (
        "gzip MTIME is non-zero, so rebuilding produces a different file hash"
    )


def test_the_licence_is_recorded_because_it_is_the_reason_this_is_committed(meta):
    """Every CME product in the data layer is licensed and gitignored. This one is
    a work of the US government and therefore public domain, which is the whole
    reason it may live in the repo at all."""
    assert "PUBLIC DOMAIN" in meta["licence"]
    assert FIXTURE.exists() and MAP.exists()


def test_the_span_reaches_back_to_1986(meta):
    assert meta["span"]["first"] <= "1986-01-15"
    assert meta["span"]["last"] >= "2026-08-01"
    assert meta["rows"] > 200_000


# ------------------------------------------- the resolution rules, no network


def test_release_date_helper(mod):
    # Tuesday -> that Friday
    assert mod.release_date_of("2026-08-25") == "2026-08-28"
    assert mod.release_date_of("2026-08-25T00:00:00.000") == "2026-08-28"
    # The holiday shift that breaks a flat +3: a Wednesday report still releases
    # on the Friday of its own week, where +3 would say Saturday.
    assert mod.release_date_of("2007-01-03") == "2007-01-05"
    # A Monday shift resolves forward to the same week's Friday, not backwards.
    assert mod.release_date_of("2020-12-28") == "2021-01-01"
    # A FRIDAY report must not release on itself. 2003-02-14 is a real one.
    assert mod.release_date_of("2003-02-14") == "2003-02-21"
    # Before the convention existed there is no answer, and we say so.
    assert mod.release_date_of("1986-01-15") == ""


def test_suspension_lookup(mod):
    assert mod.in_suspension("2019-01-08") is not None
    assert mod.in_suspension("2013-10-08") is not None
    assert mod.in_suspension("2026-08-25") is None


def test_every_symbol_declares_a_family_that_exists(mod):
    for sym, (family, pattern, exact) in mod.SYMBOLS.items():
        assert family in mod.DATASETS, sym
        assert pattern.startswith("%") and pattern.endswith("%"), sym
        if exact is not None:
            assert exact.strip() == exact and exact, sym
