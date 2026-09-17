"""The public repository: this tree, entire and unchanged, with fresh history.

    python scripts/build_public_cut.py --status          # what the cut contains, measured
    python scripts/build_public_cut.py --build DEST      # project it and make one commit
    python scripts/build_public_cut.py --build DEST --into-non-empty

WHY THIS EXISTS
---------------
`docs/decisions/D536-manifest-only-storage-for-the-bulk-panels.md:105-116` rejected `filter-repo`
outright -- it "would convert a recoverable repack into a deletion", dangling every `git_blob` in
`data/data_manifest.json` -- and named the successor in the same breath: "the clone-size problem
gets a different answer (a curated public repository); it is not this decision's to solve." **This
script is that answer.** It solves the size problem by not carrying the history at all, so the
private history stays intact, unrewritten, and every blob id still resolves.

The arithmetic it rests on: `data/**` blobs are **98.46% of the 940 MiB pack** (837 MiB of them
bulk panels D536 dropped from the index and deliberately left in history, 113 of 113 pointers
verified recoverable). Everything else across 1,392 commits -- all source, docs, tests, scripts,
and every commit and tree object -- is **14.5 MB**. A fresh-history public repository is therefore
roughly **40 MiB against 970 MiB**, and it is the history, not the content, that is dropped.

WHAT IS CUT, AND WHAT IS NOT
----------------------------
**Nothing is redacted and nothing is excluded.** The cut is the entire tracked tree at its current
state -- every negative result, every superseded record, `.github/`, `.claude/` and the dotfiles
included. The *only* difference from this repository is that the public one starts at commit one.
`working/PORTFOLIO_PLAN.md:346` states the constraint the commit message has to satisfy: "Curation
is allowed; revision is not. A public repo that shows 5 of 50 studies is curated. A public repo
that shows 5 studies *and implies there were 5* is not." So the commit message says what the cut
is, how many commits and what span it was cut from, and that the full history is retained.

THE INDEX, NOT THE FILESYSTEM
-----------------------------
The file list is `git ls-files`. The reasoning is already written down at
`scripts/build_readme_counts.py:15-24` and is not re-argued here.

THE BYTES COME FROM `HEAD`, NOT FROM THE WORKTREE
-------------------------------------------------
The first version of this script copied files off disk, and that was wrong twice over.

It published whatever happened to be half-edited at the time — a public repository is a statement
about a *committed* state, not about one working directory at one moment. And it could not run at
all while any tracked file was deleted-but-uncommitted: it named the missing paths and refused,
which sounds careful until you notice that in this repository that is the ordinary condition. Six
records were in exactly that state while this was being written (`docs/decisions/D497-*.md`,
`D498-*.md` and their `data/` and `scripts/` companions, deleted in the worktree mid-renumbering),
and the principal's research leaves something uncommitted most days. **A publishing tool that
refuses whenever the author has uncommitted work is a tool that never runs.**

Reading `HEAD` removes the failure rather than guarding it: HEAD is complete by construction, so
there is no missing-file case to report and no escape hatch to misuse. `--status` still reports a
worktree/index divergence, because a reader comparing the cut against their own checkout deserves
to know the two differ — but it is a note, not a refusal.

BYTES, NOT TEXT
---------------
Files are copied byte for byte. `.gitattributes:16` pins the index to `* text=auto eol=lf` while
this worktree is CRLF (`core.autocrlf=true`), and several tests byte-compare or hash tracked text
(`tests/unit/test_cftc_cot_fixture.py`, `tests/integration/test_binance_fixture.py:269`). Copying
bytes and letting the copied `.gitattributes` normalise on `git add` reproduces the source index
exactly -- which `--build` then checks, blob id against blob id, rather than assuming.

**Nothing here reads a price.** If a function in this file parses a bar, it is a bug.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd or REPO, capture_output=True, text=True, check=True
    ).stdout


def tracked() -> list[str]:
    """Every path in the git index, NUL-separated so a space or a quote cannot split a name."""
    return [p for p in git("ls-files", "-z").split("\0") if p]


def missing_from_worktree(paths: list[str]) -> list[str]:
    """Tracked paths with no file on disk.

    No longer what `--build` reads -- it reads HEAD -- but `--status` still reports it, because a
    reader comparing the cut against their own checkout deserves to know the two differ.
    """
    return [p for p in paths if not (REPO / p).is_file()]


def head_blobs(paths: list[str]) -> dict[str, bytes]:
    """`{path: bytes}` read out of HEAD in one `git cat-file --batch` call.

    One process, not one per file: at 3,000 paths the per-call form takes minutes on Windows and
    this takes about a second. The batch protocol is `<sha> <type> <size>\\n<size bytes>\\n`, and a
    path HEAD does not have answers `<rev> missing` instead -- which is why the caller checks for
    absences rather than trusting the count.
    """
    query = "".join(f"HEAD:{p}\n" for p in paths).encode("utf-8")
    proc = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=REPO, input=query, capture_output=True, check=True
    )
    out, pos, blobs = proc.stdout, 0, {}
    for rel in paths:
        end = out.index(b"\n", pos)
        header = out[pos:end].decode("utf-8", "replace").split()
        if header[-1] == "missing":
            pos = end + 1
            continue
        size = int(header[2])
        blobs[rel] = out[end + 1 : end + 1 + size]
        pos = end + 1 + size + 1  # the trailing newline git writes after each blob
    return blobs


def present_bytes(paths: list[str]) -> dict[str, int]:
    return {p: (REPO / p).stat().st_size for p in paths if (REPO / p).is_file()}


def top_directories(sizes: dict[str, int], limit: int = 6) -> list[tuple[str, int, int]]:
    """`(top-level directory, bytes, file count)`, largest first. Root files group as `(root)`."""
    totals: dict[str, list[int]] = {}
    for path, size in sizes.items():
        top = path.split("/")[0] if "/" in path else "(root)"
        entry = totals.setdefault(top, [0, 0])
        entry[0] += size
        entry[1] += 1
    ranked = sorted(totals.items(), key=lambda kv: -kv[1][0])
    return [(name, size, count) for name, (size, count) in ranked[:limit]]


def git_dir_kib() -> tuple[int, int]:
    """`(loose KiB, packed KiB)` for this repository, from `git count-objects -v`."""
    fields = dict(
        line.split(": ", 1) for line in git("count-objects", "-v").splitlines() if ": " in line
    )
    return int(fields.get("size", 0)), int(fields.get("size-pack", 0))


def history() -> tuple[int, str, str]:
    """`(commit count, first date, last date)` of the history this cut is taken from."""
    count = int(git("rev-list", "--count", "HEAD").strip())
    dates = git("log", "--format=%ad", "--date=short").splitlines()
    return count, dates[-1], dates[0]


def mib(n: int) -> str:
    return f"{n / 1048576:,.1f} MiB"


def commit_message() -> str:
    """What the cut is, measured, in the terms `working/PORTFOLIO_PLAN.md:346` requires.

    Curation is allowed; revision is not. The reader of this commit is told the cut is total, what
    it was cut from, and that the history still exists -- so nothing about the single commit can be
    read as a claim that the work started here.
    """
    count, first, last = history()
    return (
        "The whole tree, at its final private state, with fresh history\n"
        "\n"
        f"This repository begins here. Its contents are the complete tracked tree of a private\n"
        f"research repository of {count:,} commits spanning {first} to {last} -- every source\n"
        "file, document, test, script and data artifact that repository tracks, unchanged.\n"
        "\n"
        "The cut is total: nothing is redacted and nothing is excluded. The studies that failed\n"
        "are here alongside the ones that did not, superseded records are here marked superseded,\n"
        "and the decision log is the same append-only log. Curation is allowed; revision is not --\n"
        "no result was altered, removed or re-run to prepare this cut.\n"
        "\n"
        "What is dropped is the history itself, and the reason is size rather than secrecy. Bulk\n"
        "data blobs are 98.46% of the private repository's 940 MiB pack; everything else across\n"
        f"all {count:,} commits -- source, docs, tests, scripts, and every commit and tree object --\n"
        "is 14.5 MB. That full history is retained privately and unrewritten, with its data blobs\n"
        "still recoverable by `git cat-file blob <id>` against the ids in data/data_manifest.json.\n"
        "See docs/decisions/D536-manifest-only-storage-for-the-bulk-panels.md.\n"
    )


def cmd_status() -> int:
    paths = tracked()
    absent = missing_from_worktree(paths)
    sizes = present_bytes(paths)
    loose_kib, pack_kib = git_dir_kib()
    git_bytes = (loose_kib + pack_kib) * 1024
    count, first, last = history()

    print(f"tracked files   {len(paths):,}   (git ls-files)")
    print(f"file bytes      {mib(sum(sizes.values()))}   on disk, as the cut would copy them")
    print(f"cut from        {count:,} commits, {first} to {last}")
    print()
    for name, size, files in top_directories(sizes):
        print(f"  {name + '/':<14} {mib(size):>12}   {files:>5} files")
    print()
    print(f"this repo .git  {mib(git_bytes)}   ({mib(pack_kib * 1024)} packed)")
    print(
        f"delta           the cut carries {mib(sum(sizes.values()))} of files and no history, "
        f"against {mib(git_bytes)} here"
    )
    print("                (D536: data blobs are 98.46% of the pack; all else is 14.5 MB)")

    if absent:
        print()
        print(f"note            {len(absent)} tracked path(s) are missing from this WORKTREE:")
        for path in absent:
            print(f"                  {path}")
        print("                --build reads HEAD and is unaffected. This is a note, not a")
        print("                refusal: a reader comparing the cut against their own checkout")
        print("                deserves to know the two differ.")
    return 0


def cmd_build(dest: Path, into_non_empty: bool) -> int:
    dest = dest.expanduser().resolve()

    # Never write inside this repository. A cut nested in its own source would be copied into the
    # next cut, and `git init` under a worktree is a trap of a different kind.
    if dest == REPO or REPO in dest.parents or dest in REPO.parents:
        print(f"refusing: {dest} is inside (or contains) {REPO}")
        return 1

    if dest.exists() and any(dest.iterdir()) and not into_non_empty:
        print(f"refusing: {dest} is not empty -- pass --into-non-empty to write into it anyway")
        return 1

    paths = tracked()

    # THE BYTES COME FROM `HEAD`, NOT FROM THE WORKTREE, and that is the whole argument of this
    # function. Copying the worktree publishes whatever happens to be half-edited on disk, and it
    # cannot run at all while any tracked file is deleted-but-uncommitted -- which in this
    # repository is the ordinary state, not an exception: six records are in flight as this is
    # written. A publishing tool that refuses whenever the author has uncommitted work is a tool
    # that never runs. `HEAD` is complete by construction, so there is no missing-file case to
    # guard, and what gets published is what was committed.
    blobs = head_blobs(paths)
    unreadable = [p for p in paths if p not in blobs]
    if unreadable:
        # Not reachable through ordinary use: every path came from `git ls-files`. It would mean
        # the index and HEAD disagree, which is worth failing on rather than papering over.
        print(f"{len(unreadable)} tracked path(s) are in the index but not in HEAD:")
        for path in unreadable[:20]:
            print(f"  {path}")
        print("The index and HEAD disagree. Commit or reset, then build again.")
        return 1

    dest.mkdir(parents=True, exist_ok=True)
    copied = 0
    for rel in paths:
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blobs[rel])  # bytes, not text -- see BYTES, NOT TEXT above
        copied += 1

    git("init", "-q", "-b", "main", cwd=dest)
    # Local config, three lines, each preventing a specific failure:
    #   * the author identity is set per-repository here (`git config --show-origin user.email`
    #     reports `file:.git/config`, not global), so a fresh `git init` elsewhere on this machine
    #     cannot commit at all -- "Author identity unknown", exit 128. Carry it across.
    #   * `autocrlf`/`safecrlf` off so the copied `.gitattributes` is the ONLY thing deciding line
    #     endings, and 1,400 "CRLF will be replaced by LF" warnings do not bury the report. The
    #     blob comparison below is what proves the endings landed right.
    for key in ("user.name", "user.email"):
        # `--get` exits 1 when the key is unset, so this one call cannot be `check=True`.
        probe = subprocess.run(
            ["git", "config", "--get", key], cwd=REPO, capture_output=True, text=True
        )
        value = probe.stdout.strip()
        if not value:
            print(f"refusing: this repository has no {key} to give the cut's single commit")
            return 1
        git("config", key, value, cwd=dest)
    git("config", "core.autocrlf", "false", cwd=dest)
    git("config", "core.safecrlf", "false", cwd=dest)
    # Stage by explicit path. `git add -A` would consult the copied `.gitignore`, which ignores
    # `data/fixtures/*.csv.gz` with two negations (D538) -- one mistake there and the cut silently
    # loses a file the source tracks. The list came from the index; it goes back in as itself.
    subprocess.run(
        ["git", "add", "--force", "--pathspec-from-file=-", "--pathspec-file-nul"],
        cwd=dest,
        input="\0".join(paths).encode(),
        check=True,
    )
    subprocess.run(["git", "commit", "-q", "-m", commit_message()], cwd=dest, check=True)

    # The projection is only faithful if the cut's index holds the same BLOBS as this one. Compare
    # ids rather than trusting the copy: a line-ending rewrite, a text-mode read or a truncated
    # write shows up here and nowhere else. `.gitattributes` travels with the tree, so `git add`
    # in the cut normalises exactly as it does here -- 3,000 of 3,016 ids matched on the first run
    # of this check, and the 16 that did not were all worktree modifications in flight.
    #
    # Which is the one difference that is legitimate, and it is NOT the one this block originally
    # named. The cut's bytes come from HEAD; `source` below is the INDEX. So a path can differ for
    # exactly one innocent reason -- it is staged and not yet committed -- and `git diff`, which
    # compares the worktree against the index, cannot name a single one of those. The first version
    # of this check used it anyway, which meant every staged change would have been reported as
    # differing "for no reason git can name" and failed the build: the identical failure class the
    # module docstring claims to have removed, reintroduced twenty lines from the claim. It has
    # never fired only because nothing was staged on the runs that exercised it.
    #
    # `git diff --cached` is the one that names index-vs-HEAD. An UNSTAGED edit is now correctly
    # invisible here: it leaves the index equal to HEAD, so the path never enters `differing` at
    # all, which is right -- a HEAD-sourced cut does not carry it and should not be asked to.
    def index_blobs(root: Path) -> dict[str, str]:
        out = git("ls-files", "-s", "-z", cwd=root)
        blobs = {}
        for entry in out.split("\0"):
            if not entry:
                continue
            meta, _, path = entry.partition("\t")
            blobs[path] = meta.split()[1]
        return blobs

    source, cut = index_blobs(REPO), index_blobs(dest)
    staged = {p for p in git("diff", "--cached", "--name-only", "-z").split("\0") if p}
    differing = sorted(p for p in cut if source.get(p) != cut[p])
    explained = [p for p in differing if p in staged]
    unexplained = [p for p in differing if p not in staged]
    # Files this build meant to carry that the cut's index does not hold. `git add --force` above
    # is what makes this normally empty; it stays as the check that the force actually took.
    only_here = sorted(set(paths) - set(cut))

    print(f"{copied:,} files -> {dest}")
    print(f"  index    {len(cut):,} files staged, one commit on `main`")
    print(f"  blobs    {len(cut) - len(differing):,} of {len(cut):,} identical to this index")
    if explained:
        print(f"  ahead    {len(explained)} are staged but not committed: {explained[:5]}")
    if unexplained:
        print(f"  DIFFER   {len(unexplained)} differ for no reason git can name: {unexplained[:10]}")
    if only_here:
        print(f"  DROPPED  {len(only_here)}: {only_here[:10]}")
    return 1 if unexplained or only_here else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--build", metavar="DEST", help="project the tree into DEST and commit once")
    ap.add_argument(
        "--into-non-empty",
        action="store_true",
        help="allow --build to write into a directory that already has files in it",
    )
    args = ap.parse_args()

    if args.status:
        return cmd_status()
    if args.build:
        return cmd_build(Path(args.build), args.into_non_empty)
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
