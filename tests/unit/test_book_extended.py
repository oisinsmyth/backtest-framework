"""Gates for D243 — the book on extended history.

The load-bearing ones concern the thing that makes this test worth anything:

  * the NEW window really was never seen -- it ends before the mined fixture's
    first live bar, and it is long enough to resolve something;
  * the sub-period split is applied to SCORED RETURNS, never to the signal, so
    the pre-2018 window carries exactly the warm-up it would have had;
  * the extended fixture is the same 57 symbols, starting where it should.

Then: what the record claims. S1 failed all three hurdles on the never-seen
window and S2 cleared all three, and the amendments in BOOK.md must not drift
from the artifact.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location(
        "be", REPO / "scripts" / "run_book_extended.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["be"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


R = _load()
SUMMARY = json.loads(
    (REPO / "data" / "book_extended_summary.json").read_text(encoding="utf-8")
)
BOOK = (REPO / "docs" / "BOOK.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------
# The window really was never seen
# --------------------------------------------------------------------------


def test_the_new_window_ends_before_the_mined_fixture_began():
    """The mined fixture's first LIVE bar was 2018-12-21. Anything before that is
    data neither rule could have been fitted to."""
    assert R.TRAIN_START == "2018-12-21"
    assert SUMMARY["first_live"] < "2014-01-01"
    assert SUMMARY["period_bars"]["NEW"] >= 1_000, "too short to resolve anything"


def test_the_periods_partition_the_live_window_exactly():
    pb = SUMMARY["period_bars"]
    assert pb["NEW"] + pb["TRAIN"] + pb["FORWARD"] == pb["FULL"] == SUMMARY["live_bars"]


def test_the_extended_fixture_is_the_same_universe():
    assert SUMMARY["n_symbols"] == 57
    assert SUMMARY["first_bar"] == "2009-11-11"
    assert SUMMARY["raw_bars"] == 4_222


def test_the_split_is_applied_to_returns_not_to_the_signal(loading_a_panel):
    """A sub-period must be scored from the SAME position matrix as the full span,
    masked afterwards -- never by re-deriving the signal on a truncated series,
    which would give the early window a warm-up it never had."""
    with loading_a_panel():
        panel, start, books, ones = R.books_on(*R.FIXTURES["extended"])
    dates = np.array([d[:10] for d in panel.dates[start:]])
    full_mask = np.ones(len(dates), dtype=bool)
    a = R.sub_score(panel, books["S1"], start, full_mask)
    b = SUMMARY["by_period"]["S1"]["FULL"]
    assert a["excess_sharpe"] == pytest.approx(b["excess_sharpe"], abs=1e-9)
    assert a["bars"] == b["bars"] == len(dates)
    # and a masked window is a strict subset of the same series
    new = dates < R.TRAIN_START
    assert R.sub_score(panel, books["S1"], start, new)["bars"] == int(new.sum())


def test_the_combined_book_is_the_union_at_full_capital(loading_a_panel):
    with loading_a_panel():
        panel, start, books, _ = R.books_on(*R.FIXTURES["extended"])
    np.testing.assert_array_equal(books["C"], np.maximum(books["S1"], books["S2"]))


# --------------------------------------------------------------------------
# What the record claims
# --------------------------------------------------------------------------


def test_s1_failed_every_hurdle_on_the_never_seen_window():
    v = SUMMARY["verdict"]["S1"]
    assert v["new_sharpe"] < 0.0, "S1's excess Sharpe was not negative"
    assert v["clears_V1"] is False
    assert v["clears_V2"] is False
    assert v["clears_V3"] is False
    assert v["clears_all"] is False
    assert SUMMARY["nulls"]["S1"]["percentile_of_actual"] < 95.0


def test_s2_cleared_every_hurdle_on_the_never_seen_window():
    v = SUMMARY["verdict"]["S2"]
    assert v["clears_all"] is True
    assert v["delta_vs_bh"] > 3 * v["floor"], "the margin over the floor shrank"
    assert SUMMARY["nulls"]["S2"]["percentile_of_actual"] > 95.0


def test_d239s_mechanism_predicted_the_split():
    """S1 weakens and S2 outperforms in a continuation era, registered in advance.
    S2's ABSOLUTE Sharpe fell too, so the mechanism lives in the RELATIVE numbers."""
    p, bh = SUMMARY["by_period"], SUMMARY["by_period"]["BH"]
    s1_new = p["S1"]["NEW"]["excess_sharpe"] - bh["NEW"]["excess_sharpe"]
    s1_tr = p["S1"]["TRAIN"]["excess_sharpe"] - bh["TRAIN"]["excess_sharpe"]
    s2_new = p["S2"]["NEW"]["excess_sharpe"] - bh["NEW"]["excess_sharpe"]
    s2_tr = p["S2"]["TRAIN"]["excess_sharpe"] - bh["TRAIN"]["excess_sharpe"]
    assert s1_new < s1_tr, "S1's edge did not shrink in the continuation era"
    assert s2_new > s2_tr, "S2's edge did not grow in the continuation era"


def test_doubling_the_data_narrowed_the_intervals():
    b = SUMMARY["bootstrap"]
    assert b["S2"]["sharpe_excludes_zero"] is True
    assert b["C"]["sharpe_excludes_zero"] is True
    assert b["C"]["delta_bh_excludes_zero"] is True     # first time in the programme
    assert b["S1"]["sharpe_excludes_zero"] is False     # and S1 still does not


def test_s1s_headline_sharpe_fell_on_the_longer_sample():
    """+0.746 was a six-year number. The book must not keep quoting it alone."""
    assert SUMMARY["full"]["S1"]["excess_sharpe"] < 0.60
    assert "+0.478" in BOOK, "BOOK.md does not carry the restated figure"


def test_the_correlation_held_across_three_spans():
    assert 0.0 < SUMMARY["rho_S1_S2"] < 0.25


def test_the_money_claim_was_corrected():
    """On six-year windows the combination beat buy-and-hold on money. Over 12.8
    years it does not, and the record has to say so."""
    dep_c = SUMMARY["deployable_return"]["C"]
    assert dep_c < SUMMARY["buy_and_hold_full"]["cagr"]
    assert SUMMARY["full"]["C"]["max_drawdown"] > SUMMARY["buy_and_hold_full"]["max_drawdown"]


def test_the_book_carries_both_amendments():
    assert "S1 failed the first time-independent test" in BOOK
    assert "S2 cleared a time holdout" in BOOK
    # BOOK.md sets a typographic minus (U+2212), not an ASCII hyphen
    assert "−0.123" in BOOK, "S1's never-seen Sharpe is not recorded"
    assert "+0.396" in BOOK, "S2's never-seen delta is not recorded"


def test_zero_fresh_looks_were_spent():
    """Only the book was run. Nothing was searched, so the ledger must not move."""
    assert SUMMARY["produced"] == "D243"
    assert set(SUMMARY["verdict"]) == {"S1", "S2"}
    assert set(SUMMARY["full"]) == {"S1", "S2", "C"}


def test_every_hurdle_leg_is_present():
    """R6 -- a hurdle that names a test is not cleared until that test is run."""
    for k in ("S1", "S2"):
        assert {"clears_V1", "clears_V2", "clears_V3", "clears_all", "delta_vs_bh",
                "floor", "new_sharpe", "train_sharpe"} <= set(SUMMARY["verdict"][k])
    for k in ("S1", "S2", "C"):
        assert {"sharpe_p05", "sharpe_excludes_zero", "delta_bh_p05"} <= set(
            SUMMARY["bootstrap"][k])
    assert {"delta", "p05", "excludes_zero"} <= set(SUMMARY["bootstrap"]["C_vs_S1"])


def test_the_page_round_trips_byte_for_byte():
    on_disk = (REPO / "docs" / "results" / "BOOK_EXTENDED_RESULTS.md").read_text(encoding="utf-8")
    assert R.render(SUMMARY) == on_disk
