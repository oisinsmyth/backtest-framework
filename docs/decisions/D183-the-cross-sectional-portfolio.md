# D183 — A cross-sectional long/short portfolio: the diversification this project never had

**Status:** Committed (H1 confirmed narrowly, H2 confirmed strongly)
**Date:** 2026-08-21
**Category:** Analytics
**Source:** D182 answered the per-symbol question and named this one as the thing it did not answer

> Written and committed **before** the study runs, as D173, D178, D180 and D182 were. The
> predictions below are falsifiable and dated by git. A result section will be appended and
> nothing above it edited.

## The question, and why it is genuinely open

D182 combined each coin's own long and short books and found the pairing costs 118
percentage points of median return to buy 4.7 of drawdown. It answered *"does pairing one
coin's two books help?"* and it explicitly did not answer the question underneath.

**Every result in this project is a single-instrument book**, or a cross-section of
single-instrument books averaged after the fact. D174, D180 and D182 all report win rates
and mean deltas *across* 62 coins — but each row is one coin traded alone.

**Averaging Sharpes is not the same as earning the Sharpe of an average.** A book with a
median single-coin Sharpe of 0.443 and near-independent errors across 62 coins should, on
the arithmetic alone, produce a portfolio Sharpe far above 0.443. That arithmetic has never
been run here, and it is the one form of diversification not yet tested: **between coins**,
operating on the return distribution itself, rather than between books, which D182 showed
only rearranges a losing book's timing.

## What is built

`scripts/run_portfolio_universe.py`. Both published baselines, unchanged (D141) — the long
arm is `breakout_universe.baseline_variant()` itself.

On each date the long portfolio earns the **equal-weighted mean** of every long book with a
position open, likewise the short; the two portfolio series are combined at D181's
expanding inverse-vol weights. A coin contributes only from its own out-of-sample start, so
nothing is held before its walk-forward would have admitted it.

Equal weight, not inverse-vol across coins: a second allocation scheme is a second free
parameter, and this study has no multiplicity budget.

**One modelling choice that is stricter than the rest of the project.** Two short books
drive NAV past −100% (`LUNA1-USD` −154%, `LUNC-USD` −175%), which the engine permits
because it models no margin call (D175). Once NAV is negative, `b/a − 1` is not a return —
the denominator's sign has flipped — and averaging it would propagate nonsense across every
other coin. A book that reaches zero is therefore **dead from that bar**. That is more
realistic than letting it trade a negative account, and it is still not a liquidation model.

## What this deliberately is not

A **return-aggregation** portfolio, not a portfolio backtest. No shared capital constraint,
no cross-sectional position limit, and — the one that matters most — **no cost for
rebalancing between coins.** Each coin's own trading costs are charged inside its book;
moving capital between coins to hold equal weights is free here and is free nowhere else.
Daily-rebalanced equal weight is the most turnover-hungry construction available, so the
un-modelled cost is at its maximum. Every number this study produces is optimistic by an
amount it does not measure, and that has to be attached to any figure quoted from it.

## The predictions

**H1 — the LONG portfolio's Sharpe exceeds the median single-coin long Sharpe (+0.443) by
a wide margin: above +0.90, i.e. more than double.** Predicted **TRUE**.

This is the one positive prediction I am willing to make in this project, and it rests on
arithmetic rather than on a market mechanism. D182 measured long/short correlation at
essentially zero, but that is *within* a coin; across coins these books are driven by a
common crypto beta and will be far from independent, so the diversification benefit will be
well short of √62.

Against it: breadth is thin early, when only the oldest coins have cleared their
walk-forward, and a one-coin portfolio is a coin. If early breadth dominates the sample,
H1 could fail for a reason that has nothing to do with diversification.

**H2 — adding the short portfolio still costs Sharpe.** Predicted **TRUE**.

D182's finding at portfolio level. The short book loses on 57 of 62 coins; aggregation
changes how its losses are distributed in time, not that they are losses.

There is a real mechanism against this and it should be stated: aggregating across 62 coins
raises the short arm's in-the-market share far above any single coin's ~15%, so the short
portfolio is a *continuously* held book in a way no single short book is. If the short
book's problem were purely that it is too intermittent to hedge with, aggregation would fix
it. D182 says the problem is expectancy, not intermittency, and expectancy does not
aggregate away.

**What would falsify each:** H1, a long portfolio Sharpe at or below +0.90. H2, a combined
portfolio Sharpe above the long portfolio's.

**Track record, stated honestly:** my mechanism-first predictions have been falsified four
times (D173 H1, D178 H2, D180 all three) and confirmed twice (D182 H1 and H2). The two
confirmed ones both predicted a *cost*. **H1 predicts a benefit, which is the category I
have been consistently wrong in**, and I am making it anyway because the reasoning is
arithmetic rather than behavioural. If it fails, the interesting question will be whether
breadth or cross-coin correlation is responsible.

## Multiplicity

**None added.** Both baselines already exist and are already in their pools. Own registry
`data/portfolio_universe_registry.sqlite` under `portfolio-universe-*`, as D174, D180 and
D182 did. No DSR in either published report moves.

## What a positive result would and would not mean

If H1 holds it would be the **first thing in this project that looks like an edge rather
than an artifact** — and it would immediately owe three things it does not yet have: the
rebalancing cost it currently ignores, a deflated Sharpe against the pool of configurations
that produced the underlying baseline, and its own out-of-sample test on instruments this
universe does not contain. A portfolio Sharpe computed on a crypto bull sample with free
rebalancing is not a result; it is a number that has earned the right to be tested.

---

# RESULT — appended 2026-08-21, after the run. Nothing above this line was edited.

**Status: H1 CONFIRMED — narrowly, once the stated robustness check is applied. H2
CONFIRMED, and far more strongly than at per-symbol level.**

62 symbols, 3,762 dates, 2015-09-11 to 2025-12-28.

## The headline

| | Sharpe | Total return | Max DD | Median SINGLE coin |
|---|---|---|---|---|
| **long portfolio** | **+1.278** | **+2,912.7%** | **28.8%** | +0.437 |
| short portfolio | −0.588 | −53.6% | 61.0% | −0.450 |
| combined portfolio | +0.108 | +53.6% | 22.8% | — |

**Diversifying across coins is the first thing in this project that has worked.** The long
book goes from a median single-coin Sharpe of **+0.437** to a portfolio Sharpe of
**+1.278**, while max drawdown falls from a 48.1% single-coin mean to **28.8%**. Nothing
else tested here — four entry filters, six stops, E1, the swing stop, the within-coin
ensemble — has moved a number like that.

It is also the least surprising result in the project, because it is arithmetic. 62
partially-independent books averaged together have less variance than one of them. The
finding is not that the effect exists; it is that it is large enough to matter, and that
it is the only lever tried so far that operates on the return **distribution** rather than
on a single book's timing.

## H1 — CONFIRMED, and the margin matters

Predicted: long portfolio Sharpe above **+0.90**. Observed **+1.278** on the full sample.

The pre-registration named the way this could hold for the wrong reason — thin early
breadth, where a "portfolio" is one or two coins in the 2015–2017 bull run. Scoring only
dates with at least five coins live:

| Coins live | Dates kept | Long portfolio Sharpe | Combined Sharpe |
|---|---|---|---|
| ≥ 1 | 3,510 | **+1.275** | +0.102 |
| ≥ 5 | 2,712 | **+0.927** | −0.029 |
| ≥ 10 / 20 / 30 | 2,708 | **+0.928** | −0.014 |

**A third of the headline Sharpe was the thin early sample.** +1.278 becomes **+0.928**
once the near-single-coin period is dropped — which clears the pre-registered bar of +0.90
by 0.028. H1 holds as stated, and it holds *narrowly*, and quoting +1.278 without this
table would be the more flattering half of a two-number result.

The rows past 5 are identical because the universe fills in quickly: essentially no period
has between five and thirty coins live.

**+0.928 is still more than double the median single coin's +0.437**, so the diversification
claim survives its own robustness check even though the headline does not.

## H2 — CONFIRMED, and much worse than per symbol

Adding the short portfolio costs **−1.170 Sharpe** (+1.278 → +0.108) and takes total return
from **+2,913% to +54%**. Drawdown improves 28.8% → 22.8%, six points.

At per-symbol level (D182) combining cost 0.382 Sharpe. At portfolio level it costs three
times that, and on the breadth-conditioned sample the combined book is **negative**
(−0.014 to −0.029) — worse than holding nothing.

The mechanism against H2 that the pre-registration raised — that aggregation makes the
short arm continuously held, so it might hedge properly once it is no longer intermittent —
is refuted. The short portfolio *is* continuously held here, and it subtracts more, not
less.

## The D181 weighting flaw gets WORSE at portfolio level, not better

I wrote the opposite into the report before running it: that pooling 62 coins would raise
the short arm's in-the-market share and so make the flaw bite less. That was wrong, and the
run says so.

**Mean weight on the long portfolio: 0.302.** The losing leg carries **70%** of the risk
budget, against 61% on BTC alone (D181).

The reason is worth stating because it generalises past this study. Pooling 62 coins
**diversifies the short arm's own returns**, which lowers its measured volatility, which
inverse-vol rewards with **more** weight. **The construction pays a book for being
diversified and for being absent, and neither is a reason to give it capital.** Any
inverse-vol allocation across strategies of differing breadth has this problem.

That claim is now derived in the report rather than asserted, because asserting it is how I
got it backwards — the single most repeated defect in this project.

## Two errors this run caught in its own reporting

**The weight paragraph, above** — written before the run, wrong, now computed.

**The breadth table was mislabelled.** It counts coins **live in the sample** — whose
walk-forward has started and which have not wiped out — and I had labelled it "books with a
position open". A flat book still contributes a 0.0 return and is counted. The label is
fixed, and the gap it exposed is now stated rather than papered over: **position-level
breadth is not measured in this study.** The long book is in the market roughly half the
time and the short book far less, so the number of positions actually held is materially
below these counts. That bears directly on whether daily equal-weighting across coins is a
realistic construction, and this study does not answer it.

## What must be attached to the +0.928

**It is not a strategy result yet.** Three things are owed before it could be:

1. **The rebalancing cost this study does not charge.** Each coin's own trading costs are
   inside its book; moving capital between coins to hold equal weights is free here.
   Daily-rebalanced equal weight is the most turnover-hungry construction available, so the
   un-modelled cost is at its maximum. This is the single largest threat to the result.
2. **A deflated Sharpe.** The underlying baseline is the survivor of a 30-configuration
   search on the long book. A portfolio built from it inherits that multiplicity and has
   not been deflated against it.
3. **Its own out-of-sample test.** This is one crypto cross-section over one bull-dominated
   decade. The lesson of D180 is precisely that a number measured on a favourable sample is
   not a number about the world.

**And two of the account-destroying books were truncated**, which is stricter than the
per-symbol studies but still not a liquidation model (D175). `LUNA1-USD` and `LUNC-USD`
short both died 2022-05-14.

## What this changes

**The project's negative streak has an explanation, not just a tally.** Every rule tested
here tried to improve a single book's decisions, and every one failed out of sample. The
one intervention that operates on the return distribution instead — holding many books at
once — produced a larger, more robust improvement than all of them combined, and it needed
no new parameters, no search, and no multiplicity.

**The short book should stop being carried.** It has now failed as a standalone book
(D172), as a per-symbol hedge (D182), and as a portfolio hedge here, where it costs 1.17
Sharpe and takes 2,859 percentage points of return with it. There is no configuration of
this project's evidence in which it earns its place.

**The next test is the rebalancing cost**, not another rule. A +0.928 that survives realistic
turnover costs is worth deflating and testing out of sample; one that does not is a
measurement artifact of free trading, and no amount of further rule search would matter.

---

# BENCHMARKS — appended 2026-08-21. Nothing above this line was edited.

The result section above compares the portfolio only against the median single coin, which
answers "does diversifying help?" and not "is the outcome worth having?". Benchmarks,
computed over the matched spans.

## The conservative span (≥5 coins live, 2018-07-20 →, 2,712 bars)

| | Sharpe | Total return | Max DD |
|---|---|---|---|
| **LONG portfolio (strategy)** | **+0.927** | +316.1% | **22.9%** |
| BTC buy & hold | +0.786 | **+1,086.9%** | 76.6% |
| Equal-weight universe, daily rebalanced | +0.733 | +813.3% | 81.4% |
| Equal-weight universe, true buy & hold (38 coins) | +0.651 | +437.8% | 87.7% |
| Equal-weight universe, monthly rebalanced | +0.562 | +235.7% | 85.9% |

## The full span (2016-05-20 →, 3,510 bars)

| | Sharpe | Total return | Max DD |
|---|---|---|---|
| **LONG portfolio (strategy)** | **+1.275** | +2,912.7% | **28.8%** |
| Equal-weight universe, daily rebalanced | +1.191 | +70,139.2% | 88.7% |
| BTC buy & hold | +1.095 | **+19,921.2%** | 83.4% |
| Equal-weight universe, monthly rebalanced | +0.978 | +11,948.0% | 89.5% |
| Equal-weight universe, true buy & hold (2 coins) | +0.975 | +10,936.2% | 90.1% |

All equal-weight rows have the two unrecorded corporate actions neutralised — see D184,
without which the daily-rebalanced row reads +102,682,123%.

## The comparison that actually matters

**BTC is the wrong benchmark for this strategy and the equal-weight universe is the right
one**, because the strategy is itself an equal-weight basket of 62 coins rebalanced daily.
Comparing it to BTC compares two different bets; comparing it to the equal-weight universe
isolates what the breakout rule contributes.

And the rebalancing frequency has to match, because **daily rebalancing is worth a lot on
its own**: the equal-weight universe scores +1.191 daily-rebalanced against +0.978
monthly, a free +0.21 Sharpe from volatility harvesting alone, charged nothing.

Like for like — daily-rebalanced strategy against daily-rebalanced benchmark:

| Span | Strategy | Benchmark | **Edge** |
|---|---|---|---|
| Full | +1.275 | +1.191 | **+0.084** |
| ≥5 coins live | +0.927 | +0.733 | **+0.194** |

**The breakout rule's contribution is +0.08 to +0.19 Sharpe, not the +0.49 the naive
single-coin comparison suggested.** Most of the portfolio's Sharpe is diversification and
daily rebalancing, both of which are available without any strategy at all.

## What survives

**The drawdown result is the real one, and it is large.** 22.9% against 76.6–87.7% for every
benchmark — a third to a quarter. That is not a marginal effect and it is not explained by
diversification alone: the equal-weight universe is equally diversified and draws down 81%.
Being flat about half the time is what does it.

**The return result is unfavourable.** +316% against BTC's +1,087% on the conservative span,
and +2,913% against +19,921% over the full span — 15% of buy-and-hold's return. Against the
equal-weight universe it sits between monthly (+236%) and true buy-and-hold (+438%).

**So this is a risk-reduction result, not an alpha result** — the same shape the long study
and D179 landed on. The correct summary is: *roughly the return of an equal-weight crypto
basket, at a quarter of its drawdown, with a small Sharpe edge over the same basket
rebalanced identically.* Whether that small edge survives the rebalancing cost this study
does not charge is unknown, and it is now the whole question.

**The +0.084 on the full span is inside the range a turnover charge could erase.** That
makes the un-modelled rebalancing cost not a caveat on this result but the test of it.
