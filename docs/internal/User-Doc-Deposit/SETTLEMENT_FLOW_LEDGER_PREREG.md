# Settlement Flow Ledger (Commodity LETF + Participant Model) — Pre-Registration & Design Document

**Status:** PRE-REGISTERED — v1.5 (2026-09-21)  
**Current version:** v1.6 (2026-09-21), additive amendment. All v1.5 text is retained unchanged.  
**Current version:** v1.7 (2026-09-21), additive amendment. All v1.6 text is retained unchanged.  
**Current version:** v1.8 (2026-09-21), additive amendment. All v1.7 text is retained unchanged.  
**Current version:** v1.9 (2026-09-21), additive amendment. All v1.8 text is retained unchanged.
**Changelog:** v1.1 adds the iNAV/premium model, the ETF market-maker hedging split, the premium as a state variable, Gate 0b, Stages C1/C2, and hypotheses H8–H10. v1.2 adds the news/virality detector for retail (P3.7), Stage C3, data spec 3.3c, and H11. v1.3 adds P9 (non-US leveraged commodity ETPs), Stage G, fund list 3.1b, restrike events, and diagnostic H12. v1.4 adds the three-track testing plan (Section 13A): backtest, forward data recording, and paper/live-small trading, with a frozen forward-test protocol. v1.5 replaces the P8 roll flag with computed fund-level roll flows (P8a), keeps a scaled flag for other index trackers (P8b), and adds diagnostic H13. Nothing has been run, so all are pre-registration amendments, not post-hoc changes. **v1.6 (additive only):** adds auxiliary datasets (3.3d), the error budget and auxiliary calibrations (Section 8A), Stages H (depth-based impact) and I (large-lot measurement), diagnostics H14–H15, recorder jobs, unit tests 41–50, decisions D28–D34 and questions Q21–Q24. No existing definition, threshold or rule was removed or altered. **v1.7 (additive only):** adds the power analysis and minimum detectable effects (Section 9A), alternative validation for participants that can't be tested individually (Section 9B), marginal-contribution testing with variance inflation checks, unit tests 51–58, decisions D35–D41 and phase 2b. **v1.8 (additive only):** folds the power analysis (9A) and alternative validation (9B) into the three-track test plan (13A.7): power class per stage in `TRACK_MAP.md`, power-based forward evaluation lengths, the forward consistency test, and a power check on the Track 3 trading target. Adds unit tests 59–63 and decisions D42–D46. **v1.9 (additive only):** adds programme-level false-positive controls (Section 13A.8): sealed vault holdout, cross-document α allocation, programme-level Deflated Sharpe, 50% haircut, episode and shared-period checks, one-bar-delay robustness and a leak canary. Adds phase 0b, kill conditions, unit tests 64–71, decisions D47–D53 and question Q25.
**Owner:** Oisin
**Consumer:** Claude Code
**Suggested repo path:** `docs/research/SETTLEMENT_FLOW_LEDGER_PREREG.md`
**Related docs:** `LETF_CLOSE_FLOW_PREREG.md`, `SHOCK_CLASSIFIER_PREREG.md`. The TAS settlement-demand concept is folded into this doc as participant 5/6 inputs.

---

## 0. Instructions for Claude Code (read first)

1. **Build in stages (Section 6).** Stage A must pass its gate before Stage B starts, and so on. Each later stage is kept **only if** it improves out-of-sample results by the pre-registered margin. Otherwise it's dropped, and the simpler model stands.
2. **This document is the spec.** Do not change definitions, stages, grids, thresholds or kill conditions. If something is ambiguous or impossible, **stop and ask**. Agreed changes are versioned edits to this doc (Section 15) *before* code changes.
3. **Never fabricate data or facts.** This includes fund holdings, creation cut-offs, settlement window times, and TAS symbology. Every externally sourced fact is recorded in `data/settlement_flow/SOURCES.md` with a URL and access date.
4. **Log every configuration evaluated** to `results/settlement_flow/trials.csv` (Section 11).
5. **Reuse existing framework layers** (data / signals / strategies / portfolio / execution / backtest / analytics, CostStack, walk-forward, Monte Carlo, Tearsheet). Flag any change to core modules.
6. **No look-ahead.** Everything used at t0 must be computable from data strictly available at the t0 bar close. Fund data published after the close of day t−1 may be used on day t only if its publication time precedes t0.
7. Every new function gets unit tests (Section 12).
8. **Testing runs on three parallel tracks (Section 13A).** Start the forward data recorder (Track 2) **first**, before any backtest work, because missed days can never be recovered. Stages without usable history are tested only under the frozen forward protocol (13A.4). Never backfill forward-only stages with approximations.

---

## 1. Hypothesis in one paragraph

On each trading day, a set of participants must trade CME natural gas and crude oil futures at or near the daily **settlement window**. The largest mechanical contributors are 2× leveraged/inverse commodity ETFs, whose required rebalance is **AUM × L(L−1) × day's return**, always in the direction of the day's move. Creation/redemption flows, TAS liquidity providers, commercial hedgers and index rolls add to or offset it. Some of the flow is absorbed before the window by pre-hedging and netting. By modelling each participant's expected contribution (the **flow ledger**), updating it with flow already observed before t0, and converting the remaining expected flow into a predicted move via square-root impact, we can decide **whether, when and how large** to trade in the 20–40 minutes before the window, exiting at or shortly after it.

The creation/redemption term is modelled through the **ETF premium to its intraday fair value (iNAV)** and the behaviour of **ETF market makers**. Market makers hedge retail ETF buying in futures intraday, so hedged creations net out at settlement; only the **unhedged** portion lands in the window. The premium's size is used as an estimate of how far market makers are falling behind.

---

## 2. Scope

**In scope**
- Instruments: CME NG and CL. Execution in micro or smaller contracts (Q7 resolves which).
- Daily settlement window only. Primary trade: pre-window entry, exit at the end of the window.
- Participants 1–8 as defined in Section 4, built in stages.
- ETF prices and quotes (BOIL, KOLD, UCO, SCO, UNG, USO) as **model inputs only**. ETFs are never traded.

**Out of scope (v1)**
- Trading inside the window at speed.
- Physical supply/demand bias for commercial hedgers (participant 6). This is a Stage F+ candidate.
- Other commodities, and ICE-listed products.
- Trading an intraday "follow the ETF flow" signal. H8 may justify a separate doc later.
- ETF options activity for the creation model (Section 17).

---

## 3. Data specification

### 3.1 Fund universe

| Fund | Underlying | L | Role |
|---|---|---|---|
| BOIL | Natural gas (index-based futures) | +2 | Rebalance + creations |
| KOLD | Natural gas | −2 | Rebalance + creations |
| UCO | Crude oil | +2 | Rebalance + creations |
| SCO | Crude oil | −2 | Rebalance + creations |
| UNG | Natural gas | +1 | Creations only (L(L−1) = 0) |
| USO | Crude oil | +1 | Creations only |

For each fund, per day, store in Parquet: `date, fund, nav, shares_out, aum, futures_notional_by_contract_month, swap_notional, source, published_at`.

- **Contract months matter.** Funds hold the months specified by their index or methodology, which may **not** be the front month. Flow is mapped to the contract months actually held (from holdings). The traded contract is the one receiving the largest share of predicted flow (decision D2).
- **Point-in-time only.** Use holdings as published for each date. Never back-fill today's composition across history.

### 3.1b Non-US leveraged commodity ETPs (P9)

Initial research findings (September 2026). **All figures are indicative and must be re-sourced point-in-time.**

| Product | Listing | Exposure | Hedge route | Indicative size | Notes |
|---|---|---|---|---|---|
| BetaPro HNU / HND | TSX (CAD) | Up to +2× / −2× NG, front-month rolling index | Derivatives via counterparties (verify: swaps/forwards vs futures) | HNU roughly C$175–245m (Sept 2026); HND to source | **Leverage is "up to 2×" at manager discretion**; the manager may change it with market conditions and counterparty negotiations |
| BetaPro HOU / HOD | TSX (CAD) | Up to +2× / −2× crude | As above | To source | Same discretionary-leverage caveat |
| WisdomTree Natural Gas 3x Daily Leveraged (3NGL/NGXL) | LSE, Xetra, Borsa Italiana | +3× NG, 2nd-front-month NYMEX index | Fully collateralised swap (BNP Paribas Arbitrage reported as swap provider) | Roughly €48–69m across share lines | Intraday **restrike at a 20% threshold** |
| WisdomTree Natural Gas 3x Daily Short (3NGS) | As above | −3× NG | Swap | To source | Verify existence, index and restrike terms |
| WisdomTree WTI Crude Oil 3x Daily Leveraged / Short (3OIL / 3OIS) | As above | ±3× WTI | Swap | To source | Verify existence, index and restrike terms |

Further candidates (Asian listed leveraged crude/NG ETPs) are out of scope until the above are verified.

### 3.2 Fund facts to source and verify (Gate 0)

For each fund, record in `SOURCES.md`:
- Split of exposure between futures and swaps, over time.
- **Creation/redemption order cut-off time** and **execution timing**: whether the fund transacts creations the same day at settlement or the next day (the lag parameter `lag_c` ∈ {0, 1}).
- Whether the fund states it uses settlement-price or TAS execution for rebalancing.
- Index roll schedule (dates and fractions rolled per day).

### 3.3 Market data (Databento)

- 1-minute bars and trade-level data with aggressor side for all NG and CL contract months that funds hold, 2016-01-01 onward (or from the earliest date of reliable fund data).
- **TAS instruments** for NG and CL: trades and aggressor side. Verify symbology and coverage (Q3).
- Timezone: **America/New_York**, DST-aware.

### 3.3b ETF market data

- 1-minute NBBO quote midpoints and trades with aggressor side (exchange-provided or Lee-Ready classification, documented) for BOIL, KOLD, UCO, SCO, UNG, USO, 09:30–16:00 ET. Source and coverage to confirm (Q8).
- Official intraday indicative value (IIV) feed, if obtainable, for **validation only** (decision D14).

### 3.3c News and attention data (P3.7)

Only sources with **reproducible historical timestamps** are eligible for the primary model (decision D15):

| Source | Granularity | Use |
|---|---|---|
| GDELT (global news events and tone) | 15 min, from 2015 | Primary: news volume, tone, headline bursts |
| Wikimedia hourly pageviews | Hourly, from 2015 | Primary: public attention |
| Reddit / StockTwits archives | Per post | **Optional:** only if a timestamped archive covering the sample is obtained lawfully and within platform terms (Q12) |
| Google Trends | Varies | **Excluded** from modelling (resampled and revised, not point-in-time). Qualitative checks only |

Query definitions (keyword lists, article titles, tickers) are fixed in `data/attention/QUERIES.md` **before** any feature is computed, and not changed afterwards without a doc edit.

### 3.3d Auxiliary datasets (v1.6)

| Dataset | Source | Cost | Frequency / history | Use in this doc |
|---|---|---|---|---|
| Disaggregated Commitments of Traders, NG and CL | CFTC | Free | Weekly (Tuesday positions, released Friday); long history | Swap-dealer net position changes as an auxiliary estimate of bank netting (8A.2) |
| Public swap dissemination (commodity swaps referencing NG, crude or commodity indices) | Swap data repositories under Dodd-Frank | Free | Near real-time, capped notionals; history to confirm (Q21) | Timing of bank exposure build (8A.3, H15) |
| CME market-by-order (MBO) for traded contract months | Databento | Paid | Order-level; history depth to confirm (Q22) | Resting depth at t0 for state-dependent impact (Stage H); order-book pre-positioning diagnostics |
| Historical daily ETF holdings (futures vs swaps, contract months) | Commercial vendor, to be priced (Q23) | Paid | Daily | Backtest Stage E instead of forward-only |
| CME options open interest by strike, NG and CL | CME / Databento | Cheap | Daily | Pin-risk diagnostic now; P11 options dealers later |

Point-in-time rules from Section 0 apply to all of these: COT data is usable only after its Friday release; swap-dissemination records only after their dissemination timestamp.

### 3.4 Settlement window

`W_start`, `W_end` per product, sourced from CME settlement procedures (currently understood to be about 14:28–14:30 ET for NG and CL; **verify and record**). Historical changes to window times must be captured with effective dates.

### 3.5 Calendar

- Exclude early-close and holiday-affected sessions.
- **Flag:** contract expiry days, index roll days, EIA crude (Wed) and gas storage (Thu) report days, fund-specific roll days. Primary analysis includes flagged days; robustness reports them separately.

---

## 4. Participant models (the flow ledger)

All flows are in **contracts of the traded contract month**, signed (+ = buy). For day t and evaluation time τ:

```
r[t, τ] = P_held(t, τ) / Settle_held(t−1) − 1
```

This is the return on the fund's held contract(s), weighted by holdings, from the prior settlement to τ.

**Forecasting the rest of the day.** At τ < W_start the day's final return isn't known. The ledger uses **r[t, τ] as the forecast of the settlement-to-settlement return** (a martingale assumption, decision D3).

### P1 — Leveraged ETF rebalance (computable)

```
Q1 = Σ_funds AUM[t−1] × L × (L − 1) × r[t, τ] × f_fut[t−1] / (multiplier × P_held)
```

- `f_fut` = futures share of exposure, from holdings.
- Variance term `var_Q1` comes from uncertainty in the final return between τ and settlement: `(AUM × L(L−1) × f_fut)² × σ²_remaining(τ)`, where σ_remaining is the return volatility from τ to settlement, estimated from prior days.

### P2 — Swap counterparties (latent)

```
Q2 = Σ_funds AUM × L(L−1) × r × (1 − f_fut) × (1 − n) / (multiplier × P_held)
```

- `n` ∈ [0, 1] = internal netting fraction. **Latent**, estimated (Section 8).
- Pre-hedging is handled by the global pre-absorption parameter in the update step (Section 5), not separately.

### P3/P4 — Creations driven by retail, via ETF market makers (modelled)

**Mechanism (sequence on a creation day):**
1. Retail buys ETF shares. The ETF market maker sells them and is left short the ETF.
2. The market maker hedges by buying futures **intraday** (hedged fraction h).
3. At execution, the market maker creates shares via the authorised participant. The fund invests the new cash in futures at L× exposure.
4. The market maker sells its hedge futures at the same time.

Steps 3 and 4 net out for the hedged fraction. Only **(1 − h)** of the creation flow lands in the settlement window as net flow. Redemptions mirror this. For inverse funds, the sign follows L.

#### P3.1 iNAV (self-computed)

```
iNAV_f(τ) = NAV_f[t−1] × (1 + L_f × r_held,f(τ)) + NAV_f[t−1] × (y_cash / 360 − ER_f / 365)
```

- `r_held,f` = holdings-weighted return of fund f's held contracts from the prior settlement to τ.
- `y_cash` = collateral yield (T-bill rate, point-in-time). `ER_f` = expense ratio.
- If the prospectus shows NAV is struck on a different price basis (Q10), the formula is amended by doc edit before use.

**Gate 0b (iNAV validation):** per fund, |iNAV at settlement − official NAV[t]| ≤ 5 bp on ≥ 95% of days. Failures are investigated (holdings timing, roll weights, accrual) before any P3 work.

#### P3.2 Premium

```
prem_f(τ) = (mid_f(τ) − iNAV_f(τ)) / iNAV_f(τ)
```

- Uses the NBBO **midpoint**, never the last trade.
- A minute is **valid** only if the ETF quote updated within the last 60 s **and** the held futures contract traded within that minute.
- Premium is computed **only before W_start** (decision D10). After settlement, NAV references a fixed price while futures keep trading.

#### P3.3 Features at τ (from 09:30 ET to τ, valid minutes only)

| Feature | Definition |
|---|---|
| `prem_twa` | Time-weighted mean premium |
| `prem_frac` | Signed fraction of minutes with \|prem\| > c_AP: (count above +c_AP − count below −c_AP) / valid minutes |
| `vol_x` | ETF volume / trailing 20-day mean for the same interval |
| `sv_etf` | Aggressor-signed ETF volume × iNAV (USD) |
| `stress` | \|prem_twa\| z-scored against its trailing 60-day distribution |

`c_AP` = the authorised participant's creation cost threshold as a fraction of basket value. Primary 0.10%; sensitivity 0.05% and 0.20%. It is refined only via Q9 by doc edit.

#### P3.4 Creation model

Target: `ΔCreate_f[t] = (shares_out[t] − shares_out[t−1]) × NAV_f[t]` (USD, point-in-time, respecting `published_at` and Q11).

```
Baseline (C1):  ΔCreate_hat = a0 + a1·r[t−1] + a2·r[t−5 … t−1] + a3·ΔCreate[t−1]
Premium (C2):   ΔCreate_hat = C1 + b1·(prem_twa × AUM) + b2·prem_frac + b3·sv_etf + b4·(prem_twa × vol_x)
```

Linear, estimated by least squares in walk-forward training windows. Expected signs (reported, not constrained): a1, a2 < 0; a3 > 0; b1–b4 > 0.

**Execution day:** if `lag_c = 0`, the creation flow is transacted today and the model forecasts it. If `lag_c = 1`, today's fund purchase comes from yesterday's orders and is taken as known (`Q3_known`), while C2 forecasts tomorrow's. Which date `shares_out` reflects is resolved by Q11.

#### P3.5 Hedging split

```
Create_flow = L_f × ΔCreate_f / (multiplier × P_held)          (fund futures trade on execution day)
h           = 1 / (1 + exp(−(h0 − h1 × stress)))                (h1 ≥ 0: more stress → less hedged)
Q3_window   = (1 − h) × Create_flow                              (enters the ledger)
Q3_intraday = h × Create_flow                                    (already executed intraday; only visible via the update step)
```

`h0, h1` are fitted in Stage C2 against realised window flow (decision D11).

#### P3.6 Premium as a state variable

The premium has three uses. Only (a) is in the primary model in v1:
- **(a) Unhedged flow:** through h, above.
- **(b) Liquidity stress:** when market makers can't keep up, impact per unit flow should rise. Tested as H9 (diagnostic).
- **(c) Retail crowding:** a persistent, un-arbitraged premium signals extreme crowding and a possible next-day reversal. Tested as H10 (diagnostic).

#### P3.7 News and virality detector (retail attention)

**Purpose:** retail money arrives in bursts driven by headlines and social spread. The detector estimates *how much retail attention is building* before it shows up in ETF premiums and share counts, and feeds the creation model (C3) and the hedging split.

**Raw series per market (NG, CL), from 3.3c:**
- `news_n(τ)`: GDELT article count matching the fixed query in the last 60 min. `news_tone(τ)`: mean tone of those articles.
- `wiki_n(h)`: pageviews summed over the fixed article list in the last completed hour.
- Optional (only if Q12 is resolved): `social_n(τ)`: posts mentioning the fixed tickers or keywords in the last 60 min.

**Normalisation:** each series is converted to a z-score against the same hour-of-day and day-of-week over the trailing 60 days (prior data only): `z_news`, `z_wiki`, `z_social`.

**Detector features at τ:**

| Feature | Definition | Captures |
|---|---|---|
| `att_level` | Mean of available z-scores | How much attention there is |
| `att_accel` | Change in `att_level` over the last 3 hours vs the prior 3 hours | Whether attention is **accelerating** (virality) |
| `att_breadth` | Count of sources with z > 2 | Spread across channels (news only vs news plus public plus social) |
| `lev_share` | Share of matched social posts naming BOIL/KOLD/UCO/SCO (optional) | Retail intent to use leveraged products |
| `headline_burst` | 1 if `z_news` > 3 in any 15-min block since 09:30 | Discrete news shock |

**Point-in-time rules:** only data published before τ is used. Hourly pageviews enter only after the hour completes plus a 15-min publication buffer. GDELT enters with its publication timestamp, not the event time.

**Integration:**
- **Creation model (Stage C3):** `ΔCreate_hat = C2 + d1·att_level + d2·att_accel + d3·att_breadth` (+ `d4·lev_share` if available).
- **Hedging split:** replace `stress` with `stress + g1·att_accel` in the h function (g1 ≥ 0). Viral surges are when market makers are most likely to fall behind.
- Expected signs (reported, not constrained): d1–d4 > 0 in the direction of retail interest. The **direction** of retail flow is taken from the recent price move (retail buys dips in long funds and chases spikes in inverse funds), consistent with the C1 terms. The detector scales the size, not the sign.

**Regime-break reference cases:** USO in April–May 2020 (creation restrictions) falls inside the sample. Those dates are flagged: included in the primary analysis, excluded in robustness (decision D13). UNG in 2009 (creation suspension and prolonged premium) predates the sample and is reviewed qualitatively only, as a sanity check on the mechanism.

### P9 — Non-US leveraged commodity ETPs (computable formula, swap-routed)

**Computability verdict:** the *required* rebalance is computable with the P1 formula, but it reaches CME through swap providers, so it takes the P2 treatment (netting). Two product-specific complications apply.

```
L_eff,f[t]  = effective leverage on day t
              BetaPro: from published notional exposure ÷ NAV where available; else stated L with a flag (decision D19)
              WisdomTree: stated ±3
ΔH_f        = AUM_f,USD[t−1] × L_eff,f × (L_eff,f − 1) × r_idx,f[t, τ]
Q9          = Σ_f ΔH_f × (1 − n9) / (multiplier × P_held)
```

- `AUM_f,USD` uses the FX rate (CAD, EUR, GBP) at the prior day's settlement, point-in-time.
- `r_idx,f` uses the product's **own index contract month**: front month for BetaPro, 2nd-front month for WisdomTree NG. Flow is mapped to that month (consistent with D2).
- `n9` = netting fraction for these swap providers, estimated separately from P2's `n` (different banks, different books).

**Restrike events (WisdomTree 3× products):** if the product's intraday value falls by the threshold (20%), the swap resets exposure intraday. For a ±3× product this corresponds to an adverse underlying move of about 6.67% from the prior reset. At that moment the forced rebalance ΔH is executed **intraday**, not at settlement, and the settlement-window flow is recomputed from the restrike level.
- Restrike times are computable from futures prices and the product terms.
- They're logged as `restrike_events.csv` with timestamp, product and estimated ΔH.
- Restrike events are also candidate t0 triggers for the shock classifier (Section 17).

**Why it's worth including despite the small size:** the scaling factor L(L−1) is 6 for a +3× product and 12 for a −3× product, versus 2 and 6 for ±2× funds, so small AUM punches above its weight on big-move days.

### P5 — TAS liquidity providers (observable proxy)

```
TAS_imb[t, τ] = Σ aggressor-signed TAS volume from session open to τ     (+ = clients bought TAS)
Q5 = + TAS_imb[t, τ]
```

Liquidity providers who sold TAS must **buy** in the window. Units are converted to contracts of the traded month.

### P6 — Commercial hedgers (residual)

```
Q6 = TAS_imb − predicted TAS component attributable to funds (if funds use TAS; see Q2 in Section 16)
```

If funds are found **not** to use TAS, then Q6 = Q5 and P5/P6 collapse into one term (decision D4).

### P7 — HFTs / liquidity

Not a flow term. Enters through the impact model (Section 5.3): window volume and depth.

### P8 — Rolls

#### P8a — Fund-level rolls (computable)

Every tracked fund (US: BOIL, KOLD, UCO, SCO, UNG, USO; plus P9 products where schedules can be sourced) moves its position from one contract month to the next on a **published schedule**. Holdings are recorded daily (13A.3), so roll flows are computable per contract month.

**Schedule sources (per fund, recorded in `SOURCES.md`):**
- **UNG (verified from SEC filings):** rolls from the near month to the next month over a **four-day period beginning two weeks before the near month's expiration**. The benchmark moves 25% per day (75/25, 50/50, 25/75, then 100% next month). The issuer publishes a CSV of anticipated roll dates, subject to change.
- **USO, BOIL, KOLD, UCO, SCO, P9 products:** to source from each prospectus or index methodology (Q19). Do not assume.

**Flow on roll day d for fund f:**
```
φ_f,d        = fraction of the position rolled on day d (from the schedule; Σ_d φ = 1)
N_old,f      = contracts held in the expiring month at the start of the roll period (from holdings)
Sell_old     = − φ_f,d × N_old,f × sign(L_f)                        (contracts, expiring month)
Buy_new      = + φ_f,d × N_old,f × sign(L_f) × (P_old / P_new)      (contracts, next month, notional-matched)
```

- Inverse funds (L < 0) are short, so their roll **buys** the expiring month and **sells** the next. The sign(L) term handles this.
- Each contract month's ledger receives its own P8a flow. Roll flow is roughly **net-zero in notional across months but strongly directional per month**, so it mainly moves the **calendar spread**.
- **Backtest reconstruction:** where historical roll-date lists aren't available, reconstruct from the prospectus rule. **Validate** by checking that recorded holdings changes across the roll period match the computed φ (unit test 39). Any fund whose reconstruction fails validation falls back to P8b treatment.
- **Execution time:** assumed at settlement (via TAS or in the window) unless the fund discloses otherwise (Q20).

#### P8b — Other index-tracker rolls (scaled flag)

For index trackers not individually modelled (broad commodity index funds and swaps):

```
Q8b = roll_flag[t] × roll_fraction[t] × β8
```

- `β8` = a single scale parameter, estimated (tracker AUM is too uncertain to compute directly). The sign follows the roll direction for each contract month.
- P8b must exclude any fund already counted in P8a.

---

## 5. Aggregation, update and predicted move

### 5.1 Prior (ledger) at τ

```
μ_total = Σ active Q_i
σ²_total = Σ var_Q_i      (independence assumed; decision D5)
```

### 5.2 Update with observed pre-window flow

```
z = S_pre[t, τ] − S_norm[τ]
```

`S_pre` is the aggressor-signed outright volume in the traded contract from 13:30 ET to τ. `S_norm` is its trailing 20-day mean for the same interval.

Measurement model: `z = p × Q_total + ε`, with `ε ~ N(0, R)`.

- `p` = pre-absorption fraction (the share of total flow executed before τ). **Latent.**
- `R` = measurement noise variance. **Estimated.**

Scalar update:
```
K     = p σ²_total / (p² σ²_total + R)
Q_hat = μ_total + K (z − p μ_total)
σ²_post = (1 − K p) σ²_total
Q_rem = (1 − p) × Q_hat
σ_rem = (1 − p) × sqrt(σ²_post)
```

### 5.3 Predicted move

```
V_d  = 20-day trailing mean daily volume of the traded contract (days t−20 … t−1)
σ_d  = 20-day trailing daily return std
I    = Y × σ_d × sqrt(|Q_rem| / V_d) × P × sign(Q_rem)       (price units)
SNR  = |Q_rem| / σ_rem
```

**Y = 0.7, fixed** (decision D6).

---

## 6. Staged build (each stage adds participants)

| Stage | Active terms | New parameters |
|---|---|---|
| A | P1 only, no update (K = 0, p = 0) | none |
| B | P1 plus update step | p, R |
| C1 | + P3/P4 baseline creation model (no hedging split, h = 0) | a0…a3 |
| C2 | P3/P4 premium model + hedging split | b1…b4, h0, h1 |
| C3 | + news/virality detector (P3.7) in the creation model and h | d1…d3 (d4 optional), g1 |
| D | + P5 (TAS proxy) | none |
| E | + P2 | n |
| F | + P6 split (only if funds use TAS), + P8a computed fund rolls, + P8b tracker-roll flag | β8 (P8b only) |
| G | + P9 non-US leveraged ETPs (with restrike adjustment) | n9 |
| H | Depth-based impact I_D (8A.4), judged by H14 | none (fixed Y, fixed exponent) |
| I | Large-lot measurement split in update step (8A.5) | p_L, R_L |

**Stage retention rule (pre-registered):** stage k is kept only if, versus stage k−1, **out of sample** it:
1. improves the correlation between predicted `Q_rem` and realised in-window signed flow by **≥ 10% relative**, **and**
2. does not reduce the H2 price-test t-stat.

Otherwise the stage is dropped and later stages build on the last retained stage.

---

## 7. Trading rules

### 7.1 Evaluation times and timing rule

Candidate t0 ∈ {13:50, 14:00, 14:10} ET (for a 14:28 window start; shift if the verified window differs).

**Earliest-pass rule (primary):** evaluate at 13:50. If the trade criteria pass, signal. If not, re-evaluate at 14:00, then 14:10. At most one entry per instrument per day.

**Fixed-time variant (secondary):** t0 = 14:10 only.

### 7.2 Trade criteria

```
|I| ≥ 3 × RT_cost      AND      SNR ≥ 1.5
direction = sign(Q_rem)
```

### 7.3 Entry fill model

- **Primary:** close of bar t0+1, plus 1 tick of adverse slippage (on top of CostStack).
- **Stress:** worst close among bars t0+1 … t0+5.
- **Hard constraint:** the entry must be complete at least 3 minutes before `W_start`. If not, no trade.

### 7.4 Exits (priority order, evaluated each 1-min bar)

1. **Stop:** adverse move ≥ 1.0 × |I| from entry.
2. **Early profit (front-run detection):** favourable move ≥ 1.0 × |I| before `W_start`. Exit, since the flow was front-run.
3. **Flow reversal:** rolling 3-min signed volume against the position exceeds its trailing 20-day 80th percentile for that time of day.
4. **Structural exit (primary):** close of the `W_end` bar.
5. **Hard time stop:** 60 min after entry (never binding under 7.1, but kept as a safety).

**Intra-bar ambiguity:** if the stop and a profit condition are both hit in the same bar, assume the stop.

### 7.5 Post-window fade (diagnostic, separate)

The return from the `W_end` bar close to +30 min, in the **opposite** direction to the predicted flow. Reported only. It measures transient impact and is not part of the primary strategy.

### 7.6 Sizing

- **Hypothesis tests (H1–H6):** fixed 1 contract.
- **Sizing test (H7):** `n = clip(round(κ × (|I| − RT_cost) / σ²_I), 1, N_max)` with κ chosen so that the median trade is 1 contract, where σ_I is the impact uncertainty propagated from σ_rem. `N_max` and the daily loss cap come from prop constraints (Q5).

---

## 8. Parameter estimation

- Latent and fitted parameters (`p, R, n, n9, a0…a3, b1…b4, h0, h1, d1…d4, g1, β8`) are estimated **only** within walk-forward training windows (Section 10).
- Method: maximum likelihood or least squares against **realised in-window signed flow**, never against price returns. This keeps the flow model and the price test separate (decision D7).
- Constraints: p, n, n9 ∈ [0, 1]; R > 0; h1 ≥ 0; g1 ≥ 0.
- The creation model (C1/C2) is fitted to `ΔCreate` (share changes); h0, h1 are fitted to window flow. Neither is fitted to price.
- Report parameter paths across walk-forward windows. Unstable parameters (e.g. p swinging across its full range) are a red flag, noted in the report.

---

## 8A. Error budget and auxiliary calibration (v1.6)

### 8A.1 Error budget

After each stage is evaluated, decompose the out-of-sample window-flow forecast error `e = S_win,realised − Q_rem,predicted`:
1. **Leave-one-term-out:** the change in OOS mean squared error when each active participant term is removed.
2. **Term-level checks where a measurable counterpart exists:** e.g. predicted creations vs realised ΔShares; predicted swap-routed exposure vs the COT-implied change (8A.2); predicted roll flow vs holdings changes.

Output: `results/settlement_flow/ERROR_BUDGET.md`, ranking terms by attributable error.
**Use:** among *not-yet-run* stages, the order may be changed to target the largest attributable error first. The reordering decision is logged in the doc's decision log **before** the next stage runs. No new, unregistered stage can be added this way.

### 8A.2 Swap-dealer auxiliary calibration (netting)

Weekly, for NG and CL (all months, futures-equivalent contracts):
```
ΔSD_w  = change in CFTC swap-dealer net position, week w
ΔSX_w  = predicted change in swap-routed client exposure in the same week
         = Σ US funds' (1 − f_fut) exposure changes + Σ P9 exposure changes
Fit:  ΔSD_w = λ × ΔSX_w + ε_w,        λ ∈ [0, 1] ≈ 1 − (netting fraction)
```
- λ̂ and its standard error act as an **informative prior** on (1 − n) and (1 − n9) when fitting on window flow (Section 8).
- **Consistency check:** if the flow-fitted n differs from 1 − λ̂ by more than 2 combined standard errors, flag it in the report. Neither estimate overrides the other automatically.
- Swap dealers also hedge unrelated client books, so λ is expected to be noisy. That's why it's used as a prior, not as a replacement.

### 8A.3 Swap timing (diagnostic, H15)

From public swap dissemination, identify swaps referencing NG or crude futures or commodity indices. Aggregate by day and time of dissemination. Test whether dissemination clusters in the hours before W_start on days with large predicted P2/P9 flow. If informative, a later doc edit may add it as a measurement in the update step (5.2).

### 8A.4 Depth-based impact (Stage H)

From MBO data at t0, measure resting depth `D(t0)` within ±5 ticks on both sides of the traded contract, and its trailing 20-day same-time median `D̄`.
```
I_D = Y × σ_d × sqrt(|Q_rem| / V_d) × P × sqrt(D̄ / D(t0)) × sign(Q_rem)       (Y = 0.7 fixed; exponent 0.5 fixed)
```
No new fitted parameters. The existing impact definition (5.3) remains the baseline. Stage H replaces it **only** if H14 passes.
Diagnostic (reported only): depth imbalance at t0 = (bid depth − ask depth) / (bid depth + ask depth).

### 8A.5 Large-lot measurement split (Stage I)

In the update step (5.2), split observed pre-window flow into large-lot and small-lot parts:
- Large-lot threshold `L_min` = the 90th percentile trade size of that contract over the trailing 20 days (prior days only).
- Measurement model uses the large-lot flow only: `z_L = p_L × Q_total + ε_L` (parameters p_L, R_L).
- Stage I is judged by the existing retention rule (Section 6).

### 8A.6 Posterior-uncertainty sizing (clarification)

H7 sizing already scales with edge divided by variance. When Stage H is adopted, the impact uncertainty σ_I includes both the posterior flow uncertainty σ_rem **and** depth-measurement uncertainty.

## 9. Tests

Two frames, as standard:
- **Signal frame (path-invariant):** flow prediction, event-study curves, fixed-time exits.
- **Book frame (path-variant):** full rules, costs, fills, sizing, prop constraints.

Standard errors are clustered by day. Confidence intervals use a day-level block bootstrap.

### Gate 0 — Data and facts
All Section 3.2 facts sourced; holdings and AUM point-in-time; settlement windows verified with effective dates; TAS data available (or P5/P6 formally disabled). **Fail → STOP** (or proceed with only the stages the available data supports, documented).

### H1 — Flow prediction (Stage A first)
Predicted `Q_rem` explains realised in-window signed flow (W_start to W_end, minus its trailing norm).
- **Pass:** slope > 0 with clustered t ≥ 2, per instrument, for Stage A. Later stages are judged by the retention rule (Section 6).

### H2 — Price effect (core)
Signed return from the t0+1 fill to the `W_end` close, in `direction`, on traded days.
- **Pass:** mean > 0 and ≥ 1× RT cost, with clustered t ≥ 2 after **Holm-Bonferroni across the 2 instruments**, using the best retained stage.

### H3 — Dose-response
Across quintiles of |I| (all days), the mean signed return rises.
- **Pass:** Spearman ρ > 0 with at most one inversion.

### H4 — Timing (the execution constraint)
Event-study curve from t0 to W_end + 30 min, by quintile of |I|.
- **Pass:** at most 50% of the move to `W_end` is realised by t0+5; delay cost reported.

### H5 — Placebos
- **Time placebo:** the same ledger computed at 11:30 and applied to 11:50–12:20 (no settlement). Must show |t| < 2.
- **Day shuffle:** predicted `Q_rem` randomly reassigned across days within instrument-year (1,000 permutations). The observed H2 statistic must exceed the 95th percentile.

### H6 — AUM scaling
The yearly effect size vs yearly mean aggregate 2× fund AUM. Expected positive, or at least not negative. Reported with the table regardless.

### H7 — Sizing
Book frame: edge-scaled sizing vs fixed 1 contract.
- **Pass:** better out-of-sample Sharpe **and** no worse maximum drawdown relative to prop limits. Otherwise use fixed sizing.

### H8 — Where does creation flow land? (diagnostic)
- **(a) Intraday:** `sv_etf` in each minute predicts aggressor-signed futures flow in the held contract over the same minute to +5 min. Report the slope and clustered t per fund.
- **(b) Window:** C2 retention (Section 6) shows whether predicted creations improve window-flow prediction.
- **Interpretation:** (a) strong and (b) weak means h ≈ 1 and creation flow is intraday. This is recorded as a candidate for a separate intraday doc (Section 17), and **not traded in v1**.

### H9 — Stress and impact (diagnostic)
Realised window price move per unit realised window signed flow, top vs bottom tercile of `stress`. Report the ratio with a bootstrap CI. Adoption into the impact model happens only via a v2 doc edit.

### H10 — Crowding reversal (diagnostic)
On days with `stress` > 2, the next-day settlement-to-settlement return in the direction **opposite** to sign(prem_twa). Report the mean, clustered t and count. Not traded in v1.

### H11 — Attention leads retail flow (diagnostic, gates C3)
- **(a)** `att_level` and `att_accel` at τ predict **ETF signed volume** (`sv_etf`) over the next 60 min, and `ΔCreate` over the next 0–2 days. Report slopes and clustered t per fund.
- **(b)** Lead-lag check: attention must **lead** retail flow. The reverse regression (flow at τ predicting attention at τ+1h) is reported. If attention only lags flow, it's an echo, not a leading signal.
- **Gate for C3:** Stage C3 is attempted only if (a) is significant for at least one fund (t ≥ 2) **and** (b) shows attention leading. Otherwise C3 is skipped and documented.

### H12 — Restrike flow (diagnostic)
On days with a computed WisdomTree 3× restrike, aggressor-signed futures flow in the relevant contract month over the restrike minute to +10 min, versus the same interval on matched non-restrike days with similar returns. Report the difference with a bootstrap CI. Not traded in v1.

### H13 — Roll flow and calendar spreads (diagnostic)
On P8a roll days, the computed net roll flow (expiring month minus next month, in contracts, all funds) vs the calendar-spread change (near minus next) from t0 to W_end. Report the slope and clustered t for NG and CL. Not traded in v1. A spread-trading variant is a v2 candidate (Section 17).

### H14 — Depth-based impact (gates Stage H)
Out of sample, compare the mean absolute error of |I| (5.3) vs |I_D| (8A.4) against the realised |move| from entry to W_end.
- **Pass (adopt Stage H):** |I_D| has ≥ 10% lower MAE **and** replacing I with I_D does not reduce the H2 t-stat.

### H15 — Swap timing (diagnostic)
The share of NG/crude-linked swap dissemination in the 3 hours before W_start, on top-quintile vs bottom-quintile predicted P2+P9 days. Report the difference with a bootstrap CI.

### Book frame (Gate 3)
Full rules with the primary fill and 1× cost.
- **Pass:** positive net mean and positive net Sharpe out of sample. Also report the stress fill, 2× cost, and the post-window fade diagnostic.

### Robustness (report, do not re-select)
With and without flagged days; earliest-pass vs fixed 14:10; stress fill; 2× cost; by year; NG vs CL separately; c_AP at 0.05% and 0.20%; with and without USO April–May 2020.

---

## 9A. Power analysis and minimum detectable effects (v1.7)

**Formulas (planning, pre-registered):**
```
Flow / correlation tests:   SE ≈ 1 / sqrt(n_eff)
Price tests:                SE = σ_trade / sqrt(n_eff)
Minimum detectable effect:  MDE_t2 ≈ 2 × SE   (significance at t = 2)
                            MDE_80 ≈ 2.8 × SE (80% power at t = 2)
Clustering (design effect): n_eff = n / (1 + (m − 1) × ρ)
                            m = observations per cluster; ρ = within-cluster correlation (estimated from the data)
```

### 9A.1 Planning table (estimates; recomputed on real data before each stage)

| Stage / participant | Test | Planned n_eff | Planned SE | MDE (t = 2) | Class |
|---|---|---|---|---|---|
| A: P1 rebalance | Flow (all days, NG+CL) | ~5,000 | 0.014 | 0.028 corr | Individually testable |
| A: P1 rebalance | Price (trade days, ~30% filter) | ~1,500 | 0.026σ | 0.05σ | Individually testable |
| D: P5/P6 TAS | Flow (if TAS history) | ~5,000 | 0.014 | 0.028 corr | Individually testable |
| C1/C2: P3/P4 creations | Forecast vs ΔShares, per fund | ~2,500 | 0.020 | 0.040 corr | Individually testable |
| C3: attention (continuous, H11a) | Attention vs ETF signed volume, day-clustered | ~2,500 per fund | 0.020 | 0.040 corr | Individually testable |
| C3: attention spikes only | Event-conditional | ~125 per instrument | ~0.09 | ~0.18 | Marginal → 9B |
| F: P8a fund rolls | Flow on roll days | ~1,200 | 0.029 | 0.058 corr | Individually testable |
| H13 spreads | Roll flow vs spread change | ~1,200 | 0.029 | 0.058 corr | Individually testable |
| E: P2 netting (COT prior) | Weekly swap-dealer fit | ~520 weeks (history only) / ~24 forward | 0.044 / ~0.20 | 0.09 / ~0.41 | Latent → 9B |
| G: P9 non-US ETPs | Marginal flow | ~240 (forward, pooled) | ~0.065 | ~0.13 | Not individually testable → 9B |
| H12 restrikes | Event study | ~90 (if history) | ~0.11 | ~0.21 | Marginal → 9B |
| Pre-absorption p, hedged fraction h | Parameters | — | — | — | Not a flow source → 9B |
| Forward-only stage (any) | Flow, 120 days, NG+CL | ~240 | 0.065 | 0.13 corr | Usually underpowered |

Illustrative price scale (assumptions, to be replaced by measured values): 35-minute σ about 1.1% (NG near $3) and 0.66% (CL near $90), so the P1 price-test MDE is about 6 bp (NG) and 3 bp (CL).

### 9A.2 Rules

1. **Before each stage runs**, compute the real n_eff (with the design effect from observed within-cluster correlation), SE and MDE, and record them in `results/settlement_flow/POWER.md`.
2. **Plausible-effect statement:** for each stage, record *before* running it the smallest effect that would matter for trading (default: the partial correlation needed to move the H2 statistic by ≥ 0.5, or an MDE at or below round-trip cost for price tests).
3. **Underpowered stage:** if MDE_t2 > the plausible effect, the stage is labelled **underpowered**. It may not be adopted on an individual significance test. It is evaluated under Section 9B instead.
4. **Marginal contribution:** every individual flow test is run as a **marginal** contribution in one regression that includes all currently retained terms, with HAC/clustered SEs. Report each term's variance inflation factor (VIF). A term with VIF > 5 is flagged as confounded (P1 and P3/P4 share the day's return as a driver; P8a and P8b partly share roll days).
5. **No significance claims from underpowered tests,** in either direction. A non-significant result from an underpowered test is recorded as "inconclusive", not "no effect".

---

## 9B. Validation for participants that can't be tested individually (v1.7)

### 9B.1 Toolkit

| Method | What it answers | Used for |
|---|---|---|
| **Mechanism-chain test** | Test an earlier link in the chain where data is plentiful | Attention spikes |
| **Parameter recovery simulation** | Can our estimator find this parameter at our real sample size? | p, h, n, n9 |
| **Decision-relevance test** | Does including the term, or moving its parameter across its plausible range, change trade decisions? | P2, P9, p, h |
| **Hierarchical pooling (shrinkage)** | Borrow strength from a related, better-measured parameter | n9 pooled towards n |
| **Calibration check** | Is the realised size consistent with the prediction, rather than significantly non-zero? | Restrikes |
| **Contractual application** | Apply mechanics that are true by contract, without testing them as alpha | Restrike timing adjustment |

### 9B.2 Per-participant procedures

**Attention spikes (C3 event-conditional)**
- Rely on the continuous attention test (H11a), which is well powered (SE ≈ 0.02). Spike-only analysis is descriptive.
- C3 adoption uses the ledger retention rule (total improvement), never a spike-conditional significance test.

**P2 bank netting (latent)**
- **Parameter recovery:** simulate 200 datasets at the real n with true n ∈ {0.2, 0.5, 0.8}. The estimator is **identifiable** if it recovers the true value within ±0.15 in ≥ 80% of simulations.
- **If identifiable:** fit as specified (with the COT prior, 8A.2).
- **If not identifiable:** fix n at the COT-implied value (or 0.5 if COT is unavailable), and run the decision-relevance test across n ∈ [0, 1].
- **Decision relevance:** share of trade decisions (take/skip or direction) that change across the range. If < 5%, n is **immaterial** and stays fixed. If ≥ 5%, trading on days where the decision depends on n is **excluded** until the parameter is identifiable.

**P9 non-US ETPs**
- **Scale check first:** compute P9's forecast variance as a share of P1's. If < 5%, P9 is immaterial and excluded (simplest model wins, D1).
- **Otherwise:** n9 is **pooled** towards n (hierarchical prior: n9 ~ N(n, 0.15²)), so P9 adds no free parameter. Adoption uses the retention rule (total improvement) plus the decision-relevance test.
- No individual significance test for P9.

**Restrike events (H12)**
- **Always apply the contractual timing adjustment** (removing the reset flow from the settlement window). It follows from product terms, not from a statistical claim.
- **Calibration check** instead of significance: pooled across products, the ratio of realised to predicted flow in the restrike window should have a 90% CI overlapping [0.5, 2], with positive sign in ≥ 2/3 of events.
- **Restrikes are never traded in v1.** Failing calibration only means the timing adjustment is kept but no weight is given to restrike flow magnitude.

**Pre-absorption p and hedged fraction h (parameters)**
- **Parameter recovery** as for P2, with true values p ∈ {0.2, 0.5, 0.8} and h ∈ {0.3, 0.6, 0.9}.
- **If not identifiable:** fix p = 0.5 and h at its logistic midpoint (h0 only, h1 = 0), and run decision relevance. The same 5% rule applies.
- Report **parameter stability** across walk-forward windows. Parameters that swing across more than half their range are treated as not identifiable.

### 9B.3 Reporting

Each participant's outcome is recorded in `POWER.md` as one of: **tested individually (pass/fail)**, **underpowered → validated by [method] (pass/fail)**, **immaterial (excluded or fixed)**, or **contractual (applied, not traded)**.

## 10. Walk-forward

- train_bars = 252 trading days, test_bars = 63, rolling.
- Train: estimate the Section 8 parameters and apply the stage retention rule, where retention decisions use **only** train-window cross-validation or earlier OOS blocks, never the current test block.
- Test: apply unchanged.
- Report concatenated OOS results, the overfitting ratio (IS vs OOS Sharpe), and parameter stability.

---

## 11. Multiplicity accounting

- Primary inference: Holm-Bonferroni over 2 instruments for H2.
- Every configuration (stage, timing variant, fill model, cost multiplier, filter) is logged in `trials.csv`: `trial_id, timestamp, instrument, stage, timing_rule, t0, fill_model, cost_mult, flag_filter, sizing, n_trades, flow_corr_oos, mean_gross, mean_net, t_clustered, sharpe_net, notes`.
- Final Sharpe is reported with a **Deflated Sharpe Ratio** using the total trial count.

---

## 12. Required unit tests

1. `Q1` for L = +2, AUM = 1e9, r = 0.05, f_fut = 1 gives +1e8 notional before contract conversion. L = −2 gives +3e8 (the same sign as the move).
2. L = +1 funds contribute zero rebalance flow.
3. `f_fut = 0` routes all rebalance to P2; `f_fut = 1` routes all to P1.
4. `lag_c = 1`: Q3_known uses ΔShares from t−1 and no forecast term; `lag_c = 0`: the forecast term only.
5. Update step: with p = 0 the posterior equals the prior and Q_rem = μ_total; with R → ∞, K → 0.
6. Update step: a known synthetic case (μ = 100, σ² = 400, p = 0.5, R = 100, z = 60) matches hand-calculated K, Q_hat, Q_rem.
7. Impact: sign follows Q_rem; zero Q_rem gives zero I.
8. No look-ahead: V_d, σ_d, S_norm and the fund data used on day t exclude data from day t onward (fund data respects `published_at`).
9. Earliest-pass rule: signals at the first passing t0 and never re-enters.
10. Entry constraint: an entry that would complete less than 3 min before W_start is rejected.
11. Intra-bar pessimism: a bar spanning the stop and a profit exit records the stop.
12. Contract mapping: flow is attributed to the held contract months per holdings, not the front month by default.
13. DST: W_start/W_end and the t0 grid map correctly to UTC in both transition weeks.
14. iNAV with zero futures move equals NAV[t−1] × (1 + accruals); with L = 2 and r = +1% it rises about 2%; with L = −2 it falls about 2%.
15. Premium uses the NBBO midpoint: a synthetic series with trades at the ask but a constant mid shows zero premium.
16. Stale-minute exclusion: an ETF quote not updated for more than 60 s, or a futures minute with no trade, is excluded from all features.
17. No premium feature uses any minute at or after W_start.
18. h is in (0, 1) and non-increasing in stress when h1 ≥ 0.
19. Creation sign: a KOLD (L = −2) creation gives negative Create_flow (the fund sells futures); a BOIL creation gives positive.
20. Gate 0b check reproduces a hand-calculated iNAV-vs-NAV error for a synthetic fund.
21. Attention z-scores on day t use only data from days t−60 … t−1 for the same hour-of-day and day-of-week.
22. Publication-time guard: an hourly pageview for 13:00–14:00 is unavailable at τ = 14:10 and available at τ = 14:15 or later.
23. GDELT items are keyed on publication timestamp; items published after τ are excluded even if their event time is earlier.
24. `att_accel` on a synthetic step increase in attention is positive during the ramp and returns to about zero once the level is flat.
25. Query lists are loaded from `QUERIES.md` and hashed. The hash is stored with every trial in `trials.csv`.
26. P9 formula: a +3× product with AUM $50m and r = +4% gives ΔH = +$12m; a −3× product gives +$24m (same sign as the move).
27. FX conversion uses the rate at the prior settlement, never the current day's.
28. P9 flow is mapped to each product's own index contract month (2nd-front for WisdomTree NG, front for BetaPro).
29. Restrike detection: for a +3× product, a synthetic −6.7% underlying move from the prior reset triggers a restrike; −6.5% doesn't. After a restrike, the settlement ΔH is computed from the restrike level.
30. BetaPro L_eff: when published notional is missing for a day, stated L is used and the day is flagged.
31. Recorder never overwrites: a second fetch on the same day creates a new file; checksums differ only if content differs.
32. Recorder availability: a forward test reading a record uses `fetched_at`, not `published_at`, as the time it became usable.
33. Gap detection flags a missed daily job, and no downstream code fills the gap.
34. Frozen-protocol guard: evaluation code refuses to run if the parameters differ from `FROZEN_<stage>.json`.
35. Implementation shortfall sign: a long filled 2 ticks above the model price records +2 ticks of shortfall; a short filled 2 ticks below records +2.
36. Futility rule: synthetic trade series trigger a stop at N = 100 only when mean < 0 and t < −1.
37. UNG roll fractions: four days at 25% each; cumulative 100%; day 1 starts two weeks before near-month expiration per the rule.
38. Roll sign: a long fund's roll sells the expiring month and buys the next; an inverse fund does the reverse. New-month contracts are scaled by P_old / P_new.
39. Roll validation: synthetic holdings changing by 25% per day across the window pass; holdings that change all on one day fail and trigger the P8b fallback.
40. No double counting: a fund in P8a contributes zero to P8b.
41. COT availability: a weekly record is usable only at or after its Friday release timestamp.
42. The swap-dealer fit constrains λ to [0, 1]; the consistency flag triggers when |n_flow − (1 − λ̂)| > 2 combined SE.
43. The swap-exposure predictor includes only swap-routed exposure (1 − f_fut) and P9, never futures-held exposure.
44. Swap dissemination records are keyed on dissemination time, not execution time, for any predictive use.
45. MBO depth is measured at the t0 bar close within ±5 ticks; D̄ uses prior days only.
46. I_D equals I when D(t0) = D̄.
47. Large-lot threshold uses the trailing 20 prior days only; trades exactly at L_min count as large.
48. Error budget: removing a term with zero forecast contribution changes OOS MSE by zero on synthetic data.
49. Stage reordering: the code refuses to run a reordered stage unless a matching decision-log entry exists.
50. Options open interest by strike is joined point-in-time (the prior day's published values only).
51. Design effect: m = 10 and ρ = 0.1 give n_eff = n / 1.9.
52. MDE calculation: n_eff = 2,500 gives SE = 0.02, MDE_t2 = 0.04, MDE_80 = 0.056.
53. A stage whose MDE exceeds its recorded plausible effect is labelled underpowered, and adoption by individual significance is blocked.
54. Marginal-contribution regression includes all retained terms; VIF > 5 triggers the confounding flag.
55. Parameter recovery harness: on synthetic data with known p, h, n, the estimator's recovery rate is computed and compared with the 80% / ±0.15 rule.
56. Decision-relevance metric: the share of changed take/skip or direction decisions across a parameter range is computed correctly on a synthetic case.
57. P9 scale check: forecast variance share vs P1 computed correctly; below 5% excludes P9.
58. Restrike calibration: realised/predicted ratio CI and sign share computed correctly; restrike trades are never generated.
59. Forward evaluation length: plausible effect 0.1 with 2 instruments gives n_needed = 400 and 200 evaluation days; a plausible effect of 0.05 gives n_needed = 1,600, exceeds the cap, and routes the stage to 9B.
60. The evaluation length in `FROZEN_<stage>.json` can't be changed after evaluation starts (code refuses).
61. Forward consistency test: passes when the forward estimate lies inside the Track 1 90% CI with the same sign; fails otherwise.
62. Track 3 power check: an edge estimate of 0.08σ selects the combined-evidence route; 0.15σ selects the N = 300 efficacy route.
63. `TRACK_MAP.md` validation: every stage has a track, a power class, n_eff, SE, MDE and a plausible-effect statement before it runs.
64. Vault guard: the loader raises on any date from 2025-03-01 to 2026-09-18 unless `FROZEN_VAULT.json` exists and the vault-open flag is set.
65. One-shot vault: a second vault opening for the same model is refused and logged.
66. Programme registry: a family's promotion check uses α = 0.005; registering an eighth to tenth family uses a reserved slot; an eleventh is refused without a doc amendment.
67. Programme DSR: the trial count equals the total rows across all docs' `trials.csv` files.
68. Haircut: sizing and the Track 3 power check use 50% of the walk-forward edge, or the vault estimate if lower.
69. Episode checks: removing the best year and the best 1% of days are computed correctly on synthetic P&L.
70. One-bar-delay rerun shifts every signal by exactly one bar and reports the retained edge fraction.
71. Leak canary: a feature built from bar t+1 is rejected by the static no-future-data check.

---

## 13A. Testing tracks and forward protocol

### 13A.1 Why three tracks

The model has many participants, and not all of them have usable history. Pure backtesting would force approximations for the forward-only parts. Pure paper trading would take years to reach a verdict (one window per day per market; around 150 trades a year at a 30% trade rate) and couldn't reject a dead premise quickly. So:

| Track | Purpose | Starts |
|---|---|---|
| **1. Backtest** | Test every stage that has point-in-time history; kill or confirm the core premise fast | After Gate 0 |
| **2. Forward data recorder** | Capture data with no usable history, from today onward | **Immediately** (Phase 0) |
| **3. Paper / live-small trading** | Validate fills, latency and cost assumptions; later, forward-test stages that lack history | Once the Stage A signal code passes unit tests |

### 13A.2 Stage-to-track mapping

| Stage | Track 1 (backtest) if… | Otherwise |
|---|---|---|
| A | Fund NAV + shares history available (point-in-time) | If holdings history is missing, run **A-lite** with f_fut = 1 (an upper bound on futures flow), flagged; the recorder captures the true f_fut going forward (decision D22) |
| B | Always, given Stage A | — |
| C1 | Shares-outstanding history available | Forward |
| C2 | ETF quote history available (Q8) | Forward |
| C3 | GDELT and Wikipedia parts: always. Social parts: only if Q12 resolves | Social parts forward-only |
| D | TAS history available (Q3) | Forward |
| E | Historical futures/swap split available per fund | Forward |
| F | P8a: if holdings history supports roll validation; else forward. P8b: always. P6 split: follows D | — |
| G | P9 NAV, units and leverage history available (Q14) | Forward |
| H | MBO history available for the sample (Q22) | Forward (recorder captures MBO around windows) |
| I | Always (trade-level data already specified) | — |

Record the final mapping in `results/settlement_flow/TRACK_MAP.md` after Gate 0, before any stage is run.

**(v1.8)** `TRACK_MAP.md` also records, per stage, its **power class** from 9A (individually testable / underpowered → 9B method / immaterial / contractual), the planned n_eff, SE and MDE, and the plausible-effect statement. A stage's track and its power class are decided together, before it runs.

### 13A.3 Track 2: forward data recorder

**Jobs:**

| Job | Frequency | Content |
|---|---|---|
| Fund snapshot | Daily, after each fund's publication | Holdings (contract months, futures vs swap notional), NAV, shares/units outstanding, stated and effective leverage, for all US and P9 products |
| CME settlement | Daily | Settlement prices for all held contract months |
| TAS summary | Daily (plus trade-level if not buying history) | TAS volume, aggressor split, premium ticks |
| ETF quotes | Intraday, 1-min (only if not purchasing history, Q8) | NBBO mid and trades for the six US ETFs |
| Attention | GDELT every 15 min; Wikipedia hourly; social if Q12 resolves | Per 3.3c queries |
| Restrike check | Intraday | Computed restrike events for WisdomTree 3× products, with price evidence |
| CFTC COT (v1.6) | Weekly, after Friday release | Disaggregated positions for NG and CL |
| Swap dissemination (v1.6) | Daily | NG, crude and commodity-index-linked swap records |
| Options OI (v1.6) | Daily | NG and CL options open interest by strike |
| MBO around windows (v1.6, only if not purchasing history) | Daily, 13:30 ET to W_end | Order-level data for traded contract months |

**Storage rules:**
- Save the **raw response** (HTML/CSV/JSON) unmodified, plus a parsed Parquet copy.
- Every record carries `fetched_at` (UTC) and, where the source states it, `published_at`.
- **Never overwrite.** New fetches are new files. Store a checksum per file.
- Gap detection: alert if any daily job misses its window. Log gaps in `data/recorder/GAPS.md`. Gaps are **never** filled with estimates.
- For forward tests, **`fetched_at` is the availability time** (conservative; decision D23).

**Hosting:** an always-on machine or small server with scheduled jobs (Q17). The recorder must survive reboots and log its own health.

### 13A.4 Frozen forward-test protocol (for stages without history)

For each forward-only stage:
1. **Fit window:** the first 60 recorded trading days are used to estimate that stage's parameters. Nothing else.
2. **Freeze:** store parameter values, stage set and code version hash in `results/settlement_flow/FROZEN_<stage>.json`. No refits during evaluation.
3. **Evaluation window:** the next **120 trading days** minimum. Apply the Section 6 retention rule once, at the pre-set end date: flow-prediction improvement ≥ 10% relative, and no reduction in the price-test t-stat.
4. **One look only for adoption.** Peeking is allowed only for data quality, never for results.

For the **trading forward test** (the full retained model in Track 3):
- **Target sample:** N = 300 trades (both instruments combined).
- **Futility looks** at N = 100 and N = 200: stop if the mean net return per trade < 0 **and** t < −1.
- **Efficacy decision only at N = 300:** mean net > 0 with t ≥ 2. Also report the DSR combining the backtest trial count and the forward test.
- No parameter or rule changes during the forward test. Any change restarts the count at N = 0 under a new frozen file.

### 13A.5 Track 3: paper / live-small trading

- **Preferred mode:** live-small (1 micro contract, real account), because real fills are the point. **Fallback:** paper or prop-evaluation simulator, with its fills flagged as simulated (decision D24).
- **Log per trade:** signal time, model-intended fill price (per Section 7.3), order sent time, fill time, actual fill price, exit details.
- **Implementation shortfall** = actual fill − model fill, in ticks, signed against the trade.
- **Latency check:** the distribution of signal-to-fill time must be consistent with the t0+1 … t0+5 assumption. Report the share of fills beyond t0+5.
- **Cost review after 50 trades:** if the mean shortfall exceeds the CostStack slippage assumption by more than 50%, update CostStack via doc edit and **re-run all Track 1 results at the new cost** before continuing.
- Track 3 starts with the Stage A signal (or A-lite) and is upgraded to the best retained stage only at pre-set checkpoints, with each upgrade restarting the trading count (13A.4).

### 13A.6 Promotion to prop evaluation

All of the following:
1. Track 1: Gates 1–3 passed for the retained stages that have history.
2. Track 3: efficacy decision passed at N = 300 (or, if Track 1 alone is strong, N ≥ 100 with no futility trigger **and** the combined DSR is significant; this must be pre-declared in `TRACK_MAP.md`).
3. Implementation shortfall within the (possibly revised) CostStack.
4. Forward drawdown within prop limits (Q5).

### 13A.7 Power and alternative validation across the tracks (v1.8)

**1. Track 1 (backtest).** Every stage follows 9A.2 before it runs: real n_eff, SE, MDE and a plausible-effect statement. Underpowered stages go to their 9B method; they are never adopted on individual significance.

**2. Forward-only stages (13A.4), power-based evaluation length.** Before the fit window starts, compute the evaluation length needed for the stage's MDE to reach its plausible effect:
```
n_needed = (2 / plausible_effect)²            (flow tests, correlation units)
evaluation_days = max(120, n_needed / instruments), capped at 500 trading days
```
- If `n_needed` would exceed the cap, the stage **skips individual forward testing** and goes straight to its 9B method (parameter recovery, decision relevance, pooling or calibration), run on the recorded data.
- The evaluation length is fixed in `FROZEN_<stage>.json` **before** evaluation starts, and not extended afterwards.

**3. Forward consistency test (replaces "independently significant" where underpowered).** For any stage or strategy with a Track 1 estimate, the forward estimate must fall **within the Track 1 90% confidence interval**, and must have the same sign. This checks that the forward data agrees with the backtest, which a small forward sample *can* do, without demanding it prove the effect alone.

**4. Track 3 trading target, power check.** At N = 300 trades, SE ≈ 0.058σ per trade, so the MDE (t = 2) ≈ 0.115σ.
- If the Track 1 edge estimate is **at or above** 0.115σ, the N = 300 efficacy test (13A.4) is the primary promotion route.
- If it's **below** 0.115σ, N = 300 is underpowered. The primary route becomes the combined-evidence option in 13A.6 (point 2), and the forward test acts as a **futility and consistency check** (no futility trigger, forward mean within the Track 1 90% CI).
- Which case applies is decided from the Track 1 results and written into `TRACK_MAP.md` **before** Track 3 counting starts.

**5. 9B outcomes feed the tracks.**
- **Immaterial** terms (decision relevance < 5%) are removed from forward recording priorities (data is still recorded if cheap, but not blocking).
- **Contractual** mechanics (restrike timing) are applied in all tracks, and never traded.
- **Not identifiable** parameters stay fixed across all tracks until parameter recovery passes on a larger sample. Re-running recovery is allowed once per 250 recorded trading days.

### Programme-level false-positive controls (13A.8, v1.9)

These controls sit **on top of** every within-doc rule. They exist because each doc corrects only for its own tests, while the research programme as a whole runs many test families on shared data.

**1. Sealed holdout (the "vault")**
- **Vault period:** 2025-03-01 to 2026-09-18 inclusive (about 18 months), sealed on 2026-09-21, **before any testing in this doc has run**.
- **In-sample period** for everything else (fitting, stage selection, thresholds, label frequencies, power estimates, walk-forward, placebos, robustness): 2016-01-01 to 2025-02-28.
- **One look only.** The vault is opened once per model, after the model has passed every in-sample gate and been frozen (code hash, parameters, retained stages, rules) in `results/settlement_flow/FROZEN_VAULT.json`. The opening is logged with a timestamp. A second opening is refused.
- **Vault pass criteria (pre-registered):** the primary statistic (the H2 signed-return mean in the retained stage) has the **same sign** as in-sample, one-sided **p < 0.10**, **and** net mean > 0 at 1× cost. The vault is a confirmation test, so it's deliberately less strict than the in-sample test, but it can't be skipped.
- **A vault failure means the model is not promoted.** It's written up; it is not re-tuned and retested on the vault.
- **Power impact:** the in-sample period shrinks to about 86% of the full history. For example, the Stage A price test's n_eff falls from about 1,500 to about 1,290, raising the SE by roughly 8% (about 0.028σ). Forward-recorded data from 2026-09-21 onward belongs to Tracks 2 and 3, not to the vault.
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
| 0 | Build and start the forward data recorder (13A.3) | Recorder running; health log clean for 5 consecutive days |
| 0b | Seal the vault (13A.8): data loader blocks 2025-03-01 → 2026-09-18 unless a frozen model and vault-open flag are present; register families in `PROGRAMME_REGISTRY.md` | Loader guard tested; registry written |
| 1 | Source fund facts (Sections 3.1b and 3.2), holdings/AUM history, settlement windows, TAS data check, ETF quote/trade data (3.3b), news and attention data (3.3c); compute iNAV | **Gate 0** and **Gate 0b** |
| 2 | Market data, calendar, flags; ledger P1 and impact; unit tests | Tests pass |
| 2b | Power analysis (9A): real n_eff, SE, MDE and plausible-effect statements for every stage; parameter recovery simulations (9B) | `POWER.md` written before Stage A runs |
| 3 | Stage A (or A-lite): H1 flow, H2 price, H4 timing, H5 placebos. Write `TRACK_MAP.md`. Start Track 3 with the Stage A signal | **Gate 1:** H1 and H2 pass (Stage A) **or** H1 passes and a later stage lifts H2 to a pass. Else STOP → write-up |
| 3b | Error budget on Stage A outputs (8A.1); swap-dealer calibration (8A.2) | `ERROR_BUDGET.md` written |
| 4 | Stages B → G (C1, C2, then C3 if the H11 gate passes) under the retention rule | Retained-stage table |
| 4b | Stages H (via H14) and I (via retention rule); H15 diagnostic; error budget updated after each stage | Retention decisions logged |
| 5 | H3, H6, H8–H12 diagnostics, robustness | **Gate 2:** H5 placebos pass |
| 6 | Book frame, H7 sizing, Monte Carlo | **Gate 3** |
| 7 | Walk-forward and DSR | Track 1 report |
| 8 | Forward-only stages under the frozen protocol (13A.4) as recorded data accumulates | Per-stage adoption decisions |
| 9 | Track 3 trading forward test to N = 300 (futility looks at 100 and 200) | Promotion decision (13A.6) |

---

## 14. Kill conditions

| Condition | Verdict |
|---|---|
| Gate 0: fund holdings/AUM not available point-in-time | Stop. Untestable. |
| Gate 0b fails and can't be resolved | Disable Stage C2 (premium unusable); continue with C1. Document. |
| H1 fails at Stage A (P1 does not predict window flow) | Kill the ledger premise. Write up. |
| H1 passes, H2 fails at all retained stages | "Flow is real but priced/absorbed". Write up. |
| H4 fails (move mostly done by t0+5) | Kill at current latency. |
| Any H5 placebo significant | Kill. The effect is not settlement-specific. |
| Net fails at 1× cost | "Real, not tradable". |
| OOS Sharpe < 0.5 × IS Sharpe | Do not trade. Write up. |
| Forward futility trigger at N = 100 or 200 | Stop the forward test. Write up. |
| Implementation shortfall erases the net edge at the revised cost | "Real, not tradable at this latency". Write up. |
| Forward flow correlation < 0.5 × the backtest value for retained stages | Treat the backtest as overfit or the regime as changed. Stop and review. |
| Vault fails (13A.8) | Not promoted. Write up. No re-tuning against the vault |
| Programme-adjusted p > 0.005 or programme DSR < 0.95 | Not promoted, even if within-doc gates pass |
| Edge negative after removing the best year or best 1% of days | Treat as episode-driven. Not promoted |
| Edge falls below 50% with a one-bar delay | Too fast for your execution, or leaking. Investigate before anything else |
| Leak canary not caught | All results invalid until the pipeline check is fixed |

Every stop writes `results/settlement_flow/REPORT.md` with the verdict, evidence, retained stages, and lessons.

---

## 15. Decision log

| ID | Decision | Rationale |
|---|---|---|
| D1 | Staged build with an OOS retention rule | Errors compound across participants; the simpler model wins unless beaten |
| D2 | Trade the contract month receiving the most predicted flow | Funds may hold non-front months; flow lands where they hold |
| D3 | Current day return as the forecast of the final return | Martingale assumption; its uncertainty is carried in var_Q1 |
| D4 | P5/P6 collapse if funds don't use TAS | Avoids double-counting |
| D5 | Independence of participant errors | Simplicity; revisit if residual correlations are large |
| D6 | Y = 0.7 fixed | Prevents tuning; the SNR gate handles scale |
| D7 | Fit latent parameters to flow, not price | Keeps the price test honest |
| D8 | Earliest-pass timing rule | Uses the ledger to choose timing without look-ahead |
| D9 | Enter ≥ 3 min before the window | Your fill latency; you don't compete inside the window |
| D10 | Premium computed only before W_start | After settlement, NAV references a fixed price while futures keep trading |
| D11 | Hedging split h as a two-parameter function of stress | Captures "market makers can't keep up" with minimal parameters |
| D12 | H8–H10 diagnostic only in v1 | Limits multiplicity; each can be promoted to a v2 hypothesis by doc edit |
| D13 | USO April–May 2020 flagged as a regime break | Creation restrictions broke the normal mechanism; kept in primary, removed in robustness |
| D14 | Self-computed iNAV; official IIV for validation only | Full control of timing and holdings; the official feed may be unavailable historically |
| D15 | Only reproducibly timestamped attention sources in the primary model | Prevents look-ahead from revised or resampled series |
| D16 | Detector scales retail flow size; direction comes from price action | Attention says *how much*, not *which way*; avoids a second noisy sign model |
| D17 | C3 gated on H11 lead-lag | Attention that only echoes flow adds nothing to a forecast |
| D18 | Keyword queries frozen and hashed | Stops query-tweaking from becoming hidden multiplicity |
| D19 | BetaPro effective leverage taken from published notional where available | The stated leverage is "up to 2×" and may be cut at the manager's discretion |
| D20 | P9 routed through a separate netting parameter n9 | Swap providers differ from US fund counterparties; one n would blur them |
| D21 | Restrike events modelled explicitly | They move the forced flow from settlement to a computable intraday time |
| D22 | A-lite (f_fut = 1) allowed if holdings history is missing | Gives an upper-bound test of the core premise now instead of waiting; flagged and superseded by recorded data |
| D23 | `fetched_at` used as availability time in forward tests | Conservative: publication timestamps can be optimistic |
| D24 | Live-small preferred over paper | Real fills are what Track 3 exists to measure |
| D25 | Futility-only interim looks; efficacy only at the final N | Allows stopping a loser early without inflating false positives |
| D26 | Fund rolls computed explicitly (P8a); flag kept only for untracked trackers (P8b) | Holdings and schedules are already recorded; a computed term beats a scaled flag |
| D27 | Roll reconstruction must pass holdings validation | Prospectus rules can be changed "without notice"; recorded holdings are the ground truth |
| D28 | Error budget may reorder not-yet-run stages, never add unregistered ones | Focuses effort on the biggest error without opening a back door to new tests |
| D29 | COT swap-dealer estimate used as a prior on netting, not a replacement | The category mixes many client books; it's informative but noisy |
| D30 | Swap-dissemination timing diagnostic only in v1.6 | Record quality and coverage unknown until inspected |
| D31 | Depth-based impact has no fitted parameters | Avoids tuning the price model; adopted only if it forecasts move size better |
| D32 | Large-lot flow as the measurement in Stage I | Institutional pre-positioning shows up in size; small-lot flow is mostly noise |
| D33 | Historical ETF holdings priced before being bought | Worth it only if it materially shortens the forward-only wait for Stage E |
| D34 | All v1.6 changes additive | Preserves the v1.5 pre-registration intact |
| D35 | Minimum detectable effects computed before each stage | Prevents treating an underpowered null as evidence of no effect |
| D36 | Underpowered stages validated by alternative methods, never adopted on individual significance | Small samples can't confirm small effects |
| D37 | Individual tests run as marginal contributions with VIF checks | P1 and creations share drivers; testing alone would double-attribute |
| D38 | Parameter recovery simulation decides identifiability | If the estimator can't recover a parameter at our n, fitting it only adds noise |
| D39 | Decision-relevance 5% rule for unidentifiable or tiny terms | A term that doesn't change decisions doesn't need estimating |
| D40 | n9 pooled towards n | Removes a free parameter the data can't support |
| D41 | Restrike timing applied contractually; restrikes not traded | The mechanics are certain; the magnitude isn't testable at our sample size |
| D42 | Power class recorded with the track in `TRACK_MAP.md` | Track and test method are one decision, made before running |
| D43 | Forward evaluation length set by power, capped at 500 days | Avoids both hopeless 120-day tests and open-ended waiting |
| D44 | Forward consistency test where independent significance is underpowered | A small forward sample can check agreement even when it can't prove an effect |
| D45 | Track 3 route chosen from the Track 1 edge estimate before counting | Prevents choosing the easier route after seeing forward results |
| D46 | All v1.8 changes additive | Preserves the v1.7 pre-registration intact |
| D47 | Sealed vault, one look per model | The strongest protection against overfitting, only valid if set before testing |
| D48 | Vault test at one-sided p < 0.10 with same sign | A confirmation test on ~18 months can't carry the full burden of proof, but can refute |
| D49 | Programme α split into 10 slots of 0.005 | Corrects for the many test families across docs; leaves room for future models |
| D50 | Programme-level DSR ≥ 0.95 required | Accounts for every trial run anywhere in the programme |
| D51 | 50% haircut on edge for sizing and planning | Survivors are biased upward (winner's curse) |
| D52 | Episode and shared-period checks | Shared 2016–2025 data could make several models look good for the same reasons |
| D53 | One-bar-delay test and leak canary | Look-ahead bugs are the most common source of false positives in practice |

---

## 16. Open questions (owner to resolve)

- **Q1:** CostStack values for the chosen NG/CL contracts.
- **Q2:** Do the funds use TAS for rebalancing? This decides D4.
- **Q3:** Databento TAS symbology and history coverage for NG and CL.
- **Q4:** Creation cut-off and execution lag (`lag_c`) per fund, from each prospectus.
- **Q5:** Prop constraints: N_max, daily loss limit, trailing drawdown, flatten deadline.
- **Q6:** Minimum acceptable sample start date if fund holdings history is incomplete.
- **Q7:** Execution contract for NG: micro vs E-mini vs full. Verify symbol, liquidity and tick value around settlement.
- **Q8:** ETF 1-minute quotes and trades: source, venue coverage and history for all six ETFs.
- **Q9:** Creation unit size and creation fee per fund. Used to refine c_AP.
- **Q10:** Exact NAV strike basis per fund (which futures prices, and at what time).
- **Q11:** Which date the published shares outstanding reflect (order date vs settlement date), per fund.
- **Q12:** Can a timestamped Reddit/StockTwits archive covering the sample be obtained lawfully and within platform terms? If not, the social inputs stay disabled.
- **Q13:** Final keyword and article lists for `QUERIES.md` (owner to approve before Phase 1 completes).
- **Q14:** For each P9 product: daily NAV, units or notes outstanding, and actual exposure/leverage history. Where published, and how far back?
- **Q15:** BetaPro hedge instruments: CME futures directly, or swaps/forwards with counterparties? Does this vary over time?
- **Q16:** WisdomTree 3× products: index valuation time (settlement or other), exact restrike rule wording, and whether the short and crude lines are still listed.
- **Q17:** Recorder hosting: which always-on machine or server, with what backup?
- **Q18:** Track 3 mode: live-small on a personal account, or a prop-evaluation simulator? If simulator, which firm's fill model?
- **Q19:** Roll schedules (dates and daily fractions) for USO, BOIL, KOLD, UCO, SCO and P9 products, from prospectuses and index methodologies.
- **Q20:** Do funds execute rolls at settlement (TAS or in the window) or spread through the day?
- **Q21:** Swap dissemination: which repositories, which fields, how far back, and can records be matched to NG/crude/commodity-index underlyings?
- **Q22:** Databento CME MBO: history start date, cost for the traded NG/CL months around settlement windows.
- **Q23:** Historical ETF holdings vendors: coverage (futures vs swaps, contract months), history, price.
- **Q24:** CFTC report details: confirm the swap-dealer category definitions for NG and CL, and whether futures-and-options combined or futures-only reports are used (pre-register one before fitting).
- **Q25:** Record any earlier analysis (by the owner, in any tool) that touched 2025-03-01 → 2026-09-18 data in NG, CL or related ETFs, so the vault's cleanliness is documented honestly.

---

## 17. Future versions (not built until the v1 verdict)

- Physical bias for P6 (storage, weather and renewables gas-burn model).
- Merge with the shock classifier when a shock occurs in the 13:30–14:10 window.
- Extend to other settlement-window products where 2× funds exist.
- Separate intraday "follow the ETF flow" signal if H8(a) is strong.
- Stress-scaled impact model if H9 is informative; crowding-reversal signal if H10 is informative.
- Creation model upgrades: ETF options activity (retail call/put volume on BOIL/UNG), added under the retention rule.
- **Candidate new participants** (each would be a new stage under the retention rule):
  - **P10:** CTAs and trend followers. Replicated signal flips, executed around settlement.
  - **P11:** NG/CL options dealers. Gamma hedging estimated from CME options open interest by strike, strongest near options expiry.
  - **Commodity index annual reweighting** (BCOM/GSCI): being designed as a separate model and doc.
  - **Calendar-spread variant** of the ledger using P8a roll flows (if H13 is informative).
  - **P12:** expiry-week delivery avoiders. Physically settled contract rolls and liquidations driven by storage constraints (expiry days only).
  - **P6 split:** producers (hedge targets from 10-Q filings) vs consumers and utilities.
