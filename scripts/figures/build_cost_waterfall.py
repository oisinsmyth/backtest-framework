"""Figure: where the golden master's 100,000 goes, brick by brick.

    python scripts/figures/build_cost_waterfall.py --print
    python scripts/figures/build_all.py --build

WHAT IT SHOWS
-------------
The 5-bar golden-master scenario is a 120% short that ends +149.65 on 100,000. That single
number is the least interesting thing about it. Underneath: the price moved 967.00 in the
position's favour, and five frictions took 817.35 of it back. The largest by a distance is
the DIVIDEND the short owes its lender — 626.50, which is 4.5x the commission and the spread
put together. A reader who only ever sees the net figure would guess the opposite.

THE DECOMPOSITION EXISTS ONLY IN THE HAND LEDGER, AND THE FIGURE SAYS SO
------------------------------------------------------------------------
`BacktestResult` (src/backtest_framework/engine/backtest.py:42-79) publishes a fill's cost as
ONE number — commission and spread already summed — and publishes carry accruals and event
flows not at all. So four of the six bars here cannot be drawn from anything the engine
reports. They come from `tests/golden/test_the_golden_master.hand.json`, transcribed by hand
from the .hand.txt and recomputed from first principles by
`tests/golden/test_the_golden_master.py` on every run.

That is a genuine finding about the instrument rather than a caveat, so it is printed on the
figure. The companion figure `golden-master-ledger-diff` draws the same gap as a table.

THE AXIS DOES NOT START AT ZERO, WHICH IS STATED ON IT
-------------------------------------------------------
The whole story lives in the top 1% of the capital: 99,900 to 101,050 on a book of 100,000.
A zero-based axis would render every friction as the same invisible sliver. The range is
therefore chosen, printed in the axis label, and the two anchor bars are drawn to the axis
floor rather than floating, so the truncation is visible rather than implied.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import svgkit as k  # noqa: E402

SLUG = "cost-waterfall"
SOURCE = "tests/golden/test_the_golden_master.hand.json"
GENERATOR = "scripts/figures/build_cost_waterfall.py"

Y_LO, Y_HI = 99_900.0, 101_050.0
Y_TICKS = (100_000.0, 100_250.0, 100_500.0, 100_750.0, 101_000.0)

# Credit is brass, debit is slate. The palette has no red and no green (svgkit.COLOURS), and
# inventing one would raise — which is the intended constraint, not a limitation worked around.
CREDIT, DEBIT, ANCHOR = "--brass", "--slate", "--sunk"


def facts() -> dict:
    """Every quantity drawn, computed once so the test can recompute it the same way."""
    hand = json.loads((k.REPO / SOURCE).read_text(encoding="utf-8"))
    bars = hand["bars"]
    start = hand["scenario"]["starting_cash"]

    # Price P&L on a position whose size changes every bar: each bar's held quantity marked
    # from this close to the next. The short is negative, so a falling price is a credit.
    price_pnl = sum(
        bar["qty_after"] * (nxt["price"] - bar["price"]) for bar, nxt in zip(bars, bars[1:])
    )
    steps = [
        ("price P&L", price_pnl),
        ("commission", -sum(b["commission"] for b in bars)),
        ("spread", -sum(b["spread"] for b in bars)),
        ("borrow", -sum(b["borrow"] for b in bars)),
        ("margin interest", -sum(b["margin_interest"] for b in bars)),
        ("dividend", sum(b["dividend"] for b in bars)),  # already signed in the ledger
    ]

    running = [start]
    for _label, value in steps:
        running.append(running[-1] + value)

    return {
        "start": start,
        "steps": steps,
        "running": running,
        "final": hand["final_nav"],
        "net": hand["final_nav"] - start,
        "frictions": -sum(value for _label, value in steps[1:]),
        "published_as_one_number": -(steps[1][1] + steps[2][1]),
        "unpublished": -(steps[3][1] + steps[4][1] + steps[5][1]),
    }


def money(value: float) -> str:
    return f"{value:,.4f}"


def signed(value: float) -> str:
    return f"+{money(value)}" if value > 0 else money(value)


def render(theme: k.Theme) -> str:
    f = facts()
    frame = k.Frame(width=900.0, height=470.0, left=78.0, right=20.0, top=72.0, bottom=100.0)
    y = k.linear(Y_LO, Y_HI, frame.y1, frame.y0)

    columns = 2 + len(f["steps"])
    col_w = frame.span_x / columns
    bar_w = col_w * 0.5

    body: list[str] = []
    add = body.append

    add(
        k.text(
            frame.x0 - 2,
            24,
            "The golden master's 100,000, brick by brick — and the dividend nobody looks at",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            frame.x0 - 2,
            39,
            f"5 bars, 120% short. Price P&L {signed(f['steps'][0][1])}; frictions "
            f"{money(f['frictions'])}; net {signed(f['net'])} to a final NAV of "
            f"{f['final']:,.10f}",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )
    add(
        k.text(
            frame.x0 - 2,
            53,
            "brass is a credit, slate a debit — the palette has no red and no green, and a "
            "figure here cannot invent one",
            size=8.0,
            fill="--muted",
            track=0.03,
        )
    )

    add(k.gridlines(frame, y, Y_TICKS, fmt=lambda v: f"{v:,.0f}"))
    add(k.line(frame.x0, frame.y1, frame.x1, frame.y1, stroke="--rule", w=1.4))

    def centre(index: int) -> float:
        return frame.x0 + (index + 0.5) * col_w

    # The two anchors are drawn to the axis floor: a floating anchor would hide the fact
    # that the axis is truncated, which is the one thing a reader must not miss here.
    anchors = (
        (0, "start", f["start"], f"{f['start']:,.2f}"),
        # The final NAV carries all ten places: it is the number the golden master asserts.
        (columns - 1, "final NAV", f["final"], f"{f['final']:,.10f}"),
    )
    for index, label, value, shown in anchors:
        top = y.to(value)
        # Outlined: `--sunk` against `--paper` is nearly invisible in the light theme, and an
        # anchor a reader cannot see turns the waterfall into six unattached bars.
        add(
            k.rect(
                centre(index) - bar_w / 2, top, bar_w, frame.y1 - top, fill=ANCHOR,
                stroke="--rule", sw=1.0,
            )
        )
        add(
            k.text(
                centre(index), top - 7, shown, anchor="middle", size=8.0, fill="--ink",
                track=0.02, weight=600,
            )
        )
        add(
            k.text(
                centre(index), frame.y1 + 17, label, anchor="middle", size=8.5, fill="--muted",
                track=0.04,
            )
        )

    for i, (label, value) in enumerate(f["steps"]):
        index = i + 1
        before, after = f["running"][i], f["running"][i + 1]
        top, bottom = y.to(max(before, after)), y.to(min(before, after))
        add(
            k.rect(
                centre(index) - bar_w / 2,
                top,
                bar_w,
                max(bottom - top, 0.8),  # a sub-pixel step still has to be visible
                fill=CREDIT if value > 0 else DEBIT,
            )
        )
        add(
            k.text(
                centre(index),
                top - 7,
                signed(value),
                anchor="middle",
                size=8.0,
                fill=CREDIT if value > 0 else "--ink",
                track=0.02,
                weight=600,
            )
        )
        add(
            k.text(
                centre(index),
                frame.y1 + 17,
                label,
                anchor="middle",
                size=8.5,
                fill="--muted",
                track=0.04,
            )
        )
        # The connector from this step's resting level to the next column.
        add(
            k.line(
                centre(index) - bar_w / 2,
                y.to(before),
                centre(index - 1) + bar_w / 2,
                y.to(before),
                stroke="--rule",
                w=1.0,
                dash="3 2",
            )
        )
    add(
        k.line(
            centre(columns - 1) - bar_w / 2,
            y.to(f["final"]),
            centre(columns - 2) + bar_w / 2,
            y.to(f["final"]),
            stroke="--rule",
            w=1.0,
            dash="3 2",
        )
    )

    add(
        k.text(
            frame.x0 - 2,
            frame.y0 - 8,
            f"NAV, {Y_LO:,.0f} to {Y_HI:,.0f} — the axis is truncated; the whole story is the "
            "top 1% of the capital",
            size=8.0,
            fill="--faint",
            track=0.05,
        )
    )
    # The honest label, in three lines rather than two: the wide fallback font turns a
    # 150-character line into 740 points, and this figure has 900 to spend.
    notes = (
        f"Only {money(f['published_as_one_number'])} of the {money(f['frictions'])} in "
        "frictions is reported by the engine at all, and only as ONE number:",
        f"a fill's cost is commission plus spread, already summed. The remaining "
        f"{money(f['unpublished'])} — borrow, margin interest and the dividend —",
        "is recorded nowhere: engine/backtest.py:42-79. This split exists only in the hand "
        "ledger, which is why the figure is drawn from it.",
    )
    for offset, note in enumerate(notes):
        add(
            k.text(
                frame.x0 - 2,
                frame.y1 + 39 + offset * 12,
                note,
                size=8.0,
                fill="--muted",
                track=0.02,
            )
        )

    return k.document(
        frame=frame,
        slug=SLUG,
        title="Every dollar between the golden master's 100,000 and its final NAV",
        desc=(
            f"A waterfall of eight bars. Starting cash {f['start']:,.2f} rises by a price P&L of "
            f"{money(f['steps'][0][1])} and is then reduced by commission, spread, borrow, margin "
            f"interest and a dividend debit of {money(-f['steps'][5][1])}, the largest of the five, "
            f"ending at {f['final']:,.10f}. Four of the six components are not published by the "
            "backtest engine and come from the hand ledger."
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
        for label, value in f["steps"]:
            print(f"{label:<16} {value:>16,.10f}")
        print(f"{'net':<16} {f['net']:>16,.10f}   final {f['final']:,.10f}")
        print(f"published as one number {f['published_as_one_number']:,.4f}; "
              f"not published at all {f['unpublished']:,.4f}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
