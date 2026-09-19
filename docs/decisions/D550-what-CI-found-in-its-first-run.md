# D550 — The first thing a machine that had never seen this repository said was that one of its gates was measuring the author's laptop

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Result
**Date:** 2026-09-19
**Category:** Infrastructure
**Source:** The first ever run of `.github/workflows/tests.yml`, on the push that published this
repository ([D549](D549-the-history-a-public-clone-receives.md)).

`tests.yml` opens by stating its own purpose: *"The project's governing claim is that trust is
enforced by structure rather than convention, and a suite that only ever runs on the author's
laptop is convention. This workflow is the structure."* **It ran once and found a gate that was
convention.**

---

## The run

| job | |
|---|---|
| golden masters | **12s** ✓ |
| lint and types | **19s** ✓ |
| docs and data integrity | **27s** ✓ |
| full suite | **3m 47s, exit 1** |

Reproduced from a clone of the published repository rather than read from the log:
**1 failed, 2,125 passed, 53 skipped.**

```
AssertionError: 1128 text-IO call(s) in scripts/ pass no encoding=, above the recorded
ceiling of 1126.
```

## The cause: the gate counted a worktree, and a worktree is not what a clone receives

`tests/unit/test_encoding_is_declared.py` listed the index with `git ls-files` and then **filtered
to the files present on disk**:

```python
return [REPO / rel for rel in listed if (REPO / rel).exists()]
```

The principal has two script deletions in flight — `scripts/d497_candidate_hurdle_p.py` and
`scripts/d498_worst_day_frequency.py`, deleted in the worktree and not staged. Both are in the
index. Both are absent from the author's disk. **Each carries exactly one undeclared call site**,
measured: 1 + 1 = 2, and 1126 + 2 = 1128.

So the ceiling recorded on 2026-09-18 was never a fact about this repository. It was a fact about
one working copy on one afternoon, and it would have been wrong on any clone, any collaborator's
machine, and the moment the principal staged or reverted those deletions.

**The filtering was a deliberate fix for a real crash.** D542's class scan died reading a path the
principal had deleted without staging, and skipping absent files stopped it. That is the right
instinct and the wrong instrument **for a counted ratchet**: skipping a file does not raise, it
silently changes the number. A crash is loud. A quiet decrement is what this repository spends
its effort on.

## The fix: count the index

`_index_sources()` now reads every tracked runner's content with one batched
`git cat-file --batch` over `:<path>` specs. No `.exists()`, no disk. The count is identical on
any machine at a given commit, which is the property a ratchet needs and this one never had.

A file whose deletion is actually **staged** leaves the index and the count falls — a ratchet
moving in its permitted direction, for a reason the author can see.

**`CEILING` 1126 → 1128 is a corrected measurement, not a concession.** No call site was added, no
runner was edited, and nothing regressed. The comment in the file says which of the two it is,
because a ratchet whose ceiling rises without explanation is indistinguishable from one that has
been quietly defeated.

After the fix, the author's machine reports **1,128 sites across 401 files** — the same as the
clone.

## D549's four predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | A clone is under 60 MiB and **contains no path listed in `data/data_manifest.json`** | **FALSIFIED as worded** — 46.65 MiB, but **two** manifest paths are present |
| **P2** | No file-size rejection, no secret-scanning block | **HOLDS** — largest object 14.93 MB, push accepted |
| **P3** | Roughly 2,125 passed, 53 skipped | **HOLDS exactly** |
| **P4** | No published number changes; the tree is byte-identical | **HOLDS** |

### P1 — wrong in the wording, right in the intent, and the wording is what a prediction is

The two paths are `crypto_universe_2015_2025_raw.csv.gz` and `crypto_daily_2015_2025_raw.csv.gz`
— the pair D538 deliberately returned to the index, which D549 names in its own text three
paragraphs above the prediction that says they are not there. I wrote *"no path listed in the
manifest"* when I meant *"no path the purge removed"*, and the verification printed
`manifest panels anywhere in the published history: 2` while I read it as confirmation.

Nothing is wrong with the repository. What is wrong is a prediction that a correct outcome
falsifies, which is the same defect as a test that passes for the wrong reason.

## P3 held exactly

Predicted: *"roughly **2,125 passed, 53 skipped** — this machine's 2,178 less the 53 that want a
manifested panel."*

Measured on a clone: **2,125 passed, 53 skipped.** Not approximately — exactly, on both figures.

That settles the thing D549 said was worth being wrong about: the skip count had **not** drifted
since it was measured on 2026-09-17, so `README.md`, `docs/RUNNING.md` and `docs/VERIFICATION.md`
are all right about it, together.

## The corrections this forces

| where | said | says |
|---|---|---|
| `tests/unit/test_encoding_is_declared.py` | `CEILING = 1126` | **1128**, with the reason |
| `docs/VERIFICATION.md:154` | 1,126 text-IO calls | **1,128** |
| `.github/workflows/tests.yml` | 399 of 601 runners | **401 of 603** |
| [D543's RESULT](D543-RESULT-the-third-count-prediction-and-the-third-miss.md) | 1,126, in three places | unchanged; **amended by addendum**, because a record says what was measured and this record says why it was wrong |
| [D549](D549-the-history-a-public-clone-receives.md) | "399 of 601", "the ratchet counts 1,126" | unchanged; **amended by addendum** |

## Two errors of mine on the way, both from trusting a page

**I reported that GitHub had scheduled no workflow run at all.** The Actions page showed *"0
workflow runs"* twice and I believed it twice. Run #1 existed the whole time, on the publishing
commit. **I then pushed a commit whose message asserts the false claim, and that push cancelled
run #1** — the workflow sets `cancel-in-progress: true` on `${{ github.workflow }}-${{ github.ref }}`,
so provoking a run destroyed the one already running.

The `workflow_dispatch` trigger that commit added is worth keeping; the reason it gives is not
true, and its comment is corrected here rather than left to contradict the Actions log.

**The lesson is the same one as the gate's.** A stale page and a filtered worktree are the same
failure: reading a convenient local copy instead of the thing itself.

## What this does not settle

**Two other gates share the shape and are not fixed.**
`tests/unit/test_tracked_json_parses.py` and
`tests/unit/test_nothing_outside_tests_is_collectable.py` both filter to files present on disk.
Neither is a counted ratchet, so the failure mode is *missing* something rather than mis-counting
it: an unparseable JSON or a collectable script that is in the index and deleted locally would go
unseen on the author's machine and be caught on CI. That is the safe direction, it is not the
right one, and it is named here rather than discovered later.

**Whether the two runners should simply be committed as deleted.** They are the principal's
in-flight state and have been left untouched through nine lanes and a publication; this record
does not touch them either. The gate no longer cares, which is the point.
