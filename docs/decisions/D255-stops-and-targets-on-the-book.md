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
