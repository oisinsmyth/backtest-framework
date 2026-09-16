"""Figure: the deflated-Sharpe hurdle against the trial count.

    python scripts/figures/build_dsr_hurdle.py --print
    python scripts/figures/build_all.py --build

WHAT IT SHOWS, AND WHY IT IS THE ONE FIGURE WORTH PUTTING FIRST
---------------------------------------------------------------
The MACD ladder's best cell earns an annualised Sharpe of 0.4957 and clears six of seven hurdles.
The seventh is the noise floor a SELECTED best result has to beat, and that floor rises with the
number of looks taken. At the 42 looks this study spent it is 0.3340 and the cell clears. At the
45,783 the trial registry actually carries -- 45,741 of them inherited from earlier work on the
same fixture -- it is 0.6377 and the cell fails by 0.142.

A result that is publishable as a first study and not publishable as the 45,783rd. The registry is
what knows the difference, and one picture says it.

THE CURVE IS THE LIBRARY'S OWN FUNCTION, NOT AN INTERPOLATION
-------------------------------------------------------------
`validation.dsr.expected_max_sharpe(n_trials, var_trials)` is evaluated at ~420 log-spaced integer
counts, with `var_trials` and `periods_per_year` read from the study artifact. It is not a curve
fitted through the three recorded points: called at those three counts it reproduces the recorded
values to the last digit, which `tests/unit/test_figures.py` asserts.

`n_trials` is an integer, so the true object is a step function; the polyline is a sampling of it,
which is the honest way round -- smooth and true rather than smooth and slightly false. The
function raises below `n_trials = 2`, so that is where the curve starts.

THE CROSSING IS THE FINDING
---------------------------
The hurdle overtakes the observed Sharpe at **N = 1,086**, not somewhere near 45,000. That is
computed here by bracketing rather than read off anything, and the bracket is asserted: this cell
stopped being publishable at about the thousandth look. Nothing in the record says so, because
nobody had drawn it.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

import svgkit as k  # noqa: E402
from backtest_framework.validation.dsr import expected_max_sharpe  # noqa: E402

SLUG = "dsr-hurdle-vs-look-count"
SOURCE = "data/macd_ladder_summary.json"
GENERATOR = "scripts/figures/build_dsr_hurdle.py"

N_MIN, N_MAX = 2, 100_000
SAMPLES = 420
Y_TICKS = (0.0, 0.2, 0.4, 0.6)
X_DECADES = (10, 100, 1_000, 10_000, 100_000)


def facts() -> dict:
    """Everything drawn, computed once so the test can recompute it the same way."""
    d = json.loads((k.REPO / SOURCE).read_text(encoding="utf-8"))
    var_trials = d["multiplicity"]["var_trials_per_period"]
    annualise = math.sqrt(d["periods_per_year"])

    def hurdle(n: int) -> float:
        return expected_max_sharpe(n, var_trials) * annualise

    best = max(d["core"], key=lambda cell: cell["sharpe"])
    observed = best["sharpe"]

    crossing = N_MIN
    while hurdle(crossing) < observed:
        crossing += 1

    counts = d["multiplicity"]["counts"]
    return {
        "hurdle": hurdle,
        "observed": observed,
        "cell": f"{best['rung']}/{best['book']}/{best['gate']}",
        "crossing": crossing,
        "marks": [
            (counts["fresh"]["n_trials"], counts["fresh"]["expected_max_sharpe_annualised"]),
            (
                counts["fresh_plus_prior_configs"]["n_trials"],
                counts["fresh_plus_prior_configs"]["expected_max_sharpe_annualised"],
            ),
            (
                counts["combined_with_disclosed"]["n_trials"],
                counts["combined_with_disclosed"]["expected_max_sharpe_annualised"],
            ),
        ],
        "deficit": counts["combined_with_disclosed"]["expected_max_sharpe_annualised"] - observed,
    }


def _thousands(n: int) -> str:
    return f"{n:,}"


def render(theme: k.Theme) -> str:
    f = facts()
    hurdle, observed, crossing = f["hurdle"], f["observed"], f["crossing"]
    frame = k.Frame(width=880.0, height=400.0, left=64.0, right=22.0, top=52.0, bottom=44.0)
    x = k.log10(N_MIN, N_MAX, frame.x0, frame.x1)
    y = k.linear(0.0, 0.72, frame.y1, frame.y0)

    body: list[str] = []
    add = body.append

    add(
        k.text(
            frame.x0 - 2,
            22,
            "The noise floor a selected result must clear, against the number of looks taken",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            frame.x0 - 2,
            36,
            f"MACD ladder, best cell ({f['cell']}) — six of seven hurdles cleared, this is the seventh",
            size=8.5,
            fill="--faint",
            track=0.04,
        )
    )

    add(k.gridlines(frame, y, Y_TICKS, fmt=lambda v: f"{v:.1f}"))
    for n in X_DECADES:
        px = x.to(n)
        add(k.line(px, frame.y1, px, frame.y1 + 4, stroke="--rule"))
        add(k.text(px, frame.y1 + 15, _thousands(n), anchor="middle", fill="--faint", track=None))
    add(
        k.text(
            frame.x1,
            frame.y1 + 30,
            "looks taken (log scale)",
            anchor="end",
            size=8.0,
            fill="--faint",
            track=0.08,
        )
    )
    # Left-aligned at the viewBox edge, not right-aligned off the axis: the fallback font is
    # wider than IBM Plex and an end-anchored label here runs off the left of the frame.
    add(
        k.text(
            4,
            frame.y0 - 8,
            "annualised Sharpe",
            anchor="start",
            size=8.0,
            fill="--faint",
            track=0.08,
        )
    )

    # The region where the hurdle has overtaken the result: everything right of the crossing.
    add(
        k.rect(
            x.to(crossing),
            frame.y0,
            frame.x1 - x.to(crossing),
            frame.y1 - frame.y0,
            fill="--sunk",
            opacity=0.55,
        )
    )

    # The observed Sharpe: flat, because the result does not change. Only the floor does.
    obs_y = y.to(observed)
    add(k.line(frame.x0, obs_y, frame.x1, obs_y, stroke="--brass", w=1.8))
    add(
        k.text(
            frame.x0 + 6,
            obs_y - 7,
            f"observed {observed:.4f} — the cell's Sharpe, unchanged throughout",
            size=9.0,
            fill="--brass",
            track=0.04,
            weight=600,
        )
    )

    # The hurdle.
    step = (math.log10(N_MAX) - math.log10(N_MIN)) / (SAMPLES - 1)
    ns = sorted({max(N_MIN, round(10 ** (math.log10(N_MIN) + i * step))) for i in range(SAMPLES)})
    add(k.polyline([(x.to(n), y.to(hurdle(n))) for n in ns], stroke="--slate", w=2.0))
    add(
        k.text(
            x.to(60_000),
            y.to(hurdle(60_000)) - 10,
            "the hurdle",
            anchor="middle",
            size=9.0,
            fill="--slate",
            track=0.08,
            weight=600,
        )
    )

    # The crossing.
    add(k.line(x.to(crossing), obs_y, x.to(crossing), frame.y1, stroke="--faint", w=1.0, dash="3 3"))
    add(k.circle(x.to(crossing), obs_y, 4.0, fill="--paper", stroke="--brass", sw=2.0))
    add(
        k.text(
            x.to(crossing) + 8,
            frame.y1 - 30,
            f"{_thousands(crossing)} looks — where it stopped being publishable",
            size=9.0,
            fill="--ink",
            track=0.03,
        )
    )

    # The three counts the registry actually records.
    labels = (
        (0, "42 looks: this study alone", "start", 8.0, -12.0),
        (2, f"45,783: the verdict count — fails by {f['deficit']:.3f}", "end", -8.0, -14.0),
    )
    for n, value in f["marks"]:
        add(k.circle(x.to(n), y.to(value), 3.6, fill="--slate"))
    for idx, label, anchor, dx, dy in labels:
        n, value = f["marks"][idx]
        add(
            k.text(
                x.to(n) + dx,
                y.to(value) + dy,
                label,
                anchor=anchor,
                size=9.0,
                fill="--ink",
                track=0.03,
                weight=600,
            )
        )
    mid_n, mid_v = f["marks"][1]
    add(
        k.text(
            x.to(mid_n) - 8,
            y.to(mid_v) + 14,
            "45,388 of them inherited from earlier work on this fixture",
            anchor="end",
            size=8.0,
            fill="--muted",
            track=0.03,
        )
    )

    return k.document(
        frame=frame,
        slug=SLUG,
        title="The deflated-Sharpe hurdle rises with the number of looks taken",
        desc=(
            f"A log-scaled chart of trial count against annualised Sharpe. The observed Sharpe of "
            f"{observed:.4f} is a flat line. The hurdle rises from below it to "
            f"{f['marks'][2][1]:.4f} at 45,783 looks, crossing the observed value at "
            f"{crossing:,} looks, after which the result is no longer publishable."
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
        print(
            f"observed={f['observed']:.6f} cell={f['cell']} crossing={f['crossing']} "
            f"deficit={f['deficit']:.6f} marks={[(n, round(v, 6)) for n, v in f['marks']]}"
        )
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
