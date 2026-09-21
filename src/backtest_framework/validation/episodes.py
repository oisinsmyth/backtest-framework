"""Episode and shared-period checks on a daily P&L series in DOLLARS (D592).

The ledger of record is the deposit's programme-level false-positive controls, written
identically in two documents — `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.8(5) and
`OPENING_AGENT_STATE_PREREG.md` §12A(5):

    Episode concentration: the edge must stay positive after removing the BEST CALENDAR
    YEAR and, separately, the BEST 1% OF DAYS.

    Shared-period dependence: for any two models that both survive, report the
    correlation of their daily P&L and the overlap of their top-10 P&L days. If the
    correlation is > 0.5 AND more than 40% of each model's P&L comes from the same
    months, flag "shared-period risk".

and the ledger's unit test 69 — *"Episode checks: removing the best year and the best 1%
of days are computed correctly on synthetic P&L."*

UNITS. Every input series here is **daily P&L in dollars**, one element per session, with
a parallel array of dates. Dollars, not fractions: the futures programme is dollar-native
at one micro contract (D466, D493), and a fraction-of-compounded-peak drawdown is the
wrong object for it (D542). Nothing in this module compounds, and nothing routes a dollar
series through `analytics/metrics.py`.

THE SHARPE USED THROUGHOUT is `scripts/run_d466_components.py:sharpe` — mean over
standard deviation with `ddof=1`, annualised by sqrt(252), over ALL days in the series
including the zero-P&L ones, and `nan` when the series does not move. It is reproduced
here rather than imported because `src` must not import from `scripts`; the unit tests
assert the two agree to the last bit on a shared series.

WHAT THIS MODULE IS NOT. `episode_checks` returns NUMBERS and one boolean. It does not
return a verdict, it does not promote and it does not reject. The deposit's control 5 is
one condition among many, and CLAUDE.md §2 is explicit that a one-sided trim "is a flag,
not a verdict" — which is why `symmetric_trim` below reports both tails and why
`episode_checks` carries the symmetric trim beside the one-sided drop the docs ask for.

THE D504 PORT. `symmetric_trim` is a key-for-key port of the `concentration_usable` block
of `scripts/d504_arm_full_history.py:345-366`, whose output is published in
`data/d504_arm_full_history.json::concentration_usable`. The port is generalised in one
place only — the trim count `k = max(1, int(n * frac))` replaces the hard-coded
`max(1, len(srt) // 100)` — and the two are equal for every n up to 200,000 at
`frac = 0.01` (asserted in `tests/unit/test_episodes.py`). `top5`, `top10` and
`pnl_ex_both_top10_usd` stay at their literal 5 and 10 in D504, because they are counts
of sessions there and not fractions; generalising them would silently change a published
key's meaning.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np

TRADING_DAYS_PER_YEAR = 252

#: Ledger §13A.8(5) / opening §12A(5): the two thresholds of the shared-period flag.
SHARED_RHO_BAR = 0.5
SHARED_MONTH_SHARE_BAR = 0.40

#: The count of top P&L days whose overlap the docs ask for.
TOP_N_DAYS = 10


# --------------------------------------------------------------------------- input guards


def _as_usd(usd: Sequence[float] | np.ndarray, *, name: str = "usd") -> np.ndarray:
    """A 1-D float array of daily P&L in dollars, or a loud failure (D399's habit:
    guard the door and raise, never coerce a bad input into a plausible number)."""
    arr = np.asarray(usd, dtype=float)
    if arr.ndim != 1:
        raise ValueError(f"{name} must be a 1-D daily P&L series, got shape {arr.shape}")
    if arr.size == 0:
        raise ValueError(f"{name} is empty; there is no episode to check")
    if not np.all(np.isfinite(arr)):
        bad = int(np.count_nonzero(~np.isfinite(arr)))
        raise ValueError(f"{name} holds {bad} non-finite value(s); a P&L series must be finite")
    return arr


def _as_dates(dates: Sequence[Any] | np.ndarray, n: int, *, name: str = "dates") -> np.ndarray:
    """Dates normalised to `YYYY-MM-DD` strings, one per session, STRICTLY INCREASING.

    Strictly increasing, not merely sorted: two rows on one date are two books or a
    double-count, and either way the caller means something this module cannot see.
    The calendar-year and calendar-month groupings below are string slices of these
    values, so an unsorted input would silently mis-group rather than fail.
    """
    arr = np.asarray([str(d)[:10] for d in np.asarray(dates).ravel()], dtype="<U10")
    if arr.size != n:
        raise ValueError(f"{name} has {arr.size} entries for {n} P&L values")
    for value in arr:
        if len(value) != 10 or value[4] != "-" or value[7] != "-":
            raise ValueError(f"{name} holds {value!r}; expected an ISO date YYYY-MM-DD")
    if arr.size > 1 and not np.all(arr[1:] > arr[:-1]):
        first = int(np.argmax(~(arr[1:] > arr[:-1])))
        raise ValueError(
            f"{name} is not strictly increasing at index {first + 1}: "
            f"{arr[first]!r} then {arr[first + 1]!r}"
        )
    return arr


# --------------------------------------------------------------------------- the statistic


def sharpe_daily_usd(usd: Sequence[float] | np.ndarray) -> float:
    """Annualised Sharpe of a daily dollar P&L series: `mean / std(ddof=1) * sqrt(252)`.

    Dimensionless. Bit-for-bit `scripts/run_d466_components.py:sharpe` — the same
    `ddof=1`, the same `math.sqrt(252)`, the same `nan` when the standard deviation is
    not positive, and the same inclusion of flat days. It is annualised, which is a
    reporting unit and NOT the per-period unit the DSR contract of D98 requires; do not
    feed this number to `programme_dsr`.
    """
    x = np.asarray(usd, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(TRADING_DAYS_PER_YEAR)) if s > 0 else float("nan")


def sessions_to_half_pnl(usd: Sequence[float] | np.ndarray) -> int:
    """How many of the best sessions it takes to reach half the total P&L.

    Ported from `d504_arm_full_history.py:348-354`: sessions are taken in descending
    P&L order and counted until the running sum reaches `0.5 * total`. Raises if the
    total is not strictly positive — on a losing or flat book "half the P&L" names no
    session count, and D504's loop would return 1 for any negative total, which reads as
    extreme concentration when it is the arithmetic of a negative threshold.
    """
    x = _as_usd(usd)
    total = float(x.sum())
    if not total > 0.0:
        raise ValueError(
            f"sessions_to_half_pnl needs a positive total P&L, got {total:.6f}; "
            "on a non-positive total the statistic is undefined (the running sum "
            "clears a negative threshold at the first session)"
        )
    order = np.argsort(-x)
    run = 0.0
    for j, i in enumerate(order, 1):
        run += x[i]
        if run >= 0.5 * total:
            return int(j)
    raise AssertionError("running sum never reached half the total; unreachable")


# --------------------------------------------------------------------------- D504's block


def symmetric_trim(usd: Sequence[float] | np.ndarray, frac: float = 0.01) -> dict[str, Any]:
    """D504's `concentration_usable` block, key for key, on a daily dollar P&L series.

    Returns exactly the ten keys published in
    `data/d504_arm_full_history.json::concentration_usable`:

        sessions_to_half_pnl   sessions, taken best-first, to reach half the total
        top1 / top5 / top10    share of total P&L in the best 1 / 5 / 10 sessions
        top1pct                share in the best k sessions, k = max(1, int(n*frac))
        bottom1pct             share in the WORST k sessions — the symmetric counterpart
        pnl_ex_both_1pct_usd   dollars left after cutting k sessions from BOTH tails
        share_ex_both_1pct     that, over the total
        pnl_ex_both_top10_usd  dollars left after cutting 10 sessions from both tails
        n_trimmed_each_side    k

    `top5`, `top10` and `pnl_ex_both_top10_usd` keep D504's literal 5 and 10; only the
    `*1pct*` keys move with `frac`. CLAUDE.md §2: the one-sided share is the statistic
    that "always frightens" on a two-sided book, so the symmetric pair is computed in the
    same call and neither can be quoted without the other.

    Raises below 21 sessions: `pnl_ex_both_top10_usd` cuts ten from each end, and on a
    shorter series D504's slice returns an empty array whose sum is a silent 0.0.

    ONE DOCUMENTED DIVERGENCE FROM D504, and it is the only one. On a series whose total
    is NEGATIVE, D504's loop returns `sessions_to_half_pnl = 1` — the running sum clears a
    negative threshold at the first session — which reads as total concentration when it
    is the arithmetic of the sign. This returns `None` there instead. D504 itself ran on a
    total of +$25,697, so the published block is unaffected; the golden test exercises
    both signs and pins the agreement and the divergence separately.
    """
    x = _as_usd(usd)
    n = x.size
    if n < 2 * TOP_N_DAYS + 1:
        raise ValueError(
            f"symmetric_trim needs at least {2 * TOP_N_DAYS + 1} sessions to cut "
            f"{TOP_N_DAYS} from each tail, got {n}"
        )
    if not 0.0 < frac < 0.5:
        raise ValueError(f"frac must lie in (0, 0.5), got {frac}")
    total = float(x.sum())
    if total == 0.0:
        raise ValueError("total P&L is exactly zero; every share below would divide by it")
    srt = np.sort(x)
    k1 = max(1, int(n * frac))
    if 2 * k1 >= n:
        raise ValueError(f"trimming {k1} from each side of {n} sessions leaves nothing")
    return {
        "sessions_to_half_pnl": sessions_to_half_pnl(x) if total > 0.0 else None,
        "top1": float(srt[-1:].sum() / total),
        "top5": float(srt[-5:].sum() / total),
        "top10": float(srt[-TOP_N_DAYS:].sum() / total),
        "top1pct": float(srt[-k1:].sum() / total),
        "bottom1pct": float(srt[:k1].sum() / total),
        "pnl_ex_both_1pct_usd": float(srt[k1:-k1].sum()),
        "share_ex_both_1pct": float(srt[k1:-k1].sum() / total),
        "pnl_ex_both_top10_usd": float(srt[TOP_N_DAYS:-TOP_N_DAYS].sum()),
        "n_trimmed_each_side": int(k1),
    }


# --------------------------------------------------------------------------- control 5


def drop_best_year(
    usd: Sequence[float] | np.ndarray, dates: Sequence[Any] | np.ndarray
) -> dict[str, Any]:
    """Remove the best CALENDAR year and report what is left (ledger §13A.8(5)).

    The best year is the calendar year with the largest total dollar P&L — not the
    largest Sharpe, and not the largest mean: the control asks whether the edge survives
    losing the episode that carried it, and an episode is measured in dollars.

    Keys: `year_dropped`, `total_before`, `total_after`, `sharpe_before`, `sharpe_after`
    (dollars for the totals, annualised Sharpe of the remaining days for the rest).
    Raises on a single-year series, where "drop the best year" leaves nothing.
    """
    x = _as_usd(usd)
    d = _as_dates(dates, x.size)
    years = np.asarray([value[:4] for value in d], dtype="<U4")
    distinct = sorted(set(years.tolist()))
    if len(distinct) < 2:
        raise ValueError(
            f"drop_best_year needs at least 2 calendar years, got {distinct} - "
            "dropping the only year leaves no series to score"
        )
    totals = {year: float(x[years == year].sum()) for year in distinct}
    best = max(distinct, key=lambda year: (totals[year], year))
    keep = years != best
    if int(keep.sum()) < 2:
        raise ValueError(
            f"dropping {best} leaves {int(keep.sum())} session(s); a ddof=1 Sharpe needs "
            "at least 2"
        )
    return {
        "year_dropped": best,
        "total_before": float(x.sum()),
        "total_after": float(x[keep].sum()),
        "sharpe_before": sharpe_daily_usd(x),
        "sharpe_after": sharpe_daily_usd(x[keep]),
    }


def drop_best_days(usd: Sequence[float] | np.ndarray, frac: float = 0.01) -> dict[str, Any]:
    """Remove the best `frac` of days and report what is left (ledger §13A.8(5)).

    `n_dropped = max(1, int(n * frac))`, the same count `symmetric_trim` uses, so the
    one-sided control and the symmetric trim beside it cut the same number of sessions.
    This is deliberately the ASYMMETRIC statistic the deposit asks for; `symmetric_trim`
    is what keeps it honest, and `episode_checks` reports both.

    Keys: `n_dropped`, `frac`, `total_before`, `total_after`, `mean_before`, `mean_after`,
    `sharpe_before`, `sharpe_after`. Dollars throughout except the two Sharpes.
    """
    x = _as_usd(usd)
    n = x.size
    if not 0.0 < frac < 1.0:
        raise ValueError(f"frac must lie in (0, 1), got {frac}")
    k = max(1, int(n * frac))
    if n - k < 2:
        raise ValueError(
            f"dropping {k} of {n} days leaves {n - k}; a ddof=1 Sharpe needs at least 2"
        )
    srt = np.sort(x)
    keep = srt[: n - k]
    return {
        "n_dropped": int(k),
        "frac": float(frac),
        "total_before": float(x.sum()),
        "total_after": float(keep.sum()),
        "mean_before": float(x.mean()),
        "mean_after": float(keep.mean()),
        "sharpe_before": sharpe_daily_usd(x),
        "sharpe_after": sharpe_daily_usd(keep),
    }


# --------------------------------------------------------------------- shared-period risk


def _concentration_months(pnl_by_month: Mapping[str, float]) -> set[str]:
    """The smallest set of months, taken best-first, whose P&L reaches half the total.

    THIS IS AN OPERATIONALISATION, AND THE DOC DOES NOT GIVE ONE. §13A.8(5) says to flag
    when "more than 40% of each model's P&L comes from the same months" without saying
    which months those are. The definition chosen here is the episode definition already
    used elsewhere in this module and in D504: a model's episode months are the fewest
    months that carry half its P&L, and "the same months" is the intersection of the two
    models' episode sets. It is deterministic, it needs no tuning constant beyond the
    50% the rest of the file already uses, and it is stated rather than assumed.

    Returns an empty set when the total is not positive: a losing model has no episode
    months, and the flag is about shared WINNERS.
    """
    total = sum(pnl_by_month.values())
    if not total > 0.0:
        return set()
    chosen: set[str] = set()
    run = 0.0
    for month in sorted(pnl_by_month, key=lambda m: (-pnl_by_month[m], m)):
        chosen.add(month)
        run += pnl_by_month[month]
        if run >= 0.5 * total:
            break
    return chosen


def shared_period(
    a: Sequence[float] | np.ndarray,
    b: Sequence[float] | np.ndarray,
    dates: Sequence[Any] | np.ndarray,
) -> dict[str, Any]:
    """Shared-period dependence between two daily dollar P&L series on ONE calendar.

    Both series must already be aligned to the same dates — zero-filled onto a shared
    calendar the way `scripts/run_d466_components.py:series_on` does it, because a
    correlation between two books scored on their own active days is not a correlation
    between two books.

    Returns:
        rho                 Pearson correlation of the two daily dollar series
        top10_overlap       how many dates appear in BOTH series' 10 best P&L days
        same_month_share_a  share of a's total P&L falling in the shared episode months
        same_month_share_b  the same for b
        flag                rho > 0.5 AND both shares > 0.40 (ledger §13A.8(5))

    `flag` is the doc's "shared-period risk" trigger and nothing more: the doc's response
    to it is to size the two models as one position, which is a decision this function
    does not take. CLAUDE.md's warning applies in full — rho is a BODY statistic, and two
    books can share every drawdown at rho = 0.09 (D561), so the overlap count and the
    month shares are reported beside it and not folded into it.
    """
    xa = _as_usd(a, name="a")
    xb = _as_usd(b, name="b")
    if xa.size != xb.size:
        raise ValueError(
            f"a has {xa.size} days and b has {xb.size}; the two series must be aligned "
            "to one calendar before their dependence means anything"
        )
    d = _as_dates(dates, xa.size)
    if xa.size < TOP_N_DAYS:
        raise ValueError(f"shared_period needs at least {TOP_N_DAYS} days, got {xa.size}")
    if xa.std(ddof=1) <= 0.0 or xb.std(ddof=1) <= 0.0:
        raise ValueError("a correlation needs both series to vary; one of them is constant")

    rho = float(np.corrcoef(xa, xb)[0, 1])
    top_a = set(d[np.argsort(-xa)[:TOP_N_DAYS]].tolist())
    top_b = set(d[np.argsort(-xb)[:TOP_N_DAYS]].tolist())
    overlap = len(top_a & top_b)

    months = np.asarray([value[:7] for value in d], dtype="<U7")
    distinct = sorted(set(months.tolist()))
    by_month_a = {m: float(xa[months == m].sum()) for m in distinct}
    by_month_b = {m: float(xb[months == m].sum()) for m in distinct}
    shared = _concentration_months(by_month_a) & _concentration_months(by_month_b)

    total_a, total_b = float(xa.sum()), float(xb.sum())
    share_a = sum(by_month_a[m] for m in shared) / total_a if total_a != 0.0 else float("nan")
    share_b = sum(by_month_b[m] for m in shared) / total_b if total_b != 0.0 else float("nan")

    flag = bool(
        rho > SHARED_RHO_BAR
        and share_a > SHARED_MONTH_SHARE_BAR
        and share_b > SHARED_MONTH_SHARE_BAR
    )
    return {
        "rho": rho,
        "top10_overlap": int(overlap),
        "same_month_share_a": float(share_a),
        "same_month_share_b": float(share_b),
        "flag": flag,
    }


def episode_checks(
    usd: Sequence[float] | np.ndarray,
    dates: Sequence[Any] | np.ndarray,
    frac: float = 0.01,
) -> dict[str, Any]:
    """Control 5's episode half, assembled — REPORTED NUMBERS plus one boolean.

    Ledger §13A.8(5) and opening §12A(5): *"the edge must stay positive after removing the
    best calendar year and, separately, the best 1% of days."* This function computes both
    removals, carries the symmetric trim beside the one-sided one, and returns
    `edge_positive_after_both` — a boolean that is the doc's stated condition and NOT a
    verdict on the construction. Nothing here promotes, rejects, or scores against a
    hurdle; the caller owns the decision and the other controls.

    Keys: `n_days`, `total_usd`, `mean_usd`, `sharpe`, `drop_best_year`, `drop_best_days`,
    `symmetric_trim`, `edge_positive_after_both`. Dollars throughout except `sharpe` and
    the shares inside `symmetric_trim`.
    """
    x = _as_usd(usd)
    d = _as_dates(dates, x.size)
    year = drop_best_year(x, d)
    days = drop_best_days(x, frac=frac)
    trim = symmetric_trim(x, frac=frac)
    return {
        "n_days": int(x.size),
        "total_usd": float(x.sum()),
        "mean_usd": float(x.mean()),
        "sharpe": sharpe_daily_usd(x),
        "drop_best_year": year,
        "drop_best_days": days,
        "symmetric_trim": trim,
        "edge_positive_after_both": bool(
            year["total_after"] > 0.0 and days["total_after"] > 0.0
        ),
    }
