# D668 STAGE 0 RESULT: NOT SUPPORTED on YM and on RTY. The plain break of yesterday's range does not beat its same-clock null on either evidence root, and the expected-profit predictor cannot rank trades on any root. The break's mechanism grades by root: NQ strong, ES present, YM weak, RTY absent

*2026-09-29.*
- *One run of `scripts/stage0_d668_break_predictor.py` (`--run`) under D668 (`1e8d72e1`) and D668-A1 (`c656d0f1`), 2.4 min.*
- *In-sample through 2025-02-28; the vault is not read.*
- *Output: `data/stage0_d668_break_predictor.json`. Dealer gamma (GEX): SqueezeMetrics.*

**Inputs, gated before the run:**
- YM (37) and RTY (31) Sierra tick files, none cut short (`e33ca743`).
- A7 for YM/RTY: 451,302,751 RTH records, no multi-trade records (`c609e295`).
  - **YMZ15 was not downloaded.** It only feeds YM's A7 warm-up threshold for about the first 20 sessions of 2016.
    Those read A7 = 0 under A1 §4's missing rule.
- TICK-NASDAQ re-downloaded in full (2014-02 → live).
- Gate F passes on all four TICK series (2,344 in-sample sessions, median coverage 1.0).
  - RTY's f6 is the mean of the TICK-NYSE and TICK-NASDAQ z, as A1 §3 declared.
- **Reproduction:** ES and NQ's plain-break E4 and E2 gross equal D667 to 1e-9 (ES E4 +1.2035; NQ E4 +4.2891).
- ES and NQ's development numbers are identical to the development run `ab49940e`.

## 1. Gate 1, the mechanism (E4 gross, unfiltered; Holm across YM and RTY)

| | YM (evidence) | RTY (evidence) | *ES (dev)* | *NQ (dev)* |
|---|---|---|---|---|
| trades / a year | 1,468 / 162 | 1,228 / 164 | 1,432 / 158 | 1,435 / 158 |
| gross (HAC t) | +1.10 (1.23) | −0.40 (−0.30) | +1.20 (1.31) | +4.29 (3.57) |
| N1 (same clock, same side mix, every session): p50 / p95 (SE) / rank | −0.14 / +1.39 (0.06) / **0.90** | −1.20 / +1.15 (0.10) / **0.71** | −0.94 / +0.46 (0.05) / 0.99 | +0.44 / +2.29 (0.07) / 1.00 |
| long: break vs its null p50 | +2.17 vs +0.53 | −0.23 vs −1.77 | +2.95 vs −0.28 | +5.71 vs +1.26 |
| short: break vs its null p50 | −0.17 vs −0.86 | −0.59 vs −0.65 | −0.97 vs −1.82 | +2.40 vs −0.66 |
| without February–April 2020 | +1.32 | −0.28 | +1.48 | +4.33 |
| Holm p | 0.22 | 0.62 | — | — |
| **Gate 1** | **fails** (below N1's p95; t 1.23) | **fails** (gross negative) | dev | dev |

**The break's excess over the random-entry null grades by root:**
- NQ: +3.9 bp, rank 1.00;
- ES: +2.1, rank 0.99;
- YM: +1.2, rank 0.90;
- RTY: +0.8, rank 0.71, on a negative base.

**The trend-day capture is strongest on NQ and absent on RTY.**

## 2. Gate 2, the expected-profit predictor

| | YM | RTY | *ES* | *NQ* |
|---|---|---|---|---|
| unfiltered net (t) | −2.06 (−2.31) | −5.21 (−3.91) | −2.31 (−2.49) | +1.69 (1.40) |
| π̂ at the end | −0.18 | +0.25 | −0.19 | +0.48 |
| filtered trades (pass rate) | 0 (0%) | 32 (3.4%) | 3 | 225 (19.7%) |
| filtered net | — | −9.64 | −0.20 | +4.71 |
| β_disc (t); N2 p95 of t | −0.24 (−0.93); 1.18 | +0.25 (0.64); 1.35 | −0.23 (−0.55); 1.12 | +0.17 (0.63); 1.30 |

**The predictor does not rank trades on any root** (β_disc t < 1 everywhere, below N2). Neither evidence root reached
Gate 2.

**Verdicts: YM NOT SUPPORTED; RTY NOT SUPPORTED; the construction NOT SUPPORTED.**

## 3. The four groups and the component line (unfiltered, 1 micro)

| | YM | RTY |
|---|---|---|
| net / median / win / payoff | −2.06 / −9.76 / 35% / 1.55 | −5.21 / −16.39 / 35% / 1.38 |
| skew, kurtosis | 2.13, 11.9 | 1.57, 6.7 |
| trimmed / ex-top / ex-bottom | −3.00 / −3.94 / −1.11 | −6.30 / −7.48 / −4.02 |
| Sharpe / Sortino (per trade) | −0.74 / −1.27 | −1.36 / −2.12 |
| daily $ Sharpe; $ a year | −0.68; −$426 | −1.32; −$733 |
| ρ K8; ρ ES / NQ / the other | −0.04; 0.51 / 0.25 / 0.27 | −0.05; 0.37 / 0.19 / 0.27 |
| gross by open class: no gap / inside / through | +1.13 / +0.22 / +1.88 | −2.40 / +1.89 / +1.43 |
| before / after 2022-05-16 | +0.44 / +2.66 | −0.67 / +0.05 |
| vault power at the in-sample mean | 7% | 2% |

## 4. Predictions (§10)

| # | prediction | outcome |
|---|---|---|
| 1 | YM fails Gate 1 | held |
| 2 | at most one evidence root passes Gate 1 | held (none) |
| 3 | β_disc t < 2 on every root | held |
| 4 | NQ filtered within ±1.5 bp of unfiltered | failed (+4.71 vs +2.19 live; development) |
| 5 | long > short on every root | held |
| 6 | RTY's pass rate < 30% | held (3.4%) |
| 7 | A7 negative on NQ's final fit | held |

## 5. One pattern across all four roots, recorded and not promoted

**The walk-forward coefficient on aligned aggressor flow (f5, D × A7) is negative on every root:**

| | ES | NQ | YM | RTY |
|---|---|---|---|---|
| coefficient (standardised) | −4.90 | −2.97 | −0.37 | −6.29 |
| sign stability | 0.66 | 0.82 | 0.98 | 1.00 |

- This is the "spent flow" contraindication the analyst lanes proposed (`docs/research/opening-break-predictor-lanes.md`).
- On YM and RTY its sign is stable, and was read here for the first time.
- It is a coefficient inside a model that does not rank trades, so it is a lead, not a result.

## 6. Routing

- **The plain break of yesterday's range does not generalise across the index roots.** Only NQ carries it, and NQ's
  number is in-sample (vault power about 31%).
- **With D673, the index-root line of the opening break closes on its current constructions:**
  - the plain break (D668);
  - the re-break (D666);
  - the size-tier construction (D671);
  - the compression break (D672/D673).
- **What stays open, named:**
  - NQ's in-sample result, for the vault;
  - the quiet-overnight direction (D673 §4);
  - the spent-flow contraindication (§5);
  - the root-aware test on CL, NG, GC and SI (`docs/planning/ROOT_AWARE_BREAK_PLAN.md`), which uses roots none of
    these reads have touched.

## Amendment D668-A2, after the result (2026-09-29): the friction was counted twice; the verdicts stand

**The problem (found in D677 §1).** This runner charges friction twice:
- it fills every stop one tick through **inside the gross** (entry at the stop + 1 tick; stop exits at the stop − 1
  tick);
- and the cost line then charges $3 + the measured crossing + **one more tick** (§A1.1).

The one-tick fill already is the crossing.

**Single count, declared for every break runner from here on, and for any NQ vault pre-registration:**
- trades are scored **at the level**, with no fill ticks;
- then charged **$3 + the measured crossing** (`d508_exec`), once.
- The +1-tick slippage ladder stays as a sensitivity.

`scripts/diag_d677_single_count_index.py` (`data/diag_d677_single_count_index.json`) reproduces this record's gross
to 1e-9, then rescores. Per trade, bp (HAC t):

| | ES | NQ | YM | RTY |
|---|---|---|---|---|
| gross as recorded | +1.20 (1.31) | +4.29 (3.57) | +1.10 (1.23) | −0.40 (−0.30) |
| at the level, no fill ticks | +2.71 (2.95) | +4.80 (3.99) | +1.77 (1.98) | +0.64 (0.48) |
| net as recorded | −2.31 (−2.49) | +1.69 (1.40) | −2.06 (−2.31) | −5.21 (−3.91) |
| **net, single count** | **−0.03 (−0.03)** | **+2.48 (2.06)** | **−1.02 (−1.15)** | **−3.60 (−2.71)** |
| correction | +2.28 | +0.79 | +1.04 | +1.61 |

**No verdict changes.**
- Gate 1 compared the gross with N1, whose random entries pay the same fill ticks.
- YM and RTY fail Gate 1 either way.

**What does change:**
- **NQ's in-sample net is +2.48 bp (t 2.06), not +1.69.** That is the figure a vault pre-registration starts from.
- **ES's net is about zero, not −2.3.**
- The correction is largest where the tick is large relative to the price (ES, RTY).
