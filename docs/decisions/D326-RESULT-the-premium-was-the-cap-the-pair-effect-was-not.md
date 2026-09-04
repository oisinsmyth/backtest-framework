# D326 RESULT — the composite premium was the cap; the pair effect was not

**Status:** RESULT. Pre-registered at `eb3bb2a`, runner at `d4ca1bc`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. This corrects how D325 must be read.**

---

## 1. Q3 confirms — the premium does not merely shrink, it REVERSES

D325 measured a **+0.370** composite premium in the book and I called it synergy.
**Uncapped, per trade, it is negative:**

| at k = 10 | path-variant (bp/bar) | **path-invariant (per trade)** |
|---|--:|--:|
| C4 all-strong | **+0.583** netSHRP | **+22.82** |
| `retrace_leg` alone | +0.213 netSHRP | **+40.57** |
| **the premium** | **+0.370** | **−17.75** |

**And `retrace_leg` alone at k = 20 posts +47.10 per trade, more than double C4's
best cell.** The two lenses are never compared on the same statistic, so these
are two separate readings of the same constructions — and they disagree in sign.

**The composite premium was the slot cap re-ordering which two names survive, not
a signal interaction.** D325's synergy reading is withdrawn.

## 2. Q7 — but the PAIR effect survives, and this is the principal's point

The other half of D325 was that the same primary gives **+0.454** with
`(macd_hist, rsi)` and **−0.190** with `(retrace_leg, skew_63)` — a −0.644 swing
from a pair swap.

```
C0 minus C3     +0.644 netSHRP in the book     +38.68 bp PER TRADE
```

**It does not shrink.** `C3` is **−5.84 per trade** against `C0`'s +32.84.
**Which signals combine is a real signal effect, measurable with the cap removed.**

**So the principal's reading was right on the mechanism and wrong on the
consequence, and my framing was wrong on both.** There *is* structure in which
signals combine. It just does not produce a book worth having, because §1 shows
no composite beats the best single once the cap is off.

## 3. Q4 falsified — and this rescues D323

**Spearman between the two lenses' ranking of the five singles is +0.711**, just
above the 0.7 bar. **The lenses rank the singles almost identically.**

**So D323's leaderboard is NOT a cap artefact.** The correction I feared — that
three studies had ranked signals by how they interact with a two-slot cap — does
not apply to the singles. **It applies only to the composites**, where §1 shows it
applies completely.

## 4. Q6 confirms — the best single beats every composite on both lenses

| | path-variant | path-invariant |
|---|--:|--:|
| **`retrace_leg` k=20** | **+0.625** netSHRP | **+47.10** per trade |
| best composite | C5 k=20, +0.611 | C5 k=40, +45.83 |
| C0 incumbent | +0.454 (k=10) | +44.22 (k=20) |

**This discharges the comparison D325's declared grid could not make.** On both
lenses, independently, the best single leads.

## 5. Q5 falsified — the cap does not always help

D306 found contention drag negative at N = 2, meaning the cap holds the better
names. **Across 33 cells here it is negative in 25 and POSITIVE in 8**, ranging to
**+50.68** (`macd_hist` at k=40).

**So the cap's filter benefit is construction-specific, not a property of the
width.** D306 measured it on one construction and this generalises it in a
direction D306 could not see.

## 6. And a cost statistic worth keeping

`skew_63` at k = 40 posts the highest per-trade net in the study, **+56.22**, at
**mean/2c = 4.53** — more than double every other construction's cost coverage
(most sit near 2.0). **Its `t` is +1.63 on 1,634 trades and p = 0.0784**, so it is
not established; but a construction covering its round trip 4.5× is a different
shape from everything else here and nothing has looked at why.

## 7. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1/Q2** | reproduction, and the lens bites | **CONFIRMED** — variant reproduces D325 and D323 at 0.0e+00; uncapped holds 8.58 names against 4.00 and takes 4,004 trades against 1,828 |
| **Q3** | **C4 does not beat `retrace_leg` per trade** *(against, load-bearing)* | **CONFIRMED** — and it reverses, −17.75 |
| **Q4** | the lenses rank the singles differently | **FALSIFIED** — ρ = +0.711 |
| **Q5** | drag is negative everywhere | **FALSIFIED** — 25 of 33, positive in 8 |
| **Q6** | `retrace_leg` k=20 beats every composite, path-variant | **CONFIRMED**, and on the invariant lens too |
| **Q7** | the pair effect shrinks path-invariant | **FALSIFIED** — it survives at +38.68 bp per trade |

## 8. What this changes

**D325's §1 and §6.1 are withdrawn.** "Synergy is real" and "combination is a real
and large effect, not an artefact of a weak `hist_L`" were both measured through
the cap. **The correct statement is: the composite premium is a cap effect; the
pair-choice effect is a signal effect; and neither produces a book that beats
`retrace_leg` alone.**

**D323 and D324's single-signal rankings stand** (§3), which is the part I was
most worried about.

**And the assertion that made this readable is `[3]`** — the two lenses share no
ranking field and `rank_cells` raises in both directions. FINDINGS §10 has stated
that rule in prose since D304, and prose is why three studies skipped the lens.
**It is now enforced in code and should be carried into every runner that has a
book and a signal.**

## 9. What is owed

1. **FINDINGS §10 gains the measurement it says nothing has made** — opportunity
   cost, 33 cells, negative in 25 and positive in 8, and construction-specific.
2. **`skew_63`'s 4.53× cost coverage** is unexplained and unlike anything else
   measured here.
3. **The composite construction should be dropped from the stack** unless
   something explains why `(macd_hist, rsi)` works — §2 says the effect is real,
   §1 says it is not worth having, and both can be true.

## 10. Files

`data/d326_both_lenses.json` · `scripts/run_d326_both_lenses.py`
