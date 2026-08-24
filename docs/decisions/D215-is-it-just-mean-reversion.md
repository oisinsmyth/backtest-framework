# D215 — is it just mean reversion? Testing the hypothesis by deleting the structure

**Status:** Pre-registered — written and committed BEFORE the runner exists
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
