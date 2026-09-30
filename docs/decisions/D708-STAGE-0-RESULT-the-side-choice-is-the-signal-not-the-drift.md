# D708 STAGE 0 RESULT — SIGNAL: on ES-book short-gamma days the hourly continuation's side choice carries the edge (+$3.09 a MES trade over the time-matched drift, t 3.17, 99.9th percentile of its timing null, both legs positive); the drift adds almost nothing, because the book is nearly balanced long and short

*2026-09-30. One run of `scripts/stage0_d708_short_gamma_timing.py` (`db5092d7`), 112 s. Its
[design record](D708-STAGE-0-DESIGN-does-the-continuation-choose-its-side.md) (`9b6b10f8`) was
committed before the runner, and the runner before the run.*
- **Checks:**
  - D688's β_G was reproduced exactly.
  - D689's primary (n 2,988, +$3.7718, t 2.9339) and D692's two ES-book cells were reproduced exactly.
  - 40 decisions were re-derived from the raw 1-minute bars by a second implementation; all were equal.
  - The self-test's lag audit fired on a side taken one hour late.
  - Right-quantity: T differs from the raw mean, the per-year drift differs from the pooled drift, and N1's k = 0
    column equals T.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29. Nothing dated 2024-01-01 or later was read. D706's
  conditioner-only counts were reused for power.
- **Output:** `data/d708_short_gamma_timing.json`.

## The answer in one line

**The declared reading is SIGNAL: GO for a joint-vault pre-registration.** All five gates pass.
- The principal's objection ("it is always on, it's not really a signal?") is answered by the numbers: on these days
  choosing the side is worth about $3 a MES trade on both legs.
- The drift is real, about +$1.4 an hour. It adds to the longs and subtracts from the shorts in almost equal numbers,
  so it contributes 2% of the profit.

## 1. The timing term (P_ES: G_ES < 0, 858 days, 4,240 trades)

| statistic | $ a MES trade | day-clustered t | median |
|---|---:|---:|---:|
| **T** (side × (move − per-year clock-matched drift)) | **+3.09** | **3.17** | +2.64 |
| T with the pooled drift | +3.10 | 3.16 | |
| T in bp | +1.79 bp | 3.06 | |
| raw mean of side × move (E as proposed) | +3.16 | 3.22 | |
| **long leg over always-long** (2,234 trades) | **+2.98** | 2.28 | +3.42 |
| **short leg over always-short** (2,006 trades) | **+3.22** | 2.22 | +1.36 |
| long trades, raw | +4.37 | | |
| short trades, raw | +1.82 | | |

**Why D689's "half is drift" and this record disagree:**
- D689 read the drift from the asymmetry between the legs. Longs earn more than shorts, and the gap is 2μ: here μ ≈
  +$1.3 an hour and the continuation c ≈ +$3.1.
- But the book is 52.7% long. The drift's contribution to the book is μ × (0.527 − 0.473), about +$0.07 a trade:
  **2.2% of the raw mean**.
- The asymmetry that looked like drift is real. It moves money from the short trades to the long trades, and it does
  not create the profit.
- **In money, the principal's worry still has a practical edge.** The short trades gross only +$1.82 at MES, below the
  $4.42 round trip. They beat always-short by $3.22 because always-short loses the drift. They are the right side of
  the trade, but a thin one to pay for.

**The drift at each clock** (P_ES, always-long, pooled): 10:30 +$1.37, 11:30 +$1.63, 12:30 −$1.84, 13:30 +$0.45,
14:30 +$5.33.

## 2. The gates

| gate | result | passes |
|---|---|---|
| G1 timing | T +$3.09, t 3.17; **N1 (839 enumerated rotations of the side schedule) p50 +$0.05, p95 +$1.68, percentile 0.999** | yes |
| G2 both legs | long +$2.98, short +$3.22 | yes |
| G3 the gamma contrast | τ short − long within same-day-rv deciles **+1.82 bp**; N2 (1,970 label rotations) p50 −0.03, p95 +0.93, **percentile 0.998** | yes |
| G4 not one episode | ex Feb–Apr 2020 +$3.16 (t 3.32); ex 2022 +$3.08 (t 3.32); **7 of 8 years positive** | yes |
| G5 the unmeasured part (P_ES\SUM) | +$1.99 (t 1.60) | yes (point estimate) |

The nulls are enumerated, so the p95s have SE 0.

## 3. The populations

| population | days | trades | T $ (t) | long leg / short leg | raw $ (t) |
|---|---:|---:|---|---|---|
| **P_ES** (G_ES < 0) | 858 | 4,240 | **+3.09 (3.17)** | +2.98 / +3.22 | +3.16 (3.22) |
| P_ES ∩ SUM (G_SUM < 0) | 603 | 2,988 | +3.62 (2.83) | +3.56 / +3.68 | +3.77 (2.93) |
| P_ES \ SUM (G_SUM ≥ 0) | 255 | 1,252 | +1.99 (1.60) | +1.75 / +2.26 | +1.71 (1.33) |
| **long gamma** (G_ES ≥ 0) | 1,131 | 5,520 | **−0.18 (−0.38)** | −0.10 / −0.26 | −0.21 (−0.44) |

- **The mechanism contrast is clean.** The same rule on long-gamma days is a zero, and it stays a zero on both legs.
- **The never-measured days (P_ES\SUM) carry the effect at about half strength.** These are days when the ES book is
  short but SPX GEX outweighs it. The sign is right, but the t is 1.60, not significant alone.
  - They are 67 of the vault's 187 ES-book-short days. An unseen test on P_ES therefore mixes a stronger and a weaker
    part, in about the in-sample proportion (vault 64/36, in-sample 70/30).

**T by year** (P_ES, $ a MES trade, trades): 2016 +2.38 (384), 2017 −0.44 (255), 2018 +3.14 (626), 2019 +1.27 (507),
2020 +3.29 (431), 2021 +2.57 (425), 2022 +3.13 (969), **2023 +6.47 (643, t 2.93)**. It is positive in 7 of 8 years,
and the most recent year is the strongest. The effect does not lean on 2022, where it is at its average.

**T by clock:** 10:30 +3.39 (t 1.38), 11:30 +2.25, **12:30 +1.14 (t 0.60, the weakest)**, **13:30 +4.96 (t 2.39)**,
14:30 +3.73. Each clock has about 850 trades. No clock was dropped: the design kept all five (decision 3).

## 4. The component line and the four groups (E as proposed, P_ES, 537 trades a year)

| book | net Sharpe (Sortino) | gross Sharpe (Sortino) | mean net / trade | median net | hit | max DD | annual vol | ρ with the arm |
|---|---|---|---:|---:|---:|---:|---:|---:|
| **E, 1 MES ($4.42)** | **−0.45 (−0.62)** | +1.14 (+1.73) | −$1.26 | −$1.92 | 48.0% | $8,276 | $1,483 | −0.042 |
| E, 1 full ES ($19.24) | **+0.45 (+0.65)** | +1.14 (+1.73) | +$12.39 | +$5.76 | 50.7% | $18,972 | $14,830 | −0.039 |
| always-long, same windows, MES | −1.05 (−1.38) | +0.51 (+0.75) | −$2.98 | | 48.3% | $13,283 | | +0.071 |
| always-long, same windows, full ES | −0.17 (−0.24) | +0.51 (+0.75) | −$4.81 | | | $41,915 | | +0.075 |

**Performance.**
- Gross is +$3.16 a MES trade, 0.36 × 2c, so the breakeven round trip is $3.16 at MES. The signal is the same at both
  sizes (gross Sharpe +1.14).
- The MES fee takes more than the whole gross. At full ES the round trip is 0.61 of gross, and the book nets +0.45.

**The trade distribution (full ES, net; MES in brackets).**
- n 4,240, mean +$12.39 (−$1.26), median +$5.76 (−$1.92), win rate 50.7% (48.0%), payoff 1.03.
- Skew −0.03, kurtosis 9.0.
- Trimming 1%: ex-top −$12.40, ex-bottom +$36.88, **both tails +$12.09**. The symmetric trim leaves it intact.

**Dependence.**
- **Full ES:** longs +$54.7k, shorts −$2.1k net.
- The top 10 trades are 67% of the full-ES net. That share is high for a book whose trimmed mean holds, and it follows
  from a small edge on 4,240 trades.
- **Full ES by year:** 2016 +1.8k, 2017 −4.6k, 2018 +7.3k, 2019 −3.1k, 2020 +5.2k, 2021 +6.1k, 2022 +11.3k,
  2023 +28.6k. 2023 is 54% of the net.

**The price question E rests on** (P_ES, by year):

| year | mean ES | gross $ / bp a MES trade | round trip in bp at MES | fee ÷ gross |
|---|---:|---|---:|---:|
| 2016 | 2,022 | +2.40 / +2.37 | 4.37 | 1.84 |
| 2017 | 2,404 | +0.13 / +0.12 | 3.68 | 33 |
| 2018 | 2,692 | +3.09 / +2.32 | 3.28 | 1.43 |
| 2019 | 2,874 | +1.31 / +0.83 | 3.07 | 3.37 |
| 2020 | 3,026 | +3.12 / +1.85 | 2.92 | 1.42 |
| 2021 | 4,244 | +3.35 / +1.53 | 2.08 | 1.32 |
| 2022 | 4,052 | +3.09 / +1.62 | 2.18 | 1.43 |
| 2023 | 4,221 | +6.37 / +3.05 | 2.09 | **0.69** |

- **The claim is half right.** The fee in bp did halve over the sample (4.37 → 2.09), and the gross in bp did not
  shrink with it. The mean gross is about +1.8 bp.
- **At the unseen period's price level** (ES about 6,000–6,900), the round trip is about 1.3–1.5 bp. At the in-sample
  gross of about 1.8 bp, that is a **thin positive net at MES, about +0.3–0.5 bp (~$1–1.5 a trade)**. This is a
  projection from the in-sample bp, not a measurement. A component at MES would be marginal. At full ES it is a
  Sharpe-0.45 book with an ES-sized drawdown.

**Nulls.** N1 and N2 (§2), enumerated, p50/p95 shown. Both are decisive.

**Correlation.** ρ −0.04 with the admitted MACD arm. ρ with D707's F2 was not computed: its runner exposes no
in-sample daily series without its vault path. The clocks are adjacent (this book's last exit is 15:30, F2 enters at
15:30) and never overlap.

## 5. Power for the joint run

- **Count:** 288 unseen ES-book-short sessions (D706: 187 vault + 101 clean) × 4.94 trades a day = 1,423 trades.
- **Signal-to-noise:** T / sd(τ) without the crash window is 0.052. Clustering changes the t by × 1.01.
- **Expected t 1.98 at the full in-sample effect (a one-sided 5% pass probability of 0.63); 0.99 at half (0.26).**
- The half-effect row is the realistic one, for three reasons:
  - the grid was profiled five times before this (D684, D689, D690, D692, D693);
  - the timing statistic is new, but the population is not;
  - 2023 is the strongest year, and unseen data regresses.

## 6. What it decides, for the principal

1. **E is a signal, not an always-on long.** The side it chooses is right about $3 a MES trade more often than chance,
   on both sides, only on short-gamma days, beyond the day's volatility, in 7 of 8 years. The drift was a real
   long/short asymmetry, not the source of the profit.
2. **It is the first direction result in the short-gamma line that the unseen data can adjudicate.**
   - The pass probability is 0.63 at the full effect, against D706's best of 0.39 for the once-a-day constructions,
     and 0.26 at half.
   - This is still a coin flip at a realistic effect, and the one-look rule means a miss closes it.
3. **As a component it is marginal at MES.**
   - In-sample net is negative in 7 of 8 years at MES; only 2023, the highest-priced and strongest year, nets
     positive.
   - At the unseen period's prices the MES net projects to a thin positive. At full ES it is a Sharpe-0.45 book with
     a $19k drawdown.
   - A pre-registration should make the primary gate gross (the timing term), with MES net > 0 as the second gate,
     following D650's NG structure. A gross pass with a net miss would read MECHANISM ONLY.
   - **The dollar book is year-concentrated even though T is not.** 2023 is 54% of the full-ES net: it is the
     highest-priced year and T's strongest. D705 failed F2 on this shape (one year > 50%). T by year passes G4 in
     trade units, and a pre-registration should state which unit its one-year gate uses.
4. **The next step is a pre-registration for the joint vault run.** It freezes this rule, T as the primary, the both-legs
   gate and the long-gamma contrast, and it needs a programme slot (10 is free). It waits for the principal's word.

## CLOSED, 2026-09-30, on the principal's word

The principal, after [D713](D713-DIAG-RESULT-e-at-mes-no-single-cut-clears-the-fee.md): "Close E - If even the
oracle's best is 0.93 dollars 106 times a year we stand no chance".
- **Closed under R15:** E, the hourly continuation on ES-book short-gamma days, at the size the account trades (one
  MES). It covers D708's rule and any cut of it.
- **Why:**
  - the side choice is real (+$3.09 over the drift);
  - but the best bucket in D713's oracle profile nets about +$0.92 a trade on 106 trades a year, about $100 a year at
    one MES, and that is before the selection from 58 buckets is priced.
- **D712 was already withdrawn.** Programme slot 10 stays free.
- **What stays on the record:** the finding that short dealer gamma makes the hourly side choice right more often than
  chance is kept as mechanism evidence, beside gamma's established role as a size predictor (D665).
