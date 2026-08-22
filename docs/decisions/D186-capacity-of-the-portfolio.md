# D186 — Capacity: does the portfolio edge exist at size?

**Status:** PRE-REGISTERED — implementation committed, **sweep not yet run**
**Date:** 2026-08-22
**Category:** Analytics
**Source:** D183 and D185 both closed by naming this as the next question

> Written and committed **before** the sweep runs, as D173, D178, D180, D182, D183 and D185
> were. A result section will be appended and nothing above it edited.

## The question

D183 found a cross-sectional long portfolio at **+1.277** Sharpe against **+1.196** for a
daily-rebalanced equal-weight universe — a like-for-like edge of **+0.081**. D185 charged
the between-coin rebalancing cost and the edge barely moved, to **+0.078**.

Both closed on the same sentence: *a turnover charge is not a liquidity model*. **Every
number in this project so far assumes a fill at the quoted price regardless of size**, on
62 small-cap alts rebalanced daily. This is the debt most likely to zero the result.

## What is charged

Square-root market impact (D66), already built for the equities pairs study and reused
unchanged:

```
impact_fraction = 1.0 × σ_daily × √(|Q| / ADV)
```

so total impact dollars scale as Q^1.5. σ and ADV are calibrated per coin from the
snapshot's own bars and volumes, and a coin with missing or zero volume **raises** rather
than defaulting (D48).

**The coefficient is 1.0 and is not swept** — D66's Y ≈ 1 convention, the value
`pairs_study.py:82` already uses. Tuning it would be a search for whichever capacity number
flattered the book.

Total AUM sweeps **$100k → $100M**, per-coin slice `AUM / 62`. The D185 rebalancing charge
is held fixed at 40 bp throughout, so the sweep varies exactly one thing: **size**.

**The benchmark is charged impact too.** A passive equal-weight basket also trades to hold
its weights, and it holds every coin every day. Charging only the strategy would rig the
comparison — D185's principle, applied to impact.

## The wiring, and the rule it had to respect

`CostTier` gains `impact_coefficient`, defaulting to **0.0**, and the `sqrt_impact` brick is
emitted from `cost_stack_config()` **only when non-zero** — the D166 rule, fifth
application. "Off" means the brick is **absent**, not present with coefficient zero: a
zero-valued brick would cost nothing and still change every config hash in both studies,
orphaning every registered trial.

`CostTier.build()` now takes an optional `StackDataContext` and **raises** if impact is on
without one. A silently zero-cost impact brick is worse than no impact brick, and this
project has found that failure mode often enough to guard it explicitly.

## Disclosure before the predictions

While smoke-testing the wiring I computed the impact fraction across the cross-section, so
the predictions below are **informed by the cost table but not by any Sharpe**:

| Total AUM | Median coin | p90 | Worst coin |
|---|---|---|---|
| $0.1M | 1.8 bp | 11 bp | 279 bp |
| $1M | 5.6 bp | 36 bp | 883 bp |
| $10M | 17.6 bp | 114 bp | 2,793 bp |
| $100M | 55.6 bp | 361 bp | **8,831 bp** |

It scales as √Q exactly, as it must. Saying this plainly is better than a pre-registration
that implies more ignorance than I have.

## The predictions

**H1 — the strategy's own Sharpe falls by more than 0.10 between $100k and $100M.**
Predicted **TRUE**.

Each coin's book trades roughly 4–5 times a year one-way at close to a full slice. At $100M
that is ~4.8 × 56 bp ≈ **2.7% a year** on the median coin, and far worse on the thin ones,
against a book with ~25% annual volatility.

**H2 — the edge over the equal-weight universe reaches zero at or below $100M.** Predicted
**TRUE**, with low confidence, and I expect to be wrong in a specific way.

**D185 taught me exactly how this reasoning fails.** There I predicted the cost asymmetry
would move the edge, correctly identified a 2.7× turnover asymmetry, and was wrong because
Sharpe damage is `cost ÷ volatility` and the benchmark is **3.4× more volatile**. The same
denominator is present here. If H2 fails it will almost certainly fail that way: both books
pay more impact with size, the benchmark pays more of it, and its volatility absorbs the
difference.

I am predicting TRUE anyway because there is a mechanism D185 did not have — **the
strategy's impact is concentrated in the thin coins it actually trades**, where the worst
fraction reaches 88%, while the benchmark spreads its turnover across all 62 including the
liquid ones. Concentration is not divided away by volatility.

**What would falsify each:** H1, a Sharpe drop of 0.10 or less across the sweep. H2, a
positive edge at every level tested.

**Track record:** mechanism-first predictions falsified five times, confirmed four. Every
confirmation predicted a cost; every falsification either predicted a benefit or, twice
now, got the normalisation wrong.

## What this cannot settle

**Impact is calibrated full-sample** — D66's stated caveat carried forward verbatim. σ and
ADV come from the whole series: a mild look-ahead in cost parameters, never in the signal.
Per-window calibration remains deferred.

**ADV is a whole-period mean.** A coin's volume in 2016 and 2025 differ by orders of
magnitude, and one average across both flatters the thin years.

**And a square-root impact model is not a liquidity model.** It says what a fill costs, not
whether a counterparty exists. On a delisted coin the honest answer is that the trade does
not happen at any price, and no coefficient expresses that. **The capacity number this
produces is therefore an upper bound on capacity, not an estimate of it.**
