# D130 — The serial-dependence null resamples BAR SHAPES, by segmented permutation, not the block bootstrap

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout Monte Carlo session

## Decision

`research/breakout_nulls.py` adds a second, differently-purposed path generator beside
`analytics/monte_carlo.py::block_bootstrap_paths`. It answers the question
`BREAKOUT_RESULTS.md` leaves open — *is the breakout strategy exploiting genuine serial
dependence, or harvesting a fat-tailed, strongly-drifting marginal distribution?* — and
its construction has four load-bearing parts, each asserted by test.

**1. The resampling unit is a BAR SHAPE, not a close.** For every bar *t* after the
first, the four-tuple

    (open(t)/close(t-1), high(t)/close(t-1), low(t)/close(t-1), close(t)/close(t-1))

is retained as one indivisible object; a null path chains a permutation of those tuples
from the anchor bar's close, with the same `close(t-1)` scaling that bar's open, high and
low. The strategy's entry level is a rolling max of **highs** and its exit level a rolling
min of **lows** (D109), so a null built by shuffling closes and synthesising bars around
them would invent exactly the intrabar geometry the signal is computed from. Under this
construction a bar's four prices keep their mutual ratios, so a high stays above its own
close by the fraction it did in the source data.

**2. It is a PERMUTATION, never a draw with replacement.** The null path's multiset of bar
shapes IS the source's multiset. Therefore the marginal distribution is preserved exactly
rather than in expectation, and — because a permutation does not change a product —
close-to-close buy-and-hold over the measured span earns *identically* what it earned on
the real path, to floating-point tolerance (D47).

**3. The permutation is BLOCKED, and the block size is the ladder.** Consecutive
non-overlapping blocks have their ORDER permuted. Block 1 is the full shuffle; larger
blocks keep runs of real bars intact and randomise only the joins. The study reports
{1, 5, 20, 60}.

**4. The permutation is SEGMENTED at the first out-of-sample bar**, and the series is
trimmed to the last out-of-sample bar before resampling.

## Rationale

**Why not `block_bootstrap_paths`.** That generator resamples overlapping blocks *with
replacement*, which is the correct tool for a sampling distribution — and it is exactly
what this study's tests 3 and 4 use. It is the wrong tool for the ordering question. With
replacement, each path draws a different multiset of returns, so the marginal is preserved
only in expectation and buy-and-hold's terminal wealth varies path to path. A shortfall on
such paths could not be attributed to the destroyed ordering rather than to a re-drawn
return distribution — the two candidate explanations the whole test exists to separate.
The existing interface was NOT modified (the brief forbids it and D111 is the precedent);
a second generator sits beside it with its own stated purpose.

**Why the segmentation, which is the least obvious part.** The published result is measured
over the out-of-sample span, not over the whole fixture. A whole-fixture permutation would
move training-era bar shapes into the measured span and vice versa, so each null path's OOS
span would carry a *randomly re-drawn* marginal distribution — reintroducing precisely the
confound the permutation was chosen to remove. Splitting the shape sequence at the OOS start
and permuting each part independently makes the OOS marginal identical on every path, so the
comparison is "same drift, same fat tails, same total instrument return over the same span,
only the sequence destroyed". Within the OOS span the ordering is still destroyed completely
at block size 1, which is the hypothesis under test. The split point is fixed by the
walk-forward design and known before any resampling; it is a stratification, not a fit.

**Why the trim.** `run_variant` reads only `bars[run_start:oos_end]`, so bars past the final
walk-forward window are unused by the study — but a whole-series permutation would shuffle
them *into* the measured span. Trimming removes the contamination and changes no strategy
number; a test asserts the real result is identical either way.

**What the null deliberately is not.** A path of permuted bar shapes is not a plausible
price series: no volatility clustering, no regimes, no calendar. That is the point. It is a
null, and the only property it must have is "same marginal, no ordering". Its lack of
realism is the hypothesis, not a defect — the same reasoning D87 used to reject an
Ornstein-Uhlenbeck spread as a pairs null, applied in the opposite direction: there the null
had to *lack* the effect while keeping the signature; here it has to *keep* the distribution
while lacking the ordering.

## Consequence

`BREAKOUT_RESULTS.md`'s standing question "is this the strategy, or is it the era?" (D121)
now has a mechanical companion. The era decomposition shows the *size* of the number belongs
to the instrument; this shows whether the *rule* has timing information given that
instrument. Both are required; neither substitutes for the other.
