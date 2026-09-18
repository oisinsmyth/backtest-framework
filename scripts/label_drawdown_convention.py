"""Declare, in each artifact, which drawdown SIGN it carries (D542).

    python scripts/label_drawdown_convention.py --status   # what is labelled and what is not
    python scripts/label_drawdown_convention.py --write    # insert the marker, values untouched
    python scripts/label_drawdown_convention.py --check    # fail if a marker is missing or WRONG

WHY THE FILE HAS TO SAY IT
--------------------------
`analytics.metrics.max_drawdown` returns a POSITIVE fraction of peak. `research/
terrain_strategies` publishes the same quantity NEGATIVE. Both are internally consistent
and the repository has published both for years: across tracked `data/*.json` there are
roughly 1,800 negative drawdown values and 1,200 positive ones. A reader diffing two
summaries has no way to tell a `-0.25` from a `0.25` that means the same thing.

D542 collapsed the arithmetic to one implementation and made the sign a DISPLAY decision
applied once at the emit boundary. It deliberately did NOT rewrite the artifacts: the
values on disk are the values the studies published, and moving them is a research
decision with its own pre-registration, not something a labelling pass does in passing.
So the disagreement is DISCLOSED rather than removed — each file states its own sign.

WHY THE MARKER IS DERIVED, NOT TYPED
------------------------------------
The marker is computed from the file's own values every time, and `--check` recomputes it
and fails on disagreement. A hand-written convention note is a comment; a note that is
re-derived from the thing it describes is a gate. This is the same reason
`run_golden_master_ledger.py --check` re-runs the engine instead of trusting its artifact.

LEVELS AND DIFFERENCES ARE NOT THE SAME KEY
-------------------------------------------
`d_maxdd`, `mean_d_maxdd` and `median_d_maxdd` are DIFFERENCES of two drawdowns. A
difference is signed by definition and carries no sign convention, so it is excluded from
the census. Missing that distinction made three files look like they held both
conventions at once; they do not.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MARKER = "max_drawdown_convention"

# A key naming a drawdown LEVEL. Anchored at the end so `..._maxdd_bars` and friends do
# not match a quantity that is not a drawdown.
LEVEL = re.compile(r"(?i)(max_?draw_?down|max_?dd|maxdd)$")

# A key naming a DIFFERENCE of two drawdowns. Checked first: `d_maxdd` also matches LEVEL.
DIFFERENCE = re.compile(r"(?i)(^|_)d_(max_?draw_?down|max_?dd|maxdd)$")

NEGATIVE_NOTE = (
    "Drawdown LEVELS in this file are NEGATIVE fractions of peak (a -0.25 is a 25% "
    "decline). Arithmetic is analytics.metrics.max_drawdown, which returns the positive "
    "fraction; research/terrain_strategies negates it once at the emit boundary (D542). "
    "Keys matching d_*: differences of two drawdowns, signed by definition."
)
POSITIVE_NOTE = (
    "Drawdown LEVELS in this file are POSITIVE fractions of peak (a 0.25 is a 25% "
    "decline) — analytics.metrics.max_drawdown's own convention (D80, D542). "
    "Keys matching d_*: differences of two drawdowns, signed by definition."
)


def tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "data/*.json"], cwd=REPO, capture_output=True, text=True, check=True
    )
    return [p for p in out.stdout.splitlines() if p and (REPO / p).exists()]


def levels(node: object) -> list[float]:
    """Every drawdown LEVEL in the payload, at any depth. Differences excluded."""
    found: list[float] = []
    if isinstance(node, dict):
        for key, value in node.items():
            numeric = isinstance(value, (int, float)) and not isinstance(value, bool)
            if numeric and LEVEL.search(key) and not DIFFERENCE.search(key):
                found.append(float(value))
            else:
                found.extend(levels(value))
    elif isinstance(node, list):
        for value in node:
            found.extend(levels(value))
    return found


def convention_of(values: list[float]) -> str | None:
    """`negative`, `positive`, or None when the file cannot state one.

    A file whose levels are all exactly 0.0 has no sign to declare, and a file holding
    both signs is not mislabelled by this script — it is REFUSED, because one marker
    cannot describe it and a marker that is half right is worse than none.
    """
    negative = sum(1 for v in values if v < 0)
    positive = sum(1 for v in values if v > 0)
    if negative and positive:
        return "MIXED"
    if negative:
        return "negative"
    if positive:
        return "positive"
    return None


def payload_of(rel: str) -> dict | None:
    try:
        parsed = json.loads((REPO / rel).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return parsed if isinstance(parsed, dict) else None


def census() -> list[tuple[str, str, dict | None]]:
    """(path, convention, existing marker) for every tracked artifact holding a level."""
    rows = []
    for rel in tracked():
        parsed = payload_of(rel)
        if parsed is None:
            continue
        values = levels(parsed)
        if not values:
            continue
        convention = convention_of(values)
        if convention is None:
            continue
        rows.append((rel, convention, parsed.get(MARKER)))
    return sorted(rows)


def insert(rel: str, convention: str) -> bool:
    """Insert the marker as the first key, leaving every other byte exactly as it was.

    Textual, not a re-dump. Re-serialising would re-indent and re-order files written by
    a dozen different runners over two years, turning a one-line disclosure into a diff
    nobody can review — and the point of NOT rewriting the artifacts is defeated if the
    labelling pass rewrites them.
    """
    path = REPO / rel
    raw = path.read_bytes().decode("utf-8")
    # This worktree holds 661 CRLF artifacts against 30 LF ones (pre-.gitattributes
    # checkouts). Splicing an LF span into a CRLF file would leave mixed endings in the
    # worktree, so the inserted lines take the file's OWN ending. What the index receives
    # is git's business; what this script writes must not be the odd line out.
    eol = "\r\n" if "\r\n" in raw else "\n"
    brace = raw.index("{")
    note = NEGATIVE_NOTE if convention == "negative" else POSITIVE_NOTE
    block = json.dumps({MARKER: {"sign": convention, "note": note, "record": "D542"}}, indent=2)
    # `block` is `{\n  "max_drawdown_convention": {...}\n}`: take its interior.
    interior = block[block.index("\n") + 1 : block.rindex("\n")].replace("\n", eol)
    spliced = raw[: brace + 1] + eol + interior + "," + raw[brace + 1 :]

    before = json.loads(raw)
    after = json.loads(spliced)
    if after.pop(MARKER, None) is None:
        raise SystemExit(f"{rel}: marker did not survive the splice")
    if after != before:
        raise SystemExit(f"{rel}: splice changed an existing value; refusing to write")
    path.write_bytes(spliced.encode("utf-8"))
    return True


def cmd_status() -> int:
    rows = census()
    labelled = [r for r in rows if r[2] is not None]
    mixed = [r for r in rows if r[1] == "MIXED"]
    print(f"artifacts holding a drawdown level : {len(rows)}")
    print(f"  negative                         : {sum(1 for r in rows if r[1] == 'negative')}")
    print(f"  positive                         : {sum(1 for r in rows if r[1] == 'positive')}")
    print(f"  MIXED (refused)                  : {len(mixed)}")
    print(f"already labelled                   : {len(labelled)}")
    for rel, _, _ in mixed:
        print(f"  MIXED {rel}")
    return 1 if mixed else 0


def cmd_write() -> int:
    written = 0
    for rel, convention, existing in census():
        if convention == "MIXED":
            print(f"REFUSED  {rel} — holds both signs; one marker cannot describe it")
            return 1
        if existing is not None:
            continue
        insert(rel, convention)
        written += 1
    print(f"{written} artifact(s) labelled")
    return 0


def cmd_check() -> int:
    """A marker that no longer matches the values it describes is worse than no marker."""
    problems = []
    rows = census()
    for rel, convention, existing in rows:
        if convention == "MIXED":
            problems.append(f"{rel}: holds both signs")
        elif existing is None:
            problems.append(f"{rel}: no {MARKER} — run --write")
        elif existing.get("sign") != convention:
            problems.append(f"{rel}: marker says {existing.get('sign')!r}, values are {convention!r}")
    if problems:
        for line in problems:
            print(f"  {line}")
        print(f"{len(problems)} problem(s) of {len(rows)} artifact(s)")
        return 1
    print(f"{len(rows)} artifact(s), every marker agrees with its own values")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.status:
        return cmd_status()
    if args.write:
        return cmd_write()
    if args.check:
        return cmd_check()
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
