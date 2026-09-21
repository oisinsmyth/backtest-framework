"""Property tests for `validation/programme.py` and `validation/episodes.py` (D592).

Conventions per D78 (derandomized hypothesis, seeding owned by the library rather than a
hand-rolled seed parameter) as amended by D537 (`derandomize=True` fixes the seed but NOT
the examples drawn, because since hypothesis 6.156.6 the constant pool is harvested from
`sys.modules` at test time — so a failure here is reproducible within a run but the
example set is not byte-stable across a full-suite run and a single-file run).
`max_examples=40` and `deadline=None` keep the file cheap enough for the default gate.

What is worth a property and what is not. The arithmetic is pinned by the golden and the
unit tests; these check the RELATIONS the deposit's controls reason with but never write
down — that α allocation is conserved, that the trial log cannot lose a row, that the
programme DSR is monotone in the trial count, that the haircut can only shrink an edge,
and that the episode statistics are invariant to the things they must be invariant to
(the order of the sessions, and a positive rescaling of the currency).
"""

from __future__ import annotations

import math
import tempfile
from pathlib import Path

import numpy as np
import pytest
from hypothesis import assume, given, settings, strategies as st

from backtest_framework.validation.episodes import (
    drop_best_days,
    drop_best_year,
    sessions_to_half_pnl,
    shared_period,
    sharpe_daily_usd,
    symmetric_trim,
)
from backtest_framework.validation.programme import (
    HAIRCUT_FRACTION,
    N_SLOTS,
    PROGRAMME_ALPHA,
    SLOT_ALPHA,
    Registry,
    TrialsCsv,
    haircut,
    programme_dsr,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)

_USD = st.floats(min_value=-5_000.0, max_value=5_000.0, allow_nan=False, allow_infinity=False)


def _dates(n: int) -> list[str]:
    """n strictly increasing ISO dates, split evenly over two calendar years and spread
    across their months, so both the year grouping and the month grouping have at least
    two sessions per bucket to work with."""
    import datetime as dt

    half = n // 2
    first = [dt.date(2019, 1, 1) + dt.timedelta(days=i) for i in range(half)]
    second = [dt.date(2020, 1, 1) + dt.timedelta(days=i) for i in range(n - half)]
    return [d.isoformat() for d in first + second]


# ------------------------------------------------------------------- the α registry


@SETTINGS
@given(st.integers(min_value=1, max_value=N_SLOTS))
def test_alpha_allocated_is_exactly_the_slot_count_times_the_slot_alpha(k):
    with tempfile.TemporaryDirectory() as tmp:
        registry = Registry(path=Path(tmp) / "r.json")
        for i in range(k):
            registry.register(f"f{i}", "DOC.md")
        assert registry.alpha_total() == pytest.approx(k * SLOT_ALPHA)
        assert registry.alpha_total() <= PROGRAMME_ALPHA
        assert len(registry.free_slots()) == N_SLOTS - k


@SETTINGS
@given(st.integers(min_value=1, max_value=N_SLOTS))
def test_slots_are_allocated_lowest_first_and_never_repeat(k):
    with tempfile.TemporaryDirectory() as tmp:
        registry = Registry(path=Path(tmp) / "r.json")
        slots = [registry.register(f"f{i}", "DOC.md").slot for i in range(k)]
        assert slots == list(range(1, k + 1))
        assert sorted({f.slot for f in registry}) == slots


@SETTINGS
@given(st.floats(min_value=0.0, max_value=1.0, allow_nan=False))
def test_promotion_check_is_a_step_function_with_the_boundary_on_the_docs_side(p):
    """The doc writes "<= 0.005", so the bar itself passes."""
    with tempfile.TemporaryDirectory() as tmp:
        registry = Registry(path=Path(tmp) / "r.json")
        registry.register("F", "DOC.md")
        assert registry.promotion_check("F", p) == (p <= SLOT_ALPHA)


# ---------------------------------------------------------------------- the trial log


@SETTINGS
@given(st.lists(st.text(min_size=1, max_size=8), min_size=1, max_size=20))
def test_a_trials_log_never_loses_a_row_and_never_gains_a_duplicate(ids):
    assume(all(name.strip() for name in ids))
    with tempfile.TemporaryDirectory() as tmp:
        log = TrialsCsv(Path(tmp) / "trials.csv")
        accepted: set[str] = set()
        for name in ids:
            if name in accepted:
                with pytest.raises(ValueError, match="already logged"):
                    log.append({"trial_id": name, "doc": "D", "family": "F"})
            else:
                log.append({"trial_id": name, "doc": "D", "family": "F"})
                accepted.add(name)
            assert log.count() == len(accepted)
        assert log.trial_ids() == accepted


@SETTINGS
@given(st.text(min_size=1, max_size=40))
def test_a_logged_value_reads_back_as_written(note):
    assume("\r" not in note and "\n" not in note)
    with tempfile.TemporaryDirectory() as tmp:
        log = TrialsCsv(Path(tmp) / "trials.csv")
        log.append({"trial_id": "t1", "doc": "D", "family": "F", "notes": note})
        assert log.rows()[0]["notes"] == note


# -------------------------------------------------------------------------- the DSR


@SETTINGS
@given(
    st.floats(min_value=0.001, max_value=0.9),
    st.integers(min_value=2, max_value=5_000),
    st.integers(min_value=0, max_value=200_000),
)
def test_the_programme_dsr_is_never_above_the_docs_and_falls_with_the_pool(sr, n_doc, extra):
    got = programme_dsr(
        sr, 2000, 0.0, 3.0, n_doc=n_doc, n_programme=n_doc + extra, var_trials=4e-4
    )
    assert 0.0 <= got["dsr_programme"] <= got["dsr_doc"] <= 1.0
    if extra == 0:
        assert got["dsr_programme"] == got["dsr_doc"]


@SETTINGS
@given(st.floats(min_value=1.0000001, max_value=50.0))
def test_any_sr_above_one_per_period_is_refused(sr):
    """The D98 gate does not depend on which annualisation produced the number."""
    with pytest.raises(ValueError, match="D98"):
        programme_dsr(sr, 2000, 0.0, 3.0, n_doc=10, n_programme=10, var_trials=4e-4)


# ------------------------------------------------------------------------ the haircut


@SETTINGS
@given(
    st.floats(min_value=0.0, max_value=1e6),
    st.floats(min_value=0.01, max_value=1.0),
)
def test_the_haircut_can_only_shrink_a_positive_edge(edge, frac):
    assert 0.0 <= haircut(edge, frac=frac) <= edge
    assert haircut(edge) == pytest.approx(HAIRCUT_FRACTION * edge)


@SETTINGS
@given(st.floats(min_value=-1e6, max_value=1e6), st.floats(min_value=-1e6, max_value=1e6))
def test_the_haircut_with_a_vault_is_the_minimum_of_the_two(edge, vault):
    assert haircut(edge, vault_estimate=vault) == min(HAIRCUT_FRACTION * edge, vault)


# ----------------------------------------------------------------------- the episodes


@SETTINGS
@given(st.lists(_USD, min_size=21, max_size=120))
def test_the_trim_is_invariant_to_the_order_of_the_sessions(usd):
    """A concentration statistic is a function of the SET of daily P&Ls, not their path.
    (`sessions_to_half_pnl` is too, since it sorts.)"""
    total = float(np.sum(usd))
    assume(abs(total) > 1e-6)
    shuffled = list(np.random.default_rng(592).permutation(usd))
    a, b = symmetric_trim(usd), symmetric_trim(shuffled)
    for key in a:
        if isinstance(a[key], float):
            assert a[key] == pytest.approx(b[key], rel=1e-12, abs=1e-9)
        else:
            assert a[key] == b[key]


@SETTINGS
@given(st.lists(_USD, min_size=21, max_size=120), st.floats(min_value=0.01, max_value=100.0))
def test_the_shares_are_invariant_to_a_positive_rescaling_of_the_currency(usd, scale):
    """Doubling the contract size cannot change a concentration SHARE; it doubles every
    dollar key. The dollar keys are checked too, so the test cannot pass vacuously."""
    total = float(np.sum(usd))
    assume(abs(total) > 1e-3)
    a = symmetric_trim(usd)
    b = symmetric_trim([v * scale for v in usd])
    for key in ("top1", "top5", "top10", "top1pct", "bottom1pct", "share_ex_both_1pct"):
        assert a[key] == pytest.approx(b[key], rel=1e-9, abs=1e-12)
    for key in ("pnl_ex_both_1pct_usd", "pnl_ex_both_top10_usd"):
        assert b[key] == pytest.approx(a[key] * scale, rel=1e-9, abs=1e-9)
    assert a["n_trimmed_each_side"] == b["n_trimmed_each_side"]


@SETTINGS
@given(st.lists(_USD, min_size=21, max_size=120))
def test_sessions_to_half_pnl_is_between_one_and_n(usd):
    assume(float(np.sum(usd)) > 1.0)
    k = sessions_to_half_pnl(usd)
    assert 1 <= k <= len(usd)


@SETTINGS
@given(st.lists(_USD, min_size=30, max_size=120), st.floats(min_value=0.005, max_value=0.4))
def test_dropping_the_best_days_removes_exactly_the_k_largest(usd, frac):
    got = drop_best_days(usd, frac=frac)
    k = max(1, int(len(usd) * frac))
    assert got["n_dropped"] == k
    dropped = float(np.sum(np.sort(np.asarray(usd, float))[-k:]))
    assert got["total_before"] - got["total_after"] == pytest.approx(dropped, rel=1e-9, abs=1e-9)
    # ON A PROFITABLE BOOK the removal can only cost, which is the control's premise. On a
    # losing one the k "best" days are the least-bad and removing them RAISES the total —
    # which is why control 5 is stated as "the edge must stay POSITIVE after", not "after
    # the removal the total is lower".
    if got["total_before"] > 0.0:
        assert got["total_after"] < got["total_before"]


@SETTINGS
@given(st.lists(_USD, min_size=40, max_size=200))
def test_dropping_the_best_year_removes_exactly_the_largest_years_pnl(usd):
    dates = _dates(len(usd))
    got = drop_best_year(usd, dates)
    years = np.asarray([d[:4] for d in dates])
    totals = {y: float(np.asarray(usd, float)[years == y].sum()) for y in set(years.tolist())}
    assert got["year_dropped"] == max(totals, key=lambda y: (totals[y], y))
    assert got["total_before"] - got["total_after"] == pytest.approx(
        totals[got["year_dropped"]], rel=1e-9, abs=1e-9
    )
    if got["total_before"] > 0.0:
        assert got["total_after"] < got["total_before"], "a positive total has a positive best year"


@SETTINGS
@given(st.lists(_USD, min_size=40, max_size=120))
def test_a_series_is_perfectly_shared_with_a_positive_multiple_of_itself(usd):
    x = np.asarray(usd, float)
    assume(x.std(ddof=1) > 1e-6)
    dates = _dates(len(usd))
    got = shared_period(x, 3.0 * x, dates)
    assert got["rho"] == pytest.approx(1.0, abs=1e-12)
    assert got["top10_overlap"] == 10
    assert got["same_month_share_a"] == pytest.approx(got["same_month_share_b"], abs=1e-12)


@SETTINGS
@given(st.lists(_USD, min_size=10, max_size=120), st.floats(min_value=0.01, max_value=100.0))
def test_the_sharpe_is_scale_invariant_and_sign_flipping(usd, scale):
    x = np.asarray(usd, float)
    assume(x.std(ddof=1) > 1e-6)
    base = sharpe_daily_usd(x)
    assert sharpe_daily_usd(x * scale) == pytest.approx(base, rel=1e-9, abs=1e-12)
    assert sharpe_daily_usd(-x) == pytest.approx(-base, rel=1e-9, abs=1e-12)
    assert abs(base) < math.sqrt(252) * math.sqrt(len(usd))
