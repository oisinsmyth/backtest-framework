# D248 — The strength-filtered intraday short

**Status:** Pre-registered — committed BEFORE the runner exists and BEFORE any cell is scored
**Date:** 2026-08-28
**Area:** Strategy research
**Execution:** **HELD.** Not to be run until explicitly released.

---

## What this is

**The first rule in this programme designed for the intraday horizon rather than transported to
it.** [D247](D247-the-short-side-at-fifteen-minutes.md) moved the book's frozen daily rules onto
15-minute bars and every cell lost. This does not repeat that. It takes the two facts D247
established and builds a rule around them.

**This is therefore a NEW rule, not a frozen one.** Where D244 and D247 froze bar counts because
the book specifies bars, this record chooses its own constants — **once, declared, and never
swept.**

---

## The two facts it is built on

### 1. Essentially all equity drift accrues overnight

57 ETFs, 8.3 years, ex-dividend and split sessions excluded:

| | annualised, equal-weighted |
|---|---:|
| **overnight** (prev close → open) | **+8.59%** |
| **intraday** (open → close) | **−0.36%** |

**28 of 57 symbols have negative intraday drift** against 6 negative overnight. D238 closed
directional shorts on a close-to-close basis and was therefore paying that +8.59%. **A book flat
at every session close is exposed to −0.36% and pays no overnight borrow and no dividends over
ex-dates.**

D247 confirmed it in the book's own terms: the intraday-only S1 short held bars returning
**−4.27%/yr** against the continuous version's **+4.72%** — an **8.99-point swing**, and the
first construction in this programme to isolate bars that actually fall.

### 2. The edge concentrates monotonically in signal strength — and so does the turnover

D247 failed on cost: **334 turnover units per symbol-year, breakeven 0.13 bp against ~1.6 bp
charged.** The decomposition says where it goes:

| | units/yr | share |
|---|---:|---:|
| forced by the daily flatten and re-enter | 79 | 23.7% |
| **signal flips inside a session** | **255** | **76.3%** |

Median short episode: **8 bars**. Only 10.6% last a full session.

And the intraday held-bar return by `|hist_L| / trailing_sd`:

| quintile | held-bar return | bars |
|---|---:|---:|
| **Q1 — weakest** | **+413.69%** | 161,727 |
| Q2 | +33.14% | 161,727 |
| Q3 | −26.97% | 161,726 |
| Q4 | −44.36% | 161,727 |
| **Q5 — strongest** | **−71.07%** | 161,727 |

**Monotone across all five, and the weak bars are the churning bars** — `hist_L` near zero means
the signal is sitting on its own boundary and flipping. **One filter attacks both failures at
once.** That is the entire thesis of this record.

**These magnitudes are per-bar figures annualised at PPY 6,513 and are NOT achievable returns.**
A 15-minute bar multiplied by 6,513 is a bar-quality measure. They are reported because the
*ordering* is the finding, not the levels.

---

## The rule

```
For each instrument, on 15-minute bars, in LOG space:

    md_L, hist_L        exactly as S1 defines them (Impulse MACD 34/9, log space)

    z[i,t] = |hist_L[i,t]| / trailing_sd(hist_L[i], 1638)      strictly trailing

    SHORT  when   hist_L < 0  AND  md_L >= 0  AND  z >= c[i,t]

    c[i,t] = the (1 - TARGET) quantile of that symbol's own z over the prior 1638 bars

    FLAT at the first bar of every session -- always, unconditionally
```

**Position −1 when the condition holds, 0 otherwise. `lag = 1`. Equal-weighted across the 57.**

### Every constant, and why it is that value

| constant | value | why |
|---|---|---|
| Impulse lengths | **34 / 9** | S1's, unchanged — this filters S1's mirror rather than inventing a signal |
| direction condition | `hist_L < 0 AND md_L >= 0` | D238's mirror, unchanged |
| **normalisation window** | **1,638 bars = 63 sessions ≈ one quarter** | A volatility normaliser needs a stable, non-stale window. A quarter is the standard choice, gives 1,638 observations, and preserves span where a one-year window (6,514 bars) would cost 2.4 years of it. **Chosen once, declared, not swept.** |
| **exposure targets** | **5%, 10%, 15%** | Three declared cells. See below |
| flat overnight | always | The structural point of the whole record, not a parameter |

### Why the threshold self-calibrates rather than being a fixed `z`

**D231's construction, reused for D231's reason.** A fixed `z > 1.2` makes exposure an *outcome*
that can differ arbitrarily between the screen half and the validation half, and between
fixtures. A rolling per-symbol quantile makes **exposure a control**: it lands near the target by
construction, on any data, with nothing inherited from the fitting sample.

**That is what makes this rule portable to a holdout without re-fitting**, which the fixed-`z`
version would not be.

---

## Cells — three, and the one exclusion is declared

**Three exposure targets: 5%, 10%, 15%.** They span the range the cost arithmetic makes
plausible and each is a genuine hypothesis about where the strength/turnover trade-off balances.

**S2's downtrend short is NOT included, and that is a scope decision made in advance.** D247
measured its intraday held bars at **+4.53%** — positive, so there is no edge to filter. Filtering
a signal that does not select falling bars would be testing a cell I expect to fail for a reason
already measured. **Excluded, stated, not quietly dropped.**

D247's unfiltered `S1_short_intra` is the **reference**, already run: −1.550 excess Sharpe, 334
turnover, 0.13 bp breakeven.

---

## The split, declared before anything is scored

| | span | purpose |
|---|---|---|
| **SCREEN** | live start → **2022-06-30** | roughly 4.2 years. Cells are compared here |
| **VALIDATE** | **2022-07-01** → 2026-08-26 | roughly 4.2 years. **Carries the verdict** |

**A time split, not an instrument split, and deliberately.** D243 established that time is the
axis on which this programme's rules actually fail — S1 passed two instrument holdouts and failed
one era holdout. **An instrument holdout at 15 minutes would need a fetch of ~6,000 calls and
would test the axis that keeps passing.**

**The signal is computed on the full series and the SPLIT IS APPLIED TO SCORED RETURNS ONLY**, so
the validation half carries exactly the warm-up and the rolling quantile history it would have
had in real time. D243's construction.

---

## Hurdles

**On SCREEN, to select at most one cell:**

- **A1.** Excess Sharpe **> 0**.
- **A2.** Beats its **matched-count rotation null at p95** — same exposure, turnover and holding
  periods, wrong bars.
- **A3 — the multiplicity leg.** Beats a **best-of-three floor** (D228, one shared offset vector
  across the three cells). **D240's stop cleared at the 99.6th percentile with no correction and
  then failed out of sample at the 71.7th. That must not happen twice.**
- **A4 — the leg that killed D247.** **Breakeven cost per side > 1.6 bp**, the cost actually
  charged. A cell that only works at zero friction is not a candidate.

**On VALIDATE, which carries the verdict:**

- **A5.** Excess Sharpe **> 0** and beats its rotation null at p95.
- **A6.** Breakeven cost per side still **> 1.6 bp**.
- **A7 — the structural test, and the most informative thing here.** **The quintile monotonicity
  in `z` must survive on the validation half.** A real effect decays smoothly across strength
  quintiles on data it was not found on; a fitted one does not. **This is checkable and is worth
  more than A5 on its own**, because A5 can be luck and a preserved ordering across five buckets
  cannot easily be.

**Reported, not hurdles:** the √f decomposition (does the filter beat simply holding less?),
turnover split into daily-flatten and intra-session components, exposure actually achieved
against target, borrow paid (**asserted zero**), the conditional-return profile on both halves,
deployable return, and max drawdown.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **T-a** | **Turnover falls sharply, to under 120 units/yr at the 5% target** from 334. The weak-signal bars are the churning bars, so removing them removes flips as well as exposure | **high** |
| **T-b** | **At least one cell clears A1 and A4 on SCREEN.** The concentration is strong and monotone, and the filter attacks the cost problem directly | **moderate** |
| **T-c** | **No cell clears A5 and A6 on VALIDATE.** The programme's base rate is roughly one in eight, and this design came from looking at the data | **moderate** |
| **T-d** | **The monotonicity partly survives** — Q5 stays the most negative and Q1 the most positive, but the middle quintiles scramble | **moderate** |
| **T-e** | **The √f decomposition shows most of the improvement is exposure, not selection.** Cutting exposure from 25.9% to 5% mechanically raises Sharpe by ~√(0.259/0.05) = 2.3× before any skill | **moderate-high** |

**T-e is the one that would deflate the result quietly**, so it is registered explicitly. **A
cell that beats the unfiltered version by less than √f predicts has learned nothing** — it has
merely traded less, which is the confound the rotation null exists to catch and which D231
derived analytically.

---

## What could make this wrong, stated now

1. **It is post-hoc.** The strength concentration was found by looking at D247's output. Counted
   in the ledger as a search, and the split above is the only thing that can distinguish a
   finding from a fit.
2. **The `md_L` cut was non-monotone and is not used.** +3.83%, −1.31%, +6.43%, +3.30%, +49.39%,
   with the dead zone at −42.20%. **That is noise with a story available**, and building on it
   would be building on nothing. **Only `z` is used.**
3. **The joint `z` × `md_L` cell (−78.74% on 3% of bars) is NOT used either.** It combines a good
   factor with a bad one and reports the best result, which is an unexplained interaction found
   on 3% of bars. The programme's nulls have killed five of those.
4. **`per_side_bps` assumes a 1 bp half-spread.** On liquid ETFs intraday that is plausible and
   optimistic. **The breakeven is the headline diagnostic precisely because the charged cost is
   the weakest assumption in the study.**
5. **SEC Rule 201 is not modelled and bites this design harder than most.** It restricts short
   sales at or below the NBBO for the remainder of the day and the next after a 10% intraday
   decline — and a *strength-filtered* short is by construction most active when moves are
   largest. **Named, unmodelled, and a real reason the live result would be worse.**
6. **Locate fees are not modelled.** Intraday-only avoids overnight borrow, not the locate.

---

## Stop

**If no cell clears A5 and A6, the strength-filtered intraday short is closed** — no fourth
exposure target, no `md_L` variant, no re-cut of the normalisation window, no move to 30-minute
bars. **Committed here so that "the last reading wasn't the right one" cannot be pulled later.**

**If a cell does clear, nothing is promoted.** It becomes a candidate needing an instrument
holdout at 15 minutes, which requires a fetch that has not been made.

---

## Ledger

| count | N |
|---|---:|
| fresh — 3 cells | 3 |
| **+ the D247 anatomy this design came from: 5 strength quintiles, 5 `md_L` buckets, 1 joint cell, 2 turnover cuts** | **13** |
| + D247's 8, D245's 2, D242's 3, D241's 5, D240's 5, D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 62 |
| + the gradient anatomy | 83 |
| + disclosed ETF prior | **45,886** |

**The 13 includes the anatomy that produced the hypothesis**, because it was a search and
counting only the three cells would understate it.

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| the 15m panel, session structure, overnight flattening, borrow, scoring | `session_structure`, `flatten_overnight`, `excess_intraday`, `score`, `breakeven_bps` | `run_intraday_shorts.py` (D247) |
| `md_L` / `hist_L` | `base_masks` | `run_stops_targets.py` |
| the self-calibrating quantile threshold | `dial_threshold` | `run_exposure_dial.py` (D231) |
| trailing standard deviation | `trailing_std` | `run_filter_search.py` |
| rotation and best-of-search nulls | `rotation_nulls` | `run_intraday_shorts.py`, already shares one offset vector |
| the hoisted fast scorer | `_fast_total`'s pattern | `run_intraday_shorts.py` |

**Written fresh: the `z` filter, the screen/validate split, and the quintile-monotonicity test.**

## Verification

- `--report-only` re-renders byte-for-byte; full suite green.
- **The threshold is strictly trailing** — bar *t* is not in its own quantile. Asserted by
  perturbing `hist_L` from bar *t* onward and checking no threshold at any index ≤ *t* moves.
- **Borrow is asserted to be exactly zero** on every cell, since all are flat overnight.
- **Every cell is asserted flat at every session open**, on every symbol.
- **Achieved exposure is asserted within 3 percentage points of target** on both halves — D231's
  tolerance. If it is not, the self-calibration failed and the cells are not comparable.
- **The split is asserted to be applied to returns and never to the signal**, by checking that a
  cell's full-span position matrix equals the concatenation of its two halves.
- **D247's unfiltered reference must reproduce** at −1.550 / 334 turnover / 0.13 bp, or the
  pipeline has changed underneath the comparison.
