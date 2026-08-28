# D249 — The inverse wedge breakout

**Status:** Pre-registered — committed BEFORE any runner exists and BEFORE any cell is scored
**Date:** 2026-08-28
**Area:** Strategy research

---

## Provenance, stated first because it decides what this record may claim

**This is complement-chasing, and it is registered as such.** A wedge-breakout rule was proposed —
arm two conditional trades at ±2 ATR from the point where the pivot regression lines cross, long
the up-break and short the down-break. **Measured, that design is backwards**: down-breaks return
+14.6% to +18.3% annualised at every horizon and up-breaks straddle the market baseline, so the
spread is negative everywhere. **What is registered here is the inverse — LONG the down-break —
which is the complement of a construction that failed.**

**[D246](D246-the-search-protocol-for-s3.md) Constraint 3 is therefore binding and is obeyed
literally:**

> *"A candidate that is the complement or inverse of a failed cell is not eligible under this
> protocol. It may be registered separately, on its own merits, with that provenance stated."*

**So: this is NOT S3.** It is a separately-registered candidate. D246's protocol, its 8-cell
search budget and its reserved validation cohort are untouched by this record, and nothing here
may be presented later as having executed that protocol.

**D245's never-seen wide-universe cohort is NOT SPENT HERE.** D246 reserves it for S3 and for one
candidate only. **This study does not load `universe_wide_w1_raw` or `universe_wide_w5_raw` and
the runner will assert it did not.**

### The validation set instead, and why it is legitimate

**The 60-ETF instrument holdout** (`universe_holdout_extended_raw`), which shares **zero tickers**
with the mined 57.

**The wedge rule has never touched the 60.** Every prior use of that cohort (D237 for S1, D242 for
A0/A2/C0) scored the Impulse-MACD recovery rule and the uptrend-onset rule. A pivot-regression
convergence rule with an ATR-offset trigger has no parameter, threshold or constant inherited from
either, so for **this** candidate the 60 are genuinely out of sample.

**The residual contamination, stated honestly and not minimised.** The cohort is no longer pristine
*at the universe level*. It has been looked at three times; its behaviour, its correlation to the
57 (+0.978) and the fact that it is friendly to long-flat equity books are all known to me. **A
pass here is weaker evidence than the same pass would have been in D237**, and this record does not
get to claim otherwise. What it still tests cleanly is instrument-generality of *this* rule.

**And a second limitation, declared now:** the extended 60 fixture starts later than the extended
57. **The 57 give 3,222 live bars from 2013-11-01; the 60 give 1,963 from 2018-11-01.** The
validation window is 7.8 years against the screen's 12.8, entirely inside the era both S1 and S2
were built in. **This is an instrument holdout and not a time holdout**, and the screen restricted
to the validation span is reported beside it so the comparison is like-for-like.

---

## The measurement this is built on — verified before registering, per R9's corollary

**R9's expensive half says a number that motivates a pre-registration deserves the same scrutiny as
one that comes out of it.** The proposer's anatomy was therefore rebuilt from scratch, R9-compliant
— arm state, both lines and ATR all read at `t−1`, the trigger comparing `C[t]` to a level fixed at
`t−1`, and the forward return measured from `t+1`. **It reproduces.**

| | proposer | **this rebuild** |
|---|---:|---:|
| converging at all, share of live cells | 51.2% | **50.7%** |
| channel width, p50 in ATRs | 2.63 | **2.64** |
| armed cells at `k = 2` | 10.87% | **10.32%** |
| armed episodes at `k = 2` | 2,870 | **3,021** |
| UP triggers | 1,052 | **1,097** |
| DOWN triggers | 1,444 | **1,474** |
| market baseline | +7.84%/yr | **+7.84%/yr** |

Forward return after a trigger, annualised, 57 ETFs, 12.8 years:

| horizon | UP break | **DOWN break** | spread |
|---:|---:|---:|---:|
| 5 | +7.16% | **+15.35%** | −8.18% |
| 10 | +7.41% | +9.13% | −1.72% |
| 21 | +9.33% | **+15.15%** | −5.81% |
| 42 | +10.60% | **+18.29%** | −7.69% |
| 63 | +9.10% | **+18.09%** | −8.99% |

**The finding replicates in full: the spread is negative at every horizon and the proposed design
is pointed the wrong way.** The residual differences are convention noise in a reconstruction —
under two points on any UP leg, under 5% on any count.

### One thing the reconstruction had to pin down, and it changes the answer

**"±2 ATR from the crossover point" is ambiguous, and the two readings do not agree.** The
regression apex — the bar index where the lines actually intersect — sits a **median 113 bars ahead**
of the arming bar, so the apex *price* is a long extrapolation. Scored that way the effect is much
weaker (UP +9.89%, DOWN +16.79% at 63 bars, spread −6.90%) and the trigger counts are wrong
(891 / 1,909).

**The reading that reproduces the proposer's numbers is the channel midline at the current bar** —
`(upper + lower) / 2` — which is where the lines are converging *to*. That is the definition
registered below, it is named here rather than discovered later, and it is also the one that makes
the arming arithmetic coherent: a ±2 ATR trigger clears a channel of half-width `w/2` exactly when
`w < 4·ATR`, and `k = 2` sits comfortably inside that.

---

## THE ERROR IN THE MOTIVATING CLAIM — hurdle E does not clear

**This is the one thing in the proposal that is wrong, and it is the thing the proposal called its
single novel property.** The claim was:

> *"At `k = 2` the construction clears hurdle E at 50.4 entries/symbol — the first construction in
> this programme to do so (S1 has 20, S2 has 5)."*

**50.4 is setups per symbol, not entries per symbol, and the inverse rule does not trade most of
them.** Three separate deductions, all measured before this record was written:

1. **Only the DOWN breaks are traded.** The long-only inverse drops the up-break leg entirely, so
   1,474 of 2,571 triggers survive — **58%**.
2. **Not every armed episode triggers at all.** 3,021 episodes produce 2,571 triggers.
3. **Overlapping trades on one symbol are suppressed.** A trigger arriving while that symbol
   already holds a wedge position is skipped, which at a 42-bar hold removes a further third.

| | pooled entries | mean / symbol | **min / symbol** | hurdle E |
|---|---:|---:|---:|:--:|
| **57, 21-bar hold** | 936 | 16.4 | **5** | **FAIL** |
| **57, 42-bar hold** | 718 | 12.6 | **4** | **FAIL** |
| 60, 21-bar hold | 561 | 9.3 | **1** | **FAIL** |
| 60, 42-bar hold | 426 | 7.1 | **1** | **FAIL** |
| *S1 on the same 57* | *2,374* | — | *20* | *fail* |
| *S2 on the same 57* | *393* | — | *5* | *fail* |

**Hurdle E is `min_entries_per_symbol >= 30`, and this construction reaches 5.** It is *worse* than
S1 on the same fixture and level with S2. **The claim that this is the first construction here to
clear E is false, and it is corrected before it can be built on rather than after.** The rest of the
design is unaffected — the corrected number is registered as prediction **T-a** so the record scores
itself on it.

---

## The rule

```
For each instrument, on DAILY bars, in LOG space:

    lows  = confirmed swing lows  in the trailing 252 bars   (k = 3)
    highs = confirmed swing highs in the trailing 252 bars

    g_lo, i_lo = OLS slope and intercept of log(price) on bar index, over lows
    g_hi, i_hi = the same, over highs

    lower(t)  = i_lo + g_lo * t
    upper(t)  = i_hi + g_hi * t
    width(t)  = upper(t) - lower(t)
    centre(t) = (upper(t) + lower(t)) / 2
    atr(t)    = ATR(21) in log units

    CONVERGE(t) := g_hi < g_lo  AND  width(t) > 0     the lines close toward a crossover
    ARMED(t)    := CONVERGE(t)  AND  width(t) <= 2 * atr(t)

    trigger levels, all read at t-1:
        up(t-1) = centre(t-1) + 2 * atr(t-1)
        dn(t-1) = centre(t-1) - 2 * atr(t-1)

    DOWN BREAK at bar t  :=  ARMED(t-1)  AND  log C[t] < dn(t-1)
    UP   BREAK at bar t  :=  ARMED(t-1)  AND  log C[t] > up(t-1)

    ENTRY   the first DOWN BREAK of an armed episode; exposure begins at t+1
    EXIT    age >= HOLD bars   (per cell), or a stop (W3 only)

    UP BREAKS ARE RECORDED AND NEVER TRADED.
```

**Long-flat, `lag = 1` by construction, equal-weighted across the universe, the shared 1,000-bar
warm-up, D217's per-symbol IBKR costs and dividend-adjusted scoring frame** — so this, S1 and S2 are
scored on identical bars and ρ means something.

**One trade per armed episode and no overlapping trades on one symbol.** A second down-break inside
the same episode, or any break arriving while that symbol is still held, is skipped. Without this
the book would double-count a single structural event.

**Why the short leg is dropped and not tested.** Up-breaks show no edge in either direction and
[D238](D238-the-short-side-mirror.md) established the general case on this universe: the worst bars
any of these constructions can isolate still return +0.85%/yr, at a breakeven borrow of −6.90%/yr.
**Shorting a signal with no edge, against +7.84%/yr of drift, is a decision already made.**

### Every constant, and where it comes from

| constant | value | source |
|---|---|---|
| pivot `k` | **3** | D173, fixed. Not a free parameter |
| regression window | **252** | one year. D240's, unchanged |
| minimum pivots in a fit | **3** | D240's, unchanged |
| ATR window | **21** | D240's, unchanged |
| **arming threshold** | **width ≤ 2·ATR** | derived: a ±2 ATR trigger clears a channel of half-width `w/2` iff `w < 4·ATR`. **Not swept** — 1 and 3 are reported as anatomy above and are not cells |
| **trigger distance** | **2·ATR** | the proposer's, unchanged. **Not swept** |
| holding rule | **21 / 42 / 42+stop** | the three cells. See below |
| W3's stop | **entry − 2·ATR**, ATR frozen at entry | D240's `FLOOR_ATR` reused at the same value |

---

## Cells — three, and every one is in the ledger

| | rule | why this and not another |
|---|---|---|
| **W1** | down-break, hold **21** bars | one trading month; the shortest horizon at which the measured DOWN premium is large (+15.15%) |
| **W2** | down-break, hold **42** bars | two months; where the measured premium peaks (+18.29%) |
| **W3** | **W2 plus a stop at entry − 2·ATR** | the only overlay registered. Close-to-close, decided at the close of `t`, effective `t+1` — D235's convention, since daily OHLC cannot tell a touch from a gap |

**63 bars is NOT a cell** even though it measures marginally better than 42 at the anatomy stage,
because three horizons is already a sweep and a fourth buys nothing but multiplicity. **5 and 10 are
not cells** — they cannot survive costs at this turnover. Both exclusions are declared here rather
than dropped quietly.

---

## Hurdles

- **H — the matched-count rotation null, and it carries the verdict.** Each cell must beat its
  rotation null at the **95th percentile on net excess Sharpe AND on net total return**. Same
  exposure, same turnover, same holding periods, wrong bars. `rotation_nulls` from
  `run_short_mirror.py`, reused unchanged, including D238's money and volatility legs — **the money
  leg is a hurdle here, not a diagnostic**, because Sharpe is `mean/sd` and a book that concentrates
  exposure after 2-ATR declines is by construction exposed in noisy weather.
- **H-BEST — the multiplicity leg, and it is not optional.** Three cells are screened, so the best
  of the three must also beat a **best-of-three rotation floor** (D228: one shared offset vector
  across cells, `max` taken per simulation). **D240's stop cleared at the 99.6th percentile with no
  correction and failed out of sample at the 71.7th. That must not happen twice.**
- **H-OVL — R7, scoped to W3 only.** W3 modifies a book W2 already chose, so a rotation null is the
  wrong control for its stop. It must **additionally** beat the **matched-exit-count trade-level
  overlay null** — keep W2's book, cut the same number of trades short at random trades and random
  points inside their own spans. `null_book` from `run_uptrend_onset.py`, reused unchanged.
  **W3 passing H does not license the stop; only H-OVL does.**
- **E — asserted, and predicted to fail.** ≥100 pooled entries and ≥30 per symbol. Computed per
  symbol and reported per symbol, not just pooled. See the correction above.
- **P — beat buy-and-hold** on the same names over the same span, dividend-adjusted, on excess
  Sharpe.
- **Costs.** Gross and net reported side by side, plus the **breakeven cost in basis points per
  side**. A cell that only works at zero friction is not a candidate — the leg that killed D247.
- **The validation, which is what R8 would require of any promotion.** H, P and E are recomputed on
  the 60, with an **anti-triviality floor at 25% of the screened delta over buy-and-hold**, set the
  way D237 and D242 set theirs.

**Reported, never hurdles:** the √f decomposition, exposure, deployable return
(`CAGR + rf·(1 − exposure)`), max drawdown, Calmar, the paired block bootstrap on each cell's own
Sharpe and on its delta over buy-and-hold, and **the effective independent instrument count**.

### The sample size is reported as breadth, not as a trade count

**`1/(wᵀRw)` at equal weights, `effective_instruments` from `run_book_wide.py`.** D245 measured this
at **2.23** for the 57 and found it *falls* to 2.02 as the universe grows to 486 names. **Nine
hundred pooled trades across 57 names that correlate at ~0.4 are not 900 independent observations,
and this record will not quote them as a sample size.** Both numbers are reported together
everywhere.

---

## The overlap analysis — as important as any return number here

**The decisive question is not whether this makes money. It is whether it is S1 wearing a
different trigger.** A 2-ATR break below a converging channel selects a name that has just fallen
hard; S1 buys names at or below their volatility channel that have turned. **Those populations may
be nearly the same set of bars**, and if they are, this is a re-weighting of arm one and not a third
arm — exactly what D246 Constraint 1 forbids for S3 and what this record must answer for itself.

Four measurements, all on the 57 over the identical span, all registered here:

- **O1 — bar-level overlap, both directions.** Of the bars this rule holds, what share does S1 also
  hold (`P(S1 | wedge)`)? And of S1's held bars, what share does this rule hold (`P(wedge | S1)`)?
  **Reported against the chance baseline** — S1's own exposure is 18.2%, so `P(S1 | wedge) = 18%` is
  *independence*, not overlap. D242 reported the same statistic for S2 at **8.9%, less than half
  chance**, which is what a structurally disjoint arm looks like.
- **O2 — the correlation of the two daily excess-return streams**, with a **paired block bootstrap
  CI on ρ itself**: block 21, both arms recomputed on **identical resampled dates**, the programme's
  standard. A point estimate of ρ with no interval is exactly the failure R6 was written for.
- **O3 — the diversification condition, `SR_B > ρ · SR_A`**, evaluated with the measured ρ and both
  Sharpes, against **S1** and separately against **S2**. D246 requires the S2 comparison for
  anything claiming to be a third arm, since S2 is the entry with out-of-sample support.
- **O4 — the direct answer, in one line, with the number that carries it.** **If overlap exceeds
  50% in either direction and ρ is high, this record says so bluntly and closes the candidate**,
  regardless of what the Sharpe did. That is the most useful outcome available here and it is
  committed in advance so it cannot be softened afterwards.

**One diagnostic, declared and counted, not a cell:** the wedge book restricted to bars S1 does
*not* hold. If the residual carries nothing, O4 is settled without argument.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **T-a** | **Hurdle E FAILS, at ≤ 5 minimum entries per symbol on the 57 and ≤ 2 on the 60** — the proposal's "50.4 entries/symbol" counts setups, and the long-only inverse trades barely half of them. **The construction's one claimed novel property does not exist** | **certain** — measured before registration and disclosed above |
| **T-b** | **At least one cell beats its rotation null at p95 on BOTH Sharpe and money on the 57.** Down-break bars run +15% to +18% against a +7.84% baseline, which is a large per-bar edge for a null that matches only exposure and turnover | **moderate-high** |
| **T-c** | **No cell clears H on the 60.** The programme's base rate for surviving a holdout is roughly one in eight, this design was chosen after looking at the fixture, and it is a complement-chase — the exact pattern `AITODO.md` flags as an open methodological item | **moderate** |
| **T-d** | **This is substantially S1 in a different costume: `P(S1 | wedge)` lands ABOVE 30% — well above the 18.2% chance baseline and more than triple S2's 8.9% — and ρ with S1 lands above +0.30** | **moderate-high** |
| **T-e** | **O3 clears against S1 anyway, and that will NOT settle the question.** S1's 12.8-year Sharpe is +0.478, so at ρ = +0.35 the bar is only +0.167 and almost any positive arm clears it. **The diversification condition is a weak test when the incumbent is weak**, and O1's overlap is the number that decides O4 | **moderate-high** |

**T-d and T-e are the two that matter, and they are registered in tension with T-b on purpose.** A
cell can clear every return hurdle and still be worthless as a third arm. **T-e is registered
specifically so that a passing diversification condition cannot be quoted later as evidence of
independence** — the same trap D240 walked into when it read an uncorrected 99.6th percentile as a
result.

---

## What could make this wrong, stated now

1. **It is complement-chasing, which this programme has done three times and flagged as a problem.**
   S1 came out of D234's failed cells, D238's exclusion reading out of the mirror's failure, D239's
   inverse out of an anti-signal. **This is the fourth.** The registration and the holdout are the
   only things separating a finding from a fit, and neither is strong protection.
2. **The design was chosen after looking at the fixture.** The horizon cells came from the measured
   forward-return table above. Declared, counted, and not repairable by any amount of care.
3. **`centre` is a definitional choice with a measured consequence.** The apex reading scores
   materially worse. It was fixed by "reproduce the proposer's numbers", which is a legitimate
   reason and is not the same as being the right one.
4. **The validation cohort is not pristine.** Stated in full above.
5. **The validation span is shorter than and nested inside the screen's era.** 7.8 years from
   2018-11, which is the window S1 and S2 were built in. This tests instruments, not time.
6. **Breadth, not trade count, is the binding constraint** — D245 measured 2.23 effective
   instruments — so no result here will have a narrow interval, and the bootstrap is reported for
   width rather than as a verdict.

---

## Stop

**If no cell clears H on the 60, the inverse wedge breakout is CLOSED.** No fourth holding rule, no
re-cut of the arming threshold, no change to the ±2 ATR trigger distance, no move to the apex
definition, no re-test on a wider universe, and specifically **no use of D245's reserved cohort**.

**If a cell does clear, nothing is promoted.** Under R8 it becomes a candidate needing a **time**
holdout, which this study's fixture pair cannot supply.

**And a second stop, on the overlap rather than the return:** if O1 exceeds 50% in either direction,
**the candidate is closed as a variant of S1 even if every return hurdle clears.** Committed here so
that "the overlap wasn't the point" cannot be pulled later.

---

## Ledger

| count | N |
|---|---:|
| **fresh — 3 cells (W1, W2, W3)** | **3** |
| the motivating anatomy, re-verified and disclosed above: 5 width percentiles, 3 arming thresholds, 2 trigger-centre definitions × 2 directions × 5 horizons, 2 holding lengths × 2 fixtures for hurdle E | **32** |
| the S1-excluded residual diagnostic | **1** |
| carried from D248 | 45,886 |
| **total** | **45,922** |

**The 32 is counted because it is a search.** It chose the trigger-centre definition, the horizon
cells and the direction of the bet. Counting only the three cells would understate this study by an
order of magnitude.

---

## Reuse — D212 and R1 are binding

| need | reuse | from |
|---|---|---|
| pivots with D173's confirmation lag | `pivots` | `research/structure.py` |
| the O(T) prefix-sum rolling OLS, slope **and** intercept | `rolling_fit` | `run_uptrend_onset.py` |
| ATR in log units | `atr_log` | `run_uptrend_onset.py` |
| R7's matched-exit-count overlay null | `null_book` | `run_uptrend_onset.py` |
| panel, cleaning, per-symbol costs, dividend frame | `load_panel` | `run_macd_ladder.py` |
| the corrected signed scorer, financing, rotation null with money and vol legs | `signed_log_returns`, `score`, `excess_of`, `_excess_sharpe`, `rotation_nulls` | `run_short_mirror.py` |
| S1's book, bit-identical, so ρ and the overlap are against the real arm | `base_masks`, `hold_book` | `run_stops_targets.py` |
| S2's book, likewise | `signals`, `walk` | `run_uptrend_onset.py` |
| the fixture pair and the repointing convention | `FIXTURES`, `books_on` pattern | `run_book_extended.py` |
| effective independent instruments | `effective_instruments` | `run_book_wide.py` |
| block bootstrap machinery, block 21 | `BLOCK`, `N_BOOT` | `run_jerk_rung.py` |

**Written fresh, with the reason named for each:**

- **the wedge state machine and its walk** — nothing existing expresses *armed, then triggered, then
  held for a fixed age*;
- **the paired bootstrap on ρ** — `paired_block_bootstrap` computes a Sharpe *difference*, which is
  a different statistic;
- **`breakeven_bps` for daily bars** — the existing one is bound to `excess_intraday`.

**Efficiency is a design requirement, not an optimisation.** `rolling_fit` is O(T) per symbol by
prefix sum and already measured at 0.2s for all 57; both lines are fitted the same way. The walk is
the only per-bar loop and it visits armed bars only.

## Verification — the assertions are written BEFORE the run

**D248's four build-time amendments were every one of them caught by a pre-run assertion. That is
the house pattern and it is used here.**

- Full suite green, offline, deterministic, seed 0; **`--report-only` re-renders byte-for-byte**,
  with `CELL_ORDER` explicit from the start.
- **No look-ahead.** Perturb every close from bar `t` onward and assert **no decision at any index
  ≤ t moves** — positions, trigger bars and armed state alike.
- **The causal window is inherited and re-asserted**: no pivot with `confirmed_at > t` may enter
  either fit at bar `t`.
- **Every level is read at `t−1`.** Asserted directly: the armed mask, both lines, the ATR and both
  trigger levels are indexed at `t−1` while the comparison close is indexed at `t`. **R9.**
- **Hurdle E is asserted per symbol**, not pooled, and its failure is asserted rather than
  discovered — if it ever silently passes, the rule or the fixture changed.
- **No overlapping trades**: asserted that no symbol's position matrix contains a re-entry inside an
  open trade's span.
- **The overlay null preserves exit count exactly** — the single property that makes it the right
  control under R7.
- **S1 and S2 must reproduce +0.478 and +0.511 on the extended 57**, or ρ and the overlap are void.
- **D245's reserved cohort is asserted untouched** — the runner fails loudly if either wide-universe
  fixture path is opened.
