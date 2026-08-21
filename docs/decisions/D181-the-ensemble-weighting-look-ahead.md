# D181 — The ensemble weighted itself with whole-sample volatility, and the guard that should have caught it does not reach analytics

**Status:** Committed
**Date:** 2026-08-21
**Category:** Validation & research integrity
**Source:** Found while confirming, for an unrelated question, that the long and short books are independent

## What was wrong

`combine_books()` and `combined_series()` set their inverse-volatility weights from
`statistics.stdev()` over the **entire out-of-sample series**, then applied those weights
from the first bar:

```python
sd_a = statistics.stdev(a)          # the WHOLE series
sd_b = statistics.stdev(b)
wa, wb = 1.0 / sd_a, 1.0 / sd_b     # applied from bar 0
```

The calmer leg was handed exactly the right weight in advance. It is a mild look-ahead —
two scalars, no per-bar leakage, and neither leg's trades are affected — but every combined
Sharpe this project has published was inflated by it, and it was undocumented in D172, D179
and `BREAKDOWN_RESULTS.md`.

## The rule it broke already existed

D44 pins the convention that realized volatility is measured on a window **ending at the
previous bar**, and `InverseVolatilityWeight` implements it for strategy-level sizing. The
ensemble layer simply did not follow it.

**And that is the part worth recording.** The structural look-ahead guard (D32/D56) makes
this class of error *impossible* for a strategy: `DataView` is constructed already sliced,
so a strategy physically cannot read a future bar. The ensemble operates on **return
series**, not on a `DataView`, so none of that protection applies.

> The guard makes look-ahead impossible for strategies and does nothing for analytics built
> on their output.

Every ensemble, attribution and portfolio layer added from here is outside it. The
protection is real and its boundary was never written down.

## The missing test

Nothing asserted that the weight applied at bar `t` is unaffected by returns at bar `t` or
later. That single property is the whole definition of the bug, and it is now
`test_ensemble_weight_at_a_bar_ignores_that_bar_and_every_later_one`.

## The fix, and the false start that produced the more interesting finding

**First attempt: a 63-bar trailing window**, on the reasoning that 63 is
`BreakoutStudyConfig.test_size`, so the weight would refresh on the same timescale the
walk-forward refreshes parameters. That reasoning was about the schedule and not about the
data, and the data rejected it immediately — because the run now counted its own degenerate
cases:

| Trailing window | Bars falling back to 50/50 (BTC) |
|---|---|
| **63** | **75.0%** |
| 126 | 51.0% |
| 252 | 24.6% |
| 504 | 11.7% |

**The short book is flat on 88% of BTC's bars and 81% of ETH's.** It is regime-gated, so it
is routinely flat for an entire fixed window and has no volatility to invert. At 63 bars the
"equal-VOL weighted" book was equal-**CAPITAL** weighted three times out of four — precisely
what `EnsembleResult`'s own docstring says the construction exists to avoid.

It also explains a result that would otherwise have looked like good news: removing the
look-ahead *raised* BTC's combined Sharpe from 0.412 to 0.685. That was not the correction
working. It was the 50/50 fallback flattering the book.

**Shipped: an expanding window with a 252-bar warm-up.** Chosen on a stated principle
rather than on the table above — picking the window that produced the best Sharpe would be
exactly the search this project forbids, and it is how 63 got chosen in the first place. The
principle: an allocator sizes strategies by their **long-run** risk, not last quarter's, and
that is most true when one of them is intermittent by design. It is also the only scheme
whose validity does not depend on guessing how long the short book's flat spells run.

252 is `train_size`, an existing pinned constant, and it is a warm-up rather than a window —
there is no window length left to choose. Welford's online variance keeps it O(n); the naive
expanding `stdev` is O(n²) and would have made the 62-symbol universe run intractable.

## The restated numbers

| | Published (whole-sample) | Corrected (expanding) |
|---|---|---|
| BTC combined Sharpe | 0.412 | **0.462** |
| ETH combined Sharpe | 0.649 | **0.570** |
| BTC scored bars | 3,716 | 3,464 |
| ETH scored bars | 2,708 | 2,456 |

The direction is not uniform because two things changed at once: the weights stopped
knowing the future, and 252 warm-up bars left the sample.

**A fragility the warm-up exposed by accident.** ETH's short leg reads **+0.142** over the
full span and **−0.228** once the first 252 bars are dropped. Its positive Sharpe lived
entirely in the earliest part of the sample — the 2018 bear market. Nothing about the short
book's published verdict improves on inspection.

## Two more defects fixed in passing

**Silent truncation.** `combine_books` took `min(len(a), len(b))` and sliced from the end.
Both books currently produce identical out-of-sample spans (BTC 3,717 bars / 59 windows,
ETH 2,709 / 43), so it was a no-op — and a silent one that would have quietly misaligned
dates the first time that stopped being true. It raises now.

**Asymmetric reporting.** `EnsembleResult` carried the long and combined drawdowns but not
the short one, which invites a reader to fill the gap with a number measured over a
different span. All three arms are now quoted over the same post-warm-up span, legs
included — scoring the legs on the full series while the combination starts later would
compare three books over three periods and present the difference as an effect of combining
them.

## What is NOT fixed, and is now reported instead

**Inverse-vol weighting reads a flat book as low-risk, when what it actually is, is
absent.** The mean weight on the LONG leg is **0.389 (BTC)** and **0.453 (ETH)** — the
majority of the risk budget sits on the leg that is flat ~85% of the time and loses money,
*because* it is flat.

This is not a bug introduced here; the whole-sample version had it too. It is a flaw in the
equal-vol construction as applied to an intermittent book, and fixing it properly means
deciding what "risk" means for a strategy that is out of the market most of the time — a
research question, not a defect.

So `EnsembleResult` now carries `mean_long_weight`, and every combined result surfaces it.
The flaw is stated on the face of each report rather than left to be discovered, which is
the same treatment D175 gives the missing liquidation model.

## Consequences

- **The long study is untouched** — `data/breakout_study_summary.json` is byte-identical.
  The long book has no ensemble, so any movement there would have meant something
  unintended was changed. That was the decisive regression check.
- **D179's conclusion is downgraded.** A CORRECTION is appended to that record: BTC's
  bootstrap interval now **spans zero**, and "both intervals exclude zero" was its
  load-bearing claim.
- `n_warmup_bars`, `n_fallback_bars` and `mean_long_weight` are new on `EnsembleResult` and
  travel in the summary JSON. A degenerate-weighting count is not a diagnostic nicety here:
  it is the thing that caught the 63-bar mistake within one run.
