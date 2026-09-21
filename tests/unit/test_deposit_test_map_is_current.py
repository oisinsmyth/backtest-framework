"""`data/deposit_test_map.json` still describes this repository (D607).

Five gates, and the fourth is the one that earns the file:

  (a) the map holds 146 entries with the per-document counts the deposit declares, and no
      `(doc, number)` twice;
  (b) every `claimed` entry points at a file that is IN `git ls-files` -- the index, not the
      worktree, for the reason `tests/unit/test_encoding_is_declared.py` gives -- and every
      `function` claim's symbol is a `def` in that file;
  (c) every `covered_via` target is a `claimed` entry, so nothing is discharged by a test
      nobody wrote;
  (d) `scripts/deposit_test_map.py --scan` reports ZERO disagreements: no claim site in the
      tree the JSON has not recorded, no JSON claim the tree no longer carries, no line that
      has moved. This is the direction that catches a parallel agent writing a test that
      discharges a numbered item without anyone updating the map;
  (e) IF the five deposit documents are on disk, the parsed section counts and every item's
      verbatim text equal the JSON's. They are UNTRACKED, so a clone has none of them, and
      this one test SKIPS rather than failing there. The JSON carries the verbatim text
      precisely so that (a) through (d) and the rendered page do not need the documents.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

from backtest_framework.validation.crosswalk import (
    DOC_KEYS,
    load_map,
    load_payload,
)

REPO = Path(__file__).resolve().parents[2]
DEPOSIT = REPO / "docs" / "internal" / "User-Doc-Deposit"

#: The counts the five documents declare, read off their own numbered lists.
EXPECTED_COUNTS = {"ledger": 71, "index": 28, "opening": 25, "shock": 13, "letf": 9}
EXPECTED_TOTAL = 146


def _load_script():
    """`scripts/deposit_test_map.py`, by path, the way this suite loads every runner.

    Registered in `sys.modules` BEFORE `exec_module` because the script defines frozen
    dataclasses and `dataclasses._is_type` reads `sys.modules[cls.__module__].__dict__`;
    without the registration that lookup returns None and the import dies in the decorator.
    """
    name = "_d607_deposit_test_map"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / "deposit_test_map.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _tracked() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return {line.strip() for line in out.split("\n") if line.strip()}


ROWS = load_map()
PAYLOAD = load_payload()


# ============================================================ (a) the shape


def test_the_map_holds_every_numbered_test_in_the_five_documents():
    assert len(ROWS) == EXPECTED_TOTAL
    per_doc = {doc: sum(1 for r in ROWS if r.doc == doc) for doc in DOC_KEYS}
    assert per_doc == EXPECTED_COUNTS
    assert sum(EXPECTED_COUNTS.values()) == EXPECTED_TOTAL


def test_the_docs_block_agrees_with_the_counts_and_names_a_real_looking_section():
    for doc, count in EXPECTED_COUNTS.items():
        meta = PAYLOAD["docs"][doc]
        assert meta["count"] == count
        assert meta["file"].endswith("_PREREG.md")
        assert meta["heading"].endswith("Required unit tests")
        assert meta["heading_line"] < meta["first_item_line"] <= meta["last_item_line"]
        span = meta["last_item_line"] - meta["first_item_line"] + 1
        assert span == count, f"{meta['file']}: {span} item lines for {count} tests"


def test_no_doc_number_appears_twice_and_each_document_runs_one_to_n():
    keys = [r.key for r in ROWS]
    assert len(keys) == len(set(keys))
    for doc, count in EXPECTED_COUNTS.items():
        assert sorted(r.number for r in ROWS if r.doc == doc) == list(range(1, count + 1))


def test_every_row_carries_its_verbatim_text_so_the_page_renders_without_the_deposit():
    for row in ROWS:
        assert row.text.strip(), f"{row.key} has no verbatim text"
        assert row.paraphrase.strip(), f"{row.key} has no paraphrase"


#: The per-document claimed counts D607 quotes, as amended 2026-09-21 when round 3's tests
#: (D608-D606) were staged and recorded: 28 -> 43. **Editing these numbers is the point.**
#: They are pinned so that a claim added without amending the record turns this red; the fix
#: is to update both together, never to loosen the assertion into `>=`.
CLAIMED_PER_DOC = {"ledger": 29, "index": 6, "opening": 6, "shock": 2, "letf": 0}
CLAIMED_TOTAL = 43


def test_the_claimed_counts_are_the_ones_the_record_quotes_and_letf_is_at_zero():
    """The numbers D607 quotes. A count that drifts silently is the whole defect."""
    claimed = {doc: sum(1 for r in ROWS if r.doc == doc and r.is_claimed) for doc in DOC_KEYS}
    assert claimed == CLAIMED_PER_DOC
    assert sum(claimed.values()) == CLAIMED_TOTAL == sum(CLAIMED_PER_DOC.values())
    assert sum(1 for r in ROWS if not r.is_claimed) == EXPECTED_TOTAL - CLAIMED_TOTAL
    assert claimed["letf"] == 0, (
        "LETF_CLOSE_FLOW_PREREG.md has nine numbered tests and no repository test names any "
        "of them; when that changes, amend the record rather than this line alone"
    )


# ============================================================ (b) the claims exist


def test_every_claim_points_at_a_tracked_file():
    tracked = _tracked()
    for row in ROWS:
        if row.claim is None:
            continue
        assert row.claim.file in tracked, (
            f"{row.key} claims {row.claim.file}, which is not in `git ls-files`. A claim on "
            "an untracked file is invisible to every reader but its author."
        )


def test_every_function_claim_is_a_def_in_the_file_it_names():
    for row in ROWS:
        claim = row.claim
        if claim is None or claim.kind != "function":
            continue
        text = (REPO / claim.file).read_text(encoding="utf-8")
        assert f"def {claim.symbol}(" in text, (
            f"{row.key}: `def {claim.symbol}(` is not in {claim.file}"
        )
        line = text.split("\n")[claim.line - 1]
        assert f"def {claim.symbol}(" in line, (
            f"{row.key}: {claim.file}:{claim.line} does not define {claim.symbol}"
        )


def test_every_claim_line_exists_in_its_file():
    for row in ROWS:
        claim = row.claim
        if claim is None:
            continue
        lines = (REPO / claim.file).read_text(encoding="utf-8").split("\n")
        assert claim.line <= len(lines), f"{row.key}: {claim.file} has no line {claim.line}"


def test_claims_of_test_kinds_live_under_tests_and_record_claims_under_docs_decisions():
    for row in ROWS:
        claim = row.claim
        if claim is None:
            continue
        if claim.kind == "record":
            assert claim.file.startswith("docs/decisions/"), row.key
            assert row.status == "declined", row.key
        else:
            assert claim.file.startswith("tests/"), row.key
            assert re.search(r"/test_[^/]+\.py$", claim.file), row.key


def test_every_banner_or_message_claim_line_carries_its_number():
    for row in ROWS:
        claim = row.claim
        if claim is None or claim.kind not in ("banner", "message"):
            continue
        line = (REPO / claim.file).read_text(encoding="utf-8").split("\n")[claim.line - 1]
        assert str(row.number) in line, (
            f"{row.key}: {claim.file}:{claim.line} does not contain the number: {line!r}"
        )


# ============================================================ (c) covered_via


def test_every_covered_via_target_is_a_claimed_entry():
    claimed = {r.key for r in ROWS if r.is_claimed}
    targets = [(r.key, r.covered_via) for r in ROWS if r.covered_via is not None]
    assert targets, "the map records no covered_via at all; check the curation"
    for key, target in targets:
        assert target in claimed, f"{key} is covered via {target}, which nothing claims"


def test_the_four_opening_restatements_are_the_only_covered_via_rows():
    via = sorted(r.key for r in ROWS if r.status == "covered_via")
    assert via == [("opening", 21), ("opening", 22), ("opening", 23), ("opening", 24)]


def test_every_declined_row_names_the_record_that_declined_it():
    declined = [r for r in ROWS if r.status == "declined"]
    assert sorted(r.key for r in declined) == [("ledger", n) for n in range(54, 59)]
    for row in declined:
        assert row.claim is not None and row.claim.kind == "record"
        assert row.note.startswith("DECLINED")


# ============================================================ (d) the scan agrees


def test_the_scan_of_the_tracked_tests_reports_zero_disagreements():
    module = _load_script()
    report = module.scan(ROWS, PAYLOAD)
    assert report.scanned_files > 100, "the scan found almost no test files; read it"
    assert report.found, "the scan found no numbered claim site at all; a gate that cannot fire"
    assert not report.disagreements, (
        "the crosswalk has gone stale:\n" + report.render() + "\n\n"
        "Update data/deposit_test_map.json and re-render with "
        "`uv run python scripts/deposit_test_map.py --render`."
    )


def test_the_scan_can_fire(tmp_path):
    """A break must hit the list the assertion reads, or the test above proves nothing."""
    module = _load_script()
    trimmed = [r for r in ROWS if r.key != ("ledger", 51)]
    report = module.scan(trimmed, PAYLOAD)
    assert report.unrecorded, "dropping a claim left the scan silent"
    assert any("ledger 51" in line or "/ledger 51" in line for line in report.unrecorded)


def test_the_selftest_passes():
    module = _load_script()
    assert module.selftest() == 0


# ============================================================ (e) the documents themselves


@pytest.mark.skipif(
    not all((DEPOSIT / f"{n}.md").exists() for n in (
        "SETTLEMENT_FLOW_LEDGER_PREREG", "INDEX_REWEIGHT_FLOW_PREREG",
        "OPENING_AGENT_STATE_PREREG", "SHOCK_CLASSIFIER_PREREG", "LETF_CLOSE_FLOW_PREREG")),
    reason=(
        "the five deposit pre-registrations are UNTRACKED, so a clone has none of them. "
        "The JSON carries every item's verbatim text for exactly this case; everything "
        "else in this file still runs."
    ),
)
def test_the_parsed_sections_equal_the_json():
    module = _load_script()
    diffs: list[str] = []
    for doc in DOC_KEYS:
        diffs.extend(module.parse_document_section(doc, PAYLOAD["docs"][doc], ROWS))
    assert not diffs, "the deposit documents have moved under the map:\n" + "\n".join(diffs)
