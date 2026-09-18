# D546 — Two holes this programme found, wrote down, and did not close: a script pytest will import and a tracked JSON that has never parsed

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Infrastructure
**Source:** Neither review. Both items were found *by* the nine-lane remediation programme
(`working/REVIEW_REMEDIATION_PLAN.md`) and recorded rather than fixed. Committed before the gates
exist (R8). Nothing admitted to either book; no holdout read.

## The two holes, in the repository's own words

**1. A gate this repository has already said should exist.**
`docs/decisions/D542-RESULT-two-predictions-falsified-and-a-verdict-that-flipped.md:201` reads:

> **A tracked JSON that does not parse should fail a test**, and none does.

That sentence has sat in a committed record since Lane 6, describing a hole nobody dug and nobody
filled. The two files that prompted it — `data/D3_wb_2018.json` and `data/D3_wb_2019.json`, 117
bytes each of `<html><body><h1>429 Too Many Requests</h1>` — were handed to the principal rather
than deleted, because `data/` is evidence and retirement is written. **Handing over the files was
right and it is not the same act as closing the class.**

**2. A trap I walked into myself and filed as a task chip.** Running pytest against
`data/A4-filing-text/A4_header_test.py` during Lane 8's census dropped a stray
`A4_header_rows.json` into the working directory. The chip described one file.

## What the re-measurement found — it is seven files, not one

`git ls-files "*.py"` filtered to pytest's **default** `python_files` patterns
(`test_*.py`, `*_test.py`), excluding `tests/`:

```
data/A4-filing-text/A4_header_test.py
scripts/d273_halt_test.py
scripts/d290_entry_test.py
scripts/d290_skip_bar_test.py
scripts/run_holdout_test.py
scripts/run_withheld_test.py
working/d528_a2_test.py
```

**All seven match on the `*_test.py` suffix.** And on the other side of the ledger: **158** tracked
test files under `tests/`, **every one** named `test_*.py`, **zero** named `*_test.py`. The second
default pattern earns this repository nothing and reaches into three directories that hold no
tests.

**Only one of the seven is live, and the distinction matters.**
`data/A4-filing-text/A4_header_test.py` executes at import — module-level SEC fetches, and at
`:97`:

```python
json.dump(rows, open("A4_header_rows.json", "w"), indent=1)
```

A **relative** path, so the file lands wherever pytest was invoked. The other six are
`__main__`-guarded and their only module-level call is `sys.path.insert`; importing them is inert.
The class is what is being closed here, not the instance, and the record says which is which
rather than flattening them into one alarming number.

**And the default run was never exposed.** `pyproject.toml:43` sets `testpaths = ["tests"]`, so
`uv run pytest` collects only `tests/`. Firing the trap needs an explicit path or a repo-wide
collection — which is exactly what I did. Overstating the blast radius here would be the same fault
this programme spent nine lanes finding in the reviews.

## Decision

**1. `pyproject.toml` — narrow `python_files` to `["test_*.py"]`.** One line, all seven files out
of pytest's reach, and nothing lost: no tracked test is named `*_test.py`.

**Not a rename**, which was the chip's implied fix. `A4_header_test.py` is cited by name at
`docs/research/Scan-100926/R1-04-filing-text-at-scale.md:645` — *"[MEASURED IN BRIEF,
`A4_header_test.py`]"* — and `data/` is evidence, the same reason D542 handed the 429 pages over.
The config change touches no evidence and covers six files a rename would not.

**2. `tests/unit/test_nothing_outside_tests_is_collectable.py`** — the config line is not a gate,
it is a setting, and a setting can be deleted by anyone who does not know what it was for. The gate
**reads `python_files` back out of `pyproject.toml`** with `tomllib` rather than hard-coding it,
because a gate that restates its subject is a second copy, and two copies of the same fact drifting
apart is what `README.md` names as this project's most repeated defect.

It asserts, in this order: the key is **present** (its absence silently restores pytest's defaults,
which is the whole regression); at least **150** files under `tests/` match it (a pattern list that
matches nothing satisfies "no offenders" perfectly — the empty-scan defect closed six times in this
programme); and **no tracked `.py` outside `tests/`** matches, filtered to files present on disk,
because `git ls-files` reports the *index* and the principal routinely has deletions in flight.

**3. `tests/unit/test_tracked_json_parses.py`** — the gate D542 named. **813** tracked JSON files
present, **2** unparseable, both the 429 pages. The allow-list carries those two with their reason,
and is **re-derived rather than trusted**: each allowed path must still exist *and* still fail to
parse. A stale exception that outlives its subject grants amnesty to a path that no longer needs
it, and nothing would ever say so.

The two files stay exactly where D542 put them — visible, named, the principal's to retire.

## Predictions

**No count is predicted.** Five attempts across this programme, four misses; D543's RESULT wrote
the rule and D544 broke it in the sentence quoting it. Behaviour only.

| # | Prediction | Confidence |
|---|---|---|
| **P1** | **No published number moves.** No runner is touched, no artifact regenerated, no record retired. | High |
| **P2** | Deleting `python_files` from `pyproject.toml` reddens the new gate **by the missing-key assertion**, naming it — not by the floor and not by the offender list. | High |
| **P3** | Emptying the pattern list to `[]` reddens it **on the floor**, not on the offender assertion. The offender assertion would pass — that is the point of having a floor, and the two failure modes must be distinguishable in the message. | High |
| **P4** | Restoring either `D3_wb` file to valid JSON reddens the **allow-list re-derivation**, not the scan. | High |
| **P5** | `uv run pytest data/A4-filing-text/A4_header_test.py` collects **0 items**, writes no file, and makes no network request. | High |

**P5 is asserted on collection only.** Proving it by *running* the script would defeat its own
proof and hit SEC; the claim is that pytest no longer imports it, not anything about what it does
when someone runs it deliberately. That remains true and is recorded as still open.

P2 and P3 are the sharp pair: they name two different failures of the same gate and predict which
assertion catches each. A gate whose failures are indistinguishable is a gate that tells you
something broke and not what.

## What is deliberately not done

**Nothing in `data/` is deleted, renamed or edited.** The two 429 pages, `terrain_swing_decay.py`'s
retirement and `A4_header_test.py`'s filename are the principal's three open dispositions. They are
recorded as open in the plan's §14 rather than closed by an assistant — and §1 here neutralises the
*collection* hazard without touching the file, which is the most an assistant should do to evidence.

**The README front page is not reordered.** D545 measured it — 38 lines of what the framework is,
51 measured claims, **20 of past-error commentary (18%)** against a reviewer's claimed ~70 — and
the sharper fact, **42 consecutive lines (61–102) with no framework content**. The principal's
answer this session was to record it as open and decide later. It is now carried in the plan rather
than only in D545's closing paragraph.

## What this record does not settle

Whether `A4_header_test.py`'s relative-path write should be fixed at the source. Making it
absolute would be a one-line improvement to a file in `data/`, and this repository's rule is that a
file a record quotes is evidence. Pytest can no longer reach it; a human who runs it still can, and
that is a disposition, not a defect to be patched quietly.

Whether the JSON gate should extend to the other structured formats in `data/` — `.csv.gz`,
`.parquet`, `.jsonl`. JSON is where the known failure is and where parsing is free. A parquet
census would need the reader and the memory, and a gate that is slow enough to be skipped is worse
than one that is narrow.
