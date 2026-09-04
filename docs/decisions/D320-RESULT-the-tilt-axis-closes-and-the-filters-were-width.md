# D320 RESULT — the tilt axis closes, and the filters that "worked" were width in disguise

**Status:** RESULT. Pre-registered at `a14ea24`, runner at `e6885ad`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Q2 confirms and the tilt axis closes at the operating point

**No filter beats its price-matched control while being profitable and surviving
its own null.** At `N_eff` = 2:

| cell | netSHRP | price-matched | held ½-spread | held price | **p** |
|---|--:|--:|--:|--:|--:|
| **control** | **+0.334** | — | 18.31 | $70.70 | — |
| spread10 | +0.168 | +0.334 | 18.13 | $71 | 0.886 |
| spread25 | +0.008 | +0.341 | 16.73 | $74 | 1.000 |
| spread40 | −0.008 | +0.252 | 15.68 | $80 | 0.915 |
| price25 | +0.282 | — | 16.79 | $75 | 0.393 |
| **dv25** | **+0.464** | **+0.305** | **14.61** | **$72** | **0.119** |
| dv40 | +0.400 | +0.262 | 17.88 | $76 | 0.085 |

**`dv25` and `dv40` do beat their price-matched controls** — and neither survives
its own null. **Q2's clause held**, the one I had written carelessly three times
before (D313 Q3, D315 QB2, D319 Q5): *beats* means beats **while profitable and
surviving its null**. Stated in full, it did its job.

**Q3 confirmed:** the spread arm is the weakest of the three, exactly as predicted
from D302's finding that the per-name Corwin–Schultz estimate is noisy. It is the
only arm that makes the book worse at every threshold.

## 2. THE D305 CONFOUND, REPRODUCED — and it destroys both BH survivors

BH-FDR over 18 cells returned two survivors, **`N=19/price25` and
`N=19/price40`** (p = 0.0050 each), and the study's best cell was
`N=19/spread40` at **netSHRP +0.672** against a control of **−1.000**.

**All three are shrunken books.** D306's simulator weights each held name `1/n_t`
within its leg — its own comment says *"NOT 1/depth"* — so **a book that cannot
fill its slots is not partly in cash. It is a fully invested, NARROWER book.**

| cell | held/bar | **fill** | ≈ per leg |
|---|--:|--:|--:|
| N=19 control | 38.00 | 100% | 19 |
| N=19/price25 | 28.29 | **74%** | 14 |
| N=19/price40 | 21.81 | **57%** | 11 |
| **N=19/spread40** | **14.34** | **38%** | **7** |

**A 40% spread filter on a 19-slot book leaves it holding seven names a leg. That
is D300's width axis arriving through the back door** — precisely the confound
[D305](D305-RESULT-only-one-arm-kept-the-book-full.md) identified and named:
*"every arm that blocks re-entry also shrinks the book … its positive net is
bought by holding half as much."*

### And my turnover divided by the wrong denominator

`turn = entries / depth / 2 / bars` uses the **nominal** slot count. The fraction
of the book actually traded divides by the names **held**, so **cost is
understated by exactly 1/fill.** Corrected (`data/d320b_fill_adjusted.json`):

| cell | fill | netSHRP published | **fill-adjusted** | net published | **adjusted** |
|---|--:|--:|--:|--:|--:|
| N=19/price25 | 74% | −0.418 | **−0.787** | −6.62 | **−12.46** |
| N=19/price40 | 57% | +0.046 | **−0.455** | +0.82 | **−8.13** |
| N=19/spread40 | 38% | +0.672 | **+0.135** | +11.10 | **+2.23** |

**Both BH survivors and the study's best cell collapse.** What remains of
`spread40` is a seven-name book earning +2.23 — which is simply a worse version of
what N = 2 already does at +14.57.

**This does not touch D306, D318 or D319**, whose books all fill 100% of their
slots. It bites only where a filter starves the gate.

## 3. At N = 2 the fill effect is small, and one thread survives it

Fill stays at 88–100% at `N_eff` = 2, so the correction is minor there:

```
control    +0.334 -> +0.334      dv25   +0.464 -> +0.433      dv40  +0.400 -> +0.340
```

**`dv25` is the one result worth remembering, and it is not significant.** It cuts
the held half-spread **18.31 → 14.61** while leaving held price essentially
unchanged (**$70.70 → $72**) — so it is *not* the price level, which is what makes
it interesting and what its price-matched control confirms. It lifts net Sharpe to
**+0.433** fill-adjusted against the control's +0.334.

**And p = 0.1194.** It does not survive its own null, or BH over 18 cells.
**Dollar volume finding tighter-spread names at the same price is a real
mechanism, measured, and too small to establish here.**

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | every spread filter cuts the held half-spread | **CONFIRMED** |
| **Q2** | **no filter beats its price-matched control** *(against, load-bearing)* | **CONFIRMED** — two beat it, neither survives its null |
| **Q3** | the spread arm is weakest | **CONFIRMED** — worse than control at every threshold at N=2 |
| **Q4** | gross falls under every filter | **FALSIFIED** — `N=19/spread40` raises gross +12.00 → +16.47, because it is concentrating, not filtering |
| **Q5** | the filters move held price more at N=19 than at N=2 | **CONFIRMED** — concentration had already moved it |

## 5. The null was rejected by an assertion, before any cell was scored

I wrote a **name-label permutation** first — it preserves each name's exclusion
run-lengths exactly and destroys only *which* names are excluded, which reads like
CLAUDE.md's *"randomise the partner, not the membership"*. Assertion [4] measured
it:

```
entries --  treatment 2,248
            ROTATED   2,282  (+1.5%)
            permuted  2,883  (+28.2%)   <- rejected
            PER-BAR   2,886  (+28.4%)   <- D291's known defect
```

**The permutation churned like the per-bar re-draw it was built to avoid**, because
names differ in liveness, so permuting labels maps a persistent exclusion pattern
onto names live at other times. **Matched count is not matched turnover** (D279),
arriving in a new place. The null is a circular time rotation; the rejected
construction stays printed in the runner so it is not quietly swapped out.

## 6. What this closes

**The tilt axis is closed at the operating point.** Every filter either loses to
its price-matched control, fails its null, or wins by shrinking the book into a
concentration study that N = 2 already does better.

**Concentration had already collected the prize**, as Q5 confirms: it moved held
price $23.72 → $75.95 and half-spread 26.67 → 21.68 for free, and an explicit
filter adds nothing significant on top.

**The stack is unchanged:**

```
signal        the D293 confluence        min z +2.58 across three nulls
construction  factor-neutral spread      removes -mu - sigma^2
width         N_eff = 2, FIXED           +21 bp over N=19, basis-immune
exit          the target, or nothing     +0.69 bp/bar
overlay       CLOSED (D319)   ·   tilt filters  CLOSED (this record)
```

**The entry signal, frozen since D293, is now the whole of what remains.**

## 7. Assertions

All seven pass, and [4] is the one that earned its place by rejecting my own null.

| | |
|---|---|
| **[1]** | the unfiltered gate is **bit-identical** to D306's, and its books reproduce D306's N=2 and N=19 target cells to **0.0 bp** |
| **[2]** | every arm excludes ~25% of the live cross-section and moves its own variable in the declared direction |
| **[3]** | **causality** — the filter variable is lagged, and a peeking variant moves 0.7% of name-bars |
| **[4]** | the null is turnover-matched to **+1.5%**, and **it rejected a name-label permutation that churned +28.2%** |
| **[S]** | the universe median round trip is **rejected** at both depths |
| **[C]** | `rt × turn` reproduces d295's 52.1893; the doubled form is rejected |
| **[6]** | [1] raises on a book handed free money inside the mask |

**Owed, and not fixed here:** a `[F] FILL` assertion — any runner whose book can
fail to fill its slots must compute turnover on the names **held**, and must fail
against the nominal-slot form. §2 is the third appearance of this shape after D305
and D279.

## 8. Files

`data/d320_tilt_filters.json` · `scripts/run_d320_tilt_filters.py` ·
`data/d320b_fill_adjusted.json` · `scripts/d320b_fill_adjusted.py`
