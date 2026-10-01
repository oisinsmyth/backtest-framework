# D730 STAGE 0 RESULT — the volume profile does not detect continuation (NOTHING on NQ, YM and RTY). A heavy open, if anything, comes with WEAKER continuation; the detector picks out big days, not continuing ones; the size forecast adds nothing to the detected book (SIZE HELPS false); GO is false

*2026-10-01. The run: one run of `scripts/stage0_d730_volume_detector.py` (0.9 min, `--data-root` set to the main
checkout).*
- **The order:** the [pre-registration](D730-STAGE-0-PRE-REG-volume-profile-as-the-trend-detector.md) was committed
  first, and the runner (`1c37c4a4`) before the run.
- **The audits:**
  - NQ's, YM's and RTY's objects reproduce D727's known answers;
  - the volume lag audit (a second implementation from raw rows) passed, and its canary fired;
  - Q = R/E held;
  - the E-tier and F_close tier audits passed.
- **Seal:** nothing dated 2024-01-01 or later was read.
- **Output:** `data/stage0_d730_volume_detector.json`.

## 1. S1 — does the volume profile detect continuation?

The statistic is the continuation slope on detected rows against undetected rows, stacked over eleven clocks; the
null rotates the volume profile across days.

| root | share detected | β detected (NW t) | β not | Δβ | rotation p05 / p50 / p95; rank | without the 5 pre-roll sessions | reading |
|---|---:|---|---:|---:|---|---:|---|
| **NQ** | 11.9% | +0.015 (+0.42) | +0.043 | −0.028 | −0.072 / +0.001 / +0.086; 0.25 | −0.039 | **NOTHING** |
| YM | 12.4% | +0.015 (+0.36) | −0.007 | +0.022 | −0.089 / −0.006 / +0.088; 0.70 | +0.028 | NOTHING |
| RTY | 11.7% | +0.012 (+0.38) | +0.029 | −0.017 | −0.065 / +0.006 / +0.071; 0.27 | −0.002 | NOTHING |

- **On NQ, the detected days continue less than the rest.** At 10:00 they are higher (+0.170 against +0.094). From
  11:00 to 13:30 their slope is negative.
- **Early volume alone is monotone the wrong way.** NQ's continuation slope by the early-volume tercile is +0.071
  (quiet open), +0.054 and +0.037 (loud open). Steadiness alone does nothing (Q ≥ 1: +0.038; Q < 1: +0.039).
- **A heavy open is the burst, and bursts spend the move** (D697: short-gamma bursts are exhaustion).
- **The oracle view shows what volume does find: big days.** On detected rows, D727's trend-day precision is 0.34–0.57
  against 0.26–0.33 for all rows. But D727's trend label is |C − O| over the prior days' scale, which a loud day meets
  by being large. In the scale-free statistic (the slope), the detected days continue no better. **Volume is an
  activity forecast** (D471), the fourth size detector in a row (D720, D724, D725, D730) that finds volatility, not
  trend.

## 2. S2 — the three-part books (NQ, one MNQ, $4.07; held to the close)

| k | book | trades (contracts) | gross / net per MNQ (median) | net Sharpe (Sortino); gross | max DD | P3a $50k | years + |
|---|---|---|---|---|---:|---:|---|
| 1.0 | (i) D727's unfiltered | 1,505 | +$11.21 / +$7.14 (+$8.00) | **+0.47 (+0.66)**; +0.74 | $5,021 | 0.39 | 5/8 |
| 1.0 | (ii) volume-detected | 445 | +$6.60 / +$2.53 (+$7.50) | +0.08 (+0.11); +0.21 | $5,576 | 0.13 | 3/8 |
| 1.0 | (ii) on the F_close window | 360 | +$11.15 / +$7.08 (+$18.25) | +0.19 (+0.26) | $5,393 | 0.13 | 4/8 |
| 1.0 | (iii) detected + F_close sizing | 360 (557) | the same per MNQ | +0.18 (+0.25) | $10,209 | 1.04 | 4/8 |
| 1.0 | (iv) detected + E sizing | 445 (588) | the same per MNQ | +0.01 (+0.02) | $6,943 | 0.78 | 4/8 |
| 1.5 | (i) unfiltered | 1,024 | +$19.29 / +$15.22 | **+0.83 (+1.21)** | $4,131 | 0.26 | 5/8 |
| 1.5 | (ii) detected | 363 | +$18.49 / +$14.42 | +0.41 (+0.61) | $3,299 | 0.13 | 4/8 |

- **The filter costs money.** At k 1.0 the detected book nets $4.61 a trade less than the unfiltered one: rotation
  p05 −17.0, p95 +15.6, rank 0.32. It keeps 30% of the trades, and at every k its net Sharpe is below the
  unfiltered book's.
- **SIZE HELPS is false.** Sizing the detected book by the evening-before forecast changes its net Sharpe by −0.004
  (rotation rank 0.51), and doubles the drawdown (P3a at $50k rises to 1.04).

**GO is false:**
- the volume reading is NOTHING;
- the detected book does not beat D727's per trade;
- it grosses $6.60 at k 1.0, below 2 × $4.07.

## 3. What it says

1. **"Heavy early, then steady" does not detect a trending NQ day.** A heavy open comes with weaker continuation, and
   steadiness adds nothing. This holds on YM and RTY too.
2. **Volume, like every size measure tried, finds big days, not trending ones.** The trend line has now tried four
   ways to tell a trend day from a big day, and none has done it:
   - the size forecast (D720, D725);
   - the size forecast's effect on the mean (D724);
   - cross-asset agreement (D728);
   - volume (D730).
3. **What does stand is D727's plain follow on NQ.** It needs no detector: net Sharpe 0.47–0.83 in-sample, ρ 0.24 with
   the arm. It is NQ-only and unconfirmed.
4. **Proposed, not decided:**
   - close the volume-profile detector under R15;
   - the remaining choices for the trend line are the principal's: the slot-10 vault pre-registration of D727's NQ
     follow (which needs their explicit word), or closing the line here.
