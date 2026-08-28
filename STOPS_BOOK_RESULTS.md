# D255 — stops and targets on the book and on each arm

**Produced by** `scripts/run_stops_book.py` · seed 0 · 1,000 R7 null draws per cell · 227s

`universe_daily_extended_raw.csv.gz` — 57 ETFs x 4,222 bars, live from bar 1,000.


## Reachability — reported BEFORE any cell is scored

| arm | trades | median max gain | median max loss | reach +10% | +20% | +30% | −5% | −10% | −20% |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **S1** | 2,374 | +2.37% | -1.55% | 10.2% | 2.8% | 0.8% | 14.2% | 2.1% | 0.1% |
| **S2** | 393 | +5.89% | -3.19% | 27.2% | 9.7% | 5.3% | 33.3% | 11.7% | 2.8% |
| **C** | 2,553 | +2.84% | -1.78% | 13.6% | 4.2% | 1.5% | 17.7% | 3.7% | 0.5% |

**A level reached by few trades cannot move a book, whatever its conditional edge.**


## The 21 cells

Base arms: **S1** +0.478 (+3.11%), **S2** +0.511 (+1.85%), **C** +0.620 (+4.83%) · buy-and-hold +0.242


Best-of-21 floor (D228), p95: **+0.707**


| cell | cuts | cut rate | excess Sharpe | vs base | CAGR | max DD | H (Sharpe/money) | B | F | **success** |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| S1:SL05 | 220 | 9.3% | +0.449 | -0.029 | +2.60% | -9.49% | 0.2th / 0.0th | n | n | no |
| S1:SL10 | 27 | 1.1% | +0.486 | +0.007 | +3.09% | -10.29% | 75.5th / 14.5th | y | n | no |
| S1:SL20 | 1 | 0.0% | +0.480 | +0.001 | +3.12% | -10.28% | 97.6th / 97.9th | y | n | no |
| S1:TP10 | 229 | 9.6% | +0.382 | -0.096 | +2.25% | -10.59% | 0.0th / 0.0th | n | n | no |
| S1:TP20 | 60 | 2.5% | +0.494 | +0.016 | +3.08% | -10.21% | 86.6th / 10.9th | y | n | no |
| S1:TP30 | 10 | 0.4% | +0.483 | +0.004 | +3.08% | -10.17% | 82.0th / 3.7th | y | n | no |
| S1:TP20SL20 | 61 | 2.6% | +0.495 | +0.017 | +3.08% | -10.21% | 89.5th / 14.2th | y | n | no |
| S2:SL05 | 131 | 33.3% | +0.462 | -0.049 | +1.31% | -3.60% | 9.0th / 1.7th | n | n | no |
| S2:SL10 | 45 | 11.5% | +0.598 | +0.087 | +1.88% | -4.02% | 97.7th / 90.8th | y | n | no |
| S2:SL20 | 11 | 2.8% | +0.578 | +0.066 | +1.92% | -4.16% | 99.7th / 98.6th | y | n | no |
| S2:TP10 | 107 | 27.2% | +0.419 | -0.092 | +1.40% | -5.68% | 0.5th / 0.1th | n | n | no |
| S2:TP20 | 38 | 9.7% | +0.522 | +0.011 | +1.78% | -5.83% | 50.6th / 39.7th | y | n | no |
| S2:TP30 | 21 | 5.3% | +0.593 | +0.081 | +2.01% | -5.83% | 99.7th / 100.0th | y | n | no |
| S2:TP20SL20 | 48 | 12.2% | +0.594 | +0.082 | +1.85% | -3.92% | 96.9th / 80.8th | y | n | no |
| C:SL05 | 343 | 13.4% | +0.588 | -0.033 | +3.85% | -9.37% | 0.2th / 0.0th | n | n | no |
| C:SL10 | 73 | 2.9% | +0.668 | +0.048 | +4.88% | -10.32% | 99.9th / 80.1th | y | n | no |
| C:SL20 | 12 | 0.5% | +0.649 | +0.029 | +4.92% | -10.40% | 100.0th / 99.9th | y | n | no |
| C:TP10 | 335 | 13.1% | +0.494 | -0.126 | +3.51% | -10.57% | 0.0th / 0.0th | n | n | no |
| C:TP20 | 100 | 3.9% | +0.635 | +0.015 | +4.72% | -10.12% | 59.2th / 3.6th | y | n | no |
| C:TP30 | 31 | 1.2% | +0.658 | +0.037 | +4.97% | -9.98% | 100.0th / 100.0th | y | n | no |
| C:TP20SL20 | 111 | 4.3% | +0.665 | +0.045 | +4.81% | -10.12% | 99.5th / 33.8th | y | n | no |

## Verdict

**NO CELL CLEARS H, B AND F. Per D255's stop, stops and targets are CLOSED for this book — no further levels, no trailing variants, no per-symbol calibration, no ATR-scaled version. What is NOT closed is the same overlay on a single-name universe, where the pre-screen predicts the +20% bucket is populated.**

