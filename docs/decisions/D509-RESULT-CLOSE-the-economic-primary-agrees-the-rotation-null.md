# D509 RESULT — CLOSE: the economic primary agrees with the rank one. The rotation null swings ±$27 a session on its own, and within a year the sign reverses to −$10.71

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D509-RESULT-CLOSE-the-economic-primary-agrees-the-rotation-null-swings-27-dollars-a-session-and-within-year-the-sign-reverses-to-minus-10-71.md`. The H1 above is the full title.*

**Result of D509** (spec `4a138f4`). Runner `scripts/run_d509_quintile_primary.py --run`
(`--selftest` passes, nine checks; 0.1 min), artefact `data/d509_quintile_primary.json`.
**1,876 sessions, 2016-01-04 → 2023-12-29.** The arm is imported and reproduces D504's published
per-year figures exactly (1,876 sessions, $15,423). The 2024+ slice was never scored.

**Provenance, restated:** this primary was chosen after seeing D508 and directed by the principal.
Nothing here could have been a discovery (D509 §0), and nothing here is.

## 0. The primary, and the null that matters

| cell | Δ, $/session | top | bottom | N1 p05 | N1 p50 | N1 p95 | percentile | clears |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **\|log(P/SMA200)\|** | **+13.82** | +20.45 | +6.63 | −27.18 | +0.13 | **+26.45** | 76.9th | **no** |
| \|log(P/EMA200)\| | +7.08 | +16.49 | +9.41 | −24.91 | +0.43 | +25.66 | 65.9th | no |
| signed log(P/SMA200) | −19.16 | +6.46 | +25.62 | −29.07 | +0.76 | +26.50 | 11.4th | no |
| signed log(P/EMA200) | −11.40 | +9.38 | +20.78 | −25.22 | +0.31 | +26.43 | 24.1st | no |

**The number that decides it is the null's width, not the observed value.** Rotating the
conditioner — which leaves it a persistent gate with the same duty cycle and the same run lengths,
merely starting at a different place in the sample — swings the quintile difference from **−$27 to
+$26 a session** at the 5th and 95th percentiles, with a median of **+$0.13**. The observed +$13.82
sits at the **76.9th percentile**. **On an arm whose P&L is concentrated in two of eight years, a
persistent one-day-in-five gate is worth ±$27 a session by accident, and half of what we measured is
inside that.**

**N2 family maximum** over the four cells, 1,875 common offsets: p50 +$10.40, **p95 +$33.00**,
against an observed maximum of **+$13.82** — **40.1% of offsets beat the best real cell.**

**Verdict: CLOSE**, on all four terms.

## 1. The three controls

**N3, within-year, and it reverses the sign in dollars.**

| 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | mean | pooled |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| −1.4 | −6.6 | −38.2 | −12.2 | −32.6 | −22.0 | **+47.0** | −19.8 | **−10.71** | **+13.82** |

**Negative in seven years of eight, averaging −$10.71 a session, against a pooled +$13.82.** D508
saw this as a Spearman sign flip (−0.042 within against +0.009 pooled); in dollars it is far starker.
**One year, 2022, carries the entire pooled effect at +$47.00 a session, and every other year runs
the other way.** The conditioner ranks which year it is.

**N4, the tie control.** On traded sessions only — 1,708 of 1,876, with 168 untraded sessions sitting
at exactly $0 — Δ is **+$15.00** against +$13.82 for all sessions, a **9%** move, at the 75.7th
percentile of its own rotation, still not clearing. **The tie block was a real defect in D508's rank
statistic and a second-order one for this statistic**, which is what §1 of the spec predicted.

**The quintile shape is not monotone**, as the re-specification assumed: net dollars per session run
**+6.63, +3.58, +3.54, +6.92, +20.45**, so the *quietest* fifth beats the two middle fifths. The
rank correlation of quintile index against quintile mean is **+0.60**, not +1. A monotone statistic
cannot see that shape, which was the whole reason for re-scoring.

## 2. The methodological result, which outlives the question

**An exact rotation of the conditioner subsumes a hand-built run-length-matched random gate, and the
runner proves it rather than asserting it.** Rotation permutes *when* the states occur without
changing *how long they last*:

| | observed | rotated by 137 |
|---|---:|---:|
| duty cycle | 20.0% | 20.0% |
| number of runs | 38 | 38 |
| run-length multiset | identical | identical |

D508 had to build a matched-persistence gate by hand because its primary was a correlation over all
sessions. **A quintile-difference statistic gets that control for free from its own rotation**, and
the two agree: D508's hand-built band put the observed top quintile at the 76th percentile by Sharpe;
this rotation puts the observed difference at the 76.9th percentile by dollars. **Prefer the
statistic whose own null contains the control.**

## 3. Two defects in my own instruments, found and fixed here

**(a) D508's `spearman` divides the covariance by n and the standard deviations by n−1**, so it is
short by a factor (n−1)/n. At n = 1,876 that is 0.05% and changes D508's +0.0089 to +0.0089 — **no
number in D508 moves** — but the same helper returns 0.80 for a perfectly ordered five-point series.
`rank_corr_small` in this runner uses ddof = 0 throughout and its selftest asserts ±1.0 on ordered
and reversed inputs.

**(b) D508's guard refuses fewer than 30 points**, which is right for a session series and wrong for
a five-row quintile table: the monotonicity check silently returned NaN in the first run of this
record. It now returns +0.60, and the selftest asserts that D508's version *does* refuse five points,
so the difference is deliberate rather than accidental.

## 4. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a | Δ = +13.82 ± 0.05 | **+13.82** | right |
| X-b | p50 within ±$3, p95 in [+12, +28], Δ at the 70th–92nd percentile, not clearing | p50 **+0.13**, p95 **+26.45**, **76.9th**, not clearing | **right on all four** |
| X-c | family p95 ≥ 1.3× the single-cell p95 | **1.25×** | narrowly wrong; the observed max does not clear, as predicted |
| X-d | within-year mean below +$6, negative in ≥ 4 of 8 | **−10.71**, negative in **7 of 8** | right |
| X-e | traded-only Δ within 25% | **9%** | right |
| X-f | not monotone, index-vs-mean below +0.8, q1 > q2 and q3 | **+0.60**, both true | right |
| X-g | CLOSE | CLOSE | right |

**Six of seven, against three of seven in D508.** That is what a pre-registration written *after*
seeing the data should look like, and it is the reason this record cannot count as evidence: the
predictions were easy because the quintile table was already on the page.

## 5. What stands

- **CLOSE recommended** for the 200-day stretch as a ranker of this arm, on the economic primary as
  on the rank one; the principal closes. The two statistics disagree about how interesting the
  quintile table looks and agree exactly about the verdict.
- **The conditioner ranks years.** 2022 alone carries +$47.00 a session and seven of eight years are
  negative. Any conditioner correlated with "which year it is" will inherit this arm's concentration,
  so **stratify by year before believing one**.
- **Prefer a statistic whose own null contains its control.** The rotation of a quintile difference
  is a matched persistent gate by construction, proven in the runner.
- **Nothing spent.** 2024+ was never scored.

## 6. Files

Runner · this record · the artefact · D508 (the rank version) · PICKUP.
