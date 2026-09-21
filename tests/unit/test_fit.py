"""Unit tests for `validation/fit.py` (D606).

Two of these are REUSE PINS and are the reason this module exists in the shape it has.
`fit.ols` must be bit-identical to `scripts/run_d365_momentum_buffer.py:762 ols`, and
`fit.rolling_ols` bit-identical to `scripts/prescreen_cross_sectional.py:147 rolling_ols`
— asserted by `tobytes()` against the runners' own committed source, so that a future edit
to either side turns a test red rather than drifting silently. Neither runner is edited and
nothing is copied out of them by hand (R16).

WHY THE RUNNERS ARE COMPILED AND NOT IMPORTED, WHICH IS D593'S PATTERN AND NOT ITS METHOD
-----------------------------------------------------------------------------------------
D593 pinned four runner functions by importing their modules with
`importlib.util.spec_from_file_location`. That does not work here, and the failure is not
subtle. `run_d365_momentum_buffer.py:133` calls `sys.addaudithook` at module level to
install a default-deny holdout guard, and **CPython has no `removeaudithook`** — the runner
says so in its own comment. Importing it inside the test process therefore refuses, for the
whole remaining life of that process, every `open()` of a path containing "holdout"; it
also mutates `sys.path`, installs `memo_load` and loads four further runner modules.

Measured, not argued: with the module imported,
`tests/unit/test_nothing_outside_tests_is_collectable.py::test_nothing_collectable_fetches_
or_writes_at_import` fails with `RuntimeError: [HOLDOUT-GUARD] refused to open
scripts\\run_holdout_test.py`, because that gate imports every collectable script to check
it. The two tests pass alone and one of them fails when they share a process, which is the
worst shape a test defect can have.

`_function_from_runner` therefore parses the runner's source and compiles **only the
`FunctionDef` it needs**, in a namespace holding nothing but `numpy`. The pin is unchanged
in strength — it is still the runner's own committed bytes, and an edit to `ols` moves this
test — and nothing at module level runs.

The rest are guards, and every one of them is shown to accept the good case FIRST and then
to RAISE on a deliberately broken one. A self-test that cannot fail is worse than none.

No fixture is read and no return is computed.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest

from backtest_framework.validation.fit import (
    FeatureBudget,
    FeatureBudgetError,
    multiclass_log_loss,
    ols,
    retention_check,
    rolling_ols,
)

REPO = Path(__file__).resolve().parents[2]


def _functions_from_runner(runner: str, *names: str) -> dict[str, Callable]:
    """Compile the named top-level functions out of a runner's source, importing nothing.

    See the module docstring for why this is not `spec_from_file_location`. Source is read
    as BYTES with CRLF normalised to LF before parsing (D550): `.gitattributes` pins
    `eol=lf` in the index and the worktree here carries CRLF, and a pin that behaves
    differently depending on which the checkout produced is not a pin.

    Raises if a name is missing or defined more than once at top level — a silently absent
    function would make this file pass by testing nothing.
    """
    path = REPO / "scripts" / f"{runner}.py"
    source = path.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
    tree = ast.parse(source, filename=str(path))
    wanted = []
    for name in names:
        found = [
            n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name
        ]
        if len(found) != 1:
            raise AssertionError(
                f"{path}: expected exactly one top-level `def {name}`, found {len(found)}"
            )
        wanted.append(found[0])
    module = ast.Module(body=wanted, type_ignores=[])
    ast.fix_missing_locations(module)
    namespace: dict = {"np": np}
    exec(compile(module, str(path), "exec"), namespace)  # noqa: S102
    return {name: namespace[name] for name in names}


# ============================================================ reuse pin 1: d365's ols


@pytest.fixture(scope="module")
def d365() -> Callable:
    """`run_d365_momentum_buffer.py:762 ols`, compiled from source and nothing else."""
    return _functions_from_runner("run_d365_momentum_buffer", "ols")["ols"]


def _synthetic_design(seed: int = 606, n: int = 200, k: int = 3) -> tuple[np.ndarray, np.ndarray]:
    """A design with the intercept column FIRST, which is d365's own convention at :847
    (`Xr = np.column_stack([np.ones(n), m_f, smb])`)."""
    rng = np.random.default_rng(seed)
    X = rng.normal(size=(n, k))
    X[:, 0] = 1.0
    y = X @ np.array([0.5, -1.0, 2.0][:k]) + rng.normal(size=n) * 0.3
    return y, X


def test_ols_is_bit_identical_to_run_d365(d365) -> None:
    """`coef`, `se_ols` and `se_nw` equal `run_d365.ols(y, Xr, nw_lag=5)` byte for byte."""
    y, X = _synthetic_design()
    want_b, want_se, want_nw = d365(y, X, nw_lag=5)
    got = ols(y, X, nw_lag=5)
    assert got.coef.tobytes() == want_b.tobytes()
    assert got.se_ols.tobytes() == want_se.tobytes()
    assert got.se_nw.tobytes() == want_nw.tobytes()
    assert got.n == 200 and got.k == 3 and got.nw_lag == 5


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("nw_lag", [0, 1, 5, 12])
def test_ols_bit_identical_across_seeds_and_lags(d365, seed: int, nw_lag: int) -> None:
    y, X = _synthetic_design(seed=seed, n=120)
    want_b, want_se, want_nw = d365(y, X, nw_lag=nw_lag)
    got = ols(y, X, nw_lag=nw_lag)
    assert got.coef.tobytes() == want_b.tobytes()
    assert got.se_ols.tobytes() == want_se.tobytes()
    assert got.se_nw.tobytes() == want_nw.tobytes()


def test_intercept_true_reproduces_the_callers_ones_column(d365) -> None:
    """`intercept=True` prepends exactly the column d365's call site builds by hand."""
    y, X = _synthetic_design()
    want_b, want_se, want_nw = d365(y, X, nw_lag=5)
    got = ols(y, X[:, 1:], nw_lag=5, intercept=True)
    assert got.coef.tobytes() == want_b.tobytes()
    assert got.se_ols.tobytes() == want_se.tobytes()
    assert got.se_nw.tobytes() == want_nw.tobytes()


def test_the_measured_disagreement_with_lstsq_is_recorded_not_assumed() -> None:
    """The measurement that decided the solver, re-run here rather than quoted.

    `np.linalg.lstsq` is NOT bit-identical to the normal equations, so a library that
    re-solved D365's published numbers by SVD would move them in the last places. This test
    does not assert the exact ulp gap — that travels with LAPACK — it asserts the two facts
    the decision rested on: the answers AGREE to well within any usable tolerance, and they
    are NOT the same doubles.
    """
    y, X = _synthetic_design()
    normal = ols(y, X).coef
    svd = np.linalg.lstsq(X, y, rcond=None)[0]
    assert normal.tobytes() != svd.tobytes()
    gap = float(np.max(np.abs(normal - svd)))
    assert gap < 1e-12, f"the two solves disagree by {gap:.3e}, which is not a rounding gap"


# ====================================================== reuse pin 2: prescreen's rolling_ols


@pytest.fixture(scope="module")
def prescreen() -> Callable:
    """`prescreen_cross_sectional.py:147 rolling_ols` and the `_prefix` it calls.

    Compiled rather than imported for uniformity with the d365 pin above, and because that
    runner's import pulls in `run_uptrend_onset` for a reuse pin of its own that this file
    has no use for.
    """
    return _functions_from_runner("prescreen_cross_sectional", "_prefix", "rolling_ols")[
        "rolling_ols"
    ]


def test_rolling_ols_is_bit_identical_to_prescreen(prescreen) -> None:
    rng = np.random.default_rng(606)
    T, n_sym, window = 300, 4, 40
    x = np.cumsum(rng.normal(size=T))
    y = rng.normal(size=(n_sym, T)) + x[None, :] * 0.4
    want = prescreen(y, x, window)
    got = rolling_ols(y, x, window)
    assert len(got) == len(want) == 4
    for i, (g, w) in enumerate(zip(got, want)):
        assert np.asarray(g).tobytes() == np.asarray(w).tobytes(), f"output {i} differs"


def test_rolling_ols_short_windows_are_nan_and_the_pin_covers_them(prescreen) -> None:
    """The warm-up is where two implementations of a prefix-sum fit most easily disagree."""
    rng = np.random.default_rng(7)
    T, window = 60, 20
    x = np.arange(T, dtype=float)
    y = rng.normal(size=(2, T))
    got_alpha, got_beta, got_sd, got_n = rolling_ols(y, x, window)
    want = prescreen(y, x, window)
    assert np.isnan(got_beta[:, : window - 1]).all()
    assert not np.isnan(got_beta[:, window - 1 :]).any()
    for g, w in zip((got_alpha, got_beta, got_sd, got_n), want):
        assert np.asarray(g).tobytes() == np.asarray(w).tobytes()


def test_rolling_ols_guards_accept_then_raise() -> None:
    x = np.arange(20, dtype=float)
    y = np.zeros((1, 20))
    rolling_ols(y, x, 5)  # the good case first
    with pytest.raises(ValueError, match="one value per bar"):
        rolling_ols(y, x[:-1], 5)
    with pytest.raises(ValueError, match="window must be >= 3"):
        rolling_ols(y, x, 2)
    with pytest.raises(TypeError, match="window must be an int"):
        rolling_ols(y, x, 5.0)  # type: ignore[arg-type]


# ================================================================================ ols guards


def test_ols_accepts_the_good_case_then_raises_on_each_defect() -> None:
    y, X = _synthetic_design(n=40)
    ols(y, X)  # the good case, first

    with pytest.raises(ValueError, match="need n > k"):
        ols(y[:3], X[:3])
    with pytest.raises(ValueError, match="non-finite"):
        ols(np.where(np.arange(40) == 7, np.nan, y), X)
    with pytest.raises(ValueError, match="non-finite"):
        bad = X.copy()
        bad[5, 2] = np.inf
        ols(y, bad)
    with pytest.raises(ValueError, match="different row sets"):
        ols(y[:-1], X)
    with pytest.raises(ValueError, match="nw_lag must be >= 0"):
        ols(y, X, nw_lag=-1)
    with pytest.raises(ValueError, match="nw_lag ="):
        ols(y, X, nw_lag=40)
    with pytest.raises(ValueError, match="y must be 1-D"):
        ols(y[:, None], X)


def test_ols_names_the_rank_deficient_column() -> None:
    """A rank-deficient design RAISES, and the message names which column."""
    y, X = _synthetic_design(n=40)

    zero = X.copy()
    zero[:, 2] = 0.0
    with pytest.raises(ValueError, match=r"X column 2 is exactly zero"):
        ols(y, zero)

    dependent = np.column_stack([X, X[:, 1] * 2.0 - X[:, 0]])
    with pytest.raises(ValueError, match=r"X column 3 is a linear combination"):
        ols(y, dependent)

    duplicated = np.column_stack([X, X[:, 1]])
    with pytest.raises(ValueError, match=r"X column 3 is a linear combination"):
        ols(y, duplicated)


def test_ols_residual_and_shape_contract() -> None:
    y, X = _synthetic_design(n=40)
    fit = ols(y, X)
    assert fit.resid.shape == (40,)
    assert fit.coef.shape == (3,)
    assert fit.se_ols.shape == (3,)
    assert fit.se_nw.shape == (3,)
    # the residual is exactly y - X @ coef, which is how d365 forms it
    assert fit.resid.tobytes() == (y - X @ fit.coef).tobytes()
    # OLS residuals are orthogonal to the design, to rounding
    assert float(np.max(np.abs(X.T @ fit.resid))) < 1e-10


# ================================================================================= log loss


def test_multiclass_log_loss_accepts_then_raises() -> None:
    p = np.array([[0.5, 0.25, 0.25], [0.25, 0.5, 0.25]])
    y = np.array([0, 1])
    good = multiclass_log_loss(p, y)
    assert good == pytest.approx(math.log(2.0), abs=1e-15)

    with pytest.raises(ValueError, match="sums to"):
        multiclass_log_loss(np.array([[0.5, 0.25, 0.2], [0.25, 0.5, 0.25]]), y)
    with pytest.raises(ValueError, match="outside"):
        multiclass_log_loss(np.array([[1.5, -0.25, -0.25], [0.25, 0.5, 0.25]]), y)
    with pytest.raises(ValueError, match="not a class index"):
        multiclass_log_loss(p, np.array([0, 3]))
    with pytest.raises(TypeError, match="integer class indices"):
        multiclass_log_loss(p, np.array([0.0, 1.0]))
    with pytest.raises(ValueError, match="at least 2"):
        multiclass_log_loss(np.ones((2, 1)), np.array([0, 0]))
    with pytest.raises(ValueError, match="empty"):
        multiclass_log_loss(np.zeros((0, 3)), np.array([], dtype=int))


def test_multiclass_log_loss_sum_bar_is_one_part_in_1e12() -> None:
    """The row-sum tolerance is a declared 1e-12, so both sides of it are checked."""
    y = np.array([0])
    inside = np.array([[0.5 + 5e-13, 0.25, 0.25]])
    multiclass_log_loss(inside, y)
    outside = np.array([[0.5 + 5e-12, 0.25, 0.25]])
    with pytest.raises(ValueError, match="sums to"):
        multiclass_log_loss(outside, y)


def test_multiclass_log_loss_eps_must_be_asked_for() -> None:
    p = np.array([[0.0, 0.5, 0.5], [0.25, 0.5, 0.25]])
    y = np.array([0, 1])
    with pytest.raises(ValueError, match="REALISED class probability zero"):
        multiclass_log_loss(p, y)
    clipped = multiclass_log_loss(p, y, eps=1e-12)
    assert math.isfinite(clipped)
    assert clipped > 4.0  # -log(1e-12) / 2 is about 13.8
    with pytest.raises(ValueError, match=r"eps must be in \(0, 1\)"):
        multiclass_log_loss(p, y, eps=0.0)


# =========================================================================== feature budget


def test_feature_budget_arithmetic_at_the_defaults() -> None:
    b = FeatureBudget()
    assert b.max_features == 11
    assert b.max_parameters == 36
    assert b.parameters(0) == 3
    assert b.parameters(11) == 36
    assert b.parameters(12) == 39
    for n in range(0, 12):
        assert b.assert_within(n) == 3 * (n + 1)
    for n in (12, 13, 40):
        with pytest.raises(FeatureBudgetError):
            b.assert_within(n)


def test_feature_budget_is_not_hard_coded_to_eleven() -> None:
    """The ceiling is a product, so a different class count moves the feature count."""
    assert FeatureBudget(non_base_classes=2, ceiling=36).max_features == 17
    assert FeatureBudget(non_base_classes=4, ceiling=36).max_features == 8
    assert FeatureBudget(non_base_classes=3, ceiling=30).max_features == 9


def test_feature_budget_construction_guards() -> None:
    FeatureBudget(non_base_classes=1, ceiling=4)  # the good case
    with pytest.raises(ValueError, match="must be >= 1"):
        FeatureBudget(non_base_classes=0)
    with pytest.raises(TypeError, match="must be an int"):
        FeatureBudget(non_base_classes=3.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="typo, not a constraint"):
        FeatureBudget(non_base_classes=3, ceiling=5)
    with pytest.raises(ValueError, match="n_features must be >= 0"):
        FeatureBudget().parameters(-1)


# ================================================================================ retention


def test_retention_check_reports_both_clauses_always() -> None:
    kept = retention_check(1.0, 0.875, 2.0, 2.0)
    assert kept.kept is True
    assert "clause 1" in kept.reason and "clause 2" in kept.reason
    # clause 2 is "does not reduce": equality is not a reduction.
    assert kept.dv_not_reduced is True


def test_retention_check_boundary_is_at_or_above_the_bar() -> None:
    at_bar = retention_check(1.0, 0.98, 1.0, 1.0)
    assert at_bar.rel_reduction >= 0.02 - 1e-15
    assert at_bar.kept is True
    below = retention_check(1.0, 0.9801, 1.0, 1.0)
    assert below.kept is False


def test_retention_check_guards() -> None:
    retention_check(1.0, 0.5, 0.0, 0.0)  # the good case
    with pytest.raises(ValueError, match="logloss_prev must be > 0"):
        retention_check(0.0, 0.5, 1.0, 1.0)
    with pytest.raises(ValueError, match="logloss_new must be >= 0"):
        retention_check(1.0, -0.5, 1.0, 1.0)
    with pytest.raises(ValueError, match="must be finite"):
        retention_check(1.0, float("nan"), 1.0, 1.0)
    with pytest.raises(ValueError, match=r"rel must be in \[0, 1\)"):
        retention_check(1.0, 0.5, 1.0, 1.0, rel=1.0)
