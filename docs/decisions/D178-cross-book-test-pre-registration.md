# D178 — The cross-book test: `swing_k2` on the long book, E1 on the short book

**Status:** PRE-REGISTERED — implementation committed, **studies not yet run**
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** Both rules have only ever been judged on the book they were developed on

> Written and committed **before** either study runs, as D173 was. The predictions below
> are falsifiable and dated by git. A result section will be appended and nothing above it
> edited.

## The question

Two rules survived their own books, and neither has met the other's:

- **`SwingStructureStop(k)`** was developed and judged entirely on the **short** book. It
  beat `trail_10` on both symbols (D173) and on 69% of 62 universe coins (D174).
- **`FailedBreakoutExit(k)` (E1)** was developed and judged entirely on the **long** book,
  where it is the only recommendation in `BREAKOUT_REVERSAL_FEATURES.md` to survive (D177).

An effect that belongs to the RULE should transfer. An effect that belongs to the BOOK — a
particular exit cadence, a particular trade-length distribution — should not. That is what
this asks.

Both `k ∈ {2, 3}` are tested on both sides. Testing only the k that won would repeat
D173's actual error, which was generalising from one member of a swept set.

## What is built

- Long book: `exit_swing_k2`, `exit_swing_k3` — baseline plus the swing stop, nothing else.
- Short book: `exit_e1_k2`, `exit_e1_k3` — baseline plus E1. **E1 is not a stop** (it bounds
  duration inside a window, not loss), so on a short it rides alongside the incumbent
  `channel_stop`, which the baseline also carries. The delta therefore prices E1 alone.

## The predictions

Scored by the every-symbol rule at `SHARPE_EPS = 0.01`, against each book's own baseline.

**H1 — `swing_k2` will NOT clear the bar on the long book.**

The mechanism is a difference in what the two rules bound in TIME. E1 acts only within k
bars of entry and then leaves the trade alone; a swing stop is live for the entire life of
the position, including deep inside a winning trend, where the last confirmed swing low
sits close behind price and will cut it. The long book's returns are concentrated in a
handful of long trends — that is the finding its own report leads with — and every device
this project has tested that shortens those trends has cost more than it saved.

Against this: the long book's baseline exit is a 10-bar low, which is looser than the swing
stop would be, and on the short book "tighter and adaptive" was exactly what worked.

**H2 — E1 will NOT clear the bar on the short book.**

E1's benefit on the long book came substantially from RE-ENTRY: the trade count rose
38 → 44 on BTC while returns improved. Re-entry is only a gift on a book with positive
expectancy. The short book's entry rule sits at the 51st percentile of its own null on BTC
and it pays borrow at 10%/yr — so cutting a bad trade early helps, and re-entering into
another bad trade costs, and the second effect scales with how bad the entries are.

**Confidence, stated honestly:** lower on H1 than on H2. D173's H1 was falsified by exactly
this kind of mechanism-first reasoning, where the mechanism was sound and applied to the
wrong parameter. If H1 fails again it will most likely fail the same way — on one k and not
the other.

**What would falsify either:** a Δ Sharpe above +0.01 on BOTH symbols of that book.

## Multiplicity, paid up front

Long book 28 → 30 configurations; short book 25 → 27. Every one registered and in the DSR
pool for its cell. Both books' deflated Sharpe will move as a result, and neither has an
edge to lose: the long book sits near 1.0 only because its plateau is flat, and the short
book is at 0.04–0.54.
