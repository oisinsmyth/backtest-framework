# D293 — the confluence book as a candidate in its own right

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Stage 1 spends nothing scarce. Nothing is promoted and the holdout is not
read.**

---

## READ THIS FIRST: BY R14's OWN COST CLAUSE THIS CANDIDATE IS ALREADY CLOSED

R14: *"Stage 2 supplies margin, never rescue. **A signal failing cost by a
factor of two at stage 1 is closed at stage 1.**"*

`hist_L`'s measured round trip on the names it actually holds is **266.08 bp**
(Corwin–Schultz, 63.80 long + 69.24 short, per side). Its spread effect at its
own peak cell is **+52.52 bp**.

| | effect | round trip | **× cost** | fails by |
|---|--:|--:|--:|--:|
| `hist_L` alone | +52.52 | 266.08 | **0.197×** | **5.1×** |
| the confluence book | +61.91 | ~266 | **~0.23×** | **4.3×** |

**Both fail cost by four to five times, not two.** Under R14 as written, `hist_L`
was closable on cost at D290 and the confluence is closable now. D290 did not
apply that clause — it recorded cost as "reported, never used to rank, D289's
amendment defers magnitude to stage 2" — and **that is a live contradiction
between R14's cost clause and D290's stated practice. It is not resolved here
and it is not mine to resolve.**

### So this study is a MECHANISM test, not a VIABILITY test

**What it can establish:** whether combining two partners over a primary
produces a real effect — the question three studies have now circled without
answering cleanly.

**What it cannot establish:** that anything here is tradeable. A 4.3× cost gap is
not closable by stage 2, whose measured uplift in this programme is **~1.0×**.

**If the aim is the book, stop now and close it on cost.** If the aim is to know
whether confluence works at all — because that answer governs every future
stage 1 — run it. **The principal chooses which.** The rest of this document
assumes the second.

---

## What is being tested

One candidate, through the **complete stage-1 ladder that all 51 D290 candidates
faced and that this book has never faced**, by the identical procedure, so its
numbers sit directly beside theirs.

**This is not a new search.** It is one candidate on a fixed grid.

### The candidate, fixed exactly

```
at each bar t, ranking on scores at t-1:
   1. take hist_L's N lowest (long leg) and N highest (short leg)
   2. compute each name's within-bar percentile rank in macd_hist and in rsi
   3. keep the round(0.75 x N) names with the lowest mean of those two
      percentiles on the long leg, the highest on the short leg
```

`f = 0.75` and the partner pair are **inherited from D292 and not re-searched**.
Everything else follows D290's procedure for every one of its 51:

| | |
|---|---|
| N grid | **{3, 5, 10, 25, 50}** — D290's, unchanged, for comparability |
| horizons | D290's **12** |
| constructions | long, short, **spread** — all three, scored separately |

## The three nulls, run on the BOOK

This book has faced exactly one null — a rotation of a *partner*. It has never
faced a null on itself. D290's three, adapted with the adaptation stated:

| null | on this candidate |
|---|---|
| **rotation** | roll **all three** inputs within each name's own live bars, **independent offsets**. Coverage, turnover and autocorrelation of each survive; all alignment dies |
| **permutation** | permute the **name labels** within each bar and apply that one permutation to **all three** scores. This preserves the cross-signal correlation structure EXACTLY and destroys only which name holds which triple — independent permutation would also destroy the very thing the study is about |
| **tail-randomised** | pool the 2N most extreme by the composite selection, assign sides at random |

All three take the **grid maximum**, matched to the observed grid maximum,
exactly as D290 did.

## Pass conditions

1. **min z > 0** across all three nulls
2. **name-split CV t > 0** (gate 1f)
3. **open-entry t ≥ 2.0 and retention ≥ 50%** (gate 1e)
4. **and it must beat `hist_L` alone on the SAME ladder** — the same grid, the
   same nulls, run head to head. A confluence that ties its own primary has
   bought nothing with the extra machinery

## Reported, never gating

Gate **1g** (turnover per bar, mean holding run, dead-name share per leg) ·
gate **1i** (peak location, **plus the fine N sweep** — `hist_L`'s own edge is a
spike at N ∈ [23, 30] and the D290 grid contains it and neither neighbour) ·
measured cost · era split · overnight/intraday split · liquidity-tercile
scaling · correlation to S1 and S2 **if their daily series exist in `data/`,
otherwise recorded as not computable and why** (both are ETF strategies on a
different fixture; the overlap would be by date only).

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | the confluence clears conditions 1–3 | **FOR** | moderate |
| **Q2** | **it does NOT clear condition 4** — the head-to-head margin shrinks once `hist_L` also gets the grid max, because much of D292's margin came from comparing a searched book to a fixed one | **AGAINST** | moderate |
| **Q3** | **rotation is the binding null, not tail.** `hist_L`'s own min z is rotation at +1.12 against tail +2.73 — the opposite of D290's usual pattern, and the confluence inherits its autocorrelation | for | moderate |
| **Q4** | the composite's peak N is **not 25**. The fine sweep put its maximum at 26 and its profile broad, so the D290 grid should land it at 25 or 50 by accident of spacing | for | low-moderate |
| **Q5** | **cost still fails by more than 4×** | **AGAINST** | **high** |

**Q2 is the load-bearing one.** D292 compared a book chosen at f = 0.75 against
`hist_L` at a fixed cell. Here both search the same grid under the same
grid-max null. **If the margin survives that, it is the first symmetric
comparison the confluence has won.**

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: **5 N × 12 k × 3 constructions = 180 cells for ONE candidate**,
identical to what each of D290's 51 consumed, and priced by the same grid-max
null. Plus the same again for the `hist_L` head-to-head. Everything upstream —
`hist_L` from 51, the pair from 80, `f` from 4 — was selected in-sample and is
inherited.

## Stop

**If it fails any of conditions 1–3, confluence is closed for this programme**,
not merely for this pool: this is the strongest cell four studies produced, run
through the standard ladder, and a failure there is not a parametrisation
problem.

**If it passes 1–3 but fails 4**, the effect is real and adds nothing over its
own primary — which closes the *operator* while leaving `hist_L` where it was.

**If it passes all four**, that establishes the mechanism and **still does not
make it tradeable**, for the reason at the top of this document. The next step
would then be a cost question, not a statistics question.

## Not attempted here

Any re-search of `f`, the partner pair, or the primary. Fourth order. The
holdout. Stage 2 exits.
