"""Figure: the look-ahead guard firing on D279's concentrated short.

    python scripts/figures/build_lookahead.py --print
    python scripts/figures/build_lookahead.py --facts

WHAT IT SHOWS, AND WHY IT IS DRAWN FROM TWO ARTIFACTS RATHER THAN ONE
---------------------------------------------------------------------
D279 ran a concentrated short book over 14 cells. `top_n` ranked the qualifying names on
`score[q, t]` -- the close of the very bar the position was about to be paid for -- so **which
names QUALIFIED was honest and which N of them were HELD was not**. The base book was correctly
lagged, which is what hid it: filtering an already-lagged book feels like it cannot introduce a
lag error. `docs/decisions/D279-...md` records the mechanism; this draws the damage.

The contaminated run was withdrawn in full and KEPT rather than deleted, as
`data/d279_concentrated_summary.WITHDRAWN_lookahead.json`. Because both files survive with the
same 14 keys and the same 30 fields, the before/after is a fact on disk rather than a
reconstruction -- which is the only reason this figure can be drawn at all.

THE CONTROLS ARE THE ARGUMENT, NOT THE COLLAPSE
-----------------------------------------------
A figure showing only three cells falling across zero shows a number changing. It does not show
that the change is the BUG rather than the re-run. The eight cells the ranking never selected --
the two unconcentrated bases and the six `rnd-N` draws -- come out of `json.load` **equal as
dicts, all 30 fields**, so every one of them is drawn as a zero-length dumbbell and prints
`+0.0000` in the change column. That is the built-in control: the fix touched exactly the code
path the ranking ran through, and nothing else in the grid moved by one ULP.

`tests/unit/test_figure_lookahead.py` recomputes the identical set from the two artifacts rather
than reading a list from here, and asserts the eight are drawn at the SAME y and the SAME x in
both columns -- because a drawing that jitters its own control is a figure that lies about it.

THE SIGN IS THE POINT AND IT IS EASY TO GET BACKWARDS
------------------------------------------------------
The correction REMOVES the edge. `S1_short|top10` goes +2.3433 -> -0.6624, and the two cells the
withdrawn run recorded as survivors -- `S1_short|top25` and `S1_short|top50` -- flip `clears_all`
True -> False, emptying the survivor list. Nothing here improved.

The three S2 cells moved too, by at most 0.0613, and they are drawn at the same scale rather than
on a broken axis: the arm that had no apparent edge had almost nothing to lose.

WHY A DUMBBELL AND NOT A TWO-COLUMN SLOPE
------------------------------------------
On a shared value axis the 14 labels collide -- `S2_short|top25` and `S2_short|top50` are 0.0103
apart, about one pixel at this height, and svgkit's docstring forbids anything whose meaning
depends on two labels not colliding. A row per cell gives every key its own lane, and the value
axis runs horizontally, so `x` is the coordinate that carries the number and the coincidence of
a control's two markers is visible as one dot with no line between them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import svgkit as k  # noqa: E402

SLUG = "lookahead-before-after"
WITHDRAWN = "data/d279_concentrated_summary.WITHDRAWN_lookahead.json"
CORRECTED = "data/d279_concentrated_summary.json"
SOURCE = f"{WITHDRAWN}, {CORRECTED}"
GENERATOR = "scripts/figures/build_lookahead.py"

FIELD = "excess_sharpe"
X_LO, X_HI = -1.90, 2.45
X_TICKS = (-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5, 2.0)

# One lane per cell. 24px is the smallest pitch at which a 9px key and a 4.2px marker radius
# leave daylight between neighbouring rows at the wide fallback font.
ROW_PITCH = 24.0
FIRST_ROW_DY = 14.0
SEPARATOR_DY = 22.0
BLOCK_GAP = 28.0


def facts() -> dict:
    """Everything drawn, computed once so the test can recompute it the same way.

    Raises rather than drawing a comparison that is not one: if the two runs stopped agreeing on
    which cells exist, or on what a cell records, a before/after row would be pairing two
    different things and the picture would not say so.
    """
    before = json.loads((k.REPO / WITHDRAWN).read_text(encoding="utf-8"))
    after = json.loads((k.REPO / CORRECTED).read_text(encoding="utf-8"))

    keys = sorted(before["cells"])
    if keys != sorted(after["cells"]):
        raise SystemExit(
            f"{WITHDRAWN} and {CORRECTED} do not carry the same cells; a before/after row would "
            "be pairing two different things."
        )

    rows: list[dict] = []
    for key in keys:
        b, a = before["cells"][key], after["cells"][key]
        if sorted(b) != sorted(a):
            raise SystemExit(f"cell {key} records different fields in the two runs")
        rows.append(
            {
                "key": key,
                "before": b[FIELD],
                "after": a[FIELD],
                "delta": a[FIELD] - b[FIELD],
                # Bit-identical as a WHOLE CELL, not just on the field drawn. A cell whose
                # excess_sharpe matched while its drawdown moved is not a control.
                "identical": b == a,
                "survivor": key in before["survivors"],
                "clears_before": b["clears_all"],
                "clears_after": a["clears_all"],
            }
        )

    changed = [r for r in rows if not r["identical"]]
    controls = [r for r in rows if r["identical"]]
    collapsed = [r for r in changed if r["delta"] < 0]
    nudged = [r for r in changed if r["delta"] > 0]

    return {
        "rows": rows,
        "changed": changed,
        "controls": controls,
        "collapsed": collapsed,
        "nudged": nudged,
        "n_cells": len(rows),
        "schema": sorted(before["cells"][keys[0]]),
        "survivors_before": list(before["survivors"]),
        "survivors_after": list(after["survivors"]),
        # Computed, never read from `survivors`: the flip is the claim, the list is the record.
        "flipped": [r["key"] for r in rows if r["clears_before"] and not r["clears_after"]],
        "headline": max(changed, key=lambda r: abs(r["delta"])),
        "nudge_max": max(abs(r["delta"]) for r in nudged),
        "floor_before": before["floor"],
        "floor_after": after["floor"],
    }


def _layout(f: dict, frame: k.Frame) -> tuple[list[float], float, list[float]]:
    """Row baselines for the changed block, the separator, and the control block."""
    top = [frame.y0 + FIRST_ROW_DY + i * ROW_PITCH for i in range(len(f["changed"]))]
    separator = top[-1] + SEPARATOR_DY
    bottom = [separator + BLOCK_GAP + j * ROW_PITCH for j in range(len(f["controls"]))]
    return top, separator, bottom


def render(theme: k.Theme) -> str:
    f = facts()
    frame = k.Frame(width=880.0, height=520.0, left=132.0, right=96.0, top=82.0, bottom=56.0)
    x = k.linear(X_LO, X_HI, frame.x0, frame.x1)
    top_y, sep_y, bottom_y = _layout(f, frame)
    change_x = frame.x1 + 10.0

    body: list[str] = []
    add = body.append

    # ------------------------------------------------------------------ the header
    add(
        k.text(
            8,
            22,
            "A look-ahead guard fires: the selected cells collapse, the controls do not move",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            8,
            38,
            "D279 concentrated short — excess Sharpe against the matched-count rotation null, "
            f"{f['n_cells']} cells, {len(f['schema'])} fields each",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )
    add(
        k.text(
            8,
            58,
            f"{len(f['controls'])} of {f['n_cells']} cells are bit-identical in both artifacts; "
            f"{len(f['survivors_before'])} survivors became {len(f['survivors_after'])}",
            size=8.5,
            fill="--ink",
            track=0.03,
            weight=600,
        )
    )
    add(k.circle(470, 55, 4.2, fill="--paper", stroke="--slate", sw=1.8))
    add(k.text(480, 58, "withdrawn (look-ahead)", size=8.0, fill="--muted", track=0.03))
    add(k.circle(610, 55, 3.4, fill="--brass"))
    add(k.text(620, 58, "corrected", size=8.0, fill="--muted", track=0.03))

    # ------------------------------------------------------- the two blocks, as ground
    # One band per CONTIGUOUS run of survivor rows. Banding each row separately left a 2px seam
    # between the two, which read as two unrelated highlights rather than one marked pair.
    run: list[float] = []
    for row, yy in list(zip(f["changed"], top_y)) + [(None, None)]:
        if row is not None and row["survivor"]:
            run.append(yy)
            continue
        if run:
            add(
                k.rect(
                    frame.x0,
                    run[0] - 11,
                    frame.span_x,
                    (run[-1] + 11) - (run[0] - 11),
                    fill="--brass-soft",
                    opacity=0.6,
                )
            )
            run = []
    add(
        k.rect(
            frame.x0,
            sep_y + 14,
            frame.span_x,
            (bottom_y[-1] + 12) - (sep_y + 14),
            fill="--sunk",
            opacity=0.75,
        )
    )

    # ------------------------------------------------------------------- the axis
    for v in X_TICKS:
        px = x.to(v)
        if v != 0.0:
            add(k.line(px, frame.y0, px, frame.y1, stroke="--rule"))
        add(k.line(px, frame.y1, px, frame.y1 + 4, stroke="--rule"))
        add(k.text(px, frame.y1 + 15, f"{v:.1f}", anchor="middle", fill="--faint", track=None))
    add(k.rule_at(frame, x, 0.0, "excess Sharpe = 0", stroke="--brass"))
    add(
        k.text(
            frame.x1,
            frame.y1 + 30,
            "excess Sharpe over the matched-count rotation null",
            anchor="end",
            size=8.0,
            fill="--faint",
            track=0.08,
        )
    )
    add(
        k.text(
            frame.x0,
            frame.y0 - 6,
            f"above the rule: the {len(f['changed'])} cells the score chose",
            size=8.0,
            fill="--muted",
            track=0.04,
        )
    )
    add(k.text(change_x, frame.y0 - 6, "change", size=8.0, fill="--faint", track=0.04))

    # ------------------------------------------------------------------- the rows
    for row, yy in zip(f["changed"] + f["controls"], top_y + bottom_y):
        xb, xa = x.to(row["before"]), x.to(row["after"])
        moved = not row["identical"]
        # Drawn for a control too, and it is degenerate: x1 == x2 renders nothing, which is the
        # honest way to say the two runs put this cell in exactly the same place.
        add(k.line(xb, yy, xa, yy, stroke="--brass" if moved else "--rule", w=2.2))
        add(k.circle(xb, yy, 4.2, fill="--paper", stroke="--slate", sw=1.8))
        add(k.circle(xa, yy, 3.4, fill="--brass" if moved else "--slate"))
        add(
            k.text(
                8,
                yy + 3.2,
                row["key"],
                size=9.0,
                fill="--ink" if moved else "--muted",
                track=0.02,
            )
        )
        add(
            k.text(
                change_x,
                yy + 3.2,
                f"{row['delta']:+.4f}",
                size=8.5,
                fill="--brass" if moved else "--faint",
                track=0.02,
            )
        )

    # ------------------------------------------------------------- the annotations
    head = f["headline"]
    head_y = top_y[f["changed"].index(head)]
    add(
        k.text(
            (x.to(head["before"]) + x.to(head["after"])) / 2,
            head_y - 8,
            f"{head['before']:+.4f} → {head['after']:+.4f}",
            anchor="middle",
            size=8.5,
            fill="--brass",
            track=0.03,
            weight=600,
        )
    )

    marks = [(r, yy) for r, yy in zip(f["changed"], top_y) if r["survivor"]]
    bracket_x = min(x.to(r["after"]) for r, _ in marks) - 14
    add(k.line(bracket_x, marks[0][1] - 11, bracket_x, marks[-1][1] + 11, stroke="--brass", w=1.6))
    add(
        k.text(
            bracket_x - 6,
            (marks[0][1] + marks[-1][1]) / 2 + 3.2,
            f"the {len(marks)} recorded survivors",
            anchor="end",
            size=8.0,
            fill="--ink",
            track=0.03,
            weight=600,
        )
    )

    # Started 25px LEFT of the zero rule, which put the dashed rule through its second word and
    # read as an accident. Placed clear of the rule instead; the three dots it names are the only
    # thing on these rows, so the association survives the gap.
    nudge_y = top_y[f["changed"].index(f["nudged"][0])] + ROW_PITCH / 2
    add(
        k.text(
            x.to(0.0) + 14,
            nudge_y + 3.2,
            f"the other {len(f['nudged'])} move by at most {f['nudge_max']:.4f}",
            size=8.0,
            fill="--muted",
            track=0.03,
        )
    )

    add(k.line(frame.x0, sep_y, frame.x1, sep_y, stroke="--rule", w=1.0))
    add(
        k.text(
            frame.x0,
            sep_y + 13,
            f"below the rule: the {len(f['controls'])} cells the ranking never selected, "
            "bit-identical in both artifacts",
            size=8.0,
            fill="--muted",
            track=0.04,
        )
    )

    return k.document(
        frame=frame,
        slug=SLUG,
        title="A look-ahead fix removes the edge it appeared to find, and leaves the controls alone",
        desc=(
            f"A dumbbell chart of {f['n_cells']} D279 cells, one row each, showing excess Sharpe "
            f"before and after a look-ahead fix. {head['key']} falls from {head['before']:+.4f} "
            f"to {head['after']:+.4f}. The {len(f['survivors_before'])} cells recorded as "
            f"survivors stop clearing, leaving {len(f['survivors_after'])}. The "
            f"{len(f['controls'])} cells the ranking never selected are bit-identical in both "
            "runs and are drawn as a single point with no connecting line."
        ),
        source=SOURCE,
        generator=GENERATOR,
        body="\n".join(body),
        theme=theme,
    )


def files() -> dict[Path, str]:
    return k.write(SLUG, render)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    ap.add_argument("--facts", action="store_true", help="the numbers, without the drawing")
    args = ap.parse_args()
    if args.to_stdout:
        sys.stdout.write(render("light"))
        return 0
    if args.facts:
        f = facts()
        for row in f["rows"]:
            flag = "identical" if row["identical"] else "CHANGED"
            star = " survivor" if row["survivor"] else ""
            print(
                f"{row['key']:16s} {row['before']:+.4f} -> {row['after']:+.4f} "
                f"({row['delta']:+.4f}) {flag}{star}"
            )
        print(
            f"cells={f['n_cells']} fields={len(f['schema'])} identical={len(f['controls'])} "
            f"survivors={len(f['survivors_before'])}->{len(f['survivors_after'])} "
            f"flipped={f['flipped']} floor={f['floor_before']:.4f}->{f['floor_after']:.4f}"
        )
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
