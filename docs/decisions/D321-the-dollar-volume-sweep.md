# D321 — the dollar-volume threshold, swept, and why it beats the direct spread filter

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. What D320 left, and why it is worth one more study

D320 closed the tilt axis, and one cell survived the closing without being
significant. At `N_eff` = 2:

| | netSHRP | fill-adj | held ½-spread | held price | p |
|---|--:|--:|--:|--:|--:|
| control | +0.334 | +0.334 | 18.31 | $70.70 | — |
| **dv25** | **+0.464** | **+0.433** | **14.61** | **$72** | **0.119** |
| price-matched control | +0.305 | — | — | $72 | — |

**Three things make it worth a second look, and one makes it suspicious.**

- It **beats the control designed to kill it.** D284 died of discovering the price
  level; `dv25` cuts the held half-spread by 20% at an **unchanged price**
  ($70.70 → $72), and its price-matched control returns +0.305.
- **The dv arm is the only arm that moves anything**, and it is **humped**:
  +0.320 / +0.433 / +0.340 at the 10th / 25th / 40th percentile.
- **The direct spread filter FAILS at the same job** — every spread cell is below
  control, spread25 at −0.326. So a variable that merely *correlates* with spread
  beats the variable itself. §3 turns that into the study's real question.
- **And it is the maximum of an 18-cell search**, so some of +0.129 is selection.
  BH already rejected it.

## 2. THE BAR IS DECLARED BEFORE THE RUN, and it may be unreachable

D320's nulls give the lift over control a cell must post to clear p = 0.05:

```
dv10  needs +0.142        dv25  needs +0.207        dv40  needs +0.097
```

**`dv25` posted +0.129 against a bar of +0.207.** So unless the optimum sits away
from the 25th percentile, **this study cannot succeed on individual
significance**, and that is stated now rather than discovered later.

**What can still decide it is the SHAPE.** D297's overlay was credible not because
one cell had a small p but because **four CONTIGUOUS thresholds cleared** — X =
11, 12, 13, 14 — rising smoothly from 6 and falling smoothly to 19, with 4 of 25
swept thresholds clearing against 1.25 expected. **A hump measured at three points
is nothing; the same hump at twenty is evidence.** QA3 is that test.

## 3. The study's real question: why does dv beat the spread filter at cutting spread?

The direct spread filter conditions on the **per-name Corwin–Schultz estimate,
which D302 measured as noisy** — its clamp is a left truncation and its per-name
values are unstable. Excluding on it throws away good names that merely *measured*
wide. **Dollar volume is a cleanly measured variable that correlates with spread**,
so it may buy the same spread reduction without the estimation noise.

**That is a specific mechanism and D321 tests it with a SPREAD-MATCHED CONTROL:**
for each dv threshold, a direct spread filter calibrated to reach the **same held
half-spread**. If dv beats it, dv is not a noisy proxy for spread — it is a better
route to the same tilt. If dv does not beat it, the spread arm's failure should
have predicted this and the effect is a threshold artefact.

**This is the same shape as D312's finding in reverse** (FINDINGS §11): there, a
better-measured input made a rule better; here it would be a better-measured input
reaching the same target more cleanly.

## 4. The grid

- **Dollar-volume percentile ∈ {5, 8, 10, 12, 15, 18, 20, 22, 25, 28, 30, 33, 35,
  38, 40, 45, 50, 55, 60}** — 19 points, spanning D320's three and both tails.
- **`N_eff` = 2 only**, with the `target` exit and no overlay. The operating point,
  fixed and inherited. D320 showed N = 19 is confounded with width.
- **Per bar, cross-sectional, on the lagged trailing-63 mean of `close × volume`** —
  D320's construction unchanged.

Three controls at **every** threshold: the unfiltered book, a **price-matched**
filter, and a **spread-matched** filter.

## 5. Statistics — and the fill correction is mandatory from the start

**Net Sharpe primary**, fill-adjusted, with the nominal figure beside it.

**[F] FILL is a first-class statistic, not a footnote.** D320's headline cells
collapsed because a filter that starves the gate makes a *narrower book at full
notional*, and turnover must divide by the names **held**, not the nominal slots.
**Every cell reports fill, and any cell below 85% is flagged as confounded with
width** and excluded from the shape test.

Reported per cell: gross, spread cost, commission, net, net Sharpe (both), fill,
held half-spread, held price, held dollar volume, turnover (both), breakeven round
trip.

**Cost basis:** per-cell held round trip — D320 §5's reasoning, unchanged: the
filter's mechanism *is* the cost, so a common basis would define it away. Common
figures reported beside it.

## 6. The null

**Circular time rotation of the exclusion mask**, D320's construction — turnover
matched to +1.5%, each name's exclusion run-lengths preserved exactly, only the
alignment with when names are actually thin destroyed. **200 draws per threshold.**

**A name-label permutation is NOT used and the runner must show why**, reproducing
D320's assertion [4]: it churns +28.2% against a per-bar re-draw's +28.4%.

**Multiplicity is priced two ways**, as D297 did: BH-FDR at q = 0.10 over the 19
thresholds, **and** the count of thresholds clearing p < 0.05 against the 0.95
expected by chance.

## 7. Predictions

Three are against, and QA2 is load-bearing.

| | prediction |
|---|---|
| **QA1** | dv at 10, 25 and 40 reproduces D320's cells to floating point. **A harness check** |
| **QA2** | **no dv threshold clears its own null.** *Against — load-bearing.* §2 declares the bar at +0.10 to +0.21 and dv25 posted +0.129 |
| **QA3** | **at least four CONTIGUOUS thresholds beat the unfiltered control on fill-adjusted net Sharpe, rising and falling smoothly.** *For* — this is D297's actual evidence and the only thing that can carry the study if QA2 confirms |
| **QA4** | **dv beats its SPREAD-MATCHED control at every threshold.** *For the mechanism* — dv is a cleaner route to the same tilt, not a proxy for a noisy estimate |
| **QA5** | dv beats its price-matched control at every threshold where fill ≥ 85%, as dv25 did |
| **QA6** | fill falls monotonically in the threshold and drops below 85% somewhere in [40, 60] |
| **QA7** | **the fill-adjusted advantage is smaller than the nominal one at every threshold.** *Against* — some of D320's dv25 was already the width effect |
| **QA8** | held half-spread falls monotonically in the threshold while held price stays within 10% of the control's — the "tighter names at the same price" mechanism, measured across the whole sweep rather than at one point |

## 8. Stop conditions

- **QA2 confirms and QA3 fails** → there is no hump, `dv25` was the maximum of an
  18-cell search, and **the tilt axis closes for good.** Expected.
- **QA3 confirms** — four or more contiguous thresholds beating control — → this
  is D297's pattern, and it warrants a pre-registered confirmation on a separate
  construction. **It is not a promotion**, and R8 applies in full.
- **QA4 fails** → dv is a proxy for the spread estimate, the spread arm's failure
  predicted this, and the effect is a threshold artefact. Close.
- **QA1 fails** → misimplemented; nothing else is read.

## 9. Assertions

1. **[1] Reproduction.** dv at 10, 25, 40 reproduces `data/d320_tilt_filters.json`
   to floating point, and the unfiltered book reproduces D306's `N=2/target`.
2. **[F] FILL — owed since D320 and carried for the first time.** Turnover is
   computed on the names **held**; the check must **FAIL against the
   nominal-slot form**. `[C]` checks cost's dimensions, `[S]` its basis, and
   neither checks its denominator.
3. **[2] CAUSALITY.** The filter variable is lagged, and a peeking variant must
   produce a different exclusion set and a different book.
4. **[3] The controls match and are distinct.** Price-matched within 5% on held
   price, spread-matched within 5% on held half-spread, and **neither may be
   bit-identical to its treatment.**
5. **[4] The null is turnover-matched**, and the rejected name-permutation is
   constructed and shown to churn, as in D320.
6. **[S] SPREAD BASIS.** Round trips come from the names held and the check
   rejects the universe median.
7. **[C] Cost dimensions** against d295's 52.1893; doubled form rejected.
8. **[5] Every cell is a distinct book.**
9. **[6] The self-test raises** on a book handed free money inside the mask.

## 10. Scope

**Out:** the entry signal; the exits beyond inheriting `target`; the gate; `k`;
width; the overlay; the spread and price arms as treatments — they appear only as
controls; and any variable other than dollar volume.

**This study can close a surface or find one hump.** It cannot promote anything,
and §2 says plainly it may not be able to establish anything either. **If it
closes, the entry signal — frozen since D293 — is the whole of what remains.**

## 11. Files

`docs/decisions/D321-the-dollar-volume-sweep.md` (this record) · runner and data
to follow, in separate commits. Prior evidence: `data/d320_tilt_filters.json`,
`data/d320b_fill_adjusted.json`, `data/d318_stack_recost.json`.
