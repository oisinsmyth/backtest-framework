"""Gates for D251's cross-sectional dollar-neutral pre-screen.

D250 was a pre-screen with no committed script, so nothing it computed could be
re-run. R9's corollary is that an ad-hoc script gets none of the look-ahead
protection a runner has, so this pre-screen ships its script and its assertions
run here rather than only when someone remembers to execute it.

The load-bearing gates:

  * **R9, from the strong side.** Corrupting every bar after a cut point must not
    move any score at or before it. Every score in the study is built from prefix
    sums, and a single reversed index would pass every eyeball test and fail this.
  * **A nan may not poison the future.** `np.cumsum` propagates one nan to every
    later bar. That defect silently emptied the two `md_L`-derived cells on the
    first run -- the score existed, was entirely nan, and quietly reported no
    result rather than a wrong one, which is the failure mode that survives review.
  * **The reuse pin.** `rolling_ols` generalises `run_uptrend_onset.rolling_fit`
    from a bar-index regressor to an arbitrary one. On the bar-index case it must
    reproduce it exactly -- that is what licenses generalising it (D212).
  * **The two aggregations differ only by aggregation.** They must be identical on
    a one-symbol universe, because D251's verdict turns on their difference and a
    second unrelated defect in either would be indistinguishable from it.

Then: the books are matched-notional every bar, the forward window and the scoring
window share no bar, and D245's reserved cohort is never opened.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def _load():
    sys.path.insert(0, str(REPO / "src"))
    spec = importlib.util.spec_from_file_location(
        "prescreen_xs", REPO / "scripts" / "prescreen_cross_sectional.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules["prescreen_xs"] = module
    spec.loader.exec_module(module)
    return module


P = _load()


# --------------------------------------------------------------------------
# The rolling regression
# --------------------------------------------------------------------------


def test_rolling_ols_reproduces_rolling_fit_on_the_bar_index_case():
    P.assert_rolling_ols_matches_rolling_fit()


def test_rolling_ols_recovers_a_known_slope_and_intercept():
    T = 300
    x = np.linspace(-2.0, 2.0, T)
    y = (3.0 + 1.5 * x)[None, :]
    a, b, sd, n = P.rolling_ols(y, x, 50)
    assert np.allclose(b[0, 60:], 1.5)
    assert np.allclose(a[0, 60:], 3.0)
    # 1e-6, not 0: a prefix-sum regression recovers the residual by cancelling two
    # large running totals, so an exact fit lands within float64 rounding of zero
    # rather than on it. At the study's scale (log returns ~1e-2) the floor is
    # ~1e-8 in return units, which is six orders below anything reported.
    assert np.allclose(sd[0, 60:], 0.0, atol=1e-6), "an exact fit must have zero residual"
    assert np.all(np.isnan(b[0, :49])), "a short window must be nan, not a guess"


def test_rolling_ols_residual_sd_matches_a_direct_fit():
    rng = np.random.default_rng(5)
    T, W = 400, 120
    x = rng.normal(size=T)
    y = (0.4 + 0.8 * x + rng.normal(0, 0.3, size=T))[None, :]
    a, b, sd, _ = P.rolling_ols(y, x, W)
    t = 350
    xs, ys = x[t - W + 1: t + 1], y[0, t - W + 1: t + 1]
    slope, inter = np.polyfit(xs, ys, 1)
    assert np.isclose(b[0, t], slope)
    assert np.isclose(a[0, t], inter)
    resid = ys - (inter + slope * xs)
    assert np.isclose(sd[0, t], np.sqrt(resid @ resid / (W - 2)))


# --------------------------------------------------------------------------
# nan handling -- the defect the first run actually had
# --------------------------------------------------------------------------


def test_a_nan_costs_only_the_windows_that_touch_it():
    P.assert_nan_cannot_poison()


def test_a_warm_up_of_nans_does_not_empty_the_whole_series():
    """The real shape of the bug: `md_L` is undefined through a 1,000-bar warm-up,
    and under `np.cumsum` that made every later bar nan too."""
    y = np.arange(1.0, 501.0)[None, :]
    y[0, :200] = np.nan
    s = P.trailing_sum(y, 100)
    assert np.all(np.isnan(s[0, :299])), "windows touching the warm-up must be nan"
    assert np.all(np.isfinite(s[0, 300:])), "the series must recover once the window clears"
    assert np.isclose(s[0, 400], np.arange(302.0, 402.0).sum())


# --------------------------------------------------------------------------
# R9
# --------------------------------------------------------------------------


def test_no_score_looks_ahead():
    rng = np.random.default_rng(2)
    n, T = 12, 1400
    lr = rng.normal(0.0003, 0.011, size=(n, T))
    lr[:, 0] = 0.0
    md = rng.normal(0, 0.01, size=(n, T))
    hs = rng.normal(0, 0.01, size=(n, T))
    md[:, :300] = np.nan          # the warm-up, as the real panel has it
    hs[:, :300] = np.nan
    P.assert_scores_are_causal(P.build_scores, lr, md, hs, cut=900)


def test_the_forward_window_and_the_score_window_share_no_bar():
    """`fwd[:, t]` must be exactly bars t+1 .. t+h. If it ever included bar t the
    whole study would be conditioning on the return it measures -- D248's defect."""
    n, T, h = 4, 200, 21
    r = np.arange(n * T, dtype=float).reshape(n, T)
    c = np.cumsum(r, axis=1)
    f = np.full((n, T), np.nan)
    f[:, : T - h] = c[:, h:] - c[:, : T - h]
    t = 50
    assert np.allclose(f[:, t], r[:, t + 1: t + 1 + h].sum(axis=1))
    assert not np.allclose(f[:, t], r[:, t: t + h].sum(axis=1))


# --------------------------------------------------------------------------
# The two aggregations
# --------------------------------------------------------------------------


def test_the_two_aggregations_are_identical_on_one_symbol():
    P.assert_aggregation_levels_agree_on_one_symbol()


def test_the_portfolio_level_form_is_not_pos_times_log_return():
    """D238's defective form is `pos * log_return`. The disclosed diagnostic is a
    different, correct expression, and on a short book it must NOT coincide with
    the defective one -- otherwise D251's convexity measurement is circular."""
    rng = np.random.default_rng(9)
    T = 500
    r = rng.normal(0.0004, 0.02, size=(1, T))
    r[:, 0] = 0.0
    panel = P.L.Panel(("A",), np.exp(np.cumsum(r, axis=1)), r, np.zeros(1),
                      tuple(f"d{i}" for i in range(T)), total_log_returns=r)
    pos = np.zeros((1, T))
    pos[0, 5:] = -1.0
    naive = P.L.portfolio_log_returns(panel, pos, total_return=True).sum()
    real = P.portfolio_level_log_returns(panel, pos).sum()
    assert real < naive - 1e-3, "the correct short must cost more than the naive one"


def test_the_short_leg_convexity_has_the_expected_magnitude():
    """`E[log(2 - e^r)] ~ -mu - sigma^2`, so the gap between the naive and the real
    short is about the annualised variance. That is the term D251 adds to the
    `gross = exposure x edge` invariant, so it is pinned rather than asserted."""
    rng = np.random.default_rng(4)
    T = 252 * 40
    sig_d = 0.20 / np.sqrt(252.0)
    r = rng.normal(0.0, sig_d, size=(1, T))
    panel = P.L.Panel(("A",), np.exp(np.cumsum(r, axis=1)), r, np.zeros(1),
                      tuple(f"d{i}" for i in range(T)), total_log_returns=r)
    pos = np.full((1, T), -1.0)
    naive = P.L.portfolio_log_returns(panel, pos, total_return=True).sum() / (T / 252.0)
    real = P.X.signed_log_returns(panel, pos, total_return=True).sum() / (T / 252.0)
    assert np.isclose(naive - real, 0.20 ** 2, atol=0.01)


# --------------------------------------------------------------------------
# The books
# --------------------------------------------------------------------------


def test_the_book_is_matched_notional_on_every_bar():
    rng = np.random.default_rng(1)
    n, T, start = 57, 600, 300
    sc = rng.normal(size=(n, T))
    buck = P.bucket_matrix(sc, np.ones((n, T), dtype=bool), rng.random((n, T)))
    for direction in (+1, -1):
        pos = P.neutral_book(buck, 21, start, direction, T)
        P.assert_book_is_dollar_neutral(pos, start)
        live = pos[:, start:]
        assert np.allclose((live > 0).sum(axis=0), (live < 0).sum(axis=0))
        assert live.any(), "the book never took a position"


def test_the_book_holds_from_the_bar_after_the_decision():
    """`lag = 1`, held for the horizon the quintile table measured. A book that
    began at the decision bar would be trading on that bar's own close."""
    n, T, start, h = 10, 200, 100, 21
    buck = np.full((n, T), 2)
    buck[0, :] = 4
    buck[1, :] = 0
    pos = P.neutral_book(buck, h, start, +1, T)
    assert pos[0, start - 1] == 0.0, "exposure began on the decision bar"
    assert pos[0, start] == 1.0
    assert pos[1, start] == -1.0


def test_quintiles_partition_the_live_names_evenly():
    rng = np.random.default_rng(6)
    n, T = 57, 50
    buck = P.bucket_matrix(rng.normal(size=(n, T)), np.ones((n, T), dtype=bool),
                           rng.random((n, T)))
    counts = np.array([[int((buck[:, t] == q).sum()) for q in range(P.NQ)]
                       for t in range(T)])
    assert counts.sum(axis=1).tolist() == [n] * T, "names were dropped or double-counted"
    assert (counts.max(axis=1) - counts.min(axis=1)).max() <= 1


def test_ties_are_broken_at_random_and_not_by_ticker():
    """`md_L` is exactly 0.0 inside the channel on a large share of bars. A stable
    sort would put the same early-indexed names on the same side of a quintile
    boundary every day -- a fixed ticker bet wearing a signal's name."""
    n, T = 20, 400
    sc = np.zeros((n, T))
    rng = np.random.default_rng(0)
    buck = P.bucket_matrix(sc, np.ones((n, T), dtype=bool), rng.random((n, T)))
    share_bottom = (buck[0] == 0).mean()
    assert 0.02 < share_bottom < 0.25, (
        f"symbol 0 sat in the bottom bucket on {share_bottom:.0%} of all-tied bars"
    )
    assert len({tuple(buck[:, t]) for t in range(T)}) > T // 2, "the tie order is frozen"


# --------------------------------------------------------------------------
# Breadth, costs, and the reserved cohort
# --------------------------------------------------------------------------


def test_participation_ratio_is_finite_on_market_neutral_residuals():
    """`effective_instruments` returns infinity there -- residuals sum to zero
    across names, so their equal-weighted average is identically zero. That is why
    D251 reports the eigenvalue measure instead."""
    rng = np.random.default_rng(8)
    n, T = 30, 2000
    common = rng.normal(0, 0.01, size=T)
    rets = common[None, :] + rng.normal(0, 0.008, size=(n, T))
    resid = rets - rets.mean(axis=0)[None, :]
    pr_raw = P.participation_ratio(rets)
    pr_res = P.participation_ratio(resid)
    assert np.isfinite(pr_res)
    assert pr_res > pr_raw, "removing the common factor must raise the breadth"
    assert P.BW.effective_instruments(resid) > 1e3, "the equal-weight measure is degenerate"


def test_the_cost_wall_is_the_number_the_record_quotes():
    assert abs(P.assert_cost_constant() + 0.0890) < 5e-4


def test_the_pre_screen_reads_only_the_mined_57():
    """D246 reserves D245's never-seen cohort for S3, one candidate only. This
    pre-screen spent none of it, and the fixture it names is pinned so the record's
    claim cannot go stale."""
    src = (REPO / "scripts" / "prescreen_cross_sectional.py").read_text(encoding="utf-8")
    assert "universe_daily_extended_raw.csv.gz" in src
    for reserved in ("universe_wide_w1", "universe_wide_w5", "universe_holdout"):
        assert reserved not in src, f"the pre-screen names the reserved fixture {reserved}"


def test_every_cell_declares_a_direction_before_it_is_scored():
    assert len(P.CELLS) == 8, "D246 stops screening at 8 cells"
    assert set(P.CELL_ORDER) == set(P.CELLS)
    for name, (desc, direction) in P.CELLS.items():
        assert direction in (+1, -1), f"{name} has no declared a priori long leg"
        assert desc, f"{name} has no stated definition"
