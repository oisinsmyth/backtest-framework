# D241 — the combined book, and first-come-first-served capital

**STAGE 1 — A SCREEN, NOT A VERDICT.** screen (mined 57) -- the holdout and forward window are untouched

*seed 0, 2.6s. 57 ETFs x 1,515 live bars, 2018-12-21 .. 2024-12-30. Positions are 1/57 of total capital.*

## The books

| | total | reserve S1/A2 | shared | exposure | excess Sharpe | CAGR | **deployable** | vol | max DD | Calmar |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **C0** | 100% | 0% / 0% | 100% | 30.7% | **+0.924** | 7.71% | **10.68%** | 6.7% | -10.41% | 0.741 |
| **C1** | 50% | 0% / 0% | 50% | 27.6% | **+0.910** | 5.80% | **8.85%** | 5.0% | -7.64% | 0.759 |
| **C2** | 50% | 25% / 25% | 0% | 23.6% | **+0.804** | 4.00% | **7.17%** | 3.7% | -6.65% | 0.602 |
| **C3** | 50% | 15% / 15% | 20% | 26.0% | **+0.868** | 4.89% | **7.98%** | 4.3% | -7.09% | 0.690 |
| **C4** | 75% | 0% / 0% | 75% | 30.2% | **+0.959** | 7.57% | **10.55%** | 6.4% | -9.97% | 0.759 |
| *S1 alone* | — | — | — | *18.9%* | *+0.746* | *5.43%* | *8.83%* | *6.1%* | *-10.30%* | *0.527* |
| *A2 alone* | — | — | — | *13.0%* | *+0.822* | *2.52%* | *6.08%* | *2.4%* | *-1.93%* | *1.306* |
| *B&H* | — | — | — | *100.0%* | *+0.235* | *8.42%* | *8.42%* | *17.7%* | *-34.60%* | *0.243* |

**The closed form D240 reported predicted 1.032** at ρ = +0.1586. C0, the book actually built, scores **+0.924**.

## M1 and M2 — the paired bootstrap D240 could not do

| | delta | p05 | p95 | excludes 0 | verdict |
|---|---:|---:|---:|:--:|:--:|
| **M1 — C0 vs S1 alone** | **+0.178** | -0.010 | +0.394 | ✗ | ✗ FAILS |
| **M2 — C0 vs A2 alone** | **+0.102** | -0.513 | +0.661 | ✗ | ✗ FAILS |

## M3 — does first-come-first-served beat a fixed split?

*C1 and C2 hold the same 50% of capital. The only difference is whether it is **shared** or **partitioned 25/25**.*

| | excess Sharpe |
|---|---:|
| C1 — shared, FCFS | +0.910 |
| C2 — fixed 25/25 | +0.804 |
| **difference** | **+0.107** |
| **M3** | **✓ CLEARS** |

## How the allocator behaved

| | binds on | exposure S1 | exposure A2 | entries denied S1 | denied A2 | max deployed | reversed-order Sharpe |
|---|---:|---:|---:|---:|---:|---:|---:|
| **C0** | 0.00% | 17.9% | 12.9% | 0.0% | 0.0% | 89.5% | +0.924 |
| **C1** | 17.76% | 14.9% | 12.7% | 72.4% | 41.9% | 49.1% | +0.952 |
| **C2** | 37.29% | 12.2% | 11.4% | 85.1% | 86.8% | 49.1% | +0.885 |
| **C3** | 25.15% | 13.5% | 12.5% | 80.4% | 62.6% | 49.1% | +0.931 |
| **C4** | 5.54% | 17.4% | 12.9% | 29.3% | 5.0% | 73.7% | +0.945 |

*The reversed-order column is the arbitrariness diagnostic: entries are admitted in ascending symbol index, and this is what happens under the opposite order.*

## M4 — does any capped cell beat the unconstrained book?

| | excess Sharpe | vs C0 | beats C0 |
|---|---:|---:|:--:|
| **C1** | +0.910 | -0.014 | ✗ |
| **C2** | +0.804 | -0.120 | ✗ |
| **C3** | +0.868 | -0.056 | ✗ |
| **C4** | +0.959 | +0.035 | ✓ |

