# D395 RESULT — H0 fails on the pre-registered primary, the record stops, and cap 20 reaches 1.00× coverage without being a result

**Status:** RESULT. **H0 FAILED on the primary. §5's kill condition fires: the construction battery
was NOT run and no null was drawn.** Admits nothing (R15). Nothing retired.
**Date:** 2026-09-09 · Pre-registration: [D395](D395-the-chop-cell.md), committed **before the
runner existed** (R8) · Runner: `scripts/run_d395_chop.py` · Artifact:
`data/d395_h0_search_floor.json` · 44 s · **Holdout reads: 0.**

---

## 0. H0 — the exact best-of-36 label permutation, 10,000 draws

| cap | cells | CHOP | perm p50 | **perm p95** | SE | margin | verdict |
|--:|--:|--:|--:|--:|--:|--:|---|
| **5 — PRIMARY** | 36 | **+28.39** | +22.93 | **+31.26** | 0.13 | **−2.87** | **FAIL** |
| 20 — reported beside it | 36 | +90.43 | +63.61 | +83.54 | 0.28 | +6.89 | PASS |

**The primary fails by 2.87 bp against an SE of 0.13 — twenty-two standard errors below its floor.
There is nothing marginal about it.**

**Q1 held.** §4 declared, against the construction: *"H0 FAILS. The exact permutation p95 exceeds
+28.39."* It does.

**§5 fires as written:** *record it and stop; do not run the construction battery to produce a
favourable number from a cell the search does not support.* **A′, B, B_s and C were not drawn.**
The runner enforces this rather than trusting it — the battery refuses to start while H0's stored
verdict is FAIL, unless `--override` is passed, which exists so that overriding would be a visible
act.

---

## 1. The correction to my own floor was real, and it did not save the cell

[Addendum 4](D394-ADDENDUM-4-the-vol-x-path-efficiency-taxonomy.md) used a normal approximation over
36 **independent** subsets and got **+32.96**. §0 of the pre-registration called that too strict,
because the four ER windows are correlated, and replaced it with an exact label permutation that
preserves the real cells' sizes and overlaps.

**It was too strict, and the correction moved the floor the way I said it would: +32.96 → +31.26.**

**The cell still fails, by 2.87 bp.** **Fixing a defect in a hurdle that favours the candidate, and
reporting that the candidate fails anyway, is the only version of this that is worth anything.**

---

## 2. Cap 20 reaches 1.00× coverage — and this record does not claim it

§1 pre-declared cap 20 as *"reported beside it"*, so its verdict belongs here. The economics,
measured for completeness rather than left tantalising:

| | n | gross | median | t | trim BOTH | price | half-spread | **2c** | **NET** | **ratio** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **cap 20 CHOP** | 2,150 | **+90.43** | +41.52 | +2.95 | **+84.36** | $29.36 | 43.73 | 90.87 | **−0.44** | **1.00×** |
| cap 20, unfiltered | 20,785 | +22.06 | | | | | | 61.19 | −39.13 | 0.36× |
| cap 5 CHOP | 2,573 | +28.39 | +6.18 | +2.16 | +22.86 | $29.90 | 43.67 | 90.68 | −62.29 | 0.31× |
| cap 5, unfiltered | 24,777 | +4.72 | | | | | | 61.48 | −56.76 | 0.08× |

> **This is the first construction in the programme's signal hunt to reach gate 1c's 1.0× coverage
> — and it lands at exactly breakeven, net −0.44 bp per trade.**

**Why it is NOT a result of this record, and the reasons are structural, not modesty:**

1. **Cap 5 was the declared primary and it failed.** Promoting cap 20 *because it passed* is
   precisely the search behaviour H0 exists to price. It would need its own pre-registration with
   cap 20 named primary **in advance**, disclosing that it was chosen after cap 5 failed.
2. **The floor was computed best-of-36 at each hold SEPARATELY.** Selecting across both holds makes
   the searched space **72 cells**, and the honest floor for "the best cell at either hold" is
   higher than +83.54. The margin is +6.89 at 25 SE so it would probably survive — **probably is
   not a measurement.**
3. **No construction null has been run on it.** A′, B, B_s and C are all unrun; H0 prices the
   *search*, not the *construction*.
4. **1.00× is breakeven, not profit.** Gate 2c wants 1.5×. Net is **−0.44**, and there is no margin
   for slippage, borrow, or error in the Corwin–Schultz spread estimate — which is itself an
   estimate from OHLC, not a fill.
5. **It is 2,150 trades from a 20,785-trade book** — a 10% slice, concentrated in $29 names at
   43.7 bp a side.

---

## 3. What is worth carrying

1. **The exact permutation floor is the right instrument for a searched cell** and should replace
   normal-approximation floors wherever a study picks a cell from a grid. It needs no independence
   assumption, handles correlated definitions for free, and cost 44 seconds for 10,000 draws.
2. **A pre-registered kill condition enforced IN CODE stopped a study that would otherwise have
   produced four favourable-looking nulls.** The battery would have run on a cell the search does
   not support, and every one of its numbers would have been real and meaningless.
3. **Coverage of 1.0× exists somewhere in this space.** Nothing in the programme had reached it
   before. **Where it was found is not where it was looked for**, and that is the whole problem.

---

## 4. What this does NOT do

- **It does not close the CHOP line, or D393, or the vol×ER axis (R15).**
- **It does not admit anything**, and clearing a hurdle would not have (D289, `docs/BOOK.md`).
- **It does not authorise a cap-20 study.** That is the principal's call, and it needs a fresh
  pre-registration that declares cap 20 primary before any further number is seen.

---

**Status footer.** H0 failed on the primary; no construction null drawn; no holdout read; nothing
admitted, nothing retired. `docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md`
is empty.
