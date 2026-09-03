# D297 — a trailing stop on the spread itself

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**The holdout is not read. Holdout reads spent: 0.**

---

## What this is, and what it is not

**Not a pairs book.** Each bar the base book ranks ~805 names by `hist_L`, takes
the 25 lowest and 25 highest, filters each to 19 by the partners' mean rank, and
earns `mean(long) − mean(short)`. Long #3 is matched to nothing. **The spread is
an aggregate**, so a trailing stop on it belongs at the BOOK level, not on a
position.

**The base book is unchanged** — D295's B0 control exactly: f = 0.75, N = 25,
19 slots per leg, 5-bar hold. Nothing about selection, sizing or holding is
re-searched. **This study adds one thing: an exposure overlay.**

**AND IT CANNOT CREATE EDGE.** Scaling exposure scales return and vol together.
The only way an overlay wins is by scaling *down* before bad bars and *up*
before good ones — i.e. the drawdown state must carry timing information. That
is the entire hypothesis and Q3 states it as a falsifiable claim.

## The overlay

```
shadow    the UNMANAGED book's cumulative spread P&L, tracked continuously
peak(t)   its running maximum through t-1
dd(t)     peak(t) - shadow(t-1),  in units of the book's trailing 63-bar vol
scale(t)  1.0  if dd(t) < X
          s    otherwise
book(t)   scale(t) * base_return(t)
```

**The shadow book is why this is well posed.** If the overlay tracked its OWN
realised equity, going flat would freeze the curve, no new peak could ever
arrive, and it would stay flat forever. The shadow keeps accruing whether or not
capital is deployed, so re-risking has something to key on.

**`dd(t)` uses the shadow through t−1.** A drawdown measured to bar `t`'s own
close and acted on in bar `t` is look-ahead, and the runner will assert it.

| | |
|---|---|
| **X** — giveback that de-risks | **1.0 / 1.5 / 2.0 / 3.0** × trailing 63-bar vol |
| **s** — de-risked exposure | **0.0** (flat) and **0.5** (half) |

**8 cells + the un-overlaid control.** Vol units rather than basis points so the
threshold is scale-free and does not silently become a different rule in a
different volatility regime.

## The statistic is SHARPE, not the mean

A paired difference in mean return is the wrong test here: an overlay that is
out of the market 20% of the time earns ~20% less by construction and would
"lose" a mean test while improving every risk-adjusted measure. So:

```
statistic:  Sharpe of the overlaid book
reported:   mean, vol, maxDD, exposure, and the paired mean difference
```

## The null: same amount of de-risking, at unrelated times

For each cell, take its realised on/off schedule and build controls with **the
same number of off-episodes and the same episode-length distribution**, placed
at random. Rate- and persistence-matched, exactly as D295's was, and for the
same reason: matched-count is not matched-turnover (D279), and a control that
re-draws every bar where the treatment persists is what voided D291's veto arm.

**The question the null asks:** does de-risking *when the book is in drawdown*
beat de-risking for the same amount of time at times unrelated to it? **1000
draws** — the overlay series is cheap.

## Pass condition

**Sharpe above the cell's own null at p < 0.05.** One condition, because this is
a screen on unspent data and nothing is promoted. Per D295's amendment, a
family-wise floor is a promotion instrument and does not belong here; the
**false-positive arithmetic is reported instead** — the count at p < 0.05
against expectation, tested against the null's own correlated structure, and
Benjamini-Hochberg.

## Cost is REPORTED and does not gate

**But it must be reported, because this overlay is expensive in a way the base
book is not.** Going flat liquidates 38 positions and re-establishing them buys
them back: **one full round trip on the whole book per off-and-on cycle**,
against a measured round trip of 105–261 bp. At `s = 0.5` it is half that.
Reported per cell: transitions per year, notional turned over, and the implied
cost per bar. **It is a stage-3 question and this record will not treat it as a
stage-2 gate.**

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | **no cell beats its own null on Sharpe.** Stage 2's measured uplift here is ~1.0× across four studies | **AGAINST** | moderate-high |
| **Q2** | every cell cuts vol and maxDD | for | **high** — mechanical, and a check on the harness rather than a finding |
| **Q3** | **realised return falls in proportion to exposure**, so return-per-unit-exposure is unchanged and the drawdown state carries NO timing information | **AGAINST** | moderate-high |
| **Q4** | **transition cost exceeds any Sharpe gain**, at both `s` | **AGAINST** | moderate |
| **Q5** | `s = 0.5` beats `s = 0.0` — halving is less whipsaw-prone than flattening | for | moderate |
| **Q6** | **the tightest threshold (X = 1.0) is the worst**, because a drawdown-triggered rule on a mean-reverting curve sells the bottom, and a tighter trigger sells more bottoms | for | moderate |

**Q3 is load-bearing.** It is the hypothesis stated so it can fail: if
return-per-unit-exposure is flat across every cell, the overlay is a volatility
scaler and nothing more, whatever its Sharpe does.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: **8 cells** on one fixed base book, each against a rate- and
persistence-matched null of 1000 draws. Every upstream selection is inherited.

## Stop

**If nothing beats its own null, book-level exposure management is closed for
this candidate** — no third variant, no re-cut of X, no other trigger.

**A negative does not close:** the per-position market-referenced stop (D297's
premise measured it at 6.1% of variance and 12% of positions), the deeper-bench
exit question D295 could not pose, or the cost estimate — which remains the
binding constraint on everything.

## Not attempted here

Any change to the base book. Pairing — rank-matching would leave the aggregate
return identical while making each pair's spread mostly noise, and sector- or
beta-matched pairing invents structure the signal does not have. Re-risking on
anything other than the shadow drawdown.

---

## AMENDMENT — before the runner produced any result: the threshold grid was mis-scaled

**Declared:** X ∈ {1.0, 1.5, 2.0, 3.0} × trailing 63-bar vol.
**Measured on the built runner, from the EXPOSURE PROFILE ONLY:**

| X (daily vols) | 1.0 | 2.0 | 3.0 | 5 | **8** | **12** | **20** | **30** | 40 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| exposure | 17.5% | 27.4% | 35.2% | 45.8% | **59.6%** | **71.6%** | **80.6%** | **95.5%** | 100% |

**A drawdown of one DAILY vol is nothing.** This book's own drawdown
distribution, in the same units, is **p50 4.6, p90 19.8, max 40.1**. So every
declared threshold leaves the book de-risked most of the time — X = 1.0 is on
for **17.5%** of bars — and all four cells would have described a mostly-flat
book rather than a trailing stop. The grid asked a degenerate question.

**Re-declared: X ∈ {8, 12, 20, 30}**, spanning **59.6% → 95.5%** exposure. `s`,
the statistic, the null, the pass condition and every prediction are unchanged.

**Disclosure, and it matters.** The new grid was chosen after seeing this book's
exposure profile, so it is data-dependent and that is a look. **It cannot bias
the test, for a specific reason:** the null rotates each cell's own on/off
series, so it holds exposure EXACTLY equal to the treatment's. A threshold
chosen to produce a given exposure therefore changes which question is asked,
never the fairness of the answer. No return, Sharpe or null was computed at any
threshold before this amendment.
