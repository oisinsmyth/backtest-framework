# D487 RESULT — CLOSE: intraday continuation lives in 2018 and 2022, not in the crash year; the quiet-volatility tercile trends most; and the first half-hour reverses into the last. The ORB line closes before a breakout is tested.

**Result of the pre-registered stage-0 premise check in D487.** Runner
`scripts/run_d487_continuation_stage0.py` (`--selftest` passes; `--run` 0.5 min), artefact
`data/d487_continuation_stage0.json`. ES and NQ, 1,993 full sessions each, 2016-01-04 →
2023-12-29; **2024+ unread** (the runner raises if a row past 2023 reaches the measurement).

**Verdict under the declared rule: CLOSE.** ES clears the primary null pooled over the calm
years on neither S1 nor S4; only **one** calm year of five clears on either (the rule required
three); NQ's calm-year variance ratio is UNRESOLVED. **Under [R15](../RULES.md#r15) this closes
the opening-range-breakout construction for the prop book by its own pre-registered rule; it
does not close intraday continuation as a question.**

## 0. One amendment, made before the numbers and proved in the self-test

The spec named a **within-day permutation** as the null for S1–S4. The self-test showed it
cannot do the job: a trend day is a **day-common** component (every bucket shares the day's
drift), and permuting the buckets leaves that component untouched — the planted trend-day
matrix sat at the within-day null's median on every statistic, and the variance ratio is
exactly invariant (the day's sum does not change). The primary null is therefore the **scaled
cross-day shuffle (N-x)**: each day standardised by its own σ, the standardised returns shuffled
across every day and bucket of the group, each day rescaled — keeps each day's volatility level
and the group's return distribution, destroys lag-structured *and* day-common dependence. The
within-day permutation is kept as the order-only secondary (`[w]` in the table) and it is what
separates "the day drifted" from "the day's late hours followed its early ones".

## 1. The numbers that decide it

| ES | n | S1 variance ratio (N-x p95) | S3 rest-of-day → last-30 slope (SE) | S4 trend-day share (N-x p95) |
|---|---:|---:|---:|---:|
| pooled | 1,993 | 1.045 (1.163) | +0.017 (0.009) | **58.1%** \* (57.6) |
| calm 2016–19, 2023 | 1,245 | 1.098 (1.125) | **+0.031** \* (0.010), 3.1 SE | 56.0% (58.1) |
| stress 2020, 2022 | 497 | 1.024 (1.247) | +0.012 (0.020) | **62.0%** \* (59.0) |
| 2016 | 251 | 0.856 | −0.025 | 53.4% |
| 2017 | 249 | 0.893 | +0.005 | 55.0% |
| **2018** | 248 | **1.319** \* | **+0.093** \* (3.8 SE) | 55.6% |
| 2019 | 249 | 0.971 | −0.005 | 53.0% |
| **2020** | 247 | **0.875** | −0.012 | 59.1% |
| 2021 | 251 | 0.956 | −0.015 | 60.6% |
| **2022** | 250 | **1.228** \* | +0.032 | **64.8%** \* |
| 2023 | 248 | 1.119 | +0.003 | **62.9%** \* |
| vol tercile high / mid / low | 572 / 486 / 720 | 1.036 / 1.046 / **1.184** \* | +0.044 / −0.017 / −0.010 | 59.4% \* / 57.4% / 58.9% |

NQ tells the same story with the same two years: VR 1.316 \* in 2018 and 1.290 \* in 2022, 0.896
in 2020; S4 clears in 2021 and 2022; the calm-year pooled VR is 1.137, above the p95 but inside
2 SE (**UNRESOLVED**); the low-vol tercile again the highest VR (1.154, unresolved); the
rest-of-day → last-30 slope clears in 2018 (+0.071 \*) and in the high-vol tercile (+0.055 \*).

**What decides it:** on ES, pooled over the calm years, neither the variance ratio (1.098 against
a p95 of 1.125) nor the trend-day share (56.0% against 58.1%) clears; the calm years that
clear individually are **one** on each (2018 for S1, 2023 for S4). The pre-registered rule
asked for three of five and NQ's agreement. Closed.

## 2. What the data says about the mechanism, read before anything is concluded

- **Continuation is a property of 2018 and 2022, not of "stress".** The crash year, 2020, is
  the most *mean-reverting* year in the sample on both roots (VR 0.875 / 0.896), and 2016–2017
  are below 1 too. 2018 and 2022 are the two Fed-tightening grind years. Whatever produces
  intraday trend days, it is not high volatility as such — which is X-e's failure: **the
  quiet-volatility tercile has the highest variance ratio on both roots** (ES 1.184 \*), and
  the high-vol tercile is at 1.04. A steady drift on a low-σ day reads as continuation; a
  crash day reads as chop.
- **The late-day continuation the literature names is there in the calm years and it is one
  year.** Rest-of-day → last-30 is +0.031 (3.1 SE) pooled over the calm years and above the
  null, and it is 2018 alone (+0.093, 3.8 SE); 2016, 2017, 2019 and 2023 are within ±0.025 of
  zero. In 2020 it is absent.
- **The first half-hour reverses into the last half-hour.** ES pooled slope **−0.102 (0.024)**,
  −4.3 SE, carried by 2020 (−0.262), 2021 (−0.116) and 2022 (−0.080); NQ −0.032 (0.018). Gao,
  Han, Li and Zhou's 1993–2013 pattern has the opposite sign here in the stress years. D463's
  "a third of published" on the last-30 trade was this: the open's direction is not the close's.
- **The next-day reversal signature exists, on NQ clearly and on ES weakly.** Day-session
  autocorrelation −0.047 on ES and −0.087 on NQ, both outside the rotation band (±0.035); after
  top-decile |R| days the next session gives back **−24.5 bp (SE 11.3)** on NQ, outside its
  rotation null [−13.2, +11.8], in calm and stress alike; ES −6.9 (9.8), inside. That is the
  price-pressure fingerprint the hedging mechanism predicts, and it sits on the day-session
  return, not on the breakout.

## 3. Predictions

| | predicted | observed | |
|---|---|---|---|
| X-a pooled ES VR 0.90–1.02 inside the null; S2 ±0.03 | | 1.045 inside; +0.019 | right |
| X-b calm years inside the null on both roots; stress VR 1.05–1.20 and S4 above p95 in 2020 and 2022 | | **2018 clears on both roots**; **2020 does not** (VR 0.88); 2022 clears; 2023 S4 clears on ES | wrong in the mechanism's direction: not "stress", two specific years |
| X-c S3 rest→last positive under 2 SE in calm, > 2 SE in 2020 | | calm **+3.1 SE** (2018 alone); 2020 −0.3 SE | wrong both ways |
| X-d next-day reversal −5 to −20 bp in stress, ±5 in calm | | ES stress −18.8 (25.7), calm −1.3; NQ −21 to −32 everywhere | ES right in sign, not significant; NQ stronger and unconditional |
| X-e VR top > mid > low by vol tercile | | **low > mid ≈ high** on both roots | wrong |
| X-f CLOSE; under 3 min | | CLOSE; 0.5 min | right |

## 4. What this leaves

- **The ORB line is closed for the prop book** by this record's rule. A breakout needs trend
  days that recur; they recur in 2018 and 2022 and in the quiet tercile, and the family of
  ranges, stops and targets a breakout test would add cannot manufacture a base rate that is
  absent in three calm years out of five.
- **Two things are not closed and belong to whoever pursues intraday continuation next** (the
  other session's lane, D474/D475): the late-day continuation is real in 2018 and the quiet
  tercile trends, which is the opposite of the volatility-gated hypothesis both sessions carried;
  and the first-30 → last-30 **reversal** in 2020–2022 is a signed pattern nobody here has
  tested as a construction. Neither is a component until it clears a cost line; both are
  measured facts on read data now.
- **The next-day reversal on NQ** is the one statistic here that cleared its null in the calm
  years and the stress years alike. It is a daily-horizon effect, so it belongs to a session
  hold, not to a breakout; at micro cost it faces the same $3 arithmetic as everything else,
  and 2024+ on the day session is still unread for it.

## 5. Files

Runner · `data/d487_continuation_stage0.json` · this record.
