# D255 — Stops and targets on the book and on each arm

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-28
**Area:** Strategy research

---

## Provenance — this is a re-run of closed cells and the record says so first

**Stops and targets have failed five times in this programme:**

| | what failed |
|---|---|
| [D235](D235-stops-and-targets-on-the-recovery-rule.md) | all seven cells on S1. Best real +0.047 against a rotation-null p95 of −0.284 |
| [D236](D236-portfolio-level-risk-controls.md) | all six portfolio controls reduce drawdown, **none** improves risk-adjusted return |
| [D240](D240-the-uptrend-onset-arm.md) A1–A4 | A2 cleared at the 99.6th uncorrected and **died at the 71.7th** out of sample |
| [D249](D249-the-inverse-wedge-breakout.md) W3 | cleared its overlay null and was flagged **not quotable** |

**So this record must justify itself before it spends anything.** Three things are new:

1. **The combined book `C` has never had an overlay applied.** D235 was S1 alone and predates
   [D241](D241-the-combined-book-and-capital-allocation.md); D240 was S2 alone. **`C` is not a
   re-run.**
2. **A measured mechanism, not a hope.** A pre-screen over 92,736 ETF cells and 33,210 crypto cells
   (R9-lagged, `scripts/prescreen_wedge_volatility.py`'s sibling method) found the effect is
   **asymmetric**: a take-profit helps and a stop-loss mostly hurts.

   | trailing 5-bar move | ETF forward 21-bar (base +5.28%) | n |
   |---|---:|---:|
   | ≤ −20% | **+89.74%** — a stop cuts the recovery | 152 |
   | ≤ −10% | +22.59% — a stop cuts the recovery | 1,620 |
   | ≥ +10% | +22.92% — a target cuts a runner | 1,576 |
   | **≥ +20%** | **−14.40%** — **a target helps** | **121** |

3. **The reason it may still fail is now measurable in advance**: that `≥ +20%` bucket contains
   **121 instances in 16.8 years across 57 names**. **Reachability, not the effect, is the likely
   binding constraint**, and this study measures it before scoring a single cell.

---

## The rules

**Fixture:** `universe_daily_extended_raw.csv.gz`, 57 ETFs, 16.8 years — the book's home fixture.
Arms frozen exactly as [BOOK.md](../BOOK.md) admits them.

**Overlay convention**, inherited from `run_stops_targets.overlay` and stated because it decides
every number: `position[t]` earns `log(C[t]/C[t-1])`, so a position held at bar `a` was entered at
`C[a-1]`. **The gain is known at the close of `t`, so an exit decided there takes effect at `t+1`.**
Close-to-close per D235 — daily OHLC cannot distinguish a touch from a gap through the level.
**Once exited, stay flat until the base signal cycles**, otherwise the overlay is defeated by
immediate re-entry.

## The grid — 21 cells, counted in full

| | levels |
|---|---|
| **stop-loss** | −5%, −10%, −20% |
| **take-profit** | +10%, +20%, +30% |
| **combined** | TP +20% with SL −20%, declared in advance as the a priori best pair from the pre-screen |
| **arms** | S1, S2, **C** |

**3 arms x 7 overlays = 21 cells.** No level is added after the run. **This is a search and it is
counted as one.**

## Hurdles

- **H — carries the verdict. [R7](../RULES.md)'s matched-exit-count overlay null**, at **≥95th
  percentile on Sharpe AND money.** Keep the base book, cut **the same number of trades** short, at
  random trades and at random points inside their own spans, with cut fractions drawn from the real
  overlay's own pool. `run_uptrend_onset.null_book`, reused unmodified. **A rotation null is the
  wrong control here and D235 failed by using one.**
- **B — beat the unmodified base arm** on excess Sharpe. An overlay that does not improve what it
  modifies is pointless whatever percentile it occupies.
- **F — the best-of-21 floor (D228)**, because 21 cells is a real search and D240's stop cleared at
  the 99.6th uncorrected and died out of sample.
- **Reachability, reported BEFORE any cell is scored:** what fraction of each arm's trades ever
  touch each level while held. **If a level is unreachable the cell is reported as vacuous rather
  than as a pass**, because an overlay that never fires trivially matches its base.

## Predictions, committed before the runner exists

| | prediction | confidence |
|---|---|---|
| **Y-a** | **Reachability is the binding constraint.** Under a third of trades ever touch +20%, and under a tenth touch +30% | **~75%** |
| **Y-b** | **Take-profit cells improve raw metrics and fail H.** Five prior overlays did exactly this — the improvement is exposure removal, which the matched-exit-count null also gets | **~80%** |
| **Y-c** | **Stop-loss cells actively hurt S1**, and more than they hurt S2. S1 enters on `md_L ≤ 0` — it buys the dip by construction, so a stop cuts the signal (D236's mechanism, now measured from the universe side at +89.74%) | **~85%** |
| **Y-d** | **No cell clears H, B and F together** | **~80%** |
| **Y-e** | **`C` behaves as a blend and adds nothing** — its best cell lands between S1's and S2's, revealing no interaction the arms did not already show | **~65%** |

**Y-c is the one worth being wrong about.** If a stop *helps* S1, the entry-dip mechanism this
programme has asserted since D236 is wrong, and that matters more than any cell.

## Stop

**If no cell clears H, B and F, stops and targets are CLOSED for this book** — no further levels,
no trailing variants, no per-symbol calibration, no ATR-scaled version. **Six failures is enough**,
and a seventh study would need a new mechanism rather than a new parameter.

**What this record does NOT close:** the same overlay on a **single-name** universe, where the
pre-screen predicts the `≥ +20%` bucket is populated rather than nearly empty. That is D252's
fixture and a separate registration.

## Ledger

| count | N |
|---|---:|
| fresh — 21 cells | 21 |
| + the reachability diagnostic (3 arms x 6 levels) | 39 |
| + carried from D254 | 45,968 |
| **total** | **46,007** |

---

## AMENDMENT, made after the run and before the verdict — two control defects

**1. The registered best-of-21 floor was misconstructed, and it is mine.** It took the maximum
across all 21 null distributions — but those span three arms with **different baselines** (S1
+0.478, S2 +0.511, C +0.620), so S1's cells were being judged against C's null distribution, which
is a different book. The floor came out at **+0.707**, above every cell *and above every base arm*.
**A hurdle that cannot be passed by construction is not a test.** It is recomputed **within each
arm** below.

**2. A control the registration named and did not build, raised by the principal.**

> *"On the nulls, having consistent stop losses and take profits will tell you if they help the
> strategy or not, whereas having random stop losses and take profits tells you which stop loss and
> take profit is best."*

**R7's null keeps the base book and cuts the same NUMBER of trades at RANDOM POINTS.** That asks
*"is this level informative about which trades to cut and when?"* — and with 12 cuts on 2,553
trades it establishes only that twelve particular cuts beat twelve random ones.

**It does not ask the question a level SWEEP needs: is this level special among levels?** The
correct control applies the overlay **consistently at a level drawn at random**. Built here: 600
levels per (arm, type), log-uniform on [2%, 50%]. **This is registered as an amendment rather than
folded in silently, because it was added after seeing the cells.**

---

## RESULT — CLOSED. Every cell fails, and the ceiling is the reason.

**Produced:** 2026-08-28 · `uv run python scripts/run_stops_book.py` · `STOPS_BOOK_RESULTS.md`

### Reachability, reported before any cell — and Y-a is confirmed far past its stated margin

| arm | trades | **median max gain** | median max loss | reach +20% | reach +30% | reach −10% |
|---|---:|---:|---:|---:|---:|---:|
| **S1** | 2,374 | **+2.37%** | −1.55% | **2.8%** | 0.8% | 2.1% |
| **S2** | 393 | +5.89% | −3.19% | 9.7% | 5.3% | 11.7% |
| **C** | 2,553 | +2.84% | −1.78% | 4.2% | 1.5% | 3.7% |

**The median S1 trade's entire lifetime range is +2.37% / −1.55%.** A +20% target fires on **60 of
2,374** trades. **Y-a predicted "under a third reach +20%"; the answer is 2.8%.**

### The level-randomised null — three cells look special, and all three are take-profits

| cell | excess Sharpe | vs base | **percentile among 600 random levels** |
|---|---:|---:|---:|
| **S1:TP20** | +0.494 | +0.016 | **99.2nd** |
| **S2:TP30** | +0.593 | +0.081 | **99.8th** |
| **C:TP30** | +0.658 | +0.037 | **99.8th** |
| S1:SL10 | +0.486 | +0.007 | 93.7th |
| C:SL10 | +0.668 | +0.048 | 87.7th |
| S1:TP10 | +0.382 | −0.096 | 19.0th |
| C:TP10 | +0.494 | −0.126 | 29.8th |

**Every "special" cell is a take-profit and none is a stop** — the pre-screen's asymmetry
reproduces exactly.

### And the corrected floor kills all three

| arm | **within-arm best-of-2 p95** | base | best registered cell |
|---|---:|---:|---:|
| S1 | **+0.490** | +0.478 | +0.494 |
| S2 | **+0.627** | +0.511 | +0.598 |
| C | **+0.672** | +0.620 | +0.668 |

**S2 and C fail outright. S1 clears by +0.004, which is noise.** A cell at the 99th percentile of
600 random levels is roughly what picking the best of six registered levels produces by chance —
**the floor is the correction for exactly that, and it says no.**

### The number that closes it

**The single best level out of 600, chosen with perfect hindsight, improves S1 by +0.017 Sharpe.**

| | levels beating base | best level's edge |
|---|---:|---:|
| S1:TP | 22.8% | **+0.017** |
| S1:SL | 28.0% | +0.019 |
| C:TP | 31.8% | +0.037 |
| **S2:SL** | **61.8%** | **+0.121** |

**That is a ceiling, not an estimate.** No take-profit rule of this form can add more than about two
hundredths of a Sharpe point to S1, because **97.2% of its trades never travel far enough to be
cut.** Reachability, not the conditional edge, is what closes this.

**The one row that is not dead: `S2:SL`.** 61.8% of *all* stop levels beat the base, best +0.121 —
so a stop generically helps the trend arm, which is what a trend arm should want. **But no
particular level is special** (S2:SL10 lands at the 83.3rd, S2:SL20 at the 74.7th), so the effect is
*having a stop*, not *having a 10% stop*. And S2:SL10 fails R7's money leg at the 90.8th while
S2:SL20 clears H and fails the corrected floor. **Not admissible, and recorded as the one place a
future study could look.**

### Scoring

| | prediction | outcome |
|---|---|---|
| **Y-a** | reachability is binding; under a third reach +20% | **CONFIRMED, understated** — 2.8% on S1 |
| **Y-b** | take-profits improve raw metrics and fail H | **CONFIRMED** — and they also survive the level null and die on the corrected floor |
| **Y-c** | stops actively hurt S1 more than S2 | **CONFIRMED** — S1:SL05 −0.029 at the 30.2nd percentile, while 61.8% of S2 stop levels *help*. **The entry-dip mechanism holds** |
| **Y-d** | no cell clears H, B and F together | **CONFIRMED** |
| **Y-e** | C is a blend and adds nothing | **CONFIRMED** — C's pattern tracks S1's, being 93% S1 trades |

### The stop applies

**CLOSED. Stops and targets are finished for this book** — no further levels, no trailing variants,
no per-symbol calibration, no ATR-scaled version. **Six failures, and this one measured the ceiling
rather than merely failing to clear a bar**, which is a stronger form of closure than the previous
five.

**NOT closed:** the same overlay on a **single-name** universe. The pre-screen predicts the +20%
bucket is populated there rather than nearly empty, and **reachability is precisely the quantity
that should differ.** That is D252's fixture and a separate registration.
