# D305 RESULT — only one arm kept the book full

**Status:** RESULT. Pre-registered at `eeab1d3`, runner at `653a3cb`'s successor,
both committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. THE CONFOUND, STATED FIRST, BECAUSE I ANNOUNCED THE HEADLINE BEFORE I SAW IT

`R rank<=5` returns **net +0.19 bp/bar** at the robust round trip — the first
positive net figure in this programme. **It is not a result, and I said it was
one before looking at the risk columns.**

**Every arm that blocks re-entry also shrinks the book**, because a blocked name
leaves a slot with no eligible replacement:

| cell | entries/bar | run | **implied book** | % full |
|---|--:|--:|--:|--:|
| CONTROL | 9.489 | 4.00 | **38.0** | 100% |
| **S suppress** | 8.607 | 4.41 | **38.0** | **100%** |
| C cooldown 1 | 9.275 | 3.99 | 37.0 | 97% |
| C cooldown 3 | 8.333 | 3.97 | 33.1 | 87% |
| C cooldown 5 | 7.548 | 3.95 | 29.8 | 79% |
| R rank≤10 | 7.622 | 4.01 | 30.6 | 80% |
| **R rank≤5** | 4.656 | 4.03 | **18.8** | **49%** |

**`R rank<=5` runs a half-empty book — about 19 positions where the design holds
38.** Its positive net is bought by holding half as much, which is D300's
book-width axis arriving through the back door, not a re-entry finding.

And the risk columns say so plainly:

| cell | gross | vol | **Sharpe** | **maxDD** | net_rob |
|---|--:|--:|--:|--:|--:|
| CONTROL | +12.00 | 238.5 | **+0.799** | **8,320** | −13.03 |
| S suppress | +11.03 | 242.5 | +0.722 | 8,560 | −11.68 |
| C cooldown 5 | +13.45 | 259.7 | **+0.822** | 12,163 | −6.47 |
| **R rank≤5** | +12.47 | **309.7** | **+0.639** | **16,145** | **+0.19** |

**30% more volatility and nearly twice the drawdown**, for the second-worst
Sharpe in the study. On this programme's stated objective (FINDINGS §7, Sharpe
not return) it is one of the worst cells here, not the best.

## 2. The clean arm is S, and its result is modest

**Arm S is the only one that keeps the book at 38 positions**, so it is the only
cell where turnover moved and nothing else did:

| | CONTROL | **S suppress** |
|---|--:|--:|
| gross bp/bar | +12.00 | +11.03 |
| paired vs control | — | **−0.97 at t = −0.88** |
| turnover | 0.2500 | **0.2268** (×0.91) |
| cost (robust rt 100.1) | 25.04 | 22.71 |
| **net** | −13.03 | **−11.68** (+1.35) |
| implied book | 38.0 | **38.0** |
| Sharpe | +0.799 | +0.722 |

**Gross is statistically unchanged** (t = −0.88) and **net improves by 1.35
bp/bar**. That is a real but small win, and Sharpe falls because the mean falls
slightly while vol does not.

## 3. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | S cuts turnover 30–40% | **FAILED — 9.3%.** The 30–40% came from D304's same-bar re-entry count, which includes **cap** exits; S touches only triggers. The prediction was wrong before the study ran and is recorded that way |
| **Q2** | S's gross falls, does not hold flat *(against)* | **CONFIRMED in sign, not in size** — −0.97 bp at t = −0.88, indistinguishable from flat |
| **Q3** | S improves net at the robust round trip | **CONFIRMED**, +1.35 bp/bar |
| **Q4** | every cooldown hurts gross, monotonically in `c` | **FALSIFIED.** c=1 −0.47, c=3 −0.45, c=5 **+1.44** — not monotone, and the longest cooldown *raises* gross. But c=5 runs a 79%-full book, so this is the same confound |
| **Q5** | Arm R is net-worse than Arm S *(against)* | **FALSIFIED ON NET (+0.19 vs −11.68) AND THE FALSIFICATION IS CONFOUNDED.** R rank≤5 wins on net while running half a book; on Sharpe it loses badly. R rank≤10, which keeps 80% of the book, is net-**worse** than S |
| **Q6** | no arm beats the control on gross | **FALSIFIED narrowly** — C5 +1.44 and R≤5 +0.46, both at \|t\| < 0.6 and both on shrunken books |
| **Q7** | S's kept swaps carry a higher replacement premium | **not evaluable** — the premium needs D304's paired-swap machinery, which this runner does not carry |

## 4. What the study actually establishes

**Blocking re-entry cannot be tested independently of book size on this design.**
A blocked name frees a slot the book cannot fill, so every blocking rule is
simultaneously a concentration rule. C and R are therefore **not clean tests of
re-entry conditioning**, and their net figures are not comparable to the
control's.

**Arm S escapes this** because it never releases the slot at all — which is
exactly why it was the arm with a definitional holdings claim, and why it is the
only one worth reading at face value.

## 5. Decision

The pre-registered rule says:

> **C or R beats S on net** → re-entry is worth conditioning, and the winning
> level gets its own pre-registered confirmation before adoption.

That branch fires, **and the confirmation must control for book size** — which
the original rule did not anticipate and is added here as a condition on any
successor: a re-entry arm must be compared against a control matched on
**implied book size**, not against the full-book control, or it is measuring
concentration.

**Nothing is adopted from this study.** Arm S's +1.35 bp is real and clean but
small, and it lowers Sharpe; adopting it would be trading edge for cost, which is
the trade this programme keeps declining.

## 6. And the cost picture is unchanged

Round trip **100.1 bp robust** on this book's held names — a third independent
computation agreeing with D302's 106.7 and D303's, so the cost basis is stable.
**The full-book cells remain net-negative by 10 to 13 bp/bar.** The only cell
that crosses zero does so by halving the book, and D300 was already the study for
that question.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 7 declared cells, each against its own holding-run-matched null at 200
draws, plus six paired comparisons against the control. Six cells clear p < 0.05,
but **the null tests exit timing and does not price the re-entry blocking at
all** — no control here asks whether blocking by rank beats blocking at random,
matched on count and persistence. That is the missing control and it is named
rather than glossed.

## Stop

**Re-entry conditioning is not closed, but it cannot be answered on this design.**
Any successor needs a book-size-matched control and a null that randomises *which*
names are blocked.

**D300 comes next as planned**, and it now has a second reason to exist: three
cells here stumbled into partial concentration and two of them looked better for
it, on a confounded basis.

## Files

`data/d305_reentry.json` · `scripts/run_d305_reentry.py` · `temp/d305_run.log`
