# D376 RESULT — two unrelated books here correlate at 0.48, two cohort books at 0.92, and gate 1d is measuring pool overlap

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md`. The H1 above is the full title.*

**Date:** 2026-09-07
**Pre-registration:** [D376](D376-what-do-two-books-in-this-universe-correlate-at.md), committed `6b6d905` — **before the runner existed** (R8).
**Runner:** [`scripts/run_d376_correlation_floor.py`](../../scripts/run_d376_correlation_floor.py), committed `8d5d50b`.
**Artifacts:** `data/d376_correlation_floor.json`, `data/d376_series.npz` (500 books × 3 arms).
**Fixture:** mining prefix only. **No holdout was read.**

---

## 0. The verdict

**500 draws, 280,625 book pairs.** `[SER]` confirmed the correlated object is gate 1d's own: the
observed series reproduces D373's H7 at **ρ = 0.9346373668784** over 3,185 bars.

| | p05 | **p50** | **p95** | max | se(p95)† |
|---|---:|---:|---:|---:|---:|
| **A′** identical name set, independent timing — 124,750 pairs | +0.409 | **+0.448** | +0.485 | +0.568 | 0.0011 |
| **B** unrelated constructions — 31,125 pairs | +0.424 | **+0.476** | **+0.526** | +0.603 | 0.0028 |
| **B_c** both inside the winner cohort — 124,750 pairs | +0.916 | **+0.923** | +0.930 | +0.938 | 0.0001 |

† **book-clustered.** 280,625 pairs come from 1,250 books, so a pair-level bootstrap would treat one
book's series as ~500 independent observations. `[CLU]` resamples **books**, dropping self-pairs.

| decision | verdict |
|---|---|
| **L1** — is 0.50 reachable by two unrelated books? | **NO as written.** B's p95 is **+0.526**, above the bar. **But see §3 — the honest reading is narrower than "unreachable"** |
| **L2** — can anything inside the cohort pass? | **NO. B_c's p05 is +0.916.** Every pair of books selecting inside this cohort fails gate 1d automatically, whatever their signals |
| **L3** — does D373's H7 survive? | **YES, decisively.** 0.9346 against B_c's p95 of 0.9296 — margin **+0.0051 = +34.7 book-clustered SE** |
| **L4** — replacement | **applies** |

---

## 1. The finding that was not in the pre-registration: it is TIME, not names

**A′ books hold the identical name set and correlate at +0.448. B books hold different names and
correlate MORE, at +0.476.** That inverts Q3 and it is the most useful thing in the study.

The two arms differ in what they hold fixed:

- **A′** rotates each name's trades **to different times**. Two draws hold the same names, rarely on
  the same bar.
- **B** swaps names **within the same day** — the event days are preserved. Two draws are exposed on
  **the same bars**, holding different names.

So **two books trading the same days correlate more than two books trading the same names.** The
residual common factor is a **per-bar effect**, not a name effect: on a given bar, whatever the hedge
fails to remove hits every book that is exposed that day.

**This is a mechanism, and it is testable.** The incumbent hedge subtracts the floored equal-weight
market **1:1** — `sgn · (v − m)` — so it assumes every name has beta exactly 1. If the held names
have β ≠ 1, a large market day leaves a residual proportional to `(β − 1)·m` in **every** book
exposed that day, which is precisely a shared per-bar factor.

**[D377](D377-the-hedge-leaves-a-common-factor.md) was pre-registered before this result was read**
and its H1 candidate — the per-name rolling beta that already exists, lagged, unused in the default
path — targets exactly this. That prediction is now mechanistically motivated rather than merely
plausible, and the pre-registration predates the motivation, which is the right order.

---

## 2. The cohort number, and what it means

**Two books that share nothing but membership of the `mom_252_21` top decile correlate at +0.923,
with a p05 of +0.916.** Different names, different days, different timing.

The arithmetic was pre-registered in §3: the daily top decile is ~100 names and each book holds ~50,
so two independent draws overlap about half their held names by chance. **The consequence is that
within this cohort the signal barely affects the shape of returns.**

This is the **second independent measurement** of the same thing. D373's B_c control showed
**+126.54 bp of the observed +160.55 per trade** was available to a random name from the same cohort
on the same day — the *return* side. This is the *covariance* side. **The cohort is the strategy.**

**Practically: you cannot build a diversified book out of variations on winner-selection.** Any two
such constructions are the same strategy for portfolio purposes, and L2 says gate 1d will reject
every one of them on structure alone.

---

## 3. L1 fired, and its interpretation must be narrower than its label

The runner's L1 verdict reads *"GATE UNREACHABLE"*. **The same artifact contains evidence that this
is too strong, and it should be read with the qualification rather than without it.**

| the observed book vs each arm's draws | p50 | p95 | max |
|---|---:|---:|---:|
| A′ | +0.424 | +0.485 | +0.541 |
| **B** | **−0.091** | −0.049 | −0.010 |
| B_c | +0.914 | +0.921 | +0.926 |

**B books correlate at +0.476 with each other and at −0.091 with the observed book.** So the 0.476 is
not a universal floor — it is what two books drawn from **the same pool** share. The observed book
selects a *different* pool (the momentum top decile) and sits outside it entirely, at slightly
negative correlation.

**So gate 1d is not simply unreachable. It is measuring POOL OVERLAP rather than signal
independence:**

- two books from the **same** pool: ρ ≈ 0.42–0.53, and the 0.50 bar is inside that range → the gate
  fires on structure
- two books from **different** pools: ρ ≈ 0 or negative → the gate passes easily
- two books from the **same narrow cohort**: ρ ≈ 0.92 → the gate always fails

**A gate that returns "independent", "borderline" and "identical" according to which pool a candidate
was drawn from — before any signal is considered — is not measuring what its name claims.** That is
the finding, and it is more useful than "unreachable" because it says what to do about it.

---

## 4. The replacement, and it is a scoping rather than a re-thresholding

Pre-registered as L4 before the answer was known, and **narrowed on §3's evidence**:

> **1d′ (replaces 1d).** A candidate's correlation to an existing arm is compared to the **p95 of the
> pair distribution among books drawn from the CANDIDATE'S OWN POOL**, computed on that study's own
> null draws, with the pair count, the mask-intersection size and a **book-clustered** SE reported.
>
> **The comparison must name the pool.** A raw correlation quoted without it is uninterpretable: the
> same number means "independent" in one pool and "structurally identical" in another.
>
> **Threshold from the study's own null, never fixed in advance of the universe** — the principle H4′
> established, now applied a second time.

For this ledger 1d′ resolves to **≤ 0.526** against books from the same loose pool, **≤ 0.930**
against books from the momentum top decile.

**A caution on that second number.** A 0.930 threshold is not a licence — it means gate 1d cannot
discriminate inside this cohort at all, so **independence must be established some other way there,
or not claimed.** L2 is a statement that the gate is blind in that region, not that a 0.92
correlation is acceptable.

---

## 5. D373's H7 stands, and the margin is decisive

I flagged this margin as razor-thin when the smoke came in. **That was wrong, and the clustered
bootstrap is why I checked rather than asserting either way.**

| | |
|---|---:|
| D373 ↔ D365 | **+0.9346** |
| B_c pair p95 | +0.9296 |
| margin | **+0.0051** |
| book-clustered se(p95) | **0.0001** |
| **margin in SE** | **+34.7** |

The B_c distribution is extraordinarily tight — p05 to p95 spans 0.0134 across 124,750 pairs from 500
books — so a margin of five thousandths is 35 standard errors. **H7's conclusion stands:** D373 was
closer to D365 than two arbitrary cohort books are to each other.

**But §2 changes what that conclusion is worth.** D373 is at +0.9346 against a cohort baseline of
+0.9233. The *excess* over "two arbitrary cohort books" is **+0.011**, not the +0.43 that quoting
0.935 against a 0.50 bar implied. **D373 was not unusually similar to D365. It was about as similar
as any two cohort books are** — which is a worse fact about the construction, not a better one, and
it is the same conclusion §2 reaches from the return side.

---

## 6. Predictions, scored

| | prediction | outcome |
|---|---|---|
| **Q1** | A′ median is 0.10–0.35 | **FALSIFIED** — +0.448 |
| **Q2** | B_c median exceeds A′'s; estimate 0.45–0.75 | **HELD on direction, FALSIFIED on magnitude** — +0.923 |
| **Q3** | B has the lowest median | **FALSIFIED** — B is the *highest* of the two low arms. §1 is the finding this produced |
| **Q4** | gate 1d is sound: B's p95 below 0.50 | **FALSIFIED** — +0.526 |
| **Q5** | H7 survives: 0.9346 above B_c's p95 | **HELD** — by 34.7 SE |
| **Q6** | every pair's mask intersection ≥ 99% of 3,185 bars | **HELD** — minimum 3,185 |
| **Q7** | *against myself:* observed-vs-A′ median within 0.05 of A′'s own pair median | **HELD** — +0.424 vs +0.448 |

**Four falsified, three held.** Every magnitude I predicted was wrong, in the same direction as D374:
I systematically under-estimate how much structure these books share. That is now three studies in a
row — D374's concentration, D376's correlation — where the direction was right and the scale was not.

---

## 7. Two methodological notes worth carrying

**`[CLU]` — cluster on the object you resampled, not the pair.** A pair-level bootstrap would have
reported se(p95) around 0.0001/√250 and made every margin look decisive. The right unit is the book.
This applies to any future pairwise statistic here.

**The window is a nuisance parameter and it moved the answer.** A′ books deploy on ~4,121 bars, B and
B_c books on 3,185. On each pair's own intersection A′'s median is +0.448; on the observed book's
common window it is **+0.487**. The primary is the pre-registered per-pair intersection; the
common-window block was added after the 12-draw smoke, **before the full run, on a nuisance
observation and not on any verdict**, and is labelled secondary in the artifact. B and B_c are
unchanged by it, so §1's inversion survives either reading.

---

## 8. What this did not settle

- **Whether a better hedge removes the per-bar factor.** §1 gives the mechanism; **D377** is
  pre-registered to test it and its runner does not exist yet.
- **Whether the 0.476 same-pool floor is specific to the RSI-bucket pool** B draws from. One pool was
  measured.
- **Anything about gate 1d in the ETF universe**, where S1 and S2 live and where the only two passes
  on record were measured. This studied the single-name universe only.
- **The D373 avenue.** Still open, still the principal's under R15.

---

*Result committed separately from the pre-registration, per R8. Nothing admitted to either book. No
looks added to any strategy's multiplicity ledger — this adjudicates a gate.*
