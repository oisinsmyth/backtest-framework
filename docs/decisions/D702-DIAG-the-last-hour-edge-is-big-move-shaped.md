# D702 DIAG — the last-hour continuation's edge IS big-move-shaped: the size-only oracle nets +$12.78 a MES trade, and the prior hour's own size, known at 15:30, keeps most of it (+$8.87, Sharpe 0.74); hindsight, nothing fitted

*2026-09-30. Hindsight and descriptive only. [D702 DESIGN](D702-DESIGN-the-last-hour-oracle-profile-at-mes.md)
(`c2e519f2`); runner `scripts/diag_d702_last_hour_oracle_mes.py` (`aad52747`, fix `647bc4e9`), output
`data/diag_d702_last_hour_oracle_mes.json`.*
- **Known answers held first:**
  - D618 §3c: 1,960 non-roll sessions, +0.6795 points, hit 0.4929;
  - D688's β_G, through D692's build;
  - D691's d̄.
- **The MES candidates** are the 1,917 non-roll sessions whose prior hour moved (F5 ≠ 0): 2016-01 → 2023-12, about
  240 a year.
- **The first `--run` crashed** at a numpy-string date after every known answer had passed and before any statistic
  was computed. It was fixed and run once more.
- **Reserved:** 2024-01 → 2025-02 is not read.

## 1. The oracle lines (the ceiling and the crux), 1 MES, $4.42 a round trip

| line | trades / yr | mean gross | mean net | hit (gross > 0) | daily Sharpe (Sortino) | max DD | years + |
|---|---:|---:|---:|---:|---:|---:|---:|
| take everything | 240 | +$3.47 | −$0.95 | 0.504 | −0.30 (−0.45) | $3,403 | 4 of 8 |
| **the oracle** (net > 0) | 107 | +$38.39 | +$33.97 | 1.00 | +6.78 | $0 | 8 of 8 |
| the oracle at the bar (gross ≥ $8.84) | 88 | +$45.08 | +$40.66 | 1.00 | +6.68 | $0 | 8 of 8 |
| **size-only oracle, top 20 %** (realised \|move\|) | 48 | +$17.20 | **+$12.78** | 0.564 | **+0.86 (+1.36)** | $977 | 5 of 7 |
| size-only oracle, top 40 % | 96 | +$8.45 | +$4.03 | 0.529 | +0.51 (+0.79) | $1,193 | 4 of 8 |
| **pre-entry: top 20 % by \|F5\|** (known at 15:30) | 48 | +$13.29 | **+$8.87** | 0.535 | **+0.74 (+1.26)** | $849 | 6 of 8 |
| pre-entry: top 40 % by \|F5\| | 96 | +$9.51 | +$5.09 | 0.519 | +0.75 (+1.27) | $806 | 5 of 8 |

**The crux reads "proceed" (D702 §6).**
- **The size-only oracle's top 20 % nets +$12.78 a MES trade.** On D689's hourly continuation the same line was worth
  about nothing.
- **Here, knowing the size of the last half hour selects the profitable sessions,** because on big days the direction
  holds more often: hit 0.564 against 0.504.
- **Most of that is already knowable at 15:30.** The prior hour's own |move| keeps two thirds of the size oracle's net.

**The caveat on the pre-entry lines.** They are hindsight: the top-20 % threshold is taken over the whole sample. A
real filter needs a prior-only threshold. Both |F5| lines were declared in the design, not chosen after the run.

## 2. Where the winners sit (gross $ a MES trade, HAC t; 83 buckets, so read them with that multiplicity)

| input | the pattern |
|---|---|
| **\|F5\| / σ** (the last hour against a normal hour) | t1 −$0.77, t2 +$1.93, **t3 +$9.48 (t 3.44)**. The edge lives in big prior hours. |
| today's realised vol to 15:30 | t1 +$0.26, t2 +$2.76, **t3 +$7.40 (t 2.59)** |
| trailing σ of the last half hour | flat: +$2.52 / +$4.95 / +$3.16 |
| **dealer gamma** | short (G_SUM < 0) **+$6.50 (t 2.29)** against long +$2.07. SPX GEX < 0 +$11.67 (n 245). Quintiles fall from +$8.46 (most short) to −$0.31 (most long). |
| **short gamma × big \|F5\|** | **+$14.18 (t 2.64), net +$9.76,** 276 trades (35 a year) |
| D691's day-size forecast M1 | U-shaped: +$7.09 / +$1.05 / −$1.07 / +$4.29 / +$8.15. Not a clean size filter for this clock. |
| ivrv | U-shaped: +$4.11 / +$0.94 / +$5.28. Within big \|F5\| both extremes pay (+$10.34, +$11.85). |
| ln IV | +$0.65 / +$3.98 / +$5.69 |
| side | **short +$5.27 (t 3.31)**, long +$1.92 |
| era | before 2022-05-16 +$4.07 (t 3.41); **after +$1.16 (t 0.44)** |
| year | 2016 +$0.05, 2017 −$0.60, 2018 +$6.62, 2019 −$0.02, 2020 +$4.43, 2021 +$6.12, 2022 +$10.07, 2023 +$0.79 |
| events | **CPI days −$5.78 (n 90)**; FOMC +$9.83 (n 68, t 0.94); quarter-end +$18.44 (n 32); opex +$5.62 (n 94) |

## 3. The accuracy a filter needs (D690's partial-oracle curve, 200 draws)

| Spearman with gross | top 20 %: net a trade (p05, p95) and Sharpe | top 40 %: net and Sharpe |
|---:|---|---|
| 0.00 (null) | −$0.76 (−4.44, +2.77); −0.14 | −$0.95; −0.19 |
| 0.02 | +$0.36; +0.02 | −$0.18; −0.02 |
| 0.05 | +$2.03; +0.31 | +$1.20; +0.26 |
| 0.09–0.10 | +$5.24 (+1.66, +8.67); +0.71 | +$3.48; +0.63 |
| 0.19 | +$12.33; +1.53 | +$7.99; +1.50 |

**A filter breaks even at MES near a Spearman of 0.02, and reaches a Sharpe of about 0.5 near 0.07.**

**Each input's raw Spearman, with the gross and with the size:**

| input | with the gross | with the size |
|---|---:|---:|
| **\|F5\|/σ** | **0.066** | 0.198 |
| today's realised vol | 0.039 | **0.486** |
| ln IV | 0.020 | **0.477** |
| trailing σ30 | −0.003 | 0.376 |
| M1 | −0.030 | 0.112 |
| ivrv | −0.032 | 0.013 |
| G_SUM | −0.020 | −0.288 |
| G_ES | −0.022 | −0.340 |

**The size forecasts forecast the size well: realised vol and ln IV at about 0.48. Only |F5| carries much toward the
gross,** because the continuation's direction is more reliable after a big hour.

## 4. What this does not say

- **Nothing is fitted or traded.** The buckets use hindsight edges, and 83 of them were looked at.
- **The edge is weaker after 2022-05-16,** and 2016, 2017, 2019 and 2023 are near zero.
- **§3e's power argument stands.** A filter keeping about 48 trades a year gives the reserved 2024-01 → 2025-02 slice
  roughly 56 trades.
  - The per-trade sd is about **$85** (derived: mean × √(trades a year) / per-trade Sharpe, 8.87 × √48.0 / 0.726).
  - So at the in-sample +$8.87 the expected t is **about 0.8** even if the effect is entirely real.
  - **t = 2 would need about 360 trades,** seven to eight years at this rate.
  - The pre-registration must state this before the slice is spent.
- **Next:** the candidate filters are designed with the principal, then pre-registered.
