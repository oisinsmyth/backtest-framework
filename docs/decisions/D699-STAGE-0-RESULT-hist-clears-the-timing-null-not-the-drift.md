# D699 STAGE 0 RESULT — the gamma-gated 15-minute log MACD: the histogram variant (V1) earns +$10.47 a MES trade, net Sharpe +0.63, positive in all eight years, and beats its timing null (98.5th percentile) and the gamma-label null (99.6th); but its lead over the time-matched drift is NW t 1.64, not 2, so the declared reading fails on (b); 2022 is 75% of the net; the ROC variant (V2) and the OR (V3) carry nothing beyond chance

*2026-09-30. One run of `scripts/stage0_d699_gamma_macd_long.py` (`ecb5cb8c`), 180 s. Its
[design record](D699-STAGE-0-DESIGN-the-gamma-gated-15-minute-log-macd-long.md) (`0b0d0b08`) was committed before the
runner, and the runner before the run.*
- **Checks:** D688 reproduced bit for bit. The lag audit re-derived 40 short-gamma days in pure Python from the raw
  prices, and it RAISED on a book that reads the next close. The norms matched the design's (0.3379, 0.0867), and the
  spliced MACD differs from the gapped one. `--selftest` passed on synthetic random walks, at 0.99 / 1.31 / 1.37 trades
  a day against the design's 0.91 / 1.32.
- **What it is:** in-sample, 2016-01-05 → 2023-12-29, with nothing from 2024 read. No slice spent.
- **Output:** `data/d699_gamma_macd_long.json`.
- **The universe:** 1,989 sessions, of which 603 are short-gamma (G_SUM < 0), and all 603 are tradable.

## The answer in one line

**V1 (the histogram with a ±0.5 band) is the first construction in the short-gamma line that pays at MES:**
- +$10.47 net a trade, net Sharpe +0.63, and every year positive;
- above the family-maximum timing null (98.5th percentile) and the gamma-label null (99.6th).

**It does not clear the declared reading:**
- (b) needs its gross to beat the time-matched drift control at NW t ≥ 2. It beats it by +$8.92, at NW t 1.64.
- Three-quarters of the net is 2022.

**V2 (ROC) and V3 (OR) sit inside their nulls.**

## 1. The oracle first (the ceiling for any filter)

| variant | trades | oracle share (net > 0) | oracle mean net | oracle net Sharpe | oracle trades a year |
|---|---:|---:|---:|---:|---:|
| V1 HIST | 572 | 50.5% | +$110.07 | +4.3 | 37 |
| V2 ROC | 799 | 48.1% | +$91.01 | +4.7 | 49 |
| V3 OR | 804 | 45.3% | +$120.82 | +4.8 | 46 |

V1 already wins half its trades, above the 48.5% breakeven win rate D692 measured for the hourly grid. That is the
first time in this line the unfiltered book sits above it.

## 2. The book (1 MES, $4.42 a round trip; four groups)

**Performance**

| variant | trades a year | mean hold | exposure* | net Sharpe (Sortino) | gross Sharpe (Sortino) | mean net (NW t) | mean gross = breakeven RT | max DD | ρ with the arm |
|---|---:|---:|---:|---|---|---|---:|---:|---:|
| **V1 HIST** | 72 | 212 min | 0.52 | **+0.63 (+1.06)** | +0.90 (+1.56) | **+$10.47 (+1.91)** | $14.89 | $1,675 | +0.154 |
| V2 ROC | 101 | 133 min | 0.45 | +0.19 (+0.28) | +0.57 (+0.89) | +$2.15 (+0.54) | $6.57 | $3,051 | +0.056 |
| V3 OR | 102 | 209 min | 0.71 | +0.27 (+0.41) | +0.59 (+0.91) | +$3.89 (+0.81) | $8.31 | $2,972 | +0.106 |

\*Exposure is the share of short-gamma session time held.

- **Sharpe and Sortino** are daily, over all 1,989 sessions (√252).
- **ρ V1–V2** (daily) is +0.60.

**Trade distribution (net)**

| variant | median | hit | payoff | skew | kurtosis | trimmed 1% both / ex-top / ex-bottom |
|---|---:|---:|---:|---:|---:|---|
| V1 | +$0.58 | 50.5% | 1.21 | +1.09 | 6.3 | +$7.37 / +$3.99 / +$13.88 |
| V2 | −$6.92 | 48.1% | 1.14 | +0.71 | 6.0 | +$1.02 / −$2.52 / +$5.71 |
| V3 | −$15.67 | 45.3% | 1.30 | +1.33 | 7.9 | +$0.44 / −$3.01 / +$7.37 |

**V1's mean is far above its median, and the right tail carries it.** Ex-top 1% it is +$3.99 against +$10.47. That
is the trend-follower's shape: the exit cuts the losers when the histogram turns, and the winners run to the close.
The top five trades (net) are:
- 2020-03-13, +$734;
- 2022-02-24, +$667;
- 2022-10-13, +$618;
- 2022-01-24, +$588;
- 2022-11-30, +$579.

**Dependencies**

| V1, net by year (trades) | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| $ | +160 (53) | +55 (28) | +223 (89) | +356 (64) | +439 (44) | +122 (46) | **+4,480 (146)** | +157 (102) |

- **Every year is positive,** but 2022 is $4,480 of $5,992 (75%) on a quarter of the trades.
- **Without 2022:** +$3.55 net a trade over 426 trades ($1,512). That is still positive, but a third of the
  full-sample mean.
- **Without Feb–Apr 2020:** +$10.55 a trade, so the crash does not carry it.
- **V2 and V3 swing by year** (V2: 2018 −$2,431, 2020 +$2,002). V2 without Feb–Apr 2020 is +$0.35.

**By entry hour (V1, count, mean gross):** 09 195 +$13.1 · 10 106 +$38.5 · 11 70 −$17.9 · 12 64 +$8.1 · 13 50
+$23.8 · 14 42 +$25.2 · 15 45 +$8.2. The cells are small, and no hour is declared.

## 3. The time-matched drift control (declared, gate b)

| variant | trade gross | drift control gross (same minutes, every short-gamma day) | excess (NW t) |
|---|---:|---:|---|
| V1 | +$14.89 | +$5.97 | **+$8.92 (+1.64)** |
| V2 | +$6.57 | +$3.77 | +$2.80 (+0.71) |
| V3 | +$8.31 | +$5.87 | +$2.44 (+0.51) |

**V1's timing is worth about 60% of its gross, not the drift.** But the t is 1.64, and the declared bar was 2.

## 4. The timing null (declared, gate c)

This null applies each day's position schedule to a different short-gamma day's prices, enumerated over 584 offsets
(SE 0).

| variant | observed | own p50 / p95 | own percentile | family-max p50 / p95 | percentile in family |
|---|---:|---|---:|---|---:|
| **V1** | +$10.47 | +$1.53 / +$8.17 | 0.985 | +$2.78 / +$8.17 | **0.985, above p95** |
| V2 | +$2.15 | −$0.74 / +$4.21 | 0.832 | | 0.404 |
| V3 | +$3.89 | +$1.49 / +$5.53 | 0.817 | | 0.618 |

- **The null's centre is positive** (+$1.5 to +$2.8) because short-gamma days drift up. It is the drift, and the
  null keeps it.
- **V1 dominates the family maximum,** so its family p95 equals its own.

## 5. The gamma-label null (reported, not a gate)

This rotates the short-gamma label across all 1,989 sessions.

| variant | observed | p50 | p95 | percentile |
|---|---:|---:|---:|---:|
| V1 | +$10.47 | +$1.39 | +$6.87 | **0.996** |
| V2 | +$2.15 | −$0.68 | +$3.84 | 0.851 |
| V3 | +$3.89 | −$1.43 | +$3.25 | 0.972 |

## 6. Controls, not traded

| control | trades or days | mean gross | mean net |
|---|---:|---:|---:|
| V1 on long-gamma days | 1,024 | +$0.82 | −$3.60 |
| V1 short mirror on short-gamma days | 520 | **+$5.01** | +$0.59 |
| V2 on long-gamma days | 1,299 | +$1.78 | −$2.64 |
| V2 short mirror, short-gamma days | 813 | −$0.38 | −$4.79 |
| V3 on long-gamma days | 1,521 | +$0.09 | −$4.33 |
| V3 short mirror, short-gamma days | 811 | +$1.95 | −$2.47 |
| always long 09:46 → 16:00, short-gamma days | 603 | +$11.57 | +$7.15 (NW t 0.99) |
| always long 09:46 → 16:00, long-gamma days | 1,386 | −$0.84 | −$5.26 (NW t −1.97) |

**The contrast the mechanism predicts is there for V1:**
- the same signal on long-gamma days grosses +$0.82;
- on short-gamma days it grosses +$14.89 long and +$5.01 SHORT.

**The histogram signal carries both ways only when dealers are short gamma.** That is continuation at the MACD's
horizon (hours), not at the burst's (D697). The long side adds the short-gamma drift to it.

**Against simply being long:**
- the always-long day grosses +$11.57 over about 6.2 hours;
- V1 grosses +$14.89 over 3.5 hours, at about half the exposure.

## 7. The declared reading

| variant | (a) mean net > 0 | (b) beats drift, NW t ≥ 2 | (c) above family-max timing p95 | edge worth filtering |
|---|---|---|---|---|
| V1 HIST | yes | **no (t 1.64)** | yes | **no** |
| V2 ROC | yes | no | no | no |
| V3 OR | yes | no | no | no |

**No variant meets the declared reading.** V1 fails one of three, on the gate that separates the MACD's timing from the
short-gamma drift, at t 1.64 against 2.

## 8. What it says

1. **The principal's momentum intuition is right at the MACD horizon.** Under short dealer gamma, a 15-minute log MACD
   histogram above its band picks moves that carry: on both sides, only on short-gamma days, and above the nulls that
   keep the time-of-day profile and the drift. D695 and D697 looked faster (the hour, the 15-minute burst) and found
   fades. The smoothed, hours-long trend is where the hedging shows.
2. **The rate of change adds nothing.** V2 is inside its null, and OR-ing it into V1 dilutes V1 (V3 +$3.89). The
   histogram's level is the signal.
3. **The evidence is thinner than the Sharpe suggests:**
   - 2022, a bear market that was short gamma most of the year, is 75% of the net;
   - the mean is carried by the right tail (median +$0.58);
   - the timing's excess over the drift is t 1.64.
4. **It cannot be confirmed on the clean slice.** V1's per-trade sd is about $131, so on the ~66 short-gamma days of
   2024-01 → 2025-02 the expected t is about 0.6. The vault's short-gamma count is not yet known, and it would be the
   only unseen test.

**Component line (CLAUDE.md), V1:**
- net Sharpe +0.63 (Sortino +1.06), gross +0.90 (+1.56), at 1 MES and $4.42;
- hit 50.5%, skew +1.09;
- ρ +0.154 with the admitted MACD arm, the only ledger component.

It is a different instrument and clock from the arm (ES on 15-minute bars against NQ on the hourly clock), but the
same signal family, and ρ +0.15 is the overlap. **In-sample only, and not a candidate.**

## 9. The principal's options

1. **Stop here and record V1 as a lead.** It fails its declared reading on (b), and nothing is tuned.
2. **Build the expected-profit filter on V1,** with the principal, against the oracle in §1. It is 50.5% winners, and
   the right tail is the edge, so a filter that cuts the tail would kill it. That argues for a filter on the size of
   the expected move (gamma's proven use, D665) rather than on direction.
3. **Pre-register V1 unchanged for the vault,** after counting the vault's short-gamma days to size its power. If
   there are too few, say so before spending anything.
4. **Diagnose the 2022 dependence first:** is V1 a bear-market-rally catcher, or does it work in the 2018 and 2020
   selloffs at the same rate per short-gamma day?

For contrast: 2018 is +$223 on 89 trades and 2020 is +$439 on 44.

## CLOSED by the principal, 2026-10-01

**The principal:** "Close D699", after [D722](D722-DIAG-RESULT-no-variable-explains-2022.md) diagnosed the 2022 dependence (option 4 above).

**Why:**
- D722 found that V1 is positive in volatility units only in 2022 (and faintly in 2016–17). Per unit of risk it loses in
  2018, 2019, 2020, 2021 and 2023.
- **Its ex-2022 figure** is +$3.55 net a MES trade, net Sharpe 0.25 (Sortino 0.39).
- No pre-trade variable identifies the 2022 state.

**What follows:**
- None of the four options above is taken: no expiry-hour profile, no expected-profit filter, no vault pre-registration.
- V2 and V3 close with it.
- ES's vault holds no look for this line, and no slot was spent.
- **Reopening needs the principal's word and a new pre-registration.** Re-tuning the in-sample result is not a route.
