# D374 RESULT — the breadth bar was unreachable, and it failed a book more diversified than every random book built from its own names

**Date:** 2026-09-07
**Pre-registration:** [D374](D374-is-the-breadth-hurdle-reachable.md), committed `4c0816c` — **before the runner existed** (R8).
**Runner:** [`scripts/run_d374_breadth_calibration.py`](../../scripts/run_d374_breadth_calibration.py), committed `c2f7887`.
**Artifacts:** `data/d374_breadth_calibration.json`, `data/d374_ctrl_p{0..4}.json`.
**Fixture:** mining prefix only. **No holdout was read.**

---

## 0. The verdict

**The 10% names-to-half-P&L bar is not merely hard. It is unreachable.**

Across **4,952 defined null draws in three arms**, the most diversified random book ever produced
reached **2.98%**. The median reached **0.63%**. **Not one draw came within a factor of three of the
bar.**

And the book the bar failed — D373's, at 2.2613% — sits at the **100.00th percentile of its own
nulls**: zero of 1,971 A′ draws and zero of 981 B draws are as diversified as it is.

> **H4 marked as a breadth failure the most diversified book in its own null distribution.**

| decision | verdict |
|---|---|
| **K1** — is the absolute bar reachable? | **NO. RETIRE IT.** A′ p50 **0.6266%** against a 10% bar |
| **K2** — is the observed book concentrated relative to luck? | **NO** — and not marginally: it is above A′'s **maximum**, not merely its p05 |
| **K3** — are the top-1 and top-5 bars informative? | **Barely.** The 50% top-5 bar sits at the null **median** (50.06%) — a coin flip. And the statistic is unusable (§4) |
| **K4** — the replacement | **Applies.** Adopted for `names_to_half_share` only; the top-k bars are **dropped, not re-thresholded** (§4) |

**Consequence: D373's H4 verdict is corrected from FAIL to PASS.** §6.

---

## 1. What was run

D373's primary cell inherited unchanged — **3,932 trades, 796 names, mean +160.55, median +51.55**,
pinned by `[MIR]` against the committed report before any null ran. **One cell, no best-of-N floor**,
because nothing was being selected (pre-reg §1).

**A′ 2,000 draws, B_c 2,000, B 1,000**, five parts × 400, on D373's own RNG keys — so a given
`(arm, draw)` is literally the same draw in both studies. Measured cost **1.48 s/draw cumulative,
~0.7 s/draw marginal**; 578–586 s per part.

---

## 2. The distributions

`names_to_half_share` — names needed to reach half the P&L, as a share of names traded. **Judged on
the LOW tail**: more names is more diversified, so concentration is the p05 end (pre-reg §4, asserted
by `[DIR]` against a synthetic one-name book and a synthetic uniform book).

| arm | n | min | **p05** | **p50** | p95 | **max** | degenerate |
|---|---:|---:|---:|---:|---:|---:|---:|
| **A′** time rotation, name set held exactly fixed | 1,971 | 0.124% | **0.249%** | **0.627%** | 1.368% | **2.250%** | 29 / 2,000 |
| **B** same-day same-RSI-bucket swap | 981 | 0.098% | 0.198% | 0.794% | 1.586% | 2.146% | 19 / 1,000 |
| **B_c** same-day same-cohort swap | 2,000 | 0.854% | 1.234% | **1.739%** | 2.236% | 2.978% | **0** / 2,000 |
| | | | | | | | |
| **observed** | — | | | **2.2613%** | | | |

**The bar is 10%.** The largest value any random book reached, in any arm, across 4,952 defined
draws, is **2.98%** — and that is B_c's single most extreme draw. **A′'s maximum, 2.250%, is below
the observed book.**

Percentile of the observed book within each arm:

| arm | percentile | draws at least as diversified |
|---|---:|---:|
| **A′** | **100.00** | **0 of 1,971** |
| **B** | **100.00** | **0 of 981** |
| B_c | 95.65 | 87 of 2,000 |

**All three arms agree on K1's direction** — 0.63%, 0.79% and 1.74% are all more than five-fold below
the bar — so the verdict does not depend on which control is load-bearing. That was pre-registered as
the condition for a decisive answer (§9's third abandon clause) and it is satisfied.

---

## 3. Why the bar was unreachable — and it is not about this strategy

A′ holds **the name set and each name's trade count exactly fixed** and varies only *when* the trades
happen. It still produces books where **0.63% of names carry half the P&L**. Nothing about selection,
momentum, or the dip is involved: this is what a fat-tailed return distribution does to any book of
~800 names in this universe.

A bar of 10% asks that **80 names** be needed to reach half the P&L. The observed book needs 18, and
the *median random book with the same names* needs **5**.

**The 10% figure was mine, and D373 §5 says outright where it came from** — "calibrated to exclude
the shape that just failed". That is an honest statement of provenance and it turns out to be exactly
the failure mode it sounds like: a threshold fitted to one observed failure, carrying no information
about the next book.

---

## 4. The top-k share statistics are not fit to gate anything

D373 *passed* top-1 at 5.74% (bar 15%) and top-5 at 20.62% (bar 50%). Both passes are close to
worthless, for two separate reasons.

**(a) The bars sit at the null median.** A′'s p50 for top-1 is **13.75%** against a 15% bar, and for
top-5 **50.06%** against a 50% bar. **A random book fails the top-5 bar roughly half the time.** A
hurdle that a coin flip decides is not a hurdle. *(This falsified Q3, which predicted the top-1 median
at 4–12%; random books are far more top-heavy than I guessed.)*

**(b) The statistic itself is pathological, and worse than the pre-registration anticipated.**
§2a(i) declared that shares are undefined when total P&L ≤ 0, and `[DEG]` excluded those draws. What
`[DEG]` does **not** catch is a draw with a *small positive* total, where the denominator approaches
zero from above and the share explodes while remaining technically "defined":

| | A′ | B | B_c |
|---|---:|---:|---:|
| draws with top-5 share **> 100%** | **233 (11.8%)** | 59 (6.0%) | 0 |
| draws with top-1 share > 100% | 31 | 8 | 0 |
| A′ maxima | top-1 **8,963%** · top-5 **37,546%** · top-10 **65,290%** | | |

This is D371's real-world pathology — top-5 at 142%, top-10 at 231% — reproduced in **one A′ draw in
eight**. It means **A′'s p95 for these statistics (47% and 163%) is itself contaminated** and must not
be shipped as a threshold. K4's mechanical output includes those numbers; **they are not adopted.**

**`names_to_half_share` has none of this**, because it is a count of names divided by a count of
names: bounded in (0, 1], no denominator near zero, well-behaved in every arm.

---

## 5. The replacement hurdle, adopted

Pre-registered as K4 before the answer was known, and **narrowed on the evidence of §4**:

> **H4′ (replaces H4).** A book's `names_to_half_share` must be **at or above the p05 of A′ computed
> on that study's own ledger**, with the count of degenerate draws reported beside it.
>
> **The top-1 and top-5 name-share bars are DROPPED**, not re-thresholded. §4(b) shows the statistic
> is unbounded above and contaminated in ~12% of draws; no percentile of it is trustworthy.
>
> **The threshold is taken from the study's own null, never fixed in advance of the universe.** That
> is precisely what failed here.

For this ledger H4′ resolves to **≥ 0.2488%**, against an observed **2.2613%**.

**A caution that limits the reach of this record.** H4′ is defined *per study*, so it does not
retroactively adjudicate D371's holdout book (2 of 255 = 0.8%). That book lived in a different
universe with roughly half the breadth, and **its A′ distribution has never been computed.** Whether
0.8% is inside or outside its own null is unknown, and this record does not claim to have settled it.
D371's overall retirement rested on five other failing hurdles and is untouched either way.

---

## 6. D373's H4 is corrected: FAIL → PASS

| | D373 as committed | corrected |
|---|---|---|
| names to half, share | 2.26%, bar ≥ 10% | **2.26%, A′ p05 0.2488%** |
| **verdict** | **FAIL** | **PASS** |

**D373's overall verdict is unchanged.** H2, H3 and H7 still fail, H7 at ρ = 0.935, and the §9 abandon
condition is still met. What changes is that **one of the five failures was the hurdle's fault, not
the book's**, and the record should not be read as saying the winners' dip was badly diversified —
by its own null it was the best-diversified book available.

D373's §5 recorded a standing doubt: *"Nothing in this programme has ever cleared the 10%
names-to-half bar. That is either a real and consistent property of every construction tried here, or
the bar is mis-calibrated. D373 cannot distinguish those."* **It was the bar.**

---

## 7. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | A′'s p50 is below 10% — the bar is unreachable. **Point estimate 2–6%** | **HELD on direction, FALSIFIED on magnitude.** The p50 is **0.63%**, three to ten times lower than I guessed. I under-estimated how concentrated a random book is |
| **Q2** | the observed 2.26% is at or above A′'s p05 | **HELD, and by far more than the rule required** — it is above A′'s *maximum* |
| **Q3** | A′'s p50 of top-1 name share is 4–12% | **FALSIFIED** — 13.75% |
| **Q4** | degenerates under 5% for A′ and B_c, higher for B than either | **HELD** — A′ 1.45%, B_c 0%, B 1.9% |
| **Q5** | *against myself:* `[MONO]` finds no discrepancy | **HELD** — scan 18 = searchsorted 18 = published 18 |
| **Q6** | B_c's p50 within 2 percentage points of A′'s — concentration is the return distribution, not selection | **HELD on the letter, NOT on the substance.** 0.63% vs 1.74% is inside a 2-point band but is a **2.8× relative gap**. Selection *does* move concentration: swapping names within the cohort produces systematically more diversified books than rotating the same names in time. **My threshold was too loose to test what I meant**, and I am recording that rather than claiming the prediction |

**Two of six falsified outright, and two more qualified.** The direction of the study's central claim
was right; every magnitude I guessed was wrong.

---

## 8. What this study did not settle

- **Whether 0.8% was a real failure for D371.** §5. Its A′ distribution has never been computed.
- **Whether any *other* absolute threshold in the programme is similarly unreachable.** H4 was checked
  because it had never once been cleared. **That test — "has anything ever passed this?" — is cheap
  and has not been run on the rest of the hurdle set.**
- **A denominator-robust concentration statistic.** §4(b) rules out the top-k shares and adopts
  `names_to_half_share`; it does not go looking for something better.
- **Anything about D373's avenue.** Still open, still the principal's under R15.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book;
`docs/BOOK_PROP.md` remains empty. This study adds no looks to any strategy's multiplicity ledger —
it adjudicates a hurdle, not a strategy.*
