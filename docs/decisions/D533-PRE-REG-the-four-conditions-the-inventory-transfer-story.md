# D533 — PRE-REGISTRATION: the four conditions the inventory-transfer story implies, **singly and in pairs**

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D533-PRE-REG-the-four-conditions-the-inventory-transfer-story-implies-singly-and-in-pairs.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.**
**In sample 2016-01-04 → 2023-12-29. The 2024+ slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*On the principal's instruction, 2026-09-15. He also directed that **C2 is the primary** — that is his
judgement, not mine, and it is recorded here because it is provenance if C2 clears.*

---

## 0. Why this is not D532 again

D532's conditioner was **mislabelled as coming from the story and its sign was declared backwards.**
I predicted low-volume ranges would break and run ("a thin book is easy to push") — a *different*
mechanism from the one I had just described. The story says a break happens **because transfer flow
exhausted the standing book**, which requires flow to have gone through it. **No flow, no exhaustion.**

So the story's prediction is the opposite of what D532 declared, and D532's data is consistent with
the corrected sign (ES `V-high-up` **+3.26**, `W-high-up` **+3.28**, dose-response negative). Its
"DOES NOT PASS" is a verdict on my derivation, not on the mechanism.

**The story has not been tested.** This record tests it.

## 1. The four conditions, derived

| | the story's requirement | the observable |
|---|---|---|
| **C1** | for the book to be *exhausted*, flow must have gone through it | **break flow**: volume on the break bar + the next, over that session's own median bar volume up to the break |
| **C2** | there must have been inventory *to* transfer | **overnight depth**: night volume ÷ night range, relative to its own trailing norm |
| **C3** | the push ends when the inventory is gone — **not on a clock** | **volume-normalisation exit**: leave at the first bar whose volume drops below the session's pre-break median |
| **C4** | the range must have been built by *absorption*, not by trend | **OR path efficiency**: &#124;net move&#124; ÷ Σ&#124;bar moves&#124; inside the range; **low** = absorption |

**C2 is a RATIO where the existing instrument is a PRODUCT.** D506's activity filter is
`sqrt(range × volume)`; the story wants volume **over** range — heavy trade against a *small* range is
what absorption looks like. That is a functional-form correction, not a retune.

**C1, C2 and C4 are entry filters; C3 is an exit rule.** So "singly and in pairs" is 3 filters ×
2 exits, which yields the four singles (C1, C2, C4, C3) and the six pairs (C1C2, C1C4, C2C4, C1C3,
C2C3, C4C3) exactly. **Higher-order combinations are explicitly deferred** on the principal's
instruction.

## 2. Operational definitions, all causal

- Breaks, sessions and the both-sides skip are **D531's**, unchanged: opening range = first 6 bars of
  each root's own session; entry at the bar **after** the break; a bar spanning both sides skips the
  session.
- **C1** `= log( (vol[b] + vol[b+1]) / median(vol[first..b-1]) )`, TRUE in the **top tercile**.
- **C2** `= log( night_volume / night_range )` less its trailing 50-session mean, TRUE in the **top
  tercile**. Night segments h18–h08 from the breadth fixture. **Coverage is reported**: that fixture
  carries ~17 % NaN night rows on ES, and terciles are taken over available sessions only.
- **C3**: exit at the first bar after entry whose volume `<` the session's pre-break median, with a
  minimum hold of one bar and a hard cap at the session close.
- **C4** `= |close[OR_end] − open[OR_start]| / Σ|close[i] − close[i−1]|` inside the OR, TRUE in the
  **bottom tercile** (low efficiency = absorption).
- **Baseline exit** where C3 is not in play: **60 minutes** (12 bars), where CHECK 1 measured 9.5×
  cost coverage.

## 3. Sign predictions, from the story — all four the opposite of D532's

- **C1 TRUE → continuation IMPROVES.** Flow present means the book was genuinely exhausted.
- **C2 TRUE → continuation IMPROVES.** Inventory accumulated overnight is inventory to be transferred.
- **C4 TRUE → continuation IMPROVES.** An absorbed range has someone carrying the other side.
- **C3 → lift IMPROVES versus the fixed exit**, because a fixed clock mixes "still transferring" with
  "already reverted".

**If C1, C2 or C4 improve continuation when FALSE rather than TRUE, the mechanism is inverted** and
the story is wrong in the way that matters — which is a real outcome, not a hedge.

## 4. Reference, nulls, and the multiplicity that nearly sank D532

**Reference: the rotated base rate** — same bar index, different session — never 50 % (FINDINGS §74).
**Ties excluded.** **Up and down breaks measured separately**, pooled only after sign adjustment.

> **PRIMARY (the principal's choice): C2 TRUE, fixed 60-minute exit, pooled over CL/GC/SI/NG,
> sign-adjusted, measured as lift over the rotated base rate.**

**The family is the 20 pooled cells** — 10 condition-combinations × 2 sides, pooled over the four
candidate roots. **Per-root numbers are diagnostic only and may never be promoted**, and that is a
commitment made here rather than a judgement made afterwards. D532 priced a 192-cell family and found
its p95 at **+9.89 points**; a grid that size cannot clear anything, and the fix is to declare the
unit of selection in advance.

- **N1** — per cell, against its own rotated base-rate distribution, 1,000 draws.
- **N2** — family maximum over the 20 pooled cells, one rotation per draw common to all.

**PASS requires: the PRIMARY clears N1, the family maximum clears N2, and the primary's sign matches
its prediction.** All three.

## 5. What a pass would mean

A **candidate**, not a component. C-a…C-e are scored in dollars by the runner at minimum tradable
size under the cost that size pays — **$4.00 CL, $5.00 GC, $8.00 SI, $5.00 NG**, from measured median
spreads. C-b carries its second meaning: an arm opposing the admitted NQ arm in a *correlated*
instrument is a closure offence, which is why every candidate root here is a commodity.

**The reserved slice is not read by this record under any outcome.**
