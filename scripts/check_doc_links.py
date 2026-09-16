"""Every relative link in a tracked Markdown file must resolve to a file that exists.

    python scripts/check_doc_links.py            # all tracked .md
    python scripts/check_doc_links.py README.md docs/RULES.md

WHY THIS EXISTS
---------------
Commit `77d8bab` moved AITODO.md, AUDIT_REPORT.md and PICKUP.md into `docs/internal/`, one
directory level down, which broke links in two directions at once: ~11 inbound links pointing at
the old root paths, and 78 outbound links inside the moved files that were written relative to the
root. Both classes are invisible until someone clicks, and a portfolio repository is exactly the
place where someone clicks. (The move has no decision record. This line used to cite one -- `D538`,
a number that had never been taken by anything -- and nothing in the repository could tell, because
a dead `D<n>` in prose reads exactly like a live one. That is the hole
`tests/unit/test_cited_decisions_exist.py` now gates.)

The repo has no link checker. This is it, and it is deliberately small: no network and no anchor
resolution. It answers one question -- does the file on the other end of this link exist --
because that is the question the move could get wrong.

IT READS HTML `src`/`srcset` AS WELL AS MARKDOWN LINKS, AND THAT WAS A REAL HOLE
--------------------------------------------------------------------------------
It used to be Markdown-only, and said so. Then `docs/figures/` arrived and README.md began
selecting between a light and a dark SVG with `<picture><source srcset=...><img src=...></picture>`
-- which is the only way to theme an image on GitHub. Not one of those paths was checked by
anything. A whole class of link, in the most-read document in the repository, invisible to the
gate that exists to catch exactly this. Markdown syntax is not the boundary that matters; a path
in a tracked document is.

WHAT IT DELIBERATELY IGNORES
----------------------------
  * **Absolute URLs** (http, https, mailto) -- a network check is a different tool with different
    failure modes, and it would make the suite depend on the internet.
  * **`data:` URIs**, which resolve to nothing on disk by construction.
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

THE INDEX IS THE AUTHORITY, NOT THE DISK
----------------------------------------
A link resolves if its target is in `git ls-files`. Both halves of that matter:

  * **Tracked but absent from the worktree still resolves.** A clone that has not fetched the bulk
    panels (D536), or a record staged for deletion, must not redden a doc gate.
  * **Present on the disk but ABSENT FROM THE INDEX does NOT resolve**, and this is the half that
    was missing. Five links pointed at gitignored panels and at `temp/` -- `fut_breadth_hourly.csv.gz`,
    `fut_spread_all_1m.csv.gz`, `d526_curve_strip_CL_GC.csv.gz`, `d361_trades_gap_up_fade.csv`,
    `index1m_map_precheck.py`. Every one of them is on the author's disk, so the checker was green
    for years, and every one of them is a dead link for every other reader on earth. A clone found
    all five in one run.

    This is the same error, in the gate itself, that round five found in the README: measuring the
    author's worktree and publishing the answer as what a reader receives. A link to a file the
    repository deliberately does not distribute is a false affordance (D48) -- the path belongs in
    backticks, saying where the file lives, not in brackets, promising a click that cannot work.
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

# `<img src="...">` and `<source srcset="...">`. A srcset may carry several candidates with
# descriptors (`a.svg 1x, b.svg 2x`), so the value is split on commas and the descriptor dropped.
HTML_SRC = re.compile(r'\b(?:src|srcset)="([^"]+)"')

SKIP_SCHEMES = ("http://", "https://", "mailto:", "ftp://", "data:")


def targets_in(line: str) -> list[str]:
    """Every path this line points at, from either syntax."""
    found = list(LINK.findall(line))
    for value in HTML_SRC.findall(line):
        for candidate in value.split(","):
            head = candidate.strip().split()[0] if candidate.strip() else ""
            if head:
                found.append(head)
    return found


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


def tracked_dirs(index: set[str]) -> set[str]:
    """Every directory that contains a tracked file, at any depth.

    `git ls-files` lists files, but plenty of links point at a directory -- `docs/decisions/`,
    `tests/golden` -- and those resolve for a reader. Precomputed rather than tested per link:
    there are ~5,000 links and ~1,700 tracked paths, and the nested scan is the one part of this
    script that would be felt.
    """
    dirs: set[str] = set()
    for path in index:
        parts = path.split("/")[:-1]
        for i in range(len(parts)):
            dirs.add("/".join(parts[: i + 1]))
    return dirs


def broken_links(doc: Path, index: set[str], dirs: set[str]) -> list[tuple[int, str]]:
    bad = []
    for lineno, line in enumerate(doc.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for target in targets_in(line):
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
            if rel in index or rel in dirs:
                continue  # tracked -- a clone without the D536 panels still resolves it
            if resolved.exists():
                # The half that used to pass. On this machine only.
                bad.append((lineno, f"{target} -> on disk but NOT in git; a reader gets nothing"))
            else:
                bad.append((lineno, target))
    return bad


def main(argv: list[str]) -> int:
    docs = [REPO / a for a in argv] if argv else tracked_markdown()
    index = tracked_paths()
    dirs = tracked_dirs(index)

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
        for lineno, target in broken_links(doc, index, dirs):
            print(f"{doc.relative_to(REPO).as_posix()}:{lineno}: {target}")
            total += 1

    note = f", {absent} tracked but absent from the worktree (skipped)" if absent else ""
    print(f"\n{len(docs) - absent} documents checked, {total} unresolved link(s){note}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
