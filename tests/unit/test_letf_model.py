"""`backtest_framework.letf.model` -- the LETF close-flow model's Section 4 (Phase 3).

Covers the deposit's required unit tests 1-9 (`LETF_CLOSE_FLOW_PREREG.md` s.8), one function each, named
`test_letf_NN_...` so the crosswalk (`scripts/deposit_test_map.py`) finds them. Offline: no fixture, no network, no
strategy return; every input is synthetic or the deposit's own worked number.
"""

from __future__ import annotations

import math
from datetime import datetime

import pandas as pd
import pytest

from backtest_framework.letf.model import (
    LetfModelError,
    aggregate_flow,
    aum_prior,
    bar_label_ending_at,
    day_return,
    direction,
    equivalent_volume,
    et_to_utc,
    is_active,
    normalised_flow,
    predicted_impact,
    rebalance_flow,
    to_contracts,
    trade_days,
    trailing_sigma,
    trailing_volume,
)
from zoneinfo import ZoneInfo

UTC = ZoneInfo("UTC")


# ---------------------------------------------------------------- the rebalance flow


def test_letf_01_rebalance_flow_long_3x_up_day_buys() -> None:
    assert math.isclose(rebalance_flow(3, 1e9, 0.02), 1.2e8, rel_tol=1e-12)


def test_letf_02_rebalance_flow_inverse_3x_up_day_also_buys() -> None:
    v = rebalance_flow(-3, 1e9, 0.02)
    assert math.isclose(v, 2.4e8, rel_tol=1e-12)
    assert v > 0, "the inverse fund buys an up day: same sign as the move"


def test_letf_03_rebalance_flow_long_2x_down_day_sells() -> None:
    assert math.isclose(rebalance_flow(2, 1e9, -0.01), -2e7, rel_tol=1e-12)


def test_letf_04_zero_return_zero_flow_for_every_leverage() -> None:
    for L in (-3, -2, -1, 1, 2, 3):
        assert rebalance_flow(L, 1e9, 0.0) == 0.0


def test_rebalance_flow_has_the_sign_of_the_move_for_every_levered_fund() -> None:
    for L in (-3, -2, 2, 3):
        assert rebalance_flow(L, 5e8, 0.013) > 0 and rebalance_flow(L, 5e8, -0.013) < 0
    assert rebalance_flow(1, 5e8, 0.013) == 0.0, "an unlevered fund does not rebalance"


# ---------------------------------------------------------------- A is t-1's stored value, never t's


def test_letf_05_aum_used_on_day_t_is_the_stored_value_for_t_minus_1() -> None:
    aum = pd.Series({"2024-07-01": 100.0, "2024-07-02": 200.0, "2024-07-03": 300.0, "2024-07-05": 500.0})
    nyse = ["2024-07-01", "2024-07-02", "2024-07-03", "2024-07-05"]  # the 4th is a holiday
    assert aum_prior(aum, "2024-07-03", nyse) == 200.0
    assert aum_prior(aum, "2024-07-05", nyse) == 300.0, "t-1 is the prior NYSE day, across the holiday"
    # changing day t's stored value cannot change what day t uses
    aum2 = aum.copy()
    aum2["2024-07-03"] = 9e9
    assert aum_prior(aum2, "2024-07-03", nyse) == 200.0


def test_aum_prior_refuses_a_gap_rather_than_stepping_back() -> None:
    aum = pd.Series({"2024-07-01": 100.0, "2024-07-03": 300.0})
    with pytest.raises(LetfModelError, match="no stored AUM for 2024-07-02"):
        aum_prior(aum, "2024-07-03", ["2024-07-01", "2024-07-02", "2024-07-03"])


# ---------------------------------------------------------------- the trailing windows never read day t


def _series(n: int = 30) -> pd.Series:
    days = pd.bdate_range("2024-01-01", periods=n)
    return pd.Series([1000.0 + 13.0 * i + (i % 3) * 7.0 for i in range(n)], index=days)


def test_letf_06_trailing_volume_and_sigma_use_no_data_from_day_t_or_later() -> None:
    s = _series()
    day = s.index[25]
    v, sd = trailing_volume(s, day), trailing_sigma(s.pct_change().dropna(), day)
    assert math.isclose(v, s.iloc[5:25].mean(), rel_tol=1e-15)
    poisoned = s.copy()
    poisoned.iloc[25:] = 1e12  # day t and after
    assert trailing_volume(poisoned, day) == v
    assert trailing_sigma(poisoned.pct_change().dropna(), day) == sd
    moved = s.copy()
    moved.iloc[24] += 500.0  # day t-1 must matter: the check can fire
    assert trailing_volume(moved, day) != v


def test_trailing_windows_refuse_a_short_history() -> None:
    s = _series(15)
    with pytest.raises(LetfModelError, match="20 required"):
        trailing_volume(s, s.index[-1])


# ---------------------------------------------------------------- contract conversion


def test_letf_07_ten_million_at_nq_25000_is_20_contracts() -> None:
    assert to_contracts(1e7, "NQ", 25_000.0) == 20.0
    assert to_contracts(1e7, "ES", 5_000.0) == 40.0


# ---------------------------------------------------------------- DST


def test_letf_08_1500_et_maps_to_utc_across_both_transition_weeks() -> None:
    # 2024: DST began Sun 10 March, ended Sun 3 November
    assert et_to_utc("2024-03-08", "15:00") == datetime(2024, 3, 8, 20, 0, tzinfo=UTC)  # EST, UTC-5
    assert et_to_utc("2024-03-11", "15:00") == datetime(2024, 3, 11, 19, 0, tzinfo=UTC)  # EDT, UTC-4
    assert et_to_utc("2024-11-01", "15:00") == datetime(2024, 11, 1, 19, 0, tzinfo=UTC)  # EDT
    assert et_to_utc("2024-11-04", "15:00") == datetime(2024, 11, 4, 20, 0, tzinfo=UTC)  # EST


def test_bar_label_ending_at_is_one_minute_earlier() -> None:
    assert bar_label_ending_at("15:00") == "14:59"
    assert bar_label_ending_at("16:00") == "15:59"
    assert bar_label_ending_at("09:30") == "09:29"


# ---------------------------------------------------------------- early closes


def test_letf_09_early_close_sessions_are_excluded_from_the_trade_calendar() -> None:
    s = pd.DataFrame({"day": ["2024-11-27", "2024-11-29", "2024-12-02"],
                      "is_early_close": [False, True, False], "excluded": [False, True, False]})
    assert trade_days(s) == ["2024-11-27", "2024-12-02"]
    leaky = s.assign(excluded=[False, False, False])
    with pytest.raises(LetfModelError, match="early-close sessions not excluded"):
        trade_days(leaky)


# ---------------------------------------------------------------- the rest of section 4


def test_impact_and_activation_hand_case() -> None:
    q = normalised_flow(to_contracts(aggregate_flow({"TQQQ": 3, "SQQQ": -3}, {"TQQQ": 2e10, "SQQQ": 5e9}, 0.01),
                                     "NQ", 20_000.0), 400_000.0)
    # dH = 6 x 2e10 x 0.01 + 12 x 5e9 x 0.01 = 1.2e9 + 6e8 = 1.8e9; / (20 x 20,000) = 4,500 contracts; / 400,000
    assert math.isclose(q, 4_500 / 400_000, rel_tol=1e-12)
    impact = predicted_impact(0.012, q, 20_000.0)
    assert math.isclose(impact, 0.7 * 0.012 * math.sqrt(q) * 20_000.0, rel_tol=1e-12)
    assert is_active(impact, 3, impact / 3) and not is_active(impact, 3, impact / 3 * 1.0001)
    assert direction(1.8e9) == 1 and direction(-1.0) == -1 and direction(0.0) == 0


def test_the_guards_fire() -> None:
    with pytest.raises(LetfModelError, match="fixed at 0.7"):
        predicted_impact(0.01, 0.01, 20_000.0, Y=0.8)
    with pytest.raises(LetfModelError, match="no AUM"):
        aggregate_flow({"TQQQ": 3, "SQQQ": -3}, {"TQQQ": 1e9}, 0.01)
    with pytest.raises(LetfModelError):
        rebalance_flow(3, -1.0, 0.01)
    with pytest.raises(LetfModelError):
        day_return(0.0, 100.0)
    with pytest.raises(LetfModelError):
        normalised_flow(10.0, 0.0)
    assert equivalent_volume(1000.0, 500.0) == 1050.0
    assert math.isclose(day_return(101.0, 100.0), 0.01, rel_tol=1e-12)
