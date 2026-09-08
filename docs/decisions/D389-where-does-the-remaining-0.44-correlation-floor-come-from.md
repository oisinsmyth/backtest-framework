# D389 PRE-REGISTRATION — where does the remaining 0.44 correlation floor come from?

**R8: committed before the runner exists. Result separately.** A **mechanism decomposition**, not a
signal test: it scores no cell, admits nothing, reads no holdout, and touches no multiplicity ledger
(R13) because there is no strategy.

**Why this and not another signal.** The floor is upstream of every study in the programme — it
bounds how independent any two books can be claimed to be, and gate 1d′ is defined in terms of it.
It is also free: `data/d376_series.npz` already holds **500 A′ books, 250 B books and 500 B_c books
× 4,187 bars with their masks**, committed. **Nothing new is fetched or built.**

---

## 1. What is already established, and is not re-litigated

| | |
|---|---|
| **the floor** | **0.440** after D377's H1 beta hedge, down from 0.473 (D376: A′ p50 +0.448, B p50 +0.476, B_c p50 +0.923) |
| **it is a PER-BAR effect** | D376 §1: books sharing **days** (B, +0.476) correlate MORE than books sharing **names** (A′, +0.448). That inverted D376's own Q3 |
| **ruled out — per-name beta error** | D377's H1 removes **7%** of it (0.473 → 0.440, +10.6 SE but practically small) |
| **ruled out — price exposure** | D377's H3, +0.0288 |
| **NOT a nuisance — cohort exposure** | D377's H2 collapses the within-cohort floor 0.917 → 0.375 and **destroys 79% of the return**. The cohort IS the edge, so removing it is not available |

**Untested and named in PICKUP §0d.2:** shared **slot mechanics**, **equal-weighting**, the
**eligibility floor**. **This record adds a fourth that nobody has named: the shared HEDGE TERM.**

---

## 2. The method — EXTRACT the factor, then IDENTIFY it

**The order matters and is the point.** Every prior attempt hypothesised a mechanism and tested it
(H1 beta, H2 cohort, H3 price). Two of three explained almost nothing. **This one extracts the common
factor empirically first and only then asks what it is**, so the answer is not limited to mechanisms
someone thought of.

**Step 1 — EXTRACT.** Principal component of the A′ book matrix (500 × 4,187), computed on bars where
the mask is defined for a stated minimum of books, each book standardised. If a single common factor
drives the floor, **PC1's variance share should reproduce the observed mean pairwise ρ**; that
agreement is itself a check and is reported as `[FACTOR]`.

**Step 2 — IDENTIFY.** Correlate PC1 against candidate drivers computed from the panel:

| driver | the mechanism it stands for |
|---|---|
| `m_t` — the floored equal-weight market return | residual market exposure the hedge missed |
| **`|m_t|` and `m_t²`** | **NONLINEAR** market exposure — a beta hedge is linear, so this is exactly what H1 could not remove |
| `nlive_t`, `Δnlive_t` | **eligibility floor** and universe breadth |
| cross-sectional dispersion of returns | the scale every equal-weighted book shares |
| `1/nlive_t` | **equal-weighting** — the scorer divides by `nlive`, so this is the weighting's own footprint |

**Step 3 — DECOMPOSE.** Regress every book on the drivers that Step 2 identifies, and **re-measure the
pairwise floor on the residuals.** The drop is the attributable share. What remains is unattributed
and must be reported as such.

**Both arms, and the difference is evidence.** A′ holds names fixed and rotates time; B holds days
fixed and swaps names. **A driver that explains B but not A′ is a day effect; one that explains both
is a universe effect.**

---

## 3. Decision rules

**M1 — is it ONE factor?** PC1's variance share against the observed mean pairwise ρ. If PC1 explains
far less than ρ, the floor is **not** a single common factor and every single-mechanism hypothesis —
including all four candidates — is mis-framed. **That would be the most useful outcome.**

**M2 — what is it?** The driver, or set, whose removal drops the floor most. **Reported with the
residual floor, not as a percentage of a number nobody can check.**

**M3 — how much is unattributed?** The residual floor after removing everything identified.
**If it stays near 0.44, the answer is "we still do not know" and the record says exactly that.**

**M4 — does gate 1d′ need restating again?** 1d′ compares a candidate to the p95 of its own pool.
**If the floor is largely an artefact of the scorer (the `1/nlive` denominator, or a shared hedge
term), then 1d′ is calibrated against an artefact** and the gate should be computed on residuals
instead. That is a rule change and would be proposed, not made.

---

## 4. Assertions

| tag | what it proves |
|---|---|
| **`[SER]`** | the loaded series reproduce D376's headline numbers — A′ p50 **+0.448**, B p50 **+0.476**, B_c p50 **+0.923** — before anything is decomposed. If they do not, the artifact is not what this record thinks it is |
| **`[MASK]`** | every correlation is computed on the **intersection** of two defined masks, with the common-bar count reported. D376's `corr_masked` rule, unchanged |
| **`[CLU]`** | standard errors are **book-clustered**. 124,750 A′ pairs come from 500 books; a pair-level bootstrap would treat one book as ~500 independent observations |
| **`[FACTOR]`** | PC1's variance share is reconciled against the mean pairwise ρ **by an independent calculation**, not asserted from the eigenvalue alone |
| **`[ALIGN]`** | driver series are aligned to the book series **by date index**, and a deliberate one-bar shift must break the alignment check |
| **`[X]`** | every audit raises on a break that moves the exact scalar it compares |

---

## 5. Predictions

| | |
|---|---|
| **Q1** | **PC1 explains most of it** — the floor is one factor, not four small ones |
| **Q2** | **the driver is NONLINEAR market exposure** (`|m|`, `m²`), because a linear beta hedge removed only 7% and that is precisely the part a linear hedge cannot reach |
| **Q3** | **`1/nlive` explains little.** A common time-varying SCALE does not induce linear correlation between two zero-mean series — it induces correlation of *absolute* returns. If `1/nlive` scores highly I will suspect the diagnostic before believing it |
| **Q4** | **the drivers explain B better than A′**, since the effect is per-bar and B shares bars |
| **Q5** | **AGAINST myself: a material share stays unattributed** — I expect to remove less than half and to have to write "we still do not know" |
| **Q6** | **AGAINST myself: at least one assertion fires on the first run.** Predicted correctly in D388 for the first time in four studies, by predicting failure. Same here |

---

## 6. What would make me abandon this

- **`[SER]` fails** → the committed artifact is not D376's object; stop and re-derive it.
- **`[FACTOR]` fails** → PC1 and the pairwise ρ disagree by more than the stated tolerance, so the
  extraction is not measuring the floor. Stop; publish nothing.
- **M1 says it is not one factor** → report that and stop. Chasing four small mechanisms with this
  artifact would be a fishing expedition, and the honest output is the negative.

---

*Pre-registered 2026-09-09. Runner does not exist at the time of this commit (R8). Decomposition only:
no cell scored, nothing admitted, no holdout read, no new data fetched.*
