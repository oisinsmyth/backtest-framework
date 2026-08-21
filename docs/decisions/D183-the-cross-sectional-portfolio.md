# D183 — A cross-sectional long/short portfolio: the diversification this project never had

**Status:** PRE-REGISTERED — implementation committed, **study not yet run**
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
