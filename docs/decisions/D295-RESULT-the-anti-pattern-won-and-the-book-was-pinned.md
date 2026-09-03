# D295 RESULT — nothing clears, the anti-pattern won, and the book was pinned

**Status:** RESULT. Pre-registered at `b7262f5`, amended at `d33fc71`, runner at
`037a176`, corrected at `abaa5e0` — all committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## The result

**0 of 19 cells clear all four conditions.** Q1 confirmed. Stage 2's measured
uplift in this programme stands at **~1.0× across four studies** (D285, D286,
and now both arms of D295).

| cell | Δ bp/bar | Δ t | null p50 | null p95 | beats null | beats floor | cost ok |
|---|--:|--:|--:|--:|:--|:--|:--|
| **B6@1.0** target | **+4.95** | **+2.58** | +1.49 | +3.11 | **yes** | **yes** | **no** |
| B1 reversion | +3.73 | +1.78 | +1.82 | +3.53 | yes | no | no |
| B5@1.0 asym | +3.73 | +1.78 | +1.14 | +3.17 | yes | no | no |
| B5@1.5 asym | +3.73 | +1.78 | +1.13 | +3.03 | yes | no | no |
| B5@2.0 asym | +3.73 | +1.78 | +0.77 | +3.28 | yes | no | no |
| C1@0.5 | +2.48 | +0.96 | +2.47 | +2.61 | no | no | yes |
| B2 displacement | +0.60 | +0.29 | +1.68 | +3.54 | no | no | no |
| C2 idle | −0.22 | −0.09 | −0.08 | +0.52 | no | no | yes |
| **B4@1.0** trailing | −3.04 | −1.14 | −0.29 | +1.96 | no | no | yes |
| **B4@1.5** trailing | −5.86 | −2.05 | −1.54 | +0.96 | no | no | yes |
| **B4@2.0** trailing | **−9.38** | **−2.98** | −2.82 | −0.74 | no | no | yes |

Best-of-19 joint floor: **+4.473 bp/bar**. B6@1.0 clears it at +4.95 and **fails
on cost** — it raises turnover from 20.0% to 25.0%, so condition 2 rejects it.

## 1. THE FINDING: the book was pinned, and that governs everything else

`N_SLOTS` = 19 and the composite selects **exactly 19** names. So the refill has
no choice: a rule that exits a name still in the selected set **immediately
re-enters the same name**. The book is pinned to the current selection and the
exit rule only churns the trade ledger.

That is why four cells report identical books to four decimal places on
different turnover — B1 and all three B5 cells at Δ **+3.73**, from 35,734 /
36,708 / 29,751 / different trade counts and mean ages 3.39 / 3.30 / 4.06.

**Every rule's book return is monotone in how fast it returns to the current
selection:**

| what the rule does with a name that has LEFT the selected set | book bp/bar |
|---|--:|
| B1 / B5 — exits it at once, so the book *is* the selection | **+11.27** |
| B6 — caps winners, so it refills toward the selection sooner | +9.4 to **+12.49** |
| B0 — holds it to the 5-bar cap | +7.54 |
| B4 — holds it 10–20 bars, uncapped | **+4.50 → −1.84** |

**The edge is the cross-sectional selection and it decays. Holding a name after
it leaves the selection destroys it.** That single mechanism orders the whole
arm, and the nulls confirm it: a *random* exit at matched rate and persistence
already earns **+1.1 to +1.8 bp/bar**, because any forced re-entry pulls the
book back toward the selection.

## 2. The principle was tested and it lost — on this book, for a stated reason

**Q6 predicted B6 (profit target) would be the worst rule and B5 (asymmetric)
the best of Arm B. It inverted exactly.**

- **B6@1.0, the declared ANTI-PATTERN, is the best cell in the study** (+2.58)
  and the only one to clear the multiplicity floor.
- **B4, "let the winners run", is the worst family** (−1.14, −2.05, −2.98) —
  and it did do the thing: win/lose run ratios of **2.7, 2.6, 2.5**, winners
  running 2.5× longer than losers, exactly as specified.
- **B5, the asymmetric rule, produces the SAME BOOK as plain reversion** while
  trading more (30.3% vs 29.5% turnover). The stop adds cost and nothing else.

**"Trim losers, let winners run" is a claim about a persistent trend. This book
does not have one** — it has a cross-sectional ranking that decays, so the
winner *is* the name currently ranked best, not the name that has been rising.
Letting it run means holding yesterday's ranking.

## 3. But this design could not fully test the claim, and that is a defect

D286's `disp` beat every designed exit because **the freed slot went to a
better-ranked name** — which requires more candidates than slots. Here slots
equal the selection size, so **there is never a better candidate to promote
into**. Arm B measured *"how fast do you return to the selection"*, not *"does
trimming losers help"*.

**Testing the principle properly needs slots < candidate pool** — e.g. 19 slots
drawn from `hist_L`'s 25, ranked by the composite. That is a different book from
the one D293 validated, so it needs its own pre-registration, not a quiet
parameter change.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | no rule clears all four | **CONFIRMED** — 0 of 19 |
| **Q2** | B2 (displacement) beats B1, B3, B6 | **FAILED** — B2 is +0.29, near the bottom; B6 (+2.58) and B1 (+1.78) both beat it. D286's finding does not reproduce, and §3 says why: displacement cannot promote a better name when there is none |
| **Q3** | capped rules improve per-trade while the book stays flat | **PARTIALLY FAILED** — B6 improved BOTH (trade median +106.1, book +2.58). The coupling failure appeared in the *other* direction: B4 has the best run ratio and the worst book |
| **Q4** | C1 (partner disagreement) does nothing | **CONFIRMED** — +0.97, +0.96, −0.12, none beating its null |
| **Q5** | B4/B5 lower cost per bar, the only rules pushing with the constraint | **HALF RIGHT.** B4 does (turnover 20.0% → 7.8–15.6%, cost ok) and is the worst on the book. B5 does NOT (24.6–30.3%). The cost-aligned rule and the profitable rule are different rules |
| **Q6** | B6 worst, B5 best of Arm B | **INVERTED** |

## 5. Two bugs found and fixed before this table was read

**The simulator credited one bar of return per turnover.** The book was marked
*after* the refill, so on any bar where a slot turned over, `r1[t]` went to both
the position leaving and the one arriving. Entry-bar returns averaged **+134 bp**
under the profit target and **−227 bp** under the trailing stop, moving the
reported book by ±73–85 bp on numbers of magnitude 7–77. **The rules were being
ranked by how often they traded.** The first table produced was entirely wrong
and had B4 at +77.02 as "the best result in the programme".

**And the obvious fix broke it the other way.** Marking before the exit test let
the exit see bar `t`'s return before deciding — look-ahead — and the oracle's
foresight collapsed from +267.5 to +9.69 bp/bar. Assertion [2] caught it in one
run.

**The correct order is decide-then-mark:** exit on information through t−1, drop
the delisted, refill from what was knowable at the close of t−1, then mark every
held position with `r1[t]` exactly once.

**NEW ASSERTION [5], and it is the one this file most needed:** total book P&L ==
total position P&L to <1e-9 relative, on five rules spanning 7.7%–29.5%
turnover — deliberately not just the control, because the defect was invisible
on a fixed-schedule book. **Assertions [1]–[4] all passed while the simulator was
wrong.** [2] and [5] together are what pin it; each alone passed one of the two
broken versions.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 19 cells + control, each against a rate- and persistence-matched null
of 200 draws, with a best-of-19 joint floor.

## Stop

**Stage 2 is closed for this candidate, as pre-registered.** Nothing clears, the
programme's stage-2 uplift stands at ~1.0× across four studies, and the
candidate stands or falls on its stage-1 evidence and its cost question — which
is where D293 left it.

**Not closed:** the exits-with-a-deeper-bench question of §3, which this design
could not pose; and the cost question, still a spread-source problem.

## Files

`data/d295_exits.json` · `scripts/run_d295_exits.py`
