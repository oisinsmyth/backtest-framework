"""Golden master for `validation/error_budget.py` and `validation/fit.py` (D606).

Hand arithmetic in `test_error_budget_ledger.hand.txt`, which was written and saved before
either module existed, per D39 and CONTRIBUTING.md: the ground truth is produced by a
calculator that never imports this codebase, because a `.hand.txt` derived from the
implementation launders the implementation's assumptions into the thing meant to check
them.

The ledgers of record are `SETTLEMENT_FLOW_LEDGER_PREREG.md` §8A.1 with unit tests 48 and
49, `INDEX_REWEIGHT_FLOW_PREREG.md` §5A.1 with unit tests 19 and 20, and
`OPENING_AGENT_STATE_PREREG.md` §7.3 with unit test 13 and the retention rule at lines
176-178.

**Every assertion here is `==` except two, and both are named in the .hand.txt**: the
per-fold means 28/6 and 38/6, which are not exactly representable and are therefore not
asserted at all (the per-fold sums of squares and counts are, and they are integers), and
the multiclass log loss 4 ln(2) / 3, which is irrational and is asserted to 12 places. The
design was chosen to make everything else exact: the Gram matrix of the two fitted columns
is `diag(4, 4)` within each block, so its inverse is `diag(0.25, 0.25)` exactly, and every
sum of squares is divisible by 3 so that dividing by 12 is exact.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.error_budget import (
    ErrorBudgetRow,
    StageOrder,
    StageOrderError,
    Term,
    error_budget_page_path,
    leave_one_term_out,
    ols_fitter,
    oos_error,
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

HAND = Path(__file__).with_suffix(".hand.txt")

# --- the design of the .hand.txt, transcribed from it -----------------------------------

#: alpha -- the group indicator on the first four rows of each six-row block.
COL_A = np.array([1.0, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0])
#: beta -- the signed contrast on the last four rows of each block.
COL_B = np.array([0.0, 0, 1, -1, 1, -1, 0, 0, 1, -1, 1, -1])
#: gamma -- exactly zero everywhere. Ledger unit test 48 / index unit test 19.
COL_C = np.zeros(12)

X = np.column_stack([COL_A, COL_B, COL_C])
Y = np.array([5.0, 5, 6, 0, 5, -1, 3, 3, 4, -2, 6, 0])

BLOCK_1 = np.arange(0, 6, dtype=np.int64)
BLOCK_2 = np.arange(6, 12, dtype=np.int64)

TERMS = [
    Term("alpha", lambda x: np.asarray(x)[:, 0]),
    Term("beta", lambda x: np.asarray(x)[:, 1]),
    Term("gamma", lambda x: np.asarray(x)[:, 2]),
]


def _folds() -> list[Fold]:
    return [
        Fold(train_idx=BLOCK_2, test_idx=BLOCK_1, label="fold 1"),
        Fold(train_idx=BLOCK_1, test_idx=BLOCK_2, label="fold 2"),
    ]


def _hand_section(begin: str, end: str) -> str:
    """The text between two markers of the .hand.txt, with a trailing newline.

    Read as BYTES and normalised CRLF -> LF before decoding (D550): `.gitattributes` pins
    `eol=lf` in the index, but the worktree on the author's machine carries CRLF, and a
    byte-exact comparison that inherits whichever the checkout produced is not a comparison.
    """
    text = HAND.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    lines = text.split("\n")
    i = lines.index(begin)
    j = lines.index(end)
    assert i < j, f"{begin!r} must precede {end!r} in the hand file"
    return "\n".join(lines[i + 1 : j]) + "\n"


# ========================================================================== Cases 1 and 2


def test_hand_design_is_what_the_hand_file_says() -> None:
    """The orthogonality and the Gram entries the exactness argument rests on."""
    for block in (BLOCK_1, BLOCK_2):
        a, b = COL_A[block], COL_B[block]
        assert float(a @ a) == 4.0
        assert float(b @ b) == 4.0
        assert float(a @ b) == 0.0
    # y was built as alpha*A + beta*B + e with e orthogonal to both columns.
    assert Y[BLOCK_1].tolist() == [5.0, 5.0, 6.0, 0.0, 5.0, -1.0]
    assert Y[BLOCK_2].tolist() == [3.0, 3.0, 4.0, -2.0, 6.0, 0.0]


def test_case_1_full_model_coefficients_are_exact_integers() -> None:
    """Hand file Case 1: b = (X'X)^-1 X'y = 0.25 * (16, 12) and 0.25 * (8, 12)."""
    for block, a_dot_y, b_dot_y, want in (
        (BLOCK_1, 16.0, 12.0, (4.0, 3.0)),
        (BLOCK_2, 8.0, 12.0, (2.0, 3.0)),
    ):
        design = np.column_stack([COL_A[block], COL_B[block]])
        assert float(COL_A[block] @ Y[block]) == a_dot_y
        assert float(COL_B[block] @ Y[block]) == b_dot_y
        fit = ols(Y[block], design)
        assert fit.coef.tolist() == list(want)
        assert fit.n == 6
        assert fit.k == 2


def test_case_2_pooled_oos_mse_is_exactly_five_and_a_half() -> None:
    """Hand file Case 2: SSE 28 and 38 over 6 + 6 rows, pooled 66 / 12 = 5.5."""
    fit_fn, predict_fn = ols_fitter(TERMS)
    out = oos_error(_folds(), X, Y, fit_fn, predict_fn, ("alpha", "beta", "gamma"))
    assert [f.label for f in out.per_fold] == ["fold 1", "fold 2"]
    assert [f.n for f in out.per_fold] == [6, 6]
    assert [f.sse for f in out.per_fold] == [28.0, 38.0]
    assert out.n == 12
    assert out.mse == 5.5
    # The per-fold MEANS are 14/3 and 19/3 and are NOT exactly representable; the hand file
    # says so and they are checked only for being between the neighbouring integers.
    assert 4 < out.per_fold[0].mse < 5
    assert 6 < out.per_fold[1].mse < 7


def test_case_2_the_gamma_column_is_dropped_not_fitted() -> None:
    """The mechanism the exactly-zero delta rests on, asserted directly."""
    fit_fn, _ = ols_fitter(TERMS)
    model = fit_fn(X[BLOCK_1], Y[BLOCK_1], ("alpha", "beta", "gamma"))
    assert model.used == ("alpha", "beta")
    assert model.dropped_zero == ("gamma",)
    assert model.fit.k == 2
    without = fit_fn(X[BLOCK_1], Y[BLOCK_1], ("alpha", "beta"))
    assert model.fit.coef.tobytes() == without.fit.coef.tobytes()


# ================================================================================== Case 3


def test_case_3_leave_one_term_out_table() -> None:
    fit_fn, predict_fn = ols_fitter(TERMS)
    rows = leave_one_term_out(_folds(), X, Y, fit_fn, predict_fn, TERMS)
    assert [r.term for r in rows] == ["beta", "alpha", "gamma"]
    assert [r.rank for r in rows] == [1, 2, 3]
    assert [r.mse_full for r in rows] == [5.5, 5.5, 5.5]
    assert [r.mse_without for r in rows] == [11.5, 9.5, 5.5]
    assert [r.delta_mse for r in rows] == [6.0, 4.0, 0.0]


def test_ledger_48_zero_contribution_term_changes_oos_mse_by_exactly_zero() -> None:
    """Ledger unit test 48 and index unit test 19, on the golden's design.

    `== 0.0`, not `abs(...) < eps`. See the module docstring of `error_budget.py`: the
    equality is by construction, because the zero column is dropped and the two designs are
    then the same matrix byte for byte.
    """
    fit_fn, predict_fn = ols_fitter(TERMS)
    rows = leave_one_term_out(_folds(), X, Y, fit_fn, predict_fn, TERMS)
    gamma = next(r for r in rows if r.term == "gamma")
    assert gamma.delta_mse == 0.0
    assert gamma.mse_without == gamma.mse_full
    # And the two terms that DO contribute are not zero, so the assertion above can fail.
    assert all(r.delta_mse > 0.0 for r in rows if r.term != "gamma")


# ================================================================================== Case 4


def test_case_4_rendered_page_matches_the_hand_file_byte_for_byte(tmp_path: Path) -> None:
    fit_fn, predict_fn = ols_fitter(TERMS)
    contributions = leave_one_term_out(_folds(), X, Y, fit_fn, predict_fn, TERMS)
    counterparts = {"beta": "COT swap-dealer ratio 0.81"}
    rows = [
        ErrorBudgetRow.from_contribution(
            c, n_folds=2, n_oos=12, counterpart=counterparts.get(c.term)
        )
        for c in contributions
    ]
    out = write_error_budget_md(
        rows,
        tmp_path / "ERROR_BUDGET.md",
        study="settlement_flow",
        stage="S-A",
        date="2026-09-21",
    )
    written = out.read_bytes()
    expected = _hand_section(
        "--- BEGIN ERROR_BUDGET.md ---", "--- END ERROR_BUDGET.md ---"
    ).encode("utf-8")
    assert written == expected


def test_case_4_page_path_mapping() -> None:
    assert error_budget_page_path("settlement_flow") == Path(
        "docs/results/SETTLEMENT_FLOW_ERROR_BUDGET.md"
    )
    assert error_budget_page_path("index_reweight") == Path(
        "docs/results/INDEX_REWEIGHT_ERROR_BUDGET.md"
    )


def test_case_4_no_error_budget_page_is_committed() -> None:
    """No study has run, so the repository holds no rendered page. Stated as a test so that
    committing one becomes a deliberate act with a red test in front of it."""
    repo = Path(__file__).resolve().parents[2]
    assert not list((repo / "docs" / "results").glob("*_ERROR_BUDGET.md"))


# ================================================================================== Case 5


def test_opening_13_parameter_budget_refuses_twelve_features() -> None:
    """`OPENING_AGENT_STATE_PREREG.md` §7.3 and unit test 13."""
    budget = FeatureBudget()
    assert budget.non_base_classes == 3
    assert budget.ceiling == 36
    assert budget.max_features == 11
    # 3 x (11 + 1) = 36 <= 36 ALLOWED, with equality.
    assert budget.parameters(11) == 36
    assert budget.assert_within(11) == 36
    # 3 x (12 + 1) = 39 > 36 REFUSED, by 3 parameters.
    assert budget.parameters(12) == 39
    with pytest.raises(FeatureBudgetError) as excinfo:
        budget.assert_within(12)
    message = str(excinfo.value)
    assert "12 features" in message
    assert "39 parameters" in message
    assert "36" in message


# ================================================================================== Case 6


def test_case_6_retention_rule_all_three_cases() -> None:
    """Lines 176-178. Binary fractions throughout, so every number here is exact."""
    kept = retention_check(1.0, 0.875, 2.0, 2.125)
    assert kept.rel_reduction == 0.125
    assert kept.dv_not_reduced is True
    assert kept.kept is True

    clause1 = retention_check(1.0, 0.9921875, 2.0, 2.125)
    assert clause1.rel_reduction == 0.0078125
    assert clause1.dv_not_reduced is True
    assert clause1.kept is False
    assert "clause 1" in clause1.reason and "clause 2" not in clause1.reason

    clause2 = retention_check(1.0, 0.875, 2.0, 1.9375)
    assert clause2.rel_reduction == 0.125
    assert clause2.dv_not_reduced is False
    assert clause2.kept is False
    # BOTH clauses are readable from the result even though only one failed: the log loss
    # improved by six times the bar and a bare "not kept" would read as the opposite.
    assert "clause 2" in clause2.reason
    assert clause2.rel_reduction >= 0.02


# ================================================================================== Case 7


def test_case_7_multiclass_log_loss() -> None:
    p = np.array([[0.5, 0.25, 0.25], [0.25, 0.5, 0.25], [0.25, 0.25, 0.5]])
    y = np.array([0, 2, 2])
    loss = multiclass_log_loss(p, y)
    # 4 ln(2) / 3 = 0.924196240746593745889..., irrational: 12 places, not `==`.
    assert loss == pytest.approx(0.924196240746594, abs=1e-12)
    assert loss == pytest.approx(4.0 * math.log(2.0) / 3.0, abs=1e-15)


def test_case_7_zero_probability_on_the_realised_class_raises() -> None:
    p = np.array([[1.0, 0.0, 0.0], [0.25, 0.5, 0.25]])
    y = np.array([1, 1])
    with pytest.raises(ValueError, match="REALISED class probability zero"):
        multiclass_log_loss(p, y)
    # ...and it is the CLIP that is refused, not the input: eps makes it finite.
    assert math.isfinite(multiclass_log_loss(p, y, eps=1e-15))


# ================================================================================== Case 8

REGISTERED = ("S-A", "S-B", "S-C", "S-D")
REORDERED = ("S-A", "S-C", "S-B", "S-D")


def _log(tmp_path: Path, *entries: dict) -> Path:
    path = tmp_path / "decision_log.jsonl"
    import json

    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for entry in entries:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
    return path


ENTRY = {
    "date": "2026-09-20",
    "from_order": list(REGISTERED),
    "to_order": list(REORDERED),
    "reason": "S-C carries the largest attributable error",
    "before_stage": "S-C",
}


def test_case_8a_registered_order_needs_no_log_entry(tmp_path: Path) -> None:
    order = StageOrder(REGISTERED, tmp_path / "absent.jsonl")
    assert order.next(REGISTERED, today="2026-09-21") == "S-A"
    assert order.next(REGISTERED, completed=("S-A",), today="2026-09-21") == "S-B"


def test_ledger_49_reordered_stage_without_a_log_entry_is_refused(tmp_path: Path) -> None:
    """Ledger unit test 49 and index unit test 20, Case 8(b)."""
    order = StageOrder(REGISTERED, _log(tmp_path))
    with pytest.raises(StageOrderError) as excinfo:
        order.next(REORDERED, completed=("S-A",), today="2026-09-21")
    message = str(excinfo.value)
    assert "'S-C'" in message
    assert "decision log" in message


def test_case_8c_a_matching_entry_dated_before_the_run_permits_it(tmp_path: Path) -> None:
    order = StageOrder(REGISTERED, _log(tmp_path, ENTRY))
    assert order.next(REORDERED, completed=("S-A",), today="2026-09-21") == "S-C"
    assert order.effective_order("2026-09-21") == REORDERED
    # ...and before the entry was written, the registered order is still the one in force.
    assert order.effective_order("2026-09-19") == REGISTERED


def test_case_8d_an_unregistered_stage_is_refused_whatever_the_log_says(
    tmp_path: Path,
) -> None:
    """Deposit decision D28. The log is not even read: the check runs first."""
    order = StageOrder(REGISTERED, _log(tmp_path, ENTRY))
    with pytest.raises(StageOrderError, match="not registered"):
        order.next(("S-A", "S-B", "S-C", "S-D", "S-E"), today="2026-09-21")


def test_case_8e_a_stage_already_run_cannot_be_reordered(tmp_path: Path) -> None:
    order = StageOrder(REGISTERED, _log(tmp_path, ENTRY))
    with pytest.raises(StageOrderError, match="not-yet-run stages"):
        order.next(("S-B", "S-A", "S-C", "S-D"), completed=("S-A",), today="2026-09-21")


def test_case_8f_an_entry_dated_after_the_run_is_refused_and_says_so(
    tmp_path: Path,
) -> None:
    late = dict(ENTRY, date="2026-09-22")
    order = StageOrder(REGISTERED, _log(tmp_path, late))
    with pytest.raises(StageOrderError) as excinfo:
        order.next(REORDERED, completed=("S-A",), today="2026-09-21")
    assert "AFTER the run date" in str(excinfo.value)
