"""D586 -- the settlement-window table and its loader. Offline: reads only data/settlement_windows.csv.

Covers the ledger doc's unit test 13 (DST) and the index-reweight doc's unit test 12 (an unmapped
product raises, and no window is ever taken from anywhere but the sourced table).
"""
from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from dataclasses import asdict
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "scripts" / "settlement_windows.py"


def _load():
    """Import the script by PATH under a private name.

    pytest imports any path you name, so the module is given a name nothing else can collide with
    and is NOT put on sys.path as a directory.
    """
    spec = importlib.util.spec_from_file_location("_d586_settlement_windows", MODULE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


SW = _load()


@pytest.fixture(scope="module")
def rows():
    return SW.load_rows()


# ------------------------------------------------------------------------------ the table itself
def test_table_parses_and_every_requested_product_is_present(rows):
    mapped = {w.root for w in rows if w.history_status in SW.SERVED}
    assert set(SW.PRODUCTS_REQUESTED) <= mapped, set(SW.PRODUCTS_REQUESTED) - mapped


def test_g1_every_row_carries_a_url_an_access_time_and_a_basis(rows):
    assert SW.g1_every_row_sourced(rows) == len(rows)


def test_g1_fires_when_the_source_url_is_removed(rows):
    broken = [SW.SettlementWindow(**{**asdict(rows[0]), "source_url": ""})]
    with pytest.raises(AssertionError):
        SW.g1_every_row_sourced(broken)


def test_every_history_status_is_one_of_three(rows):
    assert {w.history_status for w in rows} <= set(SW.ALL_STATUS)


def test_current_only_rows_carry_their_access_date_as_effective_from(rows):
    for w in rows:
        if w.history_status == "current_only":
            assert w.effective_from == w.accessed_utc[:10], w.root
            assert w.effective_to == "", w.root


def test_dated_notice_rows_carry_a_real_change_date(rows):
    for w in rows:
        if w.history_status == "dated_notice":
            d = dt.date.fromisoformat(w.effective_from)
            assert dt.date(2000, 1, 1) < d < dt.date(2026, 9, 21), (w.root, d)


# ---------------------------------------------------------------- window_for: the raising loader
def test_window_for_returns_a_sourced_window_for_NG_in_2023():
    w = SW.window_for("NG", "2023-06-01")
    assert (w.start_et, w.end_et) == ("14:28:00", "14:30:00")
    assert (w.start_ct, w.end_ct) == ("13:28:00", "13:30:00")
    assert w.source_url.startswith("https://www.cmegroup.com/")
    assert "VWAP" in w.basis
    assert w.effective_from == "2009-06-01"


def test_window_for_CL_matches_NG_and_the_ledger_hypothesis_is_confirmed_in_ET():
    """The ledger doc guessed 'about 14:28-14:30 ET for NG and CL'. Confirmed -- and in ET, which
    is the half the doc could have got wrong, since CME states most other groups in CT."""
    for root in ("NG", "CL", "HO", "RB"):
        w = SW.window_for(root, "2023-06-01")
        assert (w.start_et, w.end_et) == ("14:28:00", "14:30:00"), root


def test_g2_unmapped_product_raises():
    with pytest.raises(SW.UnmappedProduct):
        SW.window_for("XX", "2023-06-01")


@pytest.mark.parametrize("bogus", ["XX", "ZZZ", "SPY", "", "ng"])
def test_unmapped_variants_all_raise(bogus):
    with pytest.raises(SW.UnmappedProduct):
        SW.window_for(bogus, "2023-06-01")


def test_g3_date_before_the_earliest_sourced_effective_date_raises():
    with pytest.raises(SW.UnsourcedDate):
        SW.window_for("NG", "2009-05-29")
    with pytest.raises(SW.UnsourcedDate):
        SW.window_for("GC", "2023-06-01")


def test_the_day_of_the_earliest_sourced_date_is_served_and_the_day_before_is_not():
    assert SW.window_for("NG", "2009-06-01").effective_from == "2009-06-01"
    with pytest.raises(SW.UnsourcedDate):
        SW.window_for("NG", "2009-05-31")


def test_window_for_accepts_a_date_object_and_a_string_and_rejects_anything_else():
    a = SW.window_for("CL", dt.date(2023, 6, 1))
    b = SW.window_for("CL", "2023-06-01")
    assert a == b
    with pytest.raises(TypeError):
        SW.window_for("CL", 20230601)


def test_ES_crosses_the_2020_boundary_on_the_dates_SER_8591_gives():
    assert SW.window_for("ES", "2020-10-26").start_ct == "14:59:30"
    with pytest.raises(SW.UnsourcedDate):
        SW.window_for("ES", "2020-10-23")


def test_the_superseded_ES_window_is_recorded_but_never_served(rows):
    old = [w for w in rows if w.root == "ES" and w.history_status == "record_only"]
    assert len(old) == 1 and old[0].start_ct == "15:14:30"
    assert old[0].effective_from == "" and old[0].effective_to == "2020-10-23"
    assert SW.window_for("ES", "2023-06-01").history_status == "dated_notice"
    # and there is no date at which window_for hands back the record_only row
    for d in ("2020-10-26", "2021-01-04", "2026-09-21"):
        assert SW.window_for("ES", d).start_ct == "14:59:30", d


# ----------------------------------------------------------------------------- G4 and unit-13 DST
def test_g4_ct_to_et_is_exactly_one_hour_on_every_row(rows):
    assert SW.g4_ct_et_is_one_hour(rows) == len(rows)


def test_g4_fires_on_a_row_whose_ct_is_not_one_hour_behind(rows):
    shifted = SW.SettlementWindow(**{**asdict(rows[0]), "start_ct": rows[0].start_et})
    with pytest.raises(AssertionError, match="ET-CT is 0s"):
        SW.g4_ct_et_is_one_hour([shifted])


def test_unit13_dst_both_transition_weeks(rows):
    """ledger unit test 13: W_start/W_end map correctly in BOTH transition weeks."""
    d = SW.dst_audit(rows)
    assert d["pairs_checked"] == len(rows) * 2 * 7 * 2 * len(d["years"])
    assert len(d["days"]) == 7 * 2 * len(d["years"])


def test_unit13_covers_the_spring_and_autumn_sundays_themselves(rows):
    d = SW.dst_audit(rows, years=(2023,))
    spring, fall = SW.dst_transition_dates(2023)
    assert spring.isoformat() == "2023-03-12" and fall.isoformat() == "2023-11-05"
    assert spring.isoformat() in d["days"] and fall.isoformat() in d["days"]


def test_unit13_fires_when_one_et_spelling_is_an_hour_wrong(rows):
    broken = [SW.SettlementWindow(**{**asdict(rows[0]), "start_et": "12:29:00"})]
    with pytest.raises(AssertionError):
        SW.dst_audit(broken, years=(2023,))


def test_dst_transition_dates_are_the_second_march_sunday_and_first_november_sunday():
    for y, s, f in ((2020, "2020-03-08", "2020-11-01"), (2021, "2021-03-14", "2021-11-07"),
                    (2022, "2022-03-13", "2022-11-06")):
        a, b = SW.dst_transition_dates(y)
        assert (a.isoformat(), b.isoformat()) == (s, f)
        assert a.weekday() == 6 and b.weekday() == 6


# ------------------------------------------------------------------------------------- G5 and G6
def test_g5_no_overlapping_effective_periods(rows):
    assert SW.g5_no_overlap(rows) == len(rows)


def test_g5_fires_on_two_open_periods_for_one_root(rows):
    base = asdict(next(w for w in rows if w.history_status == "dated_notice"))
    dup = [SW.SettlementWindow(**base),
           SW.SettlementWindow(**{**base, "effective_from": "2021-01-01"})]
    with pytest.raises(AssertionError):
        SW.g5_no_overlap(dup)


def test_g6_every_micro_maps_to_a_mapped_parent(rows):
    assert SW.g6_micros_map(rows) == len(SW.MICRO_PARENT)


def test_g6_fires_when_a_parent_row_is_missing(rows):
    with pytest.raises(AssertionError):
        SW.g6_micros_map([w for w in rows if w.root != "ES"])


@pytest.mark.parametrize("micro,parent", sorted(SW.MICRO_PARENT.items()))
def test_a_micro_returns_its_parents_row_not_a_row_of_its_own(micro, parent, rows):
    assert micro not in {w.root for w in rows}, f"{micro} must NOT be a duplicate row"
    d = SW.earliest_sourced(parent, rows)
    assert SW.window_for(micro, d) == SW.window_for(parent, d)


def test_a_micro_of_an_unmapped_parent_raises():
    assert "MZC" not in SW.MICRO_PARENT
    with pytest.raises(SW.UnmappedProduct):
        SW.window_for("MZC", "2023-06-01")


# ------------------------------------------------------------- bar mapping used by --measure only
@pytest.mark.parametrize("root,bars", [("CL", (328, 329)), ("NG", (328, 329)), ("GC", (269, 269)),
                                       ("SI", (264, 264)), ("HG", (239, 239)), ("ZC", (314, 314)),
                                       ("LE", (299, 299)), ("ES", (419, 419))])
def test_window_bars_land_where_the_clock_says(root, bars):
    w = SW.window_for(root, SW.earliest_sourced(root))
    assert SW.window_bars(w) == bars
    assert SW.inside_fixture_band(w)


def test_a_sub_minute_window_collapses_to_the_one_minute_containing_it():
    w = SW.window_for("LE", SW.earliest_sourced("LE"))
    assert (w.start_et, w.end_et) == ("13:59:30", "14:00:00")
    assert SW.window_bars(w) == (299, 299)  # 13:59 ET, the minute that contains it


def test_the_superseded_equity_window_would_fall_outside_the_fixture_band(rows):
    old = next(w for w in rows if w.root == "ES" and w.history_status == "record_only")
    assert old.start_et == "16:14:30"
    assert not SW.inside_fixture_band(old)


def test_required_outputs_is_enforced_before_any_write():
    with pytest.raises(AssertionError, match="REQUIRED_OUTPUTS"):
        SW.write_meta({"spec": "D586"})
