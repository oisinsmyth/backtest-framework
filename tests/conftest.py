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

D609 MOVED THE DECISION, NOT THE POLICY
---------------------------------------
The present / absent-but-listed / absent-and-unlisted distinction was written here and it is now
`backtest_framework.data.panels.panel_status`, with `absent_reason` and `unlisted_message`
carrying the two sentences verbatim. It moved because two OTHER places had retyped it by hand —
`scripts/futures_impact_table.py` and `tests/unit/test_fut_book_depth.py` — and three copies of
one rule drift. **The behaviour of these fixtures is unchanged**: same branches, same messages,
same skip count.
"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Callable, Iterator

import pytest

from backtest_framework.data.panels import (
    absent_reason,
    panel_names,
    panel_status,
    unlisted_message,
)

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "data" / "data_manifest.json"


def _panel_names() -> frozenset[str]:
    """The basenames D536 untracked. `panels.panel_names` is the one implementation."""
    return panel_names()


@pytest.fixture(scope="session")
def requires_panel() -> Callable[[Path], None]:
    """Skip the calling test when a bulk panel is absent (D536).

    Call it at the top of the fixture that loads the panel, not at module level — a module-level
    skip would take the file's synthetic tests down with it, and those are the majority.

    The manifest check is what makes the skip honest. Without it this helper would answer EVERY
    missing file with "the bulk panels left the index in D536", which for a typo'd path, a
    renamed artifact or a fixture nobody built is a false explanation attached to a green run.
    A panel the manifest lists is a skip; a file it does not list is a bug, and a bug must not
    be reported as absent data.
    """

    def _requires(path: Path) -> None:
        status = panel_status(path)
        if status == "present":
            return
        if status == "absent_unlisted":
            raise FileNotFoundError(unlisted_message(path))
        pytest.skip(absent_reason(Path(path).name))

    return _requires


def _reason(name: str) -> str:
    return absent_reason(name)


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
