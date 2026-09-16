# D238 — the short-side mirror of the recovery rule

**STAGE 1 — A SCREEN, NOT A VERDICT.** screen (mined 57) -- the holdout and forward window are untouched

*seed 0, 1,000 rotations, 25.7s. 57 ETFs x 1,515 live bars, 2018-12-21 .. 2024-12-30. rf 4.0%/yr on long notional, borrow 1.0%/yr on short.*

## The channel is not symmetric

| where `md_L` sits | share of live bars |
|---|---:|
| **above** the channel — `md_L > 0` | **55.37%** |
| **inside** — `md_L = 0`, the dead zone | 11.69% |
| **below** the channel — `md_L < 0` | 32.95% |

S1 and M1 fire simultaneously on **0** cells — they are disjoint, so M3 needs no weighting choice.

## The four books

| | rule | long | short | excess Sharpe | CAGR | vol | max DD | total return | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **S1** | `hist>0 & md<=0` (+1) | 18.9% | 0.0% | **+0.746** | 5.43% | 6.1% | -10.30% | +37.39% | ✗ |
| **M1** | `hist<0 & md>=0` (−1) | 0.0% | 29.5% | **-0.407** | -2.09% | 5.9% | -19.28% | -11.90% | ✗ |
| **M2** | `hist<0 & md>0` (−1) | 0.0% | 24.9% | **-0.450** | -1.96% | 4.9% | -16.93% | -11.20% | ✗ |
| **M3** | S1 − M1 | 18.9% | 29.5% | **+0.262** | 3.23% | 8.2% | -21.87% | +21.04% | ✓ |
| **M4** | `hist<0` alone (−1) *post-hoc* | 0.0% | 47.8% | **-0.458** | -5.43% | 13.2% | -43.95% | -28.49% | ✓ |
| B&H | always long | 100.0% | 0.0% | +0.235 | 8.42% | 17.7% | -34.60% | +62.59% | — |

## W1 — the rotation null, which carries the verdict

*Same exposure, same turnover, same holding periods, wrong bars — **and therefore the same drift drag.** That is why this and not profitability is the primary.*

| | actual | null p50 | null p95 | null sd | **percentile** | W1 |
|---|---:|---:|---:|---:|---:|:--:|
| **M1** | **-0.407** | -0.970 | -0.728 | 0.150 | **100.0th** | ✓ |
| **M2** | **-0.450** | -0.971 | -0.723 | 0.162 | **99.9th** | ✓ |
| **M3** | **+0.262** | -1.570 | -0.878 | 0.427 | **100.0th** | ✓ |
| **M4** | **-0.458** | -0.958 | -0.767 | 0.112 | **100.0th** | ✓ |

**Every cell clears, which under R7's corollary is a tell rather than a triumph** — so the same null was re-run on money and on volatility, because Sharpe is `mean/sd` and a *negative*-mean book can beat this hurdle purely by being exposed in noisy weather. Money cannot be inflated that way.

| | money | null p50 | **percentile** | vol | null vol p50 | **ratio** |
|---|---:|---:|---:|---:|---:|---:|
| **M1** | **-11.90%** | -25.99% | **100.0th** | 5.90% | 5.47% | 1.079x |
| **M2** | **-11.20%** | -22.68% | **99.9th** | 4.94% | 4.64% | 1.064x |
| **M3** | **+21.04%** | -21.04% | **100.0th** | 8.19% | 3.16% | 2.593x |
| **M4** | **-28.49%** | -36.92% | **99.1th** | 13.23% | 8.50% | 1.556x |

## What a held bar is actually worth

*Mean total return of the bars each condition selects, annualised. **This is the measurement that decides the reading**, because a short needs bars that FALL and a rotation null can only establish bars that UNDERPERFORM.*

| condition | bars held | annualised return of those bars |
|---|---:|---:|
| `hist>0 & md<=0  (S1)` | 16,303 | **+33.22%** |
| `hist<0 & md>=0  (M1)` | 25,444 | **+0.85%** |
| `hist<0 & md<0` | 15,834 | **+3.28%** |
| `hist<0 alone    (M4)` | 41,278 | **+1.78%** |
| `all live bars` | 86,355 | **+8.42%** |

## W2 — standalone viability, and the breakeven borrow rate

| | excess Sharpe | W2 | √f vs S1 | breakeven borrow |
|---|---:|:--:|---:|---:|
| **M1** | -0.407 | ✗ | 1.249x | -6.90% |
| **M2** | -0.450 | ✗ | 1.149x | -7.61% |
| **M3** | +0.262 | ✓ | 1.600x | +8.62% |
| **M4** | -0.458 | ✗ | 1.591x | -11.01% |

*A **negative** breakeven means the arm loses with free stock loan — the borrow charge is not what killed it.*

## W3 — does the combined book beat S1 alone?

| | excess Sharpe |
|---|---:|
| S1 alone | +0.746 |
| **M3 combined** | **+0.262** |
| **delta** | **-0.484** |
| paired bootstrap p05 | -1.043 |
| paired bootstrap p95 | -0.028 |
| **W3** | **✗ FAILS** |

**Correlation of the S1 and M1 daily excess returns: `-0.0687`.**

