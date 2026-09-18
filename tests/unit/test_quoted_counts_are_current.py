"""Counts quoted in the prose of living documents match the repository they describe.

`tests/unit/test_readme_counts_are_current.py` gates the generated `COUNTS` block in `README.md`.
This file gates everything the block cannot reach: a number typed into a sentence, a code-fence
comment, or a YAML comment in the CI workflow. **That is where every stale count in the
2026-09-17 audit lived** — the block was right and five documents around it were not.

THE FAILURE THIS EXISTS TO PREVENT, NAMED
-----------------------------------------
`docs/VERIFICATION.md` was written on 2026-09-16 with freshly measured tier counts. The golden
tier had grown from 91 tests to 101, so the new page said 101 and four older documents went on
saying 91 — `README.md`, `CONTRIBUTING.md`, `docs/TUTORIAL.md` and the comment above the `golden`
job in `.github/workflows/tests.yml`, which is the first command a reviewer runs. Nothing failed.
A reader's first act was to run a command whose comment was wrong by 10%.

A SCAN, NOT A LIST OF SITES
---------------------------
The sites are found by pattern rather than enumerated, because a list of file:line pairs is itself
a count typed by hand — it goes stale the first time someone adds a sixth document quoting the
golden tier, and it goes stale *silently*, which is the property that makes it worse than nothing.
What is enumerated instead is the set of documents that are **frozen by convention** and must not
be swept: an append-only decision record that says "all 91 golden masters" is a correct statement
about 2026-09-15 and amending it in place would break the rule in `CONTRIBUTING.md:125`. Each
exclusion below carries its reason, and `test_every_frozen_prefix_exists` fails if one of them
stops naming anything real — an exclusion that matches nothing is an exclusion that is quietly
widening.

WHERE THE NUMBERS COME FROM
---------------------------
`scripts/build_readme_counts.py` for anything it already computes, so the gate and the generator
cannot disagree with each other, and an AST walk over the tracked `src/` files for the `raise`
counts. Nothing here is typed.
"""

from __future__ import annotations

import ast
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
BUILDER = REPO / "scripts" / "build_readme_counts.py"

#: Documents that are frozen or append-only, with the reason each one is not swept. A count inside
#: these is a dated historical statement, not a claim about the repository as it stands.
FROZEN = {
    "docs/decisions/": "append-only records, amended in writing (CONTRIBUTING.md:125)",
    "docs/results/": "study ledgers emitted by a runner; regenerating the study rewrites them",
    "docs/research/": "scoping and literature for work that is not a study yet",
    "docs/specs/": "the frozen models and prompts studies were built from",
    "docs/verification/": "a dated measurement, pinned by tests/unit/test_writeup.py",
    "docs/internal/": "working logs: PICKUP.md is a journal, AITODO.md is frozen at 2026-09-01",
    "CHANGELOG.md": "Keep a Changelog: every entry is a statement about a past release",
    "MASTER_PROJECT_DOC.md": "frozen pre-implementation snapshot, 2026-07-13",
    "DESIGN_DECISIONS.md": "frozen pre-implementation snapshot, 2026-07-13",
    "VERIFICATION_SCHEME.md": "frozen pre-implementation snapshot, 2026-07-13",
    "DEVELOPMENT_TIMETABLE.md": "frozen pre-implementation snapshot, 2026-07-13",
}

TIERS = ("golden", "property", "integration", "unit")


def _int(raw: str) -> int:
    return int(raw.replace(",", ""))


# --------------------------------------------------------------------------------------------
# the patterns, each tied to a measured quantity
# --------------------------------------------------------------------------------------------

#: `# 101 ledger-anchored tests, 0.58s` — the phrasing the four drifted sites share.
LEDGER_ANCHORED = re.compile(r"([\d,]+)\s+ledger-anchored\s+tests")

#: `uv run pytest -q tests/golden     # 101 ...` — a command comment that dropped the phrase.
GOLDEN_COMMAND = re.compile(r"pytest[^\n#]*tests/golden[^\n#]*#\s*\*{0,2}([\d,]+)\b")

#: ``### `tests/property/` — 67 tests across 8 files.`` — the tier headings in VERIFICATION.md.
TIER_HEADING = re.compile(
    r"`?tests/(golden|property|integration|unit)/?`?\s*[—–-]{1,2}\s*\*{0,2}([\d,]+)\s+tests"
)

#: `| **2,057 tests** |` and `**2,057 tests are collected here**` — a bolded total.
TOTAL_TESTS = re.compile(r"\*\*([\d,]+)\s+tests\b")

#: `D1 → D539`, `D1 through D539` — the decision range, typed in three documents before D539.
#:
#: An en-dash is deliberately NOT accepted. `D1–D284` and `D1–D49` are real sub-ranges — the
#: curated half of the decision index, and the original log — and sweeping them to the maximum
#: would make three true sentences false. The arrow and the word "through" are the forms this
#: repository uses for "everything there is", and they are the only ones gated.
DECISION_RANGE = re.compile(r"\bD1\s*(?:→|->|through)\s*D(\d+)\b")

#: ``**273 `raise` statements**`` — the guard count in VERIFICATION.md.
RAISE_TOTAL = re.compile(r"\*{0,2}([\d,]+)\*{0,2}\s+`raise`\s*\n?\s*statements")

#: `spread across 46 of its 85 tracked .py files`
RAISE_FILES = re.compile(r"spread\s+across\s+(\d+)\s+of\s+its\s+(\d+)\s+tracked")


# --------------------------------------------------------------------------------------------
# measured sources
# --------------------------------------------------------------------------------------------


def _tracked(*globs: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", *globs], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


@pytest.fixture(scope="module")
def builder():
    """`scripts/build_readme_counts.py`, loaded by path — `scripts/` is not a package."""
    spec = importlib.util.spec_from_file_location("build_readme_counts", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def measured(builder) -> dict[str, int]:
    return builder.counts()


@pytest.fixture(scope="module")
def raises() -> dict[str, int]:
    """`raise` statements in the tracked `src/` tree, counted two ways.

    `total` is every AST `Raise` node. `with_exception` excludes the bare `raise` inside an
    `except`, which re-raises what it caught and is flow control rather than a guard. The two
    differ, which is why `docs/VERIFICATION.md` states which one it means.
    """
    files = sorted(set(_tracked("src/*.py")))
    total = non_bare = with_any = 0
    for name in files:
        tree = ast.parse((REPO / name).read_text(encoding="utf-8"))
        nodes = [n for n in ast.walk(tree) if isinstance(n, ast.Raise)]
        total += len(nodes)
        non_bare += sum(1 for n in nodes if n.exc is not None)
        with_any += 1 if nodes else 0
    return {
        "total": total,
        "with_exception": non_bare,
        "files_with_raise": with_any,
        "files": len(files),
    }


# --------------------------------------------------------------------------------------------
# the scan
# --------------------------------------------------------------------------------------------


def _living_documents() -> list[str]:
    paths = _tracked("*.md", "*.yml", "*.yaml", ".github/*.yml", ".github/*.yaml")
    return sorted(p for p in set(paths) if not any(p.startswith(f) for f in FROZEN))


def _sites(pattern: re.Pattern[str], group: int = 1):
    """Every (path, line, match) the pattern finds in a living document."""
    for name in _living_documents():
        text = (REPO / name).read_text(encoding="utf-8", errors="replace")
        for m in pattern.finditer(text):
            line = text.count("\n", 0, m.start()) + 1
            yield name, line, m


def _assert_all(
    pattern: re.Pattern[str], expected: int, what: str, group: int = 1, minimum: int = 1
) -> int:
    """Check every site the pattern finds, and check that it found enough of them.

    THE FLOOR IS PART OF THE HELPER, not a decision each caller remembers to make. Four of the
    seven gates in this file had no floor, and two of those watched a SINGLE site apiece: the
    `raise` count and the guard-file split, both on one line of `docs/VERIFICATION.md`. Reword
    that line -- drop the backticks, reflow the paragraph so a word lands between the number and
    the word `raise` -- and the regex matches nothing, `wrong` stays empty, and the test passes
    while the number it exists to pin is unguarded. `test_the_quoted_guard_file_split_is_current`
    had no other assertion at all, so with zero sites its whole body reduced to `assert not []`.

    A floor set to the measured count rather than to 1 is what makes losing ANY site fail.
    """
    wrong = []
    found = 0
    for name, line, m in _sites(pattern):
        found += 1
        if _int(m.group(group)) != expected:
            wrong.append(f"  {name}:{line} says {m.group(group)}, {what} is {expected}")
    assert not wrong, (
        f"{len(wrong)} document(s) quote a stale count for {what}:\n"
        + "\n".join(wrong)
        + f"\n\nEdit each line above to {expected}. This is prose outside the generated COUNTS "
        "block, so `build_readme_counts.py --build` will not fix it."
    )
    assert found >= minimum, (
        f"{pattern.pattern!r} matched {found} site(s) and at least {minimum} were expected, so "
        f"this gate is watching an emptier set than it was written for. Either a document that "
        f"quoted {what} was reworded past the pattern -- in which case reword it back or widen "
        "the pattern -- or the number is no longer stated anywhere and the gate should be "
        "retired on purpose rather than by attrition."
    )
    return found


def test_every_frozen_prefix_exists():
    """An exclusion that matches nothing is an exclusion that has quietly widened.

    If a directory is renamed, its prefix here stops excluding anything and the reason recorded
    beside it becomes a comment about a path that is gone — while some other frozen document
    starts being swept. The list is small enough to check, so it is checked.
    """
    tracked = _tracked()
    for prefix, reason in FROZEN.items():
        assert any(p.startswith(prefix) for p in tracked), (
            f"FROZEN lists {prefix!r} ({reason}) but nothing tracked starts with it"
        )


def test_the_scan_reaches_the_documents_it_is_for():
    """The four sites the 91/101 drift lived in must be inside the scan's reach.

    Without this, narrowing `_living_documents()` — or adding a frozen prefix that swallows one of
    them — would make every assertion below pass by looking at nothing. A check that cannot fire
    is worse than no check.
    """
    reachable = set(_living_documents())
    for required in (
        "README.md",
        "CONTRIBUTING.md",
        "docs/TUTORIAL.md",
        "docs/VERIFICATION.md",
        "PHILOSOPHY.md",
        ".github/workflows/tests.yml",
    ):
        assert required in reachable, f"{required} is not being scanned"


def test_the_golden_tier_count_is_current_everywhere_it_is_quoted(measured):
    """The 91 → 101 drift, in the exact phrasing all four sites used."""
    found = _assert_all(LEDGER_ANCHORED, measured["tests_golden"], "the golden tier")
    assert found >= 4, (
        f"only {found} site(s) say 'N ledger-anchored tests'; the gate was written for at least "
        "four (README.md, CONTRIBUTING.md, docs/TUTORIAL.md, .github/workflows/tests.yml). If a "
        "document was reworded, reword it back or this gate is watching an empty set."
    )


def test_a_golden_command_comment_quotes_the_golden_count(measured):
    """`uv run pytest -q tests/golden   # N ...` — the number a reader checks against by running."""
    _assert_all(GOLDEN_COMMAND, measured["tests_golden"], "the golden tier", minimum=4)


@pytest.mark.parametrize("tier", TIERS)
def test_every_quoted_tier_count_is_current(measured, tier):
    """`tests/<tier>/ — N tests`, wherever a living document writes it.

    This one cannot use `_assert_all` because it filters by tier inside the loop, so it counts
    its own sites. Each tier is quoted exactly once, in `docs/VERIFICATION.md`'s heading for it,
    which is the thinnest coverage of any gate here: lose that heading and the tier stops being
    pinned anywhere.
    """
    expected = measured[f"tests_{tier}"]
    wrong = []
    found = 0
    for name, line, m in _sites(TIER_HEADING):
        if m.group(1) != tier:
            continue
        found += 1
        if _int(m.group(2)) != expected:
            wrong.append(f"  {name}:{line} says {m.group(2)}, tests/{tier}/ holds {expected}")
    assert not wrong, (
        f"{len(wrong)} document(s) quote a stale count for tests/{tier}/:\n" + "\n".join(wrong)
    )
    assert found >= 1, (
        f"no living document states a test count for tests/{tier}/ any more. The tier headings in "
        "docs/VERIFICATION.md are the only place this is written down, so a reworded heading "
        "silently retires this gate."
    )


def test_every_quoted_total_is_current(measured):
    """A bolded `**N tests**` is the whole suite, and the header table had drifted by 10."""
    _assert_all(TOTAL_TESTS, measured["tests"], "the total collected", minimum=3)


def test_every_decision_range_ends_at_the_highest_record(measured):
    """`D1 → D537` in three documents while `docs/decisions/` held D539."""
    found = _assert_all(DECISION_RANGE, measured["max_decision"], "the highest decision number")
    assert found >= 3, (
        f"only {found} site(s) write the full decision range; the generated COUNTS block plus "
        "README.md and PHILOSOPHY.md were expected. Fewer means this gate is watching an empty set."
    )


def test_the_quoted_raise_count_is_the_non_bare_one(raises):
    """273, not 275 — and the difference is stated rather than left to be rediscovered.

    A reviewer running a plain AST count over `src/` gets 275: two of them are bare `raise` inside
    an `except`. `docs/VERIFICATION.md` says which reading it means, and this pins the reading as
    well as the number.
    """
    bare = raises["total"] - raises["with_exception"]
    assert bare == 2, (
        f"{bare} bare `raise` statements in src/, not 2 — docs/VERIFICATION.md says a plain AST "
        "walk finds 'two more' than the number it quotes, and that sentence is now wrong"
    )
    _assert_all(RAISE_TOTAL, raises["with_exception"], "the non-bare `raise` count", minimum=1)


def test_the_quoted_guard_file_split_is_current(raises):
    """`spread across 46 of its 85 tracked .py files`.

    One site, one line, one file — and until the floor below existed this test had no other
    assertion, so a reworded sentence in `docs/VERIFICATION.md` reduced its whole body to
    `assert not []`. It was the weakest check in the suite and it guarded a number the same page
    uses to describe the size of the guard surface.
    """
    wrong = []
    found = 0
    for name, line, m in _sites(RAISE_FILES):
        found += 1
        if (_int(m.group(1)), _int(m.group(2))) != (raises["files_with_raise"], raises["files"]):
            wrong.append(
                f"  {name}:{line} says {m.group(1)} of {m.group(2)}, "
                f"measured {raises['files_with_raise']} of {raises['files']}"
            )
    assert not wrong, "stale guard-file split:\n" + "\n".join(wrong)
    assert found >= 1, (
        "nothing states the guard-file split any more, so this test asserts nothing. It is "
        "written in docs/VERIFICATION.md as 'spread across N of its M tracked .py files'."
    )


def test_no_single_document_is_the_only_source_for_a_gate():
    """Concentration is a way for many gates to fail at once, and it was not being watched.

    Measured when the floors were added: 22 sites across the seven patterns, of which
    `docs/VERIFICATION.md` carried 11 — and was the SOLE source for six of the seven. Renaming or
    restructuring that one page would have disarmed six gates simultaneously, and only the two
    that had floors would have said anything.

    A floor counts sites, not coverage, so a floor alone does not catch this: three of
    `DECISION_RANGE`'s four sites are in `README.md`, so its `>= 3` could be met by `README.md`
    alone and deleting `PHILOSOPHY.md`'s range would pass.

    This does not forbid concentration — some numbers are genuinely written down once, and the
    tier headings are one of them. It records which gates are single-sourced, so that becoming
    single-sourced is a visible change rather than a silent one.
    """
    single_sourced = {
        "RAISE_TOTAL": RAISE_TOTAL,
        "RAISE_FILES": RAISE_FILES,
    }
    multi_sourced = {
        "LEDGER_ANCHORED": LEDGER_ANCHORED,
        "GOLDEN_COMMAND": GOLDEN_COMMAND,
        "TOTAL_TESTS": TOTAL_TESTS,
        "DECISION_RANGE": DECISION_RANGE,
    }

    for label, pattern in multi_sourced.items():
        files = {name for name, _, _ in _sites(pattern)}
        assert len(files) >= 2, (
            f"{label} is now quoted in only {sorted(files)}. It used to be stated in at least two "
            "documents, so it has become single-sourced — one edit to that file now disarms this "
            "gate. Either restore the second statement or move the pattern to the "
            "single_sourced set above, deliberately."
        )

    for label, pattern in single_sourced.items():
        files = {name for name, _, _ in _sites(pattern)}
        assert files, f"{label} is quoted nowhere at all; its gate is watching an empty set"
