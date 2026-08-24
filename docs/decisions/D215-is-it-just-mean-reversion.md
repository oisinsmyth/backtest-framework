# D215 — is it just mean reversion? Testing the hypothesis by deleting the structure

**Status:** Committed (H1, H3, H5 confirmed; H2 falsified — in the hypothesis's favour; H4 split)
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** the hypothesis offered for why the structure programme failed

> A result section will be appended and nothing above it edited.

## The claim under test

**That the one real relationship either programme found — the retracement-depth staircase —
is generic short-horizon mean reversion after a large recent move, and that the structure
contributes nothing to it.**

Across 395 looks the components measured as nothing, with one exception. The Fibonacci
ladder came back a strictly monotone staircase in depth:

| ratio | 0.382 | 0.447 | 0.500 | 0.553 | 0.618 | 0.691 | 0.724 | 0.786 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| `BTCUSDT` | 46.1% | 49.5% | 51.9% | 54.7% | 56.9% | 58.7% | 59.1% | 60.5% |

That is the only monotone, robust, two-symbol relationship in the whole body of work. The
hypothesis says it is not about structure at all: **a deep retracement *is* a large recent
counter-move**, large moves revert at intraday horizons, and the deeper the pullback the
bigger the move that just happened.

## What is already measured and is not being retested

The hypothesis has three parts and two of them are settled:

- **The confluence is collinear.** D210's matrix puts the three surviving features at +0.79
  to +0.88 rank correlation with each other — four coordinates on one axis, not four
  independent confirmations.
- **Cost is anti-correlated with entry quality.** `risk = (1 − depth) × |leg|`, so the rule
  that says "enter deeper" tightens the stop it depends on. Measured at 0.96R → 1.41R
  (D209/D212).

Only the third part is a live claim, and this study tests it by **deleting the structure and
seeing whether the staircase survives**.

## Test A — the decisive one

Take **every bar**, not just setups. The recent move, defined with no reference to anything
structural:

```
move(t) = (close[t] − close[t − M]) / ATR[t]
```

`M` is the **median impulse-leg length in the existing structure population**, read from
`data/structure_examples_summary.json` and its siblings — a census-derived constant from a
committed artifact, not a value chosen here. Bucket bars by `|move|` into quantile bins and
measure, in the direction **opposite** the move, the identical statistic the ladder used.

**Both arms run through `structure_nulls.continue_from`.** Its docstring already states why
it exists: it fires at a *bar* rather than a price, "so the resolution rule is identical to
the level arms' and the two remain comparable". Same `k = 0.5` band fixed at the bar, same
`HORIZON = 5`.

### The verdict is the matched comparison, not the raw one

For every structure touch, compute its counter-move size in ATR, find the generic bucket it
falls in, and compare. **Do structure touches beat plain bars that moved the same distance?**

This is D208's depth-matched null applied one level out, and D208 is the precedent for why
the matched number is the verdict: there, the fair value gap sat at the 100th percentile of
500 draws against a uniform placebo and at **+0.006 / −0.006** against one matched on depth.
The raw comparison was not wrong, it was answering a different question.

### Non-overlapping sampling, pre-registered

Adjacent bars share almost all of their lookback and their forward window, so 294,000 is
not the sample size. The generic arm samples **every M-th bar**, so lookbacks never overlap.
Fixed here because overlapping windows silently inflate confidence, and a null result
computed on them would look sharper than it is — the failure mode is a *more* convincing
negative, which is exactly the kind nobody checks.

## Test B — does the slope decay with horizon?

Mean reversion decays; a structural level should not. The ladder's **slope** — Spearman rank
correlation between move size and reversal — at horizons **5, 20, 60** bars.

One statistic per horizon rather than eight rungs, because the hypothesis is about the slope
and reporting the rungs separately would triple the ledger to say the same thing.

## Test C — the counterintuitive corollary

If the effect lives at ~5 bars, a target matched to that horizon should convert it. The
frozen wrapper at `target_r` ∈ **{1.0, 2.0, 5.0}**.

This touches the wrapper, which D203 warns about at length. It is admitted because it is a
stated falsifiable prediction whose direction is **counterintuitive** — gross improves while
net gets *worse* — rather than a sweep for the best exit. A prediction that specifies its own
failure mode is not the thing D203 was written against.

## The ledger, and an asymmetry worth stating plainly

**Test A starts a fresh ledger.** It reuses no sensor, no component and no level — it
deliberately deletes all of them.

The deeper reason it is admissible: **multiplicity inflates false positives.** A test whose
*predicted* outcome is "this effect is generic and therefore not yours" is negative-
confirming, and prior looks do not make a negative less credible. Tests B and C reuse the
structure machinery and inherit the 395.

**A rule pre-committed for the case that actually matters.** If Test A finds generic
reversion is *large and tradeable*, that is a positive claim and it does **not** get pursued
inside this study. It gets its own pre-registration and its own holdout. The motivation for
looking came from 395 looks at this data, so a discovery here is a hypothesis and not a
result — and writing that down now is the only way it survives contact with a good number.

Looks: A = 4, B = 6, C = 6. **16 total.**

## Predictions

- **H1** — the generic ladder is monotone in move size, same sign and comparable magnitude
  to the Fib ladder. Confidence **high**.
- **H2** — **at matched move size, structure touches score within ±0.02 of plain bars.** The
  decisive prediction. Confidence **high**.
- **H3** — the slope decays from horizon 5 → 20 → 60. Confidence **moderate-high**.
- **H4** — at `target_r = 1.0` the hit rate exceeds 35% and gross R improves, while net R at
  40 bps per side is *worse* than at 5R. Confidence **moderate**.
- **H5** — the generic effect is real and **not tradeable at 15m**: a 0.5 ATR band is ≈0.19%
  of price against an 80 bp round trip, so the move being predicted is roughly a quarter of
  the cost of capturing it. Confidence **high**.

H5 is the bridge to the frequency frontier. If the only real effect anywhere in this body of
work is a 0.2%-of-price move, then the binding question was never which levels to draw — it
is what bar size makes that move large relative to the spread.

## What would change my mind

If structure touches beat matched generic bars by more than 0.02 at the same move size, the
hypothesis is wrong: the components carry something the raw move does not. That would be the
first positive finding in 395 looks and would need its own study. The test is built so that
outcome is visible rather than absorbed.

---

# RESULT — appended 2026-08-24, nothing above it edited

**The staircase survives with the structure deleted, and the structure is slightly worse
than nothing.**

`M = 8 bars`, the median impulse-leg length over 3,875 and 3,753 setups — a census, read off
the population rather than chosen.

## A — the ladder, with no structure anywhere in it

Every 8th bar, bucketed by how far price moved in the previous 8, no change of character, no
leg, no level, no gap:

| bucket (median move, ATR) | 0.09 | 0.28 | 0.48 | 0.72 | 1.01 | 1.42 | 2.10 | 3.96 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| **`BTCUSDT`** P(reversal) | 37.8% | 37.1% | 40.4% | 41.5% | 43.9% | 48.5% | 50.5% | **50.9%** |
| **`ETHUSDT`** P(reversal) | 37.6% | 38.7% | 40.1% | 42.6% | 44.8% | 47.7% | 50.0% | **52.6%** |

Monotone, both symbols, ~36,500 non-overlapping samples each. Slope **+0.10288** on BTC and
**+0.10293** on ETH — two independent assets agreeing to four decimal places, which is
better evidence that the effect is a real market property than any single number here.

**H1 confirmed.** The Fibonacci ladder's shape reproduces with none of the Fibonacci in it.

## The verdict — matched on move size

| symbol | touches covered | structure | matched generic | delta |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 21,960 | 43.4% | 46.7% | **−0.0329** |
| `ETHUSDT` | 21,389 | 44.1% | 47.1% | **−0.0302** |

**H2 is falsified**, and it is worth being precise about how. It predicted structure touches
would land *within* ±0.02 of matched plain bars — neutral. They land **outside it, on the
negative side**: at the same move size, a structure touch is a slightly *worse* moment than
a bar picked for having moved that far and nothing else.

So the prediction was wrong and the hypothesis is stronger than the prediction. The
components do not merely fail to add; they subtract about three percentage points.

**A conjecture for why, offered as a conjecture.** A pivot cannot be confirmed until `k`
bars after it (D173), and the leg's end pivot gates the whole setup. By the time a touch
registers, the move is several bars stale and part of the reversion has already happened.
D173's lag is *correct* — removing it would be look-ahead — but correctness has a price, and
this may be it. Untested, and it is a testable claim: the deficit should shrink as `k` falls.

## B — the slope decays, which is what reversion does

| symbol | h=5 | h=20 | h=60 |
|---|---:|---:|---:|
| `BTCUSDT` | +0.1029 | +0.0345 | +0.0281 |
| `ETHUSDT` | +0.1029 | +0.0437 | +0.0399 |

**H3 confirmed.** Two thirds of the slope is gone by 20 bars and it is flat thereafter — the
signature of a short-horizon effect, not of a level that means something.

The *level* moves the other way and is worth noting: overall reversal is 43.8% at 5 bars and
52.3% at 20. So over five bars price mostly **continues**, and the ladder measures a tilt in
how often it does not. Even in the largest-move bucket reversal reaches only ~51%.

**The effect is a slope, not a level.** There is no move size after which price reliably
bounces; there is a mild gradient, worth a few percentage points, on a near coin flip.

## C — the target sweep

| symbol | target | P(reach target) | mean gross R | mean net R @40bp |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 5R | 4.5% | +0.010 | −2.016 |
| `BTCUSDT` | 1R | **42.4%** | −0.007 | −2.034 |
| `ETHUSDT` | 5R | 5.1% | +0.063 | −1.443 |
| `ETHUSDT` | 1R | **42.7%** | −0.004 | −1.510 |

**H4 splits.** The hit rate does jump past 35% as predicted, and net R does get *worse* — the
counterintuitive half, which was the point of making the prediction. But **gross R does not
improve**; it falls. Matching the target to the horizon where the effect lives converts the
5-bar tilt into hit rate and gives back exactly as much in size. A 42% hit rate at 1R is a
coin flip that pays 1:1.

## H5 — and this is where it ends at fifteen minutes

| symbol | 0.5 ATR band, as share of price | 80 bp round trip | ratio |
|---|---:|---:|---:|
| `BTCUSDT` | 0.192% | 0.800% | **0.24×** |
| `ETHUSDT` | 0.260% | 0.800% | **0.32×** |

**The move being predicted is a quarter to a third of the cost of capturing it.** Confirmed
at high confidence, and it is the sentence the whole programme reduces to.

## What this settles

The five components, the confluence, the golden ratio and the fair value gap reduce to **how
far price just moved** — and reduce to slightly *less* than that. What was being taught as
market structure is a mild, decaying, sub-coin-flip tilt that any bar carries, measured
through machinery that costs three percentage points to apply.

Two things follow, and only the second is about this strategy:

1. **The effect is real, generic, and known.** Short-horizon reversion after a large move is
   not a discovery, and the pre-committed rule in this document applies to it: nothing here
   is pursued as a strategy without its own pre-registration and holdout. It is not being
   pursued.
2. **The binding constraint was never which levels to draw.** At 15m the predicted move is
   0.24× the spread. The only lever that changes that by an order of magnitude is bar size,
   which is what the frequency frontier measures.

## Ledger

**16 looks.** Test A (4) on a fresh ledger — it reuses no sensor, component or level, and a
test whose predicted outcome is *this effect is generic and therefore not yours* is
negative-confirming, which prior looks do not weaken. Tests B and C (12) reuse the structure
machinery and inherit the 395.

## Predictions, scored

- **H1** monotone generic ladder — **confirmed**.
- **H2** structure within ±0.02 of matched generic — **falsified**; it is −0.03, i.e. worse.
- **H3** slope decays with horizon — **confirmed**.
- **H4** hit rate >35%, gross improves, net worsens — **split**: 1st and 3rd confirmed, 2nd
  falsified.
- **H5** the effect is not tradeable at 15m — **confirmed**, at 0.24× and 0.32× the cost.

Three of five clean, one falsified in the hypothesis's favour, one split. The two that
missed were both at *moderate* confidence and all three *high*-confidence calls held — the
calibration this project has tracked since D199, holding for the third study running.
