# D313 — universe-conditioned risk, and whether a real forecast can pay the price

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. Why this exists, and what it is NOT allowed to claim

D312 tested vol-targeted breadth with a conditioner measured at **ρ = −0.016**
and lost every cell. Its successor exists because the principal asked why λ was
computed from the held book when the whole market is available:

| forecast of the next 63 bars' book vol | **N=2** | N=5 | N=10 | N=19 | own lag-63 ρ |
|---|--:|--:|--:|--:|--:|
| the book's own trailing sd — **D312's** | **−0.016** | +0.056 | +0.185 | +0.347 | **−0.016** |
| **dispersion, whole live universe** | **+0.352** | +0.374 | +0.405 | +0.410 | **+0.616** |
| dispersion, names outside the gate | +0.355 | +0.371 | +0.403 | +0.411 | +0.598 |
| dispersion, the 50 gate names only | +0.242 | +0.300 | +0.334 | +0.342 | +0.588 |

**That measurement is post-hoc and prompted** — taken after D312's result was
known, comparing six predictors (`data/d312_universe_forecast.json`). **A study
that adopts the best of six has searched.** This one therefore pre-registers the
predictor *before* the runner exists and does not re-open the comparison.

**The forecast being real does not make the lever profitable.** That is the whole
question here, and §4 states it as a prediction *against* the study.

## 2. The predictor, declared and singular

**`xs_all` — the trailing 63-bar mean of the daily cross-sectional standard
deviation of returns across every finite name in the live universe (~1,019 a
bar), lagged one bar.**

**`xs_out` is NOT adopted despite scoring marginally higher** (+0.355 against
+0.352 at N=2). That margin is within noise, choosing on it would be selecting on
the diagnostic, and the whole-universe form is the plainer construction. It
appears in this study only as a **declared secondary arm** under the same
BH correction, never as a fallback if the primary disappoints.

### The mapping from dispersion to a book volatility, and why it is safe

Universe dispersion is not in book-volatility units, so it needs a scale. The
scale is estimated **as a constant on a long trailing window**, while the **time
variation comes entirely from the wide cross-section**:

```
c_j(t) = median over the trailing 252 bars of  [ v_j(s) / disp(s) ]      s < t
v̂_j(t) = c_j(t) × disp(t−1)
```

**This is the design's actual idea and it should be judged on it.** The noisy
quantity — a two-name book's realised vol — is used only to fix a *structural
ratio* that barely moves, where 252 bars of averaging makes it well conditioned.
The quantity that must move bar to bar is read off ~1,019 names. D312 did the
opposite: it asked a 63-bar two-name series to supply the time variation.

**Median, not mean,** for the same reason D302 chose the median half-spread: the
ratio's numerator is a noisy sd and its distribution is right-skewed.

## 3. The arms, and the target that is no longer a leverage rule

| arm | mechanism |
|---|---|
| **F — fixed** | constant `N_eff`, vol floats. The baseline |
| **B — universe-conditioned breadth** | choose the level whose **v̂** is closest to target; always fully invested |
| **E — universe-conditioned exposure** | fixed level, scale exposure by `target / v̂_base`, capped at 2.0 |
| **B_own — D312's predictor** | arm B driven by the book's own trailing sd. **The estimator A/B, and a reproduction check** |

**E is re-run rather than closed.** D312's E failed largely on a defect this
study fixes (§3.1), and closing an arm on a defect I have since identified would
repeat the error D312's §0 records.

### 3.1 The target is the MEAN OF ROLLING SDs, not the full-sample sd

D312 targeted each level's **full-sample** sd. A full-sample sd exceeds the
average of rolling sds whenever vol varies over time, so `target / v̂` averaged
**above 1** before any forecasting happened — realised mean exposure **1.34–1.53**.
**A third of D312's arm E was leverage, not risk control.**

Targets here are the **mean of each base level's rolling 63-bar sds**, already
measured and declared literally:

```
N_eff = 2 → 614      N_eff = 5 → 403      N_eff = 10 → 295      N_eff = 19 → 228
```

**Mean realised exposure is reported for every cell**, and Q6 makes the fix
falsifiable.

**4 targets × 4 arms = 16 cells.** Levels are D311's fifteen plus 19.0;
transitions charged from the weight vectors as `Σ|Δw|/2 × rt`.

## 4. The price the forecast has to beat — and the load-bearing prediction

**Arm B can only win by timing, because the static width trade-off it exploits is
already priced.** From D310 and D312's arm F:

| | N=2 | N=5 | N=10 | N=19 |
|---|--:|--:|--:|--:|
| gross | +24.12 | +19.23 | +15.12 | +10.61 |
| cost | 19.74 | 17.17 | 14.70 | 11.48 |
| vol | 780 | 487 | 346 | 263 |
| **gross/vol** | 0.0309 | 0.0395 | **0.0437** | 0.0403 |
| **net/vol** | **0.00560** | 0.00423 | 0.00124 | −0.00331 |

**Widening improves gross Sharpe up to N=10 and destroys net Sharpe at every
step**, because from N=2 to N=10 gross falls 37.3% while cost falls only 25.5%.
**Every bar arm B widens, it buys volatility reduction with net edge at a losing
exchange rate.** A ρ ≈ 0.35 forecast must beat that exchange rate, not merely be
real.

> **Q3, load-bearing and AGAINST the study: arm B does not beat its vol-matched
> fixed level on NET Sharpe at any target.**

## 5. Statistics

**Net Sharpe is primary.** D312's §8 established that D310's `sharpe` column is
**gross**; every Sharpe in this study is net and labelled as such, and gross is
reported beside it per CLAUDE.md.

Reported for every cell: gross, cost, transitions, net bp/bar, realised vol,
vol-vs-target, **net Sharpe**, gross Sharpe, realised vol dispersion, **mean
realised exposure**, maxDD.

Groups 2 and 3 of the reporting standard are **inherited from D310 and stated as
inherited** — arms B, E and B_own reweight the same trades and produce no new
ledger.

## 6. The null

**Circular rotation of the realised path** — the level path for B and B_own, the
exposure path for E: same move count, same sizes, same persistence, at unrelated
times. 200 draws, both statistics, **BH-FDR at q = 0.10 across the 12 testable
cells** (the four F cells have no path to rotate).

D312's nulls came back with **positive medians** and beat their treatments, so
this null is known to have teeth on this book and is not the R7 pathology.

## 7. Predictions

Three are against, and Q3 is load-bearing.

| | prediction |
|---|---|
| **Q1** | every targeted cell's realised vol lands within 10% of target. **A real test now** — D312 missed at all eight cells, by −11.4% to +45.5% |
| **Q2** | B and E cut realised vol **dispersion** by more than 30% against F at every target. D312's best was 35% and it *raised* dispersion in two cells |
| **Q3** | **B does not beat its vol-matched fixed level on NET Sharpe at any target.** *Against — load-bearing.* §4 is the reason |
| **Q4** | **E does not beat F on net Sharpe at any target either.** *Against* |
| **Q5** | **B beats B_own on net Sharpe at every target** — the estimator upgrade shows up in the book, not only in the correlation. *If this fails, §2's mapping is the suspect, not the predictor* |
| **Q6** | mean realised exposure in arm E is within **1.05** of 1.00 at every target, confirming §3.1 removed the structural leverage. D312 ran 1.34–1.53 |
| **Q7** | the `xs_out` secondary arm is **indistinguishable from `xs_all`** — within one BH decision of it at every target. If it separates materially, the +0.355/+0.352 margin was not noise and this study chose wrong |
| **Q8** | B's advantage over B_own is **largest at N_eff = 2 and smallest at N_eff = 19**, tracking where the two predictors' forecast correlations diverge most (−0.016 vs +0.352, against +0.347 vs +0.410) |

## 8. Stop conditions

- **Q3 confirms and Q4 confirms** → a genuine risk forecast still cannot pay §4's
  price, and **the risk axis closes** — this time on a measurement rather than on
  an estimator defect. That is the outcome I expect.
- **Q3 fails** → universe-conditioned breadth earns something. It needs its own
  confirmation before anything else, benchmarked against the vol-matched fixed
  level and never against the incumbent, and R8 applies in full.
- **Q1 fails AND the peeking variant also misses** → misimplemented; nothing else
  is read. **D312's stop condition was written without that second clause and it
  fired on a correct implementation**, so the clause is added here.
- **Q5 fails while Q1 passes** → the predictor is fine and §2's mapping is wrong.
  Report that and stop; do not search for a better mapping in the same study.

## 9. Assertions

1. **[1] Reproduction, two ways.** Arm F reproduces D310's **gross and net** at
   every shared level to floating point; **arm B_own reproduces D312's published
   B cells bit-identically** at all four targets.
2. **[2] CAUSALITY.** `c_j(t)` and `disp(t−1)` use only data through `t−1`, and a
   deliberately peeking variant **must produce a different book**. A causality
   audit that cannot fail proves nothing.
3. **[3] Stage 0 reproduces.** The predictor's lag-63 persistence and its forward
   correlations reproduce `data/d312_universe_forecast.json` exactly. **This is a
   harness check, not a test** — both values are already known, and the record
   should not read as though the gate could surprise anyone.
4. **[4] Transitions** are zero on a constant path in every arm and monotone in
   |Δ log N_eff|.
5. **[5] Every cell is a distinct book**, all 16.
6. **[6] The null matches** on move count and |Δ| distribution, up to the wrap.
7. **[7] Exposure accounting.** Arm B's mean exposure is exactly 1.00 by
   construction; arm E's is reported and enters Q6.
8. **[C] Cost dimensions** against d295's published 52.1893, doubled form
   rejected.
9. **[8] The self-test raises** on a book handed free money **inside** the mask.

## 10. Scope

**Out:** the entry signal; the exits (D306 showed them separable); the gate; `k`;
and **return-conditioned breadth, closed three times** by D299, D308 and D311.

**Out, and flagged:** the combined B+E arm, still deferred at the principal's
direction. D312 §4 argues it is a worse bet than when it was suggested, since E's
contribution was largely leverage — but §3.1 removes that leverage, so **the
argument against it is now weaker than when it was made** and it is available to
be called in.

**This study varies breadth and exposure on RISK, never on expected return.** It
is not to be read as reopening the return-timing question.

**Construction caveat, inherited and stated up front:** arm B splices between
sixteen separately-simulated books at bar granularity, charging weight-distance
turnover but not re-running the holding path. **It is an instrument, not a
tradeable book**, and it flatters B.

## 11. Files

`docs/decisions/D313-universe-conditioned-risk.md` (this record) · runner and
data to follow, in separate commits. Prior evidence:
`data/d312_universe_forecast.json`, `data/d312_vol_targeted.json`.
