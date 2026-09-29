# D693 STAGE 0 RESULT — the principal's per-cell filter fails at MES: anti-calibrated (slope −2.2), worse than the gate alone (−0.27 against +0.28), and under its rotation null; the cells are too noisy to estimate at this trade's size

*2026-09-29. One run of `scripts/stage0_d693_short_gamma_long_filter.py` (`f597edd9`, committed with the
[design record](D693-STAGE-0-DESIGN-the-short-gamma-long-filter-at-mes.md) before the run), 111 s.*
- **Checks:** D688 reproduced; the lag audit re-derived six projections and fired when today's trades were included.
- **What it is:** in-sample development, no slice spent.
- **Output:** `data/d693_short_gamma_long_filter.json`.

## The answer in one line

**Not useful in-sample: all three of the declared tests fail.**
- **(a)** The calibration slope is −2.23. The cells projected to lose realised the most.
- **(b)** The filtered book loses (net Sharpe −0.27) where the gate alone makes +0.28.
- **(c)** The filtered book sits at the 18th percentile of its rotation null (p50 +0.06, p95 +0.64).

## 1. The oracle (the ceiling), at MES

The universe is short-gamma days (G_SUM < 0), long only, 1 MES. After the 250-session burn-in it holds 1,418
trades, 205 a year.
- **52% are winners** (net > 0).
- **The oracle** takes exactly those winners: +$45.42 a trade, 107 a year, net Sharpe +5.6. That is the ceiling.

## 2. The books (CLAUDE.md's four groups; daily series over the evaluation sessions)

| | gate alone (every universe trade) | the filter (per-cell projection > $0) |
|---|---|---|
| trades a year | 205 | 92 (45% of the universe) |
| **net Sharpe (Sortino)** | **+0.28 (+0.45)** | **−0.27 (−0.40)** |
| gross Sharpe (Sortino) | +1.16 (+2.03) | +0.28 (+0.45) |
| mean net per trade (clustered t) | +$1.36 (0.74) | −$2.15 (−0.71) |
| median net; hit rate | +$1.83; 52.1% | +$0.58; 50.9% |
| mean gross | +$5.78 | +$2.27 |
| trimmed 1%: ex-top / ex-bottom / both | −$1.35 / +$3.55 / +$0.82 | −$4.81 / +$0.19 / −$2.47 |
| skew; kurtosis | +0.31; 8.7 | −0.01; 7.4 |
| max drawdown; annual vol | $1,979; $1,002 | $2,684; $723 |
| ρ with the MACD arm | +0.03 | +0.09 |
| net by year | 2017 −186, 2018 −373, 2019 −244, 2020 −222, 2021 +942, 2022 +604, 2023 +1,414 | 2017 +62, 2018 −296, 2020 −203, 2021 +728, 2022 −2,528, 2023 +882 |

**The largest trade in both** is 2022-01-26, at −$433.

**The gate alone** is positive in the body (the median is above the mean), but four of its seven evaluation years
lose. Its +0.28 is carried by 2021–23, and it is under the 0.4 a component needs.

## 3. The accuracy assessment against the oracle (D690's library)

| take rate | precision (base 0.521) | recall | balanced accuracy | AUC | Spearman with gross | capture of the oracle | calibration slope |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.446 | 0.509 | 0.436 | 0.490 | **0.491** | **−0.030** | −0.040 | **−2.23** |

**Calibration by projection bin, projected → realised mean net:**

| bin | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|
| projected → realised | −$3.16 → **+$8.17** | −$1.34 → +$4.78 | −$0.58 → −$0.50 | +$0.18 → +$4.42 | +$0.93 → −$6.74 | +$2.64 → −$0.85 |

**The filter's accuracy is below chance.** The trades it rejected did better than the ones it kept.

## 4. Where it sits on the partial-oracle curve (at the filter's take share of 45%)

| ρ (realised Spearman) | 0 (0.00) | 0.05 (0.05) | 0.1 (0.09) | 0.2 (0.19) | 0.3 (0.29) | 0.5 (0.48) | 1 |
|---|---|---|---|---|---|---|---|
| net Sharpe | +0.14 | +0.60 | +0.97 | +1.68 | +2.36 | +3.53 | +5.56 |

The filter's Spearman is −0.03, below even the random filter's +0.14. On this universe, a real forecast with a
Spearman of 0.05 would be worth about +0.6.

## 5. Why it failed: the cells cannot be estimated at this size

**The cells in hindsight** (the whole sample, descriptive), mean net and win rate:

| | low vol | mid vol | high vol |
|---|---|---|---|
| with the day's move | n 136, −$3.89, 45% | n 344, +$3.13, 52% | n 615, +$0.31, 54% |
| against the day's move | n 16, +$6.44, 62% | n 101, +$1.40, 50% | n 349, +$2.23, 50% |

- **The noise:** the per-trade sd is about $65, so a cell of 100–600 trades has a standard error of about $3–6 on its
  mean. The differences between cells are about $1–7.
- **The consequence:** a walk-forward cell mean, from even fewer trades, is mostly noise. It flips sign from month to
  month, and the filter kept trading the cells that had last looked good. The low-volatility cells were rarely traded
  (0% taken), which worked as intended; the rest was noise.
- **A design lesson for any per-cell filter:** it can separate only differences larger than about 2 × $65 / √(trades
  in the cell). At this trade's size, finding a $2 difference needs about 4,000 trades a cell. **A per-cell
  expected-profit filter needs cell differences larger than its own noise, and here they are not.**

## 6. What this leaves, for the principal

1. **The filter as designed is closed.** It is anti-calibrated, and the declared reading fails on all three counts.
2. **The gate alone** (short-gamma days, long only, 1 MES) is +0.28 net and +$1.36 a trade (t 0.74), with
   losing years 2017–2020. That is below a component's bar, and it is the whole of what this universe offers at
   MES without new information.
3. **The oracle and the curve say where the value is.** 52% of the universe's trades are winners at +$45 and more; a
   forecast with a Spearman of 0.05 would lift the book to about +0.6.
4. **None of the inputs tried so far carries that forecast:**
   - gamma (beyond the gate);
   - volatility;
   - alignment;
   - time of day;
   - the size of the last move.

   The next step, if any, is a new directional input, not a new combination of these.
