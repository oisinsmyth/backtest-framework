# D381 RESULT — a stop is a late trigger by construction, and the median/mean exchange rate is fixed at about 0.44

**Date:** 2026-09-08
**Pre-registration:** [D381](D381-stops-and-targets-at-thresholds-that-actually-select-a-tail.md), committed `6c2d6b5` — **before the runner existed** (R8).
**Runner:** [`scripts/run_d381_tail_exits.py`](../../scripts/run_d381_tail_exits.py).
**Artifacts:** `data/d381_tail_exits.json`. **Mining prefix only. No holdout was read.**
**Corrects:** [D380 §6a](D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control-inherits-the-rule.md), whose ±200 bp thresholds fired on ~80% of trades.

---

## 0. The verdict

**All six properly-scaled arms reduce the mean below the baseline. None passes V1. `[CAL]` held on
every one — realised fire rates 4.8%–19.7% against declared 5/10/20%, so this time the arms are what
their names say.**

| arm | kind | fire | threshold | hold | **mean** | median | ctrl p50 | in SE | > base | **V1** |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--|:--|
| **E0** | baseline | — | — | 39.9 | **+160.55** | +51.55 | — | — | — | — |
| T05 | target | 4.8% | +3,798.8 | 39.2 | +142.58 | +53.63 | +66.41 | +223.9 | **no** | FAIL |
| T10 | target | 9.8% | +2,837.6 | 38.3 | +140.59 | +69.13 | +22.17 | +283.0 | **no** | FAIL |
| T20 | target | 19.7% | +1,881.2 | 36.1 | +133.22 | **+114.63** | −28.98 | +350.3 | **no** | FAIL |
| S05 | stop | 4.9% | −3,229.4 | 39.2 | +142.79 | +43.05 | **+226.52** | −294.3 | **no** | FAIL |
| S10 | stop | 9.6% | −2,510.8 | 38.3 | +126.06 | +29.11 | **+253.49** | −520.7 | **no** | FAIL |
| S20 | stop | 19.4% | −1,743.0 | 36.2 | +109.86 | −11.88 | **+290.58** | −601.0 | **no** | FAIL |

**Q4 held — the prediction against myself.** No arm clears V1 on both legs.

**Q2 falsified, and this is the finding.** I predicted a stop would help a tail-driven book by
truncating the left tail. **Stops hurt, monotonically in fire rate:** +142.79 → +126.06 → +109.86 as
the stop tightens. §2.

**Q3 held decisively**, and the directional validity check passed: target controls centre **below**
the baseline (+66.41, +22.17, −28.98), stop controls **above** it (+226.52, +253.49, +290.58).
**D380 §2's inheritance mechanism is confirmed at correct scale** — and §3 shows it goes further than
D380 said.

---

## 1. Q1 held: every target reduces the mean, and the reason is arithmetic

The book's return lives in its right tail — **its mean excluding the top 1% of trades is +73.24**
against a full mean of +160.55. A profit target truncates exactly that tail, so it must cost mean,
and it does at every scale: −17.97, −19.96, −27.33 bp.

**The loss grows with the fire rate**, which is the same monotone shape as the stops and for the
mirror reason.

---

## 2. Q2 falsified: a stop is a LATE trigger by construction

**Stops do not truncate the left tail cheaply. They lock in the loss they were meant to avoid.**

| | mean per trade |
|---|---:|
| don't cut (baseline) | **+160.55** |
| cut the worst 5% **at a random bar** | **+226.52** |
| cut the worst 5% **when they reach −3,229** | **+142.79** |

**Randomly cutting the worst trades beats holding them. Cutting them at a loss threshold is worse
than either.** The mechanism is that a threshold is only reached *after* the adverse move: a random
bar in `[1, 40)` averages ~bar 20, typically **before** the path has fallen that far, so it exits
into a smaller loss. **The stop waits for the damage, then sells.**

**And these losers recover.** Holding them to the cap (+160.55) beats stopping them out (+142.79),
so on this construction the trades that fall furthest are not the trades that end worst. That is a
coherent property of a dip-buying rule inside a momentum cohort, and it is why every stop tested here
destroys value.

**Q6 also falsified:** the least-bad stop is **S05**, not S10 or S20. The damage is monotone in dose,
so the best stop is the one that barely fires.

---

## 3. The strict control is not a deployable policy, and that is new

D380 §2 found R7's control inherits the rule's trade selection. **This study shows the inheritance
includes the rule's INFORMATION SET, and that is a stronger and more limiting statement.**

The strict control cuts *the trades the stop will fire on*. Identifying that set requires knowing
which paths **will** reach −3,229 — information available only after the fact. So its **+226.52 is
not an alternative strategy anyone could run.** It is a valid null (it answers *"does the stop's
specific bar beat a random bar on the same trades?"* — decisively no, at −294 SE) and an **invalid
benchmark** for what a book could have earned.

> **The rule this adds:** an R7 matched-count control is a **null**, never a **policy**. When the
> rule's trade selection is knowable only ex post, the control's level is unattainable and must not
> be quoted as an achievable alternative. **The deployable comparison is the un-overlaid baseline** —
> which is why V1 required both legs, and why D380's control-only design was insufficient.

---

## 4. The principal's question, answered with a number

The objection that prompted this study was that these overlays **do** improve the median trade, and
that D380's thresholds were too tight to test it fairly. **Both halves were right. The corrected
thresholds change the dose and not the rate.**

| | mean lost | median gained | **bp of mean per bp of median** |
|---|---:|---:|---:|
| T05 (fires 4.8%) | −17.97 | +2.09 | **8.62** |
| T10 (fires 9.8%) | −19.96 | +17.58 | **1.14** |
| **T20 (fires 19.7%)** | −27.33 | **+63.09** | **0.43** |
| D380's E2 (fires 81.0%) | −98.12 | +220.10 | **0.45** |

**The best available exchange rate is about 0.44, and it is flat from a 20% fire rate all the way out
to 81%.** Tighter targets are much worse — T05 pays 8.6 bp of mean for 1 bp of median. **So the
scaling objection was correct about D380's arms and does not rescue the family: you can pick the dose
freely, but the price is fixed at roughly two basis points of mean for every four of median.**

**Every stop loses on both counts** — S05, S10 and S20 reduce the median *and* the mean, so there is
no trade-off to price.

**Whether 0.44 is worth paying is a capital decision, not a signal one**, and this record does not
make it. What it removes is the possibility that a better-scaled threshold buys a better rate.

---

## 5. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | all three targets reduce the mean | **HELD** |
| **Q2** | at least one stop beats the baseline | **FALSIFIED** — §2, and it is the study's finding |
| **Q3** | stop controls above the baseline, target controls below | **HELD** — the validity check passed |
| **Q4** | *against myself:* no arm clears V1 on both legs | **HELD** |
| **Q5** | `[CAL]` holds on all six | **HELD** — 4.78%, 9.77%, 19.74%, 4.86%, 9.59%, 19.40% |
| **Q6** | the best stop is S10 or S20 | **FALSIFIED** — S05; the damage is monotone in dose |
| **Q7** | the stops barely change the holding run, so cost does not decide this | **HELD** — 39.2 / 38.3 / 36.2 against 39.9. **Nothing here was decided by turnover** |

**Five held, two falsified.** Both falsifications concern the stop, and together they say the same
thing: **I expected a stop to be a cheap way to cut the left tail, and it is neither cheap nor
effective at any dose.**

---

## 6. What this closes

**Exits on this construction are closed, properly scaled.** Nine arms across two studies — a
parameter-free signal invalidation, three targets, three stops, and D380's two mis-scaled
thresholds — **and not one beats holding to the 40-bar cap.** The scaling objection that reopened the
question has been tested and answered: correct thresholds change the size of the loss, not its sign.

Combined with [D378](D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md),
**the timing picture on this book is complete: the entry day carries information worth at most half a
round trip; the exit carries none at any threshold.**

**Under [R15](../RULES.md#r15) closing the avenue remains the principal's.** This record does not
presume it.

---

## 7. What this did not settle

- **A conditional or trailing stop.** Only fixed thresholds on cumulative P&L were tested. §2's
  mechanism — that a fixed level is reached only after the damage — is an argument that a *trailing*
  or *time-conditioned* rule might behave differently, and it was not tested.
- **Whether 0.44 is worth paying.** §4 — a capital decision.
- **Whether §3 generalises.** The control's infeasibility-as-policy is a logical property of ex-post
  selection, but its size was measured once.
- **Anything out of sample.** Holdout #2 remains unspent.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book.*
