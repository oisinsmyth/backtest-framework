# D632 PRE-REGISTRATION — Stage C1 on NG: does forecasting the leveraged funds' creations improve the ledger?

*Drafted 2026-09-26, on the principal's word ("Start Stage C, pre-register it"). It is committed alone, before its
runner exists (R8). Stage C1 is the deposit's (§P3.4 baseline, §P3.5 with h = 0, §6, §8, §10), under A1–A10. It is
judged against Stage A, the last retained stage: Stage B was not retained (D631). This record fixes what the
deposit leaves open and nothing else.*

## 0. Where this comes from, and what has already been seen

- **The mechanism** (deposit line 171). Retail buys BOIL or KOLD, the fund creates shares, and it trades futures at
  L × the creation, at the settlement.
  - **ProShares' clocks** (D619): orders are taken to 2:00 p.m. ET and the NAV is struck at 2:30 p.m. `lag_c = 0`,
    so day t's creations are traded at day t's settlement and are **not known at τ**. C1 forecasts them.
- **The alignment is proven,** not assumed. The AUM of date t holds day t's creations:
  - `check_ng_contract_counts` matched the audited quarter-end futures counts with the SAME date's shares (reading
    A: KOLD 30/30, BOIL 24/27);
  - it missed with the next date's (reading B: 14/30, 13/27).
- **The flow is measured from the published AUM,** ΔCreate_f[t] = AUM_f[t] − AUM_f[t−1] × NAV_f[t] / NAV_f[t−1]. The
  deposit's line 217 (Δshares × NAV) is not used: the shares are back-adjusted for reverse splits and rounded to 10,
  which is worth $0.1–1M a day before 2020 (D619's reading C).
- **UNG is absent.** No daily shares count exists for it (the data-gap register's G7). Its creations stay outside the
  ledger.

**Read before this record, all disclosed:**
- **The predictor side, and D627–D631 in full.** D629 found that, without the return control, NG's window flow runs
  AGAINST P1 (t −7.98).
- **The creation flows, from the funds' own NAV and AUM** (C1's fitting target, deposit §8). POWER found:
  - they are LARGER than P1 (SD 2,162 against 1,814 contracts, out-of-sample days);
  - they are strongly NEGATIVELY correlated with it on the same day (**−0.68**): investors redeem BOIL and create
    KOLD on up days;
  - the funds' NET trade, P1 + creations, is therefore much smaller than P1 and often of the opposite sign.

  **That would produce D629's unconditional negative sign by itself.** C1 is the test of whether the ledger improves
  once the creations are forecast.
- **POWER's forecast skill:** the deposit's C1 (lagged regressors only) has out-of-sample R² 0.071 (BOIL) and 0.031
  (KOLD). A same-day variant with the return to τ has 0.39 and 0.29 (§6).
- No window flow or price was read for this record beyond D627–D631's published results.
- **This is the sixth test on this in-sample with this predictor** (D627–D632).

## 1. Sample

- NG, the 1,936 days with a defined τ\*, 2017-06-20 → 2025-02-28.
- **The out-of-sample days are D631's blocks:** 252 training days, then 63-day tests, rolling. They are 1,684 days
  from 2018-06-20.
- **Inputs:**
  - the P1 panel;
  - `data/fixtures/fund_nav_daily.csv.gz` (D619), read below 2025-03-01 with a guard;
  - D629's signed window panel (the window and midday flows);
  - the calendar flags;
  - D630's minute bars for the price clause.

## 2. The Stage C1 ledger at each τ ∈ {13:50, 14:00, 14:10} (and 11:30 for the midday control)

    μ_C1(τ) = P1(τ) + Q3_hat(τ),     Q3_hat(τ) = Σ_f L_f × ΔCreate_hat_f[t] / (10,000 × P_held(τ))
    σ²_C1(τ) = σ_Q(τ)² + Σ_f (L_f / (10,000 × P_held(τ)))² × s²_f

- **ΔCreate_hat_f[t] = a0 + a1·r[t−1] + a2·(r[t−5] + … + r[t−1]) + a3·ΔCreate_f[t−1]** (deposit line 220), per fund
  (BOIL L = +2, KOLD L = −2). r is the held index's settlement-to-settlement return (`R_day` − 1).
  - Fitted by least squares in each training window.
  - s²_f is the training window's residual variance (the forecast's own error, independence as D5).
  - Coefficients are applied unchanged to the test block.
  - A day with no NAV row carries a flow of 0 (2 days per fund) and is counted.
- **h = 0** (deposit §6, C1): all of the forecast creation flow is taken to land in the window. The hedging split is
  C2's.
- With Q3_hat ≡ 0, the ledger is Stage A exactly: the known answer (§8).

## 3. Stage C1's own trades

§7.2's gate on C1's quantities:
- |I| = 0.7 σ_d √(|μ_C1| / V_d) P_held ≥ 3 × RT_cost, and SNR = |μ_C1| / σ_C1 ≥ 1.5;
- τ\*_C1 is the earliest pass, else 14:10;
- the direction is sign(μ_C1), in `traded_ym` at τ\*_C1;
- the fill and exit are D630's (the close of bar t0+1 to the close of 14:29, dollars per full-size contract).

## 4. The retention rule, OUT OF SAMPLE on D631's blocks

Stage C1 is **RETAINED** if:
1. **flow:** the partial correlation of μ_C1(τ\*_C1) with the window flow S_win, net of [1, r to 14:28, flags], is
   ≥ 1.10 × Stage A's (P1 at τ\*_A, D629's predictor), with Stage A's > 0 (deposit line 417, net of the controls as
   A8 read it);
2. **price:** H2's t over C1's traded days is not below Stage A's H2 t over Stage A's traded days, on the same
   out-of-sample days (line 418);
3. **the midday control (D631's lesson, added by this record, beyond the deposit):** C1's gain at the window,
   ρ_C1 − ρ_A, exceeds its gain at midday. The midday gain uses the same ledger at 11:30 against the 11:50–12:20 flow,
   net of [1, r to 11:30, flags], on days with a clean 11:30 row.

## 5. The verdict

| outcome | condition | consequence |
|---|---|---|
| **RETAINED** | 1, 2 and 3 | C1 joins the ledger. It is frozen (A10), and C2 builds on A + C1 |
| **UNRESOLVED (midday)** | 1 and 2 hold, 3 does not | the gain is not specific to the settlement. Written up and put to the principal |
| **NOT RETAINED (inconclusive)** | 1 or 2 fails | C2 builds on Stage A. C1 is underpowered at D629's slope (0.52), so a miss is inconclusive (§9A.2 rule 5) |
| **VOID** | the NG check of Sierra's sign after 2026-10-10 gives r < 0.8 | the verdict stands as recorded, but may not be used |

## 6. Reported beside, never gating

- **The forecast** (the deposit's §9A "forecast vs ΔShares"): out-of-sample R² per fund, against a zero forecast and
  against yesterday's flow. The coefficient paths, and their signs against the deposit's expectations (a1, a2 < 0;
  a3 > 0).
- **The same-day variant,** C1 plus the held return to τ (known at τ, but not the deposit's C1): all three clauses.
- **D629's puzzle:** D629's literal regression (S on the predictor and the flags, no return control), with P1 and with
  μ_C1. Does the forecast creation flow remove the negative sign?
- **H2 on the out-of-sample days,** CLAUDE.md's four groups: gross and net, Sharpe and Sortino, the distribution with
  the trimmed means, and the traded-day overlap. For C1 beside Stage A.
- The error budget (§8A.1): the out-of-sample MSE of the window flow on each stage's predictor.

## 7. The runner and its assertions

- **File:** `scripts/run_stage_c1_ng.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
  **Output:** `data/ledger_stage_c1_ng.json`, with a `REQUIRED_OUTPUTS` guard.
- **Known answer (raises):** with Q3_hat ≡ 0 and s² = 0, C1's gate equals the panel's at every τ and τ\*_C1 equals
  τ\*_A, exactly, on all 1,936 days.
- **Lag audit (raises):**
  - D627's `audit_flow`;
  - changing ΔCreate_f[t] or r[t] must leave the forecast for day t unchanged. The regressors are dated strictly
    before t.
- **Sign audit:** a BOIL creation adds contracts and a KOLD creation subtracts them; D630's money audit.
- **Walk-forward audit:** every training row precedes its test block.
- **Selftest** (no in-sample window flow or price):
  - a synthetic world where the window flow tracks P1 plus a forecastable creation flow must be RETAINED;
  - a world where it tracks noise must not be;
  - each audit RAISES on a deliberate break.
- `-W error::RuntimeWarning`.

## 8. POWER (`data/ledger_power_stage_c1.json`)

| | value |
|---|---|
| out-of-sample forecast R², BOIL / KOLD (the deposit's C1) | 0.071 / 0.031 |
| … the same-day variant (beside only) | 0.392 / 0.294 |
| SD of P1 / realised creations / C1's forecast, contracts (out of sample) | 1,814 / 2,162 / 771 |
| corr(P1, creations), same day | −0.68 |
| **the ceiling**, if the window flow tracks the funds' net trade: perfect foresight / C1 / the same-day variant | 4.80 / **1.76** / 2.24 |

**Simulated:** the window flow = β × (P1 + creations) + pre-sample noise, with the midday flow as noise. The rate of
clauses 1 and 3 together:

| β | 0 (the null) | 0.03 | 0.061 (D629's slope) | 0.12 |
|---|---|---|---|---|
| retained (clauses 1 and 3) | **11.5%** | 33.5% | **52%** | 72% |
| the median ratio | 0.77 | 0.88 | 1.32 | 2.08 |

- **At the null, 11.5% pass clauses 1 and 3.** A ratio rule is fragile when Stage A's correlation is near zero, as it
  is in the null world. The real Stage A value out of sample is 0.137 (D631), and clause 2 filters further. The rate
  is recorded as measured, not assumed away.
- **Power class: underpowered at D629's slope (0.52),** so a miss is inconclusive.
- Clause 2 is not simulated.

## 9. What this does not touch

- No vault data (A10).
- No CL.
- No UNG (G7).
- No price move or window flow is read before the runner's one run.
- **Deviations** are listed in the output and never replace a verdict.
