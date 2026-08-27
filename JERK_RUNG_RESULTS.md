# D229 — one more rung up the derivative ladder

*`scripts/run_jerk_rung.py`, seed 0, 1,000 bootstrap replications at block 21, 7.2s. 2018-12-21 to 2024-12-30, 1,515 live bars.*

## The three rungs, long-flat, no gate

| rung | Sharpe (price) | gross | excess @rf=4% | money | CAGR | max DD | exposure | turnover |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **I0 jerk** | +0.439 | +0.542 | +0.335 | +34.94% | 5.11% | -13.01% | 48.5% | 16,421 |
| I1 acceleration | +0.658 | +0.689 | +0.570 | +52.12% | 7.23% | -11.78% | 49.9% | 4,835 |
| I2 level | +0.129 | +0.139 | +0.011 | +14.34% | 2.25% | -13.40% | 54.6% | 1,458 |
| buy and hold | +0.333 | — | +0.235 | +62.59% | 8.42% | -34.81% | 100.0% | — |

## Hurdle A — the paired delta

| book | gate | I0−I1 | gross | excess | boot p05 | boot p95 | clears A |
|---|---|---:|---:|---:|---:|---:|:--:|
| long_flat | none | **-0.218** | -0.147 | -0.235 | -0.759 | +0.402 | FAIL |
| long_flat | 200ma | **+0.006** | +0.101 | -0.013 | -0.554 | +0.563 | FAIL |
| long_short | none | **-0.224** | -0.099 | -0.251 | -1.031 | +0.621 | FAIL |
| long_short | 200ma | **-0.152** | -0.076 | -0.174 | -0.712 | +0.391 | FAIL |

*Hurdle: point estimate ≥ +0.10 **and** bootstrap p05 > +0.10.*

## The ladder, for comparison with D218

| book | gate | I0−I1 | I1−I2 | I0−I2 |
|---|---|---:|---:|---:|
| long_flat | none | -0.218 | +0.529 | +0.310 |
| long_flat | 200ma | +0.006 | +0.096 | +0.102 |
| long_short | none | -0.224 | +0.628 | +0.404 |
| long_short | 200ma | -0.152 | +0.366 | +0.213 |

## D218's headline, through the bootstrap leg it stated and never ran

| book | gate | I1−I2 | boot p05 | clears the hurdle D218 wrote |
|---|---|---:|---:|:--:|
| long_flat | none | **+0.529** | -0.055 | **FAIL** |
| long_flat | 200ma | **+0.096** | -0.322 | **FAIL** |
| long_short | none | **+0.628** | -0.133 | **FAIL** |
| long_short | 200ma | **+0.366** | -0.076 | **FAIL** |

**Primary cell `I0_jerk|long_flat|none` — A: FAILS, D: FAILS, E: CLEARS.**

## Ledger

| count | N | floor |
|---|---:|---:|
| fresh | 4 | +0.365 |
| + inherited | 66 | — |
| verdict count | 45,807 | +1.465 |

