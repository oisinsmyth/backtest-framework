# D721 DIAG DESIGN — does F2 earn on forecast-quiet days on ES, YM and RTY as it did on NQ, and does the pattern follow the root's volatility?

*2026-09-30. The principal: "Close the quiet-day pattern on F2 after check for similar patterners in other roots. It
may be down to NQ having more volatility than other roots so bigger moves revert more in that regime."*
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run. The
  result is a separate record.
- **What it is:** a check before a closure. It measures on spent in-sample data (to 2023-12-29) and proposes nothing.
  Whatever it finds, the pattern is closed on the principal's word afterwards; the finding is recorded for the
  mechanism.

## 1. The pattern being checked (D720, post hoc)

- **On NQ, sorted by the terciles of D691's day-size forecast:**
  - forecast-quiet days: 64 trades, +$48.41 net, efficiency 0.60;
  - forecast-big days: 121 trades, −$0.61, efficiency 0.036.
- **Spearman of the forecast with F2's gross:** −0.173.
- **The principal's hypothesis:** NQ is more volatile, and in a high-volatility regime bigger moves revert more.
  **Two checkable forms:**
  - **H-a (the pattern generalises):** on each other root, F2's gross falls with the day-size forecast.
  - **H-b (it follows volatility):** the pattern is strongest on the most volatile root, and within a root, on
    forecast-big days F2's larger last-hour moves continue less (or reverse).

## 2. What is built (all in-sample, all cut before 2024-01-01)

- **F2 on each root:** D711's code at 15:30, unchanged (`load_root`, `clock_frame`, `f2_on`). Trades are F2's takes
  in its window, at one micro and the root's own cost line. Known answers the runner must reproduce:
  - NQ: 274 trades, +$20.670105 (D716);
  - YM: 271 trades, +$6.147695 (D711 A2);
  - RTY: 224 trades, +$0.635786 (D711 A2);
  - ES: D707's frozen in-sample answer, 252 trades, +$13.208968.
- **The label, per root:** D671's realised-only size forecast M0 (features g, on_range, rv5, |gap|, event, opex;
  `size_forecast`, walk-forward), and its walk-forward tier τ (`tiers`). Built on each root's own frame (D668's
  `load_bars` and D663's `root_frame`) with every cut constant lowered to 2024-01-01, as in D720.
  - **Overnight range for YM and RTY:** those roots' frames hold day-session bars only, so it comes from
    `fut_opening_globex_1m_ym_rty`, cut at read time. RTY's overnight bars start 2017-07, so its label starts later.
  - **Event days:** from the CME session calendar's own rows for each root.
  - **M0 is the primary label on all four roots,** because IV exists only for ES and NQ. D691's M1 (with IV/RV) is
    reported beside it for ES and NQ, and NQ's M1 reproduces D720's calibration.
- **Audits:**
  - `forecast_audit` and `tier_audit`, each shown to fire on its leaked canary;
  - `overnight_audit`;
  - the date-keyed join of τ to trades (D720's `join_audit`);
  - no session on or after 2024-01-01 anywhere.

## 3. What is computed, per root

- **Calibration by τ tercile:** trades, mean and median gross, efficiency Σg/Σ|g|, mean net, win rate.
- **G1, the pattern:** Spearman(τ at the trade's session, the trade's gross), against the enumerated rotation of τ
  over the root's calendar (offsets 20 … n − 20; the SE of the p95 is 0). Rank, p05, p50 and p95 are reported.
- **The efficiency gap:** efficiency on the low tercile minus the high tercile, against the same rotation.
- **H-b, across roots:** the root's median σ20 (daily bp), set beside its G1 Spearman. With four roots this is a
  description, not a test.
- **H-b, within a root:** on forecast-big days (τ ≥ 2/3), Spearman(F2's a, the last hour's move in σ units, with the
  gross), and the same on forecast-quiet days (τ < 1/3). Bigger moves reverting more in the big regime shows as a
  lower (or negative) slope there.
- **The books:** F2 unsized, and F2 on τ < 1/3 only, with net and gross, Sharpe and Sortino, trades and years
  positive. Reported, and nothing is chosen.

## 4. Readings (per root, declared now)

| reading | condition |
|---|---|
| **SIMILAR** | G1's Spearman is below the 5th percentile of its rotation (F2 earns less on forecast-big days, beyond chance) |
| **NOT SIMILAR** | G1's Spearman sits inside the rotation's 5–95% band |
| **OPPOSITE** | G1 is above the 95th percentile |

- NQ is re-scored under M0 as the reference, and is not counted as evidence: it is the root the pattern was found on.
- **H-a is supported** only if at least two of ES, YM and RTY read SIMILAR.
- **H-b** is described as above.
- **The closure follows on the principal's word whatever the reading.** If H-a is supported, the result record says
  so plainly, so that the principal decides the closure with that in view.
