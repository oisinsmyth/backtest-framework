"""A runner that rewrites one section of a results document must not eat the others.

`scripts/run_structure_pnl.py --report-only` splices its ADDENDUM into
`docs/results/STRUCTURE_RESULTS.md`. It used to replace everything from its own marker to
the parking-lot anchor at the very bottom, which was correct exactly while that addendum
was the last section in the file.

It has not been since D213. Four later sections — `## D213`, `## D214`, `## D215`,
`## D216`, written by four other runners — sat inside the replaced span, and running the
script deleted **426 lines of published results** with no error and no warning. The only
symptom was the document getting shorter.

Found by diffing the document after a re-run, which is not a gate. These are.
"""

import ast
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
RESULTS = REPO / "docs" / "results" / "STRUCTURE_RESULTS.md"
RUNNER = REPO / "scripts" / "run_structure_pnl.py"

# The sections that were destroyed. Named individually rather than counted, because a
# count survives losing one section and gaining another.
SECTIONS_BELOW_THE_ADDENDUM = (
    "## D213 - can selection rescue it?",
    "## D214 - the terrain map as a confluence gate",
    "## D215 - is it just mean reversion?",
    "## D216 - the tail, the frequency, and the fill",
)


# Every runner that splices a section into a results document, with the section it owns.
# Seven of these eight would have destroyed between 9 KB and 61 KB of published results
# written by the others; only `run_reversion_tail` was still the last section and therefore
# still harmless. Named individually because the point is that the family is complete.
SPLICING_RUNNERS = {
    "run_generic_reversal": "## D215 - is it just mean reversion?",
    "run_reversion_tail": "## D216 - the tail, the frequency, and the fill",
    "run_structure_audit": "## WP6 - the discretion audit",
    "run_structure_components": "## WP3",
    "run_structure_marginal": "## WP4 - what each component adds on top of the others",
    "run_structure_pnl": "## ADDENDUM (post-close)",
    "run_structure_selection": "## D213 - can selection rescue it?",
    "run_structure_terrain_gate": "## D214 - the terrain map as a confluence gate",
}


def _code_only(source: str) -> str:
    """The source with every docstring blanked, so a text scan cannot match prose.

    Line count is preserved (each docstring becomes blank lines) so that anything reporting
    a line number still reports the right one. A file that does not parse is returned as-is
    rather than skipped: a scan that silently drops its hardest inputs is worse than one
    that occasionally matches a comment.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:  # pragma: no cover - every tracked runner parses today
        return source
    lines = source.splitlines(keepends=True)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        doc = node.body[0] if node.body else None
        if (
            isinstance(doc, ast.Expr)
            and isinstance(doc.value, ast.Constant)
            and isinstance(doc.value.value, str)
            and doc.end_lineno
        ):
            for i in range(doc.lineno - 1, doc.end_lineno):
                lines[i] = "\n"
    return "".join(lines)


def _load(name: str = "run_structure_pnl"):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_the_sections_below_the_addendum_are_still_there():
    """The state check. If this fails the document has already lost them."""
    text = RESULTS.read_text(encoding="utf-8")
    missing = [s for s in SECTIONS_BELOW_THE_ADDENDUM if s not in text]
    assert not missing, f"sections deleted from {RESULTS.name}: {missing}"


def test_the_addendum_sits_above_them_so_the_splice_really_does_span_them():
    """The anti-tautology. If the addendum were the LAST section, the test above would
    pass under the OLD code too and would be proving nothing."""
    text = RESULTS.read_text(encoding="utf-8")
    addendum = text.index("## ADDENDUM (post-close)")
    for section in SECTIONS_BELOW_THE_ADDENDUM:
        assert text.index(section) > addendum, f"{section} is above the addendum"
    parking = text.index("### Parking lot")
    assert parking > max(text.index(s) for s in SECTIONS_BELOW_THE_ADDENDUM), (
        "the parking-lot anchor no longer sits below those sections, so the old "
        "marker-to-anchor span would no longer cover them and this gate is measuring "
        "a document it no longer describes"
    )


def test_every_runner_that_splices_owns_a_section_that_is_actually_there():
    """The family is complete and each member's marker still matches the document.

    A marker that no longer matches makes the splice INSERT rather than replace, so the
    document quietly grows a second copy of the section on every run — the mirror image of
    the deletion this file exists for.
    """
    text = RESULTS.read_text(encoding="utf-8")
    missing = {n: m for n, m in SPLICING_RUNNERS.items() if m not in text}
    assert not missing, f"markers that no longer match the document: {missing}"


def test_no_runner_keeps_its_own_copy_of_the_splice():
    """One splice, in `scripts/results_document.py`, and eight callers.

    Eight byte-identical copies is how one correct function and seven stale ones happen:
    each was right on the day it was written and none of them knew when that stopped
    being true.
    """
    offenders = []
    for name in SPLICING_RUNNERS:
        source = (REPO / "scripts" / f"{name}.py").read_text(encoding="utf-8")
        if "from results_document import splice_section" not in source:
            offenders.append(f"{name}: does not import the shared splice")
        if "### Parking lot" in source and "splice_section" not in source:
            offenders.append(f"{name}: still partitions on the parking lot itself")
    assert not offenders, offenders


def test_re_rendering_the_addendum_changes_only_the_addendum(tmp_path, monkeypatch):
    """The behavioural gate, on a throwaway document rather than the real one.

    Built to the same shape: an addendum with later `## ` sections beneath it and a
    parking lot at the bottom. The old code returned `head + body + anchor + tail`, which
    drops everything between; this asserts the later sections survive a splice.
    """
    module = _load()
    marker = "## ADDENDUM (post-close) - every arm in Sharpe and PnL, against baselines"
    document = (
        "# Results\n\nIntro.\n\n"
        f"{marker}\n\n**Produced:** 2020-01-01\n\nOld addendum body.\n\n"
        "## LATER SECTION A\n\nWritten by another runner.\n\n"
        "## LATER SECTION B\n\nAlso not mine.\n\n"
        "---\n\n### Parking lot\n\nleftovers\n"
    )
    target = tmp_path / "RESULTS.md"
    target.write_text(document, encoding="utf-8")

    monkeypatch.setattr(module, "RESULTS", target)
    monkeypatch.setattr(module, "render", lambda payload: f"{marker}\n\nNEW BODY.\n")
    module.append_section({})

    after = target.read_text(encoding="utf-8")
    assert "NEW BODY." in after
    assert "Old addendum body." not in after
    for kept in ("## LATER SECTION A", "Written by another runner.",
                 "## LATER SECTION B", "Also not mine.",
                 "### Parking lot", "leftovers"):
        assert kept in after, f"the splice destroyed {kept!r}"
    # Order is preserved, not merely presence.
    assert after.index("NEW BODY.") < after.index("## LATER SECTION A")
    assert after.index("## LATER SECTION A") < after.index("### Parking lot")


def test_the_old_splice_would_have_failed_that(tmp_path):
    """Break what the assertion READS. The gate above is worth having only if the code it
    replaced actually fails it — otherwise it is a test of nothing."""
    marker = "## ADDENDUM"
    anchor = "---\n\n### Parking lot"
    document = (
        f"head\n\n{marker}\n\nold body\n\n"
        "## LATER SECTION A\n\nkeep me\n\n" + anchor + "\n\nleftovers\n"
    )
    # The old implementation, restated.
    head, _, rest = document.partition(marker)
    _, sep, tail = rest.partition(anchor)
    old_result = head + "NEW BODY\n" + anchor + tail if sep else head + "NEW BODY\n"
    assert "## LATER SECTION A" not in old_result, (
        "the old splice no longer destroys a later section, so the defect D542 recorded "
        "is not what this test describes"
    )
    assert "keep me" not in old_result


def test_the_splice_refuses_rather_than_truncating_when_it_has_no_boundary(tmp_path, monkeypatch):
    """The remaining silent path, closed. With neither a following heading nor a parking
    lot there is no honest place to stop, and the old code's answer was to keep `head` and
    drop the rest — a truncation reported as success."""
    module = _load()
    marker = "## ADDENDUM (post-close) - every arm in Sharpe and PnL, against baselines"
    target = tmp_path / "RESULTS.md"
    target.write_text(f"# Results\n\n{marker}\n\nbody with no boundary after it\n", encoding="utf-8")
    monkeypatch.setattr(module, "RESULTS", target)
    monkeypatch.setattr(module, "render", lambda payload: f"{marker}\n\nNEW\n")
    with pytest.raises(SystemExit, match="truncate"):
        module.append_section({})


def test_no_other_runner_splices_by_a_distant_anchor():
    """The class, not the instance. A `partition` on an anchor far below the section being
    written, with a fallback that keeps only `head`, is this defect wherever it appears.

    This scan is how the family was found: fixing `run_structure_pnl` alone would have left
    seven runners able to delete it back out again.
    """
    listed = subprocess.run(
        ["git", "ls-files", "scripts/*.py"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout.split()
    # The index, filtered to what is actually on disk — the same pair `git ls-files` plus
    # `.exists()` that `scripts/build_decision_register.py` uses. A path staged for
    # deletion but not yet committed is in the index and not in the worktree, and reading
    # it raises; the principal routinely has several.
    tracked = [rel for rel in listed if (REPO / rel).exists()]
    assert len(tracked) > 400, "the scan lost its input rather than the repo losing runners"

    offenders = []
    users = 0
    for rel in tracked:
        source = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        if "splice_section" in source:
            users += 1
        # A write that partitions on an anchor and keeps only `head` when it misses —
        # searched in CODE, with docstrings stripped. The first version of this scan
        # flagged `scripts/results_document.py`, whose docstring quotes the defective line
        # verbatim in order to explain it. `test_import_boundaries.py` records the same
        # trap ("the six textual mentions of `scripts/` in `src/` are all prose inside
        # docstrings"), and the answer there was the same: ask the parser, not the text.
        if re.search(r"partition\((\w+)\)\s*\n.*?else\s+head\s*\+", _code_only(source), re.S):
            offenders.append(rel)
    # A floor on the REPLACEMENT, not on the defect: "no offenders" is also what an empty
    # scan says, and the anchor string this used to key on has since moved into the shared
    # helper, so keying the floor on it would have measured the fix as a loss of input.
    assert users >= len(SPLICING_RUNNERS), (
        f"only {users} file(s) reference the shared splice; expected at least "
        f"{len(SPLICING_RUNNERS)} runners plus the helper itself"
    )
    assert not offenders, (
        f"these runners still splice a results document by a distant anchor with a "
        f"keep-the-head fallback: {offenders}"
    )
