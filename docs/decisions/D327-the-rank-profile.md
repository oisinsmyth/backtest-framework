# D327 — the rank profile: what each signal is worth at every depth, not just the top 2

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. Why, and what is still wrong with D326's "signal" lens

D326 established that the path-variant book is **signal quality × cap timing**,
and that the timing term is as large as the whole spread between signals — drag
runs from **−70 to +50 bp/trade** against a total signal spread of about 80.

**But its path-invariant lens is still `rank < 2`.** It removes slot contention
and nothing else. It is a *depth-2* signal statement, not a depth-free one, and
every ranking this programme has produced — D290's screen, D293's choice, D323's
leaderboard — has been read at one depth or another.

**No signal here has ever been scored across its own rank spread.** D301 measured
edge per position from top-2 to top-19 for one construction and that is the whole
of it.

## 1. What this measures

For each signal, at each bar, rank **the entire live cross-section** (~988 names)
and bucket by rank percentile. Then per bucket:

```
EDGE     mean forward k-bar return, cross-sectionally demeaned each bar
         (demeaned because the book is a SPREAD -- a name's contribution is
          its return against the cross-section, not its raw return)
COST     median Corwin-Schultz half-spread of the names in that bucket
RATIO    edge / (2 x half-spread), the per-trade cost coverage at that depth
```

**Three profiles per signal, and the third is the one that decides anything.**

## 2. The question it settles first

**Why does `skew_63` cover its round trip 4.53× when everything else sits near
2.0?** D326 found that on the per-trade lens and it is a signal property, not a
timing artefact.

Two candidate mechanisms, and the cost profile separates them:

- **Its edge is bigger at the extremes.** Then the EDGE profile is steeper than
  everyone else's and the COST profile is ordinary.
- **Its extreme names are CHEAPER.** Then the EDGE profile is ordinary and the
  COST profile is what differs — and given D322 found 57% of the book's P&L in
  the cheapest price tercile at 8× the commission, a signal whose extremes are
  *cheap* would be the first thing in this programme to escape that.

## 3. Scope

- **Signals:** `hist_L`, `retrace_leg`, `skew_63`, `rsi`, `macd_hist`, plus
  **`price_log` as a known-bad control** — D291 called it a static tilt and D293
  called its solvency a turnover artefact, so it should look distinctive here or
  the lens is not measuring what it claims.
- **`k` ∈ {10, 20, 40}**, matching D326.
- **20 buckets** of 5 rank-percentile each, declared, not tuned.
- **No simulation, no book, no cap, no exits, no holding path.** Forward returns
  against a lagged ranking, and nothing else.

## 4. Predictions

Three are against, and Q2 is load-bearing.

| | prediction |
|---|---|
| **Q1** | the incumbent's profile is **signed correctly** — the lowest-rank bucket's demeaned forward return is positive and the highest-rank bucket's negative, matching the book's own long/short convention. **A harness check; if it fails the sign convention is wrong and nothing else is read** |
| **Q2** | **no signal has a monotone rank profile.** The edge sits in the extreme buckets and is flat through the middle. *Against — load-bearing.* A monotone profile would mean a broad cross-sectional factor; a flat middle with live tails means a tail effect, which is what a 2-name book implies |
| **Q3** | **`skew_63`'s advantage is in the COST profile, not the EDGE profile** — its extreme buckets hold materially cheaper names than the other signals' extreme buckets |
| **Q4** | the **ratio** profile peaks at the extremes for every signal, which is the depth-free reason a concentrated book beats a wide one |
| **Q5** | **the extreme-bucket edge ranks the signals the same way D326's per-trade lens does** — Spearman above +0.7. *Two independent signal lenses that disagree would mean one of them is broken* |
| **Q6** | **`price_log` is distinctive** — a near-flat edge profile with a steeply rising cost profile, consistent with a static price tilt. *If it looks like the others, this lens is not measuring what it claims* |
| **Q7** | **the profile is flatter at k = 40 than k = 10 for every signal.** *Against the idea that longer holds are free* — if edge decays with horizon, the cost saving from a longer hold is bought with signal |

## 5. Stop conditions

- **Q2 confirms and Q4 confirms** → the edge is a tail effect and concentration
  is the correct response to it. **That closes the width question on a depth-free
  measurement** rather than on the six book-level studies that argued about it.
- **Q2 fails** → some signal has a monotone profile, meaning there is broad
  cross-sectional edge this programme has been throwing away by holding 2 names.
  **That would be the largest finding available here** and needs its own study.
- **Q3 fails** → `skew_63`'s cost coverage is an edge effect, not a cheapness
  effect, and the question moves to why its extremes are stronger.
- **Q1 or Q6 fails** → the lens is misimplemented; nothing else is read.

## 6. Assertions

1. **[1] The ranking is the same one.** The rank arrays are built by
   `R.ranked(z[s], base)` — the identical call D323 and D325 use — and the
   bucket-0 membership must match `plan.lo`'s top rows exactly.
2. **[2] CAUSALITY.** The ranking is lagged by `R.ranked` and the forward window
   starts at `t+1`; a variant that starts the window at `t` **must give a
   different profile**.
3. **[3] The buckets partition.** Every live name lands in exactly one bucket
   each bar, and the bucket counts are equal to within one name.
4. **[4] DEMEANING IS EXACT.** The cross-sectional mean of the demeaned forward
   return is zero to floating point at every bar, so the profile sums to zero
   across buckets and cannot show a spurious level.
5. **[5] The extreme buckets reproduce a known number** — bucket 0 and bucket 19
   of the incumbent at k=10 must bracket D301's published edge-per-position
   figures in sign and rough magnitude.
6. **[C] Cost dimensions** — the per-trade cost is **2 ×** the half-spread, one
   name crossing twice, and the check fails against the paired 4× form.
7. **[6] The self-test raises** on a profile handed free money in one bucket.

## 7. What this cannot do

**It has no path, so it cannot price anything.** A rank profile says what the
signal is worth at each depth *before* holding, contention, exits or turnover.
**It must never be quoted in bp/bar or compared to a book**, per FINDINGS §10 —
and D326's `rank_cells` guard is the model for enforcing that.

**Nothing here can be promoted.** It is a measurement of the signals the
programme already holds, at depths it has never looked at.

## 8. Files

`docs/decisions/D327-the-rank-profile.md` (this record) · runner and data to
follow, in separate commits. Prior evidence: `data/d326_both_lenses.json`,
`data/d323_shortlist.json`, `data/d322_four_group_report.json`.
