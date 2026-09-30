# D705 RESULT — NONE PASSES: F2 (the prior hour's size plus today's volatility) clears the edge, the best-of-three null and the ex-COVID gates (+$13.21 a MES trade, t 2.48, rank 0.996) but fails the one-year gate, with 2022 holding 60 % of its net; F1 and F3 also fail

*2026-09-30. A declared SECOND LOOK, in-sample, walk-forward; the window is 2018-05-14 → 2023-12-29 (1,359
candidates).*
- ***The spec:** [D705 PRE-REG](D705-PRE-REG-relative-size-filters-on-the-last-hour.md) (`784d2824`).*
- ***The runner:** `scripts/stage1_d705_relative_size_filters.py` (`ae0ae7aa`), run once in 2.3 min.*
  - *The rotation was projected at about 0.1 min and took 31 s over 1,815 offsets.*
  - *Output: `data/stage1_d705_relative_size_filters.json`, statistics only. GEX: SqueezeMetrics, credited.*
- ***Known answers held:** D618, D702's lines, D691 and D688. The tier canary fired.*
- ***Unspent:** the 2024-01 → 2025-02 slice was not read.*

## The answer in one line

**NONE PASSES, so the line closes again (§2).**
- **F2 passes (a), (b) and (c)** and fails only (d), the one-year gate added after D703:
  - 2022 holds 59.9 % of its net, against a 50 % bar;
  - five of its six years are positive.
- **F1 and F3 fail (a) and (d).**

## 1. The gates (1 MES, $4.42 a round trip)

**The best-of-three null** (1,815 offsets, count-matched, p95 SE 0): p50 +$1.44, **p95 +$7.94.**

| member | trades (a year) | mean net (HAC t) | Holm p | rank vs best-of-3 | ex-COVID | 2022's share of net, years + | verdict |
|---|---:|---:|---:|---:|---:|---|---|
| F1 prior hour's relative size | 261 (46) | +$9.30 (1.75) | 0.079 ✗ | 0.971 ✓ | +$8.67 ✓ | 56.8 %, 5 of 6 ✗ | FAIL |
| **F2 size + today's vol** | 252 (45) | **+$13.21 (2.48)** | **0.020 ✓** | **0.996 ✓** | +$12.48 ✓ | **59.9 %**, 5 of 6 ✗ | **FAIL on (d) only** |
| F3 F1 on short gamma | 134 (24) | +$16.04 (1.76) | 0.079 ✗ | 0.999 ✓ | +$12.29 ✓ | 56.4 %, 4 of 6 ✗ | FAIL |
| take everything (the window) | 1,359 (240) | −$0.32 (−0.21) | | | | | |

**The count-matched null worked as designed.** Across offsets, the members took 253–330 (F1), 251–340 (F2) and
105–151 (F3) trades. D703's empty books are gone.

## 2. The books

| | F1 | **F2** | F3 |
|---|---:|---:|---:|
| gross / net | +$13.72 / +$9.30 | **+$17.63 / +$13.21** | +$20.46 / +$16.04 |
| hit (net), median net, payoff | 0.506, +$0.58, 1.34 | **0.536, +$6.21, 1.33** | 0.515, +$1.83, 1.45 |
| skew | +0.92 | +0.81 | +1.04 |
| per-trade Sharpe (Sortino) | 0.69 (1.15) | **0.93 (1.59)** | 0.69 (1.27) |
| daily Sharpe (Sortino) | 0.59 (0.99) | **0.80 (1.37)** | 0.59 (1.09) |
| max drawdown | $655 | $707 | $586 |
| 1 % trims: ex-top / ex-bottom / both | 5.74 / 12.11 / 8.55 | 9.56 / 16.16 / 12.50 | 11.64 / 19.11 / 14.71 |
| long / short net | +$13.16 / +$5.09 | +$17.04 / +$8.85 | +$27.83 / +$2.74 |
| before / after 2022-05-16 | +$12.16 / −$1.18 | **+$14.47 / +$7.06** | +$23.89 / −$6.17 |
| **without 2022** (derived) | +$5.46 on 192 | **+$7.17 on 186** | +$11.16 on 84 |
| ρ with the MACD arm | +0.02 | +0.02 | +0.03 |

**By year** (n, net a trade):

| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|
| F1 | 24, +6.62 | 21, +5.04 | 68, +6.50 | 41, +9.09 | 69, +19.98 | 38, −0.83 |
| **F2** | 18, +13.36 | 21, −2.28 | 65, +4.83 | 49, +16.12 | 66, +30.22 | 33, +1.15 |
| F3 | 17, +13.74 | 10, −6.55 | 25, +26.98 | 13, +9.43 | 50, +24.23 | 19, −1.46 |

**D690's placement:** each score's Spearman with the gross is about 0.070 (a Sharpe of about 0.5 on D702's curve).
AUC is 0.53–0.54, and capture of the oracle's net is 8.5–13 %.

**Reported only, the top 33 %:** F1 +$6.82 (t 1.91), F2 +$5.84 (t 1.54), F3 +$11.17 (t 1.55).

## 3. Reading it

**F2 is the strongest filter this line has produced, and it fails the gate built from D703's lesson.** It is not the
same failure as D703, though:

| | D703 | F2 |
|---|---|---|
| where the trades sit | 79 % of its trades in 2022 | 26 % of its trades in 2022 (66 of 252) |
| where the net sits | | 60 % of its net in 2022 |
| without 2022 | | +$7.17 a trade on 186 trades |
| after 2022-05-16 | −$1.73 | +$7.06, the only member positive after it |

**The declared rule is 50 %, and F2 is at 59.9 %. The verdict is FAIL.**
- Relaxing the gate after seeing this would be a third look chosen to pass, and is not done here.
- **Prediction 2 was wrong:** today's volatility helped. F2 beat F1 by $3.91 a trade.

## 4. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | F1 passes every gate at a t near 2 | **failed** (t 1.75, and 2022 is 57 % of its net) |
| 2 | F2 at or below F1 | **failed**: F2 is higher by $3.91 |
| 3 | F3 has the highest net and fewest trades, and fails (d) | **held** |
| 4 | every member is weaker after 2022-05-16 | **held**, though F2 stays positive (+$7.06) |
| 5 | the best-of-three p95 is +$3–5 | **failed**: +$7.94 |

## 5. Routing

**Under §2, no member passes, so the line closes again.** A third in-sample look would need the principal's word and
would say so.

**What remains open, and is the principal's call:**
- **Forward-record F2 as a newly registered rule, scored only on data it has never seen:**
  - the held 2024-01 → 2025-02 slice;
  - forward sessions from 2026-09-19.
- That route does not rest on an in-sample verdict, so it does not relax (d) after the fact.
- **The power arithmetic** (D702/D703) still gives an expected t of about 0.8 on the slice alone. At about 45 trades
  a year, it needs about three years of forward data to reach the 1.2816 bar at full effect.
