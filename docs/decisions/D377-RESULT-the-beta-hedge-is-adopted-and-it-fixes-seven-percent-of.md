# D377 RESULT — the beta hedge is adopted, it fixes 7% of the problem, and the cohort hedge proves the cohort IS the edge

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D377-RESULT-the-beta-hedge-is-adopted-and-it-fixes-seven-percent-of-the-problem.md`. The H1 above is the full title.*

**Date:** 2026-09-07
**Pre-registration:** [D377](D377-the-hedge-leaves-a-common-factor.md), committed `3888ae9`, amended `c59f6de` — **both before the runner existed** (R8).
**Runner:** [`scripts/run_d377_hedge.py`](../../scripts/run_d377_hedge.py), committed `e8e20a1`.
**Artifacts:** `data/d377_hedge.json` — committed, and it carries every number quoted below.
`data/d377_ensemble.npz` (500 draws × 3 arms × 4 hedges) is **136 MB, four times the largest file
this repo tracks, and is gitignored with the reason recorded there.** It is exactly reproducible —
`uv run python scripts/run_d377_hedge.py --build --draws 500`, ~10 min, deterministic seeds — which
is the repo's standing pattern of gitignored cache plus committed rebuild script. *(D376's 34 MB
ensemble was committed; this one is not, and the asymmetry is size, stated rather than glossed.)*
**Fixture:** mining prefix only. **No holdout was read.**

---

## 0. The verdict

| hedge | what it subtracts | **B p50** | drop vs H0 | in SE | **M1** | gross/trade | kept | **M2** |
|---|---|---:|---:|---:|:--|---:|---:|:--|
| **H0** | unit market (incumbent) | +0.4728 | — | — | baseline | **+160.55** | 100% | baseline |
| **H1** | **per-name rolling beta 63/21** | **+0.4404** | +0.0324 | **+10.6** | **PASS** | +156.57 | **97.5%** | **PASS** |
| **H2** | `mom_252_21` decile cohort | **+0.3242** | +0.1485 | **+38.8** | **PASS** | **+34.08** | **21.2%** | **FAIL** |
| **H3** | price decile | +0.4439 | +0.0288 | +9.7 | PASS | +160.47 | 99.9% | PASS |

**M3 — H1 is adopted.** It clears both pre-registered legs: the floor drops by 10.6 standard errors,
and 97.5% of the gross per-trade edge survives.

**And the honest headline is the second sentence, not the first: the floor falls from 0.473 to
0.440.** That is statistically decisive and practically small. **The hedge was not the main source of
the common factor** — correcting a decade of assumed unit betas removes about **7%** of it.

**M5 fired, and it is the finding that outlives the hedge question.** H2 works exactly as designed —
it collapses the within-cohort floor from **0.917 to 0.375** — and it **destroys 79% of the return**.
**The cohort exposure is the edge.** §3.

---

## 1. What was run, and what `[REC]` caught first

500 draws × 3 arms × 4 hedges, reconstructed in **one pass** (pre-reg §2a): since the held set does
not depend on the hedge, the hedged series is the unhedged series minus the mean hedge return over
held names. 1.12 s/draw, 568 s.

**`[REC]` fired at 1.059e-03 — three orders above float noise, so a specification error rather than
rounding.** The cause was not the hedge arithmetic: **the 73 positions still open at the last bar are
in the kernel's series and not in the trade ledger**, which `assert_HX` already documents. The
mismatch was a **contiguous 39-bar tail** (4,148 → 4,186 of 4,187), and on the 3,146 bars the ledger
does cover, the reconstruction matched the kernel to **8.24e-17**.

The reconstruction was right and the mask was wrong. `[TAIL]` now restricts each book to the bars its
own ledger covers and **asserts the uncovered bars are a contiguous tail** — a non-contiguous
mismatch would mean something else entirely. Final `[REC]`: **8.240e-17 over 3,146 bars against a
1e-12 bound.**

**`[LAG]` was proved, not asserted:** 189 betas re-derived by explicit OLS over bars t−63…t−1, and
300 decile memberships re-derived from the t−1 grid, both by implementations that never call the
hedge builder. A beta rolled back from **tomorrow** and an unlagged decile both **raise**.

**`[DEG]`:** the rolling beta is defined on 61.9% of *panel* name-bars but **fallback count on HELD
name-bars is zero** — the undefined ones are warm-up on names never held. H2 and H3 fall back to the
unit market on **1.6%** and **1.7%** of held name-bars.

---

## 2. H1 is a real improvement and it does not fix the problem

| arm | H0 | **H1** | change |
|---|---:|---:|---:|
| **B** unrelated books — primary | +0.4728 | **+0.4404** | −0.032 |
| A′ identical name set | +0.4391 | +0.3649 | −0.074 |
| B_c same cohort | +0.9166 | +0.9032 | −0.013 |

With 250 books and 31,125 pairs the book-clustered SE of the drop is **0.0031**, so 0.032 is 10.6 SE.
**The 4-SE bar (§7's best-of-4 pricing) is a statistical bar, and at this sample size it is easy to
clear.** It says the improvement is real. It does not say it is large.

**Practically:** two books at ρ = 0.473 give portfolio vol of 0.858× a single book; at ρ = 0.440,
0.849×. **The diversification problem D376 identified is essentially untouched.**

**H3 is a near-tie and the choice between them is arbitrary at this margin** — +0.4439 against H1's
+0.4404, and 99.9% edge retention against 97.5%. M3 picks H1 on the lower floor, by 0.0035. **Whether
the two are complementary was not tested** — no combined hedge was in the pre-registered grid, and
adding one now would be a post-hoc fifth candidate.

**So the common factor is mostly NOT unhedged beta.** D376 §1 established it is a **per-bar** effect;
this study rules out per-name beta error as its main source and leaves the candidates D376 §8 named
and nothing has measured: **shared slot mechanics, equal-weighting, and the eligibility floor
itself.**

---

## 3. M5 — the cohort hedge works, and that is the bad news

H2 subtracts the equal-weight return of the name's own `mom_252_21` decile at t−1. It does exactly
what a hedge should:

| | H0 | **H2** |
|---|---:|---:|
| within-cohort floor (B_c p50) | +0.9166 | **+0.3752** |
| unrelated-book floor (B p50) | +0.4728 | **+0.3242** |
| **gross mean per trade** | **+160.55** | **+34.08** |
| gross median per trade | +51.55 | **−30.74** |

**It removes the factor and it removes the return with it. 79% of the edge is cohort exposure.** The
median goes negative: with the cohort hedged out, the typical trade loses money.

**This is the third independent measurement of the same fact, by three unrelated methods:**

| study | lens | finding |
|---|---|---|
| **D373** | return, per trade | B_c's p50 was **+126.54** of the observed **+160.55** — available to a random name from the same cohort on the same day |
| **D376** | covariance | two arbitrary cohort books correlate at **+0.923** |
| **D377** | hedge | removing the cohort removes **79%** of the return |

**The winners'-dip construction is a levered claim on the momentum decile, and the dip timing is a
rounding error on it.** M5 as pre-registered: *"this construction's return is compensation for a
factor, not a signal."* That is what the evidence says.

**This bears on the D373 avenue, which is still open and still the principal's under R15.** I am not
closing it.

---

## 4. M4 — what adopting H1 costs

**Every gross-per-trade number this programme has published is on the H0 convention.** For the D373
cell:

| | H0, as committed | **H1** |
|---|---:|---:|
| gross mean per trade | +160.55 | **+156.57** |
| gross median per trade | +51.55 | **+66.87** |

The mean falls 2.5% and **the median rises 30%** — beta correction takes more off the tail than the
middle, which is consistent with high-beta names carrying the large winners.

**Scope of the adoption, and it is narrow.** The pre-registration says this study *"selects a hedge
convention for future studies."* **It does not re-base past records**, which stay on H0 and must be
labelled as such wherever compared. Given that the benefit is a 0.032 reduction in a 0.47 floor, **a
wholesale re-basing of the programme's published numbers is not obviously worth it, and that is the
principal's call rather than this record's.** What binds from here is that new studies use H1 and say
so.

---

## 5. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | H1 cuts the floor; B p50 in **0.30–0.42** | **FALSIFIED** — +0.4404. It cut it, by a tenth of what I guessed |
| **Q2** | H2 cuts it most, B p50 **below 0.20** | **FALSIFIED on magnitude** — it does cut it most, at +0.3242, but not below 0.20 |
| **Q3** | *against my own proposal:* **H2 fails M2** | **HELD** — 21.2% of the edge kept against a 90% bar |
| **Q4** | H3 moves the floor by less than 0.05 | **HELD** — 0.029 |
| **Q5** | `[INV]` holds exactly | **HELD** — unhedged per-trade mean +160.55 across all four |
| **Q6** | some candidate beats H0 by ≥ 4 SE | **HELD** — all three do |
| **Q7** | A′ and B_c move the same direction as B under every hedge | **HELD** |

**Two falsified, five held — and both falsifications are magnitude, not direction.** That is now
**four studies running** (D374, D376, D377 and D373's own predictions) where I called the direction
correctly and the scale wrong. The pattern is consistent and worth naming: **I under-estimate how
much of these books is structure and over-estimate how much a correction will move.**

---

## 6. What this did not settle

- **Where the remaining 0.44 comes from.** Ruled out: per-name beta error, price-decile exposure.
  Untested: **shared slot mechanics, equal-weighting, the eligibility floor.**
- **Whether H1 and H3 are complementary.** A combined hedge was not in the pre-registered grid and
  adding one after seeing the result would be a post-hoc fifth candidate.
- **Whether any of this holds outside the D373 cell.** One cell, inherited.
- **Whether the programme's past numbers should be re-based.** §4 — the principal's.
- **The D373 avenue.** Still open, still the principal's.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book. No
looks added to any strategy's multiplicity ledger — this selects a convention.*
