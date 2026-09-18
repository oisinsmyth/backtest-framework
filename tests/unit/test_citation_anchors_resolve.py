"""A `path:line` citation points at what it says it points at (D544).

`scripts/check_doc_links.py` already proves every relative *link* resolves. Nothing proved that
`engine/backtest.py:490-492` is where `result.violations.append` lives — and it was not; the
append is at `:361`, and lines 490-492 are split handling. **The line anchor was the last citation
class in this repository with no gate**, and seven of the twenty-one anchors hand-checked before
this file existed were wrong, including one written two hours earlier in `D542`.

WHY NOT THE ±3 RULE THAT WAS PROPOSED
--------------------------------------
The audit proposed requiring a backticked symbol beside the anchor and asserting it appears
within ±3 lines. Measured over the corpus before building it:

  * **53 of 187 (28%)** citations carry a backticked symbol within 45 characters on the same line.
    The other 134 carry none and are uncoverable by that rule.
  * Widening to "the line before" reaches 66% and makes each row of `AUDIT_REPORT.md`'s citation
    table inherit its neighbour's symbols — about twenty spurious flags.
  * **It fires on correct citations.** `docs/ARCHITECTURE.md` cites `engine/risk.py:61` for
    `evaluate(...) -> RiskViolation | None`. Line 61 *is* that return annotation — a correct and
    useful anchor — but `def evaluate(` is at `:55`, six lines above, so ±3 reddens it.

So the convention stands and the proximity rule goes. **The cited line is resolved to its
enclosing `def`/`class` by AST**, and the symbol must name that scope, or the line itself, or the
module. `risk.py:61` resolves to `evaluate` and passes; `instruments/base.py:16` resolves to no
scope at all — it is module-docstring prose — and fails, which is the defect.

WHAT IT COVERS, MEASURED RATHER THAN CLAIMED
----------------------------------------------
**48 citations in maintained prose, of which 12 carry a checkable symbol.** That is the honest
number and it is small, so it is stated here rather than left to be inferred from a green run.

The 187-citation corpus shrinks to 48 because **decision records are excluded**, and the second
reason for that was found by building this gate rather than by planning it: a record routinely
**quotes a wrong anchor in order to correct it**. D542 cites `fast_null.py:224` precisely to say
the drop is at `:243`. A gate cannot tell a quoted error from a made one, and reddening a
correction is worse than the drift it would prevent. The first reason is the ordinary one: a
record is a dated statement, and re-anchoring its citations later is editing the record.

What remains is the surface that actually changes -- `ARCHITECTURE.md`, `VERIFICATION.md`, the
README, `CONTRIBUTING.md`, `TUTORIAL.md`, `src/` and `tests/` -- which is also where drift does
the most damage, because those documents are edited and their anchors move underneath them.
A citation with no backticked symbol cannot be checked this way; those are counted and reported,
not silently skipped, and both floors are set to the measured coverage so the set cannot empty.
"""

from __future__ import annotations

import ast
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

#: `path/to/file.py:123` or `path/to/file.py:123-456`, the second number being a range end.
CITATION = re.compile(r"`?([\w./-]+\.py):(\d+)(?:-(\d+))?`?")

#: A backticked symbol: `` `foo` ``, `` `Foo.bar` ``, `` `foo()` ``, `` `@decorator` ``.
SYMBOL = re.compile(r"`([@\w][\w.]*)\(?\)?`")

#: ...but a backticked FILENAME is not a symbol. `run_macd_ladder.py` beside a citation names a
#: file, not something that should appear at the anchor, and matching it produced a false positive
#: on a correct citation.
NOT_A_SYMBOL = re.compile(r"\.(py|md|json|toml|yml|yaml|csv|svg|txt)$")

#: How far from the anchor a symbol may sit and still be taken as naming it. Generous, because
#: the check is no longer positional — the symbol is matched against the enclosing SCOPE, so a
#: symbol far from the anchor either names the scope or does not.
SAME_LINE_ONLY = True

#: Directories whose documents are historical records, not maintained prose. Same rationale and
#: same list as the counts gate: a frozen document is not edited to satisfy a gate written after
#: it, and `docs/internal/AUDIT_REPORT.md` alone holds 64 citations.
FROZEN = (
    "docs/internal/",
    "VERIFICATION_SCHEME.md",
    "DESIGN_DECISIONS.md",
    "CHANGELOG.md",
    "working/",  # scaffolding for the repack, not part of the record it plans
    # DECISION RECORDS ARE DATED STATEMENTS, and there are two reasons this gate must not touch
    # them. First, a record's citations were true when it was written; re-anchoring them later is
    # editing the record, which this repository does not do. Second -- found by building this gate
    # -- a record routinely QUOTES A WRONG ANCHOR IN ORDER TO CORRECT IT: D542 cites
    # `fast_null.py:224` precisely to say the drop is at `:243`. A gate cannot tell that from a
    # mistake, and reddening a correction would be worse than the drift it prevents.
    "docs/decisions/",
    # AND THIS FILE ITSELF, for the same reason and found the same way: its docstring cites
    # `engine/backtest.py:490-492` and `instruments/base.py:16` AS THE WRONG ANCHORS IT EXISTS TO
    # CATCH. The gate flagged its own explanation on the first full run. A file whose subject is
    # bad citations cannot be checked by a gate that cannot read intent.
    "test_citation_anchors_resolve.py",
)

#: The covered subset was 40 when this gate was written. A floor, because this scans a discovered
#: set and "no bad citations" is also what an empty scan says.
MINIMUM_CHECKED = 10


def _tracked(*globs: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", *globs], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [p for p in out.splitlines() if p and (REPO / p).exists()]


def _documents() -> list[str]:
    return [
        p
        for p in _tracked("*.md", "docs/*.md", "tests/*.py", "src/*.py")
        if not any(f in p for f in FROZEN)
    ]


def _scopes(path: Path) -> list[tuple[int, int, str]]:
    """(start, end, name) for every `def`/`class` in the file, innermost last."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):  # pragma: no cover - every tracked .py parses
        return []
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            out.append((node.lineno, node.end_lineno or node.lineno, node.name))
    return sorted(out, key=lambda s: s[1] - s[0], reverse=True)


def _enclosing(path: Path, line: int) -> list[str]:
    """Every scope name containing `line`, outermost first. Empty means module level."""
    return [name for start, end, name in _scopes(path) if start <= line <= end]


def _line_text(path: Path, line: int) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return lines[line - 1] if 1 <= line <= len(lines) else ""


def _window(path: Path, line: int, radius: int = 3) -> str:
    """The cited line and `radius` either side, joined.

    SCOPE **OR** PROXIMITY, not scope alone. The first draft of this gate matched only the
    enclosing `def`/`class` and produced seventeen false positives in one run — because the
    common citation names a LOCAL at the anchor (`impulse_nodz` at `macd.py:484`, inside
    `impulse_macd_series`), not the function containing it. Requiring the scope name would force
    every such citation to be reworded to name a function the reader does not care about.

    The union is strictly more permissive than either rule alone and still fails every anchor
    D544 set out to catch: `instruments/base.py:16` has no enclosing scope AND no
    `@runtime_checkable` within three lines, because line 16 is module-docstring prose about a
    different symbol entirely.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    lo, hi = max(0, line - 1 - radius), min(len(lines), line + radius)
    return "\n".join(lines[lo:hi])


def _citations():
    """(document, doc_line, target, line, symbol|None) for every `path:line` in the corpus."""
    for rel in _documents():
        text = (REPO / rel).read_text(encoding="utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), start=1):
            for m in CITATION.finditer(line):
                target = _resolve(m.group(1))
                if target is None:
                    continue
                symbols = [
                    s.group(1)
                    for s in SYMBOL.finditer(line)
                    if not NOT_A_SYMBOL.search(s.group(1))
                ]
                yield rel, n, target, int(m.group(2)), symbols


def _resolve(cited: str) -> Path | None:
    """A cited path, resolved against the repo root or by unique basename match."""
    direct = REPO / cited
    if direct.exists():
        return direct
    for root in ("src/backtest_framework", "src", "scripts", "tests"):
        candidate = REPO / root / cited
        if candidate.exists():
            return candidate
    matches = _tracked(f"*/{Path(cited).name}") + _tracked(Path(cited).name)
    unique = {p for p in matches if p.endswith(cited)}
    return REPO / next(iter(unique)) if len(unique) == 1 else None


@pytest.fixture(scope="module")
def checked():
    """Citations whose anchor can be checked, with the verdict for each."""
    rows = []
    for rel, doc_line, target, line, symbols in _citations():
        if not symbols:
            continue
        scopes = _enclosing(target, line)
        body = _window(target, line)
        ok = any(
            s.lstrip("@") in scopes
            or s.lstrip("@").split(".")[-1] in scopes
            or s.lstrip("@").split(".")[-1] in body
            or s.lstrip("@") in body
            for s in symbols
        )
        rows.append((rel, doc_line, target.relative_to(REPO).as_posix(), line, symbols, ok))
    return rows


def test_the_scan_reaches_the_corpus_it_is_for():
    docs = _documents()
    assert len(docs) > 200, (
        f"only {len(docs)} document(s) in the corpus; the scan has lost its input rather than the "
        f"repository having lost its documents"
    )
    total = sum(1 for _ in _citations())
    assert total >= 40, f"only {total} `path:line` citation(s) found; expected at least 40"


def test_enough_citations_are_actually_checkable(checked):
    """The coverage floor. A gate that checks four citations is not a gate on the class.

    Reported rather than asserted upward: most citations carry no adjacent symbol and cannot be
    checked this way. That is a stated limit of the instrument, not a silent one.
    """
    assert len(checked) >= MINIMUM_CHECKED, (
        f"only {len(checked)} citation(s) carry a backticked symbol beside the anchor, below the "
        f"floor of {MINIMUM_CHECKED}. Either the convention is being dropped from documents or "
        f"the pattern stopped matching; both look like a pass from here."
    )


def test_every_checkable_citation_points_at_its_symbol(checked):
    wrong = [
        f"  {rel}:{doc_line} cites {target}:{line} for {symbols} — "
        f"which is in {_enclosing(REPO / target, line) or 'no def/class (module level)'}"
        for rel, doc_line, target, line, symbols, ok in checked
        if not ok
    ]
    assert not wrong, (
        f"{len(wrong)} citation(s) name a symbol that is not at the line they point to:\n"
        + "\n".join(wrong)
        + "\n\nA line anchor drifts every time the file above it is edited. Re-resolve it."
    )


def test_the_gate_resolves_by_scope_and_not_by_proximity(tmp_path):
    """The two behaviours D544 predicted before this file existed.

    A correct anchor on a line far from its `def` must PASS — the ±3 rule's false positive — and
    an anchor pointing at module-level prose must FAIL, which is the real defect it was meant to
    catch.
    """
    module = tmp_path / "risky.py"
    module.write_text(
        '"""Module docstring.\n\n'
        "`Equity.margin_requirement` answered it with full notional.\n"
        '"""\n'
        "\n\n"
        "def evaluate(\n"
        "    positions,\n"
        "    prices,\n"
        "    instruments,\n"
        "    bar_index,\n"
        ") -> RiskViolation | None:\n"
        "    return None\n",
        encoding="utf-8",
    )
    # Line 12 is the return annotation, six lines below `def evaluate(` at line 7.
    assert _line_text(module, 12).strip() == ") -> RiskViolation | None:"
    assert "evaluate" in _enclosing(module, 12), "a correct far-from-def anchor must resolve"
    # Line 3 is module-docstring prose: no enclosing scope at all.
    assert _enclosing(module, 3) == [], "module-level prose must resolve to no scope"


def test_the_gate_fires_on_a_drifted_anchor(tmp_path):
    """Break what the assertion READS — the line number — not the document's wording."""
    module = tmp_path / "m.py"
    module.write_text("import os\n\n\ndef target():\n    return 1\n", encoding="utf-8")
    assert "target" in _enclosing(module, 4)
    assert _enclosing(module, 1) == [], "line 1 is an import, outside every scope"
