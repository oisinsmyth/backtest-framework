# D222 — Does the fine-bar advantage grow as the matched window gets longer?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user prediction, made before the run: *"the 15 min will beat both by a margin
that slightly (very slightly) grows as we increase the time frame."*

> A result section will be appended and nothing above it edited.

## What is being tested

D221 established that this indicator is **scale-free in bars** — 15m with ×4 parameters
matched 1h with defaults to within 0.15 Sharpe at ρ = 0.95. It also showed a small positive
residual on the two liquid symbols: Δ = +0.054 (BTC) and +0.080 (ETH), where Δ is the
15m-matched arm minus the native arm.

D222 asks whether that residual is **structure or noise**, by testing a shape:

> **Δ(k) is positive at every k, and increases with k.**

`k` is the frequency ratio between the fine bars and the coarse reference: `k = 4` for 1h,
`k = 32` for 8h, `k = 96` for daily. A residual that is noise has no reason to order itself
by `k`; a residual that is structure should, because both candidate mechanisms scale with it.

| ladder rung | k | native reference | 15m matched arm |
|---|---:|---|---|
| 1h | 4 | 1h, `(34, 9)` | 15m, `(136, 36)` |
| 8h | 32 | 8h, `(34, 9)` | 15m, `(1088, 288)` |
| 1d | 96 | 1d, `(34, 9)` | 15m, `(3264, 864)` |

Naive `×k` scaling is used throughout because **D221 falsified the need for the lag
correction** — the derived `(133, 33)` gave no advantage over `(136, 36)`, so the practical
rule is to multiply by the frequency ratio.

## The two mechanisms, named before the run

**1. Estimation precision.** The matched arm computes the same window from `k`× more
samples, so its smoother is a less noisy estimate of the same quantity.

**2. Decision latency.** The coarse arm can only act at a bar close, so it is up to one
coarse bar late on every crossing. The fine arm is at most one 15m bar late.

**Both saturate rather than grow without bound**, and this matters for the prediction.
Latency as a *fraction of the window* is `1/34` for any native rung — scale-invariant — so
the fine arm's relative timing advantage approaches a ceiling of one coarse bar and gains
little from `k = 32` to `k = 96`. Estimation precision improves as `1/√k` at best. So the
honest reading of the mechanisms is **increase then flatten**, which is compatible with
*"very slightly"* growing but predicts the k=32→96 step is smaller than the k=4→32 step.

## The confound this design exists to avoid

Warm-up scales with `k`: 42 days at `k = 4`, 339 at `k = 32`, **1,016 at `k = 96`**. Taken
naively, each rung would run on a shorter and later span than the one below it, and a
growing Δ could simply be the later period behaving differently. The same applies to
symbols: XEM cannot support `k = 96` and BTG cannot support `k = 32`.

**So every rung runs on the same two symbols over the same span** — BTCUSDT and ETHUSDT,
starting from the latest warm-up in the whole ladder (`k = 96`, 1,016 days), giving ~5.6
years common to all six configs. **D221's Δ(4) values are NOT reused**, because they were
measured over 8.3 years and are not comparable to these.

## Test bed

| | |
|---|---|
| Fixture | `crypto_binance_15m_raw` — true as-traded frame (D161) |
| Symbols | BTCUSDT, ETHUSDT — the only two that support `k = 96` |
| Coarse series | built by `breakout_intraday.resample` from the same 15m source, on the **shared calendar** (a partial UTC day is dropped at every frequency) |
| PPY | 35,040 (15m) · 8,760 (1h) · 1,095 (8h) · 365 (1d) — D17/D108 |
| Book | long-flat, acceleration rung — the pre-declared arm |
| Metric | **gross** Sharpe is primary; costs confound a signal comparison and are reported beside it |

## The statistic, and how "slightly grows" is made testable

Δ(k) = `Sharpe(15m matched) − Sharpe(native)`, gross, per symbol.

**A trend claim over three points on two symbols is weak by construction**, so each Δ carries
a **block-bootstrap confidence interval** — 30-day blocks, 400 resamples, both arms
recomputed on each resampled index set so the pairing is preserved. The question is not only
whether the point estimates ascend but whether the ascent is **resolvable**. Reporting the
ordering without the intervals would be reporting noise with a direction.

## Hurdles

**K. The direction.** Δ(k) > 0 for both symbols at all three k.

**L. The shape.** Δ(4) < Δ(32) < Δ(96) on both symbols.

**M. Resolvability.** The Δ(96) − Δ(4) gap exceeds the width of its own bootstrap interval.
**L without M is a pattern in noise**, and this study is required to say so if that is what
it finds.

**No config is promoted.** As in D221, this asks how an estimator behaves, not whether an arm
is tradeable. Costs are reported and every rung is expected to fail them.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **N1** | Hurdle K holds — Δ > 0 at every k on both symbols | **moderate** |
| **N2** | Δ(32) > Δ(4) on both symbols | **moderate** |
| **N3** | **Δ(96) ≈ Δ(32)** — the step flattens, because both mechanisms saturate and latency as a fraction of the window is scale-invariant | **moderate-high** |
| **N4** | Hurdle M **fails**: the trend is not resolvable against its own bootstrap interval with two symbols | **high** |
| **N5** | The matched arm trades **more** round trips per year than the native at high k, because it can flip intraday where a daily arm cannot | **moderate** |

**Where this differs from the proposal:** the prediction under test says the margin grows
across the whole ladder. N3 says it grows then flattens. **If Δ(96) − Δ(32) is clearly
positive and larger than noise, the proposal is right and N3 is wrong** — and that would mean
a mechanism is operating that neither of the two named above accounts for, which is the most
interesting outcome available here.

## Ledger

| block | looks |
|---|---:|
| 3 rungs × 2 configs (native + matched) | **6** |
| **fresh, D222 only** | **6** |
| inherited from D217 + D218 + D220 + D221 | 78 |
| crypto-fixture prior + structure/terrain bar on this fixture | 3,739 |
| **verdict count** | **3,823** |

Zero-look: the block bootstrap (a confidence interval is not a hypothesis), the day census,
and the resample reports.

## Pre-committed stops

- **The shared-span gate.** If the six configs do not score on identical wall-clock spans the
  run halts — a trend measured across different periods is not a trend.
- **The shared-calendar gate.** `ResampleReport.check()` raises rather than warns; 8h and 1d
  buckets must be exact aggregations of complete UTC days.
- **No k is added after the fact.** Three rungs are declared. If the trend is ambiguous the
  answer is that it is ambiguous, not a fourth rung until it resolves.
