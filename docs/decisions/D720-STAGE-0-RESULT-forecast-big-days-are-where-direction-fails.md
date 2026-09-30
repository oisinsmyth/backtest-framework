# D720 STAGE 0 RESULT — sizing by the day-size forecast makes both NQ lines worse: the forecast knows the day's range (Spearman 0.51) but not the trade's, and the days it calls big are where the lines' direction is weakest. The MACD arm is CEILING ONLY; NQ F2 is NO CEILING

*2026-09-30. One run of `scripts/stage0_d720_size_the_direction.py` (2.0 min).*
- **The order:**
  - the [design](D720-STAGE-0-DESIGN-size-the-direction-we-have.md) (`63b40964`) was committed first;
  - A1 and the runner (`acc32753`) were committed before the run.
- **Output:** `data/stage0_d720_size.json`.
- **Known answers reproduced exactly on the cut data:**
  - the arm: 1,908 trades, net $15,423.414, gross $22,110.00 (D669);
  - NQ F2: 274 trades, +$20.670105, and the same take-session hash (D716).
- **Audits:**
  - lag: the forecast and tier audits each fired on their leaked canaries, and the arm's audit fired on a shifted
    trade;
  - sign, in money;
  - the date-keyed join;
  - rotation offset 0 equals the observed value.
- **Seal:** nothing dated 2024-01-01 or later was used.
- **Window:** 2018-02-14 → 2023-12-29, 1,434 sessions. The label is finite from 2018-02, earlier than the design's
  estimate of about 2019, so the window has six calendar years. Trades by line:
  - the arm: 1,375 in the window; 500 are before it, and 33 fall on sessions the label frame drops;
  - NQ F2: 267 in the window.

## The answer in one line

**Knowing how big the day will be does not help either line, and the forecast points the wrong way.**
- **What the forecast knows:** D691's model ranks the day's range at Spearman 0.506 (D691: 0.505), but ranks the
  trade's own window move at only 0.106 (the arm) and 0.061 (F2).
- **What it gets wrong:** it anti-ranks the trade's P&L: −0.001 on the arm, **−0.173 on NQ F2**. The days it calls
  big are the days the two lines' direction is weakest.
- **Every sizing rule** lowers net Sharpe on both lines, and sits inside or below its rotation.

## 1. The arm (L1, one MNQ, $3.50): CEILING ONLY

| book | net Sharpe (Sortino) | gross Sharpe | net $ a year | max DD | P3a at $50k / $150k | Δ net Sharpe (rotation p50 / p95; rank) |
|---|---|---|---:|---:|---|---|
| R0, one MNQ | +0.84 (+1.23) | +1.11 | 2,634 | 7,070 | 0.35 / 0 | — |
| **R1, forecast** | **+0.70 (+1.02)** | +0.94 | 3,347 | 12,493 | **1.93** / 0 | **−0.134** (−0.046 / +0.171; 0.24) |
| R2, forecast | +0.52 (+0.75) | +0.73 | 1,381 | 5,971 | — | −0.321 (0.22) |
| R3, forecast | +0.47 (+0.67) | +0.66 | 2,095 | 11,594 | 1.76 / 0 | −0.368 (0.21) |
| R4, forecast | +0.58 (+0.82) | +0.80 | 3,153 | 14,178 | — / 0.18 | −0.255 (0.13) |
| R1, oracle (the day's realised size) | +0.97 (+1.43) | +1.18 | 5,350 | 12,548 | 2.99 / 0 | +0.131 |
| R3, oracle | +1.03 (+1.53) | +1.19 | 5,639 | 11,165 | 2.99 / 0 | +0.197 |

- **Dollars (A1, reported):**
  - R1 adds $713 a year, but a random choice of the same days adds more: rank 0.40 (p50 +$4,985 over the window, p95
    +$10,274).
  - R1 costs $5,423 of extra drawdown, and **breaks P3a at $50k** (1.93 a year against the bar of 1.0).
- **Trades, position net per trade, R0 → R1:**
  - mean $10.90 → $13.85, median $4.50 → $5.00; win 51.9%; skew +0.05 → −0.11; kurtosis 6.3 → 10.0;
  - ex-top 1% $3.82 → $1.96, ex-bottom $18.10 → $26.79, both trimmed $11.02 → $14.91;
  - sessions to half the P&L: 10 → 7.
- **By year:** R1's Δ $ is positive in 5 of 6 years, but the largest year (2020) is 58% of it, and 2022 is negative
  (−$1,322).

**Calibration by tercile** (mean gross / efficiency Σg/Σ|g| / mean net per MNQ):

| tercile | forecast τ | the oracle, day's realised size | the oracle, trade's own \|move\| |
|---|---|---|---|
| low | **$19.00 / 0.150 / $15.50** | −$0.18 / −0.002 / −$3.68 | −$0.46 / −0.018 / −$3.96 |
| mid | $11.44 / 0.088 / $7.93 | $6.12 / 0.048 / $2.61 | $7.82 / 0.082 / $4.32 |
| high | $12.81 / 0.077 / $9.31 | **$35.91 / 0.166 / $32.40** | $35.87 / 0.119 / $32.36 |

- **A ceiling exists:** days that turn out big are trend days, and the arm's efficiency is highest on them (0.166
  against −0.002).
- **But days that are forecast big are not those days:** the arm's efficiency falls across the forecast's terciles,
  from 0.150 to 0.077.
- **The accuracy curve (R1, pooled terciles, 200 draws) says the ceiling is out of reach.** A partial forecast of
  the day's size gives R1 a Δ net Sharpe of:

  | correlation with the day's size ρ | 0 | 0.3 | 0.5 | 0.7 | 1 |
  |---|---|---|---|---|---|
  | Δ net Sharpe, p50 | −0.036 | −0.049 | −0.028 | −0.004 | +0.075 |

  Even a forecast at 0.7 (D691's is at 0.5) adds nothing. Only perfect foresight does.

## 2. NQ F2 (L2, one MNQ, $4.07): NO CEILING

| book | net Sharpe (Sortino) | gross Sharpe | net $ a year | max DD | Δ net Sharpe (rotation p50 / p95; rank) |
|---|---|---|---:|---:|---|
| R0 | +0.79 (+1.20) | +1.01 | 660 | 1,134 | — |
| **R1, forecast** | **+0.48 (+0.70)** | +0.68 | 647 | 2,294 | **−0.309** (−0.040 / +0.169; **0.016**) |
| R2, forecast | +0.16 (+0.23) | +0.35 | 115 | 1,669 | −0.629 (0.005) |
| R3, forecast | +0.08 (+0.11) | +0.26 | 102 | 3,592 | −0.707 (0.009) |
| R4, forecast | +0.35 (+0.50) | +0.53 | 590 | 3,331 | −0.438 (0.009) |
| R1, oracle (the day's size) | +0.78 (+1.21) | +0.98 | 1,134 | 1,839 | −0.010 |
| R1, oracle (the trade's \|move\|) | +0.87 (+1.34) | +1.02 | 1,405 | 1,931 | +0.083 |

- **The forecast is significantly WRONG-WAY for F2.** Every rule sits at or below the 1.6th percentile of its
  rotation, and the dollar rotations rank 0.0–0.1.
- **Calibration by forecast tercile:**
  - low: 64 trades, **+$48.41 net, efficiency 0.60, 75% winners**;
  - mid: 82 trades, +$8.90, 0.17;
  - high: 121 trades, **−$0.61, 0.036, 47%**.
- **Even the oracle does not help:** knowing the day's size adds nothing (−0.010). F2 already selects on realised
  relative size, so its edge is not "more on big days".
- **Trades, R0:** 267; mean $14.06, median $7.93, win 54.7%, skew −0.18, kurtosis 4.6. The trims are +$11.34
  (ex-top), +$17.36 (ex-bottom) and +$14.65 (both).
- **By year:** 2022 is 78% of the window's net.

## 3. What it says

1. **A forecast of the day's size is a forecast of volatility, not of trend.** It keys on event days, gaps, and high
   IV over RV: two-way days, on which a trailing direction (the arm) and a last-hour continuation (F2) both do worst.
   Days that turn out big, by contrast, are big because they trend. D690 found that size knowledge scales winners
   and losers alike; here it is worse, because the forecast's big days select the losers.
2. **Sizing up also breaks the smaller account.** On the arm, R1 takes P3a at $50k from 0.35 to 1.93 a year, over
   the bar.
3. **The two lines together, unsized, are worth recording.**
   - **The combined book:** L1 + L2 at one MNQ each: net Sharpe **+1.01** (Sortino +1.54), ρ −0.01 between them,
     +$3,293 a year, max drawdown $5,094, P3a 0 at $150k. R1 on both lowers it to +0.81.
   - **The caveats:** it is in-sample, and it rests on 2020 and 2022. The arm's figure is the top of a family whose
     median is 0.24 (D669).
4. **The declared readings:**
   - **the arm, CEILING ONLY:** a ceiling exists for perfect foresight, but no realistic forecast reaches it;
   - **NQ F2, NO CEILING.**
   - Neither is a LEAD, and nothing here goes to the vault.
5. **Post hoc, not evidence:** F2 earned its money on days the forecast called quiet (+$48 a trade on 64 trades).
   - The reversed rule (size up quiet days) would sit near the top of its rotation, but only because this run
     selected it. D717's reversal did not transfer.
   - F2's own vault look (D716) is sealed, so it cannot be tested there without spending that look.
   - Only a fresh root's in-sample F2 (YM or RTY, D711's A2 roots) could test it. **That is the principal's call.**
     This record proposes nothing.
6. **Closing the sizing idea under R15 is the principal's call.** In scope: a day-size forecast used to size, skip
   or scale either line.

## CLOSED, 2026-09-30, on the principal's word (for these applications only)

The principal: "Close the sizing overlay on those specific applications, I think will work on another type."
- **Closed under R15:** a day-size forecast (D691's M1, or any variant of it) used to size, skip or scale **the
  admitted MACD arm or NQ F2**.
- **Not closed:** sizing by a size forecast on another type of construction. The principal expects it to work
  elsewhere, and D720 says nothing about constructions whose P&L rises with the day's realised size in a way a
  forecast can reach.
- **The quiet-day pattern on F2 (s.3 item 5):** the principal will close it after a check for similar patterns on
  other roots, with their hypothesis: NQ is more volatile, so in a high-volatility regime bigger moves revert more.
  That check is D721.
