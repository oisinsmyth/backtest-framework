# D627 PRE-REGISTRATION — Stage A, H1a: does the leveraged funds' predicted rebalance SIZE show up as extra settlement-window volume?

*Drafted 2026-09-25. It is committed alone, before its runner exists (R8). The design is A8 and A9 (the principal's,
2026-09-25). The principal approved the verdict ladder in §6 on 2026-09-25: a failed placebo or rotation control
gives UNRESOLVED, never a kill. They also judged §0's scale check not significant enough to need a caveat on any
result.*

## 0. Where this comes from, and what has already been seen

The settlement flow ledger's Stage A kill test (deposit §9, H1) needs aggressor-signed window flow. That flow is not
free, and D624 showed the free one-second bars cannot estimate it. A8 moved Stage A to **H1a**: the *size* of the
predicted P1 rebalance against the *size* of abnormal window volume, which the free bars give exactly. Direction
rests on H2. A9 settled five design points before this record: the summed dependent, τ's cost line, the
Newey-West report, the rotation control and the plausible effect.

**Read before this record, all disclosed.** None is an association between the predictor and the dependent.
- **Predictor side, in full:** the P1 panel (`build_predicted_flow_panel.py`), its §7.2 gate and τ\* counts (CL 798
  and NG 1,028 signal days of 1,936), and its scale by year.
- **Dependent side, descriptive only:**
  - the known-answer match of the one-second window volume to the 1-minute fixture's 14:28 and 14:29 bars (exact on
    1,966 front days per root);
  - the window's median share of 09:30–14:30 volume (CL 3.4%, NG 5.9%);
  - a scale check: the per-year median of the day-by-day ratio |Q_traded| / raw window volume in the largest-share
    contract (CL 0.014–0.74, NG 0.022–1.03).

  That last one pairs the predictor with the dependent's raw LEVEL (not the abnormal A_t) day by day, in order to
  size one against the other. No correlation, slope or conditional statistic was computed. It is recorded because it
  is the closest any look came to the outcome.
- **Power** (`SETTLEMENT_FLOW_LEDGER_POWER.md`) used PRE-SAMPLE noise (2015-06-29 → 2017-05-19) and read no in-sample
  window volume.

## 1. Sample

- **Per root, CL and NG,** every NYMEX business day 2017-05-22 → 2025-02-28 on which τ\* is defined. That excludes
  the 20-day warm-up and 2020-02-28, the Databento gap whose held legs have no price.
- **CL excludes A1's transition,** 2020-04-01 → 2020-09-16.
- **Planned n:** CL 1,819 and NG 1,936. The runner reports the realised n and every excluded day by reason.
- **Inputs:**
  - `data/ledger_predicted_flow_daily.csv.gz`;
  - `data/ledger_window_volume_daily.csv.gz`;
  - `data/ledger_calendar_flags.csv`;
  - `data/ledger_fut_share_daily_a6.csv.gz`.

  All were built under A6's cut (`reserved_from="2025-03-01"`) and each carries its own guard. The runner re-asserts
  that no row is dated on or after the cut.

## 2. The regression, per root

    A_t = α + β |Q_t| + γ1 |r_t| + γ2 P_t + Σ δ_k F_k,t + ε_t

- **A_t, abnormal window volume (A9.1):**
  - Σ over the held contracts H_t of outright volume 14:28:00–14:30:00 ET (`vol_win`),
  - minus the mean over business days t−20 … t−1 of the same sum over the same contracts H_t.
  - A held contract with no row on a day traded 0.
- **|Q_t|:** |q_est| at τ\* (§7.1's earliest pass: 13:50, else 14:00, else 14:10, and 14:10 on a no-signal day).
  - Contracts, summed over the held contracts.
  - It is P1 alone (K = 0, p = 0) over BOIL+KOLD (NG) or UCO+SCO (CL), at f_est[t−1] and AUM[t−1].
- **|r_t|:** the held return from the prior settlement to 14:28 (the panel's r_held at τ = 14:28).
- **P_t:** the held contracts' 13:30–14:28 volume minus its own mean over t−20 … t−1 on the same contracts.
- **F:** the calendar flags from `ledger_calendar_flags.csv`:
  - index_roll_close, fund_roll, expiry, eia_report;
  - for CL, also index_annual_roll and index_reset;
  - for NG, also ng_spot_last3.
- **Estimation:** OLS with HC1 standard errors. That is A8's day-clustered t, since there is one row per day.

## 3. The futures share (A3, A4)

- **NG:** f = 1 is proven on every day except BOIL in 2023 and the carried days of 2025. Those use A4's
  imputation, like CL.
- **CL, A4's multiple imputation:**
  - M = 50 paths, seed 20260924.
  - On each path, each estimated segment (anchor_prev → anchor_next) of each fund gets one error e ~ N(0, σ_q²), and
    f = clip(f_est + e, 0, 1).
  - σ_q = h / 1.645 in an ordinary quarter and h in a DISFAVOURED one, with h = 0.162 (A6).
  - Proven days are not drawn.
  - The paths combine by Rubin's rules. The gate reads Rubin's t.
- **A3's four readings** (f_est, f_pit, f_lo, f_hi) are each run and reported. A3's guard applies if CL carries the
  study alone.

## 4. Controls that must fire (A8, as amended by A9)

- **C1, time placebo.** The same regression one window earlier:
  - A^plc_t: the held contracts' 11:50–12:20 volume minus its trailing mean;
  - |Q| at τ = 11:30;
  - |r| to 11:30;
  - P^plc: the 10:52–11:50 volume minus its trailing mean;
  - the same flags.

  **It must give |t| < 2.**
- **C2, the rotation null (A9.4).**
  - |Q| is regressed on the controls, and its residual is rotated circularly within each year by an offset drawn
    uniformly from [20, n_year − 20], then added back to the fitted part.
  - 1,000 rotations, seed 627, each refit with HC1.
  - **The observed t must exceed the rotations' p95.**
  - On CL it runs on the f_est reading.
  - The p50 and p95 are reported, with the p95's bootstrap SE (CLAUDE.md: a sample p95 is biased toward the centre).

## 5. What passes

Per root, **H1a PASSES** if all three hold:
1. β̂ > 0 with t ≥ 2 (Rubin's t on CL);
2. C1: the placebo has |t| < 2;
3. C2: the observed t exceeds the rotation p95. A margin within 2 bootstrap SEs of the p95 counts as UNRESOLVED
   (D373's rule).

## 6. The verdict ladder, and what each outcome does

| outcome | condition | consequence (A2, A8) |
|---|---|---|
| **PASS** | all of §5 | the instrument's line continues; Gate 1 then needs H2 (A8) |
| **FAIL** | β̂ ≤ 0, or t < 2 (Rubin's t on CL), whatever the controls show | **that instrument's line is killed** (A2). The premise is killed only if both roots fail |
| **UNRESOLVED (control)** | t ≥ 2 but C1 fires (\|t_placebo\| ≥ 2) or C2 is not beaten | neither pass nor kill: the size link is not separated from general activity. Written up and put to the principal |
| **UNRESOLVED (margin)** | C2's margin within 2 SE | as above |

**What a pass does NOT say (A8):** a pass cannot tell buying from selling, and a flow that nets still passes. It
says the predicted size arrives in the window, scaled by fund AUM. It says nothing about the ledger's sign.

## 7. Reported beside, never gating

- The Newey-West t (5 lags) for the main regression and C1. The result says so if it falls below 2 (A9.3).
- The same regression on:
  - abnormal daily TAS volume in the held months' TAS contracts (session open → 14:30; A8);
  - the largest-share contract alone (A9.1);
  - τ fixed at 14:10 (the deposit's secondary variant);
  - τ\* re-derived on the micro cost line: MCL $5.03 a round trip; MNG $4.00, hypothetical before its 2022 launch.
- Splits: by year; CL era A and era B; signal days vs no-signal days; with and without roll days.
- β̂ in contracts, and the implied share of predicted P1 that lands in the window, with the plausible effect β = 0.25
  (A9.5) beside it.
- A3's four readings on CL.
- **Not applicable:** Sharpe, Sortino, trade distribution and the component line. H1a is a premise test on
  volume and books no position; H2, a later record, carries the price test.

## 8. The runner and its assertions

- **File:** `scripts/run_h1a_stage_a.py`, with `--selftest` and `--check`. **Output:** `data/ledger_h1a_stage_a.json`,
  with a `REQUIRED_OUTPUTS` guard: the per-root verdict, β̂, the HC1 and NW t, C1, C2's p50/p95/SE, and n.
- **Lag audit.** A second implementation re-derives |Q| from q1 × f without reading `q_est`. It asserts:
  - every AUM and f date is strictly before t;
  - τ\* re-derived from `gate_pass` matches `is_tau_star`.
- **Sign audit.** Q has the sign of r for both funds; the panel's own guard is re-checked.
- **Right-quantity.** The main regression's dependent is `vol_win`-based and C1's is `vol_plc`-based. The runner
  asserts that they differ, and that A_t is not the raw level.
- **Selftest.** The real design, with the pre-sample noise from POWER:
  - β = 0.5 injected → PASS;
  - β = 0 → not PASS;
  - AUM[t] swapped for AUM[t−1] → the lag audit RAISES;
  - a rotation run on an unresidualised |Q| → a different p95 (the check reads what it claims to).
- The runner runs with `-W error::RuntimeWarning`.

## 9. What this does not touch

- No vault data (2025-03-01 → 2026-09-18).
- No signed flow and no price move after τ.
- Nothing from D624–D626's post-vault or sibling samples.
- **Deviations** are listed in the output and never replace a verdict.
