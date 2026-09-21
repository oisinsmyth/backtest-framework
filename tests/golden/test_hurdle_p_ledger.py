"""Golden tests for hurdle P (RULES.md R11) — D590.

The ledger of record is R11 itself, after all six amendments. Hand arithmetic in
`test_hurdle_p_ledger.hand.txt`, per CONTRIBUTING.md step 2: every constant below was
worked out there, from R11's own definitions, by a calculator that never imports this
codebase — and the working (including the Newton iterations on the two square roots) is
shown there so a reader can check the digit asserted on.

No market fixture is read. The fourteen sessions are a declared series chosen so that
every counting statistic is an exact rational: P3a is 36.0/yr on the nose, P3b is 2/3,
the P1 multiplier is 10/11, and the P5 haircut is $1,050 of $1,500.

WHAT IS NOT HERE. `p4_life` is a Monte Carlo through D386's venue mechanics and has no
hand-computable value; it is held to the published one in `tests/unit/test_hurdle_p.py`
instead.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from backtest_framework.validation.hurdle_p import (
    P3A_BAR,
    P3B_BAR,
    P5_CAP,
    expected_profit_before_breach_usd,
    hurdle_p,
    max_drawdown_life,
    p1_size,
    p2_flatten,
    p3,
    p5_recognised,
    p6,
)

EXACT = 1e-12          # rationals: nothing here needs slack
SQRT = 1e-6            # quantities carrying a hand-worked square root
ACCOUNT = 50_000.0

# The series, verbatim from the .hand.txt.
X = np.array([800.0, -1200.0, 600.0, 400.0, -300.0, 1500.0, -1050.0,
              700.0, 250.0, 900.0, -700.0, -600.0, -900.0, 1100.0])

# Hand-worked, .hand.txt "THE SERIES".
HAND_MEAN = 750.0 / 7.0
HAND_VAR = 495_600_000.0 / 637.0
HAND_SD = 882.0555414
HAND_SHARPE = 1.928268741
HAND_DOWNSIDE = 574.6236224
HAND_SORTINO = 2.959920


def test_the_series_is_the_one_the_hand_file_describes():
    """If the inputs drift, every case below is checking a different object."""
    assert X.size == 14
    assert X.sum() == 1500.0
    assert float((X * X).sum()) == 10_275_000.0
    assert X.mean() == pytest.approx(HAND_MEAN, abs=EXACT)
    assert float(X.var(ddof=1)) == pytest.approx(HAND_VAR, abs=1e-6)
    assert float(X.std(ddof=1)) == pytest.approx(HAND_SD, abs=SQRT)


# --------------------------------------------------------------- Case 1: P1


def test_case_1_p1_is_a_size_multiplier_and_a_number_never_a_verdict():
    s = p1_size(X, 2_000.0)
    assert s["max_trailing_dd_usd"] == pytest.approx(2_200.0, abs=EXACT)
    assert s["size_multiplier"] == pytest.approx(10.0 / 11.0, abs=EXACT)
    assert s["usd_per_year_at_traded_size"] == pytest.approx(27_000.0, abs=EXACT)
    assert s["post_sizing_usd_per_year"] == pytest.approx(270_000.0 / 11.0, abs=1e-9)
    # R11 restatement 2026-09-08: "P1 is never reported as PASS or FAIL."
    assert not any("pass" in k.lower() or "fail" in k.lower() for k in s)
    assert "OPEN equity" in s["basis"]


def test_case_1_the_drawdown_is_a_dollar_distance_from_a_ratcheting_peak_not_a_fraction():
    """D542. A compounded-peak reading of the same series gives a different number."""
    eq = np.cumsum(X)
    peak = np.maximum.accumulate(np.maximum(eq, 0.0))
    assert float((peak - eq).max()) == 2_200.0
    # the fractional reading D542 forbids, shown to disagree
    frac = float(((peak - eq) / np.maximum(peak, 1.0)).max())
    assert frac != pytest.approx(2_200.0, abs=1.0)


def test_case_1_a_series_that_never_draws_down_raises_rather_than_returning_a_size():
    with pytest.raises(ValueError, match="never draws down"):
        p1_size(np.array([1.0, 2.0, 3.0]), 2_000.0)


# --------------------------------------------------------------- Case 2: the walker


def test_case_2_one_death_at_bar_twelve_and_a_life_of_thirteen_sessions():
    n_deaths, life, episodes = max_drawdown_life(X, 2_000.0)
    assert (n_deaths, life) == (1, 13.0)
    assert episodes == [(0, 12, 13)]


def test_case_2_a_death_restarts_the_account_flat():
    y = np.array([-250.0, 100.0, -250.0, 100.0])
    n_deaths, life, episodes = max_drawdown_life(y, 250.0)
    assert (n_deaths, life) == (2, 1.5)
    assert episodes == [(0, 0, 1), (1, 2, 2)]


@pytest.mark.parametrize("cap", [0.0, -1.0, -2_000.0])
def test_case_2_a_non_positive_cap_is_not_a_dollar_distance_and_raises(cap):
    with pytest.raises(ValueError, match="positive dollar amount"):
        max_drawdown_life(X, cap)


# --------------------------------------------------------------- Case 3: P3


def test_case_3_p3a_is_thirty_six_breaches_a_year_and_fails_its_bar():
    g = p3(X, ACCOUNT)
    assert g["p3a_breaches"] == 2
    assert g["p3a_breaches_per_year"] == pytest.approx(36.0, abs=EXACT)
    assert g["p3a_bar"] == P3A_BAR
    assert g["p3a_pass"] is False
    assert g["p3a_recurrence_years"] == pytest.approx(7.0 / 252.0, abs=EXACT)
    assert g["p_breach_in_252"] == 1.0


def test_case_3_p3b_is_two_thirds_of_the_life_and_fails_its_bar():
    g = p3(X, ACCOUNT)
    assert g["life_dd_only_sessions"] == pytest.approx(13.0, abs=EXACT)
    assert g["deaths_dd_only"] == 1
    assert g["life_with_p3_sessions"] == pytest.approx(13.0 / 3.0, abs=EXACT)
    assert g["deaths_with_p3"] == 3
    assert g["p3b_life_cost"] == pytest.approx(2.0 / 3.0, abs=EXACT)
    assert g["p3b_bar"] == P3B_BAR
    assert g["p3b_pass"] is False


def test_case_3_p3c_is_reported_in_three_units_and_is_not_a_gate():
    g = p3(X, ACCOUNT)
    assert g["p3c_worst_day_usd"] == pytest.approx(-1_200.0, abs=EXACT)
    assert g["p3c_share_of_loss_budget"] == pytest.approx(0.6, abs=EXACT)
    assert g["p3c_in_sigma"] == pytest.approx(-1_200.0 / HAND_SD, abs=SQRT)
    assert not any(k.startswith("p3c") and k.endswith("pass") for k in g)


# --------------------------------------------------------------- Case 4: the bar fires


def test_case_4_p3a_passes_exactly_at_its_bar_and_fails_one_breach_later():
    d = np.zeros(252)
    d[10] = -1_200.0
    d[20:30] = 100.0
    at_bar = p3(d, ACCOUNT)
    assert at_bar["p3a_breaches_per_year"] == pytest.approx(1.0, abs=EXACT)
    assert at_bar["p3a_pass"] is True
    d2 = d.copy()
    d2[40] = -1_200.0
    over = p3(d2, ACCOUNT)
    assert over["p3a_breaches_per_year"] == pytest.approx(2.0, abs=EXACT)
    assert over["p3a_pass"] is False


# --------------------------------------------------------------- Case 5: P5


def test_case_5_the_haircut_is_thirty_percent_and_recognises_four_hundred_and_fifty():
    h = p5_recognised(X)
    assert P5_CAP == 0.30
    assert h["total_usd"] == pytest.approx(1_500.0, abs=EXACT)
    assert h["best_day_usd"] == pytest.approx(1_500.0, abs=EXACT)
    assert h["best_day_share"] == pytest.approx(1.0, abs=EXACT)
    assert h["haircut_usd"] == pytest.approx(1_050.0, abs=EXACT)
    assert h["recognised_usd"] == pytest.approx(450.0, abs=EXACT)
    assert h["haircut_applies"] is True


def test_case_5_p5_is_never_a_screen():
    """R11 2026-09-12: 'nothing is rejected for concentrating profit'."""
    h = hurdle_p(X, "mffu_rapid_eod_50k", ACCOUNT, run_lifecycle=False)
    assert h["P5_haircut_usd"] == pytest.approx(1_050.0, abs=EXACT)
    assert h["P5_pass"] is True


def test_case_5_a_losing_series_has_no_recognised_profit_and_no_haircut():
    h = p5_recognised(np.array([-1.0, -2.0, -3.0]))
    assert h["haircut_usd"] == 0.0
    assert h["haircut_applies"] is False
    assert h["recognised_usd"] == pytest.approx(-6.0, abs=EXACT)
    assert math.isnan(h["best_day_share"])


# --------------------------------------------------------------- Case 6: P4 + units


def test_case_6_the_brownian_barrier_in_dollars():
    profit, life = expected_profit_before_breach_usd(HAND_SHARPE, HAND_SD, ACCOUNT, 2_000.0)
    assert profit == pytest.approx(667.608, abs=1e-2)
    assert life == pytest.approx(6.23101, abs=1e-4)


def test_case_6_mu_is_the_mean_over_the_account_identically():
    """sigma_frac x Sharpe / sqrt(252) collapses to mean/account; the sd cancels."""
    mu = (HAND_SD / ACCOUNT) * HAND_SHARPE / math.sqrt(252.0)
    assert mu == pytest.approx(3.0 / 1400.0, abs=1e-9)


@pytest.mark.parametrize("sigma_usd,account,dd", [
    (0.01764111, 50_000.0, 2_000.0),      # a FRACTION where dollars belong
    (882.06, 0.0, 2_000.0),               # a zero account
    (882.06, 50_000.0, 60_000.0),         # a drawdown budget above the account
    (60_000.0, 50_000.0, 2_000.0),        # a daily sigma above the whole account
    (-1.0, 50_000.0, 2_000.0),            # a negative sigma
])
def test_case_6_the_unit_boundary_raises(sigma_usd, account, dd):
    with pytest.raises(ValueError):
        expected_profit_before_breach_usd(1.9, sigma_usd, account, dd)


# --------------------------------------------------------------- Case 7: P2, P6


def test_case_7_p2_reads_the_venues_own_flatten_time():
    assert p2_flatten(["09:35", "15:59"], "mffu_rapid_eod_50k") is True
    assert p2_flatten(["09:35", "16:10"], "mffu_rapid_eod_50k") is True
    assert p2_flatten(["09:35", "16:11"], "mffu_rapid_eod_50k") is False
    assert p2_flatten(["16:10"], "topstep_50k") is True          # 15:10 CT
    assert p2_flatten(["16:59"], "apex_50k") is True


def test_case_7_an_unverified_flatten_time_raises_rather_than_being_assumed():
    with pytest.raises(ValueError, match="UNVERIFIED"):
        p2_flatten(["15:59"], "take_profit_trader_50k")


def test_case_7_p6_is_a_venue_fact_and_two_of_four_firms_fail_it():
    assert p6("topstep_50k")["p6_pass"] is True
    assert p6("mffu_rapid_eod_50k")["p6_pass"] is True
    assert p6("apex_50k")["p6_pass"] is False
    assert p6("take_profit_trader_50k")["p6_pass"] is False
    assert "forfeiture" in p6("apex_50k")["provenance"]


# --------------------------------------------------------------- the assembled dict


def test_the_assembled_dict_carries_every_hand_worked_number():
    h = hurdle_p(X, "mffu_rapid_eod_50k", ACCOUNT, run_lifecycle=False)
    assert h["sharpe"] == pytest.approx(HAND_SHARPE, abs=SQRT)
    assert h["sortino"] == pytest.approx(HAND_SORTINO, abs=1e-5)      # R17: both, always
    assert h["daily_sigma_usd"] == pytest.approx(HAND_SD, abs=SQRT)
    assert h["P1_post_sizing_usd_per_year"] == pytest.approx(27_000.0, abs=EXACT)
    assert h["P1_size_multiplier"] == pytest.approx(10.0 / 11.0, abs=EXACT)
    assert h["P1_post_sizing_usd_per_year_sized"] == pytest.approx(270_000.0 / 11.0, abs=1e-9)
    assert h["P3a_breaches_per_year"] == pytest.approx(36.0, abs=EXACT)
    assert h["P3b_life_cost"] == pytest.approx(2.0 / 3.0, abs=EXACT)
    assert h["P3c_share_of_loss_budget"] == pytest.approx(0.6, abs=EXACT)
    assert h["P5_recognised_usd"] == pytest.approx(450.0, abs=EXACT)
    assert h["P6_pass"] is True
    # P2 is not asserted when no exit times are supplied: D503 hard-coded True, and a
    # hard-coded structural claim is exactly what R11's amendment forbids.
    assert h["P2_pass"] is None
    assert p2_flatten(["15:59"], "mffu_rapid_eod_50k") is True
