# D218 — Impulse MACD: does D217's mechanism reproduce on an independent construction?

**Status:** Committed (J1, J2, J4, J6, J7 confirmed; J3 and J5 falsified)
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

---

## RESULT

*Appended after the run. Nothing above this line was edited.*

**Produced:** 2026-08-24 · **Reproduce:** `uv run python scripts/run_impulse_macd.py`
(offline, deterministic, seed 0) · Ledger: [`MACD_RESULTS.md`](../results/MACD_RESULTS.md) ·
Artifact: `data/impulse_macd_summary.json`

### The one-sentence version

**D217's mechanism replicates — the acceleration rung beats the level rung again, on a
construction sharing no arithmetic with MACD — but the clean read is that the two
indicators' acceleration rungs are interchangeable to within 0.04 Sharpe, the level rung is
not merely dead but anti-predictive, the dead zone hurts on both metrics, and nothing clears
anything.**

### Scoring my own predictions

| | Prediction | Outcome |
|---|---|---|
| **J1** | No cell clears all seven hurdles; closes negative | **CONFIRMED.** 0 of 16 |
| **J2** | I1 − I2 > 0, same sign as D217's R1 − R2 | **CONFIRMED.** +0.628 long-short, +0.529 long-flat, against D217's +0.285 and +0.209. Same sign, clears the hurdle — *with the magnitude caveat below* |
| **J3** | I1 − I2 *smaller* than D217's, because the dead zone already removes some chop | **FALSIFIED, and backwards.** It is more than **twice** as large, and the reason is the opposite of the one I gave: the dead zone does not clean up I2, it makes I2 worse |
| **J4** | I2 fails to beat its rotation null | **CONFIRMED, and then some.** I2 sits at the **0.0, 0.0, 0.2 and 0.8th percentiles** of its own null — it does not fail to beat the null, it is beaten by essentially every rotation of itself |
| **J5** | The dead zone helps Sharpe and hurts money — the exposure trap | **FALSIFIED.** I2 − I3 is negative on all four cells (−0.016 to −0.032) **and** I2 earns less than I3 (+14.34% against +17.61% long-flat). The dead zone hurts both metrics. It buys nothing |
| **J6** | Impulse MACD does not beat D217's plain 12/26/9 signal-line cross | **CONFIRMED.** I1 − C = −0.038, −0.042, +0.008, −0.096 |
| **J7** | `lengthMA = 34` unremarkable within {21, 34, 55} | **CONFIRMED.** I1 gives +0.124 / +0.010 / −0.132 — 34 is the middle of a monotone decline, and the published default is not special |

**Five confirmed, two falsified.** That is a far better record than D217's one-in-seven, and
it should be discounted accordingly: **these predictions were written after D217 taught me
the mechanism.** A good score on a replication whose mechanism you already understand is
expected, not evidence of anything.

### What is actually true

**1. The replication holds in sign, and the magnitude is not what it looks like.**

I1 − I2 is +0.628 where D217's R1 − R2 was +0.285. It would be easy to report that as *the
effect is twice as strong on Impulse MACD*, and it would be wrong. **A large delta can be
manufactured two ways: by the top rung being good, or by the bottom rung being bad.**

Here it is mostly the second. **I1 − C — this indicator's acceleration rung against D217's,
on identical bars — is −0.038, −0.042, +0.008 and −0.096.** Approximately zero. A Wilder
high/low channel, a zero-lag mid of `hlc3`, and a dead zone buy **nothing** over
`EMA(12) − EMA(26)` and a 9-EMA of it. The two accelerations are the same measurement.

So the honest statement of the replication is stronger than "the delta reproduced":

> **Two trend-acceleration rules built from unrelated arithmetic agree with each other to
> within 0.04 Sharpe, while both of their trend-level counterparts are dead. The result is
> about acceleration versus level, not about either indicator.**

**2. The level rung is anti-predictive, which is a stronger claim than D217 could make.**

D217's zero-line rung was *dead* — eight sweep cells between −0.166 and +0.080, hovering
around its null. Impulse MACD's band state is worse than that: **−0.265 Sharpe long-short,
at the 0.0th percentile of its own rotation null.** Rotating the position series to point at
the wrong bars beats it almost every time. And the sensitivity block is unanimous: I2 scores
−0.542, −0.755, −0.343 at lengths 21, 34, 55.

Being reliably wrong is information, but not the useful kind here: the natural response —
invert it — is a new hypothesis needing its own pre-registration, and it is not taken.

**3. The dead zone buys nothing, on either metric.**

I predicted the classic trade: less exposure, better Sharpe, less money. It does not do
that. I2 − I3 is negative on all four cells while I2 also earns less than I3. Cutting
exposure from 60.6% to 54.6% removed *good* exposure along with bad. **The hysteresis that
is the indicator's most distinctive feature is its most useless one.**

**4. Nothing clears anything, and this time the arithmetic said so first.**

The best cell — `I1 / long_flat / no gate` at **+0.658** Sharpe, the highest number this
project has produced on this fixture — fails on three of the seven hurdles:

- **A**, because I2 − I3 is negative, so the ladder does not hold together;
- **D**, because on dividend-adjusted money it earns **+52.12%** against buy-and-hold's
  **+62.59%**. It beats the benchmark on Sharpe (+0.658 against +0.333) at a third of the
  drawdown and still loses 10 points of return. **Naming both metrics up front is what
  turned that into a `no` in the table rather than an addendum two days later**;
- **G**, because the floor at the verdict count is **+1.420** and nothing here is close.

**0 of 16 cells clear every hurdle.** The pre-registered stop applies.

**5. The fixture is exhausted, and it is now visible in the arithmetic rather than argued.**

The three counts: **20** fresh (SR0 = +0.640), **62** with D217's inherited (+0.794),
**45,803** combined (**+1.420**). Sixty-two new looks against 45,741 existing ones move the
floor from +0.794 to +1.420 — and it is the *inherited prior*, not this study, that does
almost all of that. **No arm anyone runs on this universe can clear +1.42.** That is not a
statement about Impulse MACD; it is a statement that this fixture has nothing left to say,
and D218's pre-committed rule — a positive here gets no follow-up on this fixture at all —
was written for exactly this.

### Defects and disclosures

**The sensitivity block runs on a different span from the ladder, and its levels are not
comparable.** `lengthMA = 55` needs a 1,506-bar burn-in of its own, so the block starts at
bar **1,622** against the ladder's 1,000 and sees **893** live bars against 1,515. The
within-block comparison (is 34 special?) is valid; the levels next to the ladder's are not,
and the report says so where the table is rather than in a footnote.

**Impulse MACD needs about four years of daily data before its numbers stop depending on
where you started it**, and the reason is a real defect in the published construction rather
than conservatism here. An SMA seed lags a ramp by `(n−1)/2`; an EMA's steady-state lag is
`(1−α)/α`. Those coincide **only** at `α = 2/(n+1)`. Wilder smoothing uses `α = 1/n`, so the
SMA seed starts it **16.5 slopes away from its own steady state**, and at a decay of 33/34
that takes 926 bars to become irrelevant. D217's MACD had no such problem — its ramp
identity was exact from the seed. `test_the_sma_seed_is_exact_for_the_macd_ema_and_NOT_for_wilder`
pins the asymmetry.

**The runner imports D217's runner rather than restating it.** The panel, per-ETF cost
derivation, portfolio arithmetic, nulls and DSR machinery are the same objects, checked by
identity in `test_d218_scores_its_arms_with_d217s_code_and_not_its_own`, which also asserts
D218 has **not** defined its own copies. D212 is why.

### Ledger

| block | looks |
|---|---:|
| the ladder — 4 rungs × 2 books × {gate off, on} | 16 |
| sensitivity — 3 lengths × 2 rungs, minus 2 already counted | 4 |
| **fresh, D218 only** | **20** |
| inherited from D217, in full | 42 |
| disclosed prior ETF-fixture configurations + structure/terrain bar | 45,741 |
| **verdict count** | **45,803** |

### What this changes

**D217's headline can now be stated as a general claim rather than a single-indicator one**,
with the magnitude caveat attached: trend *acceleration* carries information on this
universe where trend *level* does not, it reproduces across two unrelated constructions, and
the two constructions' acceleration rungs are interchangeable. **That is the transferable
result, and it is still not tradeable here** — it does not clear the noise floor, and the
best version of it loses to buy-and-hold on money.

The follow-up D217 named is unchanged and now better specified. It moves to a fixture this
project has not mined, it tests `acceleration − level` rather than any named indicator, and
`I1 − C ≈ 0` says it should use **whichever construction is cheapest to compute**, because
the choice of indicator is not what is being measured.
