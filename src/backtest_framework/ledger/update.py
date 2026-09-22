"""Section 5.2's scalar update and Section 7.1's timing rule (D610).

The update step is the only place the settlement flow ledger meets an observation. Everything
in `ledger/flows.py` is a PRIOR computed from fund facts; this module folds in the flow that
has already printed before tau, and decides when tau may be.

THE FORMULAS, QUOTED VERBATIM
-----------------------------
Section 5.2, line 368::

    z = S_pre[t, tau] - S_norm[tau]

line 371::

    `S_pre` is the aggressor-signed outright volume in the traded contract from 13:30 ET to
    tau. `S_norm` is its trailing 20-day mean for the same interval.

line 373::

    Measurement model: `z = p x Q_total + eps`, with `eps ~ N(0, R)`.

lines 375-376::

    `p` = pre-absorption fraction (the share of total flow executed before tau). **Latent.**
    `R` = measurement noise variance. **Estimated.**

lines 380-384::

    K     = p sigma^2_total / (p^2 sigma^2_total + R)
    Q_hat = mu_total + K (z - p mu_total)
    sigma^2_post = (1 - K p) sigma^2_total
    Q_rem = (1 - p) x Q_hat
    sigma_rem = (1 - p) x sqrt(sigma^2_post)

Section 7.1, line 428::

    Candidate t0 in {13:50, 14:00, 14:10} ET (for a 14:28 window start; shift if the verified
    window differs).

line 430::

    **Earliest-pass rule (primary):** evaluate at 13:50. If the trade criteria pass, signal.
    If not, re-evaluate at 14:00, then 14:10. At most one entry per instrument per day.

Section 7.3, line 445::

    **Hard constraint:** the entry must be complete at least 3 minutes before `W_start`. If
    not, no trade.

Section 12, required unit tests:

  5  (line 711) "Update step: with p = 0 the posterior equals the prior and Q_rem =
      mu_total; with R -> infinity, K -> 0."
  6  (line 712) "Update step: a known synthetic case (mu = 100, sigma^2 = 400, p = 0.5,
      R = 100, z = 60) matches hand-calculated K, Q_hat, Q_rem."
  8  (line 714) "No look-ahead: V_d, sigma_d, S_norm and the fund data used on day t exclude
      data from day t onward (fund data respects `published_at`)."
  9  (line 715) "Earliest-pass rule: signals at the first passing t0 and never re-enters."

WHAT IS EXACT, MEASURED
-----------------------
Required unit test 6's case is exact in binary64 on four of its five outputs and this module
asserts them with ``==`` in the golden: ``K = 200/200 = 1.0``, ``Q_hat = 110.0``,
``sigma^2_post = 200.0``, ``Q_rem = 55.0``. Every operand on the path is a binary fraction or
a small integer (0.5 is 2^-1, 0.5 x 0.5 = 0.25, 0.25 x 400 = 100), and a quotient of two
equal finite doubles is 1.0 by IEEE-754 rather than by luck. The fifth,
``sigma_rem = 5 sqrt(2) = 7.0710678118654752...``, is irrational and is the one asserted to a
tolerance.

``R = math.inf`` is ACCEPTED and gives ``K == 0.0`` exactly -- a finite double divided by
infinity is a zero under IEEE-754, so line 711's "R -> infinity, K -> 0" is an equality here
and not a limit. ``R = 0`` is refused: a measurement with no noise at all is a claim nothing
in Section 8 can fit, and at ``p = 0`` it also makes ``K = 0/0 = nan``.

WHAT IS NOT HERE
----------------
``p`` and ``R`` are LATENT and ESTIMATED (lines 375-376, Section 8). Nothing in this module
fits them; they are arguments. Section 9B.2's parameter-recovery and decision-relevance
procedures for ``p`` are a study, not a library function.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

from .flows import LedgerError, _finite, _fraction

__all__ = [
    "Update",
    "entry_decision",
    "kalman_update",
    "s_pre_z",
    "trailing_mean_20",
]

#: Section 7.1 line 428. ET, "HH:MM".
CANDIDATE_T0 = ("13:50", "14:00", "14:10")
#: Section 7.3 line 445. Minutes of clearance required between entry completion and W_start.
ENTRY_CLEARANCE_MIN = 3
#: Section 5.2 line 371. Days in S_norm's trailing window.
S_NORM_LOOKBACK_DAYS = 20


# --------------------------------------------------------------------------- S_pre, S_norm


def trailing_mean_20(
    series_by_day: Mapping[str, float], day: str, lookback_days: int = S_NORM_LOOKBACK_DAYS
) -> float:
    """``S_norm[tau]``: line 371's "trailing 20-day mean for the same interval".

    ``series_by_day`` maps an ISO day to that day's ``S_pre`` over the SAME 13:30-to-tau
    interval. One value per day; the caller has already fixed tau.

    **A day at or after ``day`` RAISES** -- required unit test 8 (line 714), which names
    ``S_norm`` explicitly among the quantities that "exclude data from day t onward". The
    refusal is loud rather than a filter for the reason `costs/futures_impact.py:361
    depth_bar` gives: a filter that drops the offending row leaves the caller believing a
    guard ran when what actually happened is that their input was wrong.

    A short window raises too. The mean is :func:`math.fsum` divided by the count, so it does
    not depend on the order the days arrived in.
    """
    if not isinstance(series_by_day, Mapping):
        raise LedgerError(
            f"trailing_mean_20: series_by_day must be a mapping, got {type(series_by_day).__name__}"
        )
    if not isinstance(day, str) or not day:
        raise LedgerError(f"trailing_mean_20: day must be a non-empty ISO string, got {day!r}")
    if isinstance(lookback_days, bool) or not isinstance(lookback_days, int) or lookback_days <= 0:
        raise LedgerError(f"trailing_mean_20: lookback_days must be a positive int, got {lookback_days!r}")

    leaked = sorted(d for d in series_by_day if d >= day)
    if leaked:
        raise LedgerError(
            f"trailing_mean_20: {len(leaked)} day(s) at or after the evaluation day {day} "
            f"reached the trailing window, first {leaked[0]}. Required unit test 8 names "
            "S_norm among the quantities that must exclude day t onward; a same-day S_pre in "
            "its own trailing mean is look-ahead."
        )
    prior = sorted(series_by_day)[-lookback_days:]
    if len(prior) < lookback_days:
        raise LedgerError(
            f"trailing_mean_20: only {len(prior)} prior day(s) before {day}, and the window "
            f"asks for {lookback_days}. A short window silently averaged is how a warm-up "
            "period becomes a result."
        )
    values = [_finite(f"S_pre on {d}", series_by_day[d]) for d in prior]
    return math.fsum(values) / len(values)


def s_pre_z(s_pre: float, s_norm: float) -> float:
    """Line 368: ``z = S_pre[t, tau] - S_norm[tau]``.

    Signed, in contracts of the traded month, on the same sign convention as every flow term
    (line 143, + = buy). Despite the name in the document it is a DIFFERENCE, not a z-score:
    nothing divides by a standard deviation here, and line 373 then treats ``z`` as a
    measurement of ``p x Q_total`` in flow units. A study that standardised it would be
    measuring a different quantity from the one ``R`` is fitted against.
    """
    return _finite("s_pre", s_pre) - _finite("s_norm", s_norm)


# --------------------------------------------------------------------------- the update


@dataclass(frozen=True)
class Update:
    """The five outputs of lines 380-384, in the caller's own flow units.

    ``k`` is dimensionless, ``q_hat`` and ``q_rem`` are in the units of ``mu_total``,
    ``var_post`` in their square and ``sigma_rem`` back in the units of ``mu_total``. Nothing
    is annualised or scaled.
    """

    k: float
    q_hat: float
    var_post: float
    q_rem: float
    sigma_rem: float


def kalman_update(mu: float, var: float, p: float, R: float, z: float) -> Update:
    """Lines 380-384, in the order the document writes them.

    ``p`` in [0, 1] (Section 8's constraint, asserted not clipped), ``var >= 0``, ``R > 0``
    with ``math.inf`` accepted, ``mu`` and ``z`` finite.

    ``R = math.inf`` returns ``k == 0.0`` EXACTLY, so ``q_hat == mu`` and ``var_post == var``
    exactly: line 711's "R -> infinity, K -> 0" is an equality under IEEE-754 division and
    this function does not approximate it. ``R = 0`` is refused -- a noiseless measurement is
    not something Section 8 can estimate, and at ``p = 0`` it makes ``K`` a ``0/0`` nan.

    ``p = 0`` returns the prior unchanged and ``q_rem == mu``, exactly, which is line 711's
    other half. Note that ``p = 1`` is admissible and means every contract of the total has
    already traded: ``q_rem`` is then ``0.0`` and ``sigma_rem`` is ``0.0``, so Section 5.3's
    predicted move is zero and Section 7.2's criteria cannot pass. That is the correct
    behaviour and it is worth stating, because it is the one input for which the strategy
    always declines to trade.
    """
    m = _finite("mu", mu)
    v = _finite("var", var)
    pp = _fraction("p", p)
    zz = _finite("z", z)
    if v < 0.0:
        raise LedgerError(f"var must be non-negative, got {v!r}")
    if isinstance(R, bool) or not isinstance(R, (int, float)):
        raise LedgerError(f"R must be a real number, got {R!r}")
    rr = float(R)
    if math.isnan(rr):
        raise LedgerError("R is nan")
    if rr <= 0.0:
        raise LedgerError(
            f"R must be positive, got {rr!r}. R is the measurement noise VARIANCE (line 376); "
            "R = 0 asserts that the observed pre-window flow measures p x Q_total with no "
            "error at all, and at p = 0 it makes K a 0/0 nan rather than the 0 line 711 "
            "requires. math.inf is accepted and gives K == 0.0 exactly."
        )

    k = pp * v / (pp * pp * v + rr)
    q_hat = m + k * (zz - pp * m)
    var_post = (1.0 - k * pp) * v
    q_rem = (1.0 - pp) * q_hat
    sigma_rem = (1.0 - pp) * math.sqrt(var_post)
    return Update(k=k, q_hat=q_hat, var_post=var_post, q_rem=q_rem, sigma_rem=sigma_rem)


# --------------------------------------------------------------------------- the timing rule


def _minutes_et(label: str, what: str) -> int:
    """"HH:MM" or "HH:MM:SS" ET as minutes past midnight. Seconds must be zero.

    A window start of 14:28:30 would make "3 minutes before" ambiguous at minute resolution,
    and the strategy's clock is one-minute bars (Section 7.3), so a non-zero second is
    refused rather than truncated.
    """
    if not isinstance(label, str):
        raise LedgerError(f"{what} must be a string like '14:10', got {label!r}")
    parts = label.split(":")
    if len(parts) not in (2, 3) or not all(q.isdigit() for q in parts):
        raise LedgerError(f"{what} must be 'HH:MM' or 'HH:MM:SS' in ET, got {label!r}")
    hh, mm = int(parts[0]), int(parts[1])
    ss = int(parts[2]) if len(parts) == 3 else 0
    if not (0 <= hh < 24 and 0 <= mm < 60 and 0 <= ss < 60):
        raise LedgerError(f"{what} is not a valid time of day: {label!r}")
    if ss != 0:
        raise LedgerError(
            f"{what} = {label!r} carries a non-zero second. Section 7.3 works in one-minute "
            "bars, so a sub-minute window start would make 'complete at least 3 minutes "
            "before W_start' ambiguous. Round it in the caller, deliberately."
        )
    return hh * 60 + mm


def entry_decision(
    candidates: Sequence[str] = CANDIDATE_T0,
    *,
    passes: Mapping[str, bool],
    w_start: str,
    entry_minutes: int,
) -> str | None:
    """Line 430's earliest-pass rule under line 445's hard constraint.

    Returns the FIRST candidate t0 whose criteria pass and whose entry completes at least
    ``ENTRY_CLEARANCE_MIN`` minutes before ``w_start``, or ``None``.

    ``entry_minutes`` is how long the entry takes to complete, measured from t0. Section
    7.3's primary fill is "close of bar t0+1", i.e. two minutes; the stress fill is "worst
    close among bars t0+1 ... t0+5", i.e. six. It is an argument rather than a constant
    because the two fill models give different answers to line 445 and the study has to say
    which one it is testing.

    ``w_start`` is ET, "HH:MM" or "HH:MM:SS". **It is an argument and this module never
    looks it up.** The table is `data/settlement_windows.csv`, served by
    `scripts/settlement_windows.py:147 window_for`, which raises rather than defaulting -- and
    `src/` may never import `scripts/` (`tests/unit/test_import_boundaries.py`). The tests
    pull NG's 14:28:00 from `window_for` and pass it in, which is also what a runner must do.

    "At most one entry per instrument per day" is carried by the shape of the function: it
    returns one t0 or ``None`` and holds no state to re-enter from. A caller that called it
    twice in a day would be writing a different rule, and no argument here permits it.
    """
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise LedgerError(f"candidates must be a sequence of 'HH:MM' strings, got {candidates!r}")
    if not candidates:
        raise LedgerError("candidates is empty; line 428 registers three and a study may not drop all of them")
    if not isinstance(passes, Mapping):
        raise LedgerError(f"passes must be a mapping, got {type(passes).__name__}")
    if isinstance(entry_minutes, bool) or not isinstance(entry_minutes, int):
        raise LedgerError(f"entry_minutes must be an int, got {entry_minutes!r}")
    if entry_minutes < 0:
        raise LedgerError(f"entry_minutes must be non-negative, got {entry_minutes}")

    mins = [_minutes_et(c, f"candidate t0 {c!r}") for c in candidates]
    if mins != sorted(mins) or len(set(mins)) != len(mins):
        raise LedgerError(
            f"candidates {list(candidates)} are not strictly increasing. 'Evaluate at 13:50 "
            "... then 14:00, then 14:10' is an ORDER, and an unordered list makes "
            "'earliest-pass' meaningless."
        )
    unknown = sorted(set(passes) - set(candidates))
    if unknown:
        raise LedgerError(
            f"passes carries {unknown}, which are not candidates {list(candidates)}. A verdict "
            "for a t0 the rule never evaluates is a rule nobody registered."
        )
    missing = [c for c in candidates if c not in passes]
    if missing:
        raise LedgerError(
            f"passes has no verdict for {missing}. Every candidate must be evaluated or "
            "explicitly declared False; a missing key read as 'did not pass' would hide a "
            "criteria function that failed to run."
        )
    for c in candidates:
        if not isinstance(passes[c], bool):
            raise LedgerError(f"passes[{c!r}] must be a bool, got {passes[c]!r}")

    deadline = _minutes_et(w_start, "w_start") - ENTRY_CLEARANCE_MIN
    for label, t0 in zip(candidates, mins):
        if not passes[label]:
            continue
        if t0 + entry_minutes > deadline:
            # Line 445 is a HARD constraint: a passing t0 whose entry lands late is not
            # traded, and the rule does not fall back to an earlier t0 that already failed.
            return None
        return label
    return None
