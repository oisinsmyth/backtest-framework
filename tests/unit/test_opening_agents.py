"""`backtest_framework.opening.agents` -- the opening agent-state model's agent pressures (s.4, OA-A7).

Covers the deposit's required unit tests 4-11 (`OPENING_AGENT_STATE_PREREG.md` s.15), one function each, named
`test_opening_NN_...` so the crosswalk finds them; plus the roll back-adjustment and the implied-vol round trip.
Synthetic inputs only.
"""

from __future__ import annotations

import math

import numpy as np

from backtest_framework.opening.agents import (
    a1_stop,
    a2_trend,
    a3_voltarget,
    a4_pressure,
    a5_macro,
    a5_return,
    a6_basis,
    a6_prints,
    b76_gamma,
    b76_price,
    dealer_gamma,
    fair_ratio_prior,
    implied_vol,
    large_lot_threshold,
    on_finite,
    prior_std,
    ratio_adjust,
    sigma20_prior,
    standardise,
)


def test_opening_04_a1_is_positive_above_the_prior_high_scaled_by_atr_and_zero_inside() -> None:
    p = a1_stop(np.array([105.0, 100.0, 93.0]), np.array([103.0, 103.0, 103.0]), np.array([95.0, 95.0, 95.0]),
                np.array([4.0, 4.0, 4.0]))
    assert p.tolist() == [0.5, 0.0, -0.5]


def test_opening_05_a2_target_change_matches_a_hand_calculation() -> None:
    rng = np.random.default_rng(5)
    c = 100 * np.exp(np.cumsum(rng.normal(0, 0.01, 200)))
    target, p2 = a2_trend(c)
    t = 150
    r = np.diff(np.log(c))
    sig = np.std(r[t - 21:t - 1], ddof=1)  # the 20 returns ending at close t-1
    hand = np.mean([np.sign(c[t - 1] / c[t - 1 - L] - 1) for L in (20, 60, 120)]) / sig
    assert math.isclose(target[t], hand, rel_tol=1e-12)
    sig_prev = np.std(r[t - 22:t - 2], ddof=1)
    hand_prev = np.mean([np.sign(c[t - 2] / c[t - 2 - L] - 1) for L in (20, 60, 120)]) / sig_prev
    assert math.isclose(p2[t], hand - hand_prev, rel_tol=1e-12)
    # nothing at or after t reaches target[t]
    c2 = c.copy()
    c2[t:] *= 3.0
    assert a2_trend(c2)[0][t] == target[t]
    assert np.isnan(target[:121]).all()
    # a session with no settlement is skipped, not allowed to blank the following twenty
    holed = np.insert(c, 140, np.nan)
    tg = on_finite(a2_trend, holed)[0]
    assert np.isnan(tg[140]) and tg[151] == target[150] and np.isfinite(tg[141:]).all()


def test_opening_06_a3_exposure_is_capped_at_two_and_rising_sigma_gives_negative_pressure() -> None:
    calm = 100 * np.exp(np.cumsum(np.full(40, 1e-5) * np.resize([1, -1], 40)))  # tiny vol: 0.10/sigma above 2
    e, _ = a3_voltarget(calm)
    assert np.nanmax(e) == 2.0
    rng = np.random.default_rng(6)
    r = np.concatenate([rng.normal(0, 0.005, 60), rng.normal(0, 0.03, 40)])
    c = 100 * np.exp(np.cumsum(r))
    e, p3 = a3_voltarget(c)
    assert np.nanmean(p3[62:80]) < 0, "rising sigma lowers exposure: these funds sell"


def test_opening_07_a4_dealer_gamma_follows_the_positioning_and_zero_move_gives_zero_pressure() -> None:
    F, K, sig, tau = np.full(2, 4000.0), np.array([4000.0, 4000.0]), np.full(2, 0.2), np.full(2, 30 / 252)
    g = b76_gamma(F, K, sig, tau)[0]
    assert math.isclose(dealer_gamma(F, K, sig, tau, np.array([10.0, 0.0]), np.array([True, False])), 10 * g)
    assert math.isclose(dealer_gamma(F, K, sig, tau, np.array([0.0, 10.0]), np.array([True, False])), -10 * g)
    G = np.array([5.0, -5.0, 5.0])
    p = a4_pressure(G, np.array([101.0, 101.0, 100.0]), np.array([100.0, 100.0, 100.0]))
    assert p.tolist() == [-5.0, 5.0, 0.0], "long-gamma dealers sell a rise; zero move, zero pressure"
    # Black-76 gamma against the closed form: ATM, one year, 20% vol, F = 100 -> pdf(0.1)/(100*0.2)
    ref = math.exp(-0.5 * 0.1 * 0.1) / math.sqrt(2 * math.pi) / (100 * 0.2)
    assert math.isclose(float(b76_gamma(100.0, 100.0, 0.2, 1.0)), ref, rel_tol=1e-12)


def test_opening_08_a5_is_zero_off_release_days_and_reads_only_to_0925() -> None:
    bars = {"08:28": 100.0, "09:24": 101.0, "09:25": 150.0, "09:30": 999.0}
    assert math.isclose(a5_return(bars), 0.01)
    later = dict(bars, **{"09:25": 1.0, "09:29": 5.0, "10:00": 7.0})
    assert a5_return(later) == a5_return(bars), "nothing after the 09:24 bar's close is read"
    rng = np.random.default_rng(8)
    r = rng.normal(0, 0.002, 300)
    rel = np.zeros(300, dtype=bool)
    rel[[100, 200]] = True
    p = a5_macro(r, rel)
    assert (p[~rel] == 0).all() and np.isfinite(p[rel]).all() and (p[rel] != 0).all()


def test_opening_09_a6_fair_ratio_uses_prior_days_only_and_the_0931_print() -> None:
    x = np.arange(1.0, 41.0)
    rho = fair_ratio_prior(x)
    assert np.isnan(rho[:20]).all() and rho[20] == np.median(x[:20]) and rho[30] == np.median(x[10:30])
    y = x.copy()
    y[30] = 1e9  # day 30's own 15:59 ratio never reaches its own rho
    assert fair_ratio_prior(y)[30] == rho[30]
    h = x.copy()
    h[25] = np.nan  # a session with no ratio is skipped, not allowed to blank the next twenty
    assert fair_ratio_prior(h)[30] == np.median(np.delete(x, 25)[9:29])
    assert np.isfinite(fair_ratio_prior(h)[26:]).all()
    f, e = a6_prints({"09:29": 1.0, "09:30": 4010.0, "09:31": 3.0}, {"09:29": 2.0, "09:30": 400.0})
    assert (f, e) == (4010.0, 400.0)
    assert math.isclose(float(a6_basis(np.array([f]), np.array([e]), np.array([10.0]), np.array([4.0]))[0]),
                        -(4010.0 / 10.0 - 400.0) / 4.0)


def test_opening_10_a7_large_lot_threshold_uses_the_prior_20_sessions_only() -> None:
    sizes = [np.arange(1, 11, dtype=float) for _ in range(25)]
    th = large_lot_threshold(sizes)
    assert np.isnan(th[:20]).all() and math.isclose(th[20], np.quantile(np.arange(1, 11), 0.9))
    sizes2 = [s.copy() for s in sizes]
    sizes2[22] = np.full(10, 1e6)  # session 22's own trades never set its own threshold
    th2 = large_lot_threshold(sizes2)
    assert th2[22] == th[22] and th2[23] > th[23]


def test_opening_11_standardisation_uses_the_prior_250_sessions_only() -> None:
    rng = np.random.default_rng(11)
    p = rng.normal(0, 1, 400)
    s = prior_std(p)
    assert np.isnan(s[:60]).all() and math.isclose(s[60], np.std(p[:60], ddof=1))
    assert math.isclose(s[300], np.std(p[50:300], ddof=1))
    p2 = p.copy()
    p2[300] = 1e6
    assert prior_std(p2)[300] == s[300] and standardise(p2)[300] == p2[300] / s[300]


def test_opening_roll_adjustment_keeps_each_contracts_own_returns() -> None:
    settle = np.array([100.0, 101.0, 102.0, 99.0, 100.0])  # the front rolls on day 3 onto a lower contract
    k = np.ones(5)
    k[3] = 99.0 / 102.5  # the new contract settled 99 while the old one settled 102.5 on the roll day
    adj = ratio_adjust(settle, k)
    assert math.isclose(adj[2] / adj[1], 102.0 / 101.0) and math.isclose(adj[4] / adj[3], 100.0 / 99.0)
    assert math.isclose(adj[3] / adj[2], 102.5 / 102.0), "across the roll: the old contract's own move"
    assert adj[-1] == settle[-1]
    assert np.isnan(sigma20_prior(settle)).all()


def test_opening_implied_vol_round_trips() -> None:
    F, K, tau = np.array([4000.0, 4000.0, 4000.0]), np.array([3800.0, 4000.0, 4300.0]), np.full(3, 45 / 252)
    is_call = np.array([False, True, True])
    sig = np.array([0.25, 0.18, 0.15])
    px = b76_price(F, K, sig, tau, is_call)
    assert np.allclose(implied_vol(px, F, K, tau, is_call), sig, atol=1e-9)
