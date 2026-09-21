"""Gates on the sourced economic release calendar (D585, `data/calendar/events.csv`).

Offline and deterministic. The one network check is marked `live_fetch` and CI runs
`-m "not live_fetch"`; the real probing lives in `fetch_release_calendar.py --probe`.

WHAT THESE TESTS ARE DEFENDING

The failure mode of a calendar fixture is that it looks right. A date filled in from "the
first Friday of the month" reads exactly like a date read off the BLS page, and a study that
conditions on it is quietly conditioning on a guess. So the tests below pin, in order:

  * that the builder REFUSES a row whose method is not `fetched` or `archived` -- the one
    rule the whole fetcher is built around;
  * the two derivations that could silently disagree -- the weekday word BLS prints beside
    each date, and the Thursday that an EIA gas-storage alternate date replaces;
  * the DST arithmetic, which is the only place a clock becomes an instant;
  * and the committed artifact itself, including the facts the record quotes.
"""

from __future__ import annotations

import csv
import importlib.util
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "data" / "calendar" / "events.csv"
META = REPO / "data" / "calendar" / "events.meta.json"
COLUMNS = ["datetime_et", "datetime_utc", "event", "source_url", "release_date_nominal",
           "holiday_shift", "method", "accessed_utc"]


def _load():
    path = REPO / "scripts" / "fetch_release_calendar.py"
    spec = importlib.util.spec_from_file_location("fetch_release_calendar", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["fetch_release_calendar"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return _load()


@pytest.fixture(scope="module")
def rows():
    if not CSV.exists():
        pytest.skip("data/calendar/events.csv not built")
    with open(CSV, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


@pytest.fixture(scope="module")
def meta():
    if not META.exists():
        pytest.skip("data/calendar/events.meta.json not built")
    return json.loads(META.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- the fetcher's own selftest

def test_selftest_passes_a_clean_case_and_every_gate_raises(mod):
    """--selftest is the contract: it asserts a clean case through all six gates and then
    proves each one RAISES on a deliberate break. If it stops raising, it stops being a gate."""
    assert mod.selftest(log=lambda *a, **k: None) == 0


def test_required_outputs_is_declared_before_the_write(mod):
    for key in ("built_utc", "sources", "rows", "gates", "not_fetched",
                "disagreements_with_macro_release_calendar_json"):
        assert key in mod.REQUIRED_OUTPUTS


# ---------------------------------------------------------------- G1: the refusal

def test_g1_refuses_a_row_whose_method_is_inferred(mod):
    clean = mod._clean_rows()
    mod.gates(clean, mod._notes())                       # the clean case passes
    dirty = [{**clean[0], "method": "inferred"}] + clean[1:]
    with pytest.raises(AssertionError, match="G1"):
        mod.gates(dirty, mod._notes())


def test_g1_refuses_a_row_without_a_source_url(mod):
    clean = mod._clean_rows()
    with pytest.raises(AssertionError, match="G1"):
        mod.gates([{**clean[0], "source_url": ""}] + clean[1:], mod._notes())


# ---------------------------------------------------------------- the two second derivations

def test_bls_weekday_word_is_checked_against_the_parsed_date(mod):
    good = ('MAIN CONTENT BEGIN<tr><td class="date-cell"><p>Wednesday, January 20, 2016</p></td>'
            '<td class="time-cell"><p>08:30 AM</p></td>'
            '<td class="desc-cell"><p><strong>Consumer Price Index</strong> for December 2015</p></td></tr>')
    out = mod.parse_bls_year(good, 2016)
    assert out == [{"event": "CPI", "date": date(2016, 1, 20), "hh": 8, "mm": 30,
                    "desc": "Consumer Price Index for December 2015"}]
    with pytest.raises(AssertionError):
        mod.parse_bls_year(good.replace("Wednesday", "Monday"), 2016)


def test_employment_situation_of_veterans_is_not_the_employment_situation(mod):
    html = ('MAIN CONTENT BEGIN<tr><td class="date-cell"><p>Tuesday, March 22, 2016</p></td>'
            '<td class="time-cell"><p>10:00 AM</p></td>'
            '<td class="desc-cell"><p><strong>Employment Situation of Veterans</strong> for Annual 2015</p></td></tr>')
    assert mod.parse_bls_year(html, 2016) == []


def test_gas_alternate_dates_match_the_thursday_they_replace_not_the_nearest_one(mod):
    """EIA's gas table gives only the alternate date. At the end of 2025 the alternates are
    Mon 12-29 (Christmas) and Wed 12-31 (New Year); the Thursday NEAREST 12-29 is 2026-01-01,
    which belongs to 12-31. Order-preserving matching is the thing being defended here."""
    got = mod.match_alternates_to_thursdays([date(2025, 12, 29), date(2025, 12, 31)], 3)
    assert got == {date(2025, 12, 25): date(2025, 12, 29), date(2026, 1, 1): date(2025, 12, 31)}
    nearest = min([date(2025, 12, 25), date(2026, 1, 1)], key=lambda t: abs((t - date(2025, 12, 29)).days))
    assert nearest == date(2026, 1, 1)      # the rule this function exists to avoid


def test_gas_alternate_with_no_slot_in_range_raises(mod):
    with pytest.raises(AssertionError):
        mod.match_alternates_to_thursdays([date(2025, 12, 1)], 3, window=1)


def test_eia_standard_slot_is_read_off_the_page(mod):
    assert mod.parse_eia_standard(
        "The standard release time and day of the week will be at 10:30 a.m. eastern time on "
        "Thursdays with the following exceptions.") == (3, 10, 30)
    with pytest.raises(AssertionError):
        mod.parse_eia_standard("<p>nothing of the sort</p>")


def test_eia_exception_row_weekday_word_is_checked(mod):
    html = ("Holiday Release Schedule<table>"
            "<tr><td>Data for the week ending</td><td>Alternate release date</td><td>Release day</td>"
            "<td>Release time</td><td>Holiday</td></tr>"
            "<tr><td>January 15, 2016</td><td>January 21, 2016</td><td>Thursday</td>"
            "<td>11:00 a.m.</td><td>Martin Luther King Jr.</td></tr></table>")
    got = mod.parse_eia_exceptions(html)
    assert got[0]["week_ending"] == date(2016, 1, 15) and got[0]["alt"] == date(2016, 1, 21)
    assert (got[0]["hh"], got[0]["mm"]) == (11, 0)
    with pytest.raises(AssertionError):
        mod.parse_eia_exceptions(html.replace("<td>Thursday</td>", "<td>Friday</td>"))


def test_fomc_meeting_last_day(mod):
    assert mod.meeting_last_day("April/May", "30-1", 2019) == date(2019, 5, 1)
    assert mod.meeting_last_day("January", "26-27", 2016) == date(2016, 1, 27)
    assert mod.meeting_last_day("October", "4", 2019) == date(2019, 10, 4)


def test_fomc_press_release_states_its_own_clock(mod):
    hh, mm, zone = mod.parse_fomc_pr("<p>For release at 2:00 p.m. EST</p>", "x")
    assert (hh, mm, zone) == (14, 0, "EST")
    with pytest.raises(AssertionError):
        mod.parse_fomc_pr("<p>Statement</p>", "x")


# ---------------------------------------------------------------- G5: DST

def test_dst_arithmetic(mod):
    assert mod.et_pair(date(2016, 1, 20), 8, 30) == ("2016-01-20T08:30:00-05:00", "2016-01-20T13:30:00Z")
    assert mod.et_pair(date(2016, 7, 15), 8, 30) == ("2016-07-15T08:30:00-04:00", "2016-07-15T12:30:00Z")
    assert mod.et_pair(date(2020, 3, 15), 17, 0)[1] == "2020-03-15T21:00:00Z"


# ---------------------------------------------------------------- the committed artifact

def test_header_and_provenance_on_every_row(rows):
    assert list(rows[0].keys()) == COLUMNS
    for r in rows:
        assert r["method"] in ("fetched", "archived"), r
        assert r["source_url"].startswith("https://"), r
        assert r["accessed_utc"].endswith("Z"), r
        assert r["holiday_shift"] in ("True", "False"), r


def test_no_duplicate_event_and_timestamp(rows):
    keys = [(r["event"], r["datetime_et"]) for r in rows]
    assert len(set(keys)) == len(keys)


def test_every_row_is_inside_the_declared_span(rows, meta):
    for r in rows:
        assert r["datetime_et"][:10] >= meta["span"]["from"]
        assert r["datetime_et"][:10] <= meta["span"]["to"]


def test_et_and_utc_are_the_same_instant(rows, mod):
    from datetime import datetime
    for r in rows[::37]:
        et = datetime.fromisoformat(r["datetime_et"])
        utc = datetime.fromisoformat(r["datetime_utc"].replace("Z", "+00:00"))
        assert et == utc, r


def test_cpi_is_twelve_a_year_except_where_the_meta_names_the_year(rows, meta):
    per = meta["rows_per_event_per_year"]["CPI"]
    named = {(p["event"], p["year"]) for p in meta["partial_or_disrupted_years"]}
    for year, n in per.items():
        if 2016 <= int(year) <= 2026 and ("CPI", year) not in named:
            assert n == 12, f"CPI {year}: {n}"


def test_the_2020_emergency_cut_is_present_and_labelled(rows):
    unscheduled = {r["datetime_et"][:10] for r in rows if r["event"] == "FOMC_UNSCHEDULED"}
    assert "2020-03-15" in unscheduled
    sunday = [r for r in rows if r["event"] == "FOMC_UNSCHEDULED" and r["datetime_et"][:10] == "2020-03-15"]
    assert date.fromisoformat("2020-03-15").weekday() == 6      # it really was a Sunday
    assert sunday[0]["source_url"].endswith("monetary20200315a.htm")


def test_empsit_is_a_friday_unless_flagged(rows):
    for r in rows:
        if r["event"] != "EMPSIT":
            continue
        d = date.fromisoformat(r["datetime_et"][:10])
        assert d.weekday() == 4 or r["holiday_shift"] == "True", r


def test_eia_rows_sit_on_their_standard_weekday_unless_flagged(rows):
    want = {"EIA_WPSR": 2, "EIA_NGSR": 3}
    for r in rows:
        if r["event"] not in want:
            continue
        d = date.fromisoformat(r["datetime_et"][:10])
        nominal = date.fromisoformat(r["release_date_nominal"])
        assert nominal.weekday() == want[r["event"]], r
        assert (d == nominal) == (r["holiday_shift"] == "False"), r
        assert abs((d - nominal).days) <= 7, r


def test_eia_weekly_grid_has_no_gap_the_meta_does_not_name(rows, meta):
    """Every standard weekday between the first and last row is present, except the ones EIA
    published at another release's instant -- after the June 2022 outage the week-ending 06-17
    and 06-24 petroleum reports came out together, so 2022-06-29 carries both nominals."""
    collapsed = {(c["event"], n) for c in meta["eia_release_instants_covering_more_than_one_data_week"]
                 for n in c["nominal_dates_collapsed"]}
    for event in ("EIA_WPSR", "EIA_NGSR"):
        nom = sorted(date.fromisoformat(r["release_date_nominal"])
                     for r in rows if r["event"] == event)
        if not nom:
            continue
        expected, d = [], nom[0]
        while d <= nom[-1]:
            if (event, d.isoformat()) not in collapsed or d in nom:
                expected.append(d)
            d += timedelta(days=7)
        assert nom == expected, (event, sorted(set(expected) ^ set(nom))[:5])


def test_meta_lists_every_disagreement_with_the_older_macro_calendar(meta):
    """G4 does not require agreement -- it requires that every difference is written down."""
    assert isinstance(meta["disagreements_with_macro_release_calendar_json"], list)
    for d in meta["disagreements_with_macro_release_calendar_json"]:
        assert set(d) == {"event", "date", "in"}


def test_meta_names_a_reason_for_every_short_year(meta):
    for p in meta["partial_or_disrupted_years"]:
        assert p["reason"] and len(p["reason"]) > 20, p


def test_every_source_url_in_the_csv_is_in_the_meta_source_list(rows, meta):
    known = {v["url"] for v in meta["sources"].values()}
    fed = "https://www.federalreserve.gov/newsevents/pressreleases/"
    for r in rows:
        assert r["source_url"] in known or r["source_url"].startswith(fed), r["source_url"]


# ---------------------------------------------------------------- network

@pytest.mark.live_fetch
def test_probe_reaches_every_source(mod):
    assert mod.probe(log=lambda *a, **k: None) == 0
