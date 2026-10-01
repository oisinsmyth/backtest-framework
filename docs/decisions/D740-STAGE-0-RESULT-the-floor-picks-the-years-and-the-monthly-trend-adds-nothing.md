# D740 STAGE 0 RESULT — the volatility floor reads SUPPORTED, in-sample and post hoc, by choosing the years (within-year p 0.29); agreement with the 20-day SMA adds nothing (p 0.45); both together are NOT SUPPORTED and fail the principal's standard

*2026-10-01.*
- *Pre-registration: [D740](D740-STAGE-0-PRE-REG-a-volatility-floor-and-higher-time-frame-agreement-on-the-nq-follow.md) (76058f63).*
- *Runner: `scripts/stage0_d740_floor_and_htf.py` (6212ea0f), one run, 0.1 min.*
- *Output: `data/stage0_d740_floor_and_htf.json`, aggregates only.*
- *In-sample 2016-02-05 → 2023-12-29: 1,022 of D727's 1,024 k 1.5 trades. 2 had no 23-session history.*

## 0. The audits

- **D727's checks:** the lag audit (its canary fired) and the three recorded known answers, to 1e-6.
- **Sign:** 40 trades re-priced from the raw rows.
- **The SMA state:**
  - a second implementation, re-chaining 23 sessions of raw minute rows, agrees on all 40 sampled sessions;
  - a canary that includes session t's own close changes 4 of them, so it fires.
- **The state on the trades:** UP 604, DOWN 280, MIXED 138. NQ's monthly trend pointed up most of 2016–23.
- **Gate 1 holds:** mean gross +\$19.33 a trade, NW t 2.93.

## 1. The table (one MNQ, \$4.0671)

| book | kept (share) | net / trade (median) | gross / trade | net dropped | Sharpe (Sortino); gross Sharpe | max DD | win rate | trimmed (ex-top / ex-bottom) | y kept / dropped |
|---|---|---|---:|---:|---|---:|---:|---|---|
| take-all | 1,022 | +\$15.26 (+\$4.68) | +\$19.33 | — | 0.83 (1.21); 1.05 | \$4,131 | 0.51 | — | 0.080 |
| **A floor** (σ\$ ≥ \$150) | 546 (53 %) | **+\$28.85 (+\$40.93)** | +\$32.91 | −\$0.33 | 0.87 (1.27); 1.00 | \$4,131 | 0.56 | +\$30.11 (+\$20.91 / +\$38.04) | 0.125 / 0.030 |
| **B 20-day SMA agrees** | 418 (41 %) | +\$16.18 (+\$10.43) | +\$20.24 | +\$14.62 | 0.55 (0.76); 0.69 | \$2,836 | 0.57 | +\$18.79 (+\$9.90 / +\$25.05) | 0.108 / 0.061 |
| **C both** | 233 (23 %) | +\$26.99 (+\$56.43) | +\$31.05 | +\$11.80 | 0.53 (0.74); 0.61 | \$2,836 | 0.60 | +\$29.67 (+\$21.04 / +\$35.60) | 0.127 / 0.067 |
| *beside:* against the trend | 466 | +\$8.72 (**−\$11.07**) | +\$12.79 | | 0.32 (0.49) | \$2,665 | **0.45** | +\$8.43 | 0.032 |
| *beside:* MIXED | 138 | +\$34.56 (+\$33.18) | +\$38.62 | | 0.74 (1.13) | \$939 | 0.56 | +\$36.15 | 0.162 |

## 2. The nulls

| filter | rotation, S1 \$: obs / p50 / p95 (p) | rotation, S2 y (p) | within-year, S1 (p) | within-year, S2 (p) | p for Gate 2 | reading |
|---|---|---|---|---|---|---|
| **A floor** | 28.85 / 15.13 / 25.76 (**0.021**) | 0.125 vs p95 0.122 (**0.046**) | 28.85 vs p50 27.48 (0.29) | (0.56) | 0.021, **raw, POST HOC (known)** | **SUPPORTED** (in-sample consistency only) |
| B SMA agrees | 16.18 / 15.08 / 27.95 (0.454) | (0.227) | (0.51) | (0.26) | 0.454 (Holm, B and C) | **NOT SUPPORTED** |
| C both | 26.99 / 14.41 / 37.04 (0.163) | (0.205) | (0.51) | (0.48) | 0.327 (Holm) | **NOT SUPPORTED** |

**By year** (net \$, with trades in brackets):

| | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|
| take-all | −197 | −537 | +2,132 | −508 | +2,732 | +3,268 | +6,325 | +2,374 |
| A floor | 0 (0) | 0 (0) | +1,257 (40) | +450 (10) | +1,858 (95) | +3,487 (142) | +6,325 (132) | +2,374 (127) |
| B agrees | −536 (51) | +142 (48) | +1,892 (46) | +296 (50) | +160 (43) | +1,580 (64) | +3,328 (58) | −99 (58) |
| C both | 0 (0) | 0 (0) | +1,466 (17) | +82 (5) | **−287 (33)** | +1,799 (62) | +3,328 (58) | **−99 (58)** |

**Gate 3, the principal's standard with abstention:**

| book | reading | detail |
|---|---|---|
| **A** | **EARNS** | abstains in 2016 and 2017; 6 of 6 traded years positive; \$1,485 a year without its two best |
| B | EARNS, barely | 6 of 8; \$257 a year ex-2 |
| C | **INTERMITTENT** | 3 of 5 traded years positive; 2019 abstains |

## 3. Predictions (D740 §5)

| # | prediction | outcome |
|---|---|---|
| 1 | B keeps 35–55 % | **Held** (41 %) |
| 2 | B reads NOT SUPPORTED | **Held** (p 0.45) |
| 3 | the against-trend trades have a positive mean net | **Held**, weakly (+\$8.72; but median −\$11.07, win 0.45) |
| 4 | C keeps < 350 trades and has the highest mean of A, B, C | **Failed in part**: 233 trades, but A's mean (\$28.85) beats C's (\$26.99) |
| 5 | C's Gate 3 reads EARNS, with 2016–17 abstaining | **Failed**: INTERMITTENT (2020 −\$287, 2023 −\$99) |

## 4. What it says

1. **The floor works the way a regime gate works, and only that way.**
   - Against the time rotation it is p 0.021 (\$) and 0.046 (y).
   - Inside each year it adds nothing (within-year p 0.29 and 0.56): it chooses years, not trades.
   - It abstains in 2016–17 as intended. 2019 is kept to 10 trades, +\$450.
   - It meets the principal's standard with abstention, but Sharpe barely moves (0.83 → 0.87) and the max drawdown is
     unchanged (\$4,131, in 2020–22).
   - **It is post hoc and known**, so this reading is consistency, not evidence (D740 §0).
2. **The 20-day trend carries no usable information for the follow.**
   - With the trend: win 0.57 but median +\$10, mean +\$16.18. Against the trend: win 0.45, median −\$11, mean +\$8.72.
     The trend shifts the hit rate, but the means are close (p 0.45).
   - The MIXED sessions are the best of the three (+\$34.56 on 138), which no trend story predicts. That reads as noise.
3. **Combining them hurts.** C keeps 233 trades, and the agreement filter removes some of the floor's good trades in
   2020 and 2023, so it fails the principal's standard.
4. **The status of the line.**
   - The follow with a volatility floor is the in-sample-consistent version of the principal's "do not trade when the
     conditions are wrong". The rule is fixed in advance and not fitted, and it has a clear reason: below \$150 a day the
     opening move does not reliably cover twice the fee.
   - It can only be confirmed on unseen data, and it is still a follow, which the principal declined as a strategy.
   - If it goes further, it is a vault pre-registration in a free slot (2 or 10) on the principal's word. NQ's 2024+ would
     be its first look.

## CLOSED (2026-10-01)

- **The principal kept floor A** and added the 1.0 σ_rem stop as a risk rule
  ([D742](D742-STAGE-0-RESULT-A1-the-stop-caps-the-worst-day-not-the-drawdown.md)). The principal then closed the
  floored follow with its stop ("close the follow plus stop and leave D737 as is"; "Write it").
- **The reasons and the lessons kept** are in D742's CLOSED section. In brief: the line is 94 % D737's days, it is
  still a follow, and its case rests on in-sample numbers after many looks.
- No vault slot is taken, and D737 is unchanged.
