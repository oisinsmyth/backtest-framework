# D256 — the short arms and the take-profit overlay, on single names

**Produced by** `scripts/run_book_single_names.py` · seed 0 · 400 null draws · 438s

`us_shorts_daily_raw.csv.gz` — **1,573 names x 4,187 bars**, 2010-01-04 → 2026-08-26. Fees 5 bp/side, borrow 3%/yr assumed.


**Ragged panel**: equal weight over LIVE names, per-symbol warm-up, no forward fill.


## Part B first — reachability, the quantity D255 said should differ

| arm | trades | median max gain | reach +10% | **+20%** | +30% | *ETF +20% (D255)* |
|---|---:|---:|---:|---:|---:|---:|
| **S1** | 38,116 | +4.24% | 25.1% | 8.9% | 4.0% | *2.8%* |
| **S2** | 6,284 | +8.42% | 44.5% | 21.4% | 11.8% | *9.7%* |
| **C** | 41,289 | +4.85% | 28.8% | 11.2% | 5.3% | *4.2%* |

### Take-profit cells

| cell | cuts | exposure | CAGR | excess Sharpe | vs base |
|---|---:|---:|---:|---:|---:|
| S1:TP10 | 9,125 | 11.2% | +1.69% | +0.416 | -0.011 |
| S1:TP20 | 3,166 | 12.8% | +2.11% | +0.423 | -0.005 |
| S1:TP30 | 1,384 | 13.3% | +2.24% | +0.420 | -0.007 |
| S2:TP10 | 2,767 | 6.0% | +0.88% | +0.456 | -0.060 |
| S2:TP20 | 1,333 | 7.4% | +1.14% | +0.486 | -0.030 |
| S2:TP30 | 724 | 7.9% | +1.27% | +0.510 | -0.006 |
| C:TP10 | 11,425 | 16.5% | +2.47% | +0.498 | -0.042 |
| C:TP20 | 4,375 | 19.6% | +3.15% | +0.519 | -0.021 |
| C:TP30 | 2,060 | 20.5% | +3.41% | +0.527 | -0.013 |

## Part A — the short arms

| cell | exposure | CAGR | **exposure x edge** | excess Sharpe | max DD | min entries/sym | H (Sharpe/money) | V | E | **success** |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **S1_short** | 13.6% | -3.03% | -2.97% | -0.725 | -43.17% | 1 | 100.0th / 0.0th | n | n | no |
| **S2_short** | 7.7% | -1.13% | -1.11% | -0.519 | -17.92% | 1 | 100.0th / 79.0th | n | n | no |
| **C_short** | 18.2% | -3.54% | -3.44% | -0.715 | -48.15% | 1 | 100.0th / 0.0th | n | n | no |

### Long arms, for reference

| arm | exposure | CAGR | excess Sharpe | max DD |
|---|---:|---:|---:|---:|
| S1 | 13.6% | +2.44% | +0.427 | -9.99% |
| S2 | 8.4% | +1.40% | +0.516 | -5.00% |
| C | 21.3% | +3.73% | +0.540 | -10.15% |

## Z-e — R10 concurrency, the mechanism test

| book | mean held | max | share of live (mean/max) | *rotated max* | **sd ratio** |
|---|---:|---:|---:|---:|---:|
| S1 | 138.3 | 736 | 13.6% / 76.6% | *185* | **9.17x** |
| S2 | 85.2 | 594 | 8.4% / 62.0% | *114* | **8.94x** |
| C | 216.5 | 746 | 21.3% / 77.6% | *265* | **8.59x** |
| S1_short | 138.3 | 736 | 13.6% / 76.6% | *185* | **9.17x** |
| S2_short | 78.4 | 305 | 7.7% / 31.7% | *105* | **6.89x** |
| C_short | 184.9 | 743 | 18.2% / 77.3% | *235* | **8.48x** |

*Prior clustering ratios: ETF wedge 3.02x, crypto S1_short 4.37x, gap screen 4.08x. Z-e predicted under 2.5x here.*

