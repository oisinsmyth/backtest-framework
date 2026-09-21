"""Property tests for `validation/error_budget.py` and `validation/fit.py` (D606).

Conventions per D78 (derandomized hypothesis, seeding owned by the library rather than a
hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the seed but NOT
the examples drawn, so a failure here is reproducible within a run and the example set is
not byte-stable across a full-suite run and a single-file run). `max_examples=40` and
`deadline=None` keep the file inside the default gate.

What is worth a property here and what is not. The closed forms and the exact numbers are
pinned by `tests/golden/test_error_budget_ledger.py`, which was hand-worked; these check
the RELATIONS the two deposit documents reason with but never write down:

  * the zero-contribution delta is **exactly** 0 on designs nobody chose (the golden's is
    one design, and "exact on the case I picked" is the failure mode a property test
    exists for);
  * a table `leave_one_term_out` produced always passes `validate_error_budget` — the
    producer and the validator are written separately and nothing else makes them agree;
  * the rank column is a permutation that orders the deltas;
  * the feature budget's raise boundary sits exactly at `max_features`, for class counts
    and ceilings other than the doc's 3 and 36;
  * the retention verdict is exactly the conjunction of its two reported clauses, so a
    caller can never read a verdict the clauses do not support;
  * the registered stage order always runs and a permutation of it never does without a
    log entry.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.validation.error_budget import (
    ErrorBudgetRow,
    StageOrder,
    StageOrderError,
    Term,
    leave_one_term_out,
    ols_fitter,
    oos_error,
    validate_error_budget,
    write_error_budget_md,
)
from backtest_framework.validation.fit import (
    FeatureBudget,
    FeatureBudgetError,
    multiclass_log_loss,
    ols,
    retention_check,
)
from backtest_framework.validation.folds import Fold

# D78 / D537: derandomized, bounded, no deadline.
SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)


@pytest.fixture(scope="session")
def scratch(tmp_path_factory):
    """ONE directory for the whole file, deliberately session-scoped.

    A function-scoped `tmp_path` inside a `@given` test is created once and reused across
    every example, which hypothesis warns about; `tmp_path_factory.mktemp` called per
    example instead creates 40 directories per test and the filesystem, not the arithmetic,
    becomes the cost of this file.
    """
    return tmp_path_factory.mktemp("d606_property")


def _panel(seed: int, n_terms: int, n_rows: int, zero_at: int):
    """A synthetic panel with one exactly-zero column at `zero_at`, and two folds."""
    rng = np.random.default_rng(seed)
    cols = [rng.normal(size=n_rows) for _ in range(n_terms)]
    cols[zero_at] = np.zeros(n_rows)
    X = np.column_stack(cols)
    weights = rng.normal(size=n_terms)
    y = X @ weights + rng.normal(size=n_rows) * 0.25
    terms = [Term(f"t{j}", (lambda j: lambda x: np.asarray(x)[:, j])(j)) for j in range(n_terms)]
    half = n_rows // 2
    a = np.arange(0, half, dtype=np.int64)
    b = np.arange(half, n_rows, dtype=np.int64)
    folds = [
        Fold(train_idx=b, test_idx=a, label="A"),
        Fold(train_idx=a, test_idx=b, label="B"),
    ]
    return X, y, terms, folds


# ============================================================== the exactly-zero delta


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n_terms=st.integers(min_value=3, max_value=5),
    n_rows=st.integers(min_value=30, max_value=90),
    zero_at=st.integers(min_value=0, max_value=4),
)
@SETTINGS
def test_zero_column_delta_is_exactly_zero_on_any_design(
    seed: int, n_terms: int, n_rows: int, zero_at: int
) -> None:
    """Ledger 48 / index 19, generalised off the golden's one hand-worked design.

    `n_terms >= 3` because with two terms and one of them zero, removing the OTHER leaves a
    design with no columns at all and `ols_fitter` refuses it — correctly, and that refusal
    is pinned in `tests/unit/test_error_budget.py` rather than papered over here.
    """
    assume(zero_at < n_terms)
    X, y, terms, folds = _panel(seed, n_terms, n_rows, zero_at)
    fit_fn, predict_fn = ols_fitter(terms)
    rows = leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms)
    zero_row = next(r for r in rows if r.term == f"t{zero_at}")
    assert zero_row.delta_mse == 0.0
    assert zero_row.mse_without == zero_row.mse_full


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n_terms=st.integers(min_value=3, max_value=5),
    n_rows=st.integers(min_value=30, max_value=90),
    zero_at=st.integers(min_value=0, max_value=4),
)
@SETTINGS
def test_a_produced_table_always_validates(
    seed: int, n_terms: int, n_rows: int, zero_at: int
) -> None:
    """The producer and the validator were written separately; this is what ties them."""
    assume(zero_at < n_terms)
    X, y, terms, folds = _panel(seed, n_terms, n_rows, zero_at)
    fit_fn, predict_fn = ols_fitter(terms)
    contributions = leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms)
    rows = [
        ErrorBudgetRow.from_contribution(c, n_folds=len(folds), n_oos=n_rows)
        for c in contributions
    ]
    validate_error_budget(rows)
    assert sorted(r.rank for r in rows) == list(range(1, n_terms + 1))
    deltas = [r.delta_mse for r in sorted(rows, key=lambda r: r.rank)]
    assert deltas == sorted(deltas, reverse=True)


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n_terms=st.integers(min_value=3, max_value=4),
    n_rows=st.integers(min_value=40, max_value=90),
)
@SETTINGS
def test_a_produced_table_always_renders(
    seed: int, n_terms: int, n_rows: int, scratch
) -> None:
    X, y, terms, folds = _panel(seed, n_terms, n_rows, zero_at=n_terms - 1)
    fit_fn, predict_fn = ols_fitter(terms)
    contributions = leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms)
    rows = [
        ErrorBudgetRow.from_contribution(c, n_folds=2, n_oos=n_rows) for c in contributions
    ]
    path = scratch / "ERROR_BUDGET.md"
    raw = write_error_budget_md(
        rows, path, study="s", stage="S-A", date="2026-09-21"
    ).read_bytes()
    assert b"\r\n" not in raw and raw.endswith(b"\n")
    text = raw.decode("ascii")
    # one line per row, plus the two table lines, inside the rendered table
    assert sum(1 for line in text.split("\n") if line.startswith("| ")) == n_terms + 1
    for row in rows:
        assert f"| {row.rank} | {row.term} |" in text


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n_rows=st.integers(min_value=30, max_value=90),
)
@SETTINGS
def test_pooled_oos_mse_is_the_pooled_sum_over_the_pooled_count(seed: int, n_rows: int) -> None:
    X, y, terms, folds = _panel(seed, 3, n_rows, zero_at=2)
    fit_fn, predict_fn = ols_fitter(terms)
    out = oos_error(folds, X, y, fit_fn, predict_fn, ("t0", "t1"))
    assert out.n == sum(f.n for f in out.per_fold) == n_rows
    assert out.mse >= 0.0
    assert out.mse == sum(f.sse for f in out.per_fold) / out.n


# ======================================================================== fit relations


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n=st.integers(min_value=20, max_value=200),
    k=st.integers(min_value=1, max_value=4),
)
@SETTINGS
def test_ols_residuals_are_orthogonal_to_the_design(seed: int, n: int, k: int) -> None:
    assume(n > k + 2)
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, k))
    y = rng.normal(size=n)
    fit = ols(y, X)
    assert fit.resid.tobytes() == (y - X @ fit.coef).tobytes()
    scale = max(1.0, float(np.max(np.abs(X))) * float(np.max(np.abs(y))) * n)
    assert float(np.max(np.abs(X.T @ fit.resid))) < 1e-8 * scale
    assert np.all(fit.se_ols >= 0.0)
    assert np.all(fit.se_nw >= 0.0)


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n=st.integers(min_value=20, max_value=120),
)
@SETTINGS
def test_ols_recovers_an_exact_linear_relation(seed: int, n: int) -> None:
    """With no noise the fit is exact, so every residual is at machine scale."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, 2))
    beta = rng.normal(size=2)
    fit = ols(X @ beta, X)
    assert float(np.max(np.abs(fit.coef - beta))) < 1e-8
    assert float(np.max(np.abs(fit.resid))) < 1e-8


@given(
    seed=st.integers(min_value=0, max_value=10_000),
    n=st.integers(min_value=2, max_value=60),
    n_classes=st.integers(min_value=2, max_value=6),
)
@SETTINGS
def test_multiclass_log_loss_is_non_negative_and_row_order_invariant(
    seed: int, n: int, n_classes: int
) -> None:
    rng = np.random.default_rng(seed)
    raw = rng.random((n, n_classes)) + 0.05
    p = raw / raw.sum(axis=1, keepdims=True)
    y = rng.integers(0, n_classes, size=n)
    loss = multiclass_log_loss(p, y)
    assert loss >= 0.0
    assert math.isfinite(loss)
    order = rng.permutation(n)
    shuffled = multiclass_log_loss(p[order], y[order])
    assert shuffled == pytest.approx(loss, rel=0, abs=1e-12)
    # a perfectly confident, correct model loses (almost) nothing
    certain = np.full((n, n_classes), 1e-300)
    certain[np.arange(n), y] = 1.0
    certain = certain / certain.sum(axis=1, keepdims=True)
    assert multiclass_log_loss(certain, y) < 1e-6


# ========================================================================= the budget


@given(
    classes=st.integers(min_value=1, max_value=8),
    ceiling=st.integers(min_value=2, max_value=200),
    n_features=st.integers(min_value=0, max_value=60),
)
@SETTINGS
def test_feature_budget_raises_exactly_above_max_features(
    classes: int, ceiling: int, n_features: int
) -> None:
    assume(ceiling >= 2 * classes)
    budget = FeatureBudget(non_base_classes=classes, ceiling=ceiling)
    assert budget.parameters(budget.max_features) <= ceiling
    assert budget.parameters(budget.max_features + 1) > ceiling
    if n_features <= budget.max_features:
        assert budget.assert_within(n_features) == classes * (n_features + 1)
    else:
        with pytest.raises(FeatureBudgetError):
            budget.assert_within(n_features)


@given(
    prev=st.floats(min_value=1e-3, max_value=10.0, allow_nan=False, allow_infinity=False),
    new=st.floats(min_value=0.0, max_value=10.0, allow_nan=False, allow_infinity=False),
    dv_prev=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    dv_new=st.floats(min_value=-5.0, max_value=5.0, allow_nan=False, allow_infinity=False),
    rel=st.floats(min_value=0.0, max_value=0.5, allow_nan=False, allow_infinity=False),
)
@SETTINGS
def test_retention_verdict_is_exactly_the_conjunction_of_its_clauses(
    prev: float, new: float, dv_prev: float, dv_new: float, rel: float
) -> None:
    result = retention_check(prev, new, dv_prev, dv_new, rel=rel)
    assert result.rel_reduction == (prev - new) / prev
    assert result.dv_not_reduced == (dv_new >= dv_prev)
    assert result.kept == ((result.rel_reduction >= rel) and result.dv_not_reduced)
    # both clauses are always readable from the reason, whichever decided
    assert "clause 1" in result.reason or "clause 2" in result.reason
    if result.kept:
        assert "clause 1" in result.reason and "clause 2" in result.reason


# ==================================================================== the stage order


STAGES = ("S-A", "S-B", "S-C", "S-D", "S-E")


@given(
    n_stages=st.integers(min_value=2, max_value=5),
    n_done=st.integers(min_value=0, max_value=4),
)
@SETTINGS
def test_the_registered_order_always_runs(n_stages: int, n_done: int, scratch) -> None:
    assume(n_done < n_stages)
    registered = STAGES[:n_stages]
    order = StageOrder(registered, scratch / "absent.jsonl")
    assert order.next(registered, completed=registered[:n_done], today="2026-09-21") == (
        registered[n_done]
    )


@given(
    n_stages=st.integers(min_value=2, max_value=5),
    seed=st.integers(min_value=0, max_value=10_000),
)
@SETTINGS
def test_any_permutation_without_a_log_entry_is_refused(
    n_stages: int, seed: int, scratch
) -> None:
    registered = STAGES[:n_stages]
    rng = np.random.default_rng(seed)
    planned = tuple(registered[i] for i in rng.permutation(n_stages))
    order = StageOrder(registered, scratch / "absent.jsonl")
    if planned == registered:
        assert order.next(planned, today="2026-09-21") == registered[0]
    else:
        with pytest.raises(StageOrderError):
            order.next(planned, today="2026-09-21")


@given(
    n_stages=st.integers(min_value=2, max_value=5),
    extra=st.sampled_from(["S-Z", "extra", "C0", "S-A2", " "]),
)
@SETTINGS
def test_an_unregistered_stage_is_always_refused(
    n_stages: int, extra: str, scratch
) -> None:
    """Deposit decision D28, as an invariant: no planned order containing an unregistered
    stage is ever permitted, whatever the log holds."""
    registered = STAGES[:n_stages]
    order = StageOrder(registered, scratch / "absent.jsonl")
    with pytest.raises(StageOrderError, match="not registered"):
        order.next(registered + (extra,), today="2026-09-21")
