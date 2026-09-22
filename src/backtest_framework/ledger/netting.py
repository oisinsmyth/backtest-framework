"""Section 8A.2's swap-dealer calibration, and the two point-in-time keys it needs (D610).

THE FORMULAS, QUOTED VERBATIM
-----------------------------
Section 8A.2, lines 491-496::

    Weekly, for NG and CL (all months, futures-equivalent contracts):

    DeltaSD_w  = change in CFTC swap-dealer net position, week w
    DeltaSX_w  = predicted change in swap-routed client exposure in the same week
                 = Sum US funds' (1 - f_fut) exposure changes + Sum P9 exposure changes
    Fit:  DeltaSD_w = lambda x DeltaSX_w + eps_w,        lambda in [0, 1] approx 1 - (netting fraction)

lines 498-500::

    - lambda-hat and its standard error act as an **informative prior** on (1 - n) and
      (1 - n9) when fitting on window flow (Section 8).
    - **Consistency check:** if the flow-fitted n differs from 1 - lambda-hat by more than 2
      combined standard errors, flag it in the report. Neither estimate overrides the other
      automatically.
    - Swap dealers also hedge unrelated client books, so lambda is expected to be noisy.
      That's why it's used as a prior, not as a replacement.

Section 3.3d, line 128::

    Point-in-time rules from Section 0 apply to all of these: COT data is usable only after
    its Friday release; swap-dissemination records only after their dissemination timestamp.

Section 8A.3, line 504::

    From public swap dissemination, identify swaps referencing NG or crude futures or
    commodity indices. Aggregate by day and time of dissemination.

Required unit tests 41 (line 747), 42 (line 748), 43 (line 749), 44 (line 750).

WHY CLIPPING IS THE EXACT CONSTRAINED FIT AND NOT A REPAIR
----------------------------------------------------------
``SSE(lambda) = Sum_w (y_w - lambda x_w)^2`` is a quadratic in ONE variable with positive
leading coefficient ``Sum x^2``, so it is strictly convex; it has the unique stationary point
``lambda_hat = Sum xy / Sum x^2`` and is strictly decreasing to its left and strictly
increasing to its right. The minimiser of a strictly convex function over a closed interval
is therefore the PROJECTION of the unconstrained minimiser onto that interval, and
``clip(lambda_hat, 0, 1)`` IS ``argmin SSE`` over [0, 1] -- exactly, not approximately.

**This is true only because there is one parameter and no intercept.** With two or more
coefficients, projecting the unconstrained solution onto a box is not the constrained
solution (the projection ignores the off-diagonal curvature) and a box-constrained solver
would be needed. There is no box-constrained fitter in this repository and this module does
not add one, because line 496 asks for exactly one slope.

The unconstrained slope and its standard error come from `validation/fit.py:ols` (D606) with
a single column and ``intercept=False``, which is itself pinned bit-for-bit to
`scripts/run_d365_momentum_buffer.py:762`. Nothing re-solves least squares here.
"""

from __future__ import annotations

import datetime as dt
import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

from ..validation.fit import ols
from .flows import LedgerError, _finite, _fraction

__all__ = [
    "COT_RELEASE_WEEKDAY",
    "FundExposure",
    "LambdaFit",
    "consistency_flag",
    "cot_usable_from",
    "fit_lambda",
    "swap_exposure_predictor",
    "swap_record_time",
]

#: Friday. `scripts/fetch_cftc_cot.py:325 RELEASE_WEEKDAY`, same integer, same meaning.
COT_RELEASE_WEEKDAY = 4
#: `scripts/fetch_cftc_cot.py:324`. Before this date there was no weekly Tuesday schedule and
#: the fetcher leaves `release_date_nominal` EMPTY rather than fabricating one.
COT_TUESDAY_CONVENTION_FROM = dt.date(1993, 1, 1)


# --------------------------------------------------------------------------- the lambda fit


@dataclass(frozen=True)
class LambdaFit:
    """8A.2's fitted slope, projected onto [0, 1], with the unconstrained value beside it.

    ``lam`` is dimensionless -- a change in dealer net position per unit change in predicted
    swap-routed client exposure, both in futures-equivalent contracts -- and is line 496's
    ``approx 1 - (netting fraction)``.

    ``se`` is the standard error of the UNCONSTRAINED slope, and that is a stated choice. At a
    binding boundary the constrained estimator's sampling distribution has an atom at the
    boundary and no ordinary standard error describes it; line 498 wants lambda-hat "and its
    standard error" as an INFORMATIVE PRIOR and line 499 puts it inside a two-SE band, so the
    unconstrained SE is the one that says how much the data actually pins the slope. Reporting
    zero -- the exact variance of a point mass -- would make the consistency check fire on
    everything. ``clipped`` is carried so a reader can always see which case they are in.
    """

    lam: float
    se: float
    clipped: bool
    lam_unconstrained: float


def fit_lambda(d_sd: Sequence[float], d_sx: Sequence[float]) -> LambdaFit:
    """Line 496: ``DeltaSD_w = lambda x DeltaSX_w + eps_w`` with ``lambda`` in [0, 1].

    Least squares through the ORIGIN -- the document's formula carries no intercept, and
    adding one would be a different registered model.

    Refuses a degenerate design rather than returning a slope: an all-zero or constant-zero
    ``d_sx`` makes ``Sum x^2 = 0`` and the slope undefined, which `validation/fit.py:ols`
    already reports as rank deficiency naming the column. Refuses fewer than two weeks, since
    ``n > k`` is needed for a residual degree of freedom and therefore for any standard error
    at all.
    """
    y = np.asarray(list(d_sd), dtype=float)
    x = np.asarray(list(d_sx), dtype=float)
    if y.ndim != 1 or x.ndim != 1:
        raise LedgerError("fit_lambda: d_sd and d_sx must be one-dimensional")
    if y.size != x.size:
        raise LedgerError(
            f"fit_lambda: {y.size} DeltaSD value(s) against {x.size} DeltaSX value(s). One week "
            "is one paired observation; a length mismatch means the two series were aligned by "
            "position rather than by week."
        )
    if y.size < 2:
        raise LedgerError(
            f"fit_lambda: {y.size} week(s). With n = k = 1 the fit is exact, the residual "
            "variance divides by zero, and there is no standard error for line 499's two-SE "
            "band to be built from."
        )
    if not np.all(np.isfinite(y)) or not np.all(np.isfinite(x)):
        raise LedgerError("fit_lambda: every DeltaSD and DeltaSX entry must be finite")

    try:
        fit = ols(y, x.reshape(-1, 1), nw_lag=0, intercept=False)
    except ValueError as exc:  # rank deficiency, n <= k, non-finite -- all of them refusals
        raise LedgerError(
            f"fit_lambda: the DeltaSX design cannot be fitted -- {exc}. A constant-zero "
            "DeltaSX means no swap-routed exposure changed in any week of the window, so "
            "lambda is not identified and no prior can be built from it."
        ) from exc
    raw = float(fit.coef[0])
    se = float(fit.se_ols[0])
    if not math.isfinite(raw) or not math.isfinite(se):
        raise LedgerError(
            f"fit_lambda: the fit overflowed (slope {raw!r}, SE {se!r}). Sum DeltaSX^2 is "
            f"{float(np.dot(x, x))!r}; a design that small relative to the residuals pins "
            "nothing, and line 498 would carry the result forward as an 'informative prior'."
        )
    lam = min(1.0, max(0.0, raw))
    return LambdaFit(lam=lam, se=se, clipped=lam != raw, lam_unconstrained=raw)


def consistency_flag(n_hat: float, se_n: float, lam: float, se_lam: float) -> bool:
    """Line 499: ``|n_flow - (1 - lambda_hat)| > 2 x sqrt(SE_n^2 + SE_lambda^2)``.

    Returns the flag and nothing else. Line 499's last sentence is the reason this function
    has no other output: "Neither estimate overrides the other automatically." It reports a
    disagreement; it does not resolve one, and it must never be used to replace ``n``.

    Both ``n_hat`` and ``lam`` are asserted into [0, 1] (Section 8's constraint and line 496's)
    and both standard errors must be finite and non-negative. A zero SE on both sides makes the
    threshold zero, so any disagreement at all flags -- which is correct and is why an SE of
    zero has to be a deliberate input rather than a default.
    """
    n = _fraction("n_hat", n_hat)
    lm = _fraction("lam", lam)
    sn = _finite("se_n", se_n)
    sl = _finite("se_lam", se_lam)
    if sn < 0.0 or sl < 0.0:
        raise LedgerError(f"standard errors must be non-negative, got se_n={sn!r} and se_lam={sl!r}")
    return abs(n - (1.0 - lm)) > 2.0 * math.sqrt(sn * sn + sl * sl)


# --------------------------------------------------------------------------- the predictor


@dataclass(frozen=True)
class FundExposure:
    """One fund's exposure change over week w, for line 495's predictor.

    ``kind`` is ``"us_fund"`` (one of table 3.1's six, which split exposure between futures
    and swaps) or ``"p9"`` (Section 3.1b's non-US leveraged ETPs, which reach CME wholly
    through swap providers -- line 278: "the *required* rebalance is computable with the P1
    formula, but it reaches CME through swap providers, so it takes the P2 treatment").

    ``exposure_change`` is the fund's TOTAL exposure change in USD; the ``(1 - f_fut)`` share
    is taken here, not by the caller, so that line 495's arithmetic lives in one place.

    ``futures_held_change`` exists only to be REFUSED. Required unit test 43 (line 749): "The
    swap-exposure predictor includes only swap-routed exposure (1 - f_fut) and P9, never
    futures-held exposure." A field that raises is a guard; a field that is silently ignored
    is an invitation.
    """

    name: str
    kind: str
    exposure_change: float
    f_fut: float | None = None
    futures_held_change: float | None = None


def swap_exposure_predictor(funds: Sequence[FundExposure]) -> float:
    """Line 495: ``Sum US funds' (1 - f_fut) exposure changes + Sum P9 exposure changes``.

    In USD, signed, summed with :func:`math.fsum` so the total does not depend on the order
    the funds were listed in.

    **A ``FundExposure`` carrying a futures-held term raises**, naming the fund. That is
    required unit test 43 and it is the one error in this predictor that would not look like
    an error: including futures-held exposure inflates ``DeltaSX`` on exactly the funds whose
    ``f_fut`` is high, which biases ``lambda`` DOWNWARD and therefore biases the implied
    netting fraction ``1 - lambda`` UPWARD -- towards "the banks net everything internally",
    which is the conclusion that quietly removes P2 from the ledger.

    A ``us_fund`` must carry ``f_fut``; a ``p9`` must not, because P9's whole exposure is
    swap-routed and an ``f_fut`` on it would be a futures share nobody sourced.
    """
    if isinstance(funds, (str, bytes)) or not isinstance(funds, Sequence):
        raise LedgerError(f"swap_exposure_predictor: funds must be a sequence, got {funds!r}")
    if not funds:
        raise LedgerError(
            "swap_exposure_predictor: no funds. A week with no swap-routed exposure change is "
            "a DeltaSX of 0 stated by the caller, not an empty list read as one."
        )
    seen: set[str] = set()
    parts: list[float] = []
    for f in funds:
        if not isinstance(f, FundExposure):
            raise LedgerError(f"swap_exposure_predictor: expected FundExposure, got {type(f).__name__}")
        if f.name in seen:
            raise LedgerError(f"swap_exposure_predictor: {f.name!r} appears twice")
        seen.add(f.name)
        if f.futures_held_change is not None:
            raise LedgerError(
                f"swap_exposure_predictor: {f.name!r} carries futures_held_change="
                f"{f.futures_held_change!r}. Required unit test 43 (line 749): the predictor "
                "'includes only swap-routed exposure (1 - f_fut) and P9, NEVER futures-held "
                "exposure'. Futures-held flow reaches CME as P1, is already in the ledger, and "
                "putting it in DeltaSX biases lambda down and the implied netting fraction up."
            )
        change = _finite(f"{f.name}.exposure_change", f.exposure_change)
        if f.kind == "us_fund":
            if f.f_fut is None:
                raise LedgerError(
                    f"swap_exposure_predictor: {f.name!r} is a us_fund and carries no f_fut. "
                    "Line 495 takes its (1 - f_fut) share, and a missing futures share is a "
                    "holdings fact nobody sourced -- not a zero."
                )
            parts.append((1.0 - _fraction(f"{f.name}.f_fut", f.f_fut)) * change)
        elif f.kind == "p9":
            if f.f_fut is not None:
                raise LedgerError(
                    f"swap_exposure_predictor: {f.name!r} is a p9 product and carries "
                    f"f_fut={f.f_fut!r}. Line 278 routes every P9 product's rebalance through "
                    "swap providers in full; a futures share on one would be a fact Section "
                    "3.1b does not record."
                )
            parts.append(change)
        else:
            raise LedgerError(
                f"swap_exposure_predictor: {f.name!r} has kind {f.kind!r}; line 495 sums exactly "
                "two groups, 'us_fund' and 'p9'."
            )
    return math.fsum(parts)


# --------------------------------------------------------------------------- the two clocks


def cot_usable_from(report_date: dt.date | str) -> dt.date:
    """Required unit test 41 (line 747): "a weekly record is usable only at or after its
    Friday release timestamp".

    **The rule is this repository's own, not a new one.** `scripts/fetch_cftc_cot.py:397
    release_date_of` computes it and its docstring states it: "The Friday of the report's
    week". Not a flat +3 days -- the survey day shifts on holidays, and the fetcher records
    the measured case (2007-01-03 is a Wednesday because 2007-01-02 was the National Day of
    Mourning for President Ford, and a flat +3 would put that release on a Saturday). This
    function reimplements those five lines rather than importing them, because `src/` may
    never import `scripts/` (`tests/unit/test_import_boundaries.py`); the test pins the two
    against each other on the fetcher's own committed bytes.

    A report dated ON a Friday is pushed to the FOLLOWING Friday, for the fetcher's stated
    reason: a report cannot be published before it is surveyed, and erring late is the only
    safe direction for a conditioning variable.

    **Before 1993-01-01 this RAISES**, where the fetcher writes an empty string. There was no
    weekly Tuesday schedule then (1986 report dates are 46.8% Friday, 16.2% Monday, 16.2%
    Wednesday), and a function that must return a date cannot represent "we do not know" any
    other way. The deposit's sample starts in 2016 (Section 3.3), so this cannot bite a study
    that stays inside it -- and if one strays outside, it is told.
    """
    if isinstance(report_date, str):
        try:
            d = dt.date.fromisoformat(report_date[:10])
        except ValueError as exc:
            raise LedgerError(f"cot_usable_from: {report_date!r} is not an ISO date") from exc
    elif isinstance(report_date, dt.datetime):
        d = report_date.date()
    elif isinstance(report_date, dt.date):
        d = report_date
    else:
        raise LedgerError(f"cot_usable_from: report_date must be a date or ISO string, got {report_date!r}")

    if d < COT_TUESDAY_CONVENTION_FROM:
        raise LedgerError(
            f"cot_usable_from: {d.isoformat()} predates {COT_TUESDAY_CONVENTION_FROM.isoformat()}, "
            "before which there was no weekly Tuesday survey schedule at all -- 1986 report dates "
            "are 46.8% Friday, 16.2% Monday, 16.2% Wednesday (scripts/fetch_cftc_cot.py:318-325). "
            "The fetcher leaves release_date_nominal EMPTY for those rows and this function "
            "raises for the same reason: a fabricated release date would look usable."
        )
    rel = d + dt.timedelta(days=(COT_RELEASE_WEEKDAY - d.weekday()) % 7)
    if rel <= d:
        rel += dt.timedelta(days=7)
    return rel


def swap_record_time(execution_ts: dt.datetime, dissemination_ts: dt.datetime) -> dt.datetime:
    """Required unit test 44 (line 750): swap records are keyed on DISSEMINATION time.

    Line 128: "swap-dissemination records only after their dissemination timestamp." Line 504
    aggregates them "by day and time of dissemination". The execution time is earlier and is
    not knowable to anyone outside the trade, so keying on it is look-ahead of exactly the
    kind Section 0 item 6 forbids -- "Everything used at t0 must be computable from data
    strictly available at the t0 bar close."

    Returns ``dissemination_ts`` unconditionally, and RAISES if it precedes execution: a
    record disseminated before it was executed is a corrupt row, and silently taking the later
    of the two would repair it into something that looks fine.

    Both timestamps must be both-aware or both-naive. Comparing a naive to an aware datetime
    raises in Python anyway; it is caught here so the message names the cause.
    """
    for name, ts in (("execution_ts", execution_ts), ("dissemination_ts", dissemination_ts)):
        if not isinstance(ts, dt.datetime):
            raise LedgerError(f"swap_record_time: {name} must be a datetime, got {type(ts).__name__}")
    aware = [t.tzinfo is not None and t.tzinfo.utcoffset(t) is not None
             for t in (execution_ts, dissemination_ts)]
    if aware[0] != aware[1]:
        raise LedgerError(
            "swap_record_time: one timestamp is timezone-aware and the other is naive. The "
            "dissemination clock is the one a study reads (line 128) and an unlabelled one is "
            "not a clock; make both aware, in UTC or in America/New_York (Section 3.3)."
        )
    if dissemination_ts < execution_ts:
        raise LedgerError(
            f"swap_record_time: dissemination {dissemination_ts.isoformat()} precedes execution "
            f"{execution_ts.isoformat()}. A record cannot be published before the trade it "
            "reports; taking the later of the two would repair a corrupt row into a usable one."
        )
    return dissemination_ts
