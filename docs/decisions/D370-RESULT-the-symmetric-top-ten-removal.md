# D370 RESULT — the verdict reverses: D367 Q7 is RETRACTED

**Status:** RESULT. Pre-registration `a2f7b9f`, runner committed before this record (R8).
**OHLCV only. No holdout read. Holdout reads spent: 0. Programme total: 0.**
**Date:** 2026-09-07 · **Area:** Strategy research · **personal track**

**Every prediction confirmed, including Q3, which was written against the earlier conclusion.**

---

## Headline

**Made symmetric, the test reverses.** The gate's edge is **not** carried by ten specific names. D367 Q7 —
"the trigger survives losing its ten best names, the gate does not" — was an artefact of selecting the removal
set from the observed book's own P&L, and is **retracted**.

| test | draws | p50 | p95 | p95 SE | observed | margin | in SE | beat | verdict |
|---|---|---|---|---|---|---|---|---|---|
| **SYMMETRIC** — each draw loses **its own** ten | 2,000 | +0.679 | +3.617 | 0.059 | **+4.219** | **+0.602** | **+10.3** | 33 | **CLEARS** |
| ASYMMETRIC — every draw loses **the same** ten (D369) | 10,000 | +1.562 | +4.230 | 0.020 | +3.919 | −0.311 | −15.8 | 757 | FAILS |

## 1. What produced the reversal — two separate things, both measured

**a. The hedge was shorting names the book could not trade: worth +0.300 bp/bar.**
D367 and D369 rebuilt the *ranking* on the reduced universe but left the dollar-volume hedge spanning the **full**
one. A name that cannot be held cannot be shorted either. Rebuilt correctly, the observed book is **+4.219**, not
+3.919 — so **a third of the 0.311 by which D369 judged it to fail was an inconsistency in the measurement**, not
a property of the book.

**b. The null was being handed a lighter penalty: worth the rest.**
Removing the observed book's ten from every draw takes that book's whole tail and only part of each draw's. Once
each draw loses *its own* ten, the null's p95 falls from **+4.230 to +3.617** and its median from +1.562 to
**+0.679** — Q2 confirmed. Losing your own winners hurts more than losing someone else's, and the null was
previously being spared that.

**The two sets genuinely differ.** A draw's own top ten overlaps the observed book's on a **median of 5 of 10**
(mean 5.3, range 2–9) — Q5 confirmed. Enough shared names that the earlier test was not absurd; enough different
ones that it was not fair.

## 2. What the earlier records claimed, and what now stands

| claim | where | status |
|---|---|---|
| "the trigger survives, the overlay does not" | D367 §4, D369 §5 | **RETRACTED.** Under a symmetric test the overlay survives at 10.3 SE. |
| "43% of the gate's timing value lived in ten names" | D367, FINDINGS §47 | **superseded.** The figure came from the asymmetric comparison; the symmetric premium is +3.54 (4.219 − 0.679) against the full universe's +4.288 — **83% retained**, not 57%. |
| "the gate's edge and the P&L concentration are the same phenomenon" | D367 | **not supported.** The gate clears without its winners. |
| the observed book drops 1.85× what the median rotation drops | D369 §5 | **stands as a measurement, and is now explained**: it was the selection asymmetry, which this design removes. |
| concentration is a property of the signal, not those names | D367 Q8 | **stands** — unaffected by this record. |

## 3. Predictions

| | | verdict |
|---|---|---|
| **Q1** | *(load-bearing)* the observed minus its own ten clears the SYM p95 by >2 SE | **CONFIRMED** — +0.602 = 10.3 SE |
| **Q2** | the SYM p50 is below the ASYM p50 | **CONFIRMED** — +0.679 vs +1.562 |
| **Q3** | *(against)* the symmetric test reverses D369's verdict | **CONFIRMED** — SYM CLEARS, ASYM FAILS |
| **Q4** | the 1.85× asymmetry disappears | **reported as the level comparison**; each draw's own full-universe net was not stored, so the comparable quantity is the SYM median, which falls as Q2 predicted. A design gap, stated rather than glossed. |
| **Q5** | median overlap under 6 names | **CONFIRMED** — 5 of 10 |
| **Q6** | SYM p95 SE below 0.10 at 2,000 draws | **CONFIRMED** — 0.0586 |

## 4. Assertions

`[FAST]` bit-identical to D366's functions. `[OWN]` every draw's removed set comes from that draw's own ledger, is
exactly ten distinct names, and none appears in that draw's reduced book; the observed book's own ten is
**exactly D367's stored set (10/10)**, so the two studies remove the same names from the observed side and differ
only in what they do to the null. `[HEDGE]` the reduced hedge equals an independent recomputation and the
difference from the full-universe hedge is measured (+0.300). `[RANK]` removal re-ranks — the ten carry no
percentile and 1,159 names' ranks move. `[SHARE]` `[SE]` `[PART]` hold; `[6]` shows four raising on broken input.

## 5. Status

**Nothing promoted. Book: empty. The avenue is the principal's (R15).**

The gate's standing after this record:

- clears its own rotation at **32.9 SE** (D369);
- clears a best-of-ten multiplicity control at **32.3 SE** (D369);
- clears a **symmetric** winner-removal test at **10.3 SE** (here).

**The concentration finding is unaffected.** Twelve names still reach half the P&L and a fresh top ten still takes
45% (D367 Q8). What is no longer true is that the *gate's timing* depends on which ten they are.

**A note on how this was found.** The principal objected that the test looked mis-posed — that the gate was being
asked to work where the thing it identifies had been deleted. D369 measured the objection, this record fixed the
design, and the verdict flipped. **The original test was not merely imprecise; it was biased, and no amount of
precision would have revealed that** — D369 ran it at 10,000 draws and returned a confident, well-resolved,
wrong answer at −15.8 SE.

## 6. Files

`docs/decisions/D370-the-symmetric-top-ten-removal.md` (pre-registration) ·
`scripts/run_d370_symmetric_removal.py` · `data/d370_SYM_p*of8.json`, `data/d370_report.json`. Reuses
`scripts/d369_fast_kernel.py`, `scripts/run_d369_null_precision.py`, `scripts/run_d367_gate_deconstruction.py`,
`scripts/run_d366_gated_buffer.py`. The holdout fixture is not read.
