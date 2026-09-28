# Information vs Liquidity Shock Classifier — Pre-Registration & Design Document

**Status:** PRE-REGISTERED — v1.0 (2026-09-21)  
**Current version:** v1.1 (2026-09-21), additive amendment: adds the power analysis (Section 7A). All v1.0 text is retained unchanged.  
**Current version:** v1.2 (2026-09-21), additive amendment: adds three-track testing with power checks (Section 7B). All v1.1 text is retained unchanged.
**Owner:** Oisin
**Consumer:** Claude Code
**Suggested repo path:** `docs/research/SHOCK_CLASSIFIER_PREREG.md`

---

## 0. Instructions for Claude Code (read first)

1. **Implement in the order of Section 10 (Build Plan).** Each phase ends at a **gate**. Do not proceed past a failed gate. Stop and report instead.
2. **This document is the spec.** Do not change definitions, thresholds, grids or kill conditions. If something is ambiguous or impossible, **stop and ask**. Agreed changes are made as a versioned edit to this doc (Section 13) *before* code changes.
3. **Never fabricate data.** This includes economic calendar dates (Section 3.4). If a source can't be found, stop and report.
4. **Log every configuration evaluated** to `results/shock_classifier/trials.csv` (Section 8), including exploratory and failed runs.
5. **Reuse existing framework layers** (data / signals / strategies / portfolio / execution / backtest / analytics, CostStack, walk-forward, Monte Carlo, Tearsheet). Flag any change to core modules.
6. Every new function gets unit tests. Section 9 lists required ones.
7. **No look-ahead anywhere.** Every quantity used at t0 must be computable from data strictly available at the t0 bar close.

---

## 1. Hypothesis in one paragraph

Large, fast price moves ("shocks") come in two kinds. **Information shocks** reflect new public information. Slower institutional money repositions over the following hour, so price **continues** in the shock direction. **Liquidity shocks** reflect a single aggressive order, stop cascade or thin book, with no new information. Temporary impact decays as liquidity providers unwind inventory, so price **reverts**. The two can be classified at t0 using **cross-asset confirmation** (did related markets move by their normal beta?) plus a **scheduled-event flag**. If the classes genuinely behave oppositely over 5–60 minutes, and the move outlasts a 1–5 minute fill delay, then trading *with* information shocks and *against* liquidity shocks is profitable net of cost.

---

## 2. Scope

**In scope**
- Instruments: NQ, ES, CL, GC. Execution in MNQ, MES, MCL, MGC.
- Timing: signal at t0, entry t0+1 to t0+5 min, maximum hold 60 min from entry.
- Primary session windows only (Section 3.3).

**Out of scope (v1)**
- Overnight/Globex-only shocks. This is a candidate v2 extension.
- Classification features 3 and 4 from the concept note (flow profile, liquidity regime). They're computed and reported as **diagnostics only**, not used in the primary classifier (decision D3).
- Any parameter values outside the grids in Section 6.

---

## 3. Data specification

### 3.1 Instruments and peers

| Traded | Peers for confirmation |
|---|---|
| NQ | ES, RTY, ZN, 6J |
| ES | NQ, RTY, ZN, 6J |
| CL | BZ (NYMEX Brent), HO, RB |
| GC | SI, 6E, ZN |

### 3.2 Market data

- 1-minute OHLCV bars for all traded and peer instruments from Databento, 2016-01-01 to latest available.
- Trade-level data with aggressor side for the **traded** instruments only. This is used for the flow-flip exit (Section 5.3) and diagnostics. If trade data is too costly for the full history, see open question Q3.
- Use the **front contract by volume on each day**. Intraday returns are computed within a single contract.
- **Roll days** (the day the front-by-volume contract changes) are **excluded** from shock detection and logged.
- Timezone: **America/New_York**, DST-aware.

### 3.3 Session windows (shock detection allowed)

| Instrument | Window (ET) |
|---|---|
| NQ, ES | 09:35 – 14:55 |
| CL | 09:05 – 13:25 |
| GC | 08:25 – 12:25 |

Each window ends at least 65 min before the main session close, so a 60-minute hold completes inside liquid hours. The first 5 min after the open are excluded (decision D5).

### 3.4 Economic calendar

Scheduled releases with timestamps, stored in `data/calendar/events.csv` with columns: `datetime_et, event, source_url`.

| Event | Typical time (ET) | Relevant to |
|---|---|---|
| CPI | 08:30 | All |
| Nonfarm Payrolls | 08:30 | All |
| FOMC statement | 14:00 | All |
| EIA Weekly Petroleum Status Report | Wed 10:30 (holiday shifts) | CL |
| EIA Natural Gas Storage | Thu 10:30 | CL (weak), diagnostic |

Dates must come from official schedules or archives (BLS, Federal Reserve, EIA). **Do not infer dates from typical rules** without verification against the source. Holiday shifts are common.

---

## 4. Signal definition

### 4.1 Time-of-day volatility

For minute-of-day m and day t:

```
σ_tod[t, m] = 1.4826 × median(|r_1m| at minute m over sessions t−60 … t−1)
```

This is a robust scale estimate, using prior sessions only.

### 4.2 Shock detection (defines t0)

For window w ∈ {1, 3} minutes, ending at bar close b:

```
r_w[b]   = P[b] / P[b − w] − 1
thresh_w = z × σ_tod[t, m(b)] × sqrt(w)
shock if |r_w[b]| > thresh_w
```

- t0 = close of bar b.
- Shock direction d = sign(r_w[b]). Shock size S = |P[b] − P[b − w]| in index points.
- **Cooldown:** no new shock in the same instrument within 60 min after a detected t0.
- If both windows trigger at the same bar, record once, labelled with the shorter window.

### 4.3 Peer betas

For each (traded, peer) pair, on day t:

```
β[t], ρ[t] = OLS beta and correlation of peer 1-min returns on traded 1-min returns,
             using session-window bars from days t−60 … t−1
```

A peer is **valid** on day t if |ρ| ≥ 0.3.

### 4.4 Confirmation ratio

For each valid peer j, over the same window w ending at b:

```
C_j = r_peer_j,w / (β_j × r_own,w)
C   = median over valid peers of C_j
```

At least 2 valid peers are required. Otherwise the class is NONE. The beta handles negatively correlated peers (e.g. ZN, 6J), so C ≈ 1 means the peers moved exactly as normally expected.

### 4.5 Event flag

`event = True` if t0 is within [release − 1 min, release + 5 min] of any relevant calendar event in Section 3.4.

### 4.6 Classification

```
INFO  if C ≥ c_hi,  OR (event AND C ≥ 0.3)
LIQ   if C ≤ c_lo  AND NOT event
NONE  otherwise   (no trade)
```

Primary: c_hi = 0.6, c_lo = 0.2.

### 4.7 Trade direction

```
INFO → trade direction = +d   (continuation)
LIQ  → trade direction = −d   (reversion)
```

---

## 5. Execution and exits

### 5.1 Entry fill model

- **Primary:** fill at the close of bar t0+1, plus 1 tick of adverse slippage (on top of CostStack).
- **Stress (must also be reported):** fill at the **worst** close among bars t0+1 … t0+5.
- **Passive diagnostic:** limit at the t0 close price. If it isn't filled by t0+5, cancel. Report the unfilled rate and compare the average outcome of unfilled vs filled trades, to measure adverse selection.

### 5.2 Baseline exits (path-invariant, signal frame)

Time-only exits at {5, 10, 15, 20, 30, 45, 60} min after entry.

### 5.3 Conditional exits (path-variant, book frame)

Evaluated in priority order at each 1-minute bar after entry:

1. **Stop:** price moves against the position by s × S from entry. Primary s = 0.5.
2. **Class-specific exit:**
   - LIQ: **retracement target** at fraction f of S from the shock's end price P[b]. Primary f = 0.5.
   - INFO: **flow-flip**. Rolling 3-min aggressor-signed volume turns against the position, and its magnitude exceeds the trailing 20-day median for that minute-of-day.
3. **Time stop:** 60 min after entry.

**Intra-bar ambiguity:** if the stop and target could both be hit within the same 1-minute bar, assume the **stop** was hit first (pessimistic).

### 5.4 Position sizing

1 micro contract per trade for evaluation. At most one open position per instrument.

---

## 6. Pre-registered parameter grid (complete)

| Parameter | Primary | Sensitivity only |
|---|---|---|
| z (shock threshold) | 4 | 3, 5 |
| w (shock window) | 1 and 3 (both primary, pooled) | separately |
| c_hi / c_lo | 0.6 / 0.2 | 0.5 / 0.3, 0.7 / 0.1 |
| s (stop multiple) | 0.5 | 0.75, 1.0 |
| f (retracement target) | 0.5 | 0.75 |
| Cost multiplier | 1× | 2× |

---

## 7. Tests

All analysis runs in **two frames**:
- **Signal frame (path-invariant):** event-study curves and time-only exits, with distribution analysis per trade.
- **Book frame (path-variant):** conditional exits, costs, fill model and prop constraints.

Standard errors are **clustered by day**. Confidence intervals use a day-level block bootstrap.

### Gate 0 — Data validity (not a hypothesis)
Bars cover at least 99% of expected session minutes. The calendar is sourced and verified. Roll days are identified. **Fail → STOP.**

### Event-study curves (produce first)
For each instrument × class, plot the mean return *in the trade direction* from the t0 close at every minute 0 … 60, with 95% CIs. Report the shock count per class.

### H1 — Class divergence (core hypothesis)
Using the primary fill (t0+1) and a 30-min time-only exit:
- INFO mean return (continuation direction) > 0, and LIQ mean return (reversion direction) > 0.
- **Pass (per instrument):** the difference between the two classes' returns *in the shock direction* is significant, with clustered t ≥ 2 after **Holm-Bonferroni across the 4 instruments** (family α = 0.05), **and** both classes have the predicted sign.

### H2 — Timing (your execution constraint)
For each class that passes H1:
- The peak of the event-study curve occurs **after t0+5**.
- **At most 50%** of the 60-min peak move is realised by t0+5.
- **Delay cost** is reported: mean capture from t0 vs from t0+5.
- **Fail → that class is untradeable at this latency.**

### H3 — Label placebo
Shuffle class labels within instrument-year, 1,000 permutations.
- **Pass:** the observed divergence exceeds the 95th percentile of the permutation distribution.

### H4 — Dose-response
Within INFO, a larger C gives stronger continuation. Within LIQ, a smaller C gives stronger reversion.
- **Pass:** Spearman ρ has the predicted sign in both classes (reported with CIs).

### H5 — Net profitability (book frame)
Conditional exits with primary parameters, primary fill, 1× cost.
- **Pass:** positive net mean per trade **and** the conditional exits beat the best pre-registered time-only exit **out of sample** (Section 11). If they don't, use the time-only exit.

### Robustness (report, do not re-select)
- Stress fill (worst of t0+1 … t0+5).
- 2× cost.
- z = 3 and 5, window 1 vs 3 separately, alternative C thresholds.
- With and without event-flagged shocks.
- By year, to check stability.
- Diagnostics: the flow-profile and liquidity-regime features vs outcome (descriptive only).

---

## 7A. Power analysis (v1.1)

**Formulas (planning, pre-registered):**
```
Flow / correlation tests:   SE ≈ 1 / sqrt(n_eff)
Price tests:                SE = σ_trade / sqrt(n_eff)
Minimum detectable effect:  MDE_t2 ≈ 2 × SE   (significance at t = 2)
                            MDE_80 ≈ 2.8 × SE (80% power at t = 2)
Clustering (design effect): n_eff = n / (1 + (m − 1) × ρ)
                            m = observations per cluster; ρ = within-cluster correlation (estimated from the data)
```

| Test | Planned n_eff | Planned SE | MDE (t = 2) |
|---|---|---|---|
| H1 class divergence (pooled, ~150 shocks per year per market × 4 × 10) | ~2,400 INFO vs ~1,800 LIQ | 0.031σ (difference) | 0.06σ |
| H1 per instrument | ~600 vs ~450 | ~0.06σ | ~0.12σ |
| H2 timing (event-study curve per class) | As H1 | As H1 | — |
| H4 dose-response within class | ~1,800–2,400 | ~0.02–0.025 | ~0.04–0.05 corr |

Rules: shocks cluster in time (several on the same volatile day), so n_eff uses the design effect with day clusters. Before Gate 1, compute the real n_eff, SE and MDE per instrument in `results/shock_classifier/POWER.md`, with a plausible-effect statement. Per-instrument cells that are underpowered are reported as inconclusive rather than failed.

## 7B. Three-track testing and power (v1.2)

**Track 1 (backtest)** is the primary evidence source. Full futures history exists; the binding input is the sourced economic calendar (Gate 0).

**Track 2 (forward recorder):** The economic calendar from official sources as releases are scheduled, plus trade-level data if not purchased historically (for the flow-flip exit). Records follow the ledger's storage rules (raw files kept, never overwritten, `fetched_at` as availability time).

**Track 3 (live-small, 1 micro, real account preferred):** logs implementation shortfall and signal-to-fill latency per trade, with the 50-trade cost review from the ledger doc (13A.5). Shocks are frequent (several a week per market across four markets), so N = 300 tradable INFO/LIQ trades is plausible within about a year. This is the model most likely to support a genuine forward efficacy test.

**Power check on the Track 3 target:** at N = 300 trades, SE ≈ 0.058σ and the MDE (t = 2) ≈ 0.115σ. If the Track 1 edge estimate is at or above that, Track 3 runs the frozen N = 300 efficacy test (futility looks at 100 and 200). If below, Track 3 is a **futility and consistency check** (forward mean within the Track 1 90% CI, same sign), and promotion rests on Track 1 plus shortfall within budget. The route is written down before counting starts.

**Promotion to prop evaluation:** Track 1 gates passed; the chosen Track 3 route passed; implementation shortfall within the (possibly revised) cost model; forward drawdown within prop limits.

## 8. Multiplicity accounting

- Primary inference: Holm-Bonferroni across the 4 instruments for H1.
- Every configuration evaluated is logged to `trials.csv`: `trial_id, timestamp, instrument, class, z, w, c_hi, c_lo, s, f, exit_type, fill_model, cost_mult, event_filter, n_trades, mean_gross, mean_net, t_clustered, sharpe_net, notes`.
- Any reported final Sharpe is accompanied by a **Deflated Sharpe Ratio** using the **total** trial count.

---

## 9. Required unit tests

1. `σ_tod` on day t uses only days t−60 … t−1 (look-ahead test).
2. Peer β and ρ on day t use only days t−60 … t−1.
3. Shock detection: a synthetic 5σ one-minute jump triggers; a 3σ jump doesn't at z = 4.
4. Cooldown: a second jump 30 min after the first is ignored; one at 61 min is detected.
5. Confirmation ratio: a peer with β = 0.5 moving exactly 0.5 × own gives C_j = 1. A negatively correlated peer (β = −0.3) moving −0.3 × own also gives C_j = 1.
6. A peer with |ρ| < 0.3 is excluded; fewer than 2 valid peers gives class NONE.
7. Classification truth table, including the event override (event and C = 0.35 gives INFO; event and C = 0.1 gives NONE).
8. Trade direction: INFO follows d; LIQ opposes d.
9. Intra-bar pessimism: a bar spanning both the stop and target records the stop.
10. Stress fill picks the worst close among t0+1 … t0+5 for the trade direction.
11. Session windows: shocks outside Section 3.3 windows and on roll days are excluded.
12. DST: window boundaries map correctly to UTC in both transition weeks.
13. Event window: a shock at release + 5 min is flagged; one at release + 6 min is not.

---

## 10. Build plan and gates

| Phase | Work | Gate |
|---|---|---|
| 1 | Bars, trades, roll calendar, economic calendar (sourced) | **Gate 0:** data validity, or STOP |
| 2 | σ_tod, shock detection, betas, C, classification, plus unit tests | All tests pass; report shock counts per class per instrument per year |
| 3 | Event-study curves, H1, H2, H3 | **Gate 1:** H1 passes for at least one instrument **and** H2 for at least one passing class. Otherwise STOP → write-up |
| 4 | H4, robustness, diagnostics | **Gate 2:** H3 passes. Otherwise STOP → write-up |
| 5 | Book frame: conditional exits, fill models, costs, prop constraints, Monte Carlo | **Gate 3:** H5 passes at 1× cost; report stress fill and 2× cost |
| 6 | Walk-forward (Section 11) and DSR | Final report |

---

## 11. Walk-forward

- train_bars = 252 trading days, test_bars = 63, rolling.
- In each train window, select from the **pre-registered grid only**: the exit type (best time-only vs conditional) and the (c_hi, c_lo) pair. Apply the selection unchanged to the following test window.
- Report the concatenated out-of-sample results and the overfitting ratio (IS vs OOS Sharpe).

---

## 12. Kill conditions (honest stop rules)

| Condition | Verdict |
|---|---|
| Gate 0 fails | Stop. Untestable. |
| H1 fails for all instruments | Kill. The classes don't diverge, so the classifier adds nothing. |
| H1 passes but H2 fails for all passing classes | Kill at current latency. Document as "real but too fast". |
| H3 permutation test fails | Kill. The divergence is not attributable to the classification. |
| Gross passes, net fails at 1× cost | Document as "real, not tradable". |
| OOS Sharpe < 0.5 × IS Sharpe in walk-forward | Do not trade. Write up. |

Every stop produces `results/shock_classifier/REPORT.md` with the verdict, the evidence (event-study plots included), and what was learned.

---

## 13. Decision log

| ID | Decision | Rationale |
|---|---|---|
| D1 | Cross-asset confirmation as the primary classifier | Information moves the whole complex; liquidity events are local to one market |
| D2 | Event flag overrides only with C ≥ 0.3 | A release-time move that peers ignore may still be liquidity-driven |
| D3 | Flow-profile and liquidity-regime features diagnostic only | Limits multiplicity in v1; candidates for v2 if diagnostics are informative |
| D4 | Time-of-day adjusted σ with robust median scale | Raw thresholds would fire mostly at the open and around releases |
| D5 | Exclude first 5 min after open and the final 65 min | Opening noise; ensures the 60-min hold completes in liquid hours |
| D6 | Exclude roll days | Volume split across contracts distorts shocks and betas |
| D7 | Pessimistic intra-bar and stress fills | Honest about the 1–5 min fill delay; paper fills overstate quality |
| D8 | NONE middle band not traded | Ambiguous shocks dilute both classes |

---

## 14. Open questions (owner to resolve)

- **Q1:** CostStack values for MNQ, MES, MCL and MGC (commission, slippage in ticks). Default: existing settings, stated in the report.
- **Q2:** Prop firm constraints: daily loss limit, trailing drawdown, flatten deadline.
- **Q3:** If full-history trade data is too costly, is v1 acceptable with bars only? The fallback replaces the INFO flow-flip exit with the time-only exit. This must be answered before Phase 5.
- **Q4:** Should overnight shocks be added in v2, using a separate σ_tod estimated on Globex hours?

---

## 15. Future versions (not built until the v1 verdict)

- v2: flow-profile and liquidity-regime features in the classifier (if the diagnostics support it); overnight sessions.
- v3: combine with LETF close-flow model signals where timing overlaps (NQ/ES, afternoon).
