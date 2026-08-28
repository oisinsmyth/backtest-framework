# D256 — the short arms and the take-profit overlay, on single names

**Produced by** `scripts/run_book_single_names.py` · seed 0 · 400 null draws · 445s

`us_shorts_daily_raw.csv.gz` — **1,580 names x 4,187 bars**, 2010-01-04 → 2026-08-26. Fees 5 bp/side, borrow 3%/yr assumed.


**Ragged panel**: equal weight over LIVE names, per-symbol warm-up, no forward fill.


## Part B first — reachability, the quantity D255 said should differ

| arm | trades | median max gain | reach +10% | **+20%** | +30% | *ETF +20% (D255)* |
|---|---:|---:|---:|---:|---:|---:|
| **S1** | 38,220 | +4.25% | 25.2% | 9.0% | 4.0% | *2.8%* |
| **S2** | 6,299 | +8.42% | 44.5% | 21.4% | 11.8% | *9.7%* |
| **C** | 41,402 | +4.85% | 28.8% | 11.2% | 5.4% | *4.2%* |

### Take-profit cells

| cell | cuts | exposure | CAGR | excess Sharpe | vs base |
|---|---:|---:|---:|---:|---:|
| S1:TP10 | 9,158 | 11.1% | +1.67% | +0.409 | -0.016 |
| S1:TP20 | 3,191 | 12.8% | +2.09% | +0.419 | -0.005 |
| S1:TP30 | 1,402 | 13.3% | +2.24% | +0.419 | -0.006 |
| S2:TP10 | 2,775 | 6.0% | +0.88% | +0.455 | -0.073 |
| S2:TP20 | 1,336 | 7.4% | +1.17% | +0.502 | -0.026 |
| S2:TP30 | 726 | 7.9% | +1.29% | +0.523 | -0.005 |
| C:TP10 | 11,463 | 16.5% | +2.44% | +0.491 | -0.051 |
| C:TP20 | 4,401 | 19.6% | +3.16% | +0.522 | -0.020 |
| C:TP30 | 2,080 | 20.5% | +3.42% | +0.531 | -0.011 |

## Part A — the short arms

| cell | exposure | CAGR | **exposure x edge** | excess Sharpe | max DD | min entries/sym | H (Sharpe/money) | V | E | **success** |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **S1_short** | 13.6% | -3.01% | -2.95% | -0.723 | -43.09% | 1 | 88.5th / 11.5th | n | n | no |
| **S2_short** | 7.7% | -1.13% | -1.11% | -0.519 | -17.94% | 1 | 90.2th / 87.2th | n | n | no |
| **C_short** | 18.1% | -3.52% | -3.43% | -0.714 | -48.08% | 1 | 83.5th / 17.0th | n | n | no |

### Long arms, for reference

| arm | exposure | CAGR | excess Sharpe | max DD |
|---|---:|---:|---:|---:|
| S1 | 13.6% | +2.42% | +0.425 | -10.10% |
| S2 | 8.4% | +1.43% | +0.528 | -4.98% |
| C | 21.3% | +3.74% | +0.542 | -10.26% |

## Z-e — R10 concurrency, the mechanism test

| book | mean held | max | share of live (mean/max) | *rotated max* | **sd ratio** |
|---|---:|---:|---:|---:|---:|
| S1 | 138.7 | 737 | 13.6% / 76.5% | *181* | **9.64x** |
| S2 | 85.4 | 595 | 8.4% / 62.0% | *113* | **8.85x** |
| C | 217.1 | 747 | 21.3% / 77.5% | *265* | **9.24x** |
| S1_short | 138.7 | 737 | 13.6% / 76.5% | *181* | **9.64x** |
| S2_short | 78.6 | 305 | 7.7% / 31.6% | *110* | **6.18x** |
| C_short | 185.4 | 744 | 18.1% / 77.2% | *237* | **8.41x** |

*Prior clustering ratios: ETF wedge 3.02x, crypto S1_short 4.37x, gap screen 4.08x. Z-e predicted under 2.5x here.*

