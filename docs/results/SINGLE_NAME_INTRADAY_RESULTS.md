# D264 — the intraday short on single names

**A SCREEN, NOT A VERDICT.** Cross-screen under R12 of [D247](../decisions/D247-the-short-side-at-fifteen-minutes.md)'s construction onto eight single names. Pre-registered in [`docs/decisions/D264-the-intraday-short-on-single-names.md`](../decisions/D264-the-intraday-short-on-single-names.md) **before this ran**.

*seed 0, 1,000 rotations, 338.3s. 8 names x 55,004 bars over 2,117 sessions (25.98/session, PPY 6547); warm-up 1,000 bars, live 8.25 years. 2018-01-02 .. 2026-08-31.*

> **SURVIVOR-ONLY. TIME_SERIES_INTRADAY serves no delisted ticker; 41.6% of the 2013-2017 cohort is unreachable. D264 declares the direction IN ADVANCE: the bias is CONSERVATIVE for a short, so a PASS is informative and a FAIL IS AMBIGUOUS and does not close the question.**

**Strata.** LOW `PG LMT PM MO` · HIGH `CLF SM YELP RH`. Half-spread 1.5/4.5 bp, borrow 0.30%/3.00%, notional $175,439/position (D247's own figure).


## Part A — the anatomy, reported before any cell was scored

### The drift decomposition — the measurement the whole construction rests on

*On the 57 ETFs D247 measured **+8.59%/yr overnight against −0.36% intraday**. A book flat at every close faces the second number instead of the first.*

| stratum | overnight/yr | intraday/yr | swing | B&H CAGR | vol |
|---|---:|---:|---:|---:|---:|
| **ALL** | +8.98% | -1.97% | +10.96 pts | +6.83% | 27.1% |
| **LOW** | +4.36% | +5.56% | -1.21 pts | +10.16% | 18.0% |
| **HIGH** | +13.81% | -8.97% | +22.78 pts | +3.59% | 45.7% |

### The variance tax, against its formula

*FINDINGS §1b: a daily-rebalanced short earns approximately `−mu − sigma^2`. D253 landed within 2.85 points on crypto. **A short book that does not clearly beat `SHORT_ALL` has found nothing.***

| stratum | sigma^2 | mu | predicted SHORT_ALL | **measured** | error |
|---|---:|---:|---:|---:|---:|
| **ALL** | 0.0732 | +6.61% | -12.82% | **-27.08%** | -14.25 pts |
| **LOW** | 0.0326 | +9.68% | -11.75% | **-14.60%** | -2.85 pts |
| **HIGH** | 0.2085 | +3.54% | -21.60% | **-37.73%** | -16.13 pts |

### Breadth — R10, and pooled counts are not sample sizes

| stratum | names | effective instruments | mean pairwise rho |
|---|---:|---:|---:|
| **ALL** | 8 | **3.02** | 0.236 |
| **LOW** | 4 | **1.87** | 0.378 |
| **HIGH** | 4 | **2.08** | 0.308 |

### What the held bars actually return

*D244's lesson: a null can be beaten or lost by drift structure alone, so this is measured before any null result is interpreted. D247's swing on ETFs was **8.99 points** between `cont` and `intra`.*

| stratum | cell | bars held | annualised return of those bars |
|---|---|---:|---:|
| **ALL** | *all bars* | 432,032 | *+6.83%* |
| | S1_short_cont | 113,164 | **+20.22%** |
| | S1_short_intra | 108,113 | **-11.94%** |
| | S2_short_cont | 54,945 | **+13.54%** |
| | S2_short_intra | 52,826 | **+8.01%** |
| **LOW** | *all bars* | 216,016 | *+10.17%* |
| | S1_short_cont | 58,028 | **+18.11%** |
| | S1_short_intra | 55,437 | **+7.86%** |
| | S2_short_cont | 27,727 | **-2.52%** |
| | S2_short_intra | 26,651 | **-10.92%** |
| **HIGH** | *all bars* | 216,016 | *+3.60%* |
| | S1_short_cont | 55,136 | **+22.48%** |
| | S1_short_intra | 52,676 | **-28.87%** |
| | S2_short_cont | 27,218 | **+32.62%** |
| | S2_short_intra | 26,175 | **+31.42%** |

## Part B — the 16 cells

*`exposure x edge` is the GROSS product per FINDINGS 1a -- signed position against the bar return, before costs and financing -- reported beside the held-bar edge it is the product of, never the edge alone. CAGR is net.*

| stratum | cell | exposure | held-bar edge | **exp x edge** | CAGR (net) | excess Sharpe | max DD | turnover/yr | borrow/yr | entries (min/sym) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ALL | **S1_short_cont** | 26.2% | +20.22% | **-4.71%** | -17.64% | **-1.816** | -81.83% | 209 | 0.51% | 6,883 (776) |
| ALL | **S1_short_intra** | 25.0% | -11.94% | **+3.23%** | -12.54% | **-1.861** | -69.20% | 334 | 0.00% | 11,004 (1270) |
| ALL | **S2_short_cont** | 12.7% | +13.54% | **-1.60%** | -5.72% | **-0.876** | -41.56% | 28 | 0.21% | 913 (107) |
| ALL | **S2_short_intra** | 12.2% | +8.01% | **-0.94%** | -6.01% | **-1.253** | -41.97% | 90 | 0.00% | 2,968 (352) |
| ALL | **S1_long_cont** | 23.2% | +23.51% | **+5.03%** | -3.08% | **-0.340** | -38.16% | 186 | 0.00% | 6,134 (711) |
| ALL | **S1_long_intra** | 22.2% | +18.87% | **+3.92%** | -8.48% | **-1.173** | -53.50% | 295 | 0.00% | 9,740 (1127) |
| ALL | **S2_long_cont** | 12.7% | +27.31% | **+3.12%** | +1.94% | **+0.213** | -13.15% | 28 | 0.00% | 915 (98) |
| ALL | **S2_long_intra** | 12.2% | +3.57% | **+0.43%** | -3.28% | **-0.814** | -26.71% | 90 | 0.00% | 2,976 (305) |
| LOW | **S1_short_cont** | 26.9% | +18.11% | **-4.37%** | -9.82% | **-1.396** | -60.91% | 216 | 0.10% | 3,568 (881) |
| LOW | **S1_short_intra** | 25.7% | +7.86% | **-1.92%** | -9.11% | **-1.790** | -56.84% | 343 | 0.00% | 5,666 (1408) |
| LOW | **S2_short_cont** | 12.8% | -2.52% | **+0.33%** | -1.06% | **-0.199** | -22.06% | 28 | 0.04% | 460 (111) |
| LOW | **S2_short_intra** | 12.3% | -10.92% | **+1.44%** | -0.89% | **-0.208** | -14.58% | 91 | 0.00% | 1,507 (364) |
| HIGH | **S1_short_cont** | 25.5% | +22.48% | **-5.04%** | -24.78% | **-1.497** | -91.64% | 201 | 0.92% | 3,315 (776) |
| HIGH | **S1_short_intra** | 24.4% | -28.87% | **+8.66%** | -15.84% | **-1.342** | -78.48% | 324 | 0.00% | 5,338 (1270) |
| HIGH | **S2_short_cont** | 12.6% | +32.62% | **-3.49%** | -10.16% | **-0.893** | -60.95% | 27 | 0.37% | 453 (107) |
| HIGH | **S2_short_intra** | 12.1% | +31.42% | **-3.26%** | -10.87% | **-1.329** | -63.59% | 89 | 0.00% | 1,461 (352) |

### The cost wall — the breakeven is the result, the charged figure is my assumption

*D247's S1_short_intra: breakeven **0.13 bp/side** against ~1.6 charged — a **12x** shortfall. That is the number this study exists to move.*

| stratum | cell | turnover/yr | **breakeven bp/side** | charged | headroom | K |
|---|---|---:|---:|---:|---:|:--:|
| *ETF* | *S1_short_intra (D247)* | *334* | ***0.13*** | *1.60* | *0.08x* | *no* |
| ALL | **S1_short_cont** | 209 | **-5.44** | 4.21 | -1.29x | no |
| ALL | **S1_short_intra** | 334 | **0.11** | 4.21 | 0.03x | no |
| ALL | **S2_short_cont** | 28 | **-17.88** | 4.21 | -4.25x | no |
| ALL | **S2_short_intra** | 90 | **-2.73** | 4.21 | -0.65x | no |
| ALL | **S1_long_cont** | 186 | **2.15** | 4.21 | 0.51x | no |
| ALL | **S1_long_intra** | 295 | **1.00** | 4.21 | 0.24x | no |
| ALL | **S2_long_cont** | 28 | **9.28** | 4.21 | 2.20x | YES |
| ALL | **S2_long_intra** | 90 | **-0.06** | 4.21 | -0.01x | no |
| LOW | **S1_short_cont** | 216 | **-2.82** | 2.00 | -1.41x | no |
| LOW | **S1_short_intra** | 343 | **-0.78** | 2.00 | -0.39x | no |
| LOW | **S2_short_cont** | 28 | **-1.98** | 2.00 | -0.99x | no |
| LOW | **S2_short_intra** | 91 | **1.02** | 2.00 | 0.51x | no |
| HIGH | **S1_short_cont** | 201 | **-8.26** | 6.42 | -1.29x | no |
| HIGH | **S1_short_intra** | 324 | **1.06** | 6.42 | 0.16x | no |
| HIGH | **S2_short_cont** | 27 | **-34.06** | 6.42 | -5.30x | no |
| HIGH | **S2_short_intra** | 89 | **-6.60** | 6.42 | -1.03x | no |

### Where the gross edge goes — the exact decomposition

*`exposure x edge` is the LINEAR product FINDINGS §1a and D250 compute. **It is not what a short earns.** A short earns `log(2 − e^r)`, so FINDINGS §1b's variance tax comes out BEFORE any trading cost does.*

**Stated as continuously-compounded %/yr, because these legs must ADD and annualised percentages do not.** Subtracting the percentage forms gives −19.48% where the net is −15.84%; in log space the identity closes exactly. Net CAGR is the same number expressed the usual way.

| stratum | cell | exp × edge | − σ² tax | = realisable | − trading cost | = **net** | *net CAGR* |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | **S1_short_cont** | -4.82% | −6.01% | -10.83% | −8.58% | **-19.41%** | *-17.64%* |
| ALL | **S1_short_intra** | +3.18% | −2.81% | +0.38% | −13.77% | **-13.40%** | *-12.54%* |
| ALL | **S2_short_cont** | -1.61% | −3.12% | -4.73% | −1.16% | **-5.89%** | *-5.72%* |
| ALL | **S2_short_intra** | -0.94% | −1.51% | -2.45% | −3.75% | **-6.20%** | *-6.01%* |
| LOW | **S1_short_cont** | -4.47% | −1.53% | -6.00% | −4.33% | **-10.33%** | *-9.82%* |
| LOW | **S1_short_intra** | -1.94% | −0.74% | -2.68% | −6.87% | **-9.55%** | *-9.11%* |
| LOW | **S2_short_cont** | +0.33% | −0.84% | -0.51% | −0.56% | **-1.07%** | *-1.06%* |
| LOW | **S2_short_intra** | +1.43% | −0.49% | +0.93% | −1.83% | **-0.89%** | *-0.89%* |
| HIGH | **S1_short_cont** | -5.18% | −10.48% | -15.66% | −12.82% | **-28.48%** | *-24.78%* |
| HIGH | **S1_short_intra** | +8.31% | −4.87% | +3.43% | −20.68% | **-17.24%** | *-15.84%* |
| HIGH | **S2_short_cont** | -3.56% | −5.39% | -8.95% | −1.76% | **-10.71%** | *-10.16%* |
| HIGH | **S2_short_intra** | -3.31% | −2.53% | -5.84% | −5.67% | **-11.51%** | *-10.87%* |

**Read the S1_short_intra rows.** They are the only cells whose realisable gross is positive, and the trading cost is what takes them under — not the signal, and not, on its own, the variance tax.


### Hurdles — all six, every leg computed (R6)

*Best-of-16 floor (D228, one shared offset vector across all strata): **+0.416**.*

| stratum | cell | H sharpe | H money | **H** | V | E | K | B | F | **ALL** |
|---|---|---:|---:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| ALL | **S1_short_cont** | 26.2th | 14.4th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S1_short_intra** | 90.6th | 99.8th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S2_short_cont** | 38.4th | 35.5th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S2_short_intra** | 40.0th | 77.0th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S1_long_cont** | 93.1th | 91.5th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S1_long_intra** | 63.3th | 80.7th | fail | fail | PASS | fail | fail | fail | **fail** |
| ALL | **S2_long_cont** | 87.1th | 83.8th | fail | PASS | PASS | PASS | fail | fail | **fail** |
| ALL | **S2_long_intra** | 17.4th | 42.4th | fail | fail | PASS | fail | fail | fail | **fail** |
| LOW | **S1_short_cont** | 23.1th | 16.8th | fail | fail | PASS | fail | fail | fail | **fail** |
| LOW | **S1_short_intra** | 20.2th | 80.0th | fail | fail | PASS | fail | fail | fail | **fail** |
| LOW | **S2_short_cont** | 88.5th | 84.8th | fail | fail | PASS | fail | fail | fail | **fail** |
| LOW | **S2_short_intra** | 97.2th | 97.9th | PASS | fail | PASS | fail | fail | fail | **fail** |
| HIGH | **S1_short_cont** | 33.4th | 25.4th | fail | fail | PASS | fail | fail | fail | **fail** |
| HIGH | **S1_short_intra** | 96.9th | 99.7th | PASS | fail | PASS | fail | fail | fail | **fail** |
| HIGH | **S2_short_cont** | 22.3th | 19.3th | fail | fail | PASS | fail | fail | fail | **fail** |
| HIGH | **S2_short_intra** | 13.1th | 50.3th | fail | fail | PASS | fail | fail | fail | **fail** |

### R10 — concurrency, actual against a per-symbol-rotated book

| stratum | cell | mean held | max | share of universe | *rotated max* | sd ratio |
|---|---|---:|---:|---:|---:|---:|
| ALL | S1_short_cont | 2.10 | 8 | 26.2% | *7* | 1.33x |
| ALL | S1_short_intra | 2.00 | 8 | 25.0% | *8* | 1.35x |
| ALL | S2_short_cont | 1.02 | 7 | 12.7% | *5* | 1.13x |
| ALL | S2_short_intra | 0.98 | 7 | 12.2% | *5* | 1.17x |
| ALL | S1_long_cont | 1.86 | 8 | 23.2% | *7* | 1.36x |
| ALL | S1_long_intra | 1.78 | 8 | 22.2% | *7* | 1.40x |
| ALL | S2_long_cont | 1.02 | 7 | 12.7% | *6* | 1.23x |
| ALL | S2_long_intra | 0.98 | 7 | 12.2% | *5* | 1.27x |
| LOW | S1_short_cont | 1.07 | 4 | 26.9% | *4* | 1.28x |
| LOW | S1_short_intra | 1.03 | 4 | 25.7% | *4* | 1.29x |
| LOW | S2_short_cont | 0.51 | 4 | 12.8% | *3* | 1.16x |
| LOW | S2_short_intra | 0.49 | 4 | 12.3% | *4* | 1.13x |
| HIGH | S1_short_cont | 1.02 | 4 | 25.5% | *4* | 1.22x |
| HIGH | S1_short_intra | 0.98 | 4 | 24.4% | *4* | 1.23x |
| HIGH | S2_short_cont | 0.50 | 4 | 12.6% | *4* | 1.10x |
| HIGH | S2_short_intra | 0.48 | 4 | 12.1% | *4* | 1.10x |

## Limitations carried into the reading, none of them discovered afterwards

1. **Survivorship.** SURVIVOR-ONLY. TIME_SERIES_INTRADAY serves no delisted ticker; 41.6% of the 2013-2017 cohort is unreachable. D264 declares the direction IN ADVANCE: the bias is CONSERVATIVE for a short, so a PASS is informative and a FAIL IS AMBIGUOUS and does not close the question.
2. **Breadth.** Effective independent instruments **3.02** of 8. R10's corollary is binding: the pooled entry counts in Part B are **not** sample sizes, and are never quoted alone.
3. **The bootstrap block is 21 bars**, inherited from D247 unchanged so the two studies stay comparable. At fifteen minutes that is **under one session**, so hurdle B under-weights any autocorrelation living at the daily scale and is the weakest of the six. Kept rather than re-chosen: picking a block length after seeing the data is the defect R9's corollary warns about.
4. **The half-spread and borrow are assumptions** (1.5/4.5 bp, 0.30/3.00%). The commission is derived from the committed IBKR schedule. **Read hurdle K off the breakeven column, which is a property of the strategy**, not off my spread guess.
5. **Locate fees and SEC Rule 201 are not modelled**, and both run *against* the short — hardest on the HIGH stratum, where a falling small-cap is exactly what becomes expensive to borrow.
6. **The volatility axis is confounded with sector** — sorting a liquid pool on volatility produced defensive mega-caps at one end and cyclicals at the other. Unavoidable, and any stratum-level reading carries it.
7. **The calendar mismatch is D247's and is severe.** S1's 34-bar Impulse is ~1.3 sessions here against seven weeks daily; S2's 252-bar regression is ~9.8 sessions against a year.

## Verdict

**ZERO of the 12 short cells clear all six hurdles.**

Per D264's stop, the construction is closed **on this sample** — no parameter sweep, no additional stratum, no third arm, no re-cut window, no 5-minute bars.

**And the closure is bounded, in the words fixed before the run:** it closes this construction on these eight survivor names. It does **not** close the intraday short as a question, because the sample is survivor-only, the bias runs *against* the short, and eight names is thin.

