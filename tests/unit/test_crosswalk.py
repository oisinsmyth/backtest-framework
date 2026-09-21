"""`validation/crosswalk.py`: the validator raises, the coverage arithmetic is hand-checked,
and the committed page is exactly what the module renders (D607).

The renderer test is the shape `tests/unit/test_programme.py:195` uses for the programme
registry: render twice into `tmp_path`, assert the two are equal to each other AND to the
bytes committed at `docs/results/DEPOSIT_TEST_MAP.md`. Determinism alone would pass on a
page nobody had regenerated since the JSON changed; equality with the committed file is
what makes the page a render rather than a second, drifting, source of truth.

The synthetic map below is deliberately NOT the real one. Coverage arithmetic checked
against the real 146 rows would restate the JSON rather than test the function -- if the
denominator were wrong in both places the test would still pass.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backtest_framework.validation.crosswalk import (
    CLASSES,
    DEFAULT_MAP_PATH,
    DEFAULT_PAGE_PATH,
    DOC_KEYS,
    MAX_PARAPHRASE_WORDS,
    SCANNABLE_KINDS,
    SCHEMA,
    STATUSES,
    Claim,
    CrosswalkError,
    CrosswalkRow,
    assert_doc_counts,
    claim_kind_tally,
    class_tally,
    coverage_by_doc,
    coverage_total,
    load_map,
    load_payload,
    render_md,
    validate_crosswalk,
    write_md,
)

REPO = Path(__file__).resolve().parents[2]


def row(**kwargs) -> CrosswalkRow:
    base = dict(
        doc="letf", number=1, line=244, text="verbatim", paraphrase="a handle",
        cls="arithmetic", status="missing",
    )
    base.update(kwargs)
    return CrosswalkRow(**base)


def a_claim(**kwargs) -> Claim:
    base = dict(kind="message", file="tests/unit/test_crosswalk.py", line=7, symbol=None)
    base.update(kwargs)
    return Claim(**base)


# ============================================================ the validator raises (D48)


def test_an_empty_map_is_refused():
    with pytest.raises(CrosswalkError, match="nothing to gate"):
        validate_crosswalk([])


def test_a_clean_row_passes_and_returns_none():
    assert validate_crosswalk([row()]) is None


def test_a_duplicate_doc_number_is_refused():
    with pytest.raises(CrosswalkError, match="DUPLICATE"):
        validate_crosswalk([row(), row()])


def test_two_documents_may_share_a_number():
    validate_crosswalk([row(doc="letf", number=1), row(doc="shock", number=1)])


@pytest.mark.parametrize(
    "field, value, fragment",
    [
        ("doc", "gamma", "unknown document"),
        ("cls", "vibes", "unknown class"),
        ("status", "pending", "unknown status"),
        ("text", "   ", "verbatim text"),
        ("paraphrase", "", "a paraphrase"),
        ("number", 0, "non-positive test number"),
    ],
)
def test_a_bad_field_is_named(field, value, fragment):
    with pytest.raises(CrosswalkError, match=fragment):
        validate_crosswalk([row(**{field: value})])


def test_a_paraphrase_over_the_ceiling_is_refused():
    ok = " ".join(["w"] * MAX_PARAPHRASE_WORDS)
    validate_crosswalk([row(paraphrase=ok)])
    with pytest.raises(CrosswalkError, match="word paraphrase against a ceiling"):
        validate_crosswalk([row(paraphrase=ok + " over")])


def test_claimed_without_a_claim_is_refused():
    with pytest.raises(CrosswalkError, match="`claimed` with no claim"):
        validate_crosswalk([row(status="claimed")])


def test_missing_with_a_claim_is_refused():
    with pytest.raises(CrosswalkError, match="never `missing`"):
        validate_crosswalk([row(status="missing", claim=a_claim())])


def test_a_claim_with_no_file_is_refused():
    with pytest.raises(CrosswalkError, match="claim with no file"):
        validate_crosswalk([row(status="claimed", claim=a_claim(file=""))])


def test_a_claim_with_a_non_positive_line_is_refused():
    with pytest.raises(CrosswalkError, match="non-positive line"):
        validate_crosswalk([row(status="claimed", claim=a_claim(line=0))])


def test_a_claim_of_unknown_kind_is_refused():
    with pytest.raises(CrosswalkError, match="unknown kind"):
        validate_crosswalk([row(status="claimed", claim=a_claim(kind="rumour"))])


def test_a_function_claim_needs_its_symbol():
    with pytest.raises(CrosswalkError, match="no symbol"):
        validate_crosswalk([row(status="claimed", claim=a_claim(kind="function"))])
    validate_crosswalk([row(status="claimed", claim=a_claim(kind="function", symbol="test_x"))])


def test_a_record_claim_may_not_claim_a_test():
    """`record` points into `docs/decisions/`, which is not a test."""
    with pytest.raises(CrosswalkError, match="is not a test"):
        validate_crosswalk([row(status="claimed", claim=a_claim(kind="record"))])


def test_declined_needs_a_record_claim():
    with pytest.raises(CrosswalkError, match="without a `record` claim"):
        validate_crosswalk([row(status="declined")])
    with pytest.raises(CrosswalkError, match="without a `record` claim"):
        validate_crosswalk([row(status="declined", claim=a_claim(kind="message"))])
    validate_crosswalk(
        [row(status="declined", claim=a_claim(kind="record", file="docs/decisions/D588-x.md"))]
    )


def test_covered_via_must_point_at_a_claimed_row():
    target = row(doc="ledger", number=66, status="claimed", claim=a_claim())
    via = row(doc="opening", number=21, status="covered_via", covered_via=("ledger", 66))
    validate_crosswalk([target, via])
    with pytest.raises(CrosswalkError, match="not a `claimed` row"):
        validate_crosswalk([via])
    unclaimed = row(doc="ledger", number=66, status="missing")
    with pytest.raises(CrosswalkError, match="not a `claimed` row"):
        validate_crosswalk([unclaimed, via])


def test_covered_via_may_not_carry_its_own_claim_or_point_at_itself():
    target = row(doc="ledger", number=66, status="claimed", claim=a_claim())
    with pytest.raises(CrosswalkError, match="belongs on the target row"):
        validate_crosswalk(
            [target, row(doc="opening", number=21, status="covered_via",
                         covered_via=("ledger", 66), claim=a_claim())]
        )
    with pytest.raises(CrosswalkError, match="covered via itself"):
        validate_crosswalk(
            [row(doc="ledger", number=66, status="claimed", claim=a_claim()),
             row(doc="opening", number=21, status="covered_via", covered_via=("opening", 21))]
        )


def test_claimed_and_covered_via_together_is_refused():
    target = row(doc="ledger", number=66, status="claimed", claim=a_claim())
    with pytest.raises(CrosswalkError, match="cannot be both"):
        validate_crosswalk(
            [target, row(doc="opening", number=21, status="claimed", claim=a_claim(),
                         covered_via=("ledger", 66))]
        )


def test_the_validator_names_the_first_offender_and_not_a_later_one():
    with pytest.raises(CrosswalkError) as caught:
        validate_crosswalk([row(doc="letf", number=1, cls="vibes"), row(doc="shock", number=99)])
    assert "number=1" in str(caught.value) and "number=99" not in str(caught.value)


# ============================================================ assert_doc_counts


META = {"letf": {"file": "LETF_CLOSE_FLOW_PREREG.md", "count": 3, "heading": "## 8. x",
                 "heading_line": 242, "first_item_line": 244, "last_item_line": 246}}


def test_doc_counts_pass_on_a_contiguous_run():
    assert_doc_counts([row(number=n, line=243 + n) for n in (1, 2, 3)], META) is None


def test_doc_counts_refuse_a_gap_and_an_overshoot():
    with pytest.raises(CrosswalkError, match=r"missing \[2\]"):
        assert_doc_counts([row(number=n) for n in (1, 3)], META)
    with pytest.raises(CrosswalkError, match=r"extra \[4\]"):
        assert_doc_counts([row(number=n) for n in (1, 2, 3, 4)], META)


def test_doc_counts_refuse_empty_metadata_and_an_unknown_document():
    with pytest.raises(CrosswalkError, match="no document metadata"):
        assert_doc_counts([row()], {})
    with pytest.raises(CrosswalkError, match="unknown document"):
        assert_doc_counts([row()], {"gamma": dict(META["letf"])})


def test_doc_counts_refuse_a_row_whose_document_has_no_metadata():
    rows = [row(number=n) for n in (1, 2, 3)] + [row(doc="shock", number=1)]
    with pytest.raises(CrosswalkError, match="no metadata"):
        assert_doc_counts(rows, META)


# ============================================================ coverage arithmetic


def synthetic() -> list[CrosswalkRow]:
    """Ten rows with a hand-countable answer: letf 6, shock 4."""
    target = row(doc="shock", number=1, status="claimed", claim=a_claim())
    return [
        row(doc="letf", number=1, status="claimed", claim=a_claim(kind="function", symbol="t")),
        row(doc="letf", number=2, status="claimed", claim=a_claim(kind="banner")),
        row(doc="letf", number=3, status="declined", claim=a_claim(kind="record",
                                                                   file="docs/decisions/D1.md")),
        row(doc="letf", number=4, status="missing"),
        row(doc="letf", number=5, status="missing"),
        row(doc="letf", number=6, status="covered_via", covered_via=("shock", 1)),
        target,
        row(doc="shock", number=2, status="missing", cls="leak"),
        row(doc="shock", number=3, status="missing", cls="leak"),
        row(doc="shock", number=4, status="missing", cls="execution"),
    ]


def test_coverage_by_doc_is_hand_countable():
    cov = coverage_by_doc(synthetic())
    assert cov["letf"] == {"count": 6, "claimed": 2, "covered_via": 1, "declined": 1,
                           "missing": 2, "pct_claimed": pytest.approx(100 * 2 / 6)}
    assert cov["shock"] == {"count": 4, "claimed": 1, "covered_via": 0, "declined": 0,
                            "missing": 3, "pct_claimed": 25.0}
    assert set(cov) == {"letf", "shock"}, "a document with no rows gets no row"


def test_coverage_counts_only_claimed_in_the_percentage():
    """A covered_via or declined item is NOT folded into pct_claimed, deliberately."""
    cov = coverage_by_doc(synthetic())["letf"]
    assert cov["pct_claimed"] < 100 * (cov["claimed"] + cov["covered_via"] + cov["declined"]) / 6


def test_coverage_total_sums_the_statuses_to_the_count():
    total = coverage_total(synthetic())
    assert total["count"] == 10
    assert sum(total[s] for s in STATUSES) == total["count"]
    assert total["claimed"] == 3 and total["pct_claimed"] == 30.0


def test_coverage_total_refuses_an_empty_map():
    with pytest.raises(CrosswalkError, match="got no rows"):
        coverage_total([])


def test_claim_kind_tally_counts_only_claimed_rows_and_sums_to_them():
    """A `declined` row carries a `record` claim and must NOT be counted as a spelling."""
    kinds = claim_kind_tally(synthetic())
    assert list(kinds) == list(SCANNABLE_KINDS)
    assert kinds == {"function": 1, "banner": 1, "message": 1}
    assert sum(kinds.values()) == coverage_total(synthetic())["claimed"] == 3
    assert "record" not in kinds, "the declined row's record claim is not a spelling"


def test_claim_kind_tally_on_the_committed_map_sums_to_its_claimed_count():
    rows = load_map()
    kinds = claim_kind_tally(rows)
    assert sum(kinds.values()) == coverage_total(rows)["claimed"]
    assert kinds["function"] > kinds["message"] > kinds["banner"] > 0


def test_class_tally_covers_every_class_and_sums_to_the_row_count():
    tally = class_tally(synthetic())
    assert list(tally) == list(CLASSES)
    assert sum(tally.values()) == 10
    assert tally["leak"] == 2 and tally["execution"] == 1 and tally["arithmetic"] == 7


# ============================================================ the renderer


SYNTH_META = {
    "letf": {"file": "LETF_CLOSE_FLOW_PREREG.md", "count": 6, "heading": "## 8. Required unit tests",
             "heading_line": 242, "first_item_line": 244, "last_item_line": 249},
    "shock": {"file": "SHOCK_CLASSIFIER_PREREG.md", "count": 4, "heading": "## 9. Required unit tests",
              "heading_line": 293, "first_item_line": 295, "last_item_line": 298},
}


def test_render_validates_before_producing_a_byte():
    bad = synthetic() + [row(doc="letf", number=1)]
    with pytest.raises(CrosswalkError, match="DUPLICATE"):
        render_md(bad, docs_meta=SYNTH_META)


def test_render_refuses_a_map_whose_counts_disagree_with_the_metadata():
    with pytest.raises(CrosswalkError, match="missing"):
        render_md(synthetic()[:-1], docs_meta=SYNTH_META)


def test_render_puts_the_unclaimed_rows_paraphrase_on_the_page():
    page = render_md(synthetic(), docs_meta=SYNTH_META)
    assert "*a handle*" in page, "an unclaimed row must carry its paraphrase"
    assert "LETF_CLOSE_FLOW_PREREG.md" in page and "](" not in page.split("## The items")[1], (
        "the deposit documents are untracked and must be named, never linked"
    )


def test_render_states_the_path_translation_and_that_a_percentage_is_a_count():
    page = render_md(synthetic(), docs_meta=SYNTH_META)
    first = page.split("---")[0]
    assert "no root `results/`" in first
    assert "COUNT, not a verdict" in first


# ---------------------------------------------------- the committed page (test_programme:195)


def test_render_md_is_deterministic_and_equals_the_committed_page(tmp_path):
    rows = load_map()
    meta = load_payload()["docs"]
    a = write_md(rows, docs_meta=meta, path=tmp_path / "a.md")
    b = write_md(rows, docs_meta=meta, path=tmp_path / "b.md")
    first = a.read_bytes()
    assert first == b.read_bytes(), "the renderer is not deterministic"
    assert first == DEFAULT_PAGE_PATH.read_bytes(), (
        "docs/results/DEPOSIT_TEST_MAP.md is stale: re-render it with "
        "`uv run python scripts/deposit_test_map.py --render`"
    )


def test_the_committed_page_is_lf_only_on_every_platform():
    """D550: the author's OS is not the runner's."""
    assert b"\r" not in DEFAULT_PAGE_PATH.read_bytes()
    assert DEFAULT_PAGE_PATH.read_bytes().endswith(b"\n")


def test_the_committed_page_is_in_docs_results_and_the_deposits_results_does_not_exist():
    assert DEFAULT_PAGE_PATH.parent == REPO / "docs" / "results"
    assert not (REPO / "results").exists(), "the path translation exists because this does not"


# ============================================================ loading


def test_load_map_validates_on_the_way_in(tmp_path):
    payload = json.loads(DEFAULT_MAP_PATH.read_text(encoding="utf-8"))
    payload["entries"].append(dict(payload["entries"][0]))
    target = tmp_path / "map.json"
    with open(target, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2) + "\n")
    with pytest.raises(CrosswalkError, match="DUPLICATE"):
        load_map(target)


def test_load_payload_refuses_a_missing_file_a_bad_schema_and_a_timestamp(tmp_path):
    with pytest.raises(CrosswalkError, match="no crosswalk at"):
        load_payload(tmp_path / "absent.json")

    payload = json.loads(DEFAULT_MAP_PATH.read_text(encoding="utf-8"))

    bad = tmp_path / "schema.json"
    doctored = dict(payload, schema="deposit_test_map/0")
    with open(bad, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(doctored) + "\n")
    with pytest.raises(CrosswalkError, match="expected"):
        load_payload(bad)

    stamped = tmp_path / "stamped.json"
    with open(stamped, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(dict(payload, generated_at="2026-09-21")) + "\n")
    with pytest.raises(CrosswalkError, match="carries a timestamp"):
        load_payload(stamped)

    headless = tmp_path / "headless.json"
    trimmed = {k: v for k, v in payload.items() if k != "docs"}
    with open(headless, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(trimmed) + "\n")
    with pytest.raises(CrosswalkError, match="no 'docs' block"):
        load_payload(headless)


def test_the_committed_json_loads_and_round_trips_through_to_json():
    rows = load_map()
    payload = load_payload()
    assert payload["schema"] == SCHEMA
    assert [r.to_json() for r in rows] == payload["entries"]
    assert set(payload["docs"]) == set(DOC_KEYS)
