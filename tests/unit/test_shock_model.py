"""`backtest_framework.shock.model` -- the shock classifier's sections 4-5 (Phase 2).

Covers the deposit's required unit tests 1-13 (`SHOCK_CLASSIFIER_PREREG.md` s.9), one function each, named
`test_shock_NN_...` so the crosswalk finds them. Offline: synthetic inputs only, no fixture, no forward return.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from backtest_framework.shock.model import (
    ShockModelError,
    bar_exit,
    classify,
    confirmation,
    detect,
    eligible_session,
    et_to_utc,
    event_flag,
    in_window,
    rolling_beta_rho,
    sigma_tod,
    stress_fill,
    trade_direction,
)
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")
MINS = list(pd.date_range("2000-01-01 09:30", "2000-01-01 15:59", freq="min").strftime("%H:%M"))


def test_shock_01_sigma_tod_on_day_t_uses_only_days_t_minus_60_to_t_minus_1() -> None:
    rng = np.random.default_rng(1)
    a = pd.DataFrame(np.abs(rng.normal(0, 1e-4, (80, 5))))
    s = sigma_tod(a)
    assert s.iloc[:60].isna().all().all(), "no value before 60 prior sessions"
    assert math.isclose(s.iloc[70, 2], 1.4826 * float(np.median(a.iloc[10:70, 2])), rel_tol=1e-12)
    b = a.copy()
    b.iloc[70:] = 9.0  # day t and later
    assert sigma_tod(b).iloc[70].equals(s.iloc[70])
    c = a.copy()
    c.iloc[40:70, 2] = 9.0  # half the prior window moves the median
    assert sigma_tod(c).iloc[70, 2] != s.iloc[70, 2]


def test_shock_02_peer_beta_and_rho_on_day_t_use_only_days_t_minus_60_to_t_minus_1() -> None:
    rng = np.random.default_rng(2)
    x = rng.normal(0, 1, (80, 50))
    y = 0.5 * x + rng.normal(0, 0.5, (80, 50))
    sums = pd.DataFrame({"n": 50.0, "sx": x.sum(1), "sy": y.sum(1), "sxx": (x * x).sum(1), "syy": (y * y).sum(1),
                         "sxy": (x * y).sum(1)})
    br = rolling_beta_rho(sums)
    xx, yy = x[10:70].ravel(), y[10:70].ravel()
    beta = np.cov(xx, yy, bias=True)[0, 1] / xx.var()
    assert math.isclose(br.loc[70, "beta"], beta, rel_tol=1e-9)
    sums2 = sums.copy()
    sums2.iloc[70:] = sums2.iloc[70:] * 5  # day t and later
    assert math.isclose(rolling_beta_rho(sums2).loc[70, "beta"], beta, rel_tol=1e-12)
    assert br.iloc[:60].isna().all().all()


def _day(jumps: dict[int, float], sig: float = 1e-4) -> tuple[np.ndarray, np.ndarray]:
    p = np.full(len(MINS), 100.0)
    for i, k in sorted(jumps.items()):
        p[i:] *= 1 + k * sig
    return p, np.full(len(MINS), sig)


def test_shock_03_a_5_sigma_jump_triggers_and_a_3_sigma_jump_does_not_at_z4() -> None:
    p, s = _day({30: 5.0})
    got = detect(p, MINS, s, ("09:35", "14:55"))
    assert len(got) == 1 and got[0]["minute"] == MINS[30] and got[0]["w"] == 1 and got[0]["d"] == 1
    p, s = _day({30: 3.0})
    assert detect(p, MINS, s, ("09:35", "14:55")) == []


def test_shock_04_cooldown_ignores_a_jump_30_min_later_and_detects_one_at_61() -> None:
    p, s = _day({20: 5.0, 50: 5.0})
    assert [h["minute"] for h in detect(p, MINS, s, ("09:35", "14:55"))] == [MINS[20]]
    p, s = _day({20: 5.0, 81: 5.0})
    assert [h["minute"] for h in detect(p, MINS, s, ("09:35", "14:55"))] == [MINS[20], MINS[81]]


def test_shock_05_confirmation_is_one_for_peers_moving_exactly_their_beta() -> None:
    C, n = confirmation(0.01, [(0.5 * 0.01, 0.5, 0.8), (-0.3 * 0.01, -0.3, -0.6)])
    assert n == 2 and math.isclose(C, 1.0, rel_tol=1e-12)


def test_shock_06_a_peer_below_rho_0_3_is_excluded_and_under_two_valid_peers_is_none() -> None:
    C, n = confirmation(0.01, [(0.005, 0.5, 0.8), (0.005, 0.5, 0.29)])
    assert n == 1 and math.isnan(C)
    assert classify(C, event=False) == "NONE" and classify(C, event=True) == "NONE"


def test_shock_07_classification_truth_table_with_the_event_override() -> None:
    assert classify(0.6, False) == "INFO" and classify(0.59, False) == "NONE"
    assert classify(0.2, False) == "LIQ" and classify(0.21, False) == "NONE"
    assert classify(0.35, True) == "INFO", "event and C = 0.35 gives INFO"
    assert classify(0.1, True) == "NONE", "event and C = 0.1 gives NONE (never LIQ with an event)"
    assert classify(-0.5, False) == "LIQ"


def test_shock_08_info_follows_the_shock_and_liq_opposes_it() -> None:
    assert trade_direction("INFO", 1) == 1 and trade_direction("INFO", -1) == -1
    assert trade_direction("LIQ", 1) == -1 and trade_direction("LIQ", -1) == 1
    assert trade_direction("NONE", 1) == 0


def test_shock_09_a_bar_spanning_the_stop_and_the_target_records_the_stop() -> None:
    assert bar_exit(high=105, low=95, stop=97, target=103, direction=1) == "stop"
    assert bar_exit(high=105, low=95, stop=103, target=97, direction=-1) == "stop"
    assert bar_exit(high=104, low=99, stop=97, target=103, direction=1) == "target"
    assert bar_exit(high=102, low=99, stop=97, target=103, direction=1) is None


def test_shock_10_stress_fill_is_the_worst_close_of_t0_plus_1_to_5_for_the_direction() -> None:
    closes = [100.0, 101.5, 99.0, 100.5, 100.25]
    assert stress_fill(closes, 1) == 101.5 and stress_fill(closes, -1) == 99.0
    with pytest.raises(ShockModelError):
        stress_fill(closes, 0)


def test_shock_11_shocks_outside_the_windows_and_on_roll_days_are_excluded() -> None:
    assert in_window("NQ", "09:35") and in_window("NQ", "14:55") and not in_window("NQ", "09:34")
    assert not in_window("NQ", "14:56") and in_window("GC", "08:25") and not in_window("CL", "13:26")
    p, s = _day({2: 6.0, 330: 6.0})  # 09:32 and 15:00: both outside NQ's window
    assert detect(p, MINS, s, ("09:35", "14:55")) == []
    assert eligible_session("2024-03-12", {"2024-03-14"}, {"2024-03-12", "2024-03-14"})
    assert not eligible_session("2024-03-14", {"2024-03-14"}, {"2024-03-12", "2024-03-14"})
    assert not eligible_session("2024-03-16", set(), {"2024-03-12"})


def test_shock_12_window_boundaries_map_to_utc_in_both_transition_weeks() -> None:
    assert et_to_utc("2024-03-08", "09:35") == datetime(2024, 3, 8, 14, 35, tzinfo=UTC)  # EST
    assert et_to_utc("2024-03-11", "09:35") == datetime(2024, 3, 11, 13, 35, tzinfo=UTC)  # EDT
    assert et_to_utc("2024-11-01", "14:55") == datetime(2024, 11, 1, 18, 55, tzinfo=UTC)  # EDT
    assert et_to_utc("2024-11-04", "14:55") == datetime(2024, 11, 4, 19, 55, tzinfo=UTC)  # EST


def test_shock_13_a_shock_at_release_plus_5_is_flagged_and_at_plus_6_is_not() -> None:
    rel = [datetime(2024, 3, 12, 12, 30, tzinfo=UTC)]
    assert event_flag(rel[0] + timedelta(minutes=5), rel)
    assert not event_flag(rel[0] + timedelta(minutes=6), rel)
    assert event_flag(rel[0] - timedelta(minutes=1), rel) and not event_flag(rel[0] - timedelta(minutes=2), rel)
