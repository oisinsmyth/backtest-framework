"""Shared test helpers. The first `conftest.py` in this project, and it exists for one reason.

D536 dropped 115 bulk panels (`*.csv.gz`, `*.parquet`, `*.npz`, `*.zip`, 844 MB) from the index.
The files are still on this machine and on any machine that built them, so the suite is unchanged
here — but a **fresh clone does not have them**, and before this file nine call sites loaded a
panel with no `exists()` check, so a clone errored on ~64 tests instead of skipping them. A test
that cannot get its data has not failed; it has not run.

The convention already existed, inline, at thirteen sites (and as a `skipif` at
`tests/unit/test_us_shorts_fixture.py`). This is that convention with one home.

It is exposed as a **session-scoped fixture** rather than an importable function on purpose:
`tests/` has no `__init__.py`, so pytest puts each test file's own directory on `sys.path` and
`from conftest import ...` would resolve to whichever conftest sits beside the test. A fixture is
found by pytest's own collection rules from any depth, and session scope lets the module-scoped
fixtures that need it depend on it (a module-scoped fixture may not depend on a function-scoped
one).

**A skip here is not a pass.** `data/data_manifest.json` lists every panel with its sha256 and the
git blob id it had when it was last tracked, so a skipped test names data that is recoverable:

    git cat-file blob <git_blob> > <path>
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path
from typing import Callable, Iterator

import pytest

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "data_manifest.json"


@lru_cache(maxsize=1)
def _panel_names() -> frozenset[str]:
    """The basenames D536 untracked, read from the manifest.

    This set is what makes `loading_a_panel` safe: a missing file whose name is in here is a
    panel the repository deliberately stopped carrying, and skipping is right. A missing file
    whose name is NOT in here is a bug — a typo'd path, a renamed artifact, a fixture nobody
    built — and it re-raises. Without that distinction the guard would convert every
    FileNotFoundError into a green run, which is how a suite stops testing anything.
    """
    if not MANIFEST.exists():  # pragma: no cover - the manifest is committed
        return frozenset()
    return frozenset(
        Path(f["path"]).name for f in json.loads(MANIFEST.read_text())["files"]
    )


@pytest.fixture(scope="session")
def requires_panel() -> Callable[[Path], None]:
    """Skip the calling test when a bulk panel is absent (D536).

    Call it at the top of the fixture that loads the panel, not at module level — a module-level
    skip would take the file's synthetic tests down with it, and those are the majority.
    """

    def _requires(path: Path) -> None:
        if not path.exists():
            pytest.skip(_reason(Path(path).name))

    return _requires


def _reason(name: str) -> str:
    return (
        f"{name} absent — the bulk panels left the index in D536. "
        "See data/data_manifest.json for its sha256 and git blob id."
    )


@pytest.fixture(scope="session")
def loading_a_panel():
    """For a test that reaches a panel through a study script rather than by naming a path.

    Several `tests/unit/test_<study>.py` files exec a `scripts/run_*.py` module and call its
    helpers, which open a panel several frames down through a fixture constant this test never
    sees. There is no path to hand `requires_panel`, so wrap the call instead:

        def test_something(loading_a_panel):
            with loading_a_panel():
                panel, books = R.books_on_crypto()

    **It is not a blanket except-and-skip.** Only a missing file the manifest lists is treated
    as an absent panel; everything else propagates, so a wrong path still fails loudly.
    """

    @contextmanager
    def _guard() -> Iterator[None]:
        try:
            yield
        except OSError as exc:
            missing = Path(exc.filename) if exc.filename else None
            if missing and missing.name in _panel_names() and not missing.exists():
                pytest.skip(_reason(missing.name))
            raise

    return _guard
