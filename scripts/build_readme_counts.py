"""The README's inventory counts, generated from the git index rather than typed.

    python scripts/build_readme_counts.py --build     # rewrite the marked region
    python scripts/build_readme_counts.py --check     # exit 1 if the region is stale
    python scripts/build_readme_counts.py --print

WHY THIS EXISTS
---------------
An audit of twenty repack commits found ~38 stale factual claims, and the largest single cause was
counts typed into prose by hand. Two were wrong in a way worth naming: the README said **741**
decision records and **586** scripts, because they were counted off the working tree while six
deletions sat uncommitted. **A clone gets 743 and 588.** The README describes what a cloner
receives, so it must be measured on what a cloner receives.

THE INDEX, NOT THE FILESYSTEM -- AND NOT `HEAD` EITHER
------------------------------------------------------
`git ls-files` is the boundary, the same one `scripts/check_doc_links.py` uses:

  * the **filesystem** counts files nobody else has (untracked scratch) and misses files everyone
    else has (tracked, deleted locally). That is exactly the error this script exists to prevent.
  * **`HEAD`** would be correct for a clone but fights the contributor: adding a decision record
    and updating the README in one commit would fail the gate right up until the commit landed.
  * the **index** reflects staged state, so `git add` is the point at which the gate agrees with
    you -- which is the moment the work is real.

`tests/unit/test_results_docs_at_root.py` deliberately globs the filesystem instead, and that is
not an inconsistency: it hunts files a runner regenerated and left untracked, which are invisible
to the index. Different question, different instrument.

ANCHOR THE PATTERN
------------------
Decision numbers are matched as `^D<digits>` against the BASENAME. An unanchored `D[0-9]+` finds
`D304` inside `D300-AMENDMENT-cost-basis-and-what-D304-and-D305-changed.md` and reports 501
distinct numbers where there are 500. That mistake was made twice in two days while preparing this
script, which is why it is written down here rather than left to be rediscovered.

WHAT IS DELIBERATELY NOT GATED
------------------------------
Wall-clock runtimes and the clone pass/skip split. They are machine-dependent -- the same suite
measured 6m21s and 7m00s on this laptop within a day -- so the README carries them as prose with a
measurement date. A gate that reddens on a slower machine teaches people to ignore gates.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"

START = "<!-- COUNTS:START -->"
END = "<!-- COUNTS:END -->"

DECISION_BASENAME = re.compile(r"^D(\d+)")


def tracked(*globs: str) -> list[str]:
    """Paths in the git index matching the given pathspecs."""
    out = subprocess.run(
        ["git", "ls-files", *globs], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


def counts() -> dict[str, int]:
    decisions = [p for p in tracked("docs/decisions/*.md") if DECISION_BASENAME.match(Path(p).name)]
    numbers = {int(DECISION_BASENAME.match(Path(p).name).group(1)) for p in decisions}

    src = [p for p in tracked("src/*.py") if not p.endswith("__init__.py")]
    library = [p for p in src if "/research/" not in p]
    research = [p for p in src if "/research/" in p]

    results = [
        p
        for p in tracked("docs/results/*.md", "docs/results/*.html")
        if "/archive/" not in p and not p.endswith("/README.md")
    ]

    return {
        "decision_files": len(decisions),
        "decision_numbers": len(numbers),
        # `scripts/figures/` is excluded and counted separately. The caption on this row says
        # "one-shot by design", which is true of the dNNN_* runners and false of a figure builder
        # that CI re-runs on every push -- and a generated count whose caption is wrong is worse
        # than a typed one, because it looks checked.
        "scripts": len([p for p in tracked("scripts/*.py") if "/figures/" not in p]),
        "figure_builders": len(tracked("scripts/figures/*.py")),
        "library_modules": len(library),
        "research_modules": len(research),
        "results_documents": len(results),
        "test_files": len([p for p in tracked("tests/*.py") if Path(p).name.startswith("test_")]),
        # Subpackages holding the LIBRARY: every `__init__.py` less the top-level one and less
        # `research/`, because the 46 modules counted above already exclude research. Counting all
        # 12 subpackages beside a figure that excludes one of them is the arithmetic slip this
        # script exists to prevent -- and `docs/ARCHITECTURE.md` shipped with exactly it.
        "packages": len([p for p in tracked("src/*__init__.py") if "/research/" not in p]) - 1,
    }


def render() -> str:
    c = counts()
    return "\n".join(
        [
            START,
            "",
            "| | |",
            "|---|---|",
            f"| **{c['decision_files']} decision records** | over **{c['decision_numbers']}** "
            "decision numbers — a pre-registration and its result share one number |",
            f"| **{c['library_modules']} library modules** | across {c['packages']} packages, plus "
            f"{c['research_modules']} in `research/`, which is study code rather than framework |",
            f"| **{c['results_documents']} studies** | in [`docs/results/`](docs/results/README.md),"
            " five of them featured |",
            f"| **{c['test_files']} test files** | golden · property · integration · unit |",
            f"| **{c['scripts']} research runners** | in `scripts/`, one-shot by design |",
            f"| **{c['figure_builders']} figure builders** | in `scripts/figures/`, regenerated "
            "and checked in CI |",
            "",
            "<sub>Generated from the git index by `scripts/build_readme_counts.py`; "
            "`tests/unit/test_readme_counts_are_current.py` fails if this block drifts.</sub>",
            "",
            END,
            "",
        ]
    )


def splice(text: str, block: str) -> str:
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return before + block + after
    return text.rstrip() + "\n\n" + block


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args()

    block = render()

    if args.to_stdout:
        sys.stdout.write(block)
        return 0

    text = README.read_text(encoding="utf-8")

    if args.check:
        if START not in text or END not in text:
            print("README.md has no COUNTS block — run --build")
            return 1
        current = START + text.split(START, 1)[1].split(END, 1)[0] + END
        if current.strip() == block.strip():
            print("README counts are current")
            return 0
        print("README counts are STALE — run `python scripts/build_readme_counts.py --build`")
        return 1

    if args.build:
        README.write_text(splice(text, block), encoding="utf-8")
        print("README counts written: " + ", ".join(f"{k}={v}" for k, v in counts().items()))
        return 0

    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
