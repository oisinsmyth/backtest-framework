"""`docs/figures/README.md` lists every figure, and every figure it lists exists.

The third of these guards, after `test_decision_index_is_complete.py` and
`test_results_index_is_complete.py`. The failure it exists to catch has happened twice in this
repository already: a directory grows, the index prose is updated to say the new things arrived,
and some of them are listed nowhere. A fifth of `docs/results/` was invisible that way.

`scripts/check_doc_links.py` cannot catch it, and the reason is worth restating because it is the
same reason both times: a link checker verifies that links RESOLVE, not that documents are LINKED.
A figure nobody links to is not a broken link. It is just gone.

There is a third direction here that the other two indexes do not have, because a figure is the
only artifact in this repository that is *displayed* rather than read: an `<img>` with no `alt` is
a figure that does not exist for anyone using a screen reader, and `alt="chart.svg"` is worse than
none because it looks like someone thought about it.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIGURES = REPO / "docs" / "figures"
INDEX = FIGURES / "README.md"

LINK = re.compile(r"\]\(([A-Za-z0-9_./-]+\.svg)\)")
IMG = re.compile(r"<img\b([^>]*)>", re.S)
ATTR = re.compile(r'(\w[\w-]*)="([^"]*)"')


def _present() -> set[str]:
    """The light figures. A dark twin is not a separate figure and is not indexed separately;
    `tests/unit/test_figures.py` is what holds the two together."""
    return {p.name for p in FIGURES.glob("*.svg") if not p.name.endswith(".dark.svg")}


def _listed() -> set[str]:
    return set(LINK.findall(INDEX.read_text(encoding="utf-8")))


def test_every_figure_is_in_the_index():
    missing = sorted(_present() - _listed())
    assert not missing, (
        f"{len(missing)} figure(s) in docs/figures/ are not listed in its index: {missing}. "
        "Add a row to the table in docs/figures/README.md."
    )


def test_the_index_does_not_list_a_figure_that_is_not_there():
    phantom = sorted({n for n in _listed() if "/" not in n} - _present())
    assert not phantom, f"docs/figures/README.md lists figures that do not exist: {phantom}"


def test_every_figure_is_registered_with_a_builder():
    """The index and the build registry must describe the same set.

    A figure listed in the gallery but absent from `build_all.BUILDERS` is never regenerated and
    never checked — it would sit there going quietly out of date while every gate stayed green.
    """
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(
        "build_all", REPO / "scripts" / "figures" / "build_all.py"
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    registered = {m.SLUG + ".svg" for m in module.modules()}
    assert registered == _present(), (
        f"the registry and the directory disagree: only registered {sorted(registered - _present())}, "
        f"only on disk {sorted(_present() - registered)}"
    )
    assert registered == _listed() - {n for n in _listed() if "/" in n}, (
        "the registry and the gallery index disagree"
    )


def test_every_embedded_figure_is_described():
    """An `<img>` without a usable `alt` is a figure that does not exist for some readers."""
    for doc in sorted(REPO.glob("*.md")) + sorted(REPO.glob("docs/**/*.md")):
        text = doc.read_text(encoding="utf-8", errors="replace")
        for raw in IMG.findall(text):
            attrs = dict(ATTR.findall(raw))
            src = attrs.get("src", "")
            if "docs/figures/" not in src and "/figures/" not in src:
                continue
            alt = attrs.get("alt", "").strip()
            where = doc.relative_to(REPO).as_posix()
            assert alt, f"{where}: <img src={src}> has no alt text"
            assert Path(src).name.lower() not in alt.lower(), (
                f"{where}: alt={alt!r} is the filename, which describes nothing"
            )
            assert len(alt) >= 40, (
                f"{where}: alt={alt!r} is too short to stand in for the figure it replaces"
            )
