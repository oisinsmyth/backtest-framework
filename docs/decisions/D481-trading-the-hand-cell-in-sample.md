# D481 — trading the hand cell, in-sample: does a construction that draws the principal's lines change what their direction is worth?

*Pre-registration, written before the runner change (R8). Runner: D478's
`scripts/run_d478_grow_trades.py` with `--source hand`, output `data/d481_hand_trades.json`.
Sequel to [D480](D480-RESULT-the-hand-cell-the-pivot-construction-re-dialled-reaches-the-eye-on-gradient-and-the-swing-envelope-loses.md).
In-sample only, the mining panel, 1,573 names; no holdout is read.*

## 1. What is traded

The **hand cell** of D480: D399's pivot construction re-dialled against the principal's 140
hand-drawn lines — pair rules off, one-bar pivots, no width kill, one pivot carried across a
break, a 3% one-bar close break, staleness 25/12, a 4% margin on the drawn level. On the card it
is the only construction above 85% sign agreement (92 / 87%) with recall above 60% (69 / 71%);
gradient within 27 / 40%/yr of the principal's. It draws five bars before the principal does.

The rule is D477's, unchanged: **in while there is a trend, out when there is not** — both lines
drawn, gradients of the same sign, both steeper than `gmin`, read at the close; enter at that
close, exit at the close of the first bar no longer in it. `gmin` ∈ {0, 10, 25, 50, 100, 200}
%/yr, headline 25. Second source in the same run: **CAUSAL**, D399's `CELL_FINAL`, which must
reproduce D478/D479 (+16.8 / −41.9 at `gmin` ≤ 25). Same eligibility, split guard, spread,
per-trade rotation null (200 draws) and book rotation null (300 draws), same audits.

## 2. Predictions, in the runner's quantities

- P1. HAND long at `gmin` 25: gross mean per trade between −20 and +30 bp; short negative; neither
  side above its per-trade null p95 by 2 SE. (D477's mechanism — a confirmed direction is a late
  one — is about confirmation, and this cell confirms *earlier*, so if anything moves it is the
  long side, upward; P1 still says not by enough.)
- P2. Both lines drawn on more than 40% of bars (D399: 28%); more long trades than CAUSAL's
  28,740 at the headline.
- P3. The gradient sweep falls: HAND long gross at `gmin` 200 below `gmin` 0.
- P4. CAUSAL reproduces exactly.
- P5. The rotation null's long p50 is positive and above the score on both sources.

## 3. What would change the plan

HAND long gross above its null p95 by more than 2 SE with a positive median at the headline, or
P3 inverted: a held-out test for this line on unseen names. Otherwise the line's direction is
closed as an entry on four constructions, and the channel's *level* — now a defined quantity
through the 4% margin — is the next thing to read.
