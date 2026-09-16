"""Gates on the D221 sampling-invariance runner and its published numbers.

The two that matter most:

**The shared calendar.** If the 15m and 1h series do not cover exactly the same
UTC days, the study is comparing samples rather than sampling rates, and every
number in it is void. `census_days` drops a partial day at BOTH frequencies and
`ResampleReport.check()` raises rather than warns — these tests pin that the
runner actually relies on that rather than merely importing it.

**The control.** The result rests on D (unmatched window) correlating at ~0.50
while B (matched) correlates at ~0.95. If that separation ever collapses, the
claim "the window is the variable, not the sampling rate" has lost its evidence.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "sampling_invariance_summary.json"
PAGE = REPO / "docs" / "results" / "SAMPLING_RESULTS.md"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


S = _load("run_sampling_invariance", "run_sampling_invariance.py")


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_sampling_invariance.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return PAGE.read_text(encoding="utf-8").replace("−", "-").replace("Δ", "d").replace("ρ", "r")


# --------------------------------------------------------------------------
# 1. The shared calendar
# --------------------------------------------------------------------------


def test_every_symbol_has_exactly_four_fifteen_minute_bars_per_hourly_bar(payload):
    """The arithmetic that must hold if the D161 contract held."""
    for sym, meta in payload["calendar"].items():
        assert meta["n_15m_bars"] == meta["n_1h_bars"] * 4, sym
        assert meta["n_1h_bars"] == meta["complete_days"] * 24, sym


def test_partial_days_are_dropped_and_the_count_is_published(payload):
    """A dropped day is a fact about the provider, reported rather than patched."""
    dropped = {s: m["dropped_days"] for s, m in payload["calendar"].items()}
    assert dropped["BTCUSDT"] == 0 and dropped["ETHUSDT"] == 0
    assert dropped["BTGUSDT"] > 0, "BTG's dropout is the disclosure; it moved"


def test_ppy_is_the_365_day_calendar_carried_down_to_the_bar():
    assert S.ppy(15) == 365.0 * 96 == 35040.0
    assert S.ppy(60) == 365.0 * 24 == 8760.0


def test_every_config_scores_on_the_same_wall_clock_span(payload):
    """B and C need ~4x the burn-in of A, so without a common start the study
    would compare different samples."""
    for sym, block in payload["per_symbol"].items():
        assert block["common_start"], sym
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    for sym in payload["per_symbol"]:
        years = [
            rows[(sym, c)]["years"] for _, c in
            [(0, cfg[0]) for cfg in S.CONFIGS] if (sym, c) in rows
        ]
        assert max(years) - min(years) < 0.02, f"{sym}: spans differ"


# --------------------------------------------------------------------------
# 2. The result, and the control that carries it
# --------------------------------------------------------------------------


def test_invariance_holds_on_every_symbol(payload):
    v = payload["verdict"]
    assert v["invariance_holds"] is True
    for sym, d in v["deltas_B_minus_A"].items():
        assert abs(d) <= S.DELTA_HURDLE, f"{sym}: delta {d}"
        assert v["corrs_B_vs_A"][sym] >= S.CORR_HURDLE, sym


def test_the_matched_window_correlates_far_above_the_unmatched_one(payload):
    """THE CONTROL. Matched ~0.95, unmatched ~0.50. Without this separation the
    study has no evidence that the WINDOW rather than the BAR RATE is the variable."""
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    for sym in payload["per_symbol"]:
        matched = rows[(sym, "B_15m_x4")]["corr_with_reference_hourly"]
        unmatched = rows[(sym, "D_15m_default")]["corr_with_reference_hourly"]
        assert matched > 0.90, sym
        assert unmatched < 0.70, sym
        assert matched - unmatched > 0.30, sym


def test_round_trips_are_set_by_the_window_not_the_bar_rate(payload):
    """~225/yr at a 33-hour window on EITHER bar rate; ~950 at an 8-hour window."""
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    for sym in payload["per_symbol"]:
        a = rows[(sym, "A_1h_default")]["round_trips_per_year"]
        b = rows[(sym, "B_15m_x4")]["round_trips_per_year"]
        d = rows[(sym, "D_15m_default")]["round_trips_per_year"]
        assert abs(a - b) / a < 0.10, f"{sym}: matched configs trade differently"
        assert d > 3.0 * b, f"{sym}: the unmatched config should trade ~4x more"


def test_the_naive_x4_is_no_worse_than_the_derived_lag_match(payload):
    """M5 falsified: the Wilder-lag correction was right arithmetic and did not
    matter. If this flips, the practical 'just multiply by the ratio' rule is wrong."""
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    naive = [abs(rows[(s, "B_15m_x4")]["delta_vs_reference"]) for s in payload["per_symbol"]]
    derived = [
        abs(rows[(s, "C_15m_lag_matched")]["delta_vs_reference"])
        for s in payload["per_symbol"]
    ]
    assert float(np.mean(naive)) <= float(np.mean(derived)) + 1e-9


# --------------------------------------------------------------------------
# 3. Nothing is promoted
# --------------------------------------------------------------------------


def test_no_matched_config_is_tradeable_at_the_reference_tier(payload):
    """The pre-committed position: this study promotes nothing. Every matched
    config is negative at taker_40bp."""
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    for sym in payload["per_symbol"]:
        for cfg in ("A_1h_default", "B_15m_x4", "C_15m_lag_matched"):
            assert rows[(sym, cfg)]["net_sharpe"]["taker_40bp"] < 0.0, f"{sym}/{cfg}"


def test_the_only_positive_net_cell_is_the_least_reliable_series(payload, page):
    """BTG is positive at maker_10bp and has a 32% day dropout on a 1.4-year span.
    It is named in the page so it cannot be quoted later as the one that worked."""
    rows = {(r["symbol"], r["config"]): r for r in payload["rows"]}
    positives = [
        (s, c)
        for s in payload["per_symbol"]
        for c in ("A_1h_default", "B_15m_x4", "C_15m_lag_matched")
        if rows[(s, c)]["net_sharpe"]["maker_10bp"] > 0
    ]
    assert {s for s, _ in positives} <= {"BTGUSDT"}
    assert "no config is promoted" in page.lower()


# --------------------------------------------------------------------------
# 4. The page is the artifact
# --------------------------------------------------------------------------


def test_the_published_table_is_the_artifact(payload, page):
    for r in payload["rows"]:
        assert f"{r['gross_sharpe']:+.3f}" in page, f"{r['symbol']}/{r['config']}"


def test_the_unusable_native_fixture_is_recorded(page):
    assert "50.4%" in page and "zero-volume" in page


def test_report_only_reproduces_the_page_byte_for_byte(payload):
    before = PAGE.read_bytes()
    try:
        PAGE.write_text(S.render(payload), encoding="utf-8")
        assert PAGE.read_bytes() == before
    finally:
        PAGE.write_bytes(before)
