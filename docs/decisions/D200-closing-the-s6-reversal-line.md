# D200 — the S6 reversal line is closed

**Status:** Committed
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** D197, D198 and D199, and the recommendation D199's result section carries

## The stop

> **The S6 reversal line is closed.** No fourth refinement of the boundary-fade rule will
> be pre-registered — not a different confirmation window, not a different stop or target,
> not a different entry book, not a different threshold, not a finer bar size.

Stated in the same form as D194's stop for S1, and for the same reason: a ladder of
refinements is infinite, every rung is a fresh look at one hypothesis, and leaving the
ladder open makes "the last version wasn't quite right" an unfalsifiable escape hatch that
can be pulled forever.

## What was actually established

Three rounds, sixty looks, one answer that never moved:

| | what was refined | against its own baseline | against the null |
|---|---|---|---|
| D197 | the map itself | beat the erasure-only control **16 of 16** | **−0.007 / −0.012** |
| D198 | the entry timing | beat the unfiltered book on **both** symbols | **−0.156 / +0.090** |
| D199 | the exit policy | failed on both | **−0.013 / −0.045** |

Every round improved the strategy against its own predecessor. Not one of them moved the
null comparison, because **not one of them was about placement** — and placement is the
only thing S6 ever claimed. D197 measured that claim at essentially zero on both symbols
and it has been zero ever since.

The clearest single demonstration is D199's `confirmed | fixed | h20` cell, which stacked
two independent refinements and beat the baseline on **both** symbols — the first
configuration in the family to clear any hurdle twice over — while still failing the null
on both and losing to buy-and-hold by more than a Sharpe point. A better wrapper around the
same empty box.

## What the line produced that outlives it

The strategies failed. Three findings did not, and they are the reason the sixty looks were
not wasted:

- **A paired null is necessary and not sufficient** (D196). Six cells beat random levels
  while losing money — "better than chance" and "worth trading" are different claims.
- **A control and a null answer different questions** (D197). S6 beat "fade every breakout"
  on all sixteen cells and was dead even against randomly-placed mass. A result that clears
  one can be nothing on the other.
- **Waiting for confirmation sells the winners to pay for a better entry** (D198). The
  discarded signals scored +0.785 and +0.310 against the kept ones at −0.288 and −0.183.

Also priced along the way, and reusable: D9's adverse selection at **0.138–0.195 Sharpe**
(D196), and the arithmetic that a 0.5-ATR stop makes a 40 bps round trip cost **0.49R**
(D196) while a 2-ATR stop makes it **0.12R** (D197).

## Ledger

**60 looks on the S6 family, closed.** Recorded so that anything reusing this sensor
inherits the count rather than starting from zero.

## What this stop does NOT cover

**The imbalance formulation** — the sum of demand mass *below* current price against supply
mass *above* it — is outside this closure, and the distinction is mechanical rather than
rhetorical:

| | the closed line | the imbalance formulation |
|---|---|---|
| what it reads | the single bucket **at** current price | the **whole field**, both sides |
| when it has a reading | the ~20% of bars outside the envelope | **every** bar |
| shape of the trade | event-driven fade at a boundary | position held on a direction |
| the claim | inventory at a boundary predicts reversal | net inventory skew predicts direction |

It never reads the erased bucket, so it is not forced into the boundary-fade shape the
erasure geometry imposed on everything above; and a map can be locally uninformative while
carrying real aggregate skew, so D197's verdict does not settle it. It was tabled during
D197's design, before any of these results existed, which is what stops it being a fourth
refinement wearing a new name.

It is nonetheless the **same map**, whose placement measured zero. That prior is
unfavourable and its pre-registration says so in its own voice rather than borrowing the
optimism of a fresh start.
