# D251 pre-screen — cross-sectional dollar-neutral ranking scores

**PRE-SCREEN on the mined 57 -- D245's never-seen cohort is UNTOUCHED**

*seed 0, 5.6s. 57 ETFs x 3,222 live bars, 2013-11-01 .. 2026-08-26. Costs 1.93 bp/side median, borrow 1.0%/yr on short notional.*

**The cost wall.** One round trip per day per leg is **-8.90%/yr** on that leg's notional. A dollar-neutral book pays it **twice**, plus borrow.

**Breadth.** Equal-weight effective instruments **2.29** — BOOK.md's saturation-near-2 figure, reproduced. That estimator is degenerate on market-neutral residuals (they sum to zero across names, so the equal-weighted average is identically zero), so the eigenvalue participation ratio is reported instead: **3.61** raw against **11.55** once the common factor is removed. **Removing the factor is what buys the breadth back** — which is the argument for this family, now measured rather than asserted.

## RS21 — trailing 21-bar return minus the universe

*A priori direction, declared before the run: long **Q5**, short Q1.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +6.22% | +8.52% | +9.21% | +8.11% | +6.87% | +0.65% | **+0.65%** | 77% | 0.68% | 1.00% | **-1.02%** |
| 63 | +7.15% | +8.32% | +9.01% | +8.59% | +5.46% | -1.69% | **-1.69%** | 78% | 0.23% | 1.00% | **-2.92%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 34.9 — ratio **0.66x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.276** | +5.13% | **-17.72%** | *-8.90%* | **8.82 pts** | **-12.12%** |
| 63 | **+0.121** | +7.07% | **-16.32%** | *-8.24%* | **8.07 pts** | **-9.11%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | -0.92% | -1.11% | **-0.237** | -1.11% | -0.73% | -1.22% | 119% | **153** |
| 63 | -0.31% | -0.51% | **-0.092** | -0.79% | +0.17% | -0.65% | 214% | **51** |

## RS63 — trailing 63-bar return minus the universe

*A priori direction, declared before the run: long **Q5**, short Q1.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +7.27% | +8.94% | +8.81% | +8.51% | +5.35% | -1.93% | **-1.93%** | 46% | 0.41% | 1.00% | **-3.34%** |
| 63 | +8.02% | +8.62% | +8.50% | +7.60% | +5.73% | -2.29% | **-2.29%** | 77% | 0.23% | 1.00% | **-3.52%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 34.6 — ratio **0.66x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.234** | +5.93% | **-16.63%** | *-7.67%* | **8.96 pts** | **-10.42%** |
| 63 | **+0.034** | +7.05% | **-16.07%** | *-7.71%* | **8.36 pts** | **-8.89%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | -0.55% | -0.74% | **-0.139** | +0.12% | -1.21% | -0.64% | 176% | **153** |
| 63 | -0.25% | -0.44% | **-0.068** | +0.03% | -0.52% | -0.43% | 275% | **51** |

## RS252 — trailing 252-bar return minus the universe

*A priori direction, declared before the run: long **Q5**, short Q1.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +4.95% | +7.17% | +9.28% | +9.01% | +8.66% | +3.71% | **+3.71%** | 22% | 0.20% | 1.00% | **+2.52%** |
| 63 | +6.57% | +7.69% | +8.02% | +8.15% | +8.20% | +1.62% | **+1.62%** | 38% | 0.11% | 1.00% | **+0.51%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 33.8 — ratio **0.68x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.067** | +8.20% | **-14.72%** | *-5.59%* | **9.13 pts** | **-6.57%** |
| 63 | **+0.095** | +8.23% | **-15.13%** | *-6.33%* | **8.79 pts** | **-6.94%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +0.34% | +0.14% | **+0.083** | +0.71% | -0.03% | -0.07% | 260% | **153** |
| 63 | +0.25% | +0.06% | **+0.064** | +0.45% | +0.06% | -0.20% | 298% | **51** |

## RESMOM — residual momentum, beta from the PRIOR 252 bars

*A priori direction, declared before the run: long **Q5**, short Q1.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +5.54% | +7.23% | +7.75% | +7.88% | +10.76% | +5.21% | **+5.21%** | 29% | 0.26% | 1.00% | **+3.96%** |
| 63 | +5.91% | +7.51% | +7.38% | +7.29% | +10.71% | +4.80% | **+4.80%** | 50% | 0.15% | 1.00% | **+3.66%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 35.1 — ratio **0.66x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.139** | +9.12% | **-12.43%** | *-6.18%* | **6.25 pts** | **-3.48%** |
| 63 | **-0.165** | +9.61% | **-11.83%** | *-5.59%* | **6.24 pts** | **-2.41%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +0.60% | +0.41% | **+0.173** | -0.08% | +1.30% | +0.07% | 139% | **153** |
| 63 | +0.82% | +0.63% | **+0.237** | +0.45% | +1.19% | +0.40% | 101% | **51** |

## IVOL — trailing residual sd, annualised

*A priori direction, declared before the run: long **Q1**, short Q5.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +7.47% | +9.26% | +8.44% | +10.10% | +3.71% | -3.76% | **+3.76%** | 3% | 0.03% | 1.00% | **+2.73%** |
| 63 | +7.26% | +9.57% | +8.56% | +9.55% | +3.67% | -3.59% | **+3.59%** | 7% | 0.02% | 1.00% | **+2.57%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 28.5 — ratio **0.81x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.741** | +6.74% | **-18.62%** | *-3.75%* | **14.87 pts** | **-11.55%** |
| 63 | **-0.736** | +6.66% | **-18.73%** | *-4.02%* | **14.70 pts** | **-11.71%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | -0.80% | -1.00% | **-0.237** | +1.62% | -3.17% | -0.97% | 103% | **153** |
| 63 | -0.86% | -1.05% | **-0.255** | +1.47% | -3.12% | -0.99% | 97% | **51** |

## BETA — trailing slope on the equal-weighted universe

*A priori direction, declared before the run: long **Q1**, short Q5.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +2.48% | +8.79% | +9.10% | +11.32% | +7.78% | +5.31% | **-5.31%** | 5% | 0.04% | 1.00% | **-6.35%** |
| 63 | +2.91% | +7.54% | +8.95% | +11.11% | +8.54% | +5.63% | **-5.63%** | 12% | 0.03% | 1.00% | **-6.67%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 30.2 — ratio **0.76x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-1.309** | +2.08% | **-19.10%** | *-7.82%* | **11.28 pts** | **-15.96%** |
| 63 | **-1.274** | +2.62% | **-19.53%** | *-8.49%* | **11.05 pts** | **-15.88%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | -1.99% | -2.19% | **-0.432** | +1.15% | -5.04% | -2.27% | 60% | **153** |
| 63 | -1.99% | -2.18% | **-0.441** | +0.69% | -4.59% | -2.19% | 59% | **51** |

## MDL — S1's md_L / its own trailing sd

*A priori direction, declared before the run: long **Q1**, short Q5.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +6.88% | +6.98% | +7.63% | +11.17% | +6.38% | -0.50% | **+0.50%** | 44% | 0.39% | 1.00% | **-0.88%** |
| 63 | +7.93% | +7.52% | +7.06% | +9.47% | +6.63% | -1.30% | **+1.30%** | 73% | 0.21% | 1.00% | **+0.08%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 35.1 — ratio **0.66x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **+0.239** | +8.18% | **-12.42%** | *-6.23%* | **6.20 pts** | **-4.36%** |
| 63 | **+0.017** | +6.96% | **-14.54%** | *-7.91%* | **6.63 pts** | **-7.54%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +0.46% | +0.27% | **+0.126** | -0.41% | +1.34% | +0.83% | 204% | **153** |
| 63 | -0.19% | -0.39% | **-0.058** | -0.93% | +0.55% | +0.11% | 388% | **51** |

## HISTL — S1's hist_L / its own trailing sd

*A priori direction, declared before the run: long **Q5**, short Q1.*

| h | Q1 | Q2 | Q3 | Q4 | Q5 | Q5−Q1 | **edge** | turnover | cost | borrow | **NET** |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | +6.36% | +7.02% | +7.58% | +9.80% | +8.32% | +1.96% | **+1.96%** | 81% | 0.71% | 1.00% | **+0.25%** |
| 63 | +6.65% | +7.77% | +8.53% | +8.98% | +6.65% | -0.00% | **-0.00%** | 86% | 0.25% | 1.00% | **-1.25%** |

**R10.** Names held per bar **23.0** mean / **23** max against a rotated 23.0 / 36.0 — ratio **0.64x**. A fixed-count cross-sectional sort holds the same headcount every day, so it is *less* crowded than its own rotated null (rotation breaks the exact-count property and lets the extremes bunch). **The literal concurrency test cannot fail for this construction**, which is why the binding version of R10 here is net beta — the market bet a dollar-neutral book can still carry:

| h | net beta | long leg | **short leg** | short leg *priced naively* | **convexity cost** | **BOOK, at 100/100** |
|---:|---:|---:|---:|---:|---:|---:|
| 21 | **-0.273** | +6.09% | **-16.44%** | *-9.34%* | **7.10 pts** | **-10.10%** |
| 63 | **-0.146** | +9.42% | **-14.34%** | *-7.41%* | **6.93 pts** | **-5.07%** |

| h | portfolio-level CAGR | net | **Sharpe** | 1st half | 2nd half | ex-2020 | top-10 days | independent periods |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 21 | -0.80% | -1.00% | **-0.234** | -1.45% | -0.15% | -1.46% | 132% | **153** |
| 63 | +0.25% | +0.05% | **+0.076** | -0.11% | +0.61% | -0.22% | 352% | **51** |

## Verdict

**Bar: net > 2%/yr after two-leg costs and borrow.**

| reading | best cell | value |
|---|---|---:|
| spread table, net of cost and borrow | RESMOM @ 21 | **+3.96%/yr** |
| **the book actually built, house scorer, at 100/100** | RESMOM @ 63 | **-2.41%/yr** |
| the same book, portfolio-level aggregation | RESMOM @ 63 | **Sharpe +0.237** |

Cells clearing the bar **on the spread table**: RS252 @ 21, RESMOM @ 21, RESMOM @ 63, IVOL @ 21, IVOL @ 63. Cells whose BOOK clears it under the mandated scorer: **none — every one of 16 loses money.**

