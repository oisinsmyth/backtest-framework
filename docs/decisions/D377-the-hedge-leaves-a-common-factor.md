# D377 — the hedge leaves a common factor. Can any of four remove it without removing the edge?

**Date:** 2026-09-07
**Kind:** **METHODOLOGY / CONVENTION.** Selects a hedge convention for future studies. Admits nothing,
reads no holdout, changes no book.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Follows:** [D376](D376-what-do-two-books-in-this-universe-correlate-at.md), whose ensemble is
running as this is written.

---

## 0. Why this record exists

D376's 12-draw smoke measured the **pairwise correlation between two books that share nothing but
this universe** — different names, different days, different timing, both hedged — at **≈ 0.46
median, ≈ 0.52 at p95**. *(Provisional. The 500-draw figures replace these in the result, and if they
move materially §8's abandon clause applies.)*

**That is what the hedge leaves behind.** If the hedge spanned the common factor, two unrelated books
would correlate near zero. They do not, and three things follow:

1. **Diversification here is worth about half what it looks like.** Two books at ρ ≈ 0.46 give
   portfolio vol ≈ 0.85× a single book, not ≈ 0.71×.
2. **Gate 1d's 0.50 bar sits inside the structural noise** — D376 L1.
3. **Every book carries uncompensated variance**, which depresses every Sharpe the programme has ever
   reported.

**The incumbent hedge is a unit subtraction.** `assert_HX(..., hedged=True)` defines the hedged
series as `sgn · (v − m)` where `m` is the floored equal-weight market: **beta is assumed to be
exactly 1 for every name, on every bar.** A properly lagged per-name rolling beta —
`V47.roll_beta(r1T, m_f)`, window 63, minimum 21 observations, window ending at t−1 — **already
exists in `d348_prep` and is not used in the default path.** It is carried only as D350's secondary
`pnl_beta_adjusted` reading.

The names these constructions hold are momentum winners and dip-buys: there is no reason to expect
them to be beta-1, and a systematic beta miss is exactly the kind of thing that shows up as a shared
factor across otherwise unrelated books.

### The tension this study exists to resolve

**A hedge that subtracts everything drives the correlation to zero and the edge to zero with it.**
D373's B_c control already showed **+126.54 bp of the observed +160.55 per trade** is available to a
random name from the same cohort on the same day, and D376's smoke puts two arbitrary cohort books at
ρ ≈ 0.92. **So the cohort exposure may BE the edge.** If so, the hedge that best removes the common
factor will also remove the return, and the honest finding is that **no hedge both diversifies and
preserves this edge** — which is a real result about the strategy, not a failure of the study.

This record therefore fixes, before anything runs, that **a hedge is an improvement only if it cuts
the floor AND preserves the edge.** §5.

---

## 1. What is fixed

**The book:** D373's primary cell, inherited unchanged and not re-selected — `rev_5` dip inside the
`mom_252_21` top decile, long, next-open fill, 40-bar cap, cell **10:90 / cap 40**, mining prefix.
Committed ledger **3,932 trades, 796 names, mean +160.55, median +51.55**.

**The populations:** D376's three arms, on D376's own `draw_rng(draw, arm)` keys, so a given
`(arm, draw)` is the same draw in D373, D374, D376 and here.

| arm | two draws share | stands for |
|---|---|---|
| **B** same-day same-RSI-bucket swap | universe, floor, calendar, slot mechanics | **two genuinely unrelated constructions — the PRIMARY** |
| **A′** per-name time rotation | the above plus the exact name set | the ceiling of structural correlation |
| **B_c** same-day same-cohort swap | the above plus the winner cohort | two books inside the same cohort |

**B is primary** because the floor that matters for diversification and for gate 1d is the one
between *unrelated* books. A′ and B_c are reported and bound it.

---

## 2. The four hedges

Each must be computable from information available at **t−1**. That is the whole game and §6's
`[LAG]` proves it rather than asserting it in prose.

| | hedge | per-name subtraction on bar t | why it is a candidate |
|---|---|---|---|
| **H0** | **incumbent — unit market** | `m_f[t]` | the baseline every past number in this programme was computed under |
| **H1** | **per-name rolling beta** | `beta[t, name] · m_f[t]`, `beta = roll_beta(r1T, m_f)`, window 63 / min 21, ending t−1 | **already built and already lagged.** Zero new estimator. The obvious first fix: our names are not beta-1 |
| **H2** | **cohort** | the equal-weight return of eligible names in the **same `mom_252_21` decile at t−1** | D376 puts two cohort books at ρ ≈ 0.92. This removes that factor directly — **and is the candidate most likely to remove the edge with it** |
| **H3** | **price decile** | the equal-weight return of eligible names in the **same price decile at t−1** | price is a live axis here: D284 died on it, and D373's edge was **+183.5 bp** below the median price against **+137.6** above |

**Four candidates including the incumbent. Disclosed as a best-of-4 and priced in §7.**

### 2a. The reconstruction that makes this cheap, and the assertion that makes it safe

The hedged deployed series is a per-bar mean over held names of `r − h`. Since the held set does not
depend on the hedge, that equals

```
book_dep_x^H[t]  =  book_dep_unhedged[t]  −  mean over names held at t of  h_name[t]
```

So **one pass over the draws** can accumulate, per draw per bar, the unhedged deployed series plus
the mean of each candidate hedge over the held names — and all four hedged series are reconstructable
afterwards without re-running the book. **Cost is one D376 run, not four.**

**`[REC]` is therefore load-bearing:** the reconstructed **H0** series must equal the kernel's own
`book_dep_x` **bit-for-bit** on every defined bar. If reconstruction does not reproduce the incumbent
exactly, nothing downstream means anything and the study stops.

---

## 3. What is measured, for each hedge

| | |
|---|---|
| **the floor** | pairwise correlation across the ensemble — p05 / p50 / p95, bootstrap SE on each, per arm, and on the common window D376 added |
| **the edge** | the observed book's **gross mean and median per trade** under that hedge |
| **the book** | the observed book's deployed **bp/bar, vol, Sharpe and maxDD**, gross and net PUB |
| **the invariant** | the **unhedged** per-trade mean, which must be **identical across all four** |

**Both lenses, never on the same statistic** (`CLAUDE.md`, FINDINGS §10): the per-trade figures are
path-invariant and the bp/bar figures path-variant, reported separately.

---

## 4. Direction

**The floor is judged on wanting it LOW** — a hedge is better when unrelated books correlate less.
**The edge is judged on wanting it HIGH.** Two opposite directions in one study is precisely the
condition under which D374's tail-direction lesson bites, so `[DIR]` asserts both: a duplicated book
must sit above the correlation p95, and a book with its returns zeroed must sit below the edge floor.

---

## 5. The decision rules, pre-registered

**A hedge is adopted only if it clears BOTH legs. Neither alone is sufficient.**

**M1 — does it cut the floor?** B-arm pair **p50** under the candidate, against H0's.
- The candidate must beat H0 by **≥ 4 bootstrap SE**. Four rather than the usual two, because this is
  a **best-of-4** selection (§7). A margin inside 4 SE is **UNRESOLVED, never adopted.**

**M2 — does it preserve the edge?** The observed book's **gross mean per trade** under the candidate,
against H0's **+160.55**.
- **≥ 90% of H0's** → preserved.
- **< 90%** → **the hedge is REJECTED however much correlation it removes.** A hedge that pays for
  diversification with return is a different strategy, not a better hedge.

**M3 — the winner.** Among candidates clearing M1 and M2, the one with the lowest B-arm p50. If none
clears both, **H0 stands** and the record says the floor is not a hedge artifact.

**M4 — the cost of adopting.** If a hedge other than H0 wins, **every gross-per-trade number this
programme has published becomes non-comparable**, because the headline statistic is hedged. The
result must therefore restate, for this cell, what H0's committed **+160.55 / +51.55** become under
the winner, and say plainly that past records are on the old convention. **A convention change is not
free and this record refuses to treat it as free.**

**M5 — the interesting failure.** If **H2 clears M1 by a wide margin and fails M2**, that is the
finding, and it is bigger than the hedge question: **the cohort exposure IS the edge**, and no hedge
can separate them. It would mean this construction's return is compensation for a factor, not a
signal — and it would bear directly on the D373 avenue, which is still open and still the principal's.

---

## 6. Assertions

| tag | what it proves |
|---|---|
| **`[MIR]`** | the inherited cell reproduces D373's committed 3,932 / +160.55 / +51.55 before anything else |
| **`[REC]`** | the reconstructed **H0** series equals the kernel's `book_dep_x` **bit-for-bit** on every defined bar (§2a) |
| **`[LAG]`** | every hedge is rebuilt from **t−1** information by a **second implementation that never calls the hedge builder**, and must match bit-for-bit. `roll_beta`'s window already ends at t−1; H2 and H3 use decile membership at t−1. This is the runner lag audit applied to the hedge, and it is the assertion this study most needs |
| **`[INV]`** | the **unhedged** per-trade mean is identical across all four hedges — the hedge must not touch the trades |
| **`[DIR]`** | both directions at once: a duplicated book scores **above** the correlation p95; a return-zeroed book scores **below** the edge floor (§4) |
| **`[SER]`** | inherited from D376 — the observed H0 series reproduces D373 H7's ρ = 0.9346373668783634 to 1e-12 |
| **`[DEG]`** | undefined correlations and undefined betas are **counted and excluded, never absorbed**; the runner refuses above 20% per arm. A name with fewer than 21 beta observations is `NaN` and must be handled explicitly, not silently zero-hedged |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken input, including a hedge deliberately given tomorrow's return |

**Persist before rendering.**

---

## 7. The search cost, stated

**Four hedge candidates, one cell, one primary statistic, on already-spent in-sample data.** Under the
principal's ruling of 2026-09-07 and R14's first amendment, selection on spent data is free and what
it costs is the **prior**. Disclosed, and priced two ways:

- M1's margin requirement is **4 SE rather than 2**, doubling the usual UNRESOLVED band for the
  best-of-4.
- The result reports **all four candidates in full**, so the reader sees the whole grid rather than
  the winner.

**No holdout is read and none is needed** — a hedge convention is a measurement choice, not a claim
about out-of-sample return. It does not touch any strategy's multiplicity ledger.

---

## 8. Predictions

D374's and D376's magnitudes were both wrong while their directions held, so the point estimates are
recorded to be scored, not defended.

| | prediction |
|---|---|
| **Q1** | **H1 (per-name beta) cuts the floor**, but not to near zero. B-arm p50 lands in **0.30–0.42** against H0's ≈ 0.46 |
| **Q2** | **H2 (cohort) cuts it most** — B-arm p50 **below 0.20** |
| **Q3** | **AND H2 FAILS M2.** Its gross mean per trade falls below 90% of +160.55, so the best diversifier is rejected. **This is the prediction against my own proposal** — I am proposing a hedge study whose most promising candidate I expect to be disqualified, and if it is, M5 says the edge is a factor exposure |
| **Q4** | **H3 (price decile) moves the floor by less than 0.05** — price is a real axis for *return* here but not the shared factor |
| **Q5** | `[INV]` holds exactly: the unhedged per-trade mean is bit-identical across all four. A failure here is a bug, not a finding |
| **Q6** | **H0 is not the winner on M1** — at least one candidate beats the incumbent by ≥ 4 SE. If none does, the premise of this study was wrong and §9 applies |
| **Q7** | the **A′** and **B_c** arms move in the same direction as **B** under every hedge. If an arm moves the other way, the hedge is doing something structural I have not understood, and the result says so rather than reporting the primary alone |

---

## 9. What would make me abandon this

- **`[REC]` or `[LAG]` fails** → stop, fix, publish nothing. A hedge that fails the lag audit is
  look-ahead, and D279 lost ~93% of its apparent edge to exactly that.
- **No candidate clears M1 by 4 SE** → **H0 stands, and the result says the floor is not a hedge
  artifact.** The common factor would then be coming from something the hedge cannot reach — shared
  slot mechanics, equal-weighting, or the eligibility floor itself — and the record names that as the
  next question rather than dressing a null result as a finding.
- **D376's final B-arm floor comes back far from the smoke's ≈ 0.46** — say below 0.20 — → the premise
  weakens and this record is **amended in writing before the result is read**, not quietly
  reinterpreted afterwards.
- **Degenerate betas exceed 20% of held name-bars** → report that instead; a hedge undefined for a
  fifth of positions is not a hedge.

---

*Pre-registered 2026-09-07. Runner does not exist at the time of this commit (R8). D376's ensemble is
still building; if its final numbers move the premise, §9's third clause governs.*
