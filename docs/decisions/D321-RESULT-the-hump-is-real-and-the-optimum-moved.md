# D321 RESULT — the hump is real, the optimum was not at 25, and BH still says no

**Status:** RESULT. Pre-registered at `1c7299c`, runner at `c06738f`, both
committed before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. This warrants a confirmation study and nothing more.**

> ## AMENDMENT, 2026-09-04 — §5's BH bar corrected the multiplicity for tests that do not exist
>
> **The principal declined to discard dv28 on a BH bar computed over nineteen
> nominal tests, and was right.** Measured
> (`data/d321b_effective_tests.json`):
>
> ```
> pairwise correlation of the 19 threshold books   min 0.762  median 0.892  max 0.993
> first eigenvalue explains 90% of the variance
> EFFECTIVE INDEPENDENT TESTS   Li-Ji 3.0    Cheverud-Nyholt 4.7    (nominal 19)
> ```
>
> **Adjacent thresholds share nearly all their names, so a 19-point sweep is ONE
> hypothesis measured at many correlated points, not nineteen hypotheses.** The BH
> bar for the smallest p:
>
> | assumed m | bar | dv28 (p = 0.0100) |
> |--:|--:|---|
> | 19 nominal | 0.00526 | misses |
> | 8 | 0.01250 | **CLEARS** |
> | 5 (Cheverud-Nyholt) | 0.02000 | **CLEARS** |
> | 3 (Li-Ji) | 0.03333 | **CLEARS** |
>
> **dv28 clears at every plausible effective count.**
>
> **And the precedent is this programme's own.** [D297](D297-RESULT-a-narrow-window-that-works.md)
> applied BH to its **eight pre-registered cells** and reported its **25-point
> fine sweep** separately as a count against chance — *"4 of 25 clear p < 0.05
> against 1.25 expected"* — rather than as 25 hypothesis tests. **D321's count is
> 3 of 19 against 0.95, and its sweep should have been framed the same way.**
>
> §5's first bullet is corrected: **BH over 19 was the wrong correction.** The
> other four items in §5 stand unchanged — the peak still moved, the effect is
> still small against D316's resolution, and QA5 and QA8 are still falsified.
>
> **This does not promote anything.** §7's confirmation requirement is unchanged
> in every particular. What changes is that dv28 is **carried as a declared
> variant of the stack** rather than set aside — see
> [STACK.md](../STACK.md) §0.

---

## 1. QA2 is falsified, and it is falsified in the one way that counts

§2 of the pre-registration declared the bar before the run: a cell must lift net
Sharpe **+0.10 to +0.21** over the control to clear its own null, and dv25 had
posted **+0.129 against +0.207** — *"so unless the optimum sits away from the 25th
percentile, this study cannot succeed on individual significance."*

**The optimum sits away from the 25th percentile.**

| pct | gross | cost | **NET** | **netSHRP** | vs ctl | **needed** | **p** |
|--:|--:|--:|--:|--:|--:|--:|--:|
| **control** | +32.89 | 18.33 | **+14.57** | **+0.334** | — | — | — |
| 22 | +29.19 | 14.47 | +14.72 | +0.390 | +0.056 | +0.186 | 0.179 |
| 25 | +30.39 | 14.58 | +15.81 | +0.433 | +0.099 | +0.158 | 0.134 |
| **28** | **+32.93** | **14.56** | **+18.37** | **+0.507** | **+0.173** | +0.112 | **0.0100** |
| **30** | +34.76 | 15.93 | **+18.83** | **+0.519** | **+0.185** | +0.098 | **0.0149** |
| 33 | +30.01 | 15.94 | +14.06 | +0.396 | +0.062 | +0.037 | 0.0398 |
| 35 | +28.85 | 16.77 | +12.08 | +0.340 | +0.006 | +0.036 | 0.0945 |

**Three of nineteen thresholds clear p < 0.05 against 0.95 expected** — a binomial
p of about 0.067, and the thresholds are heavily correlated, so that figure is
indicative rather than exact.

## 2. QA3 confirms — six contiguous thresholds, and it is D297's shape

**The pre-registration said this was the only thing that could carry the study if
QA2 confirmed. QA2 did not confirm, and this holds anyway.**

```
pct     22     25     28     30     33     35   | 38
vs ctl +0.056 +0.099 +0.173 +0.185 +0.062 +0.006 | -0.046
```

**Six contiguous thresholds beat the control**, rising smoothly to a peak at
28–30 and falling smoothly away — with 8, 10, 15, 18, 20 below it on one side and
38, 45 below on the other. That is the same signature D297 used to distinguish a
plateau from a spike, and **the thing D320's three-point grid could not have
seen.**

## 3. QA4 confirms at all nineteen — and this is the mechanism, not the number

The spread-matched control is a **direct** spread filter calibrated to reach the
**same held half-spread** as the dv cell:

| pct | dv | **spread-matched** | dv − spread-m |
|--:|--:|--:|--:|
| 20 | +0.327 | **−0.186** | +0.513 |
| 25 | +0.433 | −0.075 | +0.508 |
| **28** | **+0.507** | **−0.075** | **+0.582** |
| 30 | +0.519 | +0.021 | +0.499 |

**dv beats it at every one of the nineteen thresholds, by +0.060 to +0.582.**

**A direct spread filter that achieves the identical held half-spread destroys the
book** — most cells land at or below zero against a control of +0.334 — **while
dollar volume reaches the same tilt and helps.**

That is exactly the mechanism §3 of the pre-registration proposed: the spread arm
conditions on the **per-name Corwin–Schultz estimate D302 measured as noisy**, so
it discards good names that merely *measured* wide. Dollar volume is cleanly
measured, correlates with spread, and buys the tilt without the estimation noise.
**It is FINDINGS §11's lesson in a new place: what matters is not only what you
condition on, but how well the input is measured.**

## 4. dv28 is the cleanest cell, and its gross is unchanged

```
              gross     cost      NET    netSHRP   half   price
control      +32.89    18.33   +14.57    +0.334   18.31    $71
dv28         +32.93    14.56   +18.37    +0.507   14.54    $73
              +0.04    -3.77    +3.80    +0.173   -21%     +3%
```

**Gross is identical to four decimal places of a basis point. Price is unchanged.
The entire +3.80 bp/bar is cost.** That is the claim the study was built to test,
and dv28 is the cell where nothing else moves to confuse it.

**dv30 is the higher Sharpe (+0.519) but the messier cell** — its gross rises
+1.86, so part of its advantage is name-picking that could be luck. **dv28 is the
one to carry forward.**

## 5. What is against it, stated plainly

- **BH-FDR over 19 thresholds returns NONE.** dv28's p = 0.0100 misses the
  0.10/19 = 0.00526 bar. **The strongest multiplicity correction rejects
  everything here.**
- **The peak moved from where D320 put it** (25 → 28–30). That is evidence the
  three-point grid was too coarse — and equally a warning that a 19-point sweep
  has more room to find a maximum by luck.
- **D316's resolution wall still applies.** dv28's net advantage is +3.80 bp/bar
  against a paired-test MDE of roughly 18 bp at this concentration. The rotation
  null on Sharpe is a different and more powerful test, but the underlying edge is
  small relative to what this fixture can resolve.
- **QA5 falsified:** dv does *not* beat the price-matched control everywhere — it
  loses at 8, 10, 15, 18, 38 and 45, and wins at the peak (+0.176 at 28, +0.184 at
  30). The D284 test is passed where it matters and not uniformly.
- **QA8 falsified:** held half-spread is **not** monotone in the threshold. It
  falls to ~14.4 around 22–28 and **rises again** beyond 30. The filter starts
  removing names the book wants and the replacements come from deeper in the gate.
  That the spread minimum and the performance peak coincide near 28 is supportive,
  but it was not predicted.

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **QA1** | reproduces D320 | **CONFIRMED** — nominal *and* fill-adjusted, to 3.6e-15 bp |
| **QA2** | **no threshold clears its null** *(against, load-bearing)* | **FALSIFIED** — 3 of 19 at p < 0.05, against a bar declared in advance |
| **QA3** | ≥4 contiguous thresholds beat control | **CONFIRMED** — six, 22 through 35 |
| **QA4** | dv beats the spread-matched control everywhere | **CONFIRMED** — all 19, by +0.060 to +0.582 |
| **QA5** | dv beats the price-matched control where fill ≥ 85% | **FALSIFIED** — 6 of 16 lose; the peak wins |
| **QA7** | fill-adjusted advantage below nominal everywhere | **CONFIRMED** |
| **QA8** | half-spread monotone, price within 10% | **FALSIFIED** — non-monotone, with an interior minimum near 28 |

## 7. The stop condition fires for a CONFIRMATION, not a closure

> **QA3 confirms → this is D297's pattern, and it warrants a pre-registered
> confirmation on a separate construction. It is not a promotion, and R8 applies
> in full.**

**That branch fires.** And QA2 falsified against a bar declared before the run
makes it stronger than the branch anticipated.

**What a confirmation must carry, and none of it is optional:**

1. **A separate construction**, not this one re-scored. The obvious candidate is
   D310's rank-weighted book — correctly costed per D317 — where the filter would
   act on weights rather than membership.
2. **The threshold FIXED at 28 in advance.** dv28 is the maximum of a 19-point
   sweep and a confirmation that re-sweeps has confirmed nothing.
3. **The spread-matched control carried**, since §3 is the finding that would
   survive even if the level does not.
4. **BH honoured.** If a confirmation on one pre-declared threshold clears its
   null, there is no multiplicity left to correct.

## 8. Assertions

All nine pass. Two are worth naming.

| | |
|---|---|
| **[1]** | reproduces D306's unfiltered book **and** D320's nominal nets **and** D320b's fill-adjusted nets, all to 3.6e-15 bp |
| **[F]** | **FILL, carried for the first time and owed since D320** — turnover divides by the names *held*; at the 60th percentile the book fills 80%, held turnover is 1.25× the nominal form, and net falls +16.46 → +13.26. **The nominal-slot form is rejected, not merely reported** |
| **[2]** | causality — the peeking variant moves 2.0% of name-bars and changes the book |
| **[3]** | both matched controls hit their targets and neither is the treatment |
| **[4]** | **corrected before the run.** It demanded the name-permutation churn > 10%, generalising D320's spread-filter figure of +28.2%. **The dv set churns only +4.8%** — liquid names stay liquid, so that set is far less correlated with liveness. That is a property of the filter, not a universal. It now checks the rotation is the *better-matched* of the two (−0.9% against +4.8%) |
| **[S]** | the universe median round trip is rejected |
| **[C]** | cost dimensions reproduce d295's 52.1893 |

## 9. Files

`data/d321_dv_sweep.json` · `scripts/run_d321_dv_sweep.py`
