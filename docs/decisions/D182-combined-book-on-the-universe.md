# D182 — The combined long+short book on the D140 universe

**Status:** PRE-REGISTERED — implementation committed (85176d7), **study not yet run**
**Date:** 2026-08-21
**Category:** Analytics
**Source:** D172 combined the two books on two instruments; D180 established what two-instrument findings are worth here

> Written and committed **before** the study runs, as D173, D178 and D180 were. The
> predictions below are falsifiable and dated by git. A result section will be appended and
> nothing above it edited.

## The question

D172 combined the long and short books on BTC/ETH and found the combination has a **lower
Sharpe** than the long book alone but a **smaller drawdown**. That is a two-instrument
finding, and D180 has just shown what those are worth in this project: E1 cleared its bar
five times on BTC/ETH and failed on sixty-two coins, because those two sit at the 97th and
85th percentile of the variable that decided the outcome.

**Nobody has ever run a combined book across the cross-section.** That is the gap. Testing
a rule against an unmeasured baseline is the mistake D179 made — it landed as a headline
before the universe test that undercut it, and before the weighting fix that halved it.

## What is built

`scripts/run_combined_universe.py`. Two runs, both fixed before meeting this universe (D141):

- **Long arm:** `breakout_universe.baseline_variant()`, reused directly rather than
  re-derived — it is the same configuration the published D140/D141 universe study runs.
- **Short arm:** the published short baseline — 20/5, SMA200 regime gate, inverse-vol
  sizing, `channel_stop`, borrow at 10%/yr.

**Per-symbol, not portfolio.** Each coin's own long and short series are combined into one
book, which is the direct analogue of D179 and reuses `combine_books` unchanged. This is
**not** a long/short portfolio across 62 coins — there is no cross-sectional capital
allocation in this framework, and building one is a separate piece of work with its own
design decisions. The two legs remain entirely separate backtests blended after the fact.

Weights are the expanding-window inverse-vol from D181. Running this before that fix would
have inherited the whole-sample look-ahead sixty-two times over.

## The predictions

Scored at `taker_40bp`, per cohort (SURVIVED / COLLAPSED / DELISTED).

**H1 — the combination scores a LOWER Sharpe than the long book alone on >50% of coins,
and a SMALLER max drawdown on >50%.** Predicted **TRUE**.

This is D172's BTC/ETH finding asserted on the cross-section. The mechanism is arithmetic
rather than empirical: you cannot diversify with a negative-expectancy asset, you can only
spread the same losses more smoothly. The short book loses money on 55 of 62 coins (D180),
so adding it must cost return; what it buys is a smoother path, because its losses arrive
at different times than the long book's.

Against this: D181 has just changed the weighting, and the corrected BTC combined Sharpe
(0.462) is **above** the long leg's… no — it is far below the long leg's 1.223. On both
symbols the combination already scores below the long book alone, which is what H1 asserts.
The open question is whether it holds where the long book is weak, and there are 41
collapsed coins where it might not.

**H2 — the long/short correlation sits within ±0.2 on more than 75% of coins, and this is
NOT evidence for the ensemble.** Predicted **TRUE**, and the second clause is the point.

`BREAKDOWN_SHORT_STRATEGY.md` sets a ~0.2 correlation target and D172 reported the books
clearing it. But the short book is flat on ~85% of bars, so the two legs rarely carry
simultaneous exposure at all. **Near-zero correlation here is mechanical — an artifact of
non-overlapping exposure — not evidence of complementary payoffs.** Two books can be
perfectly uncorrelated and still combine into something worse than the better one, which is
exactly what H1 predicts. If H2's first clause holds and H1 also holds, the correlation
target is measuring something real and worthless.

**What would falsify each:** H1, a majority of coins where the combination scores a higher
Sharpe, or a majority where it draws down more. H2, correlation outside ±0.2 on more than a
quarter of coins.

**Confidence:** high on H1, which is close to an arithmetic claim; high on H2's first
clause; the second clause of H2 is an interpretation the data can support but not settle.

My last three mechanism-first predictions in this project were falsified (D173 H1, D178 H2,
D180 all three). H1 differs in kind from those — it predicts a *cost*, not a benefit, and
every one of the falsified predictions was a prediction that something would work.

## What this cannot establish

**Nothing here makes either book worth running**, whichever way H1 lands. The long book's
DSR sits near 1.0 only because its plateau is flat; the short book's is 0.04–0.538, and
D181 has just shown its ETH Sharpe was carried entirely by 2018. Combining two books does
not create an edge neither has.

**And the combination is measured with a known-flawed weighting.** Inverse-vol reads a book
that is flat 85% of the time as low-risk rather than as absent, so the short leg draws the
majority of the risk budget *because* it barely trades (mean long weight 0.389 on BTC).
That is recorded in D181 and reported on the face of this study's output; it is not fixed
here, and every combined figure inherits it.

## Multiplicity

**None added.** Both baselines already exist and are already in their pools. Own registry
`data/combined_universe_registry.sqlite` under `combined-universe-*`, exactly as D174 and
D180 did. No DSR in either published report moves.
