# D312 RESULT — the rule fails on its estimator, not on its premise

**Status:** RESULT. Pre-registered at `201dfff`, runner committed at `f2e9814`
before this file existed (R8).
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. What I nearly filed, and what the principal caught

**The first draft of this record was titled "the premise was never true" and
closed the risk axis.** Its argument: the book's volatility does not forecast, so
vol targeting has nothing to key on, so the family closes on a property of the
book.

**The principal asked why λ was being computed from the held book at all, when
the whole market is available and names outside the top 19 are just as
informative.** Measured, that changes the answer completely:

| forecast of the next 63 bars' book vol | **N=2** | N=5 | N=10 | N=19 |
|---|--:|--:|--:|--:|
| the book's own trailing sd — **what D312 used** | **−0.016** | +0.056 | +0.185 | +0.347 |
| **cross-sectional dispersion, whole live universe** | **+0.352** | +0.374 | +0.405 | +0.410 |
| **dispersion, the ~969 names OUTSIDE the gate** | **+0.355** | +0.371 | +0.403 | +0.411 |
| dispersion, the 50 gate names only | +0.242 | +0.300 | +0.334 | +0.342 |

**At the width that earns, the forecast goes from −0.016 to +0.352 by changing
nothing but where the estimate is read from.** So the premise stands and **the
estimator was the defect** — and the estimator was a fixed choice written into
the pre-registration, not a property of the book or of the lever.

**This is the third time in this programme I have taken one construction's
failure as a verdict on its whole axis**, after the selectivity/idle-state
overstatement and the one-sided trim. The pattern is the same each time: a
negative result, a mechanism that sounds sufficient, and no check that the
mechanism was a choice rather than a fact. **The measurement in this section was
prompted, not volunteered.**

**None of it rescues D312's cells.** Everything in §2–§6 is what the
pre-registered rule actually did, and it lost to everything it was measured
against.

## 1. What the pre-registered rule did — and it is not misimplemented

Q1 fails at **all eight** targeted cells, by −11.4% to +45.5%. The
pre-registration says *"Q1 fails → the rule is misimplemented and nothing else is
read."* **It is not misimplemented, and that is established rather than
asserted:** the same rule reading bar `t`'s own return — the peeking variant
assertion [3] requires to *differ* — lands on target everywhere.

| arm E | **lagged** | **peeking** |
|---|--:|--:|
| N=2 | **+32.3%** | −3.2% |
| N=5 | **+24.8%** | −1.5% |
| N=10 | **+16.6%** | −0.4% |
| N=19 | **+9.5%** | +0.5% |

**Peeking hits, lagging misses, and the miss is monotone in how blind the
estimator is at that width.** The arithmetic is right; the forecast is worthless.
So the stop condition's antecedent fired, its stated reason was disproved, and I
read the study. That decision is recorded here rather than made quietly.

## 2. The twelve cells — every treated cell loses to its own baseline

`rt` = 57.0 bp, 3,187 bars. Gross and net side by side; cost includes transitions.

| cell | gross | cost | trans | **NET** | vol | vs tgt | **SHARPE** | vol disp | expo |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **F@N2** | +24.12 | 19.74 | 0.000 | **+4.37** | 780 | −0.0% | **+0.089** | 493 | 1.00 |
| B@N2 | +20.70 | 19.24 | 0.143 | +1.45 | 692 | −11.4% | +0.033 | 405 | 1.00 |
| E@N2 | +26.37 | 30.52 | 0.418 | −4.15 | 1032 | +32.3% | −0.064 | 552 | 1.53 |
| **F@N5** | +19.23 | 17.17 | 0.000 | **+2.06** | 487 | −0.0% | **+0.067** | 278 | 1.00 |
| B@N5 | +13.23 | 18.62 | 0.370 | −5.39 | 571 | +17.2% | −0.150 | 286 | 1.00 |
| E@N5 | +19.24 | 25.07 | 0.416 | −5.83 | 608 | +24.8% | −0.152 | 280 | 1.44 |
| **F@N10** | +15.12 | 14.70 | 0.000 | **+0.43** | 346 | −0.0% | **+0.020** | 181 | 1.00 |
| B@N10 | +10.74 | 17.25 | 0.657 | −6.51 | 474 | +36.9% | −0.218 | 240 | 1.00 |
| E@N10 | +12.53 | 20.56 | 0.415 | −8.03 | 404 | +16.6% | −0.316 | 153 | 1.38 |
| **F@N19** | +10.61 | 11.48 | 0.000 | **−0.87** | 263 | −0.0% | **−0.053** | 130 | 1.00 |
| B@N19 | +8.12 | 15.04 | 0.906 | −6.92 | 383 | +45.5% | −0.287 | 203 | 1.00 |
| E@N19 | +6.79 | 15.72 | 0.383 | −8.93 | 288 | +9.5% | −0.492 | 84 | 1.34 |

**Eight treated cells, eight losses, on both statistics.** Not one is close.

**Because realised vols land 9–45% off target, the arms are NOT vol-matched as
designed.** Sharpe normalises and survives that — which is why the
pre-registration made it primary, a choice that proved load-bearing for a reason
it did not anticipate. **Net bp/bar across arms at different realised vol is not
a comparison** and is not presented as one; it is reported because CLAUDE.md
requires gross and net side by side, and because the gross column carries the
mechanism.

## 3. The null — the timing is worse than random, and the null is not a losing one

Circular rotation of the realised path: same move count, same sizes, same
persistence, at unrelated times. 200 draws.

| cell | **Sharpe** | null p50 | null p95 | **p** | net | null p50 | null p95 | **p** |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| B@N2 | +0.033 | +0.083 | +0.167 | 0.781 | +1.45 | +3.97 | +7.51 | 0.781 |
| E@N2 | −0.064 | +0.098 | +0.216 | 0.851 | −4.15 | +8.18 | +16.80 | 0.836 |
| B@N5 | −0.150 | +0.067 | +0.222 | 0.950 | −5.39 | +3.08 | +9.83 | 0.940 |
| E@N5 | −0.152 | +0.077 | +0.172 | 0.985 | −5.83 | +3.60 | +8.34 | 0.985 |
| B@N10 | −0.218 | +0.057 | +0.254 | 0.940 | −6.51 | +2.01 | +9.51 | 0.940 |
| E@N10 | −0.316 | +0.015 | +0.151 | 0.990 | −8.03 | +0.46 | +4.97 | 0.995 |
| B@N19 | −0.287 | +0.011 | +0.254 | 0.955 | −6.92 | +0.38 | +8.21 | 0.970 |
| E@N19 | −0.492 | −0.070 | +0.079 | 0.995 | −8.93 | −1.63 | +1.85 | **1.000** |

**BH-FDR at q = 0.10 over the eight testable cells: NONE survive, on either
statistic.** The four F cells have no path to rotate.

**And this is not R7's pathology.** Seven of the eight nulls have a **positive**
p50 on both statistics — the rotated controls make money where the treatments
lose it. **De-risking at the moments the rule chooses is worse than de-risking by
the same amount, in the same pattern, at unrelated moments** — which follows
directly from a conditioner measured at −0.016.

## 4. My own argument lost 0 for 4, and the reason is one I should have seen

**Q3 predicted E beats B on net at every target. B beats E at every target.**

```
N=2    B +1.45  vs  E −4.15
N=5    B −5.39  vs  E −5.83
N=10   B −6.51  vs  E −8.03
N=19   B −6.92  vs  E −8.93
```

**Vol targeting against a FULL-SAMPLE-sd target is structurally a leverage
rule.** A full-sample sd exceeds the average of rolling sds whenever vol varies
over time — the between-window component sits in one and not the other — so
`target / v_trail` averages **above 1** before any forecasting happens:

| | mean trailing | target | ratio | **realised mean exposure** |
|--:|--:|--:|--:|--:|
| N=2 | 614 | 780 | 1.27 | **1.53** |
| N=5 | 403 | 487 | 1.21 | **1.44** |
| N=10 | 295 | 346 | 1.17 | **1.38** |
| N=19 | 228 | 263 | 1.15 | **1.34** |

(realised exceeds the ratio because `E[1/v] > 1/E[v]`, partly offset by the 2.0
cap, which binds 18–31% of bars.)

**So arm E is about a third leverage and only the remainder risk control — and
leverage on a book that does not cover its costs multiplies the loss.** At N=2 it
buys **+2.25 bp of gross for +10.78 bp of cost** (19.74 → 30.52). That is the
whole of E's failure, and my domination argument assumed exactly what the cost
column denies: that leverage "cuts risk without touching the edge". It does not
touch gross *per unit of exposure*. It scales **cost** linearly — and cost is the
binding constraint here, which D300, D302 and D307 had established and which I
did not carry into the argument.

**Q7 confirmed** — E hurts at the tightest target (−0.064 against F's +0.089),
reproducing D306's −0.153. So the argument was right that E harms and wrong about
everything it concluded from that.

## 5. Breadth is a priced risk lever, not a free one

Arm B never levers; it is always fully invested, and its failure is cleaner:

```
F@N2  gross +24.12   vol 780
B@N2  gross +20.70   vol 692     an 11% vol cut bought for 14% of gross
```

**Widening cuts volatility and gross together, roughly one for one** — the same
trade D300 and D310 priced across static widths, and it does not become free for
being done dynamically. **Dynamic breadth pays the static breadth price on every
bar it widens, and D312 widened on a signal worth −0.016.** Any future risk rule
that works by widening has to beat that price, not merely produce less
volatility.

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | vol within 10% of target | **FALSIFIED** — all 8 cells miss, −11.4% to +45.5%. §1 establishes the rule is not misimplemented |
| **Q2** | dispersion cut by more than half | **FALSIFIED** — best is E@N19 at −35%; **E@N2 and E@N5 RAISE dispersion** (493→552, 278→280). The rule fails to do the one thing it was "guaranteed" to do |
| **Q3** | **E beats B on net at every target** *(mine)* | **FALSIFIED 0 for 4** |
| **Q4** | **B never beats fixed on Sharpe** *(against, load-bearing)* | **CONFIRMED** — and not close at any target |
| **Q5** | breadth path persistent, lag-1 ρ > 0.5 | **CONFIRMED IN LETTER ONLY** — ρ = +0.988 to +0.989. At that value it measures a **near-constant path**, not persistent market vol: B@N2 sits pinned at the grid's most concentrated level for **80.6%** of bars. Unlike D311's Stage 2 this had no shuffled control, so it is not evidence for the mechanism Q5 named |
| **Q6** | transitions under 5% of gross | **FALSIFIED at 2 of 8** — B@N19 11.2%, B@N10 6.1%; the other six pass |
| **Q7** | **E hurts at the tightest target** *(mine, against E)* | **CONFIRMED** — −0.064 against F's +0.089 |
| **Q8** | B beats F wide and not tight | **FALSIFIED** — B beats F nowhere |

Five falsified, three confirmed, and **one of the three confirmations is hollow**
(Q5).

## 7. The stop condition fires, and it closes THIS RULE and not the axis

> **Q4 confirms and Q3 fails → neither lever works on this book; close, and the
> reason is the book rather than the lever.**

**That branch fires and D312 closes.** But its stated reason — *the book* — is
wrong on the measurement in §0: the binding defect is the **estimator**, which
was a fixed choice in the pre-registration and is neither the book nor the lever.
The branch was written under a premise about what would be varying that turned
out not to hold.

**I do not get to keep the family open by reinterpreting a stop condition after
seeing the results.** D312 is closed as specified. A rule conditioned on
universe-wide dispersion is a **new study needing its own pre-registration**, and
§9 states what that must contain.

## 8. A qualifier owed on a published sentence

D311's stop paragraph says *"the static answer stands: `N_eff = 2` on net,
`N_eff = 10` on Sharpe, from D310."* **D310's `sharpe` column is computed on
GROSS**, which is correct for what D310 was doing and is not an error there. On
**net** Sharpe there is no crossover at all:

```
F@N2  +0.089    F@N5  +0.067    F@N10  +0.020    F@N19  −0.053
```

**On net, concentration wins on both statistics**, and "N=10 on Sharpe" does not
survive costs. The sentence needs the word *gross* wherever it is relied on. A
qualifier on a reading, not a correction to D310's arithmetic, filed because a
sizing decision could be made on that sentence.

## 9. What a successor has to carry, and what it must not do

The §0 measurement is **post-hoc and prompted** — taken after D312's result was
known — and **six predictors were compared.** A successor that simply adopts the
best of the six has searched, and must say so.

1. **Pre-register ONE predictor, or declare all of them as arms with BH.** The
   plainest construction is dispersion over the **whole live universe**; the
   marginally better `outside the gate` variant (+0.355 against +0.352) is
   **within noise of it and must not be chosen on that margin.**
2. **Check the predictor's own persistence first, as a Stage 0.** `own` has
   lag-63 ρ = **−0.016** and universe dispersion **+0.616**. One line, before the
   design, would have caught D312.
3. **Do not target a full-sample sd** — §4 shows that is a third leverage. Target
   the mean of the rolling sds, or report mean realised exposure beside every
   cell and treat the arm as leverage plus control.
4. **It still has to beat §5's price.** A ρ = 0.35 forecast is not obviously
   enough to pay 14% of gross for an 11% vol cut. **The forecast being real does
   not make the lever profitable**, and the successor's load-bearing prediction
   should be that it is not.

## 10. Two construction caveats, stated rather than buried

**Arm B splices between sixteen separately-simulated books at bar granularity.**
It charges weight-distance turnover `Σ|Δw|/2 × rt` but does not re-run the
holding path through one simulator, so it is **not a tradeable book** — it is an
instrument for measuring the effect of moving breadth. This is D308's and D311's
construction, inherited deliberately, and it **flatters B**, since a real
implementation would pay the path as well as the weights. B loses anyway.

**Groups 2 and 3 of the reporting standard are inherited, not re-run.** The trade
distribution and winner-dependence splits are D310's for arm F, unchanged and
bit-identical (assertion [1], 4.9e-15). Arms B and E hold the same trades
reweighted and produce no new ledger, so no new trade distribution is computed
and none is claimed. **Groups 1 and 4 are reported in full above.**

## 11. Assertions

All eight pass.

| | |
|---|---|
| **[1]** | arm F reproduces D310's **gross and net** at all 7 shared levels, max 4.9e-15 bp |
| **[2]** | the sizing arithmetic is correct — arm E lands within 10% of every target **when it peeks** — and every arm tracks the target more closely than its own fixed arm |
| **[3]** | **causality** — the rule reads only `t−1`, and removing the lag moves 5.1% of bars to a different level, so the audit *can* fail |
| **[4]** | transitions vanish on a constant path **in both arms** and are monotone: 2→2.5 costs 5.4 bp, 2→25 costs 48.0 |
| **[5]** | all 12 cells are distinct books |
| **[6]** | rotation preserves move count and the \|Δ\| distribution in both arms, up to the single wrap point |
| **[C]** | `rt × turn` = 52.1893 reproduces d295's 52.1893; the doubled form is rejected |
| **[7]** | assertion [1] raises on a book handed free money **inside** the mask |

## 12. What this closes and what it leaves

**Closed:** D312's rule — vol-targeted breadth and vol-targeted exposure, both
conditioned on the book's own realised vol, at all four targets.

**NOT closed, and this is the correction to my own first draft:** the risk axis.
It has been tested once, with a conditioner measured at −0.016, and a
conditioner measured at +0.352 exists and has never been run. D299, D308 and D311
closed *return*-conditioned concentration; **that remains three studies, not
four.**

**Out of scope and unchanged:** the combined B+E arm, at the principal's
direction. §4 argues it is now a worse bet than when suggested — E's contribution
is a third leverage on a book that loses money per unit of it — but that is an
argument, and arguments have done badly here.

**The entry signal remains the only untested surface of any size**, frozen since
D293.

## Files

`data/d312_vol_targeted.json` · `scripts/run_d312_vol_targeted.py` ·
`data/d312_universe_forecast.json` (the §0 measurement)
