# D209 — the stop was on the wrong side of the trade, and a guard hid it as missing trades

**Status:** Committed — a defect, found and corrected before WP4's verdict
**Date:** 2026-08-24
**Category:** Execution / fill logic
**Source:** WP4's first run, where the fully-stacked arm produced 2 trades from 120 setups

## The defect

`stop_distance` measured to **`leg.end_price`** — the extreme the impulse leg ran *to*.

After a bullish change of character the leg runs from a swing **low** up to a swing
**high**, and the entry is on the pullback *down* from that high. A long stop therefore has
to sit **below** the entry. `leg.end_price` is the high, **above** it. That is not a stop; it
is a target with the sign flipped.

The correct level is `leg.start_price`, the extreme the leg came *from*. The course says it
plainly for the bullish case — *"we can start to set ourselves up to be able to risk
underneath that low"* — and it coincides exactly with the invalidation rule, since
`retracement == 1.0` **is** `leg.start_price`. The stop and the line that kills the setup are
the same line. That coherence is what makes the corrected reading obviously right and was
the clue the first one was wrong.

## How it hid

`run_arm` has a guard refusing a stop on the wrong side of the entry, because an unguarded
division there produces an infinite R multiple rather than an error. The guard worked
perfectly and **that is the problem**: it converted a wrong answer into a *missing* one.

Measured after the fact: of 2,000 setups, the wrong-side stop rejected **1,865 and kept 135**.
The survivors were the setups where price had barely pulled back — depth at or below zero —
so the 7% that got through were not a sample of the strategy, they were an adversely
selected sliver of it.

**This is D205's finding for the third time.** An invariant asserted only over the outputs a
component produces cannot see a component that has stopped producing them. D205 caught it in
a mirrored state machine, D206 in an `if window:` that dropped 9% of setups uncounted, and
here in a guard doing exactly what it was written to do.

The tell that surfaced it was not a test. It was a **count that did not match another
count**: the census said 120 fully-stacked setups and the lattice reported 2 trades. Two
numbers that should have agreed and did not.

## What it changed

WP2's friction table was wrong in both magnitude and direction. WP3 is untouched — it uses
no stops.

| | superseded | corrected |
|---|---:|---:|
| base-arm median stop, BTC | 1.04 ATR | **2.14 ATR** |
| base-arm friction, BTC / ETH | 0.97R / 0.72R | **0.48R / 0.34R** |
| required hit rate at 5R, BTC / ETH | 32.9% / 28.6% | **24.7% / 22.3%** |
| stacked-arm friction, BTC | 0.59R | **0.71R** |

And one finding reversed. The superseded census said the confluence stack *widens* the stop
and roughly halves the friction. It does the opposite: risk is `(1 - retracement) x |leg
span|`, so a deeper entry is a **tighter** stop, and stacking the filters raises friction from
0.48R to 0.71R on BTC. **The confluence the course sells as precision is, in cost terms, a
tax** — it buys a better price by risking less, and the fixed spread then eats a larger share
of what is left.

The corrected conclusion is unchanged where it matters and is now better supported: the
course claims a 5R target breaks even at ~20%, and the true break-even at 40 bps is 22.3% to
28.4%.

## What was done about it

- `stop_price` is now its own named function with the geometry written out, so the next
  reader meets the reasoning before the number.
- Two tests pin it: one asserting the stop sits on the far side of the entry **in both
  directions** across the real setup population, and one asserting
  `stop_distance == (1 - retracement) x |span|`.
- The WP2 section carries a generated correction banner naming the superseded figures, so
  the ledger records the change rather than quietly showing new numbers under an old
  heading. The banner is generated from the artifact for the same reason the prose is
  (D176/D183/D186).

## The rule this suggests

Guards that refuse bad input are right and should stay. But **a guard's rejection count is a
number, and an uncounted number is an unchecked one.** `SetupPopulation` already returns its
drops explicitly because of D206; `run_arm` did not, and the defect lived in exactly that
gap. The general form, now three for three:

> When a guard drops something, count what it dropped and put the count where someone will
> compare it to another count.
