# D280 — The forecast pre-check, and where the edge actually lives

**Status:** **MEASUREMENT INSTRUMENT. Scores no cell, ranks no name, proposes no rule.** Same
standing as [`scripts/d268_score_independence.py`](../../scripts/d268_score_independence.py).
**Ledger: 0** — see [Ledger](#ledger) for why, and for what a study built on this *does* inherit.
**Date:** 2026-09-02
**Area:** Strategy research · measurement · **personal track**

---

## What this is, and why it ran BEFORE any pre-registration

[D279](D279-the-concentrated-short-on-dead-inclusive-names.md)'s top-N ranking was look-ahead: it
ranked with `hist_L` at bar `t` and earned bar `t`'s return. **The honest repair is not to abandon
ranking but to forecast the score one bar ahead from information through `t−1`** — R9-clean by
construction. **Before writing that pre-registration, the question is whether the thing can be
forecast at all**, and this record is that measurement.

**It ran before any pre-registration existed, deliberately, because it decides whether there is
anything to pre-register.** That is legitimate for a measurement in a way it would never be for a
study. **The distinction is not that measurement is exempt from [R8](../RULES.md#r8); it is that R8
governs candidates, and nothing here is a candidate.** No cell is scored, no book is built, no
hurdle is evaluated, and nothing here can be traded.

**The guard that makes it safe is stated rather than assumed:** every weight in every construction
is **FIXED** — Taylor's `1, 1, 1/2, 1/6`, unit weights on z-scores — and every `n` comes from a
**declared grid `{9, 21, 34}`** with none selected. **A parameter-free rule cannot overfit.** Parts 1
and 2 additionally report out of sample from **2018-01-01**, which costs nothing and removes the
objection before it is made.

Fixture throughout: `us_shorts_daily_raw.csv.gz`, **1,573 names × 4,187 bars** — the dead-inclusive
daily panel D256 and D279 used. Out-of-sample span **2,174 of 4,187 bars**.

**Five parts, run in order. Part 4 is the finding; parts 1–3 are how it was arrived at, and every
one of them is a negative result.** Part 4 leads here because it is what a reader needs, not
because it came first.

---
---

# PART 4 — THE FINDING. The edge is entirely OVERNIGHT, and close-to-close is the sum of two moves that cancel

`scripts/d280_combined_forecast.py` · `data/d280_combined_forecast.json` · `data/d280_combined.log`

Cross-sectional Information Coefficient — Spearman, **within each bar**, of the **R9-lagged**
`hist_L` against each **part** of the next bar, out of sample from 2018-01-01, minimum 20 names per
bar. **A short ranks ascending, so a NEGATIVE IC is the tradeable direction.**

```
gap(t+1)      = open(t+1)  / close(t)  - 1
intraday(t+1) = close(t+1) / open(t+1) - 1
```

| universe | target | mean IC | t |
|---|---|---:|---:|
| ALL | total | −0.00524 | −1.79 |
| ALL | **gap** | **−0.01531** | **−4.71** |
| ALL | intraday | +0.00168 | +0.65 |
| QUAL | total | +0.00462 | +1.43 |
| QUAL | **gap** | **−0.01255** | **−3.45** |
| QUAL | **intraday** | **+0.00868** | **+2.85** |

**Read the two rows that matter together and this explains the whole programme.**

> **There is a real, correctly-signed OVERNIGHT edge, and a wrong-signed INTRADAY move that cancels
> it. Close-to-close — the only quantity D256 and D279 ever measured — is the SUM OF THE TWO, which
> is why it read as noise.**

On the whole universe the gap carries **−0.01531 at `t` −4.71** and the intraday session carries
**nothing** (+0.00168, `t` +0.65). Inside the qualifying set the gap is still correctly signed at
**−0.01255** and **the intraday session actively runs against it at `t` = +2.85** — so the filtered
set's total IC comes out **positive**, the wrong sign for a short. **Two independent mechanisms are
therefore driving the same failure**: the filter/ranking collision of [part 3](#the-structural-finding-and-it-is-the-one-that-outlives-this-record),
and an intraday reversal that eats the overnight move.

**And it forecloses a whole branch in one measurement.** **No intraday stop, target, partial exit or
overlay of any kind can touch an edge that does not accrue while the market is open.** That is
consistent with [R11](../RULES.md#r11)'s record of D247 — **86.6% of the book's return is timing
that accrues overnight** — arrived at here from a completely different direction, on a different
fixture, at a different frequency.

**The converse is also closed: the position cannot be taken at the open to drop overnight risk.**
Doing so discards the entire measured edge and retains the leg that fights it.

*`gap` and `intraday` are built from raw OHLC and exclude dividends, while `total` includes them, so
the two legs are not required to sum to the total. The decomposition is about WHEN the move happens,
not a restatement of P&L — and the dividend question that raises is [part 5](#part-5--the-dividend-confound-checked-and-cleared).*

---

## PART 5 — the dividend confound, checked and cleared

`scripts/d280_dividend_check.py` · `data/d280_dividend_check.json` · `data/d280_divcheck.log`

**The confound is specific and it had to be checked before part 4 could be believed.** `gap` is built
from **raw** OHLC. The fixture is split-adjusted but **not dividend-adjusted** — `load_ragged`
carries dividends separately in `total_log_returns`, precisely because the raw series does not
contain them. **An ex-dividend drop is an overnight drop, and a short OWES the dividend.** If
`hist_L` tilts toward payers at all, part of −0.0153 is accounting rather than edge.

| score | gap RAW | **DIVIDEND-ADJUSTED** | ex-dates EXCLUDED | ex-dates ONLY (216 bars) |
|---|---:|---:|---:|---:|
| ALL `h` | −0.01531 (t −4.71) | **−0.01498 (t −4.59)** | −0.01494 (t −4.58) | **−0.05197** (t −3.08) |
| ALL `h / lagged range` | −0.01625 (t −5.97) | **−0.01574 (t −5.76)** | −0.01570 (t −5.75) | **−0.05682** (t −3.64) |
| QUAL `h` | −0.01255 (t −3.45) | −0.01122 (t −3.08) | −0.01131 (t −3.10) | too few bars |
| QUAL `h / lagged range` | −0.00488 (t −1.84) | −0.00447 (t −1.68) | −0.00437 (t −1.64) | too few bars |

**Adding the dividend back costs 2–3% of the IC. Excluding ex-dates entirely gives the same answer.
The overnight edge is real.**

**And the mechanism shows up exactly where it should**, which is what makes this a check rather than
a wave-through: **on ex-dates alone the IC is −0.05197, about 3.4× the overall figure.** The
confound exists and is localised — it is simply too rare to move a cross-sectional average, because
**only 0.834% of bars have an ex-date next session**, at a median yield of **0.6535%** against a
median |gap| of **0.5263%**. *The dividend is comparable in size to a typical gap and 120 times
rarer.*

**The score tilt toward payers is −0.0057 at `t` −0.97 over 2,174 bars: none.**

**A book built on this must still charge dividends explicitly rather than net them away**, because
the ex-date subset is where a short's payment is largest and the IC there is 3.4× the average.

### A defect in that script's own output, recorded rather than left to be tripped over

The script prints, unconditionally: *"Positive = payers score HIGHER, so the short ranking ASCENDING
under-selects them and the confound cannot bite hard."* **The measured value is NEGATIVE (−0.0057)**,
so payers score *lower* and an ascending short ranking mildly **over**-selects them — the opposite of
what the printed sentence concludes. The legend is correct; **the conclusion attached to it does not
follow from the sign actually measured.**

**It changes nothing** — the tilt is not significant, and the dividend-adjusted IC settles the
question without reference to the tilt at all. **It is recorded because a line of prose printed
beside a number, asserting what that number means, is exactly the failure mode
[R6](../RULES.md#r6) exists for**, and this one was one copy-paste away from entering a record as a
finding.

---

## WHAT MUST NOT BE CLAIMED FROM PART 4

**AN IC IS NOT MONEY, AND THE GAP BETWEEN THEM IS AN ORDER OF MAGNITUDE OF TURNOVER.**

**An overnight book trades a full round trip EVERY NIGHT.** That is roughly **252 round trips a
year**, against roughly **17** for D279's ~15-day holds — **a 15× increase in the number of times
[D265](D265-the-entry-time-reconciliation.md)'s bar has to be cleared:**

```
mean move per trade  >=  2c        = 10 bp at the 5 bp/side charged throughout D279
```

**A rough prior puts the per-night edge near 4 bp against that 10 bp toll — and that number is NOT
computed from these artefacts.** Nothing in D280 has been through a cost model, a borrow charge, a
null, a book, or the `sigma^2` variance tax of [FINDINGS §1b](../FINDINGS.md). **An IC of −0.0153 is
a ranking statistic. It says the ordering is informative; it says nothing about whether the spread
between the top and bottom of that ordering pays for two crossings of the spread.**

**[D282](D282-the-overnight-only-short.md) is pre-registered by another agent to measure exactly that arithmetic. No result from it is
referenced here, none may be read into this record, and this record makes no prediction about it.**

**The same caution in one line:** D279's own history is a study whose headline statistic was
excellent and whose book lost money before costs. **Every intraday record from D264 to D278 closed
on the cost bar, not on the signal**, and an overnight construction moves *toward* that wall by 15×,
not away from it.

---

## The rest of part 4 — normalisation, combination, and what predicts the gap

### B — volatility normalisation improves the `t` and not the IC

| universe | score | mean IC | t |
|---|---|---:|---:|
| ALL | `h` (baseline) | −0.00524 | −1.79 |
| ALL | `h / lagged range` | −0.00474 | −1.90 |
| ALL | `h / ATR` | −0.00519 | **−2.01** |
| ALL | `h / sqrt(lagged range)` | −0.00512 | −1.87 |
| QUAL | `h` (baseline) | +0.00462 | +1.43 |
| QUAL | `h / lagged range` / `h / ATR` / `h / sqrt(range)` | +0.00194 / +0.00114 / +0.00346 | +0.79 / +0.46 / +1.28 |

**`h / ATR` moves the `t` from −1.79 to −2.01 while the mean IC is essentially unchanged
(−0.00519 against −0.00524).** **That is a variance reduction, not a stronger signal** — normalising
cuts the per-bar dispersion of the IC series rather than raising its mean. Worth having, and it must
not be described as improving the ranking.

On the qualifying set all three normalisations make things **worse**, which is the collision again.

### C — a fixed-weight combination reaches the target this study declared in advance

Each component z-scored **within the bar**, unit weights, nothing fitted.

| universe | score | mean IC | t | vs `zh` |
|---|---|---:|---:|---:|
| ALL | `zh` (baseline) | −0.00524 | −1.79 | — |
| ALL | `zh + zv` | −0.00698 | −2.64 | −0.00174 |
| ALL | `zh + zv + za` | −0.00726 | −2.84 | −0.00202 |
| ALL | `zh + zv + za − zr` | +0.00116 | +0.39 | +0.00640 |
| ALL | **`zh + zv + za + zr`** | **−0.01373** | **−5.07** | **−0.00849** |
| QUAL | `zh` (baseline) | +0.00462 | +1.43 | — |
| QUAL | `zh + zv + za` | −0.00048 | −0.16 | −0.00510 |
| QUAL | **`zh + zv + za + zr`** | **−0.00185** | **−0.60** | −0.00648 |

**`zh + zv + za + zr` reaches −0.01373 on all live names, against the −0.013 this study declared in
advance as the IC needed to reach breakeven gross.** Four things attach to it:

1. **The gain is entirely `zr`.** Flip its sign and the IC goes **positive** (+0.00116). **This is a
   volatility tilt, not a stronger `hist_L`** — a `+zr` term pushes high-range names *out* of an
   ascending short ranking, so the book shorts the **quieter** names. Section D agrees
   independently: `lagged range` against the gap scores **+0.01209, `t` +2.70** — high-range names
   gap **up**, the wrong way for a short.
2. **It does nothing for the construction D279 ran.** On the qualifying set the same combination is
   **−0.00185 at `t` −0.60.**
3. **`zr` alone was never scored, so this record CANNOT say how much of −0.01373 is the volatility
   term by itself.** That is not recoverable from the artefacts and needs its own measurement.
4. **Everything in "what must not be claimed" applies here twice over**, because a volatility tilt
   is precisely the kind of loading the `sigma^2` tax prices.

### D — the gap is the most forecastable thing in this record

| universe | score | mean IC vs **gap** | t |
|---|---|---:|---:|
| ALL | `h` | −0.01531 | −4.71 |
| ALL | yesterday's return | −0.00787 | −2.30 |
| ALL | lagged range | +0.01209 | +2.70 |
| ALL | **`h / lagged range`** | **−0.01625** | **−5.97** |
| QUAL | `h` | −0.01255 | −3.45 |
| QUAL | lagged range | +0.01520 | +2.96 |
| QUAL | `h / lagged range` | −0.00488 | −1.84 |

**`t` = −5.97 is the largest statistic in this record**, it survives part 5's dividend adjustment at
**−5.76**, and it is a forecast of the **overnight gap** rather than of the tradeable day.

---
---

# PARTS 1–3 — how the finding was arrived at, and every step is a negative result

## Part 3 — TWO CORRECTIONS TO MY OWN TESTS, and they are the most important content in this half

`scripts/d280_score_extrapolation.py` · `data/d280_score_extrapolation.json` ·
`data/d280_scoreext.log`

**Both corrections are mine, both were found after parts 1 and 2 had run, and the second one
invalidates part 1's G2 as a test of this construction.**

**Correction 1 — the forecast target was wrong.** Parts 1 and 2 forecast the **raw** close and the
**raw** range. **The strategy never ranks on either.** It ranks on `hist_L`, which is **already a
smoothed quantity built from EMAs.** Extrapolating a smooth series one step is a different and far
better-posed problem, and the derivatives should be taken from the series that actually feeds the
score.

**Correction 2 — the metric was wrong, and this is the serious one.** G2 reported **pooled**
correlation over all names and all bars. **The strategy is purely CROSS-SECTIONAL**: at each bar it
ranks the qualifying names against each other and holds the worst N. **A score can rank well within
each bar and show almost nothing pooled**, because pooling mixes the cross-section with the time
series and with market-wide moves a cross-sectional book is not exposed to. **The right statistic is
the within-bar IC. G2's numbers are withdrawn as a test of this construction, and so is the
"combined IC ~0.018" bound derived from them.**

**Nothing in parts 1 or 2 is retracted as a measurement.** They measure what they measure. **They
were the wrong measurements to have made**, and this record says so where a reader meets them.

### The result — correctly signed over the universe, REVERSED inside the filter

| score | **ALL LIVE NAMES** | | **QUALIFYING SET ONLY** | |
|---|---:|---:|---:|---:|
| | mean IC | t | mean IC | t |
| **`h` — D279's corrected score** | **−0.00524** | **−1.79** | **+0.00462** | **+1.43** |
| `h + v` | −0.00601 | −2.06 | +0.00343 | +1.07 |
| `h + v + a/2` | −0.00615 | −2.10 | +0.00315 | +0.98 |
| `h + v + a/2 + j/6` (full) | −0.00613 | −2.10 | +0.00314 | +0.98 |
| `v` alone | −0.00570 | **−2.29** | −0.00286 | −0.88 |
| `a` alone | −0.00433 | −1.75 | −0.00388 | −1.24 |
| | 2,173 bars | | 2,147 bars | |

**The derivatives pull toward tradeable and do not get there.** Inside the qualifying set only `v`
alone and `a` alone carry the right sign, and the best `t` among them is **−1.24**. Adding
derivatives to `h` makes the qualifying-set IC *less positive* without reaching negative — a
sign-cancellation, not a forecast.

## The structural finding, and it is the one that outlives this record

> **[D256](D256-the-book-on-single-names.md) and [D279](D279-the-concentrated-short-on-dead-inclusive-names.md)
> both filter on `hist_L < 0 & md_L >= 0` and then rank the survivors by `hist_L` again. The filter
> and the ranking are the SAME VARIABLE. The signal is spent by the time the ranking runs, and what
> remains inside the filtered set reverses.**

That is why D279's ranking was worth only **+0.203** gross Sharpe on a book at **−0.432**, and it is
a defect in the **construction**, not in the score. **`hist_L` has cross-sectional information; the
construction had already consumed it before asking it to rank.**

**[D281](D281-the-unfiltered-ranking.md) is the pre-registered test of that construction with the
collision removed** — rank the whole universe, change nothing else. **No result from it is
referenced here.**

## The bar the whole exercise was measured against

From D279's **corrected** decomposition, in GROSS Sharpe at zero fees, zero borrow, zero `rf`:

| | |
|---|---:|
| turnover-matched random selection (`per25`) | **−0.635** |
| `+` the `hist_L` ranking as it stands | **+0.203** |
| `=` where the book actually sits | **−0.432** |
| still needed to reach **breakeven gross** | **+0.432** |
| and only then are costs charged | **+0.206** |

**A replacement score must contribute more than TWICE what the entire existing ranking does merely
to reach zero before costs**, which in IC terms the script declares in advance as roughly **−0.013**
— about **three times** the raw score's measured IC. *That is an order-of-magnitude bar read off the
decomposition linearly, not a derived identity, and it is quoted as such.*

## Part 1 — can a DEMA derivative stack forecast the next bar? No.

`scripts/d280_forecast_precheck.py` · `data/d280_forecast_precheck.json` · `data/d280_precheck.log`

```
DEMA_n(c) = 2*EMA_n(c) - EMA_n(EMA_n(c))        lag-reduced level
v = DEMA(t) - DEMA(t-1)                          velocity
a = v(t) - v(t-1)                                acceleration
j = a(t) - a(t-1)                                jerk
c_hat(t+1) = DEMA(t) + v + a/2 + j/6             Taylor extrapolation
```

Three kill conditions were declared before the numbers were read. **All three fired, and G3 fired in
the opposite direction to the one predicted.**

### G1 — it loses to naive persistence in every single comparison

MAE skill against `c_hat = c(t)`; positive means the model wins. **All 48 cells are negative.**

| n | component | DEMA only | +v | +v+a | +v+a+j |
|---:|---|---:|---:|---:|---:|
| 9 | open | −0.2850 | −0.0994 | −0.0741 | −0.0725 |
| 9 | high | −0.3922 | −0.1776 | −0.1256 | −0.1999 |
| 9 | low | −0.3901 | −0.2022 | −0.1520 | −0.1350 |
| 9 | close | −0.2350 | −0.0969 | **−0.0487** | −0.1006 |
| 21 | open | −0.7524 | −0.5479 | −0.5743 | −0.5849 |
| 21 | high | −0.8097 | −0.6321 | −0.6634 | −0.8832 |
| 21 | low | −1.0030 | −0.7653 | −0.8428 | −0.8022 |
| 21 | close | −0.6485 | −0.5058 | −0.4607 | −0.6347 |
| 34 | open | −1.1467 | −0.9741 | −1.0629 | −1.1176 |
| 34 | high | −1.1339 | −1.0641 | −1.2101 | −1.4293 |
| 34 | low | −1.5492 | −1.3530 | −1.5451 | −1.5232 |
| 34 | close | −0.9778 | −0.9206 | −0.9443 | −1.1269 |

1. **DEMA alone is the worst column everywhere.** A smoother is a lagged estimate of a level, and a
   lagged level is a worse guess at tomorrow's price than today's price is.
2. **Each derivative claws back toward persistence without ever passing it.** At `n=9, close`:
   −0.235 → −0.097 → −0.049 → −0.101. **The derivatives are correcting DEMA's own lag, not
   forecasting** — which is what a Taylor term does to a smoothed series, and the ceiling of that
   correction is the unsmoothed series itself.
3. **Longer `n` is strictly worse, monotonically, in all sixteen component × variant sequences.**
4. **Jerk hurts in 8 of the 12 `+v+a+j` cells.** Declared in advance: each difference of a white
   series multiplies noise variance by `C(2k, k)` — velocity ×2, acceleration ×6, **jerk ×20**.

### G2 — nothing tradeable, and these numbers are withdrawn by part 3

Pooled correlation of the forecast return against the actual next-bar return, ~2.23M name-bars,
against a **|0.02| tradeability floor declared in advance**:

| n | DEMA only / +v / +v+a / +v+a+j |
|---:|---|
| 9 | +0.0006 / −0.0037 / −0.0082 / **−0.0111** |
| 21 | +0.0008 / +0.0017 / +0.0012 / +0.0007 |
| 34 | +0.0011 / +0.0031 / +0.0030 / +0.0028 |
| | **`return(t)` alone, the trivial baseline: −0.0073** |

**All twelve sit inside ±0.011, every one below the declared threshold, and not one beats yesterday's
return.** *Withdrawn as a test of this construction by [part 3](#part-3--two-corrections-to-my-own-tests-and-they-are-the-most-important-content-in-this-half);
correct as pooled correlations and retained as such.*

### G3 — the prediction was WRONG, and it is the wrong kind of good news

**Predicted: the 16 terms collapse below 3 effective inputs**, because [D268](D268-score-independence.md)
found nine price scores carrying **2.87**.

| n | terms | **effective inputs** |
|---:|---:|---:|
| 9 | 16 | **15.76** |
| 21 | 16 | **15.18** |
| 34 | 16 | **13.50** |

**Wrong by a factor of five. The OHLC derivatives are very nearly independent, and the intrabar axis
— range, body, wick asymmetry — is real information a close-to-close series discards.**

**And it buys nothing.** G1 and G2 already established that none of these terms forecasts anything.
**Sixteen near-independent inputs that individually carry no signal are sixteen independent sources
of noise**, and independence makes that worse: there is no redundancy left to average away. **D268's
lesson has a mirror image and this is it** — "these inputs are correlated so they are one input" and
"these inputs are independent so they are many inputs" are both statements about the covariance, and
**neither is a statement about predictive power.**

## Part 2 — the anchored reparameterisation

`scripts/d280_delta_range_precheck.py` · `data/d280_delta_range_precheck.json`

```
open(t+1) := close(t)                  anchored, not forecast
delta     := close(t+1) - open(t+1)    the BODY -- this is the return
high, low  forecast around that anchor
```

### The anchor is NOT free, and it is half the move

| | |
|---|---:|
| median \|gap\| | **0.5263%** |
| mean \|gap\| | **0.9393%** |
| **\|gap\| / \|body\|** | **0.515** |
| corr(gap, body), pooled | −0.0429 |

**The overnight gap is 51.5% of the size of the bar's own body.** Anchoring the open to yesterday's
close does not remove a term from the forecast — **it smuggles in an unforecast term roughly as
large as the one being forecast.** *In hindsight this was part 4's finding arriving early, in
descriptive form and unrecognised: the thing being treated as a nuisance parameter was where the
edge was.*

### Delta — direction fails again, in the coordinates the objection asked for

Nine constructions. **All nine have negative MAE skill against `delta = 0`** (−0.0725 to −0.2730),
and all nine correlations sit between **−0.0110 and −0.0165** — inside the same ±0.02 band, sign
wrong. *"You tested it in the wrong coordinates" is answered: same answer.*

### Range — the correlation is large and the skill is still negative

| n | construction | corr | MAE skill vs persistence |
|---:|---|---:|---:|
| 9 | DEMA / +v / +v+a | 0.593 / 0.710 / **0.863** | −0.120 / −0.061 / **−0.019** |
| 21 | DEMA / +v / +v+a | 0.525 / 0.634 / **0.868** | −0.184 / −0.113 / −0.022 |
| 34 | DEMA / +v / +v+a | 0.493 / 0.583 / **0.829** | −0.270 / −0.190 / −0.115 |

**Correlation reaches +0.87 and MAE skill is negative in all nine cells.** Range *is* predictable —
**and persistence-of-range predicts it better than the DEMA stack does.** **A high correlation beside
a negative skill is the clearest illustration in this record of why a correlation decides nothing:**
both series are dominated by the same slow-moving volatility level, and reproducing that level is
not forecasting.

**A working range forecast would not fix a −0.432 gross Sharpe anyway**, because it carries no
direction. That was written into the script before the numbers landed, so a good range number could
not later be read as a directional edge. **What it could feed is sizing or stop placement** — a
different study, a different hurdle, and it does not exist.

### Wick asymmetry — the declared long shot, and it missed

Five intrabar shape statistics against the next bar's return, 2,219,681 bars: upper wick **+0.0112**,
lower wick **−0.0121**, asymmetry **+0.0148**, body/range **−0.0045**, close-position-in-range
**−0.0121**. **All five inside ±0.015.** The intrabar axis is independent (G3) and it is not
directional.

---

## Multiplicity honesty

**The five parts report 165 statistics, 161 of them distinct**: 48 MAE-skill comparisons and 13
pooled correlations in part 1, 41 in part 2 (18 delta, 18 range, 5 wick), 12 ICs in part 3, 36 in
part 4 and 15 in part 5 — parts 4 and 5 re-reporting several of their predecessors' values.

**Under the null, the largest of 161 independent `|t|` statistics has a median near 2.86 and exceeds
3.0 about a third of the time.** Against that bar:

- **`|t| = 2.29`** (`v` alone) and **`|t| = 2.10`** (`h + v + a/2`) are **inside the noise band and
  are NOT evidence.** They are best-of numbers, quoted only because omitting them would be worse.
- **`|t| = 4.71` (part 4's gap IC), `|t| = 5.07` (the combination) and `|t| = 5.97` (`h / lagged
  range` against the gap) clear a best-of-161 correction comfortably** — the last of them by more
  than three units of `t`. **This is stated explicitly rather than left for a reader to assume**,
  because it is the difference between the part 4 finding and everything else in the record.
- **The only un-searched baseline is `hist_L` alone over all names at `t` = −1.79**, fixed before
  anything was measured, **and it is not significant at conventional levels.**

**Part 4's gap result was not searched for either.** It is one line of a four-way decomposition —
total, gap, intraday — declared in the script before it ran, with the gap leg named in advance as the
thing that could invalidate the backtest. **It is not a survivor of a sweep.**

## Why the `t`-statistic is small on 2.2 million bars

**Because the IC is computed WITHIN each bar and then averaged, so `n` for the `t`-statistic is
2,173 BARS, not 2.2 million observations.** The 1,573 names inside a bar are one cross-section, not
1,573 independent draws — that is the point of measuring cross-sectionally, and it is also why part
1's pooled correlation over 2.23M name-bars reads as far more precise than it is.

Per-bar IC standard deviations run **0.116 to 0.151**, so the standard error on 2,173 bars is about
**0.0029**. **An IC has to reach roughly ±0.006 to be two standard errors from zero on this
fixture**, and the target set by D279's arithmetic is **−0.013** — a little over four.

---

## Ledger

| count | N |
|---|---:|
| **fresh** | **0** |

**Zero, and the reason is not that measurement is privileged.** A multiplicity ledger prices the
looks that could have produced **a reported candidate**. **This record reports no candidate.** No
cell is scored, no book is built, no hurdle is evaluated, no rule is proposed, and nothing here can
enter [BOOK.md](../BOOK.md). There is no estimate for a floor to correct.

**What DOES follow, under [R13](../RULES.md#r13) test 2, and it is the operative half:** any study
whose candidates, scores or fixtures exist *because of* these measurements **inherits all 161
comparisons.** That is not hypothetical — **D281's search space was shaped by part 3, and D282's by
part 4** — and both must carry the count. **A measurement that is free to run is not free to build
on.**

**Disclosed and not carried:** D279's 41 and D256's 21. This record scores none of their cells and
tests none of their hypotheses; it measures a property of the fixture.

---

## What this licenses, and what it forecloses

**Foreclosed:**

1. **The DEMA-derivative forecast, in every form tested.** It loses to naive persistence in **all 48**
   level comparisons, all nine delta comparisons and all nine range comparisons; longer `n` is
   monotonically worse and jerk is noise. **Nothing here needs a pre-registration; there is nothing
   to pre-register.**
2. **Intraday exit overlays on this construction**, by part 4: the edge does not accrue while the
   market is open, so no stop, target or partial exit can reach it.
3. **Taking the position at the open to avoid overnight risk**, for the same reason in reverse.

**Live, and each needs its own pre-registration before a single cell is scored:**

1. **[D281](D281-the-unfiltered-ranking.md)** — pre-registered, runner committed, **result pending
   and not referenced here.**
2. **The overnight construction that part 4 implies**, whose cost arithmetic — ~252 round trips a
   year against D265's `2c` bar — is the whole question. **[D282](D282-the-overnight-only-short.md)
   is pre-registered by another agent to measure it. This record makes no prediction about its outcome.**
3. **The volatility tilt of part 4C.** It needs `zr` scored on its own, a book, a cost model, and the
   `sigma^2` tax charged against it. **It is not a finding about `hist_L` and must not be reported as
   one.**
4. **Range as a SIZING input, never as a signal** — predictable at +0.87, carrying no direction, and
   beaten on MAE by its own persistence baseline.
