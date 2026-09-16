# D236 — portfolio-level risk controls

**STAGE 1 — SCREEN. Not a verdict.** Holdout and forward window untouched.

*seed 0, 400 overlay-null replications per cell, 11.7s. 57 symbols, 2018-12-21 to 2024-12-30, 1,515 live bars.*

## Baseline

| book | excess Sharpe | CAGR | max DD | **CAGR/\|DD\|** | vol | exposure |
|---|---:|---:|---:|---:|---:|---:|
| **recovery — baseline** | +0.746 | 5.43% | -10.30% | **0.527** | 6.1% | 18.9% |
| buy and hold | +0.235 | 8.42% | -34.60% | **0.243** | 17.7% | 100.0% |

## The six controls

| cell | binds | exposure | max DD | CAGR/\|DD\| | Δ | excess Sharpe | √f | K1 | K2 | N |
|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|
| **C@30%** | 19.3% | 13.7% | -6.03% | 0.420 | -0.107 | +0.609 | +0.637 | ✓ | — | — |
| **C@40%** | 14.1% | 15.4% | -7.19% | 0.469 | -0.058 | +0.694 | +0.675 | ✓ | — | — |
| **C@50%** | 10.4% | 16.6% | -8.07% | 0.511 | -0.016 | +0.746 | +0.700 | ✓ | — | — |
| **R SMA50>200** | 31.7% | 8.4% | -2.87% | 0.288 | -0.239 | +0.267 | +0.497 | ✓ | — | — |
| **D@5%** | 72.9% | 5.5% | -7.24% | 0.286 | -0.241 | +0.446 | +0.402 | ✓ | — | — |
| **D@8%** | 40.3% | 10.6% | -9.93% | 0.310 | -0.216 | +0.516 | +0.558 | ✓ | — | — |

## N — the overlay null (R7)

Keep the base book; hold back the **same amount at random bars**, matched on how often the control really binds. If a control does no better than that, its *timing* carries nothing.

| cell | real excess Sharpe | null p50 | null p95 | clears |
|---|---:|---:|---:|:--:|
| C@30% | **+0.609** | +0.703 | +0.840 | — |
| C@40% | **+0.694** | +0.721 | +0.845 | — |
| C@50% | **+0.746** | +0.723 | +0.815 | — |
| R SMA50>200 | **+0.267** | +0.655 | +0.868 | — |
| D@5% | **+0.446** | +0.695 | +0.915 | — |
| D@8% | **+0.516** | +0.700 | +0.879 | — |

