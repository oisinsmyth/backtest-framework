# D240 — the uptrend-onset arm, with stops and targets

**STAGE 1 — A SCREEN, NOT A VERDICT.** screen (mined 57) -- the holdout and forward window are untouched

*seed 0, 1,000 sims, 32.7s. 57 ETFs x 1,515 live bars, 2018-12-21 .. 2024-12-30. k=3, window 252, age cap 63, ATR(21), stop 1xATR, floor 2xATR.*

## The cells

| | | exposure | excess Sharpe | CAGR | **deployable** | vol | max DD | Calmar | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| **A0** | base — onset + age cap | 14.2% | **+0.610** | 2.37% | **5.87%** | 2.9% | -5.78% | 0.409 | ✗ |
| **A1** | + structural sloped stop | 12.5% | **+0.720** | 2.25% | **5.82%** | 2.4% | -2.45% | 0.921 | ✗ |
| **A2** | + fixed −8% stop | 13.0% | **+0.822** | 2.52% | **6.08%** | 2.4% | -1.93% | 1.306 | ✗ |
| **A3** | + target at +2R | 13.2% | **+0.524** | 2.06% | **5.59%** | 2.9% | -5.76% | 0.357 | ✗ |
| **A4** | + stop and target | 11.7% | **+0.652** | 2.03% | **5.63%** | 2.4% | -2.39% | 0.848 | ✗ |
| *S1* | *for scale* | *18.9%* | *+0.746* | *5.43%* | *8.83%* | *6.1%* | *-10.30%* | *0.527* | — |
| *B&H* | *for scale* | *100.0%* | *+0.235* | *8.42%* | *8.42%* | *17.7%* | *-34.60%* | *0.243* | — |

## A — R7's matched-exit-count overlay null, which carries the overlay verdict

*Keep A0's book; cut **the same number of trades** short at random trades and random points inside their own spans, with cut fractions drawn from the real overlay's own pool. What varies is only **which** trades and **where** — the claim under test.*

| | trades cut | actual | null p50 | null p95 | **percentile** | A |
|---|---:|---:|---:|---:|---:|:--:|
| **A1** | 56 of 245 | **+0.720** | +0.618 | +0.758 | **89.1th** | ✗ |
| **A2** | 40 of 245 | **+0.822** | +0.614 | +0.741 | **99.6th** | ✓ |
| **A3** | 38 of 245 | **+0.524** | +0.613 | +0.741 | **2.5th** | ✗ |
| **A4** | 85 of 245 | **+0.652** | +0.627 | +0.802 | **58.7th** | ✗ |

## B — the rotation null on the entry rule

| | actual | null p50 | null p95 | percentile | money pct | vol ratio | B |
|---|---:|---:|---:|---:|---:|---:|:--:|
| **A0** | **+0.610** | +0.203 | +0.547 | **97.3th** | 99.2th | 1.055x | ✓ |

## C — the diversification condition, which decides whether this is arm two

*Adding an arm raises the book's maximum attainable Sharpe iff `SR_B > ρ · SR_S1`.*

| | ρ with S1 | bar `ρ × 0.746` | actual | C |
|---|---:|---:|---:|:--:|
| **A0** | +0.1499 | +0.112 | **+0.610** | ✓ |
| **A1** | +0.1523 | +0.114 | **+0.720** | ✓ |
| **A2** | +0.1586 | +0.118 | **+0.822** | ✓ |
| **A3** | +0.1398 | +0.104 | **+0.524** | ✓ |
| **A4** | +0.1406 | +0.105 | **+0.652** | ✓ |

## D — versus buy-and-hold, with the √f decomposition

| | exposure | √f predicts | actual | selection quality | beats B&H |
|---|---:|---:|---:|---:|:--:|
| **A0** | 14.2% | +0.089 | +0.610 | **+587.8%** | ✓ |
| **A1** | 12.5% | +0.083 | +0.720 | **+764.9%** | ✓ |
| **A2** | 13.0% | +0.085 | +0.822 | **+869.6%** | ✓ |
| **A3** | 13.2% | +0.085 | +0.524 | **+514.3%** | ✓ |
| **A4** | 11.7% | +0.080 | +0.652 | **+712.4%** | ✓ |

## Bootstrap — NOT a registered hurdle, and that was a gap

*D240 registered no bootstrap. Given D230 — where 8 deltas cleared as scored and **zero** cleared as claimed once the leg was built — that was an omission, so it is computed here as a diagnostic. Block 21, paired on identical resampled dates.*

| | excess Sharpe | p05 | p95 | excludes 0 | Δ vs B&H | p05 | p95 | excludes 0 |
|---|---:|---:|---:|:--:|---:|---:|---:|:--:|
| **A0** | +0.610 | -0.103 | +1.295 | ✗ | +0.375 | -0.118 | +0.837 | ✗ |
| **A1** | +0.720 | +0.133 | +1.322 | ✓ | +0.485 | -0.180 | +1.091 | ✗ |
| **A2** | +0.822 | +0.207 | +1.419 | ✓ | +0.587 | -0.111 | +1.170 | ✗ |
| **A3** | +0.524 | -0.187 | +1.204 | ✗ | +0.289 | -0.213 | +0.748 | ✗ |
| **A4** | +0.652 | +0.057 | +1.255 | ✓ | +0.417 | -0.236 | +1.010 | ✗ |
| **S1** | +0.746 | -0.009 | +1.327 | ✗ | +0.511 | -0.204 | +1.098 | ✗ |

## What the pairing would be worth

*Closed form on numbers already in the table — **not a new book and not a cell.** Adding arm B raises the maximum attainable Sharpe to `sqrt((Sa² + Sb² − 2ρSaSb) / (1 − ρ²))`.*

| pairing | combined Sharpe | gain over S1 | years to significance |
|---|---:|---:|---:|
| S1 alone | 0.746 | — | 8.8y |
| **S1 + A0** | **0.900** | +0.154 | **6.7y** |
| **S1 + A1** | **0.966** | +0.220 | **6.0y** |
| **S1 + A2** | **1.032** | +0.286 | **5.5y** |
| **S1 + A3** | **0.858** | +0.112 | **7.1y** |
| **S1 + A4** | **0.929** | +0.182 | **6.4y** |

## Diagnostics — reported, never hurdles

**245 onsets**, 2 minimum entries per symbol against the 30 hurdle E requires.

**The R dispersion amendment 2 flagged**, measured:

| p5 | p25 | p50 | p75 | p95 | p95/p5 |
|---:|---:|---:|---:|---:|---:|
| 1.58% | 4.43% | **7.67%** | 13.51% | 28.91% | **16.2x** |

