# D735 STAGE 0 RESULT — NQ breaking from the market beats its timing null, unlike D733: the equity legs rank 0.94–1.00 against the same minutes on other days, matched-row gains of +$9–14 a trade, counter trades that win; the mechanism reads on YM only; no cell reaches GO, because the per-|x| bin leg fails in every cell. DRIFT ONLY by the declared rule

*2026-10-01. One run of `scripts/stage0_d735_nq_breaks_from_the_market.py` (0.7 min), with `--data-root` set to the
main checkout.*
- **The order:** the [pre-registration](D735-STAGE-0-PRE-REG-nq-breaks-from-the-market.md) (`0e6c841e`, with A1
  `985e8aba`) was committed first, and the runner (`8e216864`) before the run.
- **The audits all passed before anything was written:**
  - NQ's objects reproduce D727's known answer, and D727's own lag audit passed;
  - the trigger was re-derived from raw rows by a second implementation on 60 trades per leg, matching on every one
    (TICK from the extracted minutes), and its one-bar-lead canary fired on every leg;
  - each date join passed, and a shifted join fired the audit;
  - the E1 tables equal D733's loop exit on 240 sampled (day, minute, direction) entries per stop rule;
  - C2b's offset 0 reproduced every cell's observed trades exactly;
  - the FW null's offset 0 equals δ̂.
  - The self-test showed the FW null's size at 5/100 null worlds and its power at 100/100 planted worlds.
- **The data:** 1,941 NQ days. Leg days: ES 1,933, YM 1,928, RTY 1,550 (from 2017), EQ 1,540, TICK 1,925 (median
  coverage 1.0). Nothing dated 2024-01-01 or later was read; the Sierra read stopped at 2024-01-01 00:00 ET.
- **The output:** `data/stage0_d735_nq_breaks_from_the_market.json`.

## 1. The mechanism (S1, read first)

y_NQ = a + β·x_NQ + δ·e, where e is the leg's move orthogonalised on NQ's at each clock. Pooled over D727's 11 clocks,
the e roll null is enumerated over 1,901 offsets.

| leg | δ | rotation p05 / p50 / p95 | p_low | clustered t | Holm | δ at 10:00 / 10:30 / 11:00 | MECHANISM |
|---|---:|---|---:|---:|---:|---|---|
| ES | −0.033 | −0.048 / +0.000 / +0.048 | 0.129 | −0.83 | 0.52 | −0.195 / −0.048 / −0.052 | no |
| **YM** | **−0.044** | −0.032 / +0.000 / +0.032 | **0.010** | **−2.02** | **0.050** | −0.145 / −0.088 / −0.081 | **YES** |
| RTY | +0.004 | −0.034 / −0.001 / +0.034 | 0.57 | +0.17 | 0.88 | −0.002 / +0.015 / +0.008 | no |
| EQ | −0.015 | −0.046 / −0.000 / +0.046 | 0.29 | −0.47 | 0.88 | −0.127 / −0.047 / −0.043 | no |
| TICK | −0.007 | −0.029 / +0.000 / +0.029 | 0.35 | −0.36 | 0.88 | −0.067 / +0.067 / +0.014 | no |

- **The declared sign (δ < 0) holds for ES, YM and EQ at every clock but a few.** It is strongest at 10:00.
- **It clears its null on YM alone,** and only just (Holm exactly 0.050, clustered t −2.02).
  - On ES the 10:00 slope is the largest of any leg (−0.195), but the pooled δ is inside its null.
  - RTY carries nothing. The Russell shares too little of the Nasdaq's mega-cap flow to separate it.
- **TICK-NQ (breadth) is not the mechanism.** A cap-weighted move unmatched by breadth does not continue more.

## 2. The cells (one MNQ, $4.07; E1 = the stop or the 15:59 close)

| cell | trades | net (NW t) | gross (median) | C2a p50 / p95; rank | efficiency vs p95 | matched-row gain ± SE | O1 / O2 | net Sharpe (Sortino) | max DD | years + | reading |
|---|---:|---|---|---|---|---|---|---|---:|---|---|
| **ES k1.5 1σ (PRIMARY)** | 1,376 | **+$10.47** (+2.15) | +$14.54 (+$2.00) | +5.29 / +10.92; **0.936** | 0.109 vs 0.114 | +5.57 ± 5.20 | +12.66 / +5.19 | +0.70 (+1.17) | $3,083 | 5/8 | DRIFT ONLY |
| ES k1.5 none | 1,376 | +$11.04 (+2.05) | +$15.11 | +2.11 / +8.45; 0.987 | 0.108 vs 0.091 | +9.06 ± 5.86 | +12.66 / +5.19 | +0.69 (+1.05) | $3,139 | 6/8 | DRIFT ONLY |
| ES k1.0 1σ | 1,710 | +$12.34 (+2.55) | +$16.41 | +5.17 / +9.46; 0.997 | 0.122 vs 0.102 | +7.62 ± 4.80 | +11.09 / +4.40 | +0.92 (+1.56) | $3,656 | 6/8 | DRIFT ONLY |
| ES k1.0 none | 1,710 | +$11.28 (+2.23) | +$15.35 | +1.99 / +6.93; 1.000 | 0.110 vs 0.079 | +9.53 ± 5.47 | | +0.78 (+1.21) | $3,266 | 6/8 | DRIFT ONLY |
| YM k1.5 1σ | 1,381 | +$14.79 (+2.92) | +$18.86 | +5.26 / +10.59; 0.997 | 0.137 vs 0.112 | +9.74 ± 5.07 | +16.24 / +5.80 | +0.98 (+1.67) | $3,566 | 6/8 | DRIFT ONLY |
| YM k1.5 none | 1,381 | +$11.40 (+1.99) | +$15.46 | +2.12 / +8.15; 0.993 | 0.107 vs 0.089 | +9.34 ± 5.86 | | +0.69 (+1.05) | $4,649 | 6/8 | DRIFT ONLY |
| **YM k1.0 1σ** | 1,699 | **+$14.87** (+3.15) | +$18.94 (+$5.00) | +5.35 / +9.25; 1.000 | 0.139 vs 0.101 | **+10.14 ± 4.71** | +14.08 / +5.18 | **+1.11 (+1.85)** | $2,690 | **7/8** | DRIFT ONLY |
| YM k1.0 none | 1,699 | +$13.33 (+2.60) | +$17.40 | +2.23 / +6.68; 1.000 | 0.122 vs 0.077 | +11.58 ± 5.48 | | +0.92 (+1.40) | $2,936 | 7/8 | DRIFT ONLY |
| RTY k1.5 1σ | 1,180 | +$16.83 (+2.47) | +$20.90 | +5.05 / +11.92; 0.998 | 0.129 vs 0.119 | +11.95 ± 6.31 | **+5.58** / +4.59 | +0.91 (+1.59) | $3,425 | 6/8 | NO ROOM; DRIFT ONLY |
| RTY k1.5 none | 1,180 | +$14.54 (+2.02) | +$18.61 | +1.91 / +9.15; 0.998 | 0.110 vs 0.099 | +12.69 ± 7.26 | | +0.74 (+1.16) | $4,895 | 5/8 | NO ROOM; DRIFT ONLY |
| RTY k1.0 1σ | 1,437 | +$11.38 (+1.87) | +$15.44 | +5.15 / +10.19; 0.982 | 0.097 vs 0.105 | +6.69 ± 5.68 | +5.41 / +4.40 | +0.70 (+1.17) | $4,780 | 4/8 | NO ROOM; DRIFT ONLY |
| RTY k1.0 none | 1,437 | +$10.02 (+1.50) | +$14.08 | +2.10 / +7.24; 0.996 | 0.085 vs 0.086 | +8.32 ± 6.64 | | +0.57 (+0.87) | $6,175 | 3/8 | NO ROOM; DRIFT ONLY |
| **EQ k1.5 1σ** | 1,131 | **+$18.11** (+2.74) | +$22.18 (+$6.00) | +5.01 / +12.10; **0.998** | 0.138 vs 0.117 | **+13.25 ± 6.19** | +15.96 / +6.67 | +0.97 (+1.66) | $4,747 | 6/8 | DRIFT ONLY |
| EQ k1.5 none | 1,131 | +$16.12 (+2.21) | +$20.19 | +2.20 / +9.32; 0.999 | 0.120 vs 0.100 | +14.18 ± 7.02 | | +0.80 (+1.24) | $5,410 | 6/8 | DRIFT ONLY |
| EQ k1.0 1σ | 1,400 | +$15.87 (+2.67) | +$19.94 | +5.25 / +10.33; 1.000 | 0.126 vs 0.106 | +11.19 ± 5.49 | +13.92 / +5.78 | +0.97 (+1.63) | $3,345 | 6/8 | DRIFT ONLY |
| EQ k1.0 none | 1,400 | +$15.73 (+2.47) | +$19.80 | +2.25 / +7.51; 1.000 | 0.120 vs 0.087 | +14.00 ± 6.32 | | +0.89 (+1.37) | $5,027 | 6/8 | DRIFT ONLY |
| TICK k1.5 1σ | 1,044 | +$6.58 (+1.06) | +$10.64 | +4.85 / +12.04; 0.637 | 0.080 vs 0.127 | −0.45 ± 4.26 | +12.47 / +12.02 | +0.40 (+0.64) | $3,611 | 5/8 | DRIFT ONLY |
| TICK k1.5 none | 1,044 | +$5.87 (+0.83) | +$9.94 | +1.89 / +10.23; 0.788 | | +1.29 ± 4.63 | | +0.31 (+0.44) | $4,993 | 4/8 | DRIFT ONLY |
| TICK k1.0 1σ | 1,540 | +$5.17 (+1.13) | +$9.24 | +5.09 / +9.98; 0.508 | | −0.22 ± 3.59 | +10.42 / +9.99 | +0.38 (+0.60) | $4,398 | 5/8 | DRIFT ONLY |
| TICK k1.0 none | 1,540 | +$1.70 (+0.31) | +$5.76 | +2.00 / +7.82; 0.464 | | −1.12 ± 4.14 | | +0.11 (+0.15) | $6,424 | 3/8 | DRIFT ONLY |

- **The family p95** (the maximum over the 20 cells at each offset) is **+$14.41**.
  - Eight cells clear it: YM k1.5 1σ, YM k1.0 1σ, all four EQ cells, and both RTY k1.5 cells (NO ROOM).
- **Holm over the 20 cells' C2a p_high:** 12 cells at ≤ 0.05:
  - all four EQ cells;
  - YM k1.5 1σ and both YM k1.0 cells;
  - ES k1.0 (both);
  - RTY k1.5 (both) and RTY k1.0 none.
- **The primary misses:**
  - its C2a mean is at rank 0.936 (p95 +$10.92 against +$10.47);
  - its efficiency is 0.109 against a p95 of 0.114;
  - its matched-row gain is +$5.57 ± 5.20.
- **No cell reads EDGE, UNRESOLVED or GO.** Every equity cell fails leg (iii), the |x_NQ| bins.
  - Their 1–1.5 bin holds only 55–73 trades, so its null p95 runs $40–57.
  - The 0–0.5 bin's p95 is sometimes missed too (for example EQ k1.0 1σ: +$6.5 against +$9.6).
  - Six cells pass the matched-row leg (iv: gain ≥ $4.07 at t ≥ 2): EQ ×4 and YM k1.0 ×2. Every equity cell passes
    the counter leg (v).

## 3. What the equity-leg cells are made of (the four groups)

**The primary, ES k1.5 1σ:**
- **The distribution:** 1,376 trades; mean net +$10.47, median −$2.07; win rate 49%, payoff 1.22; skew +1.05,
  kurtosis 7.2.
- **The symmetric 1% trims:** ex-top +$2.26, ex-bottom +$15.54, both **+$7.30**.
- **Exposure:** 23% stopped at 1σ_rem. Gross Sharpe +0.98 (Sortino +1.66).
- **MFE/MAE:** +$42 / −$37 at 15 minutes, +$57 / −$49 at 30, +$76 / −$65 at 60, +$143 / −$125 at the close. Unlike
  D733's symmetric ladder, the entry starts on the favourable side.
- **By year:** 2016 −$62, 2017 −$202, 2018 +$2,041, 2019 −$1,002, 2020 +$2,866, 2021 +$2,638, 2022 +$7,307,
  2023 +$821.
  - The largest year (2022) is 50.7% in dollars and 49.4% in volatility units (SCALE-CARRIED).
  - Ex-2022 the mean net is +$6.02.

**The best-rounded cells:**

| cell | median | trims (ex-top / ex-bottom / both) | win / payoff | years (D729 label; $ / vol share) | ex-2022 net | ρ with NQ F2 | ρ with D727's follow (same day and side) |
|---|---|---|---|---|---|---|---|
| EQ k1.5 1σ | +$1.93 | +$9.26 / +$23.32 / **+$14.43** | 51% / 1.21 | 6/8 (NEITHER; 36% / 34%) | **+$13.99** | +0.05 | 0.33 (68%) |
| EQ k1.0 1σ | +$1.93 | +$7.05 / +$21.13 / +$12.28 | 51% / 1.19 | 6/8 (NEITHER; 35% / 36%) | +$12.36 | +0.03 | 0.36 (64%) |
| YM k1.0 1σ | +$0.93 | +$6.85 / +$19.92 / +$11.87 | 50% / 1.23 | 7/8 (SCALE-CARRIED; 51% / 35%) | +$8.52 | +0.05 | 0.36 (65%) |
| YM k1.5 1σ | | | | 6/8 (NEITHER; 49% / 34%) | +$8.72 | +0.07 | 0.35 (67%) |

- **The trimmed means hold** (+$7 to +$14): unlike D733, this is not a lottery book.
- **No equity cell is SAME TRADE.**
  - The daily ρ with D727's minute follow is 0.21–0.36, although 59–68% of trades are on the same day and side.
  - The ~35% that differ (the counter trades, and the days the follow does not fire) carry the difference.
  - **TICK is close to the follow** (ρ 0.59–0.75; SAME TRADE in k1.0 none), as expected when breadth barely moves the
    spread.
- **The counter trades, the mechanism's whole claim** (long NQ when it falls less than the market, short when it
  rises less):
  - gross +$5 to +$29 a trade on every equity cell, 280–532 trades each;
  - C1, the spread's direction against the drift's on the same day and minute, paired: +$10 to +$52 (t +0.5 to
    +1.9).
  - Right-signed everywhere; significant nowhere on its own.
- **The mirror** loses on every cell: $13–24 a trade on the equity legs and $8–14 on TICK. The sign is right, in
  money.
- **The entry clock: 93–97% of equity-leg trades enter in the 10:00 hour** (TICK 87–89%).
  - The trigger fires on 54–93% of a leg's days, against the 30–35% the arithmetic expected. The spread's variance is
    front-loaded, so |z_s| at 10:00 is often over k at the first look.
  - In practice the construction is "the sign of NQ's lead over the market at 10:00", not a midday onset.
- **C2b** (the same minutes on other days, in the sign of that day's spread) has a p50 above C2a's on every equity
  cell:
  - by +$2.4 to +$5.5 on ES and RTY;
  - by +$5.1 to +$7.7 on YM;
  - by +$7.1 to +$9.5 on EQ;
  - by about 0 on TICK.
  - **The spread's sign at a minute is worth several dollars a trade over the drift's sign, on any day.**
  - The threshold crossing adds little beyond it (C2b ranks 0.69–0.96).
- **The reported exits** (net, the primary):
  - no stop +$11.04;
  - a 0.5σ_rem stop +$11.54;
  - a 60-minute exit +$4.05;
  - the signal's own exit +$9.47.
  - The drift needs the whole day; the stop is neutral.
- **O1 (the room) clears $8.14 on ES, YM, EQ and TICK** (+$10.4 to +$16.2). On RTY it reads NO ROOM (+$5.4 to +$5.6),
  consistent with its δ of zero.
  - **Each equity-leg book's gross exceeds its drift budget O2 by +$9 to +$16.** TICK's falls short of it by $0.8 to
    $4.2.

## 4. Readings

- **The primary (ES k1.5 1σ): DRIFT ONLY.** It fails (ii) on efficiency (0.109 against 0.114), (iii) on the bins (1
  of 3) and (iv) on the matched rows (+$5.57 ± 5.20).
- **MECHANISM:** YM yes; ES, RTY, EQ and TICK no.
- **GO: none.** The binding failure in every cell is (iii), the bin leg.
- **The stopping rule: NOT met.** The primary's matched-row gain + 2 SE is +$15.97 against $8.14, YM reads MECHANISM,
  and eight cells clear the family p95. **Closing NQ entry timing as an axis is not proposed.**

## 5. What it says

1. **This is the first NQ entry construction here whose entries beat the same minutes on other days.**
   - Pooled, the equity legs rank 0.94–1.00 against the timing null, and eight cells clear the family-wise p95.
   - Matched-row gains are +$9–14 a trade at the same clock and displacement.
   - D733 was +$0.02 and rank 0.74.
   - The information comes from outside NQ's own path: what the rest of the equity market did since the open.
2. **The mechanism reads as declared, but thinly.**
   - The part of NQ's move shared with the Dow continues less (δ < 0 at every clock, Holm 0.050).
   - It is weaker against ES, whose 30% tech weight shares NQ's own flow, and absent against the Russell.
   - The breadth version (TICK) is not it.
3. **It fails GO on the per-|x| bins,** a leg declared to stop one displacement range from carrying the pool.
   - The pool is broad (four bins, every equity leg positive in the two populated ones), but the 1–1.5 bin is too thin
     to clear a $40–57 p95.
   - By the declared rule this is DRIFT ONLY. The bin leg is NOT relaxed after the fact, and k, the stop and the clock
     window are NOT re-tuned.
4. **In practice it is a 10:00 trade:** the sign of NQ's lead over the market after the first half hour, held to the
   close.
   - The principal declined a follow, and this is not one: ρ 0.2–0.36 with D727's follow, and the counter trades go
     against NQ's own move.
   - But it is one decision a day at one clock.
5. **The best cells look like components:**
   - EQ k1.5 1σ: net Sharpe 0.97, Sortino 1.66, trimmed mean +$14, ex-2022 +$14, no year above 36%, ρ +0.05 with NQ
     F2.
   - YM k1.0 1σ: Sharpe 1.11, 7/8 years.
   - **They were chosen after the fact from 20 cells, though,** and in-sample is spent on them. The only clean
     confirmation is a slice nothing has seen.
   - For NQ that is 2024 onward. D716's slot-7 vault family holds its last hour, and a morning-to-close trade overlaps
     that window, so a confirmation needs its own programme slot (10). **It is the principal's explicit word, and not
     proposed here as decided.**
6. **Proposed, not decided:**
   - (a) record D735 as DRIFT ONLY with the strongest cross-market lead found, and stop;
   - (b) a slot-10 vault pre-registration of ONE declared cell, the primary or a named alternative, chosen in writing
     before any 2024+ read, on the principal's word;
   - (c) a premise check on the YM mechanism alone (e.g. at the 10:00 clock), from ES and RTY's absence. This is new
     selection on spent data, so its value is low.

## 6. Recorded after the result: the named cell (2026-10-01, before any 2024+ read)

- **The principal: "I choose YM 1.0, it look really good".** The chosen cell is **YM k1.0 1σ_rem**, chosen over EQ
  k1.5 1σ_rem on the comparison set out in chat:
  - its higher Sharpe gives more power in a one-shot test;
  - it is the only leg where MECHANISM read;
  - its max drawdown is $2,690 against $4,747;
  - it needs one leg, not three.
- **This names the cell any confirmation would test. It is a post-hoc choice among 20 cells,** and any confirmation
  must say so.
- **It grants no programme slot.** A vault pre-registration in slot 10 (NQ 2024-01-01 → 2026-09-18, which overlaps
  D716's slot-7 window) needs the principal's separate, explicit word, and its pass gate and power are declared there
  before any 2024+ read.

