# D539 — The public repository is a generated cut of this tree with fresh history, and nothing in it is redacted

**Status:** Committed
**Date:** 2026-09-17
**Category:** Data layer
**Source:** Portfolio repack session, round eight. Executes the successor
[D536](D536-manifest-only-storage-for-the-bulk-panels.md) named and declined to build — *"the
clone-size problem gets a different answer (a curated public repository); it is not this decision's
to solve."* Discharges `working/PORTFOLIO_PLAN.md` §10 items 2 and 10.

## Decision

**The public repository is `scripts/build_public_cut.py --build`: every path in `git ls-files`,
with the bytes taken from `HEAD`, projected into a fresh directory and committed once.**

**Nothing is redacted and nothing is excluded.** `docs/BOOK.md`, `docs/BOOK_PROP.md`,
`docs/COMPONENTS_PROP.md`, the 26 prop-firm research documents, `working/`, `docs/internal/`,
`.claude/`, every negative result and every superseded record all go. The only difference between
the two repositories is that the public one starts at commit one.

**This repository keeps its history, unrewritten.** No `filter-repo`, no rebase, no squash.

## Rationale

**Why a second repository rather than a rewrite of this one.** D536 (`:80-92`) made the mechanical
argument and it still holds, verified today: the manifest's `git_blob` field points at bytes that
are only still reachable because history was left alone, and **113 of 113 pointers resolve with
exact byte counts, 837.5 MiB recoverable**. A `filter-repo` pass would dangle every one of them —
"it would convert a recoverable repack into a deletion". Publishing a second repository gets the
clone size without spending that.

**Why the size problem is real, in one number.** `data/**` blobs are **98.46% of the 940 MiB
pack**. Everything else — all source, docs, tests, scripts, and every commit and tree object across
1,392 commits — is **14.5 MB**. So dropping history costs the reader nothing they would have read
and saves almost all of the weight: measured, **42 MB against 965 MB, a 23× reduction**.

**Why nothing is redacted, which was the principal's call and is the interesting half.** The books
are the exhibit, not the secret. A book with two entries, an empty prop book, and a written
standard that keeps it empty is the evidence that the instrument gets used honestly; `CLAUDE.md`
already says an empty book with stated standards beats a populated one with borrowed ones. The
research lanes are how the work was actually done. Redacting them would have produced a repository
that argues for rigour while hiding the parts where rigour was exercised.

**What was found instead of a redaction problem.** A full-content scan of **4,847 distinct blobs
across all of history** found **zero credentials** — no `.env`, no key, no vendor token, ever. The
key has lived outside the repository since the beginning. The real exposures were mundane and are
fixed rather than hidden: ten scripts that only ran on one machine, a hook that printed the
author's home directory into a cloner's session, and an MIT grant that covered 595,000 characters
of other people's writing ([NOTICE](../../NOTICE), added in the same round).

**Why the bytes come from `HEAD` and not from the worktree.** The first implementation copied files
off disk and refused when any tracked file was deleted-but-uncommitted. Correct in principle,
unusable in practice: that is this repository's ordinary state — six records were in exactly that
condition while the script was written — so the tool would have refused essentially always. Reading
`HEAD` removes the failure rather than guarding it, and it fixes a second defect nobody had named:
copying the worktree would publish whatever happened to be half-edited at build time. A public
repository is a statement about a committed state.

**Why generated rather than forked.** A hand-maintained public fork drifts, and the drift is
invisible until a reader finds it. The cut is rebuilt from `HEAD` on demand, checks itself blob id
against blob id, and its gates are run *inside it* — the full suite, the link checker, the counts
block, the figures and the manifest verify. That is D536's manifest pattern applied to publication.

## Consequences

- **The private repository is unchanged.** Same history, same 1,392 commits, same recovery
  pointers. Nothing about this decision touches it.
- **The public repository has no history**, and its single commit says so — what it was cut from,
  how many commits, what span, and that the full history is retained privately. §9's constraint is
  that curation is allowed and revision is not; a reader is told which this is.
- **The recovery path does not travel.** `git cat-file blob <id>` works in this repository and not
  in the cut. The manifest's `sha256` still identifies every panel, and `--verify` in the cut
  reports 116 missing and 0 changed, which is the honest state.
- **Publishing is still a manual act.** `gh` is not installed and no remote is configured; the cut
  is produced and verified here, and pushing it is the principal's to do.
- **This is not a licence to fork.** One generated cut, rebuilt from `HEAD`. A second long-lived
  public branch would be the drift this decision exists to avoid.
