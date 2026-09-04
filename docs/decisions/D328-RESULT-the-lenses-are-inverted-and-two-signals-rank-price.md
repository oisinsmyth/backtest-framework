# D328 RESULT — Q6 fails harder, and the reason is that two signals rank price at the depth the book trades

**Status:** RESULT. Pre-registered at `cad090b`, runner at `c954ed8` — both
before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**Nothing is promoted. There is no path here, so nothing here can be priced.**

---

## 1. Q6 FAILED, and my diagnosis was wrong

**Spearman between rank-0/1 edge and D326's per-trade lens is −0.900.** D327's
was **−0.200**. Fixing the resolution did not repair the disagreement — **it
turned a weak disagreement into a nearly perfect inversion.**

D327 §4 blamed its own buckets: bucket 0 was the top 5% of ~988 live names, and
the book holds 2. **That description was right and the inference from it was
wrong.** The buckets *were* averaging the extremes away — at rank 0–1 the edges
are **1.1× to 8.8×** what D327's top-5% bucket showed — and sharpening them made
the two lenses disagree *more*, not less.

**Per the pre-registered stop condition, D329 does not run.**

| signal | D328 rank-0/1 spread | D327 b0−b19 | D326 net/trade | D326 mean/2c |
|---|--:|--:|--:|--:|
| **hist_L** | **+260** | +11 | **−1.97** | 0.98 |
| macd_hist | +128 | +44 | **−6.36** | 0.87 |
| rsi | +94 | +71 | +37.33 | 1.94 |
| retrace_leg | +87 | +55 | +47.10 | 2.42 |
| **skew_63** | **+74** | +3 | **+56.22** | 4.53 |

**The two signals with the largest depth-free extreme-rank edge are the two
losing books. The signal with the smallest is the best book.**

## 2. The inversion is monotone in ONE quantity, at ρ = −1.000

Not cost, and not depth. Charging each signal its own measured held-name round
trip moves ρ from −0.900 only to **+0.100** — so cost is most of the gap and
still leaves it unexplained.

**What is perfectly monotone is how much of the depth-free spread the book fails
to realise.** At matched `k = 20`:

| signal | D328 gross | D326 gross/trade | **unrealised ratio** | D326 net/trade |
|---|--:|--:|--:|--:|
| macd_hist | +128 | +43.7 | **2.92×** | −6.36 |
| hist_L | +260 | +94.0 | **2.76×** | −1.97 |
| skew_63 | +74 | +61.0 | 1.22× | +56.22 |
| rsi | +94 | +77.0 | 1.22× | +37.33 |
| retrace_leg | +87 | +80.2 | **1.09×** | +47.10 |

**ρ(unrealised ratio, D326 net per trade) = −1.000**, five of five, no ties.

Two signals give back **~65%** of their measured extreme-rank spread when the
book actually holds them. Three give back **9–18%**. **That split is the whole
result**, and §3 says what produces it.

## 3. `macd_hist` does not rank momentum at its extremes. It ranks PRICE.

Median price by rank bucket, `k=20`:

| signal | L0 | L1 | L2-3 | L8-15 | **MID** | S8-15 | S2-3 | S1 | S0 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **macd_hist** | **2706** | 798 | 438 | 176 | **22** | 185 | 477 | 1002 | **3020** |
| **hist_L** | **10** | 10 | 12 | 17 | **41** | 17 | 12 | 9 | **8** |
| retrace_leg | 25 | 27 | 28 | 31 | 37 | 42 | 41 | 38 | 37 |
| skew_63 | 21 | 26 | 29 | 31 | 38 | 37 | 32 | 33 | 30 |
| rsi | 19 | 21 | 22 | 26 | 37 | 43 | 40 | 36 | 37 |

**`macd_hist` is dimensional.** `src/backtest_framework/research/macd.py:185`
computes `ema_fast − ema_slow` on **raw closes**, and `signal_line_score` returns
that histogram unchanged — **in dollars**. A $3,000 stock's histogram is ~100×
a $30 stock's for the same *percentage* move. So its most extreme ranks are
**literally a price sort, symmetrically at both ends**: $2,706 at L0 and $3,020
at S0, against a **$22** middle.

That is why its edge is hugely negative at *both* extremes — **−531 bp at L0 and
−723 at S0, `t` = −10.29 and −9.61**. Both tails are measuring the same
expensive-name effect, and the book longs one and shorts the other.

**This overturns D327 §3.** D327 read the same shape as "`macd_hist` is inverted
at the long end and its real information sits in the middle, which is what a
composite harvests." The correct statement is narrower and less exciting: **its
extremes are not its signal at all.** Its middle `t` of **+9.62** is where its
information is, and a composite works on it because a 25-name gate compresses the
price dispersion that the full cross-section's extremes are sorting on.

**`hist_L` is a different fault.** It is built on **log** high/low/close
(`scripts/run_activation_threshold.py:69`), so it is scale-free and this is *not*
a dimensional bug. But its extremes still hold **$8–10** names against a **$41**
middle — a **volatility tilt**, because percentage moves are largest in the
cheapest names. **Q7's own numbers price it**: 46.7 bp half-spread at L0 against
a **11.3 bp** middle and a **14.2 bp** universe median, so the incumbent's
primary selects names costing **4×** its own middle to trade.

**The three signals that realise their spread are the three that sit near the
universe in both price and spread**: $19–27 and 9.6–16.4 bp.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | aggregation reproduces D327 to floating point | **CONFIRMED** — the same 2,623,344 name-bars, **0.0e+00 bp**. *The assertion as pre-registered was impossible; §6 says why and what replaced it* |
| **Q2** | ranks 0–1 show materially more edge than D327's top-5% bucket, everywhere | **FALSIFIED as written, CONFIRMED in substance.** In *magnitude* every signal is **1.1× to 8.8×** larger. It failed because I coded a signed `>`, and `macd_hist`'s rank-0 edge is more **negative** (−308 against −35) |
| **Q3** | `skew_63`'s rank-0/1 edge is far above its flat profile | **CONFIRMED, and it means nothing.** +6.8 against −2.3 is 3.0× a ratio of two numbers that are both noise: `t` = **−0.87** at L0 and **+1.79** at L1. *The prediction was badly specified and I am not counting it* |
| **Q4** | rank 0 is **not** distinguishable from rank 1 *(against)* | **FALSIFIED** — and only for the price-tilt signals. `macd_hist` −10.29 against −1.98, `price_log` +5.67 against +0.64; `hist_L` +3.95 against +5.66 is inside the bar. **Rank 0 is special exactly where rank 0 is the most extreme price** |
| **Q5** | `hist_L`'s short end stays positive at full resolution | **CONFIRMED** — S0 is **+21 bp**, S1 **+31**. D327 §2 survives the resolution fix |
| **Q6** | rank-0/1 ranks the signals as D326 does, ρ > +0.7 *(load-bearing)* | **FALSIFIED at −0.900**, worse than D327's −0.200. **D329 does not run** |
| **Q7** | the half-spread at rank 0 exceeds the universe median, everywhere *(against)* | **FALSIFIED, 4 of 6.** `hist_L` 46.7, `price_log` 133.4, `macd_hist` 32.7 and `retrace_leg` 16.4 are above 14.2; **`skew_63` 13.4 and `rsi` 9.6 are below.** The split is not noise — it is §3's split |

## 5. What this establishes

1. **Resolution was not the explanation for D327's Q5, and the finer lens proves
   it by failing harder.** A depth-free extreme-rank edge and a per-trade book
   measurement are **anti-correlated** across these five signals. Whatever the
   winning books earn, **it is not the rank-0/1 edge measured here.**
2. **`macd_hist` is unnormalised and its extreme ranks are a price sort.** That
   is a construction defect, not a signal property, and it invalidates D327 §3's
   reading of the composite mechanism.
3. **`hist_L`'s extremes are a volatility tilt** — $8–10 names at 4× its own
   middle's spread. The incumbent's primary pays D284's tax at the depth it
   trades, and this is the first measurement that shows it there.
4. **Edge per bar at a fixed rank separates a forecast from a standing tilt**,
   and this one *is* a result. Across `k` = 10, 20, 40 at rank 0:

   ```
                 k=10    k=20    k=40
   macd_hist    -20.0   -26.6   -26.5   CONSTANT -- a static tilt
   price_log    +18.5   +19.4   +17.4   CONSTANT -- the known-bad control
   hist_L       +22.4   +13.6    +7.4   decaying -- a real, short-lived signal
   rsi          +13.9    +3.6    +3.5   decaying
   retrace_leg  +11.0    +5.6    -0.6   decaying
   skew_63       +5.8    -1.9    -4.8   decaying
   ```

   **A constant per-bar edge means the same names sit at that rank day after day
   drifting at a constant rate, and nothing is being forecast.** `macd_hist`
   matches the control, not the signals. **Run this before trusting any
   extreme-rank edge**, and it costs one extra horizon.
5. **The unrealised ratio is a candidate instrument.** It orders these five
   perfectly and §7.2 says what does and does not explain it.

## 6. Assertions

All seven pass.

| | |
|---|---|
| **[1]** | **AGGREGATION.** *The pre-registered form was impossible*: log-spaced **rank** buckets do not nest inside equal **rank-percentile** bins, because a percentile boundary lands at a different rank every bar as the live count moves. What the two bucketings share is the **name-bars**, so D327's 20 bins are accumulated in the same pass through the same `np.add.at` call. Same **2,623,344** name-bars, reproducing D327 to **0.0e+00 bp**. Weaker than promised only in that it cannot catch a bucketing error preserving membership — which `[2]` covers |
| **[2]** | the 21 buckets partition a 900-name cross-section, and **L0, L1 and S0 hold exactly one name each** |
| **[3]** | the demeaning is exact to **3.1e-17** at every bar |
| **[4]** | CAUSALITY — peeking moves the profile by up to **20.2 bp** |
| **[5]** | the `t` is from the **per-bar** series, and halving the bars cuts it **+3.95 → +3.40**. *A `t` over pooled name-bars would barely have moved, which is the point* |
| **[C]** | the ratio is edge / (2 × half-spread); the paired 4× is rejected |
| **[6]** | the check raises on a bucket handed free money |

**A new guard was needed**: `price_log` is the known-bad control and D326 never
ran it, so the ρ is over the **five** signals D327's Q5 used, asserted to be five.

## 7. What is owed

1. **`macd_hist` should be normalised** — by price or by ATR — and re-measured.
   Every study that ranked on it cross-sectionally ranked partly on price, which
   reaches back through D290's screen and D325's composites.
2. **Why the unrealised ratio orders the books perfectly.** ***Persistence was my
   candidate when this record was first filed, and it is measured wrong***:
   ρ(unrealised, trade count) = **−0.400**, ρ(unrealised, holding run) =
   **+0.000**. What orders it is **how far the rank-0 names sit from the universe
   in price**, |log(price at L0 / price at MID)| — **ρ = +1.000, five of five**.
   **That is a hypothesis on five points with a measure chosen after seeing them,
   and it must not be cited as a result.** The test that would make it one is
   pre-registered on **D290's 51 signals**, where the price deviation is
   computable before any book is run. See
   [FINDINGS §14](../FINDINGS.md#14-a-cross-sectional-ranking-on-a-quantity-that-carries-units-ranks-those-units).
3. **`skew_63` remains open**, and D328 makes it stranger: it has the *best* book
   in the study and **no measurable edge at the depth it trades** (`t` = −0.87
   at L0). Its advantage is not in the extreme ranks.
4. **D327 §3 must be read against §3 here.** It is amended, not retired.

## 8. Files

`data/d328_profile_at_depth.json` · `scripts/run_d328_profile_at_depth.py`
