# D243 — the book on extended history

**THE FIRST TIME-INDEPENDENT TEST THIS PROGRAMME HAS HAD.**

*seed 0, 1,000 rotations, 22.3s. 57 ETFs x 4,222 bars, 2009-11-11 .. 2026-08-26; 3,222 live from 2013-11-01. Only the book — no variants, no stop, zero fresh looks.*

**The extended live window CONTAINS the training window**, so it is not a clean holdout. It splits into **NEW** (1,293 bars, never seen), **TRAIN** (1,516) and **FORWARD** (413). Every previous holdout was an *instrument* holdout at ρ = +0.978 between universes. **The verdict lives in NEW.**

## The verdict — the never-seen window

| | NEW | *TRAIN* | B&H on NEW | Δ vs B&H | floor | rot p95 | pctile | V1 | V2 | V3 | **all** |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|
| **S1** | **-0.123** | *+0.752* | -0.149 | **+0.025** | +0.128 | +0.010 | **80.6th** | ✗ | ✗ | ✗ | **✗** |
| **S2** | **+0.248** | *+0.521* | -0.149 | **+0.396** | +0.094 | +0.199 | **97.1th** | ✓ | ✓ | ✓ | **✓** |

## Every period, side by side

| | NEW | TRAIN | FORWARD | FULL |
|---|---:|---:|---:|---:|
| **S1** | -0.123 | +0.752 | +0.896 | +0.478 |
| **S2** | +0.248 | +0.521 | +1.504 | +0.511 |
| **C** | +0.023 | +0.839 | +1.528 | +0.620 |
| **BH** | -0.149 | +0.249 | +1.235 | +0.242 |

*Exposure and drawdown by period:*

| | NEW expo | NEW maxDD | TRAIN maxDD | FULL maxDD |
|---|---:|---:|---:|---:|
| **S1** | 18.2% | -8.38% | -10.28% | -10.28% |
| **S2** | 13.3% | -4.83% | -5.83% | -5.83% |
| **C** | 30.7% | -8.44% | -10.40% | -10.40% |

## V4 — the intervals, on 12.8 years instead of 6

*The whole point of doubling the data. Contaminated by containing TRAIN, so reported for **width**, not as a verdict.*

| | excess Sharpe | p05 | p95 | **excludes 0** | Δ vs B&H | p05 | excludes 0 |
|---|---:|---:|---:|:--:|---:|---:|:--:|
| **S1** | +0.478 | -0.036 | +0.917 | **✗** | +0.236 | -0.198 | ✗ |
| **S2** | +0.511 | +0.066 | +0.989 | **✓** | +0.269 | -0.134 | ✗ |
| **C** | +0.620 | +0.126 | +1.052 | **✓** | +0.378 | +0.036 | ✓ |

**The combination against S1 alone:** +0.142, p05 -0.052, p95 +0.347 — **contains zero**.

## The book, in full

| | exposure | excess Sharpe | CAGR | deployable | max DD | Calmar | E |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **S1** | 18.2% | +0.478 | 3.11% | **6.47%** | -10.28% | 0.303 | ✗ (20) |
| **S2** | 13.3% | +0.511 | 1.85% | **5.37%** | -5.83% | 0.318 | ✗ (5) |
| **C** | 30.5% | +0.620 | 4.83% | **7.73%** | -10.40% | 0.465 | ✗ (24) |
| *B&H* | *100.0%* | *+0.242* | *7.84%* | *7.84%* | *-34.55%* | *0.227* | — |

**ρ between S1 and S2 over 12.8 years: `+0.1233`** (mined +0.159, holdout +0.175).

## The reading, as declared in advance

> **S2 SURVIVES A NEW ERA; S1 DOES NOT. S1 is amended in BOOK.md in writing -- and D239's mechanism predicted exactly this.**

