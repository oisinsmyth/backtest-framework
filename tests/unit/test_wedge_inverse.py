"""Gates for D249's inverse wedge breakout.

The load-bearing ones are the three the whole record rests on:

  * **R9.** Every level is read at `t-1` and the comparison close at `t`. D248 died
    because an analysis script conditioned on `z[t]` while the rule used `z[t-1]`,
    and a 465-point spread vanished when lagged. Here it is asserted directly and
    from both sides -- the armed mask, the centre and the ATR each have to be the
    `t-1` value or the synthetic trade lands on a different bar.
  * **No look-ahead.** A close moved from bar `t` onward may not change any
    decision at an index <= `t`.
  * **Hurdle E is asserted PER SYMBOL**, and asserted to FAIL. D249's whole T-a is
    that the proposal's "50.4 entries/symbol" counts setups rather than trades. If
    this ever silently passes, the rule or the fixture changed and the record is
    stale.

Then: the up leg is never traded, overlapping trades are suppressed, D246's
reserved cohort is untouched, every hurdle leg exists in the artifact (R6), and the
page round-trips byte for byte.
"""

from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "wedge", REPO / "scripts" / "run_wedge_inverse.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["wedge"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "wedge_inverse_summary.json").read_text(encoding="utf-8")
)


class _Panel:
    """The minimum `walk` reads: closes, and a symbol count for nothing here."""

    def __init__(self, closes):
        self.closes = closes
        self.symbols = tuple(f"S{i}" for i in range(closes.shape[0]))


def _fixture(*, T=60, start=10, atr=0.01):
    closes = np.full((1, T), 100.0)
    sig = {
        "armed": np.zeros((1, T), dtype=bool),
        "centre": np.full((1, T), math.log(100.0)),
        "atr": np.full((1, T), atr),
    }
    sig["armed"][:, start:] = True
    return _Panel(closes), sig, start


# --------------------------------------------------------------------------
# R9 -- every level is read at t-1
# --------------------------------------------------------------------------


def test_a_down_break_enters_on_the_bar_after_the_break():
    panel, sig, start = _fixture()
    panel.closes[0, 30] = 100.0 * math.exp(-0.05)      # 5 log-% < 2 x 0.01 ATR
    pos, trades, _cuts, counts = R.walk(panel, sig, start, 21, stop=False)

    assert counts["down"] == 1 and counts["up"] == 0
    assert pos[0, :31].sum() == 0.0, "exposure began at or before the break bar"
    assert pos[0, 31] == 1.0, "exposure did not begin the bar AFTER the break"
    assert trades == [(0, 31, 51, pytest.approx(0.02))]


def test_the_armed_mask_is_read_at_t_minus_one():
    """Armed at the break bar but NOT at the bar before it must not trade."""
    panel, sig, start = _fixture()
    panel.closes[0, 30] = 100.0 * math.exp(-0.05)
    sig["armed"][0, 29] = False
    pos, _t, _c, counts = R.walk(panel, sig, start, 21, stop=False)
    assert counts["down"] == 0 and pos.sum() == 0.0

    sig["armed"][0, 29] = True
    sig["armed"][0, 30] = False                        # the break bar itself
    pos, _t, _c, counts = R.walk(panel, sig, start, 21, stop=False)
    assert counts["down"] == 1 and pos[0, 31] == 1.0


def test_the_trigger_level_is_read_at_t_minus_one():
    """Move the channel on the break bar only. The trade must not notice."""
    panel, sig, start = _fixture()
    panel.closes[0, 30] = 100.0 * math.exp(-0.05)
    before, _t, _c, _n = R.walk(panel, sig, start, 21, stop=False)

    sig["centre"][0, 30] -= 5.0                        # bar t, unusable by the rule
    sig["atr"][0, 30] = 9.0
    after, _t, _c, _n = R.walk(panel, sig, start, 21, stop=False)
    np.testing.assert_array_equal(before, after)

    sig["centre"][0, 29] -= 5.0                        # bar t-1, IS usable
    moved, _t, _c, counts = R.walk(panel, sig, start, 21, stop=False)
    assert counts["down"] == 0 and moved.sum() == 0.0


def test_the_up_break_is_recorded_and_never_traded():
    panel, sig, start = _fixture()
    panel.closes[0, 30] = 100.0 * math.exp(+0.05)
    pos, trades, _c, counts = R.walk(panel, sig, start, 21, stop=False)
    assert counts["up"] == 1 and counts["down"] == 0
    assert trades == [] and pos.sum() == 0.0


def test_an_overlapping_break_is_suppressed_not_bought_twice():
    panel, sig, start = _fixture(T=80)
    panel.closes[0, 30] = 100.0 * math.exp(-0.05)
    panel.closes[0, 40] = 100.0 * math.exp(-0.05)
    sig["armed"][0, 35] = False                        # so the episode re-arms
    pos, trades, _c, counts = R.walk(panel, sig, start, 21, stop=False)
    assert counts["down"] == 2 and counts["suppressed"] == 1
    assert len(trades) == 1
    assert pos[0, 31:52].sum() == 21.0 and pos[0, 52:].sum() == 0.0


def test_the_stop_exits_the_bar_after_the_close_that_breached_it():
    """D235's convention: daily OHLC cannot tell a touch from a gap, so a level is
    breached only by the CLOSE and the exit takes effect the following bar."""
    panel, sig, start = _fixture(T=80)
    panel.closes[0, 30] = 100.0 * math.exp(-0.05)
    panel.closes[0, 35] = 100.0 * math.exp(-0.09)      # below entry - 2 x ATR
    pos, _t, cuts, _n = R.walk(panel, sig, start, 42, stop=True)
    assert pos[0, 35] == 1.0, "the breaching bar itself must still be held"
    assert pos[0, 36:].sum() == 0.0
    assert len(cuts) == 1


# --------------------------------------------------------------------------
# No look-ahead, on the real panel
# --------------------------------------------------------------------------


def test_no_look_ahead_in_the_walk(requires_panel):
    R.L.FIXTURE, R.L.EVENTS = R.FIXTURES["57"]
    requires_panel(R.L.FIXTURE)
    panel, cleaned = R.L.load_panel()
    start = max(R.M.impulse_warm_up_bars(), R.M.warm_up_bars(),
                R.M.MATCHED_MOMENTUM_LOOKBACK)
    sig = R.wedge_signals(panel, cleaned, start)
    before, _t, _c, _n = R.walk(panel, sig, start, 42, stop=True)

    t = start + 400
    bumped = type(panel)(
        symbols=panel.symbols, closes=panel.closes.copy(), log_returns=panel.log_returns,
        cost_fraction=panel.cost_fraction, dates=panel.dates,
        total_log_returns=panel.total_log_returns,
    )
    bumped.closes[:, t:] *= 0.7
    after, _t2, _c2, _n2 = R.walk(bumped, sig, start, 42, stop=True)
    np.testing.assert_array_equal(before[:, : t + 1], after[:, : t + 1])
    assert not np.array_equal(before, after), "the perturbation changed nothing at all"


def test_the_regression_window_is_causal_and_both_lines_use_it():
    """Inherited from D240 and re-asserted here, because D249 fits the line TWICE
    and a copy-paste that dropped `k` from one of them would leak silently."""
    T, k = 700, R.K
    idx = np.array([200, 300, 320], dtype=int)
    y = np.array([1.0, 1.1, 1.2])
    late = 450
    without, _ = R.U.rolling_fit(T, idx, y, k)
    with_, _ = R.U.rolling_fit(T, np.append(idx, late), np.append(y, 1.3), k)
    np.testing.assert_allclose(without[: late + k], with_[: late + k],
                               rtol=0, atol=0, equal_nan=True)
    assert without[late + k] != with_[late + k]


# --------------------------------------------------------------------------
# The artifact records what the write-up claims
# --------------------------------------------------------------------------


def test_the_declared_constants_are_what_the_record_says():
    assert (R.K, R.WINDOW, R.MIN_PIVOTS, R.ATR_WINDOW) == (3, 252, 3, 21)
    assert (R.ARM_ATR, R.TRIG_ATR, R.STOP_ATR) == (2.0, 2.0, 2.0)
    assert R.HOLDS == {"W1": 21, "W2": 42, "W3": 42}
    assert R.STOPPED == {"W1": False, "W2": False, "W3": True}
    assert SUMMARY["arm_atr"] == 2.0 and SUMMARY["trig_atr"] == 2.0
    assert SUMMARY["holds"] == {"W1": 21, "W2": 42, "W3": 42}


def test_d245s_reserved_cohort_is_untouched():
    """D246 reserves the wide-universe never-seen names for S3, one candidate only.
    This study is not S3 and must not spend them."""
    assert SUMMARY["reserved_cohort_untouched"] is True
    for name in R.RESERVED:
        assert all(name not in f.name for f, _e in R.FIXTURES.values())
        assert all(name not in e.name for _f, e in R.FIXTURES.values())
    with pytest.raises(AssertionError):
        R.FIXTURES["poisoned"] = (
            Path("data/fixtures/universe_wide_w1_raw.csv.gz"),
            Path("data/fixtures/universe_wide_w1_raw_events.json"),
        )
        try:
            R.books_on("poisoned")
        finally:
            del R.FIXTURES["poisoned"]


def test_hurdle_E_is_asserted_PER_SYMBOL_and_fails():
    """T-a. The proposal's 50.4 entries/symbol counts armed SETUPS; only the
    down-breaks are traded, not every episode triggers, and overlapping trades are
    suppressed. Asserted per symbol, not pooled."""
    for half, cap in (("screen", 57), ("validation", 60)):
        eps = SUMMARY[half]["entries_per_symbol"]
        for k in R.CELL_ORDER:
            per = eps[k]
            assert len(per) == cap, "hurdle E was not computed per symbol"
            assert min(per) < 30, f"{half}/{k}: E silently passed -- the record is stale"
            assert SUMMARY[half]["verdict"][k]["clears_E"] is False
            assert SUMMARY[half]["verdict"][k]["entries_min"] == min(per)
    assert SUMMARY["screen"]["verdict"]["W1"]["entries_min"] <= 5
    assert SUMMARY["validation"]["verdict"]["W2"]["entries_min"] <= 2


def test_every_hurdle_leg_is_present():
    """R6 -- a hurdle that names a test is not cleared until that test is run, and
    a multi-leg hurdle computes EVERY leg."""
    for half in ("screen", "validation"):
        for k in R.CELL_ORDER:
            assert {"p95", "percentile_of_actual", "money_p95",
                    "money_percentile_of_actual", "vol_ratio", "vol_p50",
                    "clears_sharpe", "clears_money", "clears_H"} <= set(
                        SUMMARY[half]["nulls"][k])
            assert {"delta_vs_bh", "clears_H", "clears_P", "clears_E",
                    "breakeven_bps", "gross_sharpe"} <= set(SUMMARY[half]["verdict"][k])
            assert {"sharpe_p05", "delta_bh_p05", "delta_bh_excludes_zero"} <= set(
                SUMMARY[half]["bootstrap"][k])
        assert {"clears_H_BEST", "floor_sharpe", "floor_money"} <= set(
            SUMMARY[half]["best_of"])
        for k in R.OVERLAY_CELLS:
            assert {"n_cut", "p95", "percentile_of_actual", "clears_H_OVL"} <= set(
                SUMMARY[half]["overlay_nulls"][k])
    for k in R.CELL_ORDER:
        q = SUMMARY["overlap"][k]
        assert {"p_s1_given_wedge", "p_wedge_given_s1", "chance_s1",
                "rho_S1", "rho_S1_ci", "clears_div_S1", "clears_div_S2"} <= set(q)
        assert {"p05", "p95", "block"} <= set(q["rho_S1_ci"])


def test_the_hurdle_needs_both_legs_and_that_is_what_caught_it():
    """W2 clears the money leg at the 99.8th percentile and fails the Sharpe leg.
    If either leg alone had been the hurdle, this study would have reported a pass."""
    n = SUMMARY["screen"]["nulls"]["W2"]
    assert n["clears_money"] is True
    assert n["clears_sharpe"] is False
    assert n["clears_H"] is False
    assert n["vol_ratio"] > 2.0, "the volatility mechanism is what the page claims"
    assert n["money_per_vol"] < n["money_per_vol_null"]


def test_the_volatility_gap_is_clustering_and_not_loudness():
    """The page's central claim, pinned. If the held bars were simply louder this
    would be an ordinary risk-premium story; they are not, and the book is crowded
    instead. A per-symbol rotation null cannot produce that crowding by
    construction, which is the limitation the record states."""
    c = SUMMARY["concurrency"]["W2"]
    assert c["loudness_ratio"] < 1.25, "the held bars are much louder than the page says"
    assert c["names_held_max"] > 1.5 * c["rot_names_held_max"]
    assert c["share_bars_crowded"] > 0.05
    assert c["rot_share_bars_crowded"] < 0.01, \
        "a per-symbol rotation produced crowding -- the control is not what is claimed"
    assert c["names_held_mean"] == pytest.approx(c["rot_names_held_mean"], rel=0.02), \
        "the rotation did not preserve exposure, so the comparison is void"


def test_concurrency_is_computed_for_every_cell():
    for k in R.CELL_ORDER:
        assert {"loudness_ratio", "names_held_max", "rot_names_held_max",
                "share_bars_crowded", "rot_share_bars_crowded",
                "clustering_ratio"} <= set(SUMMARY["concurrency"][k])


def test_the_book_did_not_move_or_rho_is_void():
    for k, v in R.BOOK_EXTENDED.items():
        assert SUMMARY["screen"]["cells"][k]["excess_sharpe"] == pytest.approx(v, abs=5e-4)


def test_the_chance_baseline_is_S1s_own_exposure():
    """The overlap number only means anything against the right baseline."""
    s1 = SUMMARY["screen"]["cells"]["S1"]["exposure_gross"]
    for k in R.CELL_ORDER:
        assert SUMMARY["overlap"][k]["chance_s1"] == pytest.approx(s1, abs=1e-9)
        assert SUMMARY["overlap"][k]["chance_wedge"] == pytest.approx(
            SUMMARY["screen"]["cells"][k]["exposure_gross"], abs=1e-9)


def test_the_verdict_the_record_reports():
    assert SUMMARY["cleared_screen"] == []
    assert SUMMARY["cleared_validation"] == []
    assert SUMMARY["screen"]["best_of"]["clears_H_BEST"] is False
    # The overlap stop did NOT fire -- this is not S1 in disguise, it is just empty.
    assert SUMMARY["max_overlap_either_direction"] < 0.50
    assert all(SUMMARY["overlap"][k]["p_s1_given_wedge"]
               > SUMMARY["overlap"][k]["chance_s1"] for k in R.CELL_ORDER)
    # T-e: every cell clears the diversification condition against S1 anyway.
    assert all(SUMMARY["overlap"][k]["clears_div_S1"] for k in R.CELL_ORDER)
    assert "CLOSED" in SUMMARY["reading"]


def test_costs_are_not_what_killed_it():
    """Breakeven well above the ~1.6 bp charged, on the screen. A study that only
    fails on friction has a different write-up."""
    for k in R.CELL_ORDER:
        assert SUMMARY["screen"]["verdict"][k]["breakeven_bps"] > 1.6
        gross = SUMMARY["screen"]["verdict"][k]["gross_sharpe"]
        net = SUMMARY["screen"]["cells"][k]["excess_sharpe"]
        assert 0.0 < gross - net < 0.05


def test_effective_sample_is_reported_beside_the_trade_count():
    """D245: breadth saturates near 2 on this universe, so a pooled trade count is
    not a sample size and the page may not quote it as one."""
    for half in ("screen", "validation"):
        assert 1.0 < SUMMARY[half]["effective_instruments"] < 3.0


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "docs" / "results" / "WEDGE_INVERSE_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
