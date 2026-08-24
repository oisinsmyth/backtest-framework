"""Gates on the D218 runner and its published numbers.

The one that matters most is the first: **D218 must be scoring its arms with
D217's code, not its own.** D212 is this project's record of what happens when a
study restates a cost path — two paths disagreeing by a factor of two across a
whole study, with a test named for their agreement comparing one to itself. A
replication that reprices its own arms is not a replication, and identity checks
on the shared functions are what make that structural instead of promised.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

from backtest_framework.research import macd as M

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "impulse_macd_summary.json"
D217_SUMMARY = REPO / "data" / "macd_ladder_summary.json"
RESULTS = REPO / "MACD_RESULTS.md"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


I = _load("run_impulse_macd", "run_impulse_macd.py")  # noqa: E741


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_impulse_macd.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return RESULTS.read_text(encoding="utf-8").replace("−", "-")


def present(page: str, needle: str, label: str) -> None:
    assert needle in page, f"{label}: {needle!r} is not in MACD_RESULTS.md"


# --------------------------------------------------------------------------
# 1. The shared machinery — the D212 guard
# --------------------------------------------------------------------------


def test_d218_scores_its_arms_with_d217s_code_and_not_its_own():
    """Identity, not equality. If someone copies these functions into this script
    'to make it standalone', this test is what stops the copy diverging silently."""
    assert I.L.__name__ == "run_macd_ladder"
    for name in (
        "Panel",
        "load_panel",
        "per_side_bps",
        "portfolio_log_returns",
        "sharpe_of",
        "score_arm",
        "buy_and_hold",
        "rotation_null",
        "block_shuffle_null",
        "percentile_of",
        "prior_etf_trials",
    ):
        assert hasattr(I.L, name), f"D217 runner lost {name}"
    # The D218 module must NOT define its own copies of the pricing functions.
    for name in ("portfolio_log_returns", "per_side_bps", "score_arm", "buy_and_hold"):
        assert name not in vars(I), f"D218 has restated {name} — that is D212 again"


def test_the_hurdle_constant_is_shared_not_retyped():
    assert I.DELTA_HURDLE is I.L.DELTA_HURDLE
    assert I.PPY is I.L.PPY
    assert I.GATE_WINDOW is I.L.GATE_WINDOW


# --------------------------------------------------------------------------
# 2. Warm-up and spans, which differ from D217's and are disclosed
# --------------------------------------------------------------------------


def test_the_ladder_waits_a_thousand_bars_because_wilder_smoothing_does():
    assert I.ladder_start() == M.impulse_warm_up_bars() == 1000
    assert I.ladder_start() > M.warm_up_bars() == 393


def test_the_sensitivity_block_starts_later_than_the_ladder_and_says_so(payload, page):
    """`lengthMA = 55` needs its own 1,506-bar burn-in, so this block runs on a
    shorter, later span and its LEVELS are not comparable to the ladder's."""
    assert I.sensitivity_start() > I.ladder_start()
    assert payload["sensitivity_start"] == I.sensitivity_start()
    present(page, "not comparable to the ladder above", "the span disclosure")
    present(page, str(payload["sensitivity_start"]), "sensitivity start bar")


def test_every_rung_including_the_control_starts_on_the_same_bar(payload):
    assert payload["common_start"] == I.ladder_start()


# --------------------------------------------------------------------------
# 3. The replication claim
# --------------------------------------------------------------------------


def test_the_replication_reference_is_read_from_d217s_artifact_not_retyped(payload):
    """The comparison numbers come out of the committed D217 JSON. If D217 is ever
    re-run and its deltas move, this study's claim moves with them or goes red."""
    d217 = json.loads(D217_SUMMARY.read_text(encoding="utf-8"))
    ls = next(x for x in d217["deltas"] if x["book"] == "long_short" and x["gate"] == "none")
    lf = next(x for x in d217["deltas"] if x["book"] == "long_flat" and x["gate"] == "none")
    assert payload["d217_reference"]["r1_minus_r2_long_short"] == ls["signal_minus_zero"]
    assert payload["d217_reference"]["r1_minus_r2_long_flat"] == lf["signal_minus_zero"]


def test_the_replication_verdict_follows_from_the_numbers(payload):
    r = payload["replication"]
    ref = payload["d217_reference"]
    same = (r["long_short"] > 0) == (ref["r1_minus_r2_long_short"] > 0) and (
        r["long_flat"] > 0
    ) == (ref["r1_minus_r2_long_flat"] > 0)
    assert r["same_sign"] == same
    assert r["clears_hurdle"] == (
        r["long_short"] >= I.DELTA_HURDLE and r["long_flat"] >= I.DELTA_HURDLE
    )


def test_the_magnitude_caveat_is_published(payload, page):
    """A big I1-I2 delta can be manufactured by I2 being bad. The report has to say
    so, and has to give the clean read (I1 - C) beside it."""
    present(page, "manufactured two ways", "the magnitude caveat")
    ls = next(
        d for d in payload["deltas"] if d["book"] == "long_short" and d["gate"] == "none"
    )
    present(page, f"{ls['impulse_minus_control']:+.3f}", "I1 - C, the clean read")


def test_the_band_rung_is_anti_predictive_not_merely_dead(payload):
    """The finding the caveat rests on: I2 sits at the bottom of its own null."""
    band = [c for c in payload["core"] if c["rung"] == "I2_band"]
    assert len(band) == 4
    assert sum(1 for c in band if c["rotation_percentile"] <= 1.0) >= 3


# --------------------------------------------------------------------------
# 4. Hurdle D, and the published tables
# --------------------------------------------------------------------------


def test_hurdle_d_requires_both_metrics(payload):
    """D218's fix for the gap D217 had to disclose in an addendum: a long-flat cell
    only clears D if it beats buy-and-hold on Sharpe AND on total return."""
    v = payload["verdict"]
    bh_sharpe = v["buy_and_hold_sharpe"]
    bh_total = v["buy_and_hold_total_return_with_dividends"]
    for row, cell in zip(v["rows"], payload["core"]):
        if cell["book"] != "long_flat":
            continue
        expected = cell["sharpe"] > bh_sharpe and (
            cell["total_return_with_dividends"] > bh_total
        )
        assert row["D_benchmark_both_metrics"] == expected, row["cell"]


def test_at_least_one_cell_beats_the_benchmark_on_sharpe_and_fails_it_on_money(payload):
    """If this ever stops being true the two metrics have stopped disagreeing and
    naming both up front would no longer be buying anything."""
    v = payload["verdict"]
    split = [
        c
        for c in payload["core"]
        if c["book"] == "long_flat"
        and c["sharpe"] > v["buy_and_hold_sharpe"]
        and c["total_return_with_dividends"] <= v["buy_and_hold_total_return_with_dividends"]
    ]
    assert split, "no cell exhibits the Sharpe-beats/money-loses split"


def test_the_published_ladder_table_is_the_artifact(payload, page):
    for a in payload["core"]:
        present(page, f"{a['sharpe']:+.3f}", f"{a['rung']} sharpe")
        present(page, f"{a['total_return_with_dividends'] * 100:.2f}%", f"{a['rung']} total")
    for d in payload["deltas"]:
        present(page, f"{d['signal_minus_band']:+.3f}", "I1-I2")
        present(page, f"{d['band_minus_no_deadzone']:+.3f}", "I2-I3")


def test_the_dsr_floors_are_the_published_ones(payload, page):
    for name, f in payload["multiplicity"]["counts"].items():
        present(page, f"{f['n_trials']:,}", f"{name} n")
        present(page, f"{f['expected_max_sharpe_annualised']:.3f}", f"{name} SR0")


# --------------------------------------------------------------------------
# 5. The ledger, which is NOT fresh
# --------------------------------------------------------------------------


def test_d218_inherits_d217s_looks_rather_than_starting_over(payload):
    d217 = json.loads(D217_SUMMARY.read_text(encoding="utf-8"))
    assert I.INHERITED_D217_LOOKS == d217["fresh_looks"] == 42
    counts = payload["multiplicity"]["counts"]
    assert counts["fresh_d218_only"]["n_trials"] == I.FRESH_LOOKS == 20
    assert counts["with_inherited_d217"]["n_trials"] == 62
    assert counts["combined_with_disclosed"]["n_trials"] == max(
        f["n_trials"] for f in counts.values()
    )


def test_the_fresh_count_is_the_arithmetic_it_claims(payload):
    assert len(payload["core"]) == 4 * 2 * 2 == 16
    assert payload["sensitivity_looks"] == len(payload["sensitivity"]) - 2 == 4
    assert I.FRESH_LOOKS == 16 + 4


def test_the_raw_row_count_is_never_used_as_a_trial_count(payload):
    m = payload["multiplicity"]
    for f in m["counts"].values():
        assert f["n_trials"] < m["raw_row_ceiling"]
