# D112 — A "trade" is a position episode, and the diagnostics say so once

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout study session

## Decision

`research/trade_diagnostics.py` defines a trade as a **position episode**: from the fill
that takes the book from flat to long, to the fill that returns it to flat. Rebalancing
fills in between belong to the episode that contains them — their costs are charged to it
rather than counted as extra trades.

Stated conventions, each tested:

- **MFE/MAE** are measured against the entry fill price over the bars actually held: the
  full high/low range of bars `[entry_bar, exit_bar)`, plus the exit fill price. The exit
  bar's post-open range is excluded, because the position was already closed at that
  bar's open.
- **Episodes still open at the end of a run** are marked to the final close, flagged, and
  excluded from closed-trade statistics (win rate, holding periods, whipsaw) — their costs
  still count toward cost totals, because that money left the book.
- **`rebalance_costs`** is the subset of an episode's costs charged on interior fills, and
  `rebalance_cost_share` aggregates it: the price of sizing policy, separated from the
  price of the signal.
- **Empty statistics are NaN, not zero** — "no adverse excursion" and "no trades" must not
  render as the same number in a table someone is scanning.
- **p90 holding period uses the nearest-rank percentile**, stated because interpolated and
  exclusive conventions differ materially at the trade counts a breakout strategy produces.

## Rationale

The engine reports fills, not trades, and deliberately so (D77): a fill is what the
simulator actually produces, and "a trade" is an interpretation. But every per-trade
statistic the study reports — win rate, MFE/MAE, time-in-trade, whipsaw rate — depends on
that interpretation, so it is written down once, in one module, and asserted against hand
arithmetic in `tests/golden/test_breakout_golden.py`.

The episode rule specifically is load-bearing. Under weight-targeting with next-open fills
(D110), a vol-targeted position is trimmed on many bars; counting each trim as a trade
would report hundreds of one-bar "trades" that are really one position being adjusted, and
every holding-period, win-rate and whipsaw figure would be meaningless. Separating
`rebalance_costs` from total costs is the other half of the same idea, and it turned out to
be one of the study's more useful numbers: it is what shows that daily vol re-targeting
spends a third of its cost budget on sizing rather than on signal.
