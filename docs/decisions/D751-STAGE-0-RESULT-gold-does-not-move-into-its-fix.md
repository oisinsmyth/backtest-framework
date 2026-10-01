# D751 STAGE 0 RESULT — NOTHING on both legs: gold moves enough around the LBMA PM auction to pay, but its first US half-hour predicts neither the move into the fix nor a reversal after it

*2026-10-01. One run of `scripts/stage0_d751_gold_fix.py --run` under the system interpreter. The
[pre-registration](D751-STAGE-0-PRE-REG-the-gold-fix-on-mgc.md) was committed before the runner, and the runner
(`96ff50a8`) before its run.*
- **Output:** `data/stage0_d751_gold_fix.json`.

## 0. Checks

- **The seal:** GC was read with a parquet filter (before 2024-01-01).
- **The events:** 3,162 clean sessions 2011–2023; 1,415 gated (after the 250-session burn-in, so the scored window
  starts in 2012).
- **The clock:** the 15:00-London fix equals the statutory-rule implementation on a sample of scored sessions and on
  every business day in the self-test. There are 213 mismatch sessions at 11:00 ET, 124 of them gated.
- **The canaries fired:** the fix − 4 signal changed some signs, and the leaky gate changed some gates.
- **Sign audit in money:** a rise pays the long A leg.
- **Right quantity:** A ≠ B, the gated set is a strict subset, and the placebo clock never equals the fix clock.
- **A DESIGN ERROR IN THE PRE-REGISTRATION, disclosed: the "A15" sensitivity is void.**
  - It measured fix − 15 → fix + 5, but the signal is the move from 09:30 to fix − 5. Its first ten minutes are
    inside the signal window, so it is partly the signal itself (look-ahead). Its +\$16.23 means nothing.
  - The primary legs A (fix − 5 → fix + 5) and B (fix + 5 → fix + 30) start at or after the signal's end and are
    unaffected.
- **The component line:** daily nets of D737's twin, NQ F2 and C1, from D749's `--other-lines` mode under the project
  interpreter (temp CSV), read by the run.

## 1. The result

One MGC, cost \$5.93, so 2c = \$11.87.

| leg | trades | gross (NW t) | net | mean \|move\| (O1) | N1 rotation p50 / p95 / p | N2 11:30 placebo | Holm | reading |
|---|---|---|---|---|---|---|---|---|
| **A gated** (into the fix) | 1,415 | **+\$0.81 (+1.12)** | −\$5.13 | \$18.45 | −0.00 / +1.16 / 0.12 | +\$0.23 (Welch t 0.68) | 0.24 | NOTHING |
| **B gated** (fade after) | 1,415 | **−\$0.00 (−0.00)** | −\$5.93 | \$23.33 | −0.02 / +1.49 / 0.49 | +\$0.55 (Welch t −0.48) | 0.49 | NOTHING |
| A ungated | 3,107 | −\$0.09 (−0.20) | −\$6.03 | \$17.27 | | | | |
| B ungated | 3,107 | +\$0.23 (+0.39) | −\$5.70 | \$22.28 | | | | |

- **Room exists on both legs:** the mean |move| is 1.6–2.0 × the bar.
- **The signal carries no direction:** neither leg beats its rotation, its placebo clock or zero. **GO is false.**
- **N3, the daylight-saving control:** the 124 gated mismatch sessions are more telling than the averages.
  - A at the real fix (11:00 ET) is +\$3.25; at the ET-clock 10:00 it is +\$4.52.
  - B at the real fix is −\$0.26; at 10:00 it is −\$6.44.
  - Nothing follows the London clock.
- **Eras:** phone fixing (n 328), A +\$1.20 and B −\$0.53; ICE auction (n 1,087), A +\$0.69 and B +\$0.16. Neither
  era shows the flow.

## 2. The four groups

| | A gated | B gated |
|---|---|---|
| net Sharpe / Sortino | −1.95 / −2.62 | −1.77 / −2.18 |
| gross Sharpe | +0.31 | −0.00 |
| max drawdown | \$7,301 | \$8,839 |
| median net | −\$6.93 | −\$3.93 |
| win rate / payoff | 0.36 / 1.05 | 0.42 / 0.82 |
| skew / kurtosis | +1.06 / 6.8 | −0.21 / 13.0 |
| trims: ex-top / ex-bottom / trimmed | −6.41 / −4.26 / −5.55 | −7.19 / −4.49 / −5.74 |
| positive years | 1 of 12 (2020) | 1 of 12 (2012) |
| long / short gross | −\$0.17 (718) / +\$1.81 (697) | +\$1.90 (697) / −\$1.84 (718) |
| breakeven cost | \$0.81 | \$0.00 |
| about 109 trades a year | 20 minutes held | 25 minutes held |

**The component line:** daily ρ with D737's twin −0.01 / −0.02, with NQ F2 −0.01 / −0.02, and with C1 +0.03 / +0.01
(A / B).

## 3. Predictions against the outcome

- **The Fable agent:** 25% → NOTHING.
- **This session:** about 15% → NOTHING ✓. The higher MGC fee proved irrelevant: there is no signal to pay it with.

## 4. Reading

- **Gold does not carry a US-hours flow into its fix, as proxied by its own first half-hour.**
  - The fix window moves (about \$18–23 a micro), but in no direction the morning predicts, and no differently from
    11:30 or from the ET clock in mismatch weeks.
  - The ETF authorised-participant story may be right about who trades at the fix. But a price-only proxy for their
    flow (gold's own 09:30 move) does not see it. Their net creation would need fund-flow data, which is not on disk.
- **With D749:** both London-fix constructions on the micros are NOTHING. The fixes move prices, but not in a
  direction knowable from public price or equity information before the window.

## 5. Next

- **The reading is NOTHING.** Closing it is the principal's call (R15).
- **From the same brainstorm, still untested:**
  - the London Metal Exchange official price on copper (MHG, 07:20 ET);
  - the Dow earnings repricing (MYM; needs pre-market stock data that is not on disk);
  - Gotobi (under the micro bar by its own sizing).
