# D214 — the terrain gate: reopening D203 by amendment, and the three bars it is judged against

**Status:** Committed (H1, H3, H4, H5 confirmed; H2 falsified)
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** a decision to test the terrain map as a confluence filter on the structure setups

> A result section will be appended and nothing above it edited.

## The amendment, first, because it is the load-bearing part

**D203's stop is overridden for this one study.** It reads:

> **The S6 signed inventory map is closed.** No further statistic, sizing rule, **trading
> rule**, threshold, exit policy, bar size or symbol will be pre-registered on it.

A confluence gate is a trading rule. This is squarely inside the stop, and the stop was
written to prevent exactly this: *"the ladder is infinite and leaving it open makes 'the
last reading wasn't the right one' an escape hatch that can be pulled forever."*

The override is the project owner's decision, taken after the stop, its reasoning and the
multiplicity cost were put in front of them. It is recorded here in writing, with the prior
stated up front, because **the honest way to revoke a commitment device is in the open.**
Nothing about D203's reasoning is now believed to be wrong; a specific, bounded exception is
being spent deliberately.

**The exception does not generalise.** D194's stop on S1 stands, D200's on the S6 reversal
line stands, and D203 stands for every use other than the single gate specified below. A
second override would need its own record and would not get the benefit of this one.

## This experiment already existed

Terrain's own plan, WP7 item (1):

> terrain entry gate (F7 quantile threshold, {median, lower tertile} only) as a new link in
> the composable gate chain

It was scheduled and never ran, because WP5's stop condition triggered first. So this is a
deliberate reopening of a planned-and-cancelled work package, not a new idea, and the
threshold set below is WP7's own rather than a fresh choice.

## The prior, stated before the run

**It is worse than bad — one of the two inputs is measured as actively wrong.**

- **D197**: S6 was *dead even* against randomly placed mass (−0.007 BTC, −0.012 ETH). The
  map's placement carries nothing, so a gate on it is a gate on noise.
- **D202**: the *local* reading — the exact statistic used here — sat at the **2.6th and
  1.4th percentile** of its own rotation null at zero cost and lost in **11 years out of
  11** on BTC. Not uninformative about direction; reliably wrong.
- **D210**: the structure components carry nothing once leg size relative to ATR is held
  constant.

A confluence of two things that each measure nothing, one of which is anti-predictive.

## The headline requirement: three bars, and an explicit would-it-have-passed

Every verdict is reported against **three multiplicity counts**, each with a stated
pass/fail, because the difference between them is itself the finding:

| bar | looks | what it represents |
|---|---:|---|
| **fresh** | this study alone (12) | if none of the history existed |
| **structure only** | 124 + 12 | inheriting the structure ledger alone |
| **combined** | 124 + 259 + 12 | inheriting both families |

The combined count is not optional book-keeping. `TERRAIN_RESULTS.md` states it directly:
*"Anything that reuses these sensors inherits the count."* This study reuses S6, so it
inherits 259, and it reuses the structure setups, so it inherits 124.

`expected_max_sharpe` and the required observed Sharpe are computed at each count inside the
runner from `validation/dsr.py` rather than hardcoded, and the observed DSR value is
reported at each. **A result that clears the fresh bar and fails the combined one is
reported as exactly that** — which is the specific thing this study was asked to show.

## Design

**Population.** The structure **base arm** (C1 only — every pullback after a change of
character) at the primary cell, `k=2`, touch band 0.5 ATR, both symbols, 15m. The identical
setups D210 and D212 used, so the gate is the only thing that varies. The fully-stacked arm
is reported as secondary and **carries no verdict**: gating ~110 trades leaves ~55.

**The reading.** `terrain_field.local_imbalance`, taken at the **signal bar**
(`entry_index - 1`), so the bar that decides never also pays — D197–D202's convention.

**The calendar match, with D194's precedent.** D202 ran on daily bars. `FieldParams`
enforces only `k` and `cluster_atr`, so the windows are free parameters and are matched at
96 bars/day without touching the closed module:

| parameter | daily (D202) | 15m (here) |
|---|---:|---:|
| `atr_window` | 20 | **1,920** |
| `vol_norm_bars` | 90 | **8,640** |
| `k`, `cluster_atr`, `erase` | 2, 0.5, False | unchanged |
| `bucket_ln`, `LOCAL_DECAY_ATR` | 0.002, 2.0 ATR | unchanged — both already scale-free |

Leaving `atr_window` at 20 would put five hours of volatility under a map spanning years,
which is D194's defect exactly. The match is asserted by test, not assumed.

**The gate, both directions, both counted.**

- **`inverted`** — take the trade only if `sign(terrain) == -direction`. **Primary.**
- **`aligned`** — take it only if `sign(terrain) == +direction`. Co-primary.

`inverted` is primary and the reason is written down before the run rather than after:
D202 measured this reading as anti-predictive at the 2.6th percentile. That prior comes from
a published result in this repository, not from peeking at this run. If `aligned` turns out
to be the one that works, that is a falsification of the stated prior and will be reported
as one.

Magnitude thresholds on `|terrain|`: **0, the median, the upper tertile** — WP7's own
pre-registered set, reused rather than re-chosen.

**Cells: 2 directions × 3 thresholds × 2 symbols = 12 looks.**

## Hurdles

All required, on both symbols:

1. gated mean **gross** R exceeds the ungated arm's by ≥ **+0.10R**;
2. gated mean **net** R at 40 bps per side is **positive**;
3. the gated book's annualised Sharpe clears the DSR bar — reported at all three counts,
   with the combined count carrying the verdict.

Hurdle 2 is separate on purpose, and hurdle 3's three-way reporting is the deliverable.

## Two controls, because a gate changes the sample merely by existing

**Gate-shuffle null.** Permute the terrain readings among setups and re-apply the gate, 500
draws. A gate that keeps half the trades moves the mean whatever it selects on; this
isolates whether *terrain's placement* is doing the work or its *selectivity* is. Direct
analogue of D213's shuffled-outcome control, which found 54% of noise draws manufacture a
surviving rule.

**Rotation null** on the gated position series — the timing control D201 lacked and D202
established as necessary, preserving exposure, autocorrelation and net tilt exactly.

## The counterfactual is mandatory

WP7 required *"rejected triggers + hypothetical outcomes"* and D198 is why: a confirmation
filter there beat its baseline on both symbols and was worthless, because **the signals it
discarded scored +0.785 and +0.310 against the kept ones at −0.288 and −0.183.** A filter
can improve the book it keeps by throwing away the winners. Rejected trades' outcomes are
reported beside the kept ones, always.

## Predictions

- **H1** — `aligned` fails hurdle 1 on both symbols. Confidence **high** (D197: dead even
  against randomly placed mass).
- **H2** — `inverted` gains ≥ +0.10R gross on at least one symbol. Confidence **moderate**:
  D202's 2.6th percentile is a real measured anti-signal, and inverting a reliable error is
  the one mechanism here with evidence behind it.
- **H3** — neither direction clears hurdle 2 on both symbols. Confidence **high**. A gate
  changes which trades are taken, not what the wrapper risks, and the toll is a function of
  the stop.
- **H4** — the gate-shuffle control produces a gain within half of the real gate's, i.e.
  most of any effect is selectivity rather than placement. Confidence **moderate-high**.
- **H5** — the gated book clears **none** of the three Sharpe bars, including the lowest.
  Confidence **high**.

H5 is the one to watch. If the result clears the fresh bar and fails the combined one, the
study has done its job precisely: it will have produced a number that would have been
publishable as a first study and is not publishable as the 396th look at the same data.

## Ledger

Opens at **12**. Disclosed adjacent and inherited for the combined bar: the structure
programme's **124** and the terrain programme's **259**.

---

# RESULT — appended 2026-08-24, nothing above it edited

**Nothing clears anything.** 0 of 12 cells clear the gross-R hurdle, 0 of 12 beat the
shuffle control, 0 of 12 clear a Sharpe bar — including the lowest one, the fresh count that
pretends none of the history exists.

## The three bars, which is what this study was asked to show

| bar | looks | required annual Sharpe | cells clearing |
|---|---:|---:|---:|
| fresh | 12 | 1.27 | **0 of 12** |
| structure only | 136 | 1.69 | **0 of 12** |
| combined | 395 | 1.83 | **0 of 12** |

Best observed Sharpe across every cell: **−2.28**. Worst: **−6.00**.

**So the distinction between the bars never arises.** The question was whether a result
would have been publishable as a first study and disqualified only by the 395 looks behind
it. It would not have been publishable as a first study either. **This is not a result that
history killed; it is one that was never there.** Had it come in at, say, +1.4 Sharpe, the
table would have read PASS / fail / fail and the price of the history would have been
visible as exactly one line — that is what the three bars are for, and this run did not need
them.

## The gate

| | BTC | ETH |
|---|---:|---:|
| primary (`inverted / zero`) gross advantage | **−0.030R** | **+0.020R** |
| net R at 40 bps/side | −1.642R | −1.409R |
| cells beating the shuffle control | 0 of 6 | 0 of 6 |

**H2 is falsified.** It predicted `inverted` would clear +0.10R on at least one symbol, on
the strength of D202's measurement that this reading is anti-predictive at the 2.6th
percentile. It does not.

**The direction fared better than the effect, and that distinction is worth keeping.**
`inverted` averages −0.007R against `aligned`'s −0.038R and wins **5 of 6** paired cells. So
D202's anti-signal does show up in the sign — faintly, consistently, and at perhaps a
twentieth of the size needed to matter. The pre-registered prior pointed the right way at
something far too small to trade, which is a more precise outcome than "wrong".

**In 8 of 12 cells the trades the gate REJECTED outperformed the ones it kept.** D198's
finding repeating: a filter can improve nothing while looking like it filters, and pricing
the discarded book beside the kept one is the only way to see it.

## The census that was a tautology, and had to be rebuilt

The first version compared the full-series price grid against one built from the first half
and returned **exactly zero** on both symbols. Not a result — a tautology. `Grid.bucket`
depends only on `ln_min`, this fixture's lowest low falls in the first half on both symbols,
and causal deposits put no mass above the prefix grid's top at an early bar. **It could not
have failed.**

Rebuilt to perturb the axis *origin* by half a bucket — the largest misalignment the
discretisation admits — it says something real:

| symbol | trades | mean shift | max shift | sign flips |
|---|---:|---:|---:|---:|
| `BTCUSDT` | 3,750 | 0.0748 | 1.1017 | **215 (5.73%)** |
| `ETHUSDT` | 3,640 | 0.0573 | 0.9375 | **145 (3.98%)** |

**Roughly one gate decision in twenty is an artifact of where the buckets happen to fall.**
That bounds the precision of any gate built on this field: an advantage smaller than the
noise floor set by the discretisation cannot be trusted, and every advantage measured here
is inside it.

This is a limitation of the inherited field, not of the gate. `test_terrain_field.py` knew
the axis was not causal — its look-ahead test passes the same grid to both arms with the
comment *"same axis, or the buckets alone would differ"* — and pinning around it is the
right call for a **signal**, where the axis is a discretisation choice. For a **gate**, which
reads only the sign, it needed a number. Now it has one.

## Predictions, scored

- **H1** — `aligned` fails hurdle 1 on both symbols. **Confirmed.**
- **H2** — `inverted` gains ≥ +0.10R gross on at least one symbol. **Falsified.**
- **H3** — neither direction clears hurdle 2. **Confirmed**; the toll is a function of the
  stop and a gate does not touch stops.
- **H4** — the shuffle control produces a comparable gain. **Confirmed**, and more strongly
  than predicted: 0 of 12 cells beat it at all.
- **H5** — the gated book clears none of the three bars, the lowest included. **Confirmed.**

Four of five, with the one falsification on the hypothesis that had the most evidence behind
it. Worth noting: the prediction I held at *moderate* confidence is the one that failed, and
the four at *high* confidence all held — which is the calibration this project has been
tracking since D199.

## What this cost, and what it bought

**12 looks**, and the exception spent against D203's stop.

What it bought is a clean answer to a question that had been open since terrain WP7 was
cancelled: *does the map help someone else's signal?* No — and not because the multiplicity
bar was too high, which was the interesting failure mode, but because there is nothing there
at any bar. Terrain WP7 can now be marked answered rather than unscheduled.

**The stop is restored.** The exception was for one bounded question and it is spent. D203
stands again in full, and a second override would need its own record and would not inherit
this one's reasoning.
