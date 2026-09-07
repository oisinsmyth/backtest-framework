# D375 — the hurdle audit: the stage-1 gates are sound, and half of hurdle P has never been computed

**Date:** 2026-09-07
**Kind:** **REVIEW.** This record makes **no new measurement**. It reads the committed corpus —
`docs/RULES.md`, `docs/decisions/`, and the artifacts under `data/` — and asks of every absolute
threshold in force the question [D374](D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most-diversified-book-in-the-null.md)
asked of H4. **No pre-registration is owed for a review; every calibration it recommends needs one
before it runs (R8).**

---

## 0. The verdict, and it is not the one I predicted

After D374 I told the principal that H4's disease was likely to be widespread, and that auditing the
rest of the hurdle set was the strongest free candidate. **The audit does not support that.**

**The stage-1 gate set is in good shape, and for a structural reason:** most of it is built on
**t-statistics**, whose null centre is **zero by construction**. A bar of "t ≥ 2" means the same
thing in every universe, needs no calibration, and cannot be unreachable the way a share-of-names bar
can. That is exactly the design principle D374 arrived at the hard way, and **half the gate set
already had it.**

**The exposure is somewhere else entirely.**

| finding | |
|---|---|
| **Three of hurdle P's six thresholds have never been computed on anything** | P3, P4, P5. D266 states P4 is *"not calculable from these artifacts"* |
| **P1 cannot fail** | it is applied as a **sizing scalar**, not a filter — scale until drawdown hits 4%. It is a tax on return, not a hurdle |
| **Gate 1d has been applied exactly once in the programme's history** | in D373, where it failed at ρ = 0.935. It is defined in D289 and appears in no other record |
| **H4 was genuinely unique** | it is the only threshold in the set that nothing has ever cleared |

**Under [R6](../RULES.md#r6) — *"a hurdle that names a test is not cleared until that test is run"* —
the prop track is carrying three hurdles that have never been run, and one that structurally cannot
fail.** The personal track's stage-1 gates are not.

---

## 1. Method

For each absolute threshold in force I asked four questions, all answerable from the committed record:

1. **What kind of statistic does it gate?** A *t*-statistic has a known null centre (0). A **ratio**
   does not, and explodes when its denominator approaches zero — the pathology that made the top-k
   name shares unusable (D374 §4). An **absolute magnitude** needs a null reference that may not
   exist.
2. **How many times has it been applied to a candidate set**, as opposed to quoted?
3. **Has anything ever cleared it?** — H4's failure mode.
4. **Has anything ever failed it?** — the mirror failure mode, equally uninformative. D374 found the
   top-5 bar sitting at the null median: a coin flip.

---

## 2. The stage-1 gates ([D289](D289-the-promotion-pipeline.md) + its amendments)

| gate | threshold | statistic | applied | ever failed | ever cleared | verdict |
|---|---|---|---|---|---|---|
| **1a** | t-based best-of-N floor | **t vs its own null** | D290 (51 × 3), D292, D296, D359, D373 | yes | yes | **SOUND** — relative by construction |
| **1b** | mechanism + shape declared pre-run | qualitative | every pre-reg | n/a | n/a | procedural |
| **1c** | mean move ≥ **1.0×** round trip | **ratio**, denominator = measured cost | D290 (51) | yes — 0.09×, 0.10×, 0.14× | yes — 1.96×, 2.43×, 2.53× | **SOUND**, and explicitly non-binding since D289's amendment |
| **1d** | corr to every book arm **< 0.50** | correlation | **ONCE** (D373 H7) | once — **0.935** | never *in this universe* | **UNDER-TESTED** — §4 |
| **1e** | open-entry **t ≥ 2.0** | **t**, null centre 0 | D290 (51), D291, D293, D373 | yes | yes | **SOUND** |
| **1e** | retention **≥ 50%** | **ratio** of two edges | as above | yes — 19%, 18%, **−17%** | yes — 60%, 96%, 98.7% | **SOUND in practice** — §3 |
| **1f** | name-split CV **t > 0** | **t**, null centre 0 | D290, D291, D293 | yes | yes | sound, but a **sign test** — half of pure noise passes. D289 says so: *necessary, not sufficient* |
| **1g** | turnover / holding run / dead share | reported, **no bar** | D290 retro, D373 | n/a | n/a | reporting, not a gate |
| **1h** | direction declared before the run | qualitative | D290 retro | n/a | n/a | procedural — **and it worked**: it found `wick_asym` reversed at t +10.51 |
| **1i** | interior vs edge peak | categorical | D290 retro, D373 | demoted 2 of 5 | n/a | sound |
| **2c** | ≥ **1.5×** round trip | ratio | D264–D284, extensively | constantly | D284 at 2.41× | **SOUND** |
| ~~**H4**~~ | ~~names-to-half ≥ 10%~~ | share | D371, D373 | **always** | **never** | **RETIRED — D374.** Replaced by H4′ |

**Gate 1e's spread is the clearest demonstration that this set discriminates.** From D290's
short-only table, six candidates with retention **96%, 60%, 67%, 19%, 18%, −17%** and open-entry t
**+2.03, +1.71, +1.57, +1.96, +1.14, −0.87** — the gate cuts through the middle of a real
distribution rather than sitting outside it. Fifteen of D290's 51 collapsed on it.

---

## 3. Why the ratios here are safe, and the retired one was not

Three surviving thresholds are ratios — 1c, 2c and 1e's retention — and ratios are what killed the
top-k name shares. They are safe here for a reason worth stating, because it is the test to apply to
any future ratio-valued hurdle:

**Their denominators are bounded away from zero.**

- **1c and 2c** divide by the *measured round-trip cost*, which is a spread — strictly positive, and
  in this universe never below a few basis points.
- **1e's retention** divides by the *close-entry* edge, and 1e is only ever evaluated on candidates
  that already cleared a null. A candidate with no edge never reaches it.

The top-5 name share divided by **total book P&L**, which is a quantity that crosses zero and
approaches it from above in 11.8% of null draws. **That is the discriminating feature, not
"ratio-ness".** A hurdle whose denominator can approach zero within the population it will be applied
to is unusable; one whose denominator is bounded below is fine.

---

## 4. Gate 1d has been applied once, and the two "passes" on record are from another universe

Gate 1d — *correlation to every existing book arm < 0.50, at signal level* — is defined in D289 §92
and **appears in no other decision record.** Its only application is D373's H7, which I wrote under
R14's fixed-ordering clause rather than as gate 1d by name.

Every correlation the programme has recorded against this bar:

| pair | universe | ρ | |
|---|---|---:|---|
| S1 ↔ S2 | liquid US **ETFs** | **+0.123** (later +0.150) | pass |
| S1 ↔ M1 | liquid US **ETFs** | −0.069 | pass |
| **D373 ↔ D365** | **US single names** (`us_shorts_daily`) | **+0.935** | **fail** |

**Both passes are from the ETF universe; the single failure is the only measurement ever made in the
single-name universe.** So the bar has cleared twice and failed once, which is *not* H4's disease —
H4 had never cleared once. But **n = 3 across the whole programme, and n = 1 in the universe where
all current work happens.**

**What is not known, and what a calibration would settle:** what two books in the single-name
universe correlate at *structurally*, before any shared signal — same eligibility floor, same hedge
against the same floored market, same slot mechanics, same 3,185 bars. If that floor is near 0.5, the
gate is unreachable here and D373's 0.935 says less than it appears to. If it is near 0.1, the 0.935
is as damning as it reads.

One number in the record hints the structural floor is **high**: `docs/BOOK.md` records that the same
strategy on **two disjoint 57/60-name ETF universes correlates at ρ = +0.978.** That is a
same-strategy figure, not a two-strategy one, so it does not answer the question — but it shows how
much correlation a shared construction can carry across an entirely disjoint name set.

**Recommended, and requiring its own pre-registration: calibrate gate 1d.** The A′ null already
generates books that share everything with D373's except their timing; the correlation between two
independent A′ draws is the structural floor, computable with the machinery D374 built. **This is the
one stage-1 gate the audit finds under-evidenced.**

---

## 5. Hurdle P — three thresholds that have never been computed, and one that cannot fail

[R11](../RULES.md#r11)'s six-part hurdle for the prop track:

| | threshold | statistic | ever computed | ever failed | ever cleared | verdict |
|---|---|---|---|---|---|---|
| **P1** | trailing DD **≤ 4%** on OPEN equity | absolute % | D266 | **cannot** | **cannot** | **NOT A FILTER** — see below |
| **P2** | no exposure across the venue's flatten time | structural | D266 | yes — S1 holds overnight | yes — intraday-flat is natively compliant | **SOUND** |
| **P3** | worst single day **≤ 2%** | absolute % | **never** | never | never | **UNTESTED (R6)** |
| **P4** | E[time to breach] **> 3 years** | derived from an open-equity path | **never** — D266: *"not calculable from these artifacts"* | never | never | **UNTESTED (R6)** |
| **P5** | no single day **> 40%** of trailing-year profit | **ratio, denominator can cross zero** | **never** | never | never | **UNTESTED, and structurally fragile** |
| **P6** | venue permits automation at the funded stage | venue fact | D266 | yes — Apex, Take Profit Trader | yes — Topstep, MyFundedFutures | **SOUND** |

**P1 cannot fail, and this is a category error rather than a bad threshold.** D266 applies it by
**scaling the strategy until max drawdown reaches 4%** — *"none of it helps, because P1 is a sizing
constraint"*. A constraint satisfied by construction never rejects anything; it converts to a
**return penalty** (the best cell fell to +0.535%/yr after P1 sizing). That is a legitimate and
important calculation, but R11's table presents P1 alongside P2–P6 as though it were a filter, and it
is not one. **It should be restated as a sizing rule, not a hurdle.**

**P5 is the one place in the whole set that still carries H4's exact disease.** Its denominator is
trailing-year profit, which **can cross zero and approach it from above** — precisely the condition
§3 identifies as fatal. It has never been computed, so the pathology has never surfaced; it would on
first contact with a flat year.

**None of this is urgent, because the prop book is empty and no candidate is close.** It is recorded
so that the first candidate that gets there is not adjudicated by three thresholds nobody has ever
run.

---

## 6. What the audit changes

| | |
|---|---|
| **Retired** | nothing further. H4 was retired by D374 and remains the only one |
| **Restated** | **P1 is a sizing rule, not a hurdle.** Recommended amendment to R11's table |
| **Flagged as untested under R6** | **P3, P4, P5** — never computed on anything |
| **Flagged as structurally fragile** | **P5** — ratio over a denominator that crosses zero |
| **Recommended for calibration** | **gate 1d**, and only gate 1d. Needs its own pre-registration |
| **Confirmed sound** | 1a, 1c, 1e, 1f, 1g, 1h, 1i, 2c, P2, P6 |

**The design principle, stated so it can be applied to the next hurdle rather than rediscovered:**

> **Gate on a statistic whose null centre you know.** A *t*-statistic centres at 0 in every universe
> and needs no calibration. A ratio is safe only if its denominator is bounded away from zero within
> the population it will be applied to. **An absolute bar on anything else must be calibrated against
> its own null before it is allowed to adjudicate, and the calibration belongs in the
> pre-registration that introduces it — not five studies later.**

---

## 7. What this review did not do

- **It measured nothing.** Every number above is quoted from a committed record and is only as good
  as that record. Where a record makes a claim I could not verify from an artifact, I have said which
  record it comes from.
- **It did not calibrate gate 1d.** §4 recommends it; it needs pre-registration.
- **It did not audit study-specific hurdles** beyond D373's H-series, which map onto the gates above
  (H5 = 1e, H7 = 1d, H4 retired). Individual studies have set their own bars and this review does not
  reach them.
- **It did not revisit R6's own scope.** The observation that hurdle P partly violates R6 is made
  against R6 as written; whether R6 was intended to reach a hurdle nothing has yet been eligible for
  is the principal's call.

---

*Review, not a study. Nothing admitted, nothing retired, no fixture read. The one recommendation that
requires new measurement — calibrating gate 1d — is not carried out here.*
