"""`src/` never imports from `scripts/`, and the framework never imports from `research/`.

**This test exists because `README.md:132` calls the first of those "load-bearing rather than
tidy" and nothing enforced it.** Both boundaries hold today — an AST scan finds zero violations
across all 85 tracked `src/` files — and both held by discipline alone. `PHILOSOPHY.md`'s first
pillar is the argument against exactly that: "If something must never happen, make it
*impossible*, not merely against the rules. An honor system fails exactly once, silently,
usually at 6:50am."

The cost of the omission is asymmetric, which is why it is worth twenty lines. The boundary is
easy to hold and easy to break by accident — one `from scripts.run_macd_ladder import PPY` in a
research module, added while debugging and never removed, and the library depends on a one-shot
runner that is not packaged, not typed (mypy's scope is `files = ["src"]`) and not linted in CI
before this round. Nothing would have said so.

WHAT EACH BOUNDARY IS FOR
-------------------------
**`src/` ↛ `scripts/`** is what makes the instrument independent of any use of it. `scripts/` is
592 one-shot runners; if the framework reached into one, the framework would stop being
installable without them and a study could change the engine's behaviour by editing a runner.

**framework ↛ `research/`** is the weaker, inner version: `src/backtest_framework/research/` is
study glue that sits inside the package for convenience. It may import the framework; the
framework may not import it, or "study code, not framework surface" (`README.md:108`) stops
being true and the 46-module library silently becomes a 72-module one.

WHY A TEXT SEARCH IS NOT ENOUGH
-------------------------------
The six textual mentions of `scripts/` in `src/` are all prose inside docstrings — a grep-based
gate would have to special-case them, and would still miss `importlib.util.spec_from_file_location`
loading a runner by path, which is how `tests/` loads them. The AST walk sees imports and the
extra checks below see the dynamic route.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

#: Top-level packages `src/` must never import. `tests` is included for completeness: it has
#: never been imported and would be a stranger defect than `scripts`.
FORBIDDEN_FROM_SRC = {"scripts", "tests", "working", "temp"}


def _tracked_src() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "src/*.py"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def _imported_roots(path: Path, rel: str) -> set[str]:
    """Every top-level module name this file imports, with relative imports resolved.

    A relative import is resolved against the file's own package, so `from ..research import x`
    inside `backtest_framework/analytics/` yields `backtest_framework.research`, which the
    framework check below can see. Without resolution, relative imports are invisible.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    parts = rel.split("/")[1:]  # drop 'src/'
    package = parts[:-1] if parts[-1] != "__init__.py" else parts
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                roots.add(".".join([*base, node.module] if node.module else base))
            elif node.module:
                roots.add(node.module)
    return roots


def test_src_never_imports_from_scripts():
    """The boundary README.md:132 calls load-bearing."""
    violations = []
    for rel in _tracked_src():
        path = REPO / rel
        if not path.exists():  # tracked but deleted in this worktree
            continue
        for name in _imported_roots(path, rel):
            if name.split(".")[0] in FORBIDDEN_FROM_SRC:
                violations.append(f"  {rel} imports {name}")
    assert not violations, (
        "the instrument must not depend on any use of it:\n"
        + "\n".join(sorted(violations))
        + "\n\nscripts/ is one-shot runners — not packaged, not in mypy's scope. A library that "
        "imports one cannot be installed without it."
    )


def test_the_framework_never_imports_from_research():
    """`research/` may import the framework. The framework may not import `research/`."""
    violations = []
    for rel in _tracked_src():
        if "/research/" in rel:
            continue
        path = REPO / rel
        if not path.exists():
            continue
        for name in _imported_roots(path, rel):
            if name.startswith("backtest_framework.research") or name == "research":
                violations.append(f"  {rel} imports {name}")
    assert not violations, (
        "research/ is study code, not framework surface (README.md:108):\n"
        + "\n".join(sorted(violations))
    )


def test_src_never_loads_a_module_by_path():
    """The dynamic route around both boundaries, which an import scan cannot see.

    `importlib.util.spec_from_file_location` is how `tests/` loads a runner, and it would let a
    library module do the same while importing nothing. Asserted separately because it is a
    different mechanism, not because it has ever happened.
    """
    offenders = []
    for rel in _tracked_src():
        path = REPO / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for needle in ("spec_from_file_location", "SourceFileLoader", "sys.path.insert", "sys.path.append"):
            if needle in text:
                offenders.append(f"  {rel} uses {needle}")
    assert not offenders, (
        "a library module is loading code by path, which routes around the import boundaries:\n"
        + "\n".join(sorted(offenders))
    )


def test_the_scan_reaches_the_files_it_is_for():
    """A boundary test over an empty file list passes by looking at nothing."""
    files = _tracked_src()
    assert len(files) >= 80, (
        f"git ls-files matched {len(files)} file(s) under src/; the library has ~85 modules, so "
        "this scan is looking at far less than it should and would pass on almost anything"
    )
    assert any(f.endswith("engine/backtest.py") for f in files), "the engine is not being scanned"
    assert any("/research/" in f for f in files), "research/ is not being scanned"
