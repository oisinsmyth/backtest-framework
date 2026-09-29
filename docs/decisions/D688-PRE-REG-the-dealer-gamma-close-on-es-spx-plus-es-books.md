# D688 PRE-REGISTRATION — the dealer-gamma close on ES: does the hedge flow implied by the SPX + ES option books (−Γ × the day's move, square-root scaled) predict the last half-hour?

*Renumbered from D681 to D688 on 2026-09-29 before this branch (`wt/after-d674`) merged main, which holds a different D681. Commit messages and the recorded outputs in `data/` keep the old number.*

*Drafted 2026-09-29, after a formation discussion with the principal (§1). Committed alone, before its runner exists
(R8). **This record reopens the gamma-conditioned close,** which D582 closed "in any variant". The reopen falls under
D582's own clause (a new fixture the record names): SqueezeMetrics' SPX GEX, received 2026-09-28. **No return has been
read for this construction.** Only the GEX series' own distribution and the two books' yearly scale were read (§2).
Numbers written B6xx (B661, B662, B663, B665) are records on the unmerged branch `wt/after-d643`, read with
`git show wt/after-d643:docs/decisions/<file>`.*

## 0. The mechanism

1. **Dealers delta-hedge.** With net gamma Γ ($ of hedge per 1% move), a move of r% since their last hedge requires a
   trade of **−Γ·r** in the underlying.
2. **The sign of Γ sets the direction:**
   - **Short gamma (Γ < 0):** they must buy after rallies and sell after declines. The hedge goes with the move.
   - **Long gamma (Γ > 0):** the hedge goes against the move.
3. **The timing.** Much of the rebalancing lands late in the day: risk is measured on closing positions, the close has
   the deepest liquidity, and short-dated gamma peaks then.
4. **The price effect:** the flow moves the price by the square-root law, `Δp ≈ Y·σ_d·√(|Q|/V)`.

**So the last 30 minutes should follow the hedge flow.** When dealers are short gamma, the close continues the day.
When they are long gamma, it reverts. Both are sized by `√(|Γ·r|/V)`.

**The published anchor:** Baltussen, Da, Lammers and Martens (2021), cited in B661 (the paper is still to be read at
its source): about +6.6 bp in the last 30 minutes per 1% prior move, on negative-gamma days.

**What the record already knows:**
- D463: intraday momentum on ES is small (1.2 bp).
- **D581:** carried **ES-options** gamma, evaluated at 15:30 with a sign split, does not sort the close. The close
  continues its prior hour by about +0.10 in every regime.
- B662 and B663 (at the open): not supported.
- **B665: SPX GEX predicts the SIZE of moves** (t 8–12), beyond volatility.

**What is new here:**
- the SPX book, plus the ES book re-evaluated at the prior close;
- the literature's regime definition;
- a continuous, two-sided, square-root flow prediction;
- the close clock.

## 1. The formation decisions (the principal, 2026-09-29)

| # | decision | the principal's word |
|---|---|---|
| F1 | **The gamma measure is the SUM of SqueezeMetrics SPX GEX and our ES-options book.** Both use the same convention, both are in $ per 1%, and SPX-only and ES-only are reported beside the sum. | "(c)… both (a)+(b) would drive the price action"; agreed with the three conditions |
| F1′ | **The ES book is evaluated at the prior settlement** (the timing SqueezeMetrics uses). D581's 15:30 evaluation is reported beside it. | "Lets go with your recommendation" |
| F2 | **Continuous**, not a regime split, **with an expected-profit filter** whose pass-through is estimated separately for short- and long-gamma days | "(b), with an expectant profit filter… a balance of regime and other factors"; agreed |
| F3 | **The move to hedge** runs from the prior settlement to 15:30 | "(a)" |
| F4 | **The outcome** is 15:30 → 16:00 (primary); 15:50 → 16:00 (secondary) | "(a) primary, (b) secondary" |
| F5 | **The square-root scaling** `sign(Q)·√(\|Q\|/V)` (primary); the raw `−Γ·r` reported | "(b), with (a) reported" |
| F6 | **Controls:** the day's own move (the unconditional continuation), the LETF rebalance flow, and σ₂₀ | "Agreed" |
| F7 | **The placebo:** the same construction at 11:00 → 11:30, plus a clock profile | explained, then accepted |
| F8 | **ES only**, until NDX, QQQ or SPY gamma data exist | "ES only until we can get the other gamma data" |
| F9 | **The trade:** MES from 15:30 to 16:00, with the filter at 2 × the round trip | "Agreed" |
| F10 | **2016–2023 is a test of this new construction** (the per-line rule), not development | "Yes" |

## 2. Step 0 facts (read before drafting)

- **SqueezeMetrics' white paper** (*Gamma Exposure*, 2016, revised 2017):
  - **The convention:** calls are sold by investors and bought by market-makers; puts are bought by investors and sold
    by market-makers. So calls count + and puts −, the same convention as D581's ES book.
  - **Per strike:** Γ·OI·(±100).
  - **The units:** "denominate[d] in dollars", without the move basis.
- **Units, inferred as $ per 1%:**
  - The yearly median |GEX| ($1.7–5.9bn) is the same order as the ES book's ($2.1–6.4bn, $ per 1%).
  - Their ratio does not track 1/SPX (correlation −0.23; 0.77× from 2016 to 2023, against the 0.49× a per-point
    basis implies).
  - This is moderate evidence. **Only the SUM depends on it**, so SPX-only and ES-only are declared, unit-robust
    secondaries.
- **The timing trap:** D581's ES book was evaluated at 15:30 (a same-day expiry has τ = 30 minutes), which inflates it
  (2023: $6.4bn against SPX's $2.6bn). This record re-evaluates it at the prior settlement (F1′).
- **The short-gamma share** (SPX GEX < 0):
  - 12.7% of 2016–23, with 41% of those days in 2022;
  - **1 day in 2024-01 → 2025-02;**
  - 18 in the vault.

  The continuous design (F2) is what makes a confirmation possible at all.

## 3. Data (all on disk; no download)

- **ES prices:** `fut_ES_rth_1m.csv.gz` (D581's; day, hhmm, contract, OHLCV), for P(11:00), P(11:30), P(15:30),
  P(15:50) and P(16:00) as D581 defines them.
  - The prior settlement of the same contract comes from `fut_settle_strip.csv.gz`.
  - Sessions are those with at least 380 bars in `fut_index_sessions` (D581's rule).
- **SPX GEX:** `data/raw/squeezemetrics/DIX.csv`. The row used for session d is **the last row dated strictly before
  d**.
  - Licence: statistics and verdicts only. No per-date series is written to a tracked path, and nothing goes to the
    prop firm. Credit: SqueezeMetrics.
- **ES book:** `fut_es_options_eod.csv.gz` (OI published before 10:00 of session d, i.e. the prior close's OI).
  - It is built with D581's audited functions (`b76_gamma`, `implied_vol`, the moneyness filter |K/F−1| < 0.3, D581's
    expiry filter), imported unchanged.
  - Evaluated at **F = the prior settlement** and **τ = the trading time from the prior settlement to expiry**:
    `G_ES = Σ Γ(F_prev, K, iv, τ_settle) · sign · OI · 50 · F_prev² · 0.01`.
- **V:** the median ES regular-session **dollar volume** (Σ 1-minute volume × $50 × price) over the 20 sessions
  through d−1.
- **σ_d:** the standard deviation of daily ES settlement returns over the 20 sessions through d−1.
- **The LETF control:** D640's loader, Direxion scaling and ES set (UPRO, SPXU, SSO, SDS, SPXL, SPXS), imported from
  `scripts/run_letf_close_flow.py`.
  - `Q_L = Σ AUM_prior · L(L−1) · r`, in the same square-root form.
  - The panel ends 2025-02, so the control covers the whole window.
- **The window:** 2016-01-04 → 2023-12-29. **No row dated on or after 2024-01-01 is read by any loader.** The options
  fixture runs to 2026, and a guard raises if anything later survives.

## 4. The construction

For session d:
- **The move since the last hedge:** `r = log P(15:30) − log S_prev(c)`, in %, on the 15:30 contract c.
- **The hedge flow,** where G is the gamma measure ($ per 1%): `Q = −G · r`. Q > 0 means the dealers buy.
- **The predicted push (F5),** in bp: `Z = σ_d · sign(Q) · √(|Q| / V)`.
- **The outcome:** `R2 = log P(16:00) − log P(15:30)`, in bp.

## 5. The gates

**Gate 1, the mechanism (gross). It passes only if both hold:**

| bar | statistic | passes when |
|---|---|---|
| **G1** | `R2 = a + β_G·Z_SUM + β_r·r + β_L·Z_L + β_σ·σ_d + e`, Newey–West lag 5 | β_G > 0, NW t ≥ 2.0, **and** β_G above the p95 of its enumerated **day-rotation null**: the gamma series G is rotated by k sessions against everything else, for k = 10 … n−10, so the p95's SE is 0 |
| **G2** | the placebo: the same regression at 11:00 → 11:30, with r and Z built to 11:00 | **β_G(close) − β_G(11:00)** above the p95 of that difference under the same rotation |

**Gate 2, tradeability (net, filtered by expected profit).**
- **Position:** 1 MES from P(15:30) to P(16:00), in the sign of Z_SUM.
- **Projected gross:** `π_regime · |Z_SUM|` bp.
  - π_regime is a through-origin pass-through of the signed realised return on |Z|, from **prior sessions only**,
    estimated separately for G_SUM < 0 and G_SUM ≥ 0.
  - It needs a 250-session burn-in, and at least 60 prior observations in the regime; until then the pooled π is used.
- **Trade** when the projected gross in dollars ≥ **2 × the MES round trip**.
- **Passes when:** the net mean per session has NW t ≥ 2 on at least 60 trades. With fewer, it is UNRESOLVED.

**Verdicts:** SUPPORTED (both gates) / MECHANISM ONLY (Gate 1 alone) / NOT SUPPORTED. The filter is promotable only if
Gate 1 passes (the house rule).

## 6. Reported beside (not gated)

- **The measures:** SPX-only; ES-only (prior close); D581's ES book at 15:30; the sum with the raw form `−G·r`.
- **The outcome:** 15:50 → 16:00 (F4 secondary).
- **The clock profile:** β_G in every 30-minute window of the day, with r and Z built to each window's start.
- **The regimes:** β_G within G_SUM < 0 and within G_SUM ≥ 0. The mechanism predicts both positive.
- **Eras:** 2016–21 against 2022–23 (the 0DTE era).
- **The component line and CLAUDE.md's four groups** for the Gate 2 book and for an unfiltered sign(Z) book, at MES
  and full ES:
  - net and gross Sharpe and Sortino, trades a year, hit rate, skew, and trimmed means;
  - per year and era;
  - ρ with the admitted MACD arm (via D667's `load_arm`).
- **Reproduction:** D581's T1 interaction (−0.023) must reproduce from D581's own code before anything else runs.

## 7. Power (computed before the run)

**Per session,** at the square-root table's size (Y 0.5–1, B661's V and σ), the predicted push against the
last half-hour's noise (≈ 22 bp) is about 0.15–0.45 on days with a sizeable |Q|, and near zero on quiet days.

| slice | sessions | expected t at the table's size / at half |
|---|---:|---|
| this record, 2016–2023 | ~1,990 | ~4 / ~2 |
| 2024-01 → 2025-02 (clean for this line; D640 read it for LETF) | ~290 | ~1.5 / ~0.8 |
| + the vault | ~680 | ~2.3 / ~1.2 |

The unread slices are almost all long-gamma, so **they test the reversal half.** If this record passes, confirmation
is declared now: the frozen rule on 2024-01 → 2025-02 plus the vault, in the joint run.

## 8. Predictions (mine, before the run)

1. **β_G > 0, but Gate 1 fails.** Given D581, B662, B663 and B665, I expect gamma's information to be mostly about
   size, not direction.
2. **The SPX-only and sum β_G have the same sign;** ES-only is weaker.
3. **Short-gamma β > long-gamma β:** hedging with the move is more forceful than hedging against it.
4. **The 11:00 placebo's β_G is at least half the close's.** Continuous 0DTE hedging spreads the effect through the
   day, so G2 fails if G1 passes.
5. **β_r > 0:** the unconditional continuation D581 found.
6. **2022–23's β_G exceeds 2016–21's** (0DTE).
7. **If Gate 1 passes, Gate 2 fails:** the push is ~5–10 bp against a ~2 bp round trip, but the filter keeps only large
   |Z| days, and there are few of them.

## 9. Runner assertions and self-test

1. **Lag audit:**
   - G uses only the GEX row strictly before d and OI published before d's 10:00;
   - V and σ_d use only sessions through d−1;
   - r uses only prices up to 15:30;
   - π uses only prior sessions.

   A second path re-derives Z on sampled sessions from inputs filtered by date, never calling the vectorised builder.
2. **Sign audit, in money.** A synthetic day with dealers short gamma and an up move must give Z > 0, a long MES, and a
   positive P&L when the close rises. Inverting the sign must raise.
3. **Right quantity:**
   - the prior-close ES book differs from D581's 15:30 book;
   - R2 is measured from 15:30, not from the 15:00 bar;
   - both are asserted on real data.
4. **Window guard:** raises on any row on or after 2024-01-01, in every loader.
5. **Rotation identity:** k = 0 reproduces the observed β_G exactly.
6. **D581 reproduction:** before anything else.

**Every audit is shown to fire on a broken input.**

**Output:** `data/d688_gamma_close.json`: statistics only, no per-date GEX. Runner:
`scripts/stage0_d688_gamma_close.py`. **Projected wall time:** about 8 minutes, dominated by the ES-book rebuild, as in
D581.
