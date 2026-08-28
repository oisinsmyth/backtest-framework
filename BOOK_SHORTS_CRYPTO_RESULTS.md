# D253 — the short sides of S1 and S2, on crypto

**Produced by** `scripts/run_book_shorts_crypto.py` · seed 0 · 1,000 null draws · 6.6s

`crypto_book_2018_raw.csv.gz` — **35 coins x 2,899 bars**, 5.20 live years from bar 1,000. PPY 365, fees 10 bp/side, borrow **10%/yr (assumed)**.


## The drift confound, measured before any cell is read

Equal-weighted universe CAGR **-4.17%**, median symbol **-9.12%**, **19 of 35 coins fell**.


**A short book on a falling universe earns by existing.** The rotation null holds the same exposure, turnover and holding periods on the wrong bars, so it earns that drift too. **Only the excess over the null is evidence** — which is what hurdle H reads.


`SHORT_ALL` — short everything, always — is reported below as the drift benchmark: **-58.90% CAGR**. A cell that does not clearly beat it has found nothing.


Effective independent instruments: **1.80** of 35. Pooled trade counts are not sample sizes.


## Cells

| cell | exposure | CAGR | excess Sharpe | vol | max DD | entries | min/sym | breakeven borrow |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **S1_short** | 25.4% | -10.12% | -0.395 | 25.2% | -57.92% | 1,121 | 17 | -25.6% |
| **S2_short** | 14.7% | -6.46% | -0.472 | 14.8% | -37.20% | 162 | 2 | -31.7% |
| **C_short** | 34.0% | -13.55% | -0.463 | 29.2% | -66.32% | 1,002 | 15 | -26.1% |
| *SHORT_ALL* | 100.0% | -58.90% | -0.882 | 77.6% | -99.23% | 35 | 1 | -44.6% |
| *B&H* | 100.0% | +32.55% | +0.709 | 77.6% | -84.86% | 35 | 1 | — |

## Hurdle H — the matched-count rotation null, BOTH legs

| cell | Sharpe pct | money pct | clears H |
|---|---:|---:|:--:|
| S1_short | 98.7th | 95.8th | **YES** |
| S2_short | 86.3th | 79.6th | no |
| C_short | 99.3th | 98.5th | **YES** |

Best-of-three floor (D228), p95: **-0.329**.


## R10 — concurrency, actual against a per-symbol-rotated book

| cell | mean held | max | over ⅓ of universe | *rotated mean* | *rotated max* | *rotated over ⅓* | sd ratio |
|---|---:|---:|---:|---:|---:|---:|---:|
| S1_short | 8.9 | **35** of 35 | 30.5% | *8.9* | *16* | *14.2%* | 4.37x |
| S2_short | 5.1 | **23** of 35 | 18.2% | *5.1* | *13* | *0.9%* | 2.80x |
| C_short | 11.9 | **35** of 35 | 43.1% | *11.9* | *23* | *56.9%* | 3.92x |

## Verdict

**At least one cell clears H on both legs.**

