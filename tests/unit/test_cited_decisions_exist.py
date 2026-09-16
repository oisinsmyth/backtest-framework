"""Every decision number cited in tracked prose or source has a record in `docs/decisions/`.

**This test exists because `scripts/check_doc_links.py:8` cited `D538` and there is no D538.**
The move that docstring describes was commit `77d8bab` and it never got a decision record at all;
the number was invented and then read as fact for as long as anyone looked at the file. A citation
to a record that does not exist is a dead reference that reads exactly like a live one, and this
repository is built on decision records and cites them constantly.

**Nothing could catch it, and the near-misses are instructive:**

* `tests/unit/test_decision_index_is_complete.py` runs the *reverse* direction -- records on disk
  must appear in `docs/decisions/README.md`, and the index must not list numbers with no record.
  Its universe is the index table. A number written in a sentence is not in the index table.
* `scripts/check_doc_links.py` checks that link *paths* resolve, and deliberately skips targets
  carrying neither `/` nor `.` because `D340` writes `[ID](a)` as prose notation. A bare `D537` in
  a sentence is not a path and was never its business.

So the defect lives in the gap between them: the citation *notation*, which neither owns.

THE INDEX, NOT THE FILESYSTEM
-----------------------------
`git ls-files` is the input, the same boundary `scripts/check_doc_links.py` and
`scripts/build_readme_counts.py:15-24` use, and for the same reason: the filesystem counts scratch
files nobody else has and misses records everyone else has but this worktree deleted. A record
staged for deletion mid-renumbering must not redden the gate for a citation a clone resolves fine.

ANCHOR THE PATTERN AT THE BASENAME
----------------------------------
Valid numbers are `^D0*(\\d+)` against the BASENAME. An unanchored `D[0-9]+` finds `D304` inside
`D300-AMENDMENT-cost-basis-and-what-D304-and-D305-changed.md` -- which would quietly declare D304
valid when in fact no D304 record exists, turning this gate into a no-op for one of the numbers it
is meant to report. `scripts/build_readme_counts.py:30-35` records the same mistake made twice.
Infixes (`-PRE-REG-`, `-RESULT-`, `-AMENDMENT-`, `-CORRECTION-`) are irrelevant to the number, and
`DRAFT-capturing-the-deeper-zone.md` carries no number and is correctly not one.

WHAT COUNTS AS A CITATION, AND THE FALSE POSITIVES THAT SHAPED IT
-----------------------------------------------------------------
`D<digits>` with a non-word character on both sides. That covers `D537`, `` `D537` `` and
`[D537](...)` alike, since backticks and brackets are boundaries. Three classes of look-alike were
found by running the scan across all 2,018 tracked Markdown and Python files, and each is handled
by shape rather than by an entry in the allowlist below:

* **`n == 0` is never a citation.** Records start at `D01`. `[D0]` is a pre-registered assertion
  label -- 16 occurrences across D398/D399 and their runners, alongside `[S2] [R] [L] [X]` -- and
  `scripts/build_decision_register.py:60` carries the literal regex `D0*(?P<num>\\d+)`, whose `D0`
  is not a citation either. Requiring `n >= 1` removes both without an exclusion entry.
* **A trailing letter is not gated at all.** `D506B`, `D315a`, `D308c` are record variants;
  `D1b`, `D1c`, `D2c` are cell labels in a study grid. The two classes are indistinguishable by
  shape, so the boundary rule skips every suffixed form. Declared blind spot, not an accident: all
  19 suffixed forms in the tree resolve to a record that exists today, so gating them would buy
  nothing and risk failing on a cell label.
* **Decile columns resolve by luck, and are left alone.** `data/a3_leg_decomposition_tables.md`
  quotes literature tables whose columns are `D1 … D10` (deciles, not decisions). They pass
  because D01 and D10 happen to be real records. Reported rather than excluded: widening the
  allowlist to a whole file would hide any real citation in it, and no failure is being suppressed.
  Same for `D1 = draw_sample(...)` at `scripts/d364_auction_bound.py:1273` -- a local variable that
  resolves to D01 by coincidence.

WHY THE ALLOWLIST IS LONG, AND WHY THAT IS THE HONEST STATE
------------------------------------------------------------
Ten numbers below are cited a combined ~300 times and have no record. None is a typo: every one is
real work whose record was never written, or a reserved block that was never consumed. They cannot
be fixed from here -- writing the missing records is research work, and the documents citing them
are decision records and append-only ledgers, which are amended in writing and never silently
edited. They are listed with a reason apiece so the debt is *visible* rather than hidden, the way
`tests/unit/test_results_docs_at_root.py:31-33` keeps its empty set "because an exception, if one
is ever justified, belongs here where the reason can be written next to it". The gate still does
its job: any *new* dangling number fails immediately, which is exactly what D538 needed.
"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
DECISIONS = "docs/decisions/"

# `D` + digits, bounded on both sides by a non-word character. Backticks, brackets, parentheses and
# whitespace are all boundaries, so `D537`, [D537](...) and plain D537 are one pattern.
CITATION = re.compile(r"(?<![A-Za-z0-9_])D(\d{1,4})(?![0-9A-Za-z_])")

# `D<n>-...` at the START of the basename. See ANCHOR THE PATTERN above.
RECORD = re.compile(r"^D0*(\d+)[-.]")

# Numbers cited in the tree that have no record and CANNOT be resolved from here. Each line says
# why, because an unexplained number in this set is the same defect this file exists to catch.
#
# Two shapes, and neither is a typo:
#
#   (a) THE STUDY RAN, THE RECORD WAS NEVER WRITTEN. The runner, its data file and a commit whose
#       subject carries the number are all on disk; only `docs/decisions/D<n>-*.md` is missing.
#       Writing those records is research work, not a test fix.
#   (b) THE NUMBER WAS RESERVED OR RENUMBERED, and the citations are the narrative of that. Every
#       occurrence sits inside a decision record, which is amended in writing and never edited.
UNWRITTEN_RECORDS: dict[int, str] = {
    150: "forward reference: docs/volume_extension.md:1 proposes D150 for a design never adopted",
    294: "(a) scripts/d294_horizon_cost_profile.py + data/d294_horizon_cost_profile.json, no record",
    302: "(a) scripts/d302_cost_estimator.py + data/d302_cost_estimator.json, no record",
    304: "(a) scripts/d304_two_lenses.py + data/d304_two_lenses.json, no record",
    309: "(a) scripts/d309_n1_static.py + data/d309_n1_static.json, no record",
    316: "(a) scripts/d316_weight_shape_paired.py + data/d316_weight_shape_paired.json, no record",
    390: "(b) reserved block D390-D399, taken twice on master then renumbered (D397, D400, D402)",
    407: "(b) reserved in 044f839 for an absorption study; D412 records it as NOT consumed",
    410: "(b) the far end of the D407-D410 block reserved in 044f839; never consumed",
    496: "(a) scripts/d496_book_sharpe_bar.py + data/d496_book_sharpe_bar.json (1bd7803), no record",
}


def _tracked(*patterns: str) -> list[str]:
    """Tracked paths matching `patterns`, from the index rather than the worktree."""
    out = subprocess.run(
        ["git", "ls-files", *patterns], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def _records_on_disk() -> set[int]:
    return {
        int(m.group(1))
        for name in _tracked(f"{DECISIONS}*.md")
        if (m := RECORD.match(os.path.basename(name)))
    }


def _cited_numbers() -> dict[int, list[str]]:
    """Every cited number -> the `path:line` sites citing it.

    Scope is tracked Markdown and tracked Python. Markdown because that is where the prose lives;
    Python because the defect that prompted this file was in a module docstring
    (`scripts/check_doc_links.py:8`), and `scripts/` alone carries ~600 files whose docstrings cite
    records constantly.
    """
    sites: dict[int, list[str]] = {}
    for rel in _tracked("*.md", "*.py"):
        path = REPO / rel
        if not path.exists():
            continue  # tracked but deleted in this worktree -- git status' question, not this one
        text = path.read_text(encoding="utf-8", errors="replace")
        if "D" not in text:
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for match in CITATION.finditer(line):
                number = int(match.group(1))
                if number >= 1:  # D0 is an assertion label, never a record -- see the docstring
                    sites.setdefault(number, []).append(f"{rel}:{lineno}")
    return sites


def _untracked_note(number: int) -> str:
    """Name the one failure whose remedy is `git add` rather than an edit.

    The index is the authority (see the docstring), so a record written but not yet staged reads
    as missing -- correctly, because a clone gets nothing. That is a real state during a change
    that adds a record and its first citation together, and saying so in the message saves the
    reader from hunting for a record that is sitting right there in the worktree.
    """
    on_disk = sorted((REPO / DECISIONS).glob(f"D{number}-*.md"))
    return f" -- ON DISK as {on_disk[0].name} but UNTRACKED; `git add` it" if on_disk else ""


def test_every_cited_decision_number_has_a_record():
    records = _records_on_disk()
    cited = _cited_numbers()

    dangling = sorted(set(cited) - records - set(UNWRITTEN_RECORDS))
    shown = ", ".join(
        f"D{n} (first at {cited[n][0]}){_untracked_note(n)}" for n in dangling[:20]
    )
    if len(dangling) > 20:
        shown += f" … and {len(dangling) - 20} more"
    assert not dangling, (
        f"{len(dangling)} decision number(s) are cited but have no record in docs/decisions/: "
        f"{shown}. Three remedies, in order of likelihood: the record is written but UNSTAGED, and "
        "`git add` it is the whole fix; or the number is wrong -- `git log --all --oneline | grep "
        "D<n>` finds the commit that actually did the work, cite that instead; or the record is "
        "genuinely unwritten, in which case add it to UNWRITTEN_RECORDS with the reason."
    )


def test_the_allowlist_does_not_outlive_its_reason():
    """The other direction: an entry that a record now exists for, or that nothing cites any more.

    Without this the allowlist rots into a permanent blind spot -- the exact failure mode of the
    stale index tables `test_decision_index_is_complete.py` was written for. If another lane writes
    D496's record, this fires and the entry comes out in the same commit.
    """
    records = _records_on_disk()
    cited = set(_cited_numbers())

    now_written = sorted(set(UNWRITTEN_RECORDS) & records)
    assert not now_written, (
        f"UNWRITTEN_RECORDS still lists {now_written}, but docs/decisions/ now holds a record for "
        "each. Delete the entries -- the gate covers them properly now."
    )

    uncited = sorted(set(UNWRITTEN_RECORDS) - cited)
    assert not uncited, (
        f"UNWRITTEN_RECORDS lists {uncited}, which nothing cites any more. Delete the entries "
        "rather than carrying an exception nobody needs."
    )
