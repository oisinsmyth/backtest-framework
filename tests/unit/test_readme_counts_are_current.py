"""The README's inventory block matches the repository it describes.

**This test exists because an audit of twenty repack commits found ~38 stale factual claims, and
the single largest cause was counts typed by hand.** Two were wrong in a way worth recording: the
README said 741 decision records and 586 scripts, because they had been counted off the working
tree while six deletions sat uncommitted. A clone gets 743 and 588 — and the README is a document
about what a clone gets.

Everything gated here is deterministic and cheap, derived from `git ls-files` by
`scripts/build_readme_counts.py`. Runtimes and the clone pass/skip split are **not** gated: they
are machine-dependent (the same suite measured 6m21s and 7m00s on one laptop within a day), so the
README carries those as prose with a measurement date. A gate that reddens on a slower machine
teaches people to ignore gates.

Like `test_decision_index_is_complete.py`, this asserts **currency, not format** — it compares the
generated block against the committed one and names the command that fixes a mismatch.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
README = REPO / "README.md"
BUILDER = REPO / "scripts" / "build_readme_counts.py"


def _builder():
    spec = importlib.util.spec_from_file_location("build_readme_counts", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _builder()


def test_the_readme_counts_block_is_current(builder):
    text = README.read_text(encoding="utf-8")
    assert builder.START in text and builder.END in text, (
        "README.md has no COUNTS block. Run "
        "`python scripts/build_readme_counts.py --build`."
    )

    committed = builder.START + text.split(builder.START, 1)[1].split(builder.END, 1)[0] + builder.END
    assert committed.strip() == builder.render().strip(), (
        "The README's inventory no longer matches the repository. Regenerate it: "
        "`python scripts/build_readme_counts.py --build`."
    )


def test_the_counts_come_from_the_index_and_not_the_filesystem(builder):
    """The specific error this whole mechanism exists to prevent.

    A file that is tracked but deleted in the worktree is still in a clone. If the builder ever
    switches to globbing the filesystem, this test goes quiet while the README starts describing
    one developer's uncommitted state — which is exactly what happened, twice, in one README.
    """
    source = BUILDER.read_text(encoding="utf-8")
    assert "git" in source and "ls-files" in source, (
        "build_readme_counts.py no longer consults the git index"
    )
    counts = builder.counts()
    on_disk = len([p for p in (REPO / "scripts").glob("*.py")])
    assert counts["scripts"] >= on_disk, (
        f"index reports {counts['scripts']} scripts, filesystem {on_disk} — the index should "
        "include tracked files deleted locally, so it can never be the smaller number"
    )
