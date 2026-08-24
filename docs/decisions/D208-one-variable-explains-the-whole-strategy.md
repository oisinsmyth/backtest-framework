# D208 — one variable explains the whole strategy, and it is not any of the five

**Status:** Committed (H1 partly confirmed, H2 confirmed, H3 confirmed, H4 confirmed, H6 confirmed)
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** WP3 of `New Docs/STRUCTURE_MODEL.md` (D204), primary cell, no costs

## The result

**Retracement depth explains every apparent effect in the strategy.** The change of
character, the flipped level, the golden ratio and the fair value gap are all proxies for
one number — how far price has pulled back into the impulse leg — and once that number is
controlled for, none of them adds anything.

The finding arrived in three steps, and the order matters because the second step looked
like a discovery.

## Step 1 — the ratio ladder is a staircase

0.618 was measured against seven other numbers on the same setups and the same legs. No
random draws: the placebo ratios ARE the null, and D189's H2 confound cancels exactly
because every ratio is a point on the same leg.

| ratio | 0.382 | 0.447 | 0.500 | 0.553 | **0.618** | 0.691 | 0.724 | 0.786 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 46.1% | 49.5% | 51.9% | 54.7% | **56.9%** | 58.7% | 59.1% | 60.5% |
| `ETHUSDT` | 46.3% | 49.9% | 52.0% | 55.4% | **55.8%** | 57.2% | 58.2% | 58.0% |

**Strictly monotone in depth on BTC, monotone to within one rung on ETH.** The golden ratio
ranks **4 of 8** on both symbols and sits exactly where interpolation puts it. It beats the
shallower placebos (0.447, 0.553) and **loses to the deeper ones**: against 0.691 and 0.724
the paired bootstrap says 0.618 is not better in **97.4% and 97.6%** of draws on BTC, 93.6%
and 98.8% on ETH.

The spread across the eight ratios is 0.144, against a golden-minus-placebo gap of +0.014.
**The variation between arbitrary numbers is ten times the advantage the special one is
supposed to have.** H2 confirmed at high confidence, and more cleanly than expected: the
result is not "0.618 does nothing", it is "0.618 does exactly what its depth predicts, and
0.786 does more".

## Step 2 — which turns the other arms into a nuisance-variable problem

If continuation rises monotonically with depth, then any level that sits deep on the leg
beats a uniformly-drawn placebo whether or not it means anything. And that is precisely
what the unmatched table showed:

| arm | BTC delta | BTC percentile | ETH delta | ETH percentile |
|---|---:|---:|---:|---:|
| C2 flipped level | −0.0238 | 0.4th | −0.0091 | 13.0th |
| C4 fair value gap | **+0.0817** | **100.0th** | **+0.0643** | **100.0th** |
| C5 RSI | +0.1236 | 100.0th | +0.2069 | 100.0th |

C4 at the 100th percentile of 500 draws on both symbols is, on its face, the clean pass
this programme had not produced in 259 terrain looks plus its own.

## Step 3 — the depth-matched null, which takes it back

Real gaps sit at retracement **0.626**; the uniform placebo sits at **0.444**. So the
comparison was never gap-against-no-gap. It was deep-against-average.

Re-run against a placebo **at the same depth**:

| arm | BTC unmatched | BTC matched | ETH unmatched | ETH matched |
|---|---:|---:|---:|---:|
| C2 | −0.0238 | −0.0159 | −0.0091 | −0.0042 |
| C4 | +0.0817 | **+0.0060** | +0.0643 | **−0.0062** |
| C5 | +0.1236 | +0.0818 | +0.2069 | +0.1548 |

**C4's entire edge was depth.** It collapses by a factor of fourteen and changes sign
between the two symbols. C2 was dead before and stays dead. **C5 — the control — is the
only component that survives**, on 122 and 138 covered touches.

## The disclosure that matters: the depth-matched null was not pre-registered

It was designed after the ladder came back a staircase. That is post-hoc by any honest
accounting, it is counted as six further looks rather than folded into the arms it
re-reads, and the ledger carries it as such.

Two things make it disclosable rather than disqualifying:

1. **It makes every verdict harsher, not kinder.** It took a 100th-percentile pass and
   reduced it to nothing. A post-hoc control that kills the study's only positive result is
   the opposite of the failure mode post-hoc analysis is feared for.
2. **The confound was named before any run.** `structure_nulls.py`'s docstring states it as
   D189's H2 — "C2, C3 and C4 all sit where price has recently been, so touches cluster near
   price in the real arm regardless of meaning" — and notes that C3 is the one arm where it
   cancels. What was not anticipated is that the confound would turn out to *be* the result.

## The other two arms

**C1 — the change of character.** BTC Sharpe +0.124 against a rotation null mean of −0.009,
at the **66.2nd percentile**, delta +0.133. ETH **−0.068**, at the 43.6th percentile, delta
−0.057. BTC clears the +0.10 floor and does **not** clear the null's p95 of +0.533 — D202's
lesson 5 exactly, a delta over a wide null's mean that is not a hurdle. And the
both-symbols requirement fails outright. **H1 confirmed on ETH, and confirmed in substance
on BTC once the percentile is read beside the delta.**

The book runs at −0.0001 and −0.0015 net exposure, so this is a timing reading and not a
disguised long. The confound that made D201's best cells one multi-year long is absent by
construction here, which is the one methodological improvement this programme inherited and
actually needed.

**C5 — RSI, the control, wins.** H6 predicted at moderate confidence that a line of code
from 1978 would condition outcomes at least as well as the three structural components. It
does better than all three: after depth matching it is the only arm with a positive delta
on both symbols. Its sample is small and it fires at depth 0.796 where the placebo pool is
thin, so this is a candidate and not a finding — but the comparison it was put in the study
to make has been made, and the structural components lost it.

## What the depth effect probably is, stated as a limitation

It is very likely **not** the course's mechanism. At retracement 0.786 price has given back
most of an impulse leg, and a 5-bar move back toward the leg's direction is what
short-horizon mean reversion predicts after an extended counter-move. The deeper the
pullback, the stronger the pull.

So the honest reading is not "deep retracements are a good entry" but "the continuation
statistic at deep retracements is substantially measuring reversion, and the course's
confluence stack accidentally selects for it". Whether depth survives costs and a real exit
policy is WP4 and WP5; WP2 already showed the toll is 0.4–1.0R, which is a great deal to
pay for a 5-percentage-point edge in a 5-bar coin flip.

## What this does not close

Nothing is closed. A component can be individually null and still marginally useful, which
is exactly what WP4 asks — and `fib_depth` is now the feature every other one has to beat
rather than a control reported alongside them. That reordering is the main thing WP3 hands
forward.
