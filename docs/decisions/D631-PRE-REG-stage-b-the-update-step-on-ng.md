# D631 PRE-REGISTRATION — Stage B on NG: does updating the funds' predicted flow with the pre-window signed flow improve the ledger?

*Drafted 2026-09-26. It is committed alone, before its runner exists (R8). The principal chose to pre-register and
run Stage B "as written", after POWER showed it cannot be retained (§9). Stage B is the deposit's (§5.2, §6, §8,
§10), under A1–A10. This record fixes what the deposit leaves open and nothing else.*

## 0. Where this comes from, and what has already been seen

- **Stage A is retained on NG** (D629, D630; frozen, A10). Stage B adds the deposit's update step (lines 365–385) to
  P1. It keeps two parameters, p (the share of the flow executed before τ) and R (the measurement noise).
- **Signed flow for the measurement:** A8 blocked Stage B "until real signed flow exists". The principal's
  instruction to pre-register Stage B accepts Sierra Chart's signed flow for it, with its measured error (r ≈ 0.88 on
  the siblings), and under D629 §6's VOID condition: if the CL/NG check after 2026-10-10 gives r < 0.8 on NG, this
  record's verdict is VOID.
- **NG only.** CL's Stage A is INCONCLUSIVE (D629): there is no retained CL stage for B to improve on.

**Read before this record, all disclosed:**
- **The predictor side, and D629's and D630's results in full.**
- **Signed pre-window flow, 13:30 → 14:28, entered D629 as a reported control** (its coefficient was computed, not
  reported). The window flow's relation to the return (post hoc, t −11.7) is D629's.
- **The pre-τ panel** (`build_signed_pre_tau_panel.py`): its known answer only (13:30–14:10 + 14:10–14:28 = the
  frozen 13:30–14:28, exactly on 6,287 contract-days).
- **POWER** (`ledger_power_stage_b.py`): pre-sample signed flow, and the in-sample predictor with UNSIGNED volumes.
- **This is the fifth test on this in-sample with this predictor** (D627–D631).

## 1. Sample and inputs

- NG, NYMEX business days 2017-05-22 → 2025-02-28 on which the §7.2 gate is evaluable at all three candidates
  (1,936, less 15 without a prior variance).
- **Inputs:** the P1 panel (`q_est`, `sigma_Q`, `r_held`, `I`, `snr`, `gate_pass`, `traded_ym` at each τ), the pre-τ
  panel (signed 13:30 → τ), D629's signed window panel, the calendar flags, and D630's minute bars for the price
  clause. All are read below the cut (2025-03-01), each with its guard.

## 2. The Stage B predictor, at each τ ∈ {13:50, 14:00, 14:10}

    K = p σ² / (p² σ² + R);   Q_hat = μ + K (z − p μ);   σ²_post = (1 − K p) σ²
    Q_rem = (1 − p) Q_hat;    σ_rem = (1 − p) √σ²_post                              (deposit lines 380–384)

- **μ** = P1 at τ (`q_est`, contracts over the held contracts); **σ²** = its prior variance, `sigma_Q`² (A5's form,
  as the gate uses it).
- **z** = the abnormal signed flow 13:30 → τ, summed over the held contracts. That is Sierra's Ask − Bid, minus its
  mean over t−20 … t−1 on the same contracts (deposit line 371's S_pre − S_norm; summed over the held contracts, as
  A9.1 sums the dependent). It is then **residualised on [1, r(τ), flags]** with coefficients fitted in the training
  window only. r(τ) is the held return to τ, never later.
  - Why: D629 showed that NG's signed flow leans against the day's return (pre-sample t −5.6). A raw z would carry
    that into the update as if it were the funds. The deposit's literal raw z is reported beside it (§7).
- **p = 0 gives K = 0, Q_rem = μ, and σ_rem = σ: Stage A exactly.** That is the runner's known answer (§8).

## 3. Fitting (deposit §8, §10)

- **Walk-forward:** 252 business days of training, 63 of test, rolling by 63; the first 252 days are training
  only. Parameters come from the training window alone and are applied unchanged to the test block.
- **Per τ, separately:** (p_τ, R_τ), because p is "the share executed before τ".
- **Grid:**
  - p ∈ {0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.35, 0.5, 0.7, 0.9};
  - R = κ × Var(z) over the training window, κ ∈ {0.01, 0.03, 0.1, 0.3, 1, 3, 10};
  - p = 0 is Stage A.
- **Criterion:** the largest partial correlation of Q_rem with the realised window flow S_win (D629's dependent),
  net of [1, r to 14:28, flags] over the training window. That is least squares against window flow, never price
  (D7).

## 4. Stage B's own trades

- At each τ, **Stage B's gate** is §7.2 on its own quantities:
  - |I_B| = |I_A| × √(|Q_rem| / |μ|) ≥ 3 × RT_cost (I is √|Q|-scaled, all else equal);
  - SNR_B = |Q_rem| / σ_rem ≥ 1.5.
- **τ\*_B** = the earliest passing candidate, else 14:10.
- **Direction:** sign(Q_rem) at τ\*_B. **Contract:** `traded_ym` at τ\*_B.
- **Fill and exit:** D630's (the close of bar t0+1; the close of 14:29), in dollars per full-size contract.

## 5. The retention rule (deposit §6, line 416), OUT OF SAMPLE on the concatenated test blocks

Stage B is **RETAINED** only if both hold:
1. **Flow:** the partial correlation of Stage B's Q_rem (at τ\*_B) with S_win, net of [1, r to 14:28, flags], is
   **≥ 1.10 ×** Stage A's (Q at τ\*_A, D629's predictor), on the same out-of-sample days, with Stage A's > 0. The
   "net of the controls" reading is A8's for H1a.
2. **Price:** H2's t on the out-of-sample days, over Stage B's traded days, is **not below** Stage A's H2 t over
   Stage A's traded days on the same out-of-sample days.

## 6. The verdict, and what it does

| outcome | condition | consequence (deposit §6) |
|---|---|---|
| **RETAINED** | both clauses | Stage B joins the ledger. It is frozen (A10), and later stages build on A + B |
| **NOT RETAINED (inconclusive)** | either clause fails | "dropped, and later stages build on the last retained stage": A. POWER classes Stage B as underpowered, so under §9A.2 rule 5 this is **inconclusive** about the update, never "no effect" |
| **VOID** | the NG check of Sierra's sign after 2026-10-10 gives r < 0.8 | the verdict stands as recorded but may not be used |

## 7. Reported beside, never gating

- **Parameter paths:** (p_τ, R_τ) per training window. Unstable parameters are a red flag (deposit §8). The share
  of windows with p = 0 (where Stage B is Stage A).
- The out-of-sample partial correlations of both stages, per τ and at τ\*.
- **The deposit's literal raw z,** without the residualisation: the same fit and both clauses.
- **The full-sample fit** (in-sample, not the rule): the best (p_τ, R_τ) and its partial correlation.
- **The placebo:** the same machinery at 11:30, with z = 10:52 → 11:30 and S = the 11:50–12:20 flow. Its clause-1
  comparison must not "retain".
- **The error budget** (§8A.1): the out-of-sample MSE of S_win on each stage's predictor.
- **Stage B's H2 on the out-of-sample days, CLAUDE.md's four groups:**
  - gross and net per trade;
  - Sharpe and Sortino;
  - the trade distribution with the three trimmed means;
  - traded-day overlap with Stage A;
  - beside Stage A's same-day numbers.

## 8. The runner and its assertions

- **File:** `scripts/run_stage_b_ng.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
  **Output:** `data/ledger_stage_b_ng.json`, with a `REQUIRED_OUTPUTS` guard: the verdict, both clauses' numbers, the
  parameter paths, n, the placebo and the raw-z variant.
- **The known answer (raises):** at p = 0 on every day, Stage B's gate equals the panel's `gate_pass` at every τ, and
  τ\*_B equals `is_tau_star`, exactly.
- **Walk-forward audit (raises):** every training row is dated strictly before every row of its test block.
- **Lag audit:**
  - D627's `audit_flow` on the predictor panel;
  - z at τ uses spans ending at τ: z(13:50) ≠ z(14:10), and z(14:10) − z(13:50) is the 13:50 → 14:10 flow;
  - the residualisation reads r(τ), not r(14:28).
- **Sign audit:** D630's money audit, and Q_rem has the sign of μ when z = pμ (no news).
- **Selftest** (no in-sample signed row after 13:30):
  - a synthetic world where the prior is weak and z is informative must be RETAINED;
  - the null (z pure noise) must be NOT RETAINED;
  - each audit RAISES on a deliberate break;
  - `analyse` runs end to end before the one real run.
- `-W error::RuntimeWarning`.

## 9. POWER (`data/ledger_power_stage_b.json`): Stage B cannot be retained

- **The ceiling, from the ledger's own prior and no data:** Var(Q_true) = Var(μ) + E[σ²]. Here μ's SD is 1,683
  contracts and the prior's RMS SD is 377, so **μ explains 95.2% of Var(Q_true)**. A perfect observation of the true
  flow could raise a correlation that μ attains by at most **2.5%**, against clause 1's 10%.
- **Simulated** (the full walk-forward fit at 13:50 on NG's real design; the pre-sample's pre-window and window noise
  drawn together): clause 1 retains Stage B **1% (null), 2%, 3%, 6%, 5%, 7%, 3% and 5%** at visible pre-window
  footprints π = 0, 0.015, 0.03, 0.06, 0.15, 0.3, 0.6 and 1.0. Out of sample, Stage B's partial correlation (median
  0.04) is below Stage A's (0.07): fitting (p, R) on 252 days mostly fits noise.
- **Power class: underpowered at every effect,** by construction. Clause 2 is not simulated.
- **The expected outcome is NOT RETAINED, whatever the truth.** The update step can matter only once the ledger
  carries participants with wide priors: P2 swaps, P3/P4 creations.

## 10. What this does not touch

- No vault data. The vault's NG Sierra files are on disk and unread (A10).
- No CL.
- **Deviations** are listed in the output and never replace a verdict.
