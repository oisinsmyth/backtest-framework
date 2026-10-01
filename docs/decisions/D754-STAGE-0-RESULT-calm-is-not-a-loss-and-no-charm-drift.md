# D754 STAGE 0 RESULT — (A) NOT SUPPORTED: on the pre-registered single-variable gate, the NQ book still earns in calm markets, so the "calm bull loses" split was the three-variable label's artefact; (B) NOTHING: no long-gamma Friday-afternoon drift on MES

*2026-10-02. One run of `scripts/stage0_d754_calm_bull.py --run` (8.0 minutes). The
[pre-registration](D754-STAGE-0-PRE-REG-calm-bull-abstention-and-charm-drift.md) (`737ff35f`) was committed before the
runner, and the runner (`208017a9`) before its run.*
- **Output:** `data/stage0_d754_calm_bull.json` (statistics only; no per-date GEX).

## 0. Checks

- **The seal:** every fixture and `DIX.csv` were restricted as text before 2024-01-01.
- **Lag:**
  - the own-return canary changed walk-forward percentiles;
  - GEX and the S&P are the rows strictly before each session, re-derived by a loop on a sample.
- **The permutation null:** the within-year null (p50 ≈ 0) differs from the pooled-years canary (p50 −0.38,
  p95 16.0).
- **Sign, in money:** a rise pays the long MES.
- **Right quantity:** the within-year label differs from the walk-forward label, and no Friday is in the Mon–Thu
  set.
- **The scored window:**
  - Part A: 2,025 NQ sessions, 2016-02-24 → 2023-12-29. The walk-forward calm gate labels 40.7% of them calm,
    because volatility drifted down over the sample.
  - Part B: 51.6% of ES sessions are in the long-gamma, above-200-day state; 226 of them are Fridays.

## 1. Part A — the abstention diagnostic

Per session (zero on days a line did not trade), one MNQ each.

| series | calm mean / session | rest mean / session | calm trades, $/trade | within-year Δ (rest − calm) | null p50 / p95 | p | years Δ > 0 |
|---|---|---|---|---|---|---|---|
| **book** | **+\$5.11** | +\$26.54 | 751, +\$5.62 | **−\$9.31** | +0.01 / +15.48 | 0.84 | 5 of 8 |
| D737's twin | +\$4.06 | +\$18.27 | 740, +\$4.52 | −\$10.59 | −0.01 / +14.05 | 0.89 | 4 of 8 |
| NQ F2 | −\$0.09 | +\$4.78 | 64, −\$1.21 | +\$0.85 | +0.06 / +3.86 | 0.37 | 3 of 8 |
| C1 | +\$1.15 | +\$3.49 | 110, +\$8.64 | +\$0.43 | +0.00 / +3.88 | 0.43 | 3 of 8 |

- **The reading: NOT SUPPORTED.** A1 fails: the book's calm-session mean is +\$5.11, not ≤ \$0. A2 fails too: the
  within-year contrast is negative.
- **Calm sessions earn less than the rest, but they still earn.** The gap is mostly across years: low-volatility
  years earn less.
- **Within years, calm sessions are no worse.** In 2022 they were far better (Δ −\$93). Without 2022 the contrast is
  small and of either sign (−\$2.6 to +\$11.7).
- **The correction this record makes:** the earlier split (2026-10-01, in chat) said the book loses −\$3.44 a day in
  the "calm bull". (The vault portfolio page says only that low-volatility days carry 3% of the money, a whole-sample
  tercile, which stands.) That figure came from a three-variable label (volatility cut over
  the whole sample, the S&P above its 200-day average, long gamma above its median) chosen after looking. On the
  pre-registered single-variable walk-forward gate, the book is positive in calm markets. The calm bull is
  under-earning, not losing, and **standing aside would cost money**.
- **Per line:**
  - **NQ F2** is the only line that is about flat when calm (−\$1.21 a trade on 64), and that is not significant
    within year.
  - **D737's twin** earns +\$4.52 a trade on 740 calm trades, matching D742's floor note (+\$2.66 below \$150 σ).
  - **C1** earns +\$8.64 a trade on 110 calm trades.

## 2. Part B — the long-gamma Friday-afternoon drift (MES, 14:00 → 16:00)

| | trades | mean gross | t | mean net |
|---|---|---|---|---|
| **B, long-gamma state, Fridays** | 226 | **+\$3.42** | 1.15 | −\$0.99 |
| B-C1, the same state, Mon–Thu | 838 | −\$0.19 | −0.10 | |
| B-C2, the same Fridays, 12:00 → 14:00 | 226 | −\$0.03 | −0.01 | |
| B-C3, Fridays OUT of the state | 180 | +\$22.52 | 2.72 | |

- **The reading: NOTHING.**
  - The Friday mean is positive but at t 1.15, below 2.
  - Friday minus Mon–Thu has a Welch t of 1.01, below 1.64.
  - Room exists: the mean |move| is \$30.91, 3.5 × the \$8.84 bar.
  - GO is false.
- **The mechanism's own splits run backwards:**
  - monthly-expiry Fridays −\$8.91 (61) against other Fridays +\$7.98 (165), where the mechanism predicts the
    opposite;
  - the drift is larger OUTSIDE the long-gamma state (B-C3).
  - The 0DTE era: +\$1.01 (37), against +\$3.90 before it (189).
- **The four groups (B):**
  - **Performance:** net Sharpe −0.12, Sortino −0.15, gross Sharpe +0.41; max drawdown \$830; breakeven cost
    \$3.42 against \$4.42.
  - **Trade distribution:** median net +\$1.83, win rate 0.52, payoff 0.86, skew −0.74, kurtosis 3.5; ex-top
    −\$2.17, ex-bottom +\$0.65, trimmed −\$0.52.
  - **What it depends on:** 4 of 8 years positive; 2022 +\$137 against 2019 −\$174 and 2023 −\$202.
  - **The component line:** daily ρ with D737's twin −0.02, NQ F2 −0.02, C1 +0.00.
- **An observation, POST HOC and not a lead:** Friday 14:00 → 16:00 long, OUTSIDE the calm long-gamma state, grossed
  +\$22.52 at t 2.72 on 180. It was a control, not the hypothesis, and it is what the mechanism says should NOT
  happen. It may be the ordinary rebound drift of volatile periods (2020, 2022) landing on Fridays. Pursuing it would
  need its own pre-registration, with a day-of-week control in the volatile state.

## 3. Reading

- **The calm bull is the book's weakest regime, not a losing one.** Calm sessions earn about a fifth of what the
  rest earn. There is nothing to gain by switching the lines off, and the post-vault state-based allocation should
  not start from "abstain when calm".
- **The calm regime still has no line of its own.** A charm-flow drift on long-gamma Fridays is not visible in MES
  (the agents' best regime-native idea), and the published evidence (Baltussen et al. 2021; Ko and Yang 2021) says
  calm, long-gamma markets suppress intraday edges.
- **What remains is the other-markets route:** a component whose quiet days are not equity-quiet days. That is a
  search, not a construction yet.

## 4. Next

- **The readings are A NOT SUPPORTED and B NOTHING.** Closing them is the principal's call (R15).
- **Superseded:** the chat claim that the book loses in the calm bull. On the walk-forward gate, calm sessions earn
  +\$5.11 each.
