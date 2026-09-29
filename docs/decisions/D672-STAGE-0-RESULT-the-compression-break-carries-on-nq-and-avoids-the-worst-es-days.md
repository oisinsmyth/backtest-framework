# D672 STAGE 0 RESULT (development, ES and NQ): the compression break makes +6.93 bp net on NQ (t 2.40, 55 trades a year, daily Sharpe 0.97, the drawdown halved), positive in every full year 2018–2024. On ES it is about 0; ES's busy days are what lose

*2026-09-29.*
- *One run of `scripts/stage0_d672_compression_break.py` under D672 (`31273d90`), 0.6 min.*
- *Window: D671's evaluation window, 2018-01-09 → 2025-02-28. The run reproduces D671's B0 exactly.*
- *Dealer gamma is used as a split only (SqueezeMetrics, credited).*
- *Output: `data/stage0_d672_compression_break.json`.*
- *DEVELOPMENT, on the sample where the thread was found. **On NQ this is close to circular.** No verdict.*

## 1. The books (1 micro, per trade net of D668's micro cost)

| | NQ trades/yr | NQ net (t) | P(hold) | $/yr | daily Sharpe / Sortino | maxDD | ES net (t) | ES $/yr | ES Sharpe |
|---|---:|---|---:|---:|---|---:|---|---:|---:|
| B0, every break | 161 | +2.18 (1.50) | 0.53 | +1,086 | 0.69 / 1.34 | $2,213 | −1.58 (−1.42) | −428 | −0.48 |
| **C1, compression third** | **55** | **+6.93 (2.40)** | **0.62** | **+1,025** | **0.97 / 2.14** | **$1,102** | +0.55 (0.25) | +83 | 0.14 |
| C2, middle | 52 | +1.67 | 0.52 | +264 | 0.31 | | +0.28 | −21 | −0.04 |
| C3, busiest third | 54 | −2.17 | 0.44 | −202 | −0.25 | | **−5.66 (−2.71)** | −491 | −1.13 |

**NQ:**
- About the same dollars as every break, on a third of the trades.
- Sharpe 0.69 → 0.97; drawdown halved.
- A monotone ladder across the thirds.

**ES:** the compression third is about 0, but the busiest third loses hard. **On ES the construction works by avoiding
busy days, not by finding good ones.**

## 2. Nulls

| | NQ | ES |
|---|---|---|
| random within-year subsets of the same count: p50 / p95 (SE) / C1's rank | +2.45 / +5.75 (0.12) / **0.992** | −1.64 / +0.92 (0.11) / 0.921 |
| tier rotated across sessions: C1 − rest, p50 / p95 / rank | +7.21 against −0.11 / +4.84 / **0.990** | +3.25 against −0.10 / +4.11 / 0.910 |

## 3. By year, NQ (C1 net; B0 net in brackets)

| 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 (Jan–Feb) |
|---|---|---|---|---|---|---|---|
| +5.3 (+1.5) | +0.7 (+1.7) | **+5.8 (−5.9)** | +10.0 (+5.8) | +12.0 (+5.6) | +4.1 (−0.2) | +14.2 (+9.0) | −13.1 (−6.2), 7 trades |

- **C1 is positive in all 7 full years, and beats B0 in 6 of 7.**
- It turns 2020, the year every other version of the break lost, into a gain.

**ES:** positive in 4 of 7 full years.

## 4. The four groups, NQ C1

- 387 trades; net +6.93, median −11.4, win 42%, payoff 1.91, skew +1.5, kurtosis 3.8.
- **Trimmed means:** trimmed +5.36, ex-top +4.29, ex-bottom +8.02. **Not tail-only:** it stays positive without its
  best 1%.
- Per-trade Sharpe/Sortino 0.89/1.84. Gross breakeven 9.0 bp against a 2.1 bp cost (4.3×).
- The top trade is 2020-04-06 (long, +324 bp).
- **Component line** (daily $ at 1 MNQ):
  - Sharpe **0.97**, $1,025 a year;
  - ρ with K8 −0.05;
  - ρ with ES's C1 0.50.

## 5. Splits of C1 (reported only; not in the rule)

| | NQ | ES |
|---|---|---|
| long / short | +8.40 (t 2.48) / +4.70 | +1.45 / −1.01 |
| **dealer gamma g above / below its walk-forward median** | **+12.70 (t 2.65, 25/yr)** / +2.08 | +5.16 / −2.69 |
| SPX short gamma (GEX < 0) | +7.54 (31 trades) | +18.10 (25 trades) |
| no gap / gap inside / gap through | +9.74 / +7.87 / +4.01 | +2.40 / −4.50 / +2.52 |
| E2 exit instead of E4 | +6.61 | +1.80 |

**Each input alone** (bottom vs top third):
- NQ: recent range +5.74 vs −0.09; overnight range +5.25 vs −3.01. The combined score (+6.93) beats either alone.
- ES: the overnight range carries it alone (+1.71 vs −4.82); the recent range does nothing.

## 6. Expectations (§3)

**All five held:**
1. NQ C1 +5 to +9 bp at about 50 a year, with rotation rank > 0.95: +6.93, 55 a year, 0.990.
2. Sharpe above B0, with $ within ±40%: 0.97 vs 0.69, $1,025 vs $1,086.
3. ES within ±2 bp and inside the placebo: +0.55, rank 0.921.
4. NQ positive in ≥ 5 of 7 full years: 7 of 7.
5. Short gamma better within C1: yes (+7.54 vs +6.88 on the SPX sign; +12.70 vs +2.08 on the median split).

## 7. Reading, root by root

**NQ.** A break of yesterday's range out of a compressed market carries. The compression is low recent realised range
and a quiet overnight session. The break holds more often (0.62 against 0.53), and it pays more when it holds.
- **Mechanism:** in a quiet NQ, a move through yesterday's extreme is information arriving at the cash open (mega-caps,
  retail, leveraged ETFs), not noise.
- The effect is strongest when dealers are more short gamma, which fits D665: gamma supplies the size.

**ES.** Priced overnight and arbitraged, ES gains nothing from a quiet day. It loses heavily on busy ones (−5.66,
t −2.7), where its breaks are noise.

**YM and RTY:**
- **Expected:** RTY like NQ (it re-prices at the cash open), YM like ES.
- **The frozen rule for their pre-registration is exactly §1 of D672.** The gamma interaction is a declared secondary.

**Caveat, stated plainly.** The rule was found on NQ's in-sample data (D671's diagnostic, 127 cuts). Its passing its
nulls here shows it is internally consistent, not that it is real. **YM, RTY and the vault are the test.**
