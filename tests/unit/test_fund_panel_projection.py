"""Unit tests for D620's between-filing projection — the principal's question, and its guards.

**No numbered deposit test is claimed here.** What this file defends:

  * **The split basis.** `fund_nav_daily` is fully back-adjusted for reverse splits (D619) and a
    filing states the count as published. Comparing them directly measures BOIL's seven splits
    and calls the result a projection error; before the conversion existed the measured share
    error on BOIL was **6,548x**, which is a factor and not a fit. The conversion is asserted
    against the AUM identity, which `k` must cancel out of exactly.
  * **The look-ahead.** `linear` interpolates towards an anchor that is published 40-90 days
    after the period it closes. It is measured and it must be impossible to WRITE, because a
    projected panel that quietly interpolates is a one-quarter look-ahead on every row and
    nothing downstream would show it.
  * **The point-in-time anchor.** UNG's FY2023 10-K restates 2023 share counts by a factor of
    four. `anchors` must take the FIRST publication of a period, never the latest.
  * **The flow.** Differencing a step function is zero on almost every day. The level's error
    and the creation flow's error are different questions and only the second is the deposit's.

The exactness cases are the discriminating ones: `step` is exact on a fund whose shares do not
move, `linear` is exact on a fund whose shares move linearly, and `step` is shown NOT to be exact
on the second — a case that both methods pass proves neither.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]


def _script(name: str) -> Any:
    path = REPO / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


J = _script("project_fund_panel")


# ------------------------------------------------------------------------------- split factor
def test_split_factor_counts_only_the_splits_strictly_after_a_date() -> None:
    splits = pd.Series({"2012-05-11": 0.2, "2015-05-20": 0.25, "2018-03-20": 0.2})
    got = J.split_factor(
        ["2012-05-10", "2012-05-11", "2015-05-19", "2018-03-20", "2019-01-01"], splits
    )
    # On the ex-date itself the split has already happened, so it is NOT in the factor.
    assert got[0] == pytest.approx(0.2 * 0.25 * 0.2)
    assert got[1] == pytest.approx(0.25 * 0.2)
    assert got[2] == pytest.approx(0.25 * 0.2)
    assert got[3] == pytest.approx(1.0)
    assert got[4] == pytest.approx(1.0)


def test_split_factor_is_all_ones_when_a_ticker_never_split() -> None:
    got = J.split_factor(["2020-01-01", "2021-01-01"], pd.Series(dtype=float))
    assert list(got) == [1.0, 1.0]


def test_the_split_conversion_turns_the_back_adjusted_boil_row_into_a_forty_dollar_share() -> None:
    """D619's own example, run through the conversion: `NAV 8,000,000` and `0.50005` shares."""
    splits = pd.Series(
        {"2012-05-11": 0.2, "2015-05-20": 0.25, "2018-03-20": 0.2, "2020-04-21": 0.1,
         "2023-06-23": 0.05, "2024-11-07": 0.2, "2026-05-28": 0.5}
    )
    k = J.split_factor(["2011-10-04"], splits)[0]
    assert k == pytest.approx(5.0e-6, rel=1e-12)
    assert 8_000_000.0 * k == pytest.approx(40.0, rel=1e-12)
    assert 0.50005 / k == pytest.approx(100_010.0, rel=1e-9)


def _truth_frame() -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    days = ["2012-05-10", "2012-05-11", "2012-05-14"]
    nav = np.array([100.0, 20.0, 21.0])            # back-adjusted: the pre-split row is 5x high
    # ...and the share count 5x low. The LEVEL matters: the identity's tolerance is five shares'
    # worth of NAV (D619's rounding unit), so a two-share fund cannot show a broken identity.
    shares = np.array([200.0, 1000.0, 1000.0])
    truth = pd.DataFrame(
        {"date": days, "fund": "BOIL", "nav": nav, "shares_out": shares, "aum": nav * shares}
    )
    prices = {
        "BOIL": pd.DataFrame(
            {"close": [20.0, 20.0, 21.0], "split_coefficient": [1.0, 0.2, 1.0]}, index=days
        )
    }
    return truth, prices


def test_as_published_undoes_the_adjustment_and_leaves_the_aum_identity_standing() -> None:
    truth, prices = _truth_frame()
    got = J.as_published(truth, prices)
    assert list(got["k_split"]) == [0.2, 1.0, 1.0]
    assert list(got["nav_pub"]) == [20.0, 20.0, 21.0]
    assert list(got["shares_pub"]) == [1000.0, 1000.0, 1000.0]
    assert np.allclose(got["nav_pub"] * got["shares_pub"], got["aum"])


def test_as_published_raises_when_the_conversion_breaks_the_aum_identity() -> None:
    truth, prices = _truth_frame()
    truth.loc[0, "aum"] = truth.loc[0, "aum"] * 1.5
    with pytest.raises(J.ProjectionError, match="broke D619's AUM identity"):
        J.as_published(truth, prices)


def test_premium_refuses_the_back_adjusted_nav_column() -> None:
    truth, prices = _truth_frame()
    with pytest.raises(J.ProjectionError, match="AS-PUBLISHED NAV"):
        J.premium(truth, {"BOIL": prices["BOIL"]["close"]})


def test_premium_is_zero_when_the_close_equals_the_published_nav() -> None:
    truth, prices = _truth_frame()
    pub = J.as_published(truth, prices)
    # Make the close equal the published NAV on every day.
    close = pd.Series(pub["nav_pub"].to_numpy(dtype=float), index=[str(d) for d in pub["date"]])
    got = J.premium(pub, {"BOIL": close})
    assert float(got["median_bp"].iloc[0]) == pytest.approx(0.0, abs=1e-9)


# ------------------------------------------------------------------------------------ anchors
def test_anchors_take_the_first_publication_and_report_the_restatement() -> None:
    """UNG's shape: a 10-K filed after a 1-for-4 reverse split restates the prior year."""
    frame = pd.DataFrame(
        [
            {"fund": "UNG", "period_end": "2023-12-31", "filed_date": "2024-02-29",
             "shares_out": 47821147.0, "net_assets": 973854332.0, "nav_per_share": 20.36},
            {"fund": "UNG", "period_end": "2023-12-31", "filed_date": "2023-11-08",
             "shares_out": 191284588.0, "net_assets": 973854332.0, "nav_per_share": 5.09},
        ]
    )
    table = J.anchors(frame)
    assert len(table) == 1
    assert float(table["shares_out"].iloc[0]) == 191284588.0     # as first published
    assert float(table["shares_out_latest"].iloc[0]) == 47821147.0
    assert table["filed_date"].iloc[0] == "2023-11-08"
    found = J.restatements(table)
    assert set(found["field"]) == {"shares_out", "nav_per_share"}
    shares = found[found["field"] == "shares_out"].iloc[0]
    assert float(shares["ratio"]) == pytest.approx(0.25, rel=1e-6)


def test_anchors_raise_on_a_frame_missing_the_publication_column() -> None:
    with pytest.raises(J.ProjectionError, match="missing"):
        J.anchors(pd.DataFrame({"fund": ["X"], "period_end": ["2020-01-01"]}))


def test_anchors_raise_when_nothing_carries_a_publication_date() -> None:
    frame = pd.DataFrame(
        [{"fund": "X", "period_end": "2020-01-01", "filed_date": "2020-03-01",
          "shares_out": np.nan, "net_assets": np.nan, "nav_per_share": np.nan}]
    )
    with pytest.raises(J.ProjectionError, match="no anchor carries a publication date"):
        J.anchors(frame)


# --------------------------------------------------------------------------------- exactness
@pytest.mark.parametrize(("kind", "method"), [("flat", "step"), ("linear", "linear")])
def test_the_method_is_exact_on_the_fund_it_is_the_right_model_for(kind: str, method: str) -> None:
    table, days, price, truth = J._synthetic(kind)
    est = J.project(table, days, price, method=method, clock="filed")
    inside = J._SYNTHETIC_LAST_ANCHOR + 1
    got = est["shares_out_est"].to_numpy(dtype=float)[:inside]
    assert np.max(np.abs(got - truth[:inside])) < 1e-9


def test_step_is_NOT_exact_on_a_moving_fund_so_the_case_can_discriminate() -> None:
    table, days, price, truth = J._synthetic("linear")
    est = J.project(table, days, price, method="step", clock="filed")
    inside = J._SYNTHETIC_LAST_ANCHOR + 1
    got = est["shares_out_est"].to_numpy(dtype=float)[:inside]
    assert np.max(np.abs(got - truth[:inside])) > 100.0


def test_a_date_before_the_first_anchor_gets_no_row_at_all() -> None:
    table, days, price, _ = J._synthetic("flat")
    earlier = [str(dt.date(2019, 12, 1) + dt.timedelta(days=i)) for i in range(10)]
    price = pd.concat([pd.Series(10.0, index=earlier), price])
    est = J.project(table, list(earlier) + list(days), price, method="step", clock="filed")
    assert est["date"].min() == days[0]


def test_the_filed_clock_lags_the_period_clock_by_the_filing_lag() -> None:
    days = [str(dt.date(2020, 1, 1) + dt.timedelta(days=i)) for i in range(120)]
    table = pd.DataFrame(
        {
            "fund": "TEST", "period_end": ["2020-01-01", "2020-02-01"],
            "filed_date": ["2020-01-01", "2020-03-01"],
            "shares_out": [1000.0, 2000.0], "net_assets": [10000.0, 20000.0],
            "nav_per_share": [10.0, 10.0],
        }
    )
    price = pd.Series(10.0, index=days)
    filed = J.project(table, days, price, method="step", clock="filed").set_index("date")
    period = J.project(table, days, price, method="step", clock="period").set_index("date")
    # On 2020-02-15 the quarter has closed and the filing has not arrived.
    assert float(period.loc["2020-02-15", "shares_out_est"]) == 2000.0
    assert float(filed.loc["2020-02-15", "shares_out_est"]) == 1000.0
    assert float(filed.loc["2020-03-01", "shares_out_est"]) == 2000.0


@pytest.mark.parametrize(("method", "clock"), [("spline", "filed"), ("step", "realtime")])
def test_project_raises_on_a_method_or_clock_it_does_not_have(method: str, clock: str) -> None:
    table, days, price, _ = J._synthetic("flat")
    with pytest.raises(J.ProjectionError, match="is not one of"):
        J.project(table, days, price, method=method, clock=clock)


def test_project_raises_when_no_anchor_carries_a_share_count() -> None:
    table, days, price, _ = J._synthetic("flat")
    table["shares_out"] = np.nan
    with pytest.raises(J.ProjectionError, match="no anchor with a share count"):
        J.project(table, days, price, method="step", clock="filed")


# ------------------------------------------------------------------ the look-ahead is unwritable
def test_the_hindsight_method_cannot_be_written_to_disk() -> None:
    assert "linear" in J.HINDSIGHT_METHODS
    with pytest.raises(J.ProjectionError, match="one-quarter look-ahead"):
        J.build("linear")


def test_the_written_panel_refuses_the_no_lag_clock() -> None:
    with pytest.raises(J.ProjectionError, match="Never back-fill"):
        J.build("step", clock="period")


# ----------------------------------------------------------------------------------- the flow
def test_a_step_estimate_produces_no_daily_creation_flow_at_all() -> None:
    """The measurement behind the record's answer: differencing a step function is zero on every
    day but the anchor days, so the creation series a projection yields is not a flow series."""
    truth = 1000.0 + np.cumsum(np.tile([10.0, -5.0], 50))
    est = np.repeat([1000.0, truth[50], truth[-1]], [50, 40, 10]).astype(float)
    got = J._flow_errors(est, truth)
    assert got["days_truth_moves"] == 99
    assert got["days_est_moves"] == 2
    assert got["days_both_move"] == 2


def test_the_flow_metric_is_perfect_when_the_estimate_is_the_truth() -> None:
    truth = 1000.0 + np.cumsum(np.tile([10.0, -5.0], 50))
    got = J._flow_errors(truth.copy(), truth)
    assert got["corr"] == pytest.approx(1.0)
    assert got["sign_agreement_when_both_move"] == pytest.approx(1.0)
    assert got["median_abs_error_over_median_abs_truth_move"] == pytest.approx(0.0)


def test_creation_vs_price_reads_the_sign_it_claims() -> None:
    """A synthetic fund whose shares grow exactly when NAV falls must read a negative
    correlation; the record uses this statistic to explain why a stale share count times a
    current price is worse than a stale share count times a stale NAV."""
    nav = 100.0 * np.exp(np.cumsum(np.tile([0.01, -0.01], 100)))
    shares = 1.0e6 / nav
    days = [str(dt.date(2020, 1, 1) + dt.timedelta(days=i)) for i in range(len(nav))]
    frame = pd.DataFrame({"fund": "TEST", "date": days, "nav_pub": nav, "shares_pub": shares})
    got = J.creation_vs_price(frame)
    assert float(got["pearson_dlog_shares_vs_dlog_nav"].iloc[0]) == pytest.approx(-1.0, abs=1e-9)


def test_the_selftest_reports_every_break_firing() -> None:
    assert J.selftest() == 0
