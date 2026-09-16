# D222 — Does the fine-bar advantage grow as the matched window gets longer?

**Status:** Committed (K, L, M all fail — the residual is noise; N4 confirmed)
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

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-27 · **Reproduce:** `uv run python scripts/run_scaling_ladder.py`
(offline, deterministic) · Page: [`SCALING_RESULTS.md`](../results/SCALING_RESULTS.md) ·
Artifact: `data/scaling_ladder_summary.json`

### The one-sentence version

**The fine-bar residual is noise. Delta(k) does not ascend, does not stay positive, and every
one of the six bootstrap intervals straddles zero — and the cleanest proof needs no
hypothesis at all: the *same* Delta(4) that measured +0.054 on 8.3 years measures +0.155 on
5.6 years, so the statistic moved by 0.10 purely from changing the span.**

### The numbers

| symbol | rung | k | native | 15m matched | **Delta** | bootstrap p5..p95 | share > 0 |
|---|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | 1h | 4 | +0.574 | +0.728 | **+0.155** | −0.059 .. +0.368 | 90% |
| BTCUSDT | 8h | 32 | +0.682 | +0.558 | **−0.124** | −0.336 .. +0.166 | 26% |
| BTCUSDT | 1d | 96 | +0.560 | +0.572 | **+0.012** | −0.139 .. +0.224 | 62% |
| ETHUSDT | 1h | 4 | +0.607 | +0.756 | **+0.148** | −0.082 .. +0.332 | 85% |
| ETHUSDT | 8h | 32 | +0.324 | +0.237 | **−0.087** | −0.302 .. +0.131 | 27% |
| ETHUSDT | 1d | 96 | +0.787 | +0.667 | **−0.120** | −0.347 .. +0.075 | 16% |

Delta goes **up, down, then sideways**. It is negative at `k = 32` on both symbols and
negative at `k = 96` on ETH. There is no ordering by `k` of any kind.

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **N1** | Delta > 0 at every k on both symbols | **FALSIFIED.** Negative in 3 of 6 cells |
| **N2** | Delta(32) > Delta(4) | **FALSIFIED.** Delta(32) is *lower* on both symbols |
| **N3** | Delta(96) ≈ Delta(32) — the step flattens | **Vacuously true.** Nothing here is resolvable, so "approximately equal" is not evidence for the saturation argument |
| **N4** | Hurdle M fails; the trend is not resolvable with two symbols | **CONFIRMED, emphatically.** CI widths are 0.36–0.50 against deltas of 0.01–0.16 |
| **N5** | The matched arm trades more round trips at high k | **FALSIFIED.** BTC at k=96: 8.6 against the native's 8.3. ETH: 8.5 against 9.5. Essentially identical, which reinforces D221 — **the window sets the trading rate, and the bar rate does not** |

**One of five**, and the one that landed was the one saying the study would not be able to
tell.

### What is actually true

**1. The residual D221 left is noise, and the internal check settles it without statistics.**

D221 measured Delta(4) = +0.054 (BTC) and +0.080 (ETH) over 8.3 years. This study measures the
**same comparison, same code, same symbols** over 5.6 years and gets **+0.155 and +0.148**.
A statistic that moves 0.10 when you change the start date is not measuring a property of the
estimator. That single observation is worth more than the six bootstrap intervals, and it is
the reason the pre-registration insisted on one shared span rather than reusing D221's number.

**2. Every interval straddles zero.** The most extreme cell, ETH at k=96, still puts 16% of
its bootstrap mass above zero. Nothing here is distinguishable from chance.

**3. The trading-rate result strengthens D221's finding.** At k=96 the 15m arm decides 96×
more often than the daily arm and still trades the same 8–9 round trips per year. **Decision
frequency is set by the window, not by the bar rate** — the fine arm's extra granularity buys
it nothing in turnover, which also removes the mechanism N5 assumed.

**4. The proposal was not unreasonable; the sample cannot answer it.**

The prediction was that the margin grows *very slightly*. Take that at face value — say an
effect of 0.05 Sharpe. The bootstrap gives a standard error of about **0.130** on Delta.
Resolving 0.05 needs about **0.030**, which is a **19× reduction in variance**, which needs
roughly **19× the independent sample**: about **100 symbol-years** against the ~11 available
here. And crypto symbols are strongly correlated, so twenty coins for 5.6 years would deliver
far less than twenty times the effective sample.

**So the honest verdict is "not detectable here", not "does not exist".** A very slight effect
is exactly the kind this fixture can never confirm or refute, and that is a fact about the
data rather than about the idea.

### Defects and disclosures

**The shared-span gate fired on the first run, and it was right to.** The original assertion
demanded identical start timestamps across configs, which is impossible: a daily bar can only
begin at 00:00 UTC and an 8h bar at 00/08/16:00, so configs on different grids cannot share
an exact start. The invariant was rewritten as *all starts agree to within one coarse bar*,
and the spread is now asserted rather than assumed. **The first version was wrong in the safe
direction** — it refused to publish rather than publishing a misaligned comparison.

**Delta(4) here is not comparable to D221's Delta(4)**, and the difference between them is the
headline finding rather than an inconsistency. Both are correct on their own spans.

### Ledger

| block | looks |
|---|---:|
| 3 rungs × 2 configs | **6** |
| inherited from D217 + D218 + D220 + D221 | 78 |
| crypto-fixture prior + structure/terrain bar on this fixture | 3,739 |
| **verdict count** | **3,823** |

No config is promoted, so no floor is applied.

### What this changes

**The D221 residual is closed and should not be built on.** Any future work citing "the 15m
arm slightly beat the 1h arm" is citing noise, and this record is where that was established.

**The transferable rule stands and is now stronger:** the window is the variable, the bar rate
is not — for signal (D221) *and* for turnover (here, at k=96). Choose the sampling rate on
execution grounds alone.

**And a standing note on power.** This fixture supports roughly 11 symbol-years of independent
crypto history at the frequencies that matter. Effects below about **0.15 Sharpe are not
resolvable on it**, whatever the hypothesis. That number is worth applying *before* designing
the next study rather than discovering it in a bootstrap afterwards.
