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

---

## RESULT — appended after the run; nothing above this line edited

**Both primaries fail, on both symbols.** 16 cells, 500 null draws each, 276 seconds. The
baseline reproduced exactly (−0.437 BTC, −0.667 ETH), so the exit refactor changed nothing
it should not have.

| | BTC | ETH |
|---|---:|---:|
| D197 baseline (ALL / fixed / 60) | −0.437 | −0.667 |
| **Primary A — clock, `MAX_HOLD` 20** | −0.473 (**−0.036**) ✗ | −0.741 (**−0.073**) ✗ |
| **Primary B — chandelier trail** | −0.495 (**−0.058**) ✗ | −0.734 (**−0.067**) ✗ |

### H1 — CONFIRMED, and the reason is the useful part

The clock had **almost nothing to shorten**. At `MAX_HOLD` 60 the backstop binds on only
**16.1% of BTC trades and 10.4% of ETH's**, and the median holding period is **9.5 and 10
bars**. Moving the cap from 60 to 20 moves the median from 9.5 to 9.

D198's diagnostic was right that the winners resolve fast. It did not follow that the book
was being held too long — it already wasn't. What separated the winners was **which trades
they were, not how long they were held**, and a clock cannot express that distinction. The
lever the diagnostic seemed to point at does not exist.

This also retro-validates D196's framing of `MAX_HOLD` as a backstop rather than an exit
rule. It was one, and the numbers now say so.

### H2 — CONFIRMED, but the trail is not inert this time

Unlike D196's trail, which never fired once behind a 3R target, this one dominates the
book: at `MAX_HOLD` 60 it closes **164 of 181 BTC trades and 140 of 151 on ETH**, with
zero time-exits. Median hold falls from 9.5 bars to 5.

So "should the stop follow the trade" now has an answer: **it binds, and it does not
help.** It produces a faster, busier book (181 trades against 124) that is slightly worse
(−0.495 against −0.437). Dropping the fixed target removed the winners' upside without
removing the losers.

### H3 — CONFIRMED, mechanism and all

`MAX_HOLD` = 5 is the worst cell on both symbols by a wide margin: **−1.010 and −1.157**.
The predicted mechanism is exactly what happened — a 3R target sits 6 ATR away and five
bars covers about 2.2 ATR of typical range, so the target became unreachable:

| | target exits | time exits |
|---|---:|---:|
| BTC h=5 | **3 of 199** | 130 (65.3%) |
| ETH h=5 | **2 of 159** | 100 (62.9%) |

Two of 159 trades reached their target. That is D196's `touch_horizon` rebuilt, and it
performs like it.

### H4 — CONFIRMED

No cell beats its null by the floor on both symbols. **One cell clears it anywhere**:
`ETH | confirmed | trail | h60` at +0.190, the 74th percentile — and its BTC twin is
**−0.182 at the 18.8th percentile**. A textbook single-symbol artifact, and precisely what
the every-symbol rule exists to catch. It is also the best Sharpe in the grid at −0.068,
which is what such artifacts always look like from one side.

### H5, H6 — CONFIRMED

Nothing beats buy-and-hold; every one of the 16 cells is negative. The short leg is worse
than the long leg in **16 of 16 cells**, continuing D197's 16-of-16 and D198's clean sweep.

### The one thing that did clear a hurdle on both symbols

`confirmed | fixed | h20` — D198's confirmation entry combined with the shorter clock —
beats the baseline by **+0.131 on BTC and +0.188 on ETH**. That is the first configuration
in the entire S6 family to clear *any* hurdle on both symbols at once, and the two
refinements are additive.

It then fails the null on both (−0.204, −0.008) and loses to buy-and-hold by over a Sharpe
point. It is a better wrapper around the same empty box.

### Ledger

**D199: 20 looks. Cumulative on the S6 family: 60.**

### Recommendation — this line should stop

Three rounds of refinement, sixty looks, one unchanging answer:

| | what was refined | vs baseline | vs null |
|---|---|---|---|
| D197 | the map itself | beat the control 16/16 | **−0.007 / −0.012** |
| D198 | the entry timing | beat it on both symbols | **−0.156 / +0.090** |
| D199 | the exit policy | failed on both | **−0.013 / −0.045** |

Every round has improved the strategy against its own predecessor and left the null
comparison exactly where it was. That is the signature of tuning a wrapper around a signal
that is not there: D197 measured the placement claim at zero and nothing since has moved
it, because nothing since has been *about* placement.

The same reasoning closed S1 in D194 — an infinite ladder of refinements, each a fresh
look at one hypothesis, is an unfalsifiable escape hatch. **The recommendation is to close
the S6 reversal line and not pre-register a fourth refinement of it.**

What is untouched and does not inherit this: the **imbalance formulation** — mass above
current price against mass below — which was tabled during D197's design. It never reads
the erased bucket, so it is not constrained by the erasure geometry that forced everything
above into a boundary-fade shape. That is a different construction with a different failure
mode, and it would deserve its own document and its own ledger rather than an extension of
this one.
