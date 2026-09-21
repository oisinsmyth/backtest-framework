"""Verify, scan, render and self-test the deposit test crosswalk (D607).

    uv run python scripts/deposit_test_map.py --scan      # the tripwire
    uv run python scripts/deposit_test_map.py --render    # write docs/results/DEPOSIT_TEST_MAP.md
    uv run python scripts/deposit_test_map.py --check     # pytest --collect-only on the claims
    uv run python scripts/deposit_test_map.py --selftest  # prove every guard raises

`data/deposit_test_map.json` is the truth and **nothing here ever rewrites it**. `--scan`
reads the five deposit documents and every tracked `tests/**/test_*.py` and REPORTS the
differences; a human decides what the JSON should say. That asymmetry is the point: a
scanner that repairs the file it is checking cannot fail.

THE SCAN IS A TRIPWIRE, NOT A PROOF, and the limits are worth stating because D593 had to
state the same ones about its AST scan. It reads three textual conventions (see
`validation/crosswalk.py`). It cannot see a test that discharges a numbered item without
naming it, it cannot see whether a test that names a number actually checks that number's
claim, and where a docstring names two documents and one number it cannot decide which
document owns it -- `tests/golden/test_episodes_ledger.py:4` is exactly that case, and the
scan resolves it by accepting ANY candidate document the JSON records. The JSON is the
judgement; the scan is the alarm that the judgement has gone stale.

DOC SECTIONS. `--scan` first re-parses each document's "Required unit tests" section and
refuses if the heading line, the item lines, the count or any item's text differs from the
JSON, printing the difference. When the documents are absent -- they are untracked, so a
clone has none of them -- that half is skipped and said so; the JSON carries every item's
verbatim text precisely so the rest still works.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "src") not in sys.path:
    sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.crosswalk import (  # noqa: E402
    DEFAULT_MAP_PATH,
    DEFAULT_PAGE_PATH,
    DOC_KEYS,
    CrosswalkError,
    CrosswalkRow,
    assert_doc_counts,
    class_tally,
    coverage_by_doc,
    coverage_total,
    load_map,
    load_payload,
    validate_crosswalk,
    write_md,
)

DEPOSIT_DIR = REPO / "docs" / "internal" / "User-Doc-Deposit"

# --------------------------------------------------------------------------- the regexes

#: Convention (i). `ut` is the ledger's numbering as `tests/unit/test_frozen.py` spells it
#: ("unit test 34"), which is why it maps to `ledger` rather than to a document of its own.
FUNCTION_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+(test_(ledger|ut|index|opening|shock|letf)_?(\d+)\w*)\s*\("
)
FUNCTION_DOC = {
    "ledger": "ledger",
    "ut": "ledger",
    "index": "index",
    "opening": "opening",
    "shock": "shock",
    "letf": "letf",
}

#: Conventions (ii) and (iii): "...unit test 9", "...required unit test 10", "...test 51",
#: "...unit tests 64 / 65", "...unit tests 2 and 19".
#: The trailing `(?!\w)` is what stops a SECTION number being read as a TEST number: without
#: it `\d+` backtracks, and "§13A.8" yields a claim on 1 after "13" is rejected.
NUMBERS_RE = re.compile(
    r"(?:required\s+)?(?:unit\s+|doc\s+)?tests?\s+(\d+(?:\s*(?:[,/&]|and)\s*\d+)*)(?!\w)",
    re.IGNORECASE,
)

#: The parenthetical continuation. `# ---- ledger unit tests 64 / 65 (and opening 18 / 20)`
#: names two opening numbers with no second "test" for `NUMBERS_RE` to anchor on. Applied
#: ONLY to the remainder of a line that already matched `NUMBERS_RE`, because `index 3` in a
#: comment about array indices is otherwise a false claim waiting to happen.
TRAILING_RE = re.compile(
    r"\b(ledger|index|opening|shock|letf)\b\s*(\d+(?:\s*(?:[,/&]|and)\s*\d+)*)(?!\w)",
    re.IGNORECASE,
)

#: A document keyword. Both spellings: the short name used in prose and the file name.
KEYWORD_RE = re.compile(
    r"\b(ledger|index|opening|shock|letf)\b"
    r"|(SETTLEMENT_FLOW_LEDGER_PREREG|INDEX_REWEIGHT_FLOW_PREREG|OPENING_AGENT_STATE_PREREG"
    r"|SHOCK_CLASSIFIER_PREREG|LETF_CLOSE_FLOW_PREREG)",
    re.IGNORECASE,
)
FILENAME_DOC = {
    "settlement_flow_ledger_prereg": "ledger",
    "index_reweight_flow_prereg": "index",
    "opening_agent_state_prereg": "opening",
    "shock_classifier_prereg": "shock",
    "letf_close_flow_prereg": "letf",
}

#: How many lines back a number may look for the document that owns it. Four, because
#: `tests/golden/test_episodes_ledger.py` puts the file names on lines 3 and the number on
#: line 4, and because a wider window turns an unrelated module docstring into a claim.
LOOKBACK = 4

ITEM_RE = re.compile(r"^(\d+)\.\s+(.*)$")


# --------------------------------------------------------------------------- the scan


@dataclass(frozen=True)
class ScannedClaim:
    """One number found in one test file, with every document it could belong to."""

    file: str
    line: int
    number: int
    kind: str
    candidates: tuple[str, ...]
    symbol: str | None
    evidence: str

    def describe(self) -> str:
        sym = f" {self.symbol}" if self.symbol else ""
        return (
            f"{self.file}:{self.line}{sym} [{self.kind}] "
            f"{'/'.join(self.candidates)} {self.number}: {self.evidence.strip()[:100]}"
        )


@dataclass
class ScanReport:
    scanned_files: int = 0
    found: list[ScannedClaim] = field(default_factory=list)
    unrecorded: list[str] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    line_drift: list[str] = field(default_factory=list)
    out_of_range: list[str] = field(default_factory=list)
    doc_diffs: list[str] = field(default_factory=list)
    untracked: list[str] = field(default_factory=list)
    docs_read: bool = False

    @property
    def disagreements(self) -> list[str]:
        """Every difference between the INDEXED tree and the JSON, in report order.

        `untracked` is deliberately NOT here. A file that is not in `git ls-files` is not in
        a clone, so folding it in would make the gate depend on whatever a worktree happens
        to hold -- the exact failure `tests/unit/test_encoding_is_declared.py` records for a
        ceiling measured off the disk. It is reported, loudly, and it becomes a disagreement
        the moment the file is staged.
        """
        return self.doc_diffs + self.unverified + self.line_drift + self.unrecorded

    def render(self) -> str:
        out = [
            f"scanned {self.scanned_files} tracked test files; "
            f"{len(self.found)} numbered claim site(s) found",
            (
                "deposit documents re-parsed against the JSON"
                if self.docs_read
                else "deposit documents ABSENT from disk (they are untracked) - section "
                "parse SKIPPED; the JSON's verbatim item text stands unchecked"
            ),
        ]
        for title, rows in (
            ("SECTION DIFFERENCES (document vs JSON)", self.doc_diffs),
            ("JSON CLAIMS THE TREE DOES NOT CARRY", self.unverified),
            ("CLAIM LINES THAT MOVED", self.line_drift),
            ("CLAIM SITES THE JSON DOES NOT RECORD", self.unrecorded),
            ("NUMBERS OUTSIDE ANY DOCUMENT'S RANGE (ignored)", self.out_of_range),
            (
                "CLAIM SITES IN UNTRACKED TEST FILES (not a disagreement until staged)",
                self.untracked,
            ),
        ):
            if rows:
                out.append("")
                out.append(f"{title} - {len(rows)}:")
                out.extend(f"  {row}" for row in rows)
        if not self.disagreements:
            out.append("")
            out.append("NO DISAGREEMENTS.")
        return "\n".join(out)


def _git_paths(*args: str) -> list[str]:
    result = subprocess.run(
        ["git", *args], cwd=REPO, capture_output=True, text=True, check=True
    )
    return sorted(p.strip() for p in result.stdout.split("\n") if p.strip())


def tracked_test_files() -> list[str]:
    return _git_paths("ls-files", "tests/**/test_*.py")


def untracked_test_files() -> list[str]:
    """Test files in the worktree that the index does not hold.

    A parallel agent's new test is here until someone stages it, and a scan that reads only
    the index cannot see it. Reported separately rather than ignored.
    """
    return _git_paths("ls-files", "--others", "--exclude-standard", "tests/**/test_*.py")


def _docs_in_window(lines: list[str], index: int, upto: int) -> tuple[str, ...]:
    """Every document keyword in `lines[index][:upto]` and the `LOOKBACK` lines before it.

    Ordered nearest-first, deduplicated. Nearest-first is not used to DECIDE anything -- the
    JSON decides -- but it makes the report readable when a site names two documents.
    """
    found: list[str] = []
    for offset in range(0, LOOKBACK + 1):
        row = index - offset
        if row < 0:
            break
        text = lines[row][:upto] if offset == 0 else lines[row]
        hits = [m for m in KEYWORD_RE.finditer(text)]
        for match in reversed(hits):
            short, filename = match.group(1), match.group(2)
            doc = (
                FILENAME_DOC[filename.lower()] if filename else short.lower()
            )
            if doc in DOC_KEYS and doc not in found:
                found.append(doc)
    return tuple(found)


def _numbers(blob: str) -> list[int]:
    return [int(n) for n in re.findall(r"\d+", blob)]


def scan_file(path: str, text: str, counts: dict[str, int]) -> tuple[list[ScannedClaim], list[str]]:
    """Every numbered claim site in one test file, plus out-of-range numbers seen."""
    lines = text.split("\n")
    claims: list[ScannedClaim] = []
    out_of_range: list[str] = []

    def emit(line_no: int, number: int, kind: str, cands: tuple[str, ...], sym: str | None,
             evidence: str) -> None:
        keep = tuple(d for d in cands if 1 <= number <= counts[d])
        if not keep:
            if cands:
                out_of_range.append(
                    f"{path}:{line_no} {'/'.join(cands)} {number} (no document has that number)"
                )
            return
        claims.append(ScannedClaim(path, line_no, number, kind, keep, sym, evidence))

    for index, raw in enumerate(lines):
        line_no = index + 1

        match = FUNCTION_RE.match(raw)
        if match:
            symbol, token, digits = match.group(1), match.group(2), match.group(3)
            emit(line_no, int(digits), "function", (FUNCTION_DOC[token.lower()],), symbol, raw)
            continue

        for number_match in NUMBERS_RE.finditer(raw):
            cands = _docs_in_window(lines, index, number_match.start())
            if not cands:
                continue
            kind = "banner" if raw.lstrip().startswith("#") else "message"
            for number in _numbers(number_match.group(1)):
                emit(line_no, number, kind, cands, None, raw)
            tail = raw[number_match.end():]
            for trailing in TRAILING_RE.finditer(tail):
                doc = trailing.group(1).lower()
                for number in _numbers(trailing.group(2)):
                    emit(line_no, number, kind, (doc,), None, raw)

    return claims, out_of_range


def parse_document_section(
    doc: str, meta: dict[str, Any], rows: Sequence[CrosswalkRow]
) -> list[str]:
    """Re-parse one deposit document's section; return its differences against the map.

    `rows` is the whole map, not this document's slice, so a row filed under the wrong `doc`
    is reported as a missing entry rather than silently matching.
    """
    by_key = {row.key: row for row in rows}
    path = DEPOSIT_DIR / meta["file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    diffs: list[str] = []

    heading_line = int(meta["heading_line"])
    actual_heading = lines[heading_line - 1] if heading_line <= len(lines) else "<past EOF>"
    if actual_heading.strip() != str(meta["heading"]).strip():
        where = [i + 1 for i, row in enumerate(lines) if row.strip() == str(meta["heading"]).strip()]
        diffs.append(
            f"{meta['file']}: JSON says the heading {meta['heading']!r} is at line "
            f"{heading_line}; that line reads {actual_heading!r}"
            + (f" and the heading is at {where}" if where else " and the heading is nowhere")
        )

    items: dict[int, tuple[int, str]] = {}
    for line_no in range(int(meta["first_item_line"]), int(meta["last_item_line"]) + 1):
        raw = lines[line_no - 1] if line_no <= len(lines) else ""
        item = ITEM_RE.match(raw)
        if not item:
            diffs.append(f"{meta['file']}:{line_no} is not a numbered item: {raw!r}")
            continue
        items[int(item.group(1))] = (line_no, item.group(2).rstrip())

    expected = list(range(1, int(meta["count"]) + 1))
    if sorted(items) != expected:
        diffs.append(
            f"{meta['file']}: the section holds {sorted(items)} against the JSON's "
            f"count of {meta['count']}"
        )
    return diffs + _item_text_diffs(doc, meta, items, by_key)


def _item_text_diffs(
    doc: str,
    meta: dict[str, Any],
    items: dict[int, tuple[int, str]],
    by_key: dict[tuple[str, int], CrosswalkRow],
) -> list[str]:
    diffs: list[str] = []
    for number, (line_no, text) in sorted(items.items()):
        row = by_key.get((doc, number))
        if row is None:
            diffs.append(f"{meta['file']}:{line_no} item {number} has no JSON entry")
            continue
        if row.line != line_no:
            diffs.append(
                f"{meta['file']} item {number}: JSON line {row.line}, document line {line_no}"
            )
        if row.text != text:
            diffs.append(
                f"{meta['file']} item {number} TEXT differs:\n"
                f"      JSON: {row.text!r}\n      doc : {text!r}"
            )
    return diffs


def scan(rows: Sequence[CrosswalkRow], payload: dict[str, Any]) -> ScanReport:
    """Compare the tree and the deposit documents against the JSON. Never writes."""
    report = ScanReport()
    counts = {doc: int(meta["count"]) for doc, meta in payload["docs"].items()}

    if DEPOSIT_DIR.is_dir():
        present = [d for d in DOC_KEYS if (DEPOSIT_DIR / payload["docs"][d]["file"]).exists()]
        if len(present) == len(DOC_KEYS):
            report.docs_read = True
            for doc in DOC_KEYS:
                report.doc_diffs.extend(
                    parse_document_section(doc, payload["docs"][doc], rows)
                )

    claimed_keys = {row.key for row in rows if row.status == "claimed"}
    by_site: dict[tuple[str, int], list[CrosswalkRow]] = defaultdict(list)
    for row in rows:
        if row.claim is not None and row.claim.kind != "record":
            by_site[(row.claim.file, row.claim.line)].append(row)

    for path in tracked_test_files():
        disk = REPO / path
        if not disk.exists():
            continue
        report.scanned_files += 1
        found, bad = scan_file(path, disk.read_text(encoding="utf-8"), counts)
        report.found.extend(found)
        report.out_of_range.extend(bad)

    for path in untracked_test_files():
        disk = REPO / path
        if not disk.exists():
            continue
        found, _ = scan_file(path, disk.read_text(encoding="utf-8"), counts)
        for claim in found:
            if any((doc, claim.number) in claimed_keys for doc in claim.candidates):
                report.untracked.append(f"[already claimed elsewhere] {claim.describe()}")
            else:
                report.untracked.append(f"[NOT IN THE MAP] {claim.describe()}")

    # Direction 1: every site in the tree is one the JSON knows about.
    seen_by_file_number: set[tuple[str, int, str]] = set()
    for claim in report.found:
        seen_by_file_number.update((claim.file, claim.number, doc) for doc in claim.candidates)
        if any((doc, claim.number) in claimed_keys for doc in claim.candidates):
            continue
        report.unrecorded.append(claim.describe())

    # Direction 2: every claim in the JSON is still carried by the file it names.
    for row in rows:
        claim = row.claim
        if claim is None or claim.kind == "record":
            continue
        target = REPO / claim.file
        if not target.exists():
            report.unverified.append(
                f"{row.doc} {row.number}: claim file {claim.file} is not on disk"
            )
            continue
        file_lines = target.read_text(encoding="utf-8").split("\n")
        here = [
            c for c in report.found
            if c.file == claim.file and c.number == row.number and row.doc in c.candidates
        ]
        if not here:
            report.unverified.append(
                f"{row.doc} {row.number}: nothing in {claim.file} names it any more "
                f"(JSON points at line {claim.line})"
            )
            continue
        if claim.kind == "function":
            actual = file_lines[claim.line - 1] if claim.line <= len(file_lines) else ""
            if f"def {claim.symbol}(" not in actual:
                at = [c.line for c in here if c.symbol == claim.symbol]
                report.line_drift.append(
                    f"{row.doc} {row.number}: `def {claim.symbol}(` is not at "
                    f"{claim.file}:{claim.line}" + (f"; it is at {at}" if at else "")
                )
        elif claim.line not in {c.line for c in here}:
            report.line_drift.append(
                f"{row.doc} {row.number}: {claim.file}:{claim.line} no longer carries the "
                f"number; the file names it at {sorted({c.line for c in here})}"
            )

    return report


# --------------------------------------------------------------------------- --check


def collect_claims(rows: list[CrosswalkRow]) -> tuple[int, list[str]]:
    """`pytest --collect-only -q` over the claimed files; return (node count, problems)."""
    files = sorted({row.claim.file for row in rows if row.claim and row.claim.kind != "record"})
    if not files:
        return 0, ["no claimed test files to collect"]
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header", *files],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    nodes = [line.strip() for line in result.stdout.split("\n") if "::" in line]
    if not nodes:
        return 0, [f"pytest collected nothing:\n{result.stdout}\n{result.stderr}"]
    node_files = {node.split("::", 1)[0].replace("\\", "/") for node in nodes}
    node_ids = set(nodes)
    problems: list[str] = []
    for row in rows:
        claim = row.claim
        if claim is None or claim.kind == "record":
            continue
        if claim.file not in node_files:
            problems.append(f"{row.doc} {row.number}: {claim.file} collected no tests")
            continue
        if claim.kind == "function":
            wanted = f"{claim.file}::{claim.symbol}"
            if not any(node.replace("\\", "/").startswith(wanted) for node in node_ids):
                problems.append(
                    f"{row.doc} {row.number}: {wanted} is not a collected node id"
                )
    return len(nodes), problems


# --------------------------------------------------------------------------- --selftest


def _row(**kwargs: Any) -> CrosswalkRow:
    base: dict[str, Any] = dict(
        doc="letf", number=1, line=244, text="x", paraphrase="x", cls="arithmetic",
        status="missing",
    )
    base.update(kwargs)
    return CrosswalkRow(**base)


def selftest() -> int:
    """Prove every guard RAISES (D48), and that a break hits the scalar it reads."""
    from backtest_framework.validation.crosswalk import Claim

    good = load_map()
    payload = load_payload()
    cases: list[tuple[str, Any, str]] = []

    def expect(label: str, fn: Any, fragment: str) -> None:
        cases.append((label, fn, fragment))

    expect("empty map", lambda: validate_crosswalk([]), "nothing to gate")
    expect(
        "duplicate (doc, number)",
        lambda: validate_crosswalk([_row(), _row()]),
        "DUPLICATE",
    )
    expect(
        "claim with no file",
        lambda: validate_crosswalk(
            [_row(status="claimed", claim=Claim(kind="message", file="", line=3))]
        ),
        "claim with no file",
    )
    expect(
        "claimed with no claim",
        lambda: validate_crosswalk([_row(status="claimed")]),
        "`claimed` with no claim",
    )
    expect(
        "missing WITH a claim",
        lambda: validate_crosswalk(
            [_row(status="missing", claim=Claim(kind="message", file="tests/x.py", line=3))]
        ),
        "never `missing`",
    )
    expect(
        "declined without a record claim",
        lambda: validate_crosswalk(
            [_row(status="declined", claim=Claim(kind="message", file="tests/x.py", line=3))]
        ),
        "without a `record` claim",
    )
    expect(
        "covered_via pointing at nothing claimed",
        lambda: validate_crosswalk([_row(status="covered_via", covered_via=("ledger", 66))]),
        "not a `claimed` row",
    )
    expect(
        "function claim with no symbol",
        lambda: validate_crosswalk(
            [_row(status="claimed", claim=Claim(kind="function", file="tests/x.py", line=3))]
        ),
        "no symbol",
    )
    expect("unknown class", lambda: validate_crosswalk([_row(cls="vibes")]), "unknown class")
    expect("unknown status", lambda: validate_crosswalk([_row(status="pending")]), "unknown status")
    expect("unknown document", lambda: validate_crosswalk([_row(doc="gamma")]), "unknown document")
    expect(
        "a 16-word paraphrase",
        lambda: validate_crosswalk([_row(paraphrase=" ".join(["w"] * 16))]),
        "word paraphrase against a ceiling",
    )
    expect("missing field", lambda: validate_crosswalk([_row(text="   ")]), "verbatim text")
    expect(
        "a count mismatch",
        lambda: assert_doc_counts(
            [r for r in good if not (r.doc == "letf" and r.number == 9)], payload["docs"]
        ),
        "missing [9]",
    )
    expect(
        "no document metadata",
        lambda: assert_doc_counts(good, {}),
        "no document metadata",
    )
    expect(
        "coverage over nothing",
        lambda: coverage_total([]),
        "got no rows",
    )
    expect(
        "a timestamp in the JSON",
        lambda: _refuse_timestamp(payload),
        "carries a timestamp",
    )

    failures = 0
    for label, fn, fragment in cases:
        try:
            fn()
        except CrosswalkError as exc:
            if fragment in str(exc):
                print(f"  RAISED  {label}")
            else:
                failures += 1
                print(f"  WRONG   {label}: expected {fragment!r} in {str(exc)!r}")
        else:
            failures += 1
            print(f"  SILENT  {label} -- a guard that cannot fire is worse than none")

    # THE SCAN MUST ITSELF BE ABLE TO FIRE, and each break must hit the list it reads --
    # a break that lands in a different bucket proves nothing about that bucket.
    others = [row for row in good if row.key != ("letf", 1)]
    ledger51 = next(row for row in good if row.key == ("ledger", 51))
    assert ledger51.claim is not None

    scan_breaks: list[tuple[str, str, Any]] = [
        (
            "a claim whose symbol was never written",
            "unverified",
            others + [_row(
                doc="letf", number=1, status="claimed",
                claim=Claim(kind="function", file="tests/unit/test_power.py", line=51,
                            symbol="test_letf_1_that_was_never_written"),
            )],
        ),
        (
            "a claim whose file is gone",
            "unverified",
            others + [_row(
                doc="letf", number=1, status="claimed",
                claim=Claim(kind="function", file="tests/unit/test_no_such_file.py", line=1,
                            symbol="test_letf_1"),
            )],
        ),
        (
            "a function claim whose line moved",
            "line_drift",
            [row for row in good if row.key != ("ledger", 51)] + [CrosswalkRow(
                doc=ledger51.doc, number=ledger51.number, line=ledger51.line,
                text=ledger51.text, paraphrase=ledger51.paraphrase, cls=ledger51.cls,
                status="claimed",
                claim=Claim(kind="function", file=ledger51.claim.file,
                            line=ledger51.claim.line + 3, symbol=ledger51.claim.symbol),
            )],
        ),
        (
            "a claim site the JSON stopped recording",
            "unrecorded",
            [row for row in good if row.key != ("ledger", 51)],
        ),
    ]
    for label, bucket, rows in scan_breaks:
        report = scan(rows, payload)
        if getattr(report, bucket):
            print(f"  RAISED  the scan reports {label} in {bucket}")
        else:
            failures += 1
            print(f"  SILENT  the scan did not report {label} in {bucket}:\n{report.render()}")

    # A doctored section line must land in doc_diffs, not anywhere else.
    if DEPOSIT_DIR.is_dir() and (DEPOSIT_DIR / payload["docs"]["letf"]["file"]).exists():
        doctored = json.loads(json.dumps(payload))
        doctored["docs"]["letf"]["heading_line"] = 1
        report = scan(good, doctored)
        if report.doc_diffs:
            print("  RAISED  the scan reports a moved section heading in doc_diffs")
        else:
            failures += 1
            print("  SILENT  the scan did not report a moved section heading")
    else:
        print("  SKIP    the deposit documents are absent; the section parse cannot be broken")

    # And it must be quiet on the real map, or every check above proves nothing.
    clean = scan(good, payload)
    if clean.disagreements:
        failures += 1
        print(f"  DIRTY   the real map disagrees with the tree:\n{clean.render()}")
    else:
        print("  CLEAN   the real map agrees with the tree")

    print(f"\n{len(cases) + len(scan_breaks) + 2} checks, {failures} failure(s)")
    return 1 if failures else 0


def _refuse_timestamp(payload: dict[str, Any]) -> None:
    import tempfile

    doctored = dict(payload)
    doctored["generated_at"] = "2026-09-21"
    with tempfile.TemporaryDirectory() as tmp:
        target = Path(tmp) / "map.json"
        with open(target, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(doctored, indent=2) + "\n")
        load_payload(target)


# --------------------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scan", action="store_true", help="report every difference; never writes")
    parser.add_argument("--render", action="store_true", help="write docs/results/DEPOSIT_TEST_MAP.md")
    parser.add_argument("--check", action="store_true", help="pytest --collect-only on the claims")
    parser.add_argument("--selftest", action="store_true", help="prove every guard raises")
    parser.add_argument("--map", default=str(DEFAULT_MAP_PATH), help="the JSON to read")
    parser.add_argument("--page", default=str(DEFAULT_PAGE_PATH), help="the page to write")
    args = parser.parse_args(argv)

    if not (args.scan or args.render or args.check or args.selftest):
        parser.error("pick one of --scan, --render, --check, --selftest")

    if args.selftest:
        return selftest()

    rows = load_map(args.map)
    payload = load_payload(args.map)
    status = 0

    if args.scan:
        report = scan(rows, payload)
        print(report.render())
        cov = coverage_by_doc(rows)
        total = coverage_total(rows)
        print("")
        for doc in DOC_KEYS:
            row = cov[doc]
            print(
                f"  {payload['docs'][doc]['file']:<36} "
                f"{int(row['claimed']):>3} / {int(row['count']):<3} claimed "
                f"({row['pct_claimed']:5.1f}%)"
            )
        print(
            f"  {'ALL FIVE':<36} {int(total['claimed']):>3} / {int(total['count']):<3} claimed "
            f"({total['pct_claimed']:5.1f}%)"
        )
        print("  classes: " + ", ".join(f"{k} {v}" for k, v in class_tally(rows).items()))
        status = max(status, 1 if report.disagreements else 0)

    if args.render:
        path = write_md(rows, docs_meta=payload["docs"], path=args.page)
        print(f"wrote {path}")

    if args.check:
        nodes, problems = collect_claims(rows)
        print(f"pytest collected {nodes} node id(s) across the claimed files")
        for problem in problems:
            print(f"  {problem}")
        status = max(status, 1 if problems else 0)

    return status


if __name__ == "__main__":
    raise SystemExit(main())
