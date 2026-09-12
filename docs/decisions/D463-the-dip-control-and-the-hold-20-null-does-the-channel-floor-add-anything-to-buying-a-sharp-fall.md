# D463 — the dip control and the hold-20 null: does the channel's floor add anything to buying a sharp fall?

*Pre-registration, written before the runner change (R8). Runner: D451's
`scripts/run_d451_grow_trades.py --source hand --rule dip` (two runs: on all bars, and on bars
where the channel is drawn) and `--rule level --head 20`. Outputs `data/d463_dip_all.json`,
`data/d463_dip_drawn.json`, `data/d463_level_hold20.json`. Sequel to
[D462](D462-RESULT-the-level-read-is-the-first-channel-cell-above-its-null-plus-44-bp-gross-over-five-bars-with-a-positive-median-and-it-does-not-clear-cost.md).
In-sample, the mining panel, 1,573 names; no holdout is read.*

## 1. The question

D462's level rule — long on a close at or below the bottom tenth of the channel, whose support
level sits 4% under the pivot lows — earned +43.6 ± 5.6 bp gross over five bars, 41 SE above its
within-name rotation null, on both constructions. Such a close is, by construction, a close
well below the recent lows: a sharp fall. Short-horizon reversal after sharp falls is a known
effect, and the rotation null does not control for it, because it re-times the same events to
bars that are not falls. **A control must break the claimed ingredient**: the channel. So the
same rule, with no lines.

## 2. The control

`--rule dip`: long on the close of a bar whose close is more than **X** below the lowest low of
the previous **N** bars, short on a close more than X above the highest high of the previous N
bars; held H bars with the same run extraction; H swept {1, 3, 5, 10, 20}, headline 5; the same
nulls, books and audits. Two runs:

- **dip-all**: on every eligible bar, no lines consulted.
- **dip-drawn**: the same, restricted to bars on which the hand cell has both lines drawn — the
  channel's *existence* without its *level*.

X = 4%, N = 30 (the margin the level rule's floor carries, and the span of the principal's
lines); the event count is reported against D462's 15,603 so that a mismatch in depth is
visible rather than argued away.

## 3. The null at the cost-clearing hold

`--rule level --head 20`: D462's rule with the headline hold at 20 bars, where net was +37, so
the per-trade rotation null and the book null are computed there.

## 4. Predictions, in the runner's quantities

- P1. **dip-all long at H = 5 earns most of it**: gross between +25 and +45 bp, above its own
  rotation null p95. The channel is mostly the dip.
- P2. **dip-drawn adds little**: dip-drawn minus dip-all at H = 5 within ±10 bp. If it is above
  +10, the channel's existence carries information beyond the fall.
- P3. **The level rule beats both by less than 15 bp**: D462's +43.6 minus dip-drawn at H = 5
  below +15. If the difference is above +15, the *position in the channel* is doing work the
  fall alone does not.
- P4. The hold-20 level null: the score (+112.8) above its p95 by more than 2 SE — the effect is
  real at that hold too; the book at hold 20 above its null p95 on return.
- P5. Shorts: the dip short at H = 5 near zero (−10 to +15), as the level short was.

## 5. What follows

If P1–P3 hold as written: the channel is not the ingredient; the daily channel line closes with
that said, and what remains is a short-horizon reversal effect that belongs to a different line
(and is itself not new). If P3 fails upward — the level rule beats the dip by more than 15 bp —
the channel's floor is doing work, and the next step is a held-out test of the *level rule*, on
the principal's word, with its own pre-registration.
