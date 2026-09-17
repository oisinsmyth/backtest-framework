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

**Which means: `--build` is the LAST step, after `git add`, not the first.** Regenerate before
staging and the block records a repository that does not include the files you are about to commit.
That has now happened twice -- once in round eight when two files were added after the block was
written, and once in round nine when THIS script's own gate, being a unit test, changed the unit
count it measures the moment it was tracked. Neither was caught locally: the suite had already run,
and the gate reads the index, which agreed with itself at the moment it was asked. Both were caught
afterwards, by a clone and by the gate's own next run.

`tests/unit/test_results_docs_at_root.py` deliberately globs the filesystem instead, and that is
not an inconsistency: it hunts files a runner regenerated and left untracked, which are invisible
to the index. Different question, different instrument.

ANCHOR THE PATTERN
------------------
Decision numbers are matched as `^D<digits>` against the BASENAME. An unanchored `D[0-9]+` finds
`D304` inside `D300-AMENDMENT-cost-basis-and-what-D304-and-D305-changed.md` and reports 501
distinct numbers where there are 500. That mistake was made twice in two days while preparing this
script, which is why it is written down here rather than left to be rediscovered.

COLLECTION COUNTS ARE GATED; THE CLONE SPLIT IS NOT. THE LINE IS NOT "IS IT PYTEST"
-----------------------------------------------------------------------------------
`pytest --collect-only` does not execute anything. It walks the same tracked files `git ls-files`
walks and reports how many tests they declare, so at a given commit it returns the same numbers on
any machine, in any order, at any speed. That makes a tier count exactly as gateable as a file
count, and it is gated here for the same reason: `docs/VERIFICATION.md` was written on 2026-09-16
with freshly measured tier counts and immediately contradicted four older documents that still
said 91 golden tests when there were 101.

What stays out is the **clone pass/skip split** and wall-clock runtimes, and the reason is a
different one from "pytest is slow": they depend on what is *on the machine*. The skip count is a
function of which bulk panels a checkout happens to carry (D536, D538) and the runtime of how busy
the laptop is -- the same suite measured 6m21s and 7m00s here within a day. Those stay in prose
with a measurement date. A gate that reddens on a slower machine teaches people to ignore gates;
a gate that reddens on a stale count is the only thing that catches one.

Collection costs about 8 seconds, once, cached for the process. The `docs` CI job already runs
`uv run python` for this script, so it buys the gate without a new job.

THE REGISTRY, NOT THE GLOB, FOR FIGURE BUILDERS
-----------------------------------------------
`scripts/figures/build_all.py:23-27` states that the builder list is a registry rather than a glob
precisely so that forgetting to register a builder is loud. This script used to glob
`scripts/figures/*.py` and so counted `build_all.py` and `svgkit.py` as builders -- it reported 8
where the registry holds 6, and it was the one place in the repository that disobeyed the rule the
registry exists to enforce. It now imports `build_all.BUILDERS`, the way
`tests/unit/test_figures_index_is_complete.py` does.
"""

from __future__ import annotations

import argparse
import functools
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"

START = "<!-- COUNTS:START -->"
END = "<!-- COUNTS:END -->"

DECISION_BASENAME = re.compile(r"^D(\d+)")

TIERS = ("golden", "property", "integration", "unit")

#: `tests/unit/test_x.py::test_y` -- pytest writes node ids with forward slashes on every platform.
NODE_ID = re.compile(r"^tests/(golden|property|integration|unit)/\S+\.py::")
#: the `-q` summary, e.g. `2054/2059 tests collected (5 deselected) in 7.95s`
SUMMARY = re.compile(r"^(\d+)(?:/\d+)? tests? collected")


def tracked(*globs: str) -> list[str]:
    """Paths in the git index matching the given pathspecs."""
    out = subprocess.run(
        ["git", "ls-files", *globs], cwd=REPO, capture_output=True, text=True, check=True
    ).stdout
    return [line for line in out.splitlines() if line]


@functools.lru_cache(maxsize=1)
def collected() -> dict[str, int]:
    """Tests declared per tier, from one `--collect-only` pass. Nothing is executed.

    **The tracked test files are named explicitly rather than the `tests` directory**, for the
    reason the module docstring gives about `git ls-files`: pointing pytest at the directory
    collects untracked scratch test files that no clone has, which is the same class of error as
    counting scripts off the filesystem. The file list is the index; the file *contents* are the
    worktree, so an uncommitted edit to a tracked test file does move this count -- deliberately,
    since `git add` is the point at which the gate is meant to agree with you.

    The sum is cross-checked against pytest's own summary line rather than trusted. A node-id
    regex that silently stopped matching -- a renamed tier, a path separator changing under a new
    pytest -- would otherwise report a plausible smaller number, which is the failure mode this
    whole script exists to prevent. `declared outputs need a guard, not prose`.
    """
    files = [p for p in tracked("tests/*.py") if Path(p).name.startswith("test_")]
    if not files:  # pragma: no cover - only if the index is empty
        raise SystemExit("git ls-files found no tracked test files under tests/")

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", *files],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    lines = proc.stdout.splitlines()

    per_tier = dict.fromkeys(TIERS, 0)
    for line in lines:
        m = NODE_ID.match(line.strip())
        if m:
            per_tier[m.group(1)] += 1

    reported = next((int(m.group(1)) for m in map(SUMMARY.match, lines) if m), None)
    if reported is None:
        raise SystemExit(
            "pytest --collect-only printed no summary line; collection failed.\n"
            + "\n".join(lines[-20:])
            + (proc.stderr or "")
        )
    total = sum(per_tier.values())
    if total != reported:
        raise SystemExit(
            f"collection disagrees with itself: node ids matched {total} tests across {TIERS}, "
            f"pytest reported {reported}. Either a tier was added outside those four directories "
            "or NODE_ID no longer matches the node ids pytest writes."
        )

    return {"tests": total, **{f"tests_{tier}": n for tier, n in per_tier.items()}}


@functools.lru_cache(maxsize=1)
def registered_builders() -> tuple[str, ...]:
    """`build_all.BUILDERS` -- the registry, not a glob over `scripts/figures/*.py`.

    Loaded by path the way `tests/unit/test_figures_index_is_complete.py` loads it, because
    `scripts/` is not an importable package.
    """
    path = REPO / "scripts" / "figures" / "build_all.py"
    spec = importlib.util.spec_from_file_location("build_all", path)
    if spec is None or spec.loader is None:  # pragma: no cover - only if the file is unreadable
        raise SystemExit(f"cannot load {path}, which owns the figure registry")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return tuple(module.BUILDERS)


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
        # The highest number the directory holds. Rendered as a range so that `D1 -> DNNN` is a
        # generated string in one place instead of a typed one in three (README twice,
        # PHILOSOPHY once -- all three had drifted to D537 by D539).
        "max_decision": max(numbers),
        # `scripts/figures/` is excluded and counted separately. The caption on this row says
        # "one-shot by design", which is true of the dNNN_* runners and false of a figure builder
        # that CI re-runs on every push -- and a generated count whose caption is wrong is worse
        # than a typed one, because it looks checked.
        "scripts": len([p for p in tracked("scripts/*.py") if "/figures/" not in p]),
        "figure_builders": len(registered_builders()),
        "library_modules": len(library),
        "research_modules": len(research),
        "results_documents": len(results),
        "test_files": len([p for p in tracked("tests/*.py") if Path(p).name.startswith("test_")]),
        # Subpackages holding the LIBRARY: every `__init__.py` less the top-level one and less
        # `research/`, because the 46 modules counted above already exclude research. Counting all
        # 12 subpackages beside a figure that excludes one of them is the arithmetic slip this
        # script exists to prevent -- and `docs/ARCHITECTURE.md` shipped with exactly it.
        "packages": len([p for p in tracked("src/*__init__.py") if "/research/" not in p]) - 1,
        **collected(),
    }


def render() -> str:
    c = counts()
    return "\n".join(
        [
            START,
            "",
            "| | |",
            "|---|---|",
            f"| **{c['decision_files']} decision records** | D1 → D{c['max_decision']}, over "
            f"**{c['decision_numbers']}** decision numbers — a pre-registration and its result "
            "share one number |",
            f"| **{c['library_modules']} library modules** | across {c['packages']} packages, plus "
            f"{c['research_modules']} in `research/`, which is study code rather than framework |",
            # "documents", not "studies": five of these are not studies -- the final report, two
            # generated exhibits, a provider probe and a gate note -- and
            # `docs/results/README.md` says so of one of them. A generated count with a false
            # caption is worse than a typed one, because it looks checked.
            f"| **{c['results_documents']} documents** | in "
            "[`docs/results/`](docs/results/README.md), five of them featured |",
            f"| **{c['tests']:,} tests** | {c['tests_golden']} golden · "
            f"{c['tests_property']} property · {c['tests_integration']} integration · "
            f"{c['tests_unit']:,} unit, across {c['test_files']} files |",
            f"| **{c['scripts']} research runners** | in `scripts/`, one-shot by design |",
            f"| **{c['figure_builders']} figure builders** | registered in "
            "`scripts/figures/build_all.py`, regenerated and checked in CI |",
            "",
            "<sub>Generated by `scripts/build_readme_counts.py` from the git index, plus one "
            "`pytest --collect-only` pass for the test counts — it executes nothing, so the "
            "numbers are the same on any machine at this commit. "
            "`tests/unit/test_readme_counts_are_current.py` fails if this block drifts; "
            "`tests/unit/test_quoted_counts_are_current.py` fails if the prose around it "
            "drifts.</sub>",
            "",
            END,
            "",
        ]
    )


def splice(text: str, block: str) -> str:
    """Replace the marked region, leaving exactly one blank line on each side of it.

    The separators are normalised rather than preserved because preserving them was not
    idempotent: `block` ends in a newline after `END` and the surviving tail began with one, so
    every `--build` added a blank line. Eleven had accumulated under the table in `README.md`,
    which put a void between the counts and the paragraph whose subject they are.
    """
    if START in text and END in text:
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        return before.rstrip("\n") + "\n\n" + block.strip("\n") + "\n\n" + after.lstrip("\n")
    return text.rstrip() + "\n\n" + block


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--print", action="store_true", dest="to_stdout")
    args = ap.parse_args()

    block = render()

    if args.to_stdout:
        # The block is UTF-8 and the README is written as UTF-8, but a Windows console is cp1252
        # and cannot encode `→`. Writing bytes keeps `--print` from being the one mode of this
        # script that fails on the machine the repository is authored on.
        sys.stdout.buffer.write(block.encode("utf-8"))
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
