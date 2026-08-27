# D225 — Does the volume gate survive a change of sampling rate?

**Status:** Committed — **recorded AFTER the run**, which is a departure from this
programme's practice and is disclosed below rather than glossed
**Date:** 2026-08-27
**Category:** Validation & research integrity
**Source:** A user request to replicate D224's surviving cell on resampled 1-hour bars with
the gate and no stops, delegated to a subagent

> This record has no pre-registration section because there was none. What that costs, and
> what it does not, is stated in *Provenance* below.

## Provenance, stated first because it changes how everything else should be read

**The run preceded the record.** D217 through D224 each committed a pre-registration before
their runner existed; this did not. Two consequences, and they are different sizes:

**The replication itself is largely protected.** The hypothesis, the arm, the gate
construction, hurdle H, the null and the minimum detectable effect were all fixed in D224
*before* this ran. Re-testing an already-pre-registered claim on a different sampling rate is
confirmatory, and there was nothing left to choose. That is the low-risk half.

**The window sweep was not.** The subagent, on its own initiative and correctly, swept the
gate window across ten values on two grids and two symbols to test whether the working window
was a plateau or a spike. **That is an unregistered search of 40 cells**, it produced the most
important finding in this record, and it is counted in the ledger as what it is. **Any future
use of the 50-hour window is now an informed choice** — it was not, before this sweep existed.

## What was tested

D221 established the indicator is scale-free in bars: what matters is the wall-clock window,
not the sampling rate. D224 then found a volume gate on 15m bars beat its matched-count random
null on both symbols.

**If the gate effect is real, invariance says it must reproduce at 1h.** If it does not, the
15m result was an artifact of the sampling rate.

| cell | bars | signal | gate |
|---|---|---|---|
| **A** parent | 1h | `(34, 9)` | — |
| **B matched** | 1h | `(34, 9)` | `EMA(50) > SMA(50)` — 50h, the wall-clock match to D224's 200 × 15m |
| **B literal** | 1h | `(34, 9)` | `EMA(200) > SMA(200)` — 200h, the literal parameters |

No stops in any cell. 1h series resampled from the 15m source on the shared calendar (D161);
the fixture has **zero incomplete days**, so 294,336 15m bars became exactly 73,584 1h bars per
symbol. 10 bp per side, PPY 8,760, 8.29 live years.

## Result — it replicates

| symbol | cell | gross Sh | net Sh | net total | exposure | trades | med hold | pct in null (Sh / $) | H |
|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|
| BTC | A parent | +0.672 | −0.398 | −75.2% | 46.1% | 1,872 | 14 | — | — |
| BTC | **B matched** | **+0.953** | **+0.237** | **+89.9%** | 25.3% | 970 | 16 | **99.5 / 100.0** | **PASS** |
| BTC | B literal | −0.192 | −0.911 | −90.2% | 24.0% | 916 | 15 | 0.5 / 0.2 | FAIL |
| ETH | A parent | +0.733 | −0.096 | −35.2% | 46.5% | 1,875 | 14 | — | — |
| ETH | **B matched** | **+1.008** | **+0.462** | **+422.6%** | 25.6% | 978 | 16 | **98.5 / 98.8** | **PASS** |
| ETH | B literal | +0.097 | −0.461 | −78.9% | 24.4% | 941 | 15 | 4.8 / 3.2 | FAIL |

Against D224 at 15m:

| | BTC 15m | BTC 1h | ETH 15m | ETH 1h |
|---|---:|---:|---:|---:|
| Δ net vs parent | +0.489 | **+0.635** | +0.590 | **+0.558** |
| H percentiles | 96 / 96 | **99.5 / 100** | 100 / 100 | **98.5 / 98.8** |

**Same sign, comparable size, H clears on both symbols at both sampling rates.** The gate is
not an artifact of the 15m grid.

Scale of the effect against the mechanical alternative: removing half the parent's trades **at
random** gains about **+0.11** net Sharpe, because the average trade is fee-negative. The gate
gains **+0.635**. It beats trading-less by roughly six times.

## The finding that matters more — the working window is one point wide

| window (h) | none | 12 | 24 | 36 | **50** | 72 | 100 | 140 | **200** | 300 | 480 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC net Sh | −0.398 | −0.188 | −0.128 | −0.249 | **+0.237** | −0.103 | −0.066 | −0.263 | **−0.911** | −0.477 | −0.443 |
| ETH net Sh | −0.096 | −0.040 | **+0.673** | +0.121 | **+0.462** | +0.140 | −0.046 | −0.334 | **−0.461** | −0.104 | −0.362 |

**50h is the only positive-net window on BTC out of ten, and both its immediate neighbours are
negative** (36h −0.249, 72h −0.103).

**At 200h the identical construction inverts into a significant anti-signal** — 0.5th
percentile of its own null on BTC. That is not attenuation, it is reversal. The per-trade
decomposition shows why: the two gates are close to independent selectors (φ ≈ −0.11) picking
near-disjoint halves. The 50h gate keeps trades averaging **+26.6 bp** and blocks −2.6 bp; the
200h gate keeps **−5.3 bp** and blocks **+29.7 bp**. It is very nearly the 50h gate run
backwards.

**A real volume-regime effect should degrade gracefully as the lookback lengthens, not
reverse.** This is the strongest argument on the record against the gate being what it appears
to be.

Mitigating, and it is genuinely mitigating: the 50h window was **not selected by search**. It
fell out of fixing "200 bars" on the 15m grid, and the wall-clock duration was never chosen.
The spike is therefore a fact discovered after the fact rather than a cell that was hunted.

## A correction to the subagent's interpretation

The subagent found the *entire* window-response curve agrees between the 15m and 1h grids
(ρ ≈ 0.89, peak at 50h and trough at 200h on both) and argued this makes the spike "much
harder to write off as an artifact."

**That does not follow, and the record should not carry it.** The 1h series is resampled from
the same 15m bars — one price path at two resolutions, not two samples. D221 already
established the estimator is scale-free in bars, so agreement between the grids is a
*mathematical consequence* of that result. **The check validates the implementation; it is
silent on whether 50h is special.**

The partially independent evidence is the two symbols, and there the fine structure
disagrees: ETH shows a large spike at 24h (+0.673) where BTC is negative (−0.128).

## Two claims that are now separate

D221 established **the signal is scale-free in bars.** This study establishes that **the gate
is not scale-free in wall-clock** — it is window-critical, to the point of inverting. Those
are different properties and it is worth having them apart:

> The indicator does not care how finely you sample a given window. The gate cares enormously
> which window you pick.

## Floors

| symbol | cell | net Sh | floor @ 10 (fresh) | floor @ 3,833 (verdict) | fresh | verdict |
|---|---|---:|---:|---:|:--:|:--:|
| BTC | B matched | +0.237 | +0.368 | +0.847 | no | no |
| ETH | B matched | +0.462 | +0.378 | +0.869 | **yes** | no |

Computed from the **null's** variance, not the study's cells, per D224's correction. They agree
with D224's 15m floors to ~0.02, as they should — same null construction.

**Nothing clears the verdict floor.** ETH clears the fresh-look floor by 0.084. This is D214's
pattern for the second study running: publishable as a first look, not as the 3,833rd.

## Verification

- **Bit-exact reproduction of the committed D224 artifact.** Feeding the replication's position
  builder D224's config (15m, `(136, 36)`, `VOL_WINDOW = 200`, no stop) reproduces
  `data/assembled_strategy_summary.json` to **Δ = 0.00e+00** on net Sharpe, gross Sharpe *and*
  trade count for all four rows. The builder is D224's with the stop branch removed.
- **Deterministic on re-run**: the artifact is byte-identical across two independent runs.
- **Cross-check against D221's committed artifact**: 1h parent gross +0.6724 (BTC) / +0.7333
  (ETH) against D221's +0.6808 / +0.7331. The BTC gap of 0.0084 is the ~12-hour span
  difference; scoring from D221's common start reproduces +0.6808 exactly.
- **No look-ahead**: multiplying volume at bar 40,000 by 10⁶ changes the gate at no index
  ≤ 40,000, both windows, both symbols.
- **Resample integrity**: `ResampleReport.check()` passed; volume conserved to < 1e-6 relative;
  `len(15m) == 4 × len(1h)` asserted per symbol.

## Ledger

| block | looks |
|---|---:|
| replication cells — 3 × 2 symbols, confirmatory of D224's pre-registered claim | 6 |
| **window sweep — UNREGISTERED, 10 windows × 2 grids × 2 symbols** | **40** |
| **fresh, D225 only** | **46** |
| inherited from D217, D218, D220, D221, D222, D224 | 94 |
| crypto-fixture prior + structure/terrain bar | 3,739 |
| **verdict count** | **3,879** |

The sweep is the larger half of this study's fresh count and it was not pre-registered. That is
the cost of the ordering, stated in the ledger rather than argued away.

## What this changes

**The gate replicates and is not a sampling artifact.** That was the question and it is
answered.

**But the window fragility is a serious mark against it**, and it is the thing any future work
must address first. An effect that lives at one window and inverts two doublings away is not
yet a regime filter; it is a cell that works.

**The 50-hour window is now contaminated for selection purposes.** It was clean when D224 used
it — it fell out of a parameter, not a search. It is not clean now, and any study that picks
50h from here carries these 40 looks.

**Nothing is promoted.** Two studies have now put this gate above its selectivity null and
below its multiplicity floor.
