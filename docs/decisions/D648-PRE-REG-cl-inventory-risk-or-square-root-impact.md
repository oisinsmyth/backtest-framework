# D648 PRE-REGISTRATION — the settlement ledger's mechanism on CL: does the move into the settlement follow inventory risk (σ²·Q) or square-root impact (σ·√Q)?

*Drafted 2026-09-28, on the principal's word ("a reasoned mechanism, not just derived from data"; "Run it"). It is
committed alone, before its runner exists (R8). POWER is committed (`66725c8`,
`scripts/ledger_power_theory_cl.py` → `data/ledger_power_theory_cl.json`).*

## 0. Why, and what has already been seen

**The question.** D630 found NG's price moving into the settlement in the leveraged funds' direction ($66 a trade,
t 5.01), reverting afterwards (+$29, t 3.98). Post hoc (today, NG only; the scripts `explore_d630_*.py`), the
realized move was about **0.31 of the ledger's predicted impact |I|**, it varied by year (0.12 in 2023, 0.35 in 2022),
and a projected-profit filter looked useful in-sample. Those are fits on a spent sample. **This record asks a
theory question instead, on data no price test has read.** The two candidate mechanisms have fixed functional forms,
so only a scale is estimated and the discrimination is between theories, not between searched variables.

**The two mechanisms** (q = the funds' predicted rebalance at τ, `q_est`; V_d = the held contracts' mean
whole-session volume over t−20 … t−1; σ_d = the daily return SD; σ_rem = the SD of the return from τ to the
settlement, both the panel's trailing values; P = the held price at τ; M = 1,000 for CL):

| | mechanism | predicted move (dollars per contract) | in σ | in flow share |q|/V_d |
|---|---|---|---|---|
| **SR** | square-root impact of an unannounced metaorder (the ledger's §5.3, |I| = 0.7 × x_SR) | x_SR = σ_d · √(\|q\|/V_d) · P · M | linear | square root |
| **GM** | Grossman–Miller inventory risk: liquidity providers absorb a PREDICTABLE flow and are paid for holding it over the horizon to the settlement, with capacity scaling with volume | x_GM = σ_rem² · (\|q\|/V_d) · P · M | quadratic | linear |

**What the theory predicts, written before any CL price is read:** (i) the move is in the funds' direction (both
forms); (ii) it is temporary and reverts after the settlement (GM explicitly; SR's temporary part); (iii) under GM
the move per unit of flow scales with σ², so it is largest in high-volatility regimes; under SR with σ. T2 tests
(iii). The ledger's own predictor is SR; if GM is supported, the ledger's |I| is the wrong form, and the D630-line's
projected-profit rule should be built on x_GM.

**Read before this record, all disclosed:**
- **CL's predictor side, in full**: the P1 panel, the §7.2 gate, τ\*, the direction, |I|, V_d, σ_d, σ_rem. After A1's
  exclusion (2020-04-01 → 2020-09-16) and complete rows: **1,819 τ\* days, 739 traded**.
- **CL's window volume** (D627, H1a) and **CL's aggressor-signed window flow** (D629, H1: INCONCLUSIVE, Rubin t 1.79).
- **CL's return to 14:28 entered regressions as a CONTROL** (D627 |r|; D629 signed r, and its post hoc "net flow
  leans against the day's return": −42 contracts per +1%, t −3.6). **No statistic of CL's price move after t0 in the
  funds' direction has been computed**, in-sample or in the vault.
- **NG is spent** for this question: D630 and today's post-hoc explorations read NG's moves. The theory above was
  written after those NG results, which is why it is tested on CL.
- **The CL minute-bar builder** (`scripts/build_cl_minute_bars.py`, being built) runs its known-answer checks only
  (bar volumes against the volume panel, as-of prices against `px_1350`). No return is computed.
- **POWER** used pre-sample CL returns (2015-07 → 2017-05-19, the 1-minute fixture's front) and the in-sample
  predictor side only.
- **This is the third test on CL's in-sample with this predictor panel** (D627, D629, D648). D628 read no CL H1
  beyond D627's.

## 1. Sample and trades

- **Days:** NYMEX business days 2017-05-22 → 2025-02-28 on which τ\* is defined and the predictors are complete,
  **excluding A1's 2020-04-01 → 2020-09-16**: 1,819 (the runner re-derives and prints the count). **Traded days:** τ\*
  passes §7.2's gate (`signal_day` = 1): 739.
- **Direction:** sign(q_est) at τ\*. Both funds (UCO, SCO) buy when the held return to τ is positive.
- **The traded contract:** the largest-share held contract at τ\* (`traded_ym`), one full-size CL. In CL's era B the
  flow is spread over three held contracts (about a third each); x_GM and x_SR use the TOTAL q against the TOTAL V_d
  (the panel's definition), which assumes the held contracts move together. Stated, not tested.
- **Entry:** the close of bar t0+1 (13:51 / 14:01 / 14:11), as-of from `px_1350` when the bar has no trade.
  **Exit:** the close of the 14:29 bar, as-of. **Bars:** `data/cl_minute_bars.csv.gz` (Databento one-second bars to
  minutes, start-stamped; the vault's files never opened).
- **Dollars per contract:** g_t = direction × (exit − fill) × 1,000. Net n_t = g_t − **$31.46** (A9.2's CL line,
  $21.46 D508-effective, plus one tick of adverse entry slippage, $10).

## 2. The three tests

**T1, the flow moves CL (D630's H2 on CL).** The mean of g_t over the 739 traded days, day-clustered t (one trade a
day). PASS if all hold:
1. mean g > 0 and **t ≥ 2.2414** (the first Holm step for two instruments, as in D630; the second step, t ≥ 1.96,
   is reported beside and does not gate);
2. **C1, the time placebo:** the ledger at 11:30 (its own gate, direction and contract), fill at the 11:31 bar's
   close, exit at the 12:19 bar's close: **|t| < 2**;
3. **C2, the rotation null:** the day-level signal (traded, direction, t0) rotated circularly within each year by an
   offset in [20, n_year − 20], 1,000 rotations, seed 648, scored against each day's own returns: the observed t must
   beat the p95 by more than 2 bootstrap SEs (D373's rule).
The net mean (> 0 or not) is reported and does not gate T1: T1 is about the mechanism.

**T2, the form.** On **all 1,819 τ\* days** (the theory predicts the move on every day, traded or not):

  g_t = a + b₁·z(x_GM) + b₂·z(x_SR) + b₃·z(|r_τ| / σ_d) + e_t,  Newey–West (Bartlett, 5 lags),

where z(·) standardises over the sample and |r_τ|/σ_d, the day's held return to τ in its own daily SD, is the
**continuation control**: both x grow with the day's move (q ∝ r), so a plain "big moves continue" effect would load
on both (D629's lesson). The classification, fixed:

| t(b₁) ≥ 2 | t(b₂) ≥ 2 | verdict |
|---|---|---|
| yes | no | **GM** |
| no | yes | **SR** |
| yes | yes | **BOTH** |
| no | no | **NEITHER** |

**C3, T2's placebo:** the same regression at 11:30 (the 11:30 row's predictors and control, the 11:31 → 12:19 move).
If the placebo classifies GM, SR or BOTH, T2's verdict is **UNRESOLVED (control)**.

**Reading T2 (from POWER, at NG's pass-through 0.31):** when GM is true, T2 names GM 77% of the time; when SR is
true, it names SR only 33% and NEITHER 59%; on the null it names a form 11% of the time (GM 6%, SR 5%).
**So GM is confirmable and SR is not: a NEITHER is not evidence against SR**, and a GM verdict carries a 6%
false-positive rate at the null and 8% when SR is true.

**T3, the reversal (temporary pressure).** On traded days, the move from the 14:29 close to the 14:59 close AGAINST
the direction: mean > 0 with **t ≥ 2**. Both forms predict a temporary component; GM predicts that the move is
wholly temporary, which T3 cannot separate from SR's temporary part. T3 is reported with the share of T1's mean it
reverses.

## 3. Multiplicity and what this record can and cannot do

- T1 at 2.2414 is stricter than Holm needs after NG's pass. T2 and T3 are mechanism diagnostics at t ≥ 2 each; they
  are not promotion tests and do not enter the programme registry.
- **This record admits nothing.** It does not change the ledger's Gate 1 on CL (D629's H1 stays INCONCLUSIVE), opens
  no vault, and puts nothing in either book. If T2 names GM, the consequence is a proposal, put to the principal: to
  rebuild the NG projected-profit rule on x_GM and register it for the joint vault run (A10).
- The DSR over this record's configurations and the programme-level p are reported.

## 4. Reported beside, never gating (CLAUDE.md's four groups)

- **T1's trade, both sizes:** full CL ($31.46) and **the component line at minimum size, one MCL** (100 bbl; $3 + one
  $1 tick a round trip + $1 slippage = $5): gross and net per trade; Sharpe AND Sortino of the daily P&L over all
  1,819 days, net and gross, with the monthly block-bootstrap SE; exposure; volatility; max drawdown; mean move
  against the cost; breakeven cost. Count, mean, median, win rate, payoff, skew, kurtosis, the three trimmed means.
  By year (profitable years; without the best year), UCO+SCO AUM terciles, CL price terciles, t0, and era A vs B.
  Correlation with ledger components: not computable (no daily series on disk), stated.
- **Traded − untraded:** the same signed move on untraded days, and the difference (D629/D630's control).
- **T2 variants:** with year fixed effects; without the continuation control; x_GM and x_SR each alone (their t and
  the R²); the scale estimates (b per unit x) and the implied pass-through of |I|.
- **NG, beside and labelled spent:** T2 on NG's 1,936 τ\* days (exploratory; NG's moves have been read).
- **The projected-profit rule on CL** (the post-hoc NG idea, point-in-time): the scale from PRIOR traded days only
  (at least 100), projected dollars from x_SR and, separately, from x_GM; trade when the projection ≥ 1.5 × the round
  trip. Reported for both forms and both sizes; it gates nothing.
- **H4's event curve** (t0 → 14:59) and the share of the move to 14:29 made by t0+5.

## 5. POWER (`data/ledger_power_theory_cl.json`)

Noise: CL's pre-sample returns from the t0+1 close to the 14:29 close (2015-07 → 2017-05-19, the 1-minute fixture's
front), standardised by their trailing 20-day SD (kurtosis 1.6–5.0), rescaled by each in-sample day's σ_rem × P × M.
Corr(x_GM, x_SR) = 0.77; with the continuation control 0.26 / 0.29.

| truth (mean effect over all τ\* days) | T1 power | T2 → GM | T2 → SR | T2 → NEITHER |
|---|---|---|---|---|
| null | 0.01 | 0.06 | 0.05 | 0.89 |
| SR, β = 0.2 ($14.6) | 0.43 | 0.07 | 0.14 | 0.80 |
| GM, same mean | 0.58 | 0.52 | 0.04 | 0.44 |
| **SR, β = 0.31 ($22.7; NG's pass-through)** | **0.81** | 0.08 | **0.33** | 0.59 |
| **GM, same mean** | **0.93** | **0.77** | 0.03 | 0.18 |
| SR, β = 0.5 ($36.6) | 0.99 | 0.04 | 0.63 | 0.32 |
| GM, same mean | 1.00 | 0.94 | 0.01 | 0.02 |

Not simulated: the placebos, the rotation, fat tails beyond the pre-sample's, and CL's era-B split.

## 6. The runner and its assertions

- **File:** `scripts/run_theory_cl.py`, with `--selftest`, `--run` (refuses a second run) and `--check`. **Output:**
  `data/ledger_theory_cl.json` with a `REQUIRED_OUTPUTS` guard (T1's mean, t, C1, C2 p50/p95/SE and verdict; T2's
  coefficients, t, classification and C3; T3; n; the §4 groups).
- **Lag audit:** D627's `audit_flow` on the CL panel (NAV and f dated before t; τ\* from `gate_pass`); the fill bar
  starts after t0; no as-of price uses a bar at or after the fill bar's end; V_d's window ends at t−1.
- **Sign audit, in money:** a CL day whose price rises $0.10 after a buy books +$100 gross and +$68.54 net; the same
  rise after a sell books −$100.
- **Right-quantity:** T2's dependent differs from C3's; x_GM differs from x_SR; T1's returns differ from the
  placebo's; the net differs from the gross by exactly $31.46.
- **Classifier audit:** on synthetic data where GM (then SR) is the truth, T2 names it; the audit RAISES when the
  classifier is broken (the columns swapped).
- **Selftest** (no in-sample return after t0): POWER's noise with an injected GM effect → T1 PASS and T2 GM; β = 0 →
  neither; every audit raises on a deliberate break; the analysis runs end to end on synthetic bars before the one
  real run. `-W error::RuntimeWarning`.

## 7. What this does not touch

- No vault data; no NG verdict; no Sierra Chart data (T1–T3 are prices only); D629's CL H1 and the ledger's Gate 1
  on CL are unchanged.
- **Deviations** are listed in the output and never replace a verdict.
