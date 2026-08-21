# The breakdown short book: does crisis alpha survive borrow?

**Produced:** 2026-08-21 ·
**Snapshot:** `a2dfbc34c975895a1a2a133e00cdc36978a14f38bea5b83e568cd64b28f28032` ·
**Reproduce:** `uv run python scripts/run_breakdown_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** Directional and beta-loaded, exactly like its long
> sibling, and equally **not** part of this project's market-neutral thesis. It is short
> or flat on a single high-beta instrument. Its honest benchmark is neither the risk-free
> rate nor buy-and-hold: it is "does this pay in the regimes it claims, and does it
> diversify the long book?" — which is what the regime table and the correlation table
> below are for, and why neither is an appendix.

## Read this first: three things that bound what this study can claim

### 1. The stop is INTRABAR now — and it turns out barely to matter

Phase 2 shipped this book with a close-based stop, because `run_backtest` had no intrabar
stop execution, and said so loudly. D170 wired it: `simulator/fills.stop_fill_price` and
its D10 gap semantics now sit in the engine's bar loop, checked before the strategy is
consulted, so a stop closes a position **the moment the bar touches it** and a bar that
gaps through fills at the open rather than at a price the market never traded.

The honest result is that it changes almost nothing here, and the reason is worth more
than the fix. **The stop sits at the far side of the entry channel** — for a short
entering on an N-bar low, it is the N-bar high — which is an enormous distance from the
entry. The trailing exit channel gets there first essentially every time. See the stop
table below: the stop is armed for hundreds of bars per symbol and causes a handful of
exits, or none.

**This also corrects a Phase 2 claim.** That report said "4 of 4 stop exits filled beyond
their own stop, worst by 38.5%". That number was a measurement artifact: it inferred stop
exits by asking whether an exit price ended up beyond the stop level, which also counts
ordinary channel exits that closed past it. The engine now records which fills a stop
actually caused, and the true count is far smaller.

### 2. Borrow is charged, at a stated non-zero rate

10%/yr on the short notional for the whole life of every trade
(D124's rate, D169's decision). Assuming free shorts is the single most result-corrupting
choice available to a spot-crypto short study, because the borrow accrues on ~100% of NAV
continuously while the position is open — unlike the long book, where the equivalent cost
is structurally zero.

### 3. The parameters are NOT mirrored from the long book

Sweep is (10, 20, 30, 40) x (3, 5, 10), against the long book's
(20, 30, 40, 55) x (5, 10, 20). Bear legs are faster and shorter and bear
rallies are violent. **Different optimal parameters from the long side is the expected
finding, not a red flag** — and this sweep is counted separately for multiplicity.

---

# BTC-USD

Out-of-sample **2015-09-10 to 2025-11-12** — 3,717 daily bars
across 59 walk-forward windows. Regime mix of the sample:
**bull 62% · bear 22% · chop 16%**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

Baseline `short_20_5` at `taker_40bp`:

| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |
|---|---|---|---|---|---|
| **bull** | 2,316 | 62% | -33.3% | -0.055 | 1% |
| **bear** | 818 | 22% | -6.1% | +0.007 | 30% |
| **chop** | 582 | 16% | -54.7% | -0.096 | 29% |

## Every variant at `taker_40bp`

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |
|---|---|---|---|---|---|---|
| `short_10_3` | -68.2% | -10.6% | -0.62 | 68.2% | 51 | 10.6% |
| `short_10_5` | -78.3% | -13.9% | -0.69 | 78.5% | 47 | 14.4% |
| `short_10_10` | -61.4% | -8.9% | -0.40 | 72.3% | 35 | 18.7% |
| `short_20_3` | -66.5% | -10.2% | -0.62 | 66.5% | 38 | 8.5% |
| `short_20_5` | -71.6% | -11.6% | -0.62 | 72.4% | 35 | 11.5% |
| `short_20_10` | -57.4% | -8.0% | -0.39 | 67.1% | 26 | 14.6% |
| `short_30_3` | -52.8% | -7.1% | -0.54 | 61.0% | 27 | 6.1% |
| `short_30_5` | -59.5% | -8.5% | -0.54 | 67.6% | 25 | 8.6% |
| `short_30_10` | -60.5% | -8.7% | -0.49 | 72.4% | 21 | 10.9% |
| `short_40_3` | -49.9% | -6.6% | -0.54 | 58.6% | 25 | 5.8% |
| `short_40_5` | -54.1% | -7.4% | -0.51 | 63.3% | 23 | 7.9% |
| `short_40_10` | -53.7% | -7.3% | -0.44 | 67.7% | 19 | 10.1% |
| `short_timestop_3` | -50.0% | -6.6% | -0.42 | 58.4% | 41 | 7.7% |
| `short_timestop_5` | -56.2% | -7.8% | -0.47 | 61.3% | 38 | 8.8% |
| `short_no_regime_gate` | -92.5% | -22.5% | -0.92 | 92.5% | 61 | 19.6% |
| `stop_trail_5` | -40.6% | -5.0% | -0.34 | 52.0% | 36 | 9.5% |
| `stop_trail_10` | -58.3% | -8.2% | -0.47 | 63.4% | 35 | 10.9% |
| `stop_trail_20` | -71.5% | -11.6% | -0.62 | 72.4% | 35 | 11.5% |
| `stop_atr_2` | -63.2% | -9.3% | -0.53 | 66.3% | 35 | 11.1% |
| `stop_atr_3` | -68.3% | -10.7% | -0.59 | 70.0% | 35 | 11.4% |
| `stop_chandelier_3` | -57.8% | -8.1% | -0.53 | 57.8% | 36 | 9.3% |
| `stop_swing_k2` | -46.8% | -6.0% | -0.38 | 55.6% | 35 | 10.1% |
| `stop_swing_k3` | -57.0% | -8.0% | -0.47 | 62.7% | 35 | 10.6% |
| `gate_swing_k2` | -38.9% | -4.7% | -0.69 | 41.4% | 14 | 4.4% |
| `gate_swing_k3` | -26.4% | -3.0% | -0.45 | 34.4% | 10 | 3.0% |
| `exit_e1_k2` | -68.9% | -10.8% | -0.60 | 68.9% | 39 | 9.8% |
| `exit_e1_k3` | -65.5% | -9.9% | -0.56 | 66.5% | 39 | 9.5% |

## The stop sweep: which stops actually bind, and what they cost

| Stop | Total return | Sharpe | Max DD | Trades | Stop exits / armed bars | Bind rate | Gapped |
|---|---|---|---|---|---|---|---|
| `entry_channel` *(incumbent)* | -71.6% | -0.62 | 72.4% | 35 | 1 / 426 | 0.2% | 0 |
| `trail_5` | -40.6% | -0.34 | 52.0% | 36 | 33 / 353 | 9.3% | 0 |
| `trail_10` | -58.3% | -0.47 | 63.4% | 35 | 16 / 404 | 4.0% | 0 |
| `trail_20` | -71.5% | -0.62 | 72.4% | 35 | 1 / 426 | 0.2% | 0 |
| `atr_2` | -63.2% | -0.53 | 66.3% | 35 | 11 / 411 | 2.7% | 0 |
| `atr_3` | -68.3% | -0.59 | 70.0% | 35 | 4 / 423 | 0.9% | 0 |
| `chandelier_3` | -57.8% | -0.53 | 57.8% | 36 | 19 / 344 | 5.5% | 0 |
| `swing_k2` | -46.8% | -0.38 | 55.6% | 35 | 25 / 374 | 6.7% | 0 |
| `swing_k3` | -57.0% | -0.47 | 62.7% | 35 | 18 / 393 | 4.6% | 0 |

**Bind rate first.** A stop that never fires is not being tested — that row is the strategy without a stop, whatever else it shows. **Gapped** counts exits that filled past the level because the bar opened beyond it, which is the residue no intrabar stop can remove on daily bars.

## Deflated Sharpe

| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `stop_trail_5` | -0.0108 | 3,716 | 27 | 0.000034 | **0.0906** |
| `maker_10bp` | `stop_trail_5` | -0.0125 | 3,716 | 27 | 0.000035 | **0.0743** |
| `maker_25bp` | `stop_trail_5` | -0.0152 | 3,716 | 27 | 0.000037 | **0.0540** |
| `taker_40bp` | `stop_trail_5` | -0.0178 | 3,716 | 27 | 0.000040 | **0.0382** |

**Every tier lands between 0.04 and 0.09, far below the 0.95 bar.** The long study's convention applies unchanged: *a DSR below 0.95 means no demonstrated edge; a DSR above 0.95 would not mean the reverse.* This book is decisively on the wrong side of it.

## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. 1,000 draws, direction
-1, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **-0.619** |
| Random-entry null, 95th pct | -0.108 |
| Random-entry null, median | -0.624 |
| Random-entry null, 5th pct | -1.094 |

**Percentile vs the null: 51%.** At the conventional 95% bar the
strategy **does not beat** the null.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **+0.001** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | 1.20 |
| Short book Sharpe (alone) | -0.62 |
| Combined, equal VOL weight | 0.41 |
| Long book max drawdown | 43.0% |
| Combined max drawdown | 34.0% |

**And now with an interval rather than a point estimate.** Paired block bootstrap of
(combined − long-only) annualised Sharpe, 20-bar blocks, 4,000 sims,
seed 0 — the same resampled bar indices applied to both series, so the
correlation between them is preserved (D120). The brief asked for a Jobson–Korkie/Memmel
test; this project's established convention for a Sharpe difference is this bootstrap,
which answers the same question without assuming normality.

| | Δ Sharpe (combined − long-only) |
|---|---|
| Observed | **-0.790** |
| 90% interval | [-1.125, -0.442] |
| P(adding the short book helps) | **0%** |

**The entire interval is negative.** Adding this short book to the long one does not fail to help; it measurably hurts, and the sample is large enough to say so. This is not the 'inside the noise' verdict the long study reached on its own Sharpe gap — it is a decisive negative.

### Correlation per window

The headline correlation is one number for a decade. The brief asks for it **per window**,
and the two can disagree: a full-sample figure near zero is consistent with the books
moving together in some regimes and opposite in others, which would break the
diversification argument at exactly the moment it is needed.

| | Value |
|---|---|
| Windows with a measurable correlation | 15 of 59 |
| Windows the short book sat out entirely | 44 |
| Median per-window correlation | -0.004 |
| Min / max | -0.042 / +0.019 |
| Windows exceeding the ±0.2 target | **0** |
| Largest single-window correlation | -0.042 (window 32) |

A window the short book sat out has no correlation to measure, and is reported as
unmeasurable rather than as zero — "uncorrelated" and "not present" are different claims.

**The target holds window by window, not just on average** — no single window exceeds ±0.2, so the near-zero full-sample figure is not an artefact of opposite-signed regimes cancelling out.

### Squeeze events

The event the tail discipline exists for: an adverse excursion beyond 2 ATR against an
open short. For a short, "adverse" means price RISING — excursions are measured in price
terms (D112), so the adverse side is MFE rather than MAE, and reading the wrong one would
report profitable moves as squeezes.

| | Value |
|---|---|
| Closed trades | 35 |
| Squeezes (> 2 ATR adverse) | **6** |
| Share of trades | 17% |
| Median adverse excursion | 0.96 ATR |
| Worst squeeze | 3.70 ATR |
| Squeezes that ended at the stop | 0% |
| P&L in squeezed trades | -39,015 |

**6 of 35 trades (17%) ran more than 2 ATR against the position while open**, and those trades carry -39,015 of P&L between them. The stop was the exit on 0% of them — a squeeze the stop caught is a different event from one it did not.

### E1 on the combined book

E1 clears the every-symbol bar on both books separately (D178). That does **not** imply it
improves the combination: the two legs are weighted by inverse volatility, so a rule that
changes each leg's volatility changes the weights, and one that changes their correlation
changes how much diversification there is to have.

Both legs carry `failed_breakout` at k=3 — the stronger k on both books in
D178, so it is the consistent choice rather than one tuned per leg.

| | Without E1 | With E1 on both legs | Δ |
|---|---|---|---|
| Long leg Sharpe | +1.202 | +1.303 | +0.101 |
| Short leg Sharpe | -0.619 | -0.558 | +0.061 |
| Long/short correlation | +0.001 | +0.002 | +0.001 |
| **Combined Sharpe** | +0.412 | +0.526 | +0.114 |
| **Combined max drawdown** | 34.0% | 29.5% | -4.5 pp |

Paired block bootstrap of the combined-Sharpe difference (4,000 sims,
seed 0, D120): observed **+0.114**, 90% interval
[+0.002, +0.219], P(E1 helps the combination) =
**95%**.

**The whole interval is positive.** Adding E1 to both legs improves the combined book measurably, not just on the point estimate.

**No new configurations were introduced for this comparison.** Both legs already exist and
are already in their DSR pools, so the combined test costs no additional multiplicity — it
is a different reading of trials already paid for.

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits the stop actually caused | 1 |
| ...of which gapped past the stop | 0 |
| Bars carrying a live stop | 426 |
| Worst single gap | 0.0% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.

---

# ETH-USD

Out-of-sample **2018-07-19 to 2025-12-17** — 2,709 daily bars
across 43 walk-forward windows. Regime mix of the sample:
**bull 50% · bear 34% · chop 16%**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

Baseline `short_20_5` at `taker_40bp`:

| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |
|---|---|---|---|---|---|
| **bull** | 1,351 | 50% | -16.4% | -0.065 | 1% |
| **bear** | 911 | 34% | +33.7% | +0.026 | 40% |
| **chop** | 446 | 16% | +22.6% | +0.039 | 25% |

## Every variant at `taker_40bp`

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |
|---|---|---|---|---|---|---|
| `short_10_3` | -33.6% | -5.4% | -0.28 | 61.3% | 44 | 16.7% |
| `short_10_5` | +60.3% | +6.6% | 0.23 | 55.5% | 34 | 23.7% |
| `short_10_10` | +8.0% | +1.0% | 0.06 | 60.3% | 31 | 27.8% |
| `short_20_3` | -42.6% | -7.2% | -0.40 | 66.6% | 35 | 12.6% |
| `short_20_5` | +37.1% | +4.3% | 0.14 | 54.1% | 27 | 18.1% |
| `short_20_10` | -1.3% | -0.2% | -0.00 | 57.6% | 25 | 22.5% |
| `short_30_3` | -33.8% | -5.4% | -0.37 | 64.2% | 29 | 11.5% |
| `short_30_5` | +53.7% | +6.0% | 0.20 | 56.9% | 22 | 16.4% |
| `short_30_10` | +33.9% | +4.0% | 0.13 | 58.6% | 20 | 20.3% |
| `short_40_3` | -21.4% | -3.2% | -0.26 | 55.8% | 25 | 10.0% |
| `short_40_5` | +86.7% | +8.8% | 0.30 | 47.9% | 18 | 14.9% |
| `short_40_10` | +55.5% | +6.1% | 0.21 | 52.3% | 17 | 18.8% |
| `short_timestop_3` | +64.3% | +6.9% | 0.23 | 36.9% | 31 | 11.8% |
| `short_timestop_5` | +42.7% | +4.9% | 0.16 | 40.2% | 31 | 12.8% |
| `short_no_regime_gate` | -19.3% | -2.9% | -0.08 | 66.1% | 43 | 24.7% |
| `stop_trail_5` | +38.2% | +4.5% | 0.14 | 44.5% | 31 | 13.4% |
| `stop_trail_10` | +56.3% | +6.2% | 0.21 | 50.4% | 28 | 17.3% |
| `stop_trail_20` | +37.1% | +4.3% | 0.14 | 54.1% | 27 | 18.1% |
| `stop_atr_2` | +40.6% | +4.7% | 0.15 | 54.0% | 27 | 16.2% |
| `stop_atr_3` | +36.5% | +4.3% | 0.14 | 54.1% | 27 | 18.0% |
| `stop_chandelier_3` | +16.1% | +2.0% | 0.05 | 55.7% | 30 | 13.8% |
| `stop_swing_k2` | +86.7% | +8.8% | 0.30 | 45.2% | 28 | 15.5% |
| `stop_swing_k3` | +67.8% | +7.2% | 0.25 | 48.7% | 28 | 17.0% |
| `gate_swing_k2` | +42.1% | +4.8% | 0.14 | 39.8% | 13 | 8.8% |
| `gate_swing_k3` | +16.0% | +2.0% | -0.02 | 36.6% | 13 | 8.3% |
| `exit_e1_k2` | +53.9% | +6.0% | 0.20 | 48.3% | 28 | 16.3% |
| `exit_e1_k3` | +66.6% | +7.1% | 0.24 | 44.0% | 28 | 15.8% |

## The stop sweep: which stops actually bind, and what they cost

| Stop | Total return | Sharpe | Max DD | Trades | Stop exits / armed bars | Bind rate | Gapped |
|---|---|---|---|---|---|---|---|
| `entry_channel` *(incumbent)* | +37.1% | 0.14 | 54.1% | 27 | 0 / 489 | 0.0% | 0 |
| `trail_5` | +38.2% | 0.14 | 44.5% | 31 | 26 / 363 | 7.2% | 0 |
| `trail_10` | +56.3% | 0.21 | 50.4% | 28 | 11 / 468 | 2.4% | 0 |
| `trail_20` | +37.1% | 0.14 | 54.1% | 27 | 0 / 489 | 0.0% | 0 |
| `atr_2` | +40.6% | 0.15 | 54.0% | 27 | 9 / 439 | 2.1% | 0 |
| `atr_3` | +36.5% | 0.14 | 54.1% | 27 | 1 / 488 | 0.2% | 0 |
| `chandelier_3` | +16.1% | 0.05 | 55.7% | 30 | 18 / 374 | 4.8% | 0 |
| `swing_k2` | +86.7% | 0.30 | 45.2% | 28 | 19 / 420 | 4.5% | 0 |
| `swing_k3` | +67.8% | 0.25 | 48.7% | 28 | 13 / 460 | 2.8% | 0 |

**Bind rate first.** A stop that never fires is not being tested — that row is the strategy without a stop, whatever else it shows. **Gapped** counts exits that filled past the level because the bar opened beyond it, which is the residue no intrabar stop can remove on daily bars.

## Deflated Sharpe

| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `stop_swing_k2` | 0.0221 | 2,708 | 27 | 0.000100 | **0.5377** |
| `maker_10bp` | `stop_swing_k2` | 0.0205 | 2,708 | 27 | 0.000102 | **0.5008** |
| `maker_25bp` | `stop_swing_k2` | 0.0182 | 2,708 | 27 | 0.000105 | **0.4453** |
| `taker_40bp` | `short_40_5` | 0.0159 | 2,708 | 27 | 0.000108 | **0.3927** |

**Every tier lands between 0.39 and 0.54, far below the 0.95 bar.** The long study's convention applies unchanged: *a DSR below 0.95 means no demonstrated edge; a DSR above 0.95 would not mean the reverse.* This book is decisively on the wrong side of it.

## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. 1,000 draws, direction
-1, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **0.142** |
| Random-entry null, 95th pct | 0.132 |
| Random-entry null, median | -0.426 |
| Random-entry null, 5th pct | -1.047 |

**Percentile vs the null: 96%.** At the conventional 95% bar the
strategy **beats** the null.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **-0.001** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | 0.78 |
| Short book Sharpe (alone) | 0.14 |
| Combined, equal VOL weight | 0.65 |
| Long book max drawdown | 35.2% |
| Combined max drawdown | 29.5% |

**And now with an interval rather than a point estimate.** Paired block bootstrap of
(combined − long-only) annualised Sharpe, 20-bar blocks, 4,000 sims,
seed 0 — the same resampled bar indices applied to both series, so the
correlation between them is preserved (D120). The brief asked for a Jobson–Korkie/Memmel
test; this project's established convention for a Sharpe difference is this bootstrap,
which answers the same question without assuming normality.

| | Δ Sharpe (combined − long-only) |
|---|---|
| Observed | **-0.126** |
| 90% interval | [-0.572, +0.315] |
| P(adding the short book helps) | **31%** |

**The interval spans zero**, so the ensemble effect is not measurable at this sample size. That is not evidence of neutrality — it is the absence of evidence either way, and it should not be reported as 'the short book is roughly neutral'.

### Correlation per window

The headline correlation is one number for a decade. The brief asks for it **per window**,
and the two can disagree: a full-sample figure near zero is consistent with the books
moving together in some regimes and opposite in others, which would break the
diversification argument at exactly the moment it is needed.

| | Value |
|---|---|
| Windows with a measurable correlation | 15 of 43 |
| Windows the short book sat out entirely | 28 |
| Median per-window correlation | -0.002 |
| Min / max | -0.022 / +0.025 |
| Windows exceeding the ±0.2 target | **0** |
| Largest single-window correlation | +0.025 (window 30) |

A window the short book sat out has no correlation to measure, and is reported as
unmeasurable rather than as zero — "uncorrelated" and "not present" are different claims.

**The target holds window by window, not just on average** — no single window exceeds ±0.2, so the near-zero full-sample figure is not an artefact of opposite-signed regimes cancelling out.

### Squeeze events

The event the tail discipline exists for: an adverse excursion beyond 2 ATR against an
open short. For a short, "adverse" means price RISING — excursions are measured in price
terms (D112), so the adverse side is MFE rather than MAE, and reading the wrong one would
report profitable moves as squeezes.

| | Value |
|---|---|
| Closed trades | 27 |
| Squeezes (> 2 ATR adverse) | **6** |
| Share of trades | 22% |
| Median adverse excursion | 1.24 ATR |
| Worst squeeze | 3.94 ATR |
| Squeezes that ended at the stop | 0% |
| P&L in squeezed trades | -86,158 |

**6 of 27 trades (22%) ran more than 2 ATR against the position while open**, and those trades carry -86,158 of P&L between them. The stop was the exit on 0% of them — a squeeze the stop caught is a different event from one it did not.

### E1 on the combined book

E1 clears the every-symbol bar on both books separately (D178). That does **not** imply it
improves the combination: the two legs are weighted by inverse volatility, so a rule that
changes each leg's volatility changes the weights, and one that changes their correlation
changes how much diversification there is to have.

Both legs carry `failed_breakout` at k=3 — the stronger k on both books in
D178, so it is the consistent choice rather than one tuned per leg.

| | Without E1 | With E1 on both legs | Δ |
|---|---|---|---|
| Long leg Sharpe | +0.775 | +0.952 | +0.177 |
| Short leg Sharpe | +0.142 | +0.243 | +0.101 |
| Long/short correlation | -0.001 | -0.001 | -0.001 |
| **Combined Sharpe** | +0.649 | +0.845 | +0.197 |
| **Combined max drawdown** | 29.5% | 24.4% | -5.1 pp |

Paired block bootstrap of the combined-Sharpe difference (4,000 sims,
seed 0, D120): observed **+0.197**, 90% interval
[+0.063, +0.362], P(E1 helps the combination) =
**100%**.

**The whole interval is positive.** Adding E1 to both legs improves the combined book measurably, not just on the point estimate.

**No new configurations were introduced for this comparison.** Both legs already exist and
are already in their DSR pools, so the combined test costs no additional multiplicity — it
is a different reading of trials already paid for.

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits the stop actually caused | 0 |
| ...of which gapped past the stop | 0 |
| Bars carrying a live stop | 489 |
| Worst single gap | 0.0% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.

---

# Verdict

- **BTC-USD**: null percentile 51%, long/short correlation +0.00, combined Sharpe 0.41 against 1.20 long-only (max drawdown 34% against 43%).
- **ETH-USD**: null percentile 96%, long/short correlation -0.00, combined Sharpe 0.65 against 0.78 long-only (max drawdown 30% against 35%).

**The null verdict is SPLIT and must not be read as a pass.** ETH-USD clears the 95% bar; BTC-USD does not. The long study fixed the rule for exactly this situation before looking — a filter is kept only if it improves on EVERY symbol, because one symbol out of two is a coin flip. The same discipline applies here, and by it the entry rule is not demonstrated. Reporting the winner alone would be the single most misleading thing available in this document.

**The diversification claim holds and the profitability claim does not, and those are separate findings.** Correlation against the long book comes in at or below the brief's ~0.2 target on both symbols — genuinely near zero, which is the complementary-payoff property the ensemble argument needs. But near-zero correlation cannot rescue a book that loses money: on BTC-USD, ETH-USD the equal-vol-weighted combination has a LOWER Sharpe than the long book alone. You cannot diversify with a negative-expectancy asset; you can only spread the same losses more smoothly. The one thing that does survive is drawdown: on BTC-USD, ETH-USD the combined book's worst drawdown is smaller than the long book's. That is the same shape of result the long study landed on — a drawdown-shape finding, not an alpha finding — and it should be quoted with the Sharpe cost attached, never on its own.

### Success criteria from the brief, scored

The brief named three: *strongly profitable in bear regimes; flat-to-small-loss in bull
regimes; acceptable chop bleed.* Scored here as bear return > +10%, bull return > −20%,
chop return > −10% — thresholds fixed before reading, and blunt on purpose.

| Symbol | Bear (strongly profitable?) | Bull (flat-to-small-loss?) | Chop (acceptable bleed?) |
|---|---|---|---|
| BTC-USD | -6.1% FAIL | -33.3% at 1% exposure FAIL | -54.7% FAIL |
| ETH-USD | +33.7% PASS | -16.4% at 1% exposure PASS | +22.6% PASS |

**Split again, and along the same line as the null.** ETH-USD meets all three; BTC-USD does not. The two symbols are telling different stories about the same rule, which on a two-instrument sample is the definition of an undemonstrated result rather than a partial success.

**The gate itself works on every symbol** — bull-regime exposure is at most 1%, so the book really does stand aside when the long book is working. Note that this is a separate claim from the bull CRITERION above, and the two can diverge: on a symbol where the criterion fails, it fails not because the gate let the book trade through the bull market but because the handful of trades it did allow were bad enough to lose double digits on their own. The gate is not the problem. What it gates is.
### The stop sweep, scored

Same rule the long study fixed before looking: keep only what improves on EVERY symbol,
because one out of two is a coin flip. Δ is against the incumbent `entry_channel` stop at
`taker_40bp`; `INERT` means the variant produced results identical to the incumbent, so it is
not a distinct configuration at all.

| Stop | Δ Sharpe BTC-USD | Δ Sharpe ETH-USD | Stop exits | Decision |
|---|---|---|---|---|
| `trail_5` | +0.279 | -0.002 | 59 | DROP |
| `trail_10` | +0.144 | +0.068 | 27 | **KEEP** |
| `trail_20` | +0.002 | +0.000 | 1 | INERT |
| `atr_2` | +0.092 | +0.013 | 20 | **KEEP** |
| `atr_3` | +0.034 | -0.002 | 5 | DROP |
| `chandelier_3` | +0.092 | -0.096 | 37 | DROP |
| `swing_k2` | +0.244 | +0.161 | 44 | **KEEP** |
| `swing_k3` | +0.152 | +0.105 | 31 | **KEEP** |

**4 of the swept stops improve risk-adjusted return on every symbol by more than 0.01 Sharpe**, and the strongest by worst-case improvement is `swing_k2` (+0.16 on its weaker symbol, 44 stop exits). The mechanism is consistent: rank correlation between how often a stop binds and how much it helps is positive on every symbol (BTC-USD +0.93, ETH-USD +0.00). **Stops that actually engage do better**, which is the finding D170 could not produce with a stop that never fired.

**Three things this does not mean.**

First, **less bad is not good.** The best BTC row is still a large loss at a negative
Sharpe; a tighter stop shrinks the damage, it does not create an edge. The entry rule is
what failed its null, and no stop repairs an entry.

Second, **this is a fresh trial series and it is not free.** Six stop configurations on
two symbols across four tiers were evaluated here on top of an already-swept strategy.
One of them (`trail_20`) turned out to be inert — for a short entering on a 20-bar low, a
20-bar trailing high IS the entry channel — so the effective count is five. These trials
are NOT yet in the deflated-Sharpe accounting (see the gap noted below), and picking the
best row of five after the fact is exactly the selection this project's machinery exists
to penalise.

Third, **the sweep was run at fixed entry/exit parameters.** A stop interacts with the
exit channel it sits beside, and re-optimising both together would be a much larger
multiplicity bill for a book that has not yet shown an entry edge.
### What the stop actually did

The stop was armed for **915 bars** and caused **1 exit(s)**
(BTC-USD 1 exit(s) from 426 armed bars · ETH-USD 0 exit(s) from 489 armed bars). **None of them gapped** — each filled at its stop price, which is the intrabar machinery doing exactly what it exists to do.

**Read those two numbers against each other.** A stop armed for hundreds of bars that
closes a handful of trades is *present* rather than *binding*: it sits at the far side of
the entry channel, which is a very long way from a breakdown entry, so the trailing exit
gets there first almost every time. The brief's premise — that short expectancy becomes
calculable once the squeeze tail is truncated — is now satisfied mechanically, and turns
out not to be the thing that was limiting this book.
### Multiplicity: everything that was evaluated

| What | Count |
|---|---|
| Strategy variants per symbol | 27 |
| — of which entry/exit grid cells | 12 |
| — of which time-stop variants | 4 |
| — of which stop families | 8 |
| — of which structure gates | 2 |
| — of which gate counterfactuals | 1 |
| Cost tiers | 4 |
| Symbols | 2 |
| **Out-of-sample trials logged** | **216** |
| Per-window trial rows logged | 2754 |

Every one is registered in `data/breakdown_study_registry.sqlite` and every variant row
is in the DSR pool for its (symbol, tier) cell. One of the stop families (`trail_20`) is
inert — mechanically the incumbent under another name — so 26 of the
27 are distinct configurations, and the pool is not reduced for it: a
configuration you tried and learned nothing from still cost you a look.
### The pre-registered predictions, scored

D173 recorded three predictions and was committed before this study ran, so they are
dated by git rather than written afterwards. Scored by the same every-symbol rule at
SHARPE_EPS = 0.01.

**H1 — the structure stop will not beat `trail_10` on both symbols.**

| Comparison | Δ Sharpe BTC-USD | Δ Sharpe ETH-USD | Every-symbol rule |
|---|---|---|---|
| `stop_swing_k2` vs `stop_trail_10` | +0.100 | +0.093 | **BEATS IT** |
| `stop_swing_k3` vs `stop_trail_10` | +0.008 | +0.037 | does not |

**H1 IS FALSIFIED.** swing_k2 clears the every-symbol bar against `trail_10`. The prediction was that no structure stop would, and it was wrong.

**H2 — the structure gate will not improve on the SMA200 gate alone.**

| Comparison | Δ Sharpe BTC-USD | Δ Sharpe ETH-USD | Every-symbol rule |
|---|---|---|---|
| `gate_swing_k2` vs baseline | -0.066 | -0.006 | does not |
| `gate_swing_k3` vs baseline | +0.168 | -0.165 | does not |

**H2 holds.** Neither gate improves on the plain SMA200 baseline across both symbols — and the mechanism is visible in the trade counts, which fall by roughly two thirds. A second gate is another trade-removing device, and it removes good trades along with bad, exactly as every such device tested in this project has.

**H3 — deflated Sharpe will not reach 0.95 on either symbol.** **H3 holds.** The best DSR anywhere is 0.538, nowhere near 0.95.
### What deflation does to all of it — and this is the section that matters

Deflated Sharpe by symbol across all four tiers: **BTC-USD 0.038–0.091 · ETH-USD 0.393–0.538**. Not one cell reaches the
0.95 bar, and the weaker symbol does not reach 0.10 at any tier.

**This reframes every positive number above.** ETH's 96th-percentile null result and its
clean sweep of the three success criteria were the strongest things in this document.
Both were computed on the best of 27 configurations, and once that search
is priced in, the evidence for skill is gone. The same applies to the stop sweep: the
variant that most improved BTC (`stop_trail_5`, −71.6% → −40.6%) is precisely the one
DSR selects as the best-of-27 and deflates to near zero. That is not DSR
being harsh — it is DSR doing the exact job it exists for, on a search this study
performed and then reported.

The honest one-line summary of the short book is now: **a rule with no demonstrated edge,
whose apparent successes are consistent with having looked 27 times.**

# Standing caveats

1. **The stop is intrabar (D170) but almost never binds.** The mechanism is correct —
   touched stops fill at the stop, gapped ones at the open — but the level sits at the
   far side of the entry channel, so the trailing exit closes nearly every position
   first. A risk control that never binds has not been shown to work on this sample, only
   to be unneeded on it. A tighter stop (ATR-based, say) is a different strategy and
   would need its own sweep and its own multiplicity accounting.
2. **Borrow is a stated assumption, not a quote.** 10%/yr is mid-range for BTC/ETH spot
   margin borrow over the sample; it was neither swept nor negotiated, and hard-to-borrow
   episodes in a real crash would be worse precisely when the book is most short.
3. **No funding, no perp expression.** These are spot shorts (D108). A perpetual-futures
   implementation would pay funding, which in a falling market is often a CREDIT to
   shorts — so this is conservative in that one direction and silent about it otherwise.
4. **Live tradability is out of scope and mostly negative.** The FCA retail
   crypto-derivatives ban and the absence of retail spot margin mean this book is
   backtest-and-shadow-signals only. The one legal live expression at current capital is
   equity-index breakdown via spread betting, which is a different instrument and a
   different spec.
5. **Two instruments, both survivors.** The same selection bias the long study named as
   its largest un-deflatable problem applies here unchanged.
6. **The DSR pool counts configurations, not everything.** It does not count the
   two-symbol choice, nor the decision to test a short book on crypto after a decade of
   visible crypto trend. As the long study put it: a DSR below 0.95 means "no
   demonstrated edge"; a DSR above 0.95 would not mean the reverse.
