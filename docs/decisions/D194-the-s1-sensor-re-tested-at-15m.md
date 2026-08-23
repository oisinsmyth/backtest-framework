# D194 — Phase 3 re-opens once: S1 on real intraday volume, with a floor and a permanent stop

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-23
**Category:** Validation & research integrity
**Source:** D189's own "what it does not close", and the data path D190–D193 built

> Written and committed **before** the null test runs, as D173, D178, D180, D182, D183,
> D185, D186, D188 and D189 were. A result section will be appended and nothing above it
> edited.

## This re-opens a stopped programme, which is the most suspect move available

D189 tested S1 and it failed on **all 16 configurations, all 3 metrics, both symbols**. On
`P(reversal | touch)` the real levels sat *below* the null median — 41.4th percentile on
BTC, 26.0th on ETH. The programme stopped at WP2 by its own condition and WP3–WP8 never
ran.

Re-running a rejected hypothesis on new data, by someone who already knows the first
answer, is the shape of every p-hacked result ever published. Most of what follows exists
to constrain that rather than to make the measurement, and if the constraints look
disproportionate to the experiment, that is the point.

## Why re-opening is defensible

**D189 tested a construction nobody uses.** A 90-to-180-**day** volume profile built from
daily bars, where each bar's volume is spread across the whole day's high–low range.
Volume profile as the literature and the practice describe it is an *intraday* object over
session-to-monthly windows, where volume is attributed to the narrow range it actually
traded in. D189 measured a proxy for the idea. This measures the idea.

**D189 named this gap at the moment it failed, before the data existed:**

> **This tests one sensor on daily bars, on two instruments.** A sharper map — real
> intraday volume from an exchange API rather than the yfinance series that reports zero
> on half its bars — is a different measurement, and this result does not settle it.

A gap named in the losing result is a much better warrant than one found afterwards. And
D189's *grounds for predicting failure* explicitly included bucket coarseness — "a 0.5-ATR
bucket on BTC is hundreds to thousands of dollars wide" — which is the thing this removes.

**The data did not exist then.** D189 recorded that the 1h yfinance fixture reports zero
volume on 8,656 of 17,463 BTC bars. D190–D193 replaced it: `crypto_binance_15m_raw.csv.gz`,
exchange-native, **0.000% empty bars on BTC and ETH**, quote-notional volume declared
rather than inferred.

**The case against, stated in my own voice:** none of that changes the fact that this is a
second draw. Two guards below exist for it, and they are pre-committed: an effect-size
floor, and a permanent stop.

## What is run

Native 15m bars for the map *and* the reactions. **Every window is calendar-matched to
D189, so bar resolution is the only variable** — D162's precedent, where the vol-estimate
window scales with the design so each design stays internally coherent.

| | D189 | D194 | matched on |
|---|---|---|---|
| Bars | daily, yfinance | **15m, Binance** | — the variable |
| Span | 2015-01 – 2025-12 | 2018-02-12 – 2026-07-31 | — |
| Lookback | 90 / 180 bars | **8,640 / 17,280 bars** | 90 / 180 days |
| ATR window | 20 bars | **1,920 bars** | 20 days |
| Bucket | 0.25 / 0.5 ATR | 0.25 / 0.5 ATR | identical width |
| Touch band k | 0.5 / 1.0 | 0.5 / 1.0 | identical |
| Horizon | 5 bars | **480 bars** | 5 days |
| Rebuild every | 20 bars | **1,920 bars** | 20 days |
| Volume units | `quote_notional` | `quote_notional` | identical |
| Null draws / seed | 500 / 0 | 500 / 0 | identical |

Because the ATR window is calendar-matched, the bucket width and the touch band are the
*same prices* they were in D189. The map is not finer-grained; it is **differently
filled** — volume lands where it traded instead of being smeared across a day.

**Traversal is reported in calendar days** (`bars ÷ 96`), so it stays directly comparable
to D189's 4.31 and 4.36. Reporting it in 15-minute bars would produce a number 96× larger
that looks like a finding and is a unit change.

**Symbols.** BTC and ETH carry the verdict, matching D189 exactly. `XEMUSDT` and `BTGUSDT`
— both delisted, both in the fixture precisely because a path tested only on majors is
tested only where it works — are a **pre-committed secondary check**: reported, counted in
the multiplicity ledger, not carrying the verdict. A pass on the majors that fails on the
dying coins is D180's pattern repeating and will be reported as that.

**A span-matched daily control is mandatory.** D189's exact primary configuration re-run on
daily bars restricted to 2018-02-12 – 2025-12-31. Without it every difference between D189
and D194 is confounded with a different decade and the comparison says nothing.

## The bar, fixed before the run

The primary configuration is named now: **lookback 17,280 bars (180 days), bucket 0.5 ATR,
k = 0.5** — the same grounds D189 used, longest lookback and coarsest buckets for the most
stable map, tightest k for the strictest touch.

**Note the harness's own `verdict()` does NOT carry this decision.** It passes if *any* of
three metrics clears p ≤ 0.05, and its docstring calls that "deliberately generous". Three
generous one-sided tests is not a 5% test. The bar here is on `P(reversal | touch)` alone —
the metric the model rests on — and `verdict.passed` is reported alongside as a
cross-reference, not as the answer.

All three conditions must hold:

**1. Statistical.** `P(reversal | touch)` beats its null at the declared (high) tail on
**both** BTC and ETH. The every-symbol rule since Phase 1: one of two is a coin flip.

**2. Effect size — the guard this design needs most.** Real minus null mean on
`P(reversal | touch)` must be **≥ 0.045 in absolute terms on both symbols**.

That number is not invented here. It is the half-width of D189's own BTC null 90%
interval, `[0.3415, 0.4310]` — 0.0447, rounded to 0.045. **The effect must be large enough
that D189 would have seen it.**

The reason is arithmetic. BTC carries 294,336 bars at 15m against 4,017 daily — **73×**,
being 96 bars a day over a span 0.76× as long. A null interval narrows as 1/√n, so a
real-minus-null difference far too small to have registered in D189 will clear any
percentile bar here.

The exact multiple is deliberately **not** predicted: the null width scales with the number
of *touches*, not bars, and touch counts at 15m depend on how often price crosses a
calendar-matched band at intraday resolution — which is exactly the kind of number this
project has been burned for asserting from memory. D189 recorded 353 touches on BTC and
255 on ETH; the new counts are reported, not forecast. What the floor does not depend on is
that multiple: it is fixed at 0.045 whatever the sample turns out to be.

Without a floor, "we found it because we have more data now" is indistinguishable from a
discovery — and a pass on a difference D189's sample could not have resolved is sample size
wearing a result's clothes.

**3. Breadth.** The effect appears in **more than half** the 8-cell per-symbol sensitivity
grid, not only in the primary cell. D189's failure was unanimous: `beaten` empty in all 16.
A pass in 1 of 16 is noise, and saying so now costs nothing.

## A diagnostic that must be reported whatever happens

**The bucket-span census.** The sensor spreads a bar's volume across the buckets its range
covers, and the code comment explaining why says: *"a daily bar is not a point: putting a
whole day's volume at one price would invent precision the bar does not carry, and would
make the profile a close-price histogram wearing a volume label."*

At 15m with calendar-matched bucket widths, a bar's range is often **narrower than one
bucket**. If most bars land in a single bucket, the map has quietly become the very
close-price histogram that comment was written to prevent — and it would look exactly like
a legitimate volume profile.

So the distribution of buckets-covered-per-bar is computed and reported **before** the
verdict, for every configuration. If the median span is 1, that is the headline finding
regardless of what the null test says, and any pass would be a pass for a mechanism other
than volume-at-price.

This is stated now because it is the one way this design could produce a *true* positive
for a false reason, and finding it afterwards would be indistinguishable from explaining
away an unwelcome number.

## H2 carries over, and gets stronger

D189's H2: a high-volume node is by construction a price the market spent time at, so
price is more likely to be near one than near a uniformly placed level, and more likely to
still be near it a few bars later — which inflates a reversal rate with no causal support
or resistance behind it.

Sharper attribution couples node placement to where-price-lingered **more** tightly, not
less. So a pass is not evidence of support and resistance until that confound is ruled
out, and ruling it out is the first task of a passing branch rather than the last.

## Multiplicity, carried across both runs

`TERRAIN_RESULTS.md` records **48 looks** from D189. This run adds 48 on the majors
(2 symbols × 2 lookbacks × 2 buckets × 2 k × 3 metrics), 48 on the secondary pair, and 3
for the daily control.

**Running total: 147 looks on one hypothesis.** The ledger is updated cumulatively, never
reset. D189's failures count. The plan's own rule is that retired and failed items still
count, and the question being asked has not changed.

## The permanent stop

> **If S1 fails here, S1 is closed. No finer resolution — 5m, 1m, tick — will be tried,
> and no further S1 variant will be pre-registered.**

The grounds, stated before the numbers: the resolution ladder is infinite, every rung is a
fresh look at one hypothesis, and two rungs two orders of magnitude apart both returning
nothing means the hypothesis is not resolution-limited. Leaving the ladder open makes "the
data was not sharp enough" an unfalsifiable escape hatch that can be pulled forever, and a
programme that cannot be closed is not being tested.

A pass reopens WP3–WP8 under the implementation plan's existing gates, with H2's confound
as the first task.

## The predictions

**H1 — S1 fails the bar again.** Predicted **TRUE**, **high** confidence, up from D189's
"moderate".

Grounds: D189's failure was unanimous across a 16-cell grid rather than marginal; the two
non-primary metrics also sat in the wrong tail; and a level price genuinely respects should
leave *some* trace at daily resolution rather than none at all. Behind that, the project's
whole record — four entry filters, six stops, E1's five passes and sixty-two-coin failure,
the swing stop, the ensemble, the short book, the cross-sectional portfolio.

Against it, honestly: intraday attribution is a real mechanical difference rather than a
rescaling; volume clustering is the one adjacent literature with actual support; and
D189's own stated grounds for predicting failure included the coarseness this removes. If
H1 is wrong, that last point is why.

**H2 — a pass, if any, is the where-price-lingered confound rather than support and
resistance.** Predicted **TRUE**. Not falsifiable by this run; it constrains how a pass may
be read, and its test belongs to the passing branch.

**H3 — if S1 clears statistical significance, it fails the effect-size floor.** Predicted
**TRUE**. The pass will be small and bought with sample size. This is the prediction most
likely to look foolish if the effect turns out to be real and large, and it is stated for
that reason.

**Track record:** mechanism-first predictions falsified six times, confirmed six.
Predictions of failure have been the more reliable half. This is one, and that asymmetry is
itself a reason to distrust it — predicting failure in a project where everything has
failed is cheap.

## What a pass would and would not mean

It would mean one sensor's levels beat randomly placed ones on reaction statistics, at
intraday resolution, by a margin the previous sample could have detected. It would **not**
mean the terrain model works: the ladder's go/no-go is WP5 — F7/F8/F9 on the existing trade
population — which this phase does not touch, deliberately, because building features on an
untested sensor is the ordering the ladder exists to prevent.

## Code changes, all of them registered here before the run

- **`lookback_days` → `lookback_bars`.** The field is *applied* as a bar count
  (`bars[index - lookback + 1 : index + 1]`) but *named* days. Harmless on daily bars, a
  lie at 15m. Renaming it is D187's lesson applied before it costs anything: the name of a
  field is not a contract, the parameter that enforces it is.
- **`LOOKBACK_BARS` extended** to `(90, 180, 8_640, 17_280)`, keeping the daily values so
  D189 stays byte-reproducible. The set exists to stop unregistered search, so the new
  values are named in this document, before the run, with their calendar equivalents.
- **`ATR_WINDOW`, `HORIZON` and `REBUILD_EVERY` become parameters** rather than module
  constants read at import. Their daily defaults are unchanged; the 15m values are the
  calendar-matched ones tabulated above. `run_null` currently never forwards `horizon`,
  so that path is fixed too.
- **`scripts/run_terrain_s1_intraday.py`**, alongside the existing runner rather than
  replacing it, writing `data/terrain_s1_15m_summary.json` and appending its own dated
  section to `TERRAIN_RESULTS.md`. The existing runner overwrites that file, which
  contradicts its own append-only header; the new one appends.

Reused unmodified: `PriceDensity`, the `TerrainSensor` protocol, the null harness's touch
and reversal definitions, and `MetricSpec`/`summarise_null` from `breakout_nulls.py`
(D130), so every metric still declares its own tail.

### One change is forced by arithmetic, and it is registered here rather than discovered

`level_reactions` calls `mean_true_range` once per bar, recomputing the whole window each
time. On daily bars that is 4,017 bars × a 20-bar window and costs nothing. At 15m it is
274,655 bars × a 1,920-bar window, and it is called 501 times per configuration.

Measured, not estimated: **282.5 µs per call, 77.6 s per `level_reactions` call, 10.8 hours
per configuration, 173 hours for the grid.** The study is not runnable as written.

So the ATR is **precomputed once per symbol as a rolling series** and looked up in O(1).
Measured again: build 0.08 s, and the scan falls to 0.2 s per call — **~0.5 hours for the
grid instead of 173**. The same treatment is applied to `realized_volatility`, which the
current code recomputes over a 480-bar window twice per touch.

This is an optimisation, not a change of method, and the claim that it is has to be
demonstrated rather than asserted: the prototype agrees with `mean_true_range` to a
**maximum relative difference of 9.2 × 10⁻¹³ over 300 random probes**, and a test pins that
equivalence on the daily path so D189's numbers are reproducible from the new code.

Recording it here matters because "we had to change the implementation to make it run" is
otherwise indistinguishable, after the fact, from changing the measurement.

**`n_sims` stays at 500 and the seed stays at 0.** Reducing the draws would have been the
easy way to make the runtime fit, and it would have widened every null interval — making a
pass easier — for a reason that has nothing to do with the hypothesis.

## The controls are re-run, not inherited

Both synthetic checks run again at 15m before any real data touches the harness:

- **False-positive:** a pure random walk must yield nothing, across three seeds.
- **Positive control:** a planted level must be found. D189's positive control **failed
  twice and both times the fixture was wrong** — a `-0.9 × gap` drift term built a magnet
  rather than a wall, and the harness correctly reported the planted level as worse than
  chance. Re-running it at a new frequency is not a formality.
- **Look-ahead:** mutating every bar after `t` must leave the density at `t`
  byte-identical. D181 established that `DataView` protects strategies and does nothing for
  analytics built on their output, and a sensor is analytics.
