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

### The stop, which is the proposer's construction made robust

```
    R      = m * ATR(21) / price          (m = 1, ATR window 21 -- one month, canonical)
    line   = the frozen g_lo regression line, EVALUATED AT THE ENTRY BAR
    stop   = min(line, entry_price) * exp(-R)
```

**Frozen, and deliberately a level rather than a sloped line.** Freezing is the proposer's idea
and it is a good one — the stop is knowable at entry, so R-multiples and sizing are well defined
and the stop cannot chase price down as the fit updates. But **extrapolating a fitted slope
forward is not registered**: the median trade is 63 bars against a 252-bar fitting window, and
trend slopes mean-revert over that horizon. The *level* is frozen; the slope is not projected.

`min(line, entry_price)` guarantees the stop sits below entry — without it a sharply rising low
line would stop the trade out on its first bar.

### Cells — five

| | overlay |
|---|---|
| **A0** | none — the base rule |
| **A1** | structural stop, above |
| **A2** | fixed stop at **−8%** from entry |
| **A3** | take profit at **+2R**, full exit (`R` = the A1 stop distance) |
| **A4** | A1 and A3 together |

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
