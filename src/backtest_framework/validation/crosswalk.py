"""The crosswalk from every numbered unit test in the deposit pre-registrations to the
repository test that claims it (D607).

WHAT THIS IS FOR. Five of the documents in `docs/internal/User-Doc-Deposit/` close with a
numbered "Required unit tests" list, and between them they name **146** tests. Five rounds
of infrastructure work (D586-D588, D592-D594) have written **28** of them. Nothing in the
repository said which 28, so the only way to find out was to read six thousand lines of
pre-registration beside three thousand lines of test and hold both in your head. The
predictable failures of that are a test written twice and a test everyone assumed someone
else had written. This module is the index that makes both visible, and the 118 unwritten
ones a LIST rather than a feeling.

THREE CONVENTIONS, AND A GREP FOR ONE MISSES HALF. The 28 existing claims are spelled
three different ways, none of them wrong and none of them searchable from the others:

    (i)   the FUNCTION NAME  -- `def test_ledger_51_design_effect_...`, `def test_ut34_...`
    (ii)  a SECTION BANNER   -- `# ===== ledger test 66` above a block of functions
    (iii) a DOCSTRING or ASSERTION MESSAGE -- a docstring reading `Ledger unit test 11
          and shock unit test 9, long side.`, or the assertion message
          `INDEX_REWEIGHT_FLOW_PREREG.md unit test 9`

Ten claims use (i), three use (ii), fifteen use (iii). `grep 'def test_ledger'` finds six
of twenty-eight. That is the defect this record fixes going forward, and the fix is stated
in D607: **a new test that discharges a numbered deposit test names the number in its
FUNCTION NAME** -- `test_<doc>_<number>_<what_it_checks>` -- because that is the one
spelling `pytest -k`, a traceback, a test-id and a plain grep all see.

THE JSON IS THE TRUTH; THE PAGE IS A RENDER. `data/deposit_test_map.json` holds the 146
rows and `docs/results/DEPOSIT_TEST_MAP.md` is rendered from it, the same split D592 made
for the programme registry. The JSON also carries each item's VERBATIM TEXT, so the page
renders in a clone that has none of the deposit documents -- they are untracked, and a
crosswalk that can only be read on the author's machine is not a crosswalk.

THE PATH TRANSLATION. The deposit documents write their own outputs under `results/`; this
repository has no root `results/` (`validation/power.py:write_power_md` declined to invent
one and D592 recorded the mapping). Rendered pages live in `docs/results/`, machine-readable
state lives in `data/`.

A COVERAGE PERCENTAGE HERE IS A COUNT AND NOT A VERDICT. "19 of 71" says nineteen numbered
items have a test that names them. It does not say the nineteen are the important ones, that
the tests are good, or that the other fifty-two are unimportant. Three of the five documents
have not begun testing at all.
"""

from __future__ import annotations

import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_REPO = Path(__file__).resolve().parents[3]

#: `data/deposit_test_map.json` -- the machine-readable truth.
DEFAULT_MAP_PATH = _REPO / "data" / "deposit_test_map.json"
#: `docs/results/DEPOSIT_TEST_MAP.md` -- the rendered page.
DEFAULT_PAGE_PATH = _REPO / "docs" / "results" / "DEPOSIT_TEST_MAP.md"

#: The schema string `data/deposit_test_map.json` must carry.
SCHEMA = "deposit_test_map/1"

#: The five documents, in the order the page lists them (descending by test count).
DOC_KEYS = ("ledger", "index", "opening", "shock", "letf")

#: The six classes an item may carry. Assigned from the item's own text (D607):
#:
#:   leak        a look-ahead, point-in-time, publication-time or known-at guard
#:   data_guard  a bad, absent, unmapped or stale input is refused, excluded or flagged
#:   arithmetic  a closed-form or hand-calculated numeric identity, or a sign
#:   statistical power, SE, MDE, significance, calibration, DSR, haircut, episode checks
#:   execution   fills, entries, exits, cooldowns, session windows, rolls, DST mapping
#:   rendering   a produced artefact -- a file, a hash, a table -- is written or validated
CLASSES = ("arithmetic", "data_guard", "execution", "leak", "rendering", "statistical")

#: The four statuses. `missing` is the default and covers 109 of the 146.
STATUSES = ("claimed", "covered_via", "declined", "missing")

#: The four claim kinds. The first three are spellings inside a test file; `record` is a
#: decision record that DECLINED the item, which is evidence of a different sort.
CLAIM_KINDS = ("function", "banner", "message", "record")

#: Which claim kinds a scan of `tests/` can see. `record` lives in `docs/decisions/`.
SCANNABLE_KINDS = ("function", "banner", "message")

#: A paraphrase is a one-line handle for a future agent picking an item up. Fifteen words
#: is the ceiling because the verbatim text is one column to its left on the page.
MAX_PARAPHRASE_WORDS = 15


class CrosswalkError(ValueError):
    """Raised by `validate_crosswalk` and `load_map`. A subclass of ValueError so a caller
    that catches ValueError (the house convention in `validation/`) still catches it."""


@dataclass(frozen=True)
class Claim:
    """Where a numbered deposit test is claimed.

    `line` is 1-based and points at the LINE THAT CARRIES THE NUMBER -- the `def` for a
    `function` claim, the banner comment for a `banner` claim, the docstring or assertion
    message line for a `message` claim. It is deliberately not the line of the first
    assertion: the scan can only verify what it can read.
    """

    kind: str
    file: str
    line: int
    symbol: str | None = None

    def as_page_cell(self) -> str:
        """`file:line symbol`, the spelling the page uses."""
        base = f"`{self.file}:{self.line}`"
        return f"{base} `{self.symbol}`" if self.symbol else base

    def to_json(self) -> dict[str, Any]:
        return {"kind": self.kind, "file": self.file, "line": self.line, "symbol": self.symbol}


@dataclass(frozen=True)
class CrosswalkRow:
    """One numbered unit test in one deposit document.

    `status`, `claim` and `covered_via` are consistent by construction only after
    `validate_crosswalk` has run -- the fields are Optional so that an inconsistent row can
    be CONSTRUCTED and then caught, which is `validation/power.py:PowerRow`'s bargain and
    for the same reason: a builder that cannot express the error cannot be tested against it.
    """

    doc: str
    number: int
    line: int
    text: str
    paraphrase: str
    cls: str
    status: str
    claim: Claim | None = None
    covered_via: tuple[str, int] | None = None
    note: str = ""

    @property
    def key(self) -> tuple[str, int]:
        return (self.doc, self.number)

    @property
    def is_claimed(self) -> bool:
        return self.status == "claimed"

    def to_json(self) -> dict[str, Any]:
        return {
            "doc": self.doc,
            "number": self.number,
            "line": self.line,
            "text": self.text,
            "paraphrase": self.paraphrase,
            "cls": self.cls,
            "status": self.status,
            "claim": self.claim.to_json() if self.claim else None,
            "covered_via": (
                {"doc": self.covered_via[0], "number": self.covered_via[1]}
                if self.covered_via
                else None
            ),
            "note": self.note,
        }


_CROSSWALK_REQUIRED = (
    # Cause before symptom, as `power.py:_TRACK_MAP_REQUIRED` does it: a row with no `doc`
    # has no identity at all, so naming a missing class first would report the symptom.
    ("doc", "a document key"),
    ("number", "a test number"),
    ("line", "the line in that document"),
    ("text", "the item's verbatim text"),
    ("paraphrase", "a paraphrase, so an unclaimed item can be picked up"),
    ("cls", "a class"),
    ("status", "a status"),
)


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, bool):
        return False
    if isinstance(value, float):
        return not math.isfinite(value)
    return False


def validate_crosswalk(rows: Sequence[CrosswalkRow]) -> None:
    """Raise `CrosswalkError` naming the FIRST offending row. Return None on a clean map.

    Eight things are checked, and every one of them has been a real way to get this wrong:

      1. an empty map -- nothing to gate, and a scan over nothing passes silently;
      2. a required field missing (None, blank, or non-finite);
      3. an unknown `doc`, `cls` or `status`;
      4. a duplicate `(doc, number)`;
      5. a status that disagrees with its claim -- `claimed` without a claim, `missing`
         WITH one, `covered_via` without a target, `declined` whose claim is not a `record`;
      6. a `function` claim with no symbol, or a non-positive claim line;
      7. a `covered_via` pointing somewhere that is not a `claimed` row of this map;
      8. a paraphrase over `MAX_PARAPHRASE_WORDS`.
    """
    if len(rows) == 0:
        raise CrosswalkError(
            "validate_crosswalk got no rows: an empty crosswalk has nothing to gate, and "
            "a coverage percentage over zero items reads as complete"
        )

    claimed: set[tuple[str, int]] = {r.key for r in rows if r.status == "claimed"}
    seen: set[tuple[str, int]] = set()

    for index, row in enumerate(rows):
        where = f"crosswalk row {index} (doc={row.doc!r}, number={row.number!r})"

        for field, description in _CROSSWALK_REQUIRED:
            value = getattr(row, field, None)
            if _is_missing(value):
                raise CrosswalkError(f"{where} is missing {description}: {field}={value!r}")

        if row.doc not in DOC_KEYS:
            raise CrosswalkError(f"{where} names an unknown document: {row.doc!r} not in {DOC_KEYS}")
        if row.cls not in CLASSES:
            raise CrosswalkError(f"{where} carries an unknown class: {row.cls!r} not in {CLASSES}")
        if row.status not in STATUSES:
            raise CrosswalkError(
                f"{where} carries an unknown status: {row.status!r} not in {STATUSES}"
            )
        if not isinstance(row.number, int) or row.number < 1:
            raise CrosswalkError(f"{where} has a non-positive test number: {row.number!r}")
        if row.key in seen:
            raise CrosswalkError(
                f"{where} is a DUPLICATE: ({row.doc}, {row.number}) appears twice. A number "
                "claimed twice is how one test gets written by two agents."
            )
        seen.add(row.key)

        claim = row.claim
        if claim is not None:
            if claim.kind not in CLAIM_KINDS:
                raise CrosswalkError(
                    f"{where} has a claim of unknown kind {claim.kind!r} not in {CLAIM_KINDS}"
                )
            if _is_missing(claim.file):
                raise CrosswalkError(f"{where} has a claim with no file: {claim!r}")
            if not isinstance(claim.line, int) or claim.line < 1:
                raise CrosswalkError(f"{where} has a claim with a non-positive line: {claim!r}")
            if claim.kind == "function" and _is_missing(claim.symbol):
                raise CrosswalkError(
                    f"{where} has a `function` claim with no symbol: the symbol IS the "
                    "claim for that convention, and nothing can verify the file without it"
                )

        if row.status == "claimed":
            if claim is None:
                raise CrosswalkError(f"{where} is `claimed` with no claim: say where, or say missing")
            if claim.kind not in SCANNABLE_KINDS:
                raise CrosswalkError(
                    f"{where} is `claimed` by a {claim.kind!r} claim; only {SCANNABLE_KINDS} "
                    "live in a test file and a claim outside `tests/` is not a test"
                )
            if row.covered_via is not None:
                raise CrosswalkError(f"{where} is `claimed` AND `covered_via`: it cannot be both")
        elif row.status == "declined":
            if claim is None or claim.kind != "record":
                raise CrosswalkError(
                    f"{where} is `declined` without a `record` claim: a decline is only a "
                    "decline when a written record says so and this row points at it"
                )
        elif row.status == "covered_via":
            if row.covered_via is None:
                raise CrosswalkError(f"{where} is `covered_via` with no target")
            if claim is not None:
                raise CrosswalkError(
                    f"{where} is `covered_via` and also carries its own claim: the claim "
                    "belongs on the target row"
                )
            if row.covered_via == row.key:
                raise CrosswalkError(f"{where} is covered via itself")
            if row.covered_via not in claimed:
                raise CrosswalkError(
                    f"{where} is covered via {row.covered_via}, which is not a `claimed` row "
                    "of this map. Covering an item with an item nobody wrote covers nothing."
                )
        else:  # missing
            if claim is not None:
                raise CrosswalkError(
                    f"{where} is `missing` but carries a claim at {claim.file}:{claim.line}: "
                    "an item with a claim is `claimed` or `declined`, never `missing`"
                )
            if row.covered_via is not None:
                raise CrosswalkError(f"{where} is `missing` but carries a covered_via target")

        words = len(row.paraphrase.split())
        if words > MAX_PARAPHRASE_WORDS:
            raise CrosswalkError(
                f"{where} has a {words}-word paraphrase against a ceiling of "
                f"{MAX_PARAPHRASE_WORDS}: {row.paraphrase!r}. The verbatim text is the long "
                "form; the paraphrase is the handle."
            )


def assert_doc_counts(rows: Sequence[CrosswalkRow], docs_meta: dict[str, dict[str, Any]]) -> None:
    """Every document's rows are exactly 1..count, and every `doc` key has metadata.

    Separate from `validate_crosswalk` because it needs the `docs` block, and a caller
    holding rows alone (a synthetic map in a test) should still be able to validate them.
    """
    if not docs_meta:
        raise CrosswalkError("assert_doc_counts got no document metadata")
    for doc, meta in docs_meta.items():
        if doc not in DOC_KEYS:
            raise CrosswalkError(f"docs metadata names an unknown document: {doc!r}")
        numbers = sorted(r.number for r in rows if r.doc == doc)
        expected = list(range(1, int(meta["count"]) + 1))
        if numbers != expected:
            missing = sorted(set(expected) - set(numbers))
            extra = sorted(set(numbers) - set(expected))
            raise CrosswalkError(
                f"{meta['file']} declares {meta['count']} tests and the map holds "
                f"{len(numbers)} for {doc!r}: missing {missing}, extra {extra}"
            )
    unknown = sorted({r.doc for r in rows} - set(docs_meta))
    if unknown:
        raise CrosswalkError(f"rows name documents with no metadata: {unknown}")


def _row_from_json(payload: dict[str, Any]) -> CrosswalkRow:
    raw_claim = payload.get("claim")
    claim = (
        Claim(
            kind=raw_claim["kind"],
            file=raw_claim["file"],
            line=raw_claim["line"],
            symbol=raw_claim.get("symbol"),
        )
        if raw_claim
        else None
    )
    raw_via = payload.get("covered_via")
    via = (raw_via["doc"], raw_via["number"]) if raw_via else None
    return CrosswalkRow(
        doc=payload["doc"],
        number=payload["number"],
        line=payload["line"],
        text=payload["text"],
        paraphrase=payload["paraphrase"],
        cls=payload["cls"],
        status=payload["status"],
        claim=claim,
        covered_via=via,
        note=payload.get("note", ""),
    )


def load_payload(path: str | Path = DEFAULT_MAP_PATH) -> dict[str, Any]:
    """The whole JSON document, schema-checked. Raises `CrosswalkError` on a bad schema."""
    path = Path(path)
    if not path.exists():
        raise CrosswalkError(f"no crosswalk at {path}")
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    schema = payload.get("schema")
    if schema != SCHEMA:
        raise CrosswalkError(f"{path} carries schema {schema!r}, expected {SCHEMA!r}")
    for key in ("docs", "entries"):
        if key not in payload:
            raise CrosswalkError(f"{path} has no {key!r} block")
    if "generated_at" in payload or "timestamp" in payload:
        raise CrosswalkError(
            f"{path} carries a timestamp. This file's bytes are compared between runs; a "
            "clock in it makes every render a diff."
        )
    return payload


def load_map(path: str | Path = DEFAULT_MAP_PATH) -> list[CrosswalkRow]:
    """Load, validate and return the rows. Validation is not optional on the way in."""
    payload = load_payload(path)
    rows = [_row_from_json(entry) for entry in payload["entries"]]
    validate_crosswalk(rows)
    assert_doc_counts(rows, payload["docs"])
    return rows


def coverage_by_doc(rows: Sequence[CrosswalkRow]) -> dict[str, dict[str, float]]:
    """Per document: count, claimed, covered_via, declined, missing, pct_claimed.

    `pct_claimed` counts ONLY `claimed`. A `covered_via` item is discharged by another
    document's test and a `declined` one was refused on the record, and folding either into
    the percentage would make the number say something it does not mean. Both are reported
    in their own columns so a reader can add them up on their own terms.
    """
    out: dict[str, dict[str, float]] = {}
    for doc in DOC_KEYS:
        subset = [r for r in rows if r.doc == doc]
        if not subset:
            continue
        count = len(subset)
        tallies = {status: sum(1 for r in subset if r.status == status) for status in STATUSES}
        out[doc] = {
            "count": count,
            "claimed": tallies["claimed"],
            "covered_via": tallies["covered_via"],
            "declined": tallies["declined"],
            "missing": tallies["missing"],
            "pct_claimed": 100.0 * tallies["claimed"] / count,
        }
    return out


def coverage_total(rows: Sequence[CrosswalkRow]) -> dict[str, float]:
    """The same six numbers over every document at once."""
    count = len(rows)
    if count == 0:
        raise CrosswalkError("coverage_total got no rows")
    tallies = {status: sum(1 for r in rows if r.status == status) for status in STATUSES}
    return {
        "count": count,
        "claimed": tallies["claimed"],
        "covered_via": tallies["covered_via"],
        "declined": tallies["declined"],
        "missing": tallies["missing"],
        "pct_claimed": 100.0 * tallies["claimed"] / count,
    }


def class_tally(rows: Sequence[CrosswalkRow]) -> dict[str, int]:
    """Items per class, in `CLASSES` order. Sums to `len(rows)` by construction."""
    return {cls: sum(1 for r in rows if r.cls == cls) for cls in CLASSES}


def claim_kind_tally(rows: Sequence[CrosswalkRow]) -> dict[str, int]:
    """How the `claimed` rows spell their number, in `SCANNABLE_KINDS` order.

    Rendered on the page rather than written into its prose, because "ten of twenty-eight use
    the function name" was true for one round and the sentence outlives the round.
    """
    claimed = [r for r in rows if r.status == "claimed" and r.claim is not None]
    return {
        kind: sum(1 for r in claimed if r.claim is not None and r.claim.kind == kind)
        for kind in SCANNABLE_KINDS
    }


_STATUS_LABEL = {
    "claimed": "claimed",
    "covered_via": "covered via",
    "declined": "declined",
    "missing": "**unclaimed**",
}

_DOC_TITLE = {
    "ledger": "Settlement flow ledger",
    "index": "Index reweight flow",
    "opening": "Opening agent state",
    "shock": "Shock classifier",
    "letf": "LETF close flow",
}


def _escape(text: str) -> str:
    """Make a verbatim item safe inside a Markdown table cell."""
    return text.replace("|", "\\|")


def render_md(rows: Sequence[CrosswalkRow], *, docs_meta: dict[str, dict[str, Any]]) -> str:
    """The page, as a string. Deterministic: no clock, no environment, no sorting by hash.

    The deposit documents are UNTRACKED, so the page names each of them by file name in
    prose and never links to one: `scripts/check_doc_links.py` resolves a relative link
    against `git ls-files`, and a link to an untracked file is a dead link for every reader
    who is not the author.
    """
    validate_crosswalk(rows)
    assert_doc_counts(rows, docs_meta)

    per_doc = coverage_by_doc(rows)
    total = coverage_total(rows)
    classes = class_tally(rows)
    kinds = claim_kind_tally(rows)
    # Largest document first; ties broken by DOC_KEYS order so the page never reorders
    # itself between renders. Only documents the map actually holds.
    ordered = sorted(per_doc, key=lambda d: (-int(per_doc[d]["count"]), DOC_KEYS.index(d)))

    lines: list[str] = [
        "# DEPOSIT TEST MAP",
        "",
        "**Rendered from [`data/deposit_test_map.json`](../../data/deposit_test_map.json) by "
        "`backtest_framework.validation.crosswalk` (D607).** The JSON is the truth; this page "
        "is a render and editing it by hand is a change that the next render throws away.",
        "",
        "Five of the pre-registration documents deposited in `docs/internal/User-Doc-Deposit/` "
        "close with a numbered **Required unit tests** list: "
        "`SETTLEMENT_FLOW_LEDGER_PREREG.md`, `INDEX_REWEIGHT_FLOW_PREREG.md`, "
        "`OPENING_AGENT_STATE_PREREG.md`, `SHOCK_CLASSIFIER_PREREG.md` and "
        "`LETF_CLOSE_FLOW_PREREG.md`. Those documents are **untracked**, so they are named "
        "here in prose and never linked: a relative link to a file that is not in "
        "`git ls-files` is a dead link for every reader who is not the author, which is what "
        "`scripts/check_doc_links.py` exists to say. `ARCHITECTURE_OVERVIEW.md` has no "
        "numbered list -- its section 9 is a power-class table -- and is not on this page.",
        "",
        "**The path translation.** The deposit writes its own outputs under `results/`. This "
        "repository has no root `results/`: rendered pages live in `docs/results/` and "
        "machine-readable state lives in `data/`, the mapping D592 recorded for the programme "
        "registry and `validation/power.py` declined to invent.",
        "",
        "**A percentage below is a COUNT, not a verdict.** \"claimed\" means one repository "
        "test names that number in its function name, a section banner, or a docstring or "
        "assertion message. It does not say the test is right, that the claimed items are the "
        "important ones, or that the unclaimed ones are not. Nothing here has been run against "
        "a market.",
        "",
        "**The three spellings, and why a grep misses half.** A claim is made in one of three "
        "conventions -- a function name (`def test_ledger_51_...`), a section banner "
        "(`# ===== ledger test 66`), or a docstring or assertion message (`Ledger unit test 11 "
        "and shock unit test 9, long side.`). Of the "
        f"{int(total['claimed'])} claims here, **{kinds['function']} use the function name, "
        f"{kinds['message']} a docstring or message and {kinds['banner']} a banner**; at the 28 "
        "claims D607 opened with, `grep 'def test_ledger'` found six. **Going forward (D607): "
        "a test that discharges a numbered deposit item names the number in its FUNCTION "
        "NAME** -- `test_<doc>_<number>_<what>` -- because that is the spelling `pytest -k`, a "
        "traceback, a test id and a grep all see. The other two conventions stay valid for the "
        "tests that already use them, `scripts/deposit_test_map.py --scan` reads all three, "
        "and one function name can only carry ONE number -- an item discharged by a test named "
        "for a different document still needs the docstring spelling.",
        "",
        "---",
        "",
        "## Coverage",
        "",
        "| Document | Section | Tests | Claimed | Covered via | Declined | Unclaimed | % claimed |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for doc in ordered:
        meta = docs_meta[doc]
        cov = per_doc[doc]
        lines.append(
            f"| {_DOC_TITLE[doc]} (`{meta['file']}`) | {meta['heading'].lstrip('# ')} "
            f"(line {meta['heading_line']}) | {int(cov['count'])} | {int(cov['claimed'])} | "
            f"{int(cov['covered_via'])} | {int(cov['declined'])} | {int(cov['missing'])} | "
            f"{cov['pct_claimed']:.1f}% |"
        )
    lines.append(
        f"| **All five** | | **{int(total['count'])}** | **{int(total['claimed'])}** | "
        f"**{int(total['covered_via'])}** | **{int(total['declined'])}** | "
        f"**{int(total['missing'])}** | **{total['pct_claimed']:.1f}%** |"
    )
    lines += [
        "",
        "**By class**, over all "
        f"{int(total['count'])} items: "
        + ", ".join(f"{cls} {classes[cls]}" for cls in CLASSES)
        + ".",
        "",
        "---",
        "",
        "## The items",
        "",
        "One table per document, every numbered item in the document's own order. The "
        "**Claim** column is `file:line` and, where the convention supplies one, the symbol; "
        "the line is the one that CARRIES THE NUMBER, which for a banner or a docstring is "
        "not the line of the first assertion. An unclaimed row carries its paraphrase so a "
        "future agent can pick it up without opening the deposit.",
        "",
    ]
    for doc in ordered:
        meta = docs_meta[doc]
        cov = per_doc[doc]
        lines += [
            f"### {_DOC_TITLE[doc]} — `{meta['file']}`",
            "",
            # "Section 12. Required..." and never "12. Required...": a paragraph that starts
            # with a digit and a dot renders as an ordered list numbered from that digit.
            f"Section {meta['heading'].lstrip('# ')}, heading at line {meta['heading_line']}, "
            f"items at lines {meta['first_item_line']}–{meta['last_item_line']}. "
            f"**{int(cov['claimed'])} of {int(cov['count'])} claimed "
            f"({cov['pct_claimed']:.1f}%).**",
            "",
            "| # | Line | Class | Status | Claim | Item |",
            "|---:|---:|---|---|---|---|",
        ]
        for row in sorted((r for r in rows if r.doc == doc), key=lambda r: r.number):
            if row.claim is not None:
                claim_cell = row.claim.as_page_cell()
            elif row.covered_via is not None:
                claim_cell = f"→ {_DOC_TITLE[row.covered_via[0]]} {row.covered_via[1]}"
            else:
                claim_cell = "—"
            item = _escape(row.text)
            if row.status != "claimed":
                item = f"{item}<br>*{_escape(row.paraphrase)}*"
            if row.note:
                item = f"{item}<br>**Note:** {_escape(row.note)}"
            lines.append(
                f"| {row.number} | {row.line} | {row.cls} | {_STATUS_LABEL[row.status]} | "
                f"{claim_cell} | {item} |"
            )
        lines.append("")

    lines += [
        "---",
        "",
        "## What a future agent does",
        "",
        "1. Pick an **unclaimed** row above. Its paraphrase is the handle and its verbatim "
        "text is the specification; the deposit document is not needed to read either.",
        "2. Write the test with the number in the function name: "
        "`test_ledger_29_restrike_triggers_at_the_threshold`.",
        "3. Add the row's claim to `data/deposit_test_map.json` and re-render this page with "
        "`uv run python scripts/deposit_test_map.py --render`.",
        "4. `uv run python scripts/deposit_test_map.py --scan` must report zero disagreements, "
        "and `--check` must find the claim as a collected pytest node.",
        "",
        "A claim that is not in the JSON is invisible to everyone but its author, which is the "
        "state this page was written to end.",
        "",
    ]
    return "\n".join(lines)


def write_md(
    rows: Sequence[CrosswalkRow],
    *,
    docs_meta: dict[str, dict[str, Any]],
    path: str | Path = DEFAULT_PAGE_PATH,
) -> Path:
    """Render and write the page. Newline pinned to `\\n` (D550) on every platform."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_md(rows, docs_meta=docs_meta))
    return path
