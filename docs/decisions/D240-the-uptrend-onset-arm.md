# D240 — The uptrend-onset arm, with stops and targets

**Status:** Pre-registered — committed BEFORE any runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## The question

Is **entry at the onset of a structural uptrend, held for a capped age**, arm two?

[D239](D239-time-series-momentum-as-arm-two.md) closed twelve-month time-series momentum and
left a hard constraint: *arm two must not be another bet on reversals-beating-continuations,*
because S1 already is one. This candidate is registered because the anatomy below says it is a
**continuation** bet that works — the one thing D239 said should not exist on this fixture.
That tension is the reason to run it.

---

## The signal, and the machinery it reuses

```
For each instrument, on daily bars, in LOG space:

    lows  = confirmed swing lows  in the trailing 252 bars   (k = 3)
    highs = confirmed swing highs in the trailing 252 bars

    g_lo  = OLS slope of log(price) on bar index, over lows
    g_hi  = OLS slope of log(price) on bar index, over highs

    UPTREND  :=  g_lo > 0  AND  g_hi > 0
```

**`pivots(bars, k)` is reused unchanged** from `research/structure.py`. It stamps every pivot
with `confirmed_at = index + k`, so D173's confirmation lag — *the* place this construction
leaks if built by hand — is enforced by the existing, mutation-tested detector rather than by
this study. **`k ∈ {2, 3}` was fixed by D173 and is not a free parameter**; `k = 3` is used.

**The regression answers D173's standing objection rather than evading it.** D173 chose pivot
levels over trend lines because *"a sloped line through two chosen swing lows is a fit: which
two points, how often to refit, what to do when a third disagrees."* OLS over **all** confirmed
pivots in the window chooses no points, refits every bar, and includes the disagreeing third.
The degree of freedom that objection names does not exist here.

**D211's stop does not cover this.** It is scoped to *"the five components of
`STRUCTURE_MODEL.md`, mechanised as it defines them, on BTC/ETH 15m bars."* A pivot regression
is not one of the five and this is not that fixture — the same scoping D226 applied to D220.

**Log space makes the gradient dimensionless** (%/bar), so it is comparable across TLT and UNG
and at any price level. Same property that made `md_L` expressible.

---

## Measured before the run — and it is why the design looks like this

All of the below is descriptive anatomy on the mined 57, taken **before** this registration and
disclosed here. **It is also the reason the design is what it is, so it is a search and it is
counted in the ledger.**

### Returns inside an uptrend decay hard with age

Mean annualised total return of the bars, by age of the state episode:

| state age | 0–21 | 21–63 | 63–126 | 126–252 | 252+ |
|---|---:|---:|---:|---:|---:|
| **uptrend** | **+22.33%** | **+13.74%** | +7.54% | +4.49% | **−3.14%** |
| *downtrend* | *+37.42%* | *+16.97%* | *+0.51%* | *+14.31%* | *+0.52%* |

*Market: +8.42%.*

**The whole-state average is +6.17%, below the market — but that is a good start blended with a
losing tail.** The edge is in the first ~63 bars and the tail after 252 bars is negative.

### Which is why the exit is an age cap and not "the trend ended"

| | episodes | mean | median | p90 | max |
|---|---:|---:|---:|---:|---:|
| uptrend | 245 | 194.6 bars | **175** | 436 | 739 |
| downtrend | 231 | 142.8 bars | 125 | 316 | 615 |

**A median episode lasts 175 bars and the edge is gone by 63.** Exiting when the state ends
would hold through the entire decay and into the negative tail. **Age is the exit.**

### And why there is no short leg

Measured, holding each whole state, no stops:

| | excess Sharpe | CAGR | max DD |
|---|---:|---:|---:|
| long uptrend only | +0.104 | +3.33% | −26.56% |
| **short downtrend only** | **−0.877** | **−7.22%** | −37.05% |
| both | −0.612 | −4.13% | −29.22% |
| buy and hold | +0.235 | +8.42% | −34.60% |

**Downtrend's first 21 bars return +37.42%** — by the time a 252-bar regression plus a 3-bar
confirmation says "downtrend", the decline is over and a short would be selling the bounce.
D238 already established the general case: nothing on this universe falls enough to short, at a
breakeven borrow of **−6.90%/yr**. **The arm is long-only. This is settled, not open.**

---

## The rule

```
ENTRY   the first bar of an UPTREND episode        (onset only; no re-entry within an episode)
EXIT    the earliest of
          - age  >= 63 bars
          - the UPTREND state ends
          - a stop or target, per cell
```

**`AGE_CAP = 63`.** Two justifications and the honest one is second: it is one calendar quarter,
and **it is where the measured decay crosses the market return.** Chosen from the table above,
declared here, counted. **Not swept** — sensitivity at 21 / 126 / 252 is reported as a
diagnostic, never as a cell.

Long-flat, `lag = 1`, equal-weighted across the 57, the shared 1,000-bar warm-up, same costs and
same dividend-adjusted scoring frame as every other arm — so S1 and this are scored on identical
bars and ρ is meaningful.

### The stop — AMENDED before the run, see the amendment below

```
    line(t)  = intercept + g_lo * t      the low regression, FIT AND FROZEN AT ENTRY,
                                         then evaluated forward along its own slope
    atr      = ATR(21) in log units, also frozen at entry

    stop_log(t) = min( line(t) - 1*atr ,  entry_log - 2*atr )
```

**The line is frozen at entry and extrapolated forward along its slope**, so the entire stop
trajectory is knowable on the day the trade is opened — which is the point of freezing. It is a
trailing stop anchored to structural support rather than to the entry price.

**The `2*atr` floor is the only addition to the proposer's design**, and it exists because of a
measured defect, not a preference. See amendment 2.

### Cells — five

| | overlay |
|---|---|
| **A0** | none — the base rule |
| **A1** | structural stop, above |
| **A2** | fixed stop at **−8%** from entry |
| **A3** | take profit at **+2R**, full exit (`R` = the A1 stop distance) |
| **A4** | A1 and A3 together |

---

---

## Two amendments, written before the runner exists

### Amendment 1 — the slope IS extrapolated. My objection to it was wrong.

The first draft of this record froze the line to a **level** at entry and refused to project the
slope, on the reasoning that *"trend slopes mean-revert over a 63-bar horizon against a 252-bar
fitting window."* That was a hypothesis stated as a fact, and it replaced the proposer's rule
rather than testing it. **Measured, it is a non-issue.**

Slope of the lower line at entry, annualised, across all 245 onsets:

| p5 | p25 | **p50** | p75 | p95 | p99 |
|---:|---:|---:|---:|---:|---:|
| +0.1% | +0.8% | **+2.1%** | +4.8% | +14.0% | +32.5% |

**The line climbs +0.5% at the median across an entire 63-bar trade** (+3.3% at p95). A
regression over a year of swing lows is a long-run average and heavily damped — nothing like a
steep hand-drawn line. Directly measured, with a 1×ATR buffer:

| stop hit within 63 bars | |
|---|---:|
| **sloped, extrapolated** — as proposed | **40.8%** |
| frozen level — my substitute | 39.2% |

**1.6 points across 245 trades.** The registered rule is the sloped one. The frozen-level
variant is reported as a **diagnostic, not a cell** — it does not merit the multiplicity.

### Amendment 2 — the 2×ATR floor, and the defect that forced it

The same measurement surfaced a real problem, in R rather than in the slope. **Price sits a
median 6.1% above the low line at entry — 8.3 ATRs:**

| p5 | p25 | p50 | p75 | p95 |
|---:|---:|---:|---:|---:|
| **−11.2%** | +1.2% | **+6.1%** | +11.5% | +24.9% |

Two consequences, and the second is disqualifying without a fix:

1. **R is enormously uneven** — roughly 1% to 25% across trades. Positions are equal-*weighted*,
   not equal-*risk*, so risk per position varies by more than 20×. A `+2R` target inherits it
   exactly: 2R is +2% on one trade and +50% on another, so "take profit at 2R" is not one rule.
2. **About 5% of entries have price BELOW the line.** There the stop would sit *above* entry, and
   a naive `min(line, entry)` guard collapses it to ~1 ATR — a near-certain immediate stop-out.

**The floor `entry_log − 2*atr` fixes the tight end with one declared constant.** `min` takes the
lower of the two, so a distant line is used unchanged and only the pathological cases are
floored.

**It does not fix the wide end, and that is deliberate.** A trade whose line sits 25% below entry
still risks 25%. Capping it would be a second guessed constant, and risk-weighted sizing is a
bigger change that R8 keeps as a separate decision anyway. **The R distribution is reported as a
diagnostic** so the cost of the dispersion is measured rather than assumed, and any fix is
evidence-led.

---

## Hurdles

- **A — R7, and it carries the verdict on the overlays.** Each of A1–A4 must beat a
  **matched-exit-count trade-level overlay null** at p95: keep A0's book, and cut **the same
  number of trades** short at **random bars inside their own spans**. A rotation null is the
  wrong control for an exit rule, and D235 is the proof — its seven overlays all cleared a
  rotation null whose p95 was **−0.284**, a bar anything not actively harmful would clear, while
  the correct null put the best of them at the **63rd percentile**.
  **This null does not exist as reusable code.** D236's `overlay_null` is bar-level position
  scaling, not trade-level exits. Written fresh, and it should have been written at D235.
- **B — the entry rule's own control.** A0 must beat a **matched-count rotation null** at p95.
  Rotation is the right null for an entry rule (R7), wrong for an exit.
- **C — the diversification condition, and this is what decides whether it is arm two.**
  **`SR_A0 > ρ × 0.746`**, ρ measured on daily excess returns against S1. Weighting-independent.
- **D.** Beat buy-and-hold's **+0.235**, reported beside the √f prediction.
- **E.** Reported, **not** waived. One trade per episode across 245 episodes and 57 symbols is
  ~4.3 entries per symbol against 30 required. **It fails, and that is stated here rather than
  discovered.**
- **R6 binds:** every leg is computed in code or the runner fails loudly.

**Reported, not hurdles:** ρ itself, the √f decomposition, the null's money and volatility legs
(D238's audit), Calmar, **deployable return** (`CAGR + rf × (1 − exposure)`), and the age-cap
sensitivity.

---

## Predictions

| | prediction | confidence |
|---|---|---|
| **P1** | **A0 exposure lands near 17–18%**, from 245 episodes × up to 63 bars | **high** — arithmetic |
| **P2** | **A0 beats buy-and-hold** (+0.235). Its bars run ~+16% against the market's +8.42%, at roughly S1's exposure | **moderate** |
| **P3** | **A0's excess Sharpe lands +0.30 to +0.45** — about half of S1's, because its bars are about half as good at similar exposure | **moderate** |
| **P4** | **ρ with S1 comes in BELOW 0.35.** Oversold-turn and confirmed-uptrend are close to disjoint states, so the bar for C should be ≈ +0.26 and C is genuinely marginal | **moderate** |
| **P5** | **No overlay cell beats its matched-exit-count null.** D235 found stop triggers carry no information over random trimming; the entry differs here but the finding about *trigger* information is the more general one | **moderate-high** |
| **P6** | **A0 beats its rotation null.** The whole anatomy says onset bars are better than random bars at the same exposure | **moderate-high** |

**P5 is registered against the proposer's stated preference, and against my own prior that the
freeze is a good idea.** The stop being well-designed and the stop's trigger carrying
information are different claims, and only the second is being tested.

**P4 is the one that matters.** A0 could beat buy-and-hold and still fail as arm two if it
correlates with S1; it could lose to buy-and-hold and still succeed if it does not.

---

## Stage 1 only

**The mined 57.** The holdout 60 and the 2025–2026 forward window are **not touched.** Under R8
nothing here reaches `BOOK.md` without its own pre-registered out-of-sample test.

**And a caution that belongs in the record, not in a footnote:** the age cap, the long-only
decision and the state definition were all chosen after looking at this fixture. **This is a
fitted design being screened, not a discovery being confirmed.** The out-of-sample test is the
only thing that can distinguish them, and it has not been run.

---

## Ledger — including the anatomy that has gone undeclared until now

| count | N |
|---|---:|
| fresh — 5 cells | 5 |
| **the gradient anatomy: 4 states × 2 values of `k`** | 8 |
| **+ 3 whole-state books, 10 age buckets** | 21 |
| + D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 47 |
| + disclosed ETF prior | **45,850** |

---

## Reuse — D212 is binding

| need | reuse | from |
|---|---|---|
| pivots with D173's confirmation lag | `pivots` | `research/structure.py` |
| panel, cleaning, costs, dividend frame | `load_panel` | `run_macd_ladder.py` |
| signed scorer, financing, rotation null with money/vol legs | `score`, `_excess_sharpe`, `rotation_nulls`, `signed_log_returns` | `run_short_mirror.py` |
| S1's book, so ρ is against a bit-identical arm | `base_masks`, `hold_book` | `run_stops_targets.py` |
| trade spans, and the entry-price convention | `trade_spans`, `overlay`'s walk | `run_filter_search.py`, `run_stops_targets.py` |

**Written fresh:** the O(T) rolling pivot regression, the onset/age-cap state machine, the ATR,
and **the matched-exit-count overlay null**.

**Efficiency is a design requirement, not an optimisation.** The naive rolling OLS refits at
every `(symbol, bar)` — 86k regressions. Instead each pivot deposits its `(1, x, y, x², xy)`
contribution at its own bar index, one cumulative sum turns those into prefix sums, and a window
sum is a single subtraction. **O(T) per symbol, fully vectorised over bars; measured at 0.2s for
all 57 symbols.** The causal window is `i ∈ [t−252, t−k]`, expressed exactly as
`P[t−k] − P[t−253]`.

## Verification

- Full suite green, offline, deterministic; `--report-only` re-renders **byte-for-byte**, with
  `CELL_ORDER` explicit from the start.
- **The prefix-sum OLS is pinned against a brute-force `np.polyfit`** on sampled bars. A fast
  path that is not checked against the slow one is a defect waiting to happen.
- **The causal window is asserted directly:** no pivot with `confirmed_at > t` may enter the
  fit at bar `t`. Tested by placing a pivot and checking it is invisible for exactly `k` bars.
- **No look-ahead in the overlays:** a stop decided at close `t` takes effect at `t+1`, matching
  `run_stops_targets.overlay`'s stated convention.
- **S1 must reproduce +0.746 / 18.9% / −10.30%** in this runner, or the ρ comparison is void.
- **The overlay null must preserve exit COUNT exactly** — asserted, since that is the single
  property that makes it the right control.

---

## STAGE 1 — SCREEN RESULT

*Appended after the run. **A screen, not a verdict.** The holdout 60 and the 2025–2026 forward
window are untouched.*

**Produced:** 2026-08-28 · `uv run python scripts/run_uptrend_onset.py` · Page:
[`UPTREND_ONSET_RESULTS.md`](../results/UPTREND_ONSET_RESULTS.md)

### The one-sentence version

**Every registered hurdle cleared — the first time in this programme — and the reason it matters
is ρ = +0.150, not the Sharpe: this is the first arm that is both real and genuinely
uncorrelated with S1.**

### The cells

| | | exposure | excess Sharpe | CAGR | deployable | max DD | Calmar | E |
|---|---|---:|---:|---:|---:|---:|---:|:--:|
| **A0** | base — onset + age cap | 14.2% | **+0.610** | 2.37% | 5.87% | −5.78% | 0.409 | ✗ |
| **A1** | + structural sloped stop | 12.5% | +0.720 | 2.25% | 5.82% | −2.45% | 0.921 | ✗ |
| **A2** | **+ fixed −8% stop** | 13.0% | **+0.822** | 2.52% | 6.08% | **−1.93%** | **1.306** | ✗ |
| **A3** | + target at +2R | 13.2% | +0.524 | 2.06% | 5.59% | −5.76% | 0.357 | ✗ |
| **A4** | + stop and target | 11.7% | +0.652 | 2.03% | 5.63% | −2.39% | 0.848 | ✗ |
| *S1* | | *18.9%* | *+0.746* | *5.43%* | *8.83%* | *−10.30%* | *0.527* | — |
| *B&H* | | *100%* | *+0.235* | *8.42%* | *8.42%* | *−34.60%* | *0.243* | — |

### The four hurdles

**B — the entry rule beats its rotation null.** A0 at the **97.3rd percentile** on Sharpe and
the **99.2nd on money**, vol ratio 1.055x. Same exposure, turnover and holding periods, wrong
bars. **The onset timing carries information**, and the money leg — which cannot be inflated by
volatility — is the stronger of the two.

**C — the diversification condition, and this is the finding.** `ρ = +0.150` against S1, so the
bar is **+0.112** and A0 scores **+0.610**. Cleared by more than 5×. Every cell clears.

**A — R7's matched-exit-count overlay null.** Keep A0's book, cut the same number of trades short
at random trades and random points inside their own spans:

| | trades cut | actual | null p50 | null p95 | **percentile** | A |
|---|---:|---:|---:|---:|---:|:--:|
| A1 structural stop | 56 of 245 | +0.720 | +0.618 | +0.758 | 89.1th | ✗ |
| **A2 fixed −8%** | 40 of 245 | **+0.822** | +0.614 | +0.741 | **99.6th** | **✓** |
| A3 target | 38 of 245 | +0.524 | +0.613 | +0.741 | **2.5th** | ✗ |
| A4 both | 85 of 245 | +0.652 | +0.627 | +0.802 | 58.7th | ✗ |

**D — all five beat buy-and-hold's +0.235.**

### Three results worth separating from the headline

**The plain stop beat the clever one.** A1 — the structural sloped line, the construction this
record spent two amendments getting right — lands at the **89.1st percentile and fails**. A2, a
flat −8%, lands at the **99.6th**. The elaborate anchor added nothing over a constant.

**The target is actively harmful, at the 2.5th percentile.** Cutting winners at +2R is *worse*
than cutting the same number of trades at random. That is D235's "targets cap the tail" finding
reproduced on a different entry rule and against a correct null.

**The bootstrap, which D240 failed to register and which is the most deflating number here.**

| | excess Sharpe | p05 | excludes 0 | Δ vs B&H | p05 | excludes 0 |
|---|---:|---:|:--:|---:|---:|:--:|
| A0 | +0.610 | −0.103 | ✗ | +0.375 | −0.118 | ✗ |
| **A2** | **+0.822** | **+0.207** | **✓** | +0.587 | −0.111 | ✗ |
| *S1* | *+0.746* | *−0.009* | *✗* | *+0.511* | *−0.204* | *✗* |

**A2's own Sharpe interval excludes zero where S1's does not.** But **no arm's advantage over
buy-and-hold excludes zero**, S1 included — exactly the weakness `BOOK.md` already records.

### What the pairing would be worth

Closed form on numbers already computed — **not a book, not a cell**:

| | combined Sharpe | gain | years to significance |
|---|---:|---:|---:|
| S1 alone | 0.746 | — | 8.8y |
| **S1 + A0** | 0.900 | +0.154 | 6.7y |
| **S1 + A2** | **1.032** | **+0.286** | **5.5y** |

**8.8 years to 5.5.** Real, and still not two.

### Scoring — three of six, and two misses were pessimistic for once

| | prediction | outcome |
|---|---|---|
| **P1** | exposure near 17–18% | **FALSIFIED**, 14.2% — trades end on state exit more often than on the age cap |
| **P2** | A0 beats buy-and-hold | **CONFIRMED**, +0.610 vs +0.235 |
| **P3** | excess Sharpe +0.30 to +0.45 | **FALSIFIED**, +0.610 — above my range |
| **P4** | ρ below 0.35 | **CONFIRMED**, +0.150 — well below |
| **P5** | no overlay beats its matched-exit-count null | **FALSIFIED.** A2 at the 99.6th |
| **P6** | A0 beats its rotation null | **CONFIRMED**, 97.3rd |

### What is wrong with it — at full strength

1. **Hurdle E fails worse than anything in the book: 2 entries per symbol** against 30, from 245
   onsets across 57 names. S1's 9 was already called the weakest part of its case. **This is the
   single biggest reason not to believe this yet.**
2. **A2's pass is not multiplicity-corrected.** Four overlay cells were tested and no best-of
   null was registered (D228's pattern exists and should have been used). A Bonferroni read of
   99.6th across 4 cells still survives at ≈1.6%, but that is a reconstruction, not a
   pre-registration.
3. **The design is fitted.** The age cap, the long-only decision and the state definition were
   all chosen from anatomy on this same fixture. Declared in advance in this record, and it
   remains true.
4. **Deployable return is weak — 6.08% against buy-and-hold's 8.42%.** At 13% exposure this is a
   diversifier, not a return engine, and it does not by itself move the income arithmetic.
5. **The √f "selection quality" figures of +588% to +870% are an artifact** and should not be
   quoted. Buy-and-hold at 13% exposure predicts only +0.085, so any competent arm looks
   enormous as a ratio.
6. **R dispersion is 16.2×** (p5 1.58%, p95 28.91%) even after amendment 2's floor. Equal-weighted
   positions therefore carry very unequal risk, and A3's failure is partly this.

### What survives

**A0 and A2 are promoted to a pre-registered out-of-sample test — nothing else.** Under R8 that
is the only route to `BOOK.md`, and neither is in it.

**The next study is the one this cannot do: an actual combined book.** Hurdle C is
weighting-independent and passed, but a concrete S1 + A2 book with a paired bootstrap against S1
alone has not been built, and the table above is arithmetic rather than a measurement.

**And the honest summary of the state of play:** this is the strongest screen the programme has
produced, on a fitted design, with a sample-size hurdle failing worse than any previous arm, and
no out-of-sample evidence whatsoever.

### Ledger

| count | N |
|---|---:|
| fresh — 5 cells | 5 |
| the gradient anatomy: 8 states, 3 books, 10 age buckets | 21 |
| + D239's 3, D238's 4, D234's 6, D235's 7, D236's 6 | 47 |
| + disclosed ETF prior | **45,850** |

---

## CORRECTION, 2026-08-28 — the headline above quoted the wrong number

*Appended rather than edited, per the append-only rule.*

**This record's headline was A2 at +0.822, on the strength of the −8% stop clearing R7's
matched-exit-count overlay null at the 99.6th percentile.**
[D242](D242-the-uptrend-arm-on-withheld-data.md) tested that on withheld data and **the stop's
edge collapsed to the 71.7th percentile.**

The caveat recorded above — *"A2's pass is not multiplicity-corrected; four overlay cells were
tested and no best-of null was registered"* — is what happened. A best-of-four at the 99.6th with
no correction regressed exactly as such things do, and D242's R3 predicted it in advance.

**A0 is the finding, not A2.** A0 replicated and *grew*, +0.610 → +0.672 at the 99.7th percentile
of its rotation null, and it is what entered `BOOK.md` as **S2**.

**What the stop still does:** it lowers max drawdown from −4.40% to −2.71% out of sample. That is
a *mechanical* benefit of holding less, exactly as D236 characterised exposure controls — **it is
a risk control, not alpha.** Nothing above this line is retracted; the reading of it is corrected.
