# D735 STAGE 0 PRE-REG — NQ breaks from the market: does trading the part of NQ's move the rest of the market does not share beat the drift?

*2026-10-01. The principal, after D733 (the pullback entry, DRIFT ONLY):*
> "That is so bad, have a fable 5.1 agent analyse the results and come up with a better construction, you do the same in parallel"
>
> "Pre-reg D735, build and run it. Go for the widest construction."

- **How the design was made:** two independent analyses of D733 were written (2026-10-01, in the session scratchpad),
  one by this session and one by a Fable 5.1 agent, and compared for the principal.
  - **Both reached the same information source:** D728's finding that NQ continues about three times as strongly when
    ES, YM and RTY are not moving with it.
  - **The Fable agent's design is the skeleton:**
    - the onset of NQ's move relative to the market;
    - a volatility stop;
    - the Frisch–Waugh mechanism regression with a predictive room oracle;
    - the timing null with an efficiency leg;
    - the matched-row bar.
  - **This session's YM leg is added,** as is the TICK-NQ breadth leg (the Fable agent's alternate A).
  - **"The widest construction"** is read as every market leg on disk, the two thresholds and both stop rules, as one
    declared family with a family-wise null. GO in any cell must clear that null.
- **The order (R8):** this record is committed before the runner exists, and the runner before its one run.
- **What it is:** a premise check, oracle first. It chooses no rule.
- **The prior** (before any run):
  - the Fable agent: 25% EDGE, 15% GO;
  - this session: about 15% GO.
  - The likeliest outcome is that the mechanism is real but the edge is unresolved: too small per trade for one MNQ at
    $4.07.

## 1. Why D733 failed, and what this construction changes

D733's own numbers, read by both analyses:
1. **An entry made from NQ's own price path earns what any entry at the same minute earns.**
   - NQ has no intraday mean to buy back to (D724: κ < 0 for every anchor).
   - D733's timing null put it at rank 0.74; the matched-row gain was +$0.02.
2. **Its stop was a noise barrier.**
   - At 0.22 σ_oc from the entry, a driftless walk hits it about 81% of the time; 70% were hit.
3. **The oracles were hindsight quantities.**
   - The "room" oracles (O1, the perfect turn, +$86.62; O2, the pullbacks that held, +$128) would read room on a
     random walk.
   - The same-day follow's +$39.80 is measured on days that extended after arming. An unconditional follow from
     the same arming grosses about $11 (D728's k 1.0 book), so C1's −$31.84 is mostly selection.
4. **The information must come from outside NQ's own price path.**
   - The one outside source on disk with a measured lead is the cross-asset split:
     - NQ's continuation slope is +0.103 on rows where ES, YM and RTY disagree with it, against +0.033 where they
       agree (D728 S1; rank 0.043, not after Holm). The split runs the same way at 9 of 11 clocks.
     - YM's own move gives itself back once NQ's is in the regression (D728 S3), and ES's first half hour reverses
       (D487).
   - **The mechanism, stated so it can be wrong:** a move since the open has two parts.
     - **The part shared with the market** (macro, index arbitrage) does not continue.
     - **NQ's own part** (concentrated mega-cap flow, worked through the day, with no arbitrage pulling the NQ–market
       spread back) does continue.
   - D727's follow and D733's pullback both traded the sum. This trades NQ's own part, at the moment it first becomes
     large.

## 2. Data, seal, conventions

- **NQ:** `fut_NQ_rth_1m`, through D727's own functions:
  - its days, σ_oc (the RMS of the prior 20 sessions' open-to-close moves) and its roll and 380-bar exclusions;
  - D733's OHLC panels.
  - The window is 2016-01-04 → 2023-12-29.
- **Legs L** (each joined to NQ's days by DATE, with D728's join audit and a shifted-join canary):

| leg | source | x_L at minute m |
|---|---|---|
| **ES** | `fut_ES_rth_1m`, D727's `load_root` (its own days, roll and bar rules, σ_oc) | (P_L,m − O_L) / σ_L |
| **YM** | `fut_YM_rth_1m`, likewise | likewise |
| **RTY** | `fut_RTY_rth_1m`, likewise | likewise |
| **EQ** | the three above | the mean of x_ES, x_YM, x_RTY (all three present) |
| **TICK** | Sierra's TICK-NQ (the Nasdaq-100's own up-tick minus down-tick count). It is read with D663's `extract`, with the minute window set to 09:30–15:59, before 2024-01-01 00:00 ET | the cumulative TICK since the open (the sum of the per-minute values of bars 0 … m − 1, carried forward within the session) divided by σ_T, the RMS of the prior 20 NQ sessions' full-day cumulative TICK (at least 15 present) |

- **TICK coverage:** a session is used only if at least 90% of its 09:30–14:29 minutes hold a record. The leg is
  reported as unavailable if fewer than 1,000 NQ days join.
- **The spread:** s_m = x_NQ,m − x_L,m. The simple difference is used throughout; no ρ-fitted residual.
- **Its scale:** σ_s = the RMS of the prior 20 NQ sessions' end-of-day spread s_390 (at least 15 present), shifted one
  session.
- **The standardised spread:** z_s,m = s_m / (σ_s · √(m/390)), D727's time normalisation.
- **Bars:** bar m starts at 09:30 + m. The price at minute m is the close of bar m − 1. An entry at minute m fills at
  the open of bar m.
- **Size and cost:** one MNQ ($2 a point). The cost is D711's `cost_line("NQ")` ($4.07 a round trip), computed by the
  runner. One tick is 0.25.
- **The seal:** nothing dated 2024-01-01 or later is read on any leg. The Sierra read stops at 2024-01-01 00:00 ET
  and raises on any record at or after it.
- **Reads that are NOT made:** D716's and D680's frozen in-sample builders. D711's `load_root` reads the whole rth
  fixture before it filters, so the component line uses D720's `build_f2` (as D733 did). D680's compression C1 is
  named missing.

## 3. The construction: the family (20 cells)

| item | rule |
|---|---|
| trigger | the **first** minute m0 in 10:00 → 14:30 (m = 30 … 300) with \|z_s,m0\| ≥ k. One trade a day per cell |
| k | **1.5** (primary) and 1.0 |
| direction | **D = sign(s_m0)**: long NQ when NQ is stronger than the leg since the open, short when weaker, **whatever the sign of x_NQ** |
| entry | the open of NQ's bar m0, one MNQ |
| stop | **1σ_rem** (primary): entry − D · σ_NQ · √((390 − m0)/390), one remaining-day σ. Checked from bar m0 on; an open through it fills at the open; one tick of slippage against the trade. **none** (the second rule): no stop |
| exit E1 | the stop, or the 15:59 close |
| legs | ES (primary), YM, RTY, EQ, TICK |

- **The cells:** 5 legs × 2 k × 2 stops = **20 cells. The primary is ES, k 1.5, 1σ_rem.**
- **A leg missing on a day:** no trade in that leg's cells that day.
- **The cost arithmetic** (the Fable agent's):
  - Two round trips are $8.14 ≈ 0.037 σ_oc.
  - At k 1.5, with σ_s ≈ 0.45 σ_oc, the threshold is 0.19 σ_oc at 10:00 and 0.59 at 14:30.
  - So the spread must carry a slope of about 0.20 at 10:00, falling to 0.06 at 14:30.
  - D728's disagree slopes are 0.40 / 0.14 / 0.08 / 0.14 at 10:00 / 10:30 / 12:00 / 14:30. The room is adequate at
    10:00 and marginal from 10:30 to 13:00.
- **The expected count:** about 550–750 trades per k 1.5 cell, and 1,000–1,200 at k 1.0.
- **Power:** the per-trade standard error at N 650 is about $7, so the smallest gain this test can detect is about $14
  a trade.

## 4. The mechanism and the room (read FIRST)

**S1, the mechanism regression, per leg.** It is pooled over D727's eleven clocks (10:00 … 15:00), one row per
(day, clock):

> y_NQ = a + β · x_NQ + δ · e, where e = x_L − γ_j · x_NQ, with γ_j by OLS per clock (ES's move orthogonalised on NQ's,
> a decomposition, not a rule).

- **The mechanism predicts δ < 0:** at the same NQ displacement, the more of it the leg shares, the less NQ continues.
- **For TICK the same sign is declared:** a cap-weighted move not matched by breadth is a few mega-caps' flow and
  continues. The "healthy trend" story predicts the opposite, and only the declared sign passes.
- **The null is enumerated** (SE 0). e is rolled across days (offsets 20 … n − 20), with x_NQ and y fixed. The rolled
  e keeps its norm and its zero mean, so the null's design shares the observed one's conditioning (D614's lesson: never
  rotate the raw, correlated x_L).
- **MECHANISM (per leg):**
  - δ̂ at rank ≤ 0.05 (p_low ≤ 0.05);
  - and a day-clustered t ≤ −2;
  - and Holm over the five legs' p_low ≤ 0.05.
  - δ by clock is reported.
- **O1, the room, per cell:** the fitted model's expected gross at the cell's realised trigger rows, in the trade's
  direction. It uses the per-clock fit (β̂_j, δ̂_j at the nearest of D727's clocks):
  mean over trades of D · (β̂_j · x_NQ,m0 + δ̂_j · e_m0) · σ_NQ · $2.
  - **If O1 < 2 × cost ($8.14), the cell reads NO ROOM.** This is recorded first, whatever its book says.
  - On a process with no information, O1 reads only the drift budget, so it can fire.
- **O2, the drift budget, per cell:** D727's β at the nearest clock × x_NQ,m0 × σ_NQ × $2, signed by D. It is what
  the drift alone would pay at those rows. The entry's excess is the book's gross minus O2.

## 5. The controls

- **C2a, the timing null (per cell; primary).**
  - Every trade's entry minute m0 and its stop rule are moved to day d + j, for j = 20 … n − 20 (enumerated).
  - It enters at that day's bar-m0 open, in that day's own drift direction sign(x_NQ,m0), and exits E1.
  - It is skipped where x_NQ is 0 or not finite.
  - **The statistics are the mean net per trade AND the efficiency Σg/Σ|g| (gross).** Both must clear p95: the
    trigger picks large-|s| days, which may be volatile days, and a mean alone is anti-conservative for a
    size-selecting filter (D711-A1).
  - It is reported pooled and by |x_NQ,m0| bin (< 0.5, 0.5–1, 1–1.5, ≥ 1.5).
- **C2b (reported, and the right-quantity check).** The same moved schedule, entered in sign(s_m0) of the target day.
  **Its offset 0 must reproduce the observed trades exactly.**
- **The family null.** At each offset, the maximum over the 20 cells of C2a's mean net. The family p95 is its 95th
  percentile. Holm is applied over the 20 cells' C2a p_high.
- **Matched rows (per cell; part of EDGE).**
  - The rows are every (day, 5-minute minute m = 30, 35 … 300) with x_NQ,m ≠ 0. Each row is entered in sign(x_NQ,m)
    at bar m's open, under the cell's stop rule, and exits E1.
  - The matching cells are entry hour (10 … 14) × the |x_NQ| bin.
  - **The gain** is the trade-weighted mean, over matching cells holding a trade and at least one row, of (the trades'
    mean net − the rows' mean net).
  - **Its SE** is from a day-block bootstrap: 2,000 draws, seed 735, resampling days with replacement, with trades and
    rows together.
- **Aligned and counter.**
  - Aligned trades have sign(s_m0) = sign(x_NQ,m0); counter trades do not (x_NQ,m0 = 0 counts as counter).
  - For counter trades, **C1, the same-day follow** from m0 in sign(x_NQ,m0) under the same stop rule, is paired
    against the trade, giving the paired mean and t. It is the mechanism's whole claim on those days: the spread's
    direction beats the drift's from the same minute.
  - (For aligned trades the follow is the trade, so C1 is not computed.)
- **The mirror (per cell):** the same entry and stop distance against D. This is the sign audit in money.
- **SAME TRADE (per cell, informational).**
  - D727's follow at minute resolution: the first minute in 10:00 → 14:30 with |z_NQ| ≥ 1.0, from that bar's open to
    the close, in its sign, with no stop.
  - It reports the share of the cell's trades on the same day and side, and the daily-net ρ.
  - **ρ ≥ 0.7 reads SAME TRADE:** the signal added a clock, not information, and the principal has declined that
    trade.

## 6. Readings (declared now)

| reading | condition (per cell; the primary's is the headline) |
|---|---|
| **NO ROOM** | O1 < $8.14. Recorded first; nothing below is interpreted for that cell |
| **MECHANISM** (per leg) | §4 |
| **EDGE** | all of: (i) mean net > 0 at NW t ≥ 2 (day order, 5 lags); (ii) mean net AND efficiency above C2a's p95, pooled; (iii) mean net above p95 in ≥ 3 of the \|x_NQ\| bins holding ≥ 30 trades (in every such bin when fewer than three qualify, and at least one must); (iv) **the matched-row leg PASSES:** gain ≥ $4.07 (one round trip beyond the drift entry at the same moment) and gain / SE ≥ 2; (v) the counter subset's mean gross ≥ 0 when it holds ≥ 30 trades |
| **UNRESOLVED** | (i)–(iii) and (v) hold, the matched-row gain is > 0, and gain + 2 SE ≥ $4.07, but (iv) fails (D373's rule) |
| **DRIFT ONLY** | mean net > 0 and neither of the above |
| **NOTHING** | otherwise |
| **GO** to a rule design with the principal (per cell) | all of: EDGE; MECHANISM on its leg; C2a's mean net above the **family** p95; daily net Sharpe ≥ 0.4 at one MNQ; ≥ 5 of 8 years positive; the largest year < 50% in dollars AND in volatility units (D729's `year_concentration`, with scale = σ_NQ × $2 per trade, known before the trade; **binding here**); the mean net ex-2022 > 0; not SAME TRADE |

- **A non-primary cell can carry GO only through the family p95.** That is what makes the 20 cells one test.

**Stopping rule (declared now; a proposal to the principal, not a decision).** Closing "intraday entry timing on NQ"
as an axis, not a construction, is proposed under R15 if all three hold:
- the primary reads NOTHING or DRIFT ONLY, and its matched-row gain + 2 SE < $8.14;
- no leg reads MECHANISM;
- no cell reads GO.

Every source on disk would then have been tried as an entry conditioner:
- own-path timing (D697, D700, D724, D725, D733);
- participation (D730, D731);
- size (D720, D724);
- flow (D715, D717);
- cross-asset agreement (D728, and this record).

**If MECHANISM reads but EDGE does not:** the information exists and is limited by cost, not by signal. The record
says so, and k, the stop and the clock window are NOT re-tuned.

## 7. Reported (CLAUDE.md's four groups; every cell unless named)

- **Performance:**
  - net and gross;
  - daily Sharpe and Sortino (net and gross);
  - max drawdown;
  - P3a at $50k and $150k;
  - the mean move per trade against 2c.
- **The trade distribution:**
  - trades, mean, median, win rate, payoff, skew, kurtosis;
  - the symmetric 1% trims (ex-top, ex-bottom, both).
- **What the winners depend on:**
  - years: net by year, years positive, the largest-year share in dollars and in volatility units, ex-2022;
  - the entry-hour table;
  - aligned against counter;
  - up against down;
  - stopped share.
- **Nulls:** C2a and C2b, p05 / p50 / p95 and rank, pooled and by bin; the family p95; Holm.
- **The four exits reported beside E1** (every cell):
  - no stop;
  - a 0.5 σ_rem stop;
  - a 60-minute time exit;
  - the signal's own exit: flat at the open of the first bar m > m0 at which sign(s_m) ≠ D, else the close.
- **The primary's MFE/MAE** at +15, +30 and +60 minutes and at the close.
- **O1 and O2** per cell, against the book's gross.
- **The component line** at one MNQ: daily ρ with NQ F2 (D720's `build_f2`) and with D727's minute follow. D680's C1 is
  named missing.

## 8. The runner's assertions (all must hold before anything is written)

- **Lag:**
  - a second implementation rebuilds s_m0, z_s,m0 and the trigger from both roots' raw rows, reading only bars up to
    m0 − 1, on 60 sampled trades per leg;
  - a canary that reads bar m0's own close must raise;
  - the shifted date join must raise.
  - For TICK, the second implementation sums the raw extracted minutes.
- **Sign, in money:**
  - a hand-built day where NQ rises and the leg is flat gives a long that pays;
  - the mirror's sign is opposite;
  - a stop on a gapped open fills at the open less a tick.
- **Right quantity:**
  - NQ's panel reproduces D727's known answer (1,941 days, β at 10:00 to 1e-12);
  - C2b's offset 0 equals the observed book exactly;
  - the FW null's offset 0 equals δ̂.
- **The FW null's size, synthetic** (before the run):
  - 100 worlds where y depends on x_NQ only: δ clears its rank-0.05 bar in ≤ 10 of them;
  - 100 worlds with a planted δ < 0: it fires in ≥ 90.
- **A self-test that cannot fail is worse than none:** each audit is shown raising on a deliberately broken input.
- **Run-once:** the runner refuses if its output exists.
- **Projected wall time:** a few minutes (D733's vectorised placebo × 20 cells, five regression nulls, one bootstrap
  per cell). It is a run-once job, so no optimisation pass. The cells run in threads (numpy).

**The output:** `data/stage0_d735_nq_breaks_from_the_market.json` (aggregates only; no per-date TICK series).
