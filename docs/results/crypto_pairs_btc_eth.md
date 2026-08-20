# BTC/ETH z-score pairs: is there a spread to trade at all?

**Date produced:** 2026-08-18 ·
**Snapshot:** `a2dfbc34c975895a1a2a133e00cdc36978a14f38bea5b83e568cd64b28f28032` ·
**Registry:** `data/crypto_pairs_registry.sqlite`
(76 out-of-sample trials + per-window rows) ·
**Reproduce:** `uv run python scripts/run_crypto_pairs_study.py` (offline, deterministic)

> **Lead finding, because it changes how everything below should be read.** At **zero
> fees and zero carry** the baseline configuration returns
> **-88.7%** over the
> out-of-sample span. There is no edge here for costs to eat. Every cost number in this
> document is therefore a description of *how much faster* a losing strategy loses, not a
> viability threshold — and any reading of the form "it would work at a cheaper venue" is
> unavailable.

**Thesis frame (D37).** This IS the project's market-neutral thesis strategy: long one
leg, short the other, gross ~200% of NAV, designed to carry no market exposure. Its
honest primary hurdle is therefore the **risk-free rate**, which every Sharpe below
already carries (rf = 4%). Buy-and-hold columns are reported second,
and are a *long-only* benchmark for a market-neutral book — they answer "what did the
beta you deliberately did not take do?", not "what should this have beaten".

**Data.** BTC-USD and ETH-USD daily bars, 00:00 UTC boundary, fixed.
Fixture `data/fixtures/crypto_daily_2015_2025_raw.csv.gz`, frozen through the Step-7
pipeline (clean → validate → `SnapshotStore.create` → load). The sanity gate (D25/D26)
reported **0 cleaning change(s)** and **0
hard violation(s)**, with 7 warning(s) — genuine large crypto moves, none
quarantining.

**The sample is ETH's, not BTC's.** D45/D63 inner-join alignment drops every timestamp
that is not present on both legs, which truncates the pair at ETH-USD's inception
(2017-11-09) and discards 1,043 BTC bars. That is *correct* for a pairs trade — there is
no spread on a day one leg does not exist — and it is stated rather than worked around.
The breakout study, running one single-instrument backtest per symbol, kept BTC's full
history; **the two studies therefore do not cover the same span**, and no return in this
document is directly comparable to a BTC-USD row in `BREAKOUT_RESULTS.md`.

**Scale.** 76 out-of-sample trials
(19 variants × 4 cost tiers), plus
3,268 per-window rows and
43 training-window cointegration tests. Annualisation on
365 days (crypto trades every calendar day, D17).


## Method, in one screen

**Signal.** `strategies.zscore_pairs.ZScorePairsStrategy` (D69), **unmodified**. spread =
ln(BTC-USD) − ln(ETH-USD); z is computed against the mean and stdev of
the `lookback` spreads ending at the **previous** bar (D44). z > entry_z → short the
spread; z < −entry_z → long it; |z| < exit_z → flat; in between, hold the current side
(hysteresis). Baseline lookback 60, entry 2.0,
exit 0.5, ±100%/leg — D69's a-priori first-number parameters, carried
over unchanged so the grid is a sensitivity around a pre-existing choice.

**Hedge.** Fixed 1:1 in log space, by D69's construction. Section "Cointegration" below
tests whether that is a defensible description of this pair. It is not.

**Execution.** `fill_timing="next_open"` (D103) — a decision at bar t's close fills at bar
t+1's **open**, so the strategy never trades at the price that produced its signal. Same
convention as the breakout study, for comparability. `fill_close` is run as a sensitivity
(D105's precedent: measure the convention, do not argue about it).

**Walk-forward.** train=252, test=63, step=63,
via `walk_forward_windows` (D85). 43 windows. The out-of-sample span
starts exactly where window 0's training slice ends. **Nothing is fitted**, so the
continuous run needs no parameter schedule; the training slices are used only for the
cointegration diagnostic, through views that physically contain no test bar (D22/D56).

**Stitching.** One continuous out-of-sample backtest (D123), the breakout study's pattern
(D113) rather than the pairs studies' chained windows (D89). `stitch_chained` is run as a
sensitivity so the difference is a number, not a claim.

**Costs (D124).** `maker_0bp` = 0.00% (maker), `maker_10bp` = 0.10% (maker), `maker_25bp` = 0.25% (maker), `taker_40bp` = 0.40% (taker) — the breakout study's `CostTier` objects, unmodified, so the
fee dimension is identical between the two studies. **Plus two carry bricks a long-only
book does not pay**: `BorrowFee` at 10%/yr on the short leg's
notional (D71), and `MarginInterest` at 10%/yr on
max(gross − NAV, 0) (D5). Every stack is built through the declarative `build_cost_stack`
path (D102), so the dict the registry hashes is the dict the stack is built from.

**Benchmarks.** Buy-and-hold BTC-USD, buy-and-hold ETH-USD, and a
50/50 basket, over the same OOS span at the same tier, via `breakout_study.run_benchmark`
(D115: fixed *quantity*, bought at the second OOS bar's open, fee paid on entry notional,
marked at the final close). The basket is the mean of the two curves, which is exactly a
fixed-quantity 50/50 hold with half the capital in each leg.


---

## Read this first

### 1. The premise fails before the costs do

The a-priori question was whether BTC/ETH mean reversion clears crypto trading frictions.
It does not get that far. Stripped of **all** frictions — zero fee tier, zero borrow, zero
margin interest — the baseline configuration returns
**-88.7%** over 2,709 out-of-sample bars, with an
annualised Sharpe of -0.67 against a
4% risk-free rate. Adding the full real cost stack at the taker
tier moves that to -98.0%.

Frictions cost roughly
83% of the
zero-cost terminal wealth here, which is a large number, and it is also **irrelevant to
the verdict**: subtracting a large loss from a large loss does not produce a decision.

### 2. The pair is not cointegrated, and the 1:1 hedge is not what the data says

Tested inside each of the 43 training windows only, the log spread the
strategy actually trades is stationary at the 5% level in
**6 of 43 windows (14%)** — about
what pure noise would produce. The Engle–Granger β linking the two log price series has a
median of 0.74 and sits inside D92's
coherence band [0.7, 1.3] in only 51% of windows. The full
table is below; it is a first-class result, not a footnote.

### 3. Market neutrality: the one claim that survives

Realised beta of the baseline at the reference tier is
**-0.0112** vs BTC-USD,
**+0.0216** vs ETH-USD, and
**-0.0055** vs the 50/50 basket. The D37 expectation is ≈ 0 and it
is met on all three. The strategy is genuinely market-neutral. It is also genuinely
unprofitable, and those two facts are independent.

### 4. The stitching choice was measured, not asserted

`stitch_chained` (the pairs-study v1–v3 pattern) returns
-96.7% against the continuous run's -98.0% at
the same tier, with 52 round trips against
40. The gap is the free liquidation at each of the
43 window boundaries **plus** the silent reset of the strategy's own
hysteresis state (`_side`), which a fresh per-window instance discards. It is not a small
effect, and it is the reason the continuous pattern is the headline (D123).


---

# Cointegration: testing the premise instead of assuming it

BTC/ETH was chosen a priori, and it is famous. D22's rule — selection belongs inside the
training window, over a broad universe — cannot be satisfied by a study with no selection
step, so D70's meta-in-sample caveat applies in full. The one honest thing available is to
test the premise the strategy rests on, inside the training windows only, and report the
answer whatever it is.

**Method.** For each of the 43 training windows (`walk_forward_windows` hands out views
that physically contain no test bar, D22/D56), two tests on the 252
training bars:

1. The **traded 1:1 log spread** ln A − ln B, demeaned, through `research.cointegration`'s
   ADF (D93). The hedge ratio is *known*, not estimated, so the Dickey–Fuller τ_μ table
   applies. Critical values are anchored against `statsmodels.tsa.stattools.adfuller` in
   the unit suite rather than typed in from memory.
2. The textbook **Engle–Granger** residual: fit ln A = α + β·ln B on the window, ADF the
   residual against the stricter EG critical values (β was estimated from the same
   sample). β is reported and **not** traded — D92's coherence argument: stationarity
   evidence about ln A − 0.4·ln B is evidence about a spread this strategy does not hold.

**Why thresholds at all, when D29/D93 refused them.** Those decisions govern *selection*,
where ranking N candidates is the honest operation and a p-value adds nothing. This study
selects nothing. The only question an ADF can answer here is the binary one, and that
needs a critical value (D125).

| Test | Threshold | Windows cointegrated | Rate |
|---|---|---|---|
| traded 1:1 log spread (DF tau_mu) | -3.4568 (1%) | 1 / 43 | 2.3% |
| traded 1:1 log spread (DF tau_mu) | -2.8732 (5%) | 6 / 43 | 14.0% |
| traded 1:1 log spread (DF tau_mu) | -2.5730 (10%) | 8 / 43 | 18.6% |
| Engle-Granger residual | -3.90 (1%) | 1 / 43 | 2.3% |
| Engle-Granger residual | -3.34 (5%) | 2 / 43 | 4.7% |
| Engle-Granger residual | -3.04 (10%) | 6 / 43 | 14.0% |

β median 0.739, range
0.168 to 1.305; inside [0.7, 1.3] in
51% of windows.

**What this means.** A 5% test that fires 14% of the time is
indistinguishable from a 5% test firing on noise. The pair *tracks* — that is what makes
it famous — but tracking is not mean reversion, which is exactly the distinction study v1
of the ETF pairs work already ran into (D92). Here it is worse: β is not merely noisy, it
is systematically far from 1, so even the pairs that "look" cointegrated are cointegrated
in a spread with a hedge ratio the strategy does not use.

Per-window detail:

| Window | Train span | ADF (traded 1:1 spread) | EG beta | ADF (EG residual) | Cointegrated @5%? |
|---|---|---|---|---|---|
| 0 | 2017-11-09 → 2018-07-18 | -2.043 | +0.523 | -1.734 | — |
| 1 | 2018-01-11 → 2018-09-19 | +0.556 | +0.382 | -2.501 | — |
| 2 | 2018-03-15 → 2018-11-21 | +0.003 | +0.234 | -1.760 | — |
| 3 | 2018-05-17 → 2019-01-23 | -1.688 | +0.392 | -0.751 | — |
| 4 | 2018-07-19 → 2019-03-27 | -2.924 | +0.621 | -1.798 | 1:1 |
| 5 | 2018-09-20 → 2019-05-29 | -2.600 | +0.913 | -2.265 | — |
| 6 | 2018-11-22 → 2019-07-31 | -0.772 | +1.135 | -1.384 | — |
| 7 | 2019-01-24 → 2019-10-02 | -0.866 | +1.279 | -1.057 | — |
| 8 | 2019-03-28 → 2019-12-04 | -1.685 | +0.754 | -2.217 | — |
| 9 | 2019-05-30 → 2020-02-05 | -2.542 | +0.476 | -2.432 | — |
| 10 | 2019-08-01 → 2020-04-08 | -1.505 | +0.697 | -1.435 | — |
| 11 | 2019-10-03 → 2020-06-10 | -1.351 | +0.599 | -2.106 | — |
| 12 | 2019-12-05 → 2020-08-12 | -0.364 | +0.526 | -2.064 | — |
| 13 | 2020-02-06 → 2020-10-14 | -1.123 | +0.528 | -2.812 | — |
| 14 | 2020-04-09 → 2020-12-16 | -1.653 | +0.663 | -1.016 | — |
| 15 | 2020-06-11 → 2021-02-17 | -2.141 | +0.849 | -2.176 | — |
| 16 | 2020-08-13 → 2021-04-21 | -1.845 | +0.938 | -2.189 | — |
| 17 | 2020-10-15 → 2021-06-23 | -0.611 | +0.646 | -1.137 | — |
| 18 | 2020-12-17 → 2021-08-25 | -1.184 | +0.328 | -1.459 | — |
| 19 | 2021-02-18 → 2021-10-27 | -1.395 | +0.168 | -1.387 | — |
| 20 | 2021-04-22 → 2021-12-29 | -3.233 | +0.704 | -3.312 | 1:1 |
| 21 | 2021-06-24 → 2022-03-02 | -2.603 | +0.739 | -2.342 | — |
| 22 | 2021-08-26 → 2022-05-04 | -2.417 | +0.834 | -2.236 | — |
| 23 | 2021-10-28 → 2022-07-06 | -0.897 | +0.742 | -2.832 | — |
| 24 | 2021-12-30 → 2022-09-07 | -1.322 | +0.800 | -0.075 | — |
| 25 | 2022-03-03 → 2022-11-09 | -1.608 | +0.843 | -1.424 | — |
| 26 | 2022-05-05 → 2023-01-11 | -1.535 | +0.811 | -1.045 | — |
| 27 | 2022-07-07 → 2023-03-15 | -3.682 | +0.797 | -3.220 | 1:1 |
| 28 | 2022-09-08 → 2023-05-17 | -2.993 | +1.146 | -4.119 | 1:1, EG |
| 29 | 2022-11-10 → 2023-07-19 | -1.885 | +1.253 | -3.438 | EG |
| 30 | 2023-01-12 → 2023-09-20 | -1.843 | +1.245 | -1.763 | — |
| 31 | 2023-03-16 → 2023-11-22 | -0.866 | +0.833 | -0.562 | — |
| 32 | 2023-05-18 → 2024-01-24 | -1.666 | +1.305 | -2.191 | — |
| 33 | 2023-07-20 → 2024-03-27 | -1.866 | +1.137 | -2.555 | — |
| 34 | 2023-09-21 → 2024-05-29 | -2.888 | +1.101 | -3.137 | 1:1 |
| 35 | 2023-11-23 → 2024-07-31 | -3.050 | +1.027 | -3.124 | 1:1 |
| 36 | 2024-01-25 → 2024-10-02 | -0.692 | +0.577 | -2.191 | — |
| 37 | 2024-03-28 → 2024-12-04 | -0.999 | +0.408 | +0.189 | — |
| 38 | 2024-05-30 → 2025-02-05 | -0.628 | +0.814 | -0.290 | — |
| 39 | 2024-08-01 → 2025-04-09 | +0.141 | +0.476 | -0.928 | — |
| 40 | 2024-10-03 → 2025-06-11 | -1.234 | +0.205 | -2.299 | — |
| 41 | 2024-12-05 → 2025-08-13 | -1.283 | +0.285 | -1.781 | — |
| 42 | 2025-02-06 → 2025-10-15 | -0.587 | +0.320 | -1.674 | — |


---

# Performance

## Every variant at the reference tier (`taker_40bp`, 0.40% taker)

Costs are split into the three bricks that charge them, because for a pairs book they are
not the same story: fees scale with turnover, borrow scales with time short, margin
scales with gross exposure above NAV.

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Round trips | Exposure | Costs (fees / borrow / margin) |
|---|---|---|---|---|---|---|---|
| `grid_lb20_z1.5` | -99.88% | -59.73% | -2.04 | 99.9% | 143 | 61.6% | 23,051 / 4,556 / 4,582 |
| `grid_lb20_z2` | -99.59% | -52.35% | -1.78 | 99.6% | 111 | 52.0% | 25,058 / 5,005 / 5,037 |
| `grid_lb20_z2.5` | -99.19% | -47.74% | -1.68 | 99.2% | 87 | 43.1% | 24,502 / 4,946 / 4,980 |
| `grid_lb30_z1.5` | -99.83% | -57.52% | -1.96 | 99.8% | 95 | 62.8% | 17,927 / 5,245 / 5,264 |
| `grid_lb30_z2` | -99.52% | -51.25% | -1.71 | 99.5% | 76 | 55.3% | 16,244 / 5,008 / 5,031 |
| `grid_lb30_z2.5` | -98.91% | -45.61% | -1.52 | 99.0% | 63 | 48.9% | 17,003 / 5,135 / 5,161 |
| `grid_lb60_z1.5` | -99.18% | -47.65% | -1.49 | 99.2% | 50 | 57.1% | 14,633 / 5,694 / 5,715 |
| `grid_lb60_z2` | -98.04% | -41.11% | -1.27 | 98.1% | 40 | 51.7% | 14,589 / 6,110 / 6,129 |
| `grid_lb60_z2.5` | -96.92% | -37.43% | -1.17 | 97.0% | 34 | 44.9% | 16,513 / 6,682 / 6,703 |
| `grid_lb90_z1.5` | -95.56% | -34.27% | -0.94 | 96.0% | 42 | 52.9% | 20,863 / 8,197 / 8,218 |
| `grid_lb90_z2` | -90.32% | -26.99% | -0.72 | 91.7% | 33 | 45.5% | 23,726 / 9,531 / 9,563 |
| `grid_lb90_z2.5` | -84.25% | -22.04% | -0.62 | 86.4% | 25 | 38.3% | 27,908 / 11,363 / 11,395 |
| `gross_lw0.25` | -53.66% | -9.84% | -1.42 | 54.2% | 40 | 51.7% | 14,705 / 6,111 / 0 |
| `gross_lw0.5` | -80.21% | -19.61% | -1.23 | 80.7% | 40 | 51.7% | 18,690 / 7,751 / 318 |
| `fill_close` | -98.01% | -40.99% | -1.28 | 98.1% | 40 | 51.7% | 14,670 / 6,130 / 6,140 |
| `stitch_chained` | -96.72% | -36.90% | -1.16 | 96.9% | 52 | 45.5% | 18,030 / 6,328 / 6,348 |
| `carry_free` | -95.73% | -34.62% | -1.00 | 96.0% | 40 | 51.7% | 18,167 / 0 / 0 |
| `borrow_0pct` | -97.11% | -37.96% | -1.13 | 97.2% | 40 | 51.7% | 16,209 / 0 / 6,739 |
| `borrow_25pct` | -98.90% | -45.56% | -1.47 | 98.9% | 40 | 51.7% | 12,632 / 13,448 / 5,397 |

## The baseline across the cost tiers — maker vs taker

| Tier | Fee | Role | Total return | CAGR | Sharpe (ann.) | Max DD | Fees paid | Borrow paid | Margin paid |
|---|---|---|---|---|---|---|---|---|---|
| `maker_0bp` | 0.00% | maker | -94.81% | -32.88% | -0.94 | 95.1% | 0 | 7,874 | 7,896 |
| `maker_10bp` | 0.10% | maker | -95.93% | -35.04% | -1.02 | 96.1% | 4,454 | 7,338 | 7,359 |
| `maker_25bp` | 0.25% | maker | -97.17% | -38.15% | -1.14 | 97.3% | 10,030 | 6,662 | 6,682 |
| `taker_40bp` | 0.40% | taker | -98.04% | -41.11% | -1.27 | 98.1% | 14,589 | 6,110 | 6,129 |

**Two legs, four fills per round trip.** A pairs entry buys one leg and sells the other;
the exit reverses both. Against the breakout study's two fills per round trip that is
double the fee bill for the same tier, before accounting for the fact that this strategy
also re-normalizes both legs to constant gross every bar (the `ZScorePairsStrategy` +
`Sizer` convention, D61/D94), which is where the
31× annualised turnover comes
from. Concretely: going from `maker_0bp` to `taker_40bp` gives up
62%
of the zero-fee terminal wealth and
0.33
of annualised Sharpe. The breakout study found the same fee range worth a fraction of a
Sharpe point on a book that trades a few dozen times a decade; a book that re-normalizes
200% of gross every day is in a different regime entirely. **It is still not the binding
constraint here** — see the zero-cost row.

## Gross exposure and the margin threshold (D96)

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Round trips | Exposure | Costs (fees / borrow / margin) |
|---|---|---|---|---|---|---|---|
| `grid_lb60_z2` | -98.04% | -41.11% | -1.27 | 98.1% | 40 | 51.7% | 14,589 / 6,110 / 6,129 |
| `gross_lw0.25` | -53.66% | -9.84% | -1.42 | 54.2% | 40 | 51.7% | 14,705 / 6,111 / 0 |
| `gross_lw0.5` | -80.21% | -19.61% | -1.23 | 80.7% | 40 | 51.7% | 18,690 / 7,751 / 318 |

At `leg_weight` = 1.0 the book runs ~200% gross, so D5's margin base — max(gross − NAV, 0)
— is roughly NAV itself and margin interest accrues continuously. At 0.5, gross equals NAV
and the base collapses; at 0.25 it is zero. D96 found that threshold to be the dominant
cost lever on the ETF pairs book, and the margin column above reproduces the collapse
exactly. What it does not do is rescue the result: de-levering scales a negative return
stream toward zero without changing its sign.

## Convention and cost-assumption sensitivities

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Round trips | Exposure | Costs (fees / borrow / margin) |
|---|---|---|---|---|---|---|---|
| `grid_lb60_z2` | -98.04% | -41.11% | -1.27 | 98.1% | 40 | 51.7% | 14,589 / 6,110 / 6,129 |
| `fill_close` | -98.01% | -40.99% | -1.28 | 98.1% | 40 | 51.7% | 14,670 / 6,130 / 6,140 |
| `stitch_chained` | -96.72% | -36.90% | -1.16 | 96.9% | 52 | 45.5% | 18,030 / 6,328 / 6,348 |
| `carry_free` | -95.73% | -34.62% | -1.00 | 96.0% | 40 | 51.7% | 18,167 / 0 / 0 |
| `borrow_0pct` | -97.11% | -37.96% | -1.13 | 97.2% | 40 | 51.7% | 16,209 / 0 / 6,739 |
| `borrow_25pct` | -98.90% | -45.56% | -1.47 | 98.9% | 40 | 51.7% | 12,632 / 13,448 / 5,397 |


---

# Parameter sensitivity

12 cells: `lookback` ∈ {20, 30, 60, 90} ×
`entry_z` ∈ {1.5, 2, 2.5}, with `exit_z` held at
D69's a-priori 0.5. Holding `exit_z` is a scope choice, not an oversight —
adding it as a third axis triples the grid — and it is named again in the caveats.

Annualised Sharpe at `taker_40bp`:

| lookback \ entry_z | 1.5 | 2 | 2.5 |
|---|---|---|---|
| **20** | -2.04 | -1.78 | -1.68 |
| **30** | -1.96 | -1.71 | -1.52 |
| **60** | -1.49 | -1.27 | -1.17 |
| **90** | -0.94 | -0.72 | -0.62 |

Same surface, CAGR:

| lookback \ entry_z | 1.5 | 2 | 2.5 |
|---|---|---|---|
| **20** | -59.73% | -52.35% | -47.74% |
| **30** | -57.52% | -51.25% | -45.61% |
| **60** | -47.65% | -41.11% | -37.43% |
| **90** | -34.27% | -26.99% | -22.04% |

Same surface, round trips (the mechanical explanation for the shape):

| lookback \ entry_z | 1.5 | 2 | 2.5 |
|---|---|---|---|
| **20** | 143 | 111 | 87 |
| **30** | 95 | 76 | 63 |
| **60** | 50 | 40 | 34 |
| **90** | 42 | 33 | 25 |

**Spike test.** Best cell is lookback=90,
entry_z=2.5 at Sharpe -0.622; its immediate
neighbours average -1.053; the whole
12-cell surface spans -2.045 to
-0.622 (spread 1.423). The
best-minus-neighbours gap is **0.30 of the surface's own spread**. **Borderline.** The top cell sits meaningfully above its immediate neighbours: not a clean plateau, and the best cell should not be quoted as the strategy's performance.

**The best cell is a corner, and that matters more than the spike test.** Sharpe improves
monotonically along both axes — longer `lookback`, higher `entry_z` — so the surface's
optimum lies outside the grid, and what the surface is actually measuring is *trade less*.
The round-trip grid makes the mechanism explicit: the best cell takes
25
round trips against the worst cell's
143.
A parameter surface whose only gradient is "do this less" is not evidence of a parameter
worth tuning; it is the shape a strategy with negative expectancy per trade produces by
construction, and extending the grid would extend the gradient rather than find a peak.

Every cell in the surface is negative, which makes the plateau/spike question mostly
academic here: there is no cell worth quoting.

Same surface at the free tier (`maker_0bp`), which strips the **fee** effect out (borrow
and margin interest are still charged — they are carry, not fees, and no tier turns them
off; the `carry_free` variant above is what does):

| lookback \ entry_z | 1.5 | 2 | 2.5 |
|---|---|---|---|
| **20** | -1.20 | -1.07 | -1.07 |
| **30** | -1.34 | -1.18 | -1.05 |
| **60** | -1.10 | -0.94 | -0.87 |
| **90** | -0.60 | -0.44 | -0.38 |


---

# Tearsheet — baseline `grid_lb60_z2` at real costs (`taker_40bp`)

Benchmark for the beta row is the 50/50 basket. The ≈ 0 expectation printed next to it is
D37's, and it is the one line in this document the strategy passes cleanly.

| Metric | Value |
|---|---|
| Sharpe (rf=4.00%/yr, 365 periods/yr) | -1.268 |
| Sortino (rf=4.00%/yr) | -1.739 |
| Max drawdown | 98.12% |
| Realised beta vs benchmark | -0.0055 (market-neutral expectation: ≈ 0, D37) |
| VaR 95% (daily) | 3.18% |
| CVaR 95% (daily) | 5.33% |

Block bootstrap (n=10,000, block=20, seed=0 — D34/D36):
| | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|
| Terminal return | -99.68% | -98.99% | -97.83% | -95.45% | -87.78% |
| Max drawdown | 90.93% | 96.45% | 98.25% | 99.16% | 99.73% |


---

# Benchmarks (D37: risk-free first, buy-and-hold second)

| Series | Total return | CAGR | Sharpe (ann., rf=4%) | Max DD | Realised beta of strategy |
|---|---|---|---|---|---|
| **strategy `grid_lb60_z2`** | -98.04% | -41.11% | -1.27 | 98.1% | — |
| buy & hold BTC-USD | +1049.00% | +38.95% | 0.78 | 76.6% | -0.0112 |
| buy & hold ETH-USD | +500.91% | +27.33% | 0.66 | 82.4% | +0.0216 |
| buy & hold basket_5050 | +774.96% | +33.94% | 0.72 | 76.8% | -0.0055 |

**Read the two frames separately.**

- **Against the risk-free rate**, which D37 makes the primary hurdle for a market-neutral
  book: the strategy's Sharpe is
  -1.27. That is not
  "indistinguishable from zero"; it is decisively negative against a
  4% hurdle over 2,709 bars.
- **Against buy-and-hold**, which is a *long-only* comparison for a book built to have no
  market exposure: the gap is enormous, and it is also the wrong test. A market-neutral
  strategy that matched buy-and-hold would be a market-neutral strategy that had failed at
  being market-neutral. The realised-beta column is how you check that, and it says the
  neutrality is real.

The benchmark columns are still worth printing, because they establish the opportunity
cost honestly: over this span, the beta this strategy deliberately refused was the entire
return available on these two instruments.


---

# Deflated Sharpe (D21/D86/D98/D116)

| Tier | Best variant in pool | Its daily SR | T (bars) | N (configs in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `grid_lb90_z2.5` | -0.0199 | 2,708 | 14 | 0.000226 | **0.0087** |
| `maker_10bp` | `grid_lb90_z2.5` | -0.0231 | 2,708 | 14 | 0.000283 | **0.0035** |
| `maker_25bp` | `grid_lb90_z2.5` | -0.0278 | 2,708 | 14 | 0.000388 | **0.0007** |
| `taker_40bp` | `grid_lb90_z2.5` | -0.0326 | 2,708 | 14 | 0.000516 | **0.0001** |

**What the trial pool is.** Per D116, for a parameter-swept study N is the number of
*configurations* tried, so the pool at each tier is every **grid** and **gross** variant's
out-of-sample daily Sharpe — 14
configurations. Pool membership is decided on identity fields in the logged config
(`row_kind`, `group`, `tier`) and never on the presence of a metric (D98's rule).
Per-window rows carry `row_kind="window"` and are excluded by the same predicate. Units
are per-period (daily, non-annualised) throughout, per D98's contract.

**What the trial pool is NOT.** It excludes the convention sensitivities (fill timing,
stitching) and the cost-assumption sensitivities (borrow rate), because those are the same
configuration re-priced — D98 established that a re-pricing is a sensitivity point, not an
additional independent trial. More importantly it excludes the two largest terms of all:

- **The pair.** BTC/ETH was chosen a priori because it is the famous crypto pair. There
  is no selection step to correct, so D29's multiplicity machinery has nothing to bite on
  and D70's meta-in-sample caveat stands uncorrected. The registry's N cannot see this.
- **The asset class.** Testing a pairs strategy on the two crypto assets that survived to
  2025 is a selected sample by construction.

**The reading is unchanged from D90/D116: DSR < 0.95 means "no demonstrated edge"; DSR ≥
0.95 does not mean the reverse.** Every DSR here is below
0.009, which is what a decisively negative observed
Sharpe produces under any N — the deflation is doing almost no work, because the *best of
14 configurations* is still far below the noise floor. So the multiplicity question never
becomes load-bearing in this study. That is an accident of the sign, not a strength of the
method: had the observed Sharpe been positive, the uncounted pair-choice multiplicity
above would have made these numbers unusable at face value.


---

# Multiplicity: everything that was evaluated

| What | Count |
|---|---|
| Strategy variants | 19 |
| — parameter-grid cells (lookback × entry_z) | 12 |
| — gross-exposure (`leg_weight`) settings | 2 |
| — convention sensitivities (fill timing, stitching) | 2 |
| — cost-assumption sensitivities (borrow rate) | 3 |
| Cost tiers | 4 |
| **Out-of-sample trials logged** | **76** |
| Per-window trial rows logged | 3,268 |
| In-training-window cointegration tests (diagnostic, not trials) | 43 |
| Fitted parameters | **0** |

Nothing in this study is fitted. The cointegration tests are diagnostics computed on
training views and never feed a trading decision, so they are not selection and do not
enter N — but they are listed because "how many things did you look at" is the question
multiplicity accounting exists to answer, and the answer includes them.


---

# Verdict

**No edge, at any cost tier, at any parameter setting in the grid, before frictions or
after them.**

- Zero fees, zero carry: **-88.7%**
  (Sharpe -0.67).
- Zero fees, real carry: **-94.8%**
  (Sharpe -0.94).
- Full real costs at the taker tier: **-98.0%**
  (Sharpe -1.27, max drawdown 98.1%).
- Every one of the 12 grid cells is
  negative at every tier.

**Why, mechanically.** The strategy's premise is that ln(BTC) − ln(ETH) mean-reverts. On
this sample it does not: the ADF rejects a unit root in only
14% of training windows at the 5% level, and the relationship the data
*does* support has a median β of
0.74 — nowhere near the 1:1 hedge the
strategy holds. A 2.0σ entry into a spread that trends instead of
reverting is a loss-generating machine, and the walk-forward record shows it: the worst
single window is
window 0 (2018-07-19 → 2018-09-19) at **-49.6%** — a mean-reversion book
meets a spread that keeps widening by holding, and re-normalizing to constant gross every
bar means holding *harder* as the loss accumulates.

**Where the money goes, at real costs.** Fees 14,589, borrow
6,110, margin interest 6,129 — on
100,000 of starting capital over
7.4 years. The two carry bricks together are comparable in size to the fee
bill even at the taker tier, which is the structural point a long-only study cannot make:
**a pairs book pays rent on both the short leg and the leverage, every day it is in a
trade, whether or not it trades.**

**The borrow assumption, stated because it is the most result-corrupting choice available
(D124).** The headline uses 10%/yr on the short leg.
The sensitivity spans -97.1% at 0%/yr to
-98.9% at 25%/yr. A silent zero would have left
**1.47× the terminal wealth** the
stated rate produces — a large relative flattery on a small base — and would have been
indefensible: shorting spot BTC or ETH means borrowing the coin from a venue, and that is
neither free nor stable. What makes the verdict robust is not the rate chosen but that
**it does not move at 0%/yr either**: the strategy still loses
97%.

**Gross exposure.** De-levering to `leg_weight` = 0.5 makes gross exposure equal NAV, and
margin interest collapses from 6,129 to
318; at 0.25 it is exactly zero. That is D96's threshold
arithmetic reproduced on a different instrument, and it is the study's one clean
confirmation of an earlier finding. It does not rescue anything: total return improves to
-80.2% and -53.7% because a smaller position loses
less, while Sharpe goes -1.27 →
-1.23 → -1.42 —
**not** monotone, because the 4% risk-free hurdle does not
scale down with the position. De-levering a negative-drift strategy walks it toward cash,
and against a positive rf, cash strictly beats it.

**What survives.** The market-neutrality claim, and only that: realised beta
-0.0112 / +0.0216
/ -0.0055 against the two legs and the basket, against a D37
expectation of ≈ 0. The engineering works. The thesis does not.

## What would change the answer

Not a cheaper venue, and not a better parameter. The three levers that could matter, in
descending order:

1. **A hedge ratio the data supports.** β is systematically far from 1 and moves across
   windows. D94 already found that a static per-window β estimate cost more in estimation
   noise than it bought on the ETF universe — but on a pair whose β median is
   0.74 rather than ≈ 1, that finding
   does not transfer, and a β-hedged version of this study is the obvious next experiment.
2. **A pair chosen inside the training window, from a universe.** D22's rule, which this
   study structurally cannot satisfy. Crypto has enough liquid assets for a real selection
   step, and that would also give the DSR something honest to deflate.
3. **A cointegration gate on the trade itself**, not just as a diagnostic: stand aside in
   windows where the training-window ADF does not reject. On this pair that would mean
   standing aside 86% of the time, which is close to "do not trade
   this pair" — the same conclusion by a longer route.


---

# Standing caveats (R3)

1. **Meta-in-sample by pair choice (D22/D70).** BTC/ETH was not selected by any procedure
   in this study; it was chosen because it is the famous crypto pair. There is no
   selection step, so there is nothing for D29's multiplicity correction to work on, and
   the DSR cannot see this bias. The direction of the bias is *toward* a flattering
   result, which makes the negative verdict conservative.
2. **The sample is ETH's.** Inner-join alignment (D45/D63) truncates the study to
   2017-11-09 onward, discarding 1,043 BTC bars. Correct for a pairs trade, but it means
   no number here shares a span with `BREAKOUT_RESULTS.md`'s BTC rows.
3. **`exit_z` is not swept.** Held at D69's 0.5 across all 12 grid cells. The hysteresis
   band's width is a real degree of freedom and it was not explored.
4. **Borrow and margin rates are assumptions, not measurements.**
   10%/yr coin borrow and
   10%/yr USD margin are mid-range for this sample's
   venues; both were swept, neither was sourced from a rate history. A real study would
   use a borrow-rate time series, and crypto borrow rates spike exactly when spreads
   dislocate — i.e. precisely when this strategy is largest.
5. **Fees only, on the trade side.** No bid/ask spread, no market impact, no slippage. The
   tiers are `breakout_study`'s and carry D114's caveat unchanged: a market order into a
   dislocated spread is the adversely-selected moment to trade, and daily bars cannot see
   it. Every return here is optimistic on that axis.
6. **Spot, not perpetuals (D108).** Modelled as `Equity(quantity_precision=8)`. A
   perpetual-futures implementation would replace the borrow brick with funding — and
   funding on BTC/ETH perps has historically *paid* shorts on average, which is the one
   modelling change that could move the cost side materially in the strategy's favour.
   It would not close a -89%
   zero-cost gap.
7. **Single data source (D26).** yfinance only, no second-source cross-check. Crypto daily
   bars are a cross-venue aggregate, so "the open" is a convention rather than a price
   anyone was quoted.
8. **Constant-gross re-normalization.** `ZScorePairsStrategy` emits a target *weight*
   every bar, and `Sizer` re-sizes to current NAV (D61), so both legs are rebalanced daily
   while in a trade. That is the framework's existing pairs convention (D94) and it drives
   the 31× turnover. A
   band-rebalanced implementation would trade far less; it is a strategy change, not a
   study knob, and was not made.
