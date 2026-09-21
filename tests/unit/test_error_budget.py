"""Unit tests for `validation/error_budget.py` (D606).

The four named acceptance tests of the two deposit documents live here and in
`tests/golden/test_error_budget_ledger.py`:

  * ledger 48 / index 19 — *"removing a term with zero forecast contribution changes OOS
    MSE by zero on synthetic data"* / *"removing a zero-contribution component leaves OOS
    error unchanged on synthetic data"*. Asserted `== 0.0`, never `approx`.
  * ledger 49 / index 20 — *"the code refuses to run a reordered stage unless a matching
    decision-log entry exists"* / *"Stage reordering requires a matching decision-log
    entry."*

The golden runs them on the twelve-row hand-worked design; this file runs them on the index
document's own two components, (a) flow forecast and (b) impact, and on the failure modes a
hand-worked case cannot reach — a leaked fold index, a table pasted together from two runs,
a decision log that does not parse.

Every guard is shown to ACCEPT the good case before it is shown to raise, and the breaks
hit the scalar the guard reads rather than something adjacent to it.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.error_budget import (
    ErrorBudgetRow,
    FoldError,
    OOSError,
    StageOrder,
    StageOrderError,
    Term,
    TermContribution,
    error_budget_page_path,
    leave_one_term_out,
    ols_fitter,
    oos_error,
    validate_error_budget,
    write_error_budget_md,
)
from backtest_framework.validation.folds import Fold, leave_one_year_out

# --------------------------------------------------------------------------- fixtures


def _index_panel(n_per_year: int = 250, years: int = 4, seed: int = 606):
    """The INDEX_REWEIGHT §5A.1 shape: (a) a flow forecast and (b) an impact term, plus a
    third component whose column is exactly zero. Synthetic; no fixture is read."""
    rng = np.random.default_rng(seed)
    n = n_per_year * years
    flow = rng.normal(size=n)
    impact = rng.normal(size=n) * 0.5
    zero = np.zeros(n)
    X = np.column_stack([flow, impact, zero])
    y = 1.5 * flow + 0.4 * impact + rng.normal(size=n) * 0.2
    dates = np.array(
        [
            f"{2020 + i // n_per_year}-{1 + (i % n_per_year) // 21:02d}-"
            f"{1 + (i % n_per_year) % 21:02d}"
            for i in range(n)
        ],
        dtype="datetime64[D]",
    )
    terms = [
        Term("flow_forecast", lambda x: np.asarray(x)[:, 0]),
        Term("impact", lambda x: np.asarray(x)[:, 1]),
        Term("zero_component", lambda x: np.asarray(x)[:, 2]),
    ]
    return X, y, dates, terms


def _two_folds(n: int) -> list[Fold]:
    half = n // 2
    a = np.arange(0, half, dtype=np.int64)
    b = np.arange(half, n, dtype=np.int64)
    return [
        Fold(train_idx=b, test_idx=a, label="first half"),
        Fold(train_idx=a, test_idx=b, label="second half"),
    ]


# =============================================================== ledger 48 / index 19


def test_index_19_zero_contribution_component_leaves_oos_error_unchanged() -> None:
    """Index unit test 19, on the index document's own (a) flow / (b) impact components.

    The assertion is `== 0.0`. That is achievable only because `ols_fitter` DROPS an
    exactly-zero column instead of fitting a zero coefficient: the full design and the
    design without the zero component are then the same matrix byte for byte.
    """
    X, y, dates, terms = _index_panel()
    folds = leave_one_year_out(dates, min_days=200)
    fit_fn, predict_fn = ols_fitter(terms)
    rows = leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms)
    zero_row = next(r for r in rows if r.term == "zero_component")
    assert zero_row.delta_mse == 0.0
    assert zero_row.mse_without == zero_row.mse_full
    assert zero_row.rank == 3
    # The guard can fail: the two real components move the OOS MSE by a lot.
    assert next(r for r in rows if r.term == "flow_forecast").delta_mse > 1.0
    assert next(r for r in rows if r.term == "impact").delta_mse > 0.0


def test_ledger_48_the_zero_delta_is_exact_and_not_a_rounding_accident() -> None:
    """The same claim, checked at the mechanism: the two designs are identical bytes.

    Without the drop, a zero column makes the solve rank deficient. `fit.ols` refuses that
    outright, so a fitter that kept the column would RAISE rather than return a delta of
    1e-17 — which is the other half of the same design decision and is asserted here.
    """
    X, y, _, terms = _index_panel(n_per_year=60, years=2)
    fit_fn, _ = ols_fitter(terms)
    full = fit_fn(X, y, ("flow_forecast", "impact", "zero_component"))
    without = fit_fn(X, y, ("flow_forecast", "impact"))
    assert full.used == without.used == ("flow_forecast", "impact")
    assert full.dropped_zero == ("zero_component",)
    assert without.dropped_zero == ()
    assert full.fit.coef.tobytes() == without.fit.coef.tobytes()
    assert full.fit.resid.tobytes() == without.fit.resid.tobytes()

    from backtest_framework.validation.fit import ols

    with pytest.raises(ValueError, match="X column 2 is exactly zero"):
        ols(y, X)


def test_a_term_zero_on_train_but_not_on_test_still_has_delta_zero() -> None:
    """The exactness claim is about the TRAINING column, and the boundary is checked.

    A column the fit never saw cannot reach the prediction, so its removal is a no-op even
    though it is non-zero on the rows being scored. Stated as a test because the natural
    misreading — "zero everywhere" — is a weaker claim than the one the module makes.
    """
    n = 40
    rng = np.random.default_rng(3)
    flow = rng.normal(size=n)
    other = rng.normal(size=n)
    sometimes = np.zeros(n)
    sometimes[n // 2 :] = rng.normal(size=n - n // 2)
    y = 2.0 * flow + 0.5 * other + rng.normal(size=n) * 0.1
    X = np.column_stack([flow, other, sometimes])
    terms = [
        Term("flow", lambda x: np.asarray(x)[:, 0]),
        Term("other", lambda x: np.asarray(x)[:, 1]),
        Term("sometimes", lambda x: np.asarray(x)[:, 2]),
    ]
    # ONE fold only: train on the first half (where `sometimes` is exactly zero), test on
    # the second (where it is not).
    folds = [
        Fold(
            train_idx=np.arange(0, n // 2, dtype=np.int64),
            test_idx=np.arange(n // 2, n, dtype=np.int64),
            label="train on the zero half",
        )
    ]
    fit_fn, predict_fn = ols_fitter(terms)
    rows = leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms)
    assert next(r for r in rows if r.term == "sometimes").delta_mse == 0.0
    assert next(r for r in rows if r.term == "flow").delta_mse > 0.0


# ============================================================================ oos_error


def test_oos_error_pools_rather_than_averaging_fold_means() -> None:
    X, y, dates, terms = _index_panel(n_per_year=220, years=3)
    folds = leave_one_year_out(dates, min_days=200)
    fit_fn, predict_fn = ols_fitter(terms)
    out = oos_error(folds, X, y, fit_fn, predict_fn, ("flow_forecast", "impact"))
    assert out.n == sum(f.n for f in out.per_fold) == 660
    total_sse = sum(f.sse for f in out.per_fold)
    assert out.mse == total_sse / out.n
    assert [f.label for f in out.per_fold] == [f.label for f in folds]


def test_a_leaked_fold_index_raises_at_construction_and_again_inside_oos_error() -> None:
    """The test index never enters the fit, and BOTH guards are proved able to fire.

    `Fold.__post_init__` refuses the overlap at construction — that is the structural
    guarantee. `oos_error` re-checks, because a frozen dataclass is not sealed:
    `object.__setattr__` reaches through it. The second half of this test does exactly that
    to a fold that was legal when it was built, which is the only way to reach the
    re-check.
    """
    with pytest.raises(ValueError, match="must not have been fitted using that block"):
        Fold(
            train_idx=np.array([0, 1, 2, 3], dtype=np.int64),
            test_idx=np.array([3, 4, 5], dtype=np.int64),
            label="leaked",
        )

    X, y, _, terms = _index_panel(n_per_year=40, years=2)
    fit_fn, predict_fn = ols_fitter(terms)
    folds = _two_folds(len(y))
    oos_error(folds, X, y, fit_fn, predict_fn, ("flow_forecast", "impact"))  # good first

    leaked = folds[0]
    object.__setattr__(leaked, "train_idx", np.union1d(leaked.train_idx, leaked.test_idx))
    with pytest.raises(ValueError, match="would be fitted on"):
        oos_error([leaked], X, y, fit_fn, predict_fn, ("flow_forecast", "impact"))


def test_oos_error_guards() -> None:
    X, y, _, terms = _index_panel(n_per_year=40, years=2)
    fit_fn, predict_fn = ols_fitter(terms)
    folds = _two_folds(len(y))
    oos_error(folds, X, y, fit_fn, predict_fn, ("flow_forecast",))  # good first

    with pytest.raises(ValueError, match="no folds"):
        oos_error([], X, y, fit_fn, predict_fn, ("flow_forecast",))
    with pytest.raises(ValueError, match="no active terms"):
        oos_error(folds, X, y, fit_fn, predict_fn, ())
    with pytest.raises(IndexError, match="built on a different index"):
        oos_error(folds, X, y[:-5], fit_fn, predict_fn, ("flow_forecast",))
    with pytest.raises(KeyError, match="not registered"):
        oos_error(folds, X, y, fit_fn, predict_fn, ("nonexistent",))
    with pytest.raises(ValueError, match="exactly-zero column"):
        oos_error(folds, X, y, fit_fn, predict_fn, ("zero_component",))


def test_a_nan_column_is_not_a_zero_column() -> None:
    n = 40
    X = np.column_stack([np.arange(n, dtype=float), np.full(n, np.nan)])
    y = np.arange(n, dtype=float)
    terms = [
        Term("good", lambda x: np.asarray(x)[:, 0]),
        Term("nan", lambda x: np.asarray(x)[:, 1]),
    ]
    fit_fn, _ = ols_fitter(terms)
    fit_fn(X, y, ("good",))  # good first
    with pytest.raises(ValueError, match="non-finite"):
        fit_fn(X, y, ("good", "nan"))


def test_leave_one_term_out_needs_two_terms() -> None:
    X, y, _, terms = _index_panel(n_per_year=40, years=2)
    fit_fn, predict_fn = ols_fitter(terms)
    folds = _two_folds(len(y))
    leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms[:2])  # good first
    with pytest.raises(ValueError, match="at least 2 terms"):
        leave_one_term_out(folds, X, y, fit_fn, predict_fn, terms[:1])
    with pytest.raises(ValueError, match="repeated name"):
        leave_one_term_out(folds, X, y, fit_fn, predict_fn, [terms[0], terms[0]])


def test_ols_fitter_refuses_a_duplicate_term_name() -> None:
    ols_fitter([Term("a", lambda x: np.asarray(x)[:, 0])])  # good first
    with pytest.raises(ValueError, match="appears twice"):
        ols_fitter(
            [
                Term("a", lambda x: np.asarray(x)[:, 0]),
                Term("a", lambda x: np.asarray(x)[:, 1]),
            ]
        )


def test_term_construction_guards() -> None:
    Term("ok", lambda x: np.zeros(3))  # good first
    with pytest.raises(ValueError, match="non-blank name"):
        Term("   ", lambda x: np.zeros(3))
    with pytest.raises(TypeError, match="non-callable predict"):
        Term("a", 3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="a term is one column"):
        Term("a", lambda x: np.zeros((3, 2))).column(None, 3)
    with pytest.raises(ValueError, match="different row sets"):
        Term("a", lambda x: np.zeros(3)).column(None, 4)


def test_fold_error_mse_is_derived_not_stored() -> None:
    fe = FoldError(label="f", n=6, sse=28.0)
    assert fe.mse == 28.0 / 6.0
    out = OOSError(mse=5.5, n=12, per_fold=(fe,))
    assert out.mse == 5.5


# ==================================================================== validate/render


def _rows(**overrides) -> list[ErrorBudgetRow]:
    base = [
        ErrorBudgetRow("beta", 2, 12, 5.5, 11.5, 6.0, 1),
        ErrorBudgetRow("alpha", 2, 12, 5.5, 9.5, 4.0, 2),
        ErrorBudgetRow("gamma", 2, 12, 5.5, 5.5, 0.0, 3),
    ]
    if overrides:
        i = overrides.pop("index", 0)
        base[i] = ErrorBudgetRow(
            **{
                **{
                    "term": base[i].term,
                    "n_folds": base[i].n_folds,
                    "n_oos": base[i].n_oos,
                    "mse_full": base[i].mse_full,
                    "mse_without": base[i].mse_without,
                    "delta_mse": base[i].delta_mse,
                    "rank": base[i].rank,
                    "counterpart": base[i].counterpart,
                },
                **overrides,
            }
        )
    return base


def test_validate_error_budget_accepts_a_clean_table_then_raises_on_each_defect() -> None:
    validate_error_budget(_rows())  # the good case, first

    with pytest.raises(ValueError, match="has no rows"):
        validate_error_budget([])
    with pytest.raises(ValueError, match="is missing a term name"):
        validate_error_budget(_rows(term="  "))
    with pytest.raises(ValueError, match="is missing the full model's OOS MSE"):
        validate_error_budget(_rows(mse_full=float("nan")))
    with pytest.raises(ValueError, match="is missing a rank"):
        validate_error_budget(_rows(rank=None))
    with pytest.raises(ValueError, match="edited by hand"):
        validate_error_budget(_rows(delta_mse=6.5))
    with pytest.raises(ValueError, match="two runs were pasted into one table"):
        validate_error_budget(_rows(index=1, mse_full=5.25, delta_mse=9.5 - 5.25))
    with pytest.raises(ValueError, match="not a permutation of 1"):
        validate_error_budget(_rows(rank=3))
    with pytest.raises(ValueError, match="appears 2 times"):
        validate_error_budget(_rows(index=1, term="beta"))


def test_validate_error_budget_reports_the_cause_before_the_symptom() -> None:
    """`_ERROR_BUDGET_REQUIRED` is ordered cause-first, the shape `_TRACK_MAP_REQUIRED` in `validation/power.py` uses.

    A row missing BOTH its observation count and its rank is reported on the count: a row
    with no observations has no MSE, so naming the rank would send a reader to the wrong
    end of the pipeline.
    """
    broken = [ErrorBudgetRow("beta", 2, None, 5.5, 11.5, 6.0, None)]  # type: ignore[arg-type]
    with pytest.raises(ValueError) as excinfo:
        validate_error_budget(broken)
    assert "out-of-sample observation count" in str(excinfo.value)
    assert "a rank" not in str(excinfo.value)


def test_ranking_must_order_the_deltas() -> None:
    swapped = [
        ErrorBudgetRow("alpha", 2, 12, 5.5, 9.5, 4.0, 1),
        ErrorBudgetRow("beta", 2, 12, 5.5, 11.5, 6.0, 2),
        ErrorBudgetRow("gamma", 2, 12, 5.5, 5.5, 0.0, 3),
    ]
    with pytest.raises(ValueError, match="SMALLER delta"):
        validate_error_budget(swapped)


def test_write_error_budget_md_validates_before_writing_a_byte(tmp_path: Path) -> None:
    path = tmp_path / "ERROR_BUDGET.md"
    with pytest.raises(ValueError, match="edited by hand"):
        write_error_budget_md(
            _rows(delta_mse=6.5), path, study="settlement_flow", stage="S-A"
        )
    assert not path.exists(), "an invalid table must not leave a partial page behind"
    write_error_budget_md(_rows(), path, study="settlement_flow", stage="S-A")
    assert path.exists()


def test_write_error_budget_md_pins_lf_newlines(tmp_path: Path) -> None:
    """D550: the author's OS is not the runner's. The page is LF whatever the platform."""
    path = write_error_budget_md(
        _rows(), tmp_path / "p.md", study="s", stage="S-A", date="2026-09-21"
    )
    raw = path.read_bytes()
    assert b"\r\n" not in raw
    assert raw.endswith(b"\n")
    assert raw.decode("ascii")  # ASCII-only, per the module docstring


def test_write_error_budget_md_is_deterministic(tmp_path: Path) -> None:
    a = write_error_budget_md(
        _rows(), tmp_path / "a.md", study="s", stage="S-A", date="2026-09-21"
    ).read_bytes()
    b = write_error_budget_md(
        _rows(), tmp_path / "b.md", study="s", stage="S-A", date="2026-09-21"
    ).read_bytes()
    assert a == b


def test_share_column_is_dashed_when_no_delta_is_positive(tmp_path: Path) -> None:
    rows = [
        ErrorBudgetRow("a", 1, 10, 5.0, 5.0, 0.0, 1),
        ErrorBudgetRow("b", 1, 10, 5.0, 4.0, -1.0, 2),
    ]
    text = write_error_budget_md(
        rows, tmp_path / "p.md", study="s", stage="S-A", date="2026-09-21"
    ).read_text(encoding="utf-8")
    assert "| 1 | a | 5.000000 | 5.000000 | +0.000000 | - | - |" in text
    assert "-1.000000" in text


def test_error_budget_page_path_guards() -> None:
    assert error_budget_page_path("x").name == "X_ERROR_BUDGET.md"
    with pytest.raises(ValueError, match="non-blank"):
        error_budget_page_path("  ")


def test_row_from_contribution_carries_the_contribution_unchanged() -> None:
    c = TermContribution("beta", 5.5, 11.5, 6.0, 1)
    row = ErrorBudgetRow.from_contribution(c, n_folds=2, n_oos=12, counterpart="COT 0.81")
    assert (row.term, row.mse_full, row.mse_without, row.delta_mse, row.rank) == (
        "beta",
        5.5,
        11.5,
        6.0,
        1,
    )
    assert row.counterpart == "COT 0.81"
    validate_error_budget([row])


# =============================================================== ledger 49 / index 20

REGISTERED = ("C0", "A", "B", "C")
REORDERED = ("C0", "B", "A", "C")


def _write_log(tmp_path: Path, *entries: dict) -> Path:
    path = tmp_path / "decision_log.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return path


GOOD_ENTRY = {
    "date": "2026-09-20",
    "from_order": list(REGISTERED),
    "to_order": list(REORDERED),
    "reason": "B carries the largest attributable error in C0's budget",
    "before_stage": "B",
}


def test_index_20_stage_reordering_requires_a_matching_decision_log_entry(
    tmp_path: Path,
) -> None:
    """Index unit test 20 / ledger 49, on the index document's own stage names."""
    empty = StageOrder(REGISTERED, _write_log(tmp_path))
    assert empty.next(REGISTERED, completed=("C0",), today="2026-09-21") == "A"
    with pytest.raises(StageOrderError) as excinfo:
        empty.next(REORDERED, completed=("C0",), today="2026-09-21")
    assert "'B'" in str(excinfo.value)

    logged = StageOrder(REGISTERED, _write_log(tmp_path, GOOD_ENTRY))
    assert logged.next(REORDERED, completed=("C0",), today="2026-09-21") == "B"


def test_ledger_49_a_near_miss_entry_does_not_match(tmp_path: Path) -> None:
    """"A matching entry" is checked, not "an entry". The break hits what the guard reads."""
    other = dict(
        GOOD_ENTRY,
        to_order=["C0", "A", "C", "B"],
        before_stage="C",
    )
    order = StageOrder(REGISTERED, _write_log(tmp_path, other))
    assert order.next(("C0", "A", "C", "B"), completed=("C0",), today="2026-09-21") == "A"
    with pytest.raises(StageOrderError, match="no decision-log entry"):
        order.next(REORDERED, completed=("C0",), today="2026-09-21")


def test_the_log_chain_must_join(tmp_path: Path) -> None:
    """A second entry starting from an order nobody was in authorises nothing."""
    second = {
        "date": "2026-09-21",
        "from_order": ["C0", "A", "C", "B"],
        "to_order": ["C0", "C", "A", "B"],
        "reason": "C next",
        "before_stage": "C",
    }
    order = StageOrder(REGISTERED, _write_log(tmp_path, GOOD_ENTRY, second))
    with pytest.raises(StageOrderError, match="this link does not join"):
        order.effective_order("2026-09-21")


def test_log_entry_guards(tmp_path: Path) -> None:
    good = StageOrder(REGISTERED, _write_log(tmp_path, GOOD_ENTRY))
    assert good.entries()[0].before_stage == "B"  # good first

    cases = [
        ({"reason": "  "}, "blank reason"),
        ({"date": "20-09-2026"}, "not ISO"),
        ({"before_stage": "C"}, "first stage the reordering changes"),
        ({"to_order": list(REGISTERED)}, "reorders nothing"),
        ({"to_order": ["C0", "A", "B", "Z"]}, "unregistered stage"),
        ({"to_order": ["C0", "A", "B"]}, "not a permutation"),
    ]
    for override, message in cases:
        order = StageOrder(REGISTERED, _write_log(tmp_path, dict(GOOD_ENTRY, **override)))
        with pytest.raises(StageOrderError, match=message):
            order.entries()


def test_log_parse_guards(tmp_path: Path) -> None:
    path = tmp_path / "decision_log.jsonl"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("{not json}\n")
    with pytest.raises(StageOrderError, match="is not JSON"):
        StageOrder(REGISTERED, path).entries()

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps({"date": "2026-09-20"}) + "\n")
    with pytest.raises(StageOrderError, match="is missing"):
        StageOrder(REGISTERED, path).entries()

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps([1, 2]) + "\n")
    with pytest.raises(StageOrderError, match="not a JSON object"):
        StageOrder(REGISTERED, path).entries()


def test_log_dates_must_not_go_backwards(tmp_path: Path) -> None:
    later = dict(
        GOOD_ENTRY,
        date="2026-09-19",
        from_order=list(REORDERED),
        to_order=["C0", "B", "C", "A"],
        before_stage="C",
    )
    order = StageOrder(REGISTERED, _write_log(tmp_path, GOOD_ENTRY, later))
    with pytest.raises(StageOrderError, match="before line 1's"):
        order.entries()


def test_a_crlf_decision_log_parses(tmp_path: Path) -> None:
    """D550 again, from the reading side: a log written on Windows still parses."""
    path = tmp_path / "decision_log.jsonl"
    path.write_bytes((json.dumps(GOOD_ENTRY, sort_keys=True) + "\r\n").encode("utf-8"))
    order = StageOrder(REGISTERED, path)
    assert order.next(REORDERED, completed=("C0",), today="2026-09-21") == "B"


def test_stage_order_construction_and_next_guards(tmp_path: Path) -> None:
    log = _write_log(tmp_path, GOOD_ENTRY)
    order = StageOrder(REGISTERED, log)
    assert order.next(REGISTERED, today="2026-09-19") == "C0"  # good first

    with pytest.raises(ValueError, match="registered is empty"):
        StageOrder((), log)
    with pytest.raises(ValueError, match="repeated stage"):
        StageOrder(("A", "A"), log)
    with pytest.raises(StageOrderError, match="repeats a stage"):
        order.next(("C0", "C0", "A", "B", "C"), today="2026-09-19")
    with pytest.raises(StageOrderError, match="drops"):
        order.next(("C0", "A", "B"), today="2026-09-19")
    with pytest.raises(StageOrderError, match="every registered stage has run"):
        order.next(REGISTERED, completed=REGISTERED, today="2026-09-19")
    with pytest.raises(StageOrderError, match="not registered"):
        order.next(REGISTERED, completed=("Z",), today="2026-09-19")


def test_a_missing_log_file_fails_closed(tmp_path: Path) -> None:
    """Documented behaviour: no file means no reorderings are authorised, never all of them."""
    order = StageOrder(REGISTERED, tmp_path / "does_not_exist.jsonl")
    assert order.entries() == []
    assert order.next(REGISTERED, today="2026-09-21") == "C0"
    with pytest.raises(StageOrderError, match="no decision-log entry"):
        order.next(REORDERED, completed=("C0",), today="2026-09-21")
