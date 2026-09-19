"""The figures on `docs/RUNNING.md` that CAN be checked, are (D548).

This page exists to hold the numbers no gate can hold. Moving it off the front page was the
occasion to find out how true that was, and the answer was worse than the claim: **seven figures
were perturbed one at a time and the suite stayed green on all seven** — the clone's pass and
skip counts, the 85-character path limit, "49 of the 53", the manifest's 118 panels and 115 blob
ids, and D536's 844 MB. Not one had a gate. The counts sweep in
`tests/unit/test_quoted_counts_are_current.py` covers quantities it can compute from the git
index — records, tests, scripts, modules, `raise` statements — and none of these is one of them.

Three of the seven ARE computable, and this file pins them. The rest genuinely are not, and the
docstring says which rather than leaving the page looking better covered than it is:

| figure | why it has no gate |
|---|---|
| the runtimes (3m48s–5m52s, 5m45s) | a property of the machine and the moment |
| the clone's 2,017 passed / 53 skipped | needs a clone; the suite cannot measure it from inside the working copy |
| "49 of the 53 skips name a file" | the 53 is a clone property, so the ratio inherits it |
| D536's 844 MB / 969 MB / 1.1 GB | history, not the current tree |

Anchored the way `tests/unit/test_narrative_D190_D544.py` anchors the results page: the literal
as it appears in the prose, beside a callable that RECOMPUTES it from the artifact. A number
checked against a hard-coded copy of itself is two copies of one fact, which is the defect this
repository names most often.
"""

import json
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PAGE = REPO / "docs" / "RUNNING.md"
MANIFEST = REPO / "data" / "data_manifest.json"


def _manifest() -> list[dict]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]


def _panels() -> int:
    return len(_manifest())


def _panels_with_a_blob() -> int:
    return sum(1 for f in _manifest() if f.get("git_blob"))


def _longest_tracked_path() -> int:
    listed = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    return max(len(p) for p in listed)


# (label, the literal as the prose spells it, what recomputes it)
ANCHORS: list[tuple[str, str, Callable[[], int]]] = [
    ("panels in the manifest", "118", _panels),
    ("panels carrying a git blob id", "115", _panels_with_a_blob),
    ("longest tracked path", "85", _longest_tracked_path),
]

# A floor. A parametrized gate over an empty list collects nothing and fails nothing -- six gates
# in this repository were found that way, including the one whose job was keeping a document
# honest.
MINIMUM_ANCHORS = 3


def test_the_page_exists_and_is_not_a_stub():
    assert PAGE.exists(), f"{PAGE.relative_to(REPO)} is gone; README and CONTRIBUTING point at it"
    assert len(PAGE.read_text(encoding="utf-8").splitlines()) > 40, (
        "the page has been emptied rather than edited; the figures below would then pass by "
        "matching nothing"
    )


def test_the_anchor_list_is_not_empty():
    assert len(ANCHORS) >= MINIMUM_ANCHORS, (
        f"only {len(ANCHORS)} anchor(s); the parametrized check below would collect "
        f"{len(ANCHORS)} case(s) and report green while checking almost nothing"
    )


@pytest.mark.parametrize("label,literal,recompute", ANCHORS, ids=[a[0] for a in ANCHORS])
def test_every_checkable_figure_matches_its_source(label, literal, recompute):
    prose = PAGE.read_text(encoding="utf-8")
    actual = recompute()
    assert str(actual) == literal, (
        f"{label}: docs/RUNNING.md is written around {literal!r} and the source now says "
        f"{actual}. Update the prose and this anchor together."
    )
    assert re.search(rf"\b{re.escape(literal)}\b", prose), (
        f"{label}: {literal!r} no longer appears in docs/RUNNING.md, so this anchor is checking "
        f"a sentence that is not there. Either the prose was rewritten -- in which case re-anchor "
        f"it -- or the figure was dropped."
    )


def test_the_three_panels_without_a_blob_are_the_ones_named():
    """A count can hold while the identities drift; the page names all three, so check the set.

    This is the stronger half: `115` would still pass if a different panel lost its blob and
    another gained one, and the page's three filenames would then be wrong while its number was
    right.
    """
    prose = PAGE.read_text(encoding="utf-8")
    without = sorted(f["path"] for f in _manifest() if not f.get("git_blob"))
    missing = [p for p in without if p not in prose]
    assert not missing, (
        f"these panels have no git blob id and docs/RUNNING.md does not name them: {missing}. "
        f"The page tells a reader which artifacts are unrecoverable; that list is the point."
    )
    assert len(without) == 3, (
        f"{len(without)} panels now have no blob id, and the page's prose says three. The count "
        f"and the names have to move together."
    )
