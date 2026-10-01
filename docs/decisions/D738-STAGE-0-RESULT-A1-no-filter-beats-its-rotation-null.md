# D738 STAGE 0 RESULT (step 3, amendment A1) — the five expected-profit filters on the NQ follow: all NOT SUPPORTED; the best (volatility × IV/RV) lifts the mean to \$33 a trade and cuts the drawdown by a third, but no filter beats its rotation null after Holm

*2026-10-01.*
- *Design: [D738-A1](D738-STAGE-0-PRE-REG-the-oracle-of-an-expected-profit-filter-on-the-nq-follow.md#amendment-d738-a1-2026-10-01-step-2-the-candidate-filters-declared-with-the-principal-before-any-is-scored)
  (9a98f75d), the principal's choices.*
- *Scorer: `scripts/stage0_d738_step3_filters.py` (4b36d6e1), one run, 0.7 min.*
- *Output: `data/stage0_d738_filters.json`, aggregates only.*
- *Step 1: [the oracle and profile](D738-STAGE-0-RESULT-the-follow-loses-in-calm-regimes-and-volatility-is-the-filter-axis.md).*

## 0. The audits

- **Step 1's checks, re-run:** the lag audit, D727's three known answers (to 1e-6), the point-in-time audit, the date
  joins, and D720's forecast and tier audits with their leak canaries.
- **The walk-forward fit:** a second implementation (the normal equations on earlier trades) agrees for every filter,
  and **all five leak canaries fired** (a fit that includes the trade's own session).

## 1. The window: the calm years are inside the burn-in

**Where the window starts.** All five filters can first decide on **2017-10-30**, which is where the declared common
window starts. Two inputs set that date:
- the 252-session percentiles (gamma and relative volatility);
- 100 earlier trades with every input defined.

**What that leaves:** 781 trades on 1,510 sessions. **2016 and nearly all of 2017, the follow's two calm losing years,
are outside it.** Only 2019 tests the calm-year question.

**Gate 1 (mechanism, gross) holds:** mean gross +\$25.07 a trade, NW t 2.96.

## 2. The table (one MNQ, \$4.0671; the window 2017-10-30 → 2023-12-29)

| book | trades (share) | net / trade (median) | gross / trade | Sharpe (Sortino); gross Sharpe | max DD | win rate | trimmed mean (ex-top) | S1 vs null p50 / p95 | p (Holm) | S2 efficiency vs p95 (p) | calibration slope | reading |
|---|---|---|---:|---|---:|---:|---|---|---|---|---:|---|
| **take-all** | 781 (52 %) | +\$21.00 (+\$13.43) | +\$25.07 | 1.00 (1.45); 1.19 | \$4,131 | 0.54 | +\$22.30 (+\$13.74) | — | — | — | — | the reference |
| F1 VOL | 510 (34 %) | +\$28.07 (+\$43.93) | +\$32.13 | 0.92 (1.32); 1.05 | \$4,131 | 0.56 | +\$29.41 (+\$19.56) | \$21.38 / \$28.34 | 0.056 (0.225) | 0.151 vs 0.192 (0.39) | +0.49 | NOT SUPPORTED |
| F2 VOL+GAMMA | 539 (36 %) | +\$25.95 (+\$40.93) | +\$30.01 | 0.90 (1.30); 1.05 | \$4,131 | 0.57 | +\$27.30 (+\$18.07) | \$21.00 / \$29.69 | 0.188 (0.376) | 0.149 vs 0.201 (0.50) | **−0.07** | NOT SUPPORTED |
| **F3 VOL+IV/RV** | 491 (33 %) | **+\$33.05** (+\$20.93) | +\$37.12 | **1.18 (1.79)**; 1.32 | **\$2,607** | 0.55 | +\$33.99 (+\$26.33) | \$21.07 / \$31.52 | **0.028 (0.141)** | 0.199 vs 0.211 (0.10) | +0.71 | NOT SUPPORTED |
| F4 VOL+RELVOL | 589 (39 %) | +\$22.51 (+\$19.93) | +\$26.57 | 0.84 (1.21); 0.99 | \$4,187 | 0.54 | +\$23.57 (+\$15.10) | \$21.33 / \$27.13 | 0.378 (0.378) | 0.137 vs 0.191 (0.72) | **−0.11** | NOT SUPPORTED |
| F5 ALL | 566 (38 %) | +\$28.44 (+\$33.68) | +\$32.50 | 1.06 (1.56); 1.22 | \$3,319 | 0.56 | +\$29.77 (+\$20.96) | \$20.96 / \$29.44 | 0.082 (0.246) | 0.171 vs 0.199 (0.23) | +0.23 | NOT SUPPORTED |

**Notes:**
- The null enumerates all 781 circular offsets of each take mask (exact).
- F3 and F5 miss 16 trades whose IV/RV is undefined; they do not take them.
- **Accuracy against the oracle is weak everywhere:** AUC 0.51–0.54, and the projection's Spearman with gross 0.07–0.10.

**By year** (net \$, with trades in brackets):

| | 2017 (from 10-30) | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|
| take-all | +82 (22) | +2,132 (112) | **−508 (134)** | +2,732 (110) | +3,268 (144) | +6,325 (132) | +2,374 (127) |
| F1 VOL | 0 (0) | +616 (14) | **+361 (3)** | +1,370 (90) | +3,268 (144) | +6,325 (132) | +2,374 (127) |
| F3 VOL+IV/RV | −12 (2) | +2,031 (51) | −362 (50) | +3,383 (68) | +2,900 (83) | +6,286 (115) | +2,000 (122) |
| F5 ALL | +13 (1) | +1,577 (67) | −576 (70) | +2,757 (78) | +3,456 (111) | +6,922 (123) | +1,947 (116) |

**Gate 3, the principal's standard with abstention:**
- **Every filter reads EARNS over its traded years, and so does take-all on this window** (6 of 7 years positive;
  \$1,362 a year without its two best).
- **F1 abstains in 2017 and 2019**, trading 3 times in 2019 and none in the window's part of 2017. It sits out the calm
  year as intended.

## 3. Predictions (D738-A1 §5)

| # | prediction | outcome |
|---|---|---|
| 1 | F1 raises the mean net above take-all and abstains in one of 2016/17/19 | **Held** (\$28.07 against \$21.00; 2019 3 trades, 2017 none) |
| 2 | F1 is SIZE-CARRIED (S1 beats its null, S2 does not) | **Failed**: S1 does not beat its null after Holm (0.225) |
| 3 | F2 VOL+GAMMA has the highest S1 | **Failed**: F3 VOL+IV/RV (\$33.05). F2 is anti-calibrated (slope −0.07) |
| 4 | at least one filter reads SUPPORTED | **Failed** |
| 5 | F5 ALL does not beat the best single-axis filter | **Held** (\$28.44 against F3's \$33.05) |

## 4. What it says

1. **No expected-profit filter on these axes is distinguishable from regime luck in-sample.**
   - Each raises the mean net a trade (by \$1.50 to \$12).
   - But a take mask of the same size and clustering, laid on the trades at a random offset, does nearly as well. The
     follow's edge is regime-shaped, and so is any mask that clusters.
   - The best, F3, sits above its null's p95 before the five-way correction (raw p 0.028) and not after (0.141).
2. **F3 (volatility × IV/RV) is the one worth remembering:**
   - it is positively calibrated (slope 0.71);
   - it has the best Sharpe and Sortino (1.18 / 1.79);
   - it cuts the max drawdown from \$4,131 to \$2,607.

   It is a post hoc best of five, in-sample, so it is a lead, not evidence.
3. **Gamma and relative volatility are anti-calibrated as pass-through terms** (slopes −0.07 and −0.11). Step 1's
   profile signs did not survive the walk-forward fit.
4. **The calm-year question is only half tested.**
   - The declared common window put 2016–17 inside the burn-in. On what remains, the unfiltered follow already meets the
     principal's standard except in 2019.
   - F1 does sit out 2019. That is one year, too few to call.
5. **It stays a follow.** None of this changes its entry. The principal declined it on that ground, and this result gives
   no reason, in-sample, to reverse that.

## 5. Options, for the principal

- **(a) Close the filter line here,** noting F3 as a lead.
- **(b) Run a post hoc check:** F1 and F3 on their own shorter burn-ins (F1 can decide from late 2016), to see the
  calm-year abstention in 2016–17. It would be descriptive only.
- **(c) A forward or vault look at F3** with its form fixed. NQ's 2024+ is unread for this question, and it would need a
  programme slot on the principal's word.
