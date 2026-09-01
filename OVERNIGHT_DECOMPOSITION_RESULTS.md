# D259 — where the overnight drift accrues, and what the path does to it

**A MEASUREMENT. No rule is proposed, no cell is scored, no hurdle is claimed.**

*`index_extended_15m_raw`: 958,217 bars, 16,748 symbol-sessions, median 62 bars/session (regular hours alone would be 26), 2010-01 .. 2026-08. Decomposition on 16,648 session pairs, 2010-01-05 .. 2026-08-26.*

*Bad prints: 2,113 suspect bars (0.221%), 1,923 of them post-market. Worst raw lower wick **+908%**. Excluded from every price used below; see the fixture meta for the rule.*

## The boundaries are prints, not clock times

An extended-hours bar exists only where something traded, so keying on the clock selects on activity and then measures returns. The realised boundary times, median and 90th percentile of lateness:

| symbol | era | pairs | last post-market print | first pre-market print |
|---|---|---:|---|---|
| SPY | 2010-2019 | 2,495 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| SPY | 2020 | 251 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| SPY | 2021-2026 | 1,417 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| QQQ | 2010-2019 | 2,495 | 19:45 med, 19:45 at p10 | 04:00 med, 05:15 at p90 |
| QQQ | 2020 | 251 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| QQQ | 2021-2026 | 1,417 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| IWM | 2010-2019 | 2,495 | 19:45 med, 19:00 at p10 | 04:30 med, 07:00 at p90 |
| IWM | 2020 | 251 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| IWM | 2021-2026 | 1,417 | 19:45 med, 19:45 at p10 | 04:00 med, 04:00 at p90 |
| DIA | 2010-2019 | 2,491 | 19:45 med, 18:00 at p10 | 06:00 med, 08:00 at p90 |
| DIA | 2020 | 251 | 19:45 med, 19:45 at p10 | 04:00 med, 04:30 at p90 |
| DIA | 2021-2026 | 1,417 | 19:45 med, 19:45 at p10 | 04:00 med, 04:15 at p90 |

## The four windows

Annualised in log space against each symbol's own calendar span, then averaged equal-weighted across symbols — D247's frame. Share is of the **total overnight drift** (post + untraded + pre), so the three shares sum to 1.

**A share can exceed 100% or go negative, and where it does the boundary table above explains it.** DIA's first pre-market print in 2010-2019 lands at 06:00 median and 08:00 at the 90th percentile, so DIA's *untraded* window is absorbing 20:00->06:00 while its *pre-market* window is only 06:00->09:30. The windows are not the same clock hours for every symbol, and pooling them is the compromise this fixture's liquidity forces. **SPY and QQQ from 2020 on are the clean read**: both print 04:00 and 19:45 on essentially every session.

### Pooled, all four symbols

| era | pairs | window | annualised | ann. vol | share of overnight |
|---|---:|---|---:|---:|---:|
| ALL | 16,648 | 16:00 -> 20:00  post-market | **+1.70%** | 4.4% | 19.4% |
|  | 16,648 | 20:00 -> 04:00  **untraded** | **+5.88%** | 7.6% | 66.0% |
|  | 16,648 | 04:00 -> 09:30  pre-market | **+1.27%** | 7.7% | 14.6% |
|  | 16,648 | 09:30 -> 16:00  regular hours | **+3.12%** | 14.7% | — |
|  | 16,648 | *= overnight total* | **+9.04%** | 12.0% | 100.0% |
|  | 16,648 | *= close-to-close* | **+12.44%** | 19.1% | — |
| 2010-2019 | 9,976 | 16:00 -> 20:00  post-market | **+0.61%** | 3.3% | 7.5% |
|  | 9,976 | 20:00 -> 04:00  **untraded** | **+6.41%** | 6.3% | 75.7% |
|  | 9,976 | 04:00 -> 09:30  pre-market | **+1.39%** | 6.3% | 16.8% |
|  | 9,976 | 09:30 -> 16:00  regular hours | **+3.14%** | 13.0% | — |
|  | 9,976 | *= overnight total* | **+8.55%** | 9.6% | 100.0% |
|  | 9,976 | *= close-to-close* | **+11.96%** | 16.3% | — |
| 2020 | 1,004 | 16:00 -> 20:00  post-market | **+9.25%** | 9.8% | 51.1% |
|  | 1,004 | 20:00 -> 04:00  **untraded** | **+3.88%** | 17.5% | 22.0% |
|  | 1,004 | 04:00 -> 09:30  pre-market | **+4.77%** | 13.9% | 26.9% |
|  | 1,004 | 09:30 -> 16:00  regular hours | **+2.19%** | 22.0% | — |
|  | 1,004 | *= overnight total* | **+18.91%** | 27.0% | 100.0% |
|  | 1,004 | *= close-to-close* | **+21.52%** | 37.4% | — |
| 2021-2026 | 5,668 | 16:00 -> 20:00  post-market | **+2.34%** | 4.5% | 29.1% |
|  | 5,668 | 20:00 -> 04:00  **untraded** | **+5.32%** | 6.7% | 65.1% |
|  | 5,668 | 04:00 -> 09:30  pre-market | **+0.47%** | 8.4% | 5.8% |
|  | 5,668 | 09:30 -> 16:00  regular hours | **+3.25%** | 15.8% | — |
|  | 5,668 | *= overnight total* | **+8.28%** | 11.4% | 100.0% |
|  | 5,668 | *= close-to-close* | **+11.80%** | 19.0% | — |

### SPY

| era | pairs | window | annualised | ann. vol | share of overnight |
|---|---:|---|---:|---:|---:|
| ALL | 4,163 | 16:00 -> 20:00  post-market | **+1.45%** | 4.0% | 20.9% |
|  | 4,163 | 20:00 -> 04:00  **untraded** | **+3.33%** | 6.7% | 47.4% |
|  | 4,163 | 04:00 -> 09:30  pre-market | **+2.22%** | 7.1% | 31.7% |
|  | 4,163 | 09:30 -> 16:00  regular hours | **+4.68%** | 12.8% | — |
|  | 4,163 | *= overnight total* | **+7.16%** | 11.0% | 100.0% |
|  | 4,163 | *= close-to-close* | **+12.17%** | 17.2% | — |
| 2010-2019 | 2,495 | 16:00 -> 20:00  post-market | **+0.44%** | 3.0% | 6.8% |
|  | 2,495 | 20:00 -> 04:00  **untraded** | **+4.07%** | 5.5% | 62.7% |
|  | 2,495 | 04:00 -> 09:30  pre-market | **+1.96%** | 6.2% | 30.5% |
|  | 2,495 | 09:30 -> 16:00  regular hours | **+4.17%** | 11.4% | — |
|  | 2,495 | *= overnight total* | **+6.58%** | 9.0% | 100.0% |
|  | 2,495 | *= close-to-close* | **+11.02%** | 14.8% | — |
| 2020 | 251 | 16:00 -> 20:00  post-market | **+7.01%** | 9.3% | 67.8% |
|  | 251 | 20:00 -> 04:00  **untraded** | **+1.33%** | 15.9% | 13.2% |
|  | 251 | 04:00 -> 09:30  pre-market | **+1.92%** | 12.1% | 19.0% |
|  | 251 | 09:30 -> 16:00  regular hours | **+5.14%** | 19.8% | — |
|  | 251 | *= overnight total* | **+10.52%** | 25.6% | 100.0% |
|  | 251 | *= close-to-close* | **+16.20%** | 34.6% | — |
| 2021-2026 | 1,417 | 16:00 -> 20:00  post-market | **+2.31%** | 4.0% | 31.1% |
|  | 1,417 | 20:00 -> 04:00  **untraded** | **+2.40%** | 5.9% | 32.3% |
|  | 1,417 | 04:00 -> 09:30  pre-market | **+2.72%** | 7.4% | 36.6% |
|  | 1,417 | 09:30 -> 16:00  regular hours | **+5.52%** | 13.7% | — |
|  | 1,417 | *= overnight total* | **+7.62%** | 10.0% | 100.0% |
|  | 1,417 | *= close-to-close* | **+13.56%** | 16.5% | — |

### QQQ

| era | pairs | window | annualised | ann. vol | share of overnight |
|---|---:|---|---:|---:|---:|
| ALL | 4,163 | 16:00 -> 20:00  post-market | **+2.69%** | 5.2% | 23.7% |
|  | 4,163 | 20:00 -> 04:00  **untraded** | **+7.79%** | 7.7% | 66.9% |
|  | 4,163 | 04:00 -> 09:30  pre-market | **+1.06%** | 8.1% | 9.4% |
|  | 4,163 | 09:30 -> 16:00  regular hours | **+5.34%** | 16.3% | — |
|  | 4,163 | *= overnight total* | **+11.86%** | 12.7% | 100.0% |
|  | 4,163 | *= close-to-close* | **+17.83%** | 20.7% | — |
| 2010-2019 | 2,495 | 16:00 -> 20:00  post-market | **+1.36%** | 4.1% | 12.2% |
|  | 2,495 | 20:00 -> 04:00  **untraded** | **+6.56%** | 6.4% | 57.1% |
|  | 2,495 | 04:00 -> 09:30  pre-market | **+3.48%** | 6.8% | 30.7% |
|  | 2,495 | 09:30 -> 16:00  regular hours | **+4.20%** | 13.9% | — |
|  | 2,495 | *= overnight total* | **+11.77%** | 10.2% | 100.0% |
|  | 2,495 | *= close-to-close* | **+16.47%** | 17.2% | — |
| 2020 | 251 | 16:00 -> 20:00  post-market | **+13.25%** | 9.7% | 57.4% |
|  | 251 | 20:00 -> 04:00  **untraded** | **+14.30%** | 17.0% | 61.7% |
|  | 251 | 04:00 -> 09:30  pre-market | **-4.06%** | 12.0% | -19.1% |
|  | 251 | 09:30 -> 16:00  regular hours | **+18.94%** | 22.8% | — |
|  | 251 | *= overnight total* | **+24.20%** | 25.1% | 100.0% |
|  | 251 | *= close-to-close* | **+47.71%** | 36.5% | — |
| 2021-2026 | 1,417 | 16:00 -> 20:00  post-market | **+3.29%** | 5.8% | 34.0% |
|  | 1,417 | 20:00 -> 04:00  **untraded** | **+8.88%** | 7.3% | 89.3% |
|  | 1,417 | 04:00 -> 09:30  pre-market | **-2.19%** | 9.3% | -23.3% |
|  | 1,417 | 09:30 -> 16:00  regular hours | **+5.12%** | 18.5% | — |
|  | 1,417 | *= overnight total* | **+10.00%** | 13.3% | 100.0% |
|  | 1,417 | *= close-to-close* | **+15.63%** | 22.5% | — |

### IWM

| era | pairs | window | annualised | ann. vol | share of overnight |
|---|---:|---|---:|---:|---:|
| ALL | 4,163 | 16:00 -> 20:00  post-market | **+1.20%** | 4.8% | 11.0% |
|  | 4,163 | 20:00 -> 04:00  **untraded** | **+7.40%** | 8.7% | 65.6% |
|  | 4,163 | 04:00 -> 09:30  pre-market | **+2.59%** | 9.1% | 23.5% |
|  | 4,163 | 09:30 -> 16:00  regular hours | **-1.60%** | 17.6% | — |
|  | 4,163 | *= overnight total* | **+11.50%** | 13.5% | 100.0% |
|  | 4,163 | *= close-to-close* | **+9.71%** | 22.3% | — |
| 2010-2019 | 2,495 | 16:00 -> 20:00  post-market | **+0.41%** | 3.4% | 4.4% |
|  | 2,495 | 20:00 -> 04:00  **untraded** | **+7.26%** | 7.1% | 76.4% |
|  | 2,495 | 04:00 -> 09:30  pre-market | **+1.77%** | 7.0% | 19.2% |
|  | 2,495 | 09:30 -> 16:00  regular hours | **+0.36%** | 16.0% | — |
|  | 2,495 | *= overnight total* | **+9.61%** | 10.4% | 100.0% |
|  | 2,495 | *= close-to-close* | **+10.00%** | 19.3% | — |
| 2020 | 251 | 16:00 -> 20:00  post-market | **+4.22%** | 11.1% | 15.9% |
|  | 251 | 20:00 -> 04:00  **untraded** | **+4.77%** | 19.3% | 17.9% |
|  | 251 | 04:00 -> 09:30  pre-market | **+18.85%** | 17.9% | 66.3% |
|  | 251 | 09:30 -> 16:00  regular hours | **-8.74%** | 24.5% | — |
|  | 251 | *= overnight total* | **+29.78%** | 30.8% | 100.0% |
|  | 251 | *= close-to-close* | **+18.44%** | 41.3% | — |
| 2021-2026 | 1,417 | 16:00 -> 20:00  post-market | **+2.09%** | 5.1% | 18.4% |
|  | 1,417 | 20:00 -> 04:00  **untraded** | **+8.14%** | 8.3% | 69.4% |
|  | 1,417 | 04:00 -> 09:30  pre-market | **+1.38%** | 10.2% | 12.2% |
|  | 1,417 | 09:30 -> 16:00  regular hours | **-3.72%** | 18.8% | — |
|  | 1,417 | *= overnight total* | **+11.92%** | 13.5% | 100.0% |
|  | 1,417 | *= close-to-close* | **+7.76%** | 22.5% | — |

### DIA

| era | pairs | window | annualised | ann. vol | share of overnight |
|---|---:|---|---:|---:|---:|
| ALL | 4,159 | 16:00 -> 20:00  post-market | **+1.44%** | 3.6% | 25.5% |
|  | 4,159 | 20:00 -> 04:00  **untraded** | **+5.05%** | 7.1% | 87.7% |
|  | 4,159 | 04:00 -> 09:30  pre-market | **-0.74%** | 6.6% | -13.2% |
|  | 4,159 | 09:30 -> 16:00  regular hours | **+4.21%** | 12.0% | — |
|  | 4,159 | *= overnight total* | **+5.78%** | 10.6% | 100.0% |
|  | 4,159 | *= close-to-close* | **+10.24%** | 16.4% | — |
| 2010-2019 | 2,491 | 16:00 -> 20:00  post-market | **+0.25%** | 2.8% | 4.1% |
|  | 2,491 | 20:00 -> 04:00  **untraded** | **+7.77%** | 6.1% | 122.1% |
|  | 2,491 | 04:00 -> 09:30  pre-market | **-1.59%** | 5.3% | -26.2% |
|  | 2,491 | 09:30 -> 16:00  regular hours | **+3.90%** | 10.7% | — |
|  | 2,491 | *= overnight total* | **+6.32%** | 8.7% | 100.0% |
|  | 2,491 | *= close-to-close* | **+10.46%** | 13.9% | — |
| 2020 | 251 | 16:00 -> 20:00  post-market | **+12.79%** | 9.3% | 104.3% |
|  | 251 | 20:00 -> 04:00  **untraded** | **-4.03%** | 17.7% | -35.6% |
|  | 251 | 04:00 -> 09:30  pre-market | **+3.68%** | 13.8% | 31.3% |
|  | 251 | 09:30 -> 16:00  regular hours | **-4.43%** | 21.0% | — |
|  | 251 | *= overnight total* | **+12.23%** | 26.3% | 100.0% |
|  | 251 | *= close-to-close* | **+7.26%** | 37.0% | — |
| 2021-2026 | 1,417 | 16:00 -> 20:00  post-market | **+1.67%** | 3.1% | 44.7% |
|  | 1,417 | 20:00 -> 04:00  **untraded** | **+2.05%** | 5.1% | 54.8% |
|  | 1,417 | 04:00 -> 09:30  pre-market | **+0.02%** | 6.8% | 0.4% |
|  | 1,417 | 09:30 -> 16:00  regular hours | **+6.39%** | 12.1% | — |
|  | 1,417 | *= overnight total* | **+3.77%** | 8.8% | 100.0% |
|  | 1,417 | *= close-to-close* | **+10.40%** | 14.5% | — |

### The same decomposition on the LITERAL clock

Restricted to pairs whose boundaries are an actual 19:45 bar and an actual 04:00 bar — the windows exactly as named, at the cost of a **liquidity-conditioned subsample**: it keeps 99% of SPY's recent sessions and 22% of DIA's early ones. Reported because the two readings differ, and the difference is the finding.

| symbol | era | pairs | kept | post-market | **untraded** | pre-market | regular |
|---|---|---:|---:|---:|---:|---:|---:|
| SPY | ALL | 3,937 | 95% | +1.38% (19%) | **+3.24% (44%)** | +2.65% (37%) | +5.40% |
|  | 2010-2019 | 2,278 | 91% | +0.32% (5%) | **+3.86% (56%)** | +2.72% (40%) | +5.48% |
|  | 2020 | 251 | 100% | +7.01% (68%) | **+1.33% (13%)** | +1.92% (19%) | +5.14% |
|  | 2021-2026 | 1,408 | 99% | +2.29% (31%) | **+2.49% (33%)** | +2.66% (36%) | +5.33% |
| QQQ | ALL | 3,278 | 79% | +2.19% (23%) | **+6.62% (68%)** | +0.89% (9%) | +3.21% |
|  | 2010-2019 | 1,620 | 65% | +0.54% (7%) | **+4.56% (54%)** | +3.28% (39%) | +1.14% |
|  | 2020 | 251 | 100% | +13.25% (57%) | **+14.30% (62%)** | -4.06% (-19%) | +18.94% |
|  | 2021-2026 | 1,407 | 99% | +3.29% (34%) | **+9.02% (91%)** | -2.33% (-25%) | +4.32% |
| IWM | ALL | 2,471 | 59% | +0.53% (7%) | **+3.77% (47%)** | +3.69% (46%) | +0.41% |
|  | 2010-2019 | 842 | 34% | -0.41% (-10%) | **+0.80% (20%)** | +3.68% (90%) | +2.78% |
|  | 2020 | 229 | 91% | +4.48% (17%) | **+7.25% (26%)** | +16.37% (57%) | -6.67% |
|  | 2021-2026 | 1,400 | 99% | +1.45% (13%) | **+8.41% (72%)** | +1.64% (15%) | -2.23% |
| DIA | ALL | 1,732 | 42% | +1.19% (42%) | **+0.66% (23%)** | +0.98% (35%) | +2.84% |
|  | 2010-2019 | 353 | 14% | +0.13% (23%) | **+0.34% (60%)** | +0.10% (17%) | +1.93% |
|  | 2020 | 191 | 76% | +10.10% (78%) | **-4.26% (-35%)** | +7.25% (57%) | -1.51% |
|  | 2021-2026 | 1,188 | 84% | +1.51% (30%) | **+2.13% (42%)** | +1.43% (28%) | +5.25% |

**Read SPY 2021-2026 and QQQ 2021-2026 first.** Those are the two cells where the anchor coverage is essentially 100%, so the windows mean what they say and nothing has been selected on. Everything else carries a coverage discount.

## The path — a long opened at 18:00 ET, held to 16:00 ET the next day

The MyFundedFutures window. Entry is the 18:00 print (or the standing price at 18:00 where the 18:00 slot did not trade); exit is the 16:00 close. **Friday->Monday pairs are excluded** — Globex is shut on Friday evening, and the Sunday-evening hold that would replace it has no equity bars at all. Monday exits are therefore absent from this table, and Monday's overnight is the one most likely to carry weekend news.

**Trailing drawdown is measured on open equity with the peak including the current bar's high** — within a 15-minute bar the high may precede the low, so a bar can lift the floor and then breach it. That is the adverse assumption and it is the right direction for a ratcheting barrier.

### Maximum adverse excursion — the distribution, not the mean

| era | holds | mean | p50 | p75 | p90 | p95 | p99 | worst |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 12,985 | 0.81% | 0.55% | 1.11% | 1.87% | 2.44% | 3.98% | **13.85%** |
| 2010-2019 | 7,758 | 0.70% | 0.47% | 0.96% | 1.65% | 2.17% | 3.48% | **13.85%** |
| 2020 | 792 | 1.31% | 0.88% | 1.73% | 3.12% | 4.11% | 7.05% | **11.29%** |
| 2021-2026 | 4,435 | 0.92% | 0.68% | 1.29% | 2.03% | 2.51% | 3.90% | **6.87%** |

Per symbol, pooled across eras:

| symbol | holds | mean MAE | p90 | p99 | worst | max trailing DD, p99 |
|---|---:|---:|---:|---:|---:|---:|
| SPY | 3,266 | 0.72% | 1.66% | 3.54% | 10.22% | 4.48% |
| QQQ | 3,266 | 0.89% | 2.09% | 4.13% | 13.85% | 5.03% |
| IWM | 3,265 | 0.98% | 2.16% | 4.38% | 11.29% | 5.26% |
| DIA | 3,188 | 0.65% | 1.51% | 3.32% | 10.20% | 4.08% |

### What fraction of sessions breach a 4% trailing drawdown

At notional *k*, a 4% equity floor is breached when the price path draws down more than 4%/*k* from its running peak — 4.00% at 1x, 2.00% at 2x, 1.33% at 3x.

| era | holds | 1x | 2x | 3x |
|---|---:|---:|---:|---:|
| ALL | 12,985 | 2.07% | 16.47% | 34.73% |
| 2010-2019 | 7,758 | 1.06% | 11.34% | 26.46% |
| 2020 | 792 | 11.36% | 35.10% | 56.57% |
| 2021-2026 | 4,435 | 2.19% | 22.10% | 45.30% |

Per symbol:

| symbol | holds | 1x | 2x | 3x |
|---|---:|---:|---:|---:|
| SPY | 3,266 | 1.41% | 12.43% | 28.81% |
| QQQ | 3,266 | 2.76% | 20.09% | 39.83% |
| IWM | 3,265 | 3.00% | 23.95% | 47.57% |
| DIA | 3,188 | 1.10% | 9.22% | 22.43% |

### How much of the adverse excursion falls where it cannot be exited

**This is the point.** A trailing floor is measured on open equity, and a position cannot be stopped out of a window with no prices in it. The 20:00->04:00 stretch contributes exactly one observation to the path — the price it reopens at — so the numbers below are a **LOWER BOUND**: any excursion inside the untraded window is invisible to this fixture, and a continuously-traded futures position would have lived through it.

Where the session's maximum trailing drawdown is realised. **This table is dominated by bar counts and is the least useful of the three** — regular hours supply 26 observations, the untraded window supplies exactly one, so of course the maximum usually lands in regular hours. It is reported because its shape is what makes the next two tables readable, not because it decides anything.

| era | holds | evening 18:00-20:00 | **untraded** | pre-market | regular hours |
|---|---:|---:|---:|---:|---:|
| ALL | 12,985 | 0.66% | 0.17% | 15.93% | 83.23% |
| 2010-2019 | 7,758 | 0.57% | 0.19% | 11.15% | 88.09% |
| 2020 | 792 | 1.89% | 0.25% | 22.10% | 75.76% |
| 2021-2026 | 4,435 | 0.61% | 0.11% | 23.20% | 76.08% |

Where the **FIRST breach** of the 4% floor occurs, among breaching holds. This one decides something: a breach that first occurs in regular hours is a breach you were stopped out of, and a breach that first occurs in the untraded window is one **no stop could have prevented**. Pre-market sits in between — technically exitable, thin enough that a stop is a hope rather than a plan.

| notional | era | breaching holds | evening | **untraded** | pre-market | regular hours |
|---|---|---:|---:|---:|---:|---:|
| 1x | ALL | 269 | 1.12% | 3.72% | 15.99% | 79.18% |
|  | 2010-2019 | 82 | 1.22% | 1.22% | 6.10% | 91.46% |
|  | 2020 | 90 | 2.22% | 10.00% | 31.11% | 56.67% |
|  | 2021-2026 | 97 | 0.00% | 0.00% | 10.31% | 89.69% |
| 2x | ALL | 2,138 | 2.95% | 2.53% | 22.36% | 72.17% |
|  | 2010-2019 | 880 | 0.80% | 2.39% | 13.64% | 83.18% |
|  | 2020 | 278 | 10.07% | 8.27% | 28.78% | 52.88% |
|  | 2021-2026 | 980 | 2.86% | 1.02% | 28.37% | 67.76% |
| 3x | ALL | 4,510 | 3.46% | 3.04% | 30.84% | 62.66% |
|  | 2010-2019 | 2,053 | 1.66% | 2.83% | 19.24% | 76.28% |
|  | 2020 | 448 | 12.28% | 9.82% | 37.95% | 39.96% |
|  | 2021-2026 | 2,009 | 3.33% | 1.74% | 41.11% | 53.81% |

And the untraded gap **on its own** — the drawdown from the running peak to the first next-session print, which no stop could have avoided:

| era | holds | mean gap DD | p90 | p99 | worst | gap alone breaches 1x | 2x | 3x |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | 12,985 | 0.18% | 0.49% | 1.58% | **6.50%** | 0.10% | 0.55% | 1.42% |
| 2010-2019 | 7,758 | 0.15% | 0.43% | 1.23% | **6.50%** | 0.03% | 0.30% | 0.85% |
| 2020 | 792 | 0.44% | 1.22% | 4.46% | **5.86%** | 1.39% | 4.29% | 8.59% |
| 2021-2026 | 4,435 | 0.18% | 0.50% | 1.49% | **2.71%** | 0.00% | 0.32% | 1.15% |

### Worst single sessions, dated

| rank | symbol | session | max trailing DD | MAE | of which the untraded gap | hold return |
|---:|---|---|---:|---:|---:|---:|
| 1 | QQQ | 2010-05-06 | **14.03%** | 13.85% | 0.19% | -3.42% |
| 2 | IWM | 2020-03-12 | **12.31%** | 11.29% | 5.07% | -11.20% |
| 3 | DIA | 2020-03-12 | **11.37%** | 10.20% | 5.86% | -10.10% |
| 4 | IWM | 2020-03-18 | **11.18%** | 10.22% | 4.45% | -5.96% |
| 5 | DIA | 2020-03-18 | **11.15%** | 9.27% | 5.49% | -4.33% |
| 6 | SPY | 2020-03-12 | **10.86%** | 9.68% | 5.01% | -9.53% |
| 7 | QQQ | 2020-03-12 | **10.60%** | 9.35% | 5.17% | -9.19% |
| 8 | SPY | 2010-05-06 | **10.52%** | 10.22% | 0.27% | -3.48% |
| 9 | IWM | 2010-05-06 | **10.06%** | 9.60% | 0.00% | -3.99% |
| 10 | SPY | 2020-03-18 | **9.80%** | 8.25% | 4.87% | -3.02% |

Worst by symbol:

| symbol | session | max trailing DD | MAE | untraded gap DD | hold return |
|---|---|---:|---:|---:|---:|
| SPY | 2020-03-12 | **10.86%** | 9.68% | 5.01% | -9.53% |
| QQQ | 2010-05-06 | **14.03%** | 13.85% | 0.19% | -3.42% |
| IWM | 2020-03-12 | **12.31%** | 11.29% | 5.07% | -11.20% |
| DIA | 2020-03-12 | **11.37%** | 10.20% | 5.86% | -10.10% |

## Sensitivity — how much of this is the bad prints, and how much is real

`corroborated` is the headline: suspect bars excluded, bar highs and lows used. `raw` puts the erroneous prints back. `closes` samples the path at bar closes only and is a strict lower bound. The truth for a continuously-traded instrument sits **above** all three, because the untraded window is dark in every one of them.

| variant | holds | mean MAE | p99 MAE | worst MAE | breach 1x | breach 2x | breach 3x |
|---|---:|---:|---:|---:|---:|---:|---:|
| corroborated | 12,985 | 0.81% | 3.98% | 13.85% | 2.07% | 16.47% | 34.73% |
| raw | 12,985 | 0.86% | 4.76% | 35.84% | 2.96% | 17.17% | 35.21% |
| closes | 12,985 | 0.69% | 3.72% | 11.20% | 1.35% | 11.15% | 24.94% |

## What was excluded, and why

| | count |
|---|---:|
| symbol-sessions in the fixture | 16,748 |
| half-days dropped (13:00 close: no 16:00 print, no 16:00->20:00 window) | 23 sessions |
| usable session pairs | 16,650 |
| pairs in the decomposition (needs an evening AND a pre-market print) | 16,648 |
| holds in the path table (consecutive calendar days, evening print after 17:00) | 12,985 |

Decomposition coverage by symbol and era, as a share of available pairs:

| symbol | 2010-2019 | 2020 | 2021-2026 |
|---|---:|---:|---:|
| SPY | 2495/2495 (100%) | 251/251 (100%) | 1417/1417 (100%) |
| QQQ | 2495/2495 (100%) | 251/251 (100%) | 1417/1417 (100%) |
| IWM | 2495/2495 (100%) | 251/251 (100%) | 1417/1417 (100%) |
| DIA | 2491/2493 (100%) | 251/251 (100%) | 1417/1417 (100%) |

