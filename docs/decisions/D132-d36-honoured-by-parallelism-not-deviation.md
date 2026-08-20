# D132 — D36's n ≥ 10,000 is honoured by parallelising, not deviated from; every p-value carries its Monte Carlo standard error

**Status:** Committed
**Date:** 2026-08-18
**Category:** Analytics
**Source:** Breakout Monte Carlo session

## Decision

The breakout null suite runs at **n = 10,000 in every cell**, path nulls included, so
D36/D81's floor is met without exception. A reduction to n = 2,000 was budgeted in advance
as an explicit, costed deviation and then **not taken**, because the work parallelises
without changing any number.

Two supporting commitments:

1. **Every p-value is reported with its Monte Carlo standard error.** The p-value itself is
   the add-one empirical form `(1 + #{null at least as extreme}) / (n + 1)`; the standard
   error is the binomial `sqrt(p(1-p)/n)` of that estimate.
2. **Parallelism is admissible because it is provably inert.** Every simulation's seed is
   derived up front from the root seed via `numpy.random.SeedSequence`, never from a loop
   counter or a worker id, and results are re-assembled in index order. `--workers` changes
   throughput and nothing else, and a test asserts serial and pooled runs agree exactly.

## Rationale

**The measured cost, recorded because the deviation was nearly taken on it.** One path-null
simulation is a full strategy re-run — walk-forward spans re-derived, warm-up prefix, the real
cost stack, next-open fills, trade-episode extraction — over ~3,700 bars. Single-process:
**101 ms on BTC-USD, 65 ms on ETH-USD**. Across the 16-cell grid (D131), n = 10,000 is
~3.7 hours of serial compute, which is what made a deviation look necessary. Twelve worker
processes bring the effective cost to ~20 ms/simulation and the whole grid to well under an
hour. At that price there is no deviation to justify, and honouring a standing decision beats
documenting a departure from it.

**Why the SE is reported anyway.** It is the honest expression of a Monte Carlo p-value's
resolution at *any* n, and reporting it only when n is small would train a reader to treat
its absence as "this number is exact". At n = 10,000 the floor a p-value can report is
1/10,001 ≈ 0.0001, and an empirical p of exactly zero is a statement 10,000 draws cannot
support — the add-one form reports the floor instead, which is why it is used.

**Why seeds are derived rather than offset.** `seed + i` gives correlated streams on some
generators and is a silent source of non-independence in exactly the tail the p-value is read
from. `SeedSequence` also gives the property that the first *k* seeds of a longer draw are the
same seeds, so every cell in the grid is a paired comparison on identical null paths and each
cell reproduces on its own — the block ladder and the two cost tiers differ only in the thing
being varied.

**The relationship to D34.** D34 requires a seed on every stochastic component. This adds that
the seeding scheme must also be *independent of the execution schedule*: a study whose numbers
depend on how many cores ran it is not reproducible, whatever seed it logged.

## Consequence

`scripts/run_breakout_nulls.py` takes `--workers` (default 12) and `--n-sims`. Neither belongs
in the artifact's numbers; both are recorded in it, so a reader can see what was run and a
re-runner can match the wall clock rather than guessing at it.
