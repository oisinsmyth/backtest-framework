# D299 FIRST AMENDMENT — stage two is deferred, and the fork leaves the record

**Status:** AMENDMENT to `D299-the-ladder-and-a-null-suite-that-decomposes-it.md`
(pre-registered at `45e61c7`). Made **before the runner exists**. No result has
been seen. Nothing here is a result.
**Date:** 2026-09-03

---

## The measurement first, because the premise was mine and it was loose

D299 §3.2 described ~16,000 draws as though it were the constraint. It is not.

**D298 measured: 3,200 composite draws, 4 processes, 761 s — 4.2 draws/s.**

| | draws | at 4 shards | at 8 shards |
|---|--:|--:|--:|
| D299 as written | 16,000 | ~64 min | **~32 min** |
| dropping N1/N3/N5 entirely | 14,800 | ~59 min | ~30 min |
| **stage 1 only (this amendment)** | **11,200** | ~45 min | **~23 min** |

**D298 used 4 shards of 16 available cores**, so half the machine was idle. The
run was never the problem.

**And dropping N1/N3/N5 saves 7.5% — about three minutes.** They were already
restricted to two cells. The cost sits entirely in N2 and N4 across the grid, so
that is the only place a cut can come from.

## What changes

**Stage 2 is removed from this study.** Its 12 cells — `C_up` × drop-choice ×
`k` — become a separate pre-registration, run on D299's shortlist.

**The reason is the fork, not the clock.** D299 §2 named stage 2 as conditioning
on stage 1's winner and asked the reader to accept it. Deferring it means the
study no longer contains a results-conditional arm at all: **25 declared cells,
no fork, multiplicity counted over 25.** That is a better record than the one it
replaces, and the compute saving is incidental.

It also stops the study committing to `C_up`, drop-choice and `k` before knowing
whether the family clears Q8 at all.

## What does NOT change

**N2 and N4 both run on all 25 cells.** This is the cut that was proposed and it
is declined, with the reason on the record:

**shortlisting on N2 and then running N4 only on the survivors conditions the
selection test on the timing test.** The decomposition in §3.1 —
`treat − N2` against `treat − N4` — would then be computed on a subset already
selected for winning on timing, which biases the exact quantity the null suite
exists to measure. The suite's whole purpose is separating the two mechanisms;
sampling one conditional on the other defeats it.

**N1, N3 and N5 stay**, on the fixed declared reference cell and on stage 1's
winner. At 1,200 draws they are 11% of the reduced run, and N1 in particular
earns its place by *pricing* the invalid control rather than leaving CLAUDE.md's
warning about it as an assertion.

**Draws stay at 200.** If the run needs to be shorter still, the declared lever
is **100 draws for the screen, then 1,000 on the cells that survive** — BH at
q = 0.10 does not need finer than 0.01 resolution, and this halves the run
without touching the design's logic. That lever is recorded here so it can be
pulled without a further amendment; it has not been pulled.

## The grid, restated

**Stage 1, and it is now the whole study:** `C_up = 5`, drop by `z`, `k = 5`.
8 trigger combinations (`T_b` × `S_b`, 3×3 minus off/off) × 3 depths
(`N_min` ∈ {17, 13, 10}) + 1 control = **25 declared cells**.

**Nulls:** N2 and N4 on all 25 at 200 draws (10,000); N1, N3 and N5 on two cells
at 200 draws (1,200). **11,200 total.**

**Multiplicity:** BH-FDR at q = 0.10 across 25, and a grid-max null over 25
reported beside the winner without gating it. Per cell, beating its own null
remains the bar.

Everything else in D299 — the statistic, the shadow, the rules, the quantile
thresholds, the seven assertions and the eight predictions — is unchanged.

## Speed

**8 shards, not 4.** Processes over strided cell indices, GIL-bound pure Python,
per CLAUDE.md. Stride, don't slice, and prove the chunk equals the whole
bit-identically before trusting it.
