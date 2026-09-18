# D548 — Forty-two consecutive lines of the front page are about a checkout bug, and none of them is about the framework

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Pre-registered
**Date:** 2026-09-19
**Category:** Documentation
**Source:** The principal's decision on the one item
[D545's RESULT](D545-RESULT-the-page-exists-and-three-of-its-numbers-do-not.md) handed back.
Committed before the move (R8). Nothing admitted to either book; no holdout read; no runner
touched.

## The measurement, and the correction to it

[D545](D545-the-narrative-layer-over-D190-D544.md) answered a reviewer's claim that *"~70 of the
first 130 lines are meta-commentary on the README's own past errors"* by classifying them: over 109
content lines, **38** say what the framework is or does, **51** are measured claims about the
repository, and **20** are commentary on a past error — **18% strict self-correction, not 70
lines.** The reviewer's number was wrong by a factor of 3.5 and the record said so.

The sharper fact it found instead: **a run of 42 consecutive lines with no framework content at
all.** D545 reported it at lines 61–102 and declined to act, because *"restructuring the front page
on a reviewer's taste is a larger call than a documentation lane should take."*

**That range has since moved and this record corrects it.** A28 inserted the `CostStack` sample at
line 56, pushing everything below it down 25 lines. The run is now **86–127**, in three blocks:

| lines | what it is |
|---|---:|
| 86–92 | how long the suite takes on this laptop, and the two documents that once disagreed about it |
| 94–110 | cloning on Windows: the long-path abort that reported exit code 0, and `git clone` not copying local config |
| 112–127 | what the 53 skips want, `D536`/`D538` byte counts, and which of 118 panels carry a git blob id |

It sits **inside `## Five minutes`**, between the two commands a reader came for and *"Three ways
in"*. A reader asking *is this any good* gets `uv sync`, `uv run pytest -q tests/golden`, and then
42 lines about a checkout bug.

## What the audit found before moving anything

**`README.md:86` claims runtimes live "here and nowhere else (D544)". That is true, and narrower
than it reads.** `docs/VERIFICATION.md:188-190` already carries *"a clone runs 2,017 passed, 53
skipped"* — the same pass and skip counts the front page quotes at `:94`. Two documents, same
numbers, and **they agree**, because both are swept by
`tests/unit/test_quoted_counts_are_current.py`.

So the rule D544 wrote is about **wall-clock runtimes** specifically — the one class of number no
gate can hold, because it is a property of the machine and the moment rather than of the commit.
Pass counts and skip counts are gated and may live wherever they are useful. The distinction is
load-bearing for this move and the sentence will be rewritten to state it.

**`CONTRIBUTING.md:138`** is the only pointer at the front page for runtimes:
`# everything; for runtimes see README's "Five minutes"`. It follows.

## Decision

1. **`docs/RUNNING.md`** — a new document carrying all three blocks **verbatim**, under headings,
   with a short preamble saying what the page is for. Every figure moves byte-identical.
2. **`README.md`** loses lines 86–128 and gains a two-line pointer. `## Five minutes` goes from 52
   lines to about 12 and the front page ends the section where a reader would expect it to.
3. **The "nowhere else" sentence is amended, not dropped**, and moves with the runtimes to
   `docs/RUNNING.md` — still exactly one home, which is what D544's rule protects. It will say
   *runtimes* rather than implying every clone figure, because `docs/VERIFICATION.md` legitimately
   carries the gated ones.
4. **`CONTRIBUTING.md:138`'s pointer follows**, and `README.md`'s Doc suite gains a `docs/RUNNING.md`
   line under **Live**.

**Nothing is deleted and no number is edited.** `docs/RUNNING.md` is not in the counts gate's
`FROZEN` set, so every figure that moves stays swept — which is the half of this that a
restructuring usually gets wrong.

## Predictions

| # | Prediction | Confidence |
|---|---|---|
| **P1** | **No published number changes.** Every figure in the 42 lines lands in `docs/RUNNING.md` byte-identical; the counts gate stays green without any number being edited. | High |
| **P2** | `check_doc_links.py` reports **one more document** and **0 unresolved** — the new page's own outbound links and the two new inbound pointers all resolve. | High |
| **P3** | Perturbing one figure in `docs/RUNNING.md` reddens `test_quoted_counts_are_current`, naming **`docs/RUNNING.md`** and not `README.md` — proving the numbers kept their gate by moving rather than losing it. | High |
| **P4** | The front page's longest run of consecutive lines with no framework content falls **below 20**. Measured after, by the same hand classification D545 used, and reported whether or not it holds. | Medium |

**P4 is the one that can embarrass this record.** The 42-line run is being removed by moving it;
if what remains still has a long run, then the problem was never that one block and the
restructuring bought less than it looked like. That is worth finding out, and it is why the
prediction is on the *residual* rather than on the block being moved.

## What is deliberately not done

**No prose is rewritten and no claim is softened.** This is a move, and the argument for it is
placement rather than content. Every sentence in those 42 lines earned its place in a record —
D536, D538, D540, D544 — and the front page is simply not where a reader meets them.

**The 51 measured-claim lines stay.** They are what the page is *for*; D545's classification found
them to be the bulk of it and that is the intended shape. Only the run with no framework content
moves.

## What this record does not settle

Whether `docs/RUNNING.md` is the right name or the right home — `CONTRIBUTING.md` and
`docs/VERIFICATION.md` were both candidates. It is its own page because it is written for someone
running the suite for the first time, which is neither of those audiences: `CONTRIBUTING.md` is for
someone changing the framework and `docs/VERIFICATION.md` is for someone asking what the tests
prove.
