# D635 PRE-REGISTRATION — Gate C0 of the index-reweight model: does the index funds' predicted roll flow reach the settlement window as aggressive flow, and how much of it (κ)?

*Drafted 2026-09-27 on the principal's word ("source the settlement windows, then pre-register C0"). It is committed
alone, before its POWER step and its runner exist (R8). The spec is the deposit `INDEX_REWEIGHT_FLOW_PREREG.md`
v1.3 §5, §8 (Gate C0) and §8B, under amendments IR-A1–IR-A14. It builds on D634, where Gate R0 was RESOLVED on its
re-run and its tracker `drift_tracker_daily_rerun.csv.gz` is the one used. This record fixes only what the deposit
leaves open.*

## 0. Where this comes from, and what has already been seen

- **The deposit, §5:** "S_win = κ_B × Q_roll,B + κ_G × Q_roll,G + ε", fitted walk-forward (252/63 days) on flow,
  never on price. Then the roll-day price move is checked against the square-root impact model with Y = 0.7 fixed.
- **Gate C0, §8:**
  - κ_B (or the combined κ) is > 0 with t ≥ 2 on flow;
  - the roll-day price move in the predicted direction has a positive slope against predicted impact.
  - On a fail, R1 is still run but only descriptively, and no R1 trading hypothesis can pass (R-D5).
- **Read before this record, all disclosed:**
  - **D634 in full:** the drift tracker, the CIMs and ΔN for 2016–2025, and the published-return check.
  - **The settlement-window measurement** (`settlement_windows_vwap_check.json`). It read trade prices and sizes
    inside the windows to reproduce settlements. It read no signed flow and no relation to any roll or flow.
  - **The ledger's CL/NG work (D627–D633).** It read Sierra-signed CL and NG window flow over 2017–2025, including
    roll days, but always against the leveraged funds' rebalance (P1), never against index roll flow. Its calendar
    flags (`index_roll_close`, `fund_roll`) were used as controls, and D630 reported a "without flagged days"
    variant.
  - **The ledger's sibling sign check:** Sierra's net window flow correlates 0.877 (HO) and 0.875 (RB) with the
    exchange flag.
  - **No window flow of any root has been set against predicted index roll flow.**
- **This is the model's second gate on this in-sample.** R0 tested no hypothesis.

## 1. The sample and the observations

- **Roll periods:** every month from 2016-02 to 2025-02, **except January.** January is R1's event (the reweight),
  and leaving it out keeps R1's days out of κ's fit.
- **Observation days:** BCOM hedge business days BD5–BD9 (IR-A3), and GSCI's BD5–BD9 counted on the CME calendar,
  the union of the two. GSCI's two documents disagree on its calendar (CME or NYSE); the CME calendar is used, and
  the NYSE reading is reported beside.
- **Observed contracts:** for each of the 15 CME roots, the BCOM lead L and next N of the month, which are the
  contracts with Sierra files (`data/index_reweight/sierra_download_record.json`). A GSCI leg in a contract with no
  file is unobserved, and its flow is not counted anywhere.
- **Exclusions**, each counted in the output and never replaced by a default:
  - a (root, day) with no served settlement window: `window_for` raises (IR-A9). KE before 2017-01-01 and ZM before
    2016-01-01 are excluded this way.
  - a (contract, day) whose Sierra file does not span the window. This excludes the ZL and ZM December contracts'
    roll-in days (AITODO).
  - a (contract, day) with fewer than 15 of the 20 prior business days on file for the norm (§2). This affects the
    GC and ZS roll-in days with a short pad.
  - a root whose sign check fails (§7).

## 2. The dependent: S_win

S_win(c, d) = the Sierra-signed net aggressor volume of contract c in its settlement window on day d (the sum of
AskVolume − BidVolume over trades in [W_start, W_end), from `window_for(root, d)`), **minus its trailing norm.** The
norm is the mean of the same quantity over the 20 prior business days on which c has a file. The deposit's "trailing
20-day norm" is that mean; at least 15 of the 20 must exist.

## 3. The predictors: Q_B and Q_G, in contracts

- **BCOM (Q_B).**
  - For root i rolling in month m (Table 9a: lead(m) ≠ lead(m+1)), on each BCOM hedge day, the trackers sell 0.2 of
    their L position and buy the same dollar amount of N.
  - H_i = AUM_B(y) × w_drift,i(d−1) / (P_L(d−1) × mult_i). It uses the tracker's weight and the settlement on the
    PREVIOUS business day, both known before the window. AUM_B is IR-A5's point value.
  - Q_B(L, d) = −0.2·H_i and Q_B(N, d) = +0.2·H_i·P_L/P_N. The signs are for long trackers.
- **GSCI (Q_G), per $1bn of GSCI tracking assets** (IR-A12: no GSCI AUM is ever entered).
  - For root i rolling in month m under GSCI's schedule (SOURCES_GSCI_CFTC §2.3: GSCI's letter changes between
    months m and m+1), on each GSCI hedge day: Q_G(c_out, d) = −0.2·G_i and Q_G(c_in, d) = +0.2·G_i·P_out/P_in.
  - G_i = RPDW_i(y) × $1bn / (P_out(d−1) × mult_i).
  - RPDW is the year's published reference dollar weight. 2017 is not published, so it is the mean of 2016 and 2018,
    as declared. Within-year drift is not modelled: an estimate (IR-A2), with the band in §6.
  - GSCI holds no ZL, ZM or COMEX HG, so Q_G ≡ 0 there.
- **The identification.** BCOM rolls the energy contracts six times a year; GSCI rolls them every month. In the months
  where only GSCI rolls, the observed contracts carry Q_G alone. The grains and metals roll on nearly the same months
  in both.

## 4. The model

**Primary:**

    S_win(c, d) = κ_B · Q_B(c, d) + κ_G · Q_G(c, d) + ε,    with no intercept (the deposit's form)

- It is pooled over roots, contracts and days, and fitted by OLS.
- The standard errors are **clustered by roll month** (about 100 clusters). Every root rolls on the same days, so the
  errors correlate across roots within a month.

**Separability (R-D4).** κ_B and κ_G are SEPARATE when BOTH of these hold:
- |corr(Q_B, Q_G)| < 0.9 over the observations; and
- κ_B and κ_G each have t ≥ 2.

Otherwise they are COMBINED. The combined predictor is Q_B + AUM_B(y)·Q_G, which treats GSCI's tracking assets as
equal to BCOM's; the combined κ absorbs the true ratio. Its fit is

    S_win = κ_C · (Q_B + AUM_B(y) · Q_G) + ε

The gate's κ is κ_B when separate, κ_C when combined.

**The walk-forward (the deposit's 252/63):**
- the model is refitted on the trailing 252 business days of observations and predicts the next 63;
- the κ path, the out-of-sample correlation of prediction and outcome, and the out-of-sample MSE against a zero
  prediction are reported.
- It does not gate; the gate reads the full in-sample fit.

## 5. Gate C0

| clause | rule |
|---|---|
| **C0-flow** | the gate's κ (§4) is > 0 with clustered t ≥ 2 |
| **C0-price** | on (root, day) pairs where both L and N are observed, regress the signed spread move m on the predicted spread impact I, with t ≥ 2 and slope > 0 (clustered by roll month). **m** = ((N − L) at the last trade before W_end) − ((N − L) at the last trade at or before t0 = W_start − 10 min), in the direction the roll flow pushes the spread (buying N and selling L widens N − L), converted to dollars per contract. **I** = the sum over the two legs of 0.7 · σ_d · √(\|κ̂ · Q\| / V_d) · P · mult, with κ̂ from C0-flow's fit, σ_d the leg's 20-day trailing SD of daily settlement returns, and V_d its 20-day trailing mean window volume (both from prior days only) |
| **PASS** | both clauses |
| **FAIL** | either clause fails. R1 runs descriptively only (R-D5) |
| **INCONCLUSIVE (underpowered)** | C0-flow fails AND POWER (§8) gives power < 0.8 at κ = 0.05. It is written as inconclusive, not as no effect, with the κ excluded (κ̂ + 2 SE) stated |
| **VOID for a root** | its sign check fails (§7). The root is dropped, and the fit runs on the rest |

- **This record's reading of "positive slope"** is t ≥ 2, as for the flow clause. A slope that is positive but not
  distinguishable from zero does not pass.
- **The κ carried forward** into R1 and the freeze is the full in-sample estimate (to 2025-02). If the freeze
  (IR-A10) comes before C0 has run, it is whatever the frozen code returns on the in-sample.

## 6. Reported beside, never gating

- The fit with an intercept, per root, per year, and on L-only and N-only observations.
- **GSCI's band:** Q_G recomputed with the prior year's and the next year's RPDW in place of the year's own.
- GSCI hedge days on the NYSE calendar.
- **Dose-response:** the mean S_win by quintile of |Q_B + AUM_B·Q_G|, and Spearman ρ.
- **The placebo:** the same fit on BD12–BD16 of the same months, with each observation's Q moved to the same
  weekday there. It must show no effect. If its t ≥ 2 with the gate's sign, that is recorded as a failure of
  specificity (deposit §8's date placebo, applied here).
- The sign-check correlations per root (§7). The count of each exclusion (§1).

## 7. The prerequisite: Sierra's sign, per root (IR-A7)

- **Before C0 reads any S_win,** each root's Sierra-signed window net flow is compared with Databento's
  exchange-flagged `trades` on sessions outside the in-sample and the vault. These are post-vault sessions from
  2026-09-19 on, with at least 10 sessions per root.
- **r ≥ 0.8** keeps the root; below it, the root is VOID for C0.
- For CL, NG, HO and RB the post-vault sessions are D626's sample, readable only after its one read on 2026-10-10.
  The same comparison is D629 §6's for CL and NG.
- **The inputs this needs, each on the principal's approval:**
  - Databento `trades` for the 15 roots from 2026-09-19, quoted first (free in the last-12-months window under the
    CME Standard subscription);
  - Sierra files for the contracts trading in those sessions.

## 8. POWER (before the runner, `data/index_reweight/power_c0.json`)

- **The world:** S_win = κ·(Q_B + AUM_B·Q_G) + noise, on the real observation set, with the real predictors (the
  D634 re-run tracker, IR-A5 AUM, the published RPDW).
- **The noise:** drawn by a block bootstrap over months of each contract's S_win on NON-hedge days (BD12–BD20). That
  reads the flow's spread, never its relation to Q.
- **The grid:** κ ∈ {0, 0.02, 0.05, 0.10, 0.25}, 400 draws each.
- **Reported:** C0-flow's pass rate (the size at κ = 0), the median t, and the separability rate.
- **The plausible effect,** stated before POWER runs: κ ≈ 0.05. The ledger found about 6% of the funds' predicted
  rebalance arriving as aggressive window flow in NG (D629), and index rolls are traded largely as calendar spreads
  and TAS, which move outright aggressor flow less.

## 9. The runner and its assertions

- **File:** `scripts/run_gate_c0.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
- **Output:** `data/index_reweight/gate_c0.json`, with a `REQUIRED_OUTPUTS` guard. It is committed after this record
  and after POWER.
- **Lag audit (raises):** Q uses weights and settlements from d−1 or earlier. The norm uses days strictly before d.
  A second implementation of Q, built from the tracker panel without calling the Q function, must agree exactly.
- **Sign audit:**
  - a long tracker's roll sells L (Q < 0) and buys N (Q > 0);
  - a positive κ with Q > 0 predicts net buying (S_win > 0);
  - the spread move of a roll that buys N is positive when N − L widens.
- **Right-quantity:** the fitted S_win must not equal the norm-free quantity, and the gate's κ must not equal the
  L-only fit's.
- **Known answer:** with every Q set to 0, κ̂ is 0 and C0-flow fails. On a synthetic S_win built as 0.10·Q plus the
  bootstrapped noise, κ̂ is within 2 SE of 0.10.
- **Selftest:** each audit RAISES on a deliberate break; the synthetic world passes; the κ = 0 world fails.
- Reads go through `load_panel(..., reserved_from="2025-03-01")` and cut every Sierra file at 2025-03-01.
  `-W error::RuntimeWarning`.

## 10. What this does not touch

- **No January roll period.** R1's days are untouched.
- No vault data, no 2026 event, and no 2027 publication (IR-A10).
- No price move is read before the runner's one run, except the POWER step's non-hedge-day flow spread.
- **The CIT and swap-dealer auxiliaries (§5A)** and the error budget come after C0. They are not part of this gate.
- **Deviations** are listed in the output and never replace the verdict.
