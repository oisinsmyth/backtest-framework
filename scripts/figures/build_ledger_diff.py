"""Figure: the hand ledger against the engine, line by line, with the gap drawn.

    python scripts/figures/build_ledger_diff.py --print
    python scripts/figures/build_all.py --build

WHAT IT SHOWS
-------------
Two independent accounts of the same five bars. `tests/golden/test_the_golden_master.hand.json`
is arithmetic done by hand and recomputed from first principles by the golden test;
`data/golden_master_ledger.json` is what `BacktestResult` actually published when the engine
ran the same scenario. Every published quantity agrees to the ten decimal places the hand file
is written to.

THE DIFFERENCE COLUMN SHOWS DIGITS, NOT A TICK
-----------------------------------------------
`0.0000000000` is a measurement. A checkmark is a claim, and a claim is exactly what a reader
cannot check — it says "somebody compared these" without saying what the comparison returned
or at what precision. So the column carries the subtraction, and the subtraction is done at
build time on the two artifacts rather than asserted anywhere in prose.

THE INTERESTING PART IS THE BAND AT THE BOTTOM
-----------------------------------------------
Five rows have no engine column at all. `BacktestResult`
(src/backtest_framework/engine/backtest.py:42-79) publishes a fill's cost as ONE number, so
commission and spread are summed before anything can read them; carry accruals and event
flows are applied to `PortfolioState` and recorded nowhere. Borrow, margin interest and the
dividend — 678.82 of the 817.35 this scenario pays — are therefore invisible to any consumer
of a backtest result, and the only reason they are checkable at all is that a human worked
them out in `test_the_golden_master.hand.txt`.

A figure that showed only the agreeing rows would be a figure about a passing test. This one
is about what the instrument does not measure.

IT IS A TABLE, SO IT IS THE FIGURE MOST AT RISK FROM THE FALLBACK FONT
-----------------------------------------------------------------------
See svgkit's docstring: the face that renders is wider than the one asked for. Every column is
LEFT-aligned with ~100 points of slack against an 89-point worst-case run
(`219,934.0000000000` at 18 characters), because a right-aligned numeric column assumes
tabular figures that a substituted font does not have.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import svgkit as k  # noqa: E402

SLUG = "golden-master-ledger-diff"
HAND_SOURCE = "tests/golden/test_the_golden_master.hand.json"
ENGINE_SOURCE = "data/golden_master_ledger.json"
SOURCE = f"{HAND_SOURCE} + {ENGINE_SOURCE}"
GENERATOR = "scripts/figures/build_ledger_diff.py"

# Left edges, not centres: every cell is anchored "start". The test reads these to find the
# difference column, so the column the assertion checks is the column the figure draws.
COL_X = {"label": 46.0, "hand": 246.0, "engine": 446.0, "delta": 656.0}

ROW_H = 13.0
GROUP_GAP = 7.0

# The column titles and the rule beneath them. Named because a title sits at the same x as the
# cells it titles, so the gate has to separate the two by POSITION — separating them by content
# would also skip a checkmark, which is the one thing the difference column must never hold.
HEADER_Y = 80.0
HEADER_RULE_Y = 86.0

# The rows the engine does publish, as (label, hand key, engine key, format).
PUBLISHED_ROWS = (
    ("fill qty", "delta", "fill_qty", "{:,.0f}"),
    ("trade cost", "trade_cost", "trade_cost", "{:,.10f}"),
    ("cash", "cash", "cash", "{:,.10f}"),
    ("NAV", "nav", "nav", "{:,.10f}"),
)

# The rows it does not. Order follows the cost stack, not size.
HAND_ONLY_ROWS = ("commission", "spread", "borrow", "margin_interest", "dividend")
HAND_ONLY_LABELS = {"margin_interest": "margin interest"}

NO_VALUE = "—"  # an em dash: there is no engine number, so there is no difference either


def difference(value: float) -> str:
    """The subtraction at ten places, with a rounding artefact's sign removed.

    A residual of -2.9e-11 formats as `-0.0000000000`, which reads as a signed quantity and is
    not one: it is zero at the stated precision. The magnitude is asserted numerically by
    tests/unit/test_figure_ledger_diff.py, which is where a real disagreement would surface.
    """
    text = f"{value:,.10f}"
    if text.startswith("-") and float(text[1:].replace(",", "")) == 0.0:
        return text[1:]
    return text


def facts() -> dict:
    """Both ledgers, joined bar by bar, with every difference computed here."""
    hand = json.loads((k.REPO / HAND_SOURCE).read_text(encoding="utf-8"))
    engine = json.loads((k.REPO / ENGINE_SOURCE).read_text(encoding="utf-8"))
    hand_bars, engine_bars = hand["bars"], engine["bars"]
    if len(hand_bars) != len(engine_bars):  # pragma: no cover - one scenario, one length
        raise SystemExit("the two ledgers disagree on the number of bars")

    groups = []
    for hand_bar, engine_bar in zip(hand_bars, engine_bars):
        if hand_bar["timestamp"] != engine_bar["timestamp"]:  # pragma: no cover
            raise SystemExit(f"bar {hand_bar['index']}: the two ledgers are not aligned")
        rows = []
        for label, hand_key, engine_key, fmt in PUBLISHED_ROWS:
            hand_value = float(hand_bar[hand_key])
            engine_value = float(engine_bar[engine_key])
            rows.append(
                {
                    "label": label,
                    "hand": hand_value,
                    "engine": engine_value,
                    "delta": hand_value - engine_value,
                    "fmt": fmt,
                }
            )
        groups.append(
            {
                "index": hand_bar["index"],
                "date": hand_bar["timestamp"].split("T")[0],
                "price": hand_bar["price"],
                "traded": hand_bar["delta"] != 0.0,
                "rows": rows,
            }
        )

    hand_only = [
        {
            "label": HAND_ONLY_LABELS.get(key, key),
            "total": sum(bar[key] for bar in hand_bars),
        }
        for key in HAND_ONLY_ROWS
    ]

    # As MAGNITUDES of friction. The ledger signs a dividend debit negative (it is a cash
    # outflow) and a commission positive (it is a cost), so summing the column as it stands
    # nets the dividend against the accruals and understates the total by 2x the accruals.
    def friction(bar: dict, keys: tuple[str, ...]) -> float:
        return sum(abs(bar[key]) for key in keys)

    unpublished = sum(friction(b, ("borrow", "margin_interest", "dividend")) for b in hand_bars)
    published_as_one = sum(friction(b, ("commission", "spread")) for b in hand_bars)

    return {
        "groups": groups,
        "hand_only": hand_only,
        "worst": max(abs(row["delta"]) for group in groups for row in group["rows"]),
        "unpublished_total": unpublished,
        "frictions_total": unpublished + published_as_one,
        "final_nav": hand["final_nav"],
        "not_published": engine["not_published"],
    }


def render(theme: k.Theme) -> str:
    f = facts()
    # Tall on purpose: 25 rows at 13 points with the band and its note below them. The height
    # is the content's, not a chosen aspect ratio — a table squeezed into 440 would collide
    # with the footer, which is exactly what it did on the first build.
    frame = k.Frame(width=900.0, height=624.0, left=46.0, right=20.0, top=96.0, bottom=44.0)

    body: list[str] = []
    add = body.append

    add(
        k.text(
            COL_X["label"] - 2,
            24,
            "Two independent accounts of the same five bars, and the five rows only one of "
            "them has",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            COL_X["label"] - 2,
            39,
            "Hand arithmetic against what BacktestResult published. The difference column is "
            "the subtraction, not a verdict.",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )
    add(
        k.text(
            COL_X["label"] - 2,
            53,
            f"Largest disagreement anywhere in the published rows: {f['worst']:.2e} — the hand "
            f"file is written to ten places and the engine agrees to all of them.",
            size=8.0,
            fill="--muted",
            track=0.03,
        )
    )

    headers = (
        ("label", "bar / quantity"),
        ("hand", "hand ledger"),
        ("engine", "engine (BacktestResult)"),
        ("delta", "difference, hand - engine"),
    )
    for column, title in headers:
        add(
            k.text(
                COL_X[column],
                HEADER_Y,
                title,
                size=8.0,
                fill="--faint",
                track=0.08,
                weight=600,
            )
        )
    add(k.line(COL_X["label"], HEADER_RULE_Y, frame.x1, HEADER_RULE_Y, stroke="--rule", w=1.2))

    row_y = frame.y0 + 4.0
    for group in f["groups"]:
        note = "" if group["traded"] else " · no fill on either side"
        add(
            k.text(
                COL_X["label"],
                row_y,
                f"bar {group['index']} · {group['date']} · close {group['price']:,.2f}{note}",
                size=8.5,
                fill="--ink",
                track=0.04,
                weight=600,
            )
        )
        row_y += ROW_H
        for row in group["rows"]:
            add(k.text(COL_X["label"] + 10, row_y, row["label"], size=8.0, fill="--muted", track=0.03))
            add(
                k.text(
                    COL_X["hand"],
                    row_y,
                    row["fmt"].format(row["hand"]),
                    size=8.0,
                    fill="--ink",
                    track=0.02,
                    family="--mono",
                )
            )
            add(
                k.text(
                    COL_X["engine"],
                    row_y,
                    row["fmt"].format(row["engine"]),
                    size=8.0,
                    fill="--ink",
                    track=0.02,
                    family="--mono",
                )
            )
            add(
                k.text(
                    COL_X["delta"],
                    row_y,
                    difference(row["delta"]),
                    size=8.0,
                    fill="--slate",
                    track=0.02,
                    family="--mono",
                )
            )
            row_y += ROW_H
        row_y += GROUP_GAP

    # The band. Sunk ground, its own rule and an indent, because "the engine has no column
    # here" is a different kind of row and must not read as another comparison.
    band_top = row_y + 4.0
    band_height = ROW_H * (len(f["hand_only"]) + 2) + 6.0
    add(k.rect(COL_X["label"] - 8, band_top, frame.x1 - COL_X["label"] + 8, band_height, fill="--sunk"))
    add(k.line(COL_X["label"] - 8, band_top, frame.x1, band_top, stroke="--brass", w=1.4))

    row_y = band_top + ROW_H
    add(
        k.text(
            COL_X["label"],
            row_y,
            "hand only - the engine records none of these (engine/backtest.py:42-79)",
            size=8.5,
            fill="--brass",
            track=0.04,
            weight=600,
        )
    )
    add(
        k.text(
            COL_X["engine"],
            row_y,
            "totals across the five bars",
            size=8.0,
            fill="--faint",
            track=0.03,
        )
    )
    row_y += ROW_H
    for row in f["hand_only"]:
        add(k.text(COL_X["label"] + 10, row_y, row["label"], size=8.0, fill="--muted", track=0.03))
        add(
            k.text(
                COL_X["hand"],
                row_y,
                f"{row['total']:,.10f}",
                size=8.0,
                fill="--ink",
                track=0.02,
                family="--mono",
            )
        )
        add(k.text(COL_X["engine"], row_y, "not published", size=8.0, fill="--faint", track=0.03))
        add(k.text(COL_X["delta"], row_y, NO_VALUE, size=8.0, fill="--faint", track=None, family="--mono"))
        row_y += ROW_H

    add(
        k.text(
            COL_X["label"],
            row_y + 10,
            f"{f['unpublished_total']:,.4f} of the {f['frictions_total']:,.4f} this scenario "
            "pays in frictions is invisible to any consumer of a backtest result.",
            size=8.0,
            fill="--muted",
            track=0.02,
        )
    )

    return k.document(
        frame=frame,
        slug=SLUG,
        title="The hand ledger and the engine's own ledger, bar by bar",
        desc=(
            "A table of five bars. For each bar the hand-computed fill quantity, trade cost, cash "
            "and NAV are set beside the values BacktestResult published, with the difference "
            f"shown to ten decimal places; every difference is 0.0000000000 (largest residual "
            f"{f['worst']:.2e}). A separated band at the foot lists commission, spread, borrow, "
            "margin interest and the dividend, which the engine does not publish at all and which "
            "therefore have no column to be compared against."
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
        for group in f["groups"]:
            print(f"bar {group['index']}  {group['date']}")
            for row in group["rows"]:
                print(
                    f"  {row['label']:<11} {row['hand']:>20,.10f} {row['engine']:>20,.10f} "
                    f"{difference(row['delta']):>18}"
                )
        print("hand only:")
        for row in f["hand_only"]:
            print(f"  {row['label']:<16} {row['total']:>20,.10f}")
        print(f"worst residual {f['worst']:.3e}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
