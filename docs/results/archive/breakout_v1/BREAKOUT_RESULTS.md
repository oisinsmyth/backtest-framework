# Long-flat breakout: does trend following on BTC/ETH survive exchange fees?

**Produced:** 2026-08-18 ·
**Snapshot:** `a2dfbc34c975895a1a2a133e00cdc36978a14f38bea5b83e568cd64b28f28032` ·
**Registry:** `data/breakout_study_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** This is a **directional, beta-loaded** strategy: long
> or flat on a single high-beta instrument, never short. It is **not** part of this
> project's market-neutral thesis, and it is not evidence about it. It is here because
> the framework claims a strategy is a swappable brick, and a long-only crypto trend
> follower is about as far from a market-neutral ETF pairs book as one can get while
> reusing the same engine, cost stack, walk-forward harness and trial registry. Its
> honest benchmark is buy-and-hold, not the risk-free rate.

**Data.** BTC-USD and ETH-USD daily bars, 00:00 UTC boundary, fixed — no alternative
boundary was tested. Fixture `data/fixtures/crypto_daily_2015_2025_raw.csv.gz`, frozen
through the Step-7 pipeline. The sanity gate (D25/D26) reported
**0 cleaning change(s)** and **0 hard
violation(s)**, with 7 warning(s) — all of them genuine large crypto
moves (2017-12, 2020-03, 2021-01, 2021-05), none of them quarantining.

**Scale.** 184 out-of-sample trials logged
(23 strategy variants × 4 cost tiers ×
2 symbols) plus 4,896 in-training-window
parameter evaluations, all counted in the multiplicity section. Risk-free rate
4%; annualisation on 365 days (crypto trades
every calendar day, D17).


## Method, in one screen

**Signal.** Enter long when `close(t) > max(high)` over bars t−N_entry … t−1. Exit to
flat when `close(t) < min(low)` over bars t−N_exit … t−1. Baseline
N_entry=40, N_exit=10. Both extrema exclude the
current bar, so a bar cannot trigger on itself. No shorting; flat is the default state.

**Execution.** `fill_timing="next_open"` (D103): a decision taken at bar t's close fills
at bar t+1's **open**. The strategy never trades at the price that produced its signal.

**Sizing.** Inverse-volatility: weight = 40% target annual vol ÷ trailing realized vol
(20-day sample stdev of log returns **ending at t−1**, D44), capped at 1.0× capital,
fixed at entry for the life of the trade. Two sensitivities are run: fixed-fractional at
1.0, and inverse-vol recomputed every bar.

**Walk-forward.** train=252, test=63, step=63.
Anything fitted is fitted on a training slice only. See "one continuous run" below.

**Costs.** One `percent_spread` brick per tier through the existing `CostStack`:
`maker_0bp` = 0.00% (maker), `maker_10bp` = 0.10% (maker), `maker_25bp` = 0.25% (maker), `taker_40bp` = 0.40% (taker). No
commission, no bid/ask spread, no market impact, no funding, no borrow — this is an
**exchange fee model and nothing more**, which makes every number here optimistic.

**Benchmark.** Buy-and-hold the same instrument over the same span at the same fee tier:
buy at the second OOS bar's open (the earliest any decision could fill), hold a fixed
quantity, mark at the final close with no forced liquidation — exactly how a strategy
variant that ends long is marked.


---

## Read this first: what was found before any performance was measured

The brief said result-corrupting issues take priority over tuning. Three things surfaced.
None of them silently corrupted a number; two changed what got built, one is a blocker.

### 1. BLOCKER — the volume-confirmation filter cannot be built (D111)

Filter 2 of the brief ("trigger bar volume > 1.5× 20-day average volume") is **not
implemented**, and was not worked around.

`Bar` carries `open`, `high`, `low`, `close` and nothing else. `TimestampedBar` adds only
a timestamp. `DataView` — the structural look-ahead guard strategies receive (D32) —
hands out `Bar` objects. Volume is fetched, cleaned, validated and stored in snapshots,
but it stops at the data layer: `csv_fixture.py` says so explicitly, calling a volume
field on `TimestampedBar` "a false affordance (D48)".

The two ways around it are both worse than not having the filter:

- **Add volume to `Bar` / `TimestampedBar` / `DataView`.** That is a change to three
  existing interfaces, rippling through the simulator, the cost bricks, the golden
  masters and the cross-engine reconciliation. The brief forbids modifying existing
  interfaces, and it is right to — this is a schema change to the framework's most
  load-bearing type, not a strategy feature.
- **Pass a volume series into the strategy's constructor.** This hands strategy code
  full-sample data that sits outside the DataView guard — exactly the look-ahead hole
  D32 exists to close, and it would do so invisibly, since nothing would fail.

So the filter is absent rather than faked, and no `VolumeConfirmationFilter` class exists
to imply otherwise. **The three other filters are implemented and measured in full.**
The interface change needed is small and well-defined (a volume field on `TimestampedBar`
threaded into `build_data_view`), but it is a framework decision, not a study decision.

### 2. The chained-window harness would have distorted this strategy (D113)

The pairs study runs each walk-forward window as its own backtest, chaining capital
window to window. For a mean-reverting strategy holding for days, the seam is cheap. For
a trend follower holding for weeks-to-months it is not: every window boundary would force
the book flat, return the position to cash **with no exit cost**, and then require a
brand-new breakout before the trend could be re-entered.

That is not a small effect on a study whose whole question is whether tens of basis points
matter. So each (symbol, variant, tier) here is **one continuous out-of-sample backtest**
over the union of the test windows, with the walk-forward structure still doing its job:
the OOS span starts exactly where window 0's training slice ends, per-window returns are
sliced out for per-window trial rows, and anything fitted is fitted per window and applied
through a parameter **schedule** (`ScheduledBreakout`) that swaps configuration at window
boundaries while the position carries across. No forced flattening, no free liquidations.

The warm-up prefix is exactly the strategy's own warm-up requirement, so its guard keeps
it flat through the entire prefix and no in-sample P&L can reach the reported curve. The
harness asserts this at runtime (it raises if any fill lands in the prefix) rather than
trusting it.

### 3. Fill semantics and look-ahead: checked, clean

- **Extrema exclude the current bar.** Asserted directly, and by property test: perturbing
  any bar after the decision bar — arbitrarily, scaled by up to 100× — cannot change a
  single target the strategy produced up to that bar, at the signal level *and* through
  the full engine with costs and next-open fills.
- **Fills never use the signal bar's price.** Pinned by the golden master: the entry
  decision at bar 3's close produces a fill stamped on bar 4 at bar 4's open.
- **Costs are exactly the fee rate × traded notional**, on every fill including
  rebalances, and final NAV is monotone non-increasing in the fee tier. Both property
  tested; the golden master reconciles NAV to the penny by hand.

One typing observation, not a defect: `engine/strategy.py`'s `Strategy` protocol declares
`strategy_id` as a settable attribute, so the frozen `ScheduledWeightStrategy` does not
type-conform — the same protocol-variance trap audit F20 fixed on
`Instrument.quote_currency`. Left alone (it is an existing interface) with a narrow
`type: ignore` and this note.


---

# BTC-USD

Out-of-sample span **2015-09-10 to 2025-11-12** — 3,717 daily
bars across 59 walk-forward windows (train 252, test
63, step 63). Every number below is out of sample.

## Every variant at the reference tier (`taker_40bp`, 0.40% taker)

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_20_5` | +2214.84% | +36.14% | 1.06 | 46.9% | 77 | 34.8% | 22.4% |
| `plateau_20_10` | +7202.12% | +52.40% | 1.26 | 41.2% | 54 | 47.8% | 13.4% |
| `plateau_20_20` | +8766.78% | +55.33% | 1.22 | 37.4% | 38 | 62.5% | 12.1% |
| `plateau_30_5` | +2072.63% | +35.30% | 1.03 | 50.1% | 66 | 30.0% | 22.0% |
| `plateau_30_10` | +6447.08% | +50.78% | 1.20 | 47.9% | 47 | 41.4% | 13.5% |
| `plateau_30_20` | +10220.15% | +57.67% | 1.20 | 47.9% | 34 | 55.4% | 10.8% |
| `plateau_40_5` | +1707.16% | +32.87% | 1.00 | 48.4% | 56 | 26.5% | 19.8% |
| `plateau_40_10` | +5657.04% | +48.88% | 1.20 | 43.0% | 38 | 36.7% | 11.2% |
| `plateau_40_20` | +8708.54% | +55.23% | 1.18 | 47.4% | 30 | 48.4% | 9.6% |
| `plateau_55_5` | +1209.08% | +28.73% | 0.92 | 41.7% | 51 | 23.4% | 17.4% |
| `plateau_55_10` | +4673.10% | +46.17% | 1.17 | 35.6% | 33 | 32.8% | 7.7% |
| `plateau_55_20` | +7086.79% | +52.16% | 1.15 | 46.7% | 26 | 44.2% | 7.3% |
| `filter_debounce_m2` | +1878.62% | +34.06% | 0.96 | 38.4% | 28 | 26.7% | 10.9% |
| `filter_volcontract_0.8` | +2236.60% | +36.27% | 1.05 | 36.8% | 20 | 21.0% | 7.8% |
| `filter_volcontract_1.0` | +4103.67% | +44.36% | 1.15 | 39.1% | 31 | 31.6% | 9.6% |
| `filter_trend_gate_200` | +5962.27% | +49.64% | 1.24 | 38.9% | 33 | 34.0% | 10.2% |
| `sizing_fixed_1.0` | +8019.21% | +54.00% | 1.16 | 48.2% | 38 | 36.7% | 12.5% |
| `sizing_invvol_daily` | +2958.68% | +39.92% | 1.18 | 42.6% | 38 | 36.7% | 16.9% |
| `voltarget_020` | +3022.17% | +40.20% | 1.23 | 30.3% | 38 | 36.7% | 8.8% |
| `voltarget_030` | +5142.62% | +47.52% | 1.24 | 38.5% | 38 | 36.7% | 10.4% |
| `voltarget_060` | +6224.07% | +50.26% | 1.15 | 48.7% | 38 | 36.7% | 12.4% |
| `voltarget_080` | +6939.89% | +51.85% | 1.15 | 48.3% | 38 | 36.7% | 12.5% |
| `selected_in_train` | +4482.58% | +45.59% | 1.11 | 37.9% | 53 | 41.8% | 12.4% |
| **buy & hold** | +42386.71% | +81.17% | 1.16 | 83.4% | 1 | 100.0% | — |

## Baseline across the cost tiers — maker vs taker

| Tier | Fee | Role | Total return | CAGR | Sharpe (ann.) | Costs paid | Costs / gross P&L | Buy & hold (same tier) |
|---|---|---|---|---|---|---|---|---|
| `maker_0bp` | 0.00% | maker | +7367.18% | +52.74% | 1.27 | 0 | 0.0% | +42556.66% |
| `maker_10bp` | 0.10% | maker | +6898.03% | +51.77% | 1.26 | 205,660 | 2.9% | +42514.05% |
| `maker_25bp` | 0.25% | maker | +6247.94% | +50.32% | 1.23 | 478,930 | 7.1% | +42450.28% |
| `taker_40bp` | 0.40% | taker | +5657.04% | +48.88% | 1.20 | 713,983 | 11.2% | +42386.71% |

## Filter increments, one at a time on top of the baseline

Each row is the baseline (`plateau_40_10`) with exactly ONE filter brick added — never
stacked — so each delta prices exactly one component.

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +5657.04% | +48.88% | 1.20 | 43.0% | 38 | 36.7% | 11.2% |
| `filter_debounce_m2` | +1878.62% | +34.06% | 0.96 | 38.4% | 28 | 26.7% | 10.9% |
| `filter_volcontract_0.8` | +2236.60% | +36.27% | 1.05 | 36.8% | 20 | 21.0% | 7.8% |
| `filter_volcontract_1.0` | +4103.67% | +44.36% | 1.15 | 39.1% | 31 | 31.6% | 9.6% |
| `filter_trend_gate_200` | +5962.27% | +49.64% | 1.24 | 38.9% | 33 | 34.0% | 10.2% |
| **buy & hold** | +42386.71% | +81.17% | 1.16 | 83.4% | 1 | 100.0% | — |

At the free tier (`maker_0bp`), which isolates the filters' effect on the SIGNAL from
their effect on costs:

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +7367.18% | +52.74% | 1.27 | 40.6% | 38 | 36.7% | 0.0% |
| `filter_debounce_m2` | +2305.21% | +36.66% | 1.02 | 35.6% | 28 | 26.7% | 0.0% |
| `filter_volcontract_0.8` | +2604.91% | +38.24% | 1.10 | 33.6% | 20 | 21.0% | 0.0% |
| `filter_volcontract_1.0` | +5147.68% | +47.54% | 1.22 | 37.2% | 31 | 31.6% | 0.0% |
| `filter_trend_gate_200` | +7519.26% | +53.04% | 1.30 | 35.2% | 33 | 34.0% | 0.0% |
| **buy & hold** | +42556.66% | +81.24% | 1.16 | 83.4% | 1 | 100.0% | — |

## Parameter plateau surface — annualised Sharpe at `taker_40bp`

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | 1.06 | 1.26 | 1.22 |
| **30** | 1.03 | 1.20 | 1.20 |
| **40** | 1.00 | 1.20 | 1.18 |
| **55** | 0.92 | 1.17 | 1.15 |

Same surface, CAGR:

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | +36.14% | +52.40% | +55.33% |
| **30** | +35.30% | +50.78% | +57.67% |
| **40** | +32.87% | +48.88% | +55.23% |
| **55** | +28.73% | +46.17% | +52.16% |

Same surface, closed-trade counts (the mechanical explanation for the shape):

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | 77 | 54 | 38 |
| **30** | 66 | 47 | 34 |
| **40** | 56 | 38 | 30 |
| **55** | 51 | 33 | 26 |

**Spike test.** Best cell is N_entry=20,
N_exit=10 at Sharpe 1.262; its
immediate neighbours average 1.143; the whole
12-cell surface spans
0.916 to 1.262
(spread 0.346). The best-minus-neighbours gap is
**0.34 of the surface's own spread**.
**Borderline.** The top cell sits meaningfully above its immediate neighbours: not a clean plateau, and the best cell should not be quoted as the strategy's performance. Every N_entry row ranks the exit windows identically (N_exit=10 best, N_exit=5 worst), so the surface has consistent structure rather than scattered high cells — the neighbour gap here comes from one systematically weaker column, not from one lucky cell.

## Benchmarks: three ways to be long

Comparing a strategy that is in the market 37% of the time against a
100%-invested benchmark answers "would you have been better off just holding it" — worth
knowing, and not a like-for-like risk comparison. The third row fixes that: hold a
**constant 37% of capital** in the instrument and the rest in cash, so average
exposure matches the strategy's own and the only remaining difference is *when* the
exposure was taken. It runs through the same engine and tier, so its constant-fraction
rebalancing pays real fees (D119).

| | Total return | CAGR | Sharpe (ann.) | Max DD | Time in market |
|---|---|---|---|---|---|
| **Strategy** (`plateau_40_10`) | +5657.0% | +48.9% | 1.20 | 43.0% | 37% |
| Buy & hold, 100% | +42386.7% | +81.2% | 1.16 | 83.4% | 100% |
| Constant 37% of capital, rest cash | +1357.6% | +30.1% | 1.03 | 44.3% | 37% (always) |

Against the matched-exposure benchmark the strategy
earns 4.2× the terminal wealth
at a similar
drawdown. **Timing the exposure beat spreading it evenly** — which is a materially better
case than the 100% row alone suggests, and it is the comparison a reviewer should be
handed first.

**But the Sharpe differences are not measurable at this sample size.** Paired block
bootstrap (20-bar blocks, 4,000 sims, seed 0;
the same resampled bar indices applied to both series so their correlation is preserved,
D120):

| Comparison | Observed Δ Sharpe | 90% interval | P(Δ > 0) |
|---|---|---|---|
| Strategy − buy & hold (100%) | +0.037 | [-0.449, +0.534] | 55% |
| Strategy − constant 37% | +0.170 | [-0.314, +0.661] | 72% |

Ten years of daily data buys a standard error of roughly ±0.4 on an annualised Sharpe.
Both intervals span zero comfortably. **The return and drawdown differences are the
defensible findings; the Sharpe differences are not.** Any sentence in this report that
leans on a Sharpe gap of a few hundredths should be read as arithmetic, not evidence.

## Is this the strategy, or is it the era?

**Yes, the absolute numbers are the era.** BTC-USD closed at $238 on the
first out-of-sample bar and $101,663 on the last — **426× the price**.
Any long-biased rule applied to that decade produces a number with too many digits in it.
A four-figure percentage return here is a fact about the instrument, not about the
breakout rule, and it should never be quoted on its own.

What the rule contributed is only visible year by year.

| Year | Strategy | Buy & hold | Trades opened | Time in market |
|---|---|---|---|---|
| 2015 | +18.6% | +79.9% | 1 | 23% |
| 2016 | +89.8% | +123.8% | 3 | 39% |
| 2017 | +162.0% | +1368.9% | 5 | 56% |
| 2018 | -9.6% | -73.6% | 2 | 8% |
| 2019 | +50.5% | +92.2% | 3 | 26% |
| 2020 | +221.2% | +303.2% | 5 | 53% |
| 2021 | +44.3% | +59.7% | 4 | 47% |
| 2022 | -16.6% | -64.3% | 2 | 6% |
| 2023 | +49.2% | +155.4% | 5 | 52% |
| 2024 | +43.8% | +121.1% | 4 | 43% |
| 2025 | -13.6% | +8.8% | 4 | 42% |

The pattern is stark and it is the whole strategy in one table: **the strategy lost to
buy-and-hold in 9 of the 9 up years, and beat it in
2 of the 2 down years.** Time in market tracks it exactly —
heavily invested through the bull years, nearly flat through the bear ones. This is not an
edge in the sense of predicting returns; it is **insurance, bought with bull-market
underperformance and paid out in bear markets**. Whether that trade is good depends
entirely on how many bear markets your sample contains, and this one contains two.

Which is why the start date matters as much as the strategy:

| OOS begins | Bars | Strategy | Buy & hold | Strategy CAGR | B&H CAGR | Strategy Sharpe | B&H Sharpe | Strategy max DD | B&H max DD |
|---|---|---|---|---|---|---|---|---|---|
| 2015-09-10 | 3,717 | +5657.0% | +42386.7% | +48.9% | +81.2% | 1.20 | 1.16 | 43% | 83% |
| 2018-09-10 | 2,646 | +979.5% | +1322.1% | +38.8% | +44.2% | 1.03 | 0.84 | 43% | 77% |
| 2020-09-09 | 1,890 | +449.0% | +901.6% | +38.9% | +56.0% | 1.01 | 0.98 | 43% | 77% |
| 2021-09-10 | 1,512 | +54.9% | +140.4% | +11.1% | +23.6% | 0.39 | 0.59 | 28% | 77% |
| 2022-09-10 | 1,197 | +64.3% | +304.8% | +16.3% | +53.2% | 0.54 | 1.05 | 28% | 32% |

Identical configuration, identical rules — only the investor's start date changes. The
strategy's CAGR ranges from +11.1% to +48.9% across these
starts. **A result that moves that much on the choice of start date is describing the
sample, not the rule.** Note too that the strategy's Sharpe advantage over buy-and-hold
does not survive the later starts at all (2 of 5 start dates have
it BELOW the benchmark).

The one thing that holds in every row is the drawdown reduction — the strategy's max drawdown is lower at every start date, by 5 to 48 percentage points — and that,
rather than any return or Sharpe claim, is the finding this study can actually defend.

## Sizing sensitivity, including the vol target this study picked and never tested

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +5657.04% | +48.88% | 1.20 | 43.0% | 38 | 36.7% | 11.2% |
| `sizing_fixed_1.0` | +8019.21% | +54.00% | 1.16 | 48.2% | 38 | 36.7% | 12.5% |
| `sizing_invvol_daily` | +2958.68% | +39.92% | 1.18 | 42.6% | 38 | 36.7% | 16.9% |
| `voltarget_020` | +3022.17% | +40.20% | 1.23 | 30.3% | 38 | 36.7% | 8.8% |
| `voltarget_030` | +5142.62% | +47.52% | 1.24 | 38.5% | 38 | 36.7% | 10.4% |
| `voltarget_060` | +6224.07% | +50.26% | 1.15 | 48.7% | 38 | 36.7% | 12.4% |
| `voltarget_080` | +6939.89% | +51.85% | 1.15 | 48.3% | 38 | 36.7% | 12.5% |
| **buy & hold** | +42386.71% | +81.17% | 1.16 | 83.4% | 1 | 100.0% | — |

The 40% annual vol target was the one free parameter of the original study
that was chosen and never tested, so it is swept here (D118) over
20%, 30%, 40%, 60%, 80%.

**The dial works; the Sharpe does not move.** Total Sharpe spread across the whole ladder
is 0.09 — an order of magnitude inside the ±0.4 bootstrap band established
above — so no target level is distinguishable from any other on risk-adjusted grounds,
and its effect on drawdown and return is not monotone in the target. At 20% the strategy returns +3022.2% with a
30.3% max drawdown; at 80% it returns
+6939.9% with 48.3%. The nominally best
Sharpe (1.24) sits at a 30% target against
1.20 at the baseline, which is noise, not a discovery.

Against no vol targeting at all — `sizing_fixed_1.0`, always 100% of capital when long —
the baseline gives up
29% of terminal wealth
(+5657.0% vs +8019.2%) to buy
5.2 percentage points less drawdown
(43.0% vs 48.2%), for a Sharpe change of
+0.04 that cannot be distinguished
from zero. **Stated plainly: the vol target is a drawdown purchase priced in return, not a
Sharpe improvement — pick the level from the drawdown you can tolerate, and do not claim it
improves the risk-adjusted result.** The original write-up implied otherwise by reporting a
single target without the ladder beside it.

## Per-trade diagnostics at `taker_40bp`

| Variant | Win rate | Mean MFE | Mean MAE | Median bars held | p90 bars held | Median bars to stop-out (losers) | Whipsaw rate | Rebalance share of costs | Ann. turnover |
|---|---|---|---|---|---|---|---|---|---|
| `plateau_20_5` | 49.4% | +21.61% | -4.30% | 13 | 35 | 8 | 6.5% | 2.6% | 12.81x |
| `plateau_20_10` | 50.0% | +37.10% | -5.06% | 24 | 76 | 13 | 1.9% | 3.4% | 9.24x |
| `plateau_20_20` | 57.9% | +58.35% | -6.89% | 45 | 148 | 21 | 0.0% | 5.9% | 7.57x |
| `plateau_30_5` | 50.0% | +22.14% | -4.39% | 13 | 34 | 9 | 6.1% | 2.8% | 11.05x |
| `plateau_30_10` | 51.1% | +38.69% | -5.04% | 26 | 83 | 13 | 4.3% | 3.2% | 8.09x |
| `plateau_30_20` | 52.9% | +59.70% | -6.53% | 44 | 133 | 21 | 0.0% | 4.1% | 6.53x |
| `plateau_40_5` | 55.4% | +23.59% | -4.63% | 15 | 35 | 8 | 3.6% | 2.9% | 9.82x |
| `plateau_40_10` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 3.3% | 7.01x |
| `plateau_40_20` | 63.3% | +61.42% | -6.33% | 44 | 133 | 21 | 0.0% | 4.2% | 5.89x |
| `plateau_55_5` | 49.0% | +23.58% | -4.70% | 12 | 33 | 8 | 5.9% | 2.6% | 8.66x |
| `plateau_55_10` | 57.6% | +45.02% | -5.55% | 28 | 87 | 10 | 0.0% | 3.1% | 5.73x |
| `plateau_55_20` | 61.5% | +65.10% | -6.38% | 48 | 132 | 22 | 0.0% | 4.6% | 5.01x |
| `filter_debounce_m2` | 60.7% | +47.71% | -5.32% | 28 | 75 | 10 | 3.6% | 3.3% | 4.63x |
| `filter_volcontract_0.8` | 65.0% | +54.58% | -5.62% | 30 | 76 | 13 | 0.0% | 2.6% | 3.05x |
| `filter_volcontract_1.0` | 58.1% | +42.91% | -5.73% | 30 | 87 | 10 | 0.0% | 2.6% | 6.17x |
| `filter_trend_gate_200` | 57.6% | +47.30% | -4.53% | 30 | 87 | 21 | 0.0% | 3.2% | 6.48x |
| `sizing_fixed_1.0` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 0.2% | 8.02x |
| `sizing_invvol_daily` | 55.3% | +43.03% | -5.34% | 29 | 87 | 13 | 0.0% | 32.0% | 9.56x |
| `voltarget_020` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 11.1% | 4.79x |
| `voltarget_030` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 5.4% | 6.24x |
| `voltarget_060` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 0.7% | 7.89x |
| `voltarget_080` | 57.9% | +43.03% | -5.34% | 29 | 87 | 12 | 0.0% | 0.4% | 8.00x |
| `selected_in_train` | 45.3% | +34.83% | -5.08% | 18 | 63 | 10 | 7.5% | 3.1% | 9.11x |

## Capture ratios at `taker_40bp`

Upside captured = Σ(strategy return on bars the instrument rose) ÷ Σ(instrument return
on those bars). Downside participated is the same on down bars; downside avoided is
1 − that. Drawdown avoided = 1 − (strategy max drawdown ÷ instrument max drawdown).

| Variant | Upside captured | Downside participated | Downside avoided | Drawdown avoided |
|---|---|---|---|---|
| `plateau_20_5` | 27.1% | 23.7% | 76.3% | 43.7% |
| `plateau_20_10` | 37.9% | 33.4% | 66.6% | 50.6% |
| `plateau_20_20` | 46.0% | 42.4% | 57.6% | 55.1% |
| `plateau_30_5` | 26.0% | 22.6% | 77.4% | 40.0% |
| `plateau_30_10` | 37.5% | 33.1% | 66.9% | 42.5% |
| `plateau_30_20` | 48.0% | 44.1% | 55.9% | 42.6% |
| `plateau_40_5` | 23.8% | 20.4% | 79.6% | 42.0% |
| `plateau_40_10` | 34.5% | 30.0% | 70.0% | 48.4% |
| `plateau_40_20` | 44.8% | 40.7% | 59.3% | 43.2% |
| `plateau_55_5` | 21.6% | 18.6% | 81.4% | 50.0% |
| `plateau_55_10` | 32.1% | 27.5% | 72.5% | 57.3% |
| `plateau_55_20` | 42.0% | 38.0% | 62.0% | 44.0% |
| `filter_debounce_m2` | 27.1% | 24.0% | 76.0% | 54.0% |
| `filter_volcontract_0.8` | 23.3% | 19.1% | 80.9% | 55.9% |
| `filter_volcontract_1.0` | 30.7% | 26.3% | 73.7% | 53.2% |
| `filter_trend_gate_200` | 32.8% | 27.8% | 72.2% | 53.3% |
| `sizing_fixed_1.0` | 40.6% | 35.9% | 64.1% | 42.2% |
| `sizing_invvol_daily` | 28.4% | 24.7% | 75.3% | 48.9% |
| `voltarget_020` | 25.3% | 21.0% | 79.0% | 63.6% |
| `voltarget_030` | 31.5% | 26.7% | 73.3% | 53.8% |
| `voltarget_060` | 38.4% | 34.1% | 65.9% | 41.5% |
| `voltarget_080` | 39.6% | 35.1% | 64.9% | 42.0% |
| `selected_in_train` | 36.0% | 32.3% | 67.7% | 54.5% |

## Deflated Sharpe

| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `plateau_20_10` | 0.0711 | 3,716 | 23 | 0.000020 | **1.0000** |
| `maker_10bp` | `plateau_20_10` | 0.0698 | 3,716 | 23 | 0.000020 | **0.9999** |
| `maker_25bp` | `plateau_20_10` | 0.0679 | 3,716 | 23 | 0.000022 | **0.9999** |
| `taker_40bp` | `plateau_20_10` | 0.0660 | 3,716 | 23 | 0.000024 | **0.9998** |


---

# ETH-USD

Out-of-sample span **2018-07-19 to 2025-12-17** — 2,709 daily
bars across 43 walk-forward windows (train 252, test
63, step 63). Every number below is out of sample.

## Every variant at the reference tier (`taker_40bp`, 0.40% taker)

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_20_5` | +595.44% | +29.86% | 0.89 | 31.1% | 48 | 32.4% | 18.5% |
| `plateau_20_10` | +449.73% | +25.81% | 0.70 | 40.4% | 37 +1 open | 39.3% | 18.1% |
| `plateau_20_20` | +570.10% | +29.21% | 0.76 | 54.1% | 26 +1 open | 52.4% | 11.2% |
| `plateau_30_5` | +675.86% | +31.79% | 0.95 | 36.0% | 40 | 29.2% | 13.6% |
| `plateau_30_10` | +827.41% | +35.00% | 0.89 | 34.7% | 31 | 35.5% | 10.7% |
| `plateau_30_20` | +1165.05% | +40.76% | 0.95 | 53.3% | 22 | 47.7% | 6.4% |
| `plateau_40_5` | +485.65% | +26.89% | 0.85 | 25.5% | 36 | 26.8% | 13.1% |
| `plateau_40_10` | +552.21% | +28.74% | 0.78 | 35.2% | 28 | 32.8% | 10.4% |
| `plateau_40_20` | +815.40% | +34.76% | 0.85 | 59.8% | 20 | 43.6% | 6.3% |
| `plateau_55_5` | +574.97% | +29.34% | 0.97 | 20.5% | 30 | 23.9% | 10.2% |
| `plateau_55_10` | +687.55% | +32.06% | 0.90 | 32.4% | 23 | 29.2% | 8.4% |
| `plateau_55_20` | +741.02% | +33.23% | 0.89 | 50.6% | 18 | 37.5% | 5.9% |
| `filter_debounce_m2` | +224.44% | +17.18% | 0.59 | 30.1% | 20 | 23.0% | 10.7% |
| `filter_volcontract_0.8` | +331.86% | +21.79% | 0.67 | 34.7% | 16 | 18.4% | 8.3% |
| `filter_volcontract_1.0` | +454.59% | +25.96% | 0.73 | 35.3% | 24 | 27.9% | 10.7% |
| `filter_trend_gate_200` | +548.54% | +28.65% | 0.80 | 34.7% | 23 | 28.5% | 8.6% |
| `sizing_fixed_1.0` | +662.74% | +31.49% | 0.73 | 47.0% | 28 | 32.8% | 12.0% |
| `sizing_invvol_daily` | +251.22% | +18.44% | 0.62 | 31.5% | 28 | 32.8% | 17.6% |
| `voltarget_020` | +206.68% | +16.30% | 0.68 | 19.1% | 28 | 32.8% | 9.3% |
| `voltarget_030` | +381.80% | +23.60% | 0.75 | 27.6% | 28 | 32.8% | 9.6% |
| `voltarget_060` | +699.39% | +32.32% | 0.77 | 41.7% | 28 | 32.8% | 11.7% |
| `voltarget_080` | +692.27% | +32.16% | 0.75 | 45.3% | 28 | 32.8% | 11.7% |
| `selected_in_train` | +553.43% | +28.78% | 0.82 | 29.6% | 35 | 35.5% | 13.1% |
| **buy & hold** | +500.91% | +27.33% | 0.66 | 82.4% | 1 | 100.0% | — |

## Baseline across the cost tiers — maker vs taker

| Tier | Fee | Role | Total return | CAGR | Sharpe (ann.) | Costs paid | Costs / gross P&L | Buy & hold (same tier) |
|---|---|---|---|---|---|---|---|---|
| `maker_0bp` | 0.00% | maker | +675.23% | +31.78% | 0.84 | 0 | 0.0% | +503.32% |
| `maker_10bp` | 0.10% | maker | +642.50% | +31.01% | 0.82 | 17,341 | 2.6% | +502.71% |
| `maker_25bp` | 0.25% | maker | +595.93% | +29.87% | 0.80 | 41,574 | 6.5% | +501.81% |
| `taker_40bp` | 0.40% | taker | +552.21% | +28.74% | 0.78 | 63,804 | 10.4% | +500.91% |

## Filter increments, one at a time on top of the baseline

Each row is the baseline (`plateau_40_10`) with exactly ONE filter brick added — never
stacked — so each delta prices exactly one component.

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +552.21% | +28.74% | 0.78 | 35.2% | 28 | 32.8% | 10.4% |
| `filter_debounce_m2` | +224.44% | +17.18% | 0.59 | 30.1% | 20 | 23.0% | 10.7% |
| `filter_volcontract_0.8` | +331.86% | +21.79% | 0.67 | 34.7% | 16 | 18.4% | 8.3% |
| `filter_volcontract_1.0` | +454.59% | +25.96% | 0.73 | 35.3% | 24 | 27.9% | 10.7% |
| `filter_trend_gate_200` | +548.54% | +28.65% | 0.80 | 34.7% | 23 | 28.5% | 8.6% |
| **buy & hold** | +500.91% | +27.33% | 0.66 | 82.4% | 1 | 100.0% | — |

At the free tier (`maker_0bp`), which isolates the filters' effect on the SIGNAL from
their effect on costs:

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +675.23% | +31.78% | 0.84 | 34.2% | 28 | 32.8% | 0.0% |
| `filter_debounce_m2` | +263.39% | +18.99% | 0.65 | 29.0% | 20 | 23.0% | 0.0% |
| `filter_volcontract_0.8` | +379.13% | +23.50% | 0.71 | 34.2% | 16 | 18.4% | 0.0% |
| `filter_volcontract_1.0` | +545.48% | +28.56% | 0.80 | 34.2% | 24 | 27.9% | 0.0% |
| `filter_trend_gate_200` | +648.95% | +31.17% | 0.85 | 34.2% | 23 | 28.5% | 0.0% |
| **buy & hold** | +503.32% | +27.40% | 0.67 | 82.4% | 1 | 100.0% | — |

## Parameter plateau surface — annualised Sharpe at `taker_40bp`

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | 0.89 | 0.70 | 0.76 |
| **30** | 0.95 | 0.89 | 0.95 |
| **40** | 0.85 | 0.78 | 0.85 |
| **55** | 0.97 | 0.90 | 0.89 |

Same surface, CAGR:

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | +29.86% | +25.81% | +29.21% |
| **30** | +31.79% | +35.00% | +40.76% |
| **40** | +26.89% | +28.74% | +34.76% |
| **55** | +29.34% | +32.06% | +33.23% |

Same surface, closed-trade counts (the mechanical explanation for the shape):

| N_entry \ N_exit | 5 | 10 | 20 |
|---|---|---|---|
| **20** | 48 | 37 | 26 |
| **30** | 40 | 31 | 22 |
| **40** | 36 | 28 | 20 |
| **55** | 30 | 23 | 18 |

**Spike test.** Best cell is N_entry=55,
N_exit=5 at Sharpe 0.971; its
immediate neighbours average 0.840; the whole
12-cell surface spans
0.704 to 0.971
(spread 0.267). The best-minus-neighbours gap is
**0.49 of the surface's own spread**.
**Borderline.** The top cell sits meaningfully above its immediate neighbours: not a clean plateau, and the best cell should not be quoted as the strategy's performance. The N_entry rows do NOT agree on how to rank the exit windows, which is what an unstructured surface looks like: the parameter is not doing anything consistent, and differences between cells are correspondingly harder to distinguish from noise.

## Benchmarks: three ways to be long

Comparing a strategy that is in the market 33% of the time against a
100%-invested benchmark answers "would you have been better off just holding it" — worth
knowing, and not a like-for-like risk comparison. The third row fixes that: hold a
**constant 33% of capital** in the instrument and the rest in cash, so average
exposure matches the strategy's own and the only remaining difference is *when* the
exposure was taken. It runs through the same engine and tier, so its constant-fraction
rebalancing pays real fees (D119).

| | Total return | CAGR | Sharpe (ann.) | Max DD | Time in market |
|---|---|---|---|---|---|
| **Strategy** (`plateau_40_10`) | +552.2% | +28.7% | 0.78 | 35.2% | 33% |
| Buy & hold, 100% | +500.9% | +27.3% | 0.66 | 82.4% | 100% |
| Constant 33% of capital, rest cash | +198.0% | +15.9% | 0.53 | 41.3% | 33% (always) |

Against the matched-exposure benchmark the strategy
earns 2.8× the terminal wealth
at a different
drawdown. **Timing the exposure beat spreading it evenly** — which is a materially better
case than the 100% row alone suggests, and it is the comparison a reviewer should be
handed first.

**But the Sharpe differences are not measurable at this sample size.** Paired block
bootstrap (20-bar blocks, 4,000 sims, seed 0;
the same resampled bar indices applied to both series so their correlation is preserved,
D120):

| Comparison | Observed Δ Sharpe | 90% interval | P(Δ > 0) |
|---|---|---|---|
| Strategy − buy & hold (100%) | +0.111 | [-0.513, +0.664] | 59% |
| Strategy − constant 33% | +0.242 | [-0.380, +0.794] | 72% |

Ten years of daily data buys a standard error of roughly ±0.4 on an annualised Sharpe.
Both intervals span zero comfortably. **The return and drawdown differences are the
defensible findings; the Sharpe differences are not.** Any sentence in this report that
leans on a Sharpe gap of a few hundredths should be read as arithmetic, not evidence.

## Is this the strategy, or is it the era?

**Yes, the absolute numbers are the era.** ETH-USD closed at $470 on the
first out-of-sample bar and $2,831 on the last — **6× the price**.
Any long-biased rule applied to that decade produces a number with too many digits in it.
A four-figure percentage return here is a fact about the instrument, not about the
breakout rule, and it should never be quoted on its own.

What the rule contributed is only visible year by year.

| Year | Strategy | Buy & hold | Trades opened | Time in market |
|---|---|---|---|---|
| 2018 | +0.0% | -71.7% | 0 | 0% |
| 2019 | -29.4% | -2.8% | 5 | 21% |
| 2020 | +153.5% | +469.2% | 5 | 55% |
| 2021 | +174.2% | +399.1% | 3 | 49% |
| 2022 | -21.4% | -67.5% | 3 | 14% |
| 2023 | +37.1% | +90.6% | 4 | 43% |
| 2024 | +12.5% | +46.1% | 4 | 33% |
| 2025 | +9.5% | -15.0% | 4 | 30% |

The pattern is stark and it is the whole strategy in one table: **the strategy lost to
buy-and-hold in 4 of the 4 up years, and beat it in
3 of the 4 down years.** Time in market tracks it exactly —
heavily invested through the bull years, nearly flat through the bear ones. This is not an
edge in the sense of predicting returns; it is **insurance, bought with bull-market
underperformance and paid out in bear markets**. Whether that trade is good depends
entirely on how many bear markets your sample contains, and this one contains two.

Which is why the start date matters as much as the strategy:

| OOS begins | Bars | Strategy | Buy & hold | Strategy CAGR | B&H CAGR | Strategy Sharpe | B&H Sharpe | Strategy max DD | B&H max DD |
|---|---|---|---|---|---|---|---|---|---|
| 2018-07-19 | 2,709 | +552.2% | +500.9% | +28.7% | +27.3% | 0.78 | 0.66 | 35% | 82% |
| 2018-09-10 | 2,646 | +552.2% | +1438.6% | +29.5% | +45.8% | 0.79 | 0.83 | 35% | 79% |
| 2020-09-09 | 1,890 | +493.0% | +868.0% | +41.0% | +55.0% | 1.03 | 0.90 | 32% | 79% |
| 2021-09-10 | 1,512 | +33.6% | +18.1% | +7.2% | +4.1% | 0.25 | 0.35 | 31% | 79% |
| 2022-09-10 | 1,197 | +46.6% | +67.0% | +12.4% | +16.9% | 0.41 | 0.50 | 31% | 64% |

Identical configuration, identical rules — only the investor's start date changes. The
strategy's CAGR ranges from +7.2% to +41.0% across these
starts. **A result that moves that much on the choice of start date is describing the
sample, not the rule.** Note too that the strategy's Sharpe advantage over buy-and-hold
does not survive the later starts at all (3 of 5 start dates have
it BELOW the benchmark).

The one thing that holds in every row is the drawdown reduction — the strategy's max drawdown is lower at every start date, by 33 to 49 percentage points — and that,
rather than any return or Sharpe claim, is the finding this study can actually defend.

## Sizing sensitivity, including the vol target this study picked and never tested

| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `plateau_40_10` | +552.21% | +28.74% | 0.78 | 35.2% | 28 | 32.8% | 10.4% |
| `sizing_fixed_1.0` | +662.74% | +31.49% | 0.73 | 47.0% | 28 | 32.8% | 12.0% |
| `sizing_invvol_daily` | +251.22% | +18.44% | 0.62 | 31.5% | 28 | 32.8% | 17.6% |
| `voltarget_020` | +206.68% | +16.30% | 0.68 | 19.1% | 28 | 32.8% | 9.3% |
| `voltarget_030` | +381.80% | +23.60% | 0.75 | 27.6% | 28 | 32.8% | 9.6% |
| `voltarget_060` | +699.39% | +32.32% | 0.77 | 41.7% | 28 | 32.8% | 11.7% |
| `voltarget_080` | +692.27% | +32.16% | 0.75 | 45.3% | 28 | 32.8% | 11.7% |
| **buy & hold** | +500.91% | +27.33% | 0.66 | 82.4% | 1 | 100.0% | — |

The 40% annual vol target was the one free parameter of the original study
that was chosen and never tested, so it is swept here (D118) over
20%, 30%, 40%, 60%, 80%.

**The dial works; the Sharpe does not move.** Total Sharpe spread across the whole ladder
is 0.09 — an order of magnitude inside the ±0.4 bootstrap band established
above — so no target level is distinguishable from any other on risk-adjusted grounds,
and its effect on drawdown and return is not monotone in the target. At 20% the strategy returns +206.7% with a
19.1% max drawdown; at 80% it returns
+692.3% with 45.3%. The nominally best
Sharpe (0.78) sits at a 40% target against
0.78 at the baseline, which is noise, not a discovery.

Against no vol targeting at all — `sizing_fixed_1.0`, always 100% of capital when long —
the baseline gives up
14% of terminal wealth
(+552.2% vs +662.7%) to buy
11.9 percentage points less drawdown
(35.2% vs 47.0%), for a Sharpe change of
+0.04 that cannot be distinguished
from zero. **Stated plainly: the vol target is a drawdown purchase priced in return, not a
Sharpe improvement — pick the level from the drawdown you can tolerate, and do not claim it
improves the risk-adjusted result.** The original write-up implied otherwise by reporting a
single target without the ladder beside it.

## Per-trade diagnostics at `taker_40bp`

| Variant | Win rate | Mean MFE | Mean MAE | Median bars held | p90 bars held | Median bars to stop-out (losers) | Whipsaw rate | Rebalance share of costs | Ann. turnover |
|---|---|---|---|---|---|---|---|---|---|
| `plateau_20_5` | 54.2% | +24.42% | -6.29% | 14 | 41 | 6 | 8.3% | 5.6% | 9.59x |
| `plateau_20_10` | 54.1% | +38.78% | -7.51% | 23 | 51 | 10 | 2.7% | 8.2% | 7.99x |
| `plateau_20_20` | 53.8% | +77.39% | -10.75% | 39 | 148 | 18 | 0.0% | 17.1% | 5.77x |
| `plateau_30_5` | 60.0% | +26.64% | -5.79% | 18 | 41 | 8 | 7.5% | 6.3% | 7.79x |
| `plateau_30_10` | 58.1% | +41.84% | -6.27% | 24 | 46 | 15 | 3.2% | 8.7% | 6.45x |
| `plateau_30_20` | 59.1% | +83.58% | -9.04% | 46 | 140 | 22 | 0.0% | 15.8% | 4.69x |
| `plateau_40_5` | 50.0% | +25.80% | -6.64% | 17 | 42 | 10 | 8.3% | 6.5% | 7.08x |
| `plateau_40_10` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 9.1% | 5.78x |
| `plateau_40_20` | 50.0% | +85.84% | -10.14% | 46 | 134 | 29 | 0.0% | 15.5% | 4.39x |
| `plateau_55_5` | 60.0% | +28.46% | -6.05% | 22 | 39 | 10 | 3.3% | 7.2% | 6.07x |
| `plateau_55_10` | 65.2% | +45.36% | -6.02% | 28 | 47 | 16 | 0.0% | 10.1% | 5.10x |
| `plateau_55_20` | 55.6% | +83.67% | -7.90% | 38 | 148 | 25 | 0.0% | 17.2% | 4.00x |
| `filter_debounce_m2` | 55.0% | +40.79% | -6.75% | 28 | 50 | 16 | 0.0% | 13.1% | 4.06x |
| `filter_volcontract_0.8` | 50.0% | +53.20% | -8.80% | 28 | 52 | 14 | 0.0% | 9.0% | 3.26x |
| `filter_volcontract_1.0` | 50.0% | +43.40% | -7.74% | 26 | 52 | 14 | 0.0% | 8.1% | 5.37x |
| `filter_trend_gate_200` | 60.9% | +45.89% | -6.67% | 27 | 52 | 17 | 0.0% | 9.9% | 4.70x |
| `sizing_fixed_1.0` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 0.2% | 7.35x |
| `sizing_invvol_daily` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 37.2% | 8.09x |
| `voltarget_020` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 20.4% | 3.50x |
| `voltarget_030` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 13.7% | 4.79x |
| `voltarget_060` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 2.7% | 7.04x |
| `voltarget_080` | 53.6% | +41.08% | -7.58% | 26 | 52 | 16 | 0.0% | 0.5% | 7.24x |
| `selected_in_train` | 68.6% | +33.90% | -7.05% | 22 | 52 | 11 | 5.7% | 9.8% | 6.60x |

## Capture ratios at `taker_40bp`

Upside captured = Σ(strategy return on bars the instrument rose) ÷ Σ(instrument return
on those bars). Downside participated is the same on down bars; downside avoided is
1 − that. Drawdown avoided = 1 − (strategy max drawdown ÷ instrument max drawdown).

| Variant | Upside captured | Downside participated | Downside avoided | Drawdown avoided |
|---|---|---|---|---|
| `plateau_20_5` | 23.1% | 19.8% | 80.2% | 62.2% |
| `plateau_20_10` | 29.5% | 27.1% | 72.9% | 51.0% |
| `plateau_20_20` | 34.5% | 32.0% | 68.0% | 34.3% |
| `plateau_30_5` | 21.9% | 18.1% | 81.9% | 56.3% |
| `plateau_30_10` | 29.0% | 25.1% | 74.9% | 58.0% |
| `plateau_30_20` | 34.8% | 30.5% | 69.5% | 35.3% |
| `plateau_40_5` | 19.7% | 16.6% | 83.4% | 69.1% |
| `plateau_40_10` | 26.4% | 23.3% | 76.7% | 57.3% |
| `plateau_40_20` | 32.3% | 28.7% | 71.3% | 27.5% |
| `plateau_55_5` | 17.6% | 14.0% | 86.0% | 75.1% |
| `plateau_55_10` | 23.6% | 19.9% | 80.1% | 60.7% |
| `plateau_55_20` | 27.5% | 23.9% | 76.1% | 38.6% |
| `filter_debounce_m2` | 16.6% | 14.7% | 85.3% | 63.4% |
| `filter_volcontract_0.8` | 17.6% | 14.9% | 85.1% | 58.0% |
| `filter_volcontract_1.0` | 23.2% | 20.2% | 79.8% | 57.2% |
| `filter_trend_gate_200` | 23.7% | 20.4% | 79.6% | 58.0% |
| `sizing_fixed_1.0` | 35.2% | 31.8% | 68.2% | 42.9% |
| `sizing_invvol_daily` | 20.1% | 18.4% | 81.6% | 61.8% |
| `voltarget_020` | 14.0% | 12.3% | 87.7% | 76.8% |
| `voltarget_030` | 20.8% | 18.3% | 81.7% | 66.5% |
| `voltarget_060` | 33.0% | 29.4% | 70.6% | 49.4% |
| `voltarget_080` | 34.8% | 31.3% | 68.7% | 45.0% |
| `selected_in_train` | 25.7% | 22.7% | 77.3% | 64.1% |

## Deflated Sharpe

| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `plateau_55_5` | 0.0555 | 2,708 | 23 | 0.000033 | **0.9916** |
| `maker_10bp` | `plateau_55_5` | 0.0543 | 2,708 | 23 | 0.000032 | **0.9903** |
| `maker_25bp` | `plateau_55_5` | 0.0526 | 2,708 | 23 | 0.000031 | **0.9877** |
| `taker_40bp` | `plateau_55_5` | 0.0508 | 2,708 | 23 | 0.000031 | **0.9845** |


---

# Filters: which ones survive out of sample

**Decision rule, fixed before looking:** a filter is kept only if it improves the
out-of-sample annualised Sharpe against the baseline **on every symbol** at the
reference tier (`taker_40bp`). One symbol is a coin flip. Four filter variants across two
symbols is exactly the sample size where something looks good by accident, so the bar
is deliberately strict.

| Filter | Δ Sharpe BTC-USD | Δ Sharpe ETH-USD | Δ max DD BTC-USD | Δ max DD ETH-USD | Decision |
|---|---|---|---|---|---|
| `filter_debounce_m2` | -0.24 | -0.18 | -4.6 pp | -5.0 pp | DROP |
| `filter_volcontract_0.8` | -0.15 | -0.11 | -6.2 pp | -0.5 pp | DROP |
| `filter_volcontract_1.0` | -0.05 | -0.04 | -4.0 pp | +0.1 pp | DROP |
| `filter_trend_gate_200` | +0.04 | +0.02 | -4.1 pp | -0.5 pp | **KEEP** |

**Kept: `filter_trend_gate_200`.**
**Dropped: `filter_debounce_m2`, `filter_volcontract_0.8`, `filter_volcontract_1.0`.**

**The three dropped filters all fail the same way, and it is instructive.**
(Figures below are BTC / ETH, in that order.) Each of them does what it was meant to do
mechanically: the debounce cuts closed trades by -10 / -8
and the 0.8 volatility-contraction threshold by -18 / -12,
and both reduce max drawdown (-4.6% / -5.0% and
-6.2% / -0.5% respectively). What neither does is improve
risk-adjusted return: Sharpe falls by -0.24 / -0.18 and
-0.15 / -0.11.

The reason is visible in the free-tier tables above, which strip cost effects out
entirely: the filters lose almost exactly as much at 0 bp as at 40 bp. **They are not
saving costs; they are removing trades that were, on average, good.** A breakout
strategy's return distribution is dominated by a handful of long trends, and every
filter here is a device for entering later or less often. The trends that pay are the
ones that run away from you immediately — precisely the ones a two-close debounce or a
"wait until the market has been quiet" precondition discards. The volatility-contraction
filter at the looser 1.0 threshold does correspondingly less damage
(-0.05 / -0.04): it filters less, so it destroys less.

**The trend gate is the exception, and a marginal one.** Requiring price above its
200-day SMA improves Sharpe by +0.04 / +0.02 and reduces max drawdown by
-4.1% / -0.5%, on both symbols, at both the free and the taker
tier. That is a consistent sign rather than a large effect, and it is the filter with the
clearest mechanism: a 40-day-high breakout that fires below the 200-day average is by
construction a bounce inside a downtrend, and those are the breakouts that fail. It
survives the stated rule; it would not survive a demand for a *large* effect. Carry it as
"keep, weakly evidenced", not as a discovery.


---

# Does choosing parameters in the training window beat not choosing?

The `selected_in_train` variant re-picks (N_entry, N_exit) at every one of the
walk-forward windows, by backtesting the full 12-cell
grid on that window's **training slice only** and taking the best training-window daily
Sharpe (ties broken toward the lower N_entry, then the lower N_exit). The chosen
configuration is then applied to that window's test bars through a parameter schedule,
with the position carried across the switch. That is 4,896
training backtests in total, and it is the only part of this study that fits anything.

The structural guarantee is tested, not asserted: the fitter is handed a training slice
and the integration suite records every bar it receives and fails if any of them is at
or after that window's first test bar.

| Symbol | Fixed baseline (40/10) | In-train selected | Δ Sharpe | Δ return |
|---|---|---|---|---|
| BTC-USD | Sharpe 1.20, +5657.0% | Sharpe 1.11, +4482.6% | -0.09 | -1174.5% |
| ETH-USD | Sharpe 0.78, +552.2% | Sharpe 0.82, +553.4% | +0.04 | +1.2% |

**Adaptive parameter selection did not pay.** On BTC it lost to simply fixing 40/10 up
front; on ETH it gained slightly. Both deltas are inside the spread of the plateau
surface itself, which is the honest way to read them: since neighbouring cells of the
grid perform similarly, picking between them on 252 bars of training data is picking on
noise, and the transaction costs of switching are real while the benefit is not. **A
fixed, a-priori parameter choice is the better engineering decision here** — and that
conclusion is only available because the plateau surface was computed first.


---

# Multiplicity: everything that was evaluated

Counting honestly matters more than the count itself, so here is every knob that was
turned, whether or not it appears in a table above.

| What | Count |
|---|---|
| Strategy variants per symbol | 23 |
| — of which parameter-grid cells (N_entry × N_exit) | 12 |
| — of which filter increments | 4 |
| — of which sizing sensitivities | 2 |
| — of which in-training-window selection | 1 |
| Cost tiers | 4 |
| Symbols | 2 |
| **Out-of-sample trials logged** | **184** (92 per symbol) |
| Per-window trial rows logged | 9,384 |
| In-training-window parameter evaluations (fitting, not trials) | 4,896 |

**What the DSR trial pool is, and is not.** Bailey & López de Prado's N is the number of
*configurations* tried. This study has many, so the pool is every variant's out-of-sample
daily Sharpe at one (symbol, tier) — 23 per cell, selected on
identity fields in the logged config, never on the presence of a metric (D98). Per-window
rows carry `row_kind="window"` and are excluded by that same predicate. This is a
different pool from the pairs studies' one-row-per-window, deliberately: those studies
varied no parameters, so their windows *were* their trials.

**The pool is still too small to be a licence.** It counts neither the
4,896 in-training evaluations (fits, not out-of-sample trials —
but each one is a parameter setting a human looked at), nor the cross-symbol multiplicity,
nor the largest term of all: the decision to test a breakout strategy on crypto, taken
after a decade of visible crypto trend. **A DSR below 0.95 here means "no demonstrated
edge"; a DSR above 0.95 does not mean the reverse.**


---

# Verdict

- BTC-USD @ `taker_40bp`: baseline +5657.0% vs buy-and-hold +42386.7% (loses to it), Sharpe 1.20 vs 1.16, max drawdown 43.0% vs 83.4%
- BTC-USD @ `maker_0bp`: baseline +7367.2% vs buy-and-hold +42556.7% (loses to it), Sharpe 1.27 vs 1.16, max drawdown 40.6% vs 83.4%
- ETH-USD @ `taker_40bp`: baseline +552.2% vs buy-and-hold +500.9% (beats it), Sharpe 0.78 vs 0.66, max drawdown 35.2% vs 82.4%
- ETH-USD @ `maker_0bp`: baseline +675.2% vs buy-and-hold +503.3% (beats it), Sharpe 0.84 vs 0.67, max drawdown 34.2% vs 82.4%


**BTC-USD.** Fees move the baseline from +7367.2% (0 bp) to
+6247.9% (25 bp maker) to +5657.0% (0.40% taker): the taker
tier gives up 23% of the
zero-fee terminal wealth, and costs consume 11.2% of gross
P&L. Annualised Sharpe moves 1.27 → 1.23 →
1.20. Buy-and-hold over the same span returned +42386.7%
at Sharpe 1.16 with a 83.4% drawdown, against the
strategy's 43.0% at 37% time in market.

**ETH-USD.** Fees move the baseline from +675.2% (0 bp) to
+595.9% (25 bp maker) to +552.2% (0.40% taker): the taker
tier gives up 16% of the
zero-fee terminal wealth, and costs consume 10.4% of gross
P&L. Annualised Sharpe moves 0.84 → 0.80 →
0.78. Buy-and-hold over the same span returned +500.9%
at Sharpe 0.66 with a 82.4% drawdown, against the
strategy's 35.2% at 33% time in market.

## Does it survive costs at the maker tier?

**Yes — and that is the least interesting true thing in this document.**

The strategy survives fees comfortably at every tier tested. The whole 0 bp → 40 bp
range costs roughly 10%–11%
of gross P&L and a fraction of a Sharpe point. That is a direct consequence of what the
per-trade diagnostics show: the median trade is held for
26–29
days, the whipsaw rate at the baseline parameters is **zero** on both symbols, and
annualised turnover is around
6–7×.
A strategy that trades a few dozen times a decade cannot be killed by 40 bp. The
hysteresis between a 40-bar entry and a 10-bar exit is doing exactly the job it was
designed to do, and the golden-master and property tests confirm the two conditions can
never fire on the same bar.

**So the fee question is answered and it is not the binding constraint. Three things
that are not fees are.**

1. **The absolute returns belong to the instrument, and the risk-adjusted claim is not
   measurable.** Two separate points, both fatal to the obvious reading.

   *The era.* BTC went 426x over the out-of-sample span. Any long-biased
   rule on that decade prints four-figure percentages, so
   +5657% is a fact
   about BTC before it is a fact about breakouts. The year-by-year table is the honest
   version: the pattern is BTC lost in 9 of 9 up years and won in 2 of 2 down years; ETH lost in 4 of 4 up years and won in 3 of 4 down years. That is not return prediction, it is insurance — bought with
   bull-market underperformance, paid out in bear markets. Across both symbols the sample
   contains 6 down years in total, and the insurance paid out in
   5 of them — so the whole case rests on 5 observations.
   Change the start date and the strategy's CAGR ranges from
   +11% to +49% on BTC alone.

   *The statistics.* The Sharpe advantage over buy-and-hold — +0.04 on BTC, +0.11 on ETH —
   is inside the noise. A paired block bootstrap puts P(strategy Sharpe > benchmark
   Sharpe) at 55% and 59% respectively, with 90% intervals comfortably
   spanning zero, and at two of the five start dates tested the strategy's Sharpe is
   *below* the benchmark's. **The risk-adjusted claim, stated as a Sharpe improvement,
   is not supported.**

   What survives both objections is narrower and holds everywhere: **at matched average
   exposure the strategy earns several times the terminal wealth of holding the same
   fraction constantly, and its max drawdown is lower at every start date and on both
   symbols, typically by half.** That is a real and useful property. It is a
   drawdown-shape result, not an alpha result, and the difference matters.

2. **The cost model is the optimistic part, and fees are its smallest term.** What is
   modelled is an exchange fee. What is not modelled is the slippage of sending a market
   order into an instrument that has just printed a 40-day high — which is the single
   most adversely-selected moment to be a buyer, and on daily crypto bars it is entirely
   invisible. The maker tiers are worse than optimistic: getting a maker fee means
   resting a limit order and *not being filled* in the fast breakouts, which are the
   trades that pay. A realistic execution study — intraday bars, order-book depth,
   fill-probability modelling for resting orders — would move these numbers by more than
   the entire 0–40 bp fee range does. **That, not the fee tier, is the honest next
   experiment.**

3. **The selection bias above this study is larger than anything inside it.** The DSR
   numbers are near 1.0 at every tier, and the mechanical reason is that the plateau is
   flat: 19 variants whose Sharpes cluster tightly give a tiny V[{SRn}], so the noise
   floor SR0 barely rises and almost nothing is deflated away. That is DSR working
   correctly on the multiplicity it was given, and it is also why those numbers should
   not be read as vindication. The trial pool counts 19 configurations. It does not count
   the 4,896 training-window fits, the two-symbol choice, or the
   decision — made in 2026, with a decade of crypto trend visible — to test a trend
   follower on the two crypto assets that survived. **Treat DSR ≈ 1.0 here as "the
   multiplicity we measured was not the binding problem", not as "this is real."**

## What would change the answer

Running this on instruments chosen without hindsight (a broad basket including the
crypto assets that died), with an execution model that prices crossing the spread into a
breakout, and shorts as well as longs. Each of those is a bigger lever than every fee
tier in this document combined.


---

# Standing caveats

1. **Fees only.** No spread, no slippage, no market impact, no funding. A 0.40% taker fee
   on a market order into a breakout is the *fee*, not the *cost* — the slippage of
   crossing into a market that has just made a 40-day high is real and unmodelled. Every
   return here is therefore optimistic, and the maker tiers doubly so.
2. **The maker tiers are a lower bound, not an execution plan.** A breakout entry is a
   market order by nature: you want the fill because the level broke. Getting a *maker*
   fee means resting a limit order and accepting that in the fastest breakouts — the ones
   that pay — you do not get filled at all. The maker rows answer "how much of the result
   is fees?", not "here is a cheaper way to run this".
3. **Survivorship and selection at the instrument level.** BTC and ETH are the two crypto
   assets that survived to be worth studying. Testing a trend follower on them, over a
   decade in which they went up enormously, is a selected sample by construction — the
   single largest un-deflatable bias in this document.
4. **Single data source (D26).** yfinance only; no second-source cross-check. Crypto
   daily bars are an aggregate across venues, so "the open" is a convention, not a price
   anyone was quoted.
5. **Spot, not perpetuals.** BTC and ETH are modelled as `Equity(quantity_precision=8)`
   (D108): long-only, unlevered, no funding. A perpetual-futures implementation would need
   the funding-rate carry brick that is Step 10's deferred work (D14) — and funding would
   be a cost of exactly the kind this study is measuring.
6. **No shorting, by design.** The brief scoped it out. A symmetric long/short trend
   follower is a different strategy with a different answer.
7. **The 40% vol target is a choice, not a result.** Against BTC's ~68% and ETH's ~87%
   realized annual vol it means the strategy is typically around half invested when long.
   The `sizing_fixed_1.0` row is the control that shows what that choice costs and buys.
