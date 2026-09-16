"""Figure: one statistic, two nulls, two verdicts.

    python scripts/figures/build_two_nulls.py --print
    python scripts/figures/build_all.py --build

WHAT IT SHOWS
-------------
D393's candidate score `up_run_21` earns **22.056417616197663** bp/trade on the primary cell. That
one number -- byte-identical in both artifacts, which `facts()` refuses to run without -- is scored
against two different nulls, and they do not agree about it:

  A' (a TIMING null: each name's events rotated within its own eligible bars) puts p95 at 16.1982
     on 2,000 draws. The margin is +5.8582, which is 14.89 SE(p95). Verdict ABOVE.
  B  (a NAME-SWAP null: each event's name swapped for an eligible name in the same RSI bucket)
     puts p95 at 21.3661 on 1,000 draws. The margin is +0.6904, which is 1.76 SE(p95) -- inside
     the +-2 SE band. Verdict UNRESOLVED (within 2 SE).

This is D373's rule drawn once: a SAMPLE p95 is biased toward the centre, so every finite-draw null
is more lenient than it looks, and a margin inside 2 SE is recorded as UNRESOLVED rather than
rounded to a pass. The figure exists because the same statistic clears one null decisively and does
not clear the other at all, and nothing in the record shows the two side by side.

THE TRAP THIS FIGURE IS BUILT AROUND: 2,000 DRAWS BESIDE 1,000
--------------------------------------------------------------
The two nulls were run at different draw counts. A histogram of 2,000 draws placed beside one of
1,000 at RAW BAR HEIGHTS is quietly lying about the only comparison the figure exists to make --
A's bars would stand roughly twice as tall for no reason a reader can see. So the bars are
**density**: `count / (n_draws * bin_width)`, which makes each panel's bars integrate to exactly
1 whatever its draw count, and both draw counts are stated on the figure. The per-figure test
recomputes both histograms from the raw draws and asserts the integral.

The two panels share one x scale, one y scale, one set of bin EDGES and one pixel height, because
any of those differing between them would reintroduce the same lie by another route.

ONE BIN RULE, APPLIED TO BOTH
-----------------------------
Freedman-Diaconis width (`2 * IQR / n**(1/3)`) computed on each sample, and the WIDER of the two
taken for both panels. Taking the wider one is the conservative direction: it cannot under-smooth
either sample, and a shared width is what makes the two panels comparable bar for bar. That gives
1.4862 bp and 33 bins across the pooled range -- close to FD's own 33 bins for A' over that range,
so the rule is not being bent to a number. The test recomputes it from the draws rather than
trusting a constant here.

WHY THE TWO SEs ARE NEARLY EQUAL, WHICH IS NOT "MORE DRAWS DO NOT HELP"
-----------------------------------------------------------------------
A' has twice B's draws and almost exactly the same SE(p95): 0.3934 against 0.3913. The tempting
reading -- that draw count does not buy precision -- is wrong, and the record disproves it: B was
later re-run at 4,000 draws (`data/d393_b_resolved.json`, `scripts/run_d393_b_resolve.py`) and the
SE fell to 0.2161. A quantile's standard error rides the DENSITY of draws at that quantile as well
as the count; A's upper tail is flatter there (~0.0133 per bp against B's ~0.0170), which offsets
its 2x draws. One line on the figure says so, rather than leaving a reader to draw the wrong
inference from a coincidence.

The 4,000-draw resolution is deliberately NOT quoted on the figure: this figure names two sources
and may only draw numbers those two files hold. What it draws is true of the artifacts it names --
B, at 1,000 draws, is UNRESOLVED -- which is exactly the state D373's rule is about.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

import svgkit as k  # noqa: E402

SLUG = "two-nulls-one-statistic"
SOURCE = "data/d393_aprime_null.json + data/d393_b_null.json"
GENERATOR = "scripts/figures/build_two_nulls.py"

SCORE = "up_run_21"
PANELS = (
    (
        "data/d393_aprime_null.json",
        "A'",
        "each name's events rotated within its own eligible bars (a timing null)",
    ),
    (
        "data/d393_b_null.json",
        "B",
        "each event's name swapped for an eligible name in the same RSI bucket",
    ),
)

# Density, never counts -- see the module docstring. The ceiling is set above the taller panel's
# peak (0.0760) with room for the two in-panel marker rows, which sit at fixed pixel offsets from
# the panel top and would otherwise land inside B's modal bar.
Y_MAX = 0.09
Y_TICKS = (0.0, 0.02, 0.04, 0.06, 0.08)
X_TICKS = (-15, -10, -5, 0, 5, 10, 15, 20, 25, 30)

WIDTH, HEIGHT = 880.0, 580.0
LEFT, RIGHT = 64.0, 22.0
A_TOP, A_BOT = 100.0, 264.0
B_TOP, B_BOT = 357.0, 521.0


def _fd_width(x: np.ndarray) -> float:
    """Freedman-Diaconis bin width. Raises rather than falling back on a degenerate sample.

    A silent fallback to some default width would be the `assert-estimator-input-assumptions`
    defect: the figure would still draw, at a width nothing chose.
    """
    q25, q75 = (float(v) for v in np.percentile(x, (25.0, 75.0)))
    iqr = q75 - q25
    if not iqr > 0.0:
        raise ValueError(f"the draws have a zero IQR ({iqr!r}); no bin width can be derived")
    return 2.0 * iqr / float(x.size) ** (1.0 / 3.0)


def facts() -> dict:
    """Everything drawn, computed once so the test can recompute it the same way."""
    loaded = []
    for relpath, name, mechanism in PANELS:
        doc = json.loads((k.REPO / relpath).read_text(encoding="utf-8"))
        stats = doc["stats"][SCORE]
        draws = np.asarray(doc["draws"][SCORE], dtype=float)
        if draws.size != doc["n_draws"] or draws.size != stats["n_draws"]:
            raise ValueError(f"{relpath}: {draws.size} draws where n_draws says {doc['n_draws']}")
        loaded.append((relpath, name, mechanism, doc, stats, draws))

    # THE PREMISE. The whole figure is "the same number, two verdicts"; if the two artifacts ever
    # stopped holding the same observed value there would be no figure, only two charts.
    observed = {s["observed"] for _, _, _, _, s, _ in loaded}
    if len(observed) != 1:
        raise ValueError(f"the two nulls score different observed values {sorted(observed)}")
    obs = loaded[0][4]["observed"]

    # ONE bin grid for both panels, from the wider of the two FD widths. A per-panel grid would
    # put unequal-width bars side by side and re-open the comparability hole density closes.
    pooled = np.concatenate([d for *_, d in loaded])
    lo = float(pooled.min())
    width = max(_fd_width(d) for *_, d in loaded)
    n_bins = math.ceil((float(pooled.max()) - lo) / width)
    edges = [lo + i * width for i in range(n_bins + 1)]

    panels = []
    for relpath, name, mechanism, doc, stats, draws in loaded:
        counts = [int(v) for v in np.histogram(draws, bins=edges)[0]]
        if sum(counts) != draws.size:
            raise ValueError(f"{relpath}: {sum(counts)} of {draws.size} draws fell in the bins")
        # The stored summary is re-derived, not trusted: a figure that drew a p95 the draws do not
        # support would be the `test-the-statistic-not-just-the-story` defect in picture form.
        for field, value in (("p50", np.median(draws)), ("p95", np.percentile(draws, 95.0))):
            if float(value) != stats[field]:
                raise ValueError(f"{relpath}: stored {field}={stats[field]} but the draws give {value}")
        margin = obs - stats["p95"]
        band = 2.0 * stats["se_p95"]
        within = abs(margin) <= band
        if margin != stats["margin"] or within != stats["within_2se"]:
            raise ValueError(f"{relpath}: the stored margin/within_2se disagree with the draws")
        panels.append(
            {
                "source": relpath,
                "name": name,
                "mechanism": mechanism,
                "n_draws": int(draws.size),
                "p50": stats["p50"],
                "p95": stats["p95"],
                "se_p95": stats["se_p95"],
                "margin": margin,
                "band": band,
                "within_2se": within,
                "verdict": stats["verdict"],
                # Signed distance from the margin to the nearer band edge: positive means the
                # margin cleared the band, negative means it fell short of it. This is the number
                # the verdict actually turns on, and neither artifact stores it.
                "slack": abs(margin) - band,
                "sigmas": abs(margin) / stats["se_p95"],
                "counts": counts,
                "density": [c / (draws.size * width) for c in counts],
            }
        )

    return {
        "observed": obs,
        "edges": edges,
        "bin_width": width,
        "n_bins": n_bins,
        "panels": panels,
    }


def _panel(
    frame: k.Frame,
    x: k.Scale,
    panel: dict,
    edges: list[float],
    observed: float,
    header_y: float,
) -> list[str]:
    """One null: its density histogram, p50, p95, the +-2 SE band and the observed value."""
    out: list[str] = []
    y = k.linear(0.0, Y_MAX, frame.y1, frame.y0)

    out.append(
        k.text(
            frame.x0 - 2,
            header_y,
            f"{panel['name']}  —  {panel['mechanism']}  ·  {panel['n_draws']:,} draws",
            size=9.5,
            fill="--ink",
            track=0.03,
            weight=600,
        )
    )
    verb = "falls short of the band edge by" if panel["within_2se"] else "clears the ±2 SE band by"
    out.append(
        k.text(
            frame.x0 - 2,
            header_y + 13,
            f"{panel['verdict']} — margin {panel['margin']:+.4f} {verb} "
            f"{abs(panel['slack']):.4f}  ({panel['sigmas']:.2f} × SE)",
            size=9.0,
            fill="--muted",
            track=0.03,
        )
    )
    out.append(k.text(4, frame.y0 - 6, "density", size=8.0, fill="--faint", track=0.08))

    # The +-2 SE band, drawn FIRST so the bars sit on top of it rather than hiding behind it.
    out.append(
        k.rect(
            x.to(panel["p95"] - panel["band"]),
            frame.y0,
            x.to(panel["p95"] + panel["band"]) - x.to(panel["p95"] - panel["band"]),
            frame.span_y,
            fill="--rule",
        )
    )

    out.append(k.gridlines(frame, y, Y_TICKS, fmt=lambda v: f"{v:.2f}"))

    for i, height in enumerate(panel["density"]):
        if height <= 0.0:
            continue  # an empty bin is not a zero-height rect; it is nothing
        left, right = x.to(edges[i]), x.to(edges[i + 1])
        out.append(k.rect(left, y.to(height), right - left, frame.y1 - y.to(height), opacity=0.55))

    out.append(k.line(frame.x0, frame.y1, frame.x1, frame.y1, stroke="--faint"))

    p50_px, p95_px, obs_px = (x.to(v) for v in (panel["p50"], panel["p95"], observed))
    out.append(k.line(p50_px, frame.y0, p50_px, frame.y1, stroke="--faint", w=1.0, dash="3 3"))
    out.append(k.line(p95_px, frame.y0, p95_px, frame.y1, stroke="--muted", w=1.4))
    out.append(k.line(obs_px, frame.y0, obs_px, frame.y1, stroke="--brass", w=2.0))

    # Two label rows, not one: on B the p95 and the observed are 12px apart and a single row
    # would overprint them. Both rows sit above the modal bar at Y_MAX = 0.09.
    out.append(
        k.text(
            p50_px - 5,
            frame.y0 + 12,
            f"p50 {panel['p50']:.4f}",
            anchor="end",
            size=9.0,
            fill="--faint",
            track=0.03,
        )
    )
    out.append(
        k.text(
            p95_px - 5,
            frame.y0 + 26,
            f"p95 {panel['p95']:.4f}  ±2 SE {panel['se_p95']:.4f}",
            anchor="end",
            size=9.0,
            fill="--muted",
            track=0.03,
        )
    )
    out.append(
        k.text(
            obs_px + 6,
            frame.y0 + 12,
            "observed",
            size=9.0,
            fill="--brass",
            track=0.05,
            weight=600,
        )
    )
    return out


def render(theme: k.Theme) -> str:
    f = facts()
    a, b = f["panels"]
    frame_a = k.Frame(WIDTH, HEIGHT, left=LEFT, right=RIGHT, top=A_TOP, bottom=HEIGHT - A_BOT)
    frame_b = k.Frame(WIDTH, HEIGHT, left=LEFT, right=RIGHT, top=B_TOP, bottom=HEIGHT - B_BOT)
    x = k.linear(f["edges"][0], f["edges"][-1], frame_a.x0, frame_a.x1)

    body: list[str] = []
    add = body.append

    add(
        k.text(
            frame_a.x0 - 2,
            22,
            "One statistic, two nulls, two verdicts",
            size=11.5,
            fill="--ink",
            track=0.01,
            weight=600,
        )
    )
    add(
        k.text(
            frame_a.x0 - 2,
            38,
            f"D393 {SCORE} = {f['observed']:.4f} bp per trade — the SAME observed value in both "
            "artifacts; only the null changes",
            size=8.5,
            fill="--faint",
            track=0.04,
        )
    )
    add(
        k.text(
            frame_a.x0 - 2,
            50,
            f"Bars are DENSITY, so each panel's bars integrate to 1: {a['name']} drew "
            f"{a['n_draws']:,} and {b['name']} drew {b['n_draws']:,}, and raw counts would not "
            "be comparable",
            size=8.5,
            fill="--faint",
            track=0.04,
        )
    )

    body.extend(_panel(frame_a, x, a, f["edges"], f["observed"], header_y=72.0))
    body.extend(_panel(frame_b, x, b, f["edges"], f["observed"], header_y=329.0))

    # The observed value carried through the gap between the panels: one line, one number, two
    # panels. The notes are kept left of it so nothing is overprinted.
    obs_px = x.to(f["observed"])
    add(k.line(obs_px, frame_a.y1, obs_px, frame_b.y0, stroke="--brass", w=2.0, dash="4 3"))
    add(
        k.text(
            obs_px + 6,
            301,
            f"the same {f['observed']:.4f} in both panels",
            size=9.0,
            fill="--brass",
            track=0.04,
            weight=600,
        )
    )
    add(
        k.text(
            frame_a.x0 - 2,
            290,
            "A sample p95 is biased toward the centre, so a finite-draw null is more lenient "
            "than it looks (D373).",
            size=8.5,
            fill="--muted",
            track=0.03,
        )
    )
    add(
        k.text(
            frame_a.x0 - 2,
            303,
            f"The two SEs barely differ ({a['se_p95']:.4f} vs {b['se_p95']:.4f}): a quantile's "
            "SE rides the tail density at p95, not the count alone.",
            size=8.5,
            fill="--muted",
            track=0.03,
        )
    )

    for v in X_TICKS:
        px = x.to(v)
        add(k.line(px, frame_b.y1, px, frame_b.y1 + 4, stroke="--rule"))
        add(k.text(px, frame_b.y1 + 15, f"{v:g}", anchor="middle", fill="--faint", track=None))
    add(
        k.text(
            frame_b.x1,
            frame_b.y1 + 29,
            f"{SCORE} under the null — mean basis points per trade",
            anchor="end",
            size=8.0,
            fill="--faint",
            track=0.08,
        )
    )

    return k.document(
        frame=frame_a,
        slug=SLUG,
        title="The same statistic is decisive against one null and unresolved against another",
        desc=(
            f"Two stacked density histograms on one x axis. The observed {SCORE} of "
            f"{f['observed']:.4f} basis points per trade is marked in both. The upper panel is "
            f"null {a['name']} at {a['n_draws']:,} draws, whose p95 of {a['p95']:.4f} the observed "
            f"value clears by {a['margin']:.4f}, more than {a['sigmas']:.0f} standard errors: "
            f"{a['verdict']}. The lower panel is null {b['name']} at {b['n_draws']:,} draws, whose "
            f"p95 of {b['p95']:.4f} the observed value clears by only {b['margin']:.4f}, inside "
            f"the plus or minus two standard error band of {b['band']:.4f}: {b['verdict']}. Bars "
            "are plotted as density because the two nulls have different draw counts."
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
        print(f"observed={f['observed']!r} bins={f['n_bins']} width={f['bin_width']:.6f}")
        for p in f["panels"]:
            integral = sum(h * f["bin_width"] for h in p["density"])
            print(
                f"  {p['name']:<3} n={p['n_draws']:>5,} p50={p['p50']:.4f} p95={p['p95']:.4f} "
                f"se={p['se_p95']:.4f} margin={p['margin']:+.4f} band={p['band']:.4f} "
                f"slack={p['slack']:+.4f} sigmas={p['sigmas']:.2f} integral={integral:.12f} "
                f"verdict={p['verdict']}"
            )
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
