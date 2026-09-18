# D545 — The narrative layer the README has been conceding for 355 decisions, and the directory that would not have gated it

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Documentation
**Source:** Lane 9 of the two-reviewer audit (`working/REVIEW_REMEDIATION_PLAN.md` §10, items A7
and A28). Committed before the page exists (R8).

## The problem, in the README's own words

`README.md:171-172` says: *"there is no narrative layer over the last 350 decisions yet."*

Both documents a reader is sent to disclaim themselves. `docs/writeup.md:3-4` is headed
`Status: DRAFT (skeleton — all numbers final, prose marked [TODO prose] where narrative polish is
pending) · 2026-07-14` and carries five real `[TODO prose:` markers.
`docs/results/final_report.html:355` states on its face: *"This report is dated. It covers
D169–D189."*

So 355 decisions of research — `docs/FINDINGS.md` is 4,700 lines — are reachable only by reading
753 records. **A reviewer will not.** The candour is creditable and is not a substitute.

## The directive, and the risk it carries

**Audience: a quant reader assessing the research** (principal, this session) — organised by what
was learned about markets, not by what the instrument caught. **Every quoted number gated.**

The framing invites *"so what did you make?"*, and the honest answer is **nothing is at capital and
the prop book holds one arm**. The page says that in its opening rather than its footer. A reader
who reaches the end and only then learns nothing booked has been managed.

## What the survey found, and why it changes where the page goes

**Every `.md` in `docs/results/` is emitted by a script.** Every filename appears as a hardcoded
output path in a `scripts/*.py` runner — including the ones the index calls hand-written, whose
prose lives *inside* the runner (`scripts/run_vol_estimator_gate.py:111` writes
`w("# Does finer data give a better estimate? ...")`).

So `docs/results/README.md:36-40` describes its own naming convention wrongly:

> **`lower_snake_case.md`** — hand-written analysis pages. A human decided what to say.

A human decided what to say, and said it in a runner. **The real invariant is that a file in
`docs/results/` is the output of a script and editing it in place is undone by the next run.**
That sentence is corrected here.

**This matters because of what it exempts.** `tests/unit/test_quoted_counts_are_current.py:53`
lists `docs/results/` as FROZEN with the reason *"study ledgers emitted by a runner; regenerating
the study rewrites them"*. A hand-written page dropped there would inherit a no-gate exemption
written for files a runner owns: **nothing would ever check its numbers, and nothing would ever
rewrite them either.**

**The page still goes there, and the precedent is exact.**
`docs/results/final_report.html` is the **one genuinely hand-written document in the directory** —
no script writes it; two scripts and two tests *read* it, and `scripts/figures/svgkit.py:71` makes
it the single source of the colour tokens for all twelve SVG figures. It is the narrative of phase
one. The new page is its successor for D190–D544 and belongs beside it — **with its own gate,
because the exemption it would otherwise inherit was written for something else.**

## Two things the survey corrected before a word was written

**1. This record's own first draft mis-attributed a theorem.** It credited D373 with *"a sample p95
is biased toward the centre, so a finite-draw null is more lenient than it looks."* **That is
C2b's theorem, not D373's.** D373's pre-registered rule is narrower and different: every reported
p95 carries its bootstrap SE, and a hurdle whose margin falls within **2 SE** of its bar is recorded
**UNRESOLVED**, never passed (`D373-the-winners-dip-long-and-the-median-criterion.md:157`, `:184`).
C2b names D373 as the precedent that exists and *"is simply not universal"*. The repository
distinguishes them deliberately and the page will too.

**2. Three of the numbers this lane set out to quote cannot be sourced — and that is the finding.**
D466's **0.62 / 0.42 / 0.91** have **no committed artifact**. They came from an ad-hoc shell line;
`CLAUDE.md`, the memory file and D466 §0 were all written on them; and their only source is the
record's own confession. Only the corrected **0.37 / −0.01** exist in `data/d466_components.json`.
**Under this record's gating rule those three figures fail**, which is exactly the point: a number
that never passed through the runner cannot be sourced. The page quotes them as *withdrawn*, beside
the artifact-backed pair that replaced them.

## Decision

1. **`docs/results/D190-D544.md`** — ~1,200 words, six findings, each with its numbers, its null
   and what it cost. A finding goes on the page only if its figures trace to a committed artifact
   or a record `path:line`, **and only if it is closed**. Anything failing either test is cut and
   named in the RESULT.

   **Three findings about trading, three about whether to believe them** — which is the honest
   shape for a quant reader, because the strongest verified material in 355 decisions is about
   measurement:

   | | |
   |---|---|
   | **D373 / D376 / D377** | a +160.55 bp-per-trade book was ~80% momentum-decile exposure; two books sharing *nothing but cohort membership* correlate at **ρ = +0.923**, and the entire margin over the cohort-matched control was **one GME trade** worth 6.34% of the ledger |
   | **D340** | the same-close fill was **three quarters** of the best book — the overnight gap it credited to every entry (+44.8 bp long, +27.2 short) was larger than the published half-spread |
   | **D466 / D493** | the fee and the trailing drawdown are one constraint: the micro sits **forty σ** from the barrier and loses on the fee, the full contract sits **three to six σ** away and dies in weeks — **0 of 448 cells** carry |
   | **D279** | ~**93%** of an apparent edge was a one-bar lag bug in a *filter*, above the correctly-lagged book every guard points at |
   | **C2b** | enumerating a finite rotation group instead of sampling it: **4 of 4** published p95s were too low, and the one cell whose margin was thin fell from **+6.4 to +0.52** |
   | **D370 / D369** | precision cannot detect bias — a 10,000-draw verdict at **−15.8 SE** reversed to **+10.3 SE** when the null was made symmetric |
2. **A dedicated anchor gate**, following `tests/unit/test_writeup.py`'s `ANCHORS` pattern —
   `(number, source)` pairs asserted present in **both** the prose and its source, with
   `_normalized()` folding the Unicode minus. Anchored to committed `data/*.json` where one exists
   rather than to another prose document.
3. **A floor on the anchor count, in the new gate and in `test_writeup.py`.** That file's
   parametrized gate has none: emptying `ANCHORS` collects nothing and fails nothing. It is the
   empty-scan defect this programme has now closed in five other places, sitting in the gate that
   exists to keep a document honest.
4. **The README gets its first line of Python** (A28): a `CostStack` assembled from three bricks at
   their three scopes, **executed** by pointing the existing tutorial extractor at a second file
   rather than by pasting a copy — because a pasted copy is the exact failure `README.md:175` names
   as *"the most repeated defect in this project's own history (D176, D183, D186)"*.
5. **`docs/results/README.md:36-40`'s convention description is corrected**, and its ungated "62
   documents" / "All 62" counts are updated.

## Predictions

**No count is predicted.** Four attempts in this programme, four misses — B26 (272 → 284, predicted
278), D542's P6 (+4, predicted +1), D543's P5 (+0 on two components), D544's P2 (coverage lower,
not higher). D543's RESULT recorded the usable rule — *do not predict a count until the artifact
that moves it exists* — and D544 then broke it in the sentence that quoted it. This record predicts
**behaviour**.

| # | Prediction | Confidence |
|---|---|---|
| **P1** | **No published number moves.** The page quotes existing figures; the gate is what turns that from an intention into a check. | High |
| **P2** | The anchor gate **fails on a single perturbed digit** in the page, naming the anchor — demonstrated before the gate is trusted. | High |
| **P3** | With the floor added, emptying `ANCHORS` in `test_writeup.py` **fails**. The first half was measured before this record was committed rather than predicted: emptying it today takes the file from **29 passed to "3 passed, 1 skipped", exit code 0** — the 26 anchor checks vanish and nothing goes red. | High |
| **P4** | At least one candidate finding is **cut for being untraceable or still open**, and is named in the RESULT. A survey of 355 decisions that yields a clean sweep would mean the selection was not strict. | Medium |
| **P5** | The README code sample **executes** under the extended tutorial executor, and `IBKRCommission().trade_cost(Equity("ACME"), 100, 50.0)` returns **exactly 1.00** — the $1 minimum binding rather than the per-share rate. | High |

P3 and P5 are the sharp ones: each names a specific observable before it is looked at.

## What is deliberately not done

**The README is not reordered.** A28's second half claims ~70 of the first 130 lines are
commentary on the README's own past errors. Classified line by line over 109 content lines: **38
what the framework is or does, 51 measured claims, 20 past-error commentary** — so strict
self-correction is **18%, not 70 lines**. The sharper fact is that **lines 61–102 are 42
consecutive lines with no framework content at all** — laptop runtimes, a Windows long-path
checkout bug, `git clone` not copying local config. A reader asking "is this any good" spends 42
lines on a checkout bug.

That is real, and this repository's voice *is* self-correction. **Restructuring the front page on a
reviewer's taste is a larger call than a documentation lane should take.** The measurement is
recorded here; the principal decides.

**`docs/writeup.md` is not touched.** It is a dated draft about the ETF pairs studies; the new page
is about D190–D544. Two documents, two subjects — and the README already records why a second copy
of the same prose is this project's most repeated defect.

**Nothing in `final_report.html` is edited.** It is hand-written, dated on its face, and its
`:root` block is the token source for all twelve figures.

## What this record does not settle

Whether `docs/FINDINGS.md` is the better home. It is not FROZEN in the counts gate, so numbers
placed there **are** swept and kept current — a real advantage this record gives up in exchange for
sitting beside `final_report.html`, which is where the README's own spine points a reader. The
dedicated gate is what closes that gap, and it is a narrower instrument than the sweep.
