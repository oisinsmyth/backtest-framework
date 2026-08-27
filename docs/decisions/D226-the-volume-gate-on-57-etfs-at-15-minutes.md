# D226 — Does the volume regime gate survive 57 instruments?

**Status:** Pre-registered — committed BEFORE the study runs
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** The generalisation question D227 could not answer, redirected to breadth

> A result section will be appended and nothing above it edited.

## Provenance, stated first

**The design was fixed and approved before any code was written.** The runner
(`scripts/run_etf_intraday_gate.py`) was then built to it and has run **only a 3-symbol,
2-window smoke test** on separate `*.smoke.*` paths, producing no verdict and no cell that
enters this ledger.

**But the runner exists before this record does**, which is not the order D217–D224 used, and
saying so is cheaper than being caught. What that costs is small — every parameter, hurdle and
grid below was settled in the approved plan before implementation, so nothing was chosen after
seeing a number. What it does not cost is nothing, and D225's provenance section is the
template.

## The question

D224 and D225 established that a **volume regime gate** — `EMA(n) > SMA(n)` on volume, gating
trade entries only, never exiting — beats its matched-count random null on BTC and ETH, at two
sampling rates, by roughly six times the mechanical benefit of trading less.

D225 also found the damaging thing: **the working window is one point wide.** Across
`[12, 24, 36, 50, 72, 100, 140, 200, 300, 480]` hours only 50h is positive-net on BTC, both
neighbours are negative, and at 200h the identical construction **inverts** into a significant
anti-signal at the 0.5th percentile of its own null.

So: **is that a property of the method, or of two coins over one span?**

D227 tried to answer it by splitting the crypto span in time and was abandoned on power — the
proposed stop would have closed the study 93% of the time on an effect that is real by
assumption. Its conclusion was explicit: **the answer is more instruments, not thinner slices
of the same two.**

## The test bed

`data/fixtures/etf_intraday_15m_raw.csv.gz` — fetched, split-adjusted and committed for this
study.

| | |
|---|---|
| 57 ETFs, 3,194,849 rows | 2018-01-02 → 2026-08-26, 2,174 sessions |
| 15m bars, 26 per session (09:30–15:45) | **PPY = 26 × 252 = 6,552** |
| **zero-volume bars: 0 (0.0000%)** | 18 half-days derived and dropped |
| 12 splits back-adjusted, prices *and* volumes | 1,955 dividends, so both return bases exist |

**Why the numbers make this the right fixture**, measured before designing:

| | daily ETF | **intraday ETF** |
|---|---:|---:|
| live span | 6.01 y | **7.94 y** |
| entries per ETF | 34 (min) | **359** (median) |
| pooled trades | 2,418 | **20,463** |
| after a 50% gate | 8–17 | **179** |
| mean pairwise correlation | 0.468 | **0.282** |
| effective independent instruments | 2.10 | **3.40** |
| **effective trades** | **~89** | **~1,219** |

Two consequences that decided the design rather than being worked around:

1. **Hurdle E is NOT redefined.** The original D217/D218 conjunction — *"≥100 signals pooled
   per arm, and ≥30 entries per ETF"* — passes on both legs and **still passes after a 50%
   gate** (179 against 30). The redefinition debated earlier is unnecessary, which is a far
   better outcome than winning the argument for it.
2. **D220's stop is NOT overridden.** It is scoped to *"this fixture"* — the daily one. This
   is a different fixture, so the stop stands.

## The arms

**Parent.** Impulse MACD `(136, 36)` long-flat, `lag=1`. This is *literally* the crypto arm:
D221 established the indicator is scale-free in bars, so 136 bars at 15m is the same estimator
on both fixtures. Warm-up 4,049 bars, leaving **52,007 live bars = 7.94 years**.

**Gate.** `EMA(w) > SMA(w)` on volume, evaluated at the entry bar only, never exiting. A
blocked trade skips the whole run. `ok[:, 1:] = live_gate[:, :-1]` — the exposure held through
bar *t* is decided from bar *t−1*, so the newest legitimately available volume is `volume[t−1]`.

**Sweep, declared here and counted in full.** Windows in **bars**:
`(48, 96, 144, 200, 288, 400, 560, 800, 1200, 1920)`. **200 is D224's committed `VOL_WINDOW`**,
so the gate matches the crypto study in the same units. Every window is defined everywhere the
arm trades — the longest is inside the 4,049-bar warm-up — so there is **no per-window start
and no span truncation**, and all ten cells are directly comparable.

**The sweep is the point of the study.** D225's one-point-wide spike is the strongest argument
against the gate, and 57 instruments is the only way to test whether that fragility is a
property of the method.

## Hurdles

- **H — carries the verdict.** Beat the **matched-count random null** at ≥95th percentile on
  **both** net Sharpe and net total return. On a book whose average trade is fee-negative, any
  removal gains money mechanically; this is the only control separating a real effect from
  having traded less.
- **E — unchanged.** ≥100 pooled **and** ≥30 entries per ETF. Both legs reported.
- **P.** Beat the unfiltered parent on both metrics.
- **G.** Clear `expected_max_sharpe`, with **`var_trials` from the simulated null**, never from
  the study's own cells (D224's correction — cells gave an unusable +4.9).

## Three things named before the run

1. **Effective sample beside the raw count.** 20,463 pooled trades are **~1,219 effective** at
   ρ = 0.282. Both are reported so nobody quotes the pooled number as a sample size.
2. **Bar-time and calendar-time diverge.** 136 bars is 34 *continuous* hours on crypto (1.4
   days) but 34 *trading* hours here (5.2 calendar days, with overnight gaps). Bar counts match;
   calendar spans do not. D221's invariance is a bar-count statement, so bars is the right
   match — and D219's amendment already requires cross-fixture comparison on
   **`arm − matched buy-and-hold`**, never raw Sharpe.
3. **Both return bases.** WP0 supplied dividends, so price-only *and* dividend-adjusted are
   reported, the way D218's hurdle D named both metrics up front rather than in an addendum.
   Direction: a long-flat arm invested ~50% of the time collects ~50% of dividends while
   buy-and-hold collects 100%, so omitting them would understate the benchmark roughly twice
   as much as the arm. **Hurdle H is unaffected either way** — arm and null share a basis.

## Ledger

| count | N | what it includes |
|---|---:|---|
| fresh | **10** | the declared window sweep |
| + hypothesis lineage | **78** | D220's 12, D224's 10, D225's 46 |
| **+ disclosed ETF prior** | **45,819** | plus 45,346 registry configs + the 395 structure/terrain bar |

**Count 3 carries the verdict.** D225's 40-cell sweep attaches specifically, because the
200-bar gate is used *because* that sweep pointed there.

**What does not transfer: D225's crypto prior of 3,739.** It was logged on Binance data and has
no bearing on an ETF study; carrying it here would be arithmetic theatre. An early draft of the
runner declared 3,879 — exactly that mistake — and it is recorded because the error is easy and
looks diligent.

Zero-look: the fixture census, the oracle bound, the matched-count null, the effective-sample
calculation.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **R1** | The gate clears H on the pooled 57-ETF book at **some** window | **moderate** |
| **R2** | **The 200-bar window is not special here.** If D225's spike were a property of the method it should reappear at the same bar count; I expect it will not | **moderate** |
| **R3** | The window-response profile is **flatter** than crypto's — no single-point spike, no inversion at the long end. 57 instruments average away what two coins expressed | **moderate-high** |
| **R4** | No cell clears G at the verdict count of 45,819 | **high** |
| **R5** | The gate cuts exposure roughly in half and improves net Sharpe while **reducing total return**, the pattern every filter in this programme has produced | **moderate-high** |

**R2 and R3 are the study.** If the profile is flat and positive across many windows, the gate
is a real regime effect and D225's spike was two coins being noisy. If it is spiky *and* the
spike is somewhere else, the gate is curve-fitting and this is where it dies. **If the spike
reappears at 200 bars specifically, that is the most interesting outcome available** and would
be the first evidence that the window itself means something.

**What would change my mind:** R4 failing — a cell clearing a floor built from 45,819 looks.
Nothing in this programme has ever done that.

## Pre-committed stops

- **No parameter search.** Ten windows, one book, one parent. If the gate fails, the answer is
  not an eleventh window.
- **The random-null gate.** A cell that improves net PnL without clearing its matched-count
  null is reported as a **failure**, in those words.
- **Nothing is promoted without unmined data**, whatever the result (D215/D216).
