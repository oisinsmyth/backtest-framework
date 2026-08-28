# D254 — the wedge breakout on crypto

**Produced by** `scripts/run_wedge_crypto.py` · seed 0 · 1,000 null draws · 11.4s

`crypto_book_2018_raw.csv.gz` — 35 coins x 2,899 bars, 5.20 live years. k=3, arm ≤ 2.0 ATR, trigger ±2.0 ATR, hold 21. Armed on **12.43%** of live cells.


Universe CAGR -4.17%, 19 of 35 coins fell. Effective instruments **1.80**.


## X-2 — the anatomy, beside D249's ETF table. This is the load-bearing number.

| horizon | **crypto up** | **crypto down** | **crypto spread** | *ETF up* | *ETF down* | *ETF spread* |
|---:|---:|---:|---:|---:|---:|---:|
| 5 | +80.62% (3,490) | +81.40% (2,409) | **-0.78%** | *+6.47%* | *+14.55%* | *-8.08%* |
| 10 | +54.96% (3,490) | +32.28% (2,405) | **+22.67%** | *+6.89%* | *+9.05%* | *-2.16%* |
| 21 | -1.52% (3,490) | +18.70% (2,370) | **-20.22%** | *+8.33%* | *+15.29%* | *-6.96%* |
| 42 | -36.39% (3,488) | +7.91% (2,316) | **-44.30%** | *+9.47%* | *+18.31%* | *-8.84%* |
| 63 | -43.95% (3,484) | +18.55% (2,273) | **-62.50%** | *+8.00%* | *+18.04%* | *-10.04%* |

**Crypto spread positive at 1 of 5 horizons.** ETF spread is negative at all five. **X-2 FALSIFIED.**


## Cells

| cell | exposure | CAGR | excess Sharpe | max DD | entries | min/sym | H (Sharpe/money) | V | E | **success** |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **U_long** | 12.7% | +10.60% | +0.668 | -31.52% | 402 | 5 | 73.6th / 91.3th | yes | no | no |
| **D_long** | 10.3% | +9.47% | +0.686 | -21.57% | 326 | 3 | 64.2th / 86.0th | yes | no | no |
| **D_short** | 10.3% | -11.07% | -0.834 | -49.48% | 326 | 3 | 41.8th / 8.7th | no | no | no |

## R10 — concurrency

| cell | mean | max | *rotated max* | sd ratio |
|---|---:|---:|---:|---:|
| U_long | 4.4 | **29** of 35 | *11* | 3.02x |
| D_long | 3.6 | **26** of 35 | *10* | 2.44x |
| D_short | 3.6 | **26** of 35 | *9* | 2.88x |

## Model-A ruin — full per-name notional

| cell | worst adverse bar | | max survivable notional |
|---|---:|---|---:|
| U_long | -inf% | ADA-USD 2020-10-15 | — |
| D_long | -inf% | ADA-USD 2020-10-15 | — |
| D_short | +102.4% | BTG-USD 2025-12-09 | **RUINED** |

## Verdict

**NO CELL CLEARS BOTH H AND V. Per D254's stop this is CLOSED — no parameter sweep, no second arming threshold, no move to the 63-name universe. The anatomy's sign stands as a mechanism finding regardless.**

