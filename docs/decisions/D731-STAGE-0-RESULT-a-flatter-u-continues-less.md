# D731 STAGE 0 RESULT — NOTHING by the declared rule, and the dose runs the other way: on NQ, the flatter the volume U (a busier lunch against the open), the WEAKER the continuation into the close; with D730, NQ's move continues most on days of low relative participation, and filtering the 13:30 entry by flatness costs money

*2026-10-01. One run of `scripts/stage0_d731_flat_u.py` (0.3 min, with `--data-root` set to the main checkout).*
- **The order:** the [pre-registration](D731-STAGE-0-PRE-REG-a-flatter-u-continues-more.md) was committed first, and
  the runner (`4da8ee9f`) before the run.
- **The audits:**
  - NQ's, YM's and RTY's objects reproduce D727's known answers;
  - the flatness lag audit (raw rows) passed, and its canary fired;
  - F was constant after 13:30;
  - the f tiers passed `tier_audit`.
- **The seal:** nothing dated 2024-01-01 or later was read.
- **The output:** `data/stage0_d731_flat_u.json`.

## 1. S1 — the dose-response: γ on x·(f − 0.5), stacked over the seven clocks 12:00 → 15:00

| root | γ (NW t) | rotation p05 / p50 / p95; rank | without pre-roll | β by flatness tercile: least flat / mid / flattest | the same by the raw trough/peak ratio | reading |
|---|---|---|---:|---|---|---|
| **NQ** | **−0.065 (−1.23)** | −0.096 / +0.001 / +0.098; 0.13 | −0.068 | **+0.073 / +0.054 / +0.035** | +0.078 / +0.069 / +0.021 | **NOTHING** |
| YM | +0.018 (+0.35) | −0.111 / +0.001 / +0.111; 0.61 | +0.055 | +0.020 / −0.008 / +0.031 | +0.031 / −0.044 / +0.047 | NOTHING |
| RTY | −0.049 (−1.14) | −0.080 / −0.000 / +0.081; 0.16 | −0.036 | +0.062 / +0.005 / +0.005 | +0.052 / −0.008 / +0.013 | NOTHING |

- **The prediction ("the higher the trough against the peak, the better") is not supported.** On NQ and RTY the dose
  runs the other way:
  - NQ's continuation falls monotonically from the steepest U to the flattest, on both the normalised and the raw
    ratio;
  - at 13:30 it is +0.111 / +0.058 / +0.041.
- The direction is within the rotation (rank 0.13), so the reading is NOTHING, not ANTI-DETECTS.
- **The median day's U is slightly steeper than normal** (F 0.94–0.95), which is the 0DTE-era drift of the intraday
  shape. F is normalised by the prior 20 sessions, so that drift does not enter f.

## 2. S2 — the 13:30 entry (one MNQ, $4.07, held to 15:59)

| k | book | trades (contracts) | gross / net per MNQ (median) | net Sharpe (Sortino); gross | max DD | P3a $50k | years + |
|---|---|---|---|---|---:|---:|---|
| 0.5 | (a) every entry | 1,171 | +$15.24 / +$11.17 (+$7.00) | **+0.97 (+1.42)**; +1.32 | $1,547 | 0.13 | 5/8 |
| 0.5 | (b) the flattest third | 400 | +$11.48 / +$7.41 | +0.30 (+0.41) | $1,889 | 0.13 | 4/8 |
| 1.0 | (a) every entry | 611 | +$11.14 / +$7.08 (+$6.00) | +0.45 (+0.66); +0.72 | $1,766 | 0.13 | 4/8 |
| 1.0 | **(b) the flattest third** | 254 | +$4.64 / +$0.58 (+$2.00) | +0.02 (+0.03) | $2,531 | 0.13 | 3/8 |
| 1.0 | (c) sized by flatness | 406 (660) | +$9.58 / +$5.52 | +0.15 (+0.20) | $4,566 | 0.39 | 4/8 |
| 1.5 | (a) every entry | 302 | +$9.31 / +$5.24 | +0.25 (+0.37) | $3,219 | 0.00 | 6/8 |

- **The flatness filter costs $6.50 a trade at k 1.0** (rotation p05 −13.58, p95 +14.24; rank 0.24). Sizing up the flat
  days lowers the Sharpe at every k.
- **The ledger line for (b) at k 1.0:** ρ +0.14 with the MACD arm, −0.17 with NQ F2.
- **GO is false.**

**Reported, not a reading:**
- The unfiltered 13:30 entry at k 0.5 nets +$11.17 a trade over 1,171 trades, at net Sharpe +0.97 with a $1,547
  maximum drawdown. That is D727's curve sampled at one clock.
- It is one cell of D727's 11 clocks × 3 thresholds, so it is a selection, and is recorded only as where the
  afternoon continuation is densest.

## 3. What it says

1. **A flatter U does not mark a continuing day on NQ; if anything it marks the opposite.** A busier lunch,
   relative to the open, comes with weaker continuation into the close.
2. **With D730, a consistent picture.**
   - NQ's move continues most when relative participation is LOW: a quiet open (D730's early-volume terciles, +0.071
     against +0.037), and a deep, quiet lunch (here).
   - This agrees with D487 ("the quiet-vol tercile trends most") and with D697 (bursts are exhaustion).
   - **Continuation on NQ is a quiet-tape phenomenon.** Heavy, two-way participation is where moves stall.
3. **The volume line is exhausted for detection.** Neither the level (D730) nor the shape (D731) of participation
   picks out continuing days in the predicted direction. The reverse direction is post hoc on both, and inside its
   rotations.
4. **CLOSED under R15, 2026-10-01, on the principal's word** ("Close the volume-profile detector"). This covers
   D730's and D731's volume-profile trend detectors on NQ, YM and RTY: the level and the shape of intraday
   participation, as a detector, filter or size term for continuation. The principal also declined D727's plain
   follow as a strategy ("I don't want a dumb follow type strategy. I would like an entry signal?"), so no slot-10
   pre-registration of it is proposed. The quiet-tape observation is kept as structure only.
5. **Superseded proposals, kept for the record:**
   - close the volume-profile trend detector (D730 and D731) under R15;
   - the trend line then rests on D727's plain NQ follow, whose confirmation needs the principal's explicit word for
     a slot-10 vault pre-registration;
   - a "quiet-tape" filter would be a new, post-hoc hypothesis. It would need its own pre-registration, and its
     confirmation could only come from data not yet read.
