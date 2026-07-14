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

_FENCE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _runnable_blocks() -> list[str]:
    text = TUTORIAL.read_text(encoding="utf-8")
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
