# D175 — The engine models no margin call, no liquidation and no borrow recall, and three accounts went past −100% to prove it

**Status:** Deferred (blocked on engine work), recorded per R3
**Date:** 2026-08-21
**Category:** Backtest engine
**Source:** Discovered by the D174 universe test, which was looking for something else

## The gap

`run_backtest` has no margin model. A position that moves against the book accrues loss
without limit: there is no maintenance margin, no forced liquidation, no borrow recall,
and no bankruptcy. NAV can go negative and the simulation keeps trading.

For the long book this is harmless and structurally so — a long spot position's worst case
is the instrument reaching zero, weights are capped at 1.0, and D108 already recorded that
`Equity` semantics are exactly right for a long-only unlevered book. **For the short book
it is not harmless, and the universe test made it concrete.**

## What it looked like

Running the short book across the 62-symbol D140 cross-section, three accounts lost more
than everything:

| Symbol | Status | Total return | Max drawdown |
|---|---|---|---|
| USTC-USD | collapsed | **−1105.7%** | 321.3% |
| LUNC-USD | collapsed | −167.1% | 125.3% |
| LUNA1-USD | delisted | −149.5% | 119.4% |

These are Terra. Shorting a collapsed, near-zero-priced coin that then rallies multiples
loses many times the notional; the worst lost eleven times the account it started with.

**The stops were active.** D170's intrabar stop exits the moment price touches the level,
and it did — it cannot help when the instrument opens five times higher, and it cannot help
at all once repeated losses have taken NAV negative and the book is still trading. This is
not an argument against the stop. It is the demonstration that a stop and a margin model
are different things, and that this project has only one of them.

## Why it was not caught earlier

Every short result before this ran on BTC and ETH, which never move violently enough from
a low enough price to take an unlevered short past −100%. The gap was invisible on the two
instruments the project had, and became visible the moment it met instruments it had not
chosen — which is the argument for the universe fixture restated in a form nobody
predicted.

It also would not have been caught by the tail-discipline work. D169's position cap
(weights ≤ 1.0) bounds LEVERAGE at entry; it does not bound LOSS after entry, and those
are different guarantees. The record said the cap was "the per-trade position cap the brief
requires"; that was accurate and insufficient.

## Consequences, stated rather than filed away

- **Every short result in this project is optimistic**, and the optimism is largest exactly
  where the instrument is most violent — which is exactly where a short book looks most
  attractive. `BREAKDOWN_RESULTS.md` and `docs/results/swing_universe.md` both carry this
  as a standing caveat.
- **No short number here describes a loss a trader could actually have taken.** A real
  venue would have liquidated these positions, probably at a terrible price; a real borrow
  desk would have recalled the coin long before. Both would have truncated the loss AND
  removed the ability to re-enter, and neither is modelled.
- Aggregate statistics over a cross-section containing such a symbol are not averages of
  anything. The universe report leads on the median and names the blow-ups separately for
  this reason.
- CAGR is undefined once total return passes −100%, since a fractional power of a negative
  number is not a real rate. The universe study emits `None` there rather than `nan`,
  because a `nan` in a results document is a number nobody has thought about.

## What would need to be true to build it

Roughly in the shape D111's deferral took, and deliberately not attempted mid-study:

1. **A maintenance-margin rule on `PortfolioState`** — an equity-to-notional threshold
   below which positions are force-closed, evaluated on the same bar loop as everything
   else and before the strategy is consulted, in the same slot D170's stop check took.
2. **A liquidation fill convention.** A forced close is not a stop: it happens at the
   venue's discretion, at a worse price, and D10's gap semantics are the natural precedent
   for how to price it honestly rather than optimistically.
3. **Bankruptcy as a terminal state.** Once equity is gone the run must STOP, not continue
   trading a negative account. That is a change to the engine's loop invariants and needs
   the same golden-master and property treatment D170 got.
4. **Borrow recall**, which is the one that would bite hardest in practice and is the
   hardest to model without venue data — a hard-to-borrow coin is recalled precisely when
   everyone wants to be short it.

Until these land, the honest framing is the one both reports now carry: **the short book's
losses are unbounded in the model as well as in reality, and the model's version is the
more optimistic of the two** — because a real venue would have stopped it, and this one
does not.
