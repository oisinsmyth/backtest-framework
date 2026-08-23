# D197 — S6, a signed inventory map, tested at the boundary

**Status:** Pre-registered — written and committed BEFORE the run
**Date:** 2026-08-23
**Category:** Signals & strategy interface
**Source:** D196's 100-trade review, and a viability census run before this document existed

> A result section will be appended and nothing above it edited.

## Provenance, stated first

This design came out of **looking at charts**. D196 published 100 sampled trades for
review and this sensor is the response to what those charts showed. That is discretionary
search: it does not carry a p-value, and the fact that the design "obviously" fixes what
was wrong with S5 is exactly the feeling that precedes an overfit. Hence a document, a
fixed bar, and its own ledger.

A second disclosure. **A viability census was run before this was written**, deliberately,
because D194's runtime estimate was wrong by 6× when it was guessed rather than measured.
The census reports counts and rates, not returns — no Sharpe, no P&L, nothing that could
be read as a result. What it changed is recorded in its own section below, because it
changed three things and one of them was a defect.

## What S6 is

A single cumulative signed field over log price. Not a level set.

**Construction.** For every confirmed swing pivot at bar `i`:

- a swing **low** (price turned up) **adds** mass; a swing **high** (price turned down)
  **subtracts** it. Positive net = demand, negative = supply.
- mass is spread as a Gaussian in log price, centred on the pivot extreme, with
  `sigma = cluster_atr x ATR(i) / price(i)` — the sensor's own band width from S5, in log
  units so it is scale-free across $200 to $150,000.
- the amount is **era-normalised**: `w = volume(i) / median(volume over the trailing 90
  bars)`. Raw notional over a decade would make the map a chart of when volume was high;
  one era-typical swing is now 1.0 wherever it occurs.
- a parallel **gross** channel adds `|w|` for every pivot regardless of sign.

**Grid.** Log price, 0.002 per bucket (≈0.2%), ~3,350 buckets on BTC.

**Erasure — destroy, not mask.** At every bar `t`, take the body envelope
`[min(open,close), max(open,close)]` over bars `t-41 … t-2` and write **zero** into both
`net` and `gross` for every bucket inside it. The value is gone; later bars accumulate
from zero. A zone price has recently moved through was weak or was never real, so it does
not come back when the window slides — it comes back only if new swings rebuild it.

The two-bar exclusion is not a leak guard (bars ≤ t are already safe). It is what leaves
the map readable at a fresh extreme, and it fixes how long a signal lives — about two
bars, before the breakout bar enters the window and wipes the price it fired at. **Fixed
at 2 and not swept**: it is a direct control on firing rate and sweeping it would be
tuning the sample size until something works.

**Reading it — shrinkage, not a threshold.**

```
tilt(p) = net(p) / (gross(p) + k)          in [-1, +1]
```

`k` is a pseudo-count: the peak per-bucket mass one era-typical swing deposits,
`BUCKET / (sigma x sqrt(2*pi))`, computed from the kernel rather than chosen. Prices with
thin evidence are pulled toward zero automatically, so **virgin territory reads ~0 by
construction** and no minimum-support threshold has to be invented. This is the standard
small-sample fix for a ratio, and it is the reason the trigger is parameter-free.

Without it the sensor breaks in a specific way: a price whose only mass is kernel spill
from one nearby swing has `net ≈ gross`, so an unshrunk `net/gross` reads **±1.0** — full
confidence from no information at all. A deadband on the ratio does not help, because a
ratio does not shrink with evidence.

## What is NOT being tested

**The equilibrium claim is shelved.** The original hypothesis was that price wants to sit
where the field is near zero. The erasure makes zero the default state everywhere price
has recently been, so that claim cannot fail under this construction and is not measured
here. What is measured is a **boundary claim**.

**Only the two reversal cells are traded.** A fire has four possible shapes; two are
continuation trades and are recorded but not taken:

| | breaks up | breaks down |
|---|---|---|
| into positive (demand) | *not traded* | **LONG** — reversal |
| into negative (supply) | **SHORT** — reversal | *not traded* |

This is the approach-aware reading: a zone acts as a barrier only from the side it formed
on. Supply overhead met from below is correctly oriented; demand met from below is not.
S5 refused the "support becomes resistance" flip on the grounds it is a separate
hypothesis, and the same refusal applies here. The untraded cells are counted so the
continuation question can be pre-registered separately later.

## The census, and the three things it changed

Run on the committed daily fixture, BTC and ETH, k=2, cluster_atr=0.5, before this
document. Counts only.

| | BTC-USD | ETH-USD |
|---|---:|---:|
| bars | 4,017 | 2,974 |
| confirmed pivots | 1,064 | 791 |
| pivots destroyed the instant they confirm | **70.6%** | 70.4% |
| live buckets, median bar | 859 of 3,351 | 590 of 2,096 |
| bars where the signal fires | **816 (20.3%)** | 622 (20.9%) |
| ... of those, virgin (no mass at all) | **39.6%** | 33.3% |
| reversal LONG (break down into demand) | 171 | 181 |
| reversal SHORT (break up into supply) | **321** | 229 |
| fires producing no reversal trade | 324 | 212 |

**1. It refuted an objection to the design.** Destroy semantics plus a rolling envelope
looked analytically fatal: swings happen where price is, the envelope erases where price
has been, so mass should be destroyed as fast as it is created. It is not — 29.4% of
pivots survive their own birth, because a pivot price is a **high or a low** while the
envelope is built from **bodies**. A pivot whose extreme poked beyond the recent body
range escapes. The map holds ~26% of its buckets live at a typical bar.

**2. It exposed an implicit selection nobody chose.** The corollary of the above is that
the surviving map is a map of **wick extremes**. Seven pivots in ten are discarded, and
the ones that survive are selected for having spiked beyond the body range — sharpness,
not volume. That filter is doing more to determine the map's content than the volume
weighting is. It is defensible (a rejection wick is a plausible supply/demand event) but
it was an accident of the erasure geometry, and a passing result must not be attributed
to the volume term when this is what selected the sample.

**3. It found a calibration defect.** With `k` set to one era-typical swing's *total*
mass, observed `|tilt|` had a median of 0.048 and a maximum of 0.303 — the kernel spreads
one swing across many buckets, so per-bucket mass is a small fraction of the total and the
pseudo-count swamped it. Every reading would have been crushed toward zero and the ±0.1
trigger discussed in design would have admitted 25% of non-virgin fires on BTC and 13.5%
on ETH, for reasons of units rather than evidence. `k` is therefore specified in
**per-bucket** units above. This affects magnitudes only: the counts in the table depend
on `sign(net)` and `gross > 0`, both invariant to `k`, so they stand.

**The short bias is real and measured, not a worry.** 321 shorts against 171 longs on BTC.
The mechanism is data availability: an upside break in this sample often runs into virgin
territory at a new all-time high, but a downside break revisits ground price has already
traded. That produces a book that leans short across a decade in which BTC rose roughly
300×. It is an artifact of where information exists, not a claim about the market, and the
legs are reported separately for that reason.

## The strategy

| | |
|---|---|
| signal | bar `t` closes outside the erasure envelope, and `tilt` at that price passes `X` in the reversal orientation |
| entry | **market at the open of bar `t+1`** — the signal bar's close is not also its fill |
| stop | **2 x ATR(20)** from entry |
| target | **3R** = 6 ATR |
| backstop | `MAX_HOLD` = 60 bars, inherited from D196 |
| costs | 40 bps round trip |
| sizing | full equity, one position at a time — identical in every arm |

Intrabar ordering is pessimistic: when a bar covers both stop and target, the **stop** is
taken. Entry is market-on-open, so D9's adverse-selection problem does not arise; there is
no limit resting at a level to be picked off.

**Why 2 ATR and not D196's geometry.** `bounce_rr` stopped at 0.5 ATR ≈ 2.1% of price, so
40 bps was **0.49R** and break-even sat at 36.6% — it made money before costs and lost
after them. At 2 ATR ≈ 8.3% of price the same 40 bps is **~0.12R** and break-even falls to
**~28%**. The multiple 3R does not transfer between designs; the stop distance is what
makes it mean something.

`X = 0` is primary and has no free parameter: shrinkage already handles thin evidence.
`X = 0.1` runs as a sensitivity.

## The control, and why it matters more than the null here

**The erasure-only control**: the identical strategy on a map that is *only* the erasure —
no swings, no volume, no signs. Under the reversal rule that is **"fade every 40-bar
breakout"**, unfiltered. Same bars, same entries, same stops, same costs.

This is the primary comparison, and it is a stronger test than the null. The erasure is a
deterministic function of price, so it is present in the real arm, in the control, and in
every null draw. A null that shuffles mass positions cannot detect a confound carried by
the erasure — every draw carries it identically. The control can. **If the map does not
beat "fade every breakout", the swing and volume machinery contributes nothing.**

**The null**: 500 matched draws per cell, seed 0. Mass positions are shuffled while
**preserving the sign and magnitude distributions** and applying the erasure identically
in both arms. Matching only count and span, as `pseudo_levels` does, would hand the real
arm structure the null was never given.

## The bar

All three required, on the **primary configuration** — `cluster_atr` 0.5, `k` 2, `X` 0 —
and on **both** symbols:

1. **Beat the erasure-only control by ≥ +0.10 Sharpe.** The sensor question.
2. **Beat the matched null by ≥ +0.10 Sharpe.** The placement question.
3. **Beat buy-and-hold** on Sharpe over the traded span. The tradeability question.

The +0.10 floor is D195's and D196's, on the same grounds: D185 put the entire rebalancing
machinery at 0.025 Sharpe and D183's portfolio edge was +0.075, so below +0.10 is inside
the noise of effects this project has already shown it cannot resolve.

Sharpe is computed from the **per-bar equity curve**, marked to market while a position is
open, so it is comparable to buy-and-hold.

**Reported alongside, and not optional:** long and short legs separately; the four-cell
breakdown; firing rate and virgin share; and the decile response of `tilt` against forward
return. The decile curve is a **diagnostic, not a verdict** — a monotone response is
evidence the magnitude carries information, a single hot bucket is not. D196's post-hoc
rank slice was non-monotone (rank 4 beat rank 3) and that is what stopped it being called
a finding.

## Multiplicity

2 symbols × 2 bandwidths × 2 pivot k × 2 thresholds = **16 cells**, plus 2 control cells,
each real cell against 500 null draws. **Its own ledger, opening at 18 looks.**

This is a different hypothesis from the S1 programme's 147 and does not inherit them: S1
asked whether a volume histogram marks levels price reacts at, and was closed permanently
by D194. S6 asks whether signed, self-erasing inventory predicts what happens when price
leaves its range. Shared ancestry in the pivot detector is not shared hypothesis. It does
inherit D196's ledger in spirit — same sensor family, same author, same decade of data —
and any Sharpe that survives has to pay for every look taken to reach it.

## Predictions

**H1 — S6 fails to beat the erasure-only control by the floor on at least one symbol.**
Predicted **TRUE**, high confidence. Nothing in this project has survived a fair test, and
the control is not a weak opponent: a 40-bar breakout filter is itself a real signal, so
the map's marginal contribution has to be large to clear +0.10.

**H2 — the short leg is materially worse than the long leg on both symbols.** Predicted
**TRUE**, high confidence. The census already establishes the bias (321/171 on BTC); this
predicts its consequence in a market that rose 300×. If the aggregate is rescued by the
short leg instead, that is the interesting result and it needs a mechanism before it is
believed.

**H3 — nothing beats buy-and-hold.** Predicted **TRUE**, high confidence. D188 and D196.

**H4 — the decile response of `tilt` is non-monotone.** Predicted **TRUE**, moderate
confidence. Grounds: the only prior evidence that the sensor family's score carries
information was D196's rank-1 slice, and it was not monotone.

**H5 — the erasure-only control is itself negative-Sharpe.** Predicted **TRUE**, moderate
confidence. It is the mirror of the breakout book this project already has, and fading a
40-bar breakout across a decade-long uptrend should lose.

**The interesting failure mode, named in advance:** if S6 beats the control only through
its short leg, that is a bull-market sampling artifact wearing a result's clothes — the
sensor is silent where information is missing and that silence is correlated with
direction. It would not be a finding.

## Verification, before any real data

- **Look-ahead property test**: mutating every bar after `t` must leave `net`, `gross` and
  the erasure mask at `t` byte-identical. D181 — a sensor is analytics and the `DataView`
  guard does not cover it. The pivot confirmation lag (D173) applies to the field, and the
  envelope must read only bars ≤ `t-2`.
- **Synthetic controls**: a pure random walk must produce no edge; a planted, repeatedly
  respected level must be found. D189's positive control caught two bad fixtures.
- **Erasure unit test**: a bucket destroyed at `t` must read zero at `t+1` with no new
  pivots, and must not reappear when the envelope moves off it.
- **Shrinkage test**: a price carrying exactly one swing's mass must read `|tilt| ≈ 0.5`,
  and a virgin price adjacent to a strong one must read `≈ 0` rather than `±1`.
- Full suite green, mypy clean, summary JSON re-renders the results doc byte-identically.

## What a pass would and would not mean

It would mean that signed, self-erasing inventory tells you something about what happens
when price leaves its range that a plain breakout filter does not — on one asset class, in
one decade, after costs.

It would **not** establish supply and demand as the mechanism. The census shows the
erasure geometry selects wick extremes and discards 70% of pivots, so a pass is at least
as consistent with "sharp rejections mark prices that matter" as with anything about
volume or inventory. Separating those is the first task of a passing branch, not the last.
