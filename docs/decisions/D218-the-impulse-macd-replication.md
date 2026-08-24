# D218 — Impulse MACD: does D217's mechanism reproduce on an independent construction?

**Status:** Pre-registered — written and committed BEFORE the runner exists
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** A user-supplied indicator (Impulse MACD, LazyBear, TradingView 2015), which on
inspection turned out to be a test of D217's finding rather than a new question

> A result section will be appended and nothing above it edited.

## What is being tested

Impulse MACD, as published. The specification, taken from the open-source Pine and
restated here so the implementation has something to be wrong against:

```
lengthMA = 34,  lengthSignal = 9,  src = hlc3

smma(x, n)  = Wilder smoothing, SMA-seeded:  s[t] = (s[t-1]*(n-1) + x[t]) / n
zlema(x, n) = e1 = ema(x, n); e2 = ema(e1, n); zlema = e1 + (e1 - e2)

hi = smma(high, 34)
lo = smma(low, 34)
mi = zlema(hlc3, 34)

md = mi > hi ? (mi - hi) : (mi < lo ? (mi - lo) : 0)     <- the dead zone
sb = sma(md, 9)
sh = md - sb
```

**It is not a MACD variant, and the name is the least reliable thing about it.** There is no
difference of two EMAs of the same series anywhere in it. It is a **zero-lag mid price
measured against a slow smoothed high/low channel, with a dead zone**, and a simple moving
average laid on top as a signal line. Structurally it is closer to this project's Donchian
breakout book than to D217's ladder.

### The algebra, worked before the run

Two exact properties decide the design, and both are pinned by test rather than asserted:

**1. `smma(x, n)` is an EMA with `α = 1/n`** — Wilder's smoothing, not the `2/(n+1)`
convention D217's EMA uses. Effective period `2n − 1 = 67`. On a linear path with slope `b`
it lags by exactly `(1 − α)/α · b = (n − 1)·b = 33b`.

**2. `zlema` has centre of mass exactly zero.** `EMA₁` lags a ramp by `(n−1)/2`, `EMA₂` by
`(n−1)`, so `2·EMA₁ − EMA₂` lags by `2·(n−1)/2 − (n−1) = 0`. The name is accurate: on a
ramp `zlema(c)ₜ = cₜ` exactly.

Put together, on constant drift `b` with no bar range:

> **`md = 33b`.**

That is the same shape as D217's **`macd = 7b`**. And since `SMA(md, 9)` converges to `33b`
too, **`sh → 0` on constant drift**, exactly as D217's histogram does.

**So this indicator decomposes the same way D217's did, on a completely different
construction: `md` is a trend-LEVEL rule, `sh` is a trend-ACCELERATION rule.** That is what
makes this worth running. D217 found — against a *high*-confidence prediction that the
algebra had settled the other way — that the acceleration rung was the only one that worked
and that every parameterisation of the level rung was dead. **This is the chance to find out
whether that was a property of trend acceleration or a property of one indicator on one
sample.**

### The ladder

| Rung | Rule | What it isolates |
|---|---|---|
| **I1** | `sh` crosses zero, i.e. `md` crosses its 9-SMA | the signal line — the taught rule |
| **I2** | `sign(md)` — the band state, dead zone included | the impulse itself, no signal line |
| **I3** | `sign(mi − smma(close, 34))` — zero-lag mid against ONE slow average | the dead zone, deleted |
| **C** | D217's R1: MACD(12,26,9) signal-line cross | the incumbent, since it is the only rung D217 found alive |

I2 and I3 differ **only** by the dead zone: I3 is the same comparison with the channel
collapsed to its midpoint. I1 is I2 with the signal line added. So the two deltas are
clean and the third comparison is against the best thing this project has already found.

The dead zone is worth quantifying rather than describing. On a ramp with average bar range
`R`, `hi = c + R/2 − 33b` and `mi = c`, so **`md > 0` requires `b > R/68`** — the drift must
exceed roughly one sixty-eighth of a bar's range per bar before the indicator registers
anything at all. That is a real, statable threshold and it is why I3 exists.

## The prior, stated before the run

**I expect this to be a negative, and the reason is arithmetic rather than judgement.**

D217 closed with a verdict noise floor of **SR0 = +0.638** annualised at the multiplicity
count this fixture now carries, and the best cell it found was **+0.496**. D218 inherits
that count and adds to it. **So an Impulse MACD arm has to clear roughly +0.64 Sharpe to
mean anything, and D217's best-ever arm on this fixture fell 22% short of that.** Nothing
about swapping a Donchian-ish channel for a two-EMA difference obviously buys that much.

Saying so now costs nothing. Saying it after the result costs credibility.

**The prediction I actually care about is not the level — it is whether the I1 − I2 delta
has the same sign and rough magnitude as D217's R1 − R2 delta (+0.285 long-short, +0.209
long-flat).** That is the replication, and it is the only thing here that could change what
this project believes.

**One thing that would make me wrong in the other direction:** the dead zone is a genuine
structural difference from anything D217 tested. A rule that stands aside in the middle of
its own range is not a rule D217 measured, and if I3 − I2 is materially negative — i.e.
deleting the dead zone *hurts* — that is a finding about hysteresis rather than about MACD,
and it would deserve its own study rather than a paragraph.

## Design

Everything not named here is D217's, unchanged and deliberately so — a replication that
alters the harness is not a replication.

| | |
|---|---|
| Fixture | `universe_daily_2015_2024_raw.csv.gz`, 57 ETFs, 2,515 daily bars, unchanged |
| Periods/year | 252.0 |
| Books | long-short flip and long-flat, separate arms |
| Statistic | one equal-weighted cross-sectional portfolio Sharpe per arm; 57 ETFs are the sample, not 57 hypotheses |
| Costs | derived per ETF from the IBKR schedule at median close + 1 bp half-spread, **per side** (D212) |
| Returns | **dividend-adjusted by default**, price-only reported beside it (D217's addendum — the bias flatters part-time-exposed arms and this study has a rung that is flat by construction) |
| Fill | the same `lag=1` primary with the `lag=2` bracket, and for the same reason |
| Warm-up | the ladder's common start, max across all four rungs including C |
| Nulls | rotation (primary) and block shuffle, 400 sims, seeded |

**The dead zone makes exposure a variable rather than a constant, and that has to be handled
up front.** I2 is flat whenever `lo ≤ mi ≤ hi`, so it will be out of the market a large
fraction of the time by construction. Sharpe rewards that and total return punishes it —
which is exactly the trap D217's addendum documented. **Every arm therefore reports exposure,
dividend-adjusted total return and CAGR beside its Sharpe, and no arm is described as beating
buy-and-hold without naming the metric.** That rule is D217's addendum, applied at design
time instead of after.

### Arms and the ledger

| Block | Cells | Looks |
|---|---|---:|
| The ladder | 4 rungs (I1, I2, I3, C) × 2 books × {gate off, on} | **16** |
| Sensitivity | `lengthMA ∈ {21, 34, 55}` on I1 and I2, long-short, gate off, minus the 2 already counted | **4** |
| **Total, fresh** | | **20** |

The sensitivity grid is deliberately small: D217 already established that this indicator
family's parameter surface is flat and mid-distribution, and re-establishing it would buy
looks rather than knowledge. **`lengthMA` is checked at three values only, to answer
whether 34 is special, and the grid is not extended later.**

### Multiplicity — and this study does NOT get a fresh ledger

D217 argued a fresh ledger on three grounds: different fixture, different claim family, a
sensor that did not exist here. **None of those hold now.** Same fixture, same claim family,
and the sensors are close cousins. So:

**D218 inherits D217's 42 fresh looks in full**, plus its own 20, plus the 45,346 distinct
prior ETF-fixture configurations, plus the disclosed 395. Verdict count **45,803**. The
noise floor moves by almost nothing, because 62 looks against 45,741 is noise — and that is
itself the point: *this fixture is exhausted, and the honest response is to say so before
the run rather than discover it in the verdict.*

The raw registry row ceiling, 129,286, is reported and is **not** used as an N (D98/D116/
D126/D142).

## The hurdles

D217's, unchanged, because changing hurdles between a study and its replication is how
replications stop meaning anything.

**A.** I1 − I2 ≥ **+0.10** Sharpe and I2 − I3 ≥ +0.10, each above the paired bootstrap's p95.
**B.** Beat the matched rotation null by ≥ +0.10, above p95.
**C.** Beat the block-shuffle null by ≥ +0.10, above p95.
**D.** Long-flat arms beat buy-and-hold — **on Sharpe AND on dividend-adjusted total return,
both reported, and the cell is only a survivor if it clears both.** D217 left the metric
unnamed and had to disclose the second reading afterwards; naming both now is the fix.
**E.** n ≥ 100 signals pooled and ≥ 30 entries per ETF, else underpowered and no verdict.
**F.** Same sign in both chronological halves.
**G.** Sharpe clears the DSR floor at the verdict count.

Every delta reported with its null percentile beside it.

## Pre-committed stops

- A failing no-look-ahead test on `smma`, `zlema` or `md` blocks everything downstream.
- The dead zone leaving I2 under 30 entries per ETF makes it underpowered — **and that is a
  reportable finding about the indicator, not a reason to widen anything.**
- **If no cell clears A–G, this closes as a reportable negative and no engine stage runs.**
- No scope additions mid-study. New ideas go to the parking lot.

## Predictions, committed now

| | Prediction | Confidence |
|---|---|---|
| **J1** | No cell clears all seven hurdles; the study closes negative | **high** |
| **J2** | **I1 − I2 > 0 with the same sign as D217's R1 − R2** — the acceleration rung beats the level rung again | **moderate-high** |
| **J3** | I1 − I2 is *smaller* than D217's +0.285, because the dead zone already removes some of the chop the signal line was earning against | **moderate** |
| **J4** | I2 (the level rung) fails to beat its rotation null, reproducing D217's dead zero-line rung | **moderate-high** |
| **J5** | The dead zone helps on Sharpe and hurts on total return — I2 beats I3 on Sharpe while earning less money — the exposure trap D217's addendum documented | **moderate** |
| **J6** | Impulse MACD does not beat D217's plain MACD signal-line cross (C) on either book | **moderate** |
| **J7** | `lengthMA = 34` is unremarkable within {21, 34, 55} | **moderate-high** |

**J2 is the one to watch.** It is the only prediction whose outcome changes what this
project believes rather than what it believes about one indicator. If the
acceleration-beats-level result reproduces on a construction that shares no arithmetic with
MACD, that is a real finding about trend rules and it earns its own pre-registration on a
fixture that is not exhausted. If it does not reproduce, D217's headline was a coincidence
with a good story, and I would rather find that out here than in a writeup.

**J1 at *high* is a bet on the noise floor, not on the indicator** — and D217 is the record
of what happens when I stake *high* on arithmetic settling a question.

## The rule if it works, committed now

Unchanged from D215/D217: a surviving cell is a positive claim, does **not** get pursued
inside this study, and gets its own pre-registration and its own holdout. And given the
verdict count, an additional clause specific to this fixture:

> **A positive here does not get a follow-up on this fixture at all.** At 45,803 looks the
> ETF universe can no longer distinguish a good result from the best of its own noise. Any
> replication moves to data this project has not already mined — the crypto daily universe
> is the candidate — or it is not a replication.

## What would change my mind

**J2 failing.** If the acceleration rung does *not* beat the level rung on this
construction, then D217's central finding does not generalise past the indicator it was
found on, and the correct response is to say so in the D217 record rather than let it stand
as a general claim about trend rules.

Secondarily: J5 failing in the direction where the dead zone helps *both* Sharpe and total
return. That would make hysteresis a real effect rather than an exposure artifact, and it is
the one result here that would deserve a study of its own.
