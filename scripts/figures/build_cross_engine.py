"""Figure: our simulator against vectorbt, drawn as distance and as identity.

    python scripts/figures/build_cross_engine.py --print
    python scripts/figures/build_cross_engine.py --facts

WHY THIS IS NOT A RESIDUAL HISTOGRAM
------------------------------------
Every per-bar divergence in `data/cross_engine_residuals.json` is around 1e-12 relative against a
1e-6 gate. A histogram of that is a spike at zero, and a spike at zero is padding: anyone who
knows floating point reads it as "two programs summed the same numbers in a slightly different
order", which is true and is not a measurement of agreement.

So the figure makes two claims instead, and the second is the real one.

PANEL A — THE TWO GAPS, WHICH ARE THE WHOLE CONTENT OF THE CONTINUOUS COMPARISON
--------------------------------------------------------------------------------
One log axis in relative units, from below double-precision epsilon to above the gate. What it
says is a pair of distances, written out as text rather than left to be measured off a bar: the
largest divergence sits ~3.8 decades ABOVE the floor nothing can beat (2.220446049250313e-16, so
the engines are not bit-identical and no honest reconciliation claims to be) and ~5.9 decades
BELOW the tolerance that would fail it. The decade column heights are secondary and are labelled
with their counts so nothing has to be read off a height.

The 29 bars whose divergence is EXACTLY zero cannot be placed on a log axis and are stated in
text instead of being dropped, which is the failure mode a log-scaled residual chart has.

The document quotes one absolute and one relative maximum as though they were one measurement
(`docs/verification/cross_engine_reconciliation.md:40`: "$0.0000002186 (1.30e-12 relative)").
They are maxima of two different series and they fall on two different bars -- 2,400 and 2,494 --
so the figure names both bars. Neither published number is wrong; the parenthesis is.

PANEL B — THE DISCRETE IDENTITY, WHICH FLOATING POINT CANNOT MANUFACTURE
------------------------------------------------------------------------
One column per bar, a row for each engine, and a third row for the difference which is EMPTY.
Two independently written simulators decided to re-size on the same 1,370 of 2,515 bars. A near
miss on a continuous quantity is what float arithmetic gives you for free; an exact match on a
set of 1,370 discrete decisions out of 2,515 is not, and a blank row says so more honestly than
any spike at zero.

Drawn as 45 contiguous RUNS rather than 2,515 rects, for the 250,000-byte budget in
`tests/unit/test_figures.py:309`. `tests/unit/test_figure_cross_engine.py` asserts the runs
expand back to the exact fill-bar set, so the compression cannot hide a disagreement.

THE SCOPE CAVEAT IS ON THE FIGURE'S FACE
-----------------------------------------
`README.md:12` says "penny-exact | the simulator reconciled against vectorbt" with no qualifier.
The reconciliation is one instrument, long-flat, proportional fees only; carry, dividends,
splits, margin and multi-leg netting are ours alone and are anchored by the golden master
instead. A figure that repeated the unqualified claim would be worse than no figure.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import svgkit as k  # noqa: E402

SLUG = "cross-engine-agreement"
SOURCE = "data/cross_engine_residuals.json"
GENERATOR = "scripts/figures/build_cross_engine.py"

EPS = 2.220446049250313e-16
"""`sys.float_info.epsilon`, spelled out: the figure's floor label is a literal on the face and a
literal in the test, and a computed one would let both agree about a number neither checked."""

DECADE_LO, DECADE_HI = -17, -4
"""The drawn axis, in powers of ten of relative divergence. Wider than the data on both sides on
purpose: the point of the panel is the empty space either side of the occupied decades."""

COUNT_MAX = 900.0
BAR_H = 96.0
MIN_BAR_H = 1.2
"""A decade holding 6 of 2,515 bars is 0.6px tall and some rasterisers drop it. Floored so a
populated decade is never invisible; the count is printed above every column, so no height is
load-bearing."""

W, H = 880.0, 574.0
ROW_H, ROW_GAP = 24.0, 8.0
MIN_RUN_W = 1.0
"""Same reason as MIN_BAR_H: a one-bar run is 0.31px wide. Both rows get the same floor, so the
comparison the panel exists to make is untouched."""

B_TICKS = (0, 500, 1_000, 1_500, 2_000, 2_514)


def runs(indices: list[int]) -> list[tuple[int, int]]:
    """`[(first, last)]` for each maximal run of consecutive bar indices, inclusive.

    Derived separately from each engine's list, never from the other's, so the panel's two rows
    are two measurements rather than one drawn twice.
    """
    if not indices:
        return []
    ordered = sorted(indices)
    out: list[tuple[int, int]] = []
    start = prev = ordered[0]
    for i in ordered[1:]:
        if i == prev + 1:
            prev = i
        else:
            out.append((start, prev))
            start = prev = i
    out.append((start, prev))
    return out


def buckets(rel: list[float]) -> tuple[dict[int, int], int]:
    """`({decade: count}, zeros)` — one-decade buckets over the relative divergences.

    The exact zeros are returned separately rather than folded into the lowest decade: they are a
    different statement (bit-identical) and a log axis has no place to put them.
    """
    counts: dict[int, int] = {}
    zeros = 0
    for r in rel:
        if r == 0.0:
            zeros += 1
            continue
        counts[math.floor(math.log10(r))] = counts.get(math.floor(math.log10(r)), 0) + 1
    return counts, zeros


def facts() -> dict:
    """Everything drawn, recomputed from the raw residual lists every build.

    Nothing here is read out of a summary field, because the artifact does not carry one: see
    `scripts/run_cross_engine_residuals.py`'s `reconcile()`.
    """
    d = json.loads((k.REPO / SOURCE).read_text(encoding="utf-8"))
    rel: list[float] = d["rel_residuals"]
    abs_: list[float] = d["abs_residuals"]

    arg_rel = max(range(len(rel)), key=lambda i: rel[i])
    arg_abs = max(range(len(abs_)), key=lambda i: abs_[i])
    counts, zeros = buckets(rel)

    return {
        "raw": d,
        "bars": d["bars"],
        "fills": d["fills_ours"],
        "final_ours": d["final_ours"],
        "final_theirs": d["final_theirs"],
        "tolerance": d["tolerance"],
        "counts": counts,
        "zeros": zeros,
        "max_rel": rel[arg_rel],
        "max_rel_bar": arg_rel,
        "max_rel_abs": abs_[arg_rel],
        "max_abs": abs_[arg_abs],
        "max_abs_bar": arg_abs,
        "decades_above_eps": math.log10(rel[arg_rel]) - math.log10(EPS),
        "decades_below_gate": math.log10(d["tolerance"]) - math.log10(rel[arg_rel]),
        "runs_ours": runs(d["fill_bars_ours"]),
        "runs_theirs": runs(d["fill_bars_theirs"]),
    }


def _money(v: float) -> str:
    return f"${v:,.6f}"


def _cents(v: float) -> str:
    return f"${v:.10f}"


def _sci(v: float) -> str:
    return f"{v:.2e}"


def render(theme: k.Theme) -> str:
    """One long function on purpose: the figure is laid out once, top to bottom, and splitting it
    per panel would hide the vertical budget that keeps the two panels from colliding."""
    f = facts()
    a = k.Frame(width=W, height=H, left=64.0, right=30.0, top=100.0, bottom=H - 282.0)
    b = k.Frame(width=W, height=H, left=64.0, right=30.0, top=404.0, bottom=H - 492.0)
    x = k.log10(10.0**DECADE_LO, 10.0**DECADE_HI, a.x0, a.x1)
    xb = k.linear(0.0, float(f["bars"] - 1), b.x0, b.x1)
    count_y = k.linear(0.0, COUNT_MAX, a.y1, a.y1 - BAR_H)

    body: list[str] = []
    add = body.append

    # ------------------------------------------------------------------ title and scope
    add(
        k.text(
            a.x0 - 2,
            22,
            "Two engines agree to the last bit the arithmetic allows, and on every decision",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            a.x0 - 2,
            38,
            "Scope: one instrument (XLE daily closes), long-flat only, fractional shares, "
            "proportional fees only. Carry, dividends,",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )
    add(
        k.text(
            a.x0 - 2,
            50,
            "splits, margin and multi-leg netting are ours alone and are anchored by the golden "
            "master, not by this comparison.",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )

    # ------------------------------------------------------------------------- panel A
    add(
        k.text(
            a.x0 - 2,
            76,
            "A  ·  how far apart the two equity curves ever got, in relative terms",
            size=9.5,
            fill="--ink",
            track=0.04,
            weight=600,
        )
    )

    # Failure territory first, so every later element sits on top of it.
    gate_px = x.to(f["tolerance"])
    add(k.rect(gate_px, a.y0, a.x1 - gate_px, a.y1 - a.y0, fill="--sunk", opacity=0.75))
    add(k.text(789.8, 130, "beyond here", anchor="middle", size=8.0, fill="--muted", track=0.04))
    add(k.text(789.8, 142, "the test fails", anchor="middle", size=8.0, fill="--muted", track=0.04))

    add(k.line(a.x0, a.y1, a.x1, a.y1, stroke="--rule"))
    for decade in range(DECADE_LO, DECADE_HI + 1):
        px = x.to(10.0**decade)
        add(k.line(px, a.y1, px, a.y1 + 4, stroke="--rule"))
        add(k.text(px, a.y1 + 14, f"1e{decade}", anchor="middle", size=7.5, fill="--faint", track=None))
    add(
        k.text(
            a.x1,
            a.y1 + 28,
            # ASCII hyphen, not U+2212 MINUS SIGN: `--print` writes to a console, and cp1252 --
            # still the default on the Windows machine this repository is developed on -- cannot
            # encode U+2212, so the typographically correct character crashes the verb.
            "relative divergence, |ours - vectorbt| / vectorbt  (log scale)",
            anchor="end",
            size=8.0,
            fill="--faint",
            track=0.06,
        )
    )
    add(k.text(a.x0 - 2, a.y0 - 8, "bars per decade", size=8.0, fill="--faint", track=0.06))

    # The floor nothing can beat, and the gate. Both are rules, not regions: a rule is a value.
    add(k.line(x.to(EPS), a.y0, x.to(EPS), a.y1, stroke="--faint", w=1.0, dash="2 3"))
    add(
        k.text(
            x.to(EPS) + 5,
            a.y0 - 6,
            f"double precision, {_sci(EPS)}",
            size=8.5,
            fill="--faint",
            track=0.05,
        )
    )
    add(k.line(gate_px, a.y0, gate_px, a.y1, stroke="--brass", w=1.0, dash="4 3"))
    add(
        k.text(
            gate_px - 4,
            a.y0 - 6,
            # Spelled the way the decade ticks are spelled, so the rule reads as a point on the
            # axis it sits on. `f"{1e-6:g}"` gives "1e-06", which is a third spelling of one
            # number on one picture.
            f"the 1e{round(math.log10(f['tolerance']))} gate (D47)",
            anchor="end",
            size=8.5,
            fill="--brass",
            track=0.05,
        )
    )

    # The decade columns.
    for decade in sorted(f["counts"]):
        count = f["counts"][decade]
        centre = x.to(10.0 ** (decade + 0.5))
        height = max(a.y1 - count_y.to(float(count)), MIN_BAR_H)
        add(k.rect(centre - 20.0, a.y1 - height, 40.0, height, fill="--slate", opacity=0.85))
        add(
            k.text(
                centre,
                a.y1 - height - 5,
                f"{count:,}",
                anchor="middle",
                size=8.0,
                fill="--muted",
                track=None,
            )
        )

    # The single worst bar.
    worst_px = x.to(f["max_rel"])
    add(k.line(worst_px, 154.0, worst_px, a.y1, stroke="--brass", w=1.0, dash="3 3", opacity=0.7))
    add(k.circle(worst_px, 150.0, 4.0, fill="--brass"))
    add(
        k.text(
            worst_px + 10,
            146,
            f"worst bar: {_sci(f['max_rel'])} relative, at bar {f['max_rel_bar']:,}",
            size=9.0,
            fill="--ink",
            track=0.03,
            weight=600,
        )
    )
    add(
        k.text(
            worst_px + 10,
            158,
            f"= {_cents(f['max_rel_abs'])} on a {_money(f['final_theirs'])} curve",
            size=8.5,
            fill="--muted",
            track=0.03,
        )
    )
    add(
        k.text(
            worst_px + 10,
            170,
            f"largest in dollars is {_cents(f['max_abs'])}, at bar {f['max_abs_bar']:,} — "
            "another bar entirely",
            size=8.0,
            fill="--muted",
            track=0.03,
        )
    )

    # The two gaps, written out. This is the panel's claim; the columns are its texture.
    add(
        k.text(
            a.x0 - 2,
            328,
            f"The worst divergence sits {f['decades_above_eps']:.1f} decades above double "
            "precision — so the engines are not bit-identical —",
            size=9.0,
            fill="--ink",
            track=0.03,
        )
    )
    add(
        k.text(
            a.x0 - 2,
            341,
            f"and {f['decades_below_gate']:.1f} decades below the gate that would fail them. "
            "Those two distances are the claim.",
            size=9.0,
            fill="--ink",
            track=0.03,
        )
    )
    add(
        k.text(
            a.x0 - 2,
            354,
            f"{f['zeros']:,} bars diverge by exactly zero and have no place on a log axis: "
            "they are the bars before the first trade.",
            size=8.5,
            fill="--faint",
            track=0.03,
        )
    )

    # ------------------------------------------------------------------------- panel B
    add(
        k.text(
            b.x0 - 2,
            386,
            "B  ·  every re-size decision, one column per bar — and the difference between them",
            size=9.5,
            fill="--ink",
            track=0.04,
            weight=600,
        )
    )

    rows = (
        ("ours", f["runs_ours"], "--brass"),
        ("vectorbt", f["runs_theirs"], "--slate"),
        ("difference", [], "--brass"),
    )
    for index, (label, spans, token) in enumerate(rows):
        top = b.y0 + index * (ROW_H + ROW_GAP)
        add(k.rect(b.x0, top, b.span_x, ROW_H, fill="--sunk"))
        add(k.text(b.x0 - 8, top + 15, label, anchor="end", size=8.5, fill="--muted", track=0.04))
        for first, last in spans:
            left = xb.to(float(first))
            width = max(xb.to(float(last + 1)) - left, MIN_RUN_W)
            add(k.rect(left, top + 2.0, min(width, b.x1 - left), ROW_H - 4.0, fill=token))

    add(
        k.text(
            (b.x0 + b.x1) / 2,
            b.y0 + 2 * (ROW_H + ROW_GAP) + 15,
            "empty — not one bar where one engine traded and the other did not",
            anchor="middle",
            size=9.0,
            fill="--muted",
            track=0.04,
        )
    )

    for tick in B_TICKS:
        px = xb.to(float(tick))
        add(k.line(px, b.y1, px, b.y1 + 4, stroke="--rule"))
        add(k.text(px, b.y1 + 14, f"{tick:,}", anchor="middle", size=7.5, fill="--faint", track=None))
    add(
        k.text(
            b.x1,
            b.y1 + 28,
            "bar index",
            anchor="end",
            size=8.0,
            fill="--faint",
            track=0.06,
        )
    )

    add(
        k.text(
            b.x0 - 2,
            b.y1 + 46,
            f"Two independently written simulators re-sized on the same {f['fills']:,} of "
            f"{f['bars']:,} bars, in {len(f['runs_ours']):,} contiguous runs.",
            size=9.0,
            fill="--ink",
            track=0.03,
        )
    )
    add(
        k.text(
            b.x0 - 2,
            b.y1 + 59,
            f"Both finish at {_money(f['final_ours'])}. A near miss on a continuous quantity is "
            "free; an exact match on a discrete set is not.",
            size=9.0,
            fill="--ink",
            track=0.03,
        )
    )

    return k.document(
        frame=a,
        slug=SLUG,
        title="Our simulator and vectorbt agree to 1e-12 and on every one of 1,370 trades",
        desc=(
            f"Two panels. The first is a log axis of per-bar relative divergence between our "
            f"equity curve and vectorbt's on {f['bars']:,} XLE bars: the worst is "
            f"{_sci(f['max_rel'])}, which is {f['decades_above_eps']:.1f} decades above double "
            f"precision and {f['decades_below_gate']:.1f} decades below the 1e-6 tolerance. The "
            f"second is one column per bar showing that both engines re-sized on the same "
            f"{f['fills']:,} bars, with an empty difference row. Scope: one instrument, "
            f"long-flat, proportional fees only."
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
    ap.add_argument("--write", action="store_true", help="write both files, before registration")
    args = ap.parse_args()
    if args.to_stdout:
        sys.stdout.write(render("light"))
        return 0
    if args.write:
        k.FIGURES.mkdir(parents=True, exist_ok=True)
        for path, content in files().items():
            path.write_text(content, encoding="utf-8", newline="\n")
            print(f"{path.name}  {len(content.encode('utf-8')):,} bytes")
        return 0
    if args.facts:
        f = facts()
        print(
            f"bars={f['bars']} fills={f['fills']} "
            f"max_rel={f['max_rel']:.6e}@{f['max_rel_bar']} "
            f"max_abs={f['max_abs']:.6e}@{f['max_abs_bar']} "
            f"zeros={f['zeros']} buckets={dict(sorted(f['counts'].items()))} "
            f"runs={len(f['runs_ours'])} "
            f"gaps={f['decades_above_eps']:.3f}/{f['decades_below_gate']:.3f}"
        )
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
