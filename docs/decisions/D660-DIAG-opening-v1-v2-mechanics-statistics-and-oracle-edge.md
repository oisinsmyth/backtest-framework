# D660 — DIAG: the opening models' mechanics are exact, their results are noise around zero, and the oracle edge is real but needs near-perfect information to reach

*2026-09-28. The principal: "Before closing I would like a diagnostic on the mechanics and a statistical review of the
results. I want to know the oracle edge of this strategy", "both v1 and v2". Post hoc, in-sample only (the runners'
sealed loaders; nothing from 2025-03-01). It changes no verdict of D658 (v1: D645's final stage S-A) or D659 (v2:
D652). `scripts/diag_opening_mechanics.py`, four processes, 88 s wall (3.08×). Output:
`data/opening/opening_v1_v2_diagnostic.json`.*

*Each model is rebuilt with its runner's own functions, and the rebuild reproduces the committed statistic exactly
(`phase45.json`'s H-O2 at 09:45 and 10:00, and `v2_insample.json`'s two cells) before anything else is computed.*

## 1. Mechanics: the engines do what the documents say

| check | V1 09:45 | V1 10:00 | V2-F fade | V2-C hold |
|---|---:|---:|---:|---:|
| **M1** a second exit engine (never calls the runner's simulator): trades re-simulated | 4,079 | 4,114 | 3,039 | 3,803 |
| mismatches | **0** | **0** | **0** | **0** |
| **M2** the decision-to-entry minute, bp per traded trade (> 0 favours the trade) | −1.73 | −1.90 | −1.07 | +0.82 |
| **M3** a harsher fill: policy net per session | −0.139 (was −0.135) | −0.054 (was −0.051) | 0.33 (was 0.40) | 1.30 (was 1.32) |
| M3's variant | stop one tick worse | stop one tick worse | target needs a one-tick trade-through (3 targets lost) | stop one tick worse |

What each check says:
- **M1: exits, stops, flips, time stops and the cost line are exactly as specified.** The second engine was written
  from the documents' text, and it prices every trade to the same bp.
- **M2: the one-bar latency costs the fades about 1–2 bp a trade.** The opening move keeps going for one more minute.
  It helps the hold. It is a real execution cost, and it is not why anything fails: V2-F's per-trade net would be
  about 2.7 bp instead of 1.6.
- **M3: none of the results rests on an optimistic fill.**
- **M4, exits:**
  - V2-F's traded fades: 291 hit the target, and 551 time out at 60 minutes;
  - V2-C: 1,106 held to the close, 153 stopped;
  - V1: 62 and 82 trades, 66 stopped (37 + 29).
- **M5, cost against the gross move.** Per round trip, cost is 3.4 bp on ES and 2.2–2.4 on NQ.
  - V2-F's traded gross is +7.4 bp on ES but +2.8 on NQ, so the NQ fades barely cover cost.
  - V1's gross is negative before cost at 09:45 (ES −10.1, NQ −3.4).
- **M6, V2-F's expected-value rule is over-confident about three times.** The OLS of realised net on the forecast EV
  gives slope 0.36 (t 4.6) and intercept −2.46. The rule trades EV deciles 7–9:

  | EV decile | forecast EV | realised net per row | share traded |
  |---|---:|---:|---:|
  | 7 | +3.1 | −1.2 | 69% |
  | 8 | +7.2 | −2.2 | 100% |
  | 9 | +24.4 | **+6.9** | 100% |

  Only the top decile pays. The reason is the timed-out-trade model:
  - a_T averages −7.1 bp across the 28 windows, where a random walk gives 0;
  - β averages −0.30, where a random walk gives −1.
  - So **a fade that fails loses about 7 bp whatever the model says.** The move carries on after the fade fails,
    which the random-walk form OA-A11 anchored on does not expect.
- **M6, V2-C's rule is better calibrated** (slope 0.85, t 2.7), but its deciles are noisy. Decile 7 (EV +3.2, 92%
  traded) realises −1.6.
- **M7, long against short: the "continuation" is the long side.**
  - V2-C, trading every day: long **+2.54 bp** a row, short −0.13.
  - V2-C's policy trades: long +6.82, short +0.77.
  - V2-F: fading a gap down (a long) +3.37 a trade, fading a gap up +0.30.
  - V1 (small n, FADE only): long fades lose −17.4 and −10.7, short fades make +0.9 and +10.2.
  - **V2-C's edge is the index's upward drift from 10:30 to the close, not a continuation signal.**

## 2. Statistical review

| | V1 09:45 | V1 10:00 | V2-F | V2-C |
|---|---:|---:|---:|---:|
| policy net per session | −0.135 | −0.051 | +0.398 | +1.317 |
| block-bootstrap 95% CI (20 sessions, 10,000 draws) | −0.42, +0.15 | −0.36, +0.24 | −0.59, +1.46 | −0.15, +2.88 |
| P(mean ≤ 0) | 0.82 | 0.62 | 0.23 | 0.04 |
| HAC t at lags 0/5/10/20 | −1.02 … −0.93 | −0.34 … −0.33 | 0.77 … 0.75 | 1.48 … 1.71 |
| leave-one-year-out, range | −0.24 … −0.04 | −0.21 … +0.14 | **−0.35 (no 2022)** … +0.64 | **+0.86 (no 2024)** … +1.68 |
| diff vs the model's control, CI | +0.45, +3.03 (vs B1) | +0.62, +3.42 (vs B1) | +1.29, +3.72 (vs always) | −2.14, +2.24 (vs always) |
| vault: SE per session (scaled to 390) | 0.32 | 0.35 | 1.06 | 1.72 |
| **vault MDE at 80% power** | 0.90 bp | 0.98 bp | **2.97 bp** | **4.83 bp** |

1. **No policy mean is distinguishable from zero.** V2-C comes closest (P ≤ 0 = 4%). Across two cells its one-sided
   p 0.045 is 0.09 after Holm.
2. **Every significant "diff" is a losing control.** V1's B1 loses 1.9–2.0 bp a day, and V2-F's always-fade loses
   2.1. The model looks good by trading less (memory: "beats the control" is empty below zero). V2-C's diff, the one
   comparison against a control that does not lose, is 0.06 bp.
3. **The standard-error ladder is flat** (lags 0–20). The t's are not an autocorrelation artefact either way.
4. **V2-F is one year and V2-C is not.** Without 2022, V2-F's mean is −0.35, and four of its nine years are
   negative (2018, 2021, 2023, 2024). V2-C survives dropping any single year (min +0.86), and its year means rise: 2024 +4.4, 2025 (two
   months) +8.0. Its edge is the drift noted in M7.
5. **The vault cannot see these sizes.** V2's in-sample means are an eighth (V2-F) and a quarter (V2-C) of what 390
   sessions can detect, which is why D659's power is 5–6.5%.

## 3. The oracle edge

The same trade rules, fed better information. The ladder blends each model's probability with the truth,
p_λ = (1 − λ)p + λ·(the true outcome), and runs the SAME decision rule and simulator. λ = 0 is the model and λ = 1
is perfect foresight.

**V1, the agent-state design** (the argmax policy, sit out RANGE, the flip exits):

| λ | AUC: CONT / FADE | trades | net per session | t | per trade | vault power |
|---|---|---:|---:|---:|---:|---:|
| 0 (the model), 10:00 | 0.51 / 0.66 | 82 | −0.05 | −0.33 | −2.5 | 2% |
| 0.1 | 0.98 / 0.91 | 112 | +0.08 | 0.46 | +2.7 | 4% |
| 0.2 | 1.00 / 0.99 | 222 | +0.58 | 2.43 | +10.7 | 19% |
| 0.3 | 1.00 / 1.00 | 508 | +1.05 | 2.90 | +8.3 | 25% |
| **1 (perfect)**, 10:00 | 1 / 1 | 1,544 | **+3.49** (gross 4.55) | 5.87 | **+9.1** | 73% |
| **1 (perfect)**, 09:45 | 1 / 1 | 1,497 | **+2.85** (gross 3.88) | 5.88 | **+7.5** | 73% |

**V2** (each cell's own label; the EV rule unchanged):

| λ | V2-F: AUC | net/session | t | per trade | power | V2-C: AUC | net/session | per trade | power |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 (the model) | 0.817 | +0.40 | 0.78 | +1.6 | 6% | 0.542 | +1.32 | +4.0 | 12% |
| 0.05 | 0.857 | +1.16 | 2.21 | +4.8 | 18% | 0.802 | +14.4 | +40.3 | 100% |
| 0.1 | 0.893 | +1.90 | 3.57 | +7.9 | 40% | 0.946 | +20.7 | +51.9 | 100% |
| 0.2 | 0.950 | +3.06 | 5.59 | +12.9 | 76% | 0.999 | +26.3 | +61.2 | 100% |
| **1 (perfect)** | 1 | **+6.24** | 13.7 | **+28.7** | 100% | 1 | **+28.6** | **+57.3** | 100% |

How to read the oracle:
- **The ceilings are real:**
  - V1 with a perfect day-type label nets +2.9 to +3.5 bp per session, 7.5–9.1 bp a trade, at t 5.9;
  - V2-F with perfect knowledge of which fades reach the prior close nets +6.2 bp per session;
  - V2-C's +28.6 is partly definitional: its label is "this trade nets > 0", so perfect foresight of it is perfect
    foresight of the day's remaining direction.
- **Reaching them needs near-perfect information:**
  - V1 breaks even only at about λ = 0.1, where CONT's AUC is 0.98 and FADE's 0.91. The model has 0.51 and 0.66.
  - V2-F needs AUC about 0.95 for a 76%-powered vault look, against the model's 0.82. Most of that 0.82 is
    mechanical: the nearer the prior close, the likelier the touch.
  - V2-C's ladder is steep because its label IS the outcome's sign. An AUC of 0.80 on the sign of the rest of the
    day would be worth +14 bp a session, and no feature set here reaches 0.55.
- **The blend is an information yardstick, not a feasible model.** Mixing in the true outcome adds information
  that no pre-10:30 feature carries. The ladder measures how far the models are from paying, not a path to it.

## What it means

1. **The failures are not mechanical.** Exits, costs and fills are exact, and the harsher fills move nothing.
2. **v1: the model cannot tell the day types apart well enough to use.** Its trade rules have a real ceiling
   (+3 bp a session with the label known), and reaching it needs AUCs above 0.9 where the model has 0.51–0.66.
3. **v2's fade (V2-F):** its selection is real, but it is one year (2022) and an over-confident EV rule. Only the
   top EV decile pays, because failed fades lose about 7 bp.
4. **v2's hold (V2-C):** it earns the index's long drift from 10:30 to the close (long +2.5 bp a day, short −0.1).
   That is not continuation, and its model adds nothing to it.
5. **Neither can be confirmed on 390 vault sessions.** The minimum detectable effects are 3–5 bp a session, and the
   in-sample means are 0.4 and 1.3.
6. **Observations only, not tunable here:**
   - V2-F's top-decile-only book;
   - V2-C's long-only drift.
   Both were found by looking at this in-sample, which is spent for them. Either would need its own pre-registration
   and a sample it has not been chosen on. The futures 2024+ slice is spent for trend, so only the vault remains.
