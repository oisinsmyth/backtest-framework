"""What the DSR hurdle figure CLAIMS, pinned to `data/macd_ladder_summary.json`.

`test_figures.py` gates the mechanics every figure shares. This file gates the one thing only
this figure asserts: that a result clearing at 42 looks fails at 45,783, and that the crossing
between those two states is where it is drawn.

The curve is the library's own `expected_max_sharpe`, not a fit through the recorded points, and
the first test below is what makes that statement checkable rather than decorative.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "figures" / "build_dsr_hurdle.py"
ARTIFACT = REPO / "data" / "macd_ladder_summary.json"
FIGURE = REPO / "docs" / "figures" / "dsr-hurdle-vs-look-count.svg"


def _module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _module(BUILDER)


@pytest.fixture(scope="module")
def facts(builder):
    return builder.facts()


@pytest.fixture(scope="module")
def summary():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def test_the_curve_reproduces_every_recorded_hurdle(facts, summary):
    """The claim that the curve is the study's own arithmetic, made checkable.

    If `expected_max_sharpe` evaluated at the three recorded counts did not return the three
    recorded values, the curve would be a plausible-looking line through them and the figure
    would be asserting something the record does not.
    """
    annualise = math.sqrt(summary["periods_per_year"])
    assert annualise == pytest.approx(math.sqrt(252.0))
    for name, count in summary["multiplicity"]["counts"].items():
        assert facts["hurdle"](count["n_trials"]) == pytest.approx(
            count["expected_max_sharpe_annualised"], rel=1e-12
        ), f"the curve disagrees with the recorded hurdle at {name}"


def test_the_observed_sharpe_is_the_best_cell_in_the_ladder(facts, summary):
    best = max(summary["core"], key=lambda cell: cell["sharpe"])
    assert facts["observed"] == best["sharpe"]
    assert facts["cell"] == f"{best['rung']}/{best['book']}/{best['gate']}"
    assert best["sharpe"] == pytest.approx(0.495680381678844)


def test_the_result_clears_the_fresh_count_and_fails_the_verdict_count(facts, summary):
    """The whole figure in one assertion. If this ever stops being true the figure is a lie."""
    counts = summary["multiplicity"]["counts"]
    assert facts["observed"] > counts["fresh"]["expected_max_sharpe_annualised"]
    assert facts["observed"] < counts["combined_with_disclosed"]["expected_max_sharpe_annualised"]
    assert all(row["G_dsr_floor"] is False for row in summary["verdict"]["rows"]), (
        "the study records that no cell clears the deflated-Sharpe floor"
    )


def test_the_crossing_is_bracketed(facts):
    """Not 'about a thousand' — the first integer count at which the floor overtakes the result."""
    n = facts["crossing"]
    assert facts["hurdle"](n - 1) < facts["observed"] <= facts["hurdle"](n)
    assert n == 1086, "the crossing moved; the figure's caption names it"


def test_the_hurdle_only_ever_rises(facts):
    """A floor that fell with more looks would make the registry pointless, and the figure
    would still look fine. Checked over the range actually drawn."""
    ns = [2, 3, 5, 10, 42, 100, 1_086, 5_000, 45_388, 45_783, 100_000]
    values = [facts["hurdle"](n) for n in ns]
    assert values == sorted(values)


def test_the_figure_quotes_the_numbers_it_is_drawn_from(page, facts, summary):
    counts = summary["multiplicity"]["counts"]
    present(page, f"{facts['observed']:.4f}", "the observed Sharpe")
    present(page, f"{counts['fresh']['n_trials']:,}", "the fresh look count")
    present(page, f"{counts['combined_with_disclosed']['n_trials']:,}", "the verdict count")
    present(page, f"{counts['fresh_plus_prior_configs']['n_trials']:,}", "the inherited count")
    present(page, f"{facts['crossing']:,}", "the crossing")
    present(page, f"{facts['deficit']:.3f}", "the deficit at the verdict count")
    present(page, facts["cell"], "the cell the Sharpe belongs to")


def test_the_curve_is_sampled_densely_enough_to_read_as_a_curve(page, builder):
    """`n_trials` is an integer, so the true object is a step function and the polyline is a
    sampling of it. Too few samples and the eye reads straight segments as the claim."""
    points = re.search(r'<polyline points="([^"]+)"', page).group(1).split()
    assert len(points) >= 300, f"the hurdle is drawn from only {len(points)} points"
    assert len(points) <= builder.SAMPLES


def test_the_marked_counts_sit_on_the_curve(page, facts):
    """Each recorded count is drawn as a dot. A dot placed anywhere but on the line it annotates
    is the most quietly misleading thing a chart can do."""
    circles = [
        (float(cx), float(cy))
        for cx, cy in re.findall(r'<circle cx="([\d.-]+)" cy="([\d.-]+)"', page)
    ]
    points = [
        tuple(float(v) for v in pair.split(","))
        for pair in re.search(r'<polyline points="([^"]+)"', page).group(1).split()
    ]
    marks = [c for c in circles if any(abs(c[0] - px) < 2.0 for px, _ in points)]
    assert len(marks) >= 3, "expected a dot for each of the three recorded counts"
    for cx, cy in marks:
        nearest = min(points, key=lambda p: abs(p[0] - cx))
        assert abs(nearest[1] - cy) <= 2.0, (
            f"a marker at x={cx:.1f} sits {abs(nearest[1] - cy):.1f}px off the curve it annotates"
        )
