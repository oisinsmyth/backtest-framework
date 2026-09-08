# D393 ADDENDUM 4 — the null battery is complete on the primary cell, and **H1 IS NOT CLEARED**: B lands UNRESOLVED at +0.69

**Status:** ADDENDUM 4. **All four nulls now run on one cell of ten. H1 FAILS on this cell.**
Admits nothing (R15). **Nothing is retired either — only the principal closes an avenue.**
**Date:** 2026-09-08 · Runner: `scripts/run_d393_bs_null.py --null B|C` · Artifacts:
`data/d393_b_null.json`, `data/d393_c_null.json` · **Holdout reads: 0.**

---

## 0. The verdict

| null | what it holds fixed | p50 | p95 | SE | observed | margin | verdict |
|---|---|--:|--:|--:|--:|--:|---|
| **A′** | names, counts; destroys timing | +5.74 | +16.20 | 0.39 | +22.06 | +5.86 | **ABOVE** |
| **B_s** | day + `rev_21` decile | +10.01 | +18.97 | 0.31 | +22.06 | +3.09 | **ABOVE** |
| **C** | the real trades; draws the sign | −0.16 | +11.51 | 0.34 | +22.06 | +10.54 | **ABOVE** |
| **B** | **day + `rsi` bucket** | **+12.16** | **+21.37** | **0.39** | +22.06 | **+0.69** | **UNRESOLVED** |

**H1 requires the observed mean above the p95 of A′, B, B_s *and* C.** B is **UNRESOLVED** — the
margin **+0.69** sits inside **2 SE = 0.78** — and D369/D373's rule is that a margin within 2 SE is
**recorded UNRESOLVED, never passed.**

> **H1 is not cleared. Not on a technicality about the best-of-10 floor — on this cell, against
> one of its own four declared nulls.**

---

## 1. What B says, and it is the one that bites

**B swaps each event's name for another eligible name in the same `rsi` bucket that day**, among
names with a defined `rsi` percentile.

**Its p50 is +12.16.** Pick a *different* name in the same `rsi` bucket on the same days and you
get **+12.16** of the candidate's **+22.06** — and 5% of such draws beat **+21.37**.

**So the dates and the `rsi` bucket carry most of it.** That is a sharply different picture from
B_s, where holding the `rev_21` decile fixed left the candidate clear by +3.09. The candidate is
not a trailing-return proxy — Addendum 2 established that — **but it may be substantially an `rsi`
bucket-and-timing effect, and B cannot currently tell us.**

**The control behaved differently again**, and B had no declared expectation for it: `up_frac_21`
came in **BELOW** (−5.84). Both scores lose most of their apparent edge to the `rsi` bucket; the
candidate merely loses slightly less.

**C is the least informative of the four and it passed easily** (+10.54, p50 −0.16 ≈ 0 as asserted
before scoring). C only asks whether the *sign* is real given these exact trades and holds. It
never had a plausible chance of firing on a book with t +3.09, and it should not be read as
evidence of much.

---

## 2. The draw allocation was wrong, and §4 chose it

**§4 declared A′ 2,000, B_s 2,000, C 2,000 and B 1,000 — B the lowest.** B is the null that landed
in the band, and it is the one with the fewest draws and therefore the largest SE.

**That allocation was inherited from D373's amendment without re-deriving it for this study**, the
same defect noted in Addendum 1 §0 about the cell count. **A remedy is available and it is
pre-declared**: D373's amendment says that where a hurdle lands inside the 2-SE band, *"the answer
is to spend more draws on that one hurdle, and the record will say so rather than rounding it to a
verdict."*

**Raising B to 4,000 draws would cut the SE to roughly 0.20 and 2 SE to ~0.39**, against a margin
of 0.69 — enough to resolve it either way, at about 12 minutes on eight processes.

> **If that is run, the direction it resolves to IS the answer. Declared here, before the draws:
> a resolution BELOW retires the cell, and a resolution ABOVE clears B by under one basis point —
> which is not a strong result and must not be reported as one.**

**Adding draws because a margin is in the band is legitimate. Adding draws until a margin leaves
the band on the side you want is not.** The distinction is that the decision is being made and
written down now, without knowing which way it goes.

---

## 3. Where the candidate stands, in full

| bar | | cleared? |
|---|--:|---|
| D392 atlas floor, pool ALL | +12.67 ± 0.93 | ✔ |
| A′ p95 | +16.20 ± 0.39 | ✔ +5.86 |
| B_s p95 | +18.97 ± 0.31 | ✔ +3.09 |
| C p95 | +11.51 ± 0.34 | ✔ +10.54 |
| **B p95** | **+21.37 ± 0.39** | **✗ UNRESOLVED +0.69** |
| **H1 overall** | all four | **✗ NOT CLEARED** |
| H2 (size, ≥1.0× round trip) | 0.36× | ✗ |
| the best-of-10 floor (§7) | 10 cells | **never computed** |

**And every margin above is still an upper bound**, because §7 requires the p95 of a **best-of-10
floor** taken within each draw, which is strictly higher than any single-cell p95. **The best-of-10
floor would push B further against the candidate, not towards it.**

**Net remains −39.13 bp/trade at 0.36× the measured 61.19 bp round trip.**

---

## 4. What this means for optimisation, stated plainly

**A cost study on this candidate is now premature.** The binding constraint was thought to be cost;
B says the prior question is whether there is an edge to pay for. **Optimising the cost of a book
whose best null margin is +0.69 UNRESOLVED would be optimising something that may not exist** —
and a price/liquidity filter changes the sample, which would re-open every null above rather than
leaving them standing.

**The order that follows from the evidence:**

1. **Resolve B at 4,000 draws** (~12 min), on the terms declared in §2.
2. **If B resolves ABOVE:** run the other nine cells, because H1's best-of-10 floor is the only
   version of H1 that counts, and it has never been computed.
3. **Only then** a cost study, pre-registered under R8, scoring every filtered cell against its own
   **price-conditional** atlas floor — the unconditional floor is invalid the moment price is
   filtered, since D392 measured a 36.8 bp spread across price terciles.

**Still excluded: window length, decile width, cap-as-a-choice.** §9 forbids that search by name.

---

## 5. Assertions

- **[B]** 26,094 replacements inside the event's own `rsi` bucket, 142 kept for a short pool;
  dates and counts preserved; **the assertion RAISES on an ineligible replacement.** The pool is
  `elig` ∧ finite `rsi` percentile (D359's `elig_b`), because a name without an `rsi` percentile
  has no bucket to be swapped inside. The per-group swap function is **generic in its grouping
  array** — B and B_s are the same code with a different group, not two copies.
- **[C]** both direction nulls asserted centred on zero **before** scoring (p50 −0.16 and +0.12).
  C needs no simulation: it flips the sign of the **observed** ledger, so it costs milliseconds and
  takes no shards.
- **[SHARD]** strided == sequential bit-identically; full coverage asserted before scoring.
- **[P]** persisted before rendering. **Holdout: 0 reads.**

---

**Status footer.** Four nulls of four on one cell of ten. **H1 not cleared. Nothing admitted,
nothing retired, no holdout read.** `docs/BOOK.md` holds S1 and S2, neither at capital;
`docs/BOOK_PROP.md` is empty. **Only the principal closes a research avenue (R15).**
