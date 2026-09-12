# D462 — the level read on the hand cell, in-sample: the one reading of the channel none of the five cells made

*Pre-registration, written before the runner change (R8). Runner: D451's
`scripts/run_d451_grow_trades.py --source hand --rule level`, output `data/d462_hand_level.json`.
Sequel to [D461](D461-RESULT-the-hand-cell-trades-like-every-other-causal-channel-plus-12-bp-gross-below-its-own-rotation-null.md).
In-sample, the mining panel, 1,573 names; no holdout is read. The principal asked for this run
and for the daily channel line to be closed in writing after it, either way.*

## 1. The rule

Not the direction of the lines but **where the close sits between them**. At bar t, with both
lines of the hand cell drawn (their levels carry the 4% margin), the close's position in the
channel is

    pos = (log close − support level) / (resistance level − support level)

**Long** on the close of a bar with pos ≤ 0.10 (at or below the bottom tenth of the channel),
**short** on pos ≥ 0.90, each held **H bars** after the entry bar; a further qualifying bar
inside the hold extends it (the same run-extraction as D450's rule, on a different state
series). H swept over {1, 3, 5, 10, 20}, headline 5. Both sides on the same bar: flat.

Two sources, the same run: **HAND** (D460's cell) and **CAUSAL** (D399's `CELL_FINAL`). Same
eligibility, split guard, spread, per-trade rotation null (200 draws) and book null (300 draws),
same audits, with the no-future audit rewritten for this state series.

## 2. Predictions, in the runner's quantities

The prior is the touch effect of D412–D433: +10 / +10 / +13 bp gross on three name sets, net
Sharpe ~0 on all. So:

- P1. HAND long at H = 5: gross mean per trade between **0 and +25 bp**; net negative against
  the ~70 bp spread of the names held. Short at H = 5: between −20 and +10.
- P2. Neither side above its per-trade null p95 by 2 SE. (The rotation null here re-times
  mean-reversion events; its p50 is the drift over H bars, a few bp.)
- P3. The long gross grows with H but the *per-bar* gross does not: gross at H = 20 below four
  times gross at H = 5.
- P4. CAUSAL under the same rule: the same shape, within 10 bp of HAND at H = 5.
- P5. Median gross per trade below the mean on the long side (a tail-carried mean, as every
  channel cell so far).

## 3. What follows

A HAND long gross above +25 bp at H = 5 *and* above its null p95 by 2 SE with a positive median:
a held-out test on unseen names before anything else. Otherwise the daily channel line is
closed in writing — direction (D434, D450, D451, D452, D461) and level (D462) both read, on a
construction that reproduces the principal's own lines — and the labelled set, the scorer and
the hand cell are kept as tooling.
