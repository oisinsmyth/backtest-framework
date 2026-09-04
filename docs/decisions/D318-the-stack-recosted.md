# D318 — the stack re-costed, and D306's net/Sharpe conflict dissolves

**Status:** RE-COSTING of published cells. Runs no book, scores no rule, closes
nothing. Corrects **D306 §3** and completes the fix **D307** began.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Three cost defects, and only one had been fixed

1. **The exit axis was charged per-cell.** D307 found that at N=2 the no-exit book
   measures a round trip of 86.7 and the target book 73.2 — a 16% gap caused only
   by the exit changing *when* positions open — so four fifths of the target's
   apparent +4.05 advantage was the spread estimate. **D307 fixed two cells. The
   other 26 were never re-costed.**
2. **Commission was never charged at all** (D317). The whole spread chain charges
   Corwin–Schultz spread only.
3. **D306's published `sharpe` is a GROSS Sharpe** — verified here as
   `gross/vol × √252` to **1.1e-16**, not assumed. Its §3 compares that against
   net figures.

## 2. The two axes need opposite treatment

**Across widths — per-cell.** The spread difference is *caused by the choice under
test*: a concentrated book genuinely holds tighter, pricier names and genuinely
pays less. D300 counted that as a real second benefit and it is one.

**Within a width, across exits — common.** There the spread difference is
incidental to what is being tested. That is D307's finding.

**So every depth is charged its own no-exit book's round trip, applied to all four
exit variants at that depth** — per-cell on the width axis and common on the exit
axis at once. Plus IBKR per-share commission on D300's held median price.

## 3. The re-costed stack

| cell | gross | spread | comm | **NET** | net pub | **netSHRP** | grossSHRP |
|---|--:|--:|--:|--:|--:|--:|--:|
| **N=2 / target** | +32.89 | 20.90 | 0.63 | **+11.36** | +15.25 | +0.261 | +0.754 |
| **N=2 / none** | +28.57 | 17.37 | 0.53 | **+10.67** | +11.20 | **+0.288** | +0.770 |
| N=2 / none+overlay | +20.61 | 12.78 | 0.53 | +7.30 | +7.83 | +0.219 | +0.617 |
| N=2 / target+overlay | +21.96 | 15.71 | 0.63 | +5.61 | +8.69 | +0.144 | +0.562 |
| N=3 / target+overlay | +21.49 | 17.04 | 0.76 | +3.69 | +5.52 | +0.131 | +0.764 |
| N=5 / none+overlay | +15.60 | 11.01 | 0.76 | +3.83 | +4.59 | +0.191 | +0.777 |
| N=7 / none+overlay | +13.00 | 11.16 | 0.89 | +0.96 | +1.85 | +0.064 | +0.868 |
| N=19 / none | +7.54 | 21.36 | 1.69 | −15.51 | −13.82 | −1.054 | +0.512 |

**Best by net: `N=2 / target`, +11.36. Best by net Sharpe: `N=2 / none`, +0.288.**

## 4. D306 §3's net/Sharpe conflict was an artefact

D306 reported *"net and Sharpe point at different books, sharply — N=2/target at
+15.25 net against N=7/none+overlay at +0.868 Sharpe, a 3× difference in
volatility"*, and read it as the dedicated-vs-shared-capital choice arriving on a
second axis.

**That +0.868 is a GROSS Sharpe.** On **net** Sharpe, D306's own published numbers
already pointed at **N=2/target (+0.350)**, and after re-costing at **N=2/none
(+0.288)**. N=7/none+overlay is **+0.064**.

**Both objectives point at N_eff = 2.** There is no 3× volatility trade-off to
make. D306 §3 is corrected.

## 5. What each exit is actually worth, per depth

Net bp/bar, charged the depth's common round trip:

| N | **target − none** | **overlay on none** | overlay on target |
|--:|--:|--:|--:|
| **2** | **+0.69** | **−3.37** | −5.75 |
| 3 | +3.48 | +3.27 | +0.29 |
| 5 | −2.39 | +4.55 | +3.85 |
| 7 | −4.41 | +5.98 | +8.59 |
| 10 | −2.54 | +4.25 | +5.28 |
| 14 | −2.93 | +4.68 | +7.28 |
| 19 | −1.27 | +6.53 | +3.69 |

**The two exits are mutually exclusive in sign.** The target pays only at N = 2
and 3; the overlay pays only at N ≥ 3 and costs 3.37 bp at N = 2.

**And +0.69 at N=2 independently reproduces D307's +0.80** and D305's +0.79 at
N=19 — three routes to the same number. **The target is worth about +0.7 to +0.8
bp/bar, charged honestly, and only where the book is concentrated.**

## 6. Commission, per depth

| N | held median price | bp/side | added to rt |
|--:|--:|--:|--:|
| 2 | $75.95 | 0.66 | **2.63** |
| 10 | $36.96 | 1.35 | 5.41 |
| 19 | $23.72 | 2.11 | **8.43** |

**It works in concentration's favour** — the same price effect D300 found on the
spread — and changes no verdict, being 3–8% of a round trip.

## 7. What this is not

- **Commission is estimated from a per-depth median price**, not derived per
  symbol as D264 did. A correction of the right order, not a measurement. The
  `min($1.00)` and 1%-of-notional arms are ignored, which needs a position-size
  assumption this study does not make.
- **No cell is re-tested against a null.** These are re-costings of cells whose
  nulls were run in D300 and D306; the rankings move, so **the null p-values no
  longer attach to the cells they were computed for** on the exit axis.
- **D316's power result still binds:** at this concentration a paired per-bar test
  has an MDE near 18 bp, so **+11.36 and +10.67 are not distinguishable from each
  other.**

## 8. The stack, as it stands

```
signal        the D293 confluence           min z +2.58 across three nulls
construction  factor-neutral spread         removes -mu - sigma^2  (D285)
width         N_eff = 2, FIXED              basis-immune, +21 bp over N=19 (D300)
exit          the target, or nothing        +0.69 bp/bar, and only at N<=3
overlay       OUT at this width             -3.37 bp/bar at N=2
```

**Net +11.36 bp/bar, net Sharpe +0.261, gross Sharpe +0.754**, charged its own
held-name spread and IBKR commission.

## 9. Files

`scripts/d318_stack_recost.py` · `data/d318_stack_recost.json`
