# D257 — the cross-sectional trend arm, on a name holdout

**Produced by** `scripts/run_xsec_trend_arm.py` · split seed 20260829 · 400 null draws · 105s

1,573 names, 2010-01-04 → 2026-08-26, 5 bp/side on two legs.


**Halving the universe halves breadth**, so a perfectly reproducing signal scores about **0.43** per cohort, not 0.607. IC is the breadth-independent comparable.


| | names | Sharpe | ann. return | ann. vol | gross expo | **IC** | corr. t | residual breadth | breakeven/side | H (Sharpe/money) | V |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| **A_screen** | 786 | +0.396 | +0.31% | 0.79% | 13.8% | **+0.0032** | +0.7 | 67.0 | 32 bp | 64.2th / 89.8th | y |
| **B_holdout** | 787 | +0.564 | +0.42% | 0.75% | 13.7% | **-0.0005** | -0.1 | 69.4 | 41 bp | 88.2th / 99.0th | y |

**Hurdle G** — same sign: False; ratio B/A = 0.15; **FAILS**


## Cohort B against the committed ETF book

| | |
|---|---:|
| common dates | 3,222 |
| **rho** | **-0.124** (p05 -0.189, p95 -0.061) |
| SR ETF book | +0.831 |
| SR arm (cohort B) | +0.643 |
| bar `rho x SR_A` | -0.103 |
| **diversification** | **ADDS** |

| weight on the arm | combined Sharpe |
|---:|---:|
| 0% | +0.831 |
| 25% | +1.031 |
| 50% | +1.113 |
| 75% | +0.907 |
| 100% | +0.643 |

## Verdict

**COHORT B DOES NOT CLEAR H, G AND V TOGETHER. Per D257's stop this is CLOSED — no re-split, no second seed, no alternative neutralisation, no fallback to a time holdout.**

