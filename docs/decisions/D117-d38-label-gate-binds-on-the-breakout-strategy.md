# D117 — D38's label gate binds for the first time: the breakout strategy is labelled directional

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout study session

## Decision

`strategies/breakout.py` carries an explicit thesis label in its module docstring: it is a
**directional, beta-loaded** strategy, **not** part of this project's market-neutral
thesis, and its honest benchmark is buy-and-hold rather than the risk-free rate. The same
label opens [`BREAKOUT_RESULTS.md`](../results/BREAKOUT_RESULTS.md).

`tests/unit/test_strategy_labels.py` gains a grep test asserting each of those three
claims is present, and its registered-module list is extended from `{zscore_pairs}` to
`{zscore_pairs, breakout}`.

## Rationale

D38 required the (never-written) sector momentum strategy to carry a learning/reference
label. D82 recorded that no such strategy existed, kept the enforcement mechanism, and left
a test that **fails the moment any new module appears under
`backtest_framework.strategies` without being registered** — explicitly so a future
directional strategy could not land unlabelled.

That test went red on the first run after `breakout.py` was added. It worked exactly as
designed, and this record is the response D82 anticipated.

The label is not a formality. A long-only crypto trend follower inside a repository whose
stated philosophy is market-neutrality is a contradiction, and an unacknowledged
contradiction reads as incoherence. Acknowledged, it is the framework's own claim being
tested: that a strategy is a swappable brick, and that the same engine, cost stack,
walk-forward harness and trial registry can carry a second research strategy chosen to be
as unlike the first as possible. The label also does concrete analytical work — it is what
makes the buy-and-hold column, rather than the Sharpe-against-rf column, the one the
verdict is read from (D115, D37 inverted).
