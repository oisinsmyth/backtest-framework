"""Generate the register half of `docs/decisions/README.md` — one row per decision NUMBER.

    python scripts/build_decision_register.py --print     # the markdown, to stdout
    python scripts/build_decision_register.py --write     # replace the register section in place

WHY A SECOND TABLE RATHER THAN ONE
----------------------------------
The index's first table is 290 hand-written rows covering D1–D284, with a curated one-line summary
each. It is also **already inconsistent**: nominally four columns, but 17 rows carry two cells and
8 carry five to eight because the prose contains unescaped `|`, and the longest row is 5,228
characters. Extending it by 251 machine-made rows would force a uniformity neither half has and
would pretend the generated summaries are the same kind of object as the written ones.

So the curated table stays untouched and this appends a **register** below it: number, title,
files. The register exists to get you to the record. The curated table exists to tell you what the
record said. Different jobs, different tables, said out loud in the preamble.

ONE ROW PER NUMBER, NOT PER FILE
--------------------------------
Most numbers are one file; a good many are not. Per-file would be a table in which a single study
occupies eighteen lines — D528 has a RESULT plus sixteen addenda. Measured from the git index on
2026-09-16: 743 files, 500 numbers, 187 of them with two or more files. The counts are dated
because they are not generated: this docstring said **741** until 2026-09-16, which was the
worktree with six uncommitted deletions in it and not what a clone receives. The live numbers are

    git ls-files 'docs/decisions/D*.md' | wc -l
    git ls-files 'docs/decisions/D*.md' | xargs -n1 basename | grep -oE '^D[0-9]+' | sort -u | wc -l

WHAT CANNOT BE GENERATED, AND IS THEREFORE NOT CLAIMED
-----------------------------------------------------
**Status and Category.** 276 records carry neither (index, 2026-09-16); `**Category:**` appears on 209, all of them the
old design-decision format. Study records carry their state in the filename token (`PRE-REG`,
`RESULT`, `CLOSE`, `ADDENDUM`) and that token is the only honest source, so the register reports
the tokens present and nothing else. A synthesised Status column would look like data.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DECISIONS = REPO / "docs" / "decisions"
INDEX = DECISIONS / "README.md"

START = "<!-- REGISTER:START -->"
END = "<!-- REGISTER:END -->"

# `D<n>` optionally wrapped by a leading and/or trailing uppercase token, then a dash, then the
# title. Covers `# D537 — …`, `# D288 RESULT — …`, `# RESULT D476 — …` and
# `# D473 RESULT (forward) — …`.
H1 = re.compile(
    r"^#\s*(?:(?P<pre>[A-Z][A-Z ]*?)\s+)?D0*(?P<num>\d+)[a-z]?"
    r"(?:\s+(?P<post>[A-Z][A-Z]*(?:\s*\([a-z- ]+\))?))?\s*[—-]\s*(?P<title>.+?)\s*$"
)

TOKENS = ("PRE-REG", "RESULT", "ADDENDUM", "CLOSE", "AMENDS", "WITHDRAWN")

MAX_TITLE = 120


def number_of(path: Path) -> int:
    return int(re.match(r"D(\d+)", path.name).group(1))


def title_of(path: Path) -> str:
    """The H1's title, falling back to the filename slug.

    The fallback is not cosmetic: `D483-CLOSE-the-daily-channel-line-D399-to-D483.md` has no
    number in its H1 at all, and a handful of records put a parenthetical after the token.
    """
    first = path.read_text(encoding="utf-8", errors="replace").split("\n", 1)[0]
    m = H1.match(first)
    if m:
        title = m.group("title")
    elif first.startswith("#"):
        title = first.lstrip("# ").strip()
    else:  # pragma: no cover - every record starts with an H1 today
        title = path.stem.split("-", 1)[-1].replace("-", " ")
    title = re.sub(r"\s+", " ", title.replace("**", "").replace("`", ""))
    return title if len(title) <= MAX_TITLE else title[: MAX_TITLE - 1].rstrip() + "…"


def tokens_of(name: str) -> list[str]:
    return [t for t in TOKENS if f"-{t}-" in name or name.endswith(f"-{t}.md")]


def by_number() -> dict[int, list[Path]]:
    grouped: dict[int, list[Path]] = defaultdict(list)
    for path in sorted(DECISIONS.glob("D*.md")):
        if re.match(r"D\d+", path.name):
            grouped[number_of(path)].append(path)
    return dict(sorted(grouped.items()))


def curated_numbers() -> set[int]:
    """The numbers the hand-written table above already covers.

    Read rather than assumed: the curated half is D1–D284 *with gaps* — D245–D248, D253–D258 and
    D260–D261 were never added — so "everything from D285" would leave twelve numbers in neither
    half. The register takes whatever the curated table does not.
    """
    text = INDEX.read_text(encoding="utf-8")
    curated = text.split(START)[0] if START in text else text
    return {int(n) for n in re.findall(r"\|\s*\[D0*(\d+)", curated)}


def rows(first: int) -> list[str]:
    covered = curated_numbers()
    out = []
    for num, paths in by_number().items():
        if num < first and num in covered:
            continue
        # The record that names the number best: a RESULT if there is one, else the first file.
        lead = next((p for p in paths if "-RESULT" in p.name), paths[0])
        title = title_of(lead)
        links = " · ".join(
            f"[{'·'.join(tokens_of(p.name)) or 'record'}]({p.name})" for p in paths
        )
        out.append(f"| D{num} | {title} | {links} |")
    return out


def render(first: int) -> str:
    head = [
        START,
        "",
        "## Register — everything the curated table above does not cover",
        "",
        "Generated by `scripts/build_decision_register.py`. **One row per decision number**, with",
        "every file carrying that number linked from it. This half exists to get you to the record;",
        "the curated table above exists to tell you what the record said.",
        "",
        f"Mostly D{first} onward, plus the numbers below it the curated table never picked up.",
        "",
        "**No Status or Category column, deliberately.** 274 of these records carry neither field —",
        "study records state their position in the filename token instead — and a synthesised column",
        "would look like data. The tokens are what is shown.",
        "",
        "| # | Title | Records |",
        "|---|-------|---------|",
    ]
    return "\n".join(head + rows(first) + ["", END, ""])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--first", type=int, default=285, help="lowest number to register")
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    block = render(args.first)
    if args.to_stdout:
        sys.stdout.write(block)
        return 0
    if args.write:
        text = INDEX.read_text(encoding="utf-8")
        if START in text and END in text:
            before, rest = text.split(START, 1)
            _, after = rest.split(END, 1)
            text = before + block + after
        else:
            text = text.rstrip() + "\n\n" + block
        INDEX.write_text(text, encoding="utf-8")
        print(f"register written: {len(rows(args.first))} numbers from D{args.first}")
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
