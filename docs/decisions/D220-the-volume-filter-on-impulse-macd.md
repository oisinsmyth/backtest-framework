# D220 — Can volume tell Impulse MACD which of its trades are the bad ones?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user proposal — filter out the arm's bad trades, be in the market less,
keep the good ones

> A result section will be appended and nothing above it edited.

## What is being tested

D218's best cell, `I1_signal` long-flat, plus a condition on **volume at the entry bar**
that decides whether the trade is taken at all.

The claim is a selectivity claim and it is stated in trade terms, not portfolio terms:

> **A volume condition specified in advance removes trades that go on to lose at a higher
> rate than it removes trades that go on to win.**

Everything else — Sharpe, total return, exposure — is a consequence. If the trade-level
statement is false, an improvement in any portfolio number is arithmetic luck about which
particular trades got dropped, and the runner has to be able to tell the difference.

## The prior, measured before the design was fixed

**Filter-agnostic. Volume is deliberately not looked at anywhere in this section** — the
relationship between volume and trade outcome is the hypothesis, and measuring it before the
pre-registration is written would make the pre-registration worthless.

### The trade census

| | |
|---|---:|
| trades | 2,418 (7.1 per ETF per year) |
| **win rate** | **44.4%** |
| mean win | +6.02% |
| mean loss | −2.84% |
| median hold | 14 bars |
| sum of winners / losers | +62.68 / −38.77 log |

**A majority of this arm's trades lose.** It earns its return on a 2.1:1 payoff ratio, not on
hit rate. That matters for the design: there is a large population of losing trades available
to remove, so the proposal is not fighting the base rate. An earlier guess that a long-flat
arm in a rising universe would be mostly winners — and therefore that any filter must cut good
trades — is **wrong**, and it is recorded here because it was the reason this study was nearly
argued out of existence.

### The two bounds that bracket any filter

| remove | ORACLE Sharpe | ORACLE total | exposure | RANDOM matched, p5..p95 Sharpe | RANDOM total |
|---:|---:|---:|---:|---:|---:|
| 0% | +0.793 | +52.12% | 49.9% | — | — |
| 10% | **+1.503** | +109.47% | 47.2% | +0.737..+0.840 | +41.5..+50.1% |
| 20% | +1.871 | +144.35% | 44.9% | +0.723..+0.862 | +35.8..+45.1% |
| 30% | +2.126 | +170.12% | 42.6% | +0.684..+0.880 | +28.2..+39.8% |
| 50% | +2.451 | +198.82% | 37.2% | +0.621..+0.911 | +17.8..+28.6% |

**ORACLE** removes the worst k% of trades ranked by realised PnL. It is look-ahead by
construction, is never presented as a strategy, and exists only to bound the space. D181 is
the standing distinction: the look-ahead guard binds strategies, not analytics, and this is an
analytic bound with the word ORACLE on it in every table it appears in.

**RANDOM** removes the same *count* at random. This is the correct null for a selectivity
claim because it is matched on exactly what a filter does — remove n trades — so a delta over
it cannot be explained by having traded less.

Two things follow that shape the whole design:

1. **The oracle at 10% removal is +1.503, which clears the +1.420 verdict floor.** This is the
   first construction in this programme with headroom above its own noise floor. The standing
   claim that this fixture is exhausted was a claim about *arms* and does not transfer to
   *filters*. It remains true that the oracle is unreachable.
2. **Removing 10% of trades removes only 2.7 points of exposure**, so losing trades are
   materially *shorter* than winning ones. Any filter therefore removes less exposure than
   trade count, and exposure reduction is a weak proxy for selectivity.

## The arms

The volume condition is evaluated on the **entry bar only** and decides whether that trade is
opened. It never closes a trade early — that would be a different hypothesis (an exit rule)
and is out of scope.

| | condition at entry | the claim it encodes |
|---|---|---|
| **V1** | `volume > mean(volume, N)` | the textbook one: volume confirms the move |
| **V2** | `volume < mean(volume, N)` | the contrarian one: quiet entries are the good ones |
| **V3** | `mean(volume, N) > mean(volume, N)` one bar earlier | participation is building, level irrelevant |

`N` ∈ {20, 50}. **Both directions are declared** because testing only V1 leaves "we should
have tried it the other way" available after a failure, which is not a hurdle, it is an
escape. Both are counted.

Books: long-flat and long-short, as every prior study in this line has run them.

**6 filter configurations × 2 books = 12 fresh looks.** The grid is declared here and is not
extended later. No scope additions mid-study; new ideas go to the parking lot.

## Hurdles

The D219 dual verdict applies in full — **standalone A–G and in-portfolio P1–P5, reported side
by side, neither allowed to replace the other.** D220 adds one hurdle specific to filters:

**H. Selectivity.** The filter must beat the **matched-count random null** at or above the
95th percentile on **both** Sharpe and total return, *and* the mean PnL of the trades it
removed must be below the mean PnL of the trades it kept at p95 of a permutation test on the
trade labels.

H is the hurdle that decides the study. A filter can improve Sharpe purely by removing
exposure from a book whose marginal exposure is unprofitable, and that is not selectivity —
the random null is matched on count precisely so that this shows up as a failure.

**The capture ratio is the headline number:**

```
capture = (filter - random_median) / (oracle - random_median)
```

What fraction of the available space the filter actually took. Reported for Sharpe and for
total return, at the filter's own removal count so the oracle is matched to it.

## Predictions, committed before the run

| | Prediction | Confidence |
|---|---|---|
| **L1** | V1, the textbook confirmation rule, does **not** clear hurdle H | **moderate-high** |
| **L2** | No cell reaches a capture ratio of 20% on either metric | **moderate-high** |
| **L3** | Every filtered arm correlates **> 0.85** with its unfiltered parent and therefore fails P4. A filter can only remove exposure, so its return stream is a sub-sample of its parent's and high correlation is structural rather than empirical | **high** |
| **L4** | No cell clears both verdicts | **high** |
| **L5** | V1 and V2 do not both fail — one of the two directions will look better than random, because they are near-complements and the sample is finite. **This is the prediction that matters**, because a single direction looking good is exactly what 12 looks buys you by chance, and hurdle G is what it has to survive | **moderate** |

**What would change my mind:** L1 failing — V1 clearing H on both metrics and both books, with
a capture ratio above 20%. That would mean the oldest claim in technical analysis carries real
information on this universe, which contradicts the 200-MA gate precedent, where the one
filter already tested on this exact arm took Sharpe from +0.793 to +0.454 and 40 points off
the return.

## Ledger

| block | looks |
|---|---:|
| filters — 3 conditions × 2 windows × 2 books | **12** |
| **fresh, D220 only** | **12** |
| inherited from D217 + D218 | 62 |
| disclosed prior ETF-fixture configurations + structure/terrain bar | 45,741 |
| **verdict count** | **45,815** |

**Zero-look items, stated explicitly:** the trade census (a census is not a test), the oracle
bound (an upper bound is not a hypothesis), the matched random null and the unfiltered parent
(a null is the yardstick for a look, not an additional look), and the capture ratio (a
rescaling of numbers already counted).

## Pre-committed stops

- **The volume data gate.** Volume is present in the fixture and clean — 143,355 bars, zero
  zero-volume bars — but `load_panel` does not currently carry it. If plumbing volume through
  changes any existing published number by more than floating-point noise, everything stops
  until that is explained, because it would mean the loader change altered the price path.
- **The census gate.** Any cell whose filter leaves fewer than 30 entries per ETF is
  **underpowered and carries no verdict** (D216, WP2), and a filter that removes most of the
  book will trip this before it can look good.
- **The programme stop.** If no cell clears H, the study closes as a reportable negative and
  no volume work continues on this fixture. A cell that clears H but fails the dual verdict is
  reported as exactly that and still gets no follow-up here.
- **ETF volume is a weak instrument and it is disclosed now, not later.** ETF liquidity comes
  from the creation/redemption mechanism and the underlying basket, so on-exchange volume is a
  poor proxy for interest — a quiet tape can simply mean the authorised participants did not
  need to trade. A negative result here is therefore **weaker evidence against volume as a
  concept** than the same result would be on single names or crypto, and the report must say
  so where the verdict is rather than in a footnote.
