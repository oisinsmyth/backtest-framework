# D378 — does the entry DAY matter inside the cohort? The rotation nobody ran

**Date:** 2026-09-08
**Kind:** **SIGNAL TEST (R15).** Gross mean per trade against a new control. Admits nothing, reads no holdout.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Authorised by:** the principal's narrow reopening of the winners'-dip avenue, 2026-09-08
([D373 RESULT, second amendment](D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md);
[FINDINGS §52a](../FINDINGS.md)). **This is the one test that reopening authorises.**

---

## 0. The question, and why nothing already run answers it

D373's winners'-dip long entered a fresh `rev_5` dip inside the `mom_252_21` **top** decile and
earned a gross **+160.55 bp per trade**. [FINDINGS §52](../FINDINGS.md) retired the avenue on
**level** evidence: a random cohort name on the same day earns **+126.54** (D373's `B_c`), and
hedging the cohort out collapses the mean to **+34.08** (D377).

**Neither number says anything about when to enter.**

| existing control | rotates | holds fixed | why it cannot answer |
|---|---|---|---|
| **A′** per-name time rotation | the entry bar, to **any** eligible bar | the name, its trade count | a random eligible bar is usually one where the name was **not** in the top decile. A′ therefore prices *cohort membership plus timing together*, which is why its centre sits at **+59.42** |
| **B_c** same-day same-cohort swap | the **name** | the **day**, cohort membership | it never varies the day. Silent on day choice **by construction** |

**And the covariance evidence does not reach it either.** D376's ρ = **0.923** between cohort books
bounds their **co-movement**, not their means — correlation is computed after removing each series'
mean and dividing by its own volatility. **Two books can correlate at 0.92 and earn very
differently.** That is a correction to this record's own lineage and it is why the avenue was
reopened.

### The control this study adds

> **A′_c — a COHORT-CONDITIONED time rotation.** For each observed entry, draw a replacement entry
> bar uniformly from the set of bars on which **that same name** was **eligible** *and* **in the
> `mom_252_21` top decile**. The name is fixed, cohort membership is fixed, the per-name entry count
> is fixed. **Only the day moves.**

Beat A′_c and entry timing adds something *inside* the cohort, and §52's rule does not reach it.
Fail, and the dip is picking days a dart would have picked.

---

## 1. What is frozen

**D373's primary cell, inherited unchanged and not re-selected:** a fresh `rev_5` dip inside the
`mom_252_21` top decile, entered **long** at the next open (D340), hedged against the floored
equal-weight market. Cell **10:90 / cap 40**, mining prefix only.

Committed ledger `[MIR]` must reproduce before anything else runs: **3,932 trades, 796 names, gross
mean +160.55, median +51.55**.

**Hedge convention: H0, the incumbent unit market.** D377 adopted H1 for future studies, but this
study's whole purpose is comparability with D373's committed numbers, and switching convention would
make `[MIR]` impossible. **H0 is used, and the result reports the headline under H1 beside it** so
the record is legible under the new convention too. Stated here so it is a choice and not an
oversight.

**Direction is DECLARED LONG** before the run (gate 1h). A result in the other direction is
direction-inverted and counts against the mechanism.

**One cell, no best-of-N floor** — nothing is being selected.

---

## 2. What this study does NOT test, and why

**Exit timing is excluded, deliberately.** The principal raised entry *and* exit timing together, and
they need different controls. [R7](../RULES.md#r7) is explicit: a rule that **modifies an existing
book** — a stop, a target, an early exit — must be nulled against **the same trades cut at random
bars, matched on how many cuts it makes**, not against a rotation. D235 cleared a rotation null at a
p95 of −0.284 and then landed at the **63rd percentile** against the correct control.

Bundling an exit sweep into a rotation study would repeat that error. **Exit timing is a separate
pre-registration with a matched-count random-exit control, and it is not authorised by this
reopening.**

**What this study does report on exits, because it is free:** the **horizon profile** at caps
{5, 10, 20, 40, 60} for the observed book *and for A′_c*, per bar held. That directly settles §52a's
open question — whether the observed edge's front-loading is a property of the dip or of the cohort —
without testing any exit *rule*.

---

## 3. The measurement

**Primary, path-invariant:** gross **mean per trade**, observed against A′_c's distribution.
**Judged on the HIGH tail — p95** (the observed must be large). Same direction as H1–H3, opposite to
D374's H4; `[DIR]` asserts it.

**Reported beside it, never compared to it on the same statistic** (`CLAUDE.md`, FINDINGS §10): the
per-trade **median**, and the path-variant deployed book in bp/bar with turnover, exposure and
holding run (gate 1g).

**Draws: 2,000**, five parts × 400, keyed `default_rng([SEED, 378, ARM, draw])` so parts do not
overlap. Every reported percentile carries a **bootstrap SE**, and any margin within **2 SE** of its
bar is **UNRESOLVED, never passed** — the programme's standing convention.

---

## 4. The hurdles

**T1 and T3 must both hold.** T2 and T4 are reported and gate nothing.

| | hurdle | why |
|---|---|---|
| **T1** | **Signal (R15).** Gross mean per trade **> A′_c's p95**, by more than 2 SE | the question of the study |
| **T2** | *reported, not gating* — the same comparison on the **median** per trade | D374 showed a per-trade median is confounded with hold length, so it cannot gate across constructions; here the hold is identical on both sides, so it is informative and still not decisive |
| **T3** | **LEAVE-ONE-OUT. T1 must still hold with the single largest trade removed from the observed ledger**, against the same stored A′_c percentiles | **D373's H1 passed and then died on one trade.** GME entered 2021-01-04 was 6.34% of the ledger, and removing it took the mean below `B_c`'s p95. **That failure mode is known, so it is a hurdle this time and not a post-hoc.** |
| **T4** | *reported* — the **horizon profile per bar held**, observed vs A′_c, at caps {5, 10, 20, 40, 60} | §52a: is the front-loading the dip's or the cohort's? |

**T3 is the one I expect to bite.** It is written as a gate precisely because writing it as a
post-hoc check last time let a one-trade result stand as a pass for a day.

---

## 5. Assertions

| tag | what it proves |
|---|---|
| **`[MIR]`** | the inherited cell reproduces D373's committed 3,932 / +160.55 / +51.55 **before any draw** |
| **`[POOL]`** | **the assertion this study exists on.** Every A′_c entry lands on a bar where that name was **eligible AND in the top decile**. D351's lesson: a null that trades outside the observed events' universe inverts the headline — D347's rotation traded the sub-$5 tail and its conclusion reversed when fixed |
| **`[CNT]`** | per-name entry counts are **exactly** preserved, name by name, not merely in total |
| **`[LAG]`** | the pool is built from the same lagged grid the observed rule uses, re-derived by a **second implementation that never calls the pool builder** |
| **`[DIST]`** | the **pool-size distribution per name** and the share of draws landing on an **observed** entry bar are reported. A name whose pool is barely larger than its entry count cannot be meaningfully rotated |
| **`[DIR]`** | the comparison uses the **HIGH** tail: a duplicated ledger scores above p95, a return-zeroed one below |
| **`[DEG]`** | names with **fewer pool bars than entries** are counted and reported; the runner **refuses** if they exceed 20% of trades |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken book, including an A′_c draw placed outside the cohort |

**Persist before rendering.**

---

## 6. The search cost

**None.** One cell inherited, one control, one primary statistic, hurdles fixed before any draw. Under
[R13](../RULES.md#r13) the study adds **one look** to the winners'-dip ledger — disclosed, and on a
fixture already spent, so under R14's first amendment it costs the **prior** and not validity. **No
holdout is read.**

---

## 7. Predictions

**Four studies running — D373, D374, D376, D377 — have had my direction right and my magnitude
wrong, always in the same direction: I under-estimate how much of these books is structure.** These
point estimates are recorded to be scored against that record, not defended.

| | prediction |
|---|---|
| **Q1** | **A′_c's p50 lands in +100 to +140 bp** — near `B_c`'s +126.54, since both price "a cohort name-day held 40 bars", one weighted by name and the other by day |
| **Q2** | **T1 PASSES**, and **narrowly** — the observed clears A′_c's p95 by **less than 20 bp** |
| **Q3** | **AGAINST myself: T3 FAILS.** Removing the single largest trade takes the observed below A′_c's p95, exactly as it did against `B_c`. If T1 passes and T3 fails, the honest verdict is that the dip's entry timing is **not established**, and I expect that to be the outcome |
| **Q4** | **the observed decays faster than A′_c across the horizon profile** — observed bp/bar falls from +7.82 at cap 5 to +3.94 at cap 60, and A′_c's fall is **shallower**. This is the mechanism §52a proposed and the one place I expect a clean positive |
| **Q5** | the **median pool size per name exceeds 100 bars**, so the rotation is not degenerate |
| **Q6** | **fewer than 5%** of A′_c draws land on an observed entry bar |
| **Q7** | A′_c's centre sits **above** A′'s +59.42 and **below** the observed +160.55 — confirming it is the intermediate control it is designed to be. If it lands outside that range, the pool is wrong and §8 applies |

---

## 8. What would make me abandon this

- **`[POOL]` or `[CNT]` fails** → the control is not the one described; stop, fix, publish nothing.
- **`[DEG]` above 20%** — more than a fifth of trades on names whose pool barely exceeds their entry
  count → the rotation is degenerate for much of the book and the study reports **that** instead.
- **Q7 fails** — A′_c outside `(A′, observed)` → the pool is mis-specified, and the record says so
  rather than interpreting a number it cannot vouch for.
- **T1 fails outright** → the dip picks days a dart would have picked. **§52's retirement stands as
  written, this reopening expires, and nothing further is owed.**

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). The reopening
authorises this test and no other: mining prefix only, no holdout read, no book touched.*
