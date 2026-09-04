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

---

## 9. CORRECTION, 2026-09-04 — the first run scored the WRONG QUANTITY, and §1–§2 above are largely artefact

Appended, not edited. §1–§7 stand as the record of what was reported.

**`fwd_demeaned`, inherited from D327, SUMS simple daily returns over the k-bar
window. A held position COMPOUNDS.** Neither D327 nor D328 ran the right-quantity
assertion CLAUDE.md requires of every runner, and on the bouncy $8 names at the
extremes the two quantities differ by up to **112 bp** at k=20. The runner now
scores `prod(1+r) − 1`, asserts it differs from the summed grid (`[RQ]`), keeps
`[1]` on the summed quantity so it still reproduces D327 exactly, and writes to
`data/d328b_profile_at_depth_compounded.json`. The first run's file is kept.

**A second defect was in my analysis, not the runner.** D326's
`net_per_trade = gross − two_c`, so a D326 "trade" is one **name**. §2 compared
a two-leg pair spread to a one-leg gross — a factor of ~2 before anything else.

### 9.1 What the compounded profile shows, k=20

| signal | L0 | L1 | L2-3 | MID | S2-3 | S1 | S0 | rank-0/1 spread | t(L0) |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| hist_L | +210 | +205 | +180 | −2 | −20 | −27 | **−91** | +267 | +2.96 |
| retrace_leg | +112 | +17 | +49 | +9 | −11 | −69 | +19 | +89 | +2.74 |
| skew_63 | −47 | +20 | −30 | +8 | +89 | −41 | −98 | +56 | −1.14 |
| rsi | +57 | +75 | +156 | +6 | +7 | −77 | −18 | +114 | +1.14 |
| **macd_hist** | **−557** | −165 | −54 | +22 | −47 | −109 | **−650** | **+18** | **−12.58** |
| price_log | +107 | +17 | +473 | −12 | −196 | −305 | −605 | +518 | +1.49 |

### 9.2 What falls

1. **"The lenses are inverted, ρ = −0.900."** Compounded: **ρ = 0.000.** The
   inversion was the summing artefact, largest in the highest-vol names. The
   lenses are not inverted; they are **uncorrelated**. Q6 still fails and D329
   still does not run — but §1's framing is withdrawn.
2. **§2's "unrealised ratio", ρ = −1.000, and the price-deviation hypothesis
   built on it (§7.2, and FINDINGS §14 as first written).** Both defects stacked.
   Properly scaled and compounded, per-leg rank-0/1 edge against D326 per-name
   gross is hist_L 1.42, rsi 0.74, retrace_leg 0.55, skew_63 0.46, macd_hist
   0.21 — **four of five books realise MORE per name than the snapshot**. There
   is no unrealised-ratio phenomenon. Withdrawn entirely, including the proposed
   test on D290's 51 signals.
3. **Q5, and D327 §2.** `hist_L`'s short end is **−91 bp** compounded, not +21.
   The names it shorts **fall**. "The incumbent's short leg is actively harmful"
   was the summing artefact on $8 names; **Q5 is FALSIFIED** and D327 §2 is
   superseded.
4. **§1's "1.1× to 8.8× larger at rank 0–1."** Compounded it is mixed: hist_L
   4.1×, retrace_leg 2.3×, rsi 1.3×, `price_log` **0.33×** — its rank-0 names
   are sub-$1 and dominated by bounce; its tilt sits at ranks 2–3 (+473). Q2 is
   falsified on three signals, not one.
5. **The flat-per-bar diagnostic (§5.4)** is narrower than stated. `macd_hist`
   is still flat (−23.7, −27.9, −24.0 per bar). `price_log` at L0 is **not**
   (7.4, 5.4, 2.1) for the same sub-$1 reason. It separates `macd_hist` from the
   four signals; it is not a general instrument.
6. **Assertion `[5]` as pre-registered** — "the t must fall when the sample is
   halved" — **fired on the compounded run**: hist_L's rank-0 t is 2.96 full and
   **3.00 on the first half alone**. That asserted a property of the data, the
   third time that shape of error has appeared here (D324 `[S]`, D327 `[1]`).
   Replaced with the code property it was reaching for: MID has 991,600
   name-bars over 3,187 bars and L0 exactly one per bar. The halving stays as a
   printed diagnostic — **first-half concentration is itself a finding**
   (FINDINGS §6).

### 9.3 What stands, and is now cleaner

1. **`macd_hist` is dimensional and its extremes rank price** — a code fact and
   a price measurement, untouched by the return quantity. Compounded, it is the
   cleanest demonstration this programme has: **−557 at one end, −650 at the
   other, spread +18.** The price effect cancels almost exactly between the legs,
   and what is left is nothing, carrying 146 bp of round trip.
2. **The ∪ / ∩ shape, the independence-not-correlation point, and the mechanism:
   return cancels between the legs, cost adds across them.** All price and
   spread measurements. §3 stands.
3. **`hist_L`'s extremes are $8–10 names at 4× its own middle's spread.** Stands.
4. **Resolution was not the explanation for D327's Q5.** ρ moved −0.200 → 0.000,
   still nowhere near +0.7. Stands.
5. **`hist_L` is a real, short-lived signal**: rank-0 edge +201 (k=10), +210
   (k=20), **+80 (k=40, t=0.84)**. The summed version showed +298 at k=40 and
   hid the reversal.

### 9.4 The statistic for price-independence, mechanism-derived

Since the book trades the two ends, decompose their prices against the **live
universe median** ($30.7), not the profile's own middle — `macd_hist`'s middle is
its cheap tail. Common mode is the symmetric tilt (cost without return);
differential is the factor bet. Measured on the cost channel directly:

```
common-mode half-spread at the ends, x universe median 14.2 bp
   hist_L 2.91   macd_hist 2.22  |  retrace_leg 1.17   skew_63 0.83   rsi 0.82
```

**A threshold near 2× separates the two losing books from the three winners.**
It is a separation on n=5, not a ranking, and the ordering within either group
is noise. Neither a rank–price correlation (passes a ∪) nor a local-neighbour
deviation (passes a *smooth* ∪, which `macd_hist`'s is) can see it.

## 10. Files, amended

`data/d328b_profile_at_depth_compounded.json` (the result) ·
`data/d328_profile_at_depth.json` (the first run, superseded, kept) ·
`scripts/run_d328_profile_at_depth.py` (`--summed` reproduces the first run)

---

## 11. CORRECTION 3, same day — §9 over-corrected: there are two CONVENTIONS, not a wrong quantity, and their difference is the finding

Appended, not edited. Prompted by a read-only audit of the chain that found the
summed quantity in **every book simulator from D295 through D326**
(`run_d306_width_exits.py:184`, `st[1] += sgn * (v − mt)`, and the same line in
D295, D298–D301, D303, D305, D310), and in D304's forward-return helper.

### 11.1 The two conventions

A book that sets `ret[t] = mean(one-bar returns of the held names)` is
**equal-weight, rebalanced daily**. Over a hold that book earns the **sum** of
the one-bar returns — the summed trade `cum` is *exactly right for that book*.
Buy-and-hold with constant shares earns the **compound**. Neither is "the right
quantity"; they are two position-sizing conventions, and:

- **the programme's books use the sum**, per bar and per trade;
- **D327's profile matched them**;
- **§9 switched D328 to buy-and-hold** and then, in §9.2.2, compared it against
  D326's summed gross — a mixed-convention ratio, which the audit caught.

`[RQ]` still stands as an assertion — the two grids *must* differ — but its
message that the summed one was "the wrong quantity" is withdrawn. Both are
reported, and the runner's docstring now says so.

### 11.2 The comparison with BOTH conventions and scales matched

Per-leg summed edge (the books' convention, ÷2 for one name) against D326's
per-name gross and net, `k=20`:

| signal | per-leg edge | D326 gross/name | ratio | D326 net/name |
|---|--:|--:|--:|--:|
| hist_L | +130 | +94.0 | 1.38 | −1.97 |
| macd_hist | +64 | +43.7 | 1.46 | −6.36 |
| rsi | +47 | +77.0 | 0.61 | +37.33 |
| retrace_leg | +44 | +80.2 | 0.55 | +47.10 |
| skew_63 | +37 | +61.0 | 0.61 | +45.49 |

**ρ(per-leg edge, gross) = +0.300. ρ(per-leg edge, net) = −0.800.** The
anti-correlation with net is real under the books' own convention, and it is
**cost**: the signals with the largest depth-free edge hold the most expensive
names (§3, §9.4). It is not a paradox and it is not resolution. §9.2.1's
"ρ = 0.000" was the buy-and-hold view against a rebalanced book and is
withdrawn as a comparison.

### 11.3 The difference between the conventions is the REBALANCING PREMIUM, and on `hist_L`'s names it is the size of the effect

Summed minus compounded, per leg, `k=20`, in bp — what daily rebalancing adds
to a long and *takes from* a short on the same names:

| signal | long leg | short leg | held price |
|---|--:|--:|--:|
| **hist_L** | **+78** | **−85** | $8–10 |
| macd_hist | +53 | +57 | $2,700 (price sort) |
| rsi | +10 | −30 | $19–37 |
| skew_63 | +20 | −2 | $21–33 |
| retrace_leg | +0 | −3 | $25–38 |

A long that is topped back up after every fall and trimmed after every rise
harvests volatility; a short rebalanced the same way pays it. On a $8 name that
moves several percent a day, that is **163 bp over 20 bars between the two legs
of the same signal.** On `retrace_leg`'s names it is nothing.

**So D327 §2 is reinstated, with its mechanism.** Under the convention the book
actually runs, `hist_L`'s short leg contributes **−26 bp** per name at `k=20`
and the names it shorts do not fall net of rebalancing. §9.2.3 withdrew that
on the buy-and-hold number (−91); **buy-and-hold is not what the book does.**
The correct statement is narrower and more useful than either: **`hist_L`'s
short leg is short the rebalancing premium on bouncy names.** It is a
position-sizing artefact, not a signal failure, and the fix is not to drop the
leg — it is to hold the short leg in constant *shares*, or in names that do not
bounce. D283's "symmetry fails BY SIGN" now has a mechanism: **a rebalanced
long and a rebalanced short on the same volatile names are not symmetric.**

### 11.4 And the rebalancing is UNCOSTED

Every runner from D295 to D326 charges cost at entry and exit (`two_c`) and
earns the daily-rebalanced sum. The daily trades that make the sum realisable
are not charged. Order of magnitude on `hist_L`'s names: a ~5%-a-day name at
46.7 bp half-spread rebalances ~5% of notional a day at ~2.3 bp, so ~**30 bp
per name over a 14-bar hold** against a `two_c` of 96. Second-order, not
negligible, and **it belongs beside FINDINGS §10's unpriced turnover.** Not
measured here; flagged.

### 11.5 What this does to §9

| §9 item | status after §11 |
|---|---|
| 9.2.1 lenses uncorrelated at 0.000 | **withdrawn as a comparison** — mixed conventions. Matched: +0.300 gross, −0.800 net, and the −0.800 is cost |
| 9.2.2 unrealised ratio withdrawn | **stays withdrawn** — the matched ratio (1.38, 1.46 vs 0.55–0.61) is the rebalancing premium on bouncy names, which §11.3 measures directly |
| 9.2.3 D327 §2 withdrawn | **reversed** — §2 reinstated under the book's convention, with the mechanism in §11.3 |
| 9.2.4–9.2.6 | stand |
| 9.3 | stands |
| 9.4 the common-mode statistic | stands |
| D327 §9.2 "a long-only reading of `hist_L` is owed" (W6) | **closed** — D290 ran all 51 long-only and fifty of fifty-one are market drift (D290). The question §2 actually raises is the short leg's sizing, §11.3, not a long-only book |

### 11.6 D329 and the leg-wise composite

D329 as pre-registered — an *additive* predictor from single-signal profiles —
still does not run: ρ(edge, net) = −0.800 says the profile predicts the book's
*cost*, not its net. What §11.3 does motivate is a **leg-wise** composite:
`hist_L` owns a long leg (t = +2.96, +3.84) whose rebalancing premium *helps*;
`skew_63` owns a short leg (t = −6.43, −2.05) in $30 names at 5–8 bp where
there is **no** premium to pay. That is a pre-registrable construction with a
mechanism, and the audit's Part B says its per-trade comparison must be run on
the *same* convention as the parents. Filed as the next candidate; not run.
