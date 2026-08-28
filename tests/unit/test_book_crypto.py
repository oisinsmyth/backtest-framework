"""Gates for D244 — the book on crypto.

The load-bearing ones are about the three overrides, because a study like this
goes wrong in exactly two ways and both are silent:

  * an override LEAKS -- `PPY` and `cost_fraction` live on shared modules, and one
    left switched on would corrupt every later equity study;
  * a single-symbol book is scored on the FULL panel, so `portfolio_log_returns`
    divides by 35 and reports BTC at 1/35 weight. That defect was in the first run
    and is the same one `subset_panel` was written for in D239.

Then: the universe was chosen by date, and what the record claims.
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
        "bc", REPO / "scripts" / "run_book_crypto.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["bc"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "book_crypto_summary.json").read_text(encoding="utf-8")
)
BOOK = (REPO / "docs" / "BOOK.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The overrides must not leak
# --------------------------------------------------------------------------


def test_the_shared_modules_are_left_on_equity_settings():
    """If PPY or the fixture pointer survived the crypto run, every later study on
    the ETF fixtures would be silently wrong."""
    assert R.L.PPY == 252
    assert R.X.PPY == 252
    assert R.U.PPY == 252
    assert R.X.RF_PER_BAR == pytest.approx(math.log1p(R.RF_ANNUAL) / 252, rel=1e-12)


def test_books_on_crypto_restores_state_even_on_failure():
    before = (R.L.PPY, R.X.PPY, R.L.FIXTURE, R.L.EVENTS)
    saved = R.L.load_panel
    try:
        R.L.load_panel = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
        with pytest.raises(RuntimeError):
            R.books_on_crypto()
    finally:
        R.L.load_panel = saved
    assert (R.L.PPY, R.X.PPY, R.L.FIXTURE, R.L.EVENTS) == before


def test_the_crypto_settings_were_actually_applied():
    assert SUMMARY["ppy"] == 365.0
    assert SUMMARY["fee_bps"] == 10.0


# --------------------------------------------------------------------------
# A single-symbol book needs its own panel
# --------------------------------------------------------------------------


def test_btc_alone_is_not_scored_at_one_thirty_fifth_weight():
    """The first run reported BTC at +1.13% CAGR because it zeroed 34 of 35 rows
    and `portfolio_log_returns` still divided by 35. BTC made roughly 48%/yr over
    this window; anything near 1% means the defect is back."""
    btc = SUMMARY["btc_only"]
    assert btc is not None
    assert btc["exposure_gross"] == pytest.approx(1.0, abs=1e-9)
    assert btc["cagr"] > 0.20, "BTC's CAGR is far too low -- the 1/N defect is back"
    assert btc["max_drawdown"] < -0.50, "BTC's drawdown is far too small"


# --------------------------------------------------------------------------
# The universe was chosen by date
# --------------------------------------------------------------------------


def test_the_universe_is_the_dated_cut_not_a_performance_cut():
    u = SUMMARY["universe"]
    assert u["first"] >= R.START
    assert 30 <= len(u["symbols"]) <= 40, "the majority-retaining cut moved"
    assert SUMMARY["n_symbols"] == len(u["symbols"])


def test_the_universe_retains_losers_but_not_the_2021_blowups():
    """D244's pre-registration claimed the universe held LUNC, USTC and FTT. IT
    DOES NOT -- all three launched after 2018, so the date cut excludes them, and
    the record carries a correction. What it DOES retain is the 2017-era alts that
    lost 90%+, which is why the equal-weighted benchmark drew down 90.9%.

    Asserted on the measured property rather than on ticker names, because the
    property is what matters: nothing screened the failures out."""
    syms = set(SUMMARY["universe"]["symbols"])
    assert not (syms & {"LUNC-USD", "USTC-USD", "FTT-USD"}), \
        "the 2021 blowups are present -- the correction in D244 is now wrong"
    assert syms & {"XEM-USD", "LSK-USD", "STEEM-USD", "SC-USD", "SNT-USD"}, \
        "the 2017-era alts that collapsed were screened out"
    assert SUMMARY["buy_and_hold"]["max_drawdown"] < -0.80, \
        "the benchmark is too benign -- losers were removed somewhere"


def test_the_panel_is_rectangular_after_cleaning():
    """`clean` drops bars per symbol, so the builder iterates to a fixed point."""
    panel, start, books, ones = R.books_on_crypto()
    assert len(set(len(r) for r in panel.closes)) == 1
    assert panel.closes.shape[0] == SUMMARY["n_symbols"]
    np.testing.assert_array_equal(books["C"], np.maximum(books["S1"], books["S2"]))
    assert np.allclose(panel.cost_fraction, R.FEE_BPS / 1e4)


# --------------------------------------------------------------------------
# What the record claims
# --------------------------------------------------------------------------


def test_s1_was_worse_than_random_timing():
    """The finding. Not merely unprofitable -- below its own rotation null."""
    n = SUMMARY["nulls"]["S1"]
    assert SUMMARY["cells"]["S1"]["excess_sharpe"] < 0.0
    assert n["percentile_of_actual"] < 50.0, "S1 was not below the null median"
    assert n["clears_X2"] is False
    assert SUMMARY["verdict"]["S1"]["clears_all"] is False


def test_costs_were_not_the_cause():
    """A negative breakeven means the arm loses with FREE trading."""
    assert SUMMARY["breakeven_bps"]["S1"] < 0.0
    # and S2 had ample headroom, so fees hid nothing there either
    assert SUMMARY["breakeven_bps"]["S2"] > 3 * SUMMARY["fee_bps"]


def test_s2_beat_the_benchmark_without_demonstrating_skill():
    v, n = SUMMARY["verdict"]["S2"], SUMMARY["nulls"]["S2"]
    assert v["clears_X1"] is True
    assert v["clears_X2"] is False
    assert 50.0 < n["percentile_of_actual"] < 95.0


def test_the_benchmark_was_a_catastrophe_as_predicted():
    """Y5, registered so a win here could not be oversold."""
    bh, btc = SUMMARY["buy_and_hold"], SUMMARY["btc_only"]
    assert bh["cagr"] < 0.0
    assert bh["max_drawdown"] < -0.80
    assert btc["cagr"] - bh["cagr"] > 0.30


def test_neither_arm_cleared_the_bootstrap():
    for k in ("S1", "S2"):
        assert SUMMARY["bootstrap"][k]["clears_X3"] is False


def test_the_correlation_travelled_to_a_new_asset_class():
    assert 0.0 < SUMMARY["rho_S1_S2"] < 0.35


def test_the_book_records_both_amendments():
    assert "S1 also failed on crypto" in BOOK
    assert "S2's generality is bounded to equities" in BOOK
    assert "29.1st" in BOOK


def test_zero_fresh_looks_were_spent():
    assert set(SUMMARY["cells"]) == {"S1", "S2", "C"}
    assert set(SUMMARY["verdict"]) == {"S1", "S2"}


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "BOOK_CRYPTO_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
