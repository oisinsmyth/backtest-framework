# D376 — what do two books in this universe correlate at? Calibrating gate 1d

**Date:** 2026-09-07
**Kind:** **METHODOLOGY.** Adjudicates a gate, not a strategy. Admits nothing, reads no holdout.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**
**Follows:** [D375](D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is.md) §4,
which found gate 1d the one stage-1 gate that is under-evidenced.

---

## 0. Why this record exists

**Gate 1d — *correlation to every existing book arm < 0.50, at signal level* — has been applied
exactly once in the programme's history.** It is defined in [D289](D289-the-promotion-pipeline.md)
§92 and appears in no other decision record. Its one application is
[D373](D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md)'s H7, at **ρ = 0.9346**.

Every correlation ever recorded against it:

| pair | universe | ρ | |
|---|---|---:|---|
| S1 ↔ S2 | liquid US **ETFs** | +0.123, later +0.150 | pass |
| S1 ↔ M1 | liquid US **ETFs** | −0.069 | pass |
| **D373 ↔ D365** | **US single names** | **+0.935** | **fail** |

**Both passes are from a different universe than all current work.** The single-name universe has
exactly one measurement, and it is the failure.

**The unknown is the structural floor.** Two books here share an eligibility floor, a hedge against
the same floored equal-weight market, the same slot mechanics, the same calendar and the same 3,185
deployed bars. **How much correlation does that alone produce, before any shared signal?**

- If the floor is near **0.5**, gate 1d is unreachable in this universe and D373's 0.935 says far
  less than it appears.
- If it is near **0.1**, the 0.935 is exactly as damning as it reads, and the gate is sound.

**One number in the record suggests the floor can be high:** `docs/BOOK.md` records **the same
strategy on two disjoint 57/60-name ETF universes correlating at ρ = +0.978.** That is a
same-strategy figure and does not answer the question, but it shows how much correlation a shared
construction carries even across an entirely disjoint name set.

### What this study does NOT do

- It does not revisit D373's verdict. H2, H3 and H7 stand as committed unless L3 says otherwise, and
  the H4 correction of D374 is already recorded.
- It does not reopen the D373 avenue. Still the principal's under R15.
- It reads **no holdout.**

---

## 1. The construction, frozen

**D373's primary cell, inherited unchanged and not re-selected:** a fresh `rev_5` dip inside the
`mom_252_21` top decile, entered long at the next open, hedged against the floored market, 40-bar
cap. Cell **10:90 / cap 40**, mining prefix only. Committed ledger: **3,932 trades, 796 names, mean
+160.55, median +51.55**.

**One cell. No best-of-N floor** — nothing is being selected (as D374 §1).

---

## 2. The series, and it must be the one gate 1d was measured with

The correlated quantity is the **deployed book's hedged bar series** — `book_dep_x` masked by
`mask_dep`, exactly the object D373's H7 used against `data/d365_series_95_80.csv`.

**`[SER]` will assert that the observed book's series reproduces H7's ρ = 0.9346373668783634 to
1e-12 before any pair is computed.** If the series definition drifts, every number in this study
would be answering a different question than the gate.

**Pairs are correlated on the INTERSECTION of their two defined masks**, and the intersection size is
carried per pair. Exposure is ~99.97%, so this should be near-total; `[MASK]` makes it checkable
rather than assumed.

---

## 3. The three populations, and what each one means

Each null arm generates books that share a different amount of structure with each other. **The point
of running all three is that they bracket the question**, not that one is a control for the others.

| arm | two draws share… | two draws differ in… | the population it stands for |
|---|---|---|---|
| **B** same-day same-RSI-bucket swap | universe, floor, hedge, calendar, slot mechanics | names, drawn from a loose pool | **two genuinely unrelated constructions.** The floor that matters for gate 1d as written |
| **A′** per-name time rotation | all of the above **plus the exact name set and each name's trade count** | only *when* trades happen | **the ceiling of structural correlation.** More shared structure than two real strategies would have |
| **B_c** same-day same-cohort swap | all of B's, plus confinement to the `mom_252_21` top decile | names, drawn from that cohort | **two constructions that both select inside the winner cohort** — the population D373 and D365 both live in |

**B_c is the one that bears on D373's H7**, and there is an arithmetic reason to expect it high: the
daily top decile is ~100 names and each book holds ~50, so **two independent draws should overlap
around half their held names by chance alone.** If that produces a high correlation, then 0.935 is
above the cohort's own baseline by less than it appears.

**No arm is "load-bearing" here** — the three answer three different questions and the decision rules
below name which arm settles which. D374 §3 fixed A′ as load-bearing because that study had a single
question; this one does not.

**Direction: correlation is judged on the HIGH tail — p95.** Too much correlation is the failure.
This is the *opposite* of D374's H4 and the same as H1–H3. Stated because D374 established that tail
direction is the easiest thing here to invert, and `[DIR]` will assert it.

**Draws: 500**, single process, on D373's own `draw_rng(draw, arm)` keys so a given `(arm, draw)` is
the same draw across D373, D374 and this study. That yields **500 A′, 500 B_c and 250 B** books, so
**124,750 / 124,750 / 31,125 pairs** — far more than needed to place a p95. At D374's measured
~0.7 s/draw this is **under 10 minutes**; the result will report the measured marginal rate, not the
cumulative rate the progress log prints.

---

## 4. The decision rules, pre-registered

**L1 — is 0.50 reachable by two unrelated books here?** Compare the bar to **B**'s pair distribution.
- **B's p95 < 0.50** → two unrelated constructions in this universe are comfortably under the bar.
  **Gate 1d is SOUND**, and D373's 0.935 is a real finding about shared positions.
- **B's p95 ≥ 0.50** → the bar is inside the structural noise and **cannot separate an unrelated book
  from a duplicate. Gate 1d must be replaced** (L4).

**L2 — can anything inside a cohort ever pass?** Compare the bar to **B_c**'s pair distribution.
- **B_c's p05 > 0.50** → every pair of books selecting inside this cohort fails gate 1d automatically,
  **whatever their signals.** The gate would then be a statement about the cohort, not about the
  candidate, and must be scoped to say so.

**L3 — does D373's H7 survive?** Is **0.9346 above B_c's p95**?
- **yes** → H7's conclusion stands: D373 is closer to D365 than two arbitrary cohort books are to
  each other, and calling it the retired book re-expressed was correct.
- **no** → **H7 is corrected**, the way D374 corrected H4, and D373's record is amended in writing.

**L4 — the replacement, written before the answer is known.** If L1 or L2 fires, gate 1d becomes:

> **1d′** — a candidate's correlation to an existing arm must be **at or below the p95 of the
> same-universe pair distribution**, computed on that study's own null draws, with the pair count and
> mask-intersection size reported. **Threshold from the study's own null, never fixed in advance of
> the universe** — the principle H4′ established.

**This study cannot be passed or failed by a strategy.** Its outcomes are verdicts on a gate, and on
one already-published hurdle.

---

## 5. Assertions

| tag | what it proves |
|---|---|
| **`[MIR]`** | the inherited cell reproduces D373's committed 3,932 / +160.55 / +51.55 **before anything else runs** |
| **`[SER]`** | the observed series reproduces D373's H7 at **ρ = 0.9346373668783634** to 1e-12 — the study is correlating the object gate 1d is defined on |
| **`[PAIR]`** | the pairwise routine returns exactly **+1** for a series against itself, **−1** against its own negation, and **≈0** for independent gaussians |
| **`[MASK]`** | every pair is correlated on its mask intersection, the size is carried per pair, and the runner **refuses** if any pair falls below 500 common bars |
| **`[DIR]`** | correlation is judged on the **HIGH** tail: assert a duplicated book scores **above** p95 and an independent one **below** it |
| **`[DEG]`** | a draw whose series is constant or has zero variance yields an undefined correlation; those are **excluded and counted**, never absorbed, and the runner refuses above 20% (as D374's `[DEG]`) |
| **`[X]`** | **the one that matters** — every audit above must **RAISE** on a deliberately broken input |

**Persist before rendering.** The artifact is written before anything is printed.

---

## 6. The search cost

**None.** The cell is inherited, one statistic is computed, three arms are reported, and the decision
rules above were written before any of them ran. No best-of-N floor applies. Under
[R13](../RULES.md#r13) this adds no looks to any strategy's ledger — it adjudicates a gate.

---

## 7. Predictions

Written in the runner's own quantities. **D374's predictions were right on direction and wrong on
every magnitude**, so the point estimates below are recorded to be scored, not defended.

| | prediction |
|---|---|
| **Q1** | **A′'s median pair correlation is 0.10–0.35.** Two books with identical names but independent timing, both hedged, retain a modest shared factor exposure |
| **Q2** | **B_c's median exceeds A′'s**, on §3's overlap arithmetic — two draws from a ~100-name daily cohort holding ~50 each should overlap about half their names. Point estimate for B_c: **0.45–0.75** |
| **Q3** | **B has the lowest median of the three** — the loosest pool gives the least overlap |
| **Q4** | **gate 1d is SOUND under L1**: B's p95 is below 0.50 |
| **Q5** | **D373's H7 SURVIVES under L3**: 0.9346 is above B_c's p95. I expect the cohort baseline to be high but not that high |
| **Q6** | every pair's mask intersection is **≥ 99%** of 3,185 bars — exposure is 99.97% and the masks should be nearly identical |
| **Q7** | **AGAINST myself:** the observed book's median correlation to A′ draws is **within 0.05 of A′'s own pair median**. If the candidate is systematically more correlated to random books than random books are to each other, something about it is not a signal, and I would rather that surface here than be argued away later |

---

## 8. What would make me abandon this

- **`[SER]` fails** → the series is not the one H7 measured; stop, fix, publish nothing.
- **Degenerate draws exceed 20% of any arm**, or any pair falls below 500 common bars → report that
  instead of percentiles. It would still answer L1, in a stronger form.
- **The three arms give an incoherent ordering** (e.g. B above A′ above B_c with overlapping
  intervals) → report the incoherence and what a decisive version would need, rather than picking the
  arm that suits a conclusion.

---

*Pre-registered 2026-09-07. Runner does not exist at the time of this commit (R8).*
