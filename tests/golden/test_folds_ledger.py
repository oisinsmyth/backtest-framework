"""Golden master for `validation/folds.py` (D593). Hand arithmetic in test_folds_ledger.hand.txt.

Gate G. Every number below was worked out on a calendar before the module was run, per D39
and CONTRIBUTING.md: the ground truth is produced by a calculator that never imports this
codebase, because a `.hand.txt` derived from the implementation launders the implementation's
assumptions into the thing that is supposed to check them.

The ledger of record is `INDEX_REWEIGHT_FLOW_PREREG.md` §10 and unit test 9 (*"a model
evaluated on year y was not fitted using year y data"*), `OPENING_AGENT_STATE_PREREG.md` §11,
and D555's three eras — which are read back out of `scripts/run_d555_tsmom_replication.py`
rather than retyped, so that this golden is pinned to the runner's object and not to a copy
of it that can drift.

The twelve-date calendar straddles every era boundary and puts **both sides of each purge
boundary** in the sample: the training session exactly `embargo_days` from a test block, and
the one a day further out. A purge whose inclusivity is only stated in prose is a purge
nobody can reproduce.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

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

REPO = Path(__file__).resolve().parents[2]

#: The twelve-date calendar of the .hand.txt, in its order.
DATES = [
    "2010-12-31",  # 0  one day before era 1 opens
    "2011-01-03",  # 1  era 1 first session
    "2011-06-15",  # 2
    "2015-12-31",  # 3  era 1 last session
    "2016-01-04",  # 4  era 2 first session
    "2016-07-01",  # 5
    "2019-12-31",  # 6  era 2 last session
    "2020-01-02",  # 7  era 3 first session
    "2020-06-30",  # 8
    "2023-12-29",  # 9  era 3 last session
    "2024-01-02",  # 10 the reserved forward slice: in NO era
    "2024-06-28",  # 11
]

#: Copied from the .hand.txt, which copied it from the runner. Asserted equal below.
HAND_ERAS = [
    ("2011-01-03", "2015-12-31"),
    ("2016-01-04", "2019-12-31"),
    ("2020-01-02", "2023-12-29"),
]


def _d555():
    spec = importlib.util.spec_from_file_location(
        "run_d555_tsmom_replication", REPO / "scripts" / "run_d555_tsmom_replication.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["run_d555_tsmom_replication"] = module
    spec.loader.exec_module(module)
    return module


def test_the_eras_are_the_runners_eras_and_not_a_copy():
    """`scripts/run_d555_tsmom_replication.py:44`. Two copies of one fact drift apart."""
    assert [tuple(e) for e in _d555().ERAS] == HAND_ERAS


# --------------------------------------------------------------------------------------------
# Case 1 — year_blocks
# --------------------------------------------------------------------------------------------
def test_case_1_year_blocks():
    blocks = year_blocks(DATES)
    assert list(blocks) == [2010, 2011, 2015, 2016, 2019, 2020, 2023, 2024]
    assert blocks[2010].tolist() == [0]
    assert blocks[2011].tolist() == [1, 2]
    assert blocks[2015].tolist() == [3]
    assert blocks[2016].tolist() == [4, 5]
    assert blocks[2019].tolist() == [6]
    assert blocks[2020].tolist() == [7, 8]
    assert blocks[2023].tolist() == [9]
    assert blocks[2024].tolist() == [10, 11]
    assert sum(len(v) for v in blocks.values()) == len(DATES)


# --------------------------------------------------------------------------------------------
# Case 2 — leave-one-year-out
# --------------------------------------------------------------------------------------------
HAND_LOYO = [
    ("LOYO 2010", [0], [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    ("LOYO 2011", [1, 2], [0, 3, 4, 5, 6, 7, 8, 9, 10, 11]),
    ("LOYO 2015", [3], [0, 1, 2, 4, 5, 6, 7, 8, 9, 10, 11]),
    ("LOYO 2016", [4, 5], [0, 1, 2, 3, 6, 7, 8, 9, 10, 11]),
    ("LOYO 2019", [6], [0, 1, 2, 3, 4, 5, 7, 8, 9, 10, 11]),
    ("LOYO 2020", [7, 8], [0, 1, 2, 3, 4, 5, 6, 9, 10, 11]),
    ("LOYO 2023", [9], [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11]),
    ("LOYO 2024", [10, 11], [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
]


def test_case_2_leave_one_year_out_matches_the_hand_table():
    folds = leave_one_year_out(DATES, min_days=1)
    assert len(folds) == 8
    for fold, (label, test, train) in zip(folds, HAND_LOYO):
        assert fold.label == label
        assert fold.test_idx.tolist() == test
        assert fold.train_idx.tolist() == train
        assert len(train) == len(DATES) - len(test)


def test_case_2_unit_test_9_on_the_2011_fold():
    """`INDEX_REWEIGHT_FLOW_PREREG.md` unit test 9, checked on the fold the .hand.txt works."""
    fold = leave_one_year_out(DATES, min_days=1)[1]
    assert fold.label == "LOYO 2011"
    year_2011 = {1, 2}
    assert year_2011.isdisjoint(set(fold.train_idx.tolist()))
    assert set(fold.test_idx.tolist()) == year_2011


def test_case_2_the_test_sets_partition_the_index():
    assert_partition(leave_one_year_out(DATES, min_days=1), len(DATES))


def test_case_2_min_days_200_refuses_this_calendar():
    """Every year here holds 1 or 2 positions; the default guard fires on all eight."""
    with pytest.raises(ValueError, match="below min_days=200"):
        leave_one_year_out(DATES)


# --------------------------------------------------------------------------------------------
# Case 3 — era folds
# --------------------------------------------------------------------------------------------
HAND_ERA_FOLDS = [
    ("2011-01-03..2015-12-31", [1, 2, 3], [0, 4, 5, 6, 7, 8, 9, 10, 11]),
    ("2016-01-04..2019-12-31", [4, 5, 6], [0, 1, 2, 3, 7, 8, 9, 10, 11]),
    ("2020-01-02..2023-12-29", [7, 8, 9], [0, 1, 2, 3, 4, 5, 6, 10, 11]),
]


def test_case_3_era_folds_match_the_hand_table():
    folds = era_folds(DATES, HAND_ERAS)
    assert len(folds) == 3
    for fold, (label, test, train) in zip(folds, HAND_ERA_FOLDS):
        assert fold.label == label
        assert fold.test_idx.tolist() == test
        assert fold.train_idx.tolist() == train
        assert len(train) == 9


def test_case_3_an_era_list_is_not_a_partition():
    """0, 10 and 11 are in no era — 2010 predates the first, 2024 is the reserved slice."""
    with pytest.raises(AssertionError, match=r"3 of 12 position\(s\) are in no test set"):
        assert_partition(era_folds(DATES, HAND_ERAS), len(DATES))


# --------------------------------------------------------------------------------------------
# Case 4 — purging at embargo_days = 3
# --------------------------------------------------------------------------------------------
HAND_PURGED_ERA = [
    # label, train after purge, the one position dropped and why
    ("2011-01-03..2015-12-31 (embargo 3d)", [4, 5, 6, 7, 8, 9, 10, 11], 0),
    ("2016-01-04..2019-12-31 (embargo 3d)", [0, 1, 2, 3, 8, 9, 10, 11], 7),
    ("2020-01-02..2023-12-29 (embargo 3d)", [0, 1, 2, 3, 4, 5, 10, 11], 6),
]


def test_case_4_purging_matches_the_hand_table():
    before = era_folds(DATES, HAND_ERAS)
    after = purged(before, DATES, 3)
    for fold, prior, (label, train, dropped) in zip(after, before, HAND_PURGED_ERA):
        assert fold.label == label
        assert fold.train_idx.tolist() == train
        assert len(train) == 8, "each era loses exactly one training session"
        assert dropped in prior.train_idx.tolist()
        assert dropped not in train


def test_case_4_purging_never_removes_a_test_index():
    before = era_folds(DATES, HAND_ERAS)
    after = purged(before, DATES, 3)
    for old, new in zip(before, after):
        assert new.test_idx.tolist() == old.test_idx.tolist()


def test_case_4_the_boundary_is_inclusive_on_the_named_day_and_not_the_next():
    """Era 2 drops position 7 (three days past its block) and keeps 3 (four days before it)."""
    fold = purged(era_folds(DATES, HAND_ERAS), DATES, 3)[1]
    assert 3 in fold.train_idx.tolist(), "2015-12-31 is one day outside [2016-01-01, ...]"
    assert 7 not in fold.train_idx.tolist(), "2020-01-02 is exactly on [..., 2020-01-03]"


def test_case_4_both_ends_are_purged():
    """Era 2 loses a session AFTER its block; era 3 loses one BEFORE its block."""
    after = purged(era_folds(DATES, HAND_ERAS), DATES, 3)
    assert 7 not in after[1].train_idx.tolist() and 7 > max(after[1].test_idx.tolist())
    assert 6 not in after[2].train_idx.tolist() and 6 < min(after[2].test_idx.tolist())


def test_case_4_embargo_zero_removes_nothing():
    before = era_folds(DATES, HAND_ERAS)
    after = purged(before, DATES, 0)
    for old, new in zip(before, after):
        assert new.train_idx.tolist() == old.train_idx.tolist()


# --------------------------------------------------------------------------------------------
# Case 5 — purging a LOYO fold
# --------------------------------------------------------------------------------------------
def test_case_5_purged_loyo_2011():
    fold = purged(leave_one_year_out(DATES, min_days=1), DATES, 3)[1]
    assert fold.label == "LOYO 2011 (embargo 3d)"
    assert fold.train_idx.tolist() == [3, 4, 5, 6, 7, 8, 9, 10, 11]
    assert fold.test_idx.tolist() == [1, 2]


# --------------------------------------------------------------------------------------------
# Case 6 — a two-block test set, purged per run
# --------------------------------------------------------------------------------------------
def test_case_6_purging_is_per_contiguous_run_not_per_fold():
    """10 retained against the 3 a global-span purge would leave. The .hand.txt works both."""
    fold = Fold(
        train_idx=np.array([0, 2, 3, 4, 5, 6, 7, 8, 10, 11], dtype=np.int64),
        test_idx=np.array([1, 9], dtype=np.int64),
        label="two blocks",
    )
    after = purged([fold], DATES, 1)[0]
    assert after.train_idx.tolist() == [0, 2, 3, 4, 5, 6, 7, 8, 10, 11]
    assert after.test_idx.tolist() == [1, 9]

    # The alternative, computed here so the contrast is a number and not a claim.
    days = np.array(DATES, dtype="datetime64[D]")
    one = np.timedelta64(1, "D")
    span = (days >= days[1] - one) & (days <= days[9] + one)
    global_purge = [i for i in fold.train_idx.tolist() if not span[i]]
    assert global_purge == [0, 10, 11]
    assert len(after.train_idx) == 10 and len(global_purge) == 3


# --------------------------------------------------------------------------------------------
# Case 7 — the guards
# --------------------------------------------------------------------------------------------
def test_case_7_unsorted_and_duplicate_dates_raise_different_messages():
    with pytest.raises(ValueError, match="not sorted"):
        leave_one_year_out(["2011-01-03", "2010-12-31"], min_days=1)
    with pytest.raises(ValueError, match="twice"):
        leave_one_year_out(["2011-01-03", "2011-01-03"], min_days=1)


def test_case_7_a_single_year_has_no_training_set():
    with pytest.raises(ValueError, match="at least 2 years"):
        leave_one_year_out(["2011-01-03", "2011-06-15"], min_days=1)


def test_case_7_overlapping_and_empty_eras_raise():
    with pytest.raises(ValueError, match="overlaps"):
        era_folds(DATES, [("2011-01-01", "2016-12-31"), ("2016-01-01", "2019-12-31")])
    with pytest.raises(ValueError, match="matches no date"):
        era_folds(DATES, [("2012-01-01", "2012-12-31")])


def test_case_7_a_fold_cannot_be_fitted_on_what_it_is_evaluated_on():
    """Unit test 9, made structural: the overlap is refused at construction."""
    with pytest.raises(ValueError, match="fitted on 1 of the position"):
        Fold(
            train_idx=np.array([0, 1], dtype=np.int64),
            test_idx=np.array([1], dtype=np.int64),
            label="leaky",
        )


def test_case_7_assert_partition_names_a_double_count():
    a = Fold(np.array([1], dtype=np.int64), np.array([0], dtype=np.int64), "a")
    b = Fold(np.array([1], dtype=np.int64), np.array([0], dtype=np.int64), "b")
    with pytest.raises(AssertionError, match="more than one test set"):
        assert_partition([a, b], 2)
