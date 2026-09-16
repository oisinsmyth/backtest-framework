"""The root holds exactly the results documents it is supposed to, and no others.

**This guard exists because the move that created it could undo itself silently.** Every
`*_RESULTS.md` in this project is written by a script, and every one of those scripts hardcodes
its output path. When 25 of them moved to `docs/results/`, 34 path expressions in `scripts/` had
to move with them — and a single missed one puts the file back at root on the next run.

Two failure shapes, and the quiet one is why this is a test rather than a convention:

* the nine `STRUCTURE_RESULTS.md` appenders call `read_text()` with no `exists()` guard, so a
  missed repoint crashes and is obvious;
* `run_etf_intraday_gate.py` reads `RESULTS.read_text() if RESULTS.exists() else _scaffold()`, so
  a missed repoint would have written a **fresh, history-less** document at root and said nothing.

**Glob the filesystem, not `git ls-files`.** A regenerated file is untracked, which is exactly the
case this guard exists to catch and exactly the case the index would miss.

When the remaining 14 move, this list is what gets edited — the assertion does not need rewriting.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# **Empty, and that is the point.** This set held the 14 documents whose paths tests pinned, which
# is why they stayed at root for a round after the other 25 moved. They are now in docs/results/
# with their 17 writers and 14 test path expressions, so the assertion below has become the
# strongest form it can take: NO results document belongs at the repository root, ever. The set
# stays rather than being deleted because an exception, if one is ever justified, belongs here
# where the reason can be written next to it.
PINNED_AT_ROOT: set[str] = set()


def test_no_unexpected_results_document_at_the_repository_root():
    # `*_RESULTS*.md` rather than `*_RESULTS.md`: the smoke variant is called
    # ETF_INTRADAY_RESULTS.smoke.md, it is gitignored so it never shows in a diff, and the
    # narrower glob missed it. A guard that only catches the tracked case catches the easy case.
    found = {p.name for p in REPO.glob("*_RESULTS*.md")}

    strays = sorted(found - PINNED_AT_ROOT)
    assert not strays, (
        f"{strays} reappeared at the repository root. A writer script is still targeting "
        "REPO / '<NAME>_RESULTS.md' instead of REPO / 'docs' / 'results' / '<NAME>_RESULTS.md'."
    )

    missing = sorted(PINNED_AT_ROOT - found)
    assert not missing, (
        f"{missing} left the root without this list being updated. If they moved to "
        "docs/results/, move them out of PINNED_AT_ROOT in the same commit."
    )


def test_the_moved_documents_are_where_they_were_moved_to():
    """The other half: all 39 are present in docs/results/ under their original names.

    Named individually rather than counted, because a count passes while the wrong file sits
    there. 25 arrived in the first move, the 14 test-pinned ones in the second.
    """
    moved = {
        # the 14 whose paths tests pinned
        "ASSEMBLED_RESULTS.md", "BOOK_CRYPTO_RESULTS.md", "BOOK_EXTENDED_RESULTS.md",
        "BREAKOUT_RESULTS.md", "COMBINED_BOOK_RESULTS.md", "MACD_RESULTS.md",
        "SAMPLING_RESULTS.md", "SCALING_RESULTS.md", "SHORT_MIRROR_RESULTS.md",
        "TERRAIN_RESULTS.md", "TSMOM_ARM_RESULTS.md", "UPTREND_ONSET_RESULTS.md",
        "UPTREND_WITHHELD_RESULTS.md", "WEDGE_INVERSE_RESULTS.md",
        # the 25 that moved first
        "ACTIVATION_THRESHOLD_RESULTS.md", "BOOK_SHORTS_CRYPTO_RESULTS.md",
        "BOOK_SINGLE_NAMES_RESULTS.md", "BOOK_WIDE_RESULTS.md", "BOOTSTRAP_SWEEP_RESULTS.md",
        "BREAKDOWN_RESULTS.md", "CROSS_SECTIONAL_PRESCREEN_RESULTS.md", "ETF_INTRADAY_RESULTS.md",
        "EXPOSURE_DIAL_RESULTS.md", "FILTER_SEARCH_RESULTS.md", "INDEX_SPREAD_RESULTS.md",
        "INTRADAY_FILTERED_RESULTS.md", "INTRADAY_SHORTS_RESULTS.md", "JERK_RUNG_RESULTS.md",
        "OVERNIGHT_DECOMPOSITION_RESULTS.md", "RISK_CONTROLS_RESULTS.md",
        "SCALE_CORRECTED_RESULTS.md", "SINGLE_NAME_INTRADAY_RESULTS.md", "STOPS_BOOK_RESULTS.md",
        "STOPS_TARGETS_RESULTS.md", "STRUCTURE_RESULTS.md", "VOL_TARGETED_HOLD_RESULTS.md",
        "WEDGE_CRYPTO_RESULTS.md", "WITHHELD_TEST_RESULTS.md", "XSEC_TREND_ARM_RESULTS.md",
    }
    present = {p.name for p in (REPO / "docs" / "results").glob("*_RESULTS.md")}
    assert moved <= present, f"missing from docs/results/: {sorted(moved - present)}"
