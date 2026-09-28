# Commodity Index Annual Reweight Flow — Pre-Registration & Design Document

**Status:** PRE-REGISTERED — v1.0 (2026-09-21)  
**Current version:** v1.1 (2026-09-21), additive amendment. All v1.0 text is retained unchanged.  
**Current version:** v1.2 (2026-09-21), additive amendment. All v1.1 text is retained unchanged.    
**Current version:** v1.3 (2026-09-21), additive amendment. All v1.2 text is retained unchanged.
**Changelog:** v1.1 adds auxiliary datasets (3.6), the error budget and auxiliary calibrations (Section 5A), depth-based impact for R1 (H-R4), unit tests 14–20, decisions R-D10–R-D14 and questions R-Q9–R-Q11. v1.2 adds the power analysis (Section 8B), the yearly sign test and calibration check for the annual price effect, unit tests 21–25, decisions R-D15–R-D18 and phase 2b. v1.3 folds the power analysis and alternative validation (8B) into the three-track plan (Section 11): the 2027 event as the 11th sign-test vote, the forward consistency test, and Track 3 treated as a fill and consistency check. Adds unit tests 26–28 and decisions R-D19–R-D21.
**Owner:** Oisin
**Consumer:** Claude Code
**Suggested repo path:** `docs/research/INDEX_REWEIGHT_FLOW_PREREG.md`
**Related docs:** `SETTLEMENT_FLOW_LEDGER_PREREG.md` (shared impact model, fill model, settlement window table, recorder).

---

## 0. Instructions for Claude Code (read first)

1. **Build in the order of Section 12.** Validation gates (R0, C0) must pass before any stage. Stages run in the order R1 → R2 → R3.
2. **This document is the spec.** Do not change definitions, grids, thresholds or kill conditions. If something is ambiguous or impossible, **stop and ask**. Agreed changes are versioned edits (Section 15) *before* code changes.
3. **Never fabricate data or facts.** This includes target weights, AUM estimates, roll schedules, determination dates and settlement windows. Record every sourced fact in `data/index_reweight/SOURCES.md` with a URL and access date.
4. **Log every configuration evaluated** to `results/index_reweight/trials.csv`.
5. **Reuse shared components** from the settlement ledger (impact model, fill model, settlement window table, CostStack, recorder). Flag any change to them.
6. **No look-ahead.** Contract-count flows use prices only up to the determination date. Forecasts before that date use prices available at the forecast time.
7. **Annual events mean a small sample.** Any fitted parameter is validated with **leave-one-year-out** cross-validation (Section 10), never an ordinary random split.
8. Every new function gets unit tests (Section 13).

---

## 1. Hypothesis in one paragraph

Commodity index trackers must rebalance to new target weights every January over fixed execution days. The Bloomberg Commodity Index (BCOM) announces next year's targets in late October; for 2026 it reported estimated tracking AUM of about $108.8B, with new targets taking effect in the January roll period. The true required flow is **not** the headline change in target weights. It is the gap between the **new target** and each commodity's **drifted weight** just before the rebalance, which is computable from prices. Because index weights sum to one before and after, the flows are roughly **market-neutral** across the index. We forecast the per-commodity flow, calibrate price impact on the much more frequent **monthly index rolls**, and test three horizons: **execution days** (intraday, settlement windows), **post-rebalance reversal** (days), and **pre-positioning** (weeks).

---

## 2. Scope

**In scope**
- Index: BCOM (primary, modelled in full). S&P GSCI (stacked, single scale parameter).
- Traded universe: CME Group contracts in BCOM (about 15; the final list is verified against the methodology, R-Q1):

| Group | Contracts |
|---|---|
| Energy (NYMEX) | CL, NG, HO, RB |
| Metals (COMEX) | GC, SI, HG |
| Grains (CBOT) | ZC, ZS, ZW, KE, ZL, ZM |
| Livestock (CME) | LE, HE |

- Non-CME BCOM components (Brent, gasoil, LME metals, ICE softs) are used **only** to compute drift. They are never traded.
- Only contracts the owner's prop firm offers are traded (R-Q6). The full index is always used for drift.
- Two position constructions, both pre-registered (Section 7): **A** outright per commodity, **B** market-neutral basket.

**Out of scope (v1)**
- Other commodity indices.
- Discretionary overrides.
- Trading non-CME contracts.

---

## 3. Data specification

### 3.1 Index facts (per year, 2016 → 2027)

For each year, record in `data/index_reweight/weights/<year>.csv`: announcement date, target weights for all components, the published tracking-AUM estimate, and the source URL.

**Verified example (2026 targets, announced 30 Oct 2025):** natural gas 7.78% → 7.20%; WTI 6.97% → 6.64%; energy group 29.44%; tracking AUM estimate $108.8B.

### 3.2 Methodology facts (source and verify, R-Q1)

- BCOM monthly roll schedule: business days and daily fractions. The January rebalance is understood to run over the 6th–10th business day, with changes phased in gradually. **Verify.**
- Designated contract month per commodity for each month (the lead contract schedule).
- **CIM determination date:** the date whose prices set the new commodity index multipliers (the contract counts per commodity).
- Holiday and market-disruption rules.
- S&P GSCI: annual weights, roll days, and the equivalent determination rules (R-Q4).

### 3.3 Prices

- Daily settlement prices for **all** BCOM components' designated contracts, 2015 → present. CME from Databento; ICE and LME from sources to be confirmed (R-Q3).
- 1-minute bars and aggressor-side trades for the traded CME contracts, 2016 → present.

### 3.4 Settlement windows

A per-product table of settlement window start and end times with effective dates, sourced from CME settlement procedures (R-Q5). This is shared with the ledger doc. **No window time may be assumed.**

### 3.5 Forward recording

Add to the settlement ledger's recorder (Track 2): daily settlement prices for all BCOM components, the BCOM announcement page (checked daily from 1 October), and published index data when available.

---

### 3.6 Auxiliary datasets (v1.1)

| Dataset | Source | Cost | Frequency | Use |
|---|---|---|---|---|
| Supplemental Commodity Index Traders (CIT) report | CFTC | Free | Weekly | Direct weekly measure of index-trader positions in covered agricultural markets (confirm list, R-Q9). Auxiliary estimate of κ for ags (5A.2) |
| Disaggregated COT, energy and metals | CFTC | Free | Weekly | Swap-dealer net changes as a weaker proxy for index exposure in non-ag contracts (5A.3) |
| CME market-by-order | Databento | Paid | Order-level | Resting depth at t0 for depth-based R1 impact (5A.4) |

Add the weekly COT and CIT releases to the recorder. Both are usable only after their Friday release.

## 4. The drift tracker (shared backbone)

### 4.1 Excess-return reconstruction

For each component i, reconstruct its excess-return sub-index `R_i(t)` from designated-contract settlement prices and the roll schedule, starting at 1.0 on the prior year's CIM determination date.

### 4.2 Drifted weights

```
w_drift,i(t) = w_target,i(y−1) × R_i(t) / Σ_j [ w_target,j(y−1) × R_j(t) ]
```

Weights equal the prior targets at the determination date and then drift with relative performance.

### 4.3 Required flow in contracts

On the new determination date (det):
```
ΔN_i = AUM_B × (w_target,i(y) − w_drift,i(det)) / (P_i(det) × mult_i)       (contracts)
ΔN_i,d = φ_d × ΔN_i,       φ_d = daily fraction on execution day d (expected 0.2 × 5; verify)
```

- **Before det:** the same formula uses the latest available prices, giving a **forecast** of ΔN_i with uncertainty from possible further drift.
- `AUM_B` = the published tracking-AUM estimate for that year.
- An **effective participation factor** κ_B (Section 5) converts published AUM into flow that actually reaches the settlement window.

### 4.4 GSCI stacking

```
ΔN_i,G = κ_G × (implied GSCI weight change per component, in contracts per unit AUM)
```

κ_G is a single scale parameter, fitted as in Section 5.

### 4.5 Net-flow check

Across **all** BCOM components, Σ_i ΔN_i × P_i × mult_i ≈ 0 (weights sum to one before and after). Report the CME-subset net for each year; it indicates how neutral construction B can be.

---

## 5. Impact calibration on monthly rolls (C0)

BCOM and GSCI roll positions every month on set business days, executed like the rebalance. This gives about 12 calibration events a year per contract.

For each monthly roll day and traded contract:
```
Q_roll,i,d = predicted roll flow (contracts, from designated-month changes, reconstructed AUM exposure)
S_win,i,d  = aggressor-signed volume in the settlement window, minus its trailing 20-day norm
Fit:  S_win = κ_B × Q_roll,B + κ_G × Q_roll,G + ε
```

- κ_B and κ_G are fitted by walk-forward (252/63 days) on **flow**, never on price.
- Price impact on roll days is then checked against the square-root model: `I = Y × σ_d × sqrt(|κQ| / V_d) × P`, with **Y = 0.7 fixed**.
- **BCOM and GSCI roll days overlap**, so their κ values may be collinear. Report the correlation of the two predictors and their joint confidence region. If they can't be separated, use a single combined κ (decision R-D4).

---

## 5A. Error budget and auxiliary calibration (v1.1)

### 5A.1 Error budget
After C0 and after each stage, decompose the forecast error into (a) the flow forecast (drift, AUM, κ) and (b) impact. Use leave-one-component-out changes in out-of-sample error, plus the auxiliary checks below. Output: `results/index_reweight/ERROR_BUDGET.md`. Remaining stages may be reordered to target the largest error, logged in the decision log **before** running. No new stages may be added this way.

### 5A.2 CIT-based participation (agricultural contracts)
For each covered ag contract, weekly:
```
ΔCIT_i,w = change in CIT index-trader net long position, week w
ΔIDX_i,w = predicted index position change from monthly rolls and the January rebalance, per unit κ
Fit:  ΔCIT_i,w = κ_CIT × ΔIDX_i,w + ε
```
- κ_CIT and its SE act as an **informative prior** on κ (combined or BCOM) for ag contracts in C0.
- **Consistency flag:** the flow-fitted κ differs from κ_CIT by more than 2 combined SE.
- Note: CIT positions are **net positions** across all index participants, not window flow, so they validate the size of index exposure, not how much of it reaches the settlement window.

### 5A.3 Swap-dealer proxy (energy and metals)
Same fit as 5A.2, using disaggregated swap-dealer net positions. Expected to be noisier (swap dealers hedge many client types). **Reported only**, never used as a prior unless the ag CIT fit and this fit agree on the shared overlap period (R-D12).

### 5A.4 Depth-based impact for R1
Identical to the ledger doc's 8A.4: `I_D = I × sqrt(D̄ / D(t0))`, no fitted parameters. The existing impact definition stays as the baseline; I_D is adopted only if H-R4 passes.

## 6. Stages

### Stage R1 — Execution days (intraday)

For each of the five January execution days and each traded contract:
- `Q_i,d = κ_B × ΔN_i,d + κ_G × ΔN_i,d,G`.
- Predicted impact `I_i,d` from the square-root model using that contract's settlement-window volume and volatility.
- Timing, per product window: t0 ∈ {W_start − 20, W_start − 10} min; entry at t0+1 (stress: worst of t0+1 … t0+5); exit at the W_end bar close; stop at 1.0 × |I|; early profit if the move reaches |I| before W_start. These rules are shared with the ledger doc.

### Stage R2 — Post-rebalance reversal (multi-day)

- After the day-5 settlement, take the **opposite** direction to each commodity's total rebalance flow.
- Pre-registered holds: 1, 3 and 5 trading days, exiting at settlement.

### Stage R3 — Pre-positioning (multi-week)

- **Measurement:** for each commodity, the residual return (commodity minus the BCOM-subset average) over three fixed periods: announcement → 1 Dec, 1 Dec → 31 Dec, 1 Jan → the day before execution day 1. Correlate across commodities with the forecast flow.
- **Trading version:** enter at the settlement on the first business day of December, in the forecast flow direction; exit at the settlement on the day before execution day 1.
- R3 results also tell R1 how much flow is already priced in.

---

## 7. Position constructions (both pre-registered)

### Construction A — Outright per commodity
Each commodity is traded independently when `|I_i| ≥ 3 × RT_cost_i` **and** the flow forecast's SNR ≥ 1.5. Size: 1 contract (micro where one exists) for hypothesis tests.

### Construction B — Market-neutral basket
- Each execution day (R1), or each stage entry (R2/R3): rank traded commodities by predicted flow as a fraction of window volume.
- **Long the top k = 3 predicted buys, short the top k = 3 predicted sells.** Weight legs by inverse volatility so the long and short books have equal risk.
- **R1 timing:** all legs enter at a common time before the day's earliest settlement window among the chosen legs. Each leg exits at the end of **its own** window.
- Report the basket's daily beta to the BCOM-subset return as a neutrality diagnostic.

---

## 8. Tests

All tests run in the signal frame (path-invariant) and the book frame (path-variant). Inference uses a **wild cluster bootstrap by year**, since there are few annual events, plus day-level clustering where observations are within day.

### Gate R0 — Drift reconstruction
- Reconstructed weights at each determination date equal the prior year's targets (by construction). **Test:** reconstructed sub-index returns match any published sub-index or component returns within 5 bp per month, where available.
- Where non-CME prices are missing, report the weight error bound. If the missing components exceed 10% of index weight in a year, that year is excluded from R1–R3.
- **Fail → STOP.**

### Gate C0 — Monthly-roll calibration
- κ_B (or the combined κ) > 0 with t ≥ 2 on flow.
- The roll-day price move in the predicted direction has a positive slope against predicted impact.
- **Fail:** R1 is still run for descriptive statistics, but no R1 trading hypothesis can pass (decision R-D5).

### H-R1 — Execution-day effect (core)
Signed return from the entry to the W_end close, in the predicted direction, pooled across commodities, days and years.
- **Pass:** positive mean ≥ 1× cost, bootstrap p < 0.05 after **Holm across constructions A and B**.

### H-R2 — Reversal
Signed return in the reversal direction over 1/3/5 days.
- **Pass:** at least one hold length significant after Holm across 3 holds × 2 constructions.

### H-R3 — Pre-positioning
- **(a) Descriptive:** cross-commodity correlation of residual return with forecast flow in each period, by year.
- **(b) Trading:** the December entry → pre-execution exit return, in the forecast direction.
- **Pass (b):** positive mean after Holm across constructions.

### Dose-response (all stages)
Larger predicted flow relative to window volume should give larger signed returns. Spearman ρ > 0 reported per stage.

### Placebos
- **Date placebo:** the same computations on January business days 12–16 (no rebalance). Must show no effect.
- **Label shuffle:** forecast flows randomly reassigned across commodities within each year, 1,000 permutations. The observed statistic must exceed the 95th percentile.
- **Headline-only comparison (diagnostic):** the same tests using only the announced target change (ignoring drift). If headline-only performs as well as the drift-based forecast, the drift insight adds nothing, and that's recorded.

### H-R4 — Depth-based impact (gates 5A.4)
Out of sample on monthly roll days (C0 sample) and January execution days, compare the MAE of |I| vs |I_D| against the realised |move| to W_end.
- **Pass:** ≥ 10% lower MAE for I_D **and** no reduction in the H-R1 statistic when substituted.

### Robustness (report only)
Stress fill; 2× cost; excluding the most illiquid contract group; with and without GSCI stacking; k = 2 and 4 for construction B.

---

## 8B. Power analysis and alternative validation (v1.2)

**Formulas (planning, pre-registered):**
```
Flow / correlation tests:   SE ≈ 1 / sqrt(n_eff)
Price tests:                SE = σ_trade / sqrt(n_eff)
Minimum detectable effect:  MDE_t2 ≈ 2 × SE   (significance at t = 2)
                            MDE_80 ≈ 2.8 × SE (80% power at t = 2)
Clustering (design effect): n_eff = n / (1 + (m − 1) × ρ)
                            m = observations per cluster; ρ = within-cluster correlation (estimated from the data)
```

### 8B.1 Planning table

| Test | Observations | Clusters | Planned SE | Class |
|---|---|---|---|---|
| C0 monthly-roll calibration | ~9,000 (120 periods × ~15 contracts × 5 days) | 120 roll periods | ~0.03–0.05 | Individually testable |
| H-R1 execution-day price effect | ~750 (10 years × ~15 × 5) | **10 years** | Between 0.037 (no clustering) and 0.32 (full clustering) | Marginal: depends on within-year correlation |
| H-R2 reversal | ~150 per hold (10 × 15) | 10 years | Similar or wider than H-R1 | Marginal |
| H-R3 pre-positioning | ~150 per period | 10 years | Similar or wider than H-R1 | Marginal |
| CIT κ fit (ags, weekly) | ~520 weeks × 8 contracts | Weeks | ~0.02–0.04 | Individually testable |

Before Stage R1 runs, estimate the within-year correlation ρ from the data, compute n_eff, and record SE and MDE in `results/index_reweight/POWER.md`, with a plausible-effect statement. The same underpowered rule as the ledger (9A.2) applies.

### 8B.2 Alternative validation for the annual price effects (H-R1, H-R2, H-R3)

Because there are only about 10 independent years, pooled significance alone is not trusted. Two additional pre-registered checks are required:

1. **Yearly sign test.** For each year, compute the cross-sectional Spearman correlation between predicted flow (as a share of window volume) and the signed return across traded commodities. Count the years with a positive correlation.
   - **Pass:** one-sided binomial p < 0.05. That's **≥ 9 of 10** years, or **≥ 9 of 11** once January 2027 is included.
   - Each year is one independent vote, which is honest about the real sample size.
2. **Calibration check.** Using the impact model calibrated on monthly rolls (C0), the pooled ratio of realised to predicted execution-day move should have a 90% CI overlapping [0.5, 2].
   - This tests whether the annual effect is **consistent with the well-measured monthly mechanism**, rather than whether it's significantly non-zero on its own.

**Adoption rule for H-R1/H-R2/H-R3 trading:** pooled test pass **and** yearly sign-test pass **and** calibration pass. If the pooled test passes but the sign test doesn't, the result is recorded as "driven by a few years" and not traded.

## 9. Multiplicity accounting

- Holm within each stage, as specified in Section 8.
- Every configuration is logged in `trials.csv`: `trial_id, timestamp, stage, construction, year_set, t0_offset, hold, fill_model, cost_mult, gsci_stack, k, n_obs, mean_gross, mean_net, p_boot, notes`.
- Any final Sharpe is reported with a Deflated Sharpe Ratio using the total trial count.

---

## 10. Validation scheme

- **Annual-event parameters** (anything fitted using January data): leave-one-year-out. Fit on all other years, test on the held-out year, and repeat for every year.
- **Monthly-roll calibration** (κ values): walk-forward, 252 training days, 63 test days.
- Report per-year results. With about 10 events, a single extreme year can dominate, so the median-year result is reported alongside the pooled mean.

---

## 11. Three-track testing (aligned with the ledger doc, 13A)

- **Track 1, backtest:** 2016–2026 events, if Gates R0 and C0 pass.
- **Track 2, forward recording:** add all BCOM component settlements and the announcement page to the recorder **now**.
- **Forward event: January 2027.** The 2027 target weights are expected around late October 2026.
  - **Freeze** the model (code hash, κ values, rules) **before** the announcement in `results/index_reweight/FROZEN_2027.json`.
  - Record the forecast daily from the announcement to execution.
  - Evaluate R3, R1 and R2 on the 2027 event as a genuine out-of-sample event.
  - One event is **not** decisive. It's recorded and added to the pooled test in later years.
- **(v1.3) How the forward event enters the tests (8B):**
  - **Sign test:** January 2027 becomes the **11th yearly vote**. The pass threshold becomes ≥ 9 of 11 (one-sided p ≈ 0.033).
  - **Consistency test:** the 2027 cross-sectional correlation and calibration ratio must fall within the Track 1 90% intervals (computed from 2016–2026) and have the same sign. One event can't prove the effect, but it can contradict the backtest.
  - **Calibration:** the 2027 realised/predicted move ratio is added to the calibration sample.
- **(v1.3) Track 3 role:** with about 5 execution days × ~15 contracts a year, live-small January trading can't reach a meaningful trade count quickly. It serves as a **fill, latency and cost check** plus the consistency test above, never as independent proof.
- **(v1.3) Monthly-roll calibration (C0) forward:** roughly 12 roll periods a year accumulate in the recorder. C0 is re-estimated forward once per 12 new roll periods, using the same frozen rules.
- **Track 3, live-small:** R1 trades during the January 2027 execution days, logging implementation shortfall per the ledger doc.

---

## 12. Build plan and gates

| Phase | Work | Gate |
|---|---|---|
| 0 | Add the BCOM components and announcement page to the recorder | Recorder running |
| 1 | Source methodology facts, annual weights and AUM (2016–2027), non-CME prices, settlement windows | Facts complete |
| 2 | Sub-index reconstruction, drift tracker, flow formulas, unit tests | **Gate R0** |
| 3 | Monthly-roll calibration (C0) | **Gate C0** |
| 3b | CIT and swap-dealer auxiliary fits (5A.2, 5A.3); error budget (5A.1) | Consistency flags reported |
| 2b | Power analysis (8B.1), plausible-effect statements | `POWER.md` written before Stage R1 runs |
| 4 | Freeze for January 2027 (before the late-October announcement) | Frozen file stored |
| 5 | Stage R1: constructions A and B, placebos | H-R1 decision |
| 6 | Stage R2 | H-R2 decision |
| 7 | Stage R3 | H-R3 decision |
| 8 | Robustness, DSR, report | Final report |
| 9 | January 2027 forward event (Tracks 2 and 3) | Forward event report |

---

## 13. Required unit tests

1. Drifted weights sum to 1 at every date.
2. If all components' sub-indices move by the same factor, the drifted weights stay equal to the prior targets.
3. A component that doubles relative to the rest gets a higher drifted weight, and its ΔN is negative when its target is unchanged.
4. **Drift beats headline:** a synthetic case where the target falls but the drifted weight fell further gives **positive** ΔN (trackers buy).
5. Contract conversion: AUM $100bn, weight gap +0.5%, price 50, multiplier 1,000 gives +10,000 contracts.
6. Daily split: ΔN_i,d sums to ΔN_i across execution days per the verified fractions.
7. Full-index net dollar flow ≈ 0 (within tolerance) on a synthetic 25-component index.
8. No prices after the determination date are used in ΔN computed for that date.
9. Leave-one-year-out guard: a model evaluated on year y was not fitted using year y data.
10. Construction B: the inverse-volatility-weighted long and short books have equal risk within 1%.
11. Construction B timing: each leg exits at its own product's W_end; the common entry precedes the earliest chosen window.
12. Settlement windows are taken from the sourced table only; an unmapped product raises an error.
13. Excluded-year rule: a year with more than 10% index weight in missing-price components is excluded.
14. CIT and COT records are usable only at or after their Friday release timestamp.
15. κ_CIT fit uses only weeks before the evaluation period (walk-forward), and is restricted to covered ag contracts.
16. The consistency flag triggers when |κ_flow − κ_CIT| > 2 combined SE.
17. The swap-dealer proxy is never used as a prior unless the R-D12 agreement condition is met.
18. I_D equals I when D(t0) = D̄; depth is measured within ±5 ticks at the t0 bar close.
19. Error budget: removing a zero-contribution component leaves OOS error unchanged on synthetic data.
20. Stage reordering requires a matching decision-log entry.
21. Design effect with 10 year clusters computed from the observed within-year correlation.
22. Yearly sign test: 9 of 10 positive gives one-sided binomial p ≈ 0.011 (pass); 8 of 10 gives p ≈ 0.055 (fail).
23. Yearly Spearman uses only traded commodities with valid data for that year.
24. Calibration ratio CI computed by bootstrap over years; pass requires overlap with [0.5, 2].
25. Adoption logic requires all three checks (pooled, sign test, calibration).
26. With 11 years, 9 positive votes pass (p ≈ 0.033) and 8 fail (p ≈ 0.113).
27. The 2027 consistency test uses Track 1 intervals computed only from 2016–2026.
28. Track 3 January trades are never counted as independent efficacy evidence.

---

## 14. Kill conditions

| Condition | Verdict |
|---|---|
| Gate R0 fails | Stop. Drift can't be trusted. |
| Gate C0 fails | R1 descriptive only; no trading hypothesis can pass. |
| H-R1, H-R2 and H-R3(b) all fail | Kill. Write up (including whether drift added anything over headline-only). |
| Date placebo or label shuffle significant | Kill the stage concerned. The effect isn't rebalance-specific. |
| Headline-only equals drift-based | Keep the result, but record that the drift insight has no incremental value. |
| Net fails at 1× cost | "Real, not tradable". |

Every stop writes `results/index_reweight/REPORT.md`.

---

## 15. Decision log

| ID | Decision | Rationale |
|---|---|---|
| R-D1 | Flow from target minus **drifted** weight | The headline change ignores a year of price drift, which can reverse the sign |
| R-D2 | Calibrate impact on monthly rolls | Far more events than the annual rebalance, with the same execution mechanics |
| R-D3 | Leave-one-year-out validation for annual parameters | About 10 events; random splits would leak within-year information |
| R-D4 | Combined κ if BCOM and GSCI can't be separated | Their roll days overlap |
| R-D5 | No R1 trading pass without C0 | Without a calibrated flow-to-window link, R1 results can't be attributed to rebalancing |
| R-D6 | Both constructions pre-registered with Holm | Owner's choice; controls the extra test |
| R-D7 | Non-CME components used for drift only | Needed for correct weights; not tradable on the prop route |
| R-D8 | Freeze before the 2027 announcement | Makes the next event genuinely out of sample |
| R-D9 | When this model is active in January, the ledger's P8b excludes BCOM/GSCI flows | Prevents double counting on shared contracts |
| R-D10 | CIT used as a prior for ag κ, not a replacement | It measures total index exposure, not window flow |
| R-D11 | Error budget may reorder remaining stages, never add new ones | Focus without new hidden tests |
| R-D12 | Swap-dealer proxy used as a prior only if it agrees with CIT on the overlap | It mixes many client types; needs independent validation first |
| R-D13 | Depth-based impact has no fitted parameters | Prevents tuning the price model on few events |
| R-D14 | v1.1 changes additive | Preserves the v1.0 pre-registration intact |
| R-D15 | Yearly sign test required for annual price effects | Ten independent years is the true sample size; pooling can hide one-year flukes |
| R-D16 | Calibration against monthly rolls required | The monthly mechanism is well measured; the annual effect should be consistent with it |
| R-D17 | Power computed with an estimated within-year correlation | The design effect can shrink 750 observations to near 10 |
| R-D18 | v1.2 changes additive | Preserves the v1.1 pre-registration intact |
| R-D19 | Forward events enter as additional sign-test votes | Each year is the true unit of independent evidence |
| R-D20 | Forward consistency test for the 2027 event | One event can contradict a backtest even though it can't confirm one |
| R-D21 | Track 3 in this model is a fill/cost check only; v1.3 changes additive | Too few January trades per year for efficacy testing |

---

## 16. Open questions (owner to resolve)

- **R-Q1:** BCOM methodology: execution days and daily fractions, designated contract schedule, CIM determination date, holiday rules, and the final list of CME components.
- **R-Q2:** Target weights and tracking-AUM estimates for every year 2016–2026 (annual press releases).
- **R-Q3:** Sources for non-CME component settlement prices (ICE, LME) for the drift calculation.
- **R-Q4:** S&P GSCI methodology, annual weights, roll days, and any AUM estimates.
- **R-Q5:** Settlement window times per product, with effective dates (shared with the ledger doc).
- **R-Q6:** Which of the ~15 contracts the prop firm offers, and whether it allows overnight holds (required for R2 and R3).
- **R-Q7:** CostStack values per product, including those without micros.
- **R-Q8:** Micro contract availability and liquidity per product.
- **R-Q9:** Confirm the current list of markets covered by the CFTC's commodity index trader supplement and its history.
- **R-Q10:** Pre-register which CFTC report variant is used (futures-only vs futures-and-options combined) before any fit.
- **R-Q11:** Databento MBO history and cost for the ~15 traded contracts around their settlement windows.

---

## 17. Future versions

- Replace the ledger's P8b flag with this doc's monthly-roll flow model for all shared contracts.
- Add other commodity indices if their weights and AUM can be sourced.
- Combine R1 with the settlement ledger on January execution days in NG and CL.
