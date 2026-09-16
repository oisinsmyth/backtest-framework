"""Every study document in `docs/results/` appears in its index, and every index row resolves.

**This test is the generalisation I failed to make.** `test_decision_index_is_complete.py` was
written because the decision index silently stopped being true for 251 numbers. One round later
`docs/results/README.md` did exactly the same thing: fourteen documents moved in, the index prose
was updated to say they had arrived, and **twelve of them were listed nowhere** — a fifth of the
directory, invisible.

Nothing could have caught it. `scripts/check_doc_links.py` verifies that links *resolve*, not that
documents are *linked*; a document nobody links to is not a broken link. The absence of this file
was the whole defect.

Like its sibling it asserts **coverage, not format** — the index groups studies into themed tables
and that shape should stay free to change.

`archive/` is excluded deliberately: `archive/breakout_v1/BREAKOUT_RESULTS.md` is a superseded run
kept for history, and the index mentions it in prose rather than listing it as a study.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "docs" / "results"
INDEX = RESULTS / "README.md"

LINK = re.compile(r"\]\(([A-Za-z0-9_./-]+\.(?:md|html))\)")


def _documents_present() -> set[str]:
    return {
        path.name
        for pattern in ("*.md", "*.html")
        for path in RESULTS.glob(pattern)
        if path.name != "README.md"
    }


def _documents_linked() -> set[str]:
    return set(LINK.findall(INDEX.read_text(encoding="utf-8")))


def test_every_study_document_is_in_the_index():
    missing = sorted(_documents_present() - _documents_linked())
    assert not missing, (
        f"{len(missing)} document(s) in docs/results/ are not linked from its index: {missing}. "
        "Add them to the full log in docs/results/README.md."
    )


def test_the_index_does_not_link_a_document_that_is_not_there():
    """The other direction — a row surviving a rename or a deletion.

    Restricted to bare filenames so the index stays free to link out of the directory; those
    targets are `scripts/check_doc_links.py`'s business.
    """
    local = {name for name in _documents_linked() if "/" not in name}
    phantom = sorted(local - _documents_present())
    assert not phantom, f"index links documents that do not exist: {phantom}"
