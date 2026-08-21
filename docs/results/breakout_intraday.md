# The cost–frequency frontier: at what bar size do fees eat the breakout's edge?

**Produced:** 2026-08-18 ·
**1h snapshot:** `88b3e08d666006f7b47f08ba42eaa3bcae5ec484d9a8d3811d1c7240e177a281` ·
**Registry:** `data/breakout_intraday_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_intraday.py` (offline, deterministic) ·
**Fetch (network, one-time):** `uv run python scripts/fetch_crypto_intraday.py`

> **Thesis label (D38/D82/D117), inherited unchanged.** This is a **directional,
> beta-loaded** strategy — long or flat on a single high-beta instrument, never short. It
> is not part of this project's market-neutral thesis and is not evidence about it. Its
> honest benchmark is buy-and-hold.

**What this is.** `BREAKOUT_RESULTS.md` concluded that exchange fees are "not the binding
constraint" for the long-flat breakout. That conclusion rests entirely on **daily** bars,
where annualised turnover is 6–7× and the median trade is held 26–29 days. This study runs
the identical rule from **1h to 1d** on BTC-USD, ETH-USD and asks one question: **as frequency
rises, where does the cost curve cross the trend edge?**

It is a frontier, not a search for a better configuration. No parameter is tuned, no
filter is added, nothing is selected on out-of-sample performance. The only thing that
moves is the bar.


## The rule for calling the crossover, fixed before the numbers were looked at

The crossover frequency is the COARSEST (slowest) bar at which the cost curve has risen above the trend edge, read three ways because the three fail differently. (1) IN-SAMPLE SHARPE: net annualised Sharpe at `taker_40bp` <= 0. (2) IN-SAMPLE COST SHARE: costs >= 100% of gross P&L. (3) SPLICED: cost drag in Sharpe units (annual fee drag / annual volatility, measured HERE) >= the gross annualised Sharpe measured over 2015-2025 daily data in BREAKOUT_RESULTS.md at `maker_0bp`. Readings (1) and (2) are contaminated whenever the window's own gross edge is near zero or negative; reading (3) is not, because neither of its terms has this window's P&L in it. All three are read off the ladder ordered slow -> fast, and 'no rung on the ladder' is a legitimate answer. Fixed before the numbers were looked at.

Three readings rather than one, because each fails in a way the others do not. The
net-Sharpe reading says nothing about *why* the edge died. The cost-share reading is
undefined when gross P&L is near zero and meaningless when it is negative. Both are
hostage to whether the particular two years yfinance serves happened to contain a trend.
The spliced reading is not — but it borrows its edge term from a different sample, and
that borrowing is stated every time it is used. Reported together, they distinguish
"costs killed the edge" from "there was no edge in this window to kill", which a single
number cannot.


---

## The data, and the contract that makes frequency the only variable

**Fixture.** `data/fixtures/crypto_intraday_1h_raw.csv.gz` — BTC-USD and ETH-USD **1h**
bars, UTC, fetched once through `scripts/fetch_crypto_intraday.py`. yfinance serves 730
days of 1h, 60 days of 15m/30m, no 4h for `period='max'`, and **has no 6h interval at
all**, so 1h is the only base a multi-frequency study can stand on. 2h, 4h, 6h, 12h and
1d are **resampled** from it (D161): open = first open, high = max high, low = min low,
close = last close, volume = sum, with buckets keyed on (UTC date, minute-of-day ÷ bar
minutes) so they align to 00:00 UTC.

**Incomplete buckets are never silently short, and the drop policy is day-level.** The
provider skips the odd hour. A 6h bar built from 4 hourly bars would be a 4-hour bar
wearing a 6-hour timestamp. Dropping just that bucket is not enough either — it would
give each frequency a *different* calendar, and frequency is the one thing this study
varies. So **a UTC day the provider does not serve in full is dropped at every
frequency**:

| Symbol | Complete UTC days | Span | Walk-forward windows | Days dropped (hours served) |
|---|---|---|---|---|
| BTC-USD | 724 | 2024-08-19 → 2026-08-17 | 7 | 2025-01-02 (23/24), 2025-10-28 (13/24), 2025-11-28 (23/24), 2025-11-29 (5/24), 2026-05-08 (23/24) |
| ETH-USD | 723 | 2024-08-19 → 2026-08-17 | 7 | 2025-01-02 (23/24), 2025-09-16 (21/24), 2025-10-28 (13/24), 2025-11-28 (23/24), 2025-11-29 (5/24), 2026-05-08 (23/24) |

Every frequency then holds exactly `complete days × 1440/minutes` bars, and because the
walk-forward sizes are scaled by the same `bars_per_day`, the window count
`⌊(days − 252 − 63)/63⌋ + 1` **does not depend on the frequency at all**. The equal
window count is a theorem here, not a coincidence — and `run_frontier` asserts it against
every single run anyway.

### Does the 1h → 1d resample reconcile with the committed daily fixture?

The contract says a resample to 1d must reproduce the daily fixture's bars to
floating-point tolerance **where the provider agrees**. It does not, and the disagreement
is reported rather than papered over.

| Symbol | Overlap days | Field | Median \|rel diff\| | Max \|rel diff\| | Resampled above provider | Exactly equal |
|---|---|---|---|---|---|---|
| BTC-USD | 495 | open | 1.50e-04 | 2.60e-03 | 48.3% | 1/495 |
| BTC-USD | 495 | high | 2.04e-04 | 7.46e-03 | 0.2% | 42/495 |
| BTC-USD | 495 | low | 1.98e-04 | 2.21e-02 | 90.1% | 47/495 |
| BTC-USD | 495 | close | 4.14e-05 | 5.03e-03 | 47.7% | 23/495 |
| ETH-USD | 494 | open | 2.02e-04 | 3.74e-03 | 49.2% | 1/494 |
| ETH-USD | 494 | high | 2.73e-04 | 4.76e-03 | 0.0% | 54/494 |
| ETH-USD | 494 | low | 3.47e-04 | 1.74e-02 | 90.5% | 47/494 |
| ETH-USD | 494 | close | 4.33e-05 | 5.78e-03 | 47.2% | 18/494 |

Opens and closes differ by a couple of basis points in the median with **no sign bias**
(≈50% either way) — the signature of two independent aggregations of the same market.
Highs and lows are a different story and the bias is almost total:

| Symbol | Mean daily range, resampled from 1h | Mean daily range, provider's own 1d | Days the resampled range is narrower |
|---|---|---|---|
| BTC-USD | 3.366% | 3.441% | 99.0% |
| ETH-USD | 5.368% | 5.498% | 98.4% |

**yfinance's daily crypto bar is not the aggregate of its own hourly bars.** The
resampled high sits below the provider's daily high on essentially every day, and the
resampled low above its daily low on ~90% — i.e. the hourly feed does not contain the
day's true extremes. That is a provider fact, not a resampling bug: the aggregation of
correctly-resampled bars can only ever be an inner bound on the true range, and this one
misses roughly 2% of the daily range relative.

**Direction of the bias on THIS study, stated because it points the wrong way.** The
breakout rule triggers on `max(high)` and exits on `min(low)`. Understated highs mean a
slightly LOWER entry level; overstated lows mean a slightly HIGHER exit level. Both
produce *more* trading than the provider's own daily bars would. So the 1d rung of this
study is not byte-identical to `BREAKOUT_RESULTS.md`'s daily fixture, and what difference
there is tilts toward this study's own conclusion. Read the 1d rung as a same-fixture
anchor for the ladder above it, never as a reproduction of the daily study.

---

## What the sanity gate said about intraday bars

| Fixture | Raw bars | Price cleaning changes | Hard violations | Warnings | Bars the volume rule would have dropped |
|---|---|---|---|---|---|
| `1h` | 34,923 | 0 | **0** | 19,821 (volume_spike: 2,301, zero_volume: 17,520) | **17,520** (50%) |
| `30m` | 5,664 | 0 | **0** | 296 (volume_spike: 56, zero_volume: 240) | **240** (4%) |
| `15m` | 11,328 | 0 | **0** | 2,056 (volume_spike: 342, zero_volume: 1,714) | **1,714** (15%) |

**Nothing quarantined. Zero hard violations at every interval.** That is the literal
answer to "what did the gate say", and it is also the problem: the gate is *silent* on
intraday bars for a reason that has nothing to do with the data being clean.

**1. The bar-to-bar move check never fires.** `MOVE_WARNING_THRESHOLD` is 25% and
`MOVE_HARD_THRESHOLD` is 60%, calibrated in D74 against genuine DAILY equity moves (XOP's
2020-03-09 −37% day). An hourly BTC bar has a standard deviation of about 0.48%, so a 25%
hourly move is a fifty-sigma event. Over 730 days of hourly bars the check has literally
nothing to say:

| Symbol | Largest \|bar move\| | Bars over the 25% warning | Bars over the 60% hard | Bars over a √-scaled warning (5.10%) | Bars over a √-scaled hard (12.25%) |
|---|---|---|---|---|---|
| BTC-USD | 5.08% | 0 | 0 | 0 | 0 |
| ETH-USD | 11.90% | 0 | 0 | 10 | 0 |

**What an intraday-appropriate threshold would be.** A move threshold is a statement
about a distribution, and that distribution scales with the square root of the bar's
duration. Carrying D74's daily calibration across by that scaling gives
25%/√24 = 5.10% warning and 60%/√24 = 12.25% hard at 1h — thresholds that
actually flag something (a handful of ETH bars) while still passing the whole series. The
shared validator is **not edited** to do this: a threshold that varies with bar duration
is a change to a framework component that five other studies depend on, and it needs its
own decision, not a study's side effect. It is recorded here as the finding it is.

**2. The cleaner's volume rule is the one that would have corrupted this study, and it
would have done it silently.** `clean-v1`'s `non_positive_volume` rule drops any bar with
volume ≤ 0. yfinance reports Volume = 0 on roughly half of all hourly BTC/ETH bars —
17,520 of 34,923 — spread evenly across every hour of the day and every month
of the sample, on instruments that have never had a zero-volume hour. The prices in those
bars are present and OHLC-consistent. Running the pipeline as the daily study calls it
would have deleted half the price series to a provider reporting artifact, and the
resulting fixture would have had almost no complete UTC days left to resample from.

So `clean` is called on **prices only** here, which is a supported call of the existing
signature and not an edit to the cleaner. The volume column is still written to the
fixture and the snapshot in full, and the validator still reads it — which is why the
zero-volume artifact shows up above as thousands of non-blocking warnings instead of
disappearing along with the bars.

---

## Method

**Signal.** Unchanged from `BREAKOUT_RESULTS.md` (D109): enter long when
`close(t) > max(high)` over t−N_entry … t−1, exit when `close(t) < min(low)` over
t−N_exit … t−1. Both extrema exclude the current bar. Long or flat, never short.
`fill_timing="next_open"` (D103). Baseline inverse-vol sizing at a 40% annual vol target
(D110), fixed at entry, capped at 1.0. No filters.

**Two designs, which answer different questions (D162).**

| | Design A — constant calendar horizon | Design B — constant bar count |
|---|---|---|
| Entry / exit window | 40 days / 10 days at every frequency | 40 bars / 10 bars at every frequency |
| At 1h | 960 / 240 bars | 40 / 10 bars (= 40 h / 10 h) |
| At 1d | 40 / 10 bars | 40 / 10 bars |
| Vol-estimate window | 20 days | 20 bars |
| The question it answers | does finer SAMPLING of the same signal help, or just add cost? | does the trend effect exist at shorter HORIZONS at all? |

They coincide exactly at 1d, which is the anchor tying this ladder to the daily study.
They must not be conflated anywhere else.

**Walk-forward, scaled to equal calendar duration.** train = 252 days,
test = 63 days, step = 63 days at every frequency — 6,048/1,512/1,512 bars at
1h, 252/63/63 at 1d. Every frequency gets **7 windows over the same span**. One
continuous out-of-sample run per cell with the position carried across window boundaries
(D113), warm-up prefix exactly the strategy's own requirement, with the harness raising if
any fill lands inside it.

**`periods_per_year` in both places (D17).** 1h: 8,760, 2h: 4,380, 4h: 2,190, 6h: 1,460, 12h: 730, 1d: 365.
It is a required argument throughout `analytics.metrics` AND a field inside the
`inverse_vol_weight` config, and `assert_periods_per_year_agree` refuses to run any cell
where the two disagree — otherwise a 1h run would annualise its Sharpe on 8,760 periods
while sizing every position as though a bar were a day.

**Costs.** The same four tiers, unchanged (`DEFAULT_TIERS`, D114): `maker_0bp` 0.00%,
`maker_10bp` 0.10%, `maker_25bp` 0.25%, `taker_40bp` 0.40%. One `percent_spread` brick
each — an exchange fee and nothing else. **Every number below is therefore optimistic,
and it gets more optimistic as the bars get finer**: an hourly breakout entry crosses a
spread and pays impact exactly like a daily one, and this model prices neither.

**Benchmarks.** 100% buy-and-hold (fixed quantity, D115) and the constant-fraction
benchmark at the strategy's own average exposure (D119), at every frequency, over the
same span. **Read the constant-fraction rows with care at fine frequencies**: it
rebalances every bar, so at 1h it pays fees 8,760 times a year. Its collapse at high
frequency is the benchmark's cost problem, not the strategy's edge.

---

## Statistical power: read this before any Sharpe below

730 days of 1h data is the *longest* intraday history yfinance will serve, and it is
still only **723 days total, 441 of them out of sample — about 1.2 years**. The standard
error on an annualised Sharpe over that span is roughly **±0.91**, against the ±0.4
that ten years of daily data bought the original study. Almost every Sharpe *difference*
in this document is inside that band.

**That asymmetry is the point of framing this as a frontier rather than a horse race.**
The two halves of the frontier are not measured with the same precision:

- **The cost half is measured precisely.** Turnover, trade counts, holding periods and
  costs-as-a-share-of-gross are near-deterministic functions of the rule and the bar
  size. Re-running on a different two-year window would move them a little; it would not
  move them by an order of magnitude.
- **The edge half is barely measured at all.** The gross Sharpe at each frequency is one
  draw from a distribution about a Sharpe point wide.

So the honest reading of everything below is: **the cost curve is real, the edge curve is
noise, and a crossover found by walking a real curve into a noisy one is an upper bound on
where the crossover sits** — the true one can only be at a *coarser* frequency than the
one measured, never finer.


---

# BTC-USD — Design A: constant calendar horizon (40-day entry / 10-day exit)

## The frontier at the reference tier (`taker_40bp`, 0.40% taker)

| Frequency | Total return | CAGR | Sharpe (ann.) | Max DD | Exposure | Trades | Ann. turnover | Costs / gross P&L | Gross−net Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| `1d` | -23.18% | -19.61% | -1.24 | 36.8% | 28.6% | 6 | 10.5x | 24.1% | 0.21 |
| `12h` | -19.26% | -16.23% | -1.06 | 34.1% | 28.1% | 6 | 10.3x | 31.2% | 0.21 |
| `6h` | -15.02% | -12.60% | -0.99 | 31.4% | 22.1% | 7 | 11.4x | 54.7% | 0.27 |
| `4h` | -16.44% | -13.82% | -1.05 | 32.4% | 22.1% | 7 | 11.4x | 47.4% | 0.27 |
| `2h` | -21.49% | -18.15% | -1.27 | 36.8% | 23.5% | 7 | 11.5x | 31.3% | 0.25 |
| `1h` | -22.29% | -18.84% | -1.35 | 37.4% | 23.5% | 7 | 11.5x | 29.7% | 0.25 |

## The same ladder at every cost tier — annualised Sharpe

| Frequency | `maker_0bp` | `maker_10bp` | `maker_25bp` | `taker_40bp` | Cost wedge (0bp→40bp) |
|---|---|---|---|---|---|
| `1d` | -1.03 | -1.08 | -1.16 | -1.24 | 0.21 |
| `12h` | -0.85 | -0.90 | -0.98 | -1.06 | 0.21 |
| `6h` | -0.72 | -0.79 | -0.89 | -0.99 | 0.27 |
| `4h` | -0.78 | -0.85 | -0.95 | -1.05 | 0.27 |
| `2h` | -1.02 | -1.08 | -1.17 | -1.27 | 0.25 |
| `1h` | -1.09 | -1.16 | -1.25 | -1.35 | 0.25 |

## What the strategy turns into, in calendar units

| Frequency | Entry / exit window | Trades / yr | Median hold | p90 hold | Whipsaw rate (≤3 days) | Exposure |
|---|---|---|---|---|---|---|
| `1d` | 40/10 bars = 40d / 10d | 4.9 | 26.00 d | 34.00 d | 0.0% | 28.6% |
| `12h` | 80/20 bars = 40d / 10d | 4.9 | 25.75 d | 33.50 d | 0.0% | 28.1% |
| `6h` | 160/40 bars = 40d / 10d | 5.7 | 9.00 d | 29.25 d | 0.0% | 22.1% |
| `4h` | 240/60 bars = 40d / 10d | 5.7 | 9.00 d | 29.67 d | 0.0% | 22.1% |
| `2h` | 480/120 bars = 40d / 10d | 5.7 | 15.33 d | 29.25 d | 0.0% | 23.5% |
| `1h` | 960/240 bars = 40d / 10d | 5.7 | 15.33 d | 29.25 d | 0.0% | 23.5% |

## Against the benchmarks (`taker_40bp`)

| Frequency | Strategy return | Strategy Sharpe | Buy & hold return | B&H Sharpe | Constant-fraction return | CF Sharpe | CF fraction |
|---|---|---|---|---|---|---|---|
| `1d` | -23.18% | -1.24 | -32.50% | -0.66 | -9.18% | -0.94 | 29% |
| `12h` | -19.26% | -1.06 | -33.13% | -0.72 | -9.56% | -1.02 | 28% |
| `6h` | -15.02% | -0.99 | -32.52% | -0.66 | -7.46% | -1.07 | 22% |
| `4h` | -16.44% | -1.05 | -32.80% | -0.70 | -7.82% | -1.13 | 22% |
| `2h` | -21.49% | -1.27 | -32.96% | -0.67 | -8.68% | -1.11 | 24% |
| `1h` | -22.29% | -1.35 | -33.08% | -0.68 | -9.31% | -1.17 | 23% |


---

# BTC-USD — Design B: constant bar count (40-bar entry / 10-bar exit)

## The frontier at the reference tier (`taker_40bp`, 0.40% taker)

| Frequency | Total return | CAGR | Sharpe (ann.) | Max DD | Exposure | Trades | Ann. turnover | Costs / gross P&L | Gross−net Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| `1d` | -23.18% | -19.61% | -1.24 | 36.8% | 28.6% | 6 | 10.5x | 24.1% | 0.21 |
| `12h` | -15.00% | -12.59% | -0.92 | 28.9% | 26.3% | 10 +1 open | 16.6x | 113.8% | 0.38 |
| `6h` | -24.55% | -20.80% | -1.43 | 31.1% | 29.0% | 21 +1 open | 34.0x | 165.7% | 0.76 |
| `4h` | -13.42% | -11.24% | -0.88 | 18.9% | 23.5% | 25 | 38.2x | 401.3% | 0.94 |
| `2h` | -40.76% | -35.17% | -2.37 | 44.7% | 26.6% | 57 | 90.2x | 727.3% | 1.86 |
| `1h` | -66.15% | -59.20% | -5.00 | 67.8% | 25.7% | 117 | 188.7x | 921.5% | 3.99 |

## The same ladder at every cost tier — annualised Sharpe

| Frequency | `maker_0bp` | `maker_10bp` | `maker_25bp` | `taker_40bp` | Cost wedge (0bp→40bp) |
|---|---|---|---|---|---|
| `1d` | -1.03 | -1.08 | -1.16 | -1.24 | 0.21 |
| `12h` | -0.54 | -0.63 | -0.78 | -0.92 | 0.38 |
| `6h` | -0.67 | -0.86 | -1.15 | -1.43 | 0.76 |
| `4h` | 0.05 | -0.18 | -0.54 | -0.88 | 0.94 |
| `2h` | -0.51 | -0.98 | -1.69 | -2.37 | 1.86 |
| `1h` | -1.01 | -2.05 | -3.57 | -5.00 | 3.99 |

## What the strategy turns into, in calendar units

| Frequency | Entry / exit window | Trades / yr | Median hold | p90 hold | Whipsaw rate (≤3 days) | Exposure |
|---|---|---|---|---|---|---|
| `1d` | 40/10 bars = 40d / 10d | 4.9 | 26.00 d | 34.00 d | 0.0% | 28.6% |
| `12h` | 40/10 bars = 20d / 5d | 8.2 | 8.75 d | 22.00 d | 10.0% | 26.3% |
| `6h` | 40/10 bars = 10d / 2.5d | 17.2 | 5.00 d | 10.75 d | 33.3% | 29.0% |
| `4h` | 40/10 bars = 6.667d / 1.667d | 20.5 | 3.50 d | 6.83 d | 40.0% | 23.5% |
| `2h` | 40/10 bars = 3.333d / 0.8333d | 46.8 | 1.58 d | 5.08 d | 78.9% | 26.6% |
| `1h` | 40/10 bars = 1.667d / 0.4167d | 96.0 | 0.83 d | 1.83 d | 97.4% | 25.7% |

## Against the benchmarks (`taker_40bp`)

| Frequency | Strategy return | Strategy Sharpe | Buy & hold return | B&H Sharpe | Constant-fraction return | CF Sharpe | CF fraction |
|---|---|---|---|---|---|---|---|
| `1d` | -23.18% | -1.24 | -32.50% | -0.66 | -9.18% | -0.94 | 29% |
| `12h` | -15.00% | -0.92 | -33.13% | -0.72 | -8.95% | -1.04 | 26% |
| `6h` | -24.55% | -1.43 | -32.52% | -0.66 | -9.78% | -0.97 | 29% |
| `4h` | -13.42% | -0.88 | -32.80% | -0.70 | -8.30% | -1.11 | 24% |
| `2h` | -40.76% | -2.37 | -32.96% | -0.67 | -9.79% | -1.05 | 27% |
| `1h` | -66.15% | -5.00 | -33.08% | -0.68 | -10.15% | -1.13 | 26% |


---

# ETH-USD — Design A: constant calendar horizon (40-day entry / 10-day exit)

## The frontier at the reference tier (`taker_40bp`, 0.40% taker)

| Frequency | Total return | CAGR | Sharpe (ann.) | Max DD | Exposure | Trades | Ann. turnover | Costs / gross P&L | Gross−net Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| `1d` | -7.86% | -6.55% | -0.34 | 23.9% | 29.5% | 6 +1 open | 7.5x | 94.4% | 0.13 |
| `12h` | -7.24% | -6.03% | -0.31 | 31.5% | 28.9% | 7 +1 open | 8.9x | 181.0% | 0.15 |
| `6h` | -4.11% | -3.42% | -0.21 | 29.8% | 29.1% | 7 +1 open | 9.3x | 605.4% | 0.16 |
| `4h` | -3.80% | -3.16% | -0.20 | 28.5% | 28.0% | 7 +1 open | 9.5x | 404.3% | 0.17 |
| `2h` | -2.80% | -2.32% | -0.18 | 28.6% | 23.8% | 7 +1 open | 9.8x | 218.7% | 0.18 |
| `1h` | -2.90% | -2.40% | -0.18 | 27.7% | 23.7% | 7 +1 open | 10.3x | 213.6% | 0.19 |

## The same ladder at every cost tier — annualised Sharpe

| Frequency | `maker_0bp` | `maker_10bp` | `maker_25bp` | `taker_40bp` | Cost wedge (0bp→40bp) |
|---|---|---|---|---|---|
| `1d` | -0.21 | -0.24 | -0.29 | -0.34 | 0.13 |
| `12h` | -0.16 | -0.20 | -0.26 | -0.31 | 0.15 |
| `6h` | -0.05 | -0.09 | -0.15 | -0.21 | 0.16 |
| `4h` | -0.04 | -0.08 | -0.14 | -0.20 | 0.17 |
| `2h` | -0.00 | -0.05 | -0.12 | -0.18 | 0.18 |
| `1h` | 0.00 | -0.04 | -0.11 | -0.18 | 0.19 |

## What the strategy turns into, in calendar units

| Frequency | Entry / exit window | Trades / yr | Median hold | p90 hold | Whipsaw rate (≤3 days) | Exposure |
|---|---|---|---|---|---|---|
| `1d` | 40/10 bars = 40d / 10d | 4.9 | 17.00 d | 45.00 d | 0.0% | 29.5% |
| `12h` | 80/20 bars = 40d / 10d | 5.7 | 12.00 d | 30.50 d | 0.0% | 28.9% |
| `6h` | 160/40 bars = 40d / 10d | 5.7 | 12.25 d | 30.50 d | 0.0% | 29.1% |
| `4h` | 240/60 bars = 40d / 10d | 5.7 | 12.17 d | 30.33 d | 0.0% | 28.0% |
| `2h` | 480/120 bars = 40d / 10d | 5.7 | 11.42 d | 28.42 d | 0.0% | 23.8% |
| `1h` | 960/240 bars = 40d / 10d | 5.7 | 11.12 d | 28.42 d | 0.0% | 23.7% |

## Against the benchmarks (`taker_40bp`)

| Frequency | Strategy return | Strategy Sharpe | Buy & hold return | B&H Sharpe | Constant-fraction return | CF Sharpe | CF fraction |
|---|---|---|---|---|---|---|---|
| `1d` | -7.86% | -0.34 | +3.08% | 0.32 | +6.03% | 0.15 | 29% |
| `12h` | -7.24% | -0.31 | +1.29% | 0.28 | +4.52% | 0.08 | 29% |
| `6h` | -4.11% | -0.21 | +3.26% | 0.31 | +4.64% | 0.09 | 29% |
| `4h` | -3.80% | -0.20 | +2.87% | 0.29 | +3.88% | 0.05 | 28% |
| `2h` | -2.80% | -0.18 | +3.14% | 0.30 | +2.86% | -0.03 | 24% |
| `1h` | -2.90% | -0.18 | +2.84% | 0.30 | +1.76% | -0.09 | 24% |


---

# ETH-USD — Design B: constant bar count (40-bar entry / 10-bar exit)

## The frontier at the reference tier (`taker_40bp`, 0.40% taker)

| Frequency | Total return | CAGR | Sharpe (ann.) | Max DD | Exposure | Trades | Ann. turnover | Costs / gross P&L | Gross−net Sharpe |
|---|---|---|---|---|---|---|---|---|---|
| `1d` | -7.86% | -6.55% | -0.34 | 23.9% | 29.5% | 6 +1 open | 7.5x | 94.4% | 0.13 |
| `12h` | +7.47% | +6.15% | 0.22 | 33.0% | 31.7% | 10 +1 open | 13.9x | 52.3% | 0.18 |
| `6h` | +16.55% | +13.51% | 0.46 | 41.1% | 26.9% | 19 +1 open | 26.5x | 53.3% | 0.39 |
| `4h` | +32.29% | +26.06% | 0.86 | 24.3% | 24.5% | 24 | 31.9x | 40.3% | 0.48 |
| `2h` | -15.64% | -13.13% | -0.53 | 43.3% | 26.8% | 54 | 73.3x | 158.9% | 1.11 |
| `1h` | -40.12% | -34.59% | -1.61 | 55.0% | 25.5% | 116 | 161.0x | 236.0% | 2.41 |

## The same ladder at every cost tier — annualised Sharpe

| Frequency | `maker_0bp` | `maker_10bp` | `maker_25bp` | `taker_40bp` | Cost wedge (0bp→40bp) |
|---|---|---|---|---|---|
| `1d` | -0.21 | -0.24 | -0.29 | -0.34 | 0.13 |
| `12h` | 0.40 | 0.35 | 0.28 | 0.22 | 0.18 |
| `6h` | 0.84 | 0.75 | 0.60 | 0.46 | 0.39 |
| `4h` | 1.34 | 1.22 | 1.04 | 0.86 | 0.48 |
| `2h` | 0.59 | 0.31 | -0.11 | -0.53 | 1.11 |
| `1h` | 0.80 | 0.19 | -0.72 | -1.61 | 2.41 |

## What the strategy turns into, in calendar units

| Frequency | Entry / exit window | Trades / yr | Median hold | p90 hold | Whipsaw rate (≤3 days) | Exposure |
|---|---|---|---|---|---|---|
| `1d` | 40/10 bars = 40d / 10d | 4.9 | 17.00 d | 45.00 d | 0.0% | 29.5% |
| `12h` | 40/10 bars = 20d / 5d | 8.2 | 10.00 d | 28.50 d | 10.0% | 31.7% |
| `6h` | 40/10 bars = 10d / 2.5d | 15.6 | 4.25 d | 11.75 d | 26.3% | 26.9% |
| `4h` | 40/10 bars = 6.667d / 1.667d | 19.6 | 3.00 d | 8.50 d | 54.2% | 24.5% |
| `2h` | 40/10 bars = 3.333d / 0.8333d | 44.2 | 1.46 d | 4.58 d | 77.8% | 26.8% |
| `1h` | 40/10 bars = 1.667d / 0.4167d | 94.9 | 0.75 d | 1.92 d | 97.4% | 25.5% |

## Against the benchmarks (`taker_40bp`)

| Frequency | Strategy return | Strategy Sharpe | Buy & hold return | B&H Sharpe | Constant-fraction return | CF Sharpe | CF fraction |
|---|---|---|---|---|---|---|---|
| `1d` | -7.86% | -0.34 | +3.08% | 0.32 | +6.03% | 0.15 | 29% |
| `12h` | +7.47% | 0.22 | +1.29% | 0.28 | +4.79% | 0.10 | 32% |
| `6h` | +16.55% | 0.46 | +3.26% | 0.31 | +4.39% | 0.07 | 27% |
| `4h` | +32.29% | 0.86 | +2.87% | 0.29 | +3.52% | 0.01 | 25% |
| `2h` | -15.64% | -0.53 | +3.14% | 0.30 | +3.13% | 0.01 | 27% |
| `1h` | -40.12% | -1.61 | +2.84% | 0.30 | +1.87% | -0.06 | 26% |


---

# The frontier, stated

## The crossover

| Symbol | Design | (3) Spliced: cost drag ≥ 2015–2025 gross Sharpe | (2) Costs ≥ 100% of gross | (1) Net Sharpe ≤ 0 |
|---|---|---|---|---|
| BTC-USD | Design A | **`no rung`** | `no rung` | `1d` |
| BTC-USD | Design B | **`2h`** | `12h` | `1d` |
| ETH-USD | Design A | **`no rung`** | `12h` | `1d` |
| ETH-USD | Design B | **`2h`** | `2h` | `1d` |

**Column (1) says `1d` everywhere, and that is a fact about the WINDOW, not about
frequency.** Over the out-of-sample span, 100% buy-and-hold in BTC-USD returned -32.2% with a 53% peak-to-trough drawdown (peak +32% above the start); Over the out-of-sample span, 100% buy-and-hold in ETH-USD returned +3.5% with a 68% peak-to-trough drawdown (peak +169% above the start). A long-only trend follower loses money in a window like
that at *every* frequency, daily included, and at every cost tier including the free one —
the gross (0 bp) Sharpe column below is negative almost everywhere. So readings (1) and
(2) cannot separate "costs killed the edge" from "there was no edge in this window to
kill". They are reported because hiding them would be worse, and they are not the answer.

**Column (3) is the answer.** It compares a cost curve measured here — where it is
measured well — against a gross edge measured over ten years of daily data in
`BREAKOUT_RESULTS.md`, where *it* is measured well. The splice is stated, not hidden, and
it is the only reading whose two terms are each estimated on a sample that can support
them.

## The cost curve in Sharpe units, against the ten-year gross edge

Cost drag in Sharpe units is `annual fee drag ÷ annual volatility`. Sharpe ≈ (μ − rf)/σ,
so charging `c` per year of fees costs about `c/σ` of Sharpe. Neither term has this
window's P&L in it, which is exactly why this is the reading that survives a
no-edge sample.

**BTC-USD — Design A** (reference gross Sharpe 1.27, measured 2015–2025 daily at `maker_0bp`)

| Frequency | Ann. turnover | Fee drag / yr | Strategy ann. vol | Cost drag (Sharpe units) | vs. 2015–2025 gross Sharpe | Verdict |
|---|---|---|---|---|---|---|
| `1d` | 10.5x | 4.19% | 19.3% | 0.22 | 1.27 | edge survives |
| `12h` | 10.3x | 4.13% | 18.8% | 0.22 | 1.27 | edge survives |
| `6h` | 11.4x | 4.55% | 16.7% | 0.27 | 1.27 | edge survives |
| `4h` | 11.4x | 4.58% | 16.9% | 0.27 | 1.27 | edge survives |
| `2h` | 11.5x | 4.60% | 17.9% | 0.26 | 1.27 | edge survives |
| `1h` | 11.5x | 4.61% | 18.0% | 0.26 | 1.27 | edge survives |

**ETH-USD — Design A** (reference gross Sharpe 0.84, measured 2015–2025 daily at `maker_0bp`)

| Frequency | Ann. turnover | Fee drag / yr | Strategy ann. vol | Cost drag (Sharpe units) | vs. 2015–2025 gross Sharpe | Verdict |
|---|---|---|---|---|---|---|
| `1d` | 7.5x | 3.01% | 23.6% | 0.13 | 0.84 | edge survives |
| `12h` | 8.9x | 3.57% | 23.3% | 0.15 | 0.84 | edge survives |
| `6h` | 9.3x | 3.73% | 23.2% | 0.16 | 0.84 | edge survives |
| `4h` | 9.5x | 3.82% | 22.3% | 0.17 | 0.84 | edge survives |
| `2h` | 9.8x | 3.90% | 21.5% | 0.18 | 0.84 | edge survives |
| `1h` | 10.3x | 4.12% | 21.6% | 0.19 | 0.84 | edge survives |

**BTC-USD — Design B** (reference gross Sharpe 1.27, measured 2015–2025 daily at `maker_0bp`)

| Frequency | Ann. turnover | Fee drag / yr | Strategy ann. vol | Cost drag (Sharpe units) | vs. 2015–2025 gross Sharpe | Verdict |
|---|---|---|---|---|---|---|
| `1d` | 10.5x | 4.19% | 19.3% | 0.22 | 1.27 | edge survives |
| `12h` | 16.6x | 6.65% | 17.5% | 0.38 | 1.27 | edge survives |
| `6h` | 34.0x | 13.60% | 17.0% | 0.80 | 1.27 | edge survives |
| `4h` | 38.2x | 15.29% | 16.6% | 0.92 | 1.27 | edge survives |
| `2h` | 90.2x | 36.06% | 20.2% | 1.79 | 1.27 | **costs win** |
| `1h` | 188.7x | 75.50% | 18.4% | 4.11 | 1.27 | **costs win** |

**ETH-USD — Design B** (reference gross Sharpe 0.84, measured 2015–2025 daily at `maker_0bp`)

| Frequency | Ann. turnover | Fee drag / yr | Strategy ann. vol | Cost drag (Sharpe units) | vs. 2015–2025 gross Sharpe | Verdict |
|---|---|---|---|---|---|---|
| `1d` | 7.5x | 3.01% | 23.6% | 0.13 | 0.84 | edge survives |
| `12h` | 13.9x | 5.54% | 29.7% | 0.19 | 0.84 | edge survives |
| `6h` | 26.5x | 10.58% | 31.1% | 0.34 | 0.84 | edge survives |
| `4h` | 31.9x | 12.77% | 28.8% | 0.44 | 0.84 | edge survives |
| `2h` | 73.3x | 29.32% | 29.9% | 0.98 | 0.84 | **costs win** |
| `1h` | 161.0x | 64.38% | 31.5% | 2.04 | 0.84 | **costs win** |

### What reading (3) assumes, and which way the assumption points

It assumes **the gross edge does not change with the rule's horizon**. That assumption is
*exact for Design A* — the signal there really is the same 40-day/10-day breakout at every
frequency, so the ten-year gross Sharpe is the right number to hold it to.

For **Design B it is generous, and knowingly so.** A 40-bar entry at 2h is an 80-hour
breakout, and there is no reason a three-day trend rule should earn what a forty-day one
earns; the literature and this repo's own plateau surface both say the short-horizon
cells are the weaker ones (`plateau_20_5` was the worst column of the daily grid). Holding
the fast rules to the slow rule's gross edge therefore **flatters them**. Combined with
the fee-only cost model (no spread, no impact — see caveat 1), every distortion in this
document points the same way: **the crossover frequency reported below is an upper bound
on how fast you can trade this rule, and the true crossover is at a COARSER bar, never a
finer one.**

## The cost curve — annualised turnover and costs as a share of gross P&L, at `taker_40bp`

**Design A (constant 40-day/10-day calendar horizon):**

| Frequency | BTC-USD turnover | BTC-USD costs/gross | ETH-USD turnover | ETH-USD costs/gross |
|---|---|---|---|---|
| `1d` | 10.5x | 24.1% | 7.5x | 94.4% |
| `12h` | 10.3x | 31.2% | 8.9x | 181.0% |
| `6h` | 11.4x | 54.7% | 9.3x | 605.4% |
| `4h` | 11.4x | 47.4% | 9.5x | 404.3% |
| `2h` | 11.5x | 31.3% | 9.8x | 218.7% |
| `1h` | 11.5x | 29.7% | 10.3x | 213.6% |

**Design B (constant 40-bar/10-bar horizon):**

| Frequency | BTC-USD turnover | BTC-USD costs/gross | ETH-USD turnover | ETH-USD costs/gross |
|---|---|---|---|---|
| `1d` | 10.5x | 24.1% | 7.5x | 94.4% |
| `12h` | 16.6x | 113.8% | 13.9x | 52.3% |
| `6h` | 34.0x | 165.7% | 26.5x | 53.3% |
| `4h` | 38.2x | 401.3% | 31.9x | 40.3% |
| `2h` | 90.2x | 727.3% | 73.3x | 158.9% |
| `1h` | 188.7x | 921.5% | 161.0x | 236.0% |

## The edge curve, and the wedge costs drive between gross and net

**Design A:**

| Frequency | BTC-USD gross Sharpe (0 bp) | BTC-USD net Sharpe (40 bp) | BTC-USD wedge | ETH-USD gross Sharpe (0 bp) | ETH-USD net Sharpe (40 bp) | ETH-USD wedge |
|---|---|---|---|---|---|---|
| `1d` | -1.03 | -1.24 | 0.21 | -0.21 | -0.34 | 0.13 |
| `12h` | -0.85 | -1.06 | 0.21 | -0.16 | -0.31 | 0.15 |
| `6h` | -0.72 | -0.99 | 0.27 | -0.05 | -0.21 | 0.16 |
| `4h` | -0.78 | -1.05 | 0.27 | -0.04 | -0.20 | 0.17 |
| `2h` | -1.02 | -1.27 | 0.25 | -0.00 | -0.18 | 0.18 |
| `1h` | -1.09 | -1.35 | 0.25 | 0.00 | -0.18 | 0.19 |

**Design B:**

| Frequency | BTC-USD gross Sharpe (0 bp) | BTC-USD net Sharpe (40 bp) | BTC-USD wedge | ETH-USD gross Sharpe (0 bp) | ETH-USD net Sharpe (40 bp) | ETH-USD wedge |
|---|---|---|---|---|---|---|
| `1d` | -1.03 | -1.24 | 0.21 | -0.21 | -0.34 | 0.13 |
| `12h` | -0.54 | -0.92 | 0.38 | 0.40 | 0.22 | 0.18 |
| `6h` | -0.67 | -1.43 | 0.76 | 0.84 | 0.46 | 0.39 |
| `4h` | 0.05 | -0.88 | 0.94 | 1.34 | 0.86 | 0.48 |
| `2h` | -0.51 | -2.37 | 1.86 | 0.59 | -0.53 | 1.11 |
| `1h` | -1.01 | -5.00 | 3.99 | 0.80 | -1.61 | 2.41 |

**These wedges are the cross-check on the Sharpe-unit conversion above.** The wedge column
is measured directly — run the identical cell at 0 bp and at 40 bp and subtract the two
annualised Sharpes. The cost-drag column is derived — annual fee drag ÷ annual volatility,
never touching a second backtest.

They agree to within **0.047 of a Sharpe** at every rung whose cost wedge is below one Sharpe unit — 20 of the 24 cells. At the 4 fastest Design B rungs, where the wedge exceeds a whole Sharpe point, the gap widens to 0.37 absolute (15% relative) — which is the first-order approximation `ΔSharpe ≈ c/σ` doing what a first-order approximation does when `c` reaches 60–75% of capital a year and the two runs' position paths genuinely diverge. It does not weaken the conclusion: both the measured and the derived curve are far above the gross edge there, and they disagree only about how far. That is what says the conversion is arithmetic rather than hand-waving, and what licenses reading the cost curve as an estimate of Sharpe lost to fees.


---

# 15m and 30m: a turnover measurement, NOT a performance result

**This section makes no return claim and none can be made from it.** yfinance serves 60
days of 15m/30m data. A 252-day walk-forward training window does not fit inside 60 days,
and shrinking the window to 252 *bars* would make the training slice 2.6 days at 15m —
economically meaningless, and precisely the kind of number this project exists not to
print. So there is no walk-forward here, no out-of-sample split, and no Sharpe.

What *is* measurable on 60 days is how often the rule trades and what that costs, because
turnover is a property of the rule and the bar size rather than of the sample's returns.
Design B (40-bar entry / 10-bar exit) only, at `taker_40bp`, over the same 60-day window at
every rung so the ladder is internally comparable. "Fees alone, annualised" is costs paid
per year as a fraction of average equity — a pure fee drag, netted against nothing.

**BTC-USD**

| Frequency | Bars | Closed trades | Median hold | Whipsaw (≤3 d) | Ann. turnover | Fees alone, annualised |
|---|---|---|---|---|---|---|
| `15m` | 5,664 | 65 +1 open | 0.21 d | 100.0% | 786.3x | 314.5% |
| `30m` | 2,832 | 29 +1 open | 0.29 d | 100.0% | 352.9x | 141.1% |
| `1h` | 1,416 | 15 +1 open | 0.71 d | 93.3% | 182.7x | 73.1% |
| `2h` | 708 | 6 +1 open | 1.62 d | 66.7% | 77.4x | 31.0% |
| `4h` | 354 | 4 | 2.92 d | 50.0% | 47.9x | 19.2% |
| `6h` | 236 | 2 | 8.62 d | 0.0% | 25.0x | 10.0% |
| `12h` | 118 | 1 | 13.50 d | 0.0% | 12.5x | 5.0% |
| `1d` | 59 | 0 | n/a | n/a | 0.0x | 0.0% |

**ETH-USD**

| Frequency | Bars | Closed trades | Median hold | Whipsaw (≤3 d) | Ann. turnover | Fees alone, annualised |
|---|---|---|---|---|---|---|
| `15m` | 5,664 | 65 | 0.21 d | 100.0% | 745.9x | 298.3% |
| `30m` | 2,832 | 27 | 0.29 d | 100.0% | 325.6x | 130.2% |
| `1h` | 1,416 | 15 +1 open | 1.17 d | 93.3% | 182.0x | 72.8% |
| `2h` | 708 | 8 +1 open | 1.67 d | 75.0% | 99.2x | 39.7% |
| `4h` | 354 | 2 | 4.33 d | 50.0% | 20.8x | 8.3% |
| `6h` | 236 | 3 | 9.00 d | 0.0% | 34.5x | 13.8% |
| `12h` | 118 | 1 | 18.00 d | 0.0% | 12.5x | 5.0% |
| `1d` | 59 | 0 | n/a | n/a | 0.0x | 0.0% |

**The ladder does not flatten out below 1h — it accelerates.** At 15m, BTC-USD turns over 786× a year and pays 315% of capital in fees annually, with a median trade held 5 hours and a 100% whipsaw rate; ETH-USD turns over 746× a year and pays 298% of capital in fees annually, with a median trade held 5 hours and a 100% whipsaw rate. There
is no fee tier in this study, maker or taker, at which a rule paying a triple-digit
percentage of capital per year in fees can be run: the free `maker_0bp` tier is not an
execution plan (D114's second caveat), and every other tier is arithmetic away from
certain ruin. **This is the one part of the 15m/30m section that needs no return data to
be conclusive**, and it is why the section exists despite making no performance claim.

**These rows are not comparable to the walk-forward tables above**: different span,
different sample, no out-of-sample discipline, no return claim.

**What it would take to do this properly.** Exchange APIs — Binance and Kraken both serve
complete 1m history free — would give the years of sub-hourly data a real walk-forward
needs. That is a new `DataSource` behind the existing interface (D18), plus its own
fixture, snapshot and cleaning rules for a provider whose volume column actually works.
It is out of scope here and is named rather than attempted.


---

# Multiplicity, and what the DSR here can and cannot mean

| What | Count |
|---|---|
| Frequencies | 6 |
| Designs | 2 |
| Cost tiers | 4 |
| Symbols | 2 |
| **Out-of-sample trials logged** | **96** (12 configurations × 4 tiers × 2 symbols) |
| — of which DISTINCT configurations per (symbol, tier) | 11 (Designs A and B are the same configuration at 1d) |
| 15m/30m turnover measurement rows (not trials — no return claim) | 16 |
| Parameters tuned | **0** |
| Filters added | **0** |
| Configurations selected on out-of-sample performance | **0** |

**DSR units for a multi-frequency pool (D164).** D98's contract requires the logged
metric, the observed SR and T to share one period. The obvious per-bar choice does not
survive here: a 1h bar and a 1d bar are not the same period, so pooling per-bar Sharpes
would be exactly the units bug D98 exists to prevent, inflating SR0 by up to √24. So every
cell's out-of-sample equity curve is collapsed to **end-of-UTC-day NAV** before the DSR is
computed. One period (the calendar day), one T (the shared out-of-sample day count), for
the whole pool.

| Symbol | Tier | Best config | Its daily SR | T (days) | N (pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|---|
| BTC-USD | `maker_0bp` | `B/4h` | 0.0026 | 440 | 12 | 0.000306 | **0.2893** |
| BTC-USD | `maker_10bp` | `B/4h` | -0.0099 | 440 | 12 | 0.000599 | **0.1448** |
| BTC-USD | `maker_25bp` | `B/4h` | -0.0282 | 440 | 12 | 0.001800 | **0.0198** |
| BTC-USD | `taker_40bp` | `B/4h` | -0.0457 | 440 | 12 | 0.003612 | **0.0012** |
| ETH-USD | `maker_0bp` | `B/4h` | 0.0663 | 440 | 12 | 0.000643 | **0.7109** |
| ETH-USD | `maker_10bp` | `B/4h` | 0.0603 | 440 | 12 | 0.000494 | **0.7027** |
| ETH-USD | `maker_25bp` | `B/4h` | 0.0513 | 440 | 12 | 0.000487 | **0.6289** |
| ETH-USD | `taker_40bp` | `B/4h` | 0.0424 | 440 | 12 | 0.000713 | **0.4820** |

**What this DSR is measuring, and it is not what it looks like.** The pool here spans
configurations whose Sharpes are *wildly* dispersed — a daily trend follower and an hourly
one are not near-duplicates the way twelve neighbouring plateau cells were in
`BREAKOUT_RESULTS.md`. A large V[{SRn}] raises the noise floor SR0 sharply, so this DSR
deflates hard. That is the statistic behaving correctly on a genuinely heterogeneous pool,
and it is *still* not the binding multiplicity: this study selected nothing, so the number
worth quoting is the ladder itself, not its best cell. Standing reading, inherited from
D90/D116: **DSR < 0.95 means "no demonstrated edge"; DSR ≥ 0.95 does not mean the
reverse.**


---

# Verdict

## The headline number

**Design B's cost curve crosses the trend edge at `2h`, and both symbols say so
independently.** The finest bar that still clears its own gross edge is
`4h` on BTC-USD, `4h` on ETH-USD — and that is
before any spread, slippage or impact is charged, and while crediting a three-day
breakout with a forty-day breakout's edge. **The honest one-sentence version: this rule
does not survive above roughly 4-hourly bars, and every unmodelled cost pushes that
boundary slower rather than faster.**

Design A never crosses at all: BTC-USD peaks at a cost drag of 0.27 against a gross Sharpe of 1.27, ETH-USD peaks at a cost drag of 0.19 against a gross Sharpe of 0.84.

## The two designs give different answers, and the difference is the whole finding

**Design A — sampling the same 40-day signal more finely is nearly free.** The entry and
exit horizons stay at 40 and 10 calendar days, so the *number* of trades barely changes;
all the finer bar buys is more precise timing of the same handful of decisions. Turnover
rises by a few percent from 1d to 1h, not by an order of magnitude, and the fee drag rises
with it. **`BREAKOUT_RESULTS.md`'s conclusion survives this design intact**: fees are not
the binding constraint on a 40-day trend follower, whatever bar you sample it on.

**Design B — shortening the horizon with the bar is where the cost explosion lives.** A
40-bar entry at 1h is a 40-HOUR breakout. The rule fires constantly, holding periods
collapse from weeks to hours, and turnover multiplies (BTC-USD: 18×, ETH-USD: 21× from 1d to 1h). This is the
design that answers the question everyone actually means by "run it intraday", and it is
the one where fees become decisive.

## The ladder, 1d → 1h

- **BTC-USD, Design A.** 1d → 1h: annualised turnover 10.5× → 11.5× (1.1× more), costs 24% → 30% of gross P&L, closed trades 6 → 7, median hold 26.00 d → 15.33 d, net Sharpe -1.24 → -1.35.
- **BTC-USD, Design B.** 1d → 1h: annualised turnover 10.5× → 188.7× (18.0× more), costs 24% → 922% of gross P&L, closed trades 6 → 117, median hold 26.00 d → 0.83 d, net Sharpe -1.24 → -5.00.
- **ETH-USD, Design A.** 1d → 1h: annualised turnover 7.5× → 10.3× (1.4× more), costs 94% → 214% of gross P&L, closed trades 6 → 7, median hold 17.00 d → 11.12 d, net Sharpe -0.34 → -0.18.
- **ETH-USD, Design B.** 1d → 1h: annualised turnover 7.5× → 161.0× (21.4× more), costs 94% → 236% of gross P&L, closed trades 6 → 116, median hold 17.00 d → 0.75 d, net Sharpe -0.34 → -1.61.

## Where the curves cross

- **BTC-USD, Design A** — spliced crossover: cost drag never reaches the 2015–2025 gross Sharpe of 1.27 on any rung down to 1h. Costs ≥ 100% of this window's gross P&L from **no rung**; net Sharpe ≤ 0 from **1d** (uninformative — see above).
- **BTC-USD, Design B** — spliced crossover: cost drag first reaches the 2015–2025 gross Sharpe of 1.27 at **2h**. Costs ≥ 100% of this window's gross P&L from **12h**; net Sharpe ≤ 0 from **1d** (uninformative — see above).
- **ETH-USD, Design A** — spliced crossover: cost drag never reaches the 2015–2025 gross Sharpe of 0.84 on any rung down to 1h. Costs ≥ 100% of this window's gross P&L from **12h**; net Sharpe ≤ 0 from **1d** (uninformative — see above).
- **ETH-USD, Design B** — spliced crossover: cost drag first reaches the 2015–2025 gross Sharpe of 0.84 at **2h**. Costs ≥ 100% of this window's gross P&L from **2h**; net Sharpe ≤ 0 from **1d** (uninformative — see above).

## Standing caveats

1. **Fees only, and the omission grows with frequency.** No spread, no slippage, no
   impact, no funding (D114). A market order into an hourly breakout crosses the same
   spread a daily one does, but pays it many times more often. Every cost number here is
   a **lower bound**, and the finer the bar the looser the bound — which means the true
   crossover is at a *coarser* frequency than any measured below.
2. **Two years, not ten.** 441 out-of-sample days is what yfinance's intraday retention
   allows. The Sharpe standard error is roughly ±0.91. Return and Sharpe differences
   between adjacent rungs are not measurable; turnover and cost differences are.
3. **A different era from the daily study.** This span is 2024-08 → 2026-08. The daily
   study covered 2015–2025 and its own era decomposition (D121) showed the strategy's CAGR
   moving from +11% to +49% on the start date alone. Comparing a level here to a level
   there compares eras, not frequencies. Only the ladder is comparable, and only within
   itself.
4. **The 1d rung is not the daily study's 1d.** Different fixture (resampled from 1h),
   different span, and the reconciliation section above shows the resampled highs and lows
   are systematically inside the provider's own — which biases toward more trading.
5. **The volume column of this provider's intraday crypto bars does not work**, and the
   pipeline was called accordingly (prices-only cleaning). Any future filter that wants
   intraday volume needs a different data source, not a different threshold.
6. **The constant-fraction benchmark degrades with frequency for its own reasons.** It
   rebalances every bar by construction (D119), so at 1h it pays fees 8,760 times a year.
   Its decline up the ladder is not evidence about the strategy.
7. **Spot, not perpetuals; no shorting; single data source.** All inherited unchanged from
   `BREAKOUT_RESULTS.md`'s caveats 3–6.
