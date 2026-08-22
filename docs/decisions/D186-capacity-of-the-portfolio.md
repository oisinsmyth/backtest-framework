# D186 — Capacity: does the portfolio edge exist at size?

**Status:** Committed — **CORRECTED by D187** (H1 now falsified by 0.001, H2 still confirmed, capacity ~$66M not ~$30M)
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

---

# RESULT — appended 2026-08-22, after the sweep. Nothing above this line was edited.

**Status: H1 CONFIRMED, narrowly. H2 CONFIRMED.**

**The portfolio has a capacity of roughly $30M, and the edge is gone above it.**

| Total AUM | Per coin | Strategy | Return | Max DD | Books destroyed | Benchmark | **Edge** |
|---|---|---|---|---|---|---|---|
| $0.1M | $1,613 | +1.240 | +2,624% | 29.4% | 0 | +1.173 | **+0.067** |
| $0.3M | $4,839 | +1.233 | +2,576% | 29.4% | 0 | +1.172 | +0.061 |
| $1M | $16,129 | +1.222 | +2,498% | 29.4% | 0 | +1.171 | +0.051 |
| $3M | $48,387 | +1.207 | +2,395% | 29.5% | 0 | +1.170 | +0.037 |
| $10M | $161,290 | +1.180 | +2,226% | 29.6% | 0 | +1.166 | +0.014 |
| **$30M** | $483,871 | +1.161 | +2,117% | 29.9% | **2** | +1.161 | **−0.000** |
| $100M | $1,612,903 | +1.124 | +1,913% | 30.4% | 2 | +1.151 | **−0.026** |

## H1 — CONFIRMED

Predicted the strategy's Sharpe would fall by more than 0.10 across the sweep. It falls
**+1.240 → +1.124, a loss of 0.116** — clearing the stated bar by 0.016, which is close
enough that it should be quoted with the margin attached.

## H2 — CONFIRMED, and for the predicted reason

Predicted the edge would reach zero at or below $100M. **It reaches zero at $30M** and goes
negative at $100M.

The prediction was made with low confidence and an explicit expectation of failing D185's
way — where a cost asymmetry was correctly identified and produced no consequence, because
Sharpe damage is `cost ÷ volatility` and the benchmark is 3.4× more volatile. **That did not
happen here, and the reason is the mechanism the pre-registration named:**

| | Sharpe lost, $100k → $100M |
|---|---|
| **Strategy** | **0.116** |
| Benchmark | 0.022 |

**The strategy loses 5.3× more Sharpe to impact than the benchmark does**, despite the
benchmark turning over 2.7× more (D185). Volatility normalisation did not rescue it,
because the strategy's impact is **concentrated** in the thin coins it actually trades,
while the benchmark spreads its turnover across all 62 including the liquid ones.
Concentration is not divided away by volatility.

That is the first time in this project a mechanism-first prediction has been right about
both the mechanism and its consequence.

## Two books destroyed, and by impact alone

At $30M and above, `LUNA1-USD` and `LUNC-USD` **long** books reach zero NAV and are
truncated. **No long book dies at zero impact** — D183's only deaths were on the short side
— so impact is doing this by itself: the cost of entering those coins at $484k exceeds what
the position can bear.

**This is also the model's own edge, and it should be read that way.** A square-root impact
charge large enough to destroy an account is outside the range D66's functional form was
fitted for — it models a cost, not a bankruptcy. The honest reading is that **the trade does
not exist at this size**, which is the same answer arrived at less gracefully.

The published rows are not contaminated by it: NAV goes negative at bar 874, several hundred
bars before the raw equity curve goes NaN at 1,326, so the account-death truncation from
D183 caught it cleanly. **That was luck, not design** — `if a <= 0.0` compares False against
NaN, so the guard would have let a non-finite NAV straight through had the ordering been
reversed. It now tests `not (a > 0.0) or not isfinite(b)`.

## The deflated Sharpe — D183's second debt, paid and worth less than it looks

At $100k the portfolio scores **+1.240** annualised. Deflated against the long book's own
published pool — **30 trials**, V[SRn] = 4.99e-05 daily, read from
`breakout_study_summary.json` rather than asserted — **DSR = 0.9996**.

**That number should not be quoted on its own, and here is why.**

**It deflates against a trial pool, not against a benchmark.** DSR asks whether a Sharpe is
plausibly the best of 30 zero-skill attempts. It does not ask whether the Sharpe beat buy
and hold. At $30M the strategy scores +1.161 and the equal-weight universe scores +1.161 —
**identical** — and the DSR of the former would still be high. A deflated Sharpe near 1.0 on
a book that merely matches a passive basket is measuring crypto beta surviving a
multiplicity correction, not skill surviving one.

**The pool is an approximation.** The 30 trials are per-symbol BTC/ETH variants; the thing
being deflated is a 62-coin portfolio. Using that pool's variance as the noise floor is the
closest honest choice available — the search that selected the configuration is the right
pool — but it is not a pool of portfolios.

**And the return distribution is extreme:** skew **+4.76**, kurtosis **106.7**. The DSR
formula corrects for both, which is why it is the right tool, but a Sharpe estimated from
returns that shaped is itself unstable.

## What this settles

**The capacity is ~$30M of total AUM** — about $484k per coin across 62 coins. Below that
the edge is real and shrinking; at it, the edge is zero; above it, negative.

**All three of D183's debts are now paid.** The rebalancing cost (D185, immaterial), the
deflated Sharpe (high, and less meaningful than it looks), and capacity (~$30M). The
remaining debt is the one D183 named third: an out-of-sample cross-section, on a universe
this one does not contain.

**And the result is smaller than it was.** D183 reported +1.277 with no impact at all. At a
realistic $10M the strategy scores +1.180 against a benchmark at +1.166 — **an edge of
+0.014**. The honest summary of this project's one working idea is now:

> An equal-weight crypto basket with a breakout overlay, returning roughly what the basket
> returns at a third of its drawdown, with an edge over the basket that is small at $1M,
> marginal at $10M, and gone at $30M.

## What it does not settle

**Impact is calibrated full-sample and ADV is a whole-period mean** — D66's caveat carried
forward. A coin's 2016 and 2025 volumes differ by orders of magnitude, and one average
across both flatters the thin years, which is where capacity binds.

**Parameter selection is done on pre-impact economics**, deliberately: the sweep varies size
and nothing else, and letting fitted parameters move with AUM would make it measure two
things at once. The mismatch is real and unmeasured.

**A square-root impact model is still not a liquidity model.** It says what a fill costs, not
whether a counterparty exists. **The $30M figure is therefore an upper bound on capacity,
not an estimate of it.**

---

# CORRECTION — appended 2026-08-22. Nothing above this line was edited.

**The capacity number above was computed with ADV in the wrong units. It is corrected from
~$30M to ~$66M, and the "two books destroyed by impact" finding is withdrawn.**

D187 records the bug in full: crypto fixtures report quote-currency notional, the
calibration treated it as shares, and `SqrtImpact` divides a quantity by ADV — so every
charge was off by √price. BTC's impact was understated ~148×; `LUNC-USD`'s was overstated
~40×.

| Total AUM | Strategy | Benchmark | Edge as published | **Edge corrected** | Books destroyed |
|---|---|---|---|---|---|
| $0.1M | +1.248 | +1.173 | +0.067 | **+0.075** | 0 |
| $0.3M | +1.246 | +1.173 | +0.061 | +0.073 | 0 |
| $1M | +1.241 | +1.172 | +0.051 | **+0.068** | 0 |
| $3M | +1.233 | +1.172 | +0.037 | +0.061 | 0 |
| $10M | +1.218 | +1.170 | +0.014 | **+0.047** | 0 |
| $30M | +1.194 | +1.168 | −0.000 | **+0.026** | **0** |
| $100M | +1.149 | +1.163 | −0.026 | **−0.014** | 0 |

**Capacity ≈ $66M** (log-interpolated between the bracketing levels), about $1.06M per coin.

## What survives, what does not

**H1 still holds, more narrowly.** The strategy's Sharpe falls +1.248 → +1.149, a loss of
**0.099** against a predicted >0.10 — so it now *fails* the stated bar by 0.001. Called as
written: **H1 is FALSIFIED on the corrected numbers.** It is as close to the line as a
prediction can land, and reporting it as confirmed because it was confirmed yesterday would
be the worst available option.

**H2 still holds.** The edge reaches zero at ~$66M, below the predicted $100M.

**The concentration mechanism still holds, and is stronger.** Strategy loses 0.099 Sharpe to
impact against the benchmark's 0.010 — a **10× asymmetry**, up from 5.3×. The reasoning that
the strategy's impact concentrates in the coins it actually trades, while the benchmark
spreads across all 62, survives the correction that changed everything else.

**"Two long books destroyed by impact" is withdrawn.** `LUNA1-USD` and `LUNC-USD` are
sub-cent coins whose impact was overstated ~40×. With the units right, **no book is
destroyed at any size tested**, and the paragraph reading that as "the trade does not exist
at this size" was reading an artifact.

**The deflated Sharpe is unchanged at 0.9996**, and everything said about why it is worth
less than it looks stands — it deflates against a trial pool, not a benchmark.

## The honest summary, restated

> An equal-weight crypto basket with a breakout overlay, at roughly a third of the basket's
> drawdown, with an edge of +0.075 at $100k, +0.047 at $10M, and gone by ~$66M.

Better than the number this record first published, on every row — and arrived at by fixing
a bug that made it look worse, which is the only reason to trust the direction.
