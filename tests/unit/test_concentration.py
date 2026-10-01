"""D729: the volatility-unit year-concentration report (informational). Each rule has a case that must fail it."""
from __future__ import annotations

import numpy as np
import pytest

from backtest_framework.validation.concentration import year_concentration


def _line(seed: int = 0, n_per_year: int = 50, years=(2019, 2020, 2021, 2022, 2023)):
    rng = np.random.default_rng(seed)
    sess, g, sc = [], [], []
    for y in years:
        for i in range(n_per_year):
            sess.append(f"{y}-{1 + i % 12:02d}-{1 + i % 28:02d}")
            s = 1.0
            sc.append(s)
            g.append(s * (0.3 + 0.1 * rng.standard_normal()))   # near-equal yearly sums, so the rule is tested, not luck
    return np.array(sess), np.array(g), np.array(sc)


def test_hand_example_reproduces_exact_shares():
    r = year_concentration(["2021-01-04", "2021-06-01", "2022-03-01"], [1.0, 1.0, 2.0], [1.0, 1.0, 4.0])
    assert r["gross"]["by_year"]["2021"]["share"] == 0.5 and r["gross"]["by_year"]["2022"]["share"] == 0.5
    assert r["vol_units"]["by_year"]["2021"]["share"] == pytest.approx(2.0 / 2.5)
    assert r["gross"]["max_share"] == 0.5 and r["label"] == "VOL-ONLY"


def test_a_scale_year_reads_scale_carried_and_a_skill_year_reads_both():
    s, g, sc = _line()
    m = np.char.startswith(s, "2022")
    g3, sc3 = g.copy(), sc.copy()
    g3[m] *= 6.0
    sc3[m] *= 6.0
    assert year_concentration(s, g3, sc3)["label"] == "SCALE-CARRIED"
    assert year_concentration(s, g3, sc)["label"] == "BOTH"


def test_vol_unit_shares_are_invariant_to_a_years_common_factor():
    s, g, sc = _line(1)
    m = np.char.startswith(s, "2020")
    base = year_concentration(s, g, sc)["vol_units"]["by_year"]
    g2, sc2 = g.copy(), sc.copy()
    g2[m] *= 7.3
    sc2[m] *= 7.3
    moved = year_concentration(s, g2, sc2)["vol_units"]["by_year"]
    for y in base:
        assert moved[y]["share"] == pytest.approx(base[y]["share"], rel=1e-12)
    assert year_concentration(s, g2, sc2)["gross"]["by_year"]["2020"]["share"] != pytest.approx(
        year_concentration(s, g, sc)["gross"]["by_year"]["2020"]["share"])


def test_a_non_positive_total_is_undefined_not_a_share():
    r = year_concentration(["2021-01-04", "2022-01-04"], [1.0, -3.0], [1.0, 1.0])
    assert r["label"] == "UNDEFINED" and r["gross"]["max_share"] is None
    assert r["gross"]["by_year"]["2021"]["share"] is None


def test_without_a_scale_the_label_is_on_gross_alone():
    assert year_concentration(["2021-01-04", "2022-01-04"], [1.0, 3.0])["label"] == "CONCENTRATED"
    assert year_concentration(["2021-01-04", "2022-01-04"], [1.0, 1.0])["label"] == "NOT CONCENTRATED"


@pytest.mark.parametrize("scale", [[1.0, 0.0], [1.0, -1.0], [1.0, np.nan], [1.0]])
def test_a_bad_scale_raises(scale):
    with pytest.raises(ValueError):
        year_concentration(["2021-01-04", "2022-01-04"], [1.0, 1.0], scale)


@pytest.mark.parametrize("sessions,gross", [(["2021-01-04"], [1.0, 2.0]), (["20210104"], [1.0]),
                                            (["2021-01-04"], [np.inf]), ([], [])])
def test_bad_sessions_or_gross_raise(sessions, gross):
    with pytest.raises(ValueError):
        year_concentration(sessions, gross)


def test_the_cap_is_a_strict_greater_than():
    r = year_concentration(["2021-01-04", "2022-01-04"], [1.0, 1.0], [1.0, 1.0])
    assert r["gross"]["max_share"] == 0.5 and r["label"] == "NEITHER"
