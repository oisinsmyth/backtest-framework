# D171 — A family of stop rules, swept; tighter stops help one symbol and not the other

**Status:** Committed
**Date:** 2026-08-21
**Category:** Signals & strategy interface
**Source:** Follow-on to [D170](D170-intrabar-stop-execution.md)

## Decision

Three stop rules join `ChannelStopExit`, all direction-agnostic and all usable by either
book:

- **`TrailingChannelStop(n_bars)`** — the classic trend-following stop: the n-bar extreme
  against the trade, recomputed every bar. "Lowest low of the last n days" for a long,
  highest high for a short.
- **`AtrStop(multiple, window)`** — `multiple × ATR` from the entry reference, fixed at
  entry. The control that isolates *how far* a stop should sit from *whether it follows*.
- **`ChandelierStop(multiple, window)`** — `multiple × ATR` back from the best excursion
  since entry, trailing.

`ExitRule` gains an optional `stop_level(view, position)`. The strategy collects every
proposal each bar, keeps the **tightest**, and **ratchets** it. The close-based backstop
moves from `ChannelStopExit` onto the strategy, applied once against the ratcheted level
rather than duplicated into every rule.

The short book's tail-discipline check now accepts **any** stop-providing rule rather
than `ChannelStopExit` specifically.

## Rationale

**Why ratcheting is not optional.** The raw n-bar extreme moves both ways. A level allowed
to retreat is not a stop — it would let a loss grow after having promised not to. The
strategy therefore keeps the tightest level ever proposed for the life of the trade, where
"tightest" means nearest the price in the trade's direction: highest for a long, lowest
for a short.

**Why these three.** They separate two questions the incumbent entry-channel stop
conflates. `AtrStop` varies distance while staying fixed; `TrailingChannelStop` and
`ChandelierStop` vary whether the level follows the trade. Sweeping all three at fixed
entry/exit parameters means a difference between rows is attributable to the stop and
nothing else.

**Why a stated Sharpe floor.** `SHARPE_EPS = 0.01`, fixed before reading. Without it, an
arithmetic difference of 0.001 reads as an improvement — an earlier cut of the scorecard
marked `trail_20` KEEP on a delta that rounds to +0.00. Ten years of daily data buys a
standard error near ±0.4 on an annualised Sharpe, so 0.01 sits far below the noise floor
in both directions; its only job is to stop dust being reported as a result.

## What the sweep found

**The bind rate orders everything, and it is the column to read first.** D170's incumbent
entry-channel stop bound once in 915 armed bars. The trailing stops bind 20–60 times, and
that is the difference between a stop being tested and a stop being decorative.

Scored by the rule the long study fixed before looking — keep only what improves on every
symbol:

| Stop | Δ Sharpe BTC | Δ Sharpe ETH | Verdict |
|---|---|---|---|
| `trail_5` | +0.279 | −0.002 | DROP |
| `trail_10` | +0.144 | +0.068 | **KEEP** |
| `trail_20` | +0.002 | +0.000 | INERT |
| `atr_2` | +0.092 | +0.013 | **KEEP** |
| `atr_3` | +0.034 | −0.002 | DROP |
| `chandelier_3` | +0.092 | −0.096 | DROP |

**`trail_20` is inert, and mechanically so.** For a short entering on a 20-bar low, a
20-bar trailing high *is* the entry channel high — it is the incumbent under another
name, producing identical trades. Five distinct configurations were tested, not six.

**Binding more is not uniformly better, and that is the finding.** Rank correlation
between how often a stop binds and how much it helps is **+0.94 on BTC and −0.43 on ETH**.
On ETH the stops that fire most (`trail_5`, `chandelier_3`) are cutting winning trades
short rather than truncating losers — the same failure mode the long study found in its
entry filters, where every filter removed trades that were on average good. A stop is a
trade-removing device and inherits that risk.

**Less bad is not good.** `trail_5` takes BTC from −71.6% to −40.6% and its drawdown from
72% to 52%, which is a large improvement in damage and no improvement at all in edge: the
Sharpe is still −0.34. The entry rule is what failed its null, and no stop repairs an
entry.

## Consequences

- Two stops survive the every-symbol rule (`trail_10`, `atr_2`). Neither is **adopted**
  here: the sweep added a fresh trial series to a book that has not shown an entry edge,
  and picking the best of five after the fact is exactly the selection this project's
  machinery exists to penalise.
- **The short book still has no TrialRegistry rows and no deflated Sharpe**, which the
  brief asks for and the long book has. That gap was tolerable before this sweep and is
  not now — every Sharpe in the breakdown report is raw and should be read as an upper
  bound. Closing it is the prerequisite for adopting any stop family.
- The sweep was run at fixed entry/exit parameters. A stop interacts with the exit channel
  beside it, and re-optimising both together is a much larger multiplicity bill than this
  book currently justifies.
