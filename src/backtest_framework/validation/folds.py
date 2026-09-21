"""Leave-one-year-out, era and purged folds (D593).

Two of the User-Doc-Deposit pre-registrations fit parameters on annual events and validate
them with leave-one-year-out, and it existed nowhere in this repository:

  * `INDEX_REWEIGHT_FLOW_PREREG.md` §0.7 — *"Any fitted parameter is validated with
    leave-one-year-out cross-validation (Section 10), never an ordinary random split"* — §10
    and unit test 9, *"a model evaluated on year y was not fitted using year y data"*;
  * `OPENING_AGENT_STATE_PREREG.md` §11, *"Robustness validation: leave-one-year-out,
    reported alongside."*

**What existed instead.** `validation/walk_forward.py` cuts bar-counted, contiguous, gapless
windows and hands fitters a `DataView` built from the training slice only — the strongest
guard here, and the wrong shape for an annual event: with about ten January events, a rolling
252/63 window has no fold in which a given year is absent. `scripts/run_d555_tsmom_
replication.py:44 ERAS` is a three-way era split that is **reporting only** — it partitions
the output, never the fit. Neither is cross-validation over years.

WHY THE FOLDS ARE OBJECTS AND NOT A LOOP
----------------------------------------
Unit test 9 is a claim about a fold, not about a run: *"a model evaluated on year y was not
fitted using year y data."* Written as a loop over years inside a study runner it is a
comment; written as a `Fold` whose `__post_init__` refuses overlapping train and test indices
it is checkable by something that never saw the study. `assert_partition` is the other half —
a fold list that quietly drops a year looks identical, from the outside, to one that covers
it.

PURGING, AND WHY IT IS BOTH ENDS
--------------------------------
`purged` removes `embargo_days` of TRAIN either side of each contiguous test block.
`FEATURE_RESEARCH.md` §8.1 states the rule for a labelled sample (*"embargo ~ 1-2x the label
horizon"*), but the reason it has to be **both ends** is D555's: a signal with a lookback of L
bars contaminates the training data on BOTH sides of a held-out block — the sessions after the
block read bars inside it through their lookback, and the sessions before it are read by the
block's own. Purging one end leaves the other leaking. Test indices are never touched; only
train is removed, which is why the retained-train count is reported by the caller and not
silently absorbed.

This module reads no fixture and computes no return. Dates in, indices out.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

__all__ = [
    "Fold",
    "assert_partition",
    "era_folds",
    "leave_one_year_out",
    "purged",
    "year_blocks",
]


@dataclass(frozen=True, eq=False)
class Fold:
    """One train/test split, as positions into the date index that produced it.

    `eq=False` because two numpy arrays do not compare to a bool and a dataclass `__eq__`
    that raises `ValueError` on `fold_a == fold_b` is a false affordance (D48). Compare the
    arrays.

    `__post_init__` is where unit test 9 lives: a fold whose train and test indices intersect
    is refused at CONSTRUCTION, so no consumer has to remember to check. Every constructor in
    this module goes through it, `purged` included.
    """

    train_idx: np.ndarray
    test_idx: np.ndarray
    label: str

    def __post_init__(self) -> None:
        for name, arr in (("train_idx", self.train_idx), ("test_idx", self.test_idx)):
            a = np.asarray(arr)
            if a.ndim != 1:
                raise ValueError(f"{name} must be 1-D, got shape {a.shape}")
            if a.dtype.kind not in "iu":
                raise TypeError(f"{name} must hold integer positions, got dtype {a.dtype}")
            if a.size and np.any(np.diff(a) <= 0):
                raise ValueError(
                    f"{name} must be strictly increasing and unique; a repeated position "
                    f"would be counted twice by any consumer that sums over a fold"
                )
        if self.test_idx.size == 0:
            raise ValueError(f"fold {self.label!r} has an empty test set")
        overlap = np.intersect1d(self.train_idx, self.test_idx)
        if overlap.size:
            raise ValueError(
                f"fold {self.label!r} was fitted on {overlap.size} of the position(s) it is "
                f"evaluated on (first at index {int(overlap[0])}). A model evaluated on a "
                f"block must not have been fitted using that block."
            )


def _as_days(dates: Sequence[str] | np.ndarray) -> np.ndarray:
    """A 1-D `datetime64[D]` array from ISO strings, datetime64 or `datetime.date` objects.

    Cast through `datetime64[D]` rather than through an integer view: a `DatetimeIndex`
    viewed as int64 is nanoseconds-since-epoch on one build and something else on another,
    and the calendar arithmetic below wants days.
    """
    arr = np.asarray(dates)
    if arr.ndim != 1:
        raise ValueError(f"dates must be 1-D, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError("dates is empty")
    if arr.dtype.kind in "USM":
        return arr.astype("datetime64[D]")
    if arr.dtype.kind == "O":
        return np.array([np.datetime64(d, "D") for d in arr], dtype="datetime64[D]")
    raise TypeError(
        f"dates must be ISO strings, datetime64 or date objects, got dtype {arr.dtype}"
    )


def _checked_days(dates: Sequence[str] | np.ndarray) -> np.ndarray:
    """`_as_days`, plus strictly increasing. The two failures raise DIFFERENT messages.

    A decreasing step and a repeated date are separate defects with separate fixes — one is a
    date index that was never sorted, the other is a panel index that carries a session twice
    — and a single "not sorted" message would send a reader to the wrong one.
    """
    days = _as_days(dates)
    step = np.diff(days)
    zero = np.flatnonzero(step == np.timedelta64(0, "D"))
    if zero.size:
        i = int(zero[0])
        raise ValueError(
            f"dates holds {days[i]} twice (positions {i} and {i + 1}); a fold index cannot "
            f"tell the two apart, so a year block would carry the same session twice"
        )
    back = np.flatnonzero(step < np.timedelta64(0, "D"))
    if back.size:
        i = int(back[0])
        raise ValueError(
            f"dates is not sorted: position {i} is {days[i]} and position {i + 1} is "
            f"{days[i + 1]}. Sort before building folds; a purge measures calendar distance "
            f"from a block's endpoints and an unsorted index has none."
        )
    return days


def year_blocks(dates: Sequence[str] | np.ndarray) -> dict[int, np.ndarray]:
    """`{year: positions}` for every calendar year present, in ascending year order.

    Deliberately permissive about order — it is a grouping, not a fold — so it can be used to
    look at a raw index before deciding whether it is fit to split. `leave_one_year_out`
    applies the sortedness guard.
    """
    days = _as_days(dates)
    years = days.astype("datetime64[Y]").astype(int) + 1970
    return {int(y): np.flatnonzero(years == y).astype(np.int64) for y in np.unique(years)}


def leave_one_year_out(
    dates: Sequence[str] | np.ndarray, *, min_days: int = 200
) -> list[Fold]:
    """One fold per calendar year: test on that year, train on every other position.

    `INDEX_REWEIGHT_FLOW_PREREG.md` §10 — *"Fit on all other years, test on the held-out
    year, and repeat for every year"* — and unit test 9.

    `min_days` raises rather than dropping a thin year, and the default of 200 is roughly a
    session count. **A silently dropped year is the failure this guard is for**: it makes the
    per-year table shorter without making it wrong-looking, and the yearly sign tests those
    docs run (9 of 10 positive, one-sided p ~ 0.011) are counts over exactly this list — a
    fold list that quietly lost its first partial year changes the denominator of a
    pre-registered test. A caller who means to include a partial year passes a lower
    `min_days` and says so.
    """
    if min_days < 1:
        raise ValueError(f"min_days must be >= 1, got {min_days}")
    days = _checked_days(dates)
    blocks = year_blocks(days)
    if len(blocks) < 2:
        raise ValueError(
            f"leave-one-year-out needs at least 2 years, got {len(blocks)}: "
            f"{sorted(blocks)}. With one year the training set is empty."
        )
    thin = {y: int(idx.size) for y, idx in blocks.items() if idx.size < min_days}
    if thin:
        raise ValueError(
            f"year(s) below min_days={min_days}: {thin}. A partial year is not dropped "
            f"silently — pass a lower min_days if it is meant to be a fold, or slice it off "
            f"the index if it is not."
        )
    n = days.size
    all_idx = np.arange(n, dtype=np.int64)
    folds = []
    for year in sorted(blocks):
        test = blocks[year]
        train = np.setdiff1d(all_idx, test, assume_unique=True)
        folds.append(Fold(train_idx=train, test_idx=test, label=f"LOYO {year}"))
    return folds


def era_folds(
    dates: Sequence[str] | np.ndarray, eras: Sequence[tuple[str, str]]
) -> list[Fold]:
    """One fold per (start, end) era, both bounds INCLUSIVE, test inside and train outside.

    The golden case is D555's three eras (`scripts/run_d555_tsmom_replication.py:44`):
    `[("2011-01-03", "2015-12-31"), ("2016-01-04", "2019-12-31"), ("2020-01-02",
    "2023-12-29")]` — which in that runner are **reporting only**, a partition of the output.
    Reaching them through `Fold` is what turns the same three spans into a fit/evaluate split,
    and the difference is not cosmetic: an era table computed from a model fitted on all three
    eras is a description, not a validation.

    Overlapping eras and an era matching no date both raise. Eras need not cover the index,
    so `assert_partition` will refuse a list like D555's on a longer index — correctly: a
    reserved forward slice is deliberately in no era.
    """
    days = _checked_days(dates)
    n = days.size
    all_idx = np.arange(n, dtype=np.int64)
    folds: list[Fold] = []
    claimed = np.zeros(n, dtype=bool)
    for start, end in eras:
        lo = np.datetime64(str(start), "D")
        hi = np.datetime64(str(end), "D")
        if hi < lo:
            raise ValueError(f"era ({start}, {end}) ends before it starts")
        test = np.flatnonzero((days >= lo) & (days <= hi)).astype(np.int64)
        if test.size == 0:
            raise ValueError(
                f"era ({start}, {end}) matches no date in an index running "
                f"{days[0]}..{days[-1]}; an empty era would make a fold that cannot fire"
            )
        if np.any(claimed[test]):
            overlap = test[claimed[test]]
            raise ValueError(
                f"era ({start}, {end}) overlaps an earlier era at {days[overlap[0]]} "
                f"({overlap.size} position(s)); a position in two test sets is scored twice"
            )
        claimed[test] = True
        train = np.setdiff1d(all_idx, test, assume_unique=True)
        folds.append(Fold(train_idx=train, test_idx=test, label=f"{start}..{end}"))
    return folds


def _runs(idx: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous runs of a strictly increasing index, as (first, last) positions."""
    if idx.size == 0:
        return []
    breaks = np.flatnonzero(np.diff(idx) != 1)
    starts = np.concatenate(([0], breaks + 1))
    ends = np.concatenate((breaks, [idx.size - 1]))
    return [(int(idx[a]), int(idx[b])) for a, b in zip(starts, ends)]


def purged(
    folds: Sequence[Fold], dates: Sequence[str] | np.ndarray, embargo_days: int
) -> list[Fold]:
    """Drop `embargo_days` of TRAIN on both sides of every contiguous test block.

    The window removed around a block running `lo..hi` is the closed calendar interval
    `[lo - embargo_days, hi + embargo_days]`, so a training date exactly `embargo_days` away
    is removed and one day further is kept. Boundaries are stated because a purge whose
    inclusivity is undocumented is a purge nobody can reproduce.

    **Test indices are never removed.** Purging is a statement about what the fit may see, and
    a function that shrank the evaluation set while claiming to clean the training set would
    quietly change the denominator of every per-fold statistic.

    Each contiguous run is purged separately rather than purging once around the fold's global
    min and max: a fold whose test set is two blocks a decade apart would otherwise have its
    entire middle deleted, which is not an embargo but a different experiment.
    """
    if isinstance(embargo_days, bool) or not isinstance(embargo_days, (int, np.integer)):
        raise TypeError(f"embargo_days must be an int, got {type(embargo_days).__name__}")
    if embargo_days < 0:
        raise ValueError(f"embargo_days must be >= 0, got {embargo_days}")
    days = _checked_days(dates)
    n = days.size
    span = np.timedelta64(int(embargo_days), "D")
    out: list[Fold] = []
    for fold in folds:
        if fold.test_idx.size and int(fold.test_idx[-1]) >= n:
            raise IndexError(
                f"fold {fold.label!r} holds test position {int(fold.test_idx[-1])} but dates "
                f"has {n} entries; the folds were built on a different index"
            )
        if fold.train_idx.size and int(fold.train_idx[-1]) >= n:
            raise IndexError(
                f"fold {fold.label!r} holds train position {int(fold.train_idx[-1])} but "
                f"dates has {n} entries; the folds were built on a different index"
            )
        drop = np.zeros(n, dtype=bool)
        for first, last in _runs(fold.test_idx):
            drop |= (days >= days[first] - span) & (days <= days[last] + span)
        keep = fold.train_idx[~drop[fold.train_idx]]
        out.append(
            Fold(
                train_idx=keep.astype(np.int64),
                test_idx=fold.test_idx,
                label=f"{fold.label} (embargo {int(embargo_days)}d)",
            )
        )
    return out


def assert_partition(folds: Sequence[Fold], n: int) -> None:
    """Assert the folds' TEST sets partition `range(n)` exactly. Raises, returns None.

    Two failures, named separately because they have different causes: a position in two test
    sets (double-counted, and any pooled statistic over the folds is inflated) and a position
    in none (silently unevaluated, and a per-fold table that looks complete).
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    seen = np.zeros(n, dtype=np.int64)
    for fold in folds:
        if fold.test_idx.size and (int(fold.test_idx[0]) < 0 or int(fold.test_idx[-1]) >= n):
            raise AssertionError(
                f"fold {fold.label!r} holds a test position outside range({n}): "
                f"{int(fold.test_idx[0])}..{int(fold.test_idx[-1])}"
            )
        seen[fold.test_idx] += 1
    twice = np.flatnonzero(seen > 1)
    if twice.size:
        raise AssertionError(
            f"{twice.size} position(s) appear in more than one test set (first at "
            f"{int(twice[0])}, in {int(seen[twice[0]])} folds); every pooled statistic over "
            f"these folds counts them twice"
        )
    missing = np.flatnonzero(seen == 0)
    if missing.size:
        raise AssertionError(
            f"{missing.size} of {n} position(s) are in no test set (first at "
            f"{int(missing[0])}); they are never evaluated and nothing in a per-fold table "
            f"says so"
        )
