# D315 Stage A RESULT — the corner is real, the closed form is not

**Status:** RESULT. Pre-registered at `cdee86c`, runner committed at `2451e40`
before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Both headlines at once

**QA2 confirmed — the load-bearing prediction.** Net Sharpe peaks at
**N_eff = 2.00**, the width already in use, and the best cell below it beats N=2
by **0.0%**. The corner is real, it is flat, and it is now **measured on both
sides** rather than extrapolated to.

**QA1 falsified — D314's closed form does not survive.** Net does *not* rise
monotonically below 2. Gross turns down at N_eff = 1.15 and net at 1.45, so the
log-linear dilution curve does not extend below the fitted range. **`N* = 1.66`
is withdrawn.** §5.

## 2. The extended surface — seven widths nothing had run

`rt` = 57.0 bp, 3,187 bars. `*` = never run before.

| | N_eff | gross | cost | **NET** | vol | **netSHRP** | √N·net | turnover |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| \* | 1.00 | +25.26 | 21.26 | +4.00 | 1089 | +0.0584 | +4.005 | 0.3731 |
| \* | 1.15 | **+25.46** | 20.99 | +4.47 | 1020 | +0.0695 | +4.790 | 0.3684 |
| \* | 1.30 | +25.42 | 20.74 | +4.68 | 962 | +0.0772 | +5.334 | 0.3640 |
| \* | 1.45 | +25.24 | 20.50 | **+4.73** | 913 | +0.0823 | +5.699 | 0.3598 |
| \* | 1.60 | +24.97 | 20.28 | +4.69 | 871 | +0.0855 | +5.935 | 0.3559 |
| \* | 1.75 | +24.67 | 20.07 | +4.60 | 833 | +0.0875 | +6.079 | 0.3522 |
| \* | 1.90 | +24.34 | 19.87 | +4.47 | 800 | +0.0886 | +6.157 | 0.3487 |
| | **2.00** | +24.12 | 19.74 | +4.37 | 780 | **+0.0890** | **+6.183** | 0.3465 |
| | 2.50 | +23.04 | 19.17 | +3.87 | 697 | +0.0881 | +6.117 | 0.3364 |
| | 3.00 | +22.08 | 18.67 | +3.40 | 635 | +0.0851 | +5.896 | 0.3277 |
| | 5.00 | +19.23 | 17.17 | +2.06 | 487 | +0.0673 | +4.617 | 0.3012 |

**Gross peaks at 1.15 and net at 1.45. Sharpe rises monotonically all the way to
2.00 and turns down after it.** Concentrating past N=2 raises volatility faster
than it raises net.

## 3. The apparent net peak at 1.45 is noise, and the paired test says so

`data/d315a_paired_net.json` — **post-hoc, not pre-registered.**

The pre-registration scored every width against the rank-rotation null and
against nothing else, so it could not say whether 1.45's +4.73 differs from
2.00's +4.37. Those books share all 3,187 bars and correlate at **0.9917**, so
the difference is measured pairwise (D303's argument):

| N_eff | net | **diff vs N=2** | sd(diff) | **t** | corr | win rate |
|--:|--:|--:|--:|--:|--:|--:|
| 1.00 | +4.00 | −0.367 | 404.81 | −0.05 | 0.9598 | 47.8% |
| 1.30 | +4.68 | +0.306 | 236.74 | +0.07 | 0.9848 | 47.8% |
| **1.45** | **+4.73** | **+0.361** | 172.15 | **+0.12** | 0.9917 | 47.8% |
| 1.75 | +4.60 | +0.224 | 68.27 | +0.19 | 0.9986 | 47.6% |
| 2.50 | +3.87 | −0.503 | 104.41 | −0.27 | 0.9963 | 52.3% |
| 5.00 | +2.06 | −2.307 | 359.84 | −0.36 | 0.9428 | 51.8% |

**The largest gain over N=2 anywhere below it is +0.361 bp/bar at t = +0.12, and
its win rate is 47.8% — under half.** Nothing below 2 is distinguishable from 2.

**So there is no net gain below the floor either**, and the two objectives that
disagreed in §2 do not actually disagree once the difference is measured rather
than ranked.

## 4. The null is decisively beaten and nearly uninformative

All 24 rank rotations enumerated — an exact permutation test rather than the
pre-registered 200 samples, since `(rk + shift) % 25` admits only 24 non-identity
rotations.

| N_eff | netSHRP | null p50 | null p95 | p |
|--:|--:|--:|--:|--:|
| 1.00 | +0.0584 | **−0.9110** | −0.4881 | 0.0400 |
| 1.45 | +0.0823 | −1.0460 | −0.5492 | 0.0400 |
| 2.00 | +0.0890 | −1.0991 | −0.5864 | 0.0400 |

**Every cell sits at p = 0.0400, the enumeration floor, and all eight survive BH
on both statistics.** And that means very little.

**This is R7's named pathology: the null's p95 is −0.49 to −0.59 Sharpe.** A
rank rotation destroys the ranking, so it produces a heavily losing book, and
beating it establishes only that **the rank signal works** — which D290 and D293
established already. **It says nothing about whether the width is right**, which
is the question this stage asked.

**The width question has no null in Stage A, and the pre-registration should not
have implied one.** §3's paired test is the informative statistic, and it is
post-hoc.

## 5. What breaks in D314, and what survives

### Withdrawn: the closed form and `N* = 1.66`

The log-linear net curve was fitted on N ∈ [2, 25] and **does not extend below
2.** Refitting over the union:

| | D314, N ∈ [2,25] | refit, N ∈ [1,25] |
|---|---|---|
| gross | 29.47 − 6.50 ln N, **R² 0.9774** | 26.40 − 3.94 ln N, **R² 0.9143** |
| cost | 23.51 − 4.12 ln N, R² 0.9522 | 21.42 − 2.54 ln N, R² 0.9936 |
| net | 5.96 − 2.38 ln N | 4.98 − 1.40 ln N |
| **N\*** | **1.66** | **4.75** |

**The refit is worse (gross R² 0.9774 → 0.9143) and its `N*` = 4.75 is equally
meaningless.** The form was right on [2,25] and is wrong on [1,25]. **`ln N* =
−n0/n1 − 2` is withdrawn as a predictor of the optimum**; it remains the correct
first-order condition *for a log-linear net curve*, and this book's is not
log-linear across the full range.

**QA3 failed in the opposite direction to my prediction.** I expected cost to
break *above* the fitted line below 2, because at N_eff → 1 every top-rank change
swaps the whole book. Turnover does rise going down — 0.3465 at N=2 to 0.3731 at
N=1 — but far less than the extrapolation demanded, so cost lands **9.6% BELOW**
the fitted line at N=1. **The extrapolation failed on the gross side, not the
cost side.**

### Survives, and is strengthened

**The diversification law holds all the way to a single name.** Refitted on the
extended grid, ρ = **0.0088** (QA4's bar was 0.01) and σ = **1,095 bp** against
D314's 1,097 — and the measured vol at N_eff = 1 is **1,089**, which is σ, as
`vol = σ/√N` requires at N=1. **This is now verified at the boundary rather than
inferred.**

**`Sharpe(N) = √N · net(N)/σ` survives**, being a consequence of ρ ≈ 0.

**The corner survives and is stronger than when derived.** It is no longer an
extrapolated claim about 1.66; it is a measured statement that **N_eff = 2 is the
Sharpe maximum of a surface now sampled on both sides of it, and that nothing
below it differs from it on net.**

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **QA1** | net rises monotonically below 2, 5.5–6.5 at N=1 | **FALSIFIED** — gross turns at 1.15, net at 1.45, and net at N=1 is 4.00 |
| **QA2** | **Sharpe peaks in [1.4, 2.0], beats N=2 by <5%** *(against, load-bearing)* | **CONFIRMED** — peaks at 2.00 exactly, gain 0.0% |
| **QA3** | cost breaks ABOVE its fitted line below 2 *(against)* | **FALSIFIED** — 9.6% *below* at N=1 |
| **QA4** | ρ under 0.01 and σ within 5% | **CONFIRMED** — 0.0088 and 1,095 vs 1,097 |
| **QA5** | N_eff = 1 is not the best cell | **CONFIRMED** — it is the *worst* sub-2 cell on Sharpe |
| **QA6** | refitted N* within ±0.3 of 1.66 | **FALSIFIED** — 4.75, and meaningless; see §5 |

## 7. The stop condition fires, and Stage B does not run

> **QA1 fails → the dilution curve does not extend below 2; D314's `N*` is
> withdrawn as an extrapolation and Stage B does not run, since it fits the same
> curve.**

**Honoured.** Stage B's rule is `ln N*(t) = −n0(t)/n1(t) − 2` fitted in a
trailing window — the same functional form that just failed out of sample.
Running it would be fitting a curve this stage showed does not hold.

**This is the branch I wrote for exactly this outcome, and it fires cleanly** —
unlike D312's, whose stated reason was disproved, and D313's, whose threshold was
mis-specified. Third time.

## 8. Where this leaves the width axis

**Closed, and now for a measured reason rather than five empirical ones.**

- **N_eff = 2 is the Sharpe optimum**, with the surface measured from 1.00 to
  25.00 and no cell below 2 distinguishable from it on net (max t = 0.12).
- **Six studies have tried to vary width** — D299, D308, D311, D312, D313 and
  now this — and the corner explains all of them: **a rule that varies N can only
  move away from a corner.**
- **D314's *mechanism* stands** (ρ ≈ 0, `Sharpe = √N·net/σ`, the corner);
  **its closed-form optimum does not.**

**The entry signal remains the only untested surface of any size**, frozen since
D293. Six width studies have varied how much of the book to hold and none has
varied what goes into it.

## 9. Assertions

All six pass.

| | |
|---|---|
| **[A1]** | anchors reproduce D310 and D312 to **4.9e-15 bp** — the extended grid disturbs nothing. *Not "bit-identical": the references are JSON text and 4.9e-15 is the floor a round-tripped double can reach* |
| **[A2]** | design `N_eff` exact to 1.9e-13, weights monotone decreasing at every level; realised `N_eff` reported beside it and agreeing to two decimals |
| **[A3]** | `cost = rt × turn` at every level; `rt × turn` = 52.1893 reproduces d295's, doubled form rejected |
| **[A4]** | `N_eff = 1` puts 1.000000000000 on the top name and **matches a `hard` one-name book to 4.6e-13 bp** — a second construction that never calls `exp_weights` agrees |
| **[A5]** | all 11 cells are distinct books |
| **[A6]** | [A1] raises on a book handed free money inside the mask |

## 10. Files

`data/d315a_below_corner.json` · `scripts/run_d315a_below_corner.py` ·
`data/d315a_paired_net.json` · `scripts/d315a_paired_net.py`
