"""Unit tests for `validation/episodes.py` (D592).

The golden (`tests/golden/test_episodes_ledger.py`) pins the arithmetic against
hand-worked values and against D504's own source. This file tests the GUARDS and the
properties the golden's one fixture cannot reach: what each function refuses, what the
Sharpe is bit-for-bit, and the `int(n * frac) == n // 100` equivalence the port rests on.

No market fixture is read.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from backtest_framework.validation.episodes import (
    SHARED_MONTH_SHARE_BAR,
    SHARED_RHO_BAR,
    drop_best_days,
    drop_best_year,
    episode_checks,
    sessions_to_half_pnl,
    shared_period,
    sharpe_daily_usd,
    symmetric_trim,
)

DATES_24 = [f"{y}-{m:02d}-{d:02d}" for y in (2020, 2021) for m in range(1, 7) for d in (5, 20)]
A = [-20, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 100, 1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, -60]


# ------------------------------------------------------------------------- the Sharpe


def _d466_sharpe(x):
    """`scripts/run_d466_components.py:sharpe`, transcribed. `src` may not import
    `scripts`, so the identity is asserted against a transcription instead."""
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


@pytest.mark.parametrize("seed", [0, 1, 2, 3, 4])
def test_sharpe_is_bit_for_bit_d466s(seed):
    x = np.random.default_rng(seed).normal(3.0, 40.0, 500)
    assert sharpe_daily_usd(x) == _d466_sharpe(x)


def test_sharpe_is_nan_on_a_flat_series_rather_than_infinite():
    assert math.isnan(sharpe_daily_usd([7.0] * 30))
    assert math.isnan(sharpe_daily_usd([0.0] * 30))


def test_sharpe_counts_the_flat_days():
    """D466 scores a book on the whole calendar, zero-filled — dropping the inactive days
    would rescale the mean and the sigma by different factors."""
    active = [10.0, -5.0, 8.0, -3.0]
    padded = active + [0.0] * 4
    assert sharpe_daily_usd(padded) != sharpe_daily_usd(active)


# ----------------------------------------------------------- the trim-count equivalence


def test_int_n_frac_equals_floor_div_100_everywhere_it_could_matter():
    """The ONE generalisation in the D504 port. If this ever parts company, `symmetric_trim`
    stops being D504's block for some n and the golden's code identity would not see it."""
    mismatches = [n for n in range(1, 200_001) if max(1, int(n * 0.01)) != max(1, n // 100)]
    assert mismatches == []


def test_the_trim_count_clamps_to_one():
    got = symmetric_trim(list(range(1, 51)))  # n = 50, int(0.5) = 0
    assert got["n_trimmed_each_side"] == 1


# ------------------------------------------------------------------------- input guards


def test_usd_guards():
    with pytest.raises(ValueError, match="1-D"):
        symmetric_trim(np.zeros((5, 5)))
    with pytest.raises(ValueError, match="empty"):
        sessions_to_half_pnl([])
    with pytest.raises(ValueError, match="non-finite"):
        sessions_to_half_pnl([1.0, float("nan"), 2.0])
    with pytest.raises(ValueError, match="non-finite"):
        sessions_to_half_pnl([1.0, float("inf"), 2.0])


def test_date_guards():
    with pytest.raises(ValueError, match="strictly increasing"):
        drop_best_year(A, list(reversed(DATES_24)))
    with pytest.raises(ValueError, match="strictly increasing"):
        drop_best_year(A, DATES_24[:1] + DATES_24[:1] + DATES_24[2:])  # a repeated date
    with pytest.raises(ValueError, match="entries for"):
        drop_best_year(A, DATES_24[:-1])
    with pytest.raises(ValueError, match="ISO date"):
        drop_best_year([1.0, 2.0], ["2020/01/01", "2020/01/02"])


def test_datetime_like_dates_are_accepted():
    """Anything whose first ten characters are the ISO date: str, date, Timestamp."""
    import datetime as dt

    as_dates = [dt.date.fromisoformat(d) for d in DATES_24]
    assert drop_best_year(A, as_dates) == drop_best_year(A, DATES_24)
    as_np = np.array(DATES_24, dtype="datetime64[s]")
    assert drop_best_year(A, as_np) == drop_best_year(A, DATES_24)


def test_drop_best_year_refuses_a_single_year():
    one_year = [f"2020-{m:02d}-{d:02d}" for m in range(1, 13) for d in (5, 20)]
    with pytest.raises(ValueError, match="at least 2 calendar years"):
        drop_best_year(A, one_year)


def test_symmetric_trim_refuses_a_series_too_short_for_its_own_top10_key():
    with pytest.raises(ValueError, match="at least 21 sessions"):
        symmetric_trim([1.0] * 20)
    assert symmetric_trim([1.0] * 20 + [2.0])["n_trimmed_each_side"] == 1


def test_symmetric_trim_refuses_a_zero_total_and_a_bad_frac():
    with pytest.raises(ValueError, match="exactly zero"):
        symmetric_trim([1.0] * 12 + [-1.0] * 12)
    with pytest.raises(ValueError, match=r"frac must lie in \(0, 0.5\)"):
        symmetric_trim(list(range(1, 30)), frac=0.6)


def test_sessions_to_half_pnl_refuses_a_non_positive_total():
    with pytest.raises(ValueError, match="positive total"):
        sessions_to_half_pnl([-1.0] * 30)
    with pytest.raises(ValueError, match="positive total"):
        sessions_to_half_pnl([1.0, -1.0])


def test_drop_best_days_guards():
    with pytest.raises(ValueError, match=r"frac must lie in \(0, 1\)"):
        drop_best_days(A, frac=1.0)
    with pytest.raises(ValueError, match="needs at least 2"):
        drop_best_days([1.0, 2.0], frac=0.9)


def test_drop_best_year_refuses_to_leave_a_single_session():
    with pytest.raises(ValueError, match="needs at least 2"):
        drop_best_year([10.0, 20.0, 1.0], ["2020-01-05", "2020-01-06", "2021-01-05"])


def test_shared_period_guards():
    with pytest.raises(ValueError, match="aligned to one calendar"):
        shared_period(A, A[:10], DATES_24)
    with pytest.raises(ValueError, match="both series to vary"):
        shared_period(A, [1.0] * 24, DATES_24)
    with pytest.raises(ValueError, match="at least 10 days"):
        shared_period(A[:5], A[:5], DATES_24[:5])


# ------------------------------------------------------------------------- the content


def test_drop_best_year_picks_the_biggest_DOLLAR_year_not_the_biggest_sharpe():
    """A quiet year of small gains can out-Sharpe a loud one; the control removes the
    episode, which is measured in money."""
    dates = [f"{y}-{m:02d}-05" for y in (2020, 2021) for m in range(1, 13)]
    quiet = [1.0] * 12  # total 12, Sharpe enormous (zero variance -> nan, so nudge it)
    quiet[0] = 1.0001
    loud = [-40.0, 90.0] + [0.0] * 10  # total 50, Sharpe poor
    got = drop_best_year(quiet + loud, dates)
    assert got["year_dropped"] == "2021"
    assert got["total_after"] == pytest.approx(12.0001)


def test_drop_best_days_and_symmetric_trim_cut_the_same_count():
    for n in (24, 137, 250, 2508):
        series = list(np.random.default_rng(n).normal(5.0, 50.0, n))
        assert drop_best_days(series)["n_dropped"] == symmetric_trim(series)["n_trimmed_each_side"]


def test_shared_period_of_a_series_with_itself():
    got = shared_period(A, A, DATES_24)
    assert got["rho"] == pytest.approx(1.0)
    assert got["top10_overlap"] == 10
    assert got["same_month_share_a"] == got["same_month_share_b"]
    assert got["flag"] is True


def test_the_flag_is_the_conjunction_the_doc_writes():
    """rho > 0.5 AND both month shares > 0.40 — never two of the three."""
    assert SHARED_RHO_BAR == 0.5 and SHARED_MONTH_SHARE_BAR == 0.40
    # correlated but with disjoint episode months: a has its half in 2020-06, b in 2021-05
    dates = [f"{y}-{m:02d}-{d:02d}" for y in (2020, 2021) for m in range(1, 7) for d in (5, 20)]
    a = [1.0] * 24
    b = [1.0] * 24
    a[11] = 200.0   # 2020-06-20 carries a's half
    b[21] = 200.0   # 2021-05-20 carries b's half
    got = shared_period(a, b, dates)
    assert got["rho"] < SHARED_RHO_BAR
    assert got["flag"] is False


def test_a_losing_model_has_no_episode_months():
    dates = [f"{y}-{m:02d}-{d:02d}" for y in (2020, 2021) for m in range(1, 7) for d in (5, 20)]
    losing = [-v for v in A]
    got = shared_period(A, losing, dates)
    assert got["same_month_share_a"] == 0.0 and got["same_month_share_b"] == 0.0
    assert got["flag"] is False


def test_episode_checks_carries_the_symmetric_trim_beside_the_one_sided_drop():
    """CLAUDE.md §2: the one-sided trim always frightens on a two-sided book, so the
    symmetric one travels with it and neither can be quoted alone."""
    got = episode_checks(A, DATES_24)
    assert got["drop_best_days"]["n_dropped"] == got["symmetric_trim"]["n_trimmed_each_side"]
    assert got["symmetric_trim"]["bottom1pct"] < 0.0
    assert isinstance(got["edge_positive_after_both"], bool)


def test_episode_checks_totals_agree_with_their_parts():
    got = episode_checks(A, DATES_24)
    assert got["n_days"] == 24
    assert got["total_usd"] == got["drop_best_year"]["total_before"]
    assert got["total_usd"] == got["drop_best_days"]["total_before"]
    assert got["mean_usd"] == got["drop_best_days"]["mean_before"]
    assert got["sharpe"] == got["drop_best_year"]["sharpe_before"]
