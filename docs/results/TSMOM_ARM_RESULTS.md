# D239 — time-series momentum as arm two

**STAGE 1 — A SCREEN, NOT A VERDICT.** screen (mined 57) -- the holdout and forward window are untouched

*seed 0, 1,000 rotations, 19.1s. 57 ETFs x 1,515 live bars, 2018-12-21 .. 2024-12-30. Lookback 252 bars; blend 50%/50%.*

## The four books

| | rule | exposure | excess Sharpe | CAGR | **deployable** | vol | max DD | Calmar | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **S1** | the recovery rule (arm one) | 18.9% | **+0.746** | 5.43% | **8.83%** | 6.1% | -10.30% | 0.527 | ✗ |
| **T1** | `close[t] > close[t−252]`, all 57 | 58.3% | **+0.115** | 3.30% | **5.00%** | 8.3% | -14.19% | 0.232 | ✗ |
| **T2** | the same rule, non-equity 11 | 49.8% | **-0.068** | 1.54% | **3.56%** | 6.2% | -15.66% | 0.098 | ✗ |
| **T3** | 50/50 blend of S1 and T1 | 38.6% | **+0.563** | 4.87% | **7.43%** | 5.8% | -8.66% | 0.563 | ✗ |
| B&H | always long | 100.0% | +0.235 | 8.42% | 8.42% | 17.7% | -34.60% | 0.243 | — |

***deployable*** *credits T-bills at 4% on the idle fraction. Every CAGR in this programme earns nothing on cash, which materially understates a book that is flat most of the time.*

## P3 — the rotation null, and why it is the primary

*A 58%-exposed long-flat book, in a market that rose 8.42%/yr, posts a positive Sharpe for entirely trivial reasons. Same exposure, same turnover, same holding periods, wrong bars — this is what separates trend **timing** from **being invested a lot**.*

| | actual | null p50 | null p95 | **percentile** | money pct | vol ratio | P3 |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **T1** | **+0.115** | +0.296 | +0.423 | **0.7th** | 0.2th | 0.781x | ✗ |
| **T2** | **-0.068** | -0.165 | +0.355 | **63.7th** | 63.1th | 1.022x | ✗ |
| **T3** | **+0.563** | +0.334 | +0.442 | **100.0th** | 99.3th | 0.832x | ✓ |

## P4 — versus buy-and-hold, with the √f decomposition

| | exposure | √f predicts | actual | **selection quality** | beats B&H |
|---|---:|---:|---:|---:|:--:|
| **T1** | 58.3% | +0.179 | +0.115 | **-35.8%** | ✗ |
| **T2** | 49.8% | +0.166 | -0.068 | **-141.3%** | ✗ |
| **T3** | 38.6% | +0.146 | +0.563 | **+285.8%** | ✓ |

*√f predicts what a **selection-free** book at that exposure would score, from buy-and-hold's +0.235.*

## P1 — the diversification condition, which needs no weighting choice

*Adding an arm raises the book's maximum attainable Sharpe iff `SR_B > ρ · SR_A`.*

| | ρ with S1 | bar `ρ × 0.746` | actual | P1 |
|---|---:|---:|---:|:--:|
| **T1** | +0.2668 | +0.199 | **+0.115** | ✗ |
| **T2** | +0.0731 | +0.055 | **-0.068** | ✗ |

## P2 — does a declared 50/50 blend beat S1 alone?

| | excess Sharpe |
|---|---:|
| S1 alone | +0.746 |
| **T3 blend** | **+0.563** |
| **delta** | **-0.183** |
| paired bootstrap p05 | -0.597 |
| paired bootstrap p95 | +0.362 |
| **P2** | **✗ FAILS** |

