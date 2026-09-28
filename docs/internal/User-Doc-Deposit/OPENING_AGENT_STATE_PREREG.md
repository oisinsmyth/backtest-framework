# Opening Agent-State Model — Pre-Registration & Design Document

**Status:** PRE-REGISTERED — v1.0 (2026-09-21)  
**Current version:** v1.1 (2026-09-21), additive amendment: adds programme-level false-positive controls (Section 12A), phase 0b, kill conditions, unit tests 18–25, decisions O-D10–O-D16 and question O-Q6. All v1.0 text is retained unchanged.
**Owner:** Oisin
**Consumer:** Claude Code
**Suggested repo path:** `docs/research/OPENING_AGENT_STATE_PREREG.md`
**Parent design:** `SETTLEMENT_FLOW_LEDGER_PREREG.md` (the "last similar idea"). This doc applies the same **cross-sectional agent** approach (independent agent types acting on public information, aggregated, updated with observed flow) to the **equity index cash open**, and adds a **market-state and progression** layer.
**Related docs:** `SHOCK_CLASSIFIER_PREREG.md` (shared liquidity-shock features and economic calendar), `ARCHITECTURE_OVERVIEW.md`.

---

## 0. Instructions for Claude Code (read first)

1. **Build in the order of Section 13.** Gate O0 must pass first. Stages S-A → S-I are added one at a time under the retention rule (Section 8).
2. **This document is the spec.** Do not change definitions, label rules, grids, thresholds or kill conditions. If something is ambiguous or impossible, **stop and ask**. Changes are **additive**, versioned amendments made before code changes (same practice as the ledger, D34/D46).
3. **Never fabricate data or facts,** including release dates, options open interest and fair-value inputs. Record sources in `data/opening/SOURCES.md`.
4. **Log every configuration** to `results/opening/trials.csv`.
5. **Reuse shared components** from the ledger: fill model (ledger 7.3), impact model (ledger 5.3), CostStack, recorder (ledger 13A.3), error budget (ledger 8A.1), power rules (ledger 9A/9B) and three-track protocol (ledger 13A). Flag any change to shared code.
6. **No look-ahead.** Pre-open agent pressures use data up to 09:29 ET; t0 features use data up to the t0 bar close; day-type **labels** use the full session and are **training targets only**, never features.
7. **Parameter ceiling:** the classifier is capped at the budget in Section 7.3. Exceeding it requires a doc amendment.
8. Every new function gets unit tests (Section 15).

---

## 1. Hypothesis in one paragraph

At the equity index cash open, several independent agent types act on public information they observed overnight: stop holders at prior extremes, trend followers whose signals changed at the prior close, volatility-targeting funds reacting to realised volatility, macro traders reacting to 08:30 releases, index-arbitrage desks closing the futures-vs-stock gap, options dealers re-hedging, and institutional execution algorithms beginning their orders. Their **combined, partly predictable pressure** determines what kind of day unfolds. A small classifier using pre-open agent pressures plus observed opening behaviour can estimate the **day-type state** by 09:45–10:00 ET better than the base rate, track its **progression** through the morning, and support a **state-conditioned trading policy** (gain scheduling: continue, reverse, fade or stand aside) that beats unconditioned opening strategies out of sample, net of cost.

---

## 2. Scope

**In scope (v1)**
- Instruments: ES and NQ (execution in MES and MNQ).
- Session: US cash open, 09:30 ET, through 11:30 ET for trading; labels use 09:30–16:00 ET.
- Agents A1–A7 (Section 4); A8 (gap traders) as noise only; A9 (liquidity providers) through the impact model.

**Candidate extension (pre-registered, not built until v1 verdict):** CL around 09:00 ET with its own agent set (O-Q1).

**Out of scope (v1):** overnight Globex trading; grains; single stocks; any agent requiring non-public or unavailable data.

---

## 3. Data specification

| Data | Source | Use |
|---|---|---|
| ES, NQ 1-min bars, full Globex session, 2016 → present | Databento | Gap, overnight range/volume, prior extremes, first-window features, labels |
| ES, NQ trades with aggressor side | Databento | Signed flow, large-lot flow |
| SPY 1-min bars (and QQQ for NQ) | Databento equities | Index-arbitrage basis proxy (A6) |
| CME options on ES/NQ: daily open interest by strike, daily settlement prices | Databento / CME | Options-dealer gamma estimate (A4), partial |
| Economic calendar (08:30 ET releases), sourced | Shared with shock classifier doc 3.4 | Macro-reactor term (A5) |
| Session calendar: early closes, holidays, DST | Shared | Exclusions |

- **Exclude** early-close sessions and days with missing opening data (logged).
- **Flag** (not excluded): FOMC days, CPI and payrolls days, quad witching, month-end, index rebalance days.
- The three-track testing rules of the ledger (13A) apply. Items without usable history go to the recorder (Section 12).

---

## 4. Agents (the cross-sectional model)

Each agent produces a **pre-open pressure** `P_i` (signed; + = buying), computed from public information available by 09:29 ET, then **standardised**: `z_i = P_i / σ(P_i over the prior 250 sessions)`. Standardising avoids estimating unknown dollar sizes (decision O-D2).

| ID | Agent | Public information | Pressure definition (pre-registered) | Knowability |
|---|---|---|---|---|
| A1 | Stop holders | Prior RTH high/low/close; overnight high/low | Computed **at the open**: `P1 = +1 × (open − prior_high)/ATR20` if open > prior high; `−1 × (prior_low − open)/ATR20` if open < prior low; 0 otherwise | Levels computable; size latent |
| A2 | Trend followers (CTAs) | Closes up to t−1 | Target position = mean over L ∈ {20, 60, 120} of sign(close[t−1] / close[t−1−L] − 1), scaled by 1/σ20. `P2` = target[t] − target[t−1] | Computable (direction and relative size) |
| A3 | Volatility-targeting funds | Realised volatility | Exposure E = 0.10 / σ20 (annualised, capped at 2). `P3` = E[t] − E[t−1] (these funds are net long, so falling exposure means selling) | Computable (direction and relative size) |
| A4 | Options dealers | ES/NQ options OI by strike (t−1), implied vols (t−1), overnight move | Dealer gamma G computed under a pre-registered positioning assumption (customers net long puts and net short calls; dealers take the other side). `P4 = −G × (open − prior_close)` | Partial (CME options only) |
| A5 | Macro reactors | 08:30 ET releases (calendar) | On release days: `P5 = r(08:29 → 09:25) / σ_{08:29–09:25}`; 0 otherwise | Observable reaction; consensus not used |
| A6 | Index-arbitrage desks | Futures vs stock basket | Fair ratio ρ_t = rolling 20-day median of ES/SPY at 15:59 (prior days only). At the first SPY print after 09:30: `d = (ES / ρ_t − SPY) / ATR20_SPY`. `P6 = −d` (desks sell futures that are rich to the basket) | Estimable (see O-D5) |
| A7 | Institutional execution algorithms | Mostly private; partly calendar-driven | **Measurement, not a pre-open pressure:** large-lot signed flow from 09:30 to t0 (threshold = 90th percentile trade size, prior 20 days) | Inferred proxy |
| A8 | Discretionary gap traders | Gap, headlines | Not modelled (noise) | Latent |
| A9 | Liquidity providers | — | Enters via the impact model only | — |

**Note on A6:** the fair ratio uses prior-day closes only. The first SPY print after 09:30 means A6 is computed at 09:31 at the earliest, which is before every t0 in Section 6.

**Agent alignment summary (used in Stage S-I):**
```
Signs are expressed relative to the day's direction d0 (Section 5.2):
z̃_i = z_i × d0
N   = mean of z̃_i over active agents      (net alignment with the opening direction)
D   = standard deviation of z̃_i           (disagreement between agents)
```

---

## 5. States and labels

### 5.1 Why direction-relative states
Labelling up and down days separately doubles the classes and halves the data per class. All states are defined **relative to the day's opening direction d0**, which keeps the parameter count inside the budget (O-D3).

### 5.2 Opening direction
`d0 = sign(price at t0 − RTH open)`. If zero, the day is unclassified and not traded.

### 5.3 Day-type labels (training targets; full RTH session 09:30–16:00)

Definitions, with `IB` = initial balance (09:30–10:30 range), `R` = day range, `gap` = open − prior close:

| Label | Rule (pre-registered, applied in this order) |
|---|---|
| **CONT** (trend with d0) | `sign(close − open) = d0` **and** `|close − open| ≥ 0.6 × R` **and** `R ≥ 1.8 × IB` |
| **REV** (trend against d0, includes stop-run reversals) | `sign(close − open) = −d0` **and** `|close − open| ≥ 0.6 × R` **and** `R ≥ 1.8 × IB` |
| **FADE** (gap filled) | `|gap| ≥ 0.25 × ATR20` **and** price trades through ≥ 75% of the gap towards the prior close by 16:00 **and** not CONT/REV |
| **RANGE** | Everything else |

Report label frequencies per market and year before any modelling. If any class is below 8% of days, the label thresholds are **not** tuned. Instead, that class is merged into RANGE by pre-registered rule (O-D4).

---

## 6. Timing and policy (gain scheduling)

### 6.1 Checkpoints
Classification at t ∈ {09:45, 10:00, 10:30, 11:00}. **Trading t0 ∈ {09:45, 10:00}** (both pre-registered, Holm-corrected).

### 6.2 Policy at t0

```
p = classifier probabilities at t0 for {CONT, REV, FADE, RANGE}
if max(p) < θ or argmax = RANGE:  no trade
if argmax = CONT:  trade d0
if argmax = REV:   trade −d0
if argmax = FADE:  trade towards the prior close (−sign(gap))
```

θ = 0.45 primary; 0.40 and 0.50 sensitivity only.

### 6.3 Execution and exits (shared with the ledger's timing template)
- Entry at the t0+1 bar close plus 1 tick (stress: worst close t0+1 … t0+5).
- **Stop:** 0.5 × the 09:30–t0 range from entry.
- **State-flip exit:** at the next checkpoint, if the probability of the traded state falls below 0.30.
- **Time stop:** 60 minutes after entry.
- Intra-bar ambiguity resolves to the stop (pessimistic).
- One trade per market per day. Size: 1 micro for hypothesis tests.

### 6.4 Unconditioned baselines (for the decision-value test)
- **B1 opening momentum:** always trade d0 at t0, same exits.
- **B2 opening reversal:** always trade −d0 at t0, same exits.
- **B3 opening-range breakout:** trade the first break of the 09:30–t0 range after t0, same stop and time stop.

---

## 7. Classifier

### 7.1 Model
Multinomial logistic regression with L2 penalty (penalty strength chosen by inner cross-validation within each training window only). Coefficients **shared across ES and NQ**, with a market-specific intercept.

### 7.2 Features by stage (Section 8)
Observables (all stages): `gap/ATR20`, open location (above prior high / inside / below prior low, as two indicators), `r(09:30 → t0)/σ`, `volume(09:30 → t0)` z-score. Agent and measurement features are added by stage.

All features enter **direction-relative** (multiplied by d0 where signed).

### 7.3 Parameter budget
- Pooled ES+NQ sessions ≈ 5,000; but same-day ES and NQ are highly correlated, so the effective count is lower (Section 10).
- Rarest retained class ≈ 10–15% of days.
- **Ceiling: 3 non-base classes × (features + 1) ≤ 36**, so at most **11 features** in any stage. The alignment summary (S-I) exists partly to stay well under this.

---

## 8. Staged build and retention rule

| Stage | Adds | Features after stage |
|---|---|---|
| S-A | Observables only | 5 |
| S-B | A7 large-lot flow (09:30 → t0) | 6 |
| S-C | A1 stop pressure | 7 |
| S-D | A2 trend-follower pressure | 8 |
| S-E | A3 vol-target pressure | 9 |
| S-F | A5 macro reaction | 10 |
| S-G | A6 index-arb basis | 11 |
| S-H | A4 options-dealer gamma (only if Gate O0-H passes) | Must replace one feature or use S-I to stay ≤ 11 |
| S-I | Replace individual agent pressures with alignment summary (N, D) | Observables + A7 + N + D = 8 |

**Retention rule (pre-registered; adapted from the ledger's Section 6):** stage k is kept only if, versus the last retained stage, out of sample it
1. reduces multiclass **log loss** by ≥ 2% relative, **and**
2. does not reduce the decision-value test statistic (H-O2).

**S-I comparison:** S-I is kept if it matches the best individual-agent stage within 1% log loss (simpler wins) or beats it.

---

## 9. Tests

Two frames, as in all docs: **signal frame** (classification, event-study curves) and **book frame** (policy, costs, fills). Inference clusters by **day** (ES and NQ share days).

### Gate O0 — Data
Bars coverage ≥ 99% of expected minutes 08:00–16:00 ET; calendar sourced; SPY alignment verified; label frequencies reported. **Gate O0-H** (for S-H only): options OI and settlement prices available for ≥ 90% of sample days.

### H-O1 — Classification lift
At t0 = 10:00, out of sample:
- Log loss below the base-rate (class-frequency) log loss.
- Accuracy above the base rate, **permutation test** (1,000 label shuffles within year) p < 0.05.
- Calibration: reliability curve and Brier score reported. Large miscalibration (predicted 0.6 vs realised < 0.45 in the top bin) is flagged.

### H-O2 — Decision value (core)
The state-conditioned policy's net return per day (0 on no-trade days) minus the **best** of B1–B3 per day, paired by day, HAC standard errors.
- **Pass:** positive difference with t ≥ 2 after **Holm across t0 ∈ {09:45, 10:00}**, **and** the policy's own net mean > 0.

### H-O3 — Progression (diagnostic)
Accuracy and log loss at each checkpoint 09:45 → 11:00. Expected to improve monotonically. Report the confusion matrices and how often the argmax state changes between checkpoints.

### H-O4 — Timing (your execution constraint)
Event-study curves from t0 by predicted state: at most 50% of the 60-minute move realised by t0+5; delay cost reported.

### H-O5 — Placebos
- **Label shuffle** (in H-O1).
- **Agent shuffle:** pre-open agent pressures randomly reassigned across days within year. The retained agent stages must lose their improvement.
- **Midday placebo:** the same features computed for 12:00–12:30 against afternoon-only labels. Reported; not expected to carry the opening effect.

### H-O6 — Agent signatures (validation, marginal)
Each computable agent's pressure should predict its **own signature** in the first 60 minutes, e.g. A2 (CTA) pressure predicts the sign of signed flow; A1 predicts early continuation then reversal. Run as marginal contributions with variance inflation factors (ledger 9A.2 rule 4).

### Robustness (report only)
θ sensitivity; stress fill; 2× cost; with and without flagged days; ES and NQ separately; by year.

---

## 10. Power analysis (per ledger 9A)

```
SE ≈ 1/√n_eff (classification and flow); SE = σ/√n_eff (returns); MDE_t2 ≈ 2 × SE
n_eff for pooled ES+NQ: n / (1 + ρ_same_day), with ρ_same_day estimated (expected high, ~0.7–0.9)
```

| Test | Planned n_eff | Planned SE | MDE (t = 2) | Class |
|---|---|---|---|---|
| H-O1 classification (days) | ~2,700–2,900 | ~0.019 | ~0.04 | Individually testable |
| H-O2 decision value (all days, paired) | ~2,700–2,900 | ~0.019σ | ~0.04σ | Individually testable |
| Policy trades only (confident days, ~35%) | ~950–1,000 | ~0.032σ | ~0.065σ | Individually testable |
| H-O6 per agent | ~2,700 | ~0.019 | ~0.04 | Testable; A4 partial |
| A1 stop size, A8 gap traders | — | — | — | Latent → 9B methods (decision relevance) |

Before each stage, record real n_eff, SE, MDE and a plausible-effect statement in `results/opening/POWER.md` (ledger 9A.2). Underpowered stages follow ledger 9B.

---

## 11. Multiplicity, validation and walk-forward

- Holm within tests as specified. Every configuration logged; final Sharpe reported with a Deflated Sharpe Ratio using the total trial count.
- **Walk-forward:** train 252 days, test 63, rolling; the classifier (and its penalty) refit only on each training window.
- **Robustness validation:** leave-one-year-out, reported alongside.

---

## 12. Three-track testing (per ledger 13A)

- **Track 1 (backtest):** primary. All stages except possibly S-H have full history.
- **Track 2 (recorder):** add daily ES/NQ options OI and settlements (if history is incomplete), the economic calendar, and SPY/QQQ opening prints.
- **Track 3 (live-small MES/MNQ):** fills, latency and cost checks; power-checked route per ledger 13A.7(4). At ~35% confident days across two correlated markets, expect roughly 150–180 trades a year, so N = 300 takes about 1.5–2 years. The consistency route is likely unless the Track 1 edge exceeds ~0.115σ per trade.
- **Automation requirement:** 09:30 ET is 14:30 UK time, during the owner's working day, so Track 3 needs fully automated execution (O-Q3).

---

## 12A. Programme-level false-positive controls (v1.1)

### Controls (12A, v1.1)

These controls sit **on top of** every within-doc rule. They exist because each doc corrects only for its own tests, while the research programme as a whole runs many test families on shared data.

**1. Sealed holdout (the "vault")**
- **Vault period:** 2025-03-01 to 2026-09-18 inclusive (about 18 months), sealed on 2026-09-21, **before any testing in this doc has run**.
- **In-sample period** for everything else (fitting, stage selection, thresholds, label frequencies, power estimates, walk-forward, placebos, robustness): 2016-01-01 to 2025-02-28.
- **One look only.** The vault is opened once per model, after the model has passed every in-sample gate and been frozen (code hash, parameters, retained stages, rules) in `results/opening/FROZEN_VAULT.json`. The opening is logged with a timestamp. A second opening is refused.
- **Vault pass criteria (pre-registered):** the primary statistic (the H-O2 paired decision-value difference) has the **same sign** as in-sample, one-sided **p < 0.10**, **and** net mean > 0 at 1× cost. The vault is a confirmation test, so it's deliberately less strict than the in-sample test, but it can't be skipped.
- **A vault failure means the model is not promoted.** It's written up; it is not re-tuned and retested on the vault.
- **Power impact:** the in-sample period shrinks to about 86% of the full history. For example, H-O2's n_eff falls from about 2,700–2,900 to about 2,300–2,500 days, raising the SE by roughly 8% (about 0.020–0.021σ). The same controls are defined identically in the settlement ledger (13A.8), so both docs share one vault, one registry and one programme trial count.
- **Honesty about prior exposure:** the owner records any earlier analysis that touched the vault period in these markets (open question below). The vault is clean for *these hypotheses*, not a virgin dataset.

**2. Cross-document correction (programme registry)**
- Every primary decision family across the programme is registered in `results/PROGRAMME_REGISTRY.md` with its registration date.
- **α allocation:** programme-wide α = 0.05, split into **10 equal slots of 0.005**. Current families: LETF close flow H1; shock classifier H1; ledger H2; index H-R1, H-R2, H-R3(b); opening H-O2. That uses 7 slots; 3 are reserved for future models.
- **Promotion requires** the family's within-doc adjusted p-value ≤ **0.005** (roughly t ≥ 2.8), in addition to every within-doc criterion.
- A new model can only be registered into a free slot. When all slots are used, a new model requires a doc amendment that re-allocates α (never retroactively for families already evaluated).

**3. Programme-level Deflated Sharpe Ratio**
- A programme trial counter sums the rows of every doc's `trials.csv`.
- Any reported Sharpe carries two DSR values: one with the doc's own trial count and one with the **programme** trial count.
- **Promotion requires** the programme-level DSR probability ≥ 0.95.

**4. Standard haircut (winner's curse)**
- All sizing, drawdown planning and the Track 3 power check use **50% of the in-sample walk-forward edge estimate**.
- If the vault estimate is lower than the haircut estimate, the **vault estimate** is used instead.

**5. Shared-period and episode checks**
- **Episode concentration:** the edge must stay positive after removing the **best calendar year** and, separately, the **best 1% of days**.
- **Shared-period dependence:** for any two models that both survive, report the correlation of their daily P&L and the overlap of their top-10 P&L days. If the correlation is > 0.5 **and** more than 40% of each model's P&L comes from the same months, flag "shared-period risk". Those models are then sized as one combined position for risk purposes.

**6. Look-ahead defences**
- **One-bar-delay robustness:** rerun with every signal delayed by one extra bar. The strategy must keep ≥ 50% of its edge. Edges that vanish with a one-minute delay are either too fast for your execution or leaking future data.
- **Leak canary:** the test harness includes a deliberately leaky feature (using a future bar). The pipeline's static checks must reject it. If it isn't caught, all results are invalid until the check is fixed.

**7. The forward consistency route needs the vault**
The forward consistency test (ledger 13A.7(3)) is lenient: a null effect can land inside a wide interval. So promotion via the consistency route **also requires a vault pass**. It can't stand alone.

---

## 13. Build plan and gates

| Phase | Work | Gate |
|---|---|---|
| 0 | Recorder additions (Section 12) | Running |
| 0b | Confirm the shared vault guard (12A) covers ES/NQ/SPY/QQQ and options data; register H-O2 in `PROGRAMME_REGISTRY.md` | Loader guard tested for these datasets |
| 1 | Data, calendar, label computation, label frequency report | **Gate O0** |
| 2 | Agent pressures A1–A7, unit tests, power analysis (`POWER.md`) | Tests pass; power recorded |
| 3 | Stage S-A: H-O1, H-O3 | S-A baseline recorded |
| 4 | Stages S-B → S-G (then S-H if Gate O0-H), S-I comparison; error budget after each (ledger 8A.1) | Retained-stage table |
| 5 | H-O2 decision value, H-O4 timing, H-O5 placebos, H-O6 signatures | **Gate O1:** H-O1 and H-O2 pass |
| 6 | Book frame, robustness, Monte Carlo | Net positive at 1× cost |
| 7 | Walk-forward, leave-one-year-out, DSR | Final report |
| 8 | Track 3 per ledger 13A.7 | Promotion decision |

---

## 14. Kill conditions

| Condition | Verdict |
|---|---|
| Gate O0 fails | Stop. |
| H-O1 fails at S-A **and** at every later stage | Kill. The open doesn't reveal the day type beyond the base rate. |
| H-O1 passes, H-O2 fails | "Classifiable but not tradable": the state is predictable but no better than simple baselines after costs. Write up. |
| Agent shuffle doesn't remove agent-stage gains | Agent terms aren't doing what they claim. Revert to S-A/S-B. |
| H-O4 fails | Kill at current latency. |
| OOS Sharpe < 0.5 × IS Sharpe | Do not trade. |
| Vault fails (12A) | Not promoted. Write up. No re-tuning against the vault |
| Programme-adjusted p > 0.005 or programme DSR < 0.95 | Not promoted, even if within-doc gates pass |
| Edge negative after removing the best year or best 1% of days | Treat as episode-driven. Not promoted |
| Edge falls below 50% with a one-bar delay | Too fast for your execution, or leaking. Investigate |
| Leak canary not caught | All results invalid until fixed |

---

## 15. Required unit tests

1. Labels: synthetic sessions reproduce each rule in order (CONT/REV before FADE before RANGE).
2. Labels never enter features (static check on the feature pipeline).
3. d0 = 0 gives an unclassified, untraded day.
4. A1: open above the prior high gives positive pressure scaled by ATR; inside the range gives 0.
5. A2: a known price path gives the hand-calculated target change across L ∈ {20, 60, 120}.
6. A3: exposure capped at 2; rising σ20 gives negative pressure.
7. A4: dealer gamma sign follows the pre-registered positioning assumption; zero overnight move gives zero pressure.
8. A5: zero on non-release days; uses only data to 09:25.
9. A6: fair ratio uses prior days' 15:59 values only; computed no earlier than the first SPY print after 09:30.
10. A7: large-lot threshold uses prior 20 days only.
11. Standardisation uses the prior 250 sessions only.
12. Direction-relative transformation: flipping all prices (a mirror-image day) leaves direction-relative features and labels unchanged.
13. Parameter budget: the pipeline refuses to fit a stage exceeding 11 features.
14. Policy: argmax RANGE or max(p) < θ produces no trade; FADE trades towards the prior close.
15. State-flip exit triggers when the traded state's probability falls below 0.30 at the next checkpoint.
16. Pooled n_eff uses the estimated same-day ES/NQ correlation.
17. DST: 09:30 ET maps correctly to UTC in both transition weeks.
18. Vault guard covers ES, NQ, SPY, QQQ and ES/NQ options data for 2025-03-01 → 2026-09-18.
19. Label frequency reports and power estimates use in-sample dates only (static check).
20. One-shot vault opening, logged; a second opening refused.
21. H-O2 promotion check uses programme α = 0.005 from the shared registry.
22. Programme DSR uses the programme-wide trial count.
23. Haircut applied to sizing and the Track 3 power check.
24. Episode checks (best year, best 1% of days) and one-bar-delay rerun computed correctly.
25. Leak canary: a feature using any bar after t0 is rejected.

---

## 16. Decision log

| ID | Decision | Rationale |
|---|---|---|
| O-D1 | Reuse the ledger's cross-sectional agent structure | Proven design pattern; shared code and rules |
| O-D2 | Standardised agent pressures instead of dollar sizes | Most agent sizes are unknown; z-scores avoid fitting hidden scales |
| O-D3 | Direction-relative states | Halves the classes; keeps parameters within budget |
| O-D4 | Rare classes merged by rule, thresholds never tuned | Prevents label engineering |
| O-D5 | Index-arb basis measured against the first SPY print, fair ratio from prior closes | Avoids needing dividends, rates and pre-market liquidity assumptions |
| O-D6 | Options-dealer term partial and last | Only CME options are available; the dominant index options market isn't |
| O-D7 | Classifier shared across ES/NQ with market intercepts | Doubles usable data; the markets share structure |
| O-D8 | Decision value judged against the best simple baseline | A classifier is only useful if it beats easy alternatives |
| O-D9 | Alignment summary tested against individual agents | Compact state summaries suit the sample size and the owner's state-model approach |
| O-D10 | Shared vault with the ledger (2025-03-01 → 2026-09-18) | One sealed period for the whole programme keeps the control simple and consistent |
| O-D11 | Vault test at one-sided p < 0.10, same sign, net positive | Confirmation, not a second full test |
| O-D12 | H-O2 registered as a programme family (α = 0.005) | Cross-document correction |
| O-D13 | Programme-level DSR ≥ 0.95 | Accounts for all trials across docs |
| O-D14 | 50% haircut on edge | Winner's curse |
| O-D15 | Episode, shared-period and one-bar-delay checks | Opening effects could be driven by a few volatile episodes or by leakage at bar boundaries |
| O-D16 | v1.1 changes additive | Preserves the v1.0 pre-registration intact |

---

## 17. Cross-references to the parent design

| This doc | Reuses from `SETTLEMENT_FLOW_LEDGER_PREREG.md` |
|---|---|
| Agents A1–A9 | Participant table structure (Section 4) and knowability classes |
| Retention rule | Section 6 (adapted from flow correlation to classification log loss) |
| Execution and exits | Section 7.3–7.4 timing template |
| Error budget | Section 8A.1 |
| Power and alternative validation | Sections 9A and 9B |
| Three tracks | Section 13A, including 13A.7 power checks |
| Additive amendments | Decisions D34 and D46 practice |

Links to other docs:
- **Shock classifier:** A1 stop-run behaviour and A7 flow reuse its liquidity-shock features. A shock inside 09:30–t0 is a candidate v2 feature.
- **Equity LETF close flow:** the prior day's predicted LETF close flow is a candidate v2 agent (it can leave positioning imbalances into the next open).

---

## 18. Open questions (owner to resolve)

- **O-Q1:** Build the CL extension (09:00 ET, its own agents: physical traders, prior-evening inventory report reaction) after the v1 verdict, or in parallel?
- **O-Q2:** Confirm Databento coverage and cost for CME ES/NQ options OI and settlements (S-H) and SPY/QQQ opening prints (A6).
- **O-Q3:** Execution automation for Track 3 (broker API, hosting), given the 14:30 UK open.
- **O-Q4:** Economic calendar source (shared with the shock classifier, Q in that doc).
- **O-Q5:** CostStack values for MES/MNQ at the open (spreads and slippage are wider in the first minutes).
- **O-Q6:** Record any earlier analysis that touched 2025-03-01 → 2026-09-18 ES/NQ data (the owner's earlier idea tests included equity index futures), so the vault's cleanliness is documented honestly.
