# D297 RESULT — a narrow window where de-risking works

**Status:** RESULT. Pre-registered at `a0dd515`, grid amended at `d6799c4`, both
committed before any result existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## The result

**2 of 8 declared cells beat their own rate- and persistence-matched null**, both
at X = 12. **Q1 is falsified** — the first stage-2 arm in this programme to
produce anything.

| cell | mean | vol | **Sharpe** | maxDD | expo | ret/exp | null p95 | **p** | trans/yr | cost/bar |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **CONTROL** | +7.54 | 233.6 | **+0.512** | 9,374 | 100% | +7.54 | — | — | 0.00 | 0.000 |
| **X=12 / s=0.0** | **+8.72** | 190.2 | **+0.728** | **3,607** | 71.6% | **+12.18** | +0.631 | **0.0150** | 3.16 | 0.661 |
| **X=12 / s=0.5** | +8.13 | 202.0 | **+0.639** | 6,089 | 85.8% | +9.47 | +0.601 | **0.0250** | 3.16 | 0.331 |
| X=8 / s=0.5 | +6.33 | 190.7 | +0.527 | 5,767 | 79.8% | +7.94 | +0.591 | 0.274 | 7.12 | 0.744 |
| X=8 / s=0.0 | +5.13 | 174.1 | +0.468 | 6,353 | 59.6% | +8.61 | +0.613 | 0.329 | 7.12 | 1.488 |
| X=20 / s=0.0 | +5.62 | 206.7 | +0.432 | 9,477 | 80.6% | +6.98 | +0.649 | 0.550 | 3.64 | 0.760 |
| X=20 / s=0.5 | +6.58 | 213.7 | +0.489 | 9,425 | 90.3% | +7.29 | +0.602 | 0.571 | 3.64 | 0.380 |
| X=30 / s=0.0 | +6.69 | 229.7 | +0.462 | 9,374 | 95.5% | +7.00 | +0.587 | 0.752 | 1.58 | 0.331 |
| X=30 / s=0.5 | +7.11 | 230.7 | +0.489 | 9,374 | 97.8% | +7.28 | +0.553 | 0.768 | 1.58 | 0.165 |

**X = 12 / s = 0.0 raises Sharpe 42% (+0.512 → +0.728) and cuts maximum drawdown
62% (9,374 → 3,607 bp), while earning MORE in absolute terms (+8.72 vs +7.54) on
71.6% of the exposure.** Cells at p < 0.05: **2 of 8** against 0.40 expected.
Benjamini-Hochberg keeps both at q = 0.10.

## The shape: a hump, not a spike

X = 12 is an interior point of a grid chosen post-hoc, which is where this
programme has been burned before (`hist_L`'s N = 25). Swept finely
(`scripts/d297_fine_sweep.py`, 300 draws per X):

| X | 6 | 8 | 10 | **11** | **12** | **13** | **14** | 16 | 18 | 20 | 25 | 30 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **Sharpe** | +0.148 | +0.468 | +0.617 | **+0.656** | **+0.728** | **+0.661** | **+0.672** | +0.602 | +0.488 | +0.432 | +0.453 | +0.462 |
| **p** | 0.887 | 0.359 | 0.100 | **0.047** | **0.033** | **0.040** | **0.050** | 0.060 | 0.329 | 0.568 | 0.641 | 0.787 |

**Four CONTIGUOUS thresholds clear** — 11, 12, 13, 14 — rising smoothly from 6
and falling smoothly to 19. A genuine interior optimum with a coherent story:
too tight and the rule whipsaws, too loose and it never protects. **Unlike
`hist_L`'s N = 25, this is not a knife-edge.**

**And the sobering half: the MEDIAN Sharpe across X ∈ [6,30] is +0.455, BELOW
the control's +0.512.** Most thresholds hurt. The window that works is roughly
X ∈ [10,16], about a quarter of the range swept.

4 of 25 swept thresholds clear p < 0.05 against 1.25 expected — but they are
contiguous, so that is **one finding, not four.**

## Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | no cell beats its own null | **FALSIFIED** — 2 of 8 declared, 4 of 25 swept |
| **Q2** | every cell cuts vol and maxDD | **MOSTLY** — but X=20/s=0.0 has maxDD **9,477 against the control's 9,374**, and X=30 is exactly equal. A loose threshold fires late enough to lock a drawdown in rather than prevent it |
| **Q3** | return-per-unit-exposure unchanged; the drawdown state carries no timing information | **FALSIFIED IN THE WINDOW, CONFIRMED OUTSIDE IT.** X=12 earns **+12.18** per unit exposure against the control's +7.54 — 61% better, so the drawdown state *does* carry timing information there. The median declared cell is +7.62 ≈ control, so it carries none anywhere else |
| **Q4** | transition cost exceeds any Sharpe gain | **FALSIFIED for the winner.** X=12/s=0.0 gains +1.18 bp/bar of mean and pays **0.661 bp/bar** in transition cost — net **+0.52 bp/bar** — on only **3.16 transitions a year** |
| **Q5** | s = 0.5 beats s = 0.0 | **MIXED** — s=0.5 wins at X = 8, 20 and 30, and loses at X = 12 where it matters (+0.639 vs +0.728) |
| **Q6** | the tightest threshold is worst | **CONFIRMED** — X = 6 is the worst swept at +0.148, less than a third of the control |

## What this is, and what it is not

**IT IS NOT EDGE.** The overlay cannot create return; it scales exposure. What
the result says is that **this book's drawdown state carries timing
information** — bars following a ~12-vol drawdown are worse than average, and
skipping them raises return per unit of exposure by 61%.

**IT IS THE FIRST STAGE-2 RESULT IN THIS PROGRAMME.** Across D285, D286 and both
arms of D295 the measured uplift was ~1.0×. This is the first arm to beat its
own null, and it does so on the dimension stage 2 is supposed to supply:
**risk-adjusted** return, not gross.

**AND IT IS MARGINAL.** p = 0.033 at the peak, 0.047–0.050 at the window's
edges, one contiguous finding rather than four, and the median threshold across
the swept range is worse than doing nothing.

## The caveats that matter

**The grid was chosen post-hoc from the exposure profile** (see the amendment).
The null holds exposure exactly equal to the treatment's, so that choice cannot
bias any individual cell's test — but the *region* was located with knowledge of
this book.

**The window is about a quarter of the swept range.** A rule that works on
[10,16] and not on [6,9] or [17,30] needs a reason to prefer 12 that is not
"it won here".

**Nothing about cost is settled, and it decides this.** The 0.661 bp/bar
transition cost uses the robust round trip of 105.4 bp. Under the mean
aggregation (260.7 bp) it is **1.63 bp/bar, which EXCEEDS the +1.18 bp/bar gain
and reverses Q4.** The cost-estimator ambiguity from D293's correction is what
determines whether this pays.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 8 declared cells at 1000 draws each, plus a 25-point fine sweep at
300 draws, plus the exposure profile that set the grid.

## Stop

**Book-level exposure management is NOT closed** — it is the one thing in four
stage-2 studies that beat its own null.

**What it needs before it means more:** the window located on data this book has
not seen, and the cost question settled, because under one of the two defensible
spread aggregations the winner stops paying.

## Files

`data/d297_overlay.json` · `scripts/run_d297_overlay.py` ·
`scripts/d297_fine_sweep.py` · `scripts/d297_spread_stop_premise.py`
