"""Invariants of `validation/lookahead.py` and `validation/folds.py` (D593).

Gate P. CONTRIBUTING.md names look-ahead as the archetype for this tier — *"perturbing bars
after the decision bar must change nothing before it, and no finite set of examples covers
the shapes that would trigger it"* — and that is the first family below: the lag is
quantified over grids and delays rather than checked at three hand-picked indices, and the
static scan is quantified over identifier names and offsets rather than over the twelve
strings the unit test spells out.

The second family is the folds', and it is the deposit docs' own claim quantified:
`INDEX_REWEIGHT_FLOW_PREREG.md` unit test 9 asks that *a model evaluated on year y was not
fitted using year y data* — a statement about every fold on every calendar, which is the
shape a property test is for and the shape a single golden calendar is not. The three
invariants named in the brief are here in these words: **every LOYO fold's test year is
absent from its train indices; the union of the test sets is the whole index; purging never
removes a test index.**

Conventions per D78 (derandomized hypothesis, seeding owned by the library rather than a
hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the seed but NOT the
examples drawn, since hypothesis 6.156.6 harvests the constant pool from `sys.modules` at
test time — so a failure here is reproducible within a run but the example set is not
byte-stable between a full-suite run and a single-file one; reproduce a failure with the
whole suite). `max_examples=40` and `deadline=None` keep the file cheap enough for the
default gate.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.validation.folds import (
    assert_partition,
    leave_one_year_out,
    purged,
    year_blocks,
)
from backtest_framework.validation.lookahead import (
    delayed,
    forward_index_sites,
    lag1,
    retained_edge,
)

REPO = Path(__file__).resolve().parents[2]

# D78 / D537: derandomized, bounded, no deadline.
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = _load("run_concentrated_short", "run_concentrated_short.py")

CELL = st.one_of(
    st.floats(min_value=-1e6, max_value=1e6, allow_nan=False),
    st.just(float("nan")),
    st.just(float("inf")),
    st.just(float("-inf")),
    st.just(-0.0),
)
NAME = st.sampled_from(["t", "i", "idx", "bar", "t0", "j"])
OFFSET = st.integers(min_value=1, max_value=9)


@st.composite
def grids(draw, min_rows: int = 1, max_rows: int = 6, min_cols: int = 1, max_cols: int = 12):
    rows = draw(st.integers(min_value=min_rows, max_value=max_rows))
    cols = draw(st.integers(min_value=min_cols, max_value=max_cols))
    flat = draw(st.lists(CELL, min_size=rows * cols, max_size=rows * cols))
    return np.array(flat, dtype=float).reshape(rows, cols)


@st.composite
def date_indices(draw):
    """A sorted, unique daily index of 8-60 sessions spanning up to about eleven years."""
    n = draw(st.integers(min_value=8, max_value=60))
    offsets = draw(
        st.lists(st.integers(min_value=0, max_value=4000), min_size=n, max_size=n, unique=True)
    )
    return np.datetime64("2012-01-02", "D") + np.array(
        sorted(offsets), dtype="timedelta64[D]"
    )


# --------------------------------------------------------------------------------------------
# the lag
# --------------------------------------------------------------------------------------------
@SETTINGS
@given(a=grids())
def test_lag1_is_the_runners_lag_on_every_grid(a):
    """Bit-identical, over the shapes and the non-finite values a score grid actually carries."""
    assert lag1(a).tobytes() == C.lag1(a).tobytes()


@SETTINGS
@given(a=grids(), k=st.integers(min_value=0, max_value=6))
def test_delayed_blanks_the_first_k_columns_and_shifts_the_rest(a, k):
    out = delayed(a, k)
    assert out.shape == a.shape
    blanked = min(k, a.shape[1])
    assert np.isnan(out[:, :blanked]).all()
    if k < a.shape[1]:
        assert np.array_equal(out[:, k:], a[:, : a.shape[1] - k], equal_nan=True)


@SETTINGS
@given(
    a=grids(),
    i=st.integers(min_value=0, max_value=4),
    j=st.integers(min_value=0, max_value=4),
)
def test_delays_add(a, i, j):
    """`delayed(., i+j)` is `delayed(delayed(., i), j)` — a delay is a composition of ONE lag.

    The reason this is a property and not a comment is `scripts/d290_skip_bar_test.py`'s: the
    alternative implementation of a delay — shifting the return grid — does not compose, and
    a study that mixed the two would be quietly scoring two different constructions.
    """
    assert np.array_equal(delayed(a, i + j), delayed(delayed(a, i), j), equal_nan=True)


@SETTINGS
@given(a=grids(min_cols=2))
def test_nothing_before_the_decision_bar_can_see_a_perturbation_after_it(a):
    """CONTRIBUTING.md's archetype: change a later bar, and the lagged grid before it is fixed."""
    t = a.shape[1] - 1
    perturbed = a.copy()
    perturbed[:, t] = 12345.0
    before, after = lag1(a), lag1(perturbed)
    assert np.array_equal(before[:, : t + 1], after[:, : t + 1], equal_nan=True)


@SETTINGS
@given(a=grids(min_cols=4))
def test_retained_edge_on_a_finite_cell_count_is_the_column_ratio(a):
    """An `edge_fn` whose answer is known in closed form, so the plumbing is checkable."""
    dense = np.nan_to_num(a, nan=0.0, posinf=0.0, neginf=0.0)
    rows, cols = dense.shape
    out = retained_edge(lambda g: float(np.isfinite(g).sum()), dense)
    for d in (0, 1, 2, 3):
        assert out[d] == rows * (cols - d)
    assert out["retained_fraction_at_1"] == (cols - 1) / cols


# --------------------------------------------------------------------------------------------
# the static scan
# --------------------------------------------------------------------------------------------
@SETTINGS
@given(name=NAME, k=OFFSET)
def test_forward_shapes_are_always_caught(name, k):
    for source, kind in (
        (f"x[{name} + {k}]", "forward_index"),
        (f"x[{k} + {name}]", "forward_index"),
        (f"x[:, {name} + {k}]", "forward_index"),
        (f"x[{name} + {k}:]", "forward_slice"),
        (f"df.iloc[{name} + {k}]", "forward_iloc"),
        (f"df.shift(-{k})", "negative_shift"),
        (f"np.roll(x, -{k})", "negative_roll"),
    ):
        assert [s.kind for s in forward_index_sites(source)] == [kind], source


@SETTINGS
@given(name=NAME, k=OFFSET)
def test_backward_shapes_are_never_caught(name, k):
    """The half that decides whether anyone leaves the scan switched on."""
    for source in (
        f"x[{name} - {k}]",
        f"x[:{name} + {k}]",
        f"x[:, :{name} + {k}]",
        f"x[{name} - {k}:{name} + {k}]",
        f"x[:, :-{k}]",
        f"x[:, {k}:]",
        f"df.shift({k})",
        f"np.roll(x, {k})",
        f"x[{name} + other]",
    ):
        assert forward_index_sites(source) == [], source


# --------------------------------------------------------------------------------------------
# the folds
# --------------------------------------------------------------------------------------------
@SETTINGS
@given(dates=date_indices())
def test_every_loyo_folds_test_year_is_absent_from_its_train_indices(dates):
    """`INDEX_REWEIGHT_FLOW_PREREG.md` unit test 9, quantified over calendars."""
    years = dates.astype("datetime64[Y]")
    assume(len(set(years.tolist())) >= 2)
    for fold in leave_one_year_out(dates, min_days=1):
        held = set(years[fold.test_idx].tolist())
        assert len(held) == 1
        assert held.isdisjoint(set(years[fold.train_idx].tolist()))


@SETTINGS
@given(dates=date_indices())
def test_the_union_of_the_loyo_test_sets_is_the_whole_index(dates):
    assume(len(set(dates.astype("datetime64[Y]").tolist())) >= 2)
    folds = leave_one_year_out(dates, min_days=1)
    assert_partition(folds, dates.size)
    union = np.concatenate([f.test_idx for f in folds])
    assert np.array_equal(np.sort(union), np.arange(dates.size))
    assert len(folds) == len(year_blocks(dates))


@SETTINGS
@given(dates=date_indices(), embargo=st.integers(min_value=0, max_value=400))
def test_purging_never_removes_a_test_index_and_only_shrinks_train(dates, embargo):
    assume(len(set(dates.astype("datetime64[Y]").tolist())) >= 2)
    before = leave_one_year_out(dates, min_days=1)
    after = purged(before, dates, embargo)
    for old, new in zip(before, after):
        assert np.array_equal(new.test_idx, old.test_idx), "a purge is about the FIT only"
        assert set(new.train_idx.tolist()) <= set(old.train_idx.tolist())


@SETTINGS
@given(dates=date_indices(), embargo=st.integers(min_value=0, max_value=400))
def test_no_retained_training_date_lies_inside_the_embargo_of_its_test_block(dates, embargo):
    """The purge's contract, stated as the thing a leak would violate."""
    assume(len(set(dates.astype("datetime64[Y]").tolist())) >= 2)
    span = np.timedelta64(embargo, "D")
    for fold in purged(leave_one_year_out(dates, min_days=1), dates, embargo):
        test_days = dates[fold.test_idx]
        for day in dates[fold.train_idx]:
            # Each contiguous test run is purged separately, so the guarantee is per run:
            # no retained training date is within `embargo` of a test date it is contiguous
            # with. Checking the strongest form that holds for a single-block fold — a LOYO
            # test set is one calendar year and therefore one run whenever the index has no
            # gap inside it — via the fold's own endpoints.
            if test_days[0] - span <= day <= test_days[-1] + span:
                assert False, f"{day} survived an embargo of {embargo}d around the block"


@SETTINGS
@given(dates=date_indices())
def test_a_bigger_embargo_never_retains_more_training_data(dates):
    assume(len(set(dates.astype("datetime64[Y]").tolist())) >= 2)
    folds = leave_one_year_out(dates, min_days=1)
    sizes = [
        sum(f.train_idx.size for f in purged(folds, dates, e)) for e in (0, 3, 30, 200)
    ]
    assert sizes == sorted(sizes, reverse=True)
