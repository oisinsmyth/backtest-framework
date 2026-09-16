"""What the ledger-diff figure CLAIMS, pinned to its two artifacts.

`test_figures.py` gates the mechanics every figure shares. This file gates the three things
only this figure asserts:

1. **The difference column is a measurement.** Every cell in it must be the literal string
   `0.0000000000` — digits, at a stated precision, produced by subtracting one artifact from
   the other at build time. A checkmark would be a claim, and this test is what makes the
   difference between the two: a claim cannot be checked by reading the file, and this can.
2. **Five bar groups, and they are the five bars.** A table that silently drops a row is a
   table that agrees more than the data does.
3. **The band at the bottom is the gap.** Exactly the rows `data/golden_master_ledger.json`
   itself declares unpublished appear there, they are marked as having no engine value, and
   they are drawn apart from the rows that do.

The numbers themselves are gated upstream: `tests/golden/test_the_golden_master.py` recomputes
the hand ledger from first principles, and `scripts/run_golden_master_ledger.py --check`
re-runs the engine against the committed engine ledger.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "figures" / "build_ledger_diff.py"
HAND = REPO / "tests" / "golden" / "test_the_golden_master.hand.json"
ENGINE = REPO / "data" / "golden_master_ledger.json"
FIGURE = REPO / "docs" / "figures" / "golden-master-ledger-diff.svg"

TEXT = re.compile(
    r'<text x="([\d.-]+)" y="([\d.-]+)" text-anchor="(\w+)" font-size="([\d.]+)"[^>]*>(.*?)</text>'
)
RECT = re.compile(
    r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)" fill="var\((--[a-z-]+)\)"'
)

ZERO = "0.0000000000"


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
def engine():
    return json.loads(ENGINE.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def column(page: str, x: float, header_rule_y: float) -> list[str]:
    """Every cell drawn at one column's left edge BELOW the header rule, in document order.

    The column title sits at the same x as the cells it titles, so it has to be excluded by
    position rather than by content — excluding it by content would also exclude a checkmark,
    which is the one thing this column must never be allowed to contain.
    """
    return [
        label
        for cx, cy, _a, _s, label in TEXT.findall(page)
        if float(cx) == pytest.approx(x) and float(cy) > header_rule_y
    ]


# ------------------------------------------------------------------ the difference column


def test_the_difference_column_is_all_zeros(page, builder, facts):
    """Digits, not a tick.

    Twenty published cells, each the literal `0.0000000000`. If the two ledgers ever disagreed
    the figure would print the disagreement — which is the property a checkmark cannot have,
    and the reason the column is drawn as a subtraction at build time rather than asserted in
    a caption.
    """
    cells = column(page, builder.COL_X["delta"], builder.HEADER_RULE_Y)
    published = len(facts["groups"]) * len(builder.PUBLISHED_ROWS)
    assert cells[:published] == [ZERO] * published, (
        "the difference column is not all zeros (or is not all digits): "
        f"{sorted(set(cells[:published]))}"
    )
    assert ZERO.count("0") == 11, "the column's precision is ten places plus the units digit"


def test_the_zeros_are_true_at_the_precision_they_are_printed_to(facts):
    """The text says `0.0000000000`; this is the number behind it.

    The residual is not identically zero — the hand ledger is transcribed to ten decimals and
    the engine carries full binary precision — so the figure would be overclaiming if the
    residual were anywhere near the last printed place. It is three orders below it.
    """
    assert facts["worst"] < 1e-9, f"largest residual {facts['worst']:.3e} is not below 1e-9"
    assert facts["worst"] > 0.0, (
        "an exactly-zero residual everywhere would mean the two ledgers are one artifact, "
        "not two — check that the figure is really reading both files"
    )


def test_the_hand_only_rows_have_no_difference_cell(page, builder, facts):
    """No engine value means no subtraction. The band's difference cells carry the figure's
    own no-value mark, and it is not a zero: printing 0.0000000000 against a row that was
    never compared is exactly the lie this figure is about."""
    cells = column(page, builder.COL_X["delta"], builder.HEADER_RULE_Y)
    published = len(facts["groups"]) * len(builder.PUBLISHED_ROWS)
    band = cells[published:]
    assert band == [builder.NO_VALUE] * len(facts["hand_only"])
    assert builder.NO_VALUE != ZERO


# ------------------------------------------------------------------------------ the rows


def test_there_are_exactly_five_bar_groups(page, hand):
    groups = re.findall(r"<text[^>]*>bar (\d) · (\d{4}-\d{2}-\d{2}) · close ([\d,.]+)", page)
    assert len(groups) == len(hand["bars"]) == 5
    assert [int(index) for index, _date, _close in groups] == [b["index"] for b in hand["bars"]]
    for (_index, date, close), bar in zip(groups, hand["bars"]):
        assert date == bar["timestamp"].split("T")[0]
        assert close == f"{bar['price']:,.2f}"


def test_every_published_row_is_drawn_from_both_artifacts(facts, hand, engine, builder):
    """The join, checked against the files rather than against the builder's memory of them."""
    assert len(facts["groups"]) == len(hand["bars"]) == len(engine["bars"])
    for group, hand_bar, engine_bar in zip(facts["groups"], hand["bars"], engine["bars"]):
        assert group["date"] == hand_bar["timestamp"].split("T")[0] == engine_bar["timestamp"].split("T")[0]
        assert [row["label"] for row in group["rows"]] == [r[0] for r in builder.PUBLISHED_ROWS]
        for row, (_label, hand_key, engine_key, _fmt) in zip(group["rows"], builder.PUBLISHED_ROWS):
            assert row["hand"] == pytest.approx(hand_bar[hand_key], rel=1e-15)
            assert row["engine"] == pytest.approx(engine_bar[engine_key], rel=1e-15)
            assert row["delta"] == pytest.approx(row["hand"] - row["engine"], rel=1e-15, abs=1e-15)


def test_the_band_lists_exactly_what_the_engine_ledger_declares_unpublished(facts, engine, builder):
    """The band's membership is not a judgement made in the builder. `run_golden_master_ledger.py`
    writes `not_published` into the artifact, and the figure draws that list."""
    drawn = [row["label"] for row in facts["hand_only"]]
    declared = [builder.HAND_ONLY_LABELS.get(key, key) for key in engine["not_published"]]
    assert drawn == declared
    assert set(engine["not_published"]) == {
        "commission",
        "spread",
        "borrow",
        "margin_interest",
        "dividend",
    }


def test_the_band_is_visibly_separated(page, facts):
    """Sunk ground and a brass rule across the table's width. A 'hand only' row that looked
    like the twenty above it would read as another comparison that happened to be blank."""
    sunk = [r for r in RECT.findall(page) if r[4] == "--sunk"]
    assert len(sunk) == 1, "expected exactly one banded region"
    x, y, w, h = (float(v) for v in sunk[0][:4])
    assert w > 700.0, "the band does not span the table"
    assert h >= 13.0 * len(facts["hand_only"]), "the band does not cover its own rows"
    rules = re.findall(r'<line [^>]*stroke="var\(--brass\)" stroke-width="([\d.]+)"', page)
    assert rules, "no brass rule marks the boundary"


# ----------------------------------------------------------------------------- the quoting


def test_the_figure_quotes_every_number_it_is_drawn_from(page, facts, builder):
    for group in facts["groups"]:
        for row, (_label, _hk, _ek, fmt) in zip(group["rows"], builder.PUBLISHED_ROWS):
            present(page, fmt.format(row["hand"]), f"bar {group['index']} {row['label']} (hand)")
            present(page, fmt.format(row["engine"]), f"bar {group['index']} {row['label']} (engine)")
    for row in facts["hand_only"]:
        present(page, f"{row['total']:,.10f}", f"the {row['label']} total")
    present(page, f"{facts['unpublished_total']:,.4f}", "the unpublished friction total")
    present(page, f"{facts['frictions_total']:,.4f}", "the friction total")
    present(page, f"{facts['worst']:.2e}", "the largest residual")


def test_the_figure_says_where_the_missing_rows_are_missing_from(page):
    """`engine/backtest.py:42-79` is the class that does not publish them. A figure that said
    only 'not published' would leave the reader to find out whether that is a limitation of
    the figure or of the instrument."""
    for phrase in ("hand only", "not published", "engine/backtest.py:42-79"):
        assert phrase in page, f"the figure does not say {phrase!r}"


def test_the_columns_are_left_aligned(page, builder):
    """svgkit's docstring forbids a right-aligned numeric column: the fallback font has no
    tabular figures, so an end-anchored column of numbers is a column of ragged left edges
    that the eye reads as misalignment. Every cell here is anchored start."""
    for _x, _y, anchor, _size, label in TEXT.findall(page):
        if re.fullmatch(r"-?[\d,]+\.\d+|-?[\d,]+", label):
            assert anchor == "start", f"{label!r} is anchored {anchor!r}"
    for name in ("label", "hand", "engine", "delta"):
        assert builder.COL_X[name] == pytest.approx(builder.COL_X[name])
    xs = [builder.COL_X[n] for n in ("label", "hand", "engine", "delta")]
    assert xs == sorted(xs) and min(b - a for a, b in zip(xs, xs[1:])) >= 100.0, (
        "a column is narrower than the worst-case 89-point run of '219,934.0000000000'"
    )
