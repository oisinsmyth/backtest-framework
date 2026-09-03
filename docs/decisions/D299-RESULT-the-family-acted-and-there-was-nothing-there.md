# D299 RESULT — the family acted, and there was nothing there

**Status:** RESULT. Pre-registered at `45e61c7`, amended at `47b85d4`, runner at
`c645a4d`, all committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## 1. The headline

**Q8 confirmed emphatically. The family is not inert.**

```
held roster differs from the control on 92.2% – 99.9% of bars
                       (D298's price axis: 0.00%)
```

**And that is what makes this negative worth something.** D298's price axis
failed *mechanically* — 19 slots and 19 selected, so it could never change a
holding. The ladder changes the holdings on essentially every bar, and after
10,200 null draws it still cannot beat a control that de-risks for the same
amount of time at unrelated moments.

| | N2 (timing) | N4 (selection) |
|---|--:|--:|
| cells at p < 0.05 | **1 of 24** | **0 of 24** |
| expected by luck | 1.2 | 1.2 |
| smallest p | 0.0299 | 0.1393 |
| **BH-FDR q = 0.10 discoveries** | **0** | **0** |
| p-quantiles p10 / p50 / p90 | .137 / .540 / .844 | .193 / .662 / .958 |
| *(uniform would be)* | *.10 / .50 / .90* | *.10 / .50 / .90* |

**One cell in twenty-four against 1.2 expected is the chance rate**, and the
whole p-distribution is indistinguishable from uniform. Nothing survives BH at
q = 0.10 on either null. The grid-max is not needed to discount the winner; the
raw count already does.

## 2. The decomposition panel, and the sharpest number in the study

On the **fixed declared** reference cell `T=q85/S=q85/Nmin=13` (Sharpe +0.564):

| null | what it randomises | null p50 | treat − null | p |
|---|---|--:|--:|--:|
| **N1** memoryless | `N(t)` i.i.d., **deliberately invalid** | **+0.620** | **−0.056** | 0.751 |
| N2 rotation | timing | +0.590 | −0.026 | 0.612 |
| N3 episode permutation | sequencing | +0.579 | −0.015 | 0.562 |
| N4 selection | which pair leaves | +0.580 | −0.017 | 0.602 |
| N5 joint | both | +0.570 | −0.006 | 0.522 |

**Every null beats the treatment, including N1.**

N1 was put in the suite to *price* the invalid control — the memoryless one that
re-draws every bar where the treatment persists, the defect that voided D291's
veto arm. It churns 6× the treatment's transitions and it is the easiest control
in the study. **The ladder loses to it.** A rule that cannot beat the control
this programme's own rules describe as too weak to count has nothing in it.

**And the decomposition sums to nothing rather than to something split between
two mechanisms:** timing −0.026, selection −0.017, sequencing −0.011, joint
−0.006. There is no component to attribute.

## 3. The grid

| cell | Sharpe | mean bp | maxDD | expo | unpin | vs N2 | p_N2 | vs N4 | p_N4 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **T=q85/S=off/Nmin=17** | **+0.710** | +10.14 | 9,486 | 95.6% | 99.6% | +0.119 | **0.0299** | −0.001 | 0.527 |
| T=q85/S=off/Nmin=13 | +0.706 | +9.26 | 11,038 | 84.5% | 99.6% | +0.125 | 0.0995 | +0.080 | 0.139 |
| T=q85/S=off/Nmin=10 | +0.669 | +8.29 | 10,593 | 76.8% | 99.6% | +0.092 | 0.144 | +0.054 | 0.179 |
| T=off/S=q70/Nmin=10 | +0.649 | +7.32 | **7,446** | 75.8% | 92.4% | +0.121 | 0.134 | +0.071 | 0.149 |
| **CONTROL** | **+0.512** | +7.54 | 9,374 | 100% | — | — | — | — | — |
| T=q70/S=q85/Nmin=13 | +0.368 | +4.26 | 10,382 | 71.9% | 99.9% | −0.194 | 0.980 | −0.170 | 1.000 |

**The best cell's gain over the control is +0.198, and a randomly-timed ladder
recovers +0.079 of it** — about 40% is generic exposure reduction with no timing
content at all, and the remaining 60% is one cell in twenty-four.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the ladder beats the control somewhere | **true but empty** — many cells beat it on level; the null says the level is what de-risking buys, not when |
| **Q2** | timing matters, ≥ 1 cell at p < 0.05 | **technically met, evidentially not.** 1 of 24 *is* the chance rate |
| **Q3** | **selection does NOT matter** *(against)* | **CONFIRMED.** 0 of 24, best p = 0.139, treat − N4 = −0.017 on the reference cell |
| **Q4** | sequencing does not matter *(against)* | **CONFIRMED** — N2 and N3 are within 0.011 of each other |
| **Q5** | the invalid control is much easier | **CONFIRMED, and then some** — N1's null median is the *highest* of the five, and the treatment loses to it |
| **Q6** | depth matters, `N_min=10` beats `N_min=17` | **FALSIFIED.** The shallowest is best and Sharpe falls with depth. Cutting exposure cuts return without cutting risk in proportion |
| **Q7** | harvest beats protect | **CONFIRMED directionally** — the top three cells are all harvest-only (`S=off`) — but not significantly, and the best protect-only cell has the lowest maxDD in the study (7,446) |
| **Q8** | the ladder changes ≥ 5% of held bars | **CONFIRMED at 92.2–99.9%.** The construction did exactly what it was built to do |

## 5. This does not corroborate D297, and that should be said

D297's overlay — de-risk on the book's equity drawdown — cleared at p = 0.015.
D299's **protect** arm is the graduated version of that idea, and it clears
nothing: the four `S=*/T=off` cells sit at p = 0.134, 0.294, 0.398, 0.546.

**They are related, not identical** — D297 keyed on the book's *equity*
drawdown in units of the book's return vol; D299's `S` arm keys on the mean
*position z-score* drawdown on the shadow book. So this is not a strict
replication and it does not retract D297. **But it is the nearest thing to an
independent attempt at the same idea in this programme, and it fails.** D297's
result should be read as weaker than its own p-value until something replicates
it.

## 6. Two defects in this runner, found after the run

**The cost column is understated by 1.57×.** It used the universe-wide mean
half-spread (39.81 bp) rather than the names actually held — CLAUDE.md's rule,
and the one D285 was written to enforce. The held names are **wider**, not
narrower:

```
held-name Corwin-Schultz half-spread, 121,035 name-bars
  mean 62.31 bp   median 24.73 bp   zero-clamped 42.0%
  round trip: 4 x mean 249.2 bp  ·  4 x median 98.9 bp
runner used: universe mean 39.81 bp -> round trip 159.2 bp
```

Corrected, cost is **96–100 bp/bar** on the mean estimate or **38–40 bp/bar** on
the median, against a gross mean of **+4.3 to +10.1 bp**. It changes no
conclusion — the statistic is Sharpe, which carries no cost — but the reported
column is wrong and the corrected figures are the ones to quote. **42.0%
zero-clamping reproduces the known 41.9%.**

**N3 is a slightly weaker control than the record claims.** Permuting episodes
*merges* adjacent same-level blocks, so the re-derived episode multiset differs
from the source and N3 carries **17.1% fewer transitions** than the treatment —
more persistent, therefore easier to beat. Measured, not hidden. It does not
matter here because the treatment loses to N3 anyway.

**And the draw count is 10,200, not the amendment's 11,200** — that figure
counted the control cell, which has no null.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 24 declared ladder cells plus a control, each against N2 and N4 at
200 draws, plus N1/N3/N5 on one fixed reference cell. **10,200 draws. Zero
discoveries at BH q = 0.10 on either null.** One cell at p < 0.05 against 1.2
expected.

## Stop

**The family closes.** D299 §7's stop condition — *"nothing clears N2 or N4 →
the family closes; the position-level `(T, S)` band becomes the next
construction rather than the follow-up"* — fires exactly as written.

**D300, the deferred stage 2, does not run.** Its axes (`C_up`, drop-choice,
`k`) are refinements of a family that has no effect to refine, and Q3 killed the
drop-choice axis outright.

**What this rules out is worth stating positively:** on this book, the aggregate
convergence state of the portfolio carries **no timing information for
exposure**, and **which** pair to drop carries none either. That is a real
finding about the edge, not a failed harness — the construction unpinned the
book on 99.9% of bars and had every opportunity to act.

**The cost question is now the only thing left that can change any of it**, and
it blocks four results: D293's candidate, D297's overlay, D298, and — had this
one cleared — D299. The disagreement is 0.238× against 0.597×, and **42% of held
cells clamping to exactly zero is most of why.** That is an estimator question,
not a strategy question, and no further rule-level study moves it.

## Files

`data/d299_ladder.json` · `scripts/run_d299_ladder.py` · `temp/d299_run.log`
