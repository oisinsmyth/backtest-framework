# D647 — POST HOC: why stage S-A failed. The pre-registered trade makes money on the true labels; the observables cannot see trend days

*2026-09-28. The principal: "do some diagnosis and statistical analysis of the failures and assess whether there are
any improvements to be had". EXPLORATORY, after D646's verdict, on the same in-sample data:
`scripts/diag_opening_phase3.py` → `data/opening/diag_phase3.json`. It re-runs D646's walk-forward exactly. **Nothing
here is a test or a selection**, and nothing changes D646.*

## Findings (t0 = 10:00, 2,030 out-of-sample sessions, 4,032 session-markets)

1. **The oracle ceiling.** The TRUE label is traded with D645's exits (stop at 0.5 × the 09:30 → t0 range, 60-minute
   time stop), net of the micro cost (2.79 bp mean):

   | label | n | net per trade | t | median | win | stopped |
   |---|---:|---:|---:|---:|---:|---:|
   | CONT → d0 | 682 | +12.6 bp | 8.6 | +10.6 | 61% | 31% |
   | FADE → −sign(gap) | 862 | +6.4 bp | 4.1 | +1.7 | 51% | 35% |

   **The trade is not the bottleneck; classification is.** (A hold to the close is not a fair ceiling: CONT is
   defined on open-to-close, so it is circular.)
2. **Discrimination (one-vs-rest AUC, OOS):**
   - CONT **0.506**: no information about trend days;
   - FADE 0.655;
   - RANGE 0.593.
   - p_CONT never reaches θ (0.05% of rows), p_FADE on 2.0%. The median max p is 0.64, the RANGE base rate.
3. **Features** (the OOS log-loss increase when one is dropped):
   - `loc_against` +0.0129, `vol_z` +0.0052, `gap_atr` +0.0037;
   - `loc_with` −0.0009 and `r_sigma` −0.0012: both are noise.
4. **Dose-response by probability decile** (60-minute trade, gross):
   - p_CONT ranks the continuation trade, Spearman 0.62 over ten deciles. Top decile: +4.5 bp gross, +1.6 net
     (≈ t 0.8).
   - p_FADE is flat, Spearman 0.12. Top decile: +5.2 gross, +2.5 net (≈ t 1.2).
   - Ten looks each; neither is evidence.
5. **FADE days fill mostly inside the hour:**
   - the median fill within 60 minutes is 80% of the gap; 55% of days reach 75% inside the hour;
   - the median by the close is 129%.
   - The policy's FADE calls are right 40% of the time, and the stop takes 35% of even the true-FADE trades.
6. **Unconditioned trades:**
   - **B1 (follow d0):** +0.76 bp gross (t 1.3), −2.03 net; 47% stopped.
     - Gross by year: positive in 2017–2020 and 2024, negative in 2021–2023 and 2025.
     - Held to the close: +2.47 gross (t 1.7), under the cost.
   - **Fading the gap every day:** −0.33 gross. On gaps ≥ 0.25 ATR only: +0.59 (t 0.7).

## Assessment

- **The pre-registered route to the missing information is Phase 4.** A1/A2 (stops, trend followers) are the
  agents meant to identify trend days, and none has been examined against the labels. If they cannot lift CONT's AUC
  above 0.5, the model fails on its own terms.
- **Hypotheses the diagnosis suggests: a v2 list, NOT tested on this in-sample:**
  1. a horizon-matched label (the next hour, which p_CONT appears to rank), or a hold to the close. The first moves
     towards territory D531 and the momentum memory found empty;
  2. a cost-aware decision rule in place of argmax + θ over a 62% base class;
  3. a wider stop.
  All three were seen on this in-sample, so re-testing them here confirms nothing. The unseen data left is the sealed
  vault (one look, the joint run) or forward recording.
