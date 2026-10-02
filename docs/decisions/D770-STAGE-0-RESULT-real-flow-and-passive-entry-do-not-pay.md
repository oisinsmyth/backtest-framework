# D770 STAGE 0 RESULT — Q2 NOT ABOVE NULL, Q3 UNBALANCED (and net negative): real order flow does not mark the reversals, and a passive entry recovers about \$1.80 of the round trip but adverse selection keeps the fade below zero

*2026-10-02. One run of `scripts/stage0_d770_china_open_flow_passive.py --run` (0.4 minutes).*
- **The order:** the [pre-registration](D770-STAGE-0-PRE-REG-real-flow-and-passive-entry-at-the-china-open.md)
  (`7659bf3b`) came before the runner (`0abee5c9`), and the runner before its one run.
- **Output:** `data/stage0_d770_china_open_flow_passive.json` (statistics only).
- **The data:** the paid GC/MGC `tbbo` + `bbo-1m` China window, read in place.
- **The priors were:** Q2 SUPPORTED about 5%, Q3 about 8%.

## 0. Checks

- **Candidates:** 1,697 of D765's MGC-eligible sessions were read.
  - 80 are dropped for a contract mismatch: the GC `tbbo` price at 09:30 is more than 2 ticks from D765's bar. The
    continuous `GC.v.0` and D765's front part ways near rolls.
  - 25 are dropped for two instruments in the window.
  - 1,592 are used. Read = used + exclusions, asserted.
- **The lag audit:**
  - an explicit-loop second implementation re-derived the flow (B, S), the 09:30 quote and the sell fill on 40
    sampled sessions; all equal;
  - D767's flag audit re-derived every Q2 selection flag.
- **Right quantity:**
  - every trade-through fill is a touch fill;
  - the rotation offsets 0 reproduce the observed books;
  - each file holds one instrument;
  - nothing on or after 2024.
- **The self-test:**
  - the fill rules on both sides and the order's life;
  - quotes at or before t, with stale quotes refused;
  - chunk = whole;
  - a real paid session parses (aggressor side `S1`; B and S cover 6,049 of 6,071 contracts in the window);
  - the second implementation raises on a broken count.

## 1. Q1 (reported): the real cost at the China open

| | quoted spread at 09:31, mean (median) | at 15:00, mean (median) | taker round trip, crossing ticks (half-spread in + out) |
|---|---|---|---|
| **GC, 2016–2023** | 1.27 (1.0) | 1.30 (1.0) | **1.28** |
| **MGC, 2022–2023** | 3.63 | 3.96 | **3.80** |
| MGC − GC, same sessions (2022–23) | +0.19 ticks | +0.07 ticks | |
| the cost file's MGC line | | | 2.93 |

- **GC's median spread at this clock:** 1 tick in 2016–2019, then 1.5–2.5 ticks in 2020–2023 (March sample by
  year).
- **MGC quotes sit within 0.1–0.2 ticks of GC's.** The micro is quoted around the full-size contract.
- **So the cost file's 2.93 crossing ticks is about right on average,** low for 2022–23 at this clock (MGC 3.8) and
  high for 2016–19.

## 2. Q2: the real-flow filter (taker, \$5.93): NOT ABOVE NULL

| | |
|---|---|
| **G1, the unfiltered fade's gross** | **+\$3.18, t 2.43 (1,592): pass** |
| ρ(A, gross) on the pool (1,342) | **+0.016** (AUC 0.51); the impact variant +0.003 |
| A's top third: trades, mean gross / net | 434, **+\$6.42 / +\$0.49** (t net 0.21) |
| **N, the exact rotation of A (1,591 offsets)** | p50 −\$2.10, **p95 +\$1.19**, rank 0.905: **fail** |
| B1, the largest month-share gap; B2, net outside Dec–Mar | 2.25 points; **−\$700 (294)** |

- **Real aggressor flow points the predicted way** (Campbell, Grossman and Wang: liquidity-demand moves reverse), but
  at +0.016 it carries almost nothing.
- The partial-oracle curve needed about +0.05 to break even.
- **This closes the order-flow route on this construction,** with real signed flow. The repo's earlier order-flow
  failures (D695–D717, D760) used index futures.

## 3. Q3: the passive fade: UNBALANCED, and net negative

| | |
|---|---|
| the order: rest at the touch from 09:30, filled on a trade-through within 30 minutes | **fill rate 92.1%** (touch rule 97.6%; 10-minute life 87.3%) |
| **the passive book (GC proxy, \$3.03 a trade: commission + the MGC exit adjustment)** | **1,466 trades, gross +\$2.12, net −\$0.92** (t −0.66) |
| **N, the exact rotation of the fade side over two-sided outcomes** | observed −\$0.92 against p50 −\$4.47, p95 −\$2.14; **rank 0.996: pass** |
| B1 / B2 | 0.33 points: pass / **Dec–Mar +\$3.77 (468), the rest −\$3.11 (998): fail** |
| **adverse selection:** the taker fade's gross on filled against unfilled sessions | **+\$2.56 against +\$10.44** |
| the variants (mean net) | touch fill −\$0.61; 10-minute life −\$0.75; cross at 10:00 if unfilled −\$1.18 |
| **MGC calibration (2022–23, 394 sessions)** | fill agreement **97.5%**; MGC fill 91.9% against GC 93.9%; exit adjustment +\$0.03; the MGC book −\$0.33 (362) against the GC proxy +\$1.58 (370), difference SE \$4.10: **pass** |

- **Passive entry recovers about \$1.80 a trade.** The taker fade nets −\$2.75 (\$3.18 − \$5.93), the passive fade
  −\$0.92.
- **The fade's direction matters beyond passive mechanics:** it beats every reassigned side (rank 0.996). Resting on
  a random side loses about \$4.50.
- **But adverse selection is exactly as predicted.** The 8% of sessions where the order never filled were the best
  reversals (+\$10.44 gross), because the price turned before it traded through the resting order.
- **The season again:** EST +\$2.93 (500) against EDT −\$2.91 (966); Dec–Mar +\$3.77.
- **The micro behaves like the full-size proxy.** Fills agree 97.5% of the time, and MGC's own 2022–23 book is within
  0.5 SE of the proxy. So the GC-based estimate extends back honestly; it is the estimate itself that is negative.

## 4. The books: all four groups (one MGC)

| | Q2: A's top third (taker) | Q3: the passive fade |
|---|---|---|
| trades | 434 | 1,466 |
| **mean gross / net** | **+\$6.42 / +\$0.49** | **+\$2.12 / −\$0.92** |
| Sharpe net / gross; Sortino net | 0.08 / 1.04; 0.12 | −0.23 / 0.54; −0.34 |
| max drawdown | \$925 | \$2,736 |
| mean \|gross\| against the cost | \$34.87 (2.9 × 2c) | \$36.11 |
| breakeven cost | \$6.42 | \$2.12 |
| median net; win rate; payoff | +\$1.07; 50.9%; 0.99 | −\$1.53; 47.4%; 1.05 |
| skew; kurtosis | 0.41; 7.3 | 0.60; 14.3 |
| net ex-top 1% / ex-bottom 1% / trimmed | −1.61 / +2.12 / +0.01 | −3.19 / +1.10 / −1.18 |
| profitable years; net without the best two | 3 of 7; −\$329 | 3 of 8; −\$2,132 |
| thin-book line | −\$1.51 | −\$2.92 |
| EDT / EST | −\$1.12 / +\$3.61 | −\$2.91 / +\$2.93 |
| long / short | +\$5.77 / −\$3.28 | +\$0.72 / −\$2.43 |
| largest trades | 2022-02-24 +\$289; 2020-03-09 −\$302 | 2016-06-24 (the Brexit vote) +\$545; 2016-11-09 (the US election) −\$449 |
| Holm p (Q2, Q3) | 0.84 | 0.84 |
| ρ with D737's twin / NQ F2 / C1 | +0.07 / +0.11 / +0.01 | +0.06 / +0.08 / +0.01 |

- **POST HOC, in no reading:** the passive fade restricted to A's top third nets +\$1.68 on 402 trades. That is a
  combination chosen after the run, at a size the null says is noise. Recorded so it is not re-derived.

## 5. The reading

- **Declared:** Q2 **NOT ABOVE NULL**, Q3 **UNBALANCED**. GO false.
- **What the paid data answered:**
  1. **The cost model is about right at this clock.** GC is 1 tick wide (median) through 2019 and 1.5–2.5 ticks
     after; MGC is quoted within 0.2 ticks of GC.
  2. **True order flow does not sort the China-open reversals** (ρ +0.016).
  3. **Passive execution is worth about \$1.80 a trade** on this fade, and adverse selection takes the best 8% of
     sessions. The fade nets −\$0.92 even resting, and it earns only in the EST months.
  4. **For the repo's other sub-cost reversals** (D499's off-hours hour on 8 roots, D761): passive entry recovers a
     bit under two-thirds of the crossing cost, minus adverse selection. A reversal needs roughly \$3.5–4 gross a
     trade at one micro before a resting entry can pay. None of them had it.
- **Recommendation:** close the gold China-open line (D765, D767, D770). Closing it is the principal's call. The paid
  data stays (read-only) for any later passive-execution or spread question at this clock.
