# D738 STAGE 0 RESULT (step 1) — the NQ follow's prize is large and needs little accuracy; its winners thin out in calm regimes, and the volatility level is the strongest pre-entry axis (Spearman +0.12), then dealer gamma (−0.07); no filter is chosen

*2026-10-01.*
- *Pre-registration: [D738](D738-STAGE-0-PRE-REG-an-expected-profit-filter-on-the-nq-follow.md) (e17a3424).*
- *Runner: `scripts/stage0_d738_follow_oracle.py` (c868c917), one run, 1.6 min.*
- *Output: `data/stage0_d738_follow_oracle.json`, which holds aggregates only.*
- *In-sample 2016-02-02 → 2023-12-29: 1,941 NQ sessions, one MNQ at \$4.0671.*

## 0. The audits (all fired on their breaks)

| audit | result |
|---|---|
| D727's lag audit | its one-bar canary fired |
| the right quantity | all three books reproduce D727's recorded trades, mean net and yearly nets to 1e-6. Scoring the 15:00 close instead misses them (canary fired) |
| point in time, V4–V7 | the second implementation from the raw rows agrees. Reading today's close as yesterday's raises |
| sign, in money | 60 trades per book re-priced from the raw rows |
| the date join of V8–V11 | it agrees. Joining one session late changes 98.7 % of V9's values and raises |
| D720's forecast and tier audits | both leak canaries fired |

D691's frame was built under the lowered cut and holds no session after 2023-12-29. It joins 1,411 of the 1,941
sessions. V9 has a 250-session burn-in.

## 1. The prize

| k | trades (share) | net / trade (median) | gross / trade (median) | Sharpe (Sortino); gross Sharpe | max DD | take-all net | **oracle net** (take rate) | D736 label |
|---|---|---|---|---|---:|---:|---|---|
| 0.5 | 1,884 (97 %) | +\$3.75 (+\$1.43) | +\$7.81 (+\$5.50) | 0.27 (0.39); 0.57 | \$6,716 | \$7,057 | \$135,322 (0.51) | RESTS ON ITS BEST YEARS |
| 1.0 | 1,505 (78 %) | +\$7.14 (+\$3.93) | +\$11.21 (+\$8.00) | 0.47 (0.66); 0.74 | \$5,021 | \$10,745 | \$109,746 (0.51) | INTERMITTENT |
| **1.5** | **1,024 (53 %)** | **+\$15.22 (+\$4.68)** | **+\$19.29 (+\$8.75)** | **0.83 (1.21); 1.05** | **\$4,131** | **\$15,589** | **\$78,543 (0.51)** | INTERMITTENT |

**The oracle's winners average +\$149 a trade, against take-all's +\$15.** The payoff is in the days that continue
hard. About half the trades win. The template-bar oracle (gross ≥ 2c) is almost the same: \$78,509 on 514 trades.

**The size oracle tells us little.** It takes a trade when |close − entry| ≥ 2c = \$8.13, and at that bar it keeps 93 %
of the trades: +\$16.71 against +\$15.22. As built, it only shows that the small-move days are about break-even.

**The partial-oracle curve** at k 1.5, keeping half the trades, 1,000 draws:

| filter accuracy (Spearman) | 0 (the null) | 0.048 | 0.094 | 0.19 | 0.29 | 0.48 |
|---|---:|---:|---:|---:|---:|---:|
| mean net per trade kept | \$14.96 | \$23.27 | \$30.98 | \$46.80 | \$62.93 | \$92.99 |

**Very little accuracy pays.** The per-trade sd is large (about \$150), so a filter with a Spearman of about 0.05 already
lifts the mean by \$8. At q 0.7 the same accuracy lifts it by \$5.

**By year, at k 1.5.** The calm years have **fewer winners**, not just smaller ones:

| | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| trades | 127 | 138 | 112 | 134 | 110 | 144 | 132 | 127 |
| take-all net | −197 | −537 | +2,132 | −508 | +2,732 | +3,268 | +6,325 | +2,374 |
| oracle take rate (= win rate) | 0.46 | **0.39** | 0.58 | **0.44** | 0.56 | 0.58 | 0.58 | 0.52 |
| mean σ_oc, \$ | 59 | 54 | 136 | 107 | 243 | 231 | 419 | 264 |

Calm years average a win rate of 0.43, the other years 0.57.

## 2. The profile (k 1.5; the k 0.5 pool reads the same way unless noted)

| variable | Spearman with net | AUC vs the oracle | the quintiles' mean net, Q1 → Q5 (\$) |
|---|---:|---:|---|
| **V1 dollar volatility** (σ_oc × \$2) | **+0.122** | **0.563** | **−4.7, +2.3, +21.8, +33.3, +23.4**; win rate 0.40 in Q1 (σ < \$65) |
| **V10 prior-day dealer gamma** | **−0.071** | **0.463** | +22.1, +14.1, +25.3, **+6.4, +8.2** (high gamma is weak) |
| V8 ln(IV/RV20) | −0.049 | 0.485 | **+35.8**, +12.4, +25.3, +7.2, +5.1 (realised above implied is better) |
| V7 σ_oc's 252-day percentile | +0.045 | 0.515 | +15.5, +9.4, +16.8, +36.7, +12.0 |
| V6 volatility trend (RMS5 / σ_oc) | +0.025 | 0.531 | +16.3, +28.8, +8.5, −8.3, +30.8 (not monotone) |
| V11 overnight range | +0.020 | 0.514 | +11.7, +1.7, +34.6, +35.2, −6.9 (not monotone) |
| V4 gap with the trade | +0.010 | 0.519 | +36.3, −9.7, +20.3, +30.8, −1.5 (not monotone) |
| V9 D691's day-size tier | +0.010 | 0.532 | +41.3, +15.1, +13.9, +23.4, +29.1 (not monotone) |
| V5 yesterday with the trade | −0.009 | 0.497 | +16.5, +31.0, +20.9, +11.5, **−3.7** |
| V2 \|z\| at entry | −0.002 | 0.505 | flat |
| V3 entry clock | −0.002 | 0.490 | 10:00–10:30 +\$17.44 (798 trades); later +\$7.40 (226) |

**Categories:**
- opex days: +\$40.18 on 51 trades (non-opex +\$13.92);
- event days: +\$3.26 on 131 trades (others +\$16.98).

**On the k 0.5 pool:**
- V1 again leads (+0.059). Its Q1–Q3 (σ < \$225) lose −\$0.5 to −\$6.0, and Q4–Q5 earn +\$10.4 and +\$17.9.
- V5 has a hump. Trades *against* a moderate yesterday earn +\$28.7, and *with* a big yesterday lose −\$11.3.

## 3. Predictions (D738 §5)

| # | prediction | outcome |
|---|---|---|
| 1 | the oracle ceiling is > \$30,000 at k 1.5 | **Held** (\$78,543) |
| 2 | the calm years' oracle take rate is within 5 points of the other years' | **Failed** (0.43 against 0.57: the follow works less in calm years, not only smaller) |
| 3 | V1 has a positive Spearman with net at k 1.5 | **Held** (+0.122, the strongest of the eleven) |
| 4 | V8 has the largest \|Spearman\| with gross among V8–V11 | **Failed** (V10, dealer gamma, −0.071; V8 −0.049) |
| 5 | a Spearman of ≥ 0.05 is needed to lift the mean by \$5 at q 0.5 | **Failed**, in the follow's favour (0.048 lifts it by \$8.3) |

## 4. What it says (no filter is chosen; step 2 is the principal's)

1. **The follow does not fail in calm years by bad luck.** Its win rate drops (0.39–0.46), and the volatility level
   (σ_oc in dollars) tracks that. Below about \$65 a day, the follow loses with a 40 % win rate.
2. **The two strongest pre-entry axes are the volatility level and dealer gamma.** Both are about regime, and each has
   a mechanism story:
   - a trend continues when the market moves enough to cover the fee;
   - dealers short gamma amplify moves.
   They are weak alone (|Spearman| 0.07–0.12), but the curve says that much accuracy would pay, **if** the real filter
   behaves like the curve. That is step 3's question, scored with calibration and against the null.
3. **D703's trap applies, and here it is the point.**
   - A volatility-level filter is a volatility-regime gate. It will skip most of 2016–2017 and part of 2019, and it will
     concentrate in 2020–2022.
   - That is the principal's "do not trade when the conditions are not right". But it collides with D736's G2: a year
     the filter abstains in reads "not positive".
   - A zero year counted as an abstention would need the principal's word.
4. **It stays a follow.** A filter makes it selective but does not give it an entry signal. The principal declined it on
   that ground.

## 5. Step 2: the design questions put to the principal (D738 §6)

- **(a) The axis:**
  - volatility level (V1, in dollars, or V7, relative);
  - dealer gamma (V10);
  - IV relative to RV (V8);
  - or a combination.
- **(b) The form:**
  - the expected-profit template in dollars, where V1's units match the bar, so D703's units trap does not apply: a
    walk-forward pass-through × σ_oc\$ ≥ 2 × \$4.07;
  - or a walk-forward percentile gate.
- **(c) The pool:** filter the k 1.5 book, or let the filter select from the k 0.5 pool (97 % of sessions)?
- **(d) G2:** how a year with no trades is read.
