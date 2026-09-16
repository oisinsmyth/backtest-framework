"""Gates on the D222 scaling ladder.

The one that matters most is `test_every_rung_scores_on_one_shared_span`. The
whole study is a trend claim across k, and a trend measured over different
periods is not a trend — warm-up runs from 42 days at k=4 to 1,016 at k=96, so
without a shared span a rising Delta would be indistinguishable from the later
period behaving differently.

The second is `test_no_delta_is_resolvable_against_its_own_interval`. It pins the
finding: hurdle L without hurdle M is a pattern in noise, and if these intervals
ever tighten enough to separate the deltas, the conclusion has to be revisited.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "scaling_ladder_summary.json"
PAGE = REPO / "docs" / "results" / "SCALING_RESULTS.md"
D221_SUMMARY = REPO / "data" / "sampling_invariance_summary.json"


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


G = _load("run_scaling_ladder", "run_scaling_ladder.py")


@pytest.fixture(scope="module")
def payload():
    if not SUMMARY.exists():  # pragma: no cover - the artifact is committed
        pytest.skip("run scripts/run_scaling_ladder.py first")
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return PAGE.read_text(encoding="utf-8").replace("−", "-").replace("Δ", "Delta")


# --------------------------------------------------------------------------
# 1. Reuse, and the shared span
# --------------------------------------------------------------------------


def test_d222_scores_its_arms_with_d221s_code_and_not_its_own():
    """D212. The arm, the annualisation and the Sharpe are the same objects."""
    assert G.S.__name__ == "run_sampling_invariance"
    for name in ("arm", "ppy", "sharpe"):
        assert name not in vars(G), f"D222 has restated {name} — that is D212 again"


def test_every_rung_scores_on_one_shared_span(payload):
    """The confound the study exists to avoid."""
    for sym, block in payload["per_symbol"].items():
        years = [
            r["years"] for r in payload["rows"] if r["symbol"] == sym
        ]
        assert max(years) - min(years) < 0.01, f"{sym}: spans differ across rungs"
        assert block["span_years"] > 5.0, sym


def test_the_shared_span_gate_allows_one_coarse_bar_and_no_more():
    """A daily bar can only start at 00:00 UTC and an 8h bar at 00/08/16:00, so
    configs on different grids cannot share an exact timestamp. Demanding that is
    impossible — the first version of this gate did, and fired. The invariant is a
    bounded spread, and it must still REJECT a genuinely misaligned ladder."""
    from datetime import datetime

    ok = {
        "a": {"minutes": 1440, "first_ts": datetime(2021, 1, 1, 0), "last_ts": datetime(2026, 1, 1, 0)},
        "b": {"minutes": 15, "first_ts": datetime(2020, 12, 31, 6), "last_ts": datetime(2026, 1, 1, 23)},
    }
    G._assert_shared_span(ok, "OK")  # within one 1,440-minute bar
    bad = {
        "a": {"minutes": 60, "first_ts": datetime(2021, 1, 1, 0), "last_ts": datetime(2026, 1, 1, 0)},
        "b": {"minutes": 15, "first_ts": datetime(2021, 6, 1, 0), "last_ts": datetime(2026, 1, 1, 0)},
    }
    with pytest.raises(ValueError, match="starts spread"):
        G._assert_shared_span(bad, "BAD")


def test_d221s_delta_is_not_reused(payload):
    """The headline finding depends on these being SEPARATE measurements: the same
    comparison gives +0.054 on 8.3 years and +0.155 on 5.6."""
    d221 = json.loads(D221_SUMMARY.read_text(encoding="utf-8"))
    old = d221["verdict"]["deltas_B_minus_A"]["BTCUSDT"]
    new = payload["per_symbol"]["BTCUSDT"]["deltas"]["1h"]["delta_gross_sharpe"]
    assert abs(new - old) > 0.05, "the two spans now agree; the finding has moved"


# --------------------------------------------------------------------------
# 2. The finding
# --------------------------------------------------------------------------


def test_the_ladder_is_not_monotone(payload):
    v = payload["verdict"]
    assert v["L_holds"] is False
    for sym, block in payload["per_symbol"].items():
        d = [block["deltas"][n]["delta_gross_sharpe"] for n in v["rung_order"]]
        assert not (d[0] < d[1] < d[2]), sym


def test_delta_is_negative_somewhere(payload):
    """K fails: the margin does not even stay positive, let alone grow."""
    assert payload["verdict"]["K_holds"] is False
    negatives = [
        (s, n)
        for s, b in payload["per_symbol"].items()
        for n in payload["verdict"]["rung_order"]
        if b["deltas"][n]["delta_gross_sharpe"] < 0
    ]
    assert len(negatives) >= 2


def test_no_delta_is_resolvable_against_its_own_interval(payload):
    """Every bootstrap interval straddles zero. This is the finding."""
    for sym, block in payload["per_symbol"].items():
        for name in payload["verdict"]["rung_order"]:
            b = block["deltas"][name]["bootstrap"]
            assert b["p5"] <= 0.0 <= b["p95"], f"{sym}/{name} no longer straddles zero"
            assert b["ci_width"] > 0.3, f"{sym}/{name} interval unexpectedly tight"


def test_turnover_is_set_by_the_window_not_the_bar_rate(payload):
    """At k=96 the 15m arm decides 96x more often and trades the same amount."""
    for sym, block in payload["per_symbol"].items():
        d = block["deltas"]["1d"]
        assert abs(d["fine_rt_per_year"] - d["native_rt_per_year"]) < 2.0, sym
        assert d["native_rt_per_year"] < 15.0, sym


def test_the_naive_scaling_rule_is_what_is_used():
    assert G.matched_params(4) == (136, 36)
    assert G.matched_params(32) == (1088, 288)
    assert G.matched_params(96) == (3264, 864)


# --------------------------------------------------------------------------
# 3. The page
# --------------------------------------------------------------------------


def test_the_published_table_is_the_artifact(payload, page):
    for sym, block in payload["per_symbol"].items():
        for name in payload["verdict"]["rung_order"]:
            d = block["deltas"][name]
            assert f"{d['delta_gross_sharpe']:+.3f}" in page, f"{sym}/{name}"


def test_the_page_says_nothing_is_promoted(page):
    assert "No config is promoted" in page


def test_report_only_reproduces_the_page_byte_for_byte(payload):
    before = PAGE.read_bytes()
    try:
        PAGE.write_text(G.render(payload), encoding="utf-8")
        assert PAGE.read_bytes() == before
    finally:
        PAGE.write_bytes(before)
