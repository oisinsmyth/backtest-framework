"""Every figure in `docs/figures/`, gated the way every other generated artifact here is.

The figures are the one part of this repository a reader meets before reading anything, so the
ways they can be wrong are worth naming:

1. **The file drifts from its builder.** Someone edits an SVG by hand, or edits the source
   artifact and forgets to rebuild. Caught by regenerating and comparing bytes.
2. **A number in the picture stops matching the number in the artifact.** This is the one that
   matters, because a figure is quoted and a quoted figure is never re-derived. Every drawn value
   is re-formatted from its artifact in the figure's own format spec and asserted present -- the
   `present()` idiom from `test_structure_examples.py:57`, containment rather than extraction.
3. **A colour is hard-coded.** An inline SVG inherits the page's variables and a standalone one
   cannot, so each figure carries exactly one token block. Outside it, a literal colour would
   render one theme's ink on the other theme's ground.
4. **The two themes diverge.** The light and dark files must differ ONLY in their token blocks.
5. **Something is drawn outside the frame, or a label runs off the edge.** The fallback font is
   wider than IBM Plex (see `svgkit`'s docstring), so label overflow is a live risk on the very
   readers who have the worst fonts. Estimated rather than measured, deliberately conservatively.
6. **The build is not deterministic.** A `set` iterated while emitting produces a different file
   every process. This is not hypothetical: it happened on the first build of the first figure,
   and `--check` declared its own fresh output stale.

Per-figure content invariants -- the assertions that are the CLAIM rather than the mechanics --
live in `tests/unit/test_figure_<name>.py` beside each builder.
"""

from __future__ import annotations

import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIGURES = REPO / "docs" / "figures"
BUILD_ALL = REPO / "scripts" / "figures" / "build_all.py"

TOKENS = re.compile(r"/\* TOKENS:START.*?TOKENS:END \*/.*?(?=\ntext\{)", re.S)
HEX = re.compile(r"#[0-9A-Fa-f]{3,8}")
FUNC = re.compile(r"\b(?:rgba?|hsla?)\(")
PAINTED = re.compile(r'(?:fill|stroke|stop-color|flood-color|color|style)="([^"]*)"')
USED = re.compile(r"var\((--[a-z-]+)\)")
TEXT = re.compile(
    r'<text x="([\d.-]+)" y="([\d.-]+)" text-anchor="(\w+)" font-size="([\d.]+)"[^>]*>(.*?)</text>'
)
VIEWBOX = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')

# A wide fallback: `sans-serif` where IBM Plex Sans Condensed was asked for. 0.62em per character
# is above the average advance of DejaVu Sans, which is the widest thing a Linux reader is
# realistically served. Over-estimating is the safe direction -- it fails a label that would have
# just fitted, and never passes one that runs off.
EM_PER_CHAR = 0.62


def _module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def build_all():
    return _module(BUILD_ALL)


@pytest.fixture(scope="session")
def rendered(build_all) -> dict[Path, str]:
    return build_all.render_all()


def _svgs() -> list[Path]:
    return sorted(FIGURES.glob("*.svg"))


def _ids(paths: list[Path]) -> list[str]:
    return [p.name for p in paths]


FILES = _svgs()


def body(svg: str) -> str:
    """Everything outside the one declared token block."""
    assert len(TOKENS.findall(svg)) == 1, "a figure carries exactly one token block"
    return TOKENS.sub("", svg)


# --------------------------------------------------------------------------- currency


def test_at_least_one_figure_exists():
    assert FILES, (
        "docs/figures/ is empty. Run `python scripts/figures/build_all.py --build`."
    )


def test_every_committed_figure_is_current(rendered):
    stale = sorted(
        p.name
        for p, want in rendered.items()
        if not p.exists() or p.read_text(encoding="utf-8") != want
    )
    assert not stale, (
        f"{len(stale)} figure file(s) no longer match their builder: {stale}. "
        "Regenerate them: `python scripts/figures/build_all.py --build`."
    )


def test_no_figure_file_is_orphaned(rendered):
    """A file in the directory that no registered builder writes.

    The mirror of the currency test, and the shape a renamed slug leaves behind: the new pair
    builds and the old pair sits there for ever, indexed, linked and never regenerated again.
    """
    orphans = sorted({p.name for p in FILES} - {p.name for p in rendered})
    assert not orphans, (
        f"docs/figures/ holds {orphans}, which no builder in build_all.BUILDERS writes. "
        "Either register the builder or delete the files."
    )


def test_the_build_is_deterministic(tmp_path):
    """Two processes, two hash seeds, one output.

    An in-process double build cannot catch this: `PYTHONHASHSEED` is fixed for the life of a
    process, so a `set` iterated while emitting gives the same wrong answer twice. It has to be
    a subprocess, and it has to be two seeds.
    """
    outs = []
    for seed in ("1", "2"):
        env = os.environ | {"PYTHONHASHSEED": seed}
        proc = subprocess.run(
            [sys.executable, str(BUILD_ALL), "--check"],
            cwd=REPO,
            env=env,
            capture_output=True,
            text=True,
        )
        outs.append((seed, proc.returncode, proc.stdout))
    assert outs[0][1] == 0 and outs[1][1] == 0, (
        "the committed figures are not reproducible under a different hash seed — something "
        f"iterates a set while emitting.\nseed 1: {outs[0][2]}\nseed 2: {outs[1][2]}"
    )


# ----------------------------------------------------------------------------- colour


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_no_colour_outside_the_token_block(path: Path):
    inner = body(path.read_text(encoding="utf-8"))
    for value in PAINTED.findall(inner):
        assert not HEX.search(value), f"hard-coded colour {value!r} in {path.name}"
        assert not FUNC.search(value), f"literal colour function {value!r} in {path.name}"
        assert re.fullmatch(r"none|var\(--[a-z-]+\)", value), (
            f"{value!r} in {path.name} is not a token — figures paint with var(--x) or nothing"
        )
    assert not HEX.search(inner), f"a hex literal escaped the paint attributes in {path.name}"


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_every_token_used_is_declared(path: Path):
    svg = path.read_text(encoding="utf-8")
    declared = set(re.findall(r"(--[a-z-]+):", TOKENS.search(svg).group(0)))
    undeclared = sorted(set(USED.findall(body(svg))) - declared)
    assert not undeclared, (
        f"{path.name} paints with {undeclared}, which its token block does not declare — "
        "they would resolve to nothing and the shape would vanish."
    )


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_the_token_block_is_the_reports_palette(path: Path, build_all):
    light, dark = build_all.k.palette()
    want = dark if path.name.endswith(".dark.svg") else light
    block = TOKENS.search(path.read_text("utf-8")).group(0)
    # The FIRST `svg{...}` rule only. The light file also carries a dark `@media` block, so
    # scanning the whole token block would read the dark values over the light ones and compare
    # a figure against the palette it is not drawn in.
    base = re.search(r"\nsvg\{(.*?)\}", block, re.S).group(1)
    declared = dict(re.findall(r"(--[a-z-]+):([^;}]+)", base))
    for token, value in want.items():
        assert declared.get(token) == value, (
            f"{path.name} declares {token}={declared.get(token)!r} where "
            f"docs/results/final_report.html says {value!r}. Rebuild the figures."
        )


def test_the_report_declares_one_dark_palette(build_all):
    """`final_report.html` states the dark values twice, 25 lines apart, and nothing checked
    that the copies agreed until the figures had to choose between them."""
    build_all.k.palette()  # raises SystemExit naming every diverged token


def test_the_light_and_dark_figures_differ_only_in_their_tokens():
    pairs = [(p, p.with_suffix(".dark.svg")) for p in FILES if not p.name.endswith(".dark.svg")]
    assert pairs, "no light/dark pairs found"
    for light, dark in pairs:
        assert dark.exists(), f"{light.name} has no dark twin"
        assert body(light.read_text("utf-8")) == body(dark.read_text("utf-8")), (
            f"{light.name} and {dark.name} differ outside their token blocks — a theme-specific "
            "tweak has crept into the drawing, which is what this arrangement exists to prevent."
        )


# --------------------------------------------------------------------------- geometry


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_nothing_is_drawn_outside_the_frame(path: Path):
    svg = path.read_text(encoding="utf-8")
    width, height = (float(v) for v in VIEWBOX.search(svg).groups())
    inner = body(svg)

    for x, y, w, h in re.findall(
        r'<rect x="([\d.-]+)" y="([\d.-]+)" width="([\d.-]+)" height="([\d.-]+)"', inner
    ):
        assert -1 <= float(x) and float(x) + float(w) <= width + 1, f"rect off frame in {path.name}"
        assert -1 <= float(y) and float(y) + float(h) <= height + 1, f"rect off frame in {path.name}"

    for cx, cy, r in re.findall(r'<circle cx="([\d.-]+)" cy="([\d.-]+)" r="([\d.]+)"', inner):
        assert -1 <= float(cx) - float(r) and float(cx) + float(r) <= width + 1, f"circle off frame in {path.name}"
        assert -1 <= float(cy) - float(r) and float(cy) + float(r) <= height + 1, f"circle off frame in {path.name}"

    for pts in re.findall(r'<polyline points="([^"]+)"', inner):
        for pair in pts.split():
            px, py = (float(v) for v in pair.split(","))
            assert -1 <= px <= width + 1 and -1 <= py <= height + 1, (
                f"polyline point {pair} outside the {width:.0f}x{height:.0f} frame in {path.name}"
            )

    for x1, y1, x2, y2 in re.findall(
        r'<line x1="([\d.-]+)" y1="([\d.-]+)" x2="([\d.-]+)" y2="([\d.-]+)"', inner
    ):
        for v, limit in ((x1, width), (x2, width), (y1, height), (y2, height)):
            assert -1 <= float(v) <= limit + 1, f"line endpoint off frame in {path.name}"


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_no_label_runs_off_the_edge(path: Path):
    """Estimated width, because the font that renders is not the font that was asked for.

    A standalone SVG gets no webfont, `"Arial Narrow"` is absent on most Linux and Android, and
    the substitute is wider. This estimates generously and fails the label rather than the
    reader.
    """
    svg = path.read_text(encoding="utf-8")
    width, _ = (float(v) for v in VIEWBOX.search(svg).groups())
    for x, _y, anchor, size, label in TEXT.findall(body(svg)):
        run = len(re.sub(r"&#?\w+;", "x", label)) * float(size) * EM_PER_CHAR
        left = {"start": float(x), "middle": float(x) - run / 2, "end": float(x) - run}[anchor]
        assert left >= -1 and left + run <= width + 1, (
            f"{path.name}: {label[:44]!r} spans {left:.0f}..{left + run:.0f} in a "
            f"{width:.0f}-wide frame at the fallback font. Shorten it or move it."
        )


# ---------------------------------------------------------------- portability and hygiene


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_the_figure_is_self_contained(path: Path):
    """Nothing a host will strip, and nothing that needs the network.

    GitHub sanitises SVG it serves. A figure that depends on any of these degrades silently --
    which is worse than failing, because it still looks like a figure.
    """
    svg = path.read_text(encoding="utf-8")
    for forbidden in ("<script", "<foreignObject", "<image", "xlink:href", "@import", "url(http"):
        assert forbidden not in svg, f"{path.name} contains {forbidden!r}, which a host will strip"


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_the_figure_is_described_for_a_reader_who_cannot_see_it(path: Path):
    svg = path.read_text(encoding="utf-8")
    assert svg.count("<title") == 1 and svg.count("<desc") == 1
    assert 'role="img"' in svg
    title = re.search(r"<title[^>]*>(.*?)</title>", svg, re.S).group(1)
    desc = re.search(r"<desc[^>]*>(.*?)</desc>", svg, re.S).group(1)
    assert len(title) >= 20, f"{path.name}: the title is not a sentence"
    assert len(desc) >= 60, f"{path.name}: the description does not describe anything"
    ids = re.search(r'aria-labelledby="([^"]+)"', svg).group(1).split()
    assert all(f'id="{i}"' in svg for i in ids), f"{path.name}: aria-labelledby names a missing id"


def test_no_two_figures_share_an_id():
    """They collide the day two of them are inlined into one page, and the failure is silent."""
    seen: dict[str, str] = {}
    for path in FILES:
        for element_id in re.findall(r'id="([^"]+)"', path.read_text(encoding="utf-8")):
            if path.name.endswith(".dark.svg"):
                continue  # a figure and its own dark twin are never on one page
            assert element_id not in seen, (
                f"{path.name} and {seen[element_id]} both use id={element_id!r}"
            )
            seen[element_id] = path.name


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_the_figure_fits_in_a_readme(path: Path):
    size = path.stat().st_size
    assert size <= 250_000, f"{path.name} is {size:,} bytes; the budget is 250,000"


@pytest.mark.parametrize("path", FILES, ids=_ids(FILES))
def test_the_figure_names_its_own_source_and_generator(path: Path):
    """The convention every generated artifact here follows, and an SVG needs it most: it is the
    one artifact that travels away from the page that embedded it."""
    svg = path.read_text(encoding="utf-8")
    assert "scripts/figures/build_" in svg, f"{path.name} does not name its generator"
    assert "tests/unit/test_figures.py" in svg, f"{path.name} does not name its gate"
