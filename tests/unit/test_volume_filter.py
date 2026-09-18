"""Gates on the D220 volume-filter runner and its published numbers.

Three of these matter more than the rest.

**The loader gate.** D220's pre-registration made it a stop condition that
plumbing volume through must not move any previously published number. Volume is
therefore loaded SEPARATELY rather than by changing `load_panel`, and
`test_reading_volume_does_not_move_the_price_path` is what makes that structural
instead of promised.

**The information boundary.** The filter reads volume at the DECISION bar, not
the bar the position first exists on. A filter that peeks one bar is the easiest
way in the world to manufacture selectivity, so it is tested by perturbation
rather than by inspection.

**Idempotent rendering.** D217 published a page `--report-only` could not
reproduce, and the first version of `append_section` here reintroduced it in a
different place. Pinned.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "volume_filter_summary.json"
RESULTS = REPO / "docs" / "results" / "MACD_RESULTS.md"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


V = _load("run_volume_filter", "run_volume_filter.py")


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_volume_filter.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return RESULTS.read_text(encoding="utf-8").replace("−", "-")


# --------------------------------------------------------------------------
# 1. The shared machinery and the loader gate
# --------------------------------------------------------------------------


def test_d220_prices_its_arms_with_the_existing_runners_and_not_its_own():
    """D212. Identity, not equality."""
    assert V.L.__name__ == "run_macd_ladder"
    assert V.I.__name__ == "run_impulse_macd"
    for name in ("portfolio_log_returns", "per_side_bps", "buy_and_hold", "sharpe_of"):
        assert name not in vars(V), f"D220 has restated {name} — that is D212 again"
    assert V.PPY is V.L.PPY


def test_reading_volume_does_not_move_the_price_path(requires_panel):
    """The pre-registered stop: if plumbing volume changes a published number,
    everything halts. `load_fixture_csv` delegates to the with-volumes loader and
    drops the volumes, so the bars must be identical objects by value."""
    from backtest_framework.data.csv_fixture import (
        load_fixture_csv,
        load_fixture_csv_with_volumes,
    )

    requires_panel(V.L.FIXTURE)
    bars_only = load_fixture_csv(V.L.FIXTURE)
    bars_with, volumes = load_fixture_csv_with_volumes(V.L.FIXTURE)
    assert set(bars_only) == set(bars_with)
    for sym in bars_only:
        assert bars_only[sym] == bars_with[sym]
        assert len(volumes[sym]) == len(bars_only[sym])


def test_the_volume_matrix_is_aligned_to_the_cleaned_grid_by_timestamp(loading_a_panel):
    with loading_a_panel():
        panel, cleaned = V.L.load_panel()
    vol = V.volume_matrix(panel, cleaned)
    assert vol.shape == panel.closes.shape
    assert np.isfinite(vol).all()
    assert (vol > 0).all(), "the fixture has no zero-volume bars; that changed"


# --------------------------------------------------------------------------
# 2. The information boundary
# --------------------------------------------------------------------------


@pytest.mark.parametrize("condition", V.CONDITIONS)
def test_the_filter_reads_no_bar_later_than_the_decision_bar(condition):
    """Perturb every volume from bar t onward. The decision for a position that
    first exists at t was taken from bar t-1, so `ok[:, t]` must not move."""
    rng = np.random.default_rng(7)
    vol = rng.lognormal(mean=10.0, sigma=0.6, size=(4, 160))
    base = V.entry_allowed(vol, condition, 20)
    t = 120
    tampered = vol.copy()
    tampered[:, t:] *= 50.0
    after = V.entry_allowed(tampered, condition, 20)
    assert np.array_equal(base[:, : t + 1], after[:, : t + 1])


def test_v1_and_v2_are_complements_wherever_both_are_defined():
    rng = np.random.default_rng(3)
    vol = rng.lognormal(mean=9.0, sigma=0.5, size=(3, 120))
    a = V.entry_allowed(vol, "V1_confirmation", 20)
    b = V.entry_allowed(vol, "V2_contrarian", 20)
    defined = ~np.isnan(V.trailing_mean(vol, 20))
    both = np.zeros_like(defined)
    both[:, 1:] = defined[:, :-1]
    # Ties (volume exactly equal to its mean) are excluded from both by design.
    assert not (a & b).any(), "a bar cannot be both above and below its own mean"
    assert (a | b)[both].mean() > 0.99


def test_trailing_mean_is_the_window_ending_at_t_inclusive():
    v = np.arange(1, 11, dtype=float)[None, :]
    ma = V.trailing_mean(v, 3)
    assert np.isnan(ma[0, :2]).all()
    assert ma[0, 2] == pytest.approx(2.0)  # (1+2+3)/3
    assert ma[0, 9] == pytest.approx(9.0)  # (8+9+10)/3


# --------------------------------------------------------------------------
# 3. The bounds behave like bounds
# --------------------------------------------------------------------------


def test_the_oracle_is_an_upper_bound_on_every_cell_at_its_own_removal_count(payload):
    """No real filter may beat the look-ahead one at the same removal count. If
    this ever fails, either the oracle or the filter is not doing what it says."""
    for c in payload["cells"]:
        assert c["sharpe"] <= c["oracle_sharpe"] + 1e-9, c["cell"]
        assert c["total_return_with_dividends"] <= c["oracle_total_return"] + 1e-9, c["cell"]


def test_the_oracle_improves_monotonically_as_it_removes_more(payload):
    for book in payload["parent"]["books"].values():
        grid = book["oracle_grid"]
        sharpes = [g["sharpe"] for g in grid]
        assert sharpes == sorted(sharpes), "removing more of the worst cannot hurt"


def test_the_random_null_is_matched_on_trade_count_not_on_exposure(payload):
    """The point of the null: it removes the same NUMBER of trades, so a delta
    over it cannot be explained by the filter simply having traded less."""
    for c in payload["cells"]:
        assert c["trades_kept"] + c["trades_removed"] > 0
        lo, hi = c["random_sharpe_p50"], c["random_sharpe_p95"]
        assert lo <= hi


def test_capture_is_zero_when_the_filter_lands_on_the_random_median():
    assert V.capture(0.5, 0.5, 1.5) == pytest.approx(0.0)
    assert V.capture(1.5, 0.5, 1.5) == pytest.approx(1.0)
    assert V.capture(0.4, 0.5, 0.5) == pytest.approx(0.0)  # degenerate span


# --------------------------------------------------------------------------
# 4. Hurdle H and the verdict
# --------------------------------------------------------------------------


def test_hurdle_h_requires_all_three_components(payload):
    for row, cell in zip(payload["verdict"]["rows"], payload["cells"]):
        beats = (
            cell["sharpe_percentile_in_random"] >= V.NULL_PERCENTILE
            and cell["total_percentile_in_random"] >= V.NULL_PERCENTILE
        )
        perm = cell["permutation"]["percentile"] >= V.NULL_PERCENTILE
        assert row["H_selectivity"] == (beats and perm), row["cell"]


def test_at_least_one_cell_clears_selectivity_and_still_loses_money(payload):
    """The finding that vindicates the dual verdict: H alone would have promoted
    a book with negative Sharpe. If this stops being true the conjunction has
    stopped buying anything and the record should say so."""
    split = [
        c
        for c, r in zip(payload["cells"], payload["verdict"]["rows"])
        if r["H_selectivity"] and c["sharpe"] <= 0.0
    ]
    assert split, "no cell exhibits the selective-but-losing split"


def test_every_cell_is_underpowered_by_the_pre_registered_census_gate(payload):
    """The result. The parent barely clears 30 entries per ETF, so any filter
    removing 39-61% of trades drops below it."""
    assert payload["parent"]["books"]["long_flat"]["census"]["min_entries_per_etf"] >= 30
    for c in payload["cells"]:
        assert c["census"]["min_entries_per_etf"] < V.MIN_ENTRIES_PER_ETF, c["cell"]
    assert not any(r["E_powered"] for r in payload["verdict"]["rows"])


def test_no_cell_beats_the_parent_on_money(payload):
    assert not any(r["beats_parent_money"] for r in payload["verdict"]["rows"])


def test_there_are_no_survivors(payload):
    assert payload["verdict"]["survivors"] == []


# --------------------------------------------------------------------------
# 5. The ledger and the page
# --------------------------------------------------------------------------


def test_the_fresh_count_is_the_arithmetic_it_claims(payload):
    assert len(payload["cells"]) == 3 * 2 * 2 == 12
    assert payload["fresh_looks"] == V.FRESH_LOOKS == 12
    counts = payload["multiplicity"]["counts"]
    assert counts["with_inherited"]["n_trials"] == 12 + 62
    assert counts["combined_with_disclosed"]["n_trials"] == max(
        f["n_trials"] for f in counts.values()
    )


def test_the_raw_row_count_is_never_used_as_a_trial_count(payload):
    m = payload["multiplicity"]
    for f in m["counts"].values():
        assert f["n_trials"] < m["raw_row_ceiling"]


def test_the_published_tables_are_the_artifact(payload, page):
    for c in payload["cells"]:
        assert f"{c['sharpe']:+.3f}" in page, c["cell"]
        assert f"{c['total_return_with_dividends'] * 100:.2f}%" in page, c["cell"]
    for name, f in payload["multiplicity"]["counts"].items():
        assert f"{f['n_trials']:,}" in page, name


def test_report_only_reproduces_the_page_byte_for_byte(payload, tmp_path, monkeypatch):
    """D217's defect, and the one this runner reintroduced and had to fix: the
    insert path and the replace path must emit identical bytes.

    AGAINST A COPY. This test used to call `append_section` twice against the real
    `docs/results/MACD_RESULTS.md` -- a published result, which `CLAUDE.md` treats as evidence --
    and restore it in a `finally`. The `finally` covers an assertion failure and nothing else: not
    a kill, not an OOM, not a closed terminal. Worse, two overlapping pytest runs race on it, and
    the race is silent: the second run reads the dirtied page as its "before", the first restores
    the clean bytes, the second then restores the first's dirt, and both runs are green.

    Its three siblings -- `test_assembled_strategy`, `test_sampling_invariance`,
    `test_scaling_ladder` -- solved the same problem by reading instead of writing, asserting
    `render(payload) == PAGE.read_text(...)`. That is not available here, because the property
    under test IS the writing: `append_section` strips any existing section before inserting, so
    the insert path and the replace path run the same insertion, and only two real writes can show
    that they agree.
    """
    page = tmp_path / "MACD_RESULTS.md"
    page.write_bytes(RESULTS.read_bytes())
    monkeypatch.setattr(V, "RESULTS", page)

    V.append_section(V.render(payload))
    once = page.read_bytes()
    V.append_section(V.render(payload))

    assert page.read_bytes() == once, "re-rendering is not idempotent"
    assert once.decode("utf-8").count("## D220 —") == 1


def test_the_weak_instrument_disclosure_sits_beside_the_verdict(page):
    assert "ETF volume is a weak instrument" in page
    assert "weaker evidence against volume as" in page
