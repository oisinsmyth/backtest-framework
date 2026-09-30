# D709 STAGE 0 DESIGN — silver's leveraged-ETF rebalance into the COMEX settlement: from 12:55 ET, trade the sign of the day's move to 13:25 on one SIL, where AGQ and ZSL have struck their NAV at the settlement only since 2019-01-07

*2026-09-30. The design record only. It is committed before the runner exists (R8). The runner will be
`scripts/stage0_d709_silver_settlement_flow.py`, committed separately with its POWER output before its one run.*
- **What it is:** a premise check on 2011-01-03 → 2023-12-29. It admits nothing and spends no slice.
- **Seals:** nothing dated 2024-01-01 or later is read from any source (bars, settlements, NAV files, calendar). The
  vault (2025-03-01 → 2026-09-18) and D626's CL/NG sample are untouched; no CL or NG row is read at all.
- **The principal approved looking at it.** The proposal came from a read-only research agent and was verified.

## 1. The question

Does silver's price move into the COMEX settlement (13:24–13:25 ET) in the direction of the day's move, by an amount
that scales with the leveraged funds' predicted rebalance, **only in the era when those funds struck their NAV at that
settlement?**

## 2. The mechanism, and what it predicts that a random walk does not

- **The funds.** AGQ (L = +2) and ZSL (L = −2) reset to their leverage daily. The rebalance has the sign of the day's
  return r, and its size is Q = (L² − L)·A·|r|, which is (2·A_AGQ + 6·A_ZSL)·|r| in dollars. Both funds buy on an up
  day.
- **The clock.** From 2019-01-07 they strike NAV on the Bloomberg Silver Subindex, which prices off the COMEX
  settlement (D634 §8, the 10-K filed 2019-03-01). Their swap counterparties then hedge at the settlement, so the flow
  lands in SI's settlement window. D634's rebuild confirms the link: AGQ and ZSL match the rebuilt silver subindex
  within 5 bp on 100% of roll days and 99.6% of other days (D634 RESULT).
- **Before 2019-01-07** they tracked the LBMA fixing price (the 10-K filed 2017-03-01), set at noon London, about
  07:00 ET. The hedge then targeted the fix, not the COMEX settlement.
- **The same mechanism passed on NG.** D630: $66.02 a full-NG trade gross, t 5.01, a flat 11:30 placebo (t −0.42),
  and a post-window fade of $29 (t 3.98). The realised move was about 0.31 of the ledger's square-root impact |I|
  (D648 §0). On CL it was 0.26, and T1 missed its bar by 0.011 of a t (D648 RESULT).
- **What NG also showed:** untraded (small-|I|) days carried nothing (−$6, t −1.08). The effect lived on days with
  large predicted flow.

**What it predicts that a random walk does not:**
1. **P1:** a positive mean of s × (exit − fill), where s is the sign of the move from the prior settlement to 12:55.
2. **P2, the era:** the effect exists from 2019-01-07 and not before.
3. **P3, the clock:** it does not exist at 11:30 → 12:00 with the same rule.
4. **P4, the null member:** gold, whose leveraged funds (UGL, GLL) switched benchmark on the same date, shows a much
   smaller effect (§5).
5. **P5, dose:** the payoff rises with the predicted flow share Q/V_d.
6. **P6, temporary pressure** (not gated): the move partly reverts after 13:25.

## 3. Data, what I inspected, and the seals

| input | file | use |
|---|---|---|
| SI and GC 1-minute day-session bars, the volume front | `data/fixtures/fut_day1m.parquet` (bar 0 = 09:00 ET, start-stamped) | prices, bar presence, day volume |
| settlements, every listed month | `data/fixtures/fut_settle_strip.csv.gz` (`ref` = the trade date) | the prior settlement; σ_d; the settlement exit variant |
| the session calendar | `data/fixtures/cme_session_calendar.csv.gz` (D589) | `session_close_et`, the measured settlement minute |
| fund NAV, shares and AUM | `data/raw/recorder/proshares_nav/{AGQ,ZSL,UGL,GLL}__2026092...Z.csv` (not in `docs/data-available.md`) | A_t; the P0 premise check |
| BCOM and GSCI lead-contract schedules | `data/index_reweight/methodology_facts.json` (Table 9a); `gsci_schedule.csv` | the roll carve |
| costs | `data/futures_costs.json` | SIL and MGC lines |

**What I inspected for this design (non-return facts only).** No price column (open, high, low, close, settle) was
loaded; no return, P&L or window move of SI or GC was computed.
- `fut_day1m`, SI and GC, days before 2024-01-01: bar presence at the named minutes, contract codes, `same_front`,
  and the day's volume sum, by year (§4.4).
- The calendar's `session_close_et` for SI and GC by year.
- The strip: whether a (contract, ref) row exists. Its meta was printed, and it lists a few 2025-dated negative
  settlements on 6A, 6E and 6J. No SI or GC value was among them.
- The NAV files: AUM by year, from rows dated before 2024-01-01. **Disclosed:** reading the header printed three
  rows of each file (2023-12-27 → 12-29), including NAV change (%), the funds' daily return on those three days.
- **Records read that touch SI's session:** D676 and D677 traded SI's day session to a 13:20 flat (break trades,
  2016–2023). D677 reports a cut of SI's later entries (+4.9 bp gross for entries after 120 minutes). That overlaps
  this hold (12:56 → 13:20) but is not this statistic. **No record has tabulated SI's move into 13:25 against the
  sign of the day's move.**

**Seal guard (in code):** every read is sliced at `< 2024-01-01` and asserted on its maximum date; a row dated
2024-01-02 injected in the self-test must raise.

## 4. The construction

### 4.1 Clocks (SI settlement window 13:24:00–13:25:00 ET, D586)

| | SI primary | SI midday placebo | GC null member |
|---|---|---|---|
| decision price | as-of close at or before bar 12:54 (last trade before 12:55:00) | as-of bar 11:29 | as-of bar 12:59 |
| s | sign(decision − prior settlement of the same contract) | the same, at 11:30 | the same, at 13:00 |
| fill | close of bar 12:55 (one minute later, D630/D699) | close of bar 11:30 | close of bar 13:00 |
| exit | close of bar 13:24, the last trade in the window | close of bar 11:59 | close of bar 13:29 (window 13:29–13:30) |
| hold | 29 minutes | 29 minutes | 29 minutes |
| contract | one SIL (1,000 oz), priced off SI's bars | one SIL | one MGC (10 oz) |

- s = 0 is no trade.
- **Beside, not primary:** exit at the day's official settlement of the same contract (the strip). This is what a
  trade-at-settlement exit would get. Whether SIL lists TAS is not sourced.

### 4.2 Eras

- **Post (the treatment):** 2019-01-07 → 2023-12-29.
- **Pre (the placebo):** 2011-01-03 → 2019-01-04. It is reported whole and split at 2015-07-01, the COMEX pit
  closure. The pit date is not sourced in this repo.
- **2010-06-07 → 2010-12-31** is in neither era. Its slot fill is 0.755. It supplies POWER's noise (§9).

### 4.3 Exclusions, applied in this order and counted by year and reason

1. **Early close:** `session_close_et` is not 13:24 (SI) or 13:29 (GC). In 2010–2023 SI closes at 13:24 on 225–258
   sessions a year, with 3–6 early closes (12:59 or 13:14), plus 2020-02-27 (13:19, an archive dropout per D589).
2. **Missing bar:** the fill bar or the exit bar is absent; or no trade exists in bars 12:50–12:54 for the decision
   price (a staleness cap of five minutes).
3. **No prior settlement** for the traded contract on the previous SI settlement day. A holiday republication (every
   SI contract equal to its previous value) is not a settlement and is skipped.
4. **A roll session:** `same_front` is False.
5. **Delivery:** the traded contract is within 5 sessions of its first notice day. The standing ruling is: no
   expiring physical contract near delivery.
   - FND is the last SI session of the month before the contract month (D676 R2's definition), counted on SI's own
     calendar.
   - D676's 10-business-day buffer is reported beside.
6. **The index roll and reweight carve:** business days 5–10, counted on the root's own session calendar, of every
   month where BCOM's Table 9a or GSCI's schedule changes the root's lead contract, plus January.
   - For SI that is January, February, April, June, August and November. BCOM and GSCI agree on silver.
   - For GC, derived the same way, it is January, March, May, July and November. D676 R3 also listed September as an
     approximation; the runner derives the months from the schedules.
   - The carved days are out of the primary and reported beside. They are the days the frozen index-reweight line
     reads (D635, D636), and they carry roll flow that has nothing to do with s.

### 4.4 The counts this yields (counted for this record, no price loaded)

The proposal's caveat on missing minutes is **overstated**. SI's slot fill is 0.76–0.84 over 2014–2019 on the whole
09:00–16:00 band (`fut_day1m.meta.json`). But the three minutes this trade needs are present on 94–99% of sessions in
every year. The shortfall sits elsewhere in the band, and the missing exit bars are mostly early closes.

| SI | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| sessions | 258 | 257 | 252 | 249 | 231 | 258 | 257 | 258 | 258 | 259 | 258 | 258 | 257 |
| bars 12:54, 12:55 and 13:24 all present | 252 | 252 | 249 | 234 | 219 | 246 | 244 | 246 | 248 | 249 | 249 | 254 | 255 |
| front within 5 sessions of FND | 20 | 20 | 20 | 17 | 19 | 18 | 20 | 19 | 17 | 17 | 16 | 15 | 15 |
| carved (BD5–10, six months) | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 | 36 |
| eligible after all exclusions | 189 | 187 | 190 | 177 | 165 | 184 | 185 | 184 | 186 | 187 | 190 | 196 | 194 |

- **Eligible trades:** SI **950** post and **1,464** pre. GC 993 post and 1,546 pre.
- These counts require bar 12:54 exactly. The five-minute as-of rule of §4.3 can only add days.
- **The front and the index contract.** SI's volume front is BCOM's lead(m) on about 245 sessions a year. The front
  rolls a median 2–3 sessions before FND. The index rolls earlier (BD6–10). So in each of the five roll months, from
  BD11 until the front rolls, **the fund flow lands on the next contract while this trade holds the front.** The
  fixture carries only the front, so that is the contract traded. The split (front = index-held contract, or not) is
  reported, and the assumption is that the calendar spread transmits the pressure.

### 4.5 Money

- **Gross per SIL:** g = s × (exit − fill) × 1,000. **Net:** n = g − **$8.00**.
  - `futures_costs.json` → SI → micro → `d556_min_size`: $3 commission + one $5 tick a round trip (half a tick a
    side). Verified. The $13 line that adds stop slippage is not used; there is no stop.
- **Stresses (reported):**
  - $13.00: one extra tick of entry slippage, as D630 charged;
  - **$24.50:** $3 + SI's quoted spread at the execution instants, 4.30 ticks (`d507_exec`, measured 2025-09 →
    2026-09, a floor on crossing).
- **SIL's own spread and depth are in no fixture.** SIL is priced off SI's bars, as D676 did.
- **MGC (GC member):** g = s × (exit − fill) × 10; cost $5.93 ($3 + `d508_exec` 2.933 ticks × $1, as D676).
- **Corwin–Schultz is not used:** it is a range model that overstates by about 10× here (memory: the cost models are
  range models).

## 5. The predictor side (point-in-time, for P5 and the secondary)

- **A_t−1:** each fund's AUM at the NAV date before the trade day. Q̂_t = (2·A_AGQ + 6·A_ZSL)·|r_τ| / (P_prev × 5,000)
  in SI contracts, with r_τ the move from the prior settlement to the decision price.
- **V_d:** the mean day-session (09:00–15:59) volume of the front over t−20 … t−1, from `fut_day1m`. Whole-session
  cleared volume starts only 2015-11-19, so it cannot cover the pre-era. It is reported beside for 2016–2023, with its
  ratio to V_d by year.
- **σ_d:** the SD of 20 prior settle-to-settle log returns of the front. **σ_rem:** the SD of the 20 prior days'
  12:56 → 13:25 returns (prior-only).
- **x̂_SR** = 0.7 × σ_d × √(Q̂/V_d) × P_prev × 1,000 (the ledger's |I| per SIL). **x̂_GM** = σ_rem² × (Q̂/V_d) ×
  P_prev × 1,000 (D648's inventory-risk form).

**Flow share by year** (fund AUM from the NAV files; V from `fut_day1m`; the price is an approximate public annual
average, used for this table only, never read from the fixtures):

| | 2011 | 2013 | 2015 | 2017 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---|---|---|---|---|---|---|---|
| AGQ median AUM, $m | 899 | 551 | 283 | 262 | 203 | 250 | 619 | 410 | 383 |
| ZSL median AUM, $m | 356 | 110 | 56 | 20 | 14 | 18 | 34 | 25 | 25 |
| **SI flow per 1% move, $m** | **40.1** | 18.0 | 9.1 | 6.4 | 4.9 | 5.8 | **14.6** | 9.5 | 9.3 |
| SI day-session front volume, median | 30,950 | 19,172 | 18,472 | 36,682 | 34,423 | 33,852 | 28,132 | 25,303 | 28,998 |
| SI Q/V per 1% move (≈ price) | | | | | 17.7 bp ($16.2) | 16.7 bp ($20.5) | 41.2 bp ($25.1) | 34.6 bp ($21.8) | 27.4 bp ($23.4) |
| GC flow per 1% move, $m (UGL + GLL) | 11.4 | 12.2 | 6.3 | 4.0 | 3.0 | 4.6 | 6.4 | 6.2 | 4.5 |
| GC Q/V per 1% move | | | | | 1.7 bp | 2.6 bp | 4.4 bp | 4.8 bp | 2.8 bp |

- **The pre-era carried more fund flow, not less:** 2011's was 2–8× any post-era year's. If the hedge had landed at
  the COMEX settlement before 2019, the pre-era effect would be larger. That is what makes the era contrast a strong
  placebo.
- **GC is a small member, not a zero one.** Its flow share is about 1/8 of SI's.
  - Under square-root impact that is about 1/3 of SI's move in σ units. Gold's lower σ brings its expected t to about
    1/4 of SI's.
  - Under inventory risk it is about 1/8.
  - **Disagreement with the proposal:** it quoted UGL's flow as "~0.3 bp against GC's liquidity". Against the
    day-session front volume this record finds 1.7–4.8 bp per 1% move. Against whole-session volume it would be
    smaller, but the SI : GC ratio is what the member tests.

## 6. The primary statistic, the gates and the thresholds (fixed now)

**The primary statistic:** the mean gross dollars per SIL over the post-era's eligible days, with the ordinary t (one
trade a day). The ladder is reported beside: NW t (5 and 10 lags), White HC0/HC3, and the monthly block bootstrap.

| gate | what | bar |
|---|---|---|
| **G1 edge** | SI post, the mean gross per SIL | **> 0, t ≥ 2.00, and above the p95 of the enumerated rotation null (§7)** |
| **G2 clock** | SI post, the 11:30 → 12:00 placebo | **placebo t < +2.00, and the paired difference (settlement − midday, same days) has mean > 0** |
| **G3 era** | SI pre (2011-01-03 → 2019-01-04), the same rule | **pre t < +2.00, and post mean − pre mean > 0** |
| **G4 null member** | GC post, its own clock | **t < +2.00** |
| **G5 dose** | SI post, terciles of Q̂/V_d | **mean gross, top tercile > bottom tercile** |
| **N net** | SI post, the mean net per SIL at $8 | **> 0** |

- **Controls fire one-sided (t ≥ +2).** Only a control that reproduces the effect contradicts the attribution. A
  significant negative control is reported as such; it is not a kill.
- **G5 is a sign gate on purpose.** Tercile means carry an SE of about $6.5 each against expected steps of a few
  dollars. A Spearman bar over five quintiles would be met by chance 12% of the time and would rarely be met under
  the mechanism. The quintile table, its Spearman and the slope are reported.
- **Attribution qualifier (reported, not a gate): G5b.** The top-minus-bottom tercile difference against the
  **AUM-rotation null**. A_t is rotated circularly over the post-era days, offsets 63 … n − 63, all enumerated. Q̂/V_d
  and its terciles are recomputed on each rotation, so the null is count-matched and keeps |r| and V.
  - It asks whether the funds' actual scale orders the payoff beyond what |r| does.
  - AUM is slow (about four regimes in five years), so the null is coarse.
  - A MECHANISM verdict reads "(funds' scale shown)" when the difference beats the p95, and "(scale unresolved)"
    otherwise.

**Multiplicity.** There is one primary cell. The controls are specificity checks. Under the mechanism, the chance that
at least one of G2–G4 fires falsely is about 10% (2.5% + 2.5% + about 5% for GC at its predicted t). No programme
slot is spent: this is Stage 0.

## 7. Nulls (the distribution, not the percentile alone)

- **N1, the primary (G1):** the post-era sign series s is rotated circularly against the eligible days' window
  moves.
  - Offsets k = 20 … n − 20, every one enumerated (about 910). **The p95's SE is exactly 0.**
  - The statistic is the mean gross per SIL. Reported: p05, p50, p95, the rank, and the t's null beside.
  - The rotation keeps the sign balance and the moves' own series. The always-long drift term E[s]·E[g] is inside the
    null.
- **N1 on every control cell** (SI midday, SI pre, GC post and pre), each enumerated the same way and reported.
- **N2, the AUM rotation** (G5b, above).
- **Calibration before the run.** In POWER, datasets with β = 0 must beat N1's p95 at a rate of 3–7%. The CL/NG
  lesson was that an autocorrelated regressor makes a shuffle anti-conservative. Here the rotated object is a daily
  sign with little autocorrelation, but the rate is checked, not assumed.

## 8. Reported beside, never gating (CLAUDE.md's four groups; both lenses)

**Both lenses coincide.** There is one position a day and no slot cap, so the path-invariant per-trade series and the
daily book differ only by the zero days. Both are reported.

1. **Performance, net and gross side by side:**
   - the mean per trade;
   - Sharpe AND Sortino of the daily $ P&L over every post-era SI session (0 on untraded days, √252), with the
     monthly block-bootstrap SE;
   - exposure (29 minutes on about three sessions in four);
   - volatility and maximum drawdown;
   - the mean move against 2c ($16) and the breakeven cost (the gross mean);
   - all three cost lines.
2. **The trade distribution:** count, mean, **median**, win rate, payoff, skew, kurtosis, and the trimmed means
   (ex-top 1%, ex-bottom 1%, both). The top trade is named: date, contract, fill, exit.
3. **What it depends on:**
   - by year (profitable years; without the best year);
   - the days needed for half the P&L; the top-1/5/10 day shares;
   - price terciles (the $8 cost is a larger share of a $16 silver trade than of a $25 one);
   - AUM terciles; |r_τ|/σ_d terciles;
   - the carved days beside the primary;
   - front = index contract or not; the pre-era split at 2015-07.
   - **D629's lesson for a scale × return predictor:** the slope on x̂_SR with and without the continuation control
     z(|r_τ|/σ_d); r × year; leave-one-year-out; and the slope within AUM terciles (a proportional mechanism must show
     in the top one).
   - **D648's form question:** g on z(x̂_GM), z(x̂_SR) and z(|r_τ|/σ_d), NW(5), with the same regression at 11:30.
4. **Nulls:** N1 and N2 with p50/p95, as §7.

**Mechanism diagnostics:**
- the event curve (the mean signed move from the fill, minute by minute to 13:25);
- the fade from 13:25 to 13:55 against s (P6);
- the always-long and always-short controls in the same window;
- **the triple difference in σ units:** (SI post − SI pre) − (GC post − GC pre). UGL and GLL switched benchmark on the
  same date, so this removes a metals-wide change at the switch.

**P0, the natural experiment's premise.** The runner checks it before any window move is read. It reuses D634's NAV
model on the silver subindex rebuilt from the strip (Table 9a).
- **Expected:** post-era, AGQ and ZSL match within 5 bp on ≥ 95% of days (D634's figure reproduced on the < 2024
  window); pre-era, on ≤ 50%.
- **If the pre-era share exceeds 50%,** the funds were already struck at the settlement. The era contrast is then
  VOID and G3 is not read.
- **One limit:** Table 9a is verified identical only from the 2016 methodology onward.

**The component line.**
- one SIL at $8;
- the daily net Sharpe and Sortino over post-era SI sessions; hit rate; skew; gross beside net; C-d's daily σ;
- **ρ with every live component:**
  - #2, the admitted MACD arm (`run_d667_hike_pause_overlay.load_arm()`);
  - #3, the NG winter spread (from D565's runner if it exposes a daily series; otherwise "not computable", stated);
  - #4, F2 (its in-sample daily net from `vault_d707_last_hour_f2.frame` + `f2`, over 2018-05 → 2023-12);
  - each over the common window.
- The arm trades NQ on the hourly clock and F2 trades ES 15:30–16:00. This trade shares neither instrument nor clock,
  so ρ near 0 is the expectation; the runner computes it.

**The filter, a DECLARED SECONDARY (never a gate), oracle first** (`backtest_framework.validation.filter_oracle`,
D690). It is shown to the principal, who designs the filter.
1. **The oracle** (`oracle_take`, and `oracle_take_threshold` at k = 2 × $8). Also the size-only oracle and a profile
   of where the oracle's winners sit (year, |r_τ|, AUM, price).
2. **The D649 template:**
   - b_t = Σ g_j·x̂_SR,j / Σ x̂²_SR,j over earlier eligible days only, after a burn-in of 250 trades;
   - trade when b_t × x̂_SR,t ≥ 2 × $8;
   - reported with `assess` and `calibration` (the slope must be positive);
   - fewer than 30 filtered trades is UNRESOLVED.
   - **Expected:** at NG's pass-through, a projection of $16 needs |r_τ| of roughly 5–15% at post-era AUM, so the
     filter will fire rarely. That is stated now.

## 9. Size the prize, and the in-sample power (stated honestly)

**The prize** (square-root form, the ledger's |I|, per SIL). The inputs are §5's post-era flow shares; σ_d = 1.7% a
day (assumed, band 1.2–2.2%, not measured here); E[√(|r|/1%)] = 1.07; and 0.95 for the 12:55 sign agreeing with the
day's.

| | 2019 | 2020 | 2021 | 2022 | 2023 | mean |
|---|---|---|---|---|---|---|
| \|I\| per SIL at a 1% move | $8.1 | $10.0 | $19.2 | $15.3 | $14.6 | $13.4 |

- **The expected gross per SIL is β × $13.7:**
  - at NG's pass-through (β = 0.31): **$4.2**, band $2.5–$6.2 over σ_d;
  - at the full |I| (β = 1): $13.7.
- **Against the $8 cost:** the unfiltered trade is net-negative unless β ≥ 0.58, nearly twice NG's.

**The noise.** σ_hold is the SD of the 29-minute move per SIL = σ_d × √(its share of daily variance) × P × 1,000.
- A share of 6% gives **$89**: SI's window minute trades at 5–7.5× its flank (D586), and the 29 minutes carry an
  estimated 6–7% of the day's volume.
- The band is $53 (2.1%, uniform time) to $103 (8%).

**The bar (D661's rule):** a mean of 2.80 × σ_hold / √n is needed for 80% power at t ≥ 2. With n = 950 that is
**$8.1 gross** (band $4.8–$9.4). For a net that is confirmable as well, $16.1.

| truth | expected gross per SIL | expected t | P(G1: t ≥ 2) |
|---|---|---|---|
| β = 1 (the full ledger \|I\|) | $13.7 | 4.7 | ≈ 1.00 |
| **β = 0.31, 100% of the NG-calibrated effect** | **$4.2** | **1.44** (plausible 1.2–1.8; full band 1.0–2.8) | **0.29** (plausible 0.22–0.41; full band 0.17–0.78) |
| **50% of it** | $2.1 | 0.72 | **0.10** (0.06–0.27) |
| β = 0 | 0 | 0 | 0.025 |

- **Read it as:** the in-sample is powered for an effect about the size of its cost, not for the effect NG's
  pass-through predicts. At that effect, G1 clears about three times in ten, and the full MECHANISM reading (G1–G5)
  about one time in four.
- **Two things would lower it:** a whole-session V_d (1.5–2× the day-session front volume) cuts the expected t by
  0.71–0.82; and the era contrast is weaker than G1 (SE of the difference $3.7 against $2.9, so an expected t of
  about 1.1).
- **Confirmation:** the unread 2024-01 → 2025-02 slice holds about 230 eligible trades, for an expected t of about 0.7.
  A pass here would stay in-sample until a confirmation design is found.
- **The runner's POWER (`--power` → `data/d709_power.json`) replaces this sketch before the run.**
  - The noise is SI's 12:56 → 13:25 moves on 2010-07 → 2010-12, about 100 days, outside both eras. It is standardised
    by the trailing σ_d and rescaled to each post-era day.
  - The injection is β × x̂_SR on the post-era predictor side, at β ∈ {0, 0.155, 0.31, 0.62, 1}, 2,000 datasets each.
  - It reports the G1 rate, the full-reading rate, the N1 size check at β = 0, and the MDE.
  - **Before the run:** if POWER's G1 rate at β = 0.31 is below 0.25, the record goes back to the principal (§10).

## 10. The declared readings and the kill conditions

| reading | condition | consequence |
|---|---|---|
| **PASS** | G1–G5 and N (P0 not void) | the mechanism is real and pays unfiltered at SIL. It goes to the principal for a confirmation design; nothing is admitted |
| **MECHANISM ONLY** | G1–G5; N fails. "UNRESOLVED (net)" if the net is within 1 SE of zero (D630's amendment) | the filter step: the oracle and the secondary go to the principal, who designs the filter (a new registration) |
| **NEITHER** | G1 fails with t > −2; or G1 holds and G5 fails with no control firing | no construction is built on this in-sample. The record states the power it had. A retry needs a new statistic or new data, not a re-cut |
| **FAIL (not the funds)** | G1 holds and G2, G3 or G4 fires (or G3's post − pre ≤ 0) | the settlement-window move is generic continuation, not the funds'. This construction and its filter are not carried |
| **FAIL (inverted)** | post-era t ≤ −2.00 | DIRECTION-INVERTED; it counts against the mechanism |
| **VOID (era)** | P0: the pre-era match share > 50% | G3 is not read; the reading is capped at MECHANISM ONLY, with the era clause written as unavailable |

- Every verdict carries G5b's attribution qualifier. A result that clears only under one rung of the SE ladder is
  written as on the bar.
- **The kill on paper (before `--run`).** If POWER's G1 rate at β = 0.31 is below 0.25, the principal decides whether
  to run. A run would then return NEITHER in most worlds where the mechanism is real. The in-sample is not a scarce
  holdout, but a read on it is a read.
- **R15:** a FAIL closes this construction, not the avenue. Only the principal closes an avenue.
- No threshold, window, clock or exclusion is tuned after the run. Any change is a new design.

## 11. The runner specification

**File:** `scripts/stage0_d709_silver_settlement_flow.py`, with `--selftest`, `--power`, `--run` (refuses a second
run) and `--check` (reproduces byte for byte). **Output:** `data/d709_silver_settlement_flow.json`, with a
`REQUIRED_OUTPUTS` guard that raises unless every gate, null (p50/p95/rank), group, stress line, the component line, P0,
the exclusion waterfall by year and the timings are present. Run under `-W error::RuntimeWarning`.

**The data root** resolves as D700's does (`--data-root`, default `REPO / "data"`; the worktree passes the main
checkout's `data/`).

**Functions:**
- `load(data_root)`: pyarrow filter on root ∈ {SI, GC} and day < 2024-01-01; the strip, calendar and NAV files are
  sliced at read. Asserts the maximum date on each.
- `sessions(root)` → the eligibility table and the exclusion waterfall.
- `decide(root, clock)` → s, the decision, fill and exit prices, and the prior settlement.
- `trades()` → g and n per contract.
- `predictors()` → Q̂, V_d, σ_d, σ_rem, x̂_SR, x̂_GM.
- `score(x)` → the mean, t and ladder.
- `rotate_enumerated(s, g, lo)` and `rotate_aum(...)`.
- `groups()` → §8's four groups.
- `premise_p0()`; `component_line()`; `oracle_secondary()`; `power()`; `verdict()`.

**Assertions (each proved to RAISE in `--selftest` on a deliberately broken book):**
1. **Lag audit, a second implementation.** It recomputes s, the decision price and the fill from the raw fixture rows
   with a plain loop, on 60 sampled days per cell. It never calls `decide`: the last close with bar ≤ 12:54 and
   ≥ 12:50, then the strip row of the previous settlement day. It must reproduce the trade list exactly.
   - It also asserts AUM dated before d, V_d's window ending at d − 1, σ_d and σ_rem prior-only, and the fill bar
     starting after the decision minute.
   - **Break:** a decision price read from the fill bar (12:55) must raise.
2. **Sign audit, in money.**
   - A synthetic day rising $0.010 from fill to exit after s = +1 books +$10.00 gross and +$2.00 net on one SIL.
   - With s = −1 it books −$10.00 gross and −$18.00 net.
   - A decision above the prior settlement gives s = +1.
   - MGC: +$0.10 → +$1.00 gross.
   - **Break:** a flipped s.
3. **Right-quantity.**
   - The primary's moves differ from the placebo's, from the settlement-exit variant's and from GC's.
   - n = g − $8 exactly.
   - The carved set differs from the full set; the eras do not overlap.
   - Rotation offset 0 reproduces the observed statistic bit for bit.
   - **Break:** an exit at the fill bar (a zero-length hold).
4. **The seal:** a row dated 2024-01-02 injected into any source raises.
5. **Known answers:**
   - `session_close_et` is 13:24 on the eligible SI days;
   - the carve months derived from the schedules equal {1, 2, 4, 6, 8, 11} for SI;
   - FND is the last session of the prior month.
6. **The self-test's book check:** POWER's noise with β = 0.5 injected must give PASS or MECHANISM ONLY, and β = 0 must
   not. The analysis runs end to end on synthetic bars before the one real run.

**Speed, designed in.**
- The projected wall time is **under a minute serial** (the inspection's load of SI and GC bars and the strip took
  about 5 s). Nothing needs backgrounding, and no retro-optimisation is warranted.
- **The null is one axis-wise call.** For each cell, the enumerated rotation is a (K × n) index gather and a row
  mean. It is asserted bit-equal to the study's own scorer at k = 0 and at 20 sampled offsets, including a tie-heavy
  synthetic input (many g = 0 days).
- **Fan-out:** the seven independent cells (SI post/pre/midday-post/midday-pre, GC post/pre/midday) are dispatched
  through `fast_null.parallel_map` on threads (numpy, GIL released), and the `[SPEED]` line is logged.
- The self-test proves that 8 strided chunks of the offsets equal the whole, bit for bit.
- **`fast_null.NullContext` / `assert_matches_scorer` are not used.** They serve panel slot-books with per-symbol
  random offsets. This null is an exhaustive rotation of one daily series, and the offset-0 identity plus the
  scorer-equality assertion are its equivalent. Stated so the omission is not silent.

## 12. Decisions I made that the proposal did not fix

1. **The clock's minutes:**
   - decision as-of the last trade before 12:55:00 (bars 12:50–12:54);
   - fill at the close of bar 12:55;
   - exit at the close of bar 13:24, the last trade in the window;
   - the settlement exit reported beside.
2. **Missing bars:**
   - the fill and exit bars must be present;
   - a five-minute staleness cap on the decision price;
   - early closes are excluded on the measured `session_close_et`, because D586's SI row is `current_only` and
     `window_for("SI", date)` raises for any date before 2026-09-21. **The SI window's history is unsourced.** The
     design rests on the measured volume cliff (13:24 on every normal session 2010–2023), and it says so.
3. **The traded contract is the fixture's volume front,** not BCOM's designated contract. When the two differ, the
   fixture has no bars for the index contract.
4. **FND:** ≤ 5 sessions (the brief's statement of the standing ruling). D676's 10 business days is reported beside.
5. **The carve:** BD5–10 of every month where BCOM or GSCI rolls the root, plus January. It is out of the primary
   (D676 R3's precedent), reported beside, and derived from the schedules, not hard-coded.
6. **The eras:** the pre-era starts 2011-01-03 and is split at the pit closure (July 2015). 2010 is reserved for
   POWER's noise.
7. **The midday placebo uses its own 11:30 sign.** Applying the 12:55 sign at 11:30 would read the future.
8. **GC trades its own clock** (13:00 → 13:29, the same 29 minutes before its window) at MGC cost, with its own carve
   and FND.
9. **The statistic is in dollars per SIL** (the traded unit), with an ordinary t and the SE ladder. G1 also needs the
   exhaustive rotation null.
10. **Controls fire one-sided** (t ≥ +2); two-sided readings are reported.
11. **The dose gate is a sign test on terciles.** The AUM-rotation null is an attribution qualifier, not a gate,
    because its power is small (§6).
12. **V_d is day-session front volume** (the only volume covering both eras). The cleared whole-session volume is
    reported beside from 2015-11.
13. **Premise check P0 added:** the era contrast is read only if the pre-era NAV does NOT track the settlement-based
    subindex.
14. **Cost stresses:** $13 and $24.50. No Corwin–Schultz.
15. **The filter secondary** follows D649's template with the 250-trade burn-in and a 30-trade floor. The oracle
    comes first; the principal designs the real filter.
16. **s = 0 is no trade.** Holiday republications are not prior settlements.

## 13. What this does not touch

- No data dated 2024-01-01 or later. No vault. No CL or NG.
- No index-reweight window statistic: the carved days are reported beside this trade, and C0, R1–R3 and the 2027
  freeze are not read.
- **Deviations** are listed in the output and never replace a verdict.

## Amendment A1 (2026-09-30, before the run, after POWER only)

*Ruled by the coordinator after the runner's POWER step (`data/d709_power.json`) and before `--run`. The runner
(`scripts/stage0_d709_silver_settlement_flow.py`) was not run. POWER reads the fixture blinded from 2011-01-01: only
09:00–11:29 and the decision windows keep prices. It asserts that no fill or exit price from then on is readable, and
its noise is the 2010-07 → 2010-12 window. **No outcome of this study was read. No post-2010 window move, P&L or
return of SI or GC was computed.***

**The old gate (§6):** G4 passes when GC's post-era mean gross has t < +2.00.

**The new gate:** G4 FIRES (FAIL, not the funds) only if **gold's post-era mean, in units of its own trailing daily
σ, is at least silver's post-era mean in the same units.**
- A trade's σ-unit value is g / (σ_d × P_prev × contract multiplier), using §5's point-in-time σ_d and prior
  settlement.
- Otherwise G4 passes.
- GC's t, its mean in σ units, SI's mean in σ units, both σ-unit t's, and what the superseded rule would have said are
  all reported beside the gate.

**Why.**
- §5 of this record predicts that gold carries a real but smaller effect. Under square-root impact it is about 1/3 of
  silver's move in σ units, and about 1/4 of silver's t. It is not zero.
- A test of "gold's t < 2" therefore fires on a true mechanism whenever the effect is large enough, because gold's t
  grows with the effect even when gold stays a quarter of silver.
- POWER measured this. The share of datasets in which G4 held, by β (the share of the ledger's |I| injected into both
  roots):

| β | 0 | 0.155 | 0.31 | 0.62 | 1.0 |
|---|---|---|---|---|---|
| **old G4 (GC t < 2) held** | 0.977 | 0.946 | 0.918 | **0.800** | **0.547** |
| full reading (G1–G5), old G4 | 0.013 | 0.088 | 0.338 | 0.704 | 0.522 |
| **new G4 (A1) held** | 0.449 | 0.670 | 0.864 | 0.987 | 1.000 |
| full reading (G1–G5), new G4 | 0.013 | 0.091 | 0.364 | 0.879 | 0.950 |
| PASS (adds net > 0), new G4 | 0.000 | 0.011 | 0.095 | 0.701 | 0.947 |

- The old gate turned a true mechanism into "FAIL (not the funds)" 20% of the time at β = 0.62 and 45% at β = 1.
- The new gate is the comparison the mechanism actually makes: silver's flow share is about 8× gold's, so silver must
  move more than gold in σ units.

**What the new gate costs.**
- At β = 0 it is a coin flip (0.449). That is harmless, because G1 must also pass.
- At NG's pass-through (β = 0.31), it holds 0.864 of the time against the old 0.918. Silver's σ-unit mean is noisy at
  that effect size, and gold's sometimes matches it.

**Checked in the self-test:**
- On exact series, gold at a quarter of silver does not fire and gold equal to silver fires.
- A rule that never fires, and the superseded t-rule, each raise on that check. The superseded rule fires at a quarter
  of silver, because scaling a series leaves its t unchanged.
- On synthetic bars:
  - gold at a quarter of silver's effect reads PASS, although gold's t was +2.23 and the old rule would have fired;
  - gold at twice silver's effect reads FAIL (not the funds).

**Nothing else changes.** G1–G3, G5, N, the nulls, the readings of §10 and the thresholds stand.

**Also ruled, and not an amendment.** The component line's ρ with #2 (the admitted MACD arm) uses
`run_d667_hike_pause_overlay.load_arm()`, as D685, D699, D707 and D708 did.
- That loader reads the arm's own NQ fixture, including rows from 2024 on.
- It scores only 2016-01-04 → 2023-12-29. That slice is spent (D503).
- This is disclosed in the runner's deviations and in its output. No SI, GC or fund row dated 2024-01-01 or later is
  read.
