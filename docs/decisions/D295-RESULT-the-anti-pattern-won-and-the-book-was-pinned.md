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

---

# AMENDMENT — 2026-09-03: the floor and the cost gate were promotion instruments, and this stage promotes nothing

Raised by the principal, and it is **the same correction made on D291 that this
study then repeated.** Two of the four pre-registered pass conditions do not
belong at this stage:

- **the best-of-19 joint floor** controls the chance that *any* cell is a false
  positive. That is the right question when a study makes one claim. **The mined
  fixture is not spent, no holdout is read, and nothing is promoted** — the
  question is which cells to *carry*, not which to certify.
- **the cost gate** is a stage-3 question. Cost coverage was made a pass
  condition here; it should be reported and nothing more.

Re-scored on **"beats its own rate- and persistence-matched null"** alone, cost
reported not gating (`scripts/d295_false_positive_rate.py`).

## The re-scored screen

| cell | Δ bp/bar | Δ t | **p** | turnover | cost/bar | run w/l | screen |
|---|--:|--:|--:|--:|--:|--:|:--|
| **B6@1.0** target | +4.95 | +2.58 | **0.0050** | 25.0% | 26.34 | 0.64 | **YES** |
| **C3** wide-spread idle | +0.25 | +0.10 | **0.0050** | 20.0% | 21.08 | 1.00 | **YES** |
| **B5@1.0** asym | +3.73 | +1.78 | **0.0100** | 30.3% | 31.97 | 1.26 | **YES** |
| **B5@1.5** asym | +3.73 | +1.78 | **0.0149** | 26.7% | 28.18 | 1.05 | **YES** |
| **B1** reversion | +3.73 | +1.78 | **0.0299** | 29.5% | 31.12 | 0.76 | **YES** |
| **B5@2.0** asym | +3.73 | +1.78 | **0.0299** | 24.6% | 25.92 | 0.91 | **YES** |
| B6@2.0 | +2.54 | +1.33 | 0.1592 | 21.5% | 22.62 | 0.87 | no |
| … | | | | | | | |
| B4@1.0 trailing | −3.04 | −1.14 | 0.9801 | 15.6% | 16.39 | 2.66 | no |
| B4@1.5 trailing | −5.86 | −2.05 | 0.9950 | 10.6% | 11.15 | 2.56 | no |
| B4@2.0 trailing | −9.38 | −2.98 | **1.0000** | 7.8% | 8.26 | 2.45 | no |

## The false-positive arithmetic

```
cells at p < 0.05          6 of 19
expected by luck (0.05m)   0.95

THE COUNT, against the null's OWN correlated structure:
  observed                 6
  null p50 / p95 / max     1 / 3 / 4
  P(null count >= 6)       0.0%     <- not one draw of 200 reached it

BENJAMINI-HOCHBERG
  q = 0.05  ->  keep 2
  q = 0.10  ->  keep 6
  q = 0.20  ->  keep 6
  q = 0.50  ->  keep 8
```

**Six survivors against 0.95 expected, and the null's own joint distribution
never once produced six in 200 draws.** BH keeps all six at q = 0.10 — a
shortlist in which roughly **16%** is expected to be noise.

**This is the strongest screen result the programme has produced**, and the
pre-registered verdict of "0 of 19" was an artifact of applying a promotion bar
to a screen.

## The caveat that matters most

**B1 and all three B5 cells are ONE book, not four findings.** They report
identical returns to four decimal places (§1) because the book is pinned to the
selected 19. Their p-values differ only because each is scored against its own
turnover- and persistence-matched null.

So the six survivors are really **three distinct findings**:

1. **B6@1.0** — the profit target, p = 0.005
2. **B1 / B5** — exit when the name leaves the selected set, p = 0.010–0.030
3. **C3** — the wide-spread idle, p = 0.005

**And the count test is optimistic about this.** Under the null those four cells
decorrelate (each draws its own random runs), so the null's joint distribution
does not carry the exact duplication the observed cells have — its measured sd
was 1.0× the binomial, i.e. it treated them as independent when they are not.
Three findings from ~16 effectively distinct books against ~0.8 expected is still
a clear excess, but it is **three, not six**.

**C3 clears on a weak claim.** Its Δ is only +0.25 bp/bar; it clears because its
null is centred *negative* (p50 −0.94), i.e. a random idle at matched rate
*hurts* and C3 does not. And it keys on the estimator that clamps 41.9% of cells
to zero, exactly as the pre-registration flagged.

## What does NOT change

**B4 fails on its own null too**, not merely on the floor: p = **0.98, 0.995,
1.000**. "Let the winners run" is not a marginal miss on this book — it is
decisively the wrong direction, and §2's mechanism explains why.

**Section 3 stands unchanged and is still the binding limitation:** slots equal
the selection size, so no rule could ever promote a *better* name into a freed
slot. Every one of the three findings above is a statement about how fast the
book returns to the current selection.

**Cost is reported and gates nothing here.** For the record, all three survivors
raise turnover (25.0%, 24.6–30.3%, 20.0% against the control's 20.0%) and none
covers its round trip — but that is a stage-3 question and this record should not
have treated it as a stage-2 one.

---

# ADDENDUM — 2026-09-03: why the trailing stop loses, measured

`scripts/d295_why_trailing_fails.py`. The decay curve is measured on a **long
fixed hold** (every position lives exactly 25 bars), so each age is sampled by
the same population and the curve is the signal's own rather than a rule's.

## 1. The edge is front-loaded and then it is gone

| age | position-bars | bp/bar |
|--:|--:|--:|
| 1 | 4,875 | **+18.46** |
| 2 | 4,873 | +9.80 |
| 3 | 4,870 | +12.59 |
| 4 | 4,868 | +8.74 |
| 5 | 4,866 | +3.45 |
| 10 | 4,861 | +7.21 |
| 15 | 4,834 | −1.96 |
| 20 | 4,822 | −2.27 |
| 25 | 4,813 | −2.76 |

```
age 1-5   +10.61 bp/bar   over  24,352 position-bars
age 6+     -1.14 bp/bar   over  96,754 position-bars
```

## 2. And "front-loaded" is really "while the name is still selected"

```
in the selected set     +9.74 bp/bar   over 32,310 bars
out of it               -1.87 bp/bar   over 88,796 bars
```

The two cuts are the same fact: a name is selected while its signal is fresh,
and the edge is worth **+9.74 bp/bar** for exactly that long.

## 3. Where each rule spends its exposure

| rule | bar-weighted mean age | % of bars at age ≤ 5 | **% of bars OUT of selection** |
|---|--:|--:|--:|
| B0 — 5-bar hold | 3.00 | 100.0% | **26.5%** |
| **B4@1.0** trailing | 6.20 | 57.4% | **45.7%** |
| **B4@2.0** trailing | 9.96 | 35.4% | **61.4%** |

**That is the whole explanation.** The trailing stop puts 46–61% of its exposure
into bars worth −1.87 bp, against the baseline's 26.5%.

## 4. And the trailing stop is the worst possible shape for this edge

A trailing stop exits only after the position **gives back** `p × vol` from its
peak. On an edge that is front-loaded and decays:

1. the peak arrives in the first few bars, while the name is still selected
2. the position then drifts sideways at ≈0 bp
3. the stop cannot fire until the drift has cost `p × vol`
4. so it exits **after the edge is gone AND after handing part of it back**

Widening the stop makes it strictly worse — B4@2.0 waits longer, holds 61.4% of
its bars out of selection, and loses most (−9.38 bp/bar, p = 1.000).

**The rule is not badly tuned. It is structurally mismatched to the signal**, and
that is why every parameter fails in the same direction.

## 5. What this says about the principle

**"Let the winners run" presumes the winner keeps winning.** Here the winner is
whoever is *currently ranked best*, and that title moves to another name within
days. Running a position is holding a name that has already handed the title
over.

**The corollary is testable and not tested here:** on a signal whose edge does
NOT decay — a trend rather than a cross-sectional rank — the same rule should
win. Nothing in this study speaks to that, and §3 of the main record still
applies: with slots equal to the selection size, no rule here could promote a
better name into a freed slot.

---

# CORRECTION — 2026-09-03: B4 was a malformed test, and the addendum's conclusion is withdrawn

Raised by the principal: *"this seems like a malformed trailing stop rather than
pointing at the fact that trailing stops do not work."* Correct.

## What B4 actually varied

B4 changed **two things at once** — it made the exit trailing AND removed the
5-bar cap — so no comparison in the study could separate them. Post-hoc
diagnostic cell `trailing_capped`, which is B4 with the cap put back:

| cell | cap | bp/bar | vs B0 | Δ t | run | w/l | turnover | **% bars out of selection** |
|---|:--|--:|--:|--:|--:|--:|--:|--:|
| trailing@1.0 | **no** | +4.50 | −3.04 | −1.14 | 6.4 | 2.66 | 15.6% | **45.7%** |
| trailing@1.5 | **no** | +1.68 | −5.86 | −2.05 | 9.5 | 2.56 | 10.6% | **54.7%** |
| trailing@2.0 | **no** | −1.84 | −9.38 | −2.98 | 12.8 | 2.45 | 7.8% | **61.4%** |
| **trailing_capped@1.0** | yes | **+8.57** | **+1.03** | +0.58 | 3.7 | 1.63 | 26.8% | 22.0% |
| trailing_capped@1.5 | yes | +6.93 | −0.61 | −0.32 | 4.2 | 1.36 | 23.6% | 22.7% |
| **trailing_capped@2.0** | yes | **+8.46** | **+0.92** | +0.50 | 4.6 | 1.21 | 22.0% | 23.1% |
| B0 — 5-bar hold | yes | +7.54 | — | — | 5.0 | 1.00 | 20.0% | 26.5% |

**The trailing rule is neutral-to-mildly-positive when capped** (Δt +0.58,
−0.32, +0.50 — noise, with the outer two above the control) and **decisively
negative when uncapped**. The out-of-selection share moves 22% → 61% and the P&L
tracks it.

## WITHDRAWN

> *"the trailing stop is the worst possible shape for this edge … the rule is
> not badly tuned, it is structurally mismatched to the signal"*

**That is wrong.** The mismatch is with holding a position after the signal stops
selecting it. Trailing was the vehicle I attached that to, and the write-up
generalised from a confounded cell to a claim about a rule family.

**The decisive comparison was already in the pre-registered data and I missed
it.** B4 and B5 are both uncapped and stop losers identically — for a losing
position `peak = 0`, so B4's `(peak − cum) ≥ p·vol` IS B3's adverse stop. They
differ in exactly one thing:

| | loser exit | **winner exit** | result |
|---|---|---|--:|
| **B5** | `cum ≤ −p·vol` | **name leaves the selected set** | **+3.73**, p = 0.010 |
| **B4** | `cum ≤ −p·vol` (identical) | **gives back p·vol from peak** | **−3.04**, p = 0.980 |

**The entire 6.77 bp/bar gap is in the winner exit**, and the finding is:
*on a decaying cross-sectional edge, the winner's exit signal must be the SIGNAL,
not the price path.* That is narrower and more useful than what the addendum
claimed.

## What survives from the addendum

The decay curve is unaffected and remains the mechanism: **+10.61 bp/bar at age
1–5, −1.14 at age 6+; +9.74 in the selected set, −1.87 out of it.** Any rule that
raises out-of-selection exposure loses in proportion, whatever its shape.

## And for the principle

`trailing_capped@1.0` **does** trim losers and let winners run — run ratio
**1.63** within the cap — and is the best non-anti-pattern cell tested at +8.57
against the control's +7.54. Not significant, but pointing the right way. **The
principle was never actually tested by B4**; it was tested by B5, which screens
at p = 0.010, and by this cell, which is a post-hoc diagnostic and not
pre-registered.

## Disclosure

`trailing_capped` is a **post-hoc diagnostic cell, added after the result and
not in the pre-registration.** It carries no null and does not enter any count,
floor or FDR. It exists to separate two things a pre-registered cell conflated,
and its numbers are descriptive only.
