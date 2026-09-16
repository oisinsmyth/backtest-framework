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

---

## RESULT — closed, and it is a market timer wearing a per-instrument signal

**Produced:** 2026-08-28 · `uv run python scripts/run_wedge_inverse.py` · Page:
[`WEDGE_INVERSE_RESULTS.md`](../results/WEDGE_INVERSE_RESULTS.md)

### The one-sentence version

**The wedge down-break is not a per-instrument signal — it fires across the universe at once,
holding up to 41 of 57 names simultaneously where a rotated book never exceeds 23 — so W2 builds a
book 2.2× more volatile than its own null, earns more money than 99.8% of rotations and less per
unit of risk than the median one, and on the holdout it is not paid at all.**

### The three cells

| | | exposure | net exSh | *gross* | Δ vs B&H | CAGR | max DD | breakeven | entries | min/sym | E |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|
| **W1** | hold 21 | 9.8% | +0.115 | *+0.125* | −0.127 | 0.92% | −17.54% | 24.9 bp | 853 | **5** | ✗ |
| **W2** | hold 42 | 15.4% | +0.265 | *+0.272* | +0.023 | 2.11% | −18.24% | 81.6 bp | 675 | **4** | ✗ |
| **W3** | 42 + −2·ATR stop | 9.3% | **+0.318** | *+0.335* | +0.075 | 1.05% | **−4.66%** | 38.7 bp | 675 | **4** | ✗ |
| *S1* | | *18.2%* | *+0.478* | — | *+0.236* | *3.11%* | *−10.28%* | — | *2,374* | *20* | — |
| *S2* | | *13.3%* | *+0.511* | — | *+0.269* | *1.85%* | *−5.83%* | — | *393* | *5* | — |
| *B&H* | | *100%* | *+0.242* | — | — | *7.84%* | *−34.55%* | — | — | — | — |

**Screen: 57 ETFs × 3,222 live bars, 2013-11-01 → 2026-08-26. Effective independent instruments
2.29** — so the 675–853 pooled trades are *not* a sample size and are not quoted as one.

### Every hurdle, scored

| hurdle | screen (57) | validation (60) |
|---|---|---|
| **H — rotation null, p95 on Sharpe AND money** | **FAILS 3 of 3.** 29.0th / 63.0th / 74.7th on Sharpe | **FAILS 3 of 3.** 10.1st / 15.7th / 7.3rd |
| *H, money leg alone* | *W2 clears at the 99.8th, W3 at the 91.8th* | *W2 55.6th, the others below the 11th* |
| **H-BEST — best-of-three floor (D228)** | **FAILS.** W3 at +0.318 against a +0.505 floor, 60.0th percentile | — |
| **H-OVL — R7, the stop only** | **CLEARS**, W3 at the 97.9th of its matched-exit-count null | — |
| **E — ≥100 pooled and ≥30 per symbol** | **FAILS**, minimum **4–5** per symbol | **FAILS**, minimum **1** |
| **P — beats buy-and-hold** | W1 ✗, W2 ✓ (+0.023), W3 ✓ (+0.075) | **✗ on all three**, by −0.21 to −0.35 |
| **anti-triviality floor** | — | **FAILS 3 of 3** |
| **costs** | **not the cause.** Breakeven 24.9 / 81.6 / 38.7 bp against ~1.6 bp charged | 2.6 / 46.4 / **0.1** bp |

**Gross and net differ by less than 0.02 of Sharpe on every cell.** This does not fail on friction.

### The finding: money passed, Sharpe failed, and the book is 2.2× the null's volatility

| | vol | null vol p50 | **ratio** | money / vol | null money / vol | better bars? |
|---|---:|---:|---:|---:|---:|:--:|
| **W1** | 4.66% | 1.68% | **2.77×** | 2.68 | 5.72 | ✗ |
| **W2** | 5.59% | 2.54% | **2.20×** | 5.47 | 6.40 | ✗ |
| **W3** | 2.15% | 1.66% | 1.29× | 6.67 | 5.98 | ✓ |

**The +15% to +18% annualised after a down-break — the number that motivated this whole study — is
compensation for risk, not timing skill.** W2 earns 5.47 units of money per unit of volatility
where a randomly-timed book of the same exposure earns 6.40. **It is not merely unpaid for its risk
— it is paid slightly below the going rate.** The rotation null matches exposure, turnover and
holding periods; it does not match the volatility of the book that results, and that gap is the
whole distance between the money column and the Sharpe column.

### Where that volatility comes from, and it is NOT the obvious answer

**The obvious reading is that a 2-ATR break selects loud bars. Measured, that is barely true and it
is not the mechanism.**

| | loudness of held bars | names held, mean | max | *rotated max* | bars over 20 names | *rotated* | clustering |
|---|---:|---:|---:|---:|---:|---:|---:|
| **W1** | 1.22× | 5.6 | **36** | *19* | **4.3%** | *0.0%* | 1.44× |
| **W2** | **1.14×** | 8.8 | **41** | *23* | **13.7%** | *0.0%* | **1.36×** |
| **W3** | 0.89× | 5.3 | **30** | *19* | **2.0%** | *0.0%* | 1.33× |

**The bars are 1.14× as volatile as average. The book is vastly more crowded.** W2 holds more than
20 of 57 names on **13.7%** of bars where a per-symbol-rotated book of identical exposure does so
on **0.0%**, and it peaks at **41** names against the rotation's **23**. **Converging channels
break downward together, because they break when the market falls.**

**So the rule is not selecting which ETF to buy; it is selecting *when* to buy all of them.** That
is a legitimate thing to be — it is roughly what S1 is — but it means the diversification across 57
names the equal-weighted book appears to have is largely illusory on exactly the bars that matter,
and it is why W2 carries an −18.24% drawdown at 15.4% exposure where S2 carries −5.83% at 13.3%.

**A limitation of the rotation null, recorded rather than buried.** `rotation_nulls` draws an
**independent offset per symbol**, which destroys cross-sectional synchrony by construction — so it
**understates the volatility of any book whose signal is market-wide.** It is therefore a
*conservative* control for such a rule on money and a *harsh* one on Sharpe. Both legs were
registered and between them they bracket the truth, which is the practical argument for the
two-legged form and is a stronger one than the argument the registration actually gave.

**D249 registered the money leg for the opposite reason and it caught this anyway.** The record's
argument was D238's: a high-volatility book could inflate its *Sharpe*, so money was added as the
leg that cannot be inflated. **What happened is the mirror image — money was the inflated leg and
Sharpe was the honest one — because D238's arm had a negative mean and this one does not.** The
reasoning was pointed the wrong way; requiring **both** legs is what made that harmless, and that
is a general point about R6 rather than about this study.

### The overlap analysis, which was the question worth asking

| | `P(S1 \| wedge)` | *chance* | ratio | `P(wedge \| S1)` | ρ with S1 | ρ p05 | ρ p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| **W1** | 28.2% | *18.2%* | 1.55× | 15.1% | +0.199 | +0.138 | +0.370 |
| **W2** | **32.5%** | *18.2%* | **1.79×** | **27.6%** | **+0.389** | +0.257 | +0.588 |
| **W3** | 29.5% | *18.2%* | 1.62× | 15.1% | +0.382 | +0.308 | +0.478 |

*Chance is S1's own exposure: independent rules would sit exactly there. D242 measured **8.9%** for
S2 — **half** chance — which is what a structurally disjoint arm looks like.*

**The diversification condition clears against S1 in all three cells** — bars of +0.095 / +0.186 /
+0.183 against actuals of +0.115 / +0.265 / +0.318 — and against S2 in two of three. **It clears
while every return hurdle fails, which is exactly what T-e registered.**

**The S1-excluded residual:** W2 with every bar S1 also holds removed keeps 67.5% of its bars and
scores +0.190 at 10.4% exposure, against W2's +0.265 at 15.4%. **The result is not living in the
S1 overlap** — it is thin everywhere.

### O4 — the direct answer

> **NEITHER. It is not S1 in disguise — overlap peaks at 32.5% of the wedge's held bars against an
> 18.2% chance baseline (1.79× chance) with ρ at most +0.389, so the two rules lean on a shared
> population without being the same rule. But it is not a new arm either, and that is the operative
> half: there is no edge here to diversify. No cell beats its rotation null on the screen, and on
> the holdout the best of the three sits at the 7.3rd–15.7th percentile of randomly-timed books
> holding the same amount. What the two rules share is the thing the concurrency measurement
> names: both are buying broad market weakness. The wedge holds up to 41 of 57 names at once, so
> it is a market timer wearing a per-instrument signal, and S1 is the same bet made better.**

**The overlap stop did not fire** — 32.5% is below the 50% line D249 committed to — so this record
does not get to close the candidate on that ground. **It closes on the return hurdles instead**,
which is a cleaner outcome: the honest statement is *shared population, no edge*, not *duplicate of
S1*.

### The screen restricted to the validation span

*So that a 12.8-year screen and a 7.8-year validation can be compared at all.*

| | 57, from 2018-11 | 60, full |
|---|---:|---:|
| W1 | +0.059 | +0.001 |
| **W2** | **+0.243** | **+0.115** |
| W3 | +0.240 | −0.021 |
| *S1* | *+0.626* | *+0.660* |
| *S2* | *+0.673* | *+0.468* |
| *B&H* | *+0.363* | *+0.326* |

**Over the validation era the wedge loses to buy-and-hold on both universes** while S1 and S2 both
beat it comfortably. The shrinkage from the 57 to the 60 is real but secondary — the rule was
already behind the market on the same era, same-instrument.

### Scoring — four of five, and the miss is the informative one

| | prediction | outcome |
|---|---|---|
| **T-a** | hurdle E fails, ≤5 minimum per symbol on the 57 and ≤2 on the 60 | **CONFIRMED.** 5 / 4 / 4 on the 57, **1** on the 60. The proposal's "50.4 entries/symbol" was setups |
| **T-b** | at least one cell beats its rotation null on both Sharpe and money on the 57 | **FALSIFIED.** Zero on Sharpe. W2 clears money at the 99.8th and fails Sharpe at the 63.0th — **the split is the finding, not the miss** |
| **T-c** | no cell clears H on the 60 | **CONFIRMED**, 7.3rd–15.7th percentile |
| **T-d** | `P(S1 \| wedge)` above 30% and ρ above +0.30 | **PARTIALLY CONFIRMED.** True for W2 (32.5%, +0.389); W3 clears on ρ and misses on overlap (29.5%); W1 misses both (28.2%, +0.199). **The direction is unambiguous in every cell** — 1.55× to 1.79× chance, against S2's 0.49× |
| **T-e** | the diversification condition clears against S1 anyway and settles nothing | **CONFIRMED.** 3 of 3 clear it while 0 of 3 clear a null |

**T-b is the miss and it is worth more than the four hits.** I expected the conditional-return
table to survive a null that matched exposure. It survived on *money* and died on *risk-adjusted*
money, and the concurrency measurement names the reason. **A forward-return table computed per
(symbol, bar) tells you nothing about the book those bars assemble into** — 1,474 down-breaks look
like 1,474 independent observations and are in fact a few dozen market-wide events.

### Build-time amendments — one, and it was caught by a pre-run check

**The apex reading of "the crossover point" was rejected before the runner existed**, because a
pre-registration check on the reconstruction showed the regression apex sits a **median 113 bars
ahead** of the arming bar. The apex *price* is therefore a long extrapolation, it does not
reproduce the proposer's trigger counts (891/1,909 against 1,052/1,444), and it scores materially
differently. **The channel midline is the registered definition and the reason is written into the
record rather than discovered afterwards.** No amendment was needed during the build itself; every
runner assertion passed first time.

### The stop applies as written

**CLOSED.** No fourth holding rule, no re-cut arming threshold, no change to the ±2 ATR trigger, no
move to the apex definition, no wider universe — **and D245's reserved cohort was never opened**,
asserted in code and pinned by test.

### What survives

**Two measurements and one method, none of which is a strategy.**

- **Concurrency belongs beside every pooled conditional-return table this programme produces.** A
  per-(symbol, bar) forward-return table cannot see that its 1,474 observations are a few dozen
  market-wide events, and the book that results carries risk the table never showed. **This is R9's
  neighbour rather than a case of it**: R9 catches conditioning on the bar being measured; this
  catches a table that is *correct per bar* and misleading about the portfolio. Cheap to compute —
  names held per bar, actual against rotated — and it should be reported wherever a rule's
  triggers can synchronise across the universe.
- **A per-symbol rotation null is a biased control for a market-wide signal**, in a known
  direction: it under-states the arm's volatility, so it flatters the arm on money and penalises it
  on Sharpe. Not a reason to stop using it — it remains the right control for exposure and turnover
  — but a reason to report the concurrency gap beside the percentile.
- **A two-legged null with a money leg and a Sharpe leg is worth its cost**, and the leg that
  catches the problem is not the one you expect. D238's audit found volatility inflating Sharpe;
  this one found it inflating money. **Registering both is cheap and the asymmetry is unpredictable
  in advance.**

**The wedge geometry itself is not retired, only this bet on it.** The lines, the convergence test
and the ATR-scaled width are D240 machinery and are unaffected.

### What is wrong with this study, at full strength

1. **It is complement-chasing, the fourth time in this programme.** The registration states it and
   the holdout tested it, and neither is strong protection. `AITODO.md`'s open methodological item
   stands.
2. **The validation cohort is not pristine** and its span is nested inside the screen's era. This
   was an instrument test, not a time test, and the record said so in advance.
3. **Breadth is 2.29.** Every interval here is wide and none excludes zero for any cell.
4. **W3's H-OVL pass is a lone positive in a failing study and should not be quoted.** The stop
   beats random trimming of the same book — but the book it trims does not beat its own rotation
   null, so the stop is a better way of holding less of something worthless. **This is exactly the
   reading D242 forced on D240's −8% stop**, arrived at one study earlier this time.

### Ledger

| count | N |
|---|---:|
| fresh — 3 cells (W1, W2, W3) | 3 |
| the motivating anatomy, re-verified and disclosed: 5 width percentiles, 3 arming thresholds, 2 trigger-centre definitions × 2 directions × 5 horizons, 2 holding lengths × 2 fixtures | 32 |
| the S1-excluded residual diagnostic | 1 |
| **+ the concurrency decomposition, computed on the analyst's initiative after the two null legs disagreed — disclosed, and counted** | **1** |
| carried from D248 | 45,886 |
| **total** | **45,923** |

*The pre-registration's ledger said 45,922. The extra look is the concurrency measurement: the
registration anticipated a volatility explanation and named the money leg for it, but did not
anticipate decomposing that volatility into loudness and clustering. It was computed after the
result, following D238's M4 precedent — **disclosed, counted, and not presented as
pre-registered.***
