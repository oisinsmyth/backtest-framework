"""The error budget, and the stage-order gate that hangs off it (D606).

THE SPEC, QUOTED. `SETTLEMENT_FLOW_LEDGER_PREREG.md` §8A.1, "Error budget":

    After each stage is evaluated, decompose the out-of-sample window-flow forecast error
    `e = S_win,realised - Q_rem,predicted`:
    1. **Leave-one-term-out:** the change in OOS mean squared error when each active
       participant term is removed.
    2. **Term-level checks where a measurable counterpart exists:** e.g. predicted
       creations vs realised dShares; predicted swap-routed exposure vs the COT-implied
       change (8A.2); predicted roll flow vs holdings changes.

    Output: `results/settlement_flow/ERROR_BUDGET.md`, ranking terms by attributable error.
    **Use:** among *not-yet-run* stages, the order may be changed to target the largest
    attributable error first. The reordering decision is logged in the doc's decision log
    **before** the next stage runs. No new, unregistered stage can be added this way.

and deposit decision D28 (line 1014): *"Error budget may reorder not-yet-run stages, never
add unregistered ones | Focuses effort on the biggest error without opening a back door to
new tests"*. Unit tests 48 and 49 (lines 754-755):

    48. Error budget: removing a term with zero forecast contribution changes OOS MSE by
        zero on synthetic data.
    49. Stage reordering: the code refuses to run a reordered stage unless a matching
        decision-log entry exists.

`INDEX_REWEIGHT_FLOW_PREREG.md` §5A.1 is the same instrument with two components:

    After C0 and after each stage, decompose the forecast error into (a) the flow forecast
    (drift, AUM, kappa) and (b) impact. Use leave-one-component-out changes in
    out-of-sample error, plus the auxiliary checks below. Output:
    `results/index_reweight/ERROR_BUDGET.md`. Remaining stages may be reordered to target
    the largest error, logged in the decision log **before** running. No new stages may be
    added this way.

with unit tests 19 and 20 (lines 367-368): *"Error budget: removing a zero-contribution
component leaves OOS error unchanged on synthetic data"* and *"Stage reordering requires a
matching decision-log entry."* The two docs' "term" and "component" are the same object
here, so one module serves both.

WHY THE ZERO-CONTRIBUTION TERM IS DROPPED AND NOT FITTED AT ZERO
---------------------------------------------------------------
Units 48 and 19 say *"changes OOS MSE by zero"* and *"leaves OOS error unchanged"*, and
this module asserts that with `delta_mse == 0.0` rather than a tolerance. That is only
achievable by construction. A zero column left in the design makes the least-squares
problem rank deficient, and the surviving coefficients of a rank-deficient solve are not a
bitwise function of which zero columns are present — they move in the last places, the
predictions move with them, and the delta comes out at 1e-17 rather than at 0. `ols_fitter`
therefore DROPS any term whose column is exactly zero on the training rows, so that "all
terms" and "all terms but the zero one" are **the same design matrix, byte for byte**: the
same call, the same result, and a delta that is exactly 0 because it is the same double
minus itself. `fit.ols` refuses a rank-deficient design outright, which is the other half
of the same decision.

The exactness claim is precisely: **a term whose column is exactly zero on every TRAINING
block changes the OOS MSE by exactly zero.** A column that is zero on train and non-zero on
test also qualifies, because the fitted model never carried it.

THE SIGN CONVENTION, BECAUSE §8A.1 DOES NOT FIX IT
--------------------------------------------------
`delta_mse = mse_without - mse_full`. POSITIVE means removing the term made the
out-of-sample forecast worse. "Ranking terms by attributable error" is read as this
quantity, descending, so rank 1 is the term whose removal costs most. The phrase admits the
opposite reading — the error a badly-modelled term *leaves behind* — and nothing in either
document disambiguates it; this module states which it computes rather than leaving a
reader to infer it from a table.

WHY `Fold` AND NOT `walk_forward_windows`
-----------------------------------------
`validation/walk_forward.py` (D22/D28/D85) is the stronger guard of the two: it hands a
fitter a `DataView` BUILT from the training slice, so the test window is physically absent
and there is no index, attribute or reflection path to a test bar. It is also the wrong
shape here, for D593's reason — it cuts bar-counted, contiguous, gapless windows over
`TimestampedBar`s, and §8A.1's budget is scored on whatever folds the study's own validation
uses, which for the index document is leave-one-year-out over annual events. `oos_error`
therefore takes `Fold`s, whose `__post_init__` refuses train/test overlap at construction,
and re-checks the overlap itself besides: a frozen dataclass is not sealed, and
`object.__setattr__` reaches through it. The property that matters — a model evaluated on a
block was not fitted using that block — is carried; the mechanism carrying it is weaker, and
saying so is the point of this paragraph.

WHERE THE PAGE LIVES IN THIS REPOSITORY
---------------------------------------
The deposit names `results/<study>/ERROR_BUDGET.md` and there is no root `results/` tree
here. Same mapping `validation/programme.py:21-26` recorded for `PROGRAMME_REGISTRY.md`,
and the same reason `validation/power.py:write_power_md` gave for declining to invent one:

    results/settlement_flow/ERROR_BUDGET.md -> docs/results/SETTLEMENT_FLOW_ERROR_BUDGET.md
    results/index_reweight/ERROR_BUDGET.md  -> docs/results/INDEX_REWEIGHT_ERROR_BUDGET.md

`error_budget_page_path` computes it. **No page is committed by D606**, because no study
has run and a rendered page with no study behind it is a claim about nothing.

This module reads no fixture and computes no strategy return.
"""

from __future__ import annotations

import datetime as _dt
import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from .fit import OLSFit, ols
from .folds import Fold

__all__ = [
    "ErrorBudgetRow",
    "FittedTerms",
    "FoldError",
    "OOSError",
    "ReorderEntry",
    "StageOrder",
    "StageOrderError",
    "Term",
    "TermContribution",
    "error_budget_page_path",
    "leave_one_term_out",
    "ols_fitter",
    "oos_error",
    "validate_error_budget",
    "write_error_budget_md",
]


# --------------------------------------------------------------------------- terms


@dataclass(frozen=True, eq=False)
class Term:
    """One participant term (ledger) or forecast component (index reweight).

    `predict(X) -> (n,)` is the term's raw contribution to the design: the column a fitter
    is allowed to weight, in whatever units the study's `X` carries. `X` is deliberately
    untyped — an array, a mapping, a record array — because the fitter is abstract and this
    module never looks inside it.

    `eq=False`: a term is identified by its `name`, and two `Term`s wrapping the same
    closure are not interchangeable objects. Compare names.
    """

    name: str
    predict: Callable[[Any], np.ndarray]

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(f"a term needs a non-blank name, got {self.name!r}")
        if not callable(self.predict):
            raise TypeError(f"term {self.name!r} has a non-callable predict")

    def column(self, X: Any, n_rows: int) -> np.ndarray:
        """`predict(X)` as a finite 1-D float array of exactly `n_rows` entries. Raises."""
        col = np.asarray(self.predict(X), dtype=float)
        if col.ndim != 1:
            raise ValueError(
                f"term {self.name!r} returned shape {col.shape}; a term is one column"
            )
        if col.size != n_rows:
            raise ValueError(
                f"term {self.name!r} returned {col.size} value(s) for {n_rows} row(s); the "
                f"term and the fold were built on different row sets"
            )
        bad = np.flatnonzero(~np.isfinite(col))
        if bad.size:
            raise ValueError(
                f"term {self.name!r} returned {bad.size} non-finite value(s), first at row "
                f"{int(bad[0])}. A NaN column is not a zero column and must not be treated "
                f"as one: mask the rows upstream and say how many were masked."
            )
        return col


@dataclass(frozen=True, eq=False)
class FittedTerms:
    """What `ols_fitter`'s `fit_fn` returns. A Kalman-style fitter would return its own."""

    active: tuple[str, ...]
    """The terms the caller asked for, in their registered order."""
    used: tuple[str, ...]
    """Those actually in the design, in design-column order."""
    dropped_zero: tuple[str, ...]
    """Active terms whose training column was exactly zero. Carried, never silently lost."""
    fit: OLSFit


def ols_fitter(
    terms: Sequence[Term], *, nw_lag: int = 0
) -> tuple[Callable[[Any, np.ndarray, tuple[str, ...]], FittedTerms], Callable[[FittedTerms, Any], np.ndarray]]:
    """`(fit_fn, predict_fn)` over `terms`, by `fit.ols`. The reference implementation.

    `fit_fn(X_train, y_train, active) -> FittedTerms` builds the design from the active
    terms' columns IN REGISTERED ORDER, drops any column that is exactly zero (see the
    module docstring — this is what makes unit 48's delta exactly 0), and fits.
    `predict_fn(model, X_test) -> (n,)` rebuilds the same columns and returns
    `design @ coef`.

    The pair is returned rather than an object with two methods so that a study can supply
    any other pair — a Kalman update, a constrained maximum likelihood, the ledger's
    p/R/n/a0..a3 model — without this module knowing anything about it. `oos_error` and
    `leave_one_term_out` only ever call these two callables.
    """
    by_name = {}
    for t in terms:
        if t.name in by_name:
            raise ValueError(
                f"term {t.name!r} appears twice; a leave-one-term-out table indexed by name "
                f"cannot tell the two apart"
            )
        by_name[t.name] = t
    order = tuple(by_name)

    def _design(X: Any, active: tuple[str, ...], n_rows: int) -> tuple[np.ndarray, tuple[str, ...], tuple[str, ...]]:
        unknown = [a for a in active if a not in by_name]
        if unknown:
            raise KeyError(f"term(s) not registered with this fitter: {unknown}")
        if len(set(active)) != len(active):
            raise ValueError(f"active holds a repeated term: {list(active)}")
        cols, used, dropped = [], [], []
        for name in order:
            if name not in active:
                continue
            col = by_name[name].column(X, n_rows)
            if not np.any(col):
                dropped.append(name)
                continue
            cols.append(col)
            used.append(name)
        if not cols:
            raise ValueError(
                f"every active term has an exactly-zero column on these rows "
                f"({list(active)}); there is no design to fit and no forecast to score"
            )
        return np.column_stack(cols), tuple(used), tuple(dropped)

    def fit_fn(X_train: Any, y_train: np.ndarray, active: tuple[str, ...]) -> FittedTerms:
        yy = np.asarray(y_train, dtype=float)
        design, used, dropped = _design(X_train, tuple(active), yy.size)
        return FittedTerms(
            active=tuple(active),
            used=used,
            dropped_zero=dropped,
            fit=ols(yy, design, nw_lag=nw_lag),
        )

    def predict_fn(model: FittedTerms, X_test: Any) -> np.ndarray:
        if not model.used:
            raise ValueError("the fitted model has no design columns")
        probe = by_name[model.used[0]].predict(X_test)
        n_rows = int(np.asarray(probe, dtype=float).size)
        design = np.column_stack([by_name[n].column(X_test, n_rows) for n in model.used])
        return design @ model.fit.coef

    return fit_fn, predict_fn


# --------------------------------------------------------------------------- OOS error


@dataclass(frozen=True)
class FoldError:
    """One fold's contribution. `sse` is in squared units of `y`; `n` is a count.

    The per-fold MEAN is deliberately a property and not a stored field: on the golden's
    two folds it is 28/6 and 38/6, neither of which is exactly representable, while the
    pooled 66/12 is. A table that stored the means and summed them would be a different
    (and worse) statistic from the pooled one, weighted by nothing.
    """

    label: str
    n: int
    sse: float

    @property
    def mse(self) -> float:
        return self.sse / self.n


@dataclass(frozen=True)
class OOSError:
    """Pooled out-of-sample mean squared error. `mse = sum(sse) / sum(n)` over the folds.

    Pooled, not the mean of the folds' means: the folds of `leave_one_year_out` have
    different lengths and averaging their means would weight a 210-session year like a
    252-session one.
    """

    mse: float
    n: int
    per_fold: tuple[FoldError, ...]


def oos_error(
    folds: Sequence[Fold],
    X: Any,
    y: np.ndarray,
    fit_fn: Callable[[Any, np.ndarray, tuple[str, ...]], Any],
    predict_fn: Callable[[Any, Any], np.ndarray],
    active: Sequence[str],
) -> OOSError:
    """Fit on each fold's train rows, score on its test rows, pool.

    THE TEST INDEX NEVER ENTERS THE FIT. `folds.Fold.__post_init__` refuses a fold whose
    train and test indices intersect, at construction, so the guarantee is structural; this
    function re-checks anyway, because a `Fold` is a frozen dataclass and `object.__setattr__`
    can still reach through it, and because the check costs one `intersect1d` against a
    result nobody can audit afterwards. `tests/unit/test_error_budget.py` proves the
    re-check fires by doing exactly that.

    `X` is passed to `fit_fn` and `predict_fn` as `_rows(X, idx)` — a row subset — for an
    ndarray or a mapping of arrays. Anything else is handed a `RowView` and the fitter is
    responsible for it.
    """
    yy = np.asarray(y, dtype=float)
    if yy.ndim != 1:
        raise ValueError(f"y must be 1-D, got shape {yy.shape}")
    if not folds:
        raise ValueError("no folds; the out-of-sample error of an empty fold list is not 0")
    act = tuple(str(a) for a in active)
    if not act:
        raise ValueError("no active terms; there is nothing to fit")
    n_all = yy.size

    per_fold: list[FoldError] = []
    total_sse = 0.0
    total_n = 0
    for fold in folds:
        train = np.asarray(fold.train_idx)
        test = np.asarray(fold.test_idx)
        for name, idx in (("train_idx", train), ("test_idx", test)):
            if idx.size and (int(idx.min()) < 0 or int(idx.max()) >= n_all):
                raise IndexError(
                    f"fold {fold.label!r} {name} reaches position {int(idx.max())} but y has "
                    f"{n_all} row(s); the folds were built on a different index"
                )
        if train.size == 0:
            raise ValueError(f"fold {fold.label!r} has an empty training set")
        leak = np.intersect1d(train, test)
        if leak.size:
            raise ValueError(
                f"fold {fold.label!r} would be fitted on {leak.size} of the position(s) it "
                f"is scored on (first at {int(leak[0])}). A model evaluated on a block must "
                f"not have been fitted using that block."
            )
        model = fit_fn(_rows(X, train), yy[train], act)
        pred = np.asarray(predict_fn(model, _rows(X, test)), dtype=float)
        if pred.shape != (test.size,):
            raise ValueError(
                f"fold {fold.label!r}: predict_fn returned shape {pred.shape} for "
                f"{test.size} test row(s)"
            )
        bad = np.flatnonzero(~np.isfinite(pred))
        if bad.size:
            raise ValueError(
                f"fold {fold.label!r}: predict_fn returned {bad.size} non-finite "
                f"prediction(s), first at test position {int(test[bad[0]])}"
            )
        resid = yy[test] - pred
        sse = float(resid @ resid)
        per_fold.append(FoldError(label=fold.label, n=int(test.size), sse=sse))
        total_sse += sse
        total_n += int(test.size)

    if total_n == 0:
        raise ValueError("the folds hold no test rows between them")
    return OOSError(mse=total_sse / total_n, n=total_n, per_fold=tuple(per_fold))


class _RowView:
    """`X` restricted to `idx`, for an `X` this module cannot subset itself."""

    __slots__ = ("source", "idx")

    def __init__(self, source: Any, idx: np.ndarray) -> None:
        self.source = source
        self.idx = idx


def _rows(X: Any, idx: np.ndarray) -> Any:
    if isinstance(X, np.ndarray):
        return X[idx]
    if isinstance(X, dict):
        return {k: (v[idx] if isinstance(v, np.ndarray) else v) for k, v in X.items()}
    return _RowView(X, idx)


# --------------------------------------------------------------------------- the budget


@dataclass(frozen=True)
class TermContribution:
    """One row of the leave-one-term-out table, before it becomes an `ErrorBudgetRow`.

    `delta_mse = mse_without - mse_full`, in squared units of `y`. `rank` is 1-based and
    ranks `delta_mse` DESCENDING, so rank 1 is the term whose removal costs most.
    """

    term: str
    mse_full: float
    mse_without: float
    delta_mse: float
    rank: int


def leave_one_term_out(
    folds: Sequence[Fold],
    X: Any,
    y: np.ndarray,
    fit_fn: Callable[[Any, np.ndarray, tuple[str, ...]], Any],
    predict_fn: Callable[[Any, Any], np.ndarray],
    terms: Sequence[Term] | Sequence[str],
) -> list[TermContribution]:
    """§8A.1 item 1 / §5A.1: the change in OOS MSE when each active term is removed.

    `terms` may be `Term` objects or bare names — `leave_one_term_out` never calls
    `predict` itself, only `fit_fn` and `predict_fn`, so the names are all it needs.

    Removing a term must leave at least one; with a single term there is nothing to compare
    against and that raises rather than returning a one-row table whose delta is the full
    model's own error.
    """
    names = tuple(t.name if isinstance(t, Term) else str(t) for t in terms)
    if len(set(names)) != len(names):
        raise ValueError(f"terms holds a repeated name: {list(names)}")
    if len(names) < 2:
        raise ValueError(
            f"leave-one-term-out needs at least 2 terms, got {len(names)}: {list(names)}. "
            f"Removing the only term leaves no design, and its 'delta' would be the full "
            f"model's own error rather than a contribution."
        )
    full = oos_error(folds, X, y, fit_fn, predict_fn, names)
    rows = []
    for name in names:
        without = oos_error(
            folds, X, y, fit_fn, predict_fn, tuple(n for n in names if n != name)
        )
        rows.append((name, without.mse))
    ordered = sorted(rows, key=lambda r: (-(r[1] - full.mse), r[0]))
    return [
        TermContribution(
            term=name,
            mse_full=full.mse,
            mse_without=mse_without,
            delta_mse=mse_without - full.mse,
            rank=i + 1,
        )
        for i, (name, mse_without) in enumerate(ordered)
    ]


# --------------------------------------------------------------------------- the page


@dataclass(frozen=True)
class ErrorBudgetRow:
    """One line of `ERROR_BUDGET.md`.

    Units: `mse_full`, `mse_without` and `delta_mse` are in squared units of the forecast
    error `e = S_win,realised - Q_rem,predicted`, whatever the study measures that in.
    `n_oos` and `n_folds` are counts. `counterpart` is §8A.1 item 2's term-level check,
    free text, and is None where no measurable counterpart exists — which is the common
    case and not a defect.
    """

    term: str
    n_folds: int
    n_oos: int
    mse_full: float
    mse_without: float
    delta_mse: float
    rank: int
    counterpart: str | None = None

    @classmethod
    def from_contribution(
        cls, c: TermContribution, *, n_folds: int, n_oos: int, counterpart: str | None = None
    ) -> "ErrorBudgetRow":
        return cls(
            term=c.term,
            n_folds=int(n_folds),
            n_oos=int(n_oos),
            mse_full=c.mse_full,
            mse_without=c.mse_without,
            delta_mse=c.delta_mse,
            rank=c.rank,
            counterpart=counterpart,
        )


_ERROR_BUDGET_REQUIRED: tuple[tuple[str, str], ...] = (
    # CAUSE BEFORE SYMPTOM, the ordering `power.py:578 _TRACK_MAP_REQUIRED` uses. A row
    # with no term name identifies nothing, so it is named first; a row with no
    # observations has no MSE to speak of; a delta cannot exist without both MSEs; and a
    # rank cannot exist without a delta. Reporting "row 2 has no rank" about a row that has
    # no observations sends the reader to the wrong end of the pipeline.
    ("term", "a term name"),
    ("n_folds", "a fold count"),
    ("n_oos", "an out-of-sample observation count"),
    ("mse_full", "the full model's OOS MSE"),
    ("mse_without", "the OOS MSE with the term removed"),
    ("delta_mse", "the change in OOS MSE (mse_without - mse_full)"),
    ("rank", "a rank"),
)


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (int, np.integer)):
        return False
    try:
        return not np.isfinite(float(value))
    except (TypeError, ValueError):
        return True


def validate_error_budget(rows: Sequence[ErrorBudgetRow]) -> None:
    """Raise `ValueError` naming the FIRST offending row and field. Returns None when clean.

    Empty input FAILS. An error budget with no rows is not an error budget with nothing to
    report: §8A.1 runs it "after each stage is evaluated", and a stage with no active terms
    did not happen.

    Beyond the per-field checks the table is checked as a whole, because the defects that
    actually happen here are cross-row ones: rows pasted together from two different runs
    (different `mse_full`, `n_oos` or `n_folds`), a hand-edited `delta_mse` that no longer
    equals `mse_without - mse_full`, and a rank column that no longer orders the deltas.
    """
    if not rows:
        raise ValueError(
            "the error budget has no rows. §8A.1 runs after each stage is evaluated; a "
            "table with nothing in it is not an empty result, it is a run that did not "
            "happen or a table that lost its rows."
        )
    for i, row in enumerate(rows):
        for field, what in _ERROR_BUDGET_REQUIRED:
            if _blank(getattr(row, field, None)):
                raise ValueError(
                    f"error-budget row {i} ({getattr(row, 'term', None)!r}) is missing "
                    f"{what} ({field}={getattr(row, field, None)!r})"
                )
        if int(row.n_folds) < 1:
            raise ValueError(f"error-budget row {i} ({row.term!r}) has n_folds={row.n_folds}")
        if int(row.n_oos) < 1:
            raise ValueError(f"error-budget row {i} ({row.term!r}) has n_oos={row.n_oos}")
        if int(row.rank) < 1:
            raise ValueError(f"error-budget row {i} ({row.term!r}) has rank={row.rank}")
        expected = float(row.mse_without) - float(row.mse_full)
        if float(row.delta_mse) != expected:
            raise ValueError(
                f"error-budget row {i} ({row.term!r}): delta_mse is {row.delta_mse!r} but "
                f"mse_without - mse_full is {expected!r}. The delta is not an independent "
                f"number and a row where it disagrees has been edited by hand."
            )
    names = [r.term for r in rows]
    if len(set(names)) != len(names):
        dup = next(n for n in names if names.count(n) > 1)
        raise ValueError(f"error-budget term {dup!r} appears {names.count(dup)} times")
    for field in ("mse_full", "n_oos", "n_folds"):
        values = {getattr(r, field) for r in rows}
        if len(values) > 1:
            raise ValueError(
                f"error-budget rows disagree on {field}: {sorted(values)}. Every row of one "
                f"budget is scored against the same full model on the same folds, so two "
                f"values mean two runs were pasted into one table."
            )
    ranks = [int(r.rank) for r in rows]
    if sorted(ranks) != list(range(1, len(rows) + 1)):
        raise ValueError(
            f"error-budget ranks are {ranks}, not a permutation of 1..{len(rows)}"
        )
    ordered = sorted(rows, key=lambda r: int(r.rank))
    for a, b in zip(ordered, ordered[1:]):
        if float(a.delta_mse) < float(b.delta_mse):
            raise ValueError(
                f"error-budget rank {a.rank} ({a.term!r}, delta {a.delta_mse!r}) is ranked "
                f"above rank {b.rank} ({b.term!r}, delta {b.delta_mse!r}) but has the "
                f"SMALLER delta. Ranking is by delta_mse descending (see the module "
                f"docstring's sign convention)."
            )


def error_budget_page_path(study: str, root: str | Path = ".") -> Path:
    """`docs/results/<STUDY>_ERROR_BUDGET.md` for the deposit's `results/<study>/...`."""
    s = str(study).strip()
    if not s:
        raise ValueError("study must be a non-blank name, e.g. 'settlement_flow'")
    return Path(root) / "docs" / "results" / f"{s.upper()}_ERROR_BUDGET.md"


_PREAMBLE = (
    "Terms ranked by attributable error. `delta_mse = mse_without - mse_full` is the change",
    "in out-of-sample mean squared error when the term is removed from the design",
    "(SETTLEMENT_FLOW_LEDGER_PREREG.md 8A.1 item 1). A term whose column is exactly zero on",
    "every training block is dropped from the design rather than fitted at zero, so its delta",
    "is exactly 0.",
)

_COLUMNS = (
    "Rank",
    "Term",
    "MSE full",
    "MSE without",
    "Delta MSE",
    "Share of positive delta",
    "Counterpart check",
)

_FOOTER = (
    "Use: among NOT-YET-RUN stages the order may be changed to target the largest attributable",
    "error first, and the reordering is logged in the doc's decision log BEFORE the next stage",
    "runs. No new, unregistered stage can be added this way (deposit decision D28).",
)


def write_error_budget_md(
    rows: Sequence[ErrorBudgetRow],
    path: str | Path,
    *,
    study: str,
    stage: str,
    date: str | None = None,
) -> Path:
    """Write `ERROR_BUDGET.md` to `path`; return the path written.

    `validate_error_budget` runs FIRST — an incomplete table is not written at all, the
    shape `power.py:668 write_power_md` established. Parent directories are created. The
    caller supplies the path; `error_budget_page_path` computes this repository's
    convention, and no page is committed by D606 because no study has run.

    The bytes are deterministic given the rows, the study, the stage and the date, and they
    are ASCII and LF-terminated. ASCII rather than the house's en dashes and middots because
    this page is byte-compared against a hand-written golden, and an encoding round-trip
    through an editor or a checkout is the least interesting way for that to go red.
    """
    validate_error_budget(rows)
    if not str(study).strip():
        raise ValueError("study must be a non-blank name")
    if not str(stage).strip():
        raise ValueError("stage must be a non-blank name")
    stamp = date if date is not None else _dt.datetime.now(_dt.timezone.utc).date().isoformat()
    ordered = sorted(rows, key=lambda r: int(r.rank))
    total_positive = sum(float(r.delta_mse) for r in ordered if float(r.delta_mse) > 0.0)

    lines = [
        f"# {str(study).strip().upper()} - ERROR BUDGET",
        "",
        f"**Generated:** {stamp} | `backtest_framework.validation.error_budget` (D606)",
        "",
        f"**Study:** {str(study).strip()} | **Stage:** {str(stage).strip()} | "
        f"**Folds:** {int(ordered[0].n_folds)} | "
        f"**OOS observations:** {int(ordered[0].n_oos)}",
        "",
        *_PREAMBLE,
        "",
        "| " + " | ".join(_COLUMNS) + " |",
        "|" + "|".join("---" for _ in _COLUMNS) + "|",
    ]
    for row in ordered:
        share = (
            f"{100.0 * float(row.delta_mse) / total_positive:.2f}%"
            if total_positive > 0.0
            else "-"
        )
        lines.append(
            "| "
            + " | ".join(
                [
                    str(int(row.rank)),
                    row.term,
                    f"{float(row.mse_full):.6f}",
                    f"{float(row.mse_without):.6f}",
                    f"{float(row.delta_mse):+.6f}",
                    share,
                    row.counterpart if row.counterpart else "-",
                ]
            )
            + " |"
        )
    lines += ["", *_FOOTER]

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return out


# --------------------------------------------------------------------------- stage order


class StageOrderError(ValueError):
    """A stage would run in an order the decision log does not authorise."""


@dataclass(frozen=True)
class ReorderEntry:
    """One JSON line of the doc's decision log.

    `{"date", "from_order", "to_order", "reason", "before_stage"}`. `date` is ISO
    `YYYY-MM-DD` and is the date the decision was LOGGED, which §8A.1 requires to be before
    the next stage runs. `before_stage` is the stage the reordering is made ahead of, and is
    checked against the orders rather than trusted: it must be the first position at which
    `from_order` and `to_order` differ.
    """

    date: str
    from_order: tuple[str, ...]
    to_order: tuple[str, ...]
    reason: str
    before_stage: str
    line: int = 0


_ENTRY_FIELDS = ("date", "from_order", "to_order", "reason", "before_stage")


@dataclass(frozen=True)
class StageOrder:
    """The registered stage order, and the decision log that may permute the unrun tail.

    `registered` is the pre-registration's own order. It is the ONLY set of stages that may
    ever run: deposit decision D28, *"No new, unregistered stage can be added this way"*,
    and that clause is checked before the log is read at all, so no log entry can smuggle a
    stage in.

    A MISSING LOG FILE IS TREATED AS AN EMPTY LOG, AND THAT FAILS CLOSED: with no entries
    the only permitted order is the registered one, so a mistyped path refuses every
    reordering rather than permitting one. It is stated here because the alternative — a
    path that must exist — would make the ordinary case (no reordering has ever happened)
    require a file with nothing in it.
    """

    registered: tuple[str, ...]
    decision_log_path: Path

    def __post_init__(self) -> None:
        reg = tuple(str(s) for s in self.registered)
        if not reg:
            raise ValueError("registered is empty; there are no stages to order")
        if len(set(reg)) != len(reg):
            raise ValueError(f"registered holds a repeated stage: {list(reg)}")
        for s in reg:
            if not s.strip():
                raise ValueError(f"registered holds a blank stage name: {list(reg)}")
        object.__setattr__(self, "registered", reg)
        object.__setattr__(self, "decision_log_path", Path(self.decision_log_path))

    # -- the log

    def entries(self) -> list[ReorderEntry]:
        """Parse the JSON-lines decision log. Raises naming the line number and the defect."""
        path = Path(self.decision_log_path)
        if not path.exists():
            return []
        raw = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
        out: list[ReorderEntry] = []
        for lineno, text in enumerate(raw.split("\n"), start=1):
            if not text.strip():
                continue
            try:
                obj = json.loads(text)
            except json.JSONDecodeError as exc:
                raise StageOrderError(
                    f"{path}:{lineno} is not JSON: {exc.msg}. The decision log is JSON "
                    f"lines, one reordering per line."
                ) from exc
            if not isinstance(obj, dict):
                raise StageOrderError(f"{path}:{lineno} is not a JSON object")
            missing = [f for f in _ENTRY_FIELDS if f not in obj]
            if missing:
                raise StageOrderError(
                    f"{path}:{lineno} is missing {missing}. A reordering entry records all "
                    f"of {list(_ENTRY_FIELDS)}: without the orders it authorises nothing, "
                    f"without the date it cannot be shown to precede the run, and without "
                    f"the reason it is not a decision."
                )
            entry = ReorderEntry(
                date=str(obj["date"]),
                from_order=tuple(str(s) for s in obj["from_order"]),
                to_order=tuple(str(s) for s in obj["to_order"]),
                reason=str(obj["reason"]),
                before_stage=str(obj["before_stage"]),
                line=lineno,
            )
            self._check_entry(entry, path)
            out.append(entry)
        for a, b in zip(out, out[1:]):
            if b.date < a.date:
                raise StageOrderError(
                    f"{path}:{b.line} is dated {b.date}, before line {a.line}'s {a.date}. "
                    f"The log is read in file order as a chain of orders; an out-of-order "
                    f"date means the chain and the calendar disagree."
                )
        return out

    def _check_entry(self, entry: ReorderEntry, path: Path) -> None:
        try:
            _dt.date.fromisoformat(entry.date)
        except ValueError as exc:
            raise StageOrderError(
                f"{path}:{entry.line} has date {entry.date!r}, not ISO YYYY-MM-DD"
            ) from exc
        if not entry.reason.strip():
            raise StageOrderError(f"{path}:{entry.line} has a blank reason")
        for field, order in (("from_order", entry.from_order), ("to_order", entry.to_order)):
            unknown = [s for s in order if s not in self.registered]
            if unknown:
                raise StageOrderError(
                    f"{path}:{entry.line} {field} names unregistered stage(s) {unknown}. "
                    f"Deposit decision D28: no new, unregistered stage can be added by "
                    f"reordering. Registered: {list(self.registered)}."
                )
            if sorted(order) != sorted(self.registered):
                raise StageOrderError(
                    f"{path}:{entry.line} {field} is {list(order)}, not a permutation of "
                    f"the registered {list(self.registered)}; a reordering permutes the "
                    f"stages, it does not drop or duplicate them"
                )
        if entry.from_order == entry.to_order:
            raise StageOrderError(
                f"{path}:{entry.line} reorders nothing: from_order == to_order"
            )
        first = next(
            i for i, (a, b) in enumerate(zip(entry.from_order, entry.to_order)) if a != b
        )
        if entry.before_stage != entry.to_order[first]:
            raise StageOrderError(
                f"{path}:{entry.line} says before_stage={entry.before_stage!r}, but the "
                f"first stage the reordering changes is {entry.to_order[first]!r}. The "
                f"field names the stage the decision was made ahead of and is checked "
                f"against the orders, not trusted."
            )

    def effective_order(self, as_of: str) -> tuple[str, ...]:
        """The order authorised on `as_of` (ISO date): the registered order, folded through
        every log entry dated on or before that day. Raises if the chain is broken."""
        _dt.date.fromisoformat(as_of)
        order = tuple(self.registered)
        for entry in self.entries():
            if entry.date > as_of:
                continue
            if entry.from_order != order:
                raise StageOrderError(
                    f"{self.decision_log_path}:{entry.line} reorders from "
                    f"{list(entry.from_order)}, but the order in force on {entry.date} is "
                    f"{list(order)}. The log is a chain and this link does not join: an "
                    f"entry that starts from an order nobody was in authorises an order "
                    f"nobody decided."
                )
            order = entry.to_order
        return order

    # -- the gate

    def next(
        self,
        planned_order: Sequence[str],
        *,
        completed: Sequence[str] = (),
        today: str | None = None,
    ) -> str:
        """The next stage to run under `planned_order`, or raise `StageOrderError`.

        Ledger unit test 49 / index unit test 20: *"the code refuses to run a reordered
        stage unless a matching decision-log entry exists."* Four refusals, in this order,
        because the first cause found is the one worth reporting:

        1. any stage outside `registered`, whatever the log says (deposit D28);
        2. a `planned_order` that is not a permutation of `registered`;
        3. a reordering that moves a stage in `completed` — §8A.1 permits reordering
           *"among not-yet-run stages"* only;
        4. a `planned_order` that is not the order in force today, naming the missing log
           entry — and saying so specifically when an entry exists but is dated AFTER the
           run, which is the exact failure the "logged before the next stage runs" clause
           was written against.
        """
        planned = tuple(str(s) for s in planned_order)
        done = tuple(str(s) for s in completed)
        as_of = today if today is not None else _dt.datetime.now(_dt.timezone.utc).date().isoformat()
        _dt.date.fromisoformat(as_of)

        for label, seq in (("planned_order", planned), ("completed", done)):
            unknown = [s for s in seq if s not in self.registered]
            if unknown:
                raise StageOrderError(
                    f"{label} names stage(s) {unknown} that are not registered. Registered: "
                    f"{list(self.registered)}. Deposit decision D28: the error budget may "
                    f"reorder not-yet-run stages and may NEVER add an unregistered one, and "
                    f"no decision-log entry can authorise this."
                )
        if len(set(planned)) != len(planned):
            raise StageOrderError(f"planned_order repeats a stage: {list(planned)}")
        if sorted(planned) != sorted(self.registered):
            missing = [s for s in self.registered if s not in planned]
            raise StageOrderError(
                f"planned_order is {list(planned)} and drops {missing} from the registered "
                f"{list(self.registered)}. A reordering permutes the registered stages; "
                f"dropping one is a different pre-registration."
            )
        if len(set(done)) != len(done):
            raise StageOrderError(f"completed repeats a stage: {list(done)}")
        if planned[: len(done)] != done:
            raise StageOrderError(
                f"planned_order starts {list(planned[: len(done)])} but the stages already "
                f"run are {list(done)}, in that order. Section 8A.1 permits reordering "
                f"\"among not-yet-run stages\" only; a stage that has run cannot be moved."
            )
        remaining = planned[len(done) :]
        if not remaining:
            raise StageOrderError(
                f"every registered stage has run: {list(done)}. There is no next stage."
            )
        nxt = remaining[0]

        effective = self.effective_order(as_of)
        if planned == effective:
            return nxt

        late = [
            e
            for e in self.entries()
            if e.to_order == planned and e.date > as_of
        ]
        if late:
            e = late[0]
            raise StageOrderError(
                f"stage {nxt!r} would run under the order {list(planned)}, and the only "
                f"decision-log entry authorising it ({self.decision_log_path}:{e.line}) is "
                f"dated {e.date}, AFTER the run date {as_of}. Section 8A.1: the reordering "
                f"decision is logged \"before the next stage runs\"."
            )
        raise StageOrderError(
            f"stage {nxt!r} would run under the order {list(planned)}, but the order in "
            f"force on {as_of} is {list(effective)} and no decision-log entry in "
            f"{self.decision_log_path} reorders {list(effective)} to {list(planned)}. "
            f"Section 8A.1: among not-yet-run stages the order may be changed to target the "
            f"largest attributable error first, and the reordering decision is logged in the "
            f"doc's decision log BEFORE the next stage runs. Log the decision, then run."
        )
