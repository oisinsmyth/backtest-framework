# D639 — PRE-REG: the LETF close-flow model, H1–H5 on NQ and ES (deposit Phases 4–7)

*2026-09-27. The principal: "Yes, do 1 then write the pre-registration". Committed ALONE, before the POWER step and
before any runner exists (R8). **No return of any kind has been computed on this line.** Spec: `LETF_CLOSE_FLOW_PREREG.md`
v1.2 (read-only), with amendments LETF-A1..A6 (`docs/internal/LETF_CLOSE_FLOW_AMENDMENTS.md`). This record fixes every
choice the deposit leaves open; where it and the deposit differ, the deposit wins, unless an amendment says otherwise.*

## 1. Data (built, gated, not yet read for any return)

- **In-sample 2016-01-04 → 2025-02-28** (LETF-A2). The vault (2025-03-01 → 2026-09-18) is scored only in the
  programme's joint run; the forward is Track 2/3.
- **Sessions:** `data/letf/phase2_{NQ,ES}_sessions.csv.gz` (D638), **2,285 usable sessions each** (the 2,303 NYSE days
  less 18 half-days; 59 NYSE-closed CME sessions dropped). Every bar used below is present on every usable session.
- **AUM:** `data/letf/letf_aum_daily.csv.gz` (D637 with its addendum). Gate 0 passes for all ten funds on every row.
  - NDX set = TQQQ (+3), SQQQ (−3), QLD (+2), QID (−2): issuer data throughout.
  - SPX set = UPRO (+3), SPXU (−3), SSO (+2), SDS (−2) (issuer data) plus SPXL (+3), SPXS (−3) (Direxion,
    estimated). Direxion is 39% of the SPX set's L(L−1)A.
- **Volume:** `nq_equiv_volume` / `es_equiv_volume` = the front's full-day volume + the micro's / 10 (D638).
- **Prices:** D462's one-minute RTH bars (front by full-day volume), and `fut_index_anchor_bars` for off-front months.

## 2. The prior reads, disclosed in every result (LETF-A1)

- D530 read 2016-01-04 → 2023-12-29 for this mechanism (reset flow, return-of-day continuation into the close). It found
  no direction: Q5 z ≈ 0.49; equity-index hit rate 50.03%.
- D463 (15:30 → 16:00 momentum, 2010–2023): NQ −0.01, ES −0.29 net Sharpe (ledger K2/K3).
- D487 (ES/NQ continuation, 2016–2023): a 2018/2022 property.
- **So 2016–2023 is not blind for H1/H2.** The verdicts are computed as specified, and every result carries the split
  2016–2023 vs **2024-01-02 → 2025-02-28 (about 290 sessions, which no prior line read)**, reported side by side.

## 3. Definitions, fixed here

| symbol | definition |
|---|---|
| τ | 14:30, 15:00, 15:30 ET (primary); 11:00 for H4 only |
| P(t, τ) | close of the one-minute bar ENDING at τ (the bar labelled τ − 1 min; `bar_label_ending_at`), front contract |
| P(t−1, close) | `p_prev_close_same`: the prior NYSE day's close (the 15:59 bar, or 12:59 after a half-day) of TODAY's contract |
| r[t, τ] | P(t, τ) / P(t−1, close) − 1 (`day_return`) |
| A_i[t−1] | the panel's AUM for the prior NYSE day (`aum_prior`) — issuer AUM for ProShares, the estimate for Direxion |
| Q_usd, Q_contracts | Σ L(L−1)A r over the set (NDX → NQ, SPX → ES); ÷ (multiplier × P(t, τ)), NQ 20, ES 50 |
| V[t] | mean of the 20 prior USABLE sessions' equivalent volume (day t never enters) |
| σ_d[t] | sample std (ddof 1) of the 20 prior usable sessions' daily returns p1600 / p_prev_close_same − 1 |
| q, I | Q_contracts / V; I = 0.7 · σ_d · √|q| · P(t, τ) (index points; Y fixed, D4) |
| RT_cost_points | the repo's default cost line (D508 execution-hours crossing, `data/futures_costs.json`): **MNQ ($3.00 + 2.1342 ticks × $0.50) / $2 = 2.0336 points; MES ($3.00 + 1.1345 ticks × $1.25) / $5 = 0.8836 points** |
| active | I ≥ k · RT_cost_points; k = 3 primary, 2 and 5 sensitivity |
| direction | sign(Q_usd) = sign(r[t, τ]) (every fund's ΔH has the sign of r) |
| entry | the close of the bar LABELLED τ (ending τ + 1 min): one minute after the signal's price |
| exit | the close of the 15:59 bar (16:00) |
| signed return s | direction × (P_exit / P_entry − 1) × 10⁴, in bp; the trade's cost in bp is RT_cost_points / P_entry × 10⁴ |

The one-minute gap between signal and entry is deliberate: the lag audit (§8) proves that nothing at or after the
entry bar enters the signal.

## 4. The tests (deposit §6; family α = 0.05)

**Primary cells:** τ ∈ {14:30, 15:00, 15:30} × {NQ, ES}, k = 3, hold to close. Six cells.

- **H1 (Gate 1, with H4):** on active days, the mean of s > 0.
  - Statistic: a one-sided Newey–West (HAC) t, Bartlett kernel, lag = ⌊4 (n/100)^(2/9)⌋.
  - Holm–Bonferroni over the six cells.
  - **A cell passes if** its Holm-adjusted p < 0.05 **and** its mean gross s exceeds its mean cost in bp (1×).
- **H2 (Gate 2):** on ALL usable days of each H1-passing cell, rank |q| into quintiles and take the mean s per quintile.
  **Pass:** Spearman ρ(quintile rank, mean s) > 0, with at most one inversion.
- **H3 (Gate 2, "not negative"):** per calendar year, β_y is the OLS slope of s on q over all usable days. It is
  compared with the year's mean aggregate L(L−1)A of the set by Spearman ρ, with the exact permutation p over the
  year labels.
  - **Fails only if** ρ < 0 with one-sided p < 0.05.
  - The per-year table is always reported. H3 is directional only (about 9–10 years).
- **H4 (Gate 1):** the identical rule at τ = 11:00 (r and I at 11:00, the same k, instrument and entry convention),
  exiting at the close of the 11:59 bar.
  - **Pass (for the H1 cell's instrument):** |t_HAC| < 2.
  - A significant placebo kills the line as generic intraday momentum.
- **H5 (diagnostic, not traded):** on active days, direction × (the 09:45 open of today's contract on the next NYSE
  day / the exit price − 1). Reported, never gating.

**Gates (deposit §9):**
- **Gate 1** = H1 in ≥ 1 cell AND H4 for that cell's instrument.
- **Gate 2** = H2 AND H3 not negative.
- **Gate 3** = the book frame is net positive at 1× cost; 2× is reported.

A failed gate stops the line and a write-up follows (deposit §11).

## 5. Nulls, reported beside every H1 statistic (CLAUDE.md; not a gate the deposit defines)

For each cell, **the exact circular rotation** of the (direction, active) sequence against the day sequence of τ→close
returns, over all T − 1 offsets of the usable-session series. The group is finite, so it is enumerated and has no
sampling SE. p50, p95 and the observed mean's rank are reported. The rotation keeps each day's return distribution and
the signal's persistence, and breaks only their pairing.

## 6. Robustness (report, never re-select; deposit §6)

- with and without the flagged days: FOMC, CPI, quad witching, index rebalance, quarter-end;
- k = 2 and k = 5; cost 1× and 2×;
- the hold sweep in the signal frame: 5, 10, 15, 30 and 60 minutes, and to-close;
- **ES cells with and without 2017-11-01 → 2019-07-31**, Direxion's quarterly-anchor stretch (LETF-A6: fund-level band
  p95 16%);
- **ES cells with Direxion's AUM set to its measured band edges** (p05 and p95 of the regime's daily error), to show
  whether any verdict moves;
- the 2016–2023 / 2024-01 → 2025-02 split (§2).

## 7. Multiplicity

Every configuration evaluated is one row of `data/letf/trials.csv` (the deposit's `results/` path, translated: this
repository has no root `results/`, D592), with the deposit's §7 columns plus
`reads_2024_plus`. A surviving configuration's Sharpe carries a Deflated Sharpe Ratio on the total trial count. **The
six primary cells are the only inference; everything else is labelled sensitivity.**

## 8. The runner's assertions (CLAUDE.md), each proved to fire on a broken input

1. **Lag audit:** re-derive A[t−1], V[t], σ_d[t] and the signal in a second implementation that never calls
   `backtest_framework.letf.model`. Assert it is equal on every day. Assert that P_entry's bar is strictly after the
   signal's bar.
2. **Sign audit, in money:**
   - a favourable move pays positively, long and short;
   - an inverse fund's ΔH has the sign of r (`rebalance_flow(−3, A, r) > 0` for r > 0).
3. **Right quantity:**
   - the returns scored are τ→close of TODAY's contract, which differs from the continuous-front series on roll days;
   - the AUM used is t−1's, which differs from t's.

## 9. The POWER step (next, before any runner; deposit §6A)

`docs/results/LETF_CLOSE_FLOW_POWER.md` and `data/letf/power.json` give, per primary cell:
- the active-day count;
- n_eff with the HAC design effect;
- SE and MDE (t = 2 and 80% power) in σ units and in bp;
- a plausible-effect statement: the default is the mean cost in bp, as the deposit says.

**It reads only:**
- the flow, V, σ_d and I (the signal's inputs);
- the DISPERSION of the τ→close move (its std, unsigned).

**Never** its mean, and never its sign against the flow. A cell whose MDE exceeds the plausible effect is labelled
underpowered, and a null there is recorded as inconclusive.

## 10. Reporting (CLAUDE.md, all four groups) and the component line

- Net and gross side by side; Sharpe and Sortino together; exposure, vol, max DD, mean move per trade against 2× cost,
  breakeven cost.
- The trade distribution with both-tail trims.
- What the winners depend on: years, flagged days, price level.
- The null distributions (§5).
- **The component line for `docs/COMPONENTS_PROP.md`, whatever the verdict:**
  - net Sharpe at 1 MNQ / 1 MES and the dollar cost the runner computes;
  - hit rate, skew, gross beside net;
  - **correlation with every ledger component**, and in particular K2/K3 (D463's 15:30 → 16:00 momentum). The τ = 15:30
    cell shares their clock and, through sign(Q) = sign(r), their signal.
  - **A τ = 15:30 cell that correlates with K2/K3 above 0.7 is recorded as the same construction, not a new component**
    (CLAUDE.md, "two that share a clock and a signal do not diversify").

## 11. Book frame and walk-forward (Phases 6–7, only if Gates 1–2 pass)

- **Book:** 1 MNQ / 1 MES per trade; one trade per instrument per day.
  - The prop constraints (deposit Q2) are D386's fourteen provider plans through D440's `simulate_provider`, as the
    D493/D630 lifecycle runs.
  - Any plan whose flatten deadline is at or before 15:59 ET is flagged, not silently scored.
  - Monte Carlo: a month-block bootstrap of the best primary cell's equity curve.
- **Walk-forward (deposit §10):** train 252 sessions, test 63, rolling. In each train window choose the (τ, k) with the
  best net mean. Report the concatenated out-of-sample result and the IS/OOS Sharpe ratio. "Do not trade" if the OOS
  Sharpe < 0.5 × IS.

## 12. What is fixed from this commit

Every definition, threshold, lag rule, cost line and test above. **A change is a versioned amendment (LETF-A7 onward),
written before the code that uses it.** Nothing is chosen after a return is seen. The runner is committed after this
record and after the POWER step, and before its one run.
