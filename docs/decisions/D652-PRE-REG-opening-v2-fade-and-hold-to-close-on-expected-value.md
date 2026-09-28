# D652 — PRE-REG: the opening model's v2, a separate construction. A gap fade at 09:45 and a hold to the close from 10:30, each traded on expected value from a model of its own trade's outcome

*2026-09-28. The principal, after the external-evidence round
([`docs/research/opening-v2-external-evidence.md`](../research/opening-v2-external-evidence.md)): "lets make those
changes and test them as a separate model". The principal chose the vault **after an in-sample test**, and the S-A
observables **plus A4 rescaled**. Committed ALONE, before any runner exists (R8). **No v2 model has been fitted and
no v2 trade scored.** Phase 4 (D645) has not run; no agent pressure has been compared with a label or a return.*

## 0. Where this comes from — a post-hoc design, disclosed as one

- **Its three parts were suggested by reading the in-sample.** D646 (S-A fails accuracy) and D647 (the oracle, the
  deciles, the gap fill inside the hour) are OA-A8's parked v2 list: V2-1 the target, V2-2 the decision rule, V2-3
  the stop. The research round added the entry clocks, the liquidity scaling of A4 and the 0DTE break.
- **OA-A8.3 said a v2 item waits for a trigger after Phase 4, and one item only.** The principal has chosen to run
  v2 now, as a separate construction outside D645's family. OA-A10 records the ruling. D645, Phase 4 and OA-A8's
  diagnostics are unchanged.
- **Therefore the in-sample run below can only kill, never confirm.** The in-sample was read for these designs; a
  positive in-sample number is the reason to spend the vault look, not evidence (as D649 §0).

## 1. Two cells

| | **V2-F: the gap fade** | **V2-C: the continuation, held to the close** |
|---|---|---|
| t0 | 09:45 | 10:30 |
| direction s | −sign(gap), towards the prior close | d0(10:30) = sign(price at 10:30 − open) |
| eligible row | usable, gap ≠ 0, and the prior close lies ≥ 2 × cost ahead (below) | usable, d0 ≠ 0, σ_h defined |
| entry | the close of the bar starting at t0 (D645 §4's "close of bar t0+1") | the same |
| exit | **the target: the prior close**; else the time stop, the close of the bar starting 60 minutes after the entry bar. **No price stop** | **the RTH close** (the 15:59 bar's close); else **the stop at 1.5 × σ_h** from the entry |
| label y | 1 if the target is reached before the time stop | 1 if the trade's net P&L > 0 |

Both cells:
- **Days:** D644's usable sessions from 2016-01-04, with OA-A6.8's exclusions read at the cell's t0 (≥ 90% of the
  09:30 → t0 bars; the 09:30 bar present). ES and NQ pooled, shared coefficients, a market dummy, 1 micro each.
- **Prices:** OA-A6 (open = the 09:30 bar's open; the prior close = the prior session's 15:59 close; price at t =
  the close of the bar ending at t).
- **Cost:** D645's line (OA-A5): D508's crossing + $3 + one adverse tick per round trip, `COST_USD` / (dollars per
  point × the entry price), in bp. **The tick is in the cost, not in the price.**

**V2-F's eligibility, point-in-time:** dist = s × (prior close − price at 09:45) in points, cost_pts = `COST_USD` /
dollars per point. Eligible if **dist ≥ 2 × cost_pts**: the most the trade can make must clear twice its cost (the
rule D649 uses, reasoned from the cost, not fitted). At the entry, if the entry price is already at or beyond the
prior close, the trade is cancelled (0).

**V2-F's fills:** the target fills at the prior close, never better (a bar that opens through it still fills at the
target). The time-stop fill is the bar's close.

**V2-C's stop:** σ_h is the standard deviation of ln(close of 15:59 / close of the entry bar) over the market's 20
prior eligible sessions (at least 15, else not eligible). The stop sits at entry × (1 − s × 1.5 × σ_h). It fills at
the stop price, or at the bar's open when the bar opens through it; intra-bar, the stop is taken first. This is
D645's stop convention.

## 2. Features (at t0, from bars closing by t0; prior-session quantities from earlier rows only)

Every signed feature is multiplied by **s, the cell's own trade direction**. For V2-C this equals D645's × d0.

1. `gap_atr` = gap × s / ATR20 (OA-A6.2);
2. `loc_with`: the open lies beyond the prior RTH extreme in s's direction (1/0);
3. `loc_against`: the open lies beyond the extreme against s (1/0);
4. `r_sigma` = r(09:30 → t0) × s / σ, σ as D645 §2's feature 4;
5. `vol_z`, as D645 §2's feature 5;
6. **`z4s` = z4\* × s, A4 rescaled by liquidity:**
   - `P4* = −G × (open − prior close) / DV20`;
   - G is OA-A7.4's dealer gamma (the `G` column of `data/opening/agents.csv`, from the same code);
   - DV20 is the mean over the market's 20 prior sessions (at least 15) of Σ close × volume over that session's
     09:30 → t0 bars, the window-matched trailing dollar volume (Barbon & Buraschi's denominator; **never the same
     day's volume**, which is itself a trend-day tell);
   - z4\* = `agents.standardise(P4*)` per market (OA-A7.3);
7. **`z4s_post` = z4s × 1{session ≥ 2022-05-11}:** the 0DTE break, dated from the calendar. It is the first session
   on which every weekday carries an SPX expiry (Cboe added Tuesday expiries on 2022-04-18 and Thursday expiries
   on 2022-05-11). One date for both markets; it is not chosen from any result.

Plus the market dummy: 7 features + 1, within D645's budget of 11. A row with any feature not finite is dropped, as in
D645's `dataset`.

## 3. The model and the walk-forward (D645 §3, binary)

- Binary logistic regression, L2, with no class weights and no resampling. Features are standardised on each
  training window's own mean and standard deviation.
- **In-sample:** train 252 sessions, test the next 63, rolling by 63 over the union calendar of the cell's eligible
  sessions. Both markets' rows of a session always fall in the same window. The last test window stops at
  2025-02-28.
- **C** ∈ {0.001, 0.01, 0.1, 1, 10} is chosen inside each training window: 5 contiguous blocks, the lowest mean
  validation log loss, ties to the smaller C.
- **Base rate:** the training window's frequency of y = 1, per market.

## 4. The decision: expected value, fixed from the training window

- **V2-F:**
  - **EV = p̂ × (dist_bp − cost_bp) + (1 − p̂) × m_T**, where dist_bp and cost_bp are dist and cost_pts in bp of
    the price at 09:45;
  - m_T is the mean net bp of the training window's eligible trades that did not reach the target, pooled over
    both markets.
- **V2-C:**
  - **EV = p̂ × m⁺ − (1 − p̂) × m⁻**, where m⁺ is the mean net bp of the training window's winning eligible trades
    (net > 0), and m⁻ is minus the mean of its losing ones;
  - both are pooled.
- **Trade iff EV > 0.** Otherwise the row is flat and scores 0.
- There is no sizing (one micro). m_T, m⁺ and m⁻ come only from training rows, whose trades are complete before the
  test window starts.

## 5. What each run reports (the in-sample run and the vault run alike)

**The statistic, per cell:** per session, the mean over the two markets of the net bp. A row not eligible, or not
traded, scores 0.
- **policy:** the EV rule;
- **always:** every eligible row traded, the construction without the model;
- **diff:** policy − always, paired by session;
- the Newey–West HAC t, lag 5 (D645's `nw_t`).

**Beside it, all four groups (CLAUDE.md) and R17:**
- **Performance, net and gross:**
  - Sharpe and Sortino of the daily dollar P&L at one MES/MNQ;
  - exposure (sessions traded, minutes held);
  - vol and maxDD;
  - the mean move per trade against 2c;
  - the breakeven cost.
- **The trade distribution:**
  - n, mean, median, win rate, payoff, holding time, skew and kurtosis;
  - the three 1%-trimmed means (ex-top, ex-bottom, both).
- **What the winners depend on:**
  - by year and by market;
  - before and after 2022-05-11;
  - the top trade named with its bar.
- **Classification:**
  - log loss against the base rate, and the Brier score;
  - AUC with a day-block bootstrap 95% interval (2,000 resamples of sessions, seed 652);
  - a 10-bin reliability curve.
- **Null, reported, not gating:**
  - p̂ is shuffled across rows within market × year (1,000 draws, seed 652), and the policy's per-session mean is
    recomputed each time;
  - the report gives the null's p50 and p95, and the p95's bootstrap SE;
  - a margin within 2 SE is UNRESOLVED (D373).
- **The component line (CLAUDE.md, the books):**
  - net and gross Sharpe and Sortino at one micro, with the cost in dollars computed by the runner;
  - the hit rate and the skew;
  - the correlation with each component in `docs/COMPONENTS_PROP.md` whose daily series is on disk; the missing
    ones are named.
- **Robustness, reported only:**
  - δ = 1 bp in place of 0;
  - 2× cost;
  - the stress fill (the worst close of t0+1 … t0+5);
  - V2-F with D645's 0.5 × range stop;
  - V2-C with no stop;
  - A4 unscaled (`z4` × s) in place of z4\*;
  - the break moved ±63 sessions.

## 6. The in-sample run: once, and it can only kill

- It runs **after D645's Phase 4 run**, so no v2 output exists before Phase 4's one look.
- **A cell is carried to the vault only if both hold on its in-sample out-of-sample rows:**
  - policy mean > 0;
  - diff > 0.
- **A cell that fails is closed without spending the vault.** If neither cell is carried, v2 closes and slot 9 is
  not taken.
- Its RESULT record is written before anything is frozen.

## 7. Power, before the look is spent (memory: compute the holdout's power before spending it)

- `--power`, seed 652, on each carried cell's in-sample out-of-sample per-session series (policy and always,
  paired):
  - 20-session blocks drawn to the vault's length, **390 sessions**;
  - the edge kept is s_e ∈ {1, 0.5, 0.25, 0}, applied by shrinking the series' mean;
  - 2,000 draws per row;
  - the vault rule of §8 is applied, and the report gives PASS, FAIL and UNRESOLVED rates.
- It is optimistic in the same way as D649 §4: the blocks resample the in-sample's regimes.
- **If PASS at s_e = 1 is below 0.5, the RESULT headline says so.** The vault look is spent only on the principal's
  word, whatever the power.

## 8. The vault read: once, in the joint run (A10), on the principal's word

- **The walk-forward continues into the vault.** Test windows of 63 eligible sessions start at the first session
  on or after 2025-03-01. Each is trained on the 252 eligible sessions before it, some of them in the vault, whose
  outcomes are complete by then. The last window ends at 2026-09-18.
- **Inputs:** the same code with the cut moved:
  - the ES/NQ bars;
  - G from `build_opening_agents.dealer_gamma` over the vault sessions. The option and settlement fixtures run to
    2026-09-09/10, and the 2026-10-09 top-up extends them.
  - The vault inputs are proved first to reproduce the in-sample's G and features.
  - **If they cannot be built, the cell is not scored,** and the gap is written up.
- **Per carried cell:**
  - **UNRESOLVED** if fewer than 30 traded rows (the look is spent);
  - **PASS** if the policy mean > 0 with **one-sided HAC p < 0.05 after Holm across the carried cells**, and the
    diff > 0;
  - **FAIL** otherwise.
- **Programme level:**
  - a new family, **slot 9** (α 0.005): "opening V2 (D652)";
  - the promotion check, Holm-adjusted one-sided p ≤ 0.005, is reported.
  - The slot is registered in the runner's commit (`data/programme_registry.json` and its test), only once a cell
    is carried.
- **One look.**
  - `--vault` refuses without the principal's word, or unless the freeze verifies;
  - the freeze is `data/opening/FROZEN_v2.json`: the runner's sha256 and this record's (LF-pinned), the
    parameters and the carried cells;
  - it refuses a second opening.
- **A PASS** is the out-of-sample confirmation R8 requires, and admits nothing by itself (components ledger,
  hurdle P). **A FAIL** closes v2: no re-tuning of the clocks, the exits, the rule or the inputs afterwards.

## 9. The runner's assertions, each proved to fire in `--selftest` on a deliberately broken input

1. **Lag:**
   - D645's leak canary at each cell's t0: a bar at or after t0 is corrupted, and the feature row must not move;
   - a second canary on z4\*: the same day's 09:30 → t0 volume is corrupted, and DV20 must not move;
   - no training row falls in the test window;
   - the out-of-sample predictions differ from a fit that saw the test rows;
   - **the traded set is re-derived** from p̂, dist and the training window's m values by a second implementation
     that never calls the decision function.
2. **Money:**
   - a favourable move pays long and short;
   - V2-F trades towards the prior close;
   - the target never fills better than the prior close;
   - V2-C's stop never fills better than the stop.
3. **Right quantity:**
   - **the label equals the scorer on every row:** y_F is "the target was reached" in the same simulation that
     prices the trade, and y_C is net > 0 from that price (the repository's `assert_matches_scorer` rule);
   - net differs from gross;
   - diff is policy − always, not the reverse;
   - m_T, m⁺ and m⁻ are unchanged when the test rows' outcomes are scrambled.
4. **The oracle positive control:** trading exactly the rows with y = 1 must give a positive net mean for each cell,
   or the engine is broken.

**Modes:**
- `--selftest`;
- `--dry-run` (synthetic bars, writes nothing);
- `--run` (the in-sample, once);
- `--check` (the rebuild equals the committed output);
- `--power`;
- `--freeze`;
- `--vault`.

**Trials rows:** `data/opening/trials.csv`, family "opening V2 (D652)", one row per cell and run.

## 10. What this does not touch

- D645 (its stages, tests, Gate O1 and the one Phase 4 run), OA-A8's diagnostics and its parked list, and OA-A9.
- The vault seal: no vault or post-vault ES/NQ price, option or flow is read by this line before the joint run.
- **Deviations** are listed in the output and never replace a verdict.
