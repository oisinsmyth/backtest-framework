# D203 — the S6 map is closed

**Status:** Committed
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** the permanent stop fixed in D202, triggered by D202's result

## The stop

> **The S6 signed inventory map is closed.** No further statistic, sizing rule, trading
> rule, threshold, exit policy, bar size or symbol will be pre-registered on it.

D200 closed the *reversal line* on this map. This closes the map itself. Same form as
D194's stop for S1, same reason: the ladder is infinite and leaving it open makes "the last
reading wasn't the right one" an escape hatch that can be pulled forever.

## The record

Five documents, five ways of reading one field, one answer:

| | what was read | verdict against its null |
|---|---|---|
| D197 | the bucket **at** price, at a boundary | **−0.007 / −0.012** |
| D198 | the same, entered on a second approach | −0.156 / +0.090 |
| D199 | the same, with a shorter clock and a trail | −0.013 / −0.045 |
| D201 | **all** mass either side of price | −0.052 / −0.077 |
| D202 | mass **near** price, sized on its magnitude | **−0.822 / −0.829** |

Every refinement that changed the *wrapper* — entry timing, exits, stops — improved the
strategy against its own predecessor and left the null exactly where D197 put it. The one
refinement that changed the *statistic* (D202) fixed every defect it set out to fix and
produced the worst result of the five.

**That progression is the case for stopping.** It is not that the map has never been read
correctly; it is that reading it better makes the answer worse.

## What D202 established, which the earlier documents could not

D201 was uninterpretable: a book at +0.78 net exposure, nine decisions in eleven years, and
its best cells 78–92% one multi-year long. D202 fixed all three — net exposure −0.07, 393
decisions, 48.7% sign agreement with the old reading — and with a clean measurement:

**At zero cost, the local reading sits at the 2.6th and 1.4th percentile of its own rotation
null, and loses in 11 years out of 11 on BTC.**

The map's local structure is not uninformative about direction. It is **reliably wrong**,
persistently, with costs removed and the beta confound gone.

The likely mechanism unifies the whole family: demand mass accumulates below price exactly
when price has been *falling into* that area, so trading it is fading a decline. Fading has
lost in every form measured here — short leg worse than long in 16 of 16 cells (D197), 16 of
16 (D199), 8 of 8 (D201), 11 years of 11 (D202).

**The obvious inversion is not available.** Flipping the sign of a signal that failed is a
post-hoc reversal of a rejected test. If anyone wants it, it needs its own document, its own
bar, its own predictions written first, and its own line in a ledger that already stands at
92 looks — not a footnote to this one.

## Ledger

**92 looks on the S6 map, closed.**

- 60 — the reversal line (D197, D198, D199), closed by D200
- 12 — the global imbalance (D201)
- 20 — the local imbalance (D202)

Recorded so that anything reusing this map inherits the count rather than starting from zero.

## What outlives it

The strategies all failed. The methodology did not, and this is the reason the 92 looks were
not wasted:

- **A paired null is necessary and not sufficient** (D196) — six cells beat random levels
  while losing money.
- **A control and a null answer different questions** (D197) — S6 beat "fade every breakout"
  on 16 of 16 cells and was dead even against randomly placed mass.
- **Waiting for confirmation sells the winners to buy a better entry** (D198) — the
  discarded signals scored +0.785 and +0.310 against the kept ones at −0.288 and −0.183.
- **A timing control is not an exposure control** (D201/D202) — Sharpe is invariant to
  constant leverage, so a book with a net tilt cannot be judged by buy-and-hold alone;
  rotating the position series is what isolates *when* from *how much*.
- **An effect-size floor has a width assumption** (D202) — +0.10 over a null *mean* is not a
  hurdle when the null is wide. D201's global statistic cleared it at the 67th percentile.
  D194 built a floor to stop large samples manufacturing significance; this is the mirror
  failure, and both need the percentile reported beside the delta.

Reusable numbers: D9's adverse selection priced at **0.138–0.195 Sharpe** (D196), and the
stop-width arithmetic that turns 40 bps into **0.49R at 0.5 ATR** and **0.12R at 2 ATR**
(D196/D197).

## What is not closed

Nothing about supply and demand as a concept, and nothing about the swing detector, the
volume normalisation, or the log-price kernel — those are components and several are pinned
by test against older implementations.

What is closed is **this map, read as a directional or reversal signal on daily crypto
bars**. A different claim, a different data source, or a genuinely new construction is a new
document and starts its own ledger, with this one disclosed.
