# D270 — Volume structure, retested under a control that can fail

**Status:** PRE-REGISTERED. Committed **before the retest is run**. Nothing here is a result.
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
