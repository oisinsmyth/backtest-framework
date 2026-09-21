"""Least squares, multiclass log loss, the parameter budget and the retention rule (D606).

The six User-Doc-Deposit pre-registrations fit things — participant terms against realised
window flow, kappa against index flow, a multinomial logit over day types — and then ask
whether each fitted piece earned its place. **There is no OLS, ridge, logit, log-loss or
parameter-budget helper anywhere in `src/`**, and sklearn and statsmodels are not
dependencies of this project and must not become ones. What exists is three one-off
fitters in runner and research code, which this module is pinned to rather than
duplicating:

  * `scripts/run_d365_momentum_buffer.py:762 ols(y, Xr, nw_lag=5)` — the normal-equation
    solve with a classical SE and a Newey-West(5) SE beside it;
  * `scripts/prescreen_cross_sectional.py:147 rolling_ols(y, x, window)` — O(T) rolling
    OLS by prefix sums, itself carrying a reuse pin at `:239` against
    `run_uptrend_onset.rolling_fit`;
  * `src/backtest_framework/research/cointegration.py:40,64` — the only `np.linalg.lstsq`
    calls in `src/`, both Engle-Granger.

THE SPEC, QUOTED. `OPENING_AGENT_STATE_PREREG.md` §7.3, "Parameter budget":

    - Pooled ES+NQ sessions ~ 5,000; but same-day ES and NQ are highly correlated, so the
      effective count is lower (Section 10).
    - Rarest retained class ~ 10-15% of days.
    - **Ceiling: 3 non-base classes x (features + 1) <= 36**, so at most **11 features** in
      any stage. The alignment summary (S-I) exists partly to stay well under this.

and §1 line 21, "**Parameter ceiling:** the classifier is capped at the budget in Section
7.3. Exceeding it requires a doc amendment." — so the ceiling RAISES rather than warning
(D48); a warning is a thing a run scrolls past. Unit test 13: *"Parameter budget: the
pipeline refuses to fit a stage exceeding 11 features."*

§8, the retention rule, lines 176-178:

    **Retention rule (pre-registered; adapted from the ledger's Section 6):** stage k is
    kept only if, versus the last retained stage, out of sample it
    1. reduces multiclass **log loss** by >= 2% relative, **and**
    2. does not reduce the decision-value test statistic (H-O2).

WHY `ols` SOLVES BY THE NORMAL EQUATIONS AND USES `lstsq` ONLY AS A RANK ORACLE
------------------------------------------------------------------------------
`np.linalg.lstsq` and `inv(X'X) @ (X'y)` are **not bit-identical**, measured on this
machine before this module was written: up to 4.4e-16 apart (a few units in the last
place) on a 60x3 Gaussian design, and on a six-row design whose exact answer is the
integer pair (4, 3), `lstsq` returns `0x1.7ffffffffffffp+1` = 2.9999999999999996 for the
second coefficient. D365's numbers are the ones this programme has published. A library
that re-solved them by SVD would move every future number in the last bits against the
runner it claims to reuse, for no accuracy that anything here can use — so the solve is
D365's, asserted `==` against it on arbitrary synthetic designs, and `lstsq` supplies the
**rank and the singular values**, which is what naming a linearly dependent column
requires and which `np.linalg.inv` cannot give. `inv` on a singular matrix raises
`LinAlgError` and on a nearly-singular one returns confident nonsense; the rank check runs
first, so the second case is refused rather than reported.

This module reads no fixture and computes no strategy return.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

__all__ = [
    "FeatureBudget",
    "FeatureBudgetError",
    "OLSFit",
    "RetentionResult",
    "multiclass_log_loss",
    "ols",
    "retention_check",
    "rolling_ols",
]


# --------------------------------------------------------------------------- OLS


@dataclass(frozen=True, eq=False)
class OLSFit:
    """One least-squares fit.

    `eq=False` for the reason `folds.Fold` gives: a dataclass `__eq__` over numpy arrays
    raises `ValueError` on `a == b`, and a comparison that raises is a false affordance.
    Compare `coef.tobytes()`.

    Units are the caller's: `coef[j]` carries units of `y` per unit of column `j`, `resid`
    and both standard errors follow. Nothing here is annualised, scaled or in basis points.

    `se_ols` is the classical homoskedastic standard error — **the primary one**, because
    it is the one `run_d365_momentum_buffer.py` quotes. `se_nw` is Newey-West with a
    Bartlett kernel at `nw_lag` lags and no small-sample correction on the meat matrix; at
    `nw_lag = 0` it is the White heteroskedasticity-consistent standard error, which is why
    0 is the default rather than an error.
    """

    coef: np.ndarray
    resid: np.ndarray
    se_ols: np.ndarray
    se_nw: np.ndarray
    n: int
    k: int
    nw_lag: int


def _checked_design(y: np.ndarray, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    yy = np.asarray(y, dtype=float)
    XX = np.asarray(X, dtype=float)
    if yy.ndim != 1:
        raise ValueError(f"y must be 1-D, got shape {yy.shape}")
    if XX.ndim != 2:
        raise ValueError(f"X must be 2-D (n, k), got shape {XX.shape}")
    if XX.shape[0] != yy.size:
        raise ValueError(
            f"X has {XX.shape[0]} row(s) and y has {yy.size}; the design and the target "
            f"were built from different row sets"
        )
    bad_y = np.flatnonzero(~np.isfinite(yy))
    if bad_y.size:
        raise ValueError(
            f"y holds {bad_y.size} non-finite value(s), first at row {int(bad_y[0])} "
            f"({yy[bad_y[0]]}). A NaN target is dropped by nothing here: it would "
            f"propagate silently into the coefficients, the residuals and both SEs."
        )
    bad_X = np.argwhere(~np.isfinite(XX))
    if bad_X.size:
        r, c = int(bad_X[0, 0]), int(bad_X[0, 1])
        raise ValueError(
            f"X holds {bad_X.shape[0]} non-finite value(s), first at row {r}, column {c} "
            f"({XX[r, c]}). Mask the rows before fitting, and say how many were masked."
        )
    return yy, XX


def _assert_full_rank(XX: np.ndarray) -> None:
    """Raise naming the FIRST column that adds no rank, with `lstsq`'s rank as the oracle."""
    n, k = XX.shape
    rank = int(np.linalg.lstsq(XX, np.zeros(n), rcond=None)[2])
    if rank == k:
        return
    for j in range(k):
        if not np.any(XX[:, j]):
            raise ValueError(
                f"X column {j} is exactly zero, so the design has rank {rank} of {k}. A "
                f"zero column is not a coefficient of zero: the least-squares problem is "
                f"rank deficient and its solution is not unique. Drop the column."
            )
    for j in range(1, k):
        if int(np.linalg.matrix_rank(XX[:, : j + 1])) <= int(
            np.linalg.matrix_rank(XX[:, :j])
        ):
            raise ValueError(
                f"X column {j} is a linear combination of columns 0..{j - 1}: the design "
                f"has rank {rank} of {k}. The normal equations would either raise or "
                f"return a confident answer that depends on rounding. Drop the column or "
                f"reparameterise."
            )
    raise ValueError(  # pragma: no cover - defensive; the loop above finds the column
        f"X has rank {rank} of {k} and no single column explains it"
    )


def ols(
    y: np.ndarray, X: np.ndarray, *, nw_lag: int = 0, intercept: bool = False
) -> OLSFit:
    """Ordinary least squares, bit-identical to `run_d365_momentum_buffer.py:762 ols`.

    `intercept=False` is the default because that is the convention of the one existing
    call site: `run_d365_momentum_buffer.py:847` builds `Xr = np.column_stack([np.ones(n),
    m_f, smb])` and passes it in, so the ones column is the CALLER's and is column 0.
    `intercept=True` prepends that same column here, in that same position, so a coefficient
    vector means the same thing either way.

    Raises on `n <= k` (no residual degrees of freedom, and `s2` would divide by zero or a
    negative), on any non-finite entry, and on a rank-deficient design — naming the column.
    """
    yy, XX = _checked_design(y, X)
    if intercept:
        XX = np.column_stack([np.ones(yy.size), XX])
    n, k = XX.shape
    if n <= k:
        raise ValueError(
            f"need n > k, got n = {n} and k = {k}. With n == k the fit is exact and s2 "
            f"divides by zero; with n < k it is underdetermined. There is no standard "
            f"error to report either way."
        )
    if isinstance(nw_lag, bool) or not isinstance(nw_lag, (int, np.integer)):
        raise TypeError(f"nw_lag must be an int, got {type(nw_lag).__name__}")
    if nw_lag < 0:
        raise ValueError(f"nw_lag must be >= 0, got {nw_lag}")
    if nw_lag >= n:
        raise ValueError(
            f"nw_lag = {nw_lag} with only {n} observation(s): the lag-{nw_lag} "
            f"autocovariance is formed from an empty overlap and contributes exactly zero, "
            f"so the SE would look finite and mean nothing"
        )
    _assert_full_rank(XX)

    # ---- from here to `se_nw` this is run_d365_momentum_buffer.py:762, operation for
    # ---- operation, so that the equality asserted in tests/unit/test_fit.py is `==`.
    XtX_inv = np.linalg.inv(XX.T @ XX)
    b = XtX_inv @ (XX.T @ yy)
    e = yy - XX @ b
    s2 = float(e @ e) / (n - k)
    se = np.sqrt(np.diag(s2 * XtX_inv))
    S = (XX * e[:, None]).T @ (XX * e[:, None])
    for L in range(1, nw_lag + 1):
        w = 1.0 - L / (nw_lag + 1.0)
        G = (XX[L:] * e[L:, None]).T @ (XX[:-L] * e[:-L, None])
        S = S + w * (G + G.T)
    se_nw = np.sqrt(np.diag(XtX_inv @ S @ XtX_inv))
    # ---- end of the pinned block.

    return OLSFit(coef=b, resid=e, se_ols=se, se_nw=se_nw, n=n, k=k, nw_lag=nw_lag)


# --------------------------------------------------------------------------- rolling OLS


def _prefix(a: np.ndarray, axis: int = -1) -> np.ndarray:
    """`prescreen_cross_sectional.py:130 _prefix`, retyped operation for operation."""
    pad = list(a.shape)
    pad[axis] = 1
    return np.concatenate((np.zeros(pad), np.cumsum(a, axis=axis)), axis=axis)


def rolling_ols(
    y: np.ndarray, x: np.ndarray, window: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """OLS of each row of `y` on `x` over the CAUSAL window `[t-window+1 .. t]`.

    Bit-identical to `scripts/prescreen_cross_sectional.py:147 rolling_ols`, which itself
    carries a reuse pin at `:239` against `run_uptrend_onset.rolling_fit`. Returns
    `(alpha, beta, resid_sd, n)`, NaN wherever the window is short; `resid_sd` is the
    per-bar residual standard deviation with ddof = 2.

    The runner states the property with `assert`, which `python -O` removes; this raises.
    Nothing else about the arithmetic differs, and the guards run before any of it.
    """
    y = np.atleast_2d(np.asarray(y, dtype=float))
    x = np.asarray(x, dtype=float)
    if y.ndim != 2:
        raise ValueError(f"y must be 1-D or 2-D, got shape {y.shape}")
    T = y.shape[1]
    if x.shape != (T,):
        raise ValueError(
            f"the regressor must be one value per bar: x has shape {x.shape} and y has "
            f"{T} bar(s)"
        )
    if isinstance(window, bool) or not isinstance(window, (int, np.integer)):
        raise TypeError(f"window must be an int, got {type(window).__name__}")
    if window < 3:
        raise ValueError(
            f"window must be >= 3, got {window}: resid_sd divides by n - 2, so a window of "
            f"2 reports a standard deviation of zero for a line through two points"
        )

    # ---- prescreen_cross_sectional.py:147 from here down.
    Px, Pxx = _prefix(x), _prefix(x * x)
    Py, Pxy, Pyy = _prefix(y, 1), _prefix(y * x[None, :], 1), _prefix(y * y, 1)

    t = np.arange(T)
    hi = t + 1
    lo = np.clip(t + 1 - window, 0, T)
    n = (hi - lo).astype(float)
    Sx, Sxx = Px[hi] - Px[lo], Pxx[hi] - Pxx[lo]
    Sy, Sxy, Syy = (P[:, hi] - P[:, lo] for P in (Py, Pxy, Pyy))

    den = n * Sxx - Sx * Sx
    good = (n >= window) & (den > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        beta = np.where(good[None, :], (n * Sxy - Sx[None, :] * Sy) / den[None, :], np.nan)
        alpha = (Sy - beta * Sx[None, :]) / n[None, :]
        sse = np.maximum(Syy - alpha * Sy - beta * Sxy, 0.0)
        sd = np.sqrt(sse / np.maximum(n - 2.0, 1.0)[None, :])
    return alpha, beta, np.where(good[None, :], sd, np.nan), n
    # ---- end of the pinned block.


# --------------------------------------------------------------------------- log loss


def multiclass_log_loss(p: np.ndarray, y: np.ndarray, *, eps: float | None = None) -> float:
    """Mean `-log p[i, y[i]]` over the rows of `p`. The retention rule's clause 1 statistic.

    `p` is `(n, n_classes)` of probabilities, `y` is `(n,)` of class indices. Rows must sum
    to 1 within 1e-12; a row that does not is a model whose output is not a distribution and
    whose log loss is not comparable to anything.

    **A zero probability on the realised class RAISES unless `eps` is given, and that is
    deliberate.** `-log(0)` is `+inf`, and a library that silently clipped it would return a
    large finite number — which reads as "a bad model" when what actually happened is that
    the model called the observed outcome impossible. Those two have different fixes: the
    first is a worse feature set, the second is a broken fit, a mislabelled class or a
    softmax that underflowed. Clipping makes them indistinguishable in exactly the place the
    retention rule reads. A caller who means to clip passes `eps` and the clip is then
    visible at the call site, in the record, rather than buried in this function.
    """
    pp = np.asarray(p, dtype=float)
    yy = np.asarray(y)
    if pp.ndim != 2:
        raise ValueError(f"p must be 2-D (n, n_classes), got shape {pp.shape}")
    if pp.shape[1] < 2:
        raise ValueError(
            f"p has {pp.shape[1]} class column(s); a multiclass loss needs at least 2"
        )
    if yy.ndim != 1:
        raise ValueError(f"y must be 1-D, got shape {yy.shape}")
    if yy.size != pp.shape[0]:
        raise ValueError(f"p has {pp.shape[0]} row(s) and y has {yy.size}")
    if yy.size == 0:
        raise ValueError("p and y are empty; the mean of no losses is not 0, it is undefined")
    if yy.dtype.kind not in "iu":
        raise TypeError(f"y must hold integer class indices, got dtype {yy.dtype}")
    if not np.all(np.isfinite(pp)):
        bad = np.argwhere(~np.isfinite(pp))
        raise ValueError(f"p holds a non-finite value at row {int(bad[0, 0])}, class {int(bad[0, 1])}")
    lo = np.flatnonzero((pp < 0.0).any(axis=1) | (pp > 1.0).any(axis=1))
    if lo.size:
        raise ValueError(
            f"p row {int(lo[0])} holds a value outside [0, 1]: {pp[lo[0]].tolist()}"
        )
    sums = pp.sum(axis=1)
    off = np.flatnonzero(np.abs(sums - 1.0) > 1e-12)
    if off.size:
        raise ValueError(
            f"p row {int(off[0])} sums to {sums[off[0]]!r}, which is {sums[off[0]] - 1.0:+.3e} "
            f"from 1 and outside the 1e-12 bar. An unnormalised row is not a distribution "
            f"and its log loss is not on the same scale as a normalised one's."
        )
    out = np.flatnonzero((yy < 0) | (yy >= pp.shape[1]))
    if out.size:
        raise ValueError(
            f"y[{int(out[0])}] = {int(yy[out[0]])} is not a class index of a "
            f"{pp.shape[1]}-class distribution"
        )
    realised = pp[np.arange(yy.size), yy]
    if eps is None:
        zero = np.flatnonzero(realised <= 0.0)
        if zero.size:
            raise ValueError(
                f"p[{int(zero[0])}, {int(yy[zero[0]])}] = {realised[zero[0]]!r}: the model "
                f"gave the REALISED class probability zero, so the log loss is +inf. This "
                f"is not clipped by default, because a clipped loss hides a broken model "
                f"behind a merely bad number. Pass eps= to clip, and say so in the record."
            )
    else:
        if not (0.0 < eps < 1.0):
            raise ValueError(f"eps must be in (0, 1), got {eps!r}")
        realised = np.maximum(realised, eps)
    return float(np.mean(-np.log(realised)))


# --------------------------------------------------------------------------- the budget


class FeatureBudgetError(ValueError):
    """A stage asks for more features than §7.3's ceiling allows."""


@dataclass(frozen=True)
class FeatureBudget:
    """`OPENING_AGENT_STATE_PREREG.md` §7.3: "3 non-base classes x (features + 1) <= 36".

    The ceiling is a PARAMETER count, not a feature count, and the `+ 1` is the per-class
    intercept: a multinomial logit with `F` features and one intercept per non-base class
    carries `non_base_classes * (F + 1)` free parameters. `max_features` inverts it.

    Defaults are the doc's: 3 non-base classes (four day types, one of them the base) and a
    ceiling of 36, giving 11 — which §8's stage table reaches with equality at S-G, so an
    off-by-one in either direction changes the pre-registration rather than a margin.
    """

    non_base_classes: int = 3
    ceiling: int = 36

    def __post_init__(self) -> None:
        for name, value in (
            ("non_base_classes", self.non_base_classes),
            ("ceiling", self.ceiling),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an int, got {type(value).__name__}")
            if value < 1:
                raise ValueError(f"{name} must be >= 1, got {value}")
        if self.ceiling < 2 * self.non_base_classes:
            raise ValueError(
                f"ceiling {self.ceiling} with {self.non_base_classes} non-base class(es) "
                f"leaves room for {self.ceiling // self.non_base_classes - 1} feature(s); a "
                f"budget that forbids even one feature is a typo, not a constraint"
            )

    @property
    def max_parameters(self) -> int:
        """The ceiling itself, named, so the arithmetic below is readable."""
        return self.ceiling

    @property
    def max_features(self) -> int:
        """`floor(ceiling / non_base_classes) - 1`. 36 / 3 - 1 = **11** at the defaults."""
        return self.ceiling // self.non_base_classes - 1

    def parameters(self, n_features: int) -> int:
        """`non_base_classes * (n_features + 1)`. 3 * (11 + 1) = 36; 3 * (12 + 1) = 39."""
        if isinstance(n_features, bool) or not isinstance(n_features, (int, np.integer)):
            raise TypeError(f"n_features must be an int, got {type(n_features).__name__}")
        if n_features < 0:
            raise ValueError(f"n_features must be >= 0, got {n_features}")
        return self.non_base_classes * (int(n_features) + 1)

    def assert_within(self, n_features: int) -> int:
        """Raise `FeatureBudgetError` if the stage exceeds the ceiling; else return the count.

        Unit test 13: *"the pipeline refuses to fit a stage exceeding 11 features."* Returns
        the parameter count so a caller can log what it spent, and raises rather than
        warning because §1 line 21 says *"Exceeding it requires a doc amendment"* — a
        warning is not an amendment.
        """
        used = self.parameters(n_features)
        if used > self.ceiling:
            raise FeatureBudgetError(
                f"stage asks for {n_features} features = {self.non_base_classes} non-base "
                f"classes x ({n_features} + 1) = {used} parameters, above the ceiling of "
                f"{self.ceiling}. OPENING_AGENT_STATE_PREREG.md 7.3: \"Ceiling: 3 non-base "
                f"classes x (features + 1) <= 36, so at most 11 features in any stage.\" "
                f"The most this budget allows is {self.max_features}. Exceeding it requires "
                f"a doc amendment (7.3, line 21), not a code change."
            )
        return used


# --------------------------------------------------------------------------- retention


@dataclass(frozen=True)
class RetentionResult:
    """Both clauses of the retention rule, reported whichever one decided.

    `rel_reduction` is dimensionless — `(logloss_prev - logloss_new) / logloss_prev`, so
    +0.125 is "12.5% better". `dv_not_reduced` is clause 2 on its own. `reason` names every
    clause that failed, never only the first.
    """

    kept: bool
    rel_reduction: float
    dv_not_reduced: bool
    reason: str


def retention_check(
    logloss_prev: float,
    logloss_new: float,
    dv_prev: float,
    dv_new: float,
    *,
    rel: float = 0.02,
) -> RetentionResult:
    """`OPENING_AGENT_STATE_PREREG.md` lines 176-178, both clauses, both reported.

    Stage k is kept only if, versus the last retained stage, out of sample it (1) reduces
    multiclass log loss by >= `rel` relative AND (2) does not reduce the decision-value
    statistic (H-O2). Ties go to the incumbent on clause 1 — the bar is `>= rel` on the
    reduction, so an exactly-2% improvement is kept — and to the challenger on clause 2,
    where `dv_new == dv_prev` is "not reduced".

    **Both clauses are in the result even when only one fired**, because a bare "not kept"
    reads as a log-loss failure and the two have opposite fixes: clause 1 says the features
    add nothing, clause 2 says they add something the decision cannot use.
    """
    for name, value in (
        ("logloss_prev", logloss_prev),
        ("logloss_new", logloss_new),
        ("dv_prev", dv_prev),
        ("dv_new", dv_new),
        ("rel", rel),
    ):
        v = float(value)
        if not math.isfinite(v):
            raise ValueError(f"{name} must be finite, got {value!r}")
    if float(logloss_prev) <= 0.0:
        raise ValueError(
            f"logloss_prev must be > 0, got {logloss_prev!r}: the relative reduction "
            f"divides by it, and a non-positive multiclass log loss is impossible"
        )
    if float(logloss_new) < 0.0:
        raise ValueError(f"logloss_new must be >= 0, got {logloss_new!r}")
    if not (0.0 <= float(rel) < 1.0):
        raise ValueError(f"rel must be in [0, 1), got {rel!r}")

    rel_reduction = (float(logloss_prev) - float(logloss_new)) / float(logloss_prev)
    clause1 = rel_reduction >= float(rel)
    dv_not_reduced = float(dv_new) >= float(dv_prev)
    failed = []
    if not clause1:
        failed.append(
            f"clause 1: log loss fell {rel_reduction:+.4%} relative, below the "
            f"{float(rel):.2%} bar"
        )
    if not dv_not_reduced:
        failed.append(
            f"clause 2: decision value fell {float(dv_prev):.6f} -> {float(dv_new):.6f}"
        )
    if failed:
        reason = "; ".join(failed)
    else:
        reason = (
            f"clause 1: log loss fell {rel_reduction:+.4%} relative, at or above the "
            f"{float(rel):.2%} bar; clause 2: decision value {float(dv_prev):.6f} -> "
            f"{float(dv_new):.6f}, not reduced"
        )
    return RetentionResult(
        kept=bool(clause1 and dv_not_reduced),
        rel_reduction=rel_reduction,
        dv_not_reduced=dv_not_reduced,
        reason=reason,
    )
