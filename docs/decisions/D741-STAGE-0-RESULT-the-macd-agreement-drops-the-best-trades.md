# D741 STAGE 0 RESULT — NOT SUPPORTED: the 30-minute log-MACD agreement filter trims the floored follow's drawdown only by trading less, and halves its net; the trades it drops (histogram against the trade) are A's best

*2026-10-01.*
- *Pre-registration: [D741](D741-STAGE-0-PRE-REG-a-macd-histogram-agreement-filter-for-drawdown-on-the-floored-nq-follow.md) (05141b9a).*
- *Runner: `scripts/stage0_d741_macd_drawdown.py` (c7e27729), one run, 0.1 min.*
- *Output: `data/stage0_d741_macd_drawdown.json`, aggregates only.*
- *In-sample ≤ 2023-12-29; one MNQ, \$4.0671 a round trip.*

## 0. The audits

- **D727's checks:** the lag audit (its canary fired) and the known answers, to 1e-6.
- **A reproduces D740's 546 trades.**
- **The entry bar's close equals the follow's entry price on every trade.**
- **Causality:** the histogram equals an explicit-recursion second implementation on a series truncated at the entry bar.
  The next-bar canary changed all 25 sampled values.
- **Sign:** 30 trades re-priced from the raw rows.
- **Gate 1 holds on A:** mean gross +\$32.91, NW t 2.79.

## 1. The table

| book | trades | net / trade (median) | gross / trade | total net | Sharpe (Sortino) | max DD | **Calmar** | worst day | longest drawdown | win rate | trimmed mean |
|---|---:|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| **A** (D740's floor) | 546 | +\$28.85 (+\$40.93) | +\$32.91 | \$15,751 | 0.87 (1.27) | \$4,131 | **3.81** | −\$1,142 | 162 sessions | 0.56 | +\$30.11 |
| **M** (A and MACD agrees) | 368 (67 %) | +\$21.13 (+\$45.43) | +\$25.20 | \$7,776 | 0.53 (0.71) | \$3,066 | **2.54** | −\$1,142 | 140 | 0.57 | +\$24.24 |
| *beside:* dropped (MACD against) | 178 | **+\$44.80** (+\$31.93) | +\$48.87 | \$7,975 | 0.75 (1.33) | \$1,864 | **4.28** | −\$740 | 212 | 0.54 | +\$42.43 |

**By year** (net \$, with trades in brackets):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| A | +1,257 (40) | +450 (10) | +1,858 (95) | +3,487 (142) | +6,325 (132) | +2,374 (127) |
| M | +1,173 (25) | +293 (9) | +253 (58) | +2,522 (97) | +1,505 (86) | +2,030 (93) |
| dropped | +83 (15) | +156 (1) | +1,606 (37) | +964 (45) | **+4,820 (46)** | +345 (34) |

2016 and 2017 abstain in every book.

**The nulls** (M's take mask over A's 546 trades):

| statistic | rotation: observed / p50 / p95 (p) | within-year (p) |
|---|---|---|
| **C1 Calmar** (primary) | 2.54 / 3.13 / 6.63 (**0.659**) | 0.669 |
| C2 max DD (lower is better) | \$3,066 / \$3,353 / \$2,105 at p05 (0.383) | 0.402 |
| S1 mean net | \$21.13 / \$28.98 / \$42.41 (0.832) | 0.821 |

**Gate 2 fails.** The max DD falls (\$4,131 → \$3,066), but Calmar falls too (3.81 → 2.54), and the rotation p is 0.659.
The drawdown cut is what dropping a third of the trades gives anyway: the null's median max DD is \$3,353.

**Reading: NOT SUPPORTED.** Gate 3 alone would read EARNS (5 of 5 traded years positive).

## 2. Predictions (D741 §4)

| # | prediction | outcome |
|---|---|---|
| 1 | M keeps 60–85 % of A | **Held** (67 %) |
| 2 | M's max DD is below \$4,131 | **Held** (\$3,066) |
| 3 | NOT SUPPORTED (Calmar rotation p > 0.05) | **Held** (0.659) |
| 4 | the dropped trades' mean net is below the kept trades' | **Failed**, and by a lot: the dropped average +\$44.80 against the kept +\$21.13 |

## 3. What it says

1. **The MACD agreement does not manage drawdown.** It cuts the drawdown by trading less, and it removes the follow's
   best trades: the dropped third carries half the net, at Calmar 4.28.
2. **POST HOC, not tested.** When the 30-minute histogram has already turned against the morning's move (momentum
   fading while the drift is still ≥ 1.5σ), the follow does better. That fits D730/D731 (quiet tapes continue, bursts
   exhaust). It is one observation from one cut, the complement of a failed filter. It is not a finding, and it is
   not pre-registered.
3. **A's drawdown comes from its 2020–22 high-volatility days.** The worst day is −\$1,142, and the longest drawdown
   is 162 sessions. A directional agreement filter does not reach that. A drawdown tool for this book would have to act
   on size or exit, not on agreement.
