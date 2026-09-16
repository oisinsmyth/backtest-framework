"""What the cross-engine figure CLAIMS, pinned to `data/cross_engine_residuals.json`.

`test_figures.py` gates the mechanics every figure shares. This file gates the two claims only
this figure makes:

1. **The continuous one** — the worst per-bar divergence is a specific distance above double
   precision and a specific distance below D47's gate. Every number behind that sentence is
   recomputed here from the RAW residual lists, by a different route than the builder takes, and
   compared against the values `docs/verification/cross_engine_reconciliation.md` published in
   2026-07. A figure whose max was copied out of a summary field would be a picture of a claim
   rather than a measurement of one, so the first test below checks that no such field exists.

2. **The discrete one** — both engines re-sized on the same 1,370 of 2,515 bars. That is the real
   evidence and it is the one the drawing compresses (45 runs, not 2,515 rects, for the
   250,000-byte budget), so the compression is checked by expanding it back.

And one more, because `README.md:12` says "the simulator reconciled against vectorbt" with no
qualifier: the figure's face must carry the scope it was actually run at.
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
BUILDER = REPO / "scripts" / "figures" / "build_cross_engine.py"
ARTIFACT = REPO / "data" / "cross_engine_residuals.json"
FIGURE = REPO / "docs" / "figures" / "cross-engine-agreement.svg"

# `docs/verification/cross_engine_reconciliation.md`, the 2026-07-14 reconciliation, rows 36-41.
# Typed here rather than read from the document: this is the claim the artifact has to reproduce,
# and a test that parsed the prose would move whenever the prose did.
PUBLISHED_BARS = 2_515
PUBLISHED_TRADES = 1_370
PUBLISHED_FINAL = "$159,233.023491"
PUBLISHED_MAX_ABS = "$0.0000002186"
PUBLISHED_MAX_REL = "1.30e-12"

TEXT = re.compile(
    r'<text x="([\d.-]+)" y="([\d.-]+)" text-anchor="(\w+)" font-size="([\d.]+)"[^>]*>(.*?)</text>'
)
RECT = re.compile(
    r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)" fill="var\((--[a-z-]+)\)"'
)
DECADE_LABEL = re.compile(r"^1e(-\d+)$")


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
def raw():
    return json.loads(ARTIFACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def texts(page: str) -> list[str]:
    return [label for _x, _y, _a, _s, label in TEXT.findall(page)]


# ------------------------------------------------ the artifact is primitives, not conclusions


def test_the_artifact_carries_no_summary_for_the_figure_to_copy(raw):
    """The structural version of "recomputed, not read".

    If `cross_engine_residuals.json` held a `max_abs_divergence`, the builder and this test could
    both quote it and agree about a number neither had derived. It holds the residual series and
    nothing that summarises it, so agreement between the figure and this file is agreement
    between two computations.
    """
    forbidden = [
        key
        for key in raw
        if re.search(r"max|worst|argmax|decade|bucket|summary|divergence", key, re.I)
    ]
    assert not forbidden, (
        f"{ARTIFACT.name} has grown summary field(s) {forbidden}. The figure must derive its "
        "max, its argmax and its bucket counts from `rel_residuals`; a field like that lets it "
        "stop."
    )
    assert len(raw["abs_residuals"]) == len(raw["rel_residuals"]) == raw["bars"]


def test_the_residuals_reproduce_the_published_maximum(raw):
    """The 2026-07 reconciliation's headline, re-derived from the per-bar series."""
    assert raw["bars"] == PUBLISHED_BARS
    assert f"${max(raw['abs_residuals']):.10f}" == PUBLISHED_MAX_ABS
    assert f"{max(raw['rel_residuals']):.2e}" == PUBLISHED_MAX_REL
    for side in ("final_ours", "final_theirs"):
        assert f"${raw[side]:,.6f}" == PUBLISHED_FINAL, f"{side} is not the published final value"
    assert raw["final_ours"] == pytest.approx(raw["final_theirs"], rel=raw["tolerance"])


def test_the_two_maxima_fall_on_different_bars(raw):
    """The one thing the published document gets slightly wrong, recorded so the figure does not
    inherit it.

    `cross_engine_reconciliation.md:40` reads "$0.0000002186 (1.30e-12 relative)", which reads as
    one measurement expressed two ways. They are the maxima of two different series and they are
    two different bars: the largest dollar gap is not the largest relative gap, because the curve
    is not flat. Both published numbers are correct; only the parenthesis is.
    """
    arg_abs = max(range(raw["bars"]), key=lambda i: raw["abs_residuals"][i])
    arg_rel = max(range(raw["bars"]), key=lambda i: raw["rel_residuals"][i])
    assert arg_abs != arg_rel, "the two maxima coincided; the figure's caption says they do not"
    assert f"{raw['rel_residuals'][arg_abs]:.2e}" != PUBLISHED_MAX_REL


# ------------------------------------------------------ everything drawn, recomputed from raw


def test_every_number_the_builder_draws_is_recomputed_from_the_raw_series(facts, raw):
    """Same numbers, a different route: `sorted()` and an explicit sweep rather than `max()` with
    a key and a `floor(log10())` accumulator."""
    rel = list(raw["rel_residuals"])
    abs_ = list(raw["abs_residuals"])

    assert facts["max_rel"] == sorted(rel)[-1]
    assert facts["max_abs"] == sorted(abs_)[-1]
    assert rel[facts["max_rel_bar"]] == facts["max_rel"]
    assert abs_[facts["max_abs_bar"]] == facts["max_abs"]
    assert facts["max_rel_abs"] == abs_[facts["max_rel_bar"]]

    zeros = 0
    counts: dict[int, int] = {}
    for value in rel:
        if value == 0.0:
            zeros += 1
            continue
        decade = int(math.floor(math.log10(value)))
        counts[decade] = counts.get(decade, 0) + 1
    assert facts["zeros"] == zeros
    assert facts["counts"] == counts
    assert zeros + sum(counts.values()) == raw["bars"], "a bar fell out of the buckets"

    assert facts["decades_above_eps"] == pytest.approx(
        math.log10(facts["max_rel"] / builder_eps()), rel=1e-12
    )
    assert facts["decades_below_gate"] == pytest.approx(
        math.log10(raw["tolerance"] / facts["max_rel"]), rel=1e-12
    )


def builder_eps() -> float:
    """`sys.float_info.epsilon`, which is what the figure labels as the floor."""
    return sys.float_info.epsilon


def test_the_epsilon_the_figure_labels_is_the_machine_epsilon(builder):
    assert builder.EPS == sys.float_info.epsilon
    assert builder.EPS == 2.220446049250313e-16


def test_the_worst_divergence_is_inside_the_gate_and_above_the_floor(facts, raw):
    """The panel in one assertion. Both inequalities matter: inside the gate is the pass, and
    above the floor is the honesty — the engines are NOT bit-identical and the figure says so."""
    assert builder_eps() < facts["max_rel"] < raw["tolerance"]
    assert facts["decades_above_eps"] > 1.0
    assert facts["decades_below_gate"] > 1.0
    assert max(raw["abs_residuals"]) < 1e-6, "a whole cent would not be floating-point noise"


def test_every_bucket_count_drawn_is_a_recomputed_count(page, facts):
    """Each decade column's label, matched against the recount — and nothing else labelled as a
    count. A column drawn at the wrong height would still be caught by the label, and a label
    invented for a decade with no bars would be caught here."""
    labels = texts(page)
    for decade, count in sorted(facts["counts"].items()):
        assert f"{count:,}" in labels, f"the 1e{decade} bucket count {count:,} is not on the figure"
    assert len(facts["counts"]) == 5, "the occupied decades moved; the panel is drawn per decade"


# ----------------------------------------------------------------- the discrete identity


def test_both_engines_resized_on_exactly_the_same_bars(raw):
    """The claim floating point cannot manufacture, and the one the second panel is for."""
    ours, theirs = raw["fill_bars_ours"], raw["fill_bars_theirs"]
    assert raw["fills_ours"] == raw["fills_theirs"] == PUBLISHED_TRADES
    assert len(ours) == len(theirs) == PUBLISHED_TRADES
    assert set(ours) == set(theirs), "the engines disagreed about which bars to trade"
    assert len(set(ours)) == PUBLISHED_TRADES, "a bar was listed twice; the panel is one per bar"
    assert set(ours) <= set(range(raw["bars"])), "a fill landed outside the fixture"


def test_the_runs_the_figure_draws_expand_back_to_the_exact_fill_set(builder, raw):
    """The compression check. 2,515 rects would blow the 250,000-byte budget, so the panel draws
    45 contiguous runs; if a run's bounds were off by one the picture would show an agreement
    that is not the measured one, and every other test here would still pass."""
    for side in ("fill_bars_ours", "fill_bars_theirs"):
        spans = builder.runs(raw[side])
        expanded = [i for first, last in spans for i in range(first, last + 1)]
        assert expanded == sorted(raw[side]), f"{side}: the runs do not expand back to the fills"
        assert len(expanded) == len(set(expanded)), f"{side}: the runs overlap"
    assert builder.runs(raw["fill_bars_ours"]) == builder.runs(raw["fill_bars_theirs"])


def test_the_run_expansion_can_actually_fail(builder, raw):
    """A self-test that cannot fail is worse than none (CLAUDE.md).

    Perturb one bar of the fill list and the expansion must stop matching the original set. If it
    still matched, the test above would be asserting nothing.
    """
    broken = sorted(raw["fill_bars_ours"])
    broken[len(broken) // 2] += 1
    expanded = [i for first, last in builder.runs(broken) for i in range(first, last + 1)]
    assert expanded != sorted(raw["fill_bars_ours"])


def test_the_difference_row_is_drawn_and_is_empty(page, builder, facts):
    """The image the whole panel exists for: three rows, and the third one blank.

    Asserted as rect counts by row, not by eye. An empty row that was never drawn at all would
    look identical in a screenshot and would say nothing.
    """
    rects = [
        (float(x), float(y), float(w), float(h), token)
        for x, y, w, h, token in RECT.findall(page)
    ]
    tops = [404.0 + i * (builder.ROW_H + builder.ROW_GAP) for i in range(3)]
    grounds = [r for r in rects if r[1] in tops and r[4] == "--sunk"]
    assert len(grounds) == 3, "the second panel does not have three row grounds"

    runs_drawn = {}
    for index, top in enumerate(tops):
        runs_drawn[index] = [r for r in rects if r[1] == pytest.approx(top + 2.0) and r[3] == builder.ROW_H - 4.0]
    assert len(runs_drawn[0]) == len(facts["runs_ours"]) == 45
    assert len(runs_drawn[1]) == len(facts["runs_theirs"]) == 45
    assert runs_drawn[2] == [], "the difference row has something drawn in it"
    assert [r[4] for r in runs_drawn[0]] != [r[4] for r in runs_drawn[1]], (
        "the two engines' rows are painted with one token — a reader cannot see them as two "
        "independent measurements"
    )


# ----------------------------------------------------------------------- the log axis


def _decade_ticks(page: str) -> dict[int, float]:
    out: dict[int, float] = {}
    for x, _y, anchor, _size, label in TEXT.findall(page):
        match = DECADE_LABEL.match(label)
        if match and anchor == "middle":
            out[int(match.group(1))] = float(x)
    return out


def test_every_decade_boundary_is_where_a_log_scale_puts_it(page, builder):
    """A log axis is defined by equal pixels per decade. Checked off the emitted x attributes
    rather than by re-running the builder's own `Scale`, which would prove nothing."""
    ticks = _decade_ticks(page)
    assert sorted(ticks) == list(range(builder.DECADE_LO, builder.DECADE_HI + 1)), (
        f"the drawn decades are {sorted(ticks)}, not the declared "
        f"{builder.DECADE_LO}..{builder.DECADE_HI}"
    )
    ordered = [ticks[d] for d in sorted(ticks)]
    gaps = [b - a for a, b in zip(ordered, ordered[1:])]
    assert max(gaps) - min(gaps) <= 0.11, (
        f"decade spacing runs {min(gaps):.2f}..{max(gaps):.2f}px — that is not a log axis "
        "(0.1px of slack is svgkit.c()'s one-decimal rounding)"
    )
    assert min(gaps) > 20.0, "the decades are too tightly packed to read"


def test_the_rules_and_the_marker_sit_at_their_own_values(page, builder, facts):
    """Epsilon, the D47 gate and the worst bar, each placed by interpolating the decade ticks the
    previous test just proved are a log axis. A marker one decade out would be the most quietly
    wrong thing in the set."""
    ticks = _decade_ticks(page)
    origin, per_decade = ticks[builder.DECADE_LO], (
        ticks[builder.DECADE_HI] - ticks[builder.DECADE_LO]
    ) / (builder.DECADE_HI - builder.DECADE_LO)

    def expected(value: float) -> float:
        return origin + (math.log10(value) - builder.DECADE_LO) * per_decade

    eps_rule = re.search(
        r'<line x1="([\d.]+)" y1="100.0" x2="[\d.]+" y2="282.0"[^>]*stroke-dasharray="2 3"', page
    )
    gate_rule = re.search(
        r'<line x1="([\d.]+)" y1="100.0" x2="[\d.]+" y2="282.0"[^>]*stroke-dasharray="4 3"', page
    )
    assert eps_rule and gate_rule, "the floor rule and the gate rule are not both drawn"
    assert float(eps_rule.group(1)) == pytest.approx(expected(builder.EPS), abs=0.15)
    assert float(gate_rule.group(1)) == pytest.approx(expected(facts["tolerance"]), abs=0.15)

    circles = re.findall(r'<circle cx="([\d.]+)"', page)
    assert len(circles) == 1, "the worst bar is meant to be the only dot on the figure"
    assert float(circles[0]) == pytest.approx(expected(facts["max_rel"]), abs=0.15)
    assert float(circles[0]) < float(gate_rule.group(1)), "the marker is drawn in failure territory"
    assert float(circles[0]) > float(eps_rule.group(1)), "the marker is drawn below the floor"


# ------------------------------------------------------------------ what the face says


def test_the_figure_quotes_the_numbers_it_is_drawn_from(page, builder, facts, raw):
    esc = builder.k.esc
    present(page, PUBLISHED_MAX_REL, "the worst relative divergence")
    present(page, PUBLISHED_MAX_ABS, "the largest dollar divergence")
    present(page, PUBLISHED_FINAL, "the final value both engines reach")
    present(page, f"${facts['max_rel_abs']:.10f}", "the dollar value at the worst relative bar")
    present(page, f"{builder.EPS:.2e}", "double-precision epsilon")
    present(page, f"1e{round(math.log10(facts['tolerance']))}", "the D47 tolerance")
    present(page, f"{facts['bars']:,}", "the bar count")
    present(page, f"{facts['fills']:,}", "the trade count")
    present(page, f"{facts['max_rel_bar']:,}", "the worst relative bar index")
    present(page, f"{facts['max_abs_bar']:,}", "the worst absolute bar index")
    present(page, esc(f"{facts['decades_above_eps']:.1f} decades above"), "the gap above the floor")
    present(page, esc(f"and {facts['decades_below_gate']:.1f} decades below"), "the gap to the gate")
    present(page, esc(f"{facts['zeros']:,} bars diverge by exactly zero"), "the bit-identical bars")
    present(page, esc(f"in {len(facts['runs_ours']):,} contiguous runs"), "the run count")
    assert raw["fixture"] in page or "cross_engine_residuals" in page


def test_the_figure_carries_the_scope_it_was_actually_run_at(page, builder, raw):
    """`README.md:12` claims "the simulator reconciled against vectorbt" unqualified. The
    reconciliation is one instrument, long-flat, proportional fees only. A figure that repeated
    the unqualified claim would be the most misleading thing in the set, so the qualification is
    on its face and is asserted here rather than left to a caption someone may not carry."""
    esc = builder.k.esc
    for phrase in (
        "Scope: one instrument",
        "long-flat only",
        "proportional fees only",
        "Carry, dividends,",
        "splits, margin and multi-leg netting are ours alone",
        "golden master",
    ):
        present(page, esc(phrase), "the scope caveat")
    for word in ("long-flat", "proportional", "golden"):
        assert word in raw["scope"], (
            f"the artifact's scope sentence does not mention {word!r}; the figure's face and the "
            "JSON have drifted apart"
        )
