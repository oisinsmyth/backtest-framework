# D552 — The purge and the recovery path were mutually exclusive, and three documents kept promising the one the purge removed

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result
**Date:** 2026-09-19
**Category:** Documentation
**Source:** Garbage-collecting after the worktree cleanup, which swept the last unreachable copies
and made the state visible.

**113 of the manifest's 115 git blob ids are dangling. Three documents describe them as a recovery
path. They have been dangling since publication, and the two facts were decided in the same
record without either noticing the other.**

---

## What is true

[`data/data_manifest.json`](../../data/data_manifest.json) carries, for each of 118 bulk panels, a
sha256 and — for 115 of them — the git blob id the panel had while it was tracked. D536 made that
blob id *"the load-bearing field"*, and it was: a blob id is exact, and a provider's checksum is a
promise about a file you have not got yet.

[D549](D549-the-history-a-public-clone-receives.md) then purged those blobs, because they **are**
the CME- and Alpha-Vantage-derived panels this repository is not entitled to redistribute. It
verified the tree hash, the commit count, the clone size and the absence of every purged path, and
never asked what else pointed at the objects it was removing.

| | |
|---|---:|
| manifest panels with a blob id | **115** |
| resolvable in the published repository | **2** |
| dangling | **113** |

The two that resolve are the Binance panels D538 returned to the index, which were never purged.

## Why it stayed invisible for a day

Immediately after the rewrite, **70 of the 115 still resolved locally** — they were unreachable
objects pinned by a stale worktree's index, which is exactly the 650 MB the cleanup then
reclaimed. So the author's machine reported a number that was neither the truth before nor the
truth after, and a spot check would have found the blob it looked for.

A clone never had them. **The claim has been false since the first push**, and the only reason
anyone measured it was that garbage collection finally made the local repository agree with what
everyone else receives. Third time in three days that the author's machine was the thing being
measured: [D550](D550-what-CI-found-in-its-first-run.md) counted a worktree,
[D551](D551-a-snapshot-id-that-depended-on-the-os.md) counted an operating system, and this
counted objects nobody could reach.

## The part that is not a bug

**The recovery path and the licence purge cannot both exist.** Those blobs are the vendor data.
Restoring them to the published history would undo the reason the history was rewritten. There is
no fix in which a public clone recovers a Databento-derived panel from this repository's objects.

So D549 did not break something that should be repaired — it made a trade, correctly, and then
three documents went on describing the side it had given up. **The defect is the description, not
the decision.**

## What the documents said, and now say

| | said | says |
|---|---|---|
| `docs/RUNNING.md` | *"Every panel a skipped test names does have a blob id, which is what makes the skip **recoverable** rather than merely explained."* | the ids record the pre-publication history, 113 of 115 dangle in any clone, restoring them would undo the licence fix, and the **sha256** is the field that still works |
| `docs/data-available.md` | *"the git blob id of the ones **recoverable from history**"* | the id each panel carried *before publication*; the sha256 is the usable field |
| `CONTRIBUTING.md` | *"its sha256 and the git blob id it had when it was tracked"* | accurate as far as it went, and it now says the id **no longer resolves** |

`CONTRIBUTING.md` is the interesting one: its sentence was **literally true** — the id is what the
panel *had* when it was tracked — and a reader would still have drawn the wrong conclusion. A
sentence can be true and load-bearing in the wrong direction.

**Recovery still exists, for exactly one person.** The pre-publication history survives in the
mirror backup taken before the rewrite. It holds every vendor panel, which is why it must never be
pushed anywhere. That is the principal's copy and nobody else's, and saying so is more honest than
a blob id that looks like it would work.

## What this does not settle

**Whether `data_manifest.json` should keep the field.** It is now a record of what was, not a
handle on what is. Dropping it would be tidier and would lose the only statement of what the
pre-publication objects were; keeping it needs the documents to say what it is for, which is what
this record has just made them do. The builder is `scripts/build_data_manifest.py` and its
`git_blobs()` still records live ids, so a panel re-tracked in future gets a working one.

**Nothing gates a claim like this.** [D548](D548-RESULT-none-of-the-figures-had-a-gate.md) measured
that the counts sweep only checks numbers it can recompute; *"this identifier makes the panel
recoverable"* is not a number, and no test in this repository can read a sentence and check
whether it is still true. Three documents asserted a broken recovery path for a day and the suite
stayed green throughout. That is the honest limit of the instrument.
