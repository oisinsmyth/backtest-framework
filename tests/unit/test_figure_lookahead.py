"""What the look-ahead figure CLAIMS, pinned to the two D279 artifacts.

`test_figures.py` gates the mechanics every figure shares. This file gates the three things only
this figure asserts:

1. **The two artifacts are comparable at all.** Same 14 keys, same 30 fields per cell. A
   before/after row across two grids that had drifted would be pairing two different things.
2. **The control is real and is not a claim in prose.** The cells the ranking never selected come
   out of `json.load` equal as whole dicts. That set is RECOMPUTED here by dict equality and
   cross-checked against a second, independent derivation from the key naming -- never read from
   a list in the builder, which is the thing under test.
3. **The drawing does not move its own control.** Every control's two markers must sit at the
   same `y` AND the same `x`, with a zero-length connector between them. A figure whose drawing
   jitters the cells it says did not move is lying about the only thing that makes it evidence.

`_check_controls_coincide` is a function rather than an inline loop so that the last test can feed
it a deliberately broken page and watch it raise -- `CLAUDE.md`: a self-test that cannot fail is
worse than none. The break moves the coordinate the assertion READS, not the label next to it.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "figures" / "build_lookahead.py"
WITHDRAWN = REPO / "data" / "d279_concentrated_summary.WITHDRAWN_lookahead.json"
CORRECTED = REPO / "data" / "d279_concentrated_summary.json"
FIGURE = REPO / "docs" / "figures" / "lookahead-before-after.svg"

N_CELLS = 14
N_FIELDS = 30
SURVIVORS = ("S1_short|top25", "S1_short|top50")

TOKENS = re.compile(r"/\* TOKENS:START.*?TOKENS:END \*/.*?(?=\ntext\{)", re.S)
CIRCLE = re.compile(r'<circle cx="([\d.-]+)" cy="([\d.-]+)" r="([\d.]+)"')
LINE = re.compile(r'<line x1="([\d.-]+)" y1="([\d.-]+)" x2="([\d.-]+)" y2="([\d.-]+)"')
ROW_LABEL = re.compile(r'<text x="8\.0" y="([\d.-]+)" text-anchor="start"[^>]*>([^<]+)</text>')


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
def before():
    return json.loads(WITHDRAWN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def after():
    return json.loads(CORRECTED.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def page():
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def identical_cells(before: dict, after: dict) -> list[str]:
    """The cells that came out of the two runs equal as WHOLE dicts. Computed, never listed."""
    return sorted(k for k, cell in before["cells"].items() if after["cells"][k] == cell)


# ------------------------------------------------------------------------ the artifacts


def test_both_artifacts_carry_the_same_cells_and_the_same_schema(before, after):
    """Without this the rest of the file compares two grids and calls the difference a bug."""
    keys = sorted(before["cells"])
    assert keys == sorted(after["cells"])
    assert len(keys) == N_CELLS
    for key in keys:
        fields = sorted(before["cells"][key])
        assert fields == sorted(after["cells"][key]), f"{key} records different fields"
        assert len(fields) == N_FIELDS, f"{key} carries {len(fields)} fields, not {N_FIELDS}"


def test_the_cells_the_ranking_never_selected_are_bit_identical(before, after):
    """The figure's control, derived twice and asserted equal.

    First derivation: whole-cell dict equality between the two artifacts. Second: the key naming,
    where `top-N` is the ranked book and `all`/`rnd-N` are the two things the defective `top_n`
    never touched. If those two sets ever disagreed, either the fix reached further than the
    ranking or a ranked cell coincidentally reproduced, and the figure's argument would be gone.
    """
    identical = identical_cells(before, after)
    untouched = sorted(k for k in before["cells"] if not k.split("|")[1].startswith("top"))
    assert identical == untouched, (
        "the set of bit-identical cells is no longer exactly the set the ranking never selected"
    )
    assert len(identical) == 8, f"{len(identical)} control cells, not 8"
    assert len(before["cells"]) - len(identical) == 6


def test_exactly_the_two_recorded_survivors_stop_clearing(before, after):
    flipped = sorted(
        k
        for k, cell in before["cells"].items()
        if cell["clears_all"] and not after["cells"][k]["clears_all"]
    )
    assert flipped == sorted(SURVIVORS)
    assert sorted(before["survivors"]) == sorted(SURVIVORS)
    assert after["survivors"] == []
    assert not any(cell["clears_all"] for cell in after["cells"].values()), (
        "the corrected run records no surviving cell; the figure says so"
    )


def test_the_correction_removes_the_edge_and_never_adds_one(before, after):
    """The sign, which is the one thing in this figure that is easy to draw backwards.

    Three cells stood above +1.8 and all three end below zero. Nothing ends above zero, so no
    reading of the corrected grid supports the withdrawn claim.
    """
    field = "excess_sharpe"
    high = sorted(k for k, c in before["cells"].items() if c[field] > 1.8)
    assert high == ["S1_short|top10", "S1_short|top25", "S1_short|top50"]
    for key in high:
        assert after["cells"][key][field] < 0.0, f"{key} did not fall below zero"
    assert max(c[field] for c in after["cells"].values()) < 0.0, (
        "some corrected cell scores above zero; the figure claims none does"
    )


def test_the_floor_moved_too_so_the_control_claim_is_about_the_cells(before, after):
    """The two files are NOT identical outside the six ranked cells, and the figure must not be
    read as saying they are. `floor` is D228's best-of-14 over the whole grid, so the contaminated
    cells dragged it: -0.1651 becomes -0.1779. The claim drawn is per-cell, and this pins it."""
    assert before["floor"] != after["floor"]
    assert after["floor"] == pytest.approx(-0.17791714663047015)
    assert before["elapsed_s"] != after["elapsed_s"]


# ----------------------------------------------------------------------------- the facts


def test_every_delta_drawn_is_recomputed_from_the_artifacts(facts, before, after):
    field = "excess_sharpe"
    drawn = {row["key"]: row for row in facts["rows"]}
    assert sorted(drawn) == sorted(before["cells"])
    for key, row in drawn.items():
        b, a = before["cells"][key][field], after["cells"][key][field]
        assert row["before"] == b
        assert row["after"] == a
        assert row["delta"] == a - b
        assert row["identical"] == (before["cells"][key] == after["cells"][key])
        if row["identical"]:
            assert row["delta"] == 0.0, f"{key} is bit-identical but its delta is not exactly 0"


def test_the_facts_name_the_right_headline_and_the_right_nudge(facts):
    head = facts["headline"]
    assert head["key"] == "S1_short|top10"
    assert head["before"] == pytest.approx(2.343314165236262)
    assert head["after"] == pytest.approx(-0.6623516910788982)
    assert head["delta"] == pytest.approx(-3.0056658563151602)
    assert [r["key"] for r in facts["collapsed"]] == [
        "S1_short|top10",
        "S1_short|top25",
        "S1_short|top50",
    ]
    assert [r["key"] for r in facts["nudged"]] == [
        "S2_short|top10",
        "S2_short|top25",
        "S2_short|top50",
    ]
    assert facts["nudge_max"] == pytest.approx(0.0613, abs=5e-5)
    assert facts["flipped"] == sorted(SURVIVORS)


def test_the_figure_quotes_the_numbers_it_is_drawn_from(page, facts, builder, before, after):
    """Containment, re-formatted from the artifacts in the figure's own format spec.

    `esc` is applied because svgkit turns every space into `&#160;` -- comparing against the raw
    sentence would pass vacuously on a figure that had stopped drawing it.
    """
    esc = builder.k.esc
    field = "excess_sharpe"
    for key in sorted(before["cells"]):
        delta = after["cells"][key][field] - before["cells"][key][field]
        present(page, f"{delta:+.4f}", f"the change on {key}")
    head = facts["headline"]
    present(page, esc(f"{head['before']:+.4f} → {head['after']:+.4f}"), "the headline collapse")
    present(
        page,
        esc(
            f"{len(facts['controls'])} of {facts['n_cells']} cells are bit-identical in both "
            f"artifacts; {len(before['survivors'])} survivors became {len(after['survivors'])}"
        ),
        "the control count and the survivor count",
    )
    present(page, esc(f"the {len(before['survivors'])} recorded survivors"), "the survivor mark")
    present(
        page,
        esc(f"the other {len(facts['nudged'])} move by at most {facts['nudge_max']:.4f}"),
        "the S2 cells' much smaller move",
    )
    present(page, esc(f"above the rule: the {len(facts['changed'])} cells the score chose"), "A")
    present(
        page,
        esc(f"below the rule: the {len(facts['controls'])} cells the ranking never selected"),
        "B",
    )


# --------------------------------------------------------------------------- the drawing


def rows_from(page: str) -> dict[str, dict]:
    """`key -> {y, before_x, after_x, connector}`, read out of the emitted SVG.

    Anchored on each row's own label rather than on the builder's layout constants, so this reads
    the picture a reader sees instead of re-running the arithmetic under test. The legend circles
    sit above the first row and belong to no label, so they are never picked up.
    """
    body = TOKENS.sub("", page)
    circles = [(float(cx), float(cy), float(r)) for cx, cy, r in CIRCLE.findall(body)]
    lines = [tuple(float(v) for v in m) for m in LINE.findall(body)]

    out: dict[str, dict] = {}
    for y_text, key in ROW_LABEL.findall(body):
        if "|" not in key:
            continue  # a caption that happens to start at the label column
        yy = float(y_text) - 3.2
        mine = [c for c in circles if abs(c[1] - yy) < 0.05]
        assert len(mine) == 2, f"{key} is drawn with {len(mine)} markers, not 2"
        big = [c for c in mine if c[2] > 4.0]
        small = [c for c in mine if c[2] < 4.0]
        assert len(big) == 1 and len(small) == 1, f"{key}: cannot tell before from after"
        connectors = [ln for ln in lines if abs(ln[1] - yy) < 0.05 and abs(ln[3] - yy) < 0.05]
        assert len(connectors) == 1, f"{key} has {len(connectors)} connectors, not 1"
        out[key] = {
            "y": yy,
            "before": big[0],
            "after": small[0],
            "connector": connectors[0],
        }
    return out


def _check_controls_coincide(rows: dict[str, dict], controls: list[str]) -> None:
    """Raise if any control cell's two markers are not the same point.

    THE ASSERTION THE WHOLE FIGURE RESTS ON. If the drawing separates a control's before and
    after by so much as a rounded tenth of a pixel, the picture shows movement in a cell that did
    not move, and a reader would take that as the fix having reached the control.
    """
    for key in controls:
        row = rows[key]
        bx, by, _ = row["before"]
        ax, ay, _ = row["after"]
        assert by == ay == row["y"], (
            f"{key} is bit-identical in both artifacts but is drawn at y={by} in one column and "
            f"y={ay} in the other"
        )
        assert bx == ax, (
            f"{key} is bit-identical in both artifacts but is drawn at x={bx} in one column and "
            f"x={ax} in the other — the figure would show it moving by "
            f"{abs(ax - bx):.1f}px"
        )
        x1, _, x2, _ = row["connector"]
        assert x1 == x2, f"{key}'s connector spans {abs(x2 - x1):.1f}px; it must be degenerate"


def test_the_controls_are_drawn_at_identical_positions_in_both_columns(page, before, after):
    rows = rows_from(page)
    assert sorted(rows) == sorted(before["cells"]), "the figure does not draw all 14 cells"
    _check_controls_coincide(rows, identical_cells(before, after))


def test_each_changed_cell_is_drawn_moving_the_way_the_artifacts_say(page, facts):
    """Direction, in pixels. A dumbbell drawn the wrong way round would still pass every
    containment check above, because the numbers in the change column would be unaffected."""
    rows = rows_from(page)
    for row in facts["changed"]:
        drawn = rows[row["key"]]
        shift = drawn["after"][0] - drawn["before"][0]
        assert shift != 0.0, f"{row['key']} moved by {row['delta']:+.4f} and is drawn flat"
        assert (shift > 0) == (row["delta"] > 0), (
            f"{row['key']} changed by {row['delta']:+.4f} but is drawn moving "
            f"{'right' if shift > 0 else 'left'}"
        )


def test_the_value_axis_is_monotone_across_all_fourteen_rows(page, facts):
    """The rows are ordered by block, not by value, so nothing else here would notice an axis
    that had been built from the wrong scale."""
    rows = rows_from(page)
    by_value = sorted(facts["rows"], key=lambda r: r["before"])
    xs = [rows[r["key"]]["before"][0] for r in by_value]
    assert xs == sorted(xs), "the drawn positions do not follow the values they encode"


def test_the_survivor_band_covers_the_two_survivor_rows_and_no_others(page, facts):
    """The mark has to name the two cells, not a neighbourhood of them."""
    body = TOKENS.sub("", page)
    bands = [
        (float(y), float(y) + float(h))
        for y, h in re.findall(
            r'<rect x="[\d.-]+" y="([\d.-]+)" width="[\d.-]+" height="([\d.-]+)" '
            r'fill="var\(--brass-soft\)"',
            body,
        )
    ]
    assert bands, "the survivor rows carry no highlight"
    rows = rows_from(page)
    inside = sorted(k for k, r in rows.items() if any(lo <= r["y"] <= hi for lo, hi in bands))
    assert inside == sorted(SURVIVORS)


def test_the_coincidence_check_fires_when_a_control_is_moved(page, before, after):
    """The planted break. `_check_controls_coincide` reading a page that is fine proves nothing
    about whether it can fail, and the break moves the COORDINATE the assertion reads rather than
    the cell's label, which is the dud this repository has shipped three times.
    """
    controls = identical_cells(before, after)
    victim = controls[0]
    row = rows_from(page)[victim]
    cx, cy, r = row["after"]
    original = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}"'
    broken = page.replace(original, f'<circle cx="{cx + 6:.1f}" cy="{cy:.1f}" r="{r}"', 1)
    assert broken != page, f"the planted break did not match anything ({original!r})"

    with pytest.raises(AssertionError, match="bit-identical in both artifacts"):
        _check_controls_coincide(rows_from(broken), controls)
