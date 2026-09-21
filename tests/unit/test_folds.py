"""`validation/folds.py` — the parts the golden does not pin (D593).

Gate U. `tests/golden/test_folds_ledger.py` pins the arithmetic against a hand-worked
twelve-date calendar. This file pins the surface around it: what a date may be, what a `Fold`
refuses at construction, which guard fires on which defect, and that leave-one-year-out works
on a calendar that looks like the ones the deposit docs will actually hand it — ten years of
business days, where the default `min_days=200` is a floor rather than a tripwire.

**Every guard here is asserted to FIRE.** A validation module whose error paths are never
exercised is a module whose error paths do not exist; D48's "a method that returns a wrong
number instead of raising is a bug" is only checkable by breaking what the assertion reads.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import datetime as dt

import numpy as np
import pytest

from backtest_framework.validation.folds import (
    Fold,
    assert_partition,
    era_folds,
    leave_one_year_out,
    purged,
    year_blocks,
)


def _business_days(start: str = "2016-01-01", end: str = "2026-01-01") -> np.ndarray:
    days = np.arange(np.datetime64(start), np.datetime64(end), dtype="datetime64[D]")
    return days[np.is_busday(days)]


def _idx(*values: int) -> np.ndarray:
    return np.array(values, dtype=np.int64)


# --------------------------------------------------------------------------------------------
# what a date may be
# --------------------------------------------------------------------------------------------
def test_year_blocks_accepts_strings_datetime64_and_date_objects():
    strings = ["2020-01-02", "2020-06-30", "2021-01-04"]
    as_dt64 = np.array(strings, dtype="datetime64[D]")
    as_nanos = np.array(strings, dtype="datetime64[ns]")
    as_objects = np.array([dt.date.fromisoformat(s) for s in strings], dtype=object)

    expected = {2020: [0, 1], 2021: [2]}
    for dates in (strings, as_dt64, as_nanos, as_objects):
        blocks = year_blocks(dates)
        assert {y: v.tolist() for y, v in blocks.items()} == expected


def test_a_nanosecond_timestamp_is_truncated_to_its_day_not_viewed_as_an_integer():
    """The cast goes through datetime64[D]; an int64 view of a DatetimeIndex is not a date."""
    stamps = np.array(["2020-12-31T23:59:59", "2021-01-01T00:00:01"], dtype="datetime64[s]")
    assert {y: v.tolist() for y, v in year_blocks(stamps).items()} == {2020: [0], 2021: [1]}


def test_year_blocks_is_deliberately_permissive_about_order():
    """It is a grouping, not a fold. `leave_one_year_out` is where sortedness is required."""
    blocks = year_blocks(["2021-01-04", "2020-06-30", "2020-01-02"])
    assert {y: v.tolist() for y, v in blocks.items()} == {2020: [1, 2], 2021: [0]}
    with pytest.raises(ValueError, match="not sorted"):
        leave_one_year_out(["2021-01-04", "2020-06-30", "2020-01-02"], min_days=1)


@pytest.mark.parametrize(
    "dates,match",
    [
        ([], "empty"),
        (np.zeros((2, 2), dtype="datetime64[D]"), "1-D"),
        (np.array([1, 2, 3]), "ISO strings"),
    ],
)
def test_year_blocks_refuses_what_is_not_a_date_index(dates, match):
    with pytest.raises((ValueError, TypeError), match=match):
        year_blocks(dates)


# --------------------------------------------------------------------------------------------
# Fold: the construction guarantee
# --------------------------------------------------------------------------------------------
def test_a_fold_refuses_train_and_test_overlap():
    with pytest.raises(ValueError, match="fitted on"):
        Fold(_idx(0, 1, 2), _idx(2), "overlapping")


def test_a_fold_refuses_an_empty_test_set():
    with pytest.raises(ValueError, match="empty test set"):
        Fold(_idx(0, 1), _idx(), "nothing to evaluate")


def test_a_fold_refuses_a_repeated_or_unsorted_position():
    with pytest.raises(ValueError, match="strictly increasing"):
        Fold(_idx(0, 0, 1), _idx(2), "repeated")
    with pytest.raises(ValueError, match="strictly increasing"):
        Fold(_idx(1, 0), _idx(2), "unsorted")


def test_a_fold_refuses_a_float_or_two_dimensional_index():
    with pytest.raises(TypeError, match="integer positions"):
        Fold(np.array([0.0, 1.0]), _idx(2), "float")
    with pytest.raises(ValueError, match="1-D"):
        Fold(np.zeros((2, 2), dtype=np.int64), _idx(2), "2-D")


def test_an_empty_training_set_is_allowed_and_a_fold_says_so_by_its_length():
    """Not every empty train set is a defect — a first-fold cold start is one. It is visible."""
    fold = Fold(_idx(), _idx(0, 1), "cold start")
    assert fold.train_idx.size == 0


# --------------------------------------------------------------------------------------------
# leave-one-year-out on a realistic calendar
# --------------------------------------------------------------------------------------------
def test_ten_years_of_business_days_give_ten_folds_at_the_default_min_days():
    days = _business_days()
    folds = leave_one_year_out(days)
    assert len(folds) == 10
    assert [f.label for f in folds] == [f"LOYO {y}" for y in range(2016, 2026)]
    assert_partition(folds, days.size)
    for fold in folds:
        held = days[fold.test_idx].astype("datetime64[Y]")
        assert len(set(held.tolist())) == 1, "a fold's test set is exactly one year"
        assert set(days[fold.train_idx].astype("datetime64[Y]").tolist()).isdisjoint(
            set(held.tolist())
        ), "INDEX_REWEIGHT_FLOW_PREREG.md unit test 9"


def test_a_partial_year_raises_rather_than_being_dropped():
    days = _business_days("2016-01-01", "2026-03-01")  # 2026 holds ~42 sessions
    with pytest.raises(ValueError, match="below min_days=200"):
        leave_one_year_out(days)
    folds = leave_one_year_out(days, min_days=40)
    assert len(folds) == 11 and folds[-1].label == "LOYO 2026"


def test_min_days_below_one_is_refused():
    with pytest.raises(ValueError, match="min_days must be >= 1"):
        leave_one_year_out(_business_days(), min_days=0)


# --------------------------------------------------------------------------------------------
# purging
# --------------------------------------------------------------------------------------------
def test_purging_removes_train_on_both_sides_and_scales_with_the_embargo():
    days = _business_days("2019-01-01", "2022-01-01")
    folds = leave_one_year_out(days)
    middle = folds[1]  # LOYO 2020: a year with training data on BOTH sides
    retained = [purged([middle], days, e)[0].train_idx.size for e in (0, 1, 5, 20)]
    assert retained[0] == middle.train_idx.size
    assert retained == sorted(retained, reverse=True), "a longer embargo cannot retain more"
    assert retained[-1] < retained[0]

    after = purged([middle], days, 5)[0]
    lo, hi = days[middle.test_idx[0]], days[middle.test_idx[-1]]
    kept = days[after.train_idx]
    assert (kept < lo - np.timedelta64(5, "D")).sum() > 0, "training before the block survives"
    assert (kept > hi + np.timedelta64(5, "D")).sum() > 0, "training after the block survives"
    assert not ((kept >= lo - np.timedelta64(5, "D")) & (kept <= hi + np.timedelta64(5, "D"))).any()


def test_purging_refuses_a_fold_built_on_a_different_index():
    """The silent version of this is a purge that measures distance on the wrong calendar."""
    days = _business_days("2020-01-01", "2021-01-01")
    fold = Fold(_idx(0, 1), _idx(5_000), "off the end")
    with pytest.raises(IndexError, match="built on a different index"):
        purged([fold], days, 3)


@pytest.mark.parametrize("embargo", [-1, 1.5, True])
def test_purging_refuses_a_bad_embargo(embargo):
    days = _business_days("2020-01-01", "2022-01-01")
    folds = leave_one_year_out(days)
    with pytest.raises((TypeError, ValueError)):
        purged(folds, days, embargo)


def test_purging_keeps_the_label_and_records_the_embargo_in_it():
    days = _business_days("2020-01-01", "2022-01-01")
    after = purged(leave_one_year_out(days), days, 7)
    assert [f.label for f in after] == ["LOYO 2020 (embargo 7d)", "LOYO 2021 (embargo 7d)"]


# --------------------------------------------------------------------------------------------
# eras and partitions
# --------------------------------------------------------------------------------------------
def test_an_era_ending_before_it_starts_is_refused():
    with pytest.raises(ValueError, match="ends before it starts"):
        era_folds(_business_days(), [("2020-12-31", "2020-01-02")])


def test_era_folds_that_do_cover_the_index_are_a_partition():
    days = _business_days("2020-01-01", "2022-01-01")
    folds = era_folds(days, [("2020-01-01", "2020-12-31"), ("2021-01-01", "2021-12-31")])
    assert_partition(folds, days.size)


def test_assert_partition_names_the_two_failures_separately():
    a = Fold(_idx(2, 3), _idx(0, 1), "a")
    b = Fold(_idx(0, 1), _idx(2), "b")  # position 3 is in no test set
    with pytest.raises(AssertionError, match="in no test set"):
        assert_partition([a, b], 4)

    c = Fold(_idx(2, 3), _idx(1), "c")  # position 1 is already in a's test set
    with pytest.raises(AssertionError, match="more than one test set"):
        assert_partition([a, c], 2)


def test_assert_partition_names_an_out_of_range_position():
    with pytest.raises(AssertionError, match=r"outside range\(2\)"):
        assert_partition([Fold(_idx(0), _idx(1, 9), "past the end")], 2)


def test_assert_partition_refuses_a_nonsense_n():
    with pytest.raises(ValueError, match="n must be >= 1"):
        assert_partition([Fold(_idx(1), _idx(0), "a")], 0)
