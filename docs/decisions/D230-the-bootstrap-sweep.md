# D230 — The bootstrap sweep: every delta this programme reported

**Status:** Committed (E1–E5 all confirmed) — **zero of twenty-four clear the hurdle as the records claimed it**
**Date:** 2026-08-27
**Area:** Validation & research integrity

---

## Why this exists

D229 built the paired block bootstrap that D217 and D218 both **named as part of hurdle A and
neither ever ran**. Applied to D218's own headline it fails in all four cells: `I1 − I2 =
+0.628` has a 90% interval of **−0.133 to +1.325**, containing zero.

That was one delta, checked because it happened to sit next to the one D229 was testing. **The
programme has reported twenty of them.** Every one was scored the same way — a point estimate
against `DELTA_HURDLE = 0.10`, with the bootstrap leg written into the hurdle and never
computed.

This sweep computes it for all of them.

---

## This spends no looks, and that must be said before the tables

**No new strategy configuration is evaluated anywhere in this study.** Every arm, every rung,
every book and gate combination below is already in the multiplicity ledger from D217, D218 or
D229. This is a **precision audit of numbers already reported**, not a search.

The distinction is exactly D228's boundary applied to the programme's own output: computing a
confidence interval around a published estimate conditions on nothing new. **No ledger entry
moves and no floor changes.** A reader who sees twenty-four rows below and reaches for a
multiplicity correction has misread what is being done.

---

## Scope

**In scope — 24 deltas, all nested-rung comparisons on the daily ETF fixture:**

| study | delta | cells | start |
|---|---|---:|---:|
| **D217** | `signal_line − zero_line` (R1−R2) | 4 | 393 |
| **D217** | `zero_line − momentum` (R2−R3) | 4 | 393 |
| **D218** | `I1 − I2` (`signal_minus_band`) | 4 | 1,000 |
| **D218** | `I2 − I3` (`band_minus_no_deadzone`) | 4 | 1,000 |
| **D218** | `I1 − C` (`impulse_minus_control`) | 4 | 1,000 |
| **D229** | `I0 − I1` | 4 | 1,000 |

Cells are `{long_short, long_flat} × {no gate, 200ma}` throughout.

**Each study is reproduced at its own warm-up start** — D217 at bar 393, D218 and D229 at
1,000 — because a delta recomputed on a different span is not the delta that was reported.

**Out of scope, and stated rather than silently omitted:**

- **D220, D224, D225, D226** (crypto and intraday-ETF). Their verdicts rest on **matched-count
  random nulls**, not on a delta hurdle with a bootstrap leg. They do not carry the defect
  being audited. Extending the sweep to them would be a precision audit of a different kind of
  claim and is a separate study.
- **D228's eight candidates.** They were scored against a **best-of-search null**, which is a
  stronger test than a confidence interval, and adding a weaker one beside it would invite the
  reader to quote whichever is more convenient.

---

## The method

`run_jerk_rung.paired_block_bootstrap`, reused unchanged — block **21**, **1,000**
replications, seed **0**, both arms recomputed on **identical resampled dates**.

**The reproduction gate, and it is the audit's integrity check.** Every point estimate computed
here must match the committed summary artifact (`data/macd_ladder_summary.json`,
`data/impulse_macd_summary.json`, `data/jerk_rung_summary.json`) **to 1e-9**. If a point
estimate does not reproduce, the sweep stops and reports that instead: an audit that cannot
reproduce the numbers it is auditing has found a bigger problem than imprecision.

### The two readings, reported side by side

| | test | what it was |
|---|---|---|
| **as scored** | point estimate ≥ +0.10 | what the runners actually computed |
| **as claimed** | point ≥ +0.10 **and** p05 > +0.10 | what the records said hurdle A was |

The headline number of this study is **how many of the 24 change verdict between those two
columns.**

---

## Predictions

Committed before any runner exists.

| | prediction | confidence |
|---|---|---|
| **E1** | **Every one of D217's four `R1−R2` deltas fails the p05 leg.** They are smaller than D218's (+0.285 max against +0.628), and D218's already failed | **high** |
| **E2** | **Zero of the 24 clear the claimed hurdle.** Not one point-and-interval pass in the whole programme | **moderate-high** |
| **E3** | **D218's `I2−I3` deltas have intervals straddling zero by a wide margin.** D218 read those near-zero point estimates (−0.016 to −0.032) as evidence the dead zone does not matter. With this much dispersion **a near-zero estimate is not evidence of absence**, and that is a different error from an overstated positive | **moderate-high** |
| **E4** | **At least one delta has a 90% interval wider than 5× its point estimate** | **moderate** |
| **E5** | **All 24 point estimates reproduce to 1e-9.** The studies are deterministic and seeded, so failure here would mean something worse than imprecision | **high** |

E2 is the one that would hurt to be wrong about in the comfortable direction: a pass would mean
the programme has a result stronger than this record expects, and it would deserve more scrutiny
than a failure, not less.

---

## What this cannot do

**A wide interval is not a refutation.** It says the sample does not pin the estimate down, not
that the estimate is wrong. Three things this sweep must not be read as saying:

1. **It does not zero out the point estimates.** `+0.529` remains the best estimate of `I1−I2`
   whatever its interval.
2. **It does not touch cross-construction replication.** D218's strongest argument is that
   D217's `+0.285` and its own `+0.628` come from **unrelated arithmetic** and agree in sign,
   with `I1 − C ≈ 0`. Two independent estimates agreeing is evidence a single-fixture bootstrap
   cannot see, and this study does not weigh it.
3. **A block bootstrap is one choice among several.** Block 21 is the repo's only precedent on
   daily bars; a different block length would give a different interval. The sensitivity is not
   swept here, and that is a limitation rather than a defence.

What it *does* establish is whether the programme's stated hurdles were met on their own terms.

---

## The stop

**This study has no stop, because it has no hypothesis to abandon** — it reports a measurement
on work already done.

What follows from it is a **standing rule**, proposed here and binding if the result supports it:

> **A hurdle that names a test is not cleared until the test is run.** Any record claiming a
> hurdle passed must point at the artifact field where the test's output lives, and any runner
> implementing a hurdle with more than one leg must compute every leg or fail loudly.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the paired bootstrap | `paired_block_bootstrap` | `scripts/run_jerk_rung.py` |
| D217's arms, panel, scoring | `arm_positions`, `load_panel`, `portfolio_log_returns`, `sharpe_of`, `ladder_start` | `scripts/run_macd_ladder.py` |
| D218's arms | `arm_positions`, `ladder_start` | `scripts/run_impulse_macd.py` |
| D229's arms | `arm_positions`, `jerk_score` | `scripts/run_jerk_rung.py` |

**Written fresh:** only the sweep harness and the reproduction gate. If anything else needs
writing, the delta being audited is not the delta that was reported.

---

## RESULT

*Appended after the run. Nothing above this line was edited except the Status field.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_bootstrap_sweep.py`
(offline, deterministic, seed 0, 8.9 s) · Page:
[`BOOTSTRAP_SWEEP_RESULTS.md`](../results/BOOTSTRAP_SWEEP_RESULTS.md) · Artifact:
`data/bootstrap_sweep_summary.json`

### The one-sentence version

**Eight of twenty-four deltas cleared the hurdle as the runners scored it. Zero clear it as the
records claimed it. All twenty-four intervals contain zero.**

**The reproduction gate is clean** — every point estimate matches its committed artifact to
1e-9, so this is an audit of the published numbers and not of a re-derivation of them.

### Every delta

| study | delta | book | gate | point | p05 | p95 | width | as scored | as claimed |
|---|---|---|---|---:|---:|---:|---:|:--:|:--:|
| D217 | `R1−R2` | long_short | none | **+0.285** | −0.167 | +0.809 | 0.977 | PASS | **FAIL** |
| D217 | `R1−R2` | long_short | 200ma | +0.186 | −0.081 | +0.495 | 0.576 | PASS | **FAIL** |
| D217 | `R1−R2` | long_flat | none | +0.209 | −0.152 | +0.572 | 0.724 | PASS | **FAIL** |
| D217 | `R1−R2` | long_flat | 200ma | +0.093 | −0.250 | +0.433 | 0.682 | — | FAIL |
| D217 | `R2−R3` | long_short | none | +0.163 | −0.078 | +0.443 | 0.521 | PASS | **FAIL** |
| D217 | `R2−R3` | long_short | 200ma | +0.089 | −0.043 | +0.241 | 0.283 | — | FAIL |
| D217 | `R2−R3` | long_flat | none | +0.129 | −0.070 | +0.322 | 0.391 | PASS | **FAIL** |
| D217 | `R2−R3` | long_flat | 200ma | +0.078 | −0.078 | +0.212 | 0.290 | — | FAIL |
| **D218** | **`I1−I2`** | long_short | none | **+0.628** | **−0.133** | +1.325 | **1.458** | PASS | **FAIL** |
| D218 | `I1−I2` | long_short | 200ma | +0.366 | −0.076 | +0.721 | 0.797 | PASS | **FAIL** |
| **D218** | **`I1−I2`** | long_flat | none | **+0.529** | **−0.055** | +1.015 | 1.070 | PASS | **FAIL** |
| D218 | `I1−I2` | long_flat | 200ma | +0.096 | −0.322 | +0.435 | 0.757 | — | FAIL |
| D218 | `I2−I3` | long_short | none | −0.016 | −0.068 | +0.031 | 0.099 | — | FAIL |
| D218 | `I2−I3` | long_short | 200ma | −0.032 | −0.102 | +0.020 | 0.121 | — | FAIL |
| D218 | `I2−I3` | long_flat | none | −0.024 | −0.115 | +0.049 | 0.165 | — | FAIL |
| D218 | `I2−I3` | long_flat | 200ma | −0.029 | −0.105 | +0.034 | 0.139 | — | FAIL |
| D218 | `I1−C` | long_short | none | −0.038 | −0.378 | +0.279 | 0.657 | — | FAIL |
| D218 | `I1−C` | long_short | 200ma | −0.042 | −0.299 | +0.169 | 0.468 | — | FAIL |
| D218 | `I1−C` | long_flat | none | +0.008 | −0.258 | +0.263 | 0.521 | — | FAIL |
| D218 | `I1−C` | long_flat | 200ma | −0.096 | −0.339 | +0.152 | 0.490 | — | FAIL |
| D229 | `I0−I1` | long_short | none | −0.224 | −1.031 | +0.621 | 1.652 | — | FAIL |
| D229 | `I0−I1` | long_short | 200ma | −0.152 | −0.712 | +0.391 | 1.104 | — | FAIL |
| D229 | `I0−I1` | long_flat | none | −0.218 | −0.759 | +0.402 | 1.161 | — | FAIL |
| D229 | `I0−I1` | long_flat | 200ma | +0.006 | −0.554 | +0.563 | 1.118 | — | FAIL |

### Scoring the predictions

| | prediction | outcome |
|---|---|---|
| **E1** | Every one of D217's four `R1−R2` deltas fails the p05 leg | **CONFIRMED.** 0 of 4 |
| **E2** | Zero of the 24 clear the claimed hurdle | **CONFIRMED.** 0 of 24 |
| **E3** | `I2−I3`'s intervals straddle zero by a wide margin | **CONFIRMED.** 4 of 4, on point estimates of −0.016 to −0.032 with widths of 0.099 to 0.165 — **three to six times the estimate** |
| **E4** | At least one delta has an interval wider than 5× its point estimate | **CONFIRMED, 12 times.** Half the sweep. The extremes are `I0−I1` long_flat/200ma at **180.8×** and `I1−C` long_flat/none at **63.6×** |
| **E5** | All 24 point estimates reproduce to 1e-9 | **CONFIRMED.** No drift anywhere |

**Five of five** — and, as in D229, that is the *easy* case. Four of these predicted failure and
were arithmetic given what D229 already showed. Only E5 could have surprised.

### The error that runs through this, and it is not the one everybody expects

The obvious reading is *"the positives were overstated."* That is true of the eight that changed
verdict. **The subtler and more common error is in the other direction.**

**D218 reported `I2−I3` at −0.016 to −0.032 as evidence the dead zone does not matter, and
`I1−C` at ≈ 0 as evidence the two constructions measure the same thing.** Both were read as
*confirmations* — as knowing something. But:

- `I2−I3` intervals are **0.099 to 0.165 wide** on estimates of ~0.02.
- `I1−C` intervals span **−0.378 to +0.279**.

**An interval that wide around zero is not evidence of absence. It is evidence of nothing at
all** — consistent with the dead zone mattering a great deal in either direction, and with the
two constructions differing substantially. A near-zero point estimate got reported as a settled
equivalence when the sample could not distinguish it from a large effect.

That is the more dangerous mistake, because a null result reads as modest and careful, and
nobody asks a modest claim for its confidence interval.

### A correction to what D229 said, and to what was said in conversation

D229's RESULT stated that D218's cross-construction argument was *"untouched by this"* —
specifically *"D217's +0.285 and D218's +0.628, with `I1 − C ≈ 0`, is independent evidence
that a single-fixture bootstrap cannot see."* **That was too generous, in two ways.**

1. **The `I1 − C ≈ 0` leg is not untouched — it is exactly what this sweep dissolves.** Its
   four intervals span roughly ±0.3. The claim that Impulse MACD's acceleration rung and plain
   MACD's *"are the same measurement"* is not supported by the data that was used to make it.
2. **"Independent" overstates the relationship.** D217 runs from bar 393 and D218 from bar
   1,000 on the **same 57 ETFs** — D218's span is a *subset* of D217's. Two different
   estimators on heavily overlapping data are correlated, not independent.

**What actually survives** is weaker and should be stated at its real strength: **two
structurally different trend estimators produced same-signed positive deltas on overlapping
data.** That is corroboration. It is not independent replication, and it is not what D218
described.

### What this does *not* say

Restated from the pre-registration because the tables above invite over-reading:

- **The point estimates are unchanged and remain the best estimates.** `+0.529` is still the
  best estimate of `I1−I2`. A wide interval is not a refutation.
- **Nothing here says trend acceleration does not work.** It says this fixture, over this span,
  cannot tell you how well.
- **Block 21 is one choice** — the repo's only precedent on daily bars. Its sensitivity is not
  swept, and that is a limitation of this study rather than a defence of the results.

### The standing rule, now binding

> **A hurdle that names a test is not cleared until the test is run.** A record claiming a
> hurdle passed must point at the artifact field holding that test's output, and a runner
> implementing a multi-leg hurdle must compute every leg or fail loudly.

Twenty of these deltas were reported against a hurdle whose second leg existed only in prose.
**Prose that is not enforced in code gets skipped** — which is the correction D226 already
recorded, in a different context, and which has now cost the programme its headline result's
credibility rather than one study's benchmark.

### What this changes

**No verdict in D217, D218 or D229 flips from pass to fail on the substance** — every one of
those studies already closed as a negative or a qualified negative on other grounds. What
changes is the **confidence attached to the one positive the programme was carrying forward.**

`I1 − I2` was the reason to believe acceleration beats level, and it was the reason D229
existed. It is a plausible estimate on an interval containing zero, corroborated by a
correlated study on overlapping data.

**The arm itself is unaffected by all of this.** D228 established it at **+0.570** excess
Sharpe against buy-and-hold's **+0.235** — an absolute measurement, not a delta between rungs,
and not audited here. Whether *acceleration beats level* is now open; whether *this arm beat
this benchmark over this span* is not in question.

**The next step is unchanged and is now better motivated: unmined data.** No further work on
this fixture can narrow these intervals, because the intervals are a property of the sample.

---

## ADDENDUM — the comparison the sweep did not cover

*Prompted by the obvious question the RESULT above does not answer: if every rung delta is
inside the noise, what about the arm against the benchmark — the number the programme is
actually carrying forward?*

### The defect

**D230's scope was twenty-four nested-rung deltas, and the one comparison that matters most was
not among them.** `arm − buy-and-hold` is D218's hurdle D. It has been quoted in every record
since, most recently as D228's *"+0.570 excess Sharpe against buy-and-hold's +0.235"*, and **it
has never been given an interval.**

### The number

Same instrument, same basis as it was reported on — excess Sharpe at `rf = 4%` charged on the
exposed fraction (D228's correction), paired block bootstrap, block 21, 1,000 replications:

| | excess Sharpe |
|---|---:|
| arm (I1, long-flat, no gate) | **+0.570** |
| buy and hold | +0.235 |
| **difference** | **+0.335** |

> **90% interval: −0.242 to +0.804. It contains zero.**

**The programme's one carried-forward positive is not statistically distinguishable from zero
on this fixture** — the same verdict the twenty-four rung deltas received, now applied to the
number they were all in service of.

### Stated fairly

- **+0.335 remains the best estimate**, and the arm still achieved it at **8.8% volatility
  against 17.7%** and a **−12.70% drawdown against −34.81%**. Those are descriptive facts about
  what happened, not inferences, and the interval does not touch them.
- What is not established is that the advantage **generalises**. A 1,515-bar sample of 57
  correlated ETFs — roughly 2.1 effective independent instruments by D226's measure — does not
  contain enough information to separate +0.335 from noise.
- This is **not** a new failure. It is the same finding as the RESULT above, reaching the
  headline number instead of the ones underneath it.

### Why this was added after the sweep

Same justification as D229's post-hoc `I1 − I2` bootstrap, and it should be checked against the
same test: **it spends no looks** — this comparison was already reported and is already in the
ledger — and **it can only make the programme's headline worse.** A post-hoc addition that can
only cut against you is not the freedom the pre-registration discipline exists to control.

It is now computed by `run_bootstrap_sweep.py` and lives in
`data/bootstrap_sweep_summary.json` under `arm_vs_benchmark`, so it is reproducible rather
than a number quoted once in conversation.

### What this changes

**Nothing about the plan, and everything about what the plan is for.**

Before this, the holdout test read as a *confirmation* exercise: the arm looks good in-sample,
go check it holds up. It is not. **The in-sample result does not establish the arm**, so the
holdout is not a confirmation — **it is the experiment.**

That is a better position to be in than it sounds. A confirmation that fails teaches you little
because you never knew what you had. An experiment on data selected by a rule fixed in advance
gives an answer either way.
