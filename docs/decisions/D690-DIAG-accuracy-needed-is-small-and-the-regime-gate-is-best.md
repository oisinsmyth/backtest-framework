# D690 DIAG — the oracle yardstick: on this trade a filter pays once its rank correlation with the trade's gross passes about 0.01; every real filter sits at 0.04–0.06, the regime gate is still the best of them, and a perfect SIZE forecast is worth almost nothing

*2026-09-29. One run of `scripts/diag_d690_oracle_filter.py` (`cc7a69bc`), 180 s.*
- **Declared first:** the [D690 design record](D690-DESIGN-the-oracle-filter-and-the-accuracy-assessment.md)
  (`114345c6`) and the runner's docstring, both committed before the output was read.
- **What it is:** post hoc on spent in-sample data. It is a method and a diagnostic, not a verdict, and no slice was
  spent.
- **Reproduction:** D688's β_G reproduced exactly.
- **Output:** `data/d690_oracle_filter.json`.
- **The yardstick** is the new library `backtest_framework.validation.filter_oracle` (12 unit tests).

## The answer in one line

**Accuracy is not what's missing; information and the take rule are.**
- **A little accuracy pays on this trade, at full ES:** the 60-minute continuation on every day.
  - **Breakeven:** a filter whose ranking correlates with the trade's gross at Spearman ≈ 0.01 already breaks even.
  - **A component:** about 0.03 reaches a component-grade Sharpe of 0.5.
  - **The mechanism:** single trades have a standard deviation of about $650 at full ES, so a slight tilt towards the
    big winners is enough.
- **The real filters and the curve:**
  - Every real filter has a Spearman of 0.04–0.06. The partial-oracle curve says that accuracy is worth a Sharpe of
    about 0.7–1.0.
  - The real books realise 0.13–0.54.
  - **The regime gate (G_SUM < 0) keeps the most of it (+0.54)**, and no model-based filter beats it under the
    declared rule.
- **What decides it:**
  - how the take rule spends the accuracy;
  - whether the projection is calibrated. D689's projection was anti-calibrated (slope −1.7), which alone would have
    predicted its failure.

## 1. A — the oracle, the ceiling (evaluation rows after a 250-session burn-in: 8,555 candidates, 32% on short-gamma days)

| filter (full ES, $19.24 a round trip) | daily net Sharpe | mean net per trade | trades a year |
|---|---:|---:|---:|
| take everything | −0.42 | −$6.31 | 1,240 |
| **the oracle: realised net > 0** | +14.4 | +$349 | 588 (47% taken) |
| the oracle at the template's bar (gross ≥ 2c) | +14.3 | +$377 | 544 |
| **size-only oracle:** the top 20% by realised \|next-hour move\|, direction by the rule | +0.33 | +$22 | 248 |
| size-only oracle, the top 40% | +0.34 | +$12 | 496 |

**At MES size:** take everything −2.10, the oracle +13.6, the size-only oracle top 20% −0.04.

**The size-only oracle is the important line.**
- **What it shows:** perfect knowledge of how far the next hour will move, with the direction left to the rule, lifts
  this trade only from −0.42 to +0.33.
- **Why:** the continuation is right about half the time, so knowing size scales the winners and the losers alike.
- **The consequence:** gamma's proven strength, forecasting size (D665, D683), cannot rescue a trade that has little
  direction per unit of size. D668's size oracle found the same for the opening break.

## 2. B — the partial-oracle curve: how accurate must a filter be?

This is a forecast of the realised gross with normal-score correlation ρ. It keeps the top 20% of candidates, over
200 draws. ρ = 0 is the null.

| ρ | 0 | 0.05 | 0.1 | 0.15 | 0.2 | 0.3 | 0.5 | 1 |
|---|---|---|---|---|---|---|---|---|
| realised Spearman with the gross | 0.001 | 0.049 | 0.095 | 0.143 | 0.192 | 0.287 | 0.482 | 1.000 |
| mean net per trade | −$5.9 | +$28.6 | +$62.5 | +$97.1 | +$133.2 | +$200.7 | +$338.3 | +$671.2 |
| **daily net Sharpe** (p05, p95) | **−0.18** (−0.66, +0.27) | **+0.85** (+0.32, +1.35) | **+1.84** (+1.25, +2.38) | +2.82 | +3.75 | +5.30 | +7.62 | +11.27 |

At q = 40% it is almost the same: +0.73 at ρ 0.05 and +1.74 at ρ 0.1.

**Reading it:**
- Interpolated, a filter breaks even at a Spearman of about 0.01 and reaches a Sharpe of 0.5 at about 0.03.
- **Each further 0.05 of accuracy is worth about +1 of Sharpe.**
- **The same curve for a SIZE forecast is flat:** −0.21 at ρ 0, and +0.33 even at ρ 1.

**The curve is an upper envelope for real filters.** Its errors are independent from trade to trade, which
diversifies them within a day. A real filter's errors cluster in regimes and days.

## 3. C — five real filters, prior-only (walk-forward, refit monthly on strictly earlier days)

Accuracy is scored against the oracle label (net > 0 at full ES, base rate 0.474). The books are at full ES.

| filter | take rate | precision | recall | balanced accuracy | AUC | Spearman with gross | curve's Sharpe at that accuracy | **real net Sharpe (Sortino)** | trades/yr | mean net | rotation null p50 / p95 (percentile) | calibration slope |
|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---|---:|
| **R1 regime gate** | 0.317 | 0.517 | 0.346 | 0.527 | 0.527 | +0.042 | ≈ +0.70 | **+0.54 (+0.79)** | 393 | +$19.85 | −0.23 / +0.26 (**0.992**) | — |
| R2 D689's π·\|m\| | 0.015 | 0.472 | 0.015 | 0.500 | 0.526 | +0.039 | — | −0.28 (−0.35) | 18 | −$64.13 | −0.09 / +0.52 (0.321) | **−1.68** |
| R3 linear expected profit | 0.144 | 0.532 | 0.162 | 0.517 | 0.536 | +0.044 | ≈ +0.74 | +0.35 (+0.52) | 179 | +$18.14 | −0.10 / +0.45 (0.905) | +0.38 |
| R4 logistic, P ≥ 0.5 | 0.299 | 0.519 | 0.328 | 0.527 | **0.550** | **+0.056** | ≈ +1.0 | +0.13 (+0.18) | 371 | +$4.69 | −0.22 / +0.28 (0.867) | — |
| R5 regime-cell expected profit | 0.075 | **0.536** | 0.085 | 0.509 | 0.543 | +0.045 | ≈ +0.76 | +0.28 (+0.44) | 93 | +$21.77 | −0.14 / +0.50 (0.865) | **+1.03** |

**At MES size,** every one is negative: R1 −0.14, R3 −0.13, R4 −0.55, R5 −0.04, R2 −0.39.

**Better than the regime gate (declared):** none of R2–R5. The gate is the only filter above its rotation p95.

## 4. What the assessment says about building a better filter

1. **Check the calibration before trading the filter.**
   - D689's projection (R2) is anti-calibrated: slope −1.68, with its lowest projection bin realising +$95 and its
     highest +$25. That test would have killed it on the in-sample data, before any trade.
   - R3's linear projection is overconfident (slope 0.38).
   - R5's per-regime constant is honest (slope 1.03), which confirms D689 §4's design point.
2. **The take rule spends the accuracy.**
   - The logistic model is the most accurate (AUC 0.550, Spearman 0.056), yet has the weakest positive book (+0.13).
     P ≥ 0.5 takes 30% of the candidates, marginal ones included.
   - The gate at a similar accuracy (0.042) takes the right 32%, whole regimes rather than scattered rows.
   - **Accuracy has to be converted by a threshold at the expected-profit bar on a CALIBRATED projection.**
3. **The lever is information, not model form.**
   - The features available at the decision (gamma, volatility, the last move, the hour, the day's move so far) cap
     accuracy at a Spearman of about 0.05, whether they are used linearly, logistically or as a regime gate.
   - The curve says doubling that to 0.1 would roughly double the Sharpe. **A better filter needs a new input,** not a
     better fit.
4. **Precision lifts by 4–6 points over the 0.474 base rate.**
   - It is the whole edge: at full ES, 52–54% winners at payoff about 1 clears the round trip.
   - It is also why MES never pays: its round trip is 2.3× dearer per point.

## 5. What this leaves, for the principal

- **The tool now exists** (`filter_oracle`, tested). Every future expected-profit filter can be held to its oracle,
  its partial-oracle curve (the accuracy it needs), the confusion, AUC and capture against the oracle, and a
  calibration slope. **Proposed as house practice:** no filter is traded whose calibration slope is not clearly
  positive.
- **On D689's trade,** the regime gate remains the filter. Its book, +0.54 net at full ES in this evaluation window,
  is D689's.
- **The next gain would come from a new input that raises the Spearman above about 0.05.** It must be an input whose
  mechanism bears on the NEXT hour's direction, not its size.

## Addendum, 2026-09-29: the principal's ruling on §3–§5

"Hold up, I am not happy with those filters, first of all, a filter should tested on the real trades we are doing so MES
no the full ES contracts. Next you did not show me what the results of the oracle was and we did not design the
candidate filters together."
- **Sections 2–5 do not stand as a filter assessment.**
  - The oracle label, the partial-oracle curve and the accuracy scores used full ES. The account trades MES.
  - R1–R5 were chosen by me, not designed with the principal.
- **What remains is the library, and §1's oracle.** At MES ($4.42), over 8,555 candidates (1,240 a year):
  - take everything: −2.10 (−$3.12 a trade);
  - the oracle (net > 0): +13.6 (+$35.17, 44% taken);
  - the oracle at the 2c bar: +13.4 (+$40.86, 37% taken);
  - a perfect size forecast: −0.04 (top 20%) and −0.35 (top 40%).
- **Next, in order:**
  - the oracle at MES shown to the principal and profiled (where the winners are);
  - the candidate filters designed together;
  - then scored at MES.
