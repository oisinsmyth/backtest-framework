"""Every relative link in a tracked Markdown file must resolve to a file that exists.

    python scripts/check_doc_links.py            # all tracked .md
    python scripts/check_doc_links.py README.md docs/RULES.md

WHY THIS EXISTS
---------------
`docs/internal/` (D538) moved three documents down one directory level, which broke links in two
directions at once: ~11 inbound links pointing at the old root paths, and 78 outbound links inside
the moved files that were written relative to the root. Both classes are invisible until someone
clicks, and a portfolio repository is exactly the place where someone clicks.

The repo has no link checker. This is it, and it is deliberately small: no network, no anchor
resolution, no HTML. It answers one question -- does the file on the other end of this link exist
-- because that is the question the move could get wrong.

WHAT IT DELIBERATELY IGNORES
----------------------------
  * **Absolute URLs** (http, https, mailto) -- a network check is a different tool with different
    failure modes, and it would make the suite depend on the internet.
  * **Pure anchors** (`#section`) -- nothing to resolve on disk.
  * **The anchor half** of `path.md#section` -- the path is checked, the anchor is not. Checking
    anchors means parsing every heading and normalising GitHub's slug rules; worth doing later,
    not worth blocking this on.
  * **Untracked files.** `git ls-files` is the input, so `temp/` and the gitignored panels cannot
    produce a false failure.
  * **Markdown-link syntax used as prose notation.** `D340` writes `[ID](a)` and `[ID](b)` meaning
    "identity check (a)"; `D306` does the same. A target carrying neither a `/` nor a `.` cannot be
    a path to a file in this repo, so it is skipped rather than reported. Without this the checker
    cries wolf on notation nobody intends as a link, and a checker that cries wolf gets ignored.

Percent-encoding is decoded before resolving, because `docs/prop firm leads/` has spaces in its
name and three decision records link into it as `../prop%20firm%20leads/…`.

A link into a path that is tracked but absent from the working tree still counts as resolving:
existence is checked against the index as well as the disk, so a clone that has not fetched the
bulk panels (D536) does not fail this check.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote

REPO = Path(__file__).resolve().parent.parent

# [text](target) -- the target runs to the first ')' or whitespace. Markdown allows nesting and
# titles; this repo does not use them, and a regex that pretends otherwise would be a false
# affordance (D48).
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")

SKIP_SCHEMES = ("http://", "https://", "mailto:", "ftp://")


def tracked_markdown() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*.md"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [REPO / line for line in out.splitlines() if line]


def tracked_paths() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return {line for line in out.splitlines() if line}


def broken_links(doc: Path, index: set[str]) -> list[tuple[int, str]]:
    bad = []
    for lineno, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for target in LINK.findall(line):
            if target.startswith(SKIP_SCHEMES) or target.startswith("#"):
                continue
            path_part = unquote(target.split("#", 1)[0])
            if not path_part:
                continue
            if "/" not in path_part and "." not in path_part:
                continue  # prose notation, e.g. D340's `[ID](a)` -- see the docstring
            resolved = (doc.parent / path_part).resolve()
            try:
                rel = resolved.relative_to(REPO).as_posix()
            except ValueError:
                bad.append((lineno, f"{target} -> outside the repository"))
                continue
            # Tracked-but-not-on-disk still counts: a clone without the D536 panels is fine.
            if not resolved.exists() and rel not in index:
                bad.append((lineno, target))
    return bad


def main(argv: list[str]) -> int:
    docs = [REPO / a for a in argv] if argv else tracked_markdown()
    index = tracked_paths()

    total, absent = 0, 0
    for doc in sorted(docs):
        if not doc.exists():
            # Tracked, but deleted in this worktree -- a normal mid-work state, and NOT a link
            # problem: a file that is not there has no links to check. Counting it as a failure
            # made the checker red whenever anyone had an uncommitted deletion, which is exactly
            # when a doc gate must still be usable. Whether a tracked file should be present is
            # git's question, and `git status` already answers it.
            absent += 1
            continue
        for lineno, target in broken_links(doc, index):
            print(f"{doc.relative_to(REPO).as_posix()}:{lineno}: {target}")
            total += 1

    note = f", {absent} tracked but absent from the worktree (skipped)" if absent else ""
    print(f"\n{len(docs) - absent} documents checked, {total} unresolved link(s){note}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
