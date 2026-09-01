# D270 — Volume structure, retested under a control that can fail

**Status:** **RUN AND CLOSED.** Stage 1 passes emphatically; stage 2 fails. Volume is **independent but uninformative**.

**Everything above the RESULT heading was committed in `4e186ce`, BEFORE the retest was written.**
**Date:** 2026-09-01
**Area:** Strategy research · **personal track**

---

## Why this exists

[D269](D269-volume-structure-as-the-third-input.md) was **voided by its own control**, exactly as
registered. The diagnosis afterwards showed **the control was mis-specified, not the method**:

- `signed_vol = rel_vol × sign(return)` correlates **+0.013 with `rel_vol` itself** — multiplying by
  a symmetric ±1 sends high values to *both* ends of the ordering, so the product decorrelates from
  **both** parents.
- And a sign could never have reached the 0.5 bar regardless: `sign_only` on its own reaches only
  **+0.279** against `trailing_return`, because a sign discards magnitude and rank correlation is
  mostly magnitude.

**A control that cannot reach its own threshold in pure form cannot test anything.**

**D269's stage-2 reading is not recovered by that diagnosis and is not being recovered here.** "The
control was silly, so use the result anyway" is the move this programme's stops exist to prevent.
The retest is a fresh registration and the whole thing is re-run.

---

## What changes, and it is only the controls

**The five volume scores, the bar-of-day normalisation, the 20-session trailing window, the
horizon `H = 8`, and every hurdle threshold are UNCHANGED from D269.** Nothing about the
measurement is being tuned after seeing it — the numbers are deterministic and will reproduce.

`signed_vol` is **removed as a control** and is not replaced by another price-contaminated product.
In its place, **two synthetic controls that bracket the test from both sides**:

| control | construction | **required outcome** |
|---|---|---|
| **`ctrl_blend`** *(positive)* | `0.5 × rank(rel_vol) + 0.5 × rank(trailing_return)` — a literal 50/50 blend of a volume score and a price score | **MUST FAIL V1b.** It is half a price score by construction; if it reads as orthogonal, correlation cannot detect contamination here and the run is void |
| **`ctrl_noise`** *(negative)* | a seeded uniform random score, seed 0, independent of everything | **MUST PASS V1b.** If a pure random series reads as *correlated*, the instrument is broken and the run is void |

**Two-sided, so the instrument has to be right in both directions rather than merely permissive.**
D269's control tested only one side, and it was the side that could be passed for a reason unrelated
to the hypothesis.

**Neither control is a volume score and neither is eligible to pass the study.** They are
instrumentation.

---

## Hurdles — unchanged from D269

**Stage 1.** **V1a:** effective independent scores rises from 2.87 to **≥ 3.5**. **V1b:** at least
one *real* volume score has `max abs(rho) < 0.5` against all nine price scores. Both.

**Stage 2.** Only V1b passers proceed, against D267's **M1** (monotone quintiles), **M2** (extreme
quintile ≥ `2c`) and **M3** (best-of-N shuffle floor, one shared draw), at `H = 8`.

**Void conditions, both:** `ctrl_blend` passing V1b, or `ctrl_noise` failing it.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **W-a** | **Both controls behave** — `ctrl_blend` fails V1b, `ctrl_noise` passes | **high** |
| **W-b** | **At least one real volume score clears V1b**, and the effective count rises above 3.5. D269's voided run showed `rel_vol` at 0.09 and `dollar_vol` at 0.01, and the run is deterministic, so this is close to a formality — **stated anyway, because a prediction that is nearly certain still has to be written down before it is confirmed** | **high** |
| **W-c** | **No volume score clears M1–M3.** This is D269's V-b unchanged and it is the substantive question: FINDINGS §8 already closes the volume regime gate (D226), and D267 found the achievable dispersion bounded below cost for **every** price score | **moderate-high** |

**W-c is the one that matters.** W-a and W-b are instrument checks; W-c is the market question.

---

## Stop

**If V1 fails, volume is closed as the third input** and the consensus proposal closes with it.

**If V1 passes and V2 fails — the outcome W-c predicts — then volume is INDEPENDENT BUT
UNINFORMATIVE at this horizon**, and that is the reportable finding: a consensus rule could carry
volume for genuine diversification while expecting no edge from it, and D267's cost arithmetic says
diversification alone does not pay a round trip.

**No sixth volume score, no second normalisation window, no per-stratum retry, under any outcome.**

---

## Ledger

| count | N |
|---|---:|
| fresh — 5 volume scores × 3 strata | **15** |
| carried from D267 | 46,194 |
| **total** | **46,209** |

**D269's voided run adds nothing**, because no stage-2 cell was read from it. The 15 are counted
once, here.

---

## RESULT — volume is genuinely orthogonal, and it still does not pay

`uv run python scripts/run_volume_structure.py` · `data/d270_volume_summary.json` · 432,032 bars.

### The controls behaved, so the instrument is trustworthy this time

| control | required | measured max abs(rho) | |
|---|---|---:|---|
| `ctrl_blend` — half a price score | **must FAIL** | **0.68** | correctly fails |
| `ctrl_noise` — pure random | **must PASS** | **0.00** | correctly passes |

**Two-sided and both correct.** D269's one-sided control could be passed for a reason unrelated to
the hypothesis; this one cannot.

### Stage 1 — V1a and V1b PASS, and not narrowly

| score | max abs(rho) vs all nine price scores |
|---|---:|
| `dollar_vol` | **0.01** |
| `vol_trend` | **0.01** |
| `rel_vol`, `vol_z` | **0.09** |
| `signed_vol` | 0.14 |

**Effective independent scores: 2.87 of 9 → 5.25 of 16.** Against a bar of 3.5.

**Volume is a real third input.** Not a clock artifact — the bar-of-day normalisation is in place and
`ctrl_blend` proves contamination would have been detected. **W-a and W-b confirmed.**

### Stage 2 — M2 fails on all 15, and W-c is confirmed

**Nothing clears M1 and M2 together, so M3 was not computed.**

But volume produced something no price score did:

| LOW stratum | Q1 | Q2 | Q3 | Q4 | Q5 | spread | vs 4.00 bp bar | M1 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **`rel_vol`** | +1.71 | +1.23 | +1.00 | +0.96 | **−1.97** | **−3.68 bp** | **0.92×** | **MONOTONE** |
| `vol_z` | +1.61 | +1.37 | +1.10 | +0.79 | −1.95 | −3.56 bp | 0.89× | **MONOTONE** |
| `dollar_vol` | +1.75 | +1.22 | +1.28 | +0.86 | −2.18 | **−3.93 bp** | **0.98×** | no |

**In [D267](D267-the-magnitude-calibration-screen.md), 0 of 27 price cells were monotone. Here 2 of
15 are** — and they are the same quantity twice (`vol_z` is `rel_vol` z-scored), so it is **one**
finding, not two.

**And the relationship is clean and in the direction a short wants:** on the low-volatility
mega-caps, **high relative volume precedes falls and low relative volume precedes rises, ordered
across all five quintiles.** Low volume +1.71 bp, high volume −1.97 bp.

**It fails anyway.** The best spread is **0.98×** the round-trip cost and the best *monotone* one is
**0.92×**. Every other stratum is worse: ALL peaks at −1.88 bp against an 8.42 bp bar, HIGH at +1.36
against 12.84.

### The reading

**Volume is independent but uninformative at this horizon — which is exactly the outcome D270
registered as reportable rather than null.** A consensus rule could carry volume as a genuine third
opinion, and D267's arithmetic already says diversification alone does not pay a round trip.

**And the shape is the same one this entire thread keeps producing.** The closest cell is on the LOW
stratum, where the cost bar is lowest; the effect is real, monotone, and about **0.9 of one round
trip**. Nothing here is broken — the edge is simply smaller than the toll, once again, and this time
by 8%.

---

## Stop — fired

**Volume is closed as the third input.** No sixth score, no second normalisation window, no
per-stratum retry, as registered. **Nothing is promoted; R8 governs.**

---

## ADDENDUM — M3 was specified and the runner skipped it. R6 defect, now closed.

**D270 named three hurdles. The runner computed M3 only for cells that had already cleared M1 and
M2, so when none did it printed *"M3 not computed"* and stopped.** That is precisely the defect
[R6](../RULES.md#r6) exists for — *"a runner implementing a multi-leg hurdle must compute every leg
or fail loudly"* — and it is the same short-circuit D230 found in D217 and D218.

**Computed now. 300 shuffle draws, one shared permutation per simulation, best-of-15 across all
volume cells: the floor is 2.56 bp.**

| cell | spread | M1 | M2 | **M3** |
|---|---:|---|---|---|
| **LOW `rel_vol`** | **−3.68 bp** | **YES** | no *(0.92×)* | **YES** |
| **LOW `vol_z`** | −3.56 bp | **YES** | no *(0.89×)* | **YES** |
| **LOW `dollar_vol`** | **−3.93 bp** | no | no *(0.98×)* | **YES** |
| LOW `vol_trend` | −2.26 bp | no | no | no |
| every ALL and HIGH cell | ≤ 1.88 bp | no | no | no |

**Three of fifteen beat the null, all on the LOW stratum.** `rel_vol` and `vol_z` clear **M1 and M3
together** and fail only M2 — **the ordering is real, monotone, and statistically distinguishable
from a shuffle. It is 8% short of paying for a round trip.**

**The verdict is unchanged** — M2 is a hurdle, not a tiebreak, and nothing clears all three. But the
record now says *how* it failed, which the short-circuit had hidden: **not for want of signal, and
not for want of surviving a null.**
