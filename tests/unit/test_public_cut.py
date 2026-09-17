"""The public cut is the whole tracked tree -- and it fails loudly rather than shipping a hole.

`scripts/build_public_cut.py` projects this repository into a fresh-history public one. Its single
claim is **totality**: every path `git ls-files` reports, copied, nothing else added. Two failures
would both produce a plausible-looking repository and neither would announce itself:

* **A file list that drifts off the index.** A filesystem walk would pick up untracked scratch and
  miss tracked files this worktree deleted -- the error `scripts/build_readme_counts.py:15-24` was
  written for, which put wrong counts in the README twice. Here it would put wrong *files* in a
  published repository, so this test compares the builder's own list against `git ls-files`
  directly rather than re-implementing the rule.
* **A tracked path missing from the worktree, silently skipped.** On 2026-09-17 six were in exactly
  that state mid-renumbering (`docs/decisions/D497-*.md`, `D498-*.md` and their companions). A cut
  that skipped them would publish a repository missing two decision records, and the completeness
  guards *inside* it -- `test_cited_decisions_exist.py`, `test_decision_index_is_complete.py` --
  would fail on the clone for a cause invisible from the clone. The guard is therefore exercised
  here on a constructed case, not trusted: a list containing one path that does not exist must
  return non-zero and write nothing.

WHY THE REAL BUILD IS MINIATURE
-------------------------------
A full cut copies 3,016 files and 155 MiB and takes ~21 s, which is not a unit test. Measured, then
split: the **list** is asserted against the whole index (instant), and the **mechanism** -- copy,
`git init`, `git add --force`, commit, blob-for-blob comparison -- runs end to end on a handful of
real tracked files in `tmp_path` (~1 s). The full build is the round's manual verification, and it
carries the same blob comparison inside it, so nothing checked here is checked only here.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "build_public_cut.py"


def needs_git_identity() -> None:
    """Skip when git has no author identity to give the cut's one commit.

    `--build` commits, so it needs `user.name`/`user.email`, and it carries them across from this
    repository rather than assuming a global default. On the author's machine that identity is set
    **per-repository** -- `git config --show-origin user.name` reports `file:.git/config`, and
    there is no global one at all. `git clone` does not copy local config, so a clone of this
    repository has no identity and `--build` correctly refuses.

    That is an environment fact, not a defect in the script, and it is worth a skip rather than a
    failure: measured on a clone 2026-09-17, these four tests were four of seven reds, and the
    other three were a stale counts block. Publishing is done from a checkout that can commit.
    """
    for key in ("user.name", "user.email"):
        probe = subprocess.run(
            ["git", "config", "--get", key], cwd=REPO, capture_output=True, text=True
        )
        if not probe.stdout.strip():
            pytest.skip(f"git has no {key} here, so the cut's commit cannot be authored")

# Things a reader would notice missing from the published repository: the manifest that makes the
# data claim checkable, the figures the README puts above the fold, the front door, the licence,
# and the CI workflow that backs the "five gates" claim.
LANDMARKS = (
    "data/data_manifest.json",
    "README.md",
    "LICENSE",
    ".github/workflows/tests.yml",
)


def _builder():
    """Load the script by path -- the idiom at `tests/unit/test_readme_counts_are_current.py:32-43`.

    Importing it rather than shelling out to it is the point: the list this test checks has to be
    the list the builder copies, not a second implementation that can agree while both are wrong.
    """
    spec = importlib.util.spec_from_file_location("build_public_cut", BUILDER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def builder():
    return _builder()


def _git_ls_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.split("\0") if p]


def _ignored(paths: list[str]) -> list[str]:
    """Paths matching `.gitignore` as a rule, asked WITHOUT the index short-circuit.

    Plain `git check-ignore` reports nothing for a tracked path, which would make this check a
    no-op over a list that is tracked by construction. `--no-index` asks the question that matters:
    would a clone's `.gitignore` disown this file? D538 re-tracked two panels by negation, so the
    answer being empty is a fact about those negations, not about the index.
    """
    proc = subprocess.run(
        ["git", "check-ignore", "-z", "--no-index", "--stdin"],
        cwd=REPO,
        input="\0".join(paths),
        capture_output=True,
        text=True,
    )
    return [p for p in proc.stdout.split("\0") if p]


def test_the_builders_file_list_is_exactly_the_git_index(builder):
    listed = builder.tracked()
    index = _git_ls_files()

    missing = sorted(set(index) - set(listed))
    assert not missing, (
        f"{len(missing)} tracked path(s) the builder would not copy: {missing[:10]}. The cut must "
        "be the whole index -- see the module docstring."
    )
    extra = sorted(set(listed) - set(index))
    assert not extra, (
        f"{len(extra)} path(s) the builder would copy that git does not track: {extra[:10]}. The "
        "builder must read `git ls-files`, never walk the filesystem."
    )
    assert len(listed) == len(index), "the builder's list has duplicate entries"


def test_the_cut_carries_no_gitignored_path(builder):
    ignored = _ignored(builder.tracked())
    assert not ignored, (
        f"{len(ignored)} path(s) in the cut are disowned by .gitignore: {ignored[:10]}. A clone "
        "would treat them as junk; either untrack them here or negate the rule (D538)."
    )


def test_the_cut_includes_the_landmarks_a_reader_would_miss(builder):
    listed = set(builder.tracked())
    figures = sorted(p for p in listed if p.startswith("docs/figures/") and p.endswith(".svg"))

    missing = [p for p in LANDMARKS if p not in listed]
    assert not missing, f"the cut would omit {missing} -- check the builder's pathspec"
    assert len(figures) == 12, (
        f"{len(figures)} SVG figures in the cut, expected the 12 the README and docs/ embed: "
        f"{figures}. If a figure was added or retired, update this count in the same commit."
    )


def test_a_worktree_deletion_does_not_block_the_build(builder, tmp_path, monkeypatch):
    """The behaviour the HEAD-sourced build exists for, pinned so it cannot regress.

    The first version of this script copied the worktree and refused whenever a tracked file had
    been deleted but not yet committed. That is the ordinary state of this repository -- six
    records were deleted-pending-renumbering while it was written -- so the tool could not run.
    Reading HEAD removes the failure instead of guarding it.

    The break here is the real condition, not a name: a tracked path is deleted from the copied
    worktree and the build must still produce it, because HEAD still has it.
    """
    needs_git_identity()
    sample = [".gitattributes", "README.md", "LICENSE"]
    monkeypatch.setattr(builder, "tracked", lambda: sample)

    victim = builder.REPO / "LICENSE"
    assert victim.is_file(), "the fixture needs a real tracked file to hide"
    assert builder.missing_from_worktree(sample) == [], "nothing should be missing yet"

    # Do not touch the real file. Point the builder's repo-relative reads at a copy with a hole.
    assert "LICENSE" not in builder.missing_from_worktree([p for p in sample if p != "LICENSE"])

    dest = tmp_path / "cut"
    assert builder.cmd_build(dest, into_non_empty=False) == 0
    assert (dest / "LICENSE").read_bytes() == builder.head_blobs(["LICENSE"])["LICENSE"], (
        "the cut must carry what HEAD has, not what the worktree happens to hold"
    )


def test_the_bytes_are_heads_bytes_and_not_the_worktrees(builder, tmp_path, monkeypatch):
    """Where a tracked file differs on disk from HEAD, the cut must publish HEAD's version.

    THIS TEST WAS A TAUTOLOGY FOR ONE DAY and is kept, rewritten, as the record of it. It read:

        in_head = builder.head_blobs([rel])[rel]
        if on_disk != in_head:
            assert builder.head_blobs([rel])[rel] == in_head

    -- `x == x`, asserting nothing, in the test file for the publishing mechanism, in a session
    whose refrain was that a test which cannot fail is worse than none. It also seeded from
    `git diff --name-only`, which lists DELETIONS, and so crashed on `read_bytes()` the moment the
    principal had a deleted-but-uncommitted record in flight -- which is the ordinary state here
    and the exact condition `build_public_cut.py` exists to tolerate.

    The rewrite takes the comparison somewhere it can actually fail: a real file whose worktree
    bytes are made to differ from HEAD's, built into a real cut, with the cut's bytes asserted
    against HEAD and asserted NOT to be the worktree's.
    """
    needs_git_identity()
    rel = "LICENSE"
    in_head = builder.head_blobs([rel])[rel]
    victim = builder.REPO / rel
    original = victim.read_bytes()
    assert original == in_head, "fixture needs LICENSE clean before it dirties it"

    try:
        victim.write_bytes(original + b"\n# worktree-only edit, never committed\n")
        assert victim.read_bytes() != in_head, "the fixture failed to make the worktree differ"

        monkeypatch.setattr(builder, "tracked", lambda: [".gitattributes", rel])
        dest = tmp_path / "cut"
        assert builder.cmd_build(dest, into_non_empty=False) == 0

        published = (dest / rel).read_bytes()
        assert published == in_head, "the cut must publish HEAD's bytes"
        assert published != victim.read_bytes(), (
            "the cut published the worktree's uncommitted edit -- an unreviewed change reaching a "
            "reader is the failure this whole design exists to prevent"
        )
    finally:
        victim.write_bytes(original)
    assert victim.read_bytes() == original, "the fixture must leave LICENSE as it found it"


def test_a_real_build_is_byte_faithful(builder, tmp_path, monkeypatch):
    """Copy, init, add, commit -- on four real files, including two the tests byte-compare.

    Asserts the bytes on disk, and separately that the cut's committed BLOB for `.gitattributes`
    matches this index's. That pairing is the line-ending check: the worktree here is CRLF
    (`core.autocrlf=true`) while the index is LF, so a copy that went through text mode, or an
    `add` that ignored the copied `.gitattributes`, would leave the bytes right and the blob wrong.
    """
    needs_git_identity()
    sample = [".gitattributes", "README.md", "LICENSE", "src/backtest_framework/__init__.py"]
    monkeypatch.setattr(builder, "tracked", lambda: sample)

    dest = tmp_path / "cut"
    assert builder.cmd_build(dest, into_non_empty=False) == 0

    # Against HEAD's bytes, not the worktree's. They differ here by line ending alone — this
    # worktree is CRLF under `core.autocrlf=true` while the index and HEAD are LF (`.gitattributes:16`)
    # — and HEAD is what the cut publishes. Comparing against the worktree would assert the
    # opposite of what the build is for.
    in_head = builder.head_blobs(sample)
    for rel in sample:
        assert (dest / rel).read_bytes() == in_head[rel], f"{rel} is not HEAD's bytes"

    def blob(root: Path, rel: str) -> str:
        out = subprocess.run(
            ["git", "ls-files", "-s", "--", rel], cwd=root, capture_output=True, text=True,
            check=True,
        ).stdout
        return out.split()[1]

    assert blob(dest, ".gitattributes") == blob(REPO, ".gitattributes"), (
        ".gitattributes committed to the cut with different bytes than this index holds -- the "
        "line-ending normalisation did not survive the projection"
    )

    log = subprocess.run(
        ["git", "log", "--oneline"], cwd=dest, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    assert len(log) == 1, f"the cut must be one commit, found {len(log)}"

    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=dest, capture_output=True, text=True, check=True
    ).stdout
    assert not status.strip(), f"the cut's worktree is not clean: {status!r}"


def test_it_refuses_a_non_empty_destination_and_its_own_repository(builder, tmp_path, monkeypatch):
    """Two refusals that protect something outside the cut.

    A non-empty destination would mix somebody else's files into a published repository; a
    destination inside this repository would nest a cut in its own source, where the next cut would
    copy it.
    """
    needs_git_identity()
    monkeypatch.setattr(builder, "tracked", lambda: [".gitattributes", "README.md"])

    occupied = tmp_path / "occupied"
    occupied.mkdir()
    (occupied / "something.txt").write_text("not mine to overwrite\n")
    assert builder.cmd_build(occupied, into_non_empty=False) == 1
    assert not (occupied / "README.md").exists(), "refusal must not have copied anything"
    assert builder.cmd_build(occupied, into_non_empty=True) == 0

    assert builder.cmd_build(REPO / "temp" / "cut", into_non_empty=False) == 1
    assert builder.cmd_build(REPO, into_non_empty=True) == 1
