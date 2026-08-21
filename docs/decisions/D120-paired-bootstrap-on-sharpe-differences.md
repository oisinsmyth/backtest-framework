# D120 — Sharpe differences get a paired block bootstrap, and the risk-adjusted claim is retracted

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout study review session

## Decision

`sharpe_difference_bootstrap` computes a **paired** block bootstrap of
(strategy Sharpe − benchmark Sharpe): the same resampled bar indices are applied to both
return series, in contiguous 20-bar blocks, seeded (D34). It reports the observed
difference, a 90% interval, and P(difference > 0).

Every Sharpe comparison in `BREAKOUT_RESULTS.md` now carries that interval, and the
report's headline claim is corrected: the strategy's Sharpe advantage over buy-and-hold is
**not supported at this sample size**.

## Rationale

The first version of the report concluded that "the entire case for this strategy is a
risk-adjusted one", resting on annualised Sharpe 1.20 vs 1.164 (BTC) and 0.775 vs 0.665
(ETH). Ten years of daily data buys a standard error of roughly ±0.4 on an annualised
Sharpe. The observed gaps are a tenth and a quarter of one standard error. Stating them as
the study's case was an overstatement of exactly the kind this project exists not to make —
the arithmetic was right and the inference was not.

The bootstrap makes it concrete: P(strategy Sharpe > benchmark Sharpe) is 55% on BTC and
59% on ETH, with 90% intervals spanning zero comfortably. And under D121's start-date
analysis, at two of five start dates the strategy's Sharpe is *below* the benchmark's.

**Two design choices worth stating:**

- **Paired, not independent.** A long-flat strategy's returns are a filtered version of the
  instrument's, so the two series are strongly correlated. Bootstrapping them independently
  would inflate the variance of their difference and make everything look insignificant for
  the wrong reason. Resampling one index vector and applying it to both preserves the
  correlation, which is what makes the interval meaningful. A test pins this: bootstrapping
  a series against itself must give a degenerate interval at exactly zero, which only holds
  if the pairing is intact.
- **Blocks, not single bars.** D23's argument, reused: contiguous blocks preserve the local
  dependence a trend follower lives on; a per-bar shuffle would destroy it.

## What replaced the retracted claim

The narrower statement that survives both this and D119: at matched average exposure the
strategy earns several times the terminal wealth of constant exposure, and its max drawdown
is lower at every start date and on both symbols, typically by half. **That is a
drawdown-shape result, not an alpha result**, and the report now says so in those words.
