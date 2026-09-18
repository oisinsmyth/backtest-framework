"""Executes docs/TUTORIAL.md's code, verbatim (D91).

Every ```python fence whose first line is `# runnable` is extracted and exec'd in
ONE shared namespace, in document order — later blocks intentionally use earlier
blocks' variables, exactly as a reader following along would. `WORKDIR` is injected
as a temp directory. If any framework API the tutorial shows drifts, this test
fails: the tutorial cannot silently rot (same discipline as the D82 label test and
the D84 options-doc test, but stronger — the doc is *executed*, not grepped).
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
TUTORIAL = REPO / "docs" / "TUTORIAL.md"

#: The README carries one runnable block too, added in D545, and it is EXTRACTED rather than
#: copied. The README itself names why (line ~175): "two copies of the same prose drift apart --
#: the most repeated defect in this project's own history (D176, D183, D186)". Pasting the
#: tutorial's code into the front page would gate neither copy; pointing this extractor at a
#: second file gates both.
#:
#: The README block runs in its OWN namespace, not the tutorial's shared one: a front-page
#: sample a reader copies must stand alone, and inheriting a variable from a document it never
#: mentions is exactly the kind of false affordance D48 refuses.
SOURCES = (TUTORIAL, REPO / "README.md")

_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _runnable_blocks(source: Path = TUTORIAL) -> list[str]:
    text = source.read_text(encoding="utf-8")
    blocks = [m.group(1) for m in _FENCE.finditer(text)]
    return [b for b in blocks if b.lstrip().startswith("# runnable")]


def test_tutorial_has_a_meaningful_number_of_runnable_blocks():
    blocks = _runnable_blocks()
    assert len(blocks) >= 8, f"only {len(blocks)} runnable blocks — did the markers change?"


def test_every_runnable_tutorial_block_executes_in_order(tmp_path, capsys):
    namespace: dict = {"WORKDIR": tmp_path}
    for i, block in enumerate(_runnable_blocks()):
        try:
            exec(compile(block, f"TUTORIAL.md[runnable block {i}]", "exec"), namespace)
        except Exception as exc:  # pragma: no cover - the message is the point
            raise AssertionError(
                f"Tutorial block {i} no longer runs against the current API "
                f"({type(exc).__name__}: {exc}) — fix TUTORIAL.md or the regression."
            ) from exc


def test_the_readme_carries_a_runnable_example(capsys):
    """The front page had no Python at all until D545 (A28).

    `CostStack` did not appear in `README.md` in any form — not in a fence, not in prose — in a
    repository whose central claim is composability, and the first pointer to a usable example
    was an outbound link on line 203.
    """
    blocks = _runnable_blocks(REPO / "README.md")
    assert len(blocks) >= 1, (
        "README.md carries no `# runnable` python block. The front page is allowed to have no "
        "code; it is not allowed to have code that nothing executes."
    )
    for i, block in enumerate(blocks):
        try:
            exec(compile(block, f"README.md[runnable block {i}]", "exec"), {})
        except Exception as exc:  # pragma: no cover - the message is the point
            raise AssertionError(
                f"README block {i} no longer runs against the current API "
                f"({type(exc).__name__}: {exc}) — fix README.md or the regression."
            ) from exc


def test_every_runnable_source_is_actually_scanned():
    """A floor on the SOURCES list, not on one file's block count.

    `_runnable_blocks` takes a default argument, so a caller that forgets to pass a source
    silently re-scans the tutorial and passes. This asserts each declared source contributes at
    least one block, which is the property the two tests above rely on.
    """
    for source in SOURCES:
        assert source.exists(), f"{source} is declared a runnable source and is not there"
        assert _runnable_blocks(source), (
            f"{source.name} is in SOURCES but carries no `# runnable` block, so whichever test "
            f"covers it is executing nothing"
        )
