# D630 PRE-REGISTRATION — H2 on NG: does NG's price move into the settlement in the direction of the leveraged funds' predicted rebalance?

*Drafted 2026-09-26, on the principal's word ("Pre-register H2 on NG"). It is committed alone, before its runner
exists (R8). H2 is the deposit's (§9, line 542), under A1–A9. This record fixes what the deposit leaves open (the
traded contract, the bars, Holm with one instrument tested, the controls, the vault protocol) and nothing else.*

## 0. Where this comes from, and what has already been seen

- **Gate 1** (deposit line 946, as A8 amends it) needs H1 and H2 to pass at Stage A. D629 passed NG's H1 on
  aggressor-signed flow. That pass is **provisional** until the CL/NG check of Sierra's sign after 2026-10-10.
  This record is H2. Its result does not depend on Sierra: H2 reads Databento prices only.
- CL's H1 was INCONCLUSIVE (D629), so H2 runs on NG only. Holm keeps both instruments in the family (§5).
- **D629's warning, carried here:** unconditionally, NG's window flow runs AGAINST the funds' predicted trade
  (t −7.98), and D629's pass is conditional on the return. **A pass of H1 therefore implies no sign for H2.**
  H2 is the direct test of the ledger's trade.

**Read before this record, all disclosed.** No statistic of the price move after t0 in the ledger's direction has
been computed, in-sample or in the vault.
- **The predictor side, in full:** the P1 panel, the §7.2 gate, τ\*, and the direction. On NG's 1,028 traded days
  the direction is + on 50.3%.
- **The price to 14:28 has entered regressions as a CONTROL:** D627 (|r|), D629 (signed r, against flow) and D629's
  post-hoc (window flow against r: t −11.7). The move from the fill to 14:28 is most of H2's return. It has never
  been tabulated against the direction, the gate or Q.
- **σ_rem** (the trailing SD of the return from τ to the settlement) is a gate input. It is a dispersion, unsigned.
- **The minute-bar builder** (`build_ng_minute_bars.py`) ran its known-answer checks only: bar volumes against the
  volume panel (0 mismatches on 58,827 contract-days), and the 13:49 close against `px_1350` (0 of 15,866). No
  return was computed.
- **POWER** (`ledger_power_h2_ng.py`) used pre-sample NG returns (2015–2017, the 1-minute fixture) and the
  in-sample predictor side only.
- **This is the fourth test on this in-sample with this predictor** (D627, D628, D629, D630).
- **The vault's exposures are Q25's.** NG's price path through the vault has been seen by trend, carry, spread and
  COT lines. No settlement-window return has been seen in any period.

## 1. Sample and trades

- **Days:** NYMEX business days 2017-05-22 → 2025-02-28 on which τ\* is defined (NG: 1,936). **Traded days:** τ\*
  passes §7.2's gate (|I| ≥ 3 × RT_cost and SNR ≥ 1.5, full-size cost, A9.2): **1,028** (t0 = 13:50 on 928, 14:00 on
  52, 14:10 on 48). The runner re-derives them from `gate_pass` (D627's lag audit).
- **Direction:** sign(Q_rem) at t0 = sign(q_est) (§7.2). Both funds buy when the held return to t0 is positive.
- **The traded contract:** the largest-share held contract at τ\* (`traded_ym`), one full-size NG contract (§7.6).
- **Entry (§7.3 primary):** the close of the bar t0+1 (the 1-minute bar starting one minute after t0: 13:51, 14:01
  or 14:11). If that bar has no trade, the fill is the last trade before the bar's end (the as-of price, carried
  from `px_HHMM` and the bars in between). Complete ≥ 3 minutes before W_start on every t0 (§7.3's constraint).
- **Exit (§7.4 structural):** the close of the W_end bar, 14:29 (the last trade before 14:30:00), as-of in the same
  way.
- **Bars:** `data/ng_minute_bars.csv.gz` (Databento one-second bars aggregated to minutes, start-stamped).
  The vault's files are never opened.
- **The return per trade, in dollars per contract:**
  - gross g_t = direction × (exit − fill) × 10,000;
  - net n_t = g_t − $16 (A9.2's round trip) − $10 (§7.3's one tick of adverse entry slippage) = g_t − $26.

## 2. The statistic

**H2 = the mean of g_t over traded days**, with the day-clustered t (one trade per day, so the ordinary SE of the
mean). The Newey-West t (5 lags, over the trade sequence) is reported beside it.

## 3. Controls that must fire

- **C1, the time placebo (deposit H5).** The ledger at 11:30, applied to 11:31 → 12:20:
  - traded days: the 11:30 row's gate passes (661 days);
  - direction: sign(q_est at 11:30); contract: `traded_ym` at 11:30;
  - fill: the close of the 11:31 bar; exit: the close of the 12:19 bar; the same dollars.

  **Its mean's |t| must be < 2.**
- **C2, the rotation null** (A9's replacement for the deposit's day shuffle, in H2's form). The day-level signal
  (traded flag, direction, t0) is rotated circularly within each year, by an offset drawn uniformly from
  [20, n_year − 20] over all 1,936 days, and scored against each day's own returns at the rotated t0.
  1,000 rotations, seed 630. **The observed t must exceed the rotations' p95** by more than 2 bootstrap SEs
  (D373's rule). p50, p95 and the SE are reported.

## 4. What passes

**H2 PASSES on NG** if all four hold:
1. mean g > 0 with **t ≥ 2.2414** (§5);
2. **mean net > 0**: mean g ≥ $26, the deposit's "≥ 1× RT cost" with §7.3's slippage;
3. C1: the placebo |t| < 2;
4. C2: the observed t beats the rotation p95 by more than 2 SE.

## 5. Multiplicity

- **Holm across the deposit's two instruments** (line 543, kept by A2). CL is not tested (H1 inconclusive), so it
  enters Holm as untested (p = 1). NG must then clear the first Holm step: two-sided **p ≤ 0.025, t ≥ 2.2414**.
- **Programme level** (§13A.8, not gating this record): promotion needs the family's adjusted p ≤ 0.005 (NG alone:
  p ≤ 0.0025, t ≥ 3.02) and a programme-level DSR ≥ 0.95. Both are reported.

## 6. The verdict ladder

| outcome | condition | consequence (deposit §14, as amended) |
|---|---|---|
| **PASS** | all of §4 | Gate 1 is met on NG (with H1 provisional). **The vault's one look (§8) is then put to the principal** |
| **REAL, NOT TRADABLE** | 1, 3 and 4 hold but the net mean ≤ 0 | "Real, not tradable" (line 968). Not promoted, no vault look. Write-up |
| **FAIL** | mean g ≤ 0, or t < 2.2414 | "Flow is real but priced/absorbed" (line 965) at Stage A. Later stages could still lift H2 (Gate 1's second route); none is built. Write-up |
| **UNRESOLVED (control)** | 1 holds but C1 fires or C2 is not beaten | not settlement-specific. Written up and put to the principal, as D627/D629 ruled |
| **UNRESOLVED (margin)** | C2's margin within 2 SE | as above |

**If D629's H1 turns VOID after 2026-10-10,** H2's verdict stands as recorded, but Gate 1 lacks its H1 half, and
the record says so.

## 7. Reported beside, never gating (CLAUDE.md's four groups, both lenses)

**Performance, net and gross side by side.** The mean per trade; Sharpe AND Sortino of the daily dollar P&L over
all 1,936 days (0 on untraded days, √252), both net and gross; exposure (the share of the session in a position);
volatility; max drawdown; the mean move against the $26 cost; the breakeven cost (the mean gross).

**Trade distribution.** Count, mean, median, win rate, payoff, skew, kurtosis, and the three trimmed means (ex-top
1%, ex-bottom 1%, both).

**What the result depends on:**
- by year (profitable years; the result without its best year, §13A.8.5), and the best 1% of days removed;
- the days needed for half the P&L;
- NG price terciles;
- t0 (13:50 / 14:00 / 14:10);
- **the funds' size terciles (D629's lesson):** a fund footprint must show in the top tercile;
- **H3, dose-response:** the mean by |I| quintile, with Spearman ρ and the inversion count;
- **H6:** the yearly mean against the yearly mean BOIL+KOLD AUM.

**The controls D629 taught (§0):**
- **the same signed return on the 908 untraded days**, and the difference traded − untraded with its t. The rule
  "follow the return to t0" runs on every day, so the funds' claim is the traded days' EXCESS;
- the mean with the estimated-f days excluded (BOIL 2023, and the carried days of 2025). NG gates on f_est, as in
  D627 and D629.

**Variants (§9 robustness, report, do not re-select):**
- the fixed-time 14:10 variant (§7.1 secondary);
- the stress fill (the worst close among bars t0+1 … t0+5, §7.3);
- 2× cost;
- **the one-bar-delay** (fill at the close of t0+2; §13A.8.6: must keep ≥ 50% of the edge);
- with and without flagged days (roll, expiry, EIA, the spot month's last three days).

**H4, timing.** The event curve from t0 to W_end + 30 min by |I| quintile, and the share of the move to W_end made by
t0+5. The deposit's reading is "≤ 50%", and the record states which side it falls on. **§7.5's post-window fade:**
the W_end close to +30 min, against the direction.

**Book frame.** §7.4's exits on the minute bars: the stop at 1 × |I| adverse (the minute's high or low); the early
profit at 1 × |I| favourable before W_start; the structural exit at W_end; a stop and a profit in one bar is taken as
the stop. §7.4's flow-reversal exit (3) needs a trailing time-of-day percentile of signed volume. It is **not
built**, and the record says so. Performance as above.

**The component line** (CLAUDE.md, at minimum size): one MNG (1,000 MMBtu), $3 + one tick ($1) a round trip plus
one tick of slippage. Net and gross Sharpe and Sortino, hit rate and skew. The correlation with every entry in
`COMPONENTS_PROP.md` where a daily P&L is on disk, and "not computable" where it is not (#2's and #3's are not
stored as daily series).

**The DSR** with this record's trial count (the configurations in this section), and the programme-level p (§5).

## 8. The vault, if and only if H2 PASSES and the principal says so

- **Inputs, built only then:** NG's P1 panel and minute bars for 2025-03-01 → 2026-09-18, by the same code with the
  cut moved, under an explicit vault flag. The inputs are the funds' NAV to 2026-09-18 (D619), the index holdings
  rules, the settlement strip, and the main pull's 2025 and 2026 one-second files. If any input cannot be built, the
  gap is written up before anything opens.
- **Frozen first:** `data/ledger_frozen_vault_h2_ng.json`. The deposit names `results/settlement_flow/FROZEN_VAULT.json`
  (line 901), but no `results/` tree exists, as with POWER. It holds the sha256 of the runner, of both builders and
  of this record, the parameters, and the retained stage (A). The opening is logged. A second opening is refused.
- **Pass (deposit line 902):** the vault's mean g has the in-sample sign; one-sided p < 0.10 (t ≥ 1.2816); and the
  net mean is > 0 at 1× cost. A failure: "not promoted", written up, with no re-tuning.
- POWER's vault pass rate: 0.82 at a quarter of the ledger's predicted move, 0.40 at one tenth, 0.09 at none.

## 9. POWER (`data/ledger_power_h2_ng.json`)

Noise: NG's pre-sample returns from the t0+1 close to the 14:29 close (2015-07-02 → 2017-05-10, 456 days, the
1-minute fixture's front). Each is standardised by its trailing 20-day SD, then rescaled by each in-sample day's
σ_rem × P. The in-sample shape is 1,028 traded days of 1,936; the median |I| on traded days is $163 a contract and
the median return SD $247.

| | value |
|---|---|
| SE of the mean (analytic) | $11.58 per trade |
| MDE at t 2.2414 / at 80% power | $26.0 / $35.7 |
| **the plausible effect (§9A.2 rule 2): the cost, $26** | **MDE = plausible: individually testable, at the edge** |
| size (β = 0; two-sided at the Holm bar) | 2.7% |
| the null's p95 of t | 1.74 |
| C2's false-pass rate (null datasets beating their own p95); the combined gate | 7%; 1% |
| power at mean effect β × \|I\|: β = 0.1 / 0.25 / 0.5 / 1 | 0.41 / 0.995 / 1.00 / 1.00 |
| vault pass rate at β = 0 / 0.1 / 0.25 | 0.09 / 0.40 / 0.82 |

- **How to read it:** an H2 whose mean just covers the cost is found about 40% of the time. A tenth of the ledger's
  predicted move clears the cost by about $2 a trade. The ledger claims |I| ≥ 3 × cost on every traded day (β = 1),
  and at a quarter of that H2 is near certain to pass.
- **Not simulated:** fat tails beyond the pre-sample's (its standardised kurtosis is 1.6–2.7), and the placebo.

## 10. The runner and its assertions

- **File:** `scripts/run_h2_ng_stage_a.py`, with `--selftest`, `--run` (refuses a second run) and `--check`.
  **Output:** `data/ledger_h2_ng_stage_a.json`, with a `REQUIRED_OUTPUTS` guard: the verdict, the gate mean and t,
  the net mean, C1, C2's p50/p95/SE, n, and the §7 groups.
- **Lag audit.** D627's `audit_flow` (NAV and f dated before t; q_est from q1 × f; τ\* from `gate_pass`). The fill
  bar must start after t0, and the as-of prices must use no bar at or after the fill bar's end.
- **Sign audit, in money:** a synthetic day whose price rises $0.010 after a buy signal books +$100 gross and +$74
  net; the same rise after a sell signal books −$100 gross.
- **Right-quantity:** the gate's returns differ from the placebo's and from the fixed-14:10 variant's; the net
  differs from the gross by exactly $26 a trade.
- **Selftest** (no in-sample return after t0): POWER's noise with an injected β = 0.5 → PASS; β = 0 → not PASS;
  each audit RAISES on a deliberate break (a fill bar at t0; a NAV dated t; a flipped direction); `analyse` runs end
  to end on synthetic data before the one real run.
- `-W error::RuntimeWarning`.

## AMENDMENT, 2026-09-26: a near miss on the net bar is UNRESOLVED, not REAL, NOT TRADABLE

*The principal, after the commit of this record and before its runner existed, with no H2 statistic computed:
"add an unresolved/potential if it barely misses the net bar."*

A new row goes into §6's ladder, between PASS and REAL, NOT TRADABLE:

| outcome | condition | consequence |
|---|---|---|
| **UNRESOLVED (net, potential)** | §4's 1, 3 and 4 hold; the net mean is ≤ 0 but **within one standard error of zero** (mean g > $26 − SE, where SE is the gate's SE of the mean) | the cost bar lies inside the estimate's own uncertainty. Not promoted, and no vault look. It is written up as a potential and put to the principal (e.g. cheaper execution, or more data) |

**REAL, NOT TRADABLE** now requires a net mean at or below −1 SE. Every other row is unchanged. The one-SE band is
about $11.6 a trade on POWER's SE.

## 11. What this does not touch

- No vault data (§8 governs its one look).
- No Sierra Chart data (H2 is price only).
- No CL.
- **Deviations** are listed in the output and never replace a verdict.
