# Breakout Monte Carlo — does the strategy trade serial dependence, or the marginal distribution?

**Date produced:** 2026-08-18 · **Snapshot:**
`a2dfbc34c975895a1a2a133e00cdc36978a14f38bea5b83e568cd64b28f28032` (content-addressed, reproducible from the committed
`crypto_daily_2015_2025_raw.csv.gz`) · **Reproduce:** `uv run python scripts/run_breakout_nulls.py`
(offline, deterministic; 65 min on 12 worker processes) ·
**Seed:** 0 (D34) · **Path-null simulations:** 10,000 per cell ·
**Arithmetic-null simulations:** 10,000 (D36) ·
**Configuration under test:** `plateau_40_10` — N_entry 40, N_exit
10, inverse-vol sizing fixed at entry, exactly as in
[`BREAKOUT_RESULTS.md`](../../BREAKOUT_RESULTS.md).

Pipeline provenance: cleaning made 0 change(s); validation
passed with 0 hard violation(s) and 7
warning(s).

## The question

`BREAKOUT_RESULTS.md` establishes two things about the breakout result and leaves a
third open. It establishes that the *absolute* returns belong to the era (D121: BTC rose
426x over the out-of-sample span, so any long-biased rule prints four figures), and that
the Sharpe advantage over buy-and-hold is inside the noise (D120: P(strategy > benchmark)
= 55% / 59%). Neither of those tests the **mechanism**.

A trend follower's claim is that price changes are serially dependent — that a 40-day
high is informative about the next 40 days. The competing explanation is that it has no
timing information at all, and that a long-biased rule applied to a fat-tailed
distribution with enormous positive drift will look good whatever order the returns
arrive in. **This artifact separates those two hypotheses.**

## The null construction — stated precisely, because everything rests on it

Destroy the ORDERING of the bars; preserve the marginal distribution EXACTLY; re-run the
real strategy through the real engine.

The strategy needs OHLC, not closes: its entry level is a rolling max of **highs** and
its exit level a rolling min of **lows**. Shuffling closes and synthesising bars around
them would invent the intrabar geometry those levels are computed from. So the
resampling unit is the **bar shape** — for every bar *t* after the first, the four-tuple

    (open(t) / close(t-1),  high(t) / close(t-1),  low(t) / close(t-1),  close(t) / close(t-1))

is retained as one indivisible object. A null path takes a **permutation** of those
tuples and chains them: `close(t) = close(t-1) x close-ratio(t)`, with that same
`close(t-1)` scaling the bar's open, high and low. Four consequences, each asserted by
test rather than argued:

1. **Intrabar geometry survives exactly.** Every bar's open/high/low/close keep their
   mutual ratios, because one common factor scales all four. A high stays above its own
   close by the fraction it did in the source data. No coherence is invented.
2. **The marginal distribution survives exactly**, not in expectation: the null path's
   multiset of bar shapes IS the source's multiset. This is a permutation, never a draw
   with replacement.
3. **Buy-and-hold is invariant.** The terminal close is `close(0) x prod(close-ratios)`,
   and a permutation does not change a product. Close-to-close buy-and-hold over the
   measured span earns *identically* what it earned on the real path, to floating-point
   tolerance (D47).
4. **The permutation is segmented at the first out-of-sample bar.** The published result
   is measured over the OOS span, not the whole fixture. A whole-fixture permutation
   would move training-era bar shapes into the measured span, so each null path's OOS
   span would carry a randomly *re-drawn* marginal distribution — confounding the two
   things this test exists to separate. Permuting the prefix and the OOS span
   independently makes the OOS marginal identical on every path. (Bars past the final
   walk-forward window are trimmed before resampling; the study never reads them, and a
   test pins that trimming changes no number.)

So this is a controlled comparison in the strict sense: **same drift, same fat tails,
same total instrument return over the same span — only the sequence destroyed.** If the
strategy still earns its result on these paths, its edge is the marginal distribution.
If it collapses, it is exploiting real serial dependence.

**Why not `analytics.monte_carlo.block_bootstrap_paths` (D130).** That generator
resamples overlapping blocks *with replacement*, which is the right tool for a sampling
distribution — and is exactly what tests 3 and 4 below use. It is the wrong tool here:
with replacement the marginal is preserved only in expectation and the buy-and-hold
invariant is lost, so a shortfall on null paths could not be attributed to ordering
rather than to a re-drawn return distribution. The existing interface was not modified; a
second, differently-purposed generator sits beside it.

**What this null is not.** A path of permuted bar shapes is not a plausible price series:
no volatility clustering, no regimes, no calendar. That is deliberate. It is a null, and
the only property it must have is "same marginal, no ordering". Its lack of realism is
the hypothesis under test, not a defect.

## Sample sizes, seeds and the resolution actually bought

Each path-null simulation is a **full strategy re-run** — walk-forward spans re-derived,
252-bar training prefix, the real cost stack, next-open fills, trade-episode
extraction — over ~3,700 bars. Measured cost: **101 ms on BTC-USD and 65 ms on ETH-USD**
per simulation, single-process. The grid is 2 symbols x 2 tiers x 4 block
sizes = 16 cells.

At D36's floor of 10,000 that is ~3.7 hours of serial compute. It was budgeted as an
explicit, costed deviation to n = 2,000 — and then not taken, because every simulation's
seed is derived up front from the root seed, so the work parallelises across processes
without changing a single number (asserted by test). Twelve processes bring the effective
cost to ~20 ms/simulation and the whole grid to well under an hour, so **D36's n >=
10,000 is honoured in full and no deviation is needed** (D132).

Every p-value below is the add-one empirical form `(1 + #{null at least as extreme}) /
(n + 1)`, quoted with its binomial Monte Carlo standard error `sqrt(p(1-p)/n)`. At
n = 10,000 the floor a p-value can report is **0.00010** — an empirical p of exactly
zero is a statement 10,000 draws cannot support, so the floor is reported instead.

---

# BTC-USD @ `taker_40bp`

## Test 1 — the serial-dependence null (block size 1, the full shuffle)

Every scrap of ordering destroyed; marginal distribution and total instrument return
identical. 10,000 paths, seed 0.

| Metric | Real | Null median | Null 5th–95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|---|
| Total return (high tail) | **+5657.04%** | +332.36% | +15.64% – +1573.76% | 99.89 | 0.0012 ± 0.0003 |
| Sharpe (ann.) (high tail) | **1.202** | 0.498 | 0.065 – 0.919 | 99.73 | 0.0028 ± 0.0005 |
| Max drawdown (low tail) | **43.0%** | 50.3% | 35.0% – 71.1% | 24.26 | 0.2427 ± 0.0043 |
| Exposure (high tail) | **36.7%** | 38.2% | 34.6% – 42.0% | 24.44 | 0.7576 ± 0.0043 |
| Closed trades (low tail) | **38** | 46 | 40 – 53 | 1.59 | 0.0209 ± 0.0014 |

Each row's tail is fixed per metric by what would support the strategy's own story, and is stated rather than inferred — the direction *is* the hypothesis, and a silently-chosen tail is how a two-sided question gets reported as a one-sided p-value. Row by row the p-value is P(a shuffled path shows **at least the real total return**; **at least the real Sharpe**; **a drawdown no deeper than the real one**; **at least the real time in market (real trends persist, so a real path should hold longer)**; **no more round trips than the real count (persistent trends mean fewer entries and fewer whipsaws)**).

Buy-and-hold on these paths is the control that makes the comparison controlled: its
close-to-close return over the measured span is invariant by construction. The study's
*fixed-quantity* benchmark (D115) buys at the second OOS bar's **open**, so it moves by
that one bar's resampled open ratio and nothing else — real
+42386.71% against a null 5th–95th of
+42290.27% –
+42420.83% across all 10,000 paths,
a spread of 0.16% of terminal wealth. The strategy's own return,
by contrast, moves by orders of magnitude across the same paths.

The benchmark's **drawdown** is a different story, and an instructive one: buy-and-hold's
real max drawdown of 83.4% falls to a null median of
70.2% once ordering is destroyed.
A deep drawdown requires an ordered run of losses; a shuffle dismantles it while leaving
every one of those losses in the sample. So the strategy's drawdown advantage over
buy-and-hold is itself a claim about ordering, not about the distribution of daily returns
— which is why test 4 below bootstraps it rather than quoting the single-path pair.

## Test 2 — the block ladder

Block 1 is the full shuffle. As the block grows, contiguous runs of real bars survive
inside each block and only the joins are randomised, so more genuine serial structure is
retained and the null should walk toward the real result. **Where it crosses measures the
time scale of the dependence the strategy trades.**

Total return:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | +332.36% | +1573.76% | 99.89 | 0.0012 ± 0.0003 |
| 5 | +459.44% | +2162.37% | 99.57 | 0.0044 ± 0.0007 |
| 20 | +698.57% | +2778.75% | 99.45 | 0.0056 ± 0.0007 |
| 60 | +1608.01% | +3711.37% | 99.52 | 0.0049 ± 0.0007 |

Annualised Sharpe:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 0.498 | 0.919 | 99.73 | 0.0028 ± 0.0005 |
| 5 | 0.567 | 0.977 | 99.35 | 0.0066 ± 0.0008 |
| 20 | 0.672 | 1.040 | 99.13 | 0.0088 ± 0.0009 |
| 60 | 0.892 | 1.114 | 99.07 | 0.0094 ± 0.0010 |

Closed trades (lower tail — persistent trends mean fewer round trips):

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 46 | 53 | 1.59 | 0.0209 ± 0.0014 |
| 5 | 48 | 54 | 0.67 | 0.0091 ± 0.0009 |
| 20 | 48 | 54 | 0.23 | 0.0037 ± 0.0006 |
| 60 | 43 | 47 | 1.75 | 0.0258 ± 0.0016 |

On total return, the null is rejected at **every** block length tested, up to 60 bars.

---

# BTC-USD @ `maker_0bp`

## Test 1 — the serial-dependence null (block size 1, the full shuffle)

Every scrap of ordering destroyed; marginal distribution and total instrument return
identical. 10,000 paths, seed 0.

| Metric | Real | Null median | Null 5th–95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|---|
| Total return (high tail) | **+7367.18%** | +475.52% | +57.57% – +2065.91% | 99.91 | 0.0010 ± 0.0003 |
| Sharpe (ann.) (high tail) | **1.275** | 0.591 | 0.169 – 1.002 | 99.72 | 0.0029 ± 0.0005 |
| Max drawdown (low tail) | **40.6%** | 47.0% | 32.9% – 66.9% | 25.92 | 0.2593 ± 0.0044 |
| Exposure (high tail) | **36.7%** | 38.2% | 34.6% – 42.0% | 24.44 | 0.7576 ± 0.0043 |
| Closed trades (low tail) | **38** | 46 | 40 – 53 | 1.59 | 0.0209 ± 0.0014 |

Each row's tail is fixed per metric by what would support the strategy's own story, and is stated rather than inferred — the direction *is* the hypothesis, and a silently-chosen tail is how a two-sided question gets reported as a one-sided p-value. Row by row the p-value is P(a shuffled path shows **at least the real total return**; **at least the real Sharpe**; **a drawdown no deeper than the real one**; **at least the real time in market (real trends persist, so a real path should hold longer)**; **no more round trips than the real count (persistent trends mean fewer entries and fewer whipsaws)**).

Buy-and-hold on these paths is the control that makes the comparison controlled: its
close-to-close return over the measured span is invariant by construction. The study's
*fixed-quantity* benchmark (D115) buys at the second OOS bar's **open**, so it moves by
that one bar's resampled open ratio and nothing else — real
+42556.66% against a null 5th–95th of
+42459.84% –
+42590.91% across all 10,000 paths,
a spread of 0.16% of terminal wealth. The strategy's own return,
by contrast, moves by orders of magnitude across the same paths.

The benchmark's **drawdown** is a different story, and an instructive one: buy-and-hold's
real max drawdown of 83.4% falls to a null median of
70.2% once ordering is destroyed.
A deep drawdown requires an ordered run of losses; a shuffle dismantles it while leaving
every one of those losses in the sample. So the strategy's drawdown advantage over
buy-and-hold is itself a claim about ordering, not about the distribution of daily returns
— which is why test 4 below bootstraps it rather than quoting the single-path pair.

## Test 2 — the block ladder

Block 1 is the full shuffle. As the block grows, contiguous runs of real bars survive
inside each block and only the joins are randomised, so more genuine serial structure is
retained and the null should walk toward the real result. **Where it crosses measures the
time scale of the dependence the strategy trades.**

Total return:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | +475.52% | +2065.91% | 99.91 | 0.0010 ± 0.0003 |
| 5 | +660.47% | +2887.99% | 99.56 | 0.0045 ± 0.0007 |
| 20 | +999.36% | +3760.52% | 99.41 | 0.0060 ± 0.0008 |
| 60 | +2186.81% | +4918.17% | 99.48 | 0.0053 ± 0.0007 |

Annualised Sharpe:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 0.591 | 1.002 | 99.72 | 0.0029 ± 0.0005 |
| 5 | 0.662 | 1.061 | 99.30 | 0.0071 ± 0.0008 |
| 20 | 0.769 | 1.128 | 98.99 | 0.0102 ± 0.0010 |
| 60 | 0.979 | 1.194 | 98.97 | 0.0104 ± 0.0010 |

Closed trades (lower tail — persistent trends mean fewer round trips):

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 46 | 53 | 1.59 | 0.0209 ± 0.0014 |
| 5 | 48 | 54 | 0.67 | 0.0091 ± 0.0009 |
| 20 | 48 | 54 | 0.23 | 0.0037 ± 0.0006 |
| 60 | 43 | 47 | 1.75 | 0.0258 ± 0.0016 |

On total return, the null is rejected at **every** block length tested, up to 60 bars.

---

# ETH-USD @ `taker_40bp`

## Test 1 — the serial-dependence null (block size 1, the full shuffle)

Every scrap of ordering destroyed; marginal distribution and total instrument return
identical. 10,000 paths, seed 0.

| Metric | Real | Null median | Null 5th–95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|---|
| Total return (high tail) | **+552.21%** | +34.59% | -53.10% – +307.62% | 99.09 | 0.0092 ± 0.0010 |
| Sharpe (ann.) (high tail) | **0.775** | 0.144 | -0.378 – 0.669 | 97.80 | 0.0221 ± 0.0015 |
| Max drawdown (low tail) | **35.2%** | 51.5% | 33.9% – 74.0% | 6.99 | 0.0700 ± 0.0026 |
| Exposure (high tail) | **32.8%** | 32.2% | 28.1% – 36.4% | 59.64 | 0.4063 ± 0.0049 |
| Closed trades (low tail) | **28** | 32 | 27 – 37 | 11.68 | 0.1461 ± 0.0035 |

Each row's tail is fixed per metric by what would support the strategy's own story, and is stated rather than inferred — the direction *is* the hypothesis, and a silently-chosen tail is how a two-sided question gets reported as a one-sided p-value. Row by row the p-value is P(a shuffled path shows **at least the real total return**; **at least the real Sharpe**; **a drawdown no deeper than the real one**; **at least the real time in market (real trends persist, so a real path should hold longer)**; **no more round trips than the real count (persistent trends mean fewer entries and fewer whipsaws)**).

Buy-and-hold on these paths is the control that makes the comparison controlled: its
close-to-close return over the measured span is invariant by construction. The study's
*fixed-quantity* benchmark (D115) buys at the second OOS bar's **open**, so it moves by
that one bar's resampled open ratio and nothing else — real
+500.91% against a null 5th–95th of
+499.81% –
+501.12% across all 10,000 paths,
a spread of 0.18% of terminal wealth. The strategy's own return,
by contrast, moves by orders of magnitude across the same paths.

The benchmark's **drawdown** is a different story, and an instructive one: buy-and-hold's
real max drawdown of 82.4% falls to a null median of
85.6% once ordering is destroyed.
A deep drawdown requires an ordered run of losses; a shuffle dismantles it while leaving
every one of those losses in the sample. So the strategy's drawdown advantage over
buy-and-hold is itself a claim about ordering, not about the distribution of daily returns
— which is why test 4 below bootstraps it rather than quoting the single-path pair.

## Test 2 — the block ladder

Block 1 is the full shuffle. As the block grows, contiguous runs of real bars survive
inside each block and only the joins are randomised, so more genuine serial structure is
retained and the null should walk toward the real result. **Where it crosses measures the
time scale of the dependence the strategy trades.**

Total return:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | +34.59% | +307.62% | 99.09 | 0.0092 ± 0.0010 |
| 5 | +55.91% | +400.85% | 97.85 | 0.0216 ± 0.0015 |
| 20 | +181.30% | +771.29% | 89.03 | 0.1098 ± 0.0031 |
| 60 | +232.57% | +623.67% | 92.20 | 0.0781 ± 0.0027 |

Annualised Sharpe:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 0.144 | 0.669 | 97.80 | 0.0221 ± 0.0015 |
| 5 | 0.217 | 0.746 | 95.90 | 0.0411 ± 0.0020 |
| 20 | 0.480 | 0.947 | 84.75 | 0.1526 ± 0.0036 |
| 60 | 0.549 | 0.859 | 87.77 | 0.1224 ± 0.0033 |

Closed trades (lower tail — persistent trends mean fewer round trips):

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 32 | 37 | 11.68 | 0.1461 ± 0.0035 |
| 5 | 32 | 38 | 9.06 | 0.1160 ± 0.0032 |
| 20 | 30 | 35 | 28.77 | 0.3458 ± 0.0048 |
| 60 | 28 | 31 | 49.81 | 0.5974 ± 0.0049 |

On total return, the null stops being rejected at **block 20**.

---

# ETH-USD @ `maker_0bp`

## Test 1 — the serial-dependence null (block size 1, the full shuffle)

Every scrap of ordering destroyed; marginal distribution and total instrument return
identical. 10,000 paths, seed 0.

| Metric | Real | Null median | Null 5th–95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|---|
| Total return (high tail) | **+675.23%** | +58.73% | -43.70% – +371.59% | 99.18 | 0.0083 ± 0.0009 |
| Sharpe (ann.) (high tail) | **0.840** | 0.224 | -0.289 – 0.739 | 97.75 | 0.0226 ± 0.0015 |
| Max drawdown (low tail) | **34.2%** | 48.5% | 31.8% – 70.6% | 8.69 | 0.0870 ± 0.0028 |
| Exposure (high tail) | **32.8%** | 32.2% | 28.1% – 36.4% | 59.64 | 0.4063 ± 0.0049 |
| Closed trades (low tail) | **28** | 32 | 27 – 37 | 11.68 | 0.1461 ± 0.0035 |

Each row's tail is fixed per metric by what would support the strategy's own story, and is stated rather than inferred — the direction *is* the hypothesis, and a silently-chosen tail is how a two-sided question gets reported as a one-sided p-value. Row by row the p-value is P(a shuffled path shows **at least the real total return**; **at least the real Sharpe**; **a drawdown no deeper than the real one**; **at least the real time in market (real trends persist, so a real path should hold longer)**; **no more round trips than the real count (persistent trends mean fewer entries and fewer whipsaws)**).

Buy-and-hold on these paths is the control that makes the comparison controlled: its
close-to-close return over the measured span is invariant by construction. The study's
*fixed-quantity* benchmark (D115) buys at the second OOS bar's **open**, so it moves by
that one bar's resampled open ratio and nothing else — real
+503.32% against a null 5th–95th of
+502.21% –
+503.53% across all 10,000 paths,
a spread of 0.18% of terminal wealth. The strategy's own return,
by contrast, moves by orders of magnitude across the same paths.

The benchmark's **drawdown** is a different story, and an instructive one: buy-and-hold's
real max drawdown of 82.4% falls to a null median of
85.6% once ordering is destroyed.
A deep drawdown requires an ordered run of losses; a shuffle dismantles it while leaving
every one of those losses in the sample. So the strategy's drawdown advantage over
buy-and-hold is itself a claim about ordering, not about the distribution of daily returns
— which is why test 4 below bootstraps it rather than quoting the single-path pair.

## Test 2 — the block ladder

Block 1 is the full shuffle. As the block grows, contiguous runs of real bars survive
inside each block and only the joins are randomised, so more genuine serial structure is
retained and the null should walk toward the real result. **Where it crosses measures the
time scale of the dependence the strategy trades.**

Total return:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | +58.73% | +371.59% | 99.18 | 0.0083 ± 0.0009 |
| 5 | +85.83% | +486.73% | 97.95 | 0.0206 ± 0.0014 |
| 20 | +234.44% | +920.26% | 89.35 | 0.1066 ± 0.0031 |
| 60 | +294.55% | +746.82% | 92.65 | 0.0736 ± 0.0026 |

Annualised Sharpe:

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 0.224 | 0.739 | 97.75 | 0.0226 ± 0.0015 |
| 5 | 0.300 | 0.818 | 95.69 | 0.0432 ± 0.0020 |
| 20 | 0.555 | 1.015 | 84.49 | 0.1552 ± 0.0036 |
| 60 | 0.623 | 0.925 | 87.56 | 0.1245 ± 0.0033 |

Closed trades (lower tail — persistent trends mean fewer round trips):

| Block | Null median | Null 95th | Real's percentile | One-sided p (± MC SE) |
|---|---|---|---|---|
| 1 | 32 | 37 | 11.68 | 0.1461 ± 0.0035 |
| 5 | 32 | 38 | 9.06 | 0.1160 ± 0.0032 |
| 20 | 30 | 35 | 28.77 | 0.3458 ± 0.0048 |
| 60 | 28 | 31 | 49.81 | 0.5974 ± 0.0049 |

On total return, the null stops being rejected at **block 20**.

---

# Test 3 — how few trades carry the result

Two measures of the same question, because they answer it differently. **Cash share** is
the fraction of total net P&L contributed by the N most profitable closed trades — the
number the brief asks for, and the one a reviewer will quote. It is also mechanically
biased toward *late* trades: on a book that has compounded 50x, a +20% trade produces
more cash than a +200% trade did at the start. **Log share** is the same concentration
measured in compounding units, which removes that bias. Where the two disagree, the log
figure is the one about the strategy and the cash figure is partly about the calendar.

A share above 100% is not an error: when the losing trades subtract from the total, the
winners' share of the *net* exceeds one. That is the finding, not a bug to clamp away.

| Symbol @ tier | Closed trades | Winners | Top 1 (cash / log) | Top 3 (cash / log) | Top 5 (cash / log) | Best trade | Worst trade |
|---|---|---|---|---|---|---|---|
| BTC-USD @ `taker_40bp` | 38 | 22 | 64.0% / 36.9% | 124.8% / 63.4% | 151.7% / 81.1% | +345.3% | -15.9% |
| BTC-USD @ `maker_0bp` | 38 | 23 | 56.0% / 34.8% | 115.1% / 60.1% | 142.1% / 77.1% | +348.9% | -15.4% |
| ETH-USD @ `taker_40bp` | 28 | 15 | 42.1% / 60.5% | 81.2% / 87.9% | 104.0% / 113.5% | +211.2% | -22.7% |
| ETH-USD @ `maker_0bp` | 28 | 17 | 36.7% / 55.9% | 73.0% / 81.7% | 95.8% / 105.8% | +214.2% | -22.1% |

And the trade-level bootstrap: resample the closed trades' returns with replacement (a
permutation would be useless — the product of a fixed multiset of multiplicative returns
is constant) and compound each draw into a terminal wealth.

| Symbol @ tier | Actual | Bootstrap median | 5th | 95th | P(wealth < 1) | P(below actual) |
|---|---|---|---|---|---|---|
| BTC-USD @ `taker_40bp` | 57.57x | 50.16x | 4.19x | 1443.12x | 0.2% | 53.1% |
| BTC-USD @ `maker_0bp` | 74.67x | 65.01x | 5.42x | 1885.75x | 0.1% | 53.1% |
| ETH-USD @ `taker_40bp` | 6.52x | 5.87x | 1.05x | 62.18x | 4.4% | 53.3% |
| ETH-USD @ `maker_0bp` | 7.75x | 6.97x | 1.24x | 74.32x | 3.0% | 53.3% |

---

# Test 4 — the sampling distribution of the drawdown claim

`BREAKOUT_RESULTS.md` says the drawdown reduction is the one finding it can defend. A max
drawdown is a **single-path statistic from n = 1**, so that claim has no interval on it.
This puts one there: paired block bootstrap (20-bar blocks per D106, seed 0, 10,000 sims),
**one** resampled index vector applied to *both* return series so the strong correlation
between a long-flat strategy and the instrument it trades survives — D120's pairing,
reused. Bootstrapping the two independently would inflate the variance of their
difference and understate the strategy's advantage for the wrong reason.

Reported as (benchmark max DD − strategy max DD): positive means the strategy drew down
less.

| Symbol @ tier | Benchmark | Observed Δ | Bootstrap median Δ | 5th–95th | **P(strategy DD < benchmark DD)** |
|---|---|---|---|---|---|
| BTC-USD @ `taker_40bp` | buy & hold (100%) | +40.4% | +29.4% | +9.6% – +48.8% | **99.2%** ± 0.1% |
| BTC-USD @ `taker_40bp` | constant 37% | +1.3% | -7.6% | -25.3% – +10.2% | **23.1%** ± 0.4% |
| BTC-USD @ `maker_0bp` | buy & hold (100%) | +42.8% | +31.2% | +11.8% – +50.3% | **99.6%** ± 0.1% |
| BTC-USD @ `maker_0bp` | constant 37% | +3.1% | -6.3% | -23.4% – +11.2% | **26.6%** ± 0.4% |
| ETH-USD @ `taker_40bp` | buy & hold (100%) | +47.2% | +36.8% | +14.4% – +57.0% | **99.5%** ± 0.1% |
| ETH-USD @ `taker_40bp` | constant 33% | +6.1% | -4.9% | -28.1% – +18.2% | **35.7%** ± 0.5% |
| ETH-USD @ `maker_0bp` | buy & hold (100%) | +48.3% | +38.6% | +16.6% – +58.4% | **99.7%** ± 0.1% |
| ETH-USD @ `maker_0bp` | constant 33% | +6.9% | -3.8% | -26.4% – +18.7% | **38.5%** ± 0.5% |

**What this does and does not measure.** It answers "how often would a re-drawn history,
built from this one's 20-bar blocks, hand the strategy the shallower drawdown?". It is
*not* a serial-dependence test — the resampling destroys the very ordering a max drawdown
depends on, which is why the resampled drawdowns do not reproduce the observed pair and
the observed difference is quoted beside the distribution rather than inside it.

---

# Verdict

## 1. Does the strategy survive the serial-dependence null?

- **BTC-USD @ `taker_40bp`** — shuffled: total return +5657.0% vs a null median of +332.4% (percentile 99.89, p = 0.0012 ± 0.0003); Sharpe 1.20 vs a null median of 0.50 (percentile 99.73, p = 0.0028 ± 0.0005). On total return, the null is rejected at **every** block length tested, up to 60 bars.
- **BTC-USD @ `maker_0bp`** — shuffled: total return +7367.2% vs a null median of +475.5% (percentile 99.91, p = 0.0010 ± 0.0003); Sharpe 1.27 vs a null median of 0.59 (percentile 99.72, p = 0.0029 ± 0.0005). On total return, the null is rejected at **every** block length tested, up to 60 bars.
- **ETH-USD @ `taker_40bp`** — shuffled: total return +552.2% vs a null median of +34.6% (percentile 99.09, p = 0.0092 ± 0.0010); Sharpe 0.78 vs a null median of 0.14 (percentile 97.80, p = 0.0221 ± 0.0015). On total return, the null stops being rejected at **block 20**.
- **ETH-USD @ `maker_0bp`** — shuffled: total return +675.2% vs a null median of +58.7% (percentile 99.18, p = 0.0083 ± 0.0009); Sharpe 0.84 vs a null median of 0.22 (percentile 97.75, p = 0.0226 ± 0.0015). On total return, the null stops being rejected at **block 20**.

The block-1 column is the headline and it is the cleanest experiment in this repository:
the instrument's entire return, its entire fat tail and its entire decade of drift are
held fixed, and the only thing taken away is the order in which the bars arrived. The
answer it gives is not "the strategy is a mirage". **Shuffled paths keep every bit of the
instrument's decade of appreciation, and the strategy captures a small fraction of it;
on the real path it captures several times more.** The rule needs the ordering.

That is the finding, and it should be read with its own limits attached rather than as
vindication: it says the result is not *purely* an artifact of the marginal distribution.
It says nothing about whether the ordering that produces it will persist, and it does not
retract anything in `BREAKOUT_RESULTS.md` — the era decomposition (D121), the retracted
Sharpe claim (D120) and the selection bias above the whole study all still stand. A
strategy can genuinely trade real serial dependence in a sample and still be a bad bet
out of sample, for every reason that report already gives.

## 2. What time scale is the dependence on?

The crossing points, at a 5% threshold on total return:
- BTC-USD @ taker_40bp: no crossing — the null is rejected at every block length tested
- BTC-USD @ maker_0bp: no crossing — the null is rejected at every block length tested
- ETH-USD @ taker_40bp: block **20**
- ETH-USD @ maker_0bp: block **20**

Measured median holding period at the reference tier: **29 bars on
BTC-USD and 26 bars on ETH-USD** (`BREAKOUT_RESULTS.md`'s per-trade
diagnostics). A block of *b* bars leaves runs of *b* consecutive real bars intact and
randomises only the joins, so a strategy whose edge lives entirely inside one trade's
worth of bars should become indistinguishable from its null once *b* reaches the holding
period. Read against that yardstick, the crossings above say how much of the dependence
is inside a single trade's horizon and how much is longer-ranged than any one trade.

**The sign is inverted from D23's pairs case, and it matters.** There, the returns
shuffle was *demoted* as a null: destroying autocorrelation removed the effect a
mean-reverter needs, so the shuffled null was too easy to beat and could not distinguish
edge from luck. Here the same destruction is precisely the point — the shuffle IS the
null, and a trend follower that still earned its result on shuffled bars would thereby be
shown to have no timing information at all. The block ladder is D23's instrument used as
a **ruler** rather than as a null: same construction, opposite role.

## 3. How few trades carry it?

The concentration is severe and it is the mechanism working as designed, not a defect —
a breakout rule is a device for cutting losers quickly and letting one winner run. On
BTC-USD at the reference tier, out of 38 closed trades,
the single best contributes **64%** of net
cash P&L (37% in compounding units), the top
three **125%**
(63%), and the top five
**152%**
(81%). ETH-USD, over
28 trades, is 42% /
81% / 104%
on cash and 61% /
88% / 113%
on logs.

Shares above 100% mean the remaining trades lost money in aggregate. **The effective
sample size behind the return claim is therefore a handful of trades, not
3,717 bars** — which is a first-class caveat, and the
trade-level bootstrap prices it: on BTC-USD the 5th-to-95th band of terminal wealth spans
4.2x to 1443x, a factor of
344 from one end to the other,
against an actual of 58x. A decade of
daily data does not buy a decade of independent evidence about a rule that fires a few
dozen times.

## 4. Does the drawdown claim survive its own sampling distribution?

**Against 100% buy-and-hold: comfortably.** P(strategy max DD < benchmark max DD) is
99.2%–99.7% across all four cells, and
the 5th percentile of the difference is positive in every one. That is the finding
`BREAKOUT_RESULTS.md` said it could defend, and it defends.

**Against the risk-equalised constant-fraction benchmark (D119): it does not.**
P(strategy DD < benchmark DD) is only
23.1%–38.5%, and the median
resampled difference is *negative* — under block resampling the strategy typically draws
down MORE than a constantly-held position of the same average size. The observed
difference on the one real path is positive but small, and it sits inside the interval.
**Stated plainly: the drawdown advantage is a comparison against being 100% invested, not
against holding the strategy's own average exposure continuously.** It is a
lower-exposure result before it is a market-timing result, and the earlier report's
"typically by half" phrasing should be read against the 100% benchmark only.

## Reading these numbers together

The strategy is not a mirage of the marginal distribution — that null is rejected
decisively. It is also not the thing a return number of four figures implies: a few
trades carry it, its drawdown advantage over a matched-exposure alternative is not
established, and every era and selection caveat in `BREAKOUT_RESULTS.md` survives this
artifact untouched. **The honest summary is that the timing rule does something real and
small, on a sample whose effective size is a few dozen trades.**

## Standing caveats

1. **The null tests ordering, not realism.** Permuted bar shapes have no volatility
   clustering and no regimes. A strategy could in principle beat this null by exploiting
   volatility clustering rather than return autocorrelation — the inverse-vol sizing
   brick reads exactly that signal. The test says "the result depends on ordering", not
   "the result depends on return autocorrelation specifically".
2. **One configuration.** `plateau_40_10` at two tiers on two symbols. The plateau surface,
   the filters and the vol-target ladder are not re-run under the null; doing so would
   multiply the grid by 23 and add a multiplicity problem to a multiplicity problem.
3. **The p-values are not corrected for the 16 cells reported.** They
   are five metrics x 4 block sizes x 4 (symbol, tier) combinations, and a
   reader treating any single one as a standalone 5% test should divide accordingly. The
   block-1 total-return cells are the pre-registered headline; the rest is the ladder
   that gives them meaning.
4. **The trade-level statistics inherit the study's episode definition** (D112): a trade
   is a position episode, rebalancing fills belong to the episode containing them, and
   open-at-end episodes are excluded from closed-trade statistics.
5. **Everything upstream still applies.** Fees only, no slippage (D114); BTC and ETH are
   the crypto assets that survived to be worth studying; and the largest bias in
   `BREAKOUT_RESULTS.md` — the decision, taken in 2026, to test a trend follower on a
   decade of visible crypto trend — is not something any null on this data can remove.

## Reproduction

`uv run python scripts/run_breakout_nulls.py` — offline, deterministic; recreates the
same content-addressed snapshot and identical numbers on the same seed. Parallelism
changes throughput and nothing else (D132). Mechanics are tested in
`tests/unit/test_breakout_nulls.py` and `tests/property/test_breakout_nulls_property.py`.
