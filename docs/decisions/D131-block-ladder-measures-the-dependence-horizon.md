# D131 — The block ladder is a RULER for the dependence horizon, and its sign is inverted from D23

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout Monte Carlo session

## Decision

The serial-dependence null (D130) is run at block sizes **{1, 5, 20, 60}** and reported as
a ladder, not as a single p-value. `docs/results/breakout_monte_carlo.md` reads the ladder
as a **measurement of the time scale of the dependence the strategy trades**, and states
explicitly that this reuses D23's block-versus-shuffle construction with the opposite sign.

The ladder is checked against an independently-measured quantity: the strategy's own median
holding period (26–29 bars, from D112's per-trade diagnostics). A block of *b* bars leaves
runs of *b* consecutive real bars intact and randomises only the joins, so a strategy whose
edge lives entirely inside one trade's worth of bars should stop being distinguishable from
its null once *b* reaches the holding period. Where the ladder actually crosses says how much
of the dependence is inside a single trade's horizon and how much is longer-ranged.

## Rationale

**A single p-value at block 1 answers "is there ordering information?" and nothing else.**
It cannot say *what kind*, and a reviewer's immediate next question is what horizon the rule
is reading. The ladder answers that with the same machinery, at the cost of three more cells
per (symbol, tier), and it makes the result falsifiable in a second way: a claimed
26–29-day trend follower whose null crossed at block 1 or refused to cross at block 200
would be describing something other than what its diagnostics say it holds.

**The inverted sign is worth stating, because the same construction means the opposite
thing here.** D23 *demoted* the returns shuffle as a null for the pairs book: destroying
autocorrelation removes the effect a mean-reverter needs, so the shuffled null was too easy
to beat and could not distinguish edge from luck. Block bootstrap replaced it precisely
because it preserves local dependence.

For a trend follower the destruction is the entire point. The shuffle IS the null: a rule
that still earned its result on shuffled bars would thereby be shown to have no timing
information at all, and the marginal distribution would be the whole explanation. So here
the block bootstrap's dependence-preserving property is not what makes it a better null —
it is what makes it a **ruler**. Same instrument, opposite role, and a reader who knows D23
would otherwise reasonably expect this study to have made D23's mistake.

**Why permuted blocks rather than bootstrapped blocks for the ladder.** The ladder has to be
comparable to block 1, and block 1's whole value is the exact buy-and-hold invariance D130
buys with a permutation. A ladder whose rungs used different resampling schemes would not be
a ladder.

## Consequence

The reported grid is 2 symbols x 2 cost tiers x 4 block sizes = 16 path-null cells, each with
five metrics. Those 80 numbers are **not** multiplicity-corrected, and the artifact says so:
the block-1 total-return cells are the headline, and the rest is the ladder that gives them
meaning rather than 79 additional independent tests.
