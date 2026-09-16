"""What the cost-waterfall figure CLAIMS, pinned to `tests/golden/test_the_golden_master.hand.json`.

`test_figures.py` gates the mechanics every figure shares. This file gates the two things only
this figure asserts: that the six components it draws account for the whole distance between
100,000 and the final NAV with nothing left over, and that each bar's HEIGHT is the component
it is labelled with — a waterfall whose segments do not sum, or whose bars are not drawn to
scale, is the most quietly misleading chart there is, because it still looks like a waterfall.

The hand ledger it reads is itself gated: `tests/golden/test_the_golden_master.py` recomputes
every value in it from the scenario block with stdlib arithmetic, and requires every value to
appear in `test_the_golden_master.hand.txt`. This file does not re-derive that; it checks that
the figure does not invent, drop or rescale anything on the way to the page.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "figures" / "build_cost_waterfall.py"
HAND = REPO / "tests" / "golden" / "test_the_golden_master.hand.json"
FIGURE = REPO / "docs" / "figures" / "cost-waterfall.svg"

TEXT = re.compile(
    r'<text x="([\d.-]+)" y="([\d.-]+)" text-anchor="(\w+)" font-size="([\d.]+)"[^>]*>(.*?)</text>'
)
RECT = re.compile(r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"')
VIEWBOX = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


def _viewbox(page: str) -> tuple[float, float]:
    """The frame the figure declares. Read rather than restated, so a resize does not need
    an edit here to keep the paper-ground rect identifiable."""
    return tuple(float(v) for v in VIEWBOX.search(page).groups())


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
def hand():
    return json.loads(HAND.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def value_to_y(page: str):
    """The figure's own value->pixel map, read back off its gridline labels.

    Recovered from the drawing rather than imported from the builder, so a change to the
    frame or the scale cannot move the bars and the checker in the same direction at once.
    """
    ticks = {}
    for x, y, anchor, _size, label in TEXT.findall(page):
        if anchor == "end" and re.fullmatch(r"[\d,]+", label):
            ticks[float(label.replace(",", ""))] = float(y) - 3.2  # gridlines() nudges the label
    assert len(ticks) >= 2, "could not find two axis ticks to read the scale from"
    lo, hi = min(ticks), max(ticks)
    slope = (ticks[hi] - ticks[lo]) / (hi - lo)
    return lambda v: ticks[lo] + (v - lo) * slope


# ------------------------------------------------------------------------- the arithmetic


def test_the_segments_sum_to_the_whole_result(facts, hand):
    """The identity a waterfall exists to show, and the one nothing else here would catch.

    Six components, no residual, no 'other' bucket: start + every step == the final NAV the
    golden master asserts.
    """
    total = facts["start"] + sum(value for _label, value in facts["steps"])
    assert total == pytest.approx(hand["final_nav"], rel=1e-12)
    assert sum(value for _label, value in facts["steps"]) == pytest.approx(
        hand["final_nav"] - hand["scenario"]["starting_cash"], rel=1e-9
    )
    assert facts["running"][0] == hand["scenario"]["starting_cash"]
    assert facts["running"][-1] == pytest.approx(hand["final_nav"], rel=1e-12)


def test_every_component_is_the_hand_ledgers_own_column(facts, hand):
    """Each friction is the sum of its own per-bar column — not a figure-only aggregate.

    The signs are asserted too: five components take money away and exactly one adds it.
    """
    bars = hand["bars"]
    expected = {
        "price P&L": sum(b["qty_after"] * (n["price"] - b["price"]) for b, n in zip(bars, bars[1:])),
        "commission": -sum(b["commission"] for b in bars),
        "spread": -sum(b["spread"] for b in bars),
        "borrow": -sum(b["borrow"] for b in bars),
        "margin interest": -sum(b["margin_interest"] for b in bars),
        "dividend": sum(b["dividend"] for b in bars),
    }
    assert [label for label, _ in facts["steps"]] == list(expected)
    for label, value in facts["steps"]:
        assert value == pytest.approx(expected[label], rel=1e-12)
    credits = [label for label, value in facts["steps"] if value > 0]
    assert credits == ["price P&L"], "only the price move is a credit in this scenario"


def test_the_price_pnl_is_967_exactly(facts):
    """The short is 1,200 shares into a 2-point fall, 1,253 into a 3-point rise and 1,163 into
    a 2-point fall: +2,400 - 3,759 + 2,326. It comes to a whole number, which is a useful
    sanity anchor for a figure whose other five bars are fractions of a cent."""
    assert facts["steps"][0][1] == pytest.approx(967.0, abs=1e-9)


def test_the_dividend_is_the_largest_friction(facts):
    """The claim in the title. A short pays the dividend it owes its lender, and here that
    one debit is larger than commission, spread, borrow and margin interest together."""
    frictions = {label: -value for label, value in facts["steps"][1:]}
    assert max(frictions, key=frictions.get) == "dividend"
    assert frictions["dividend"] > sum(v for k, v in frictions.items() if k != "dividend")


def test_the_unpublished_share_is_what_the_figure_says_it_is(facts):
    """The honesty line's two numbers. `published_as_one_number` is commission plus spread —
    which the engine reports, but only as their sum inside a fill; `unpublished` is borrow,
    margin interest and the dividend, which it does not report at all."""
    assert facts["published_as_one_number"] + facts["unpublished"] == pytest.approx(
        facts["frictions"], rel=1e-12
    )
    assert facts["unpublished"] > facts["published_as_one_number"] * 4


# --------------------------------------------------------------------------- the drawing


def test_every_bar_is_drawn_to_the_value_it_is_labelled_with(page, facts):
    """The check that makes the picture the claim rather than an illustration of it.

    Each step's rectangle must span exactly the two running levels it sits between, on the
    figure's own axis. A bar drawn at the wrong height is invisible to every other test here,
    to the shared geometry gate, and to the eye.
    """
    y_of = value_to_y(page)
    width, height = _viewbox(page)
    rects = [
        tuple(float(v) for v in r)
        for r in RECT.findall(page)
        if not (float(r[2]) == width and float(r[3]) == height)  # the paper ground
    ]
    assert len(rects) == 2 + len(facts["steps"]), "expected two anchors and one bar per component"

    steps = rects[2:]
    for index, ((label, _value), (_x, y, _w, h)) in enumerate(zip(facts["steps"], steps)):
        before, after = facts["running"][index], facts["running"][index + 1]
        assert y == pytest.approx(y_of(max(before, after)), abs=0.2), f"{label}: wrong top"
        assert y + h == pytest.approx(y_of(min(before, after)), abs=0.2), f"{label}: wrong bottom"


def test_the_anchors_are_drawn_to_the_axis_floor(page, facts):
    """A truncated axis with floating anchors reads as a chart starting at zero. Both anchor
    bars run to the baseline so the truncation is visible, and the axis label says the range
    out loud."""
    y_of = value_to_y(page)
    rects = [tuple(float(v) for v in r) for r in RECT.findall(page)][1:3]
    floors = {round(y + h, 1) for _x, y, _w, h in rects}
    assert len(floors) == 1, "the two anchors do not share a baseline"
    for (_x, y, _w, _h), value in zip(rects, (facts["start"], facts["final"])):
        assert y == pytest.approx(y_of(value), abs=0.2)
    present(page, "the axis is truncated", "the axis-range disclosure")


def test_the_figure_quotes_the_numbers_it_is_drawn_from(page, facts, hand):
    present(page, f"{hand['final_nav']:,.10f}", "the final NAV")
    present(page, f"{hand['scenario']['starting_cash']:,.2f}", "the starting cash")
    for label, value in facts["steps"]:
        shown = f"+{value:,.4f}" if value > 0 else f"{value:,.4f}"
        present(page, shown, f"the {label} component")
    present(page, f"{facts['frictions']:,.4f}", "the friction total")
    present(page, f"{facts['unpublished']:,.4f}", "the share the engine never reports")
    present(page, f"{facts['published_as_one_number']:,.4f}", "the share reported as one number")


def test_the_figure_says_the_decomposition_is_not_the_engines(page):
    """The finding, not a caveat: four of the six bars cannot be drawn from anything
    `BacktestResult` publishes. A figure that quietly implied otherwise would be claiming the
    instrument measures something it does not."""
    for phrase in ("engine/backtest.py:42-79", "hand ledger", "ONE number"):
        assert phrase in page, f"the figure does not say {phrase!r}"


def test_the_figure_paints_credit_and_debit_apart(page, facts, builder):
    """One credit, five debits, and the reader can tell which is which without the sign."""
    assert builder.CREDIT != builder.DEBIT
    rects = [r for r in re.findall(r'<rect [^>]*fill="var\((--[a-z-]+)\)"', page)]
    assert rects.count(builder.CREDIT) == 1
    assert rects.count(builder.DEBIT) == len(facts["steps"]) - 1
