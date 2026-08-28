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
