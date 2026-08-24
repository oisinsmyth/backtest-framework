# D202 — the local imbalance: fixing the statistic, not the wrapper

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-24
**Category:** Signals & strategy interface
**Source:** D201's failure, and a counts-only census run before this document

> A result section will be appended and nothing above it edited.

## Why D201 was a bad design, in my own words

```
imbalance = (all demand BELOW price - all supply ABOVE price) / their sum
```

is **confounded with price level by construction**. In an uptrend almost all accumulated
mass sits below price, so the reading is a proxy for *where price sits in its own history*
— a trend indicator wearing an inventory label. It was long 89–93% of the time, made 9–30
decisions in eleven years, and every cell that cleared a hurdle was 78–92% one multi-year
long.

**The census found this before the run and I pre-registered around it instead of fixing
it.** Naming a defect in a pre-registration does not stop it being a defect. Two more, in
the same direction: it thresholded at zero, discarding the magnitude D197 built the field to
provide and D196 identified as never tested; and it had no timing control, so with a book
at **+0.78 net exposure** and Sharpe invariant to constant leverage, most of what it
measured was beta.

This is **not** another D198/D199 wrapper refinement. Those changed entry timing and exits
around a fixed statistic and moved nothing. This changes what is computed.

## The three changes

**1. The reading is local.**

```
s(t)   = 2 x ATR(t) / price(t)                    # log units
w(p)   = exp( -|ln p - ln price(t)| / s(t) )
local  = (D_near - S_near) / (D_near + S_near + 1)
```

Only inventory near price counts. The decay scale reuses `STOP_ATR = 2` — *the distance the
trade actually risks* — so no new constant enters. The window travels with price, so the
level confound cannot survive.

The pseudo-count is **1.0, one era-typical swing's total mass**, and its units are the
opposite of D197's `_shrinkage` deliberately: that reads a single bucket, this reads a
weighted sum. Both are pinned by test. The invariant is `d / (d + 1)`, so one unit of
weighted mass reads 0.5 — while a single swing near price reads about **0.30**, because the
kernel is 0.5 ATR wide against a 2 ATR decay and part of any nearby swing always falls on
the far side of price. Geometry, not miscalibration, and recorded rather than tuned away.

**The raw field is primary.** The erasure destroys everything inside the 40-bar envelope,
which is exactly the neighbourhood a local reading needs.

**2. Sizing is the magnitude.** `position = local`, continuous in [−1, +1]. This is the thing
D196 found had never been tested in this project. Exposure falls as conviction falls, which
is the natural risk control — and why **no stop is primary**: D201 already measured what a
hard stop does to this family (94.3% of bars flat), and a stop on a scaled position is
ill-defined.

**3. A timing control — the hurdle D201 lacked.** Circularly rotate the realised position
series, 500 draws. This preserves the exposure distribution, autocorrelation, turnover and
net tilt **exactly** and destroys only the alignment with price, so a rotated book carries
the same beta against the same uptrend. Only rotation asks *did the exposure change at the
right moments*.

## The census

Counts only. It says the fix worked and then hands over a new problem.

| | BTC-USD | ETH-USD |
|---|---:|---:|
| **net average exposure** | **−0.075** | **+0.014** |
| *(D201's global statistic)* | *+0.583* | *+0.290* |
| share of bars positive | 47.8% | 50.6% |
| **sign flips** | **393** | **369** |
| *(D201)* | *9* | *29* |
| median \|local\| | 0.327 | 0.257 |
| sign agreement with D201's statistic | **48.7%** | 58.0% |
| turnover | 33.1 units/yr | 35.4 |
| **implied cost drag at 40 bps** | **13.2%/yr** | **14.2%/yr** |

**The confound is gone.** Net exposure moved from +0.78 to −0.075. The book is now balanced,
so its Sharpe can no longer be mostly beta, and buy-and-hold stops being the only control
that bites.

**The sample is real.** 393 decisions against nine. D201's verdict rested on ten regime
calls, one of which was 92% of the result; this one cannot.

**It is a genuinely different statistic.** Sign agreement with D201's reading is 48.7% on
BTC — barely better than a coin flip. The locality fix is not a reparameterisation.

**And it turns over far too fast.** 13–14% a year in costs. That is not a detail; it is
larger than any edge this project has ever measured.

### What the census changes, decided here before any returns

Rather than tune a smoothing parameter until the costs are affordable, the run adds a
**zero-cost diagnostic arm**. It separates two very different findings that a single
cost-laden number cannot:

- the signal carries no information → it fails at 0 bps too;
- the signal carries information at a frequency this cost structure cannot support → it
  passes at 0 bps and fails at 40.

D196 made exactly this decomposition ("before costs this strategy makes money") and it was
the most useful thing in that document. **The zero-cost arm is a diagnostic and never a
strategy**, and is labelled so wherever it appears.

One smoothing arm also runs — a **5-bar trailing mean** of the signal, the window being
`terrain_nulls.HORIZON`, itself `breakout_study.E2_N`, so no new constant. One window, not
a sweep.

## The grid

5 configurations × 2 symbols = **10 cells**:

| | statistic | sizing | cost | note |
|---|---|---|---|---|
| **primary** | local | continuous | 40 bps | |
| diagnostic | local | continuous | **0 bps** | never a strategy |
| smoothed | local, 5-bar mean | continuous | 40 bps | |
| binary | local | sign only | 40 bps | isolates sizing |
| global | **D201's** | continuous | 40 bps | isolates the locality fix |

No stop cell: D201 answered that decisively and continuous sizing is the risk control here.

## The bar

All three required on **both** symbols, on the primary:

1. **Beat the rotation null by ≥ +0.10 Sharpe** — timing, not exposure.
2. **Beat the mass-shuffle null by ≥ +0.10 Sharpe** — placement. 500 draws, seed 0.
3. **Beat buy-and-hold.**

Reported alongside: turnover and realised cost drag; net exposure; share long/short/flat;
long and short legs; by-year; and the gross-versus-net decomposition.

## A permanent stop, fixed here

> **If the local statistic fails, the S6 map is closed entirely.** No further statistic,
> sizing rule or trading rule will be pre-registered on it.

The ledger reaches **60 (S6 reversal, closed) + 12 (D201) + 20 here ≈ 92 looks** on one map
whose placement measured zero at its first fair test. This is the last refinement worth
running without a new data source or a genuinely new claim, and saying so now costs nothing.

## Multiplicity

10 cells × 2 nulls, plus 4 paired comparisons (local vs global, continuous vs binary,
gross vs net, smoothed vs raw) = **20 looks**. Own ledger, lineage disclosed.

## Predictions

**H1 — the primary fails to beat buy-and-hold.** Predicted **TRUE**, high confidence. A
13.2%/yr cost drag has to be overcome before anything else happens.

**H2 — the primary fails the rotation null by the floor on at least one symbol.** Predicted
**TRUE**, moderate-to-high. My record is reliable on null failures and unreliable on
baseline comparisons, and this is a null.

**H3 — the ZERO-COST diagnostic also fails the rotation null on at least one symbol.**
Predicted **TRUE**, moderate. This is the one worth watching: it separates "no information"
from "information the costs eat". D197 measured placement at zero, which is the reason for
the prediction; a pass here would be the first evidence in the family that the map carries
anything at all, and it would be about *timing* rather than placement.

**H4 — local and global differ by ≥ +0.10 Sharpe on both symbols.** Predicted **TRUE**, high
confidence. 48.7% sign agreement means they are nearly independent readings.

**H5 — net exposure stays within ±0.2 on both symbols**, so the beta confound really is
gone rather than merely reduced. Predicted **TRUE**, very high — the census already shows
−0.075 and +0.014, so this is a check that the run reproduces it, not a discovery.

**H6 — continuous sizing beats binary on at least one symbol.** Predicted **TRUE**,
moderate. It uses the magnitude and it trades in smaller increments, so it should pay less
of the 13% drag — but this project's record on "the refinement helps" predictions is poor
in both directions.

**The interesting failure mode, named in advance.** If the primary passes, the first
suspicion is that the turnover estimate is wrong and the realised cost drag is far below
13%. The run must report realised drag directly, and a pass with a drag materially under
the census figure is a bug report before it is a result.

## Verification

- Look-ahead **guard and poison pair** on the local reading.
- **Shrinkage units** pinned by the `d/(d+1)` doubling invariant, not by a guessed value.
- **Locality asserted in both directions**: far mass must not move the reading, near mass
  must — a guard that always returned zero would pass only the first.
- **The rotation null preserves** the exposure distribution and net exposure exactly and
  **changes** the equity curve, or the control is vacuous.
- Continuous cost is proportional: a position moving 0.1 costs a tenth of one moving 1.0.
- Census reproduces; one-cell benchmark with projected runtime before the full run.
