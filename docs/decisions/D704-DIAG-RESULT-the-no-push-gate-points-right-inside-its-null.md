# D704 DIAG RESULT — NO INFORMATION: the no-aggressive-push gate ranks V1's trades the right way (Spearman +0.044, the upper half +$18.72 a trade against +$2.23), but inside its null (84.6th percentile), about one standard error from zero

*2026-09-30. One run of `scripts/diag_d704_no_push_gate_on_v1.py` (`aca1babb`), 99 s. Its
[design record](D704-DIAG-DESIGN-a-no-aggressive-push-gate-on-v1.md) was committed before the runner, and the runner
before the run.*
- **Checks:** D688 reproduced. V1 was reproduced exactly (572 trades, +$10.4748).
  - The signed-flow fixture's validation flag is true, and it covers all 1,989 panel sessions.
  - 30 windows were re-derived by a loop, and the check fired on a 15-minute shift.
  - The sign and the residualisation were asserted.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, a diagnostic. No threshold is fitted.
- **Output:** `data/d704_no_push_gate_on_v1.json`.

## The answer in one line

**The declared reading is NO INFORMATION.** Scoring V1's trades by how little aggressive buying came with the last
hour's rise ranks them in the direction the mechanism predicts:
- the upper half nets +$18.72 a trade (median +$10.58);
- the lower half nets +$2.23.

**But the ranking's Spearman (+0.044) sits at the 84.6th percentile of its rotation null.** That is about one standard
error from zero (SE 0.042). The data cannot tell it from chance.

## 1. The oracle (D699 §1, shown again)

- 50.5% of V1's 572 trades win after cost.
- Their mean net is +$110.07.

## 2. The expected imbalance for a move

- **The fit:** Î = +0.0004 + 0.0175·z over 49,725 windows, R² 0.32.
- **What it says:** one standard deviation of a one-hour rise comes, on average, with 1.75 points more aggressive
  buying out of every 100 contracts.

## 3. The accuracy assessment

| score | Spearman vs net (rotation p50 / p95, percentile) | vs drift excess | AUC vs oracle | calibration slope (on rank) | net by quintile, low → high |
|---|---|---:|---:|---:|---|
| **S_B** (less buying than the move predicts) | **+0.0436** (−0.0005 / +0.0686, 0.846) | +0.0415 | 0.538 | +26.0 | +$1.69, +$11.29, +$0.11, +$15.65, +$23.59 |
| S_A1 (less buying, raw) | +0.0518 (−0.0006 / +0.0630, 0.902) | +0.0472 | 0.521 | +32.1 | −$15.12, −$0.64, +$32.36, +$18.53, +$17.41 |

**The upper half by S_B against V1:**

| | trades | mean net | median | hit | net Sharpe (Sortino) | edge per unit of noise |
|---|---:|---:|---:|---:|---|---:|
| V1, all | 572 | +$10.47 | +$0.58 | 50.5% | +0.63 (+1.06) | 0.064 |
| S_B upper half | 286 | **+$18.72** | +$10.58 | 54.2% | **+0.70 (+1.21)** | 0.108 (**1.69×**) |
| S_B lower half | 286 | +$2.23 | | | | |

The lift is 1.69× against a declared 1.70×. The declared reading only looks at the lift after the ranking has
cleared its null, and the ranking did not.

## 4. Checks against the known false positives

- **The mechanism check:** the same score on V1's trades on long-gamma days has a Spearman of −0.022 on 1,024 trades,
  so there is nothing there. That is what the hedging story predicts, but it is only weak support, because the
  short-gamma figure is itself not significant.
- **Not a 2022 artefact:** without 2022 the Spearman is +0.084.
  - By year: 2016 +0.14, 2017 +0.34, 2018 +0.01, 2019 +0.07, 2020 −0.10, 2021 +0.13, 2022 −0.05, 2023 +0.17.
  - It is positive in 6 of 8 years. The two negative years are the two crisis years.
- **It leans toward bigger moves:** S_B has a Spearman of +0.29 with the window's signed move and +0.20 with its size.
  The gate favours rises that were large for the little aggressive buying behind them, which is the design's intent,
  not a small-move filter.
- **Truncated windows:** 46% of the trades have a window cut at the open. On full windows only, the Spearman is +0.052.

## 5. What it says

1. **The no-push reading points the way the mechanism predicts.** It shows in 6 of 8 years, is stronger outside 2022,
   and is absent on long-gamma days. It agrees in sign with D695's reading of the same flow on a different set of
   trades (−0.031 for aggressive buying).
2. **It is not detectable on this sample.** A Spearman of 0.044 on 572 trades is one standard error.
3. **The line now holds several weak signals that all point the same way,** none of them established:

   | signal | where | strength |
   |---|---|---|
   | V1's timing | D699 | t 1.64 against the drift |
   | the 15-minute channel | D700–D701 | t 1.86, independent of V1 |
   | this gate | D704 | about 1 SE |

   **No pre-2016 data can add sample.** The ES options book starts 2016-01-04, the Sierra files hold no ES contract
   before ESZ15, and the Databento archive lacks most index day sessions before 2016. The only unseen data is the vault.
