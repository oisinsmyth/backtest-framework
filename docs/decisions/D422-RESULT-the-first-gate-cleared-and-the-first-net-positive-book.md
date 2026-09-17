# D422 RESULT — the first gate cleared, the first net-positive book, and the candidate still fails

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D422-RESULT-the-first-gate-cleared-and-the-first-net-positive-book-and-the-candidate-still-fails.md`. The H1 above is the full title.*

**FAILS THE CANDIDATE CONDITION: T1 clears, T2 is UNRESOLVED, T3 fails.** Pre-registration
`1c3044b` predates the runner and this file (R8). **The ledger does not move. Nothing was admitted.
No holdout was read — the condition that would have permitted it was not met.**

Cost: 257 s, plus 40 s of extras.

```
[STAGE0]  every flag share reproduces the record's section 2a
P2        D419's FIXED book reproduced bit-identically before any depth book ran
[RECON]   every book;  [CHUNK]  worker draw 0 == in-process
```

---

## 1. The bar — STACK2-SAME

```
T1  second half (2018-2026), pooled:  +13.60 ± 5.48 bp    +2.5 SE     CLEARS
T2  pooled, vs within-day permutation: +6.43 vs p95 +6.77 (±0.22)   -1.5 SE   UNRESOLVED
T3  cell-2 SAME-REQUIRED book:  net +0.508 (all three seeds positive)
                                 vs random pools of the same count: p95 +0.636 (±0.115)   -1.1 SE   FAILS
CANDIDATE                        NOT MET
```

**T1 is the first gate to clear in twenty-two studies**, and it cleared on the second-half number
— the half every prior edge had shrunk in. **T3 produced the first net-positive book in the
line**, positive on every seed. **And the condition still fails**, because the same-side rung's
pooled premium sits at its null's edge and its book does not beat a random pool of the same size
at p95. Both misses are honest misses: T2 is inside 2 SE of the p95 (D373's rule says UNRESOLVED,
and a sample p95 is biased toward the centre, so more draws would likely make the fail clearer,
not reverse it); T3's book beats the random pool's *median* by 1.2 bp/bar and not its p95.

---

## 2. THE SIDE RESTRICTION WEAKENED EVERYTHING — the stronger arm was the secondary

```
                     pooled            2018+             cell 2           cell 2 2018+
STACK2-SAME   gap    +6.43 (+1.7)     +13.60 (+2.5)     +12.27 (+1.4)    +13.40 (+1.2)
STACK2-ANY    gap    +9.48 (+3.1)     +17.76 (+3.9)     +22.84 (+2.9)    +28.07 (+2.7)

within-day permutation      SAME pooled  -1.5 SE (unresolved)     SAME 2018+  +15.1 SE
                            ANY  pooled  +9.7 SE                  ANY  2018+  +20.3 SE
```

**The side-blind rung is stronger in every cell, and it clears every per-trade null decisively.**
X-a predicted the same-side restriction would sharpen the rung to +8–14; it *cut* it to +6.43.
The prior touch that makes the second zone pay is not required to be the same side.

**And its book is the best in the record:**

```
cell 2, 10 slots      gross     net     cost    util    per trade    net by seed
FIXED                +4.590   -0.718   5.308   92.3%    +24.85
SAME-REQUIRED        +3.564   +0.533   3.031   52.4%    +33.99      [+0.53, +0.64, +0.35]
ANY-REQUIRED         +4.889   +0.993   3.896   68.2%    +35.85      [+0.99, +1.51, +1.20]
FLIP-REQUIRED        +2.107   -0.517   2.624   46.5%    +22.65      [-0.52, -0.60, -0.52]
```

**ANY-REQUIRED has a *higher* gross per bar than FIXED at 68% utilisation** — it selects better
trades *and* takes fewer of them, both levers at once, which no prior book here has done — and it
nets +1.24 bp/bar on every seed. **Run as an extra, after the primary, with the control the
pre-registration ran only for SAME: it beats a random pool of the same count at +5.4 SE**
(p95 +0.493 ± 0.137).

**It cannot clear D422.** It was declared secondary, and the control that would have cleared it was
run after the result was seen. **Under D408's rule it earns exactly one thing: its own
pre-registration, with T3's control declared in advance.** That is the only legitimate next step
this record contains.

---

## 3. THE FLIP CLAIM HAS THE WRONG SIGN, AND IT IS SAID IN THOSE WORDS

The declared reading, printed by the runner:

> **NEGATIVE by more than 2 SE — the claim has the wrong sign here. −13.95 bp, −4.0 SE pooled;
> −8.79 second half.**

```
FLIP  pooled   yes  +2.44 (median 0.00)    no  +16.39     gap  -13.95 ± 3.52   -4.0 SE
FLIP within STACK2-ANY:   flip  +2.82 (n 14,164)    not flip  +24.13 (n 49,133)    -21.31   -3.8 SE
FLIP concentration:       2 names to half the P&L;  top name 29.2%;  2020 = 111.5% of the P&L
```

**A zone sitting on a broken opposite-side level pays essentially nothing** — +2.44 bp, median
zero — **and it drags down whatever it is combined with**: inside the second-zone rung, the events
that sit on a flipped level pay +2.82 against +24.13 for those that don't. Its P&L is two names and
one year; outside 2020 the population is net-negative. The FLIP-REQUIRED book is the only cell-2
required book that loses money.

**On this construction, "supply becomes demand" is not merely empty; it selects against.** A
broken level is a breakdown, which is what D421's DEEP-2-only cell (+4.95) had already said from
the same-side direction. The claim is dismissed with a sign, not a shrug — and the principal's
instruction to test it before dismissing it is what makes the dismissal worth anything.

**One caveat on what was tested.** FLIP is the claim as it *reads* — a new zone at a broken
opposite-side level. It is not the same as "a prior opposite-side touch somewhere on the name,"
which is the half of STACK2-ANY that SAME excludes, and which *helps* (§2). Those two things are
different: activity on the name is not the same as this level having changed role.

---

## 4. THE HUMP HOLDS, AND THE TREND IS WHERE CELL 2 DIES

```
                 STACK1    STACK2-SAME   STACK2-ANY   STACK3+
pooled            +9.81      +18.44        +19.36       +9.96
cell 2           +29.87      +39.53        +44.84      +14.75
cell 2 2018+     +23.48      +36.91        +44.68      +10.44
```

X-e held. Under distinct-day counting the second rung still pays double the first and the third
pays like the first — and in cell 2's second half the third-or-later rung pays **+10.44 against
+44.68**: the trend is where the cell's edge goes to die.

---

## 5. THE TIME STRUCTURE — T1's pass is a 2020-onward number, and that is a warning

```
STACK2-SAME premium by year    2010 -0  2011 -10  2012 +4  2013 +12  2014 -6  2015 +4  2016 -16  2017 -5
                               2018 -15  2019 -12  2020 +22  2021 +9  2022 +2  2023 +2  2024 +21  2025 +27  2026 +92
STACK2-ANY  by year            2010 -6  2011 -24  2012 +5  2013 +5  2014 +6  2015 +1  2016 +6  2017 -6
                               2018 +2  2019 +16  2020 +38  2021 +14  2022 +29  2023 +9  2024 +20  2025 -7  2026 +56

SAME   2018-2019 mean  -16.13       2020-2026 mean  +30.03
ANY    2018-2019 mean    0.00       2020-2026 mean  +26.14
```

**The second-half premium is entirely a 2020-onward premium.** 2018–2019 contribute nothing or
worse; 2020 — the pandemic reversal — and 2026 — a partial year — are the largest single
contributions (2026 is 21.8% of SAME's P&L). X-b predicted the premium would be present at *half*
its pooled size in the second half, following every prior edge's decay; **it is *double* the
pooled size, concentrated late.** That is the reverse of the base edge's front-loading, and it is
not more comforting: **a premium that lives in seven years, one of them a regime and one of them
incomplete, is exactly the kind that has looked good here and died.** It is the first thing any
pre-registration of the ANY rung would have to survive — declared, on a window that excludes 2020.

---

## 6. Predictions — two of five

| | prediction | outcome |
|---|---|---|
| X-a | SAME premium +8 to +14 | **wrong, low** — +6.43; the side restriction cut it |
| X-b | second half positive at half the pooled size | **wrong direction** — double, and late-concentrated |
| **X-c** | FLIP inside 2 SE of zero | **wrong — −4.0 SE, inverted, not empty** |
| **X-d** | SAME-REQ book net-positive at 1–2 SE, inside its control's p95 | **correct** — +0.508 on all seeds, +1.3 SE vs FIXED, −1.1 SE vs the control |
| X-e | the hump persists | correct |

X-d was the study and it held exactly. The three misses are, again, about what the structure
*means*: the side does not need to match, the flip is not a support, the premium is not decaying
but arriving.

---

## 7. What this leaves

1. **Not a candidate.** The declared condition is T1 and T2 and T3 on the primary; T2 is
   unresolved at the null's edge and T3 fails at −1.1 SE. **The holdout stays shut**, by the rule
   the principal set and this study wrote against itself.
2. **STACK2-ANY — the side-blind second zone — earns a pre-registration and nothing else.** It
   clears both per-trade nulls, its cell-2 required book nets +1.24 on every seed at higher gross
   than FIXED, and it beats its random pool at +5.4 SE — all measured on the secondary arm, the
   last of them after the fact. Declared in advance, with T3's control and a window excluding 2020,
   it would be the first pre-registration in this line with a positive prior on every gate.
3. **The flip claim is closed by measurement, with its sign.**
4. **The premium is a 2020–2026 phenomenon.** Whatever survives the holdout survives on a window
   the base edge had already left.
5. **Twenty-two of twenty-two have failed their bar.** This is the first to clear a gate and the
   first to produce a book that makes money net of cost. It is also the one whose pre-registration
   chose the wrong primary for a mechanism reason — the same failure mode as D418 and D421, in a
   different place.

**Disposition is the principal's.**

---

## 8. R13

Twenty-second look by object on price levels. No new data spent.

**Evidence:** `data/d422_second_zone.json` (both lenses, all arms, the nulls, 24 books, the
control) and `data/d422_extras.json` (the ANY control, post-hoc). Runners
`scripts/run_d422_second_zone.py` and `scripts/run_d422_extras.py`; flags
`scripts/d422_stack_flags.py`, committed with the pre-registration.
