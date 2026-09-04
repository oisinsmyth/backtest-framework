# D328 — the rank profile at the depth the book actually trades

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Fixing D327's own defect, which D327 declared

D327 bucketed by **20 equal rank percentiles**. Bucket 0 is the top **5%** of
~988 live names — about **49 names**. **The book holds 2.**

That is why its Q5 failed at ρ = −0.200: `skew_63` showed the *flattest* profile
in the study (+3 bp spread) while D326 gave it the *best* per-trade net (+56.22)
at 4.53× cost coverage. **The buckets averaged away exactly the region the book
trades**, and D327's own §4 said so.

**Two further defects this fixes:**

1. **Percentile buckets are the wrong unit.** The book selects by **rank** — top
   2 — not by percentile, and the live cross-section varies bar to bar. A fixed
   percentile is a moving number of names.
2. **No per-bucket `t`.** D327 reported edges with no standard error, so nothing
   there says whether rank-0's edge is distinguishable from zero or from rank 1.

## 1. The buckets, declared

**Log-spaced by RANK from each end, with one coarse middle.** Ranks are
0-indexed from the long end and mirrored from the short end:

```
[0]  [1]  [2-3]  [4-7]  [8-15]  [16-31]  [32-63]  [64-127]  [128-255]  [256-...]
                                middle
[...-256]  [255-128]  [127-64]  [63-32]  [31-16]  [15-8]  [7-4]  [3-2]  [1]  [0]
```

**21 buckets. Rank 0 and rank 1 get their own**, because that is what a two-name
book holds. Powers of two, chosen for being the obvious log spacing and not tuned.

## 2. What is reported per bucket

| | |
|---|---|
| **edge** | mean forward k-bar return, cross-sectionally demeaned each bar |
| **t** | on that mean — **new, and D327 had none** |
| **half-spread** | median Corwin–Schultz, bp |
| **price** | median as-traded close, connecting to D322's price finding |
| **ratio** | edge / (2 × half-spread) — one name crossing twice |

## 3. Signals and horizons

`hist_L`, `retrace_leg`, `skew_63`, `rsi`, `macd_hist`, and `price_log` as the
known-bad control. `k` ∈ {10, 20, 40}. **All unchanged from D327**, so the two
studies differ in resolution and nothing else.

## 4. Predictions

Two are against, and Q6 is load-bearing **because it tests my own diagnosis**.

| | prediction |
|---|---|
| **Q1** | **aggregating the new buckets back to D327's 20 equal percentiles reproduces D327's profile to floating point.** A harness check: if the two disagree, one of the two studies is wrong and this one is not automatically the right one |
| **Q2** | **ranks 0–1 show materially more edge than D327's top-5% bucket** for every signal — the coarse bucket understates the traded region |
| **Q3** | **`skew_63`'s edge at ranks 0–1 is far above its flat 5% profile**, and that is what D326's +56.22 per trade and 4.53× coverage were measuring |
| **Q4** | **rank 0 is NOT distinguishable from rank 1** for most signals — \|t\| on the difference below 2. *Against the idea that the very top name is special* |
| **Q5** | `hist_L`'s short-end anomaly survives at full resolution — its rank-0-from-the-short-end edge is **positive**, so the book's short leg is shorting names that rise |
| **Q6** | **rank-0/1 edge ranks the six signals as D326's per-trade lens does, ρ > +0.7.** *Load-bearing.* D327's Q5 failed at −0.200 and I attributed it to resolution. **If it still fails here, that explanation was wrong** and something other than depth separates the two lenses |
| **Q7** | **the half-spread at rank 0 is HIGHER than the cross-sectional median** for every signal — the best-ranked names are the expensive ones. *Against, and it is D322's finding restated at the traded depth* |

## 5. Stop conditions

- **Q6 confirms** → the lenses agree once resolution is fixed, D327's Q5 failure
  is explained, and **these profiles are sound enough to build a predictor on**,
  which is D329.
- **Q6 fails** → my resolution explanation was wrong. **D329 does not run**, and
  the question becomes what else separates a depth-free profile from a per-trade
  book measurement.
- **Q1 fails** → one of D327 or this is misimplemented; nothing else is read.
- **Q3 fails** → `skew_63`'s cost coverage is not a depth effect either, and the
  question is genuinely open.

## 6. Assertions

1. **[1] Aggregation.** Summing the new buckets into D327's 20 equal percentile
   bins reproduces `data/d327_rank_profile.json` to floating point.
2. **[2] The buckets partition.** Every live name lands in exactly one bucket
   each bar; bucket [0] holds exactly one name per side per bar.
3. **[3] DEMEANING IS EXACT** to floating point at every bar, as D327's `[4]`.
4. **[4] CAUSALITY.** The ranking is lagged and a peeking variant must give a
   different profile.
5. **[5] The `t` is real** — recomputed from the per-bar series, not from the
   pooled variance, and it must **fall** when the sample is halved.
6. **[C] Cost dimensions** — the ratio is edge / (2 × half-spread) and the
   paired 4× form is rejected.
7. **[6] The self-test raises** on a bucket handed free money.

## 7. Scope

**Out:** composites — D329 builds those from these profiles; any signal outside
the six; the book, the cap, holding, exits and turnover, none of which exist in
this lens; and the holdout.

**This lens has no path and cannot price anything.** It must never be quoted in
bp/bar or set beside a book, per FINDINGS §10.

## 8. Files

`docs/decisions/D328-the-profile-at-the-depth-the-book-trades.md` (this record) ·
runner and data to follow. Prior evidence: `data/d327_rank_profile.json`,
`data/d326_both_lenses.json`.
