# D241 — The combined book, and first-come-first-served capital

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## The question

[D240](D240-the-uptrend-onset-arm.md) cleared every hurdle it registered and reported that
pairing S1 with A2 would reach a combined Sharpe of **1.032**, cutting time-to-significance from
8.8 years to 5.5. **That number is closed-form arithmetic on `SR_a`, `SR_b` and ρ — not a book.**

**This study builds the book.** And it parameterises capital, because two arms sharing one pool
is a decision that has never been made explicitly in this programme.

---

## The measurement that reframes the design

Demand for capital at the existing 1/57-per-name sizing, on the mined 57:

| | mean | max |
|---|---:|---:|
| S1 alone | 18.88% | 89.47% |
| A2 alone | 13.00% | 43.86% |
| **combined** | **31.88%** | **94.74%** |

| cap | binds on | mean excess demand |
|---:|---:|---:|
| **100%** | **0.00% of days** | 0.00% |
| 75% | 7.00% | 0.69% |
| 50% | 19.47% | 3.67% |
| 25% | 53.33% | 12.29% |

**At 100% capital the allocator never binds.** First-come-first-served is a *rationing* rule and
there is nothing to ration until total capital is capped below ~95%. So the allocation
parameters are inert in the baseline cell and only become live under a cap — which is stated
here so the baseline is not mistaken for a test of the allocator.

**The two arms rarely want the same instrument**: only **1,000 cells**, 3.63% of combined
demand. Contention is for the *pool*, not for particular names.

---

## The construction

```
TOTAL        total capital the book may deploy
RESERVE_S1   capital reserved for S1, unusable by A2
RESERVE_A2   capital reserved for A2, unusable by S1
SHARED     = TOTAL - RESERVE_S1 - RESERVE_A2
```

Each position is **1/57 of total capital**, unchanged from every book published so far, so the
arms' standalone numbers remain directly comparable.

At each bar, in order:

1. **Release.** Positions whose arm has exited free their capital.
2. **Incumbents hold.** A position already open keeps its claim and is never evicted.
3. **New demand** is met from that arm's `RESERVE` first, then from `SHARED`.
4. **If `SHARED` cannot meet both arms' unmet demand, it is split pro-rata to that demand.**
5. **Rationing denies entries; it does not shrink positions.**

### Three design decisions, named because they are choices

**FCFS on daily bars means incumbency, not intra-bar ordering.** Both arms' signals arrive at
the same close, so there is no natural "first" within a bar. The real content of
first-come-first-served is that **an incumbent keeps its capital against a newcomer**, and that
is what step 2 implements. Step 4's pro-rata split is the neutral resolution of the intra-bar
tie, chosen over an arbitrary arm priority.

**Denial, not scaling.** D236 rationed by scaling every position proportionally and found that
**all six controls cut better-than-average bars** — every cell landed below its overlay null.
FCFS denies *entries* instead, which is a different mechanism and is not covered by that result.

**When an arm's new demand exceeds its available capital, entries are admitted in ascending
symbol index.** This is arbitrary but deterministic. **The reversed order is reported as a
diagnostic**, so the arbitrariness is measured rather than hidden.

---

## Cells — five

| | TOTAL | RESERVE S1 / A2 | SHARED | what it isolates |
|---|---:|---:|---:|---|
| **C0** | 100% | 0 / 0 | 100% | **the unconstrained combined book** — the direct answer to "build the combined book". The allocator is inert here by construction |
| **C1** | 50% | 0 / 0 | 50% | pure FCFS on a pool that binds 19.5% of days |
| **C2** | 50% | 25% / 25% | 0% | **fixed allocation, no sharing** — the contrast that isolates *sharing* from *capping* |
| **C3** | 50% | 15% / 15% | 20% | the hybrid the proposal describes |
| **C4** | 75% | 0 / 0 | 75% | pure FCFS at a cap that binds 7.0% of days |

**C1 against C2 is the only clean test of FCFS itself** — same total capital, same arms, the
only difference being whether capital is shared or partitioned.

---

## Hurdles

- **M1 — carries the verdict, and it is the thing D240 could not do.** **C0 beats S1 alone on
  excess Sharpe, with a paired block bootstrap `p05 > 0`** (block 21, both books recomputed on
  identical resampled dates). D230 is why the bootstrap leg is mandatory and not optional: eight
  deltas once cleared as scored and **zero** cleared as claimed.
- **M2.** C0 beats **A2 alone** on the same terms. An arm pairing that only beats the weaker of
  its two components has not earned its complexity.
- **M3 — the allocator's own test.** **C1 beats C2.** If sharing a pool first-come-first-served
  does no better than partitioning it fixed, the allocator carries nothing and the simpler rule
  wins.
- **M4.** No capped cell (C1–C4) beats C0. **Registered as a prediction of failure**, because
  D236 found every exposure control on S1 cut above-average bars. If a capped cell *does* beat
  C0, that contradicts D236 and needs its own explanation rather than a victory lap.
- **R6 binds:** every leg is computed in code or the runner fails loudly.

**Reported, not hurdles:** realised exposure per arm, how often each cap binds, the fraction of
entries denied per arm, deployable return, Calmar, max drawdown, and the **reversed-symbol-order
diagnostic**.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **N1** | **C0 beats S1 alone on the point estimate**, landing near the closed-form 1.032 | **high** — the arithmetic is sound and the arms are measured |
| **N2** | **C0's bootstrap `p05` is still below zero**, so M1 fails as claimed even though it passes as scored | **moderate** — S1's own p05 is −0.009 and A2's is +0.207; the combination should improve but six years is six years |
| **N3** | **No capped cell beats C0** — D236's finding should carry | **moderate-high** |
| **N4** | **C1 ≈ C2**, so M3 fails. Contention binds on 19.5% of days but the two arms want the same *name* only 3.63% of the time, so sharing has little to arbitrage | **moderate** |
| **N5** | **The reversed-order diagnostic moves the result by less than 0.05 Sharpe** at every cell | **moderate-high** |

**N2 is the one to watch.** M1 passing on the point estimate and failing on the interval would be
the fourth time in this programme that a result cleared as scored and failed as claimed — and it
is the honest expected outcome, not a pessimistic one.

---

## Stage 1 only

**The mined 57.** The holdout 60 and the 2025–2026 forward window are **not touched.** Under R8
nothing here reaches `BOOK.md` without its own pre-registered out-of-sample test.

**And the caution D240 already carries applies with more force here:** A2's design was fitted on
this fixture, so a combined book containing it inherits that. **This measures whether the
pairing works arithmetically, not whether it works.**

---

## Ledger

| count | N |
|---|---:|
| fresh — 5 cells | 5 |
| + D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 36 |
| + the gradient anatomy disclosed at D240 | 57 |
| + disclosed ETF prior | **45,860** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the A2 book, signals, walk, ATR, rolling fit | `signals`, `walk` | `run_uptrend_onset.py` |
| S1's book | `base_masks`, `hold_book` | `run_stops_targets.py` |
| signed scorer, financing, rotation null | `score`, `signed_log_returns`, `excess_of` | `run_short_mirror.py` |
| the paired block bootstrap, block 21 | `paired_block_bootstrap` | `run_jerk_rung.py` |

**Written fresh:** the capital allocator. It is a forward walk over bars with per-position
claims, which nothing in the repo does — D236's control scales a position matrix that already
exists, and cannot express "this entry was denied because the pool was full."

## Verification

- Full suite green, offline, deterministic; `--report-only` re-renders **byte-for-byte**.
- **C0 must reproduce the union of the two books exactly**, since the allocator is inert at
  TOTAL = 100%. Asserted against `max(s1, a2)` cell by cell — if it does not, the allocator is
  rationing when it should not be.
- **S1 and A2 must reproduce +0.746 and +0.822** in this runner, or the comparison is void.
- **Capital is never over-committed:** assert total deployed ≤ TOTAL at every bar, in every cell.
- **Incumbency is asserted directly:** a position open at bar `t` is still open at `t+1` unless
  its own arm exited, regardless of how much new demand arrived.
- **No look-ahead:** the allocator reads only bars ≤ `t`; perturbing a close from bar `t` onward
  moves no allocation at any index ≤ `t`.

---

## Two amendments, both forced by assertions during the build

### Amendment 1 — a name is held once and charged once

The registration never said what happens when **both arms want the same name** — 1,000 cells,
3.63% of demand. The first draft summed the two granted books and **double-funded them**; the
`book.max() <= 1.0` assertion caught it on the first run.

**The allocator now works on names, not on (arm, name) pairs.** An owning arm is tracked for
reserve accounting and reporting only. A position whose owner exits but which the other arm
still wants **continues, with ownership transferring and no capital event** — which is the
correct reading of a shared pool: you cannot buy the same ETF twice with the same money.

### Amendment 2 — `TOTAL` is a hard constraint and needs enforcing separately

Ownership transfer moves a position between arms *without* a capital event, so an arm can come
to hold more than its reserve. After that the per-arm room checks no longer bound the sum, and
C2 over-committed. **`RESERVE` is a funding constraint on an arm; `TOTAL` is a hard cap on the
book**, applied globally after the per-arm budgets are computed.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.** The holdout 60 and the 2025–2026 forward
window are untouched.*

**Produced:** 2026-08-28 · `uv run python scripts/run_combined_book.py` · Page:
[`COMBINED_BOOK_RESULTS.md`](../results/COMBINED_BOOK_RESULTS.md)

### The one-sentence version

**The combined book is the first thing this programme has produced that beats buy-and-hold on
money *and* on drawdown — 10.68% against 8.42%, at −10.41% against −34.60% — and its advantage
over S1 alone still fails its bootstrap by a hair.**

### The books

| | total | reserve | exposure | excess Sharpe | CAGR | **deployable** | max DD | Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **C0** | 100% | — | 30.7% | **+0.924** | 7.71% | **10.68%** | −10.41% | 0.741 |
| **C1** | 50% | — | 27.6% | +0.910 | 5.80% | 8.85% | −7.64% | 0.759 |
| **C2** | 50% | 25/25 | 23.6% | +0.804 | 4.00% | 7.17% | −6.65% | 0.602 |
| **C3** | 50% | 15/15 | 26.0% | +0.868 | 4.89% | 7.98% | −7.09% | 0.690 |
| **C4** | 75% | — | 30.2% | **+0.959** | 7.57% | 10.55% | −9.97% | 0.759 |
| *S1 alone* | | | *18.9%* | *+0.746* | *5.43%* | *8.83%* | *−10.30%* | *0.527* |
| *A2 alone* | | | *13.0%* | *+0.822* | *2.52%* | *6.08%* | *−1.93%* | *1.306* |
| *B&H* | | | *100%* | *+0.235* | *8.42%* | *8.42%* | *−34.60%* | *0.243* |

### The closed form promised more than the book delivers

**D240 predicted 1.032. The book built scores 0.924.** The gap is **weighting**: the closed form
assumes *optimal* weights, while the union book holds each arm at its natural exposure — 18.9%
against 13.0%. Closing it requires a sizing decision, which R8 keeps as a separate record.

**Quoting 1.032 as what the pairing achieves would have been wrong**, and it is exactly why this
study exists.

### M1 and M2 — both fail, and M1 by a whisker

| | delta | p05 | p95 | excludes 0 |
|---|---:|---:|---:|:--:|
| **M1 — C0 vs S1 alone** | **+0.178** | **−0.010** | +0.394 | ✗ |
| **M2 — C0 vs A2 alone** | +0.102 | −0.513 | +0.661 | ✗ |

**p05 = −0.010.** The combination beats S1 on the point estimate and the interval contains zero
by one part in a hundred. **This is the fourth time in this programme that a result has cleared
as scored and failed as claimed** — and N2 predicted it in advance.

### M3 clears — sharing beats partitioning

| | excess Sharpe |
|---|---:|
| C1 — shared, FCFS | +0.910 |
| C2 — fixed 25/25 | +0.804 |
| **difference** | **+0.107** |

Same 50% of capital, same two arms; the only difference is whether it is pooled or split.
**First-come-first-served is worth +0.107 of Sharpe**, and the direction survives the
reversed-symbol-order diagnostic (+0.066) even though the magnitude does not.

The mechanism is visible in the denial rates: at C2 both arms are starved (**85.1% and 86.8%**
of entries denied) because neither can borrow the other's idle reserve. At C1 the same capital
denies **72.4% and 41.9%** — A2, the smaller-demand arm, gets served far better.

### M4 fails — and it contradicts D236

**C4, capped at 75%, scores +0.959 against the uncapped C0's +0.924.** A capped cell beat the
unconstrained book, which D236 said should not happen — there, all six exposure controls cut
better-than-average bars.

**The likely reconciliation is the mechanism, not the direction:** D236 rationed by *scaling
every position proportionally*; this rations by *denying entries*. D241 registered that
distinction in advance. But the margin is **0.035** and the reversed-order diagnostic moves C4
to +0.945, so this is a lead, not a finding.

### The order-dependence is worse than I predicted

Entries are admitted in ascending symbol index — arbitrary but deterministic. Reversing it:

| | forward | reversed | move |
|---|---:|---:|---:|
| C0 | +0.924 | +0.924 | 0.000 |
| C1 | +0.910 | +0.952 | **+0.042** |
| C2 | +0.804 | +0.885 | **+0.081** |
| C3 | +0.868 | +0.931 | **+0.063** |
| C4 | +0.959 | +0.945 | −0.014 |

**At the heavily-binding cells an arbitrary tie-break moves the answer by up to 0.081** — larger
than M3's entire effect under one ordering. C0 is unmoved because it never rations. **Any
conclusion drawn from a capped cell has to survive both orderings**, and only M3's direction
does.

### Scoring — one confirmed, one partial, three falsified

| | prediction | outcome |
|---|---|---|
| **N1** | C0 beats S1 and lands near 1.032 | **PARTIAL.** Beats S1 by +0.178, but lands at 0.924 — the closed form assumed optimal weights |
| **N2** | C0's `p05` is still below zero; M1 fails as claimed | **CONFIRMED**, −0.010 |
| **N3** | no capped cell beats C0 | **FALSIFIED.** C4 does, +0.959 |
| **N4** | C1 ≈ C2, M3 fails | **FALSIFIED.** +0.107, and M3 clears |
| **N5** | reversed order moves under 0.05 everywhere | **FALSIFIED.** C2 moves 0.081 |

### What survives

**Nothing is promoted.** C0 is the strongest book this programme has produced and it has **no
out-of-sample evidence at all** — and it contains A2, whose design was fitted on this fixture.

**Three things are kept.**

1. **The combined book exists and is measurable**, which is what D240 could not do. Its
   advantage over S1 is +0.178 with p05 −0.010 — the honest statement is *"probably real, not
   demonstrated."*
2. **Sharing beats partitioning**, direction-robust across orderings. If two arms ever run
   together, pool the capital.
3. **The allocator**, with both amendments — a name is held once, and `TOTAL` binds globally.

**The next step is unchanged and this study sharpens it:** C0 at p05 −0.010 needs *more data*,
not more analysis. Extending the fixture back to ~2005 remains the only action that can move it.

### Ledger

| count | N |
|---|---:|
| fresh — 5 cells | 5 |
| + D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 36 |
| + the gradient anatomy | 57 |
| + disclosed ETF prior | **45,860** |
