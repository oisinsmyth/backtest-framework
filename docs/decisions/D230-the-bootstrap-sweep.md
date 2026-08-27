# D230 — The bootstrap sweep: every delta this programme reported

**Status:** Pre-registered — committed BEFORE any runner exists
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
