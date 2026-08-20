# D144 — A peg screen was added to the universe policy after its first run, and the amendment is recorded rather than hidden

**Status:** Committed
**Date:** 2026-08-18
**Category:** Data layer
**Source:** Breakout universe session

## Decision

`UniversePolicy` gains a fourth clause: **median absolute daily log return ≥ 0.5%**. A
symbol below it is excluded with the reason "a pegged instrument is not a trend-following
candidate (peg screen)".

This clause was **not** in the policy as first written. It was added after the first study
run, and this record exists so that fact is on the page rather than in a commit message.

## What happened

The policy's first version screened for positive prices, minimum history and liquidity —
all tradability and data-adequacy rules, none of which look at an outcome. It admitted
`UST-USD`, TerraUSD, which reached the roster through the `sought_failures` cohort because
its depeg is one of the defining crypto failures.

TerraUSD is a **stablecoin**. Over its out-of-sample span it was pinned at $1 and then fell;
it never printed a 40-bar high, so the strategy never entered, its return series was
identically zero, and its annualised Sharpe was not merely bad but **−∞** (excess return is
a negative constant, sample standard deviation is zero). The study raised, loudly, from the
guard in `_dsr_for` — a non-finite Sharpe in the trial pool is neither imputed nor dropped
(D98, [D142](D142-dsr-pool-is-the-cross-section.md)).

## Rationale for fixing it in the policy rather than at the DSR

Three options existed and two are wrong:

- **Impute or drop the metric.** Imputing distorts V, dropping distorts N. This is exactly
  the bug D98 fixed one level up, and re-introducing it here would be indefensible.
- **Select the DSR pool around it.** The pool would then be selected on a property of the
  result, which D98 forbids in as many words: the predicate must select on config/identity
  fields, never on presence of the metric.
- **Fix the universe policy**, which is what the gap actually was. The policy had no clause
  answering "is this instrument a candidate for trend following at all". A pegged
  instrument is not — not because it performs badly, but because the strategy is undefined
  on it. That is a definitional requirement of the same kind as "prices must be positive",
  and it belongs in the same list.

## Why the threshold cannot be doing any work

The honest risk in a post-hoc rule is that its threshold is tuned to change a result. Here
nothing could plausibly turn on it: the pegged series sits at **0.14%/day**, and the least
volatile *real* asset in the universe — BTC — sits at **1.42%/day**. The threshold is 0.5%,
a factor of 3.5 above the peg and a factor of 2.8 below the nearest real asset, in an
empty gap an order of magnitude wide. `USTC-USD` — the same token after it depegged and
began floating — sits at 1.52% and stays in the universe, in the collapsed bucket where it
belongs.

The amendment was made **before any performance number in this study had been read**: the
only output seen at that point was the raised exception and the fact that the symbol had
zero trades. That claim is checkable against the sequence of events recorded here, and it
is the reason this record exists at all — a policy amended silently after seeing results is
worthless as a pre-statement, whatever its threshold.
