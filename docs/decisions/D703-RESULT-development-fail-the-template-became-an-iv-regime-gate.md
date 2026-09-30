# D703 RESULT — DEVELOPMENT FAIL: the expected-profit filter nets +$11.02 a MES trade on 211 trades but at t 1.51, and 167 of the 211 fall in 2022; in dollars the template became an implied-vol regime gate and lost the prior hour's relative size

*2026-09-30. In-sample development, walk-forward, 2017-06-23 → 2023-12-29 (1,565 evaluated candidates). The slice
2024-01 → 2025-02 was not read, and the vault was not touched.*
- ***The spec:** [D703 PRE-REG](D703-PRE-REG-the-last-hour-expected-profit-filter.md) (`6c17028a`), the principal's
  design after [D702](D702-DIAG-the-last-hour-edge-is-big-move-shaped.md).*
- ***The runner:** `scripts/stage1_d703_last_hour_ep_filter.py` (`1d06bc87`), run once in 3.1 min. Output:
  `data/stage1_d703_last_hour_ep_filter.json`, statistics only. GEX: SqueezeMetrics, credited.*
- ***Known answers held:** D618, D702's lines, D691 and D688. Both lag canaries fired.*

## The answer in one line

**DEVELOPMENT FAIL: gates (b) and (c) fail. Under the pre-registration the line closes again,** with the reason
recorded below.
- **The filtered book is positive, but not significant.**
- **It is one year:** 79 % of its trades are in 2022.
- **The template's dollar bar turned it into an implied-vol regime gate.** The prior hour's relative size, D702's best
  input, never reached the bar on its own.

## 1. The gates

| gate | observed | pass |
|---|---|---|
| (a) calibration slope, realised gross on projected gross | **+1.11** (intercept −0.57) | ✓ |
| (b) filtered mean net > 0 at one-sided HAC t ≥ 1.645 | **+$11.02, t 1.51** | ✗ |
| (c) above the exact p95 of the enumerated joint rotation of the three features | p50 −$5.73, **p95 +$46.28**; rank 0.82 | ✗ |
| (d) positive without Feb–Apr 2020 | +$7.29 | ✓ |

**Gate (c) is uninformative as built, and this is recorded as a design fault.**
- At 1,397 of the 1,813 offsets, the scrambled features never cleared the bar, so the filtered book was empty and its
  mean undefined. Only 416 offsets entered the null.
- The per-trade mean of a near-empty book swings widely, which is what put the p95 at +$46.
- **A count-matched statistic would have been the right null.** The pre-registration did not declare one.
- **The verdict does not rest on (c):** (b) fails independently.

## 2. The filtered book (1 MES, $4.42 a round trip)

| | filtered | take everything (same 1,565 candidates) |
|---|---:|---:|
| trades (a year) | 211 (32.4) | 1,565 (240) |
| mean gross / mean net | +$15.44 / **+$11.02** | +$4.24 / −$0.19 |
| HAC t (net) | 1.51 | −0.14 |
| hit (net), median, payoff | 0.521, +$3.08, 1.26 | |
| skew | +1.04 | |
| per-trade Sharpe (Sortino), net | 0.62 (1.07) | |
| per-trade Sharpe, gross | 0.87 | |
| daily Sharpe (Sortino), net | 0.57 (0.99) | −0.05 (−0.07) |
| max drawdown | $1,007 | $2,128 |
| 1 % trims: ex-top / ex-bottom / both | +$6.63 / +$14.23 / +$9.83 | |
| long / short net | +$12.29 / +$9.20 | |
| ρ with the MACD arm | +0.05 | |

**By year** (n, net a trade):

| 2017–19 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|
| none | 18, +$51.00 | 9, +$17.80 | **167, +$7.81** | 17, −$3.39 |

- Before 2022-05-16 the book nets +$29.55; after, −$1.73.

**The component line:** net Sharpe 0.57 (Sortino 0.99) at one MES, $4.42 a round trip, hit 52 %, skew +1.04, gross
Sharpe 0.87 against net 0.62 per trade, ρ +0.05 with the arm. **It is not entered: development failed, and it is
one year.**

## 3. Why: what the filter became

**The size model forecasts size well:** Spearman of P with the realised |move| is 0.47.
- **Its final slopes:** ln IV 19.1, ln(|F5|/σ) 4.8, **G_SUM 0.0.** The sign-constrained fit dropped gamma.
- **P ranges** $7.43 / $28.18 / $67.55 at the 5th / 50th / 95th percentiles. 0.8 % of forecasts sit at the $1.25
  floor.
- **π̂ ranges** −0.10 / +0.13 / +0.20.

**The rule clears $8.84 only when π̂ × P is large in dollars, and P is large in dollars only when implied vol is
high.** That makes the filter a volatility-level gate: 2022, the 2020 crash and a few other high-IV sessions.

**The ablations confirm it:**

| size model | trades over the window | mean net | t |
|---|---:|---:|---:|
| ln IV alone | 104 | +$7.50 | 0.85 |
| **ln(\|F5\|/σ) alone** | **4** | +$34.02 | — |
| G_SUM alone | 0 | — | — |

**The prior hour's size is a relative measure,** normalised by its own σ. Without a volatility level in the model,
its projected dollar move almost never clears the bar. **So the input that carried D702's profile (top 20 % by
|F5|: +$8.87, Sharpe 0.74, six of eight years) could not express itself through this rule.** The template's dollar
bar and D702's relative signal do not fit together.

**Placement (D690):**
- Spearman of projected gross with realised gross: **0.031.** On D702's curve that sits between break-even (≈0.02)
  and Sharpe 0.5 (≈0.07).
- AUC against the oracle label: 0.539; precision 0.52 on a base rate of 0.46; recall 0.15.
- The filter captures 8.5 % of the oracle's net.
- **The calibration is honest:** slope 1.11, with the top two projected deciles realising +$11.88 and +$17.32.

## 4. Predictions (§6 of the pre-registration)

| # | prediction | outcome |
|---|---|---|
| 1 | calibration slope positive but below 1 | **failed**: +1.11, positive and slightly above 1 |
| 2 | 30–60 trades a year at +$3 to +$9 net | **failed**: 32 a year at +$11.02 (above the range), and one year carries it |
| 3 | gate (c) passes, with its p95 near $0 | **failed**: the null was mostly empty books, p95 +$46 |
| 4 | the \|F5\| ablation does about as well | **failed**: 4 trades. The dollar bar silenced it (§3). |
| 5 | 2016–17 and post-2022 are the weakest | **partly**: post-2022 is weak (−$1.73); 2016–17 took no trades |

## 5. What this leaves (routing)

**Under the pre-registration's §2, DEVELOPMENT FAIL closes the line again.**
- **The slice is not spent.**
- **The lesson is about form, not the mechanism.** D702's finding stands: the edge is big-move-shaped, and the prior
  hour's relative size is knowable at 15:30. D703 shows that the expected-profit template in dollars can't carry a
  relative signal. It selects the volatility regime instead.

**Reopening with a different form would be a new pre-registration on the same in-sample window,** so a second look.
The forms would be:
- the walk-forward threshold on |F5|/σ, the option the principal did not choose;
- a template with the size model's target normalised by volatility.

**Either is the principal's call, and would state that this is a second look.**
