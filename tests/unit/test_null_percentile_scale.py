"""A null percentile and the bar it is compared against must be on the same scale (D542).

D542 collapsed `research/breakdown_study`'s null percentile from strictly-below on 0–1 to
the repository's canonical mid-rank on 0–100. The arithmetic change was tiny and fully
predicted — 0.507 became exactly 50.7, 0.955 exactly 95.5 — but `run_breakdown_study.py`
rendered the value with `{:.0%}` and compared it against a bar of `0.95`.

So the first re-run published **"Percentile vs the null: 5070%"** and, far worse, flipped
a verdict: BTC-USD went from *"does not beat the null"* to *"beats the null"*, and the
summary line from *"The null verdict is SPLIT and must not be read as a pass"* to *"The
entry rule beats the exposure-matched null on every symbol tested."* Nothing failed. It
was caught by diffing the rendered document, which is not a gate.

These are the gate. A unit change is exactly the kind of edit that looks safe in the
producer and is wrong in the consumer.
"""

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / "data" / "breakdown_study_summary.json"
REPORT = REPO / "docs" / "results" / "BREAKDOWN_RESULTS.md"
RUNNER = REPO / "scripts" / "run_breakdown_study.py"


@pytest.fixture(scope="module")
def nulls() -> dict[str, dict]:
    payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    detail = payload["baseline_detail"]
    found = {symbol: block["null"] for symbol, block in detail.items() if "null" in block}
    # A floor. This test scans a discovered set, and an empty scan passes every assertion
    # below without testing anything.
    assert len(found) >= 2, f"only {len(found)} null block(s) found; the scan has lost its input"
    return found


def test_every_published_null_percentile_is_on_the_zero_to_hundred_scale(nulls):
    """0–100, mid-rank. A value in [0, 1] would be indistinguishable from the old
    convention for any book that genuinely sits in the bottom percentile."""
    for symbol, null in nulls.items():
        value = null["percentile"]
        assert 0.0 <= value <= 100.0, f"{symbol}: {value} is outside [0, 100]"


def test_the_runner_compares_against_a_bar_on_the_same_scale(nulls):
    """Break what the assertion READS: the literal the verdict branches on.

    `>= 0.95` against a 0–100 value passes for every book above the 1st percentile, which
    is how a split verdict became a clean pass with no test failing.
    """
    source = RUNNER.read_text(encoding="utf-8")
    bars = re.findall(r'\["percentile"\]\s*(?:>=|<)\s*([0-9.]+)', source)
    assert bars, "no percentile threshold found in the runner; this gate has lost its input"
    for bar in bars:
        assert float(bar) == 95.0, (
            f"the runner compares the null percentile against {bar}, which is the 0-1 "
            f"convention; the published value is now mid-rank on 0-100"
        )


def test_the_report_never_renders_a_percentile_above_one_hundred(nulls):
    """`{:.0%}` on a 0–100 value prints 5070%. Nothing else in this document can."""
    text = REPORT.read_text(encoding="utf-8")
    absurd = [m for m in re.findall(r"percentile[^.\n]{0,40}?(\d{3,})%", text, re.IGNORECASE)]
    assert not absurd, f"percentages above 100 rendered beside 'percentile': {absurd[:5]}"


def test_the_written_verdict_agrees_with_the_number_it_claims_to_read(nulls):
    """The consumer check, not the producer one. The report states, per symbol, whether
    the strategy beats the null; that sentence must agree with the committed value."""
    text = REPORT.read_text(encoding="utf-8")
    beats = len(re.findall(r"strategy \*\*beats\*\* the null", text))
    misses = len(re.findall(r"strategy \*\*does not beat\*\* the null", text))
    expected_beats = sum(1 for n in nulls.values() if n["percentile"] >= 95.0)
    expected_misses = len(nulls) - expected_beats
    assert (beats, misses) == (expected_beats, expected_misses), (
        f"the report says {beats} beat / {misses} miss; the summary holds "
        f"{expected_beats} beat / {expected_misses} miss"
    )


def test_the_split_verdict_is_still_the_split_verdict(nulls):
    """The specific reading the scale bug erased, pinned by value.

    BTC-USD at 50.7 does not clear 95; ETH-USD at 95.5 does. The document must keep
    saying the verdict is SPLIT — the long study's rule is that a filter is kept only if
    it improves on EVERY symbol, and one of two is a coin flip.
    """
    assert nulls["BTC-USD"]["percentile"] == pytest.approx(50.7, abs=0.05)
    assert nulls["ETH-USD"]["percentile"] == pytest.approx(95.5, abs=0.05)
    assert "SPLIT and must not be read as a pass" in REPORT.read_text(encoding="utf-8")
