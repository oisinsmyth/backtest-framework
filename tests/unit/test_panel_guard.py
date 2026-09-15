"""The guard in `tests/conftest.py` must be able to fail.

`loading_a_panel` turns a missing bulk panel into a skip. A guard that turned EVERY missing
file into a skip would be worse than no guard: a typo'd path, a renamed artifact or a fixture
nobody built would all read as "data absent, nothing to see" and the suite would quietly stop
testing. So the discrimination is the behaviour worth pinning, and it is pinned in both
directions — one file the manifest lists, one it does not.
"""

from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "data" / "data_manifest.json"


def _a_listed_panel() -> Path:
    """Any path from the manifest — by construction one D536 stopped tracking."""
    entries = json.loads(MANIFEST.read_text())["files"]
    return REPO / entries[0]["path"]


def test_a_missing_file_the_manifest_does_not_know_still_raises(loading_a_panel, tmp_path):
    """The half that keeps the guard honest."""
    absent = tmp_path / "no_such_panel_anywhere.csv.gz"
    with pytest.raises(OSError):
        with loading_a_panel():
            gzip.open(absent, "rt").read()


def test_a_missing_file_the_manifest_lists_becomes_a_skip(loading_a_panel):
    """The other half, asserted without deleting anything.

    If the panel is present on this machine the guard has nothing to convert, so the test
    states that and stops — the interesting assertion is the one above, which holds either way.
    """
    panel = _a_listed_panel()
    if panel.exists():
        pytest.skip(f"{panel.name} is present here; the skip path needs it absent")

    with pytest.raises(BaseException) as caught:  # pytest.skip raises Skipped, not an Exception
        with loading_a_panel():
            gzip.open(panel, "rt").read()
    assert caught.typename == "Skipped"
