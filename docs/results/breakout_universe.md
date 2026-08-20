# Does the crypto breakout result generalise? A 63-coin cross-section including the ones that died

**Date produced:** 2026-08-18 ·
**Snapshot:** `28afa9fb4992aa4d2e8af5c5ff2324550e4bb1bc8030066e49d66511c6a6024f` ·
**Registry:** `data/breakout_universe_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_universe.py` (offline, deterministic) ·
**Fixture:** `data/fixtures/crypto_universe_2015_2025_raw.csv.gz`
(fetched once by `scripts/fetch_crypto_universe.py`, the only step that touches the network)

> **Thesis label (D38/D82/D117).** Same label as
> [`BREAKOUT_RESULTS.md`](../../BREAKOUT_RESULTS.md): this is a **directional,
> beta-loaded** strategy, long or flat on one high-beta instrument, never short. It is
> **not** part of this project's market-neutral thesis and is not evidence about it. Its
> honest benchmark is buy-and-hold, not the risk-free rate.

## Why this exists

`BREAKOUT_RESULTS.md` names its own worst problem in its own caveats:

> "BTC and ETH are the two crypto assets that survived to be worth studying. Testing a
> trend follower on them, over a decade in which they went up enormously, is a selected
> sample by construction — the single largest un-deflatable bias in this document."

Adding twenty more of today's largest coins would restate that bias at greater scale.
This study instead runs the **identical, unmodified machinery** — `run_variant`,
`run_benchmark`, `run_constant_fraction_benchmark`, the same cost tiers, the same
walk-forward geometry — over a universe deliberately built to contain assets that
**failed**, and reports every statistic split **survived vs collapsed/delisted**. That
split is the point. It converts the bias from a disclaimer into a measurement.

**Universe:** 63 coins admitted of
77 attempted —
20 survived, 41 collapsed,
2 delisted;
13 excluded by the pre-stated policy and
1 that the provider would not serve at all. Every one of them is
named below with its reason.

**Scale.** One configuration (`plateau_40_10`, the BTC/ETH study's baseline),
4 cost tiers, 63 symbols =
**252 out-of-sample trials**, each its own continuous walk-forward run
(D113). Risk-free rate 4%; annualisation on
365 days (crypto trades every calendar day, D17).


## Method, in one screen

**Nothing here is new machinery.** Every number is produced by
`research.breakout_study`, imported unmodified: `run_variant`, `run_benchmark`,
`run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
`annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`. If a
number here disagrees with `BREAKOUT_RESULTS.md`, the data disagreed, not the code.

**Signal.** The BTC/ETH baseline, unchanged: enter long when `close(t)` exceeds the
40-bar high over t−40 … t−1, exit to flat when it
falls below the 10-bar low. Both extrema exclude the current bar.
Inverse-volatility sizing at a 40% annual vol target, fixed at entry. No filters.

**One configuration, deliberately (D141).** No per-coin parameter sweep. The BTC/ETH
study already showed the plateau is flat and that in-training selection did not pay;
sweeping 12 grid cells per coin would multiply the multiplicity by twelve to re-answer a
settled question. Holding the rule fixed is what makes the cross-section the only
variable.

**Walk-forward.** train=252, test=63, step=63;
one continuous out-of-sample run per (symbol, tier) with the warm-up prefix taken from
inside window 0's training slice, and a runtime assertion that nothing fills inside it
(D113).

**Alignment (D45/D64).** Each symbol is its own single-instrument backtest — the N=1
case — so **no coin is truncated to another's inception**. The fixture is deliberately
not inner-joined; if it were, D45 would cut all 63 coins back to the
youngest one's start and delete most of the sample.

**Costs.** The same four tiers:
`maker_0bp` = 0.00% (maker), `maker_10bp` = 0.10% (maker), `maker_25bp` = 0.25% (maker), `taker_40bp` = 0.40% (taker). One
`percent_spread` brick each — an exchange fee model and nothing more (D114), which makes
every number here optimistic.

**Three benchmarks per coin, all over the identical span.**

1. **100% buy-and-hold** at the same fee tier, fixed quantity (D115).
2. **Constant-fraction at the strategy's own average exposure** (D119) — the fairer
   test, run through the engine so its rebalancing pays real fees.
3. **The risk-free hurdle** — cash at 4%/yr over the same number of
   bars.


---

# The universe: policy first, then the list

## The candidate roster, and exactly how honest it is

Three cohorts, chosen for **point-in-time prominence** rather than present size:

| Cohort | Tickers attempted | Admitted |
|---|---|---|
| `top30_at_2018_01` | 29 | 25 |
| `prominent_at_2021_peak` | 33 | 27 |
| `sought_failures` | 15 | 11 |

**Selection-time honesty, stated plainly because it is the study's own weak point.**
The roster was assembled **by hand, in 2026, with hindsight**. It is not a
reconstruction from an archived point-in-time index — no such archive is wired into this
repo, and pretending otherwise would be exactly the self-deception this framework exists
to prevent. What can be said for it is narrower and still worth something:

- two of the three cohorts were chosen for what an asset was worth at a **past** date
  (the 2017/18 peak and the 2021 peak), not for what it is worth now;
- the third cohort was chosen **because those assets failed** — Terra/LUNA, TerraUSD,
  FTX's FTT, Celsius, Serum — which biases the universe *against* the strategy's
  flattering case, not toward it;
- 43 of the 63 admitted coins
  ended the sample down 90% or more from their own peak, or with the provider no longer
  quoting them at all. A universe of today's top names would contain almost none of them.

What is left un-removed: survivorship inside the *data provider*. A 2017 token that
yfinance never listed, or has since dropped entirely, cannot appear here at any price —
and those are, by construction, the worst outcomes of all. **This universe is less
biased than BTC/ETH. It is not unbiased.**

## The screen, pre-stated and mechanical

Applied by `research.breakout_universe.apply_policy` — one implementation, run at fetch
time to decide the fixture's contents and run **again** by the study on the committed
fixture, so a symbol that fails cannot reach the engine by being quietly present in a
CSV. It screens the **cleaned** series (D25), because the engine trades cleaned bars.

1. **All prices strictly positive.** Log returns and inverse-vol sizing are undefined
   otherwise. Applied after cleaning, so a symbol is not lost to a single bad print the
   cleaner already drops — only to a series that is genuinely part-zero.
2. **Minimum history: 520 bars.** The mechanical floor is lower: the
   harness takes its warm-up prefix from *inside* window 0's training slice, so
   252 + 63 = 315
   bars already produce one walk-forward window even for the longest lookback in this
   strategy family (a 200-day SMA gate needs 201 bars, which fits inside the 252-bar
   training slice). That floor would also be useless: one 63-bar test window is ten weeks
   of out-of-sample data for a strategy whose median trade lasts about four weeks.
   520 bars is the shortest history yielding **four windows and a full year
   (252 bars) out of sample**.
3. **Liquidity floor: median daily volume ≥ 5,000,000 USD**
   over the symbol's own history. **Median**, not mean — crypto volume is spiked hard by
   launch weeks and collapse weeks, and a mean describes those days rather than a typical
   one. The level is derived from this study's own capital: 100,000 USD starting cash
   with a 1.0× position cap means the largest opening order is ~100,000 USD, which is 2%
   of a 5,000,000 USD median day — the region D95's capacity work treats unmodelled
   impact as second-order in. It binds hardest on exactly the small tokens whose
   backtests would otherwise be the most flattering and the least real.

**Nothing in the screen touches a return, a Sharpe, a drawdown or a trade count.** That
is the difference between a universe rule and a survivorship filter, and it is why the
screen can be stated in full before any performance is computed.

## Classification: survived, collapsed, delisted

Mechanical, and **hindsight by construction** — which is legitimate here and only here,
because the label decides nothing about what is traded. Every coin is run identically;
the label only splits the results afterwards.

- **delisted** — last bar more than 90 days before the fixture's
  end date: the provider stopped quoting it. Checked first, because losing the quote is
  the more specific fact.
- **collapsed** — final close at or below 10%
  of the symbol's own highest close in the fixture (i.e. down
  90% or worse, terminally). Scale-free by
  construction.
- **survived** — neither.

**Survived (20):** `AAVE-USD`, `ADA-USD`, `BAT-USD`, `BCH-USD`, `BNB-USD`, `BTC-USD`, `CRO-USD`, `DOGE-USD`, `ETH-USD`, `HBAR-USD`, `LINK-USD`, `LTC-USD`, `MKR-USD`, `OKB-USD`, `SOL-USD`, `TRX-USD`, `XLM-USD`, `XMR-USD`, `XRP-USD`, `ZEC-USD`

**Collapsed (41):** `ALGO-USD`, `ATOM-USD`, `AVAX-USD`, `AXS-USD`, `BSV-USD`, `BTG-USD`, `CRV-USD`, `DASH-USD`, `DOT-USD`, `EGLD-USD`, `EOS-USD`, `ETC-USD`, `FIL-USD`, `FTT-USD`, `HT-USD`, `ICX-USD`, `KSM-USD`, `LSK-USD`, `LUNC-USD`, `MANA-USD`, `NEAR-USD`, `NEO-USD`, `OMG-USD`, `ONT-USD`, `QTUM-USD`, `REP-USD`, `SAND-USD`, `SC-USD`, `SNT-USD`, `SNX-USD`, `SRM-USD`, `STEEM-USD`, `SUSHI-USD`, `THETA-USD`, `USTC-USD`, `VET-USD`, `WAVES-USD`, `XEM-USD`, `XTZ-USD`, `YFI-USD`, `ZRX-USD`

**Delisted (2):** `LUNA1-USD`, `MATIC-USD`

## Every exclusion and every fetch failure, with its reason

A documented "could not obtain" is evidence. A silent omission is the bias itself.

| Symbol | Cohort | Outcome | Reason | Bars | Median daily volume (USD) | Median abs. daily return |
|---|---|---|---|---|---|---|
| `APE-USD` | prominent_at_2021_peak | excluded | median daily volume 15,818 USD < required 5,000,000 (liquidity floor) | 1,540 | 15,818 | 3.66% |
| `BTS-USD` | top30_at_2018_01 | excluded | median daily volume 2,907,337 USD < required 5,000,000 (liquidity floor) | 2,974 | 2,907,337 | 2.29% |
| `CEL-USD` | sought_failures | excluded | median daily volume 1,221,872 USD < required 5,000,000 (liquidity floor) | 2,648 | 1,221,872 | 3.14% |
| `COMP-USD` | prominent_at_2021_peak | excluded | 334 bar(s) with a non-positive price — log returns and inverse-vol sizing are undefined on them | 745 | 98 | 0.00% |
| `DCR-USD` | top30_at_2018_01 | excluded | median daily volume 3,347,258 USD < required 5,000,000 (liquidity floor) | 2,974 | 3,347,258 | 2.56% |
| `DGB-USD` | top30_at_2018_01 | excluded | median daily volume 4,866,510 USD < required 5,000,000 (liquidity floor) | 2,974 | 4,866,510 | 2.90% |
| `GRT-USD` | prominent_at_2021_peak | excluded | 387 bars < required 520 (min-history rule) | 387 | 3,007,158 | 4.40% |
| `ICP-USD` | prominent_at_2021_peak | excluded | 1 bar(s) with a non-positive price — log returns and inverse-vol sizing are undefined on them | 1,696 | 89,083,170 | 2.91% |
| `LEO-USD` | sought_failures | excluded | median daily volume 3,076,463 USD < required 5,000,000 (liquidity floor) | 2,416 | 3,076,463 | 0.83% |
| `LUNA-USD` | sought_failures | excluded | median daily volume 183 USD < required 5,000,000 (liquidity floor) | 1,127 | 183 | 5.73% |
| `MIOTA-USD` | top30_at_2018_01 | **fetch failed** | KeyError: 'Dividends' | — | — | — |
| `SHIB-USD` | prominent_at_2021_peak | excluded | 218 bar(s) with a non-positive price — log returns and inverse-vol sizing are undefined on them | 1,934 | 253,515,158 | 0.00% |
| `UNI-USD` | prominent_at_2021_peak | excluded | median daily volume 17 USD < required 5,000,000 (liquidity floor) | 1,922 | 17 | 2.14% |
| `UST-USD` | sought_failures | excluded | median \|daily return\| 0.141% < required 0.500% — a pegged instrument is not a trend-following candidate (peg screen) | 684 | 57,706,866 | 0.14% |

Four of these are worth a sentence, and none of them flatters the study.

- **`MIOTA-USD`** is IOTA, a genuine 2018 top-ten asset. yfinance no longer serves it
  under any ticker this study could find, so it is **missing, not omitted** — and it is a
  token that fell ~99% from its peak, so its absence biases the cross-section toward the
  strategy looking *worse*, not better.
- **`CEL-USD`** (Celsius) and **`LEO-USD`** are real tokens removed by the liquidity
  floor, not by any judgement about them. CEL is a genuine bankruptcy and its loss from
  the collapsed cohort is a real cost of having a mechanical rule; the rule is kept
  because a rule that bends for an interesting name is not a rule.
- **`UNI-USD`** and **`LUNA-USD`** are provider ticker collisions: yfinance serves a
  stale or near-zero series under both, at 17 and 183 USD of median daily volume. The
  liquidity floor removed them mechanically, without anyone eyeballing a chart — an
  unplanned benefit of writing the screen in terms of tradability.
- **`SHIB-USD`**, **`COMP-USD`** and **`ICP-USD`** are excluded on data quality: their
  series contain bars the provider prints at zero. SHIB is a large asset and its
  exclusion is a real loss; ICP loses its whole history to a single zero bar the
  cleaner's spike-and-revert rule cannot reach (that rule needs a bar on each side).
  Both are the honest cost of refusing to hand the engine a price of zero.


---

# The sanity gate fired, and this study overrode it — on purpose (D143)

The Step-7 pipeline ran normally: cleaning made **25 change(s)**
(dropped bars, never rewritten prices — D25's ruleset is drop-and-report). The validator
then recorded **143 hard violation(s)** across
41 symbols and 2,368 warning(s), so the snapshot is
**quarantined** — `SnapshotStore.load` refuses it unless the caller says
`allow_quarantined=True`, which this runner does, explicitly, and says so here.

Every hard violation is the same check: `unexplained_move`, a >60% single-bar move with
no split to explain it. That threshold was calibrated on ETFs (D74), where a 60% day
means the scraper served a bad print. **On a broad crypto cross-section it means
Tuesday.** ADA rose 137% on 2017-11-28; BNB rose 62% on 2018-01-05; these are real.

The distribution is the argument:

| | Hard violations |
|---|---|
| Symbols that survived | 30 |
| Symbols that collapsed or were delisted | 113 |

Concentrated in: `BTG-USD` (16), `HT-USD` (15), `LUNC-USD` (8), `USTC-USD` (8), `LUNA1-USD` (7), `REP-USD` (7), `FIL-USD` (5), `SNT-USD` (5), `SRM-USD` (5), `STEEM-USD` (5).

**Respecting the gate mechanically would have deleted the collapsed cohort and handed
back the exact survivorship bias this study exists to remove.** So the gate's verdict is
reported in full rather than suppressed, and overridden in one visible place rather than
worked around. The honest reading is that D74's threshold is an *equity* threshold and a
crypto-calibrated one does not exist yet — recorded as a deferral in D143, not fixed
here, because recalibrating a cross-cutting data gate from inside a study is how gates
stop meaning anything.


---

# Every coin at the reference tier (`taker_40bp`)

Sorted survivors first, then collapsed/delisted. `Matched-exposure` is the D119
constant-fraction benchmark at that coin's own average exposure; `Risk-free` is cash at
4%/yr over the same span. Every row is out of sample.

**Reconciliation against `BREAKOUT_RESULTS.md`, and why it matters.** BTC-USD and ETH-USD appear in both studies. The two share the strategy code and the harness but **not the data**: the BTC/ETH study reads `crypto_daily_2015_2025_raw.csv.gz` and this one reads `crypto_universe_2015_2025_raw.csv.gz`, fetched separately from a provider that restates history (D24's whole rationale). Their `plateau_40_10` @ `taker_40bp` rows nevertheless **agree to the precision that document prints** — the largest disagreement across every reported statistic is 0.98x the last digit it states, on total return, Sharpe, max drawdown, exposure, trade count, buy-and-hold and matched-exposure alike. So the cross-section's numbers can be read directly against the published ones, and a test pins the agreement so a future provider restatement shows up as a failure rather than as two documents quietly quoting different BTC histories.

**One column needs a warning.** `Costs/gross` is round-trip costs over |gross P&L|, so it
explodes toward meaninglessness on any coin whose gross P&L is near zero — a strategy that
made and lost almost exactly the same amount can show a four-figure percentage there. Read
it on the coins that made money and ignore it on the ones that did not; the tier table
further down reports the cross-sectional median, which is the number that means something.

| Symbol | Status | Cohort | OOS span | Bars | Total return | CAGR | Sharpe | Max DD | Exposure | Trades | Whipsaw | Costs/gross | B&H return | B&H max DD | Matched-exposure | Risk-free |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `AAVE-USD` | survived | prominent_at_2021_peak | 2021-06-15 → 2025-12-08 | 1,638 | -5.7% | -1.3% | -0.05 | 47.0% | 23.4% | 16 | 0.0% | 1020.9% | -38.8% | 88.4% | +28.1% | +19.2% |
| `ADA-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +509.2% | +27.6% | 0.80 | 45.8% | 26.2% | 24 | 0.0% | 9.0% | +102.9% | 91.9% | +126.1% | +33.8% |
| `BAT-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +97.7% | +9.6% | 0.32 | 55.5% | 28.6% | 27 | 3.7% | 25.9% | -38.2% | 93.6% | +82.7% | +33.8% |
| `BCH-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +56.0% | +6.2% | 0.24 | 51.6% | 29.0% | 30 | 0.0% | 27.7% | -33.9% | 94.2% | +79.2% | +33.8% |
| `BNB-USD` | survived | prominent_at_2021_peak | 2018-07-19 → 2025-12-17 | 2,709 | +671.5% | +31.7% | 0.78 | 45.7% | 36.7% | 30 | 3.3% | 11.0% | +6399.0% | 75.8% | +703.5% | +33.8% |
| `BTC-USD` | survived | top30_at_2018_01 | 2015-09-10 → 2025-11-12 | 3,717 | +5657.0% | +48.9% | 1.20 | 43.0% | 36.7% | 38 | 0.0% | 11.2% | +42386.7% | 83.4% | +1357.6% | +49.1% |
| `CRO-USD` | survived | prominent_at_2021_peak | 2019-08-23 → 2025-11-06 | 2,268 | +1781.2% | +60.4% | 1.17 | 45.3% | 23.8% | 18 | 5.6% | 5.0% | +182.6% | 94.6% | +105.4% | +27.6% |
| `DOGE-USD` | survived | prominent_at_2021_peak | 2018-07-19 → 2025-12-17 | 2,709 | +358.5% | +22.8% | 0.55 | 65.8% | 24.9% | 25 | 0.0% | 8.6% | +3182.1% | 92.3% | +671.9% | +33.8% |
| `ETH-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +552.2% | +28.7% | 0.78 | 35.2% | 32.8% | 28 | 0.0% | 10.4% | +500.9% | 82.4% | +198.0% | +33.8% |
| `HBAR-USD` | survived | prominent_at_2021_peak | 2020-05-26 → 2025-12-01 | 2,016 | +704.3% | +45.9% | 1.03 | 34.6% | 26.3% | 13 | 0.0% | 3.6% | +196.1% | 92.8% | +141.1% | +24.2% |
| `LINK-USD` | survived | prominent_at_2021_peak | 2018-07-20 → 2025-12-18 | 2,709 | +53.0% | +5.9% | 0.22 | 64.8% | 33.4% | 35 | 2.9% | 36.5% | +5363.3% | 90.2% | +861.0% | +33.8% |
| `LTC-USD` | survived | top30_at_2018_01 | 2015-09-10 → 2025-11-12 | 3,717 | +364.8% | +16.3% | 0.45 | 79.1% | 28.5% | 42 | 2.4% | 36.9% | +3194.7% | 93.5% | +556.0% | +49.1% |
| `MKR-USD` | survived | prominent_at_2021_peak | 2018-07-30 → 2025-12-28 | 2,709 | +4.6% | +0.6% | 0.09 | 55.2% | 26.4% | 31 | 3.2% | 79.3% | +135.2% | 91.6% | +158.4% | +33.8% |
| `OKB-USD` | survived | sought_failures | 2020-01-07 → 2025-11-17 | 2,142 | +225.3% | +22.3% | 0.56 | 48.1% | 34.2% | 25 | 0.0% | 12.3% | +3772.3% | 78.6% | +561.0% | +25.9% |
| `SOL-USD` | survived | prominent_at_2021_peak | 2020-12-18 → 2025-12-18 | 1,827 | +250.1% | +28.4% | 0.86 | 40.7% | 33.7% | 22 | 4.5% | 12.2% | +6908.5% | 96.3% | +719.8% | +21.7% |
| `TRX-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +101.8% | +9.9% | 0.31 | 47.3% | 30.1% | 30 | 0.0% | 19.3% | +634.3% | 77.6% | +211.0% | +33.8% |
| `XLM-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +81.9% | +8.4% | 0.29 | 60.0% | 21.3% | 28 | 0.0% | 11.6% | -30.8% | 90.3% | +57.5% | +33.8% |
| `XMR-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +132.5% | +12.0% | 0.40 | 33.7% | 29.9% | 23 | 0.0% | 13.1% | +198.1% | 78.5% | +129.1% | +33.8% |
| `XRP-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +120.1% | +11.2% | 0.36 | 64.9% | 23.1% | 27 | 3.7% | 13.0% | +289.2% | 83.2% | +148.6% | +33.8% |
| `ZEC-USD` | survived | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +511.6% | +27.6% | 0.76 | 53.8% | 28.7% | 25 | 0.0% | 5.1% | +87.5% | 94.3% | +163.1% | +33.8% |
| `ALGO-USD` | collapsed | prominent_at_2021_peak | 2020-02-28 → 2025-11-06 | 2,079 | +175.6% | +19.5% | 0.56 | 48.3% | 20.7% | 19 | 0.0% | 7.9% | -55.0% | 96.3% | +41.7% | +25.0% |
| `ATOM-USD` | collapsed | prominent_at_2021_peak | 2019-11-21 → 2025-12-03 | 2,205 | +68.7% | +9.0% | 0.31 | 30.7% | 25.2% | 20 | 0.0% | 19.6% | -25.3% | 94.9% | +71.1% | +26.7% |
| `AVAX-USD` | collapsed | prominent_at_2021_peak | 2021-05-30 → 2025-11-22 | 1,638 | +230.3% | +30.5% | 0.83 | 28.4% | 20.9% | 15 | 0.0% | 8.3% | -20.3% | 93.5% | +36.7% | +19.2% |
| `AXS-USD` | collapsed | prominent_at_2021_peak | 2021-07-14 → 2025-11-04 | 1,575 | -20.9% | -5.3% | -0.30 | 37.4% | 17.5% | 12 | 0.0% | 31.3% | -94.9% | 99.3% | -16.9% | +18.4% |
| `BSV-USD` | collapsed | sought_failures | 2019-07-19 → 2025-12-04 | 2,331 | -60.5% | -13.5% | -0.29 | 79.9% | 15.9% | 20 | 5.0% | 19.7% | -85.9% | 95.4% | +17.9% | +28.5% |
| `BTG-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-21 | 2,709 | +84.9% | +8.6% | 0.29 | 54.4% | 23.4% | 21 | 0.0% | 16.0% | -98.2% | 99.8% | +354.2% | +33.8% |
| `CRV-USD` | collapsed | prominent_at_2021_peak | 2021-04-23 → 2025-12-18 | 1,701 | -1.4% | -0.3% | -0.00 | 51.6% | 20.9% | 18 | 0.0% | 127.3% | -87.2% | 96.8% | +9.7% | +20.1% |
| `DASH-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +81.7% | +8.4% | 0.29 | 54.1% | 21.4% | 27 | 0.0% | 19.9% | -85.4% | 95.9% | +20.9% | +33.8% |
| `DOT-USD` | collapsed | prominent_at_2021_peak | 2021-04-29 → 2025-12-24 | 1,701 | +28.4% | +5.5% | 0.20 | 40.1% | 18.3% | 13 | 0.0% | 23.9% | -95.2% | 96.8% | -24.7% | +20.1% |
| `EGLD-USD` | collapsed | prominent_at_2021_peak | 2021-05-14 → 2025-11-06 | 1,638 | +50.4% | +9.5% | 0.33 | 24.8% | 15.0% | 9 | 0.0% | 12.0% | -94.9% | 98.3% | -19.1% | +19.2% |
| `EOS-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | -10.8% | -1.5% | -0.01 | 44.4% | 20.1% | 23 | 0.0% | 715.3% | -98.2% | 98.9% | -21.1% | +33.8% |
| `ETC-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +156.6% | +13.5% | 0.43 | 43.3% | 21.0% | 24 | 0.0% | 13.4% | -31.1% | 91.0% | +61.5% | +33.8% |
| `FIL-USD` | collapsed | prominent_at_2021_peak | 2018-08-22 → 2025-11-19 | 2,646 | +313.4% | +21.6% | 0.56 | 37.6% | 23.3% | 17 +1 open | 0.0% | 9.8% | -60.3% | 99.3% | +241.8% | +32.9% |
| `FTT-USD` | collapsed | sought_failures | 2020-04-08 → 2025-12-16 | 2,079 | +187.1% | +20.3% | 0.54 | 61.8% | 25.7% | 20 | 0.0% | 17.5% | -80.3% | 99.3% | +72.6% | +25.0% |
| `HT-USD` | collapsed | sought_failures | 2018-10-13 → 2025-11-16 | 2,583 | +388.9% | +25.1% | 0.58 | 63.6% | 26.5% | 19 | 0.0% | 9.3% | -84.0% | 100.0% | +5031103.4% | +32.0% |
| `ICX-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +479.1% | +26.7% | 0.72 | 38.8% | 23.9% | 17 | 0.0% | 8.3% | -96.5% | 98.3% | -3.6% | +33.8% |
| `KSM-USD` | collapsed | prominent_at_2021_peak | 2020-08-20 → 2025-12-24 | 1,953 | +148.3% | +18.5% | 0.50 | 38.4% | 24.9% | 14 | 0.0% | 10.4% | -52.9% | 98.9% | +64.9% | +23.4% |
| `LSK-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +70.5% | +7.5% | 0.25 | 47.0% | 16.5% | 17 | 0.0% | 21.3% | -96.6% | 98.2% | -2.4% | +33.8% |
| `LUNA1-USD` | delisted | sought_failures | 2020-04-03 → 2022-09-02 | 882 | +1682.3% | +229.4% | 1.88 | 33.1% | 39.0% | 10 +1 open | 0.0% | 2.2% | -99.8% | 100.0% | +622.4% | +9.9% |
| `LUNC-USD` | collapsed | sought_failures | 2020-04-04 → 2025-12-13 | 2,079 | +1210.8% | +57.1% | 0.97 | 52.1% | 28.8% | 18 +1 open | 0.0% | 9.5% | -100.0% | 100.0% | +297.0% | +25.0% |
| `MANA-USD` | collapsed | prominent_at_2021_peak | 2018-07-19 → 2025-12-17 | 2,709 | +448.2% | +25.8% | 0.60 | 45.5% | 24.3% | 24 | 0.0% | 12.1% | +7.2% | 97.7% | +158.3% | +33.8% |
| `MATIC-USD` | delisted | prominent_at_2021_peak | 2020-01-05 → 2025-03-09 | 1,890 | +199.8% | +23.6% | 0.66 | 40.9% | 29.2% | 19 | 0.0% | 10.4% | +1373.8% | 92.3% | +360.8% | +22.5% |
| `NEAR-USD` | collapsed | prominent_at_2021_peak | 2021-06-23 → 2025-12-16 | 1,638 | +231.6% | +30.6% | 0.74 | 48.8% | 27.1% | 15 | 0.0% | 9.1% | -27.3% | 95.1% | +54.7% | +19.2% |
| `NEO-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +96.5% | +9.5% | 0.32 | 39.7% | 23.7% | 23 | 4.3% | 17.1% | -90.0% | 97.1% | +10.8% | +33.8% |
| `OMG-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +189.3% | +15.4% | 0.45 | 49.7% | 20.1% | 21 | 0.0% | 13.8% | -98.9% | 99.6% | -13.4% | +33.8% |
| `ONT-USD` | collapsed | sought_failures | 2018-11-15 → 2025-12-10 | 2,583 | -49.8% | -9.3% | -0.27 | 64.3% | 25.9% | 25 | 0.0% | 32.4% | -95.3% | 97.5% | -7.7% | +32.0% |
| `QTUM-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +59.9% | +6.5% | 0.24 | 48.4% | 23.3% | 26 | 0.0% | 30.0% | -84.9% | 95.3% | +31.2% | +33.8% |
| `REP-USD` | collapsed | sought_failures | 2018-07-19 → 2025-12-17 | 2,709 | -38.3% | -6.3% | -0.18 | 52.1% | 18.9% | 22 | 0.0% | 27.0% | -97.4% | 99.6% | +25.6% | +33.8% |
| `SAND-USD` | collapsed | prominent_at_2021_peak | 2021-04-23 → 2025-12-19 | 1,701 | +291.6% | +34.0% | 0.79 | 38.6% | 20.8% | 12 | 0.0% | 6.8% | -72.1% | 98.7% | +26.2% | +20.1% |
| `SC-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +168.4% | +14.2% | 0.45 | 49.2% | 19.1% | 19 | 0.0% | 8.1% | -88.8% | 97.4% | +22.4% | +33.8% |
| `SNT-USD` | collapsed | sought_failures | 2018-07-19 → 2025-12-17 | 2,709 | +23.0% | +2.8% | 0.15 | 50.2% | 17.3% | 20 | 0.0% | 39.0% | -83.4% | 95.3% | +37.9% | +33.8% |
| `SNX-USD` | collapsed | prominent_at_2021_peak | 2018-11-21 → 2025-12-16 | 2,583 | +490.3% | +28.5% | 0.80 | 41.8% | 27.4% | 21 | 4.8% | 9.1% | +418.4% | 98.4% | +410.5% | +32.0% |
| `SRM-USD` | collapsed | sought_failures | 2021-04-20 → 2025-12-15 | 1,701 | -60.7% | -18.2% | -0.87 | 74.5% | 15.0% | 13 | 0.0% | 7.3% | -99.9% | 100.0% | -24.7% | +20.1% |
| `STEEM-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | -12.4% | -1.8% | -0.04 | 61.2% | 16.7% | 20 | 0.0% | 4767.4% | -95.9% | 95.9% | +3.7% | +33.8% |
| `SUSHI-USD` | collapsed | prominent_at_2021_peak | 2021-05-07 → 2025-10-30 | 1,638 | +27.6% | +5.6% | 0.23 | 52.2% | 20.4% | 16 | 0.0% | 19.0% | -97.0% | 97.8% | -19.5% | +19.2% |
| `THETA-USD` | collapsed | prominent_at_2021_peak | 2018-09-26 → 2025-12-23 | 2,646 | +608.4% | +31.0% | 0.80 | 59.5% | 24.0% | 23 | 0.0% | 8.2% | +218.0% | 98.1% | +205.7% | +32.9% |
| `USTC-USD` | collapsed | sought_failures | 2021-08-04 → 2025-11-25 | 1,575 | -59.7% | -19.0% | -1.19 | 62.3% | 10.9% | 10 | 0.0% | 5.4% | -99.4% | 99.4% | -2.8% | +18.4% |
| `VET-USD` | collapsed | prominent_at_2021_peak | 2019-04-12 → 2025-10-30 | 2,394 | +308.9% | +24.0% | 0.65 | 37.4% | 28.4% | 22 | 0.0% | 10.2% | +125.2% | 94.2% | +159.9% | +29.3% |
| `WAVES-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +118.5% | +11.1% | 0.35 | 55.5% | 21.3% | 24 | 0.0% | 18.6% | -77.2% | 98.9% | +60.2% | +33.8% |
| `XEM-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +51.4% | +5.7% | 0.21 | 45.7% | 21.0% | 19 | 0.0% | 24.8% | -99.3% | 99.9% | -28.6% | +33.8% |
| `XTZ-USD` | collapsed | prominent_at_2021_peak | 2018-07-19 → 2025-12-17 | 2,709 | +197.4% | +15.8% | 0.47 | 48.2% | 20.9% | 23 | 0.0% | 11.3% | -80.7% | 94.9% | +31.0% | +33.8% |
| `YFI-USD` | collapsed | prominent_at_2021_peak | 2021-03-31 → 2025-11-25 | 1,701 | -26.3% | -6.3% | -0.13 | 50.4% | 17.2% | 16 | 0.0% | 33.1% | -88.6% | 95.2% | -8.4% | +20.1% |
| `ZRX-USD` | collapsed | top30_at_2018_01 | 2018-07-19 → 2025-12-17 | 2,709 | +200.2% | +16.0% | 0.46 | 50.1% | 21.9% | 22 | 4.5% | 9.5% | -90.1% | 94.6% | +24.3% | +33.8% |


---

# The cross-section: the actual result

The question is not "what did the strategy return" — with 63 coins over a
decade, some number will be large. The question is **in what fraction of the
cross-section did a fixed breakout rule beat each benchmark.**

| Bucket | Coins | Beat 100% buy & hold | Beat matched-exposure (D119) | Beat risk-free | Reduced max drawdown | Positive total return |
|---|---|---|---|---|---|---|
| All | 63 | 51/63 (81%) | 38/63 (60%) | 50/63 (79%) | 63/63 (100%) | 52/63 (83%) |
| Survived | 20 | 9/20 (45%) | 9/20 (45%) | 18/20 (90%) | 20/20 (100%) | 19/20 (95%) |
| Collapsed / delisted | 43 | 42/43 (98%) | 29/43 (67%) | 32/43 (74%) | 43/43 (100%) | 33/43 (77%) |

Read the second column against the third. Beating 100% buy-and-hold is a low bar on a
cross-section this full of assets that fell 90%+ — you clear it by being in cash. Beating
the **matched-exposure** benchmark is the real test (D119): it holds the same average
fraction of capital in the same coin over the same span, so the only difference left is
*when* the exposure was taken. That is the only column that isolates the timing claim.

## Distributions, not means

A cross-section dominated by one or two coins is exactly the failure this study exists to
expose, so the whole distribution is reported.

**Total return (out of sample, `taker_40bp`):**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | -60.7% | -20.9% | +50.4% | +148.3% | +358.5% | +608.4% | +5657.0% | +332.6% |
| Survived | 20 | -5.7% | +4.6% | +81.9% | +237.7% | +511.6% | +704.3% | +5657.0% | +611.4% |
| Collapsed / delisted | 43 | -60.7% | -38.3% | +23.0% | +118.5% | +231.6% | +479.1% | +1682.3% | +203.0% |

**Buy-and-hold total return over the same spans:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | -100.0% | -98.2% | -94.9% | -60.3% | +182.6% | +3182.1% | +42386.7% | +1149.6% |
| Survived | 20 | -38.8% | -38.2% | +87.5% | +243.7% | +3194.7% | +6399.0% | +42386.7% | +3669.6% |
| Collapsed / delisted | 43 | -100.0% | -99.3% | -96.6% | -87.2% | -55.0% | +7.2% | +1373.8% | -22.5% |

**Annualised Sharpe:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | -1.19 | -0.13 | 0.22 | 0.43 | 0.72 | 0.83 | 1.88 | 0.40 |
| Survived | 20 | -0.05 | 0.09 | 0.29 | 0.50 | 0.78 | 1.03 | 1.20 | 0.56 |
| Collapsed / delisted | 43 | -1.19 | -0.27 | 0.15 | 0.35 | 0.60 | 0.80 | 1.88 | 0.33 |

**Max drawdown:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | +24.8% | +35.2% | +40.7% | +48.3% | +55.2% | +64.3% | +79.9% | +49.1% |
| Survived | 20 | +33.7% | +34.6% | +43.0% | +47.7% | +55.5% | +64.9% | +79.1% | +50.9% |
| Collapsed / delisted | 43 | +24.8% | +37.4% | +39.7% | +48.4% | +54.1% | +62.3% | +79.9% | +48.3% |

**Buy-and-hold max drawdown:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | +75.8% | +83.4% | +92.8% | +95.9% | +98.7% | +99.6% | +100.0% | +94.4% |
| Survived | 20 | +75.8% | +77.6% | +82.4% | +90.9% | +93.5% | +94.3% | +96.3% | +88.2% |
| Collapsed / delisted | 43 | +91.0% | +94.6% | +95.3% | +97.8% | +99.3% | +99.9% | +100.0% | +97.3% |

**Time in market:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | +10.9% | +17.2% | +20.7% | +23.7% | +28.4% | +32.8% | +39.0% | +24.1% |
| Survived | 20 | +21.3% | +23.1% | +24.9% | +28.7% | +32.8% | +34.2% | +36.7% | +28.9% |
| Collapsed / delisted | 43 | +10.9% | +16.5% | +18.9% | +21.0% | +24.9% | +27.4% | +39.0% | +21.9% |

**Closed trades per coin:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | 9.00 | 13.00 | 17.00 | 21.00 | 25.00 | 30.00 | 42.00 | 21.35 |
| Survived | 20 | 13.00 | 16.00 | 23.00 | 27.00 | 30.00 | 35.00 | 42.00 | 26.85 |
| Collapsed / delisted | 43 | 9.00 | 12.00 | 16.00 | 19.00 | 22.00 | 24.00 | 27.00 | 18.79 |

**Costs as a share of gross P&L:**

| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |
|---|---|---|---|---|---|---|---|---|---|
| All | 63 | +2.2% | +7.3% | +9.1% | +12.3% | +24.8% | +36.9% | +4767.4% | +120.7% |
| Survived | 20 | +3.6% | +5.0% | +9.0% | +12.3% | +25.9% | +36.9% | +1020.9% | +68.6% |
| Collapsed / delisted | 43 | +2.2% | +7.9% | +9.1% | +13.4% | +23.9% | +33.1% | +4767.4% | +144.9% |

The median coin's strategy return is +148.3% against a median
buy-and-hold of -60.3%; the mean strategy return is
+332.6% against a mean buy-and-hold of +1149.6%.
**The gap between the median and the mean is the whole story of a crypto
cross-section** — a handful of coins carry the average, and neither the strategy nor the
benchmark is described by its own mean.


---

# Survived vs collapsed: the headline

The standing prior for a trend follower is that its value is concentrated in the assets
that fell apart — it is insurance, and insurance pays out on the wreck. `BREAKOUT_RESULTS`
could not test that: it had two survivors and five down years. This universe has
43 wrecks.

| Bucket | Coins | Beat 100% buy & hold | Beat matched-exposure (D119) | Beat risk-free | Reduced max drawdown | Positive total return |
|---|---|---|---|---|---|---|
| All | 63 | 51/63 (81%) | 38/63 (60%) | 50/63 (79%) | 63/63 (100%) | 52/63 (83%) |
| Survived | 20 | 9/20 (45%) | 9/20 (45%) | 18/20 (90%) | 20/20 (100%) | 19/20 (95%) |
| Collapsed / delisted | 43 | 42/43 (98%) | 29/43 (67%) | 32/43 (74%) | 43/43 (100%) | 33/43 (77%) |

**The prior is confirmed on the buy-and-hold comparison.** Against 100% buy-and-hold the strategy wins
42/43 (98%) of the collapsed/delisted coins versus
9/20 (45%) of the survivors — and it survives the matched-exposure test too, which is the harder one:
29/43 (67%) versus 9/20 (45%) at matched
exposure.

**Why the two columns disagree, mechanically.** Against a 100%-invested benchmark on an
asset that fell 99%, being flat most of the time is enough to win; the strategy does not
have to be right about anything except *not holding*. The matched-exposure benchmark
removes that advantage by construction — it holds the same average fraction — so what it
measures is whether the exposure was taken at better moments than average. Those are two
different claims, and a cross-section is the first place in this project where they can
be separated cleanly.

## The same split on the underlying statistics

| Statistic (median) | Survived | Collapsed / delisted |
|---|---|---|
| Strategy total return | +237.7% | +118.5% |
| Buy & hold total return | +243.7% | -87.2% |
| Strategy CAGR | +19.3% | +11.1% |
| Buy & hold CAGR | +20.9% | -26.4% |
| Strategy Sharpe (ann.) | 0.50 | 0.35 |
| Buy & hold Sharpe (ann.) | 0.65 | 0.27 |
| Strategy max drawdown | 47.7% | 48.4% |
| Buy & hold max drawdown | 90.9% | 97.8% |
| Time in market | 28.7% | 21.0% |
| Closed trades | 27 | 19 |
| Costs / gross P&L | 12.3% | 13.4% |

Note the drawdown rows, which are the finding `BREAKOUT_RESULTS` said was the one it
could defend. Median strategy drawdown is 47.7% on
survivors and 48.4% on the wrecks, against buy-and-hold
drawdowns of 90.9% and 97.8%. Whether
that is worth its cost is the return rows above, and a reader should decide from both.

## Where BTC and ETH sit in their own cross-section

| Coin | Total return | Rank of 63 | Sharpe | Rank | Beat B&H? | Beat matched-exposure? |
|---|---|---|---|---|---|---|
| `BTC-USD` | +5657.0% | 1 | 1.20 | 2 | no | yes |
| `ETH-USD` | +552.2% | 8 | 0.78 | 13 | yes | yes |

Both of the original study's coins sit in the top quartile of this cross-section (worst rank 13 of 63) — flattering, but not the extreme outlier case. The hit-rate tables above are the test that matters.


---

# Are any of these Sharpe differences measurable? (D120)

`BREAKOUT_RESULTS.md` retracted its risk-adjusted claim because the paired block
bootstrap put the 90% interval on the Sharpe difference comfortably across zero on both
of its symbols, concluding that ten years of daily data buys roughly ±0.4 of standard
error. With 63 coins the same test can be *counted* instead of described. Each coin gets
its own paired block bootstrap (20-bar blocks, 4,000 sims, seed 0, the
same resampled bar indices applied to both series so their correlation is preserved).

| Comparison | Coins | Median P(Δ Sharpe > 0) | p10 | p90 | Coins whose 90% interval excludes zero |
|---|---|---|---|---|---|
| Strategy − buy & hold (100%) | 63 | 47% | 8% | 86% | **3 of 63** |
| Strategy − constant fraction (D119) | 63 | 66% | 16% | 94% | **4 of 63** |

**On this evidence, no Sharpe comparison in this document should be read as a measurement.** The return and drawdown differences are the defensible findings, exactly as the
two-symbol study concluded — and the cross-section says so with a count rather than an
anecdote. Note also that these are 63 separate 90% intervals: at that confidence level
roughly 6 would be expected to exclude zero by chance alone, and no
multiplicity correction is applied to them.


---

# Costs across the cross-section

| Tier | Fee | Role | Median total return | Median Sharpe | Beat B&H | Beat matched-exposure | Median costs / gross P&L |
|---|---|---|---|---|---|---|---|
| `maker_0bp` | 0.00% | maker | +169.8% | 0.48 | 51/63 (81%) | 40/63 (63%) | 0.0% |
| `maker_10bp` | 0.10% | maker | +163.3% | 0.47 | 51/63 (81%) | 40/63 (63%) | 3.1% |
| `maker_25bp` | 0.25% | maker | +155.7% | 0.45 | 51/63 (81%) | 40/63 (63%) | 7.7% |
| `taker_40bp` | 0.40% | taker | +148.3% | 0.43 | 51/63 (81%) | 38/63 (60%) | 12.3% |

Median return is monotone non-increasing in the fee tier by construction — the same
property the BTC/ETH study property-tested at the NAV level. What the cross-section adds
is the median cost share: the fee question is answered the same way on 60-odd coins as it
was on two, because the mechanism (a few dozen trades per decade, hysteresis between a
40-bar entry and a 10-bar exit) is a property of the
rule, not of the instrument.


---

# Is this the strategy, or is it the era? (D121, lifted to the cross-section)

D121 makes these two tables mandatory for any crypto backtest. Here they are computed
across the whole universe rather than per coin, using `bs.annual_breakdown` and
`bs.start_date_sensitivity` unmodified.

## Year by year, across the cross-section

| Year | Coins live | Median strategy | Median buy & hold | Share beating B&H | Mean time in market |
|---|---|---|---|---|---|
| 2015 | 2 | +1.7% | +48.7% | 0% | 19% |
| 2016 | 2 | +56.9% | +74.1% | 0% | 28% |
| 2017 | 2 | +464.9% | +3317.5% | 0% | 50% |
| 2018 | 38 | +0.0% | -69.7% | 97% | 4% |
| 2019 | 42 | -3.4% | -16.8% | 55% | 23% |
| 2020 | 51 | +35.3% | +130.9% | 18% | 37% |
| 2021 | 63 | +52.9% | +153.3% | 14% | 38% |
| 2022 | 63 | -15.5% | -79.6% | 100% | 10% |
| 2023 | 62 | +16.6% | +81.3% | 15% | 27% |
| 2024 | 62 | +10.7% | -5.2% | 68% | 24% |
| 2025 | 62 | -12.4% | -61.6% | 82% | 16% |

The `share beating B&H` column is the one to read: it is a per-year cross-sectional hit
rate, and its swing between bull and bear years is the insurance mechanism showing up in
60-odd instruments at once instead of two.

## Start date, across the cross-section

Identical configuration, identical universe; only the investor's start date changes.

| OOS begins in | Coins with enough history | Share beating B&H | Share with lower max DD | Median strategy CAGR | Median B&H CAGR | Median strategy max DD | Median B&H max DD |
|---|---|---|---|---|---|---|---|
| 2015 | 63 | 81% | 100% | +13.5% | -13.1% | 48% | 96% |
| 2018 | 63 | 79% | 100% | +12.3% | -12.4% | 48% | 95% |
| 2020 | 63 | 73% | 100% | +15.5% | -10.9% | 48% | 95% |
| 2021 | 63 | 87% | 100% | +3.0% | -37.8% | 43% | 93% |
| 2022 | 62 | 77% | 97% | +4.8% | -29.3% | 40% | 84% |


---

# Deflated Sharpe and multiplicity

| Tier | Best symbol | Its daily SR | T (bars) | N (symbols in pool) | V[{SRn}] | **DSR** |
|---|---|---|---|---|---|---|
| `maker_0bp` | `LUNA1-USD` | 0.0996 | 881 | 63 | 0.000593 | **0.9636** |
| `maker_10bp` | `LUNA1-USD` | 0.0993 | 881 | 63 | 0.000594 | **0.9621** |
| `maker_25bp` | `LUNA1-USD` | 0.0988 | 881 | 63 | 0.000596 | **0.9597** |
| `taker_40bp` | `LUNA1-USD` | 0.0983 | 881 | 63 | 0.000598 | **0.9573** |

**Read the "best symbol" column before the DSR column.** At the reference tier the best
cross-sectional daily Sharpe belongs to `LUNA1-USD` — a coin this study labels
**delisted** — over 881 out-of-sample bars, which is
2.4 years, the short end of this universe.
Its DSR of 0.9573 clears the standing 0.95 line. A selected best-of-63 result on a short span, from a
token that no longer trades, is the single least robust number in this document, and it
is printed here rather than in a headline for that reason.

**What the pool is.** One row per **symbol** at that tier — N = 63 — selected on
identity fields in the logged config (`row_kind == "symbol"`, matching tier, matching
trial-id prefix), never on the presence of a metric (D98's rule). Units are daily
throughout, matching D98's contract. Per-benchmark rows (`row_kind="benchmark"`) and
per-window rows (`row_kind="window"`) are in the registry as the program-level
multiplicity record and are excluded by that same predicate.

**Why symbols and not configurations.** D116 set the pool to configurations *for a study
that swept configurations*. This study sweeps none — one fixed rule everywhere — so its
multiplicity lives entirely in the cross-section: 63 coins were run and the best one
will inevitably look good. That is precisely the selection DSR was built to deflate, and
it is the honest pool here.

**What the pool is NOT.** It does not count:

- the **roster construction** — a hand-assembled list, in 2026, of coins someone
  remembered. That is the largest uncounted term and it cannot be deflated away by any
  statistic computed inside this document;
- the **4 cost tiers** (the same run at a different fee is a
  sensitivity point, not an independent trial — D98's rule);
- the **23 configurations** the BTC/ETH study already evaluated before this one fixed the
  baseline. That study's multiplicity is upstream of this study's rule, and this study
  inherits it;
- the multiplicity of having asked the crypto question at all, in 2026, with a decade of
  crypto trend visible.

**The standing reading, inherited from D90/D116:** a DSR below 0.95 means "no
demonstrated edge"; a DSR above 0.95 does **not** mean the reverse.

| What | Count |
|---|---|
| Symbols admitted | 63 |
| Strategy configurations per symbol | 1 |
| Cost tiers | 4 |
| **Out-of-sample trials logged** | **252** |
| Benchmark rows logged | 756 |
| Per-window rows logged | 9,552 |
| In-training-window parameter evaluations | 0 (nothing is fitted — the rule is fixed a priori) |


---

# Verdict: does the BTC/ETH result generalise?

**Only where the asset fell apart.** The timing claim holds on the coins that collapsed and fails on the coins that survived — which is the standing prior for a trend follower, confirmed here for the first time in this project on a sample large enough to see it.

Across 63 coins at the reference tier, the fixed baseline beat the
matched-exposure benchmark (D119 — the fair test) in **38 of 63 (60%)** and
beat 100% buy-and-hold in **51 of 63 (81%)**. The drawdown claim, by contrast, holds everywhere: **63 of 63 (100%)**.

The median coin returned +148.3% out of sample against a
median buy-and-hold of -60.3%, at a median Sharpe of
0.43 against 0.41, with a
median max drawdown of 48.3% against
95.9%.

**The survived/collapsed split.** Beat-buy-and-hold: 45% of
survivors versus 98% of the wrecks. Beat-matched-exposure:
45% versus 67%. Lower
drawdown: 100% versus 100%.

**Where the original two coins sit.** `BTC-USD` ranks 1 of 63 on total return and 2 of 63 on Sharpe;
`ETH-USD` ranks 8 of 63 on total return and 13 of 63 on Sharpe. That is the number
`BREAKOUT_RESULTS.md` could not compute about itself, and it is the direct answer to its
own caveat 3.

## What this study does and does not settle

- It **does** settle whether the BTC/ETH numbers were an instrument-selection artifact:
  the ranks above answer that with a number rather than a disclaimer.
- It **does** separate two claims the two-symbol study could not: "better than holding"
  (easy on a dying asset — you win by being in cash) and "better than holding the same
  average exposure" (hard, and the only version that is about timing).
- It **does not** remove selection bias. The roster is hand-assembled with hindsight, and
  the provider's own coverage removes the worst failures before this study ever sees
  them. It removes the *specific* bias of studying only two survivors, and it measures
  what removing it costs.
- It **does not** change the execution story. Every number is still fees-only (D114): no
  spread, no slippage, no market impact. On the small and dying end of this universe that
  understatement is far worse than on BTC — an exit signal on a token that has fallen 95%
  is a market order into a book that is not there. **That, not the fee tier, is what
  would move these numbers most.**


---

# Standing caveats (R3)

1. **The roster is hindsight-assembled.** Stated at length above. This universe is less
   biased than BTC/ETH; it is not unbiased, and no statistic in this document can fix
   that.
2. **Provider survivorship.** A token yfinance never listed, or has dropped entirely,
   cannot appear here — and those are the worst outcomes by construction. `MIOTA-USD` is
   the visible case; the invisible ones are the problem.
3. **Fees only (D114).** No spread, no slippage, no market impact, no funding. On
   collapsed and illiquid names this is a much larger understatement than it was on
   BTC/ETH, and it biases every collapsed-cohort number optimistically — which is
   precisely the cohort this study leans on.
4. **The liquidity floor is a full-history median.** A token that was liquid for three
   years and then died is judged on both eras at once. The floor is stated, mechanical
   and reported per exclusion, but it is not a point-in-time tradability test, and a
   point-in-time one would be better.
5. **The sanity gate was overridden (D143).** 520-bar
   coverage and the liquidity floor are respected; the validator's ETF-calibrated 60%
   move threshold is not. Every hard violation is counted and reported above.
6. **Capital is unmodelled at scale.** The liquidity floor is derived from 100,000 USD of
   starting capital. Several coins compound to many multiples of that inside the
   backtest, at which point the same order is no longer 2% of a day's volume. D95's
   capacity machinery exists and was not run here.
7. **Spot, not perpetuals; no shorting (D108).** Unchanged from `BREAKOUT_RESULTS.md`. A
   long-flat rule on a universe of assets that mostly went to zero is leaving the obvious
   trade on the table, and saying so is not the same as having tested it.
8. **One configuration, inherited.** The baseline was chosen by the BTC/ETH study, on
   BTC/ETH. Fixing it here is the right call for multiplicity (D141) and it also means
   this cross-section is evaluating a rule that was, in a small way, already fitted to
   two of its members.
