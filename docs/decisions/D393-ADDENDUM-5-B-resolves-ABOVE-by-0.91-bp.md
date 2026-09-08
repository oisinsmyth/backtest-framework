# D393 ADDENDUM 5 — B resolves **ABOVE by +0.91 bp**, H1 clears on this cell, and that is the weakest pass the programme has recorded

**Status:** ADDENDUM 5. **All four nulls now ABOVE on the primary cell. H1 clears HERE — and the
version of H1 that §7 actually requires has never been computed and would push this margin down.**
Admits nothing (R15).
**Date:** 2026-09-08 · Runner: `scripts/run_d393_b_resolve.py` · Artifact:
`data/d393_b_resolved.json` · 9 processes, 332 s · **Holdout reads: 0.**

---

## 0. The result, against what was declared before the draws

| draws | observed | p50 | p95 | SE | 2 SE | margin | verdict |
|--:|--:|--:|--:|--:|--:|--:|---|
| 1,000 | +22.06 | +12.16 | +21.37 | 0.39 | 0.78 | +0.69 | **UNRESOLVED** |
| **4,000** | +22.06 | +12.26 | **+21.15** | **0.22** | **0.43** | **+0.91** | **ABOVE** |

**Addendum 4 §2 declared, before these draws: *"the direction it resolves to IS the answer …
ABOVE clears B by under one basis point, which is not a strong result and must not be reported as
one."*** It resolved ABOVE. **That commitment is now honoured rather than quietly dropped.**

---

## 1. WHY THIS PASS IS FRAGILE, and the fragility is structural not rhetorical

**1. The observed value cannot move. The bar did.** The margin improved from +0.69 to +0.91
**not because the candidate earned more** — +22.06 is fixed — but because the *estimated* p95 fell
from +21.37 to +21.15. **The verdict turned on a 0.22 bp movement in an estimate.**

**2. And the known bias runs the wrong way.** CLAUDE.md: *"A SAMPLE p95 IS BIASED TOWARD THE
CENTRE, so every finite-draw null is more lenient than it looks."* For a right-tail p95 that means
the **true** p95 is likely **higher** than any sample estimate, so **+0.91 is an optimistic reading
of the margin, not a conservative one.** The estimate happening to fall between 1,000 and 4,000
draws is sampling noise in the lenient direction.

**3. The remedy that exists elsewhere does not exist here.** C2b enumerated a finite rotation group
and drove its SE to exactly zero. **B is a per-bar, per-bucket name swap and is NOT enumerable**
(CLAUDE.md names B among the non-enumerable nulls). **Only more draws touch this, and more draws
have already been spent.**

**4. §7's floor is best-of-10 and has never been computed.** H1 requires the p95 of the **maximum
over the ten-cell grid within each draw**, which is strictly higher than any single-cell p95.
**A margin of +0.91 on the binding null is very unlikely to survive it.**

> **So: H1 clears on this cell. H1 as the pre-registration defines it remains uncomputed, and the
> single number it would most likely overturn is this one.**

---

## 2. Where the candidate now stands

| bar | p95 | margin | |
|---|--:|--:|---|
| D392 atlas floor (ALL) | +12.67 | +9.39 | ✔ |
| C — random direction | +11.51 | +10.54 | ✔ |
| A′ — rotated timing | +16.20 | +5.86 | ✔ |
| B_s — same `rev_21` decile | +18.97 | +3.09 | ✔ |
| **B — same `rsi` bucket** | **+21.15** | **+0.91** | ✔ **binding, and barely** |
| **best-of-10 floor (§7)** | — | — | **NEVER COMPUTED** |
| H2 — size, ≥ 1.0× round trip | 0.36× | — | ✗ |

**The ordering is the finding.** Each null that shares more of the candidate's nuisance leaves less
margin: random direction +10.54, rotated timing +5.86, same trailing-return decile +3.09, **same
`rsi` bucket +0.91.** Hold the dates and the `rsi` bucket and almost nothing is left — **p50 +12.26
of an observed +22.06.**

**Net remains −39.13 bp/trade at 0.36× the measured 61.19 bp round trip.**

---

## 3. The optimisation, and what was deliberately not optimised

**Every change is a hoist or a skip. Nothing reorders a float sum; nothing revectorises an RNG
draw.** Proved, not claimed: **`--verify` and `--merge` both assert the first 1,000 draws are
BIT-IDENTICAL to the stored 1,000-draw run** (`data/d393_b_null.json`) on the same seeds. If the
optimisation had moved the null by one ULP, neither would have run.

| | before | after |
|---|--:|--:|
| per draw | 0.587 s | **0.507 s** (1.16×) |
| worker RSS | 1.44 GB | **0.40 GB** |
| worker startup | 29 s panel build | **1 s cached-cell load** |
| wall, 4,000 draws | ~2,028 s serial | **332 s on 9 processes** (6.11×, **68% efficiency**) |

**What was hoisted:** the swap plan (per-bar, per-bucket event indices *and* replacement pools are
fixed across draws — a full-width boolean recomputed 4,000 times); the 53 MB constant score grid;
the output buffer, zeroing only the rows that can ever be written. **The workers no longer build
the panel at all** — a cached mask under `need_grids=False` replaced a **3.08 GB build peak with a
0.24 GB load**, which is what let the fan run nine wide inside the memory budget.

**`run_mirror` was left alone, and it is 72% of every draw.** It is the published event-book kernel
behind A′, B_s, C and every prior study. **A faster version that shifted any float would make this
null incomparable to its own study**, and 1.16× does not buy that risk.

**The largest single win was not code.** `up_frac_21` had already resolved BELOW at −5.84, far
outside the band, so re-drawing it buys nothing. **Only the candidate is drawn** — half the work,
for free.

**Memory budget respected as instructed:** 9 workers × 0.40 GB ≈ 3.6 GB; free RAM measured at
**13.8 GB** during the run against a 10 GB floor.

**68% efficiency is still under CLAUDE.md's 70% floor**, recorded rather than rounded up. It is up
from 59% on the previous fan, and the remainder is the kernel's GIL-bound Python.

---

## 4. What follows, and none of it is authorised here

1. **The other nine cells, and the best-of-10 floor.** This is the only version of H1 that counts,
   and it is the measurement most likely to overturn §0. **It should be run before anything else,
   precisely because it can take the result away.**
2. **A cost study remains premature** for the same reason as before, now sharper: the binding
   null margin is +0.91 bp, and any entry filter changes the sample and re-opens all four nulls.
3. **Not on the list: window length, decile width, cap-as-a-choice** — §9 forbids that search by
   name.

**Nothing is admitted. Nothing is retired. Only the principal closes a research avenue (R15).**

---

**Status footer.** Four nulls of four ABOVE on one cell of ten; H1's own best-of-10 floor
uncomputed; H2 failing at 0.36×. `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. **No holdout read.**
