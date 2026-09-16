"""What the two-nulls figure CLAIMS, pinned to `data/d393_aprime_null.json` and `data/d393_b_null.json`.

`test_figures.py` gates the mechanics every figure shares -- drift, colour, frame, label overflow.
This file gates the three things only this figure asserts, each of which would leave a figure that
still looked fine:

1. **The premise.** The story is "the SAME number, two verdicts". If the two artifacts ever stopped
   holding the same `observed`, the picture would be two unrelated charts sharing an axis.
2. **The trap.** A' drew 2,000 and B drew 1,000. Bars at RAW COUNTS would make A's distribution
   stand twice as tall for a reason no reader can see, which is the one comparison this figure
   exists to make. So the histograms are recomputed here from the raw draws and their INTEGRAL is
   asserted, not their shape -- a density that does not integrate to 1 is a count in disguise.
3. **The verdicts.** `margin` and `within_2se` are recomputed as `observed - p95` against
   `2 * se_p95` and checked against BOTH the stored fields and the stored verdict strings. A
   figure that drew "UNRESOLVED" because a JSON string said so would be quoting, not checking --
   and `memory/runner-must-compute-the-preregistered-statistic.md` is about exactly that.

Nothing here reads a number out of the builder and compares it to itself: every expected value is
derived from `draws.up_run_21` or from arithmetic on the stored summary.
"""

from __future__ import annotations

import importlib.util
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "figures" / "build_two_nulls.py"
ARTIFACTS = {
    "A'": REPO / "data" / "d393_aprime_null.json",
    "B": REPO / "data" / "d393_b_null.json",
}
FIGURE = REPO / "docs" / "figures" / "two-nulls-one-statistic.svg"
SCORE = "up_run_21"

# The panel rectangles, as the builder lays them out. Repeated rather than imported so that a
# silent change to one of the constants shows up here as a failure instead of being followed.
X0, X1 = 64.0, 858.0
PANEL_PX = {"A'": (100.0, 264.0), "B": (357.0, 521.0)}
Y_MAX = 0.09


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
def nulls() -> dict:
    return {
        name: json.loads(path.read_text(encoding="utf-8")) for name, path in ARTIFACTS.items()
    }


@pytest.fixture(scope="module")
def draws(nulls) -> dict:
    return {name: np.asarray(d["draws"][SCORE], dtype=float) for name, d in nulls.items()}


@pytest.fixture(scope="module")
def page() -> str:
    return FIGURE.read_text(encoding="utf-8")


def present(page: str, text: str, what: str) -> None:
    assert text in page, f"{what}: {text!r} is not on the figure"


def shown(builder, s: str) -> str:
    """A label as it appears in the file. `svgkit.esc` escapes U+00A0, not the ordinary space."""
    return builder.k.esc(s)


def emitted(v: float) -> float:
    """A coordinate as `svgkit.c` writes it. The builder rounds ONCE, at emission.

    Rounding the endpoints first and subtracting gives a different width for a bar whose edges
    straddle a tenth -- which is how this test first disagreed with the file over 0.1px.
    """
    return float(f"{v:.1f}")


def panel(facts: dict, name: str) -> dict:
    (found,) = [p for p in facts["panels"] if p["name"] == name]
    return found


# ------------------------------------------------------------------------- the premise


def test_the_two_nulls_score_the_same_observed_statistic(nulls, facts):
    """Without this the figure is not a comparison, and every other test here is decoration."""
    values = {name: d["stats"][SCORE]["observed"] for name, d in nulls.items()}
    assert len(set(values.values())) == 1, f"the artifacts disagree on the observed value: {values}"
    assert values["A'"] == 22.056417616197663
    assert facts["observed"] == values["A'"]


def test_the_two_nulls_were_run_at_different_draw_counts(nulls, draws, facts):
    """The thing that makes raw bar heights a lie, asserted rather than assumed."""
    counts = {name: d["n_draws"] for name, d in nulls.items()}
    assert counts == {"A'": 2000, "B": 1000}
    for name, n in counts.items():
        assert draws[name].size == n, f"{name}: the draw list is not {n} long"
        assert panel(facts, name)["n_draws"] == n


# -------------------------------------------------------------------- the histogram trap


def test_the_bin_grid_is_recomputed_from_the_raw_draws(draws, facts):
    """Freedman-Diaconis on each sample, the WIDER width taken, one grid for both panels.

    Recomputed from `draws.up_run_21` rather than read back out of the builder: a bin count
    trusted from a constant is a bin count nobody chose.
    """
    widths = {
        name: 2.0 * float(np.subtract(*np.percentile(x, (75.0, 25.0)))) / x.size ** (1 / 3)
        for name, x in draws.items()
    }
    pooled = np.concatenate(list(draws.values()))
    width = max(widths.values())
    n_bins = math.ceil((float(pooled.max()) - float(pooled.min())) / width)

    assert facts["bin_width"] == pytest.approx(width, rel=1e-15)
    assert facts["n_bins"] == n_bins == 33
    assert facts["edges"][0] == float(pooled.min())
    assert len(facts["edges"]) == n_bins + 1
    for i, edge in enumerate(facts["edges"]):
        assert edge == pytest.approx(float(pooled.min()) + i * width, rel=1e-15)
    assert facts["edges"][-1] >= float(pooled.max()), "the top bin does not reach the largest draw"


def test_every_draw_lands_in_a_bin(draws, facts):
    """A draw outside the grid vanishes from the picture without changing anything visible."""
    for name, x in draws.items():
        counts = panel(facts, name)["counts"]
        assert sum(counts) == x.size, f"{name}: {sum(counts)} of {x.size} draws are drawn"
        assert np.histogram(x, bins=facts["edges"])[0].tolist() == counts


def test_each_panel_integrates_to_one_which_is_what_density_means(draws, facts):
    """THE TRAP. 2,000 draws beside 1,000 at raw counts doubles one panel for free.

    Density removes it, and the check that it was actually applied is the integral: bars that
    still carried counts would integrate to `n_draws`, not to 1.
    """
    for name, x in draws.items():
        p = panel(facts, name)
        integral = sum(h * facts["bin_width"] for h in p["density"])
        assert integral == pytest.approx(1.0, rel=1e-12), f"{name} integrates to {integral}"
        for count, height in zip(p["counts"], p["density"]):
            assert height == pytest.approx(count / (x.size * facts["bin_width"]), rel=1e-15)


def test_at_raw_counts_the_panels_would_not_have_been_comparable(draws, facts):
    """The lie this figure exists to avoid, stated as a number.

    A' holds exactly twice B's draws, so a count histogram would have made its bars stand ~2x
    taller on the same axis. After normalising, the two panels' totals are equal at 1.
    """
    a, b = draws["A'"], draws["B"]
    assert a.size / b.size == 2.0
    integrals = [
        sum(h * facts["bin_width"] for h in panel(facts, n)["density"]) for n in ("A'", "B")
    ]
    assert integrals[0] == pytest.approx(integrals[1], rel=1e-12)

    # And the two views disagree about which distribution is the taller one. Counts would put A'
    # above B by the factor its draw count buys; density puts B above A'. No constant is pinned
    # here -- the two ratios differ by exactly the 2x in draws, and they straddle 1.
    peak_counts = [max(panel(facts, n)["counts"]) for n in ("A'", "B")]
    peak_density = [max(panel(facts, n)["density"]) for n in ("A'", "B")]
    count_ratio = peak_counts[0] / peak_counts[1]
    density_ratio = peak_density[0] / peak_density[1]
    assert count_ratio == pytest.approx(density_ratio * (a.size / b.size), rel=1e-12)
    assert count_ratio > 1.0 > density_ratio, (
        f"counts rank the panels {count_ratio:.3f} and density ranks them {density_ratio:.3f}; "
        "if they ever agreed, this figure's caveat would have nothing to warn about"
    )


# ------------------------------------------------------------------------ the statistics


def test_p50_and_p95_are_the_draws_own_quantiles(draws, nulls, facts):
    """The stored summary is re-derived, not quoted."""
    for name, x in draws.items():
        stats = nulls[name]["stats"][SCORE]
        assert float(np.median(x)) == stats["p50"] == panel(facts, name)["p50"]
        assert float(np.percentile(x, 95.0)) == stats["p95"] == panel(facts, name)["p95"]
        assert float(x.min()) == stats["min"] and float(x.max()) == stats["max"]


def test_the_stored_se_is_a_bootstrap_se_of_the_p95_and_the_two_are_nearly_equal(nulls, facts):
    """`scripts/run_d393_bs_null.py:447-456` -- 400 resamples, `std(ddof=1)` of the resampled p95.

    It cannot be recomputed here without re-running that RNG, so what is asserted is the claim the
    figure makes ABOUT it: the two SEs are within 1% of each other despite A' having twice the
    draws. That is the line of text the figure carries, and it is the one a reader would otherwise
    mis-read as "more draws buy nothing".
    """
    se = {name: d["stats"][SCORE]["se_p95"] for name, d in nulls.items()}
    assert se == {"A'": 0.39343513244423994, "B": 0.39134575805568095}
    for name, value in se.items():
        assert value > 0.0 and panel(facts, name)["se_p95"] == value
    assert abs(se["A'"] / se["B"] - 1.0) < 0.01, "the figure's 'barely differ' line would be false"


def test_margin_and_the_two_se_band_are_recomputed_not_trusted(nulls, facts):
    """`margin = observed - p95`, `within_2se = |margin| <= 2 * se_p95`, D373's rule verbatim."""
    for name, d in nulls.items():
        stats = d["stats"][SCORE]
        margin = stats["observed"] - stats["p95"]
        within = abs(margin) <= 2.0 * stats["se_p95"]
        assert margin == stats["margin"], f"{name}: the stored margin is not observed - p95"
        assert within == stats["within_2se"], f"{name}: the stored within_2se does not follow"
        p = panel(facts, name)
        assert p["margin"] == margin and p["within_2se"] == within
        assert p["band"] == 2.0 * stats["se_p95"]
        assert p["slack"] == pytest.approx(abs(margin) - 2.0 * stats["se_p95"], rel=1e-15)
        assert p["sigmas"] == pytest.approx(abs(margin) / stats["se_p95"], rel=1e-15)


def test_the_verdict_string_follows_from_the_recomputed_band(nulls):
    """The string is the artifact's; the RULE that produces it is checked here."""
    for name, d in nulls.items():
        stats = d["stats"][SCORE]
        margin = stats["observed"] - stats["p95"]
        want = (
            "UNRESOLVED (within 2 SE)"
            if abs(margin) <= 2.0 * stats["se_p95"]
            else "ABOVE"
            if margin > 0
            else "BELOW"
        )
        assert stats["verdict"] == want, f"{name}: verdict {stats['verdict']!r}, rule says {want!r}"


def test_the_two_nulls_disagree_about_the_same_number(nulls, facts):
    """The whole figure in one assertion. If this stops being true there is nothing to draw."""
    a, b = (nulls[n]["stats"][SCORE] for n in ("A'", "B"))
    assert a["observed"] == b["observed"]
    assert a["verdict"] == "ABOVE" and a["within_2se"] is False
    assert b["verdict"] == "UNRESOLVED (within 2 SE)" and b["within_2se"] is True
    assert a["margin"] > 0 and b["margin"] > 0, "both margins are positive; only the band differs"
    assert panel(facts, "A'")["sigmas"] > 2.0 > panel(facts, "B")["sigmas"]
    assert panel(facts, "A'")["slack"] > 0.0 > panel(facts, "B")["slack"]


# -------------------------------------------------------------------------- the drawing


def test_both_panels_mark_the_observed_at_one_data_value_and_one_pixel(page, facts):
    """Two brass rules at different x would say the two nulls scored different numbers.

    Checked in PIXELS, which is what a reader actually compares, and against the x scale
    recomputed here from the bin edges rather than from the builder's `Scale`.
    """
    brass = re.findall(
        r'<line x1="([\d.]+)" y1="([\d.]+)" x2="([\d.]+)" y2="([\d.]+)" '
        r'stroke="var\(--brass\)" stroke-width="2.0"',
        page,
    )
    assert len(brass) == 3, "expected the observed rule in both panels plus the gap connector"
    xs = {x1 for x1, _, _, _ in brass} | {x2 for _, _, x2, _ in brass}
    assert len(xs) == 1, f"the observed value is drawn at more than one x: {sorted(xs)}"

    lo, hi = facts["edges"][0], facts["edges"][-1]
    want = X0 + (facts["observed"] - lo) / (hi - lo) * (X1 - X0)
    assert float(xs.pop()) == pytest.approx(want, abs=0.06)

    spans = sorted((float(y1), float(y2)) for _, y1, _, y2 in brass)
    assert spans == sorted([PANEL_PX["A'"], PANEL_PX["B"], (PANEL_PX["A'"][1], PANEL_PX["B"][0])])


def test_the_bars_are_drawn_at_the_density_and_on_one_shared_geometry(page, facts, draws):
    """Every bar's pixel rectangle recomputed from the RAW DRAWS and the panel boxes.

    This is where "plot density" stops being a claim in a docstring. The density is recomputed
    here from `draws.up_run_21` rather than read out of `facts()`: a builder that went back to
    counts would otherwise be compared against its own broken numbers and pass.
    """
    drawn = [
        tuple(float(v) for v in m)
        for m in re.findall(
            r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"'
            r' fill="var\(--slate\)" opacity="0.55"/>',
            page,
        )
    ]
    lo, hi = facts["edges"][0], facts["edges"][-1]

    def px(v: float) -> float:
        return X0 + (v - lo) / (hi - lo) * (X1 - X0)

    want = []
    for name in ("A'", "B"):
        top, base = PANEL_PX[name]
        x = draws[name]
        density = np.histogram(x, bins=facts["edges"])[0] / (x.size * facts["bin_width"])
        for i, height in enumerate(density):
            if height <= 0.0:
                continue
            y = base - height / Y_MAX * (base - top)
            left, right = px(facts["edges"][i]), px(facts["edges"][i + 1])
            want.append((emitted(left), emitted(y), emitted(right - left), emitted(base - y)))

    assert drawn == want, "the bars are not the recomputed densities on the shared geometry"
    assert len(drawn) == sum(
        sum(1 for c in panel(facts, n)["counts"] if c) for n in ("A'", "B")
    ), "an empty bin was drawn as a zero-height rect, or a non-empty one was dropped"


def test_the_panels_are_the_same_height_and_carry_the_same_y_scale(page):
    """Equal draw counts are not the only way to make two panels incomparable.

    Unequal pixel heights, or two different density ceilings, would do it just as well and would
    be invisible. The gridlines are the evidence: the same five density values, the same spacing.
    """
    a_top, a_base = PANEL_PX["A'"]
    b_top, b_base = PANEL_PX["B"]
    assert a_base - a_top == b_base - b_top

    labels = [
        (float(y), text)
        for y, text in re.findall(
            r'<text x="56.0" y="([\d.]+)" text-anchor="end" font-size="9.0"[^>]*>(0\.\d\d)</text>',
            page,
        )
    ]
    assert len(labels) == 10, "expected five density gridline labels in each panel"
    per_panel = {}
    for y, value in labels:
        per_panel.setdefault("A'" if y < b_top else "B", []).append((value, y))
    assert set(per_panel) == {"A'", "B"}
    a_rows, b_rows = per_panel["A'"], per_panel["B"]
    assert [v for v, _ in a_rows] == [v for v, _ in b_rows] == [
        "0.00",
        "0.02",
        "0.04",
        "0.06",
        "0.08",
    ]
    offsets = [round(y - a_base, 1) for _, y in a_rows]
    assert offsets == [round(y - b_base, 1) for _, y in b_rows], "the two y scales differ"


def test_the_two_se_band_is_drawn_around_the_p95_of_its_own_panel(page, facts):
    bands = [
        tuple(float(v) for v in m)
        for m in re.findall(
            r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"'
            r' fill="var\(--rule\)"/>',
            page,
        )
    ]
    assert len(bands) == 2, "one +-2 SE band per panel"
    lo, hi = facts["edges"][0], facts["edges"][-1]

    def px(v: float) -> float:
        return X0 + (v - lo) / (hi - lo) * (X1 - X0)

    obs_px = px(facts["observed"])
    for (x, y, w, h), name in zip(bands, ("A'", "B")):
        p = panel(facts, name)
        top, base = PANEL_PX[name]
        assert (y, h) == (top, base - top)
        assert x == pytest.approx(px(p["p95"] - p["band"]), abs=0.06)
        assert x + w == pytest.approx(px(p["p95"] + p["band"]), abs=0.12)
        # The verdict, read off the picture: is the brass rule inside this band or outside it?
        inside = x <= obs_px <= x + w
        assert inside == p["within_2se"], (
            f"{name}: the drawn band {'contains' if inside else 'excludes'} the observed rule, "
            f"but the artifact records within_2se={p['within_2se']}"
        )


def test_the_figure_quotes_the_numbers_it_is_drawn_from(page, builder, facts, nulls):
    present(page, f"{facts['observed']:.4f}", "the observed statistic")
    present(page, shown(builder, "the same 22.0564 in both panels"), "the shared-value label")
    for name in ("A'", "B"):
        p, stats = panel(facts, name), nulls[name]["stats"][SCORE]
        present(page, shown(builder, f"{p['n_draws']:,} draws"), f"{name}'s draw count")
        present(page, shown(builder, f"p50 {stats['p50']:.4f}"), f"{name}'s p50")
        present(page, shown(builder, f"p95 {stats['p95']:.4f}"), f"{name}'s p95")
        present(page, f"{stats['se_p95']:.4f}", f"{name}'s SE(p95)")
        present(page, f"{p['margin']:+.4f}", f"{name}'s margin")
        present(page, f"{abs(p['slack']):.4f}", f"{name}'s distance to the band edge")
        present(page, f"{p['sigmas']:.2f}", f"{name}'s margin in SEs")
        present(page, shown(builder, stats["verdict"]), f"{name}'s verdict")
    present(page, shown(builder, "Bars are DENSITY"), "the density caveat")


def test_the_builder_refuses_to_draw_a_figure_whose_premise_has_gone(builder, monkeypatch, tmp_path):
    """A check that cannot fire is worse than none (CLAUDE.md).

    `facts()` guards the premise -- the same `observed` in both artifacts -- and the guard is
    proved by feeding it an artifact whose observed value has moved.
    """
    real = builder.k.REPO
    fake = tmp_path
    (fake / "data").mkdir()
    for path in ARTIFACTS.values():
        doc = json.loads(path.read_text(encoding="utf-8"))
        if path.name.startswith("d393_b_"):
            doc["stats"][SCORE]["observed"] += 1.0
        (fake / "data" / path.name).write_text(json.dumps(doc), encoding="utf-8")
    monkeypatch.setattr(builder.k, "REPO", fake)
    try:
        with pytest.raises(ValueError, match="different observed values"):
            builder.facts()
    finally:
        monkeypatch.setattr(builder.k, "REPO", real)
