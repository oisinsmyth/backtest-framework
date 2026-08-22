# D189 — Phase 3 opens: the S1 terrain sensor and the null test that can close it

**Status:** PRE-REGISTERED — implementation committed, **null test not yet run**
**Date:** 2026-08-22
**Category:** Signals & strategy interface
**Source:** `New Docs/TERRAIN_MODEL.md` WP1 + WP2 — the last unstarted work in the roadmap

> Written and committed **before** the null test runs, as D173, D178, D180, D182, D183,
> D185, D186 and D188 were. A result section will be appended and nothing above it edited.

## Why this scope

`TERRAIN_IMPLEMENTATION_PLAN.md` puts a stop condition at WP2:

> If S1 fails its null, STOP the terrain programme and report — do not proceed to WP3+ on
> the theory that other sensors will save it.

So WP1 alone would produce code and no decision. WP1 + WP2 is the smallest scope that
produces a verdict, and the verdict either opens the programme or ends it.

**WP0 was already complete** — its gate (two years of clean 1h data, a resampling contract,
a reconciliation report) was met by D160/D161/D165. The plan doc's checklist was stale.

## Two data findings that shaped the build

**The 1h fixture's volume is unusable.** `crypto_intraday_1h_raw` reports **zero volume on
half its bars** — BTC 8,656 non-zero of 17,463, median volume 0, scattered rather than
time-of-day patterned. That is the known yfinance defect for crypto hourly. S1 is a
volume-at-price sensor; a map built there would be missing half its mass, non-randomly.

**Daily is the better base, not merely the available one.** Volume is complete across
2015–2025 — eleven years against two — and it is the frequency the accepted baselines trade
at, which is what WP5 must annotate. A two-year intraday sensor could annotate almost none
of that trade population. The spec wants intraday for *sharpness*, not necessity.

**The deviation is recorded, not silently taken.**

## What was built

`research/terrain.py` — the sensor interface, frozen here for every later sensor:

- `PriceDensity` — normalised mass over ATR-width buckets, with `bucket_of`/`mass_at`
  returning **None outside the mapped range**. A price the lookback never visited has no
  density, and `0.0` would be indistinguishable from a visited-but-empty bucket.
- `TerrainSensor` protocol — `density(bars, index, volumes) -> PriceDensity | None`, where
  `None` means unavailable and never an imputed empty density.
- `VolumeProfileSensor` — lookback ∈ {90, 180}, bucket ∈ {0.25, 0.5} ATR, both **raising**
  outside the spec's stated sets. A bar's volume is spread across the buckets its **range**
  covers rather than dumped at its close: a daily bar is not a point, and putting a whole
  day's volume at one price would make this a close-price histogram wearing a volume label.

`research/terrain_nulls.py` — the harness, with the touch and reversal definitions fixed in
the module docstring before any run, as the spec requires. It reuses `MetricSpec`,
`NullDistribution` and `summarise_null` from `breakout_nulls.py` (D130), so **every metric
declares its own tail** — the direction is the hypothesis, not something chosen once the
numbers are in.

**Volume units are declared, not inferred** (D187). These fixtures report quote-currency
notional, so this is a dollars-traded-at-price map.

**The look-ahead guard is built here, not inherited.** D181 established that `DataView`
makes look-ahead impossible for a *strategy* and does nothing for analytics built on
strategy output. A sensor is analytics. `test_terrain.py` asserts the property directly:
mutating every bar after `t` — prices ×10, volumes ×100 — must leave the density at `t`
byte-identical, with a companion test proving the mutation does reach a later density.

## The two synthetic checks, and what they caught

**The false-positive check passed first time.** On a pure geometric random walk, across
three seeds, the harness finds nothing. That is the mandatory check, and after D180 the
reason is concrete: a harness that manufactures structure would invalidate every downstream
terrain result invisibly, because the output would look exactly like a discovery.

**The positive control failed twice, and both times the fixture was wrong.** First attempt
used a drift term of `-0.9 × gap`, which pushes price *toward* the level — a **magnet, not a
wall** — and duly produced fewer reversals than random placement; the harness reported the
planted level as worse than chance and was right. Flipping the sign to `+1.2 × gap` built a
wall price could not return to: **one touch in 1,500 bars.**

The working fixture is a triangular oscillation, where a level at either bound is somewhere
price keeps coming back to *and* keeps turning at. It discriminates cleanly — **p_reversal
1.000 at the bound against 0.000 mid-range** — and the mid-range level is crossed four times
a period, which is what makes it a test rather than a tautology.

Worth stating plainly: **the harness caught both fixture errors.** That is the positive
control doing its job in the only direction that matters.

## The multiplicity, and the primary configuration named in advance

Two symbols × two lookbacks × two bucket widths × two touch bands, on three metrics, is
**48 looks**. A 5% test taken 48 times is not a 5% test.

So **one configuration carries the verdict**: **(lookback 180, bucket 0.5 ATR, k = 0.5)**,
chosen on stated grounds rather than results — the longest lookback and coarsest buckets
give the most stable map with the fewest nodes, and the tightest k is the strictest touch
definition. The other seven per symbol are reported as sensitivity, and **all of them count
in the multiplicity ledger**, because the deflated Sharpe at WP7 has to pay for every one.

**It must pass on both symbols.** The every-symbol rule this project has applied since Phase
1: one of two is a coin flip.

## The prediction

**H1 — S1 FAILS the every-symbol bar at the primary configuration.** Predicted **TRUE**,
moderate confidence, against the spec's own prior that S1 is the lead sensor and expected to
pass.

Grounds: every rule-level idea in this project has failed out of sample — four entry
filters, six stops, E1, the swing stop, the ensemble, the short book — and the one thing
that worked turned out to be a property of one asset class in one decade (D188). Daily
buckets are coarse: 0.5 ATR on BTC is hundreds to thousands of dollars wide. And the spec's
support for S1 is that it is *adjacent* to validated microstructure work, which is not
validation.

Against it: volume-at-price is the most mechanically plausible of the three sensors, and it
is the only one computing from immutable data this project already trusts.

**H2 — if S1 passes, it passes for a reason that is not support and resistance.** Predicted
**TRUE**.

**This is the interpretation risk and it should be stated before the numbers, not after.** A
high-volume node is *by construction* a price the market spent time at. Price is therefore
more likely to be near an HVN than near a uniformly-placed level, and more likely to still
be near it a few bars later — which inflates a reversal rate without any causal support or
resistance. The pseudo-levels match the real map's **count and span** but cannot match its
*where-price-lingered* property without destroying the thing being tested.

So a pass is **not** evidence of support and resistance until that confound is ruled out,
and ruling it out is the first task of a passing branch rather than the last.

**What would falsify each:** H1, a pass on both symbols. H2 is not falsifiable by this run —
it is a stated constraint on how a pass may be read, and its test belongs to whatever comes
after.

**Track record:** mechanism-first predictions falsified six times, confirmed six. Predictions
of failure have been the more reliable half, and this is one.

## What a pass would and would not mean

It would mean one sensor's levels beat randomly placed ones on reaction statistics. It would
**not** mean the terrain model works: the ladder's actual go/no-go is WP5 — F7/F8/F9 on the
existing trade population — which this phase does not touch, deliberately, because building
features on an untested sensor is the ordering the ladder exists to prevent.
