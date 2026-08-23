# D199 — the exit policy: a shorter clock, and a stop that follows the trade

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-24
**Category:** Signals & strategy interface

> A result section will be appended and nothing above it edited.

## Why this exists

D198 found that **the trades worth having resolve quickly**. Its hindsight diagnostic —
the signals the confirmation filter discarded, which by construction are the ones where
price went straight back inside the range — scored **+0.785 and +0.310 Sharpe at 57% and
43% hit rates**, against the kept ones at −0.288 and −0.183 at 28–30%.

That diagnostic is not tradeable: membership is only knowable 20 bars later. But it points
at something that is. If the winners resolve fast, the lever is the **holding period**, and
`MAX_HOLD` has been 60 bars since D196 without ever being examined.

The second question is older. D196 built a trailing stop into `bounce_rr` and it was
**completely inert** — none of 115 stop exits finished in profit, because the 3R target
always resolved first. D197 dropped the trail rather than fix it. So "should the stop
follow the trade" has been asked twice in this project and never answered.

## A calibration note on my own predictions

D197 and D198 both predicted, at **high confidence**, that a refinement would fail to beat
its own baseline. Both were **falsified**: S6 beat the erasure-only control on 16 of 16
cells, and D198's confirmation rule beat the unfiltered book on both symbols.

The pattern is specific — I have been reliably right that things fail the *null* and
reliably wrong that they fail their *baseline*. Baseline-relative predictions below are
therefore stated at **moderate** confidence, and that downgrade is recorded here rather
than applied silently.

## What changes, one thing at a time

Everything not named below is D197's and D198's, unchanged: the S6 field at k=2,
cluster_atr=0.5, X=0; reversal cells only; entry market-on-open the bar after the signal;
2 × ATR(20) stop distance; 40 bps round trip; full equity; one position at a time; stop
taken first when a bar covers both.

**Two questions, two primaries, each isolating a single change from D197's baseline.**

| | entry | exit policy | `MAX_HOLD` |
|---|---|---|---|
| **D197 baseline** | ALL signals | 2 ATR stop + 3R target | 60 |
| **Primary A — the clock** | ALL signals | 2 ATR stop + 3R target | **20** |
| **Primary B — the trail** | ALL signals | **chandelier trail** | 60 |

### The holding periods

`MAX_HOLD` ∈ **{5, 20, 60}**. Every value is an existing named constant in this codebase,
not a new number: 5 is `terrain_nulls.HORIZON` (itself `breakout_study.E2_N`), 20 is
`terrain_field.CONFIRM_WINDOW` from D198, and 60 is the incumbent `MAX_HOLD`.

Naming it honestly: at 60 bars `MAX_HOLD` was a **backstop**, explicitly "not an exit rule
that competes with the others" (D196). At 5 and 20 it becomes a real time-based exit. That
is the change, and calling it a backstop at those values would be a lie.

### The trailing stop

**`ChandelierStop` at multiple 2, window 20** — the trade's best excursion so far, less
2 × ATR(20), recomputed every bar and **ratcheted** so it can only tighten.

Chosen because it introduces no new numbers: D197's stop is exactly `AtrStop(multiple=2,
window=20)`, and the chandelier reuses both. The comparison is also the one the codebase
was already built for — `AtrStop`'s docstring says so in as many words:

> Fixed rather than trailing on purpose — it is the control that isolates "how far away
> should a stop sit" from "should a stop follow the trade". Compare it against
> TrailingChannelStop to separate the two questions.

`TrailingChannelStop` was the alternative and is **not** used: it would add an `n_bars`
lookback that nothing here fixes, and a swept lookback is the search this project spends
its documents preventing.

**The trailing policy drops the 3R target.** This is deliberate and it is the only way the
test is not vacuous: D196 measured a trail sitting behind a 3R target and the target won
every single time, 115 out of 115. Keeping both would re-run a known null result. So the
two exit policies are compared as *whole policies* — "fixed stop plus fixed target" against
"a stop that follows" — rather than as one bolt-on.

### Entry book

**ALL SIGNALS** carries both primaries, not D198's CONFIRMED book. The hypothesis is that
fast reverters are the winners, and CONFIRMED *structurally excludes them* — a signal is
confirmed only when price came back and left again, so the trades that reverted and stayed
reverted are precisely what it filters out. Testing a short clock on CONFIRMED would be
testing it on the book with the relevant trades already removed.

CONFIRMED is run at both primary settings anyway, as four sensitivity cells, so the
interaction is measured rather than assumed.

## The bar

Each primary is judged on its own, and all three conditions are required on **both**
symbols:

1. **Beats the D197 baseline by ≥ +0.10 Sharpe** — ALL / fixed / 60, which measured
   −0.437 on BTC and −0.667 on ETH.
2. **Beats its matched local-band null by ≥ +0.10 Sharpe** — 500 draws, seed 0, the exit
   policy applied identically in both arms.
3. **Beats buy-and-hold** — +0.773 BTC, +0.308 ETH.

Floor and grounding unchanged from D195 through D198.

**Reported alongside, not optional:** long and short legs separately; exit-reason mix per
cell (stop / target / trail / time), because the whole question is which rule is doing the
closing; median bars held; and the by-year split.

## Multiplicity

ALL × 2 exit policies × 3 holds = 12 cells, plus CONFIRMED at the 2 primaries = 4, so
**16 cells and 4 baseline comparisons = 20 looks**, each against 500 null draws.

**Cumulative on the S6 family: 40 → 60 looks.** That is a large ledger for one sensor, and
it is the honest cost of three rounds of post-hoc refinement on a map whose placement claim
was measured at zero. Any Sharpe that survives has to pay for all sixty.

## Predictions

**H1 — a shorter `MAX_HOLD` fails to beat the 60-bar baseline by the floor on at least one
symbol.** Predicted **TRUE**, *moderate* confidence (see the calibration note). The
diagnostic's edge came from **selection** — knowing which trades reverted — not from
timing, and a shorter clock is applied blindly to winners and losers alike. Against that:
a 2-ATR stop held for 60 bars is very likely to be hit by noise alone, since a random walk
covers roughly √60 ≈ 7.7 ATR in that time, so a shorter clock genuinely reduces
noise-stopping. This one is a real coin-flip and is marked as such.

**H2 — the chandelier trail fails to beat the fixed policy by the floor on at least one
symbol.** Predicted **TRUE**, *moderate* confidence.

**H3 — `MAX_HOLD` = 5 is the worst of the three holds on both symbols.** Predicted
**TRUE**, moderate-to-high. A 3R target is 6 ATR away and five bars covers about √5 ≈ 2.2
ATR of typical range, so the target is close to unreachable and nearly every exit becomes a
time-exit at the close. That is D196's `touch_horizon` rebuilt, and `touch_horizon` was the
worst thing in that grid at −0.777.

**H4 — no cell beats its null by the floor on both symbols.** Predicted **TRUE**, high
confidence. This is the prediction I have been consistently right about: an exit policy
changes when trades close, not where the mass sits, and D197 measured the placement claim
at −0.007 and −0.012.

**H5 — nothing beats buy-and-hold.** Predicted **TRUE**, high confidence.

**H6 — the short leg stays worse than the long leg in every cell.** Predicted **TRUE**,
high confidence. D197: 16 of 16. D198: every book, both symbols, including inside its
positive diagnostic.

**The interesting failure mode, named in advance.** If a shorter clock passes, the first
suspicion is not that the clock is wise but that it **cuts the short leg's losses** — the
shorts are where the damage is and they are the trades that run longest against a
decade-long uptrend. That would be a directional-exposure effect wearing a timing label,
and the leg split is what exposes it. Hence legs are mandatory reporting, not a follow-up.

## Verification

- The chandelier trail restated on a bare bar sequence is **pinned by test against
  `strategies.breakout.ChandelierStop`** on real bars, the same arrangement
  `terrain.mean_true_range` has with `_mean_true_range` and `terrain_swing._is_swing_bars`
  has with `_is_swing`. An optimisation or a restatement is only valid if it is provably
  the same number.
- The ratchet is asserted: the trail must never loosen, on any bar, in either direction.
- A trade whose stop and trail both trigger on one bar takes the worse of the two.
- Exit-reason accounting sums to the trade count in every cell.
- Full suite green, mypy clean, summary JSON re-renders byte-identically.
