# A cross-sectional long/short portfolio across 62 coins

**Produced:** 2026-08-22 ·
**Snapshot:** `318edab51866d81986f1426abf9ab275908b27f2c6b0b8330a6529263c89b957` ·
**Reproduce:** `uv run python scripts/run_portfolio_universe.py` (offline, deterministic)

## What this is

D182 combined each coin's own two books and found the pairing costs 118 percentage points
of median return to buy 4.7 of drawdown. That answered *"does pairing one coin's two books
help?"* and deliberately did not answer the question underneath: **does a long/short book
run ACROSS the cross-section work?**

The difference is diversification between coins — the one thing no study in this project
has ever had. Every prior result is a single-instrument book, or a cross-section of
single-instrument books averaged afterwards. **Averaging Sharpes is not the same as
earning the Sharpe of an average**, and that gap is the whole subject here.

Both baselines are the published ones, unchanged (D141); the long arm is
`breakout_universe.baseline_variant()` itself. On each date the long portfolio earns the
equal-weighted mean of every long book with a position open, likewise the short, and the
two are combined at D181's expanding inverse-vol weights.

62 symbols, 3,762 dates, 2015-09-11 to 2025-12-28.
Reference tier `taker_40bp`; the short leg pays borrow at
10%/yr. The first 252 bars are weighting warm-up and
are excluded from every figure, all three arms alike.

## Does diversifying across coins do what diversifying within a coin could not?

| | Sharpe | Total return | Max DD | Median SINGLE coin Sharpe | Median single coin return |
|---|---|---|---|---|---|
| long portfolio | +1.277 | +2,907.9% | 28.8% | +0.437 | +152.4% |
| short portfolio | -0.580 | -52.8% | 60.8% | -0.450 | -55.9% |
| **combined portfolio** | **+0.115** | +55.0% | 22.4% | — | — |

**Diversifying across coins lifts the long book from +0.437 on the median single coin to +1.277 as a portfolio — +0.840.** That is the one form of diversification this project had never tested, and it is the only one that operates on the return distribution rather than on a losing book's timing.

**Adding the short portfolio costs -1.162 Sharpe** and moves max drawdown by -6.4 pp. The D182 finding survives at portfolio level: the short book subtracts.

## Breadth — how many coins the portfolio could hold

A portfolio of one coin is a coin. This counts the books **live in the sample** on each
date — coins whose own walk-forward has started and which have not wiped out. It is an
upper bound on positions, not a position count: a book that is flat still contributes a
0.0 return and is counted here.

| Date | Long books live | Short books live |
|---|---|---|
| 2015-09-11 | 2 | 2 |
| 2018-04-08 | 2 | 2 |
| 2020-11-04 | 50 | 50 |
| 2023-06-02 | 61 | 60 |
| 2025-12-28 | 1 | 1 |

Median **50** live, maximum 62. On **1,048 of
3,762** dates (28%) fewer than four coins were live at all, and those
dates sit at the start of the sample where only the oldest coins had cleared their
walk-forward.

**Position-level breadth is not measured here.** The long book is in the market roughly
half the time and the short book far less, so the number of positions actually held is
materially below these counts. That matters for whether daily equal-weighting across coins
is a realistic construction, and this study does not answer it.

## Does the long portfolio's Sharpe survive dropping the thin early sample?

The pre-registration named this as the way H1 could hold for the wrong reason. Each row
keeps only the dates on which at least that many long books were open, and rescores.

| Long books live | Dates kept | Long portfolio Sharpe | Combined Sharpe |
|---|---|---|---|
| >= 1 | 3,510 | +1.274 | +0.109 |
| >= 5 | 2,712 | +0.926 | -0.026 |
| >= 10 | 2,708 | +0.927 | -0.012 |
| >= 20 | 2,708 | +0.927 | -0.012 |
| >= 30 | 2,708 | +0.927 | -0.012 |

The rows above 5 are identical because the universe fills in quickly: there is essentially
no period with between five and thirty coins live, so every threshold past five selects the
same 2,708 dates.

A Sharpe that climbed as the thin dates were dropped would mean the early, near-single-coin
period was dragging the headline down; one that collapsed would mean the headline was that
period's luck. Conditioning on breadth is not a free lunch either — it is a filter applied
after the fact, and the rows are a robustness reading rather than a tradable variant.

## Charging the rebalancing cost

D183 charged nothing for moving capital between coins and named that as the test of its own
result. This charges it — **on the benchmark too**, because the equal-weight universe
rebalances daily as well and charging only the strategy would rig the comparison.

Turnover is one-way, `0.5 * sum |drifted weight - target weight|`, and buy-and-hold is
charged nothing after its initial purchase because it does not trade again.

Net Sharpe at each cost level:

| Book | Annual turnover | 0 bp | 10 bp | 25 bp | 40 bp |
|---|---|---|---|---|---|
| **LONG portfolio (strategy)** | 1.8x | +1.277 | +1.271 | +1.261 | +1.252 |
| Equal-weight universe | 4.8x | +1.196 | +1.191 | +1.182 | +1.174 |
| BTC buy & hold | 0.0x | +1.096 | +1.096 | +1.096 | +1.096 |

Strategy edge over the equal-weight universe: 0bp **+0.081** · 10bp **+0.080** · 25bp **+0.079** · 40bp **+0.078**.

**The edge breaks even at 972 bp** of one-way cost per unit of turnover. Below that the strategy beats the equal-weight universe on a like-for-like basis; above it, it does not.

**A flat book holds cash and moving cash is free**, which the turnover measure gets right
on its own: a flat book reports exactly 0.0, so its slice does not drift. What is still
over-charged is a flat book joining or leaving the live set, counted as a full slice
traded when it was cash — and over-charging is the right direction for a test built to
threaten a result.

## How the risk budget splits, and the flaw it carries

Mean weight on the LONG portfolio: **0.302**. Long/short correlation
**-0.0410**; the weighting fell back to 50/50 on 0
bars.

Inverse-vol weighting reads a book that is flat most of the time as low-risk, when what it actually is, is absent (D181). **Aggregation makes this WORSE, not better.** Pooling 62 coins diversifies the short arm's own returns, which lowers its measured volatility, which inverse-vol rewards with MORE weight — so the losing leg carries 70% of the risk budget here against 61% on BTC alone (D181). The construction pays a book for being diversified and for being absent, and neither is a reason to give it capital.

## 2 book(s) wiped out and were truncated

Once NAV reaches zero the per-bar return is not a return — the denominator's sign has
flipped — and averaging it into a portfolio would propagate nonsense across every other
coin. These books are dead from the date shown and contribute nothing after it.

| Book | Dead from |
|---|---|
| `LUNA1-USD/short` | 2022-05-14 |
| `LUNC-USD/short` | 2022-05-14 |

This is **stricter** than the per-symbol studies, which let a book keep trading a negative
account (D175), and it is the more realistic of the two. It is still not a liquidation
model: a real venue would have closed the position earlier, and at a worse price.

## Standing caveats

1. **No rebalancing cost between coins.** Each coin's own trading costs are charged inside
   its book. Moving capital between coins to hold equal weights is free here and is free
   nowhere else. Every number above is optimistic by an amount this study does not measure,
   and the daily-rebalanced equal weight is the most turnover-hungry construction there is.
2. **Return aggregation, not a portfolio backtest.** No shared capital constraint, no
   cross-sectional position limit, no netting of a long and a short in the same coin beyond
   what the arithmetic does on its own.
3. **Universe membership is fixed in advance.** `UniversePolicy` admits on tradability and
   data adequacy only, with no return, Sharpe or drawdown input (D140) — but a coin is
   admitted because of how much history it *turns out* to have, which is not knowable on
   the first day it is held. The same limitation D140/D141 carries.
4. **Early breadth is thin.** The portfolio starts with whatever had cleared its
   walk-forward by 2015-09-11, and a one-coin "portfolio" is a single coin.
5. **The short book is what it is.** It loses on 57 of 62 coins (D182), and no allocation
   scheme creates an edge from a leg that does not have one.
6. **No margin call, no liquidation, no borrow recall (D175).** Books that wipe out are
   truncated here rather than allowed to trade a negative account, which is stricter than
   the per-symbol studies and still not a model of what a venue would have done.
