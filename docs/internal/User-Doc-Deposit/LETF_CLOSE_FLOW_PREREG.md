# LETF Close-Flow Model — Pre-Registration & Design Document

**Status:** PRE-REGISTERED — v1.0 (2026-09-21)  
**Current version:** v1.1 (2026-09-21), additive amendment: adds the power analysis (Section 6A). All v1.0 text is retained unchanged.  
**Current version:** v1.2 (2026-09-21), additive amendment: adds three-track testing with power checks (Section 6B). All v1.1 text is retained unchanged.
**Owner:** Oisin
**Consumer:** Claude Code
**Suggested repo path:** `docs/research/LETF_CLOSE_FLOW_PREREG.md`

---

## 0. Instructions for Claude Code (read first)

1. **Implement in the order of Section 9 (Build Plan).** Each phase ends at a **gate**. Do not proceed past a failed gate. Stop and report instead.
2. **This document is the spec.** Do not change hypotheses, thresholds, parameter grids or kill conditions. If something is ambiguous or impossible, **stop and ask**. Do not improvise. Any agreed change is made as a versioned edit to this doc (Section 12) *before* code changes.
3. **Never fabricate data.** If point-in-time AUM cannot be built from real sources (Section 3.2), stop at Gate 0 and report.
4. **Log every configuration evaluated** to `results/letf_close_flow/trials.csv` (Section 7), including failed and exploratory ones. The trial count feeds the multiplicity correction.
5. **Reuse existing framework layers** (data / signals / strategies / portfolio / execution / backtest / analytics, CostStack, walk-forward, Monte Carlo, Tearsheet). Do not modify core modules without flagging it.
6. Every new function gets unit tests. Section 8 lists required ones.

---

## 1. Hypothesis in one paragraph

Leveraged and inverse ETFs must rebalance daily to maintain constant leverage. The required rebalance is mechanical: **ΔH = L(L−1) · A · r**. It is always **in the direction of the day's move**, for both long and inverse funds. Issuers and their swap counterparties hedge this late in the session. **If** a meaningful share of that hedging runs through, or transmits into, index futures in the last hour, then NQ/ES returns from mid-afternoon to the close should be positively related to the predicted flow, and the relationship should scale with flow size and with aggregate LETF AUM over time.

---

## 2. Scope

**In scope**
- Instruments traded: NQ/MNQ (primary) and ES/MES (secondary).
- Flow sources: index-level leveraged/inverse ETFs listed in Section 3.1.
- Intraday only: entry between 14:30 and 15:30 ET, exit by 15:59 ET.

**Out of scope (v1)**
- Single-stock leveraged ETFs (NVDL, TSLL, etc.).
- Vol-control/risk-parity and CTA flow components. These are future overlays, only if v1 passes.
- Options, cash equities, ETFs as traded instruments.
- Any parameter tuning beyond the grids in Section 5.

---

## 3. Data specification

### 3.1 ETF universe

| Ticker | Issuer | Underlying | L |
|---|---|---|---|
| TQQQ | ProShares | Nasdaq-100 | +3 |
| SQQQ | ProShares | Nasdaq-100 | −3 |
| QLD | ProShares | Nasdaq-100 | +2 |
| QID | ProShares | Nasdaq-100 | −2 |
| UPRO | ProShares | S&P 500 | +3 |
| SPXU | ProShares | S&P 500 | −3 |
| SSO | ProShares | S&P 500 | +2 |
| SDS | ProShares | S&P 500 | −2 |
| SPXL | Direxion | S&P 500 | +3 |
| SPXS | Direxion | S&P 500 | −3 |

Nasdaq-100 funds map to NQ. S&P 500 funds map to ES.

### 3.2 Point-in-time AUM (critical)

- `A[t-1]` = shares outstanding × NAV **as of the prior day's close**. This is the exposure the fund carries into day t.
- **Source priority:** (1) issuer historical NAV and shares-outstanding downloads; (2) other documented historical sources. Record the source per ticker in `data/letf/SOURCES.md`.
- **Do not** back-fill today's shares outstanding across history. yfinance's current `sharesOutstanding` is **not acceptable** for history.
- Store in Parquet: `date, ticker, nav, shares_out, aum, source`.

**Validation (Gate 0):**
- No gaps longer than 3 trading days (after excluding holidays).
- Day-over-day AUM change is explained by NAV return ± creations/redemptions. Flag days where |ΔAUM| > 25% for manual review.
- Spot-check at least five dates per ticker against an independent source. Document the checks.

### 3.3 Futures data

- NQ, ES 1-minute bars from Databento, 2016-01-01 to latest available.
- Use the **front contract by volume on each day**, i.e. the actual contract that would be traded. Intraday returns are computed within a single contract, so no back-adjustment is needed.
- Timezone: all timestamps converted to **America/New_York**, DST-aware.

### 3.4 Session calendar

- Regular session reference close: **16:00 ET**.
- **Exclude early-close sessions** (e.g., day after Thanksgiving, Christmas Eve). Log excluded dates.
- **Flag, but do not exclude**, in the primary analysis: FOMC days, CPI days, quad-witching days, NDX/S&P index rebalance days, and quarter-ends. Section 6 reports results with and without flagged days as a robustness check.

---

## 4. Model definition

### 4.1 Day's return so far

For entry time τ on day t:

```
r[t, τ] = P_fut(t, τ) / P_fut(t-1, 16:00) − 1
```

Uses the futures price as a proxy for the index return. The prior reference is the 16:00 ET bar close on t−1. The basis drift between 16:00 and τ is accepted as noise (documented decision D3).

### 4.2 Required rebalance per fund

```
ΔH_i[t, τ] = L_i · (L_i − 1) · A_i[t−1] · r[t, τ]     (USD notional of underlying)
```

Sign check (must be unit-tested): for both L = +3 and L = −3, an up day gives positive ΔH (buy). The multipliers are 6 and 12 respectively.

### 4.3 Aggregate flow and contract equivalent

```
Q_usd[t, τ] = Σ_i ΔH_i[t, τ]      (separately for NDX set and SPX set)
Q_contracts = Q_usd / (multiplier × P_fut(t, τ))
```

Multipliers: NQ = 20, ES = 50.

### 4.4 Normalised flow and predicted impact

```
V[t]     = 20-day trailing mean daily volume, NQ-equivalent (NQ + MNQ/10), using days t−20..t−1 only
σ_d[t]   = 20-day trailing daily return std, days t−20..t−1 only
q[t, τ]  = Q_contracts / V[t]
I[t, τ]  = Y · σ_d[t] · sqrt(|q[t, τ]|) · P_fut(t, τ)      (predicted impact, index points)
```

**Y = 0.7, fixed.** It is not fitted or tuned (decision D4).

### 4.5 Signal

```
direction[t, τ] = sign(Q_usd[t, τ])
active[t, τ]    = I[t, τ] ≥ k · RT_cost_points
```

where `RT_cost_points` is the CostStack round-trip cost for the traded instrument, in index points, and k is from the grid in Section 5.

### 4.6 Trade rule (book frame)

- If active: enter at the τ bar close in `direction`, exit at the 15:59 ET bar close.
- One trade per instrument per day maximum.
- Execution in micros (MNQ/MES). Position sizing is defined in Section 6.3.

---

## 5. Pre-registered parameter grid (complete — nothing else may be tested)

| Parameter | Values |
|---|---|
| Entry time τ | 14:30, 15:00, 15:30 ET |
| Instrument | NQ (NDX funds), ES (SPX funds) |
| Activation multiple k | 3 (primary), 2 and 5 (sensitivity only) |
| Hold (signal frame sweep) | 5, 10, 15, 30, 60 min, to-close |

**Primary cells:** τ ∈ {14:30, 15:00, 15:30} × instrument ∈ {NQ, ES} at k = 3, hold to close. That's **6 primary cells**.

---

## 6. Tests

All tests run in **two frames**, per standard practice:
- **Signal frame (path-invariant):** signed forward returns from τ, sweeping hold lengths, distribution analysis per trade.
- **Book frame (path-variant):** the trade rule with costs, sizing and prop constraints applied.

Standard errors use **Newey-West/HAC** estimators where observations overlap or are autocorrelated.

### Gate 0 — Data validity (not a hypothesis)
Point-in-time AUM passes all checks in Section 3.2. **Fail → STOP.**

### H1 — Primary effect
On active days, the mean signed return (τ → close) in `direction` is positive.
- **Pass:** at least one primary cell has a gross t-stat ≥ 2 after **Holm-Bonferroni** correction across the 6 primary cells (family α = 0.05), **and** the mean exceeds 1× round-trip cost.

### H2 — Dose-response
The mean signed return increases with |q| across **quintiles** of all days, not only active days.
- **Pass:** Spearman ρ between quintile rank and mean signed return is > 0, with a monotonic or near-monotonic pattern (at most one inversion).

### H3 — AUM scaling (built-in placebo)
The regression coefficient of signed return on q is compared by year. Aggregate LETF AUM grew substantially over 2016–2026.
- **Pass:** a positive relationship between yearly effect size and yearly mean aggregate AUM, or at minimum no significant *negative* trend. Report the per-year table regardless.

### H4 — Time placebo
Apply the identical signal (same day's q, computed at 11:00 ET) to the 11:00–12:00 ET window.
- **Pass:** effect **not** significant (|t| < 2). A significant placebo means the "effect" is generic intraday momentum, not LETF flow.

### H5 — Transient impact (diagnostic only, not intraday)
Signed return from close(t) to the 09:45 ET open(t+1) on active days. **Reported, not traded.** It informs whether impact reverts.

### Robustness (report, do not re-select)
- With and without flagged event days (Section 3.4).
- k = 2 and k = 5.
- Costs at 1× and 2× CostStack.
- Monte Carlo (block bootstrap) on the book-frame equity curve for the best primary cell.

### 6.3 Book frame specifics
- Size: fixed 1 MNQ / 1 MES per trade for evaluation. Scaling is out of scope for v1.
- Prop constraints are simulated as parameters: daily loss limit, trailing drawdown, flatten deadline. Values are to be supplied by the owner (open question Q2). The flatten deadline must be later than 15:59 ET, otherwise flag it.

---

## 6A. Power analysis (v1.1)

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
| H1 primary cell (active days at k = 3, per instrument) | ~500–1,500 | ~0.026σ–0.045σ | ~0.05σ–0.09σ |
| H2 dose-response (all days, quintiles) | ~2,500 per instrument | 0.020 | 0.040 corr |
| H3 AUM scaling (yearly coefficients) | ~10 years | Wide | Descriptive; direction only |
| H4 time placebo | Same as H1 | Same as H1 | — |

Rules: before Gate 1, compute the real n_eff, SE and MDE per primary cell in `results/letf_close_flow/POWER.md`, with a plausible-effect statement (default: MDE at or below round-trip cost). A primary cell whose MDE exceeds the plausible effect is labelled underpowered, and a null result there is recorded as inconclusive, not as evidence of no effect. H3 is treated as directional only, given about 10 yearly observations.

## 6B. Three-track testing and power (v1.2)

**Track 1 (backtest)** is the primary evidence source. Full futures history exists; the binding input is point-in-time AUM (Gate 0).

**Track 2 (forward recorder):** Daily snapshots of each ETF's NAV, shares outstanding and published AUM from today onward, so the model never depends on a single historical source. Records follow the ledger's storage rules (raw files kept, never overwritten, `fetched_at` as availability time).

**Track 3 (live-small, 1 micro, real account preferred):** logs implementation shortfall and signal-to-fill latency per trade, with the 50-trade cost review from the ledger doc (13A.5). At roughly 20% of days active across NQ and ES, expect on the order of 100 trades a year, so N = 300 takes about 3 years. That makes the consistency route the likely one unless the Track 1 edge is large.

**Power check on the Track 3 target:** at N = 300 trades, SE ≈ 0.058σ and the MDE (t = 2) ≈ 0.115σ. If the Track 1 edge estimate is at or above that, Track 3 runs the frozen N = 300 efficacy test (futility looks at 100 and 200). If below, Track 3 is a **futility and consistency check** (forward mean within the Track 1 90% CI, same sign), and promotion rests on Track 1 plus shortfall within budget. The route is written down before counting starts.

**Promotion to prop evaluation:** Track 1 gates passed; the chosen Track 3 route passed; implementation shortfall within the (possibly revised) cost model; forward drawdown within prop limits.

## 7. Multiplicity accounting

- Primary inference uses Holm-Bonferroni over the 6 primary cells.
- Every configuration evaluated, including sensitivity, robustness, and anything exploratory, is logged to `trials.csv` with: `trial_id, timestamp, tau, instrument, k, hold, cost_mult, event_filter, n_trades, mean_gross, mean_net, t_hac, sharpe_net, notes`.
- The final reported Sharpe for any surviving configuration is accompanied by a **Deflated Sharpe Ratio** using the **total** trial count from `trials.csv`.

---

## 8. Required unit tests

1. `rebalance_flow(L=3, A=1e9, r=0.02)` = +1.2e8.
2. `rebalance_flow(L=-3, A=1e9, r=0.02)` = +2.4e8 (same sign as the move).
3. `rebalance_flow(L=2, A=1e9, r=-0.01)` = −2e7.
4. Zero return gives zero flow for all L.
5. Point-in-time guard: the AUM used on day t equals the stored value for t−1, and never t.
6. The rolling V and σ_d on day t use no data from day t or later (look-ahead test).
7. Contract conversion: Q_usd = 1e7 at NQ price 25,000 gives 20 contracts.
8. DST: 15:00 ET maps correctly to UTC in both March and November transition weeks.
9. Early-close sessions are excluded from the trade calendar.

---

## 9. Build plan and gates

| Phase | Work | Gate |
|---|---|---|
| 1 | Build point-in-time AUM dataset (Section 3.2), sources documented | **Gate 0:** validation passes, or STOP and report |
| 2 | Futures bars, session calendar, event flags | Data QA report: bar coverage, excluded dates |
| 3 | Model functions (Section 4) and unit tests (Section 8) | All tests pass |
| 4 | Signal-frame analysis: H1–H5, hold sweep, distributions | **Gate 1:** H1 pass **and** H4 pass. Otherwise STOP → write-up |
| 5 | H2, H3, robustness | **Gate 2:** H2 pass and H3 not negative. Otherwise STOP → write-up |
| 6 | Book frame, costs, prop constraints, Monte Carlo | **Gate 3:** net positive at 1× cost; report 2× |
| 7 | Walk-forward (Section 10) and DSR | Final report |

---

## 10. Walk-forward

The model has almost no fitted parameters, since Y and the grid are fixed. Walk-forward is used only to **select k and τ** out of sample:
- train_bars = 252 trading days, test_bars = 63, rolling.
- In each train window, choose the (τ, k) cell with the best net mean. Apply it unchanged to the next test window.
- Report the concatenated out-of-sample result and the overfitting ratio (in-sample vs out-of-sample Sharpe).

---

## 11. Kill conditions (honest stop rules)

| Condition | Verdict |
|---|---|
| Gate 0 fails | Stop. Model is untestable without point-in-time AUM. |
| H1 fails in all primary cells | Kill. No detectable effect. |
| H1 passes but H4 placebo is also significant | Kill. It's generic late-day momentum, not LETF flow. |
| H1 passes, H2 fails | Kill as likely spurious (no dose-response). |
| Gross passes, net fails at 1× cost | Document as "real, not tradable". Candidate for overlays in v2. |
| Walk-forward overfitting ratio collapses (OOS Sharpe < 0.5 × IS) | Do not trade. Write up. |

A kill is a valid outcome. Every stop produces a write-up in `results/letf_close_flow/REPORT.md` with the verdict, the evidence, and what was learned.

---

## 12. Decision log

| ID | Decision | Rationale |
|---|---|---|
| D1 | Index-level LETFs only in v1 | Direct mapping to NQ/ES; single-stock LETF flow transmits indirectly |
| D2 | AUM at t−1 close | The fund's exposure entering day t is what gets rebalanced |
| D3 | Futures return as index-return proxy | Avoids needing intraday index data; the basis noise is small relative to the signal |
| D4 | Y = 0.7 fixed | Middle of the empirical range for square-root impact; fixed to prevent tuning |
| D5 | Exclude early closes, flag event days | Early closes shift the rebalance timing; event days are kept but tested separately |
| D6 | Micros for execution | Prop-compatible sizing; costs modelled per micro |
| D7 | Exit 15:59 ET | Captures the close hedging window before settlement |

---

## 13. Open questions (owner to resolve before Phase 6)

- **Q1:** CostStack values to use for MNQ/MES at the close (commission, slippage in ticks). Default: existing CostStack settings, stated explicitly in the report.
- **Q2:** Prop firm constraints: daily loss limit, trailing drawdown, flatten deadline.
- **Q3:** If issuer shares-outstanding history is only partially available, is a shorter sample (e.g., from the earliest complete year) acceptable? This must be answered in writing before relaxing Gate 0.

---

## 14. Future versions (not to be built until v1 verdict)

- v2 overlays: vol-control flow sign, month- and quarter-end rebalancing, conditioning on late-day moves.
- v3: commercial hedger model (energy), using the same pre-registration format.
