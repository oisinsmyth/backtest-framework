"""The vocabulary the repository's figures are written in.

    python scripts/figures/build_all.py --build     # write every figure
    python scripts/figures/build_all.py --check     # fail if any committed file has drifted

THIS IS A VOCABULARY, NOT A FRAMEWORK
-------------------------------------
It owns the document wrapper, the palette, two scales and the primitive elements -- the things
that must be identical across every figure or the set stops looking like one set. It owns **no
chart types**. Each figure's geometry is its own content, written out in its own builder where
`tests/unit/test_figures.py` can recompute it against the claim the figure makes.

Deliberately absent, each for a reason: tick-choosing algorithms (an axis whose labels an
algorithm chose is an axis nobody checked, and the test pinning them would have to re-run the
algorithm to know what to expect, which pins nothing); any Chart/Series/Axis object graph (six
figures is below the threshold where the abstraction pays, and a dumbbell chart and a waterfall
share nothing structural); legend layout and text measurement (labels are short and hand-placed
-- see THE FONTS WILL NOT BE IBM PLEX below); colour ramps; and `<defs>`, `<use>`, gradients and
transforms, each of which would defeat the geometry gate's ability to bound-check a `<rect>` by
reading its own attributes.

THE PALETTE IS PARSED, NEVER TYPED
----------------------------------
`docs/results/final_report.html` declares the tokens three times -- `:root`, a
`prefers-color-scheme` block and a `[data-theme]` block. Typing them here would make a fourth
copy, and the figures would drift from the report the first time anyone adjusted a hue.
`build_structure_examples_report.py:223` already lifts that stylesheet verbatim; this parses it.

`palette()` also RAISES if the report's two dark declarations have diverged. That gate did not
exist before these figures needed it, and the drift it catches is in the flagship document.

COLOURS CANNOT BE INVENTED, STRUCTURALLY
----------------------------------------
Every drawing function takes a TOKEN NAME (`"--brass"`), not a colour. A hex literal and a
`var(--gain)` copied from the other report's palette both raise at build time, naming the legal
tokens. `tests/unit/test_figures.py` asserts the same thing over the emitted file, but the API is
the first line of defence rather than the only one -- which is this repository's thesis applied
to its own tooling.

A STANDALONE SVG CARRIES ITS OWN TOKENS, AND THAT IS THE ONE PLACE A HEX MAY APPEAR
----------------------------------------------------------------------------------
The existing chart gate (`tests/unit/test_structure_examples.py:266`) forbids literal colour
outright, because an inline SVG inherits the page's variables. A file referenced by `<img>` is an
independent document and cannot. So each figure carries exactly one `TOKENS:START/END` block, the
test excises it, and forbids hex, `rgb()`, `hsl()` and named colours everywhere else.

Two files per figure, `<name>.svg` and `<name>.dark.svg`, selected by `<picture media=...>`:
`prefers-color-scheme` inside an `<img>`-loaded SVG is unreliable, while `<picture>` is evaluated
by the host document. The light file carries the dark media query anyway so it is correct when
opened on its own. The bodies are byte-identical, which the gate asserts -- a theme-specific tweak
in a drawing is a test failure.

THE FONTS WILL NOT BE IBM PLEX
------------------------------
A standalone SVG on a host like GitHub gets no external resources, so the fallback chain is what
renders, and `"Arial Narrow"` is absent on most Linux and Android -- those readers get plain
`sans-serif`, which is WIDER than a condensed face. Treat it as a hard constraint: no tight label
packing, no right-aligned numeric columns assuming tabular figures, generous slack around every
label, and nothing whose meaning depends on two labels not colliding.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, Sequence

REPO = Path(__file__).resolve().parent.parent.parent
TOKEN_SOURCE = REPO / "docs" / "results" / "final_report.html"
FIGURES = REPO / "docs" / "figures"

TOKENS_START = "/* TOKENS:START"
TOKENS_END = "TOKENS:END */"

_LIGHT = re.compile(r"^  :root \{\n(.*?)^  \}", re.S | re.M)
_MEDIA = re.compile(r':root:not\(\[data-theme="light"\]\) \{(.*?)\n    \}', re.S)
_ATTR = re.compile(r':root\[data-theme="dark"\] \{(.*?)\n  \}', re.S)
_DECL = re.compile(r"(--[a-z-]+):\s*([^;]+);")

# The tokens a figure may name. `--serif`, `--measure` and `--wide` are the report's prose
# furniture and have no meaning inside a chart, so they are not carried into the figures.
COLOURS = (
    "--paper",
    "--surface",
    "--sunk",
    "--ink",
    "--muted",
    "--faint",
    "--rule",
    "--brass",
    "--brass-soft",
    "--slate",
)
FONTS = ("--cond", "--mono")

# ORDERED, and the order is load-bearing. `LEGAL` was a frozenset for one build, and the token
# block came out in a different order in every process -- `--check` called the builder it had
# just run and declared its own output stale. Membership tests read the set; anything that EMITS
# iterates the tuple.
ORDER = COLOURS + FONTS
LEGAL = frozenset(ORDER)

Theme = Literal["light", "dark"]


# --------------------------------------------------------------------------- palette


def _declarations(block: str) -> dict[str, str]:
    return {k: " ".join(v.split()) for k, v in _DECL.findall(block)}


def palette() -> tuple[dict[str, str], dict[str, str]]:
    """`(light, dark)`, read out of `final_report.html`.

    Raises if the report's two dark declarations disagree. They are 25 lines apart, contain the
    same ten values, and nothing checked them until this function did.
    """
    src = TOKEN_SOURCE.read_text(encoding="utf-8")
    for name, pattern in (("light :root", _LIGHT), ("dark @media", _MEDIA), ("dark [data-theme]", _ATTR)):
        if pattern.search(src) is None:  # pragma: no cover - the report is committed
            raise SystemExit(f"{TOKEN_SOURCE.name}: could not find the {name} block")

    light = _declarations(_LIGHT.search(src).group(1))
    media = _declarations(_MEDIA.search(src).group(1))
    attr = _declarations(_ATTR.search(src).group(1))

    diverged = sorted(k for k in set(media) | set(attr) if media.get(k) != attr.get(k))
    if diverged:
        raise SystemExit(
            f"{TOKEN_SOURCE.name} declares the dark palette twice and the two copies have "
            f"diverged on {diverged}. Fix the report; the figures cannot choose between them."
        )

    dark = dict(light) | attr  # dark redeclares only the colours; the fonts come from :root
    missing = sorted(t for t in ORDER if t not in light)
    if missing:  # pragma: no cover - the report is committed
        raise SystemExit(f"{TOKEN_SOURCE.name}: :root is missing {missing}")
    return ({t: light[t] for t in ORDER}, {t: dark[t] for t in ORDER})


def token_block(theme: Theme) -> str:
    """The one place in a figure where a literal colour may appear.

    The light file carries the dark media query as well, so it renders correctly when opened on
    its own rather than through `<picture>`. The dark file does not: `<picture media=...>` has
    already made the choice, and a media query inside it could only undo that.
    """
    light, dark = palette()
    chosen = dark if theme == "dark" else light
    decls = "".join(f"{k}:{v};" for k, v in chosen.items()).rstrip(";")
    out = [
        f"{TOKENS_START} — parsed from docs/results/final_report.html by scripts/figures/svgkit.py.",
        "   The only place in this file a literal colour may appear; tests/unit/test_figures.py",
        f"   forbids one anywhere else. {TOKENS_END}",
        f"svg{{{decls}}}",
    ]
    if theme == "light":
        dark_decls = "".join(f"{k}:{v};" for k, v in dark.items() if k in COLOURS).rstrip(";")
        out.append(f"@media (prefers-color-scheme:dark){{svg{{{dark_decls}}}}}")
    out.append("text{font-family:var(--cond)}")
    return "\n".join(out)


# ------------------------------------------------------------------- frame and scales


@dataclass(frozen=True)
class Frame:
    """The plot rectangle. Margins are generous because the fallback font is wide."""

    width: float
    height: float
    left: float = 64.0
    right: float = 18.0
    top: float = 34.0
    bottom: float = 38.0

    @property
    def x0(self) -> float:
        return self.left

    @property
    def x1(self) -> float:
        return self.width - self.right

    @property
    def y0(self) -> float:
        return self.top

    @property
    def y1(self) -> float:
        return self.height - self.bottom

    @property
    def span_x(self) -> float:
        return self.x1 - self.x0

    @property
    def span_y(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class Scale:
    """A mapping from data to pixels. `a` is the pixel at `lo`, `b` the pixel at `hi`.

    For a vertical scale, pass `a` as the BOTTOM pixel and `b` as the top, which is how an
    inverted axis is expressed -- there is no `invert=` flag, because a flag is a thing to get
    backwards and the pixel arguments say what they mean.
    """

    lo: float
    hi: float
    a: float
    b: float
    log: bool = False

    def to(self, v: float) -> float:
        if self.log:
            t = (math.log10(v) - math.log10(self.lo)) / (math.log10(self.hi) - math.log10(self.lo))
        else:
            t = (v - self.lo) / (self.hi - self.lo)
        return self.a + t * (self.b - self.a)

    def contains(self, v: float) -> bool:
        return self.lo <= v <= self.hi


def linear(lo: float, hi: float, a: float, b: float, *, pad: float = 0.0) -> Scale:
    """`pad` widens the domain by a fraction of its span, so a series does not touch the frame."""
    if hi == lo:
        hi = lo + (abs(lo) * 1e-3 or 1.0)
    room = (hi - lo) * pad
    return Scale(lo - room, hi + room, a, b)


def log10(lo: float, hi: float, a: float, b: float) -> Scale:
    if lo <= 0 or hi <= 0:
        raise ValueError(f"a log scale needs positive bounds, got lo={lo}, hi={hi}")
    return Scale(lo, hi, a, b, log=True)


# ------------------------------------------------------------------------- elements


def c(v: float) -> str:
    """The one coordinate format. Defined once so twelve files cannot round differently."""
    return f"{v:.1f}"


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace(" ", "&#160;")
    )


def paint(token: str) -> str:
    if token not in LEGAL:
        raise ValueError(
            f"{token!r} is not a token in final_report.html's :root — the palette has "
            f"{sorted(LEGAL)}. Figures do not invent colours."
        )
    return f"var({token})"


def _opt(name: str, value: object) -> str:
    return "" if value is None else f' {name}="{value}"'


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = "--rule",
    w: float = 1.0,
    dash: str | None = None,
    opacity: float | None = None,
) -> str:
    return (
        f'<line x1="{c(x1)}" y1="{c(y1)}" x2="{c(x2)}" y2="{c(y2)}" '
        f'stroke="{paint(stroke)}" stroke-width="{w}"'
        f"{_opt('stroke-dasharray', dash)}{_opt('opacity', opacity)}/>"
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = "--slate",
    opacity: float | None = None,
    stroke: str | None = None,
    sw: float | None = None,
) -> str:
    return (
        f'<rect x="{c(x)}" y="{c(y)}" width="{c(w)}" height="{c(h)}" fill="{paint(fill)}"'
        f"{_opt('opacity', opacity)}"
        f"{'' if stroke is None else f' stroke=\"{paint(stroke)}\"'}"
        f"{_opt('stroke-width', sw)}/>"
    )


def circle(
    cx: float,
    cy: float,
    r: float,
    *,
    fill: str = "--brass",
    stroke: str | None = None,
    sw: float | None = None,
    opacity: float | None = None,
) -> str:
    return (
        f'<circle cx="{c(cx)}" cy="{c(cy)}" r="{r}" fill="{paint(fill)}"'
        f"{'' if stroke is None else f' stroke=\"{paint(stroke)}\"'}"
        f"{_opt('stroke-width', sw)}{_opt('opacity', opacity)}/>"
    )


def polyline(
    points: Sequence[tuple[float, float]],
    *,
    stroke: str = "--slate",
    w: float = 1.6,
    dash: str | None = None,
    opacity: float | None = None,
) -> str:
    pts = " ".join(f"{c(x)},{c(y)}" for x, y in points)
    return (
        f'<polyline points="{pts}" fill="none" stroke="{paint(stroke)}" stroke-width="{w}"'
        f"{_opt('stroke-dasharray', dash)}{_opt('opacity', opacity)}/>"
    )


def text(
    x: float,
    y: float,
    s: str,
    *,
    anchor: str = "start",
    size: float = 9.0,
    fill: str = "--muted",
    track: float | None = 0.06,
    family: str = "--cond",
    weight: int | None = None,
) -> str:
    if family not in FONTS:
        raise ValueError(f"{family!r} is not a font token; the figures have {list(FONTS)}")
    ls = "" if track is None else f' letter-spacing="{track}em"'
    fam = "" if family == "--cond" else f' font-family="{paint(family)}"'
    return (
        f'<text x="{c(x)}" y="{c(y)}" text-anchor="{anchor}" font-size="{size}" '
        f'fill="{paint(fill)}"{ls}{fam}{_opt("font-weight", weight)}>{esc(s)}</text>'
    )


# ------------------------------------------------------- the two things every figure repeats


def gridlines(
    frame: Frame,
    y: Scale,
    values: Sequence[float],
    *,
    fmt: Callable[[float], str] = lambda v: f"{v:g}",
) -> str:
    """Horizontal rules with a right-aligned label in the left margin.

    `values` is given by the figure. Nothing here chooses ticks -- see the module docstring.
    """
    out: list[str] = []
    for v in values:
        py = y.to(v)
        out.append(line(frame.x0, py, frame.x1, py, stroke="--rule"))
        out.append(text(frame.x0 - 8, py + 3.2, fmt(v), anchor="end", fill="--faint", track=None))
    return "".join(out)


def rule_at(
    frame: Frame,
    x: Scale,
    v: float,
    label: str,
    *,
    stroke: str = "--brass",
    dash: str | None = "4 3",
    anchor: str = "start",
    dy: float = 0.0,
) -> str:
    """A labelled vertical rule -- a threshold, a tolerance, a crossing."""
    px = x.to(v)
    nudge = 4 if anchor == "start" else -4
    return line(px, frame.y0, px, frame.y1, stroke=stroke, w=1.0, dash=dash) + text(
        px + nudge, frame.y0 - 6 + dy, label, anchor=anchor, fill=stroke, size=8.5, track=0.08
    )


# ------------------------------------------------------------------------- the document


def document(
    *,
    frame: Frame,
    slug: str,
    title: str,
    desc: str,
    source: str,
    generator: str,
    body: str,
    theme: Theme,
) -> str:
    """One figure, as a complete standalone SVG document.

    The footer naming `source` and `generator` is not decoration: an SVG travels away from the
    page that embedded it, and this repository's convention is that a generated artifact names
    its own generator and its own gate in its own text.
    """
    ids = f"t-{slug} d-{slug}"
    return (
        f'<svg viewBox="0 0 {c(frame.width)} {c(frame.height)}" width="{c(frame.width)}" '
        f'height="{c(frame.height)}" role="img" xmlns="http://www.w3.org/2000/svg" '
        f'aria-labelledby="{ids}">\n'
        f"<!-- generated by {generator} from {source}; "
        f"tests/unit/test_figures.py fails if this file drifts -->\n"
        f'<title id="t-{slug}">{esc(title)}</title>\n'
        f'<desc id="d-{slug}">{esc(desc)}</desc>\n'
        f"<style>\n{token_block(theme)}\n</style>\n"
        f'<rect x="0" y="0" width="{c(frame.width)}" height="{c(frame.height)}" '
        f'fill="{paint("--paper")}"/>\n'
        f"{body}\n"
        + text(
            frame.width / 2,
            frame.height - 9,
            f"{source}  ·  {generator}",
            anchor="middle",
            size=7.0,
            fill="--faint",
            track=0.05,
        )
        + "\n</svg>\n"
    )


def write(slug: str, render: Callable[[Theme], str]) -> dict[Path, str]:
    """`{path: content}` for a figure's two files. Callers compare or write; this never does."""
    return {
        FIGURES / f"{slug}.svg": render("light"),
        FIGURES / f"{slug}.dark.svg": render("dark"),
    }
