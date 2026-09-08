# D389 RESULT — the floor is ONE factor, it is not any of the four candidates, and 85–98% of it is unattributed

**The most useful thing here is a negative, and it is a sharp one:** the 0.44 floor is a **single
common factor** — PC1 reproduces the pairwise ρ to three decimals — and **none of the named
candidates explains it.** Removing every driver moves the A′ floor 0.449 → 0.383 and the B floor
0.476 → 0.469.

Pre-registration `5bd7d97` predates this file (R8). Decomposition only: no cell scored, nothing
admitted, no holdout read, nothing fetched. Built entirely on the committed `data/d376_series.npz`.

---

## 1. It IS one factor — M1 answered, and cleanly

```
  [A] 4,124 covered bars   PC1 variance share 0.449 vs pairwise rho 0.449   [FACTOR] gap 0.000
       PC2 0.006  PC3 0.005  loading sign agreement 1.00
  [B] 3,185 covered bars   PC1 variance share 0.478 vs pairwise rho 0.476   [FACTOR] gap 0.002
       PC2 0.014  PC3 0.006  loading sign agreement 1.00
```

**PC1's variance share equals the observed pairwise correlation to three decimals in both arms, and
PC2 is an order of magnitude smaller.** Every book loads on it with the same sign — 500 of 500.

**So the floor is not four small mechanisms adding up. It is one thing, and the search for it is
well-posed** — which is the useful half of this study, because it means a single correct
identification would explain the whole floor rather than a slice.

---

## 2. What it is NOT — M2, and every candidate fails

`|corr|` with PC1, and the floor after regressing it out:

```
                        driver     A' |corr|   R^2       B |corr|   R^2
       m (equal-weight market)         0.480  0.231         0.138  0.019
        |m| (NONLINEAR market)         0.070  0.005         0.087  0.008
        m^2 (NONLINEAR market)         0.066  0.004         0.009  0.000
     nlive (eligibility floor)         0.029  0.001         0.054  0.003
      d nlive (breadth change)         0.053  0.003         0.001  0.000
    cross-sectional dispersion         0.008  0.000         0.059  0.003
     1/nlive (equal-weighting)         0.031  0.001         0.052  0.003

  DECOMPOSE                            A' floor    drop      B floor    drop
                nothing (baseline)       0.4488       —       0.4759       —
           m (equal-weight market)       0.3852 -0.0635       0.4721 -0.0038
                  ALL market terms       0.3837 -0.0651       0.4690 -0.0069
                        EVERYTHING       0.3829 -0.0658       0.4688 -0.0071
```

**PICKUP's three named candidates — slot mechanics, equal-weighting, the eligibility floor — score
0.029, 0.031 and 0.052 in A′ and no better in B. They are not it.** Nor is the fourth this record
added, the shared hedge term, in the form `1/nlive` and `nlive` can express it.

**M3 — THE UNATTRIBUTED SHARE: 85% in A′, 98.5% in B.** After removing all seven drivers the A′
floor is **0.383** against a book-clustered SE of **0.0014**, and B's is **0.469** against
**0.0017**. **We still do not know what the floor is.** That is the answer, in the words §3 of the
pre-registration required.

---

## 3. The arms disagree, and that is the finding worth carrying

**Q4 predicted the drivers would explain B better than A′, because the effect is per-bar and B shares
bars. The opposite happened, by a factor of nine.**

- **A′** — same names, rotated times — PC1 correlates **0.480** with the equal-weight market.
- **B** — same days, swapped names — PC1 correlates **0.138** with it, and with nothing else.

**A′ books share market exposure because they hold the same names on a similar exposure schedule, and
that is a quarter of their common factor. B books share the trading DAYS themselves, and their common
factor is almost entirely something about those days that is NOT the market.**

**B is the arm that matters.** It is "two unrelated constructions", the arm gate 1d′ is calibrated
against, and **its floor of 0.476 is 98.5% unexplained.** Whatever makes two independently-built
books co-move here is a property of *which days get traded*, and it is not market direction, not
market magnitude, not breadth, not dispersion, and not the weighting.

---

## 4. M4 — what this means for gate 1d′

**The floor is NOT a scorer artefact.** `1/nlive` — the denominator every book divides by — scores
0.031 and 0.052. **So 1d′ is not calibrated against an artefact of the arithmetic**, which was the
worry §3 of the pre-registration raised. **No rule change is proposed.**

**But 1d′ is calibrated against something real and unidentified.** The gate compares a candidate to
the p95 of its own pool, and that p95 is set by a factor nobody can name. That is not a defect in the
gate — it is the honest state of knowledge, and the gate's pool-relative form (D376 §4) is exactly
the right shape for a floor whose cause is unknown.

---

## 5. Predictions scored

| | prediction | outcome |
|---|---|---|
| **Q1** | PC1 explains most of it — one factor, not four | **HELD, exactly.** Share 0.449 vs ρ 0.449; PC2 0.006 |
| **Q2** | the driver is **nonlinear** market exposure, since a linear hedge removed only 7% | **FALSIFIED.** It is the **linear** market that correlates (0.480) and `|m|`/`m²` that do not (0.070, 0.066). My reasoning — that a linear hedge leaves a nonlinear residual — was wrong: it leaves a *linear* one |
| **Q3** | `1/nlive` explains little | **HELD.** 0.031 and 0.052 |
| **Q4** | drivers explain **B** better than A′ | **FALSIFIED, and backwards by 9×** (15% vs 1.5%). §3 |
| **Q5** | **AGAINST myself: a material share stays unattributed, I remove less than half** | **HELD emphatically.** 85% and 98.5% unattributed |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run** | **HELD.** `[SER]` fired on my own capped subsampling and `[FASTC]` at 9.9e-3. **Second study running that this held, both times by predicting failure** |

**Three of six falsified, and the two aimed at myself both held.**

---

## 6. Assertions

```
  [FASTC]  A identical masks False, median gap 9.87e-04, worst pair 1.81e-02
  [SER]    A p50 rho +0.4488 over 124,750 pairs   (D376: +0.448)
  [FASTC]  B identical masks True,  median gap 8.88e-16, worst pair 2.05e-15
  [SER]    B p50 rho +0.4759 over  31,125 pairs   (D376: +0.476)
  [FASTC] Bc identical masks True,  median gap 8.88e-16, worst pair 2.89e-15
  [SER]   Bc p50 rho +0.9233 over 124,750 pairs   (D376: +0.923)
  [FACTOR] gap 0.000 (A), 0.002 (B)
  [ALIGN]  best driver m: |r| 0.480, shifted one bar 0.018
  [X]      {'SER': True, 'FACTOR': True, 'ALIGN': True}
```

**`[SER]` fired first and caught my own error, not the data's:** the initial runner estimated the
floor from a capped 1,770-pair subsample and disagreed with D376's B p50 by 0.008 — pure sampling.
Replaced with the exact full-pair computation, which is **one matrix product** because B and Bc
masks are identical across books.

**`[FASTC]` then fired at 9.9e-3, and the guard itself was wrong.** It asserted individual-pair
equality between two estimators that genuinely differ for A′ (per-pair mask intersection against a
common mask, up to 3 bars of 4,124). **The study reads the arm's median, so the guard was restated to
bound the median gap (9.87e-04) and report the worst pair beside it** — and to demand exactness where
the masks *are* identical, which it gets at 8.9e-16.

---

## 7. What this establishes

**Establishes:**
- **The floor is ONE common factor**, not an accumulation — PC1 reproduces ρ exactly, PC2 is 1/75th
  of it, and all 500 books load with the same sign.
- **It is none of the four named candidates.** Slot mechanics, equal-weighting, the eligibility floor
  and the shared hedge term are all ≤ 0.052 in `|corr|`.
- **It is not a scorer artefact**, so gate 1d′ needs no restating.
- **In the arm that matters — two unrelated constructions sharing days — it is 98.5% unexplained.**

**Does NOT establish:** what it is. **The honest state is that a single, strong, universal factor
drives every book in this universe and nothing measured here identifies it.**

**Where a successor should look, and it follows from §3:** the factor lives in *which days get
traded*, not in the market's behaviour on them. That points at the **entry-condition distribution**
— what makes a bar eligible — rather than at anything in the return generating process. **That is a
different object from every driver tested here and it was not available in this artifact.**

---

*Result committed 2026-09-09, separately from the pre-registration, per R8. No cell scored, nothing
admitted, no holdout read, no new data fetched.*
