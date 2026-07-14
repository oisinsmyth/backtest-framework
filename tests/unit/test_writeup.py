"""Anti-rot tests for the Phase G writeup (docs/writeup.md, D97).

Same discipline as the D84 options-doc test and the D91 executable tutorial:
documents decay unless a test greps. The writeup quotes headline numbers from
five results artifacts; if a study is ever re-run and a headline moves, the
writeup must fail CI instead of silently lying.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
DOCS = REPO / "docs"

SNAPSHOT = "54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd"

#: (anchor string, source document) — each must appear in BOTH the writeup and
#: its source. Unicode minus is normalized to ASCII hyphen before comparison.
ANCHORS = [
    # One frozen snapshot behind every study
    (SNAPSHOT, DOCS / "results" / "pairs_study_v1.md"),
    (SNAPSHOT, DOCS / "results" / "pairs_study_v2.md"),
    (SNAPSHOT, DOCS / "results" / "pairs_study_v3.md"),
    (SNAPSHOT, DOCS / "results" / "capacity_analysis.md"),
    (SNAPSHOT, DOCS / "results" / "gross_exposure_study.md"),
    # v1: the Gatev baseline
    ("+3.45%", DOCS / "results" / "pairs_study_v1.md"),
    ("-13.01%", DOCS / "results" / "pairs_study_v1.md"),
    # v2: cointegration selection
    ("+19.03%", DOCS / "results" / "pairs_study_v2.md"),
    ("+5.70%", DOCS / "results" / "pairs_study_v2.md"),
    ("-6.43%", DOCS / "results" / "pairs_study_v2.md"),
    # v3: beta-hedged trading
    ("+6.12%", DOCS / "results" / "pairs_study_v3.md"),
    ("-16.53%", DOCS / "results" / "pairs_study_v3.md"),
    # capacity
    ("-5.77%", DOCS / "results" / "capacity_analysis.md"),
    ("2.68%", DOCS / "results" / "capacity_analysis.md"),
    ("+2.01%", DOCS / "results" / "capacity_analysis.md"),
    ("143.33%", DOCS / "results" / "capacity_analysis.md"),
    # gross exposure
    ("+0.12%/yr", DOCS / "results" / "gross_exposure_study.md"),
    ("-1.61", DOCS / "results" / "gross_exposure_study.md"),
    ("0.866%", DOCS / "results" / "gross_exposure_study.md"),
    ("+1.03%", DOCS / "results" / "gross_exposure_study.md"),
    # convention sensitivity (D105)
    ("+16.79%", DOCS / "results" / "convention_sensitivity.md"),
    ("-7.90%", DOCS / "results" / "convention_sensitivity.md"),
    # cross-engine reconciliation
    ("1,370", DOCS / "verification" / "cross_engine_reconciliation.md"),
    ("159,233.023491", DOCS / "verification" / "cross_engine_reconciliation.md"),
    ("1.30e-12", DOCS / "verification" / "cross_engine_reconciliation.md"),
    ("2,515", DOCS / "verification" / "cross_engine_reconciliation.md"),
]

REQUIRED_SECTIONS = [
    "## 1. Abstract",
    "## 2. The question",
    "## 3. Methodology",
    "## 4. Data",
    "## 5. The cost model",
    "## 6. Five studies, one variable each",
    "## 7. Statistical honesty",
    "## 8. Limitations",
    "## 9. Conclusions",
    "## 10. Future work",
    "## Appendices",
]


def _normalized(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("−", "-")


@pytest.fixture(scope="module")
def writeup() -> str:
    return _normalized(DOCS / "writeup.md")


def test_writeup_has_every_required_section(writeup):
    for section in REQUIRED_SECTIONS:
        assert section in writeup, f"writeup.md lost its '{section}' section"


@pytest.mark.parametrize("anchor,source", ANCHORS, ids=[f"{a[:24]}" for a, _ in ANCHORS])
def test_headline_number_matches_its_source_artifact(writeup, anchor, source):
    assert anchor in writeup, f"writeup.md no longer quotes {anchor!r}"
    assert anchor in _normalized(source), (
        f"{source.name} no longer contains {anchor!r} — a study was re-run and its "
        "headline moved; update the writeup, it is now lying"
    )


def test_readme_links_the_writeup():
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    assert "docs/writeup.md" in readme


def test_writeup_todos_are_prose_only():
    # Skeleton discipline: TODO markers may flag missing narrative, never
    # missing numbers - every quantitative claim must be final.
    text = _normalized(DOCS / "writeup.md")
    for marker_start in _find_all(text, "[TODO"):
        marker_end = text.index("]", marker_start)
        marker = text[marker_start : marker_end + 1]
        assert marker.startswith("[TODO prose"), (
            f"writeup TODO marker {marker!r} is not a prose marker - numbers must "
            "never be TODO in this document"
        )


def _find_all(text: str, needle: str) -> list[int]:
    positions, start = [], 0
    while (i := text.find(needle, start)) != -1:
        positions.append(i)
        start = i + 1
    return positions
