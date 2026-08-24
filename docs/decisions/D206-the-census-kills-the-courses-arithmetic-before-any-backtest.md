# D206 — the census kills the course's arithmetic before any backtest runs

**Status:** Committed
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** WP2 of `New Docs/STRUCTURE_MODEL.md` (D204), counts only

## The result

**A 40 bps round trip costs 0.40% of price. The median stop on this strategy's C1-only arm
is 0.41% of price on BTC and 0.56% on ETH. The cost of trading is roughly the entire
distance to the stop.**

Everything below follows from that one line, and none of it required a backtest.

| symbol | arm | n | median stop (% of price) | friction (R) | hit rate needed at 5R |
|---|---|---:|---:|---:|---:|
| `BTCUSDT` | C1 only | 3,875 | 0.41% | 0.972 | 32.9% |
| `BTCUSDT` | C1+C2+C3+C4 | 120 | 0.68% | 0.589 | 26.5% |
| `ETHUSDT` | C1 only | 3,753 | 0.56% | 0.718 | 28.6% |
| `ETHUSDT` | C1+C2+C3+C4 | 106 | 1.01% | 0.395 | 23.3% |

**The course's central claim is a hit-rate argument stated with no costs at all**: a 5R
target, break-even at "two out of ten", "highly profitable" at 30%. Frictionless it is
nearly right — the true break-even is 16.7%. At 40 bps it is 23.3% to 32.9% depending on
the arm and the symbol.

**A 20% hit rate at 5R loses money in every cell measured here.** That is arithmetic, it is
independent of whether any of the five components carries information, and it is the single
most decisive thing this programme will produce.

## Why this is a census result and not a test

Nothing here compares anything to anything. No hypothesis is scored, no null is drawn, no
parameter is chosen on the strength of it. **The multiplicity ledger stays at 0 looks.**

The value is the same as D198's census, which rejected a proposed rule outright once the
counts showed 86% of signals already had a second approach within 20 bars — the "filter"
was a one-bar entry delay wearing a filter's name. Counting first is cheap and it keeps
being the thing that settles the question.

## What else the counts settled

**The stop condition clears; H5 is falsified.** 120 and 106 fully-stacked entries against a
floor of 30. Predicted at moderate confidence that four conjunctive filters would leave the
arm underpowered, and that was wrong. WP3 and WP4 proceed.

**C5 is dropped as a stacked filter, on counts alone.** RSI at the textbook 30/70 collapses
the stacked arm from 120 to **2** entries on BTC and 106 to **2** on ETH. The thresholds
essentially never coincide with structural confluence. It is retained as a *continuous
feature* in WP4a, where a 2-trade arm has nothing to say and a rank correlation over 3,875
trades still does. This is a scope reduction made on counts before any outcome was seen, and
it is recorded here rather than folded in silently.

**C3 barely filters.** The 61.8% band admits 69% and 70% of setups on its own. A filter that
rejects three setups in ten is doing very little work — and that is *before* WP3 asks
whether 0.618 differs from `structure.PLACEBO_RATIOS`.

**The stack's one measurable effect so far is that it enters deeper, and that is not a
signal.** Median retracement moves from 0.32 to 0.54, which widens the median stop from
~1.05 to ~1.75 ATR and roughly halves the friction. A real mechanical benefit — and waiting
for a deeper pullback achieves it without any of the structure. Separating "the confluence
means something" from "the confluence is a proxy for depth" is now WP4's central job, and
naming the confound before the run is the point of writing it here.

**The discretion gap, measured.** 340 BTC setups have all three conditions somewhere in the
pullback window; only **120** have them at the same bar. ETH: 388 against **106**. So
roughly two thirds of the confluence a trader would see on a chart afterwards was never
simultaneous. Which bar you would actually have entered on is a judgement call, and this is
the first number attached to that.

## Two implementation defects the census flushed out

Both were caught by tests written before the run, and both are the same shape: a guard that
turns a bad case into a *missing* case rather than a wrong one.

**ATR warm-up punched holes in windows.** The first implementation skipped bars with no ATR,
producing non-contiguous windows whose first bar was not the bar an entry became possible —
silently shifting every base-arm entry forward by an unrecorded amount. Now the setup is
**refused outright** and counted as `dropped_no_atr`. 27 and 28 setups on the two symbols.

**Setups dead on arrival were dropped without being counted.** An `if window:` discarded
setups whose window was empty because price had already closed beyond the leg's origin by
the bar the leg confirmed — the leg's end pivot needs `k` bars to confirm, and a fast market
can retrace the whole leg inside them. 373 and 333 setups, roughly 9% of the population,
vanishing silently. Found because `SetupPopulation`'s counts were asserted to add up to the
change-of-character total, and they did not.

That assertion exists because of D205's finding, one work package earlier: an invariant
asserted only over the outputs a component produces cannot see a component that has stopped
producing them. **A count that only ever appears as a subtraction is a count nobody checks**,
so the drops are returned explicitly and their arithmetic is a test.

## What this does not establish

Nothing about whether the components carry information. The friction result says the
strategy as taught cannot pay for itself at 15m under 40 bps at the hit rate it claims; it
says nothing about whether a change of character, a flipped level, a retracement or a fair
value gap predicts anything at all. That is WP3 and WP4, and the answer there is
independent — a component can be informative and still not clear a 0.6R toll.
