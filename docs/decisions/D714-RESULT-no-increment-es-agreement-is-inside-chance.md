# D714 RESULT — NO INCREMENT: trading NQ F2 only when ES F2 agrees lifts the mean by $4.81 a trade, but random deletion of as many NQ trades does that 14 % of the time (efficiency rank 0.856)

*2026-09-30. In-sample, 2018-05-14 → 2023-12-29; nothing dated 2024-01-01 or later was read.*
- ***The spec:** [D714 PRE-REG](D714-PRE-REG-nq-f2-only-when-es-f2-agrees.md) (`c1069fd5`).*
- ***The runner:** `scripts/stage1_d714_nq_when_es_agrees.py` (`dc022c03`), run once in 0.15 min.*
- ***Output:** `data/stage1_d714_nq_when_es_agrees.json`.*
- ***Known answers held:** D707's frozen ES F2 exactly; D711's NQ book (274, +$20.670105); the 217 / 33 / 52 overlap.*

## The answer

| book | trades | efficiency Σnet / Σ\|net\| | mean net a MNQ trade |
|---|---:|---:|---:|
| **A: NQ F2 when ES F2 agrees** | 216 | 0.268 | **+$25.58** |
| B: NQ F2 (from 2018-05-14) | 271 | 0.223 | +$20.77 |
| dropped: B's other trades | 55 | 0.022 | +$1.88 |

**The null** (20,000 random 216-trade subsets of B):

| statistic | p50 | p95 | A's rank | role |
|---|---:|---:|---:|---|
| **efficiency** | 0.222 | **0.294** (bootstrap SE 0.0007) | **0.856** | gating |
| mean net | +$20.77 | +$27.47 | 0.880 | reported |

**NO INCREMENT.**
- **ES's agreement drops the right trades,** those 55 trades average +$1.88.
- **But in this sample, dropping any 55 of NQ's trades at random does at least as well 14 % of the time.**
- **Prediction 1 held** (rank 0.80–0.94). The lift in dollars was also as predicted ($4.81, inside $3–5).

## The books (one micro, net and gross side by side)

| | A: NQ when ES agrees | B: NQ F2 | dropped | ES on the agreement days | ES F2 |
|---|---:|---:|---:|---:|---:|
| trades | 216 | 271 | 55 | 216 | 252 |
| mean gross / net | +$29.65 / **+$25.58** | +$24.84 / +$20.77 | +$5.95 / +$1.88 | +$19.93 / +$15.51 | +$17.63 / +$13.21 |
| net HAC t | 2.90 | 2.93 | 0.12 | 2.50 | 2.48 |
| median net, hit | +$15.68, 0.574 | +$11.43, 0.554 | −$9.07, 0.473 | +$8.08, 0.556 | +$6.21, 0.536 |
| daily Sharpe (Sortino) | **0.98 (1.71)** | 0.91 (1.55) | 0.04 (0.06) | 0.82 (1.41) | 0.80 (1.37) |
| per-trade Sharpe (Sortino) | 1.16 (2.01) | 1.08 (1.82) | 0.05 (0.07) | 0.96 (1.65) | 0.93 (1.59) |
| max drawdown | $837 | $990 | $808 | $683 | $707 |
| skew | +0.62 | +0.56 | +0.14 | +0.74 | +0.81 |
| two-tailed trims, 1 / 5 / 10 % | +24.21 / +24.04 / +23.82 | +19.61 / +19.52 / +19.03 | +1.88 / +2.57 / +1.24 | +14.72 / +13.61 / +12.10 | +12.50 / +11.21 / +9.79 |
| 2022's share of net | 63 % | 67 % | more than all of it | 66 % | 60 % |
| before / after 2022-05-16 | +26.85 / +18.99 | +22.05 / +14.15 | +3.16 / −4.68 | +16.53 / +10.22 | +14.47 / +7.06 |
| long / short | +31.57 / +19.24 | +19.79 / +21.76 | −30.49 / +30.90 | +19.26 / +11.54 | +17.04 / +8.85 |
| ρ with the MACD arm | +0.007 | +0.016 | | +0.018 | +0.020 |

- **ρ of A's daily net with ES F2's is 0.96.** A is ES F2's signal traded on NQ.
- **The dropped set is 55, not 52.** The 52 NQ-only days are joined by the one opposite-direction day and two sessions
  where ES had no candidate.

**The increment by year:**

| year | A n, net | B n, net | increment |
|---|---|---|---:|
| 2018 | 17, +13.2 | 23, −0.6 | +13.8 |
| 2019 | 18, −0.8 | 19, −1.5 | +0.8 |
| **2020** | 59, +9.1 | 79, +15.4 | **−6.3** |
| 2021 | 38, +29.1 | 50, +10.2 | +18.9 |
| 2022 | 58, +59.7 | 65, +58.0 | +1.6 |
| 2023 | 26, +8.1 | 35, +4.8 | +3.3 |

**Five of six years are positive, but 2020 goes the other way and 2022 adds almost nothing.** The increment is
modest and uneven, consistent with the null's rank.

## Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | NO INCREMENT, rank 0.80–0.94 | **held** (0.856) |
| 2 | A beats B by $3–5 | **held** (+$4.81) |
| 3 | A holds at a 10 % trim | **held** (+$23.82) |
| 4 | A's 2022 share is above B's | **failed** (63 % against 67 %) |

## Meaning

- **The agreement rule is not a demonstrated improvement.** Its better numbers in D711's addendum are the size of
  gain that dropping any 55 trades produces about one time in seven. It is not carried anywhere, and it is not
  re-tested in-sample with another cut.
- **NQ F2 on its own is unchanged** as described in D711. Whether it goes to the vault is still the principal's call.
