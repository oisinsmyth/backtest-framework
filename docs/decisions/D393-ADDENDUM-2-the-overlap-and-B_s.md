# D393 ADDENDUM 2 — the overlap check REFUTES Addendum 1 §2, and `up_run_21` survives `B_s` while the null's own positive control dies

**Status:** ADDENDUM 2, amending [Addendum 1](D393-ADDENDUM-the-primary-cell-in-money.md) **in
writing** (§1 below). **One null of four, on one cell of ten. H1 is NOT cleared — see §5.**
Admits nothing (R15).
**Date:** 2026-09-08 · Runner: `scripts/run_d393_bs_null.py` · Artifacts: `data/d393_overlap.json`,
`data/d393_bs_null.json` · **Holdout reads: 0.**
**Authorised by the principal 2026-09-08:** the overlap check, then B_s on the primary cell — a
narrowing of §4's ten-cell scope to one.

---

## 1. AMENDMENT — Addendum 1 §2's hypothesis is refuted, and by its own §7 test

**Addendum 1 §2 said:** *"The parsimonious reading is that `up_run_21` is the same reversal effect
at lower fidelity."* §7 named the test. The test was run and **the hypothesis fails.**

| pair | events J | held-bar J | held/a | shared trades | **trades/a** |
|---|--:|--:|--:|--:|--:|
| `up_run_21` ∣ `rev_21` | 0.020 | 0.201 | 0.322 | 603 | **2.9%** |
| `up_run_21` ∣ `up_frac_21` | 0.037 | 0.302 | 0.470 | 1,221 | **5.9%** |
| `up_frac_21` ∣ `rev_21` | 0.059 | 0.278 | 0.414 | 1,629 | 7.6% |

**They are not the same book.** D365/D373's precedent found 70.1% shared held name-bars; this finds
**20–30%**, and at trade level 2.9%.

**The deciding split** — `up_run_21`'s trades by whether `rev_21`'s own E1 takes them:

| | n | mean | median |
|---|--:|--:|--:|
| shared with `rev_21` E1 | 603 | +105.59 | +50.20 |
| **disjoint from `rev_21` E1** | **20,182** | **+19.56** | **+12.57** |

**Delete every trade `rev_21` also takes and 97.1% of the book survives at +19.56 bp.**

**What stands from §2, and it is stranger than the refuted reading:** `up_run_21` (+22.06) and
`up_frac_21` (+21.62) do earn the same thing — **while sharing 5.9% of their trades.** Two nearly
disjoint books, one of them K1-killed, converging on the same mean. That is what raised the
possibility, tested in §3, that ~+20 bp is a property of the **E1 decile-crossing shape** rather
than of either score.

**A free consistency check:** `rev_21`'s own E1 books **+40.53 bp**, against FINDINGS §31's **+38**.
The machinery reproduces the record.

**What does NOT change:** §2's observation that K1 sorted two scores into different buckets while
the money did not agree with the sort. That was measured and it stands — the *explanation* offered
for it was wrong.

---

## 2. `B_s` — 2,000 draws, E1, cap 20, long

Each event's name replaced by a random eligible name in the **same `rev_21` decile that day**.
§4 declared this null **load-bearing**.

| score | observed | p50 | **p95** | SE | margin | verdict |
|---|--:|--:|--:|--:|--:|---|
| **`up_run_21`** *(candidate)* | +22.06 | +10.01 | **+18.97** | 0.31 | **+3.09** | **ABOVE** |
| **`up_frac_21`** *(positive control)* | +21.62 | **+20.72** | +28.76 | 0.30 | **−7.14** | **BELOW** |

**Margin 3.09 against SE 0.31 is ~10 SE — outside D369/D373's 2-SE UNRESOLVED band.** Draw range
−9.23 to +28.93 for the candidate.

---

## 3. THE RESULT IS THE TWO p50s, NOT THE TWO VERDICTS

> **`up_frac_21`'s null centres at +20.72 against an observed +21.62. `up_run_21`'s null centres at
> +10.01 against an observed +22.06.**

**Hold the `rev_21` decile fixed and a random name reproduces `up_frac_21` almost exactly.** It *is*
the decile — which is what K1 said at ρ +0.601 and what §4 predicted in money before the run. **The
null had to kill it, and it did.**

**The same null does not reproduce `up_run_21`.** Roughly 10 of its 22 bp is the decile composition;
the rest is not, and it clears the null's p95.

**This is why the positive control was not optional.** A B_s that failed to kill the known proxy
would have proved nothing about the candidate. It killed it, so the null has demonstrated power on
this exact cell — and CLAUDE.md's rule that a self-test which cannot fail is worse than none applies
to nulls as much as to assertions.

**And B_s is the more demanding bar**, as a proper control should be: its p95 **+18.97** sits well
above the D392 unconditional atlas floor of **+12.67**. The candidate clears the harder one.

---

## 4. Q5, scored — and it was written against the candidate

§6 predicted: **Q5 — *"if Stage 1 runs, the book is INSIDE `B_s`'s p95"*.** **Q5 FAILED.**
`up_run_21` is outside it by 3.09 bp. **Q5 held for `up_frac_21`**, which is not a candidate.

That makes **five of six** pre-registered predictions scored, and this is the first one to fail.

---

## 5. WHAT THIS DOES NOT CLEAR, and H1 is not cleared

1. **One null of four.** **A′ (time rotation), B (`rsi` bucket) and C (random direction) are
   unrun.** B_s answers *"is it the `rev_21` decile?"* — nothing else. In particular **nothing here
   tests whether ~+20 bp is generic to the E1 decile-crossing shape**, which §1 raised and which
   A′ is the null for. **That is the open question, not a closed one.**
2. **H1 requires a BEST-OF-10 floor** (§7): the maximum over the 10-cell grid *within each draw*.
   **This is one cell.** A best-of-10 floor is strictly higher than a single-cell p95, so
   **+3.09 is an upper bound on the margin H1 would see, not the margin itself.** H1 is **not
   cleared**, and no reading of this file should say it is.
3. **Net is −39.13 bp/trade at 0.36× the measured round trip.** Gate 1c needs ≥ 1.0×. **Nothing is
   tradeable.** B_s is a statement about signal, not about money after costs.
4. **The grid is not blind.** The primary cell was seen in Addendum 1 before this null ran.
5. **Multiplicity is 20** under the per-score reading, not the 10 §7 priced.

---

## 6. Assertions, and the engineering

- **[Bs]** dates and counts preserved; every replacement eligible and **in the event's own decile**;
  the shortfall recounted independently. **26,236 replacements, 0 kept for a short pool** — every
  event found a same-decile partner, so the null never silently falls back to observed names.
  **The assertion RAISES on an ineligible replacement.**
- **[SHARD]** 12 draws in 4 strides reproduce the sequential list **bit-identically**; every path
  reads the draw list through one `item_at()` definition, so a shard cannot disagree with the whole
  about which draw an index names. `merge_shards` asserts full coverage and no index in two shards
  **before** anything is scored.
- **[P]** the JSON was persisted before rendering.
- **Holdout: 0 reads.** Mining fixture; the holdout is a disjoint symbol set.

**Threads were 0.37× — SLOWER than serial** (8 draws: 17.4 s wall against 6.5 s serial).
`run_mirror` is GIL-bound, so `parallel_map` was the wrong tool and the calibration caught it
before the launch rather than after. **8 processes over `items[i::8]`: 3,240 s of work in 691 s
wall = 4.69×, 59% efficiency** — still below CLAUDE.md's 70% floor, recorded rather than rounded
up. Projected 8 min, actual 11.5.

---

## 7. What the record now needs, in order

1. **A′ on this cell** — the time rotation. It is the null for §1's live question: whether the
   decile-crossing *shape* earns ~+20 bp regardless of which score draws it. **Not authorised.**
2. **The other nine cells**, if H1 is ever to be assessed as §7 specified.
3. Neither is authorised by this file, and **only the principal opens them (R15).**

---

**Status footer.** One null of four, one cell of ten, no holdout read, nothing admitted.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
