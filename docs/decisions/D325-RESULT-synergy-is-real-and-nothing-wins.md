# D325 RESULT — synergy is real, my mechanism was wrong, and nothing wins on the declared condition

**Status:** RESULT. Pre-registered at `7199dac`, amended at `fe2e500`, runner at
`bc6cb7b`, all committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. ALL FIVE predictions are falsified.**

---

## 1. Q3 falsified — the premium does NOT shrink on a stronger primary

I argued **repair**: that the confluence's premium measures how weak `hist_L` is,
so a composite on a strong primary would show little. **The opposite happened.**

| composite | k | composite | its primary alone | **premium** |
|---|--:|--:|--:|--:|
| **C4 all-strong** (retrace_leg · skew_63, rsi) | 10 | **+0.583** | +0.213 | **+0.370** |
| C0 incumbent (hist_L · macd_hist, rsi) | 10 | +0.454 | +0.108 | +0.346 |
| C4 all-strong | 40 | +0.415 | +0.307 | +0.108 |
| C2 skew (skew_63 · macd_hist, rsi) | 10 | +0.314 | +0.239 | +0.075 |
| C5 rsi-primary | 10 | +0.341 | +0.585 | **−0.244** |
| C3 hist_L · strong pair | 10 | −0.190 | +0.108 | **−0.297** |

**C4, built on a strong primary, shows the LARGEST premium in the study
(+0.370) — bigger than C0's +0.346 on a weak one.** Repair predicted the reverse.

**Q5 falsified too: C4 IS the best cell**, which was synergy's best case and which
I predicted would disappoint.

## 2. But the best SINGLE still beats the best composite

**D325's declared `k` grid is {10, 40}, fixed before D323's correction — when
`retrace_leg` peaked at k=40. Corrected, it peaks at k=20, which this study does
not test.**

```
retrace_leg ALONE, k=20   +0.625      (D323, corrected)
C4 all-strong,     k=10   +0.583      the best cell here
C0 incumbent,      k=10   +0.454
```

**So synergy is real and still does not clear the best single.** That is a scope
limitation of this study's grid, not a measurement, and it is stated rather than
worked around.

## 3. Nothing wins on the condition declared before the numbers

§4 of the pre-registration: *"A composite must beat the incumbent on net Sharpe
AND not be worse on the low-price share to count as a win."*

| | netSHRP | vs C0 (same k) | **low-price share** | names/half |
|---|--:|--:|--:|--:|
| C0 k=10 | +0.454 | — | **51.5%** | 3 |
| **C4 k=10** | **+0.583** | **+0.129** | **70.9%** | 8 |
| C1 k=40 | +0.336 | +0.176 | 48.6% | 5 |
| C4 k=40 | +0.415 | +0.255 | **112.3%** | 3 |
| C5 k=40 | +0.265 | +0.105 | **104.4%** | 2 |
| C0 k=40 | +0.160 | — | **95.7%** | **1** |

**C4 beats C0 by +0.129 on Sharpe and pushes the low-price share from 51.5% to
70.9%. It is not a win.** The co-primary statistic did exactly the job D324
established it for.

**And the k=40 cells are worse than they look.** Three of them put **95.7%,
104.4% and 112.3%** of P&L in the cheapest tercile — a share above 100% means the
other two terciles are net *negative*. **C0 at k=40 has ONE name carrying half its
P&L.** Sharpe alone would have hidden all of that.

**Q4 is falsified narrowly**, by `C1` at k=40 (+0.336 against C0's +0.160, with a
48.6% low-price share) — a k-matched comparison against one of C0's weakest cells.

## 4. The specific pair matters enormously — Q7's failure is the sharpest result

```
hist_L + (macd_hist, rsi)        +0.454      the incumbent
hist_L + (retrace_leg, skew_63)  -0.190      the same primary, a "stronger" pair
```

**Swapping in two individually stronger signals as the pair destroys the book** —
a swing of −0.644. Q7 predicted the opposite.

**So the premium is not "add strong signals".** C3 pairs the strongest available
components onto the incumbent's own primary and produces the worst cell in the
study. **What the confluence does is specific to `macd_hist` and `rsi` together**,
and neither "repair" nor a naive "synergy" explains that.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | reproduction, and the degenerate composite | **CONFIRMED** — C0 reproduces D323's incumbent at 0.0e+00, and `pair=(primary,primary)` reproduces the single book at 0.0e+00 for all four |
| **Q2** | every composite beats its own primary | **FALSIFIED** — 5 of 12 cells have a negative premium |
| **Q3** | **the premium shrinks on stronger primaries** *(load-bearing)* | **FALSIFIED** — C4's +0.370 exceeds C0's +0.346 |
| **Q4** | no composite wins on Sharpe and holds the low-price share | **FALSIFIED** narrowly, by C1 at k=40 |
| **Q5** | C4 is not the best cell | **FALSIFIED** — it is |
| **Q7** | C3 beats C0 | **FALSIFIED** — C3 is the worst cell in the study, by −0.644 |

**Five of six falsified, and the mechanism I argued for is dead.** The composite
premium is not repair.

## 6. What this actually establishes

1. **Combination is a real and large effect** — +0.370 at its best, on a strong
   primary. It is not an artefact of a weak `hist_L`.
2. **It is not additive in signal strength.** The strongest available pair on the
   incumbent's primary produces the worst book here. **Which signals combine
   matters more than how strong they are individually**, and nothing in this
   programme predicts which pairs work.
3. **No composite improves the book on the declared condition**, and the
   composition statistics kill several cells that Sharpe alone would have
   promoted.
4. **The best single still leads**, at a `k` this study did not test.

## 7. What is owed

1. **`retrace_leg` alone at k=20 (+0.625) against C4 at its own best `k`** — the
   comparison this grid missed. One cheap sweep, and it decides whether the
   composite construction survives at all.
2. **Why `(macd_hist, rsi)` works and `(retrace_leg, skew_63)` does not.** §4 is
   the largest unexplained effect now on the table, and pair *correlation* is the
   obvious first place to look — a pair that agrees adds nothing, and one that
   disagrees may be doing the work D291's `disagree` term was built for.
3. **Nothing here is promoted**, and any cell that eventually is must be confirmed
   on a construction this set was not drawn from — §0's caveat about choosing the
   set with knowledge of the leaderboard stands.

## 8. Assertions

All five pass, and **[1b] is the one that earned its place** — it caught D323's
short-leg defect at a 12 bp discrepancy, and now passes at **0.0e+00 for all four
singles**, so composites and singles are demonstrably comparable and the premium
column is a real number.

| | |
|---|---|
| **[1]** | C0 reproduces D323's incumbent at k=10 and k=40 to **0.0e+00 bp** |
| **[1b]** | `pair=(primary,primary)` reproduces that primary's single book to **0.0e+00** for all four singles |
| **[2]** | causality — rotating `rankT` moves gross +29.61 → +0.84 |
| **[S]** | the round trip spans **90%** across composites (66.5 to 126.5) — data-dependent, not a constant |
| **[C]** | `rt × turn` = 52.1893 reproduces d295's; doubled form rejected |

## 9. Files

`data/d325_composites.json` · `scripts/run_d325_composites.py`
