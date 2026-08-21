# Changelog

All notable changes to the framework's code are logged here, in
[Keep a Changelog](https://keepachangelog.com/) style. This tracks *what shipped and when* —
the *why* behind each change belongs in [`docs/decisions/`](docs/decisions/README.md), not here.

No tagged releases yet. Entries accumulate under **Unreleased** until the first tagged
version (likely at the Phase C "first real number" milestone, see
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)).

## [Unreleased]

### Added (Phase 2 — the breakdown short book, 2026-08-21 — see `BREAKDOWN_RESULTS.md`, D169)
- **`ExitRule` brick family on the breakout strategy** — the mirror of `EntryFilter`: a
  filter can only keep you OUT of a trade, an exit rule can only get you OUT of one. The
  trailing channel stays the safety net underneath every added rule. `exit_rules` is
  emitted from `config()` only when non-empty, so long-flat configs written before it
  existed still hash identically.
- **`ChannelStopExit` and `TimeStopExit`** — the per-trade stop at the entry channel's
  opposite boundary fixed at entry, and the "not in profit within n bars" exit. Both are
  signal-level rules measured against the trigger bar's close, because the strategy
  decides on a close and the engine fills at the next open — it genuinely does not know
  what it paid.
- **Tail discipline enforced at construction (D169)** — a SHORT strategy without a
  `ChannelStopExit`, or with a weight source capping above 1.0, refuses to build. There
  is no flag that disables either. The long book is deliberately NOT held to this: a
  long's worst case is the instrument going to zero, a short's has no ceiling.
- **`CostTier.borrow_annual_rate` + `SHORT_TIERS`** — 10%/yr on short notional (D124's
  rate). The brick is emitted only when non-zero, so every long-side tier config and
  trial hash is unchanged.
- **`research/breakdown_study.py`** — the short book's own sweep ({10,20,30,40} x
  {3,5,10}, deliberately faster than the long book's), ex-post bull/bear/chop regime
  slicing, long-vs-short correlation computed INCLUDING flat bars, equal-vol ensemble
  metrics, an exposure-matched random-entry null that takes a `direction` parameter (the
  last outstanding D166 forward-compat requirement), and stop-gap measurement.
- **`scripts/run_breakdown_study.py` + `BREAKDOWN_RESULTS.md`** — 120 out-of-sample
  trials across 15 variants and 4 tiers on two symbols.

### Known limitation (D169)
- **The short stop is CLOSE-based, so the squeeze tail is not truncated by construction.**
  `stop_fill_price` has correct D10 gap semantics but is a Step-2 demonstration vehicle
  wired only to `config/fill_model.py`, never to `run_backtest`. The study measures the
  shortfall instead of assuming it away, and the measurement is damning: every stop exit
  on both symbols filled beyond its own stop, by roughly 18%.


### Added (volume reaches strategy code, 2026-08-21 — closes D111, see D168)
- **`DataView` carries volume (D168)** — an aligned, optionally-present series
  constructed sliced exactly as bars are, so the look-ahead guarantee is inherited
  rather than re-argued. `Bar` and `TimestampedBar` are unchanged. `build_data_view`,
  `run_backtest` and `walk_forward_windows` each gain one optional parameter with a
  default, so no existing call site changed — and all pre-existing golden masters pass
  untouched, which is the evidence the change is additive rather than a claim about it.
- **Three volume states, only one of them loud.** `has_volume` False means the
  instrument has none (silent, correct); a `None` entry means a gap on that bar
  (silent, consumer states its policy); `require_volume` on a view with no series
  raises `MissingVolumeError`. Collapsing the first and third is the trap — a volume
  filter with no volume rejects every entry and returns a clean-looking, entirely wrong
  result. `NaN` is normalised to `None` once at construction and never enters a view.
- **`VolumeConfirmationFilter(multiple=1.5, window=20)`** — the filter the original
  brief specified and D111 recorded as blocked. Added as a fifth filter variant facing
  the same keep/drop rule as the others. Averaging baseline ends at t−1 (D44) so a big
  trigger bar cannot inflate the threshold it has to beat; any missing volume in the
  window or on the trigger bar rejects the entry, stated and tested.
- **Feature F2 (trigger volume ratio) is computable** for the first time; D167 recorded
  it blocked by the same gap.
- **Verification** — the D32 reflection audit extended to the new surface (its Attack 5
  inspected only tuples of `Bar`, so the volume tuple would have been untested by
  construction); a property test that perturbing any future volume cannot change a
  target already produced; and a hand-computed golden master
  (`test_volume_confirmation_golden.hand.txt`) whose bar 3 and bar 9 differ in volume
  and nothing else.


### Added (breakout Phase 1.1, 2026-08-21 — see `BREAKOUT_RESULTS.md`, D166–D167)
- **`Direction` / `PositionState` on the breakout brick (D166)** — the strategy is now
  sign-parameterized: one `_channel_extreme` / `_beyond` pair serves both sides, the
  boolean `_in_position` flag is replaced by a three-state enum whose value IS the sign of
  the exposure, and `TrendGateFilter` gates longs above its SMA and shorts below it. These
  are the forward-compatibility requirements `BREAKDOWN_SHORT_STRATEGY.md` places on the
  long-side session; Phase 1 shipped without them. Behaviour-preserving for a long book,
  and `direction` is omitted from `config()` at its LONG default so every v1 trial hash
  survives unchanged.
- **`TradeEpisode.features` open map + `research/feature_analysis.py` (D167)** — the
  at-trigger feature pass from `BREAKOUT_REVERSAL_FEATURES.md`, which Phase 1 never ran.
  F1/F3/F4/F6 computed, F2 and F5 logged as blocked with reasons, quintile tables and a
  monotonicity/stability verdict per feature. Features are read off the TRIGGER bar
  (`entry_index - 1`), not the entry bar — reading the entry bar would be a one-bar
  look-ahead living inside the diagnostics. Logged only: nothing here gates a run or
  enters the DSR pool.
- **Sweep-edge section in the report** — the brief's sweep-edge rule mandated recording
  the boundary gradient and flagging an N_entry extension when performance is still
  improving at the sweep boundary. v1 did not report it at all, despite one symbol's best
  cell sitting exactly on the boundary. Now reported symmetrically, since the two symbols
  point at opposite edges.

### Fixed (breakout report, 2026-08-21)
- **The multiplicity breakdown did not sum.** Sub-rows totalled 19 against a stated 23
  variants — the four vol-target sensitivities had no row — and the verdict prose then
  quoted the wrong 19 in two places while the DSR tables correctly said 23. The row is
  added, the prose is computed rather than hardcoded, and the builder now raises if the
  breakdown ever disagrees with the variant count again.
- **The era section was hardcoded to BTC's shape.** "that decade" and "a four-figure
  percentage return" were emitted verbatim for ETH, whose out-of-sample span is 7.4 years
  and whose returns are three-figure. Both are now derived from the symbol's own span and
  its own headline number.


### Added (breakout cost–frequency frontier, 2026-08-19 — see `docs/results/breakout_intraday.md` and D160–D165)
- **`scripts/fetch_crypto_intraday.py` + `data/fixtures/crypto_intraday_{1h,30m,15m}_raw*`
  (D160)** — BTC-USD/ETH-USD intraday fixtures. yfinance serves 730 days of 1h, 60 days of
  15m/30m, no 4h over a usable span and **no 6h interval at all**, so 1h is the study base
  and 2h/4h/6h/12h/1d are resampled from it. One-time manual fetch; the only step that
  touches the network. A `live_fetch`-marked test pins the assumption the offline pipeline
  cannot check for itself — that the provider stamps intraday crypto bars in UTC, on the
  hour.
- **`research/breakout_intraday.py` (D161/D162)** — the resampling contract (exact OHLCV
  aggregation on 00:00-UTC-anchored buckets, incomplete buckets raise), the two frequency
  designs, calendar-scaled walk-forward, calendar-unit trade diagnostics, and the frontier
  renderers. Every number comes from `research.breakout_study` imported unmodified
  (`run_variant`, `run_benchmark`, `run_constant_fraction_benchmark`, `breakout_config`,
  `CostTier`, `DEFAULT_TIERS`). No existing interface changed.
- **Equal walk-forward windows across frequencies as a theorem, not a check (D161).** A UTC
  day the provider does not serve in full is dropped at *every* frequency, so each rung
  holds exactly `complete_days × bars_per_day` bars and the window count
  `floor((days − 315)/63) + 1` is frequency-independent by construction. `window_count`
  takes no frequency argument; `run_frontier` asserts the equality against every run anyway.
  7 windows over 441 out-of-sample days at every rung, both symbols.
- **`periods_per_year` consistency enforced at runtime (D162).** It lives in two places —
  the argument `analytics.metrics` requires (D17) and the field inside the
  `inverse_vol_weight` config (D110) — and `assert_periods_per_year_agree` refuses any cell
  where they disagree. Both copies are logged with every trial so the check is auditable
  after the fact.
- **The headline (D165).** Design B (40-bar/10-bar at every frequency) crosses at **2h on
  both symbols independently**, with **4h the finest bar that still clears its own gross
  edge**; annualised turnover runs 10.5× → 188.7× and fee drag 4.2% → 75.5% of capital a
  year from 1d to 1h on BTC. Design A (constant 40-day/10-day calendar horizon) **never
  crosses** at any rung down to 1h — turnover rises only 10.5× → 11.5×. So
  `BREAKOUT_RESULTS.md`'s "fees are not the binding constraint" **survives for the 40-day
  signal at any sampling rate and fails decisively for the shortened-horizon rule below
  roughly 4-hourly bars.**
- **`data/breakout_intraday_registry.sqlite`** — 112 rows (96 out-of-sample trials +
  16 sub-hourly measurement rows), all distinct hashes, config and snapshot id logged per
  D20. DSR pooled in per-calendar-day units after collapsing every equity curve to
  end-of-day NAV (D164), because pooling per-bar Sharpes across frequencies is exactly the
  units bug D98 exists to prevent.
- **Two data-layer findings, reported rather than absorbed.** (1) `clean-v1`'s
  `non_positive_volume` rule would have deleted **17,520 of 34,923** hourly bars — yfinance
  reports Volume = 0 on roughly half of them — so the intraday fixture is cleaned on prices
  only, with the volume column still written to the snapshot and the artifact surfacing as
  non-blocking warnings (D160). (2) The 1h → 1d resample **does not** reconcile with the
  committed daily fixture: opens and closes differ ~2 bp with no sign bias, but the
  resampled high is at or below the provider's daily high on 99.8% of days and the low at
  or above on ~90% — yfinance's daily crypto bar is not the aggregate of its own hourly
  bars, and the bias tilts toward *more* trading (D161). A test pins the negative so a
  future reconciliation cannot pass silently.
- **Tests** — `tests/unit/test_breakout_intraday.py` (21) and
  `tests/integration/test_breakout_intraday_study.py` (15, + 1 `live_fetch`): exact OHLCV
  aggregation, loud incomplete buckets, 00:00-UTC anchoring, frequency-independent window
  counts, `periods_per_year` agreement in both places, fixture and snapshot round-trips,
  cost monotonicity across tiers *at every frequency*, registry hash uniqueness, and the
  derived-vs-measured cost-wedge cross-check.

### Added (crypto breakout universe cross-section, 2026-08-18 — see `docs/results/breakout_universe.md` and D140–D144)
- **`scripts/fetch_crypto_universe.py` + `data/fixtures/crypto_universe_2015_2025_raw*` (D140)** —
  a 63-symbol crypto fixture built to contain the assets that **died**. 77 tickers attempted
  across three cohorts chosen for *point-in-time* prominence (the 2018 top-30, the 2021 peak,
  and a cohort sought out because it failed: Terra/LUNA under both provider tickers, TerraUSD,
  FTT, Celsius, Serum, with OKB/LEO as the surviving exchange-token control). Outcome:
  **20 survived, 41 collapsed, 2 delisted**; 13 excluded by the pre-stated policy and 1
  (`MIOTA-USD`) the provider would not serve, every one named in the meta with the statistic
  that rejected it. The one-time fetch is the only step that touches the network.
- **`research/breakout_universe.py` (D140/D141)** — selection policy, cross-sectional
  aggregation and rendering, and *nothing else*. Every number comes from
  `research.breakout_study` imported unmodified (`run_variant`, `run_benchmark`,
  `run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
  `annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`); an
  integration test pins that every logged config is byte-identical to
  `breakout_config(40, 10)`. `apply_policy` is the single implementation of the screen,
  run at fetch time and re-run by the study on the committed fixture so a rejected symbol
  cannot reach the engine — tested by feeding the study a symbol that fails the coverage
  rule and asserting it appears in neither the results nor the registry.
- **The headline (D140).** Across 63 coins at `taker_40bp` the fixed baseline beat 100%
  buy-and-hold in **51/63 (81%)**, beat the matched-exposure benchmark (D119, the fair
  test) in **38/63 (60%)**, and reduced max drawdown in **63/63 (100%)**. Split by
  outcome: against buy-and-hold it wins **45%** of survivors and **98%** of the wrecks;
  at matched exposure **45%** vs **67%**. **The timing claim generalises only to the
  assets that fell apart, and fails on the ones that survived** — the standing prior for
  a trend follower, measured for the first time here. BTC and ETH rank 1st and 8th of 63
  on total return and 2nd and 13th on Sharpe: the original study's caveat 3 answered with
  a number.
- **DSR pool = the cross-section (D142)** — one row per symbol per tier, N = 63, selected
  on identity fields (`row_kind == "symbol"`), never on presence of a metric (D98). New
  registry `data/breakout_universe_registry.sqlite`: 252 out-of-sample trials, 756
  benchmark rows, 9,552 per-window rows, all hashed with the snapshot id. DSR ≈ 0.96 at
  every tier, and the best symbol is `LUNA1-USD` — a delisted token over 881 bars, printed
  next to that fact rather than in a headline.
- **D120's bootstrap, counted instead of described** — a per-coin paired block bootstrap
  (20-bar blocks, 4,000 sims, seed 0) puts the Sharpe difference's 90% interval clear of
  zero in **3 of 63** coins against buy-and-hold and **4 of 63** against matched exposure,
  where ~6 would be expected by chance at that confidence level. No Sharpe comparison in
  the document is a measurement.
- **`SnapshotStore` quarantine overridden, loudly (D143)** — the validator's ETF-calibrated
  >60% move threshold (D74) fires 143 times across 41 of 63 crypto symbols, concentrated in
  the collapsed cohort. Respecting it mechanically would delete the failed assets and
  restore the very survivorship bias the study measures, so the run loads with
  `allow_quarantined=True` in one visible place and the report carries the full violation
  census. The validator is not modified; recalibration is deferred per R3.
- **Peg screen added post-hoc and recorded as such (D144)** — the policy's first run raised
  on `UST-USD` (a stablecoin never prints a 40-bar high, so its Sharpe is −∞ rather than
  bad). Fixed in the universe policy rather than by imputing or by selecting the DSR pool
  around it. The threshold sits in an order-of-magnitude-wide empty gap (peg 0.14%/day vs
  BTC 1.42%/day), and the amendment is dated and explained in D144 rather than folded in.
- `tests/unit/test_breakout_universe.py` (25) and
  `tests/integration/test_breakout_universe_study.py` (19, one `live_fetch`-marked) — policy exclusions and their
  reasons, "the screen never looks at a return", fixture round-trip and 00:00 stamping,
  empty events sidecar, cost monotonicity across tiers, registry id/hash uniqueness, DSR
  pool composition, cross-study reconciliation of the BTC/ETH rows against
  `BREAKOUT_RESULTS.md`, and determinism. 644 tests green (44 new), mypy clean.

### Added (BTC/ETH z-score pairs study, 2026-08-18 — see `docs/results/crypto_pairs_btc_eth.md` and D122–D127)
- **`research/crypto_pairs_study.py` (D122)** — the study harness for the repo's
  market-neutral thesis strategy on crypto. `strategies/zscore_pairs.py` is reused
  **unmodified** (D69): no new strategy was needed, so none was written. The harness
  imports `breakout_study.CostTier` / `run_benchmark` (D114/D115), `capacity`'s
  `recording_cost_stack` (D95) and `cointegration`'s Engle–Granger/ADF machinery
  (D92/D93) rather than reimplementing any of them. It does **not** reuse
  `run_pairs_study`, whose `StudyConfig` hard-codes the ETF cost stack and logs it
  verbatim — running it here would have produced trials whose logged `cost_stack`
  described bricks that did not run, the exact drift D102 closed.
- **Continuous stitching, with the chained seam priced (D123)** — one continuous OOS
  backtest per (variant, tier), the breakout study's pattern. The chained alternative
  ships as a sensitivity row: −96.7% vs −98.0% at the reference tier, 52 round trips vs
  40. Two seams motivate the choice for a pairs book, not one — the free liquidation
  D113 already named, plus the silent reset of `ZScorePairsStrategy._side`, which
  discards the hysteresis band at every boundary and is a *signal* artifact.
- **A pairs cost stack that charges what a pairs book pays (D124)** — the tier fee brick
  byte-identical to the breakout study's, plus `BorrowFee` at a stated, swept, non-zero
  10%/yr on the short leg and `MarginInterest` at 10%/yr on `max(gross − NAV, 0)`. All
  built through `build_cost_stack` (D102). `leg_weight` swept {1.0, 0.5, 0.25}; the D96
  margin-threshold collapse reproduces exactly (6,129 → 318 → 0).
- **Cointegration tested rather than assumed (D125)** — `cointegration_report` runs the
  ADF on each *training* window only, on both the traded 1:1 log spread (Dickey–Fuller
  τ_μ) and the Engle–Granger residual, with critical values anchored against
  `statsmodels.tsa.stattools.adfuller` in the unit suite. Positive and negative controls
  (a synthetic AR(1) spread; two independent random walks) ship with it.
- **Per-brick cost attribution and pair-level diagnostics (D127)** — fees / borrow /
  margin from a recording stack, plus round trips, exposure and annual turnover computed
  locally rather than by extending `trade_diagnostics.py`, whose "trade = long-flat
  position episode" definition (D112) does not describe a pairs book.
- **`tests/golden/test_crypto_pairs_golden.py` + `.hand.txt`** — a six-bar scenario
  hand-computed to the cent, pinning the axes the breakout golden master cannot reach:
  two legs filling per decision, borrow charged on the short leg *and only* the short
  leg, margin charged on gross above NAV, and the constant-gross re-normalization that
  produces interior fills as NAV moves. Reconciles exactly on first run.
- `tests/unit/test_crypto_pairs.py` (24), `tests/property/test_zscore_pairs_invariants.py`
  (9 — headline: perturbing bars after the decision bar cannot change a target, at signal
  level and through the full engine with carry), `tests/integration/test_crypto_pairs_study.py`
  (22), `tests/golden/test_crypto_pairs_golden.py` (8). 453 → 516 tests green.

### Added (breakout study review, 2026-08-18 — see D118–D121)
- **Era decomposition (D121)** — `annual_breakdown`, `exposure_by_year` and
  `start_date_sensitivity` in `research/breakout_study.py`, with a mandatory
  "Is this the strategy, or is it the era?" report section. Answers the question a
  four-figure crypto return always raises: BTC rose 426× over the OOS span, the strategy
  lost to buy-and-hold in every up year and beat it in 5 of 6 down years, and its CAGR
  ranges +11% to +49% purely on start date.
- **Risk-equalised benchmark (D119)** — `run_constant_fraction_benchmark` holds a constant
  fraction of capital (set to the strategy's own average exposure) through the same engine
  and tier, so the benchmark's average exposure matches the strategy's and the only
  remaining difference is *when* exposure was taken.
- **Paired block bootstrap on Sharpe differences (D120)** —
  `sharpe_difference_bootstrap`, seeded, resampling one index vector applied to BOTH return
  series so their correlation is preserved.
- **Vol-target sweep (D118)** — `voltarget_*` variants at 20/30/60/80% alongside the 40%
  baseline, registered as trials. DSR pool per (symbol, tier) grows 19 → 23 configurations.
- `tests/unit/test_breakout_era_analysis.py` (15 tests): bootstrap-against-itself is
  degenerate at zero (which fails if the pairing breaks), determinism under seed,
  constant-fraction at f=1 matching engine buy-and-hold, exposure-by-year computed from
  timestamps rather than run-relative indices, and the vol sweep varying exactly one key.
  438 → 453 tests green.

### Fixed (breakout study review)
- **`BREAKOUT_RESULTS.md`'s risk-adjusted claim retracted (D120).** The first version
  concluded "the entire case for this strategy is a risk-adjusted one" from Sharpe gaps of
  +0.04 (BTC) and +0.11 (ETH). Those are a tenth and a quarter of one standard error;
  P(strategy > benchmark) is 55% and 59%. Replaced with the narrower claim that survives:
  a drawdown-shape result, not an alpha result.
- **The 100%-invested benchmark was doing unfair work in both directions (D119).** A
  ~35%-exposed strategy was being judged against a 100%-exposed alternative; the
  matched-exposure row shows the strategy earning several times the terminal wealth of
  constant exposure at comparable drawdown.
- An up-year/down-year claim in the verdict was hardcoded and wrong for ETH (it has a down
  year, 2019, in which the strategy lost to holding). Now counted from the data.
- `exposure_by_year` originally indexed the OOS calendar with run-relative episode indices,
  misattributing time-in-market across years; now computed from episode timestamps, pinned
  by a test.

### Added (breakout study, 2026-08-18 — see BREAKOUT_RESULTS.md and D108–D117)
- **`strategies/breakout.py` (D109)** — long-flat Donchian breakout, the repo's second
  research strategy and its first directional one. Entry on an N_entry-bar high, exit on a
  faster N_exit-bar low, both extrema computed over completed bars strictly before the
  current one. Filters (`ConsecutiveCloseFilter`, `VolatilityContractionFilter`,
  `TrendGateFilter`) and sizing (`FixedWeight`, `InverseVolatilityWeight`) are separate
  toggleable bricks behind `Protocol`s with declarative configs and factory registries, so
  a strategy rebuilds from the exact dict the registry hashes (D102). `n_exit > n_entry` is
  refused: the nesting is what makes entry/exit mutually exclusive on any bar.
- **`research/breakout_study.py` (D113, D114, D116)** — walk-forward harness
  (train 252 / test 63 / step 63) running each (symbol, variant, tier) as ONE continuous
  OOS backtest with a per-window parameter schedule (`ScheduledBreakout`) rather than
  chained windows; four crypto fee tiers built through the declarative cost-stack path;
  plateau surface, in-training-window grid selection, per-(symbol, tier) DSR whose pool is
  configurations rather than windows; report renderers.
- **`research/trade_diagnostics.py` (D112)** — position-episode reconstruction from engine
  fills: MFE/MAE, time-in-trade distribution, time-to-stop-out for losers, whipsaw rate,
  capture ratios, round-trip cost as a share of gross P&L, and rebalance-vs-signal cost
  split.
- **`data/fixtures/crypto_daily_2015_2025_raw.csv.gz` (D108)** + fetch script — BTC-USD and
  ETH-USD daily bars at a fixed 00:00 UTC boundary; 0 cleaning changes and 0 hard
  validation violations through the Step-7 pipeline.
- **`scripts/run_breakout_study.py`** → `BREAKOUT_RESULTS.md` + `data/breakout_study_summary.json`
  (offline, deterministic; 152 out-of-sample trials, 7,904 registry rows).
- **Tests:** `tests/golden/test_breakout_golden.py` (+ `.hand.txt`) — 9-bar scenario
  asserted line by line against hand arithmetic; `tests/property/test_breakout_invariants.py`
  — no-look-ahead under arbitrary future-bar perturbation (signal level and through the
  engine), hysteresis, cost application, fee monotonicity; `tests/unit/test_breakout.py`,
  `tests/unit/test_trade_diagnostics.py`, `tests/integration/test_breakout_study.py`.
  361 → 438 tests green (77 new).

### Changed
- `tests/unit/test_strategy_labels.py` (D117) — D38's label gate fired for the first time
  when `breakout.py` landed, exactly as D82 designed it to. The breakout module now carries
  an explicit directional / not-market-neutral / benchmarked-against-buy-and-hold label, and
  the gate greps for all three.
- `strategies/breakout.py`'s `EntryFilter` / `WeightSource` protocols declare `name` and
  `rebalance` as read-only properties, so frozen brick dataclasses type-conform — the same
  variance fix audit F20 applied to `Instrument.quote_currency`.

### Deferred
- **Volume-confirmation filter (D111)** — not built. `Bar` carries no volume and
  `DataView` hands strategies `Bar` objects; adding volume to the bar schema is a framework
  change with its own gate, and smuggling a volume series past `DataView` would open the
  look-ahead hole D32 exists to close. Recorded rather than worked around; no class exists
  claiming the capability.

### Fixed (audit remediation, 2026-07-14 — see AUDIT_REPORT.md and D98–D107)
- **DSR wiring (D98, the audit's one result-corrupting finding):** per-window Sharpes are
  now logged in daily (per-period) units matching the observed SR — the old code logged
  annualized values under the same name, inflating SR0 by √252 and forcing DSR toward 0
  regardless of the strategy; the trial pool is the study's 1×-cost rows only, undefined
  window Sharpes are omitted (loud at 1×), and capacity/gross levels skip the per-level
  DSR entirely (`compute_dsr=False`).
- **Silent failure modes made loud (D99):** duplicate bar timestamps raise in `align_bars`
  and hard-quarantine in the validator (was last-wins collapse); zero-overlap alignment
  raises in `run_backtest` (was a silently-empty result at starting cash); the pairs study
  asserts per-symbol bar grids match the aligned universe; dividends in a gap containing a
  split now pay on the share count held on their ex-date; cleaner volume indexing is
  bounds-guarded.
- Doc rot: validator docstring matched to its actual thresholds and the real XOP split
  date; strategy-module Kalman promise removed (cut per D97); loader duplication collapsed;
  `hello()` scaffolding removed; mypy 7 → 0 across `src/`.

### Added (audit remediation)
- `config/cost_stack.py` (D102) — the study's real cost stack is built from the same
  declarative dict logged to the TrialRegistry; `StudyConfig.to_dict()` covers every
  determining field (starting_cash and multipliers were missing) and `from_dict()` closes
  the study-level reproducibility loop, tested end to end.
- `StudyConfig.impact_calibration="train_window"` (D102) — per-window σ/ADV estimation from
  the train slice only (D44-compliant), alongside the documented full-sample default.
- `run_backtest(fill_timing="next_open")` (D103) — decisions fill at the next bar's open;
  hand-computed golden + property invariants; default "close" preserves every baseline.
- `run_backtest(enforce_pretrade=True)` (D101) — the previously-unwired pre-trade gate
  rejects breaching netted orders and rolls back the instrument's virtual orders.
- `BacktestResult.virtual_fills` / `final_virtual_positions` (D101) — D46's strategy-tagged
  fill stream at the result surface.
- Carry/event bricks declare their carry component and the engine consults
  `Instrument.carry_components()` (D100) — no behaviour change for equities.
- `deflated_sharpe_from_trials(include=...)` predicate with a stated units contract (D98).
- Property suite: signed positions, real OHLC bars, unconditional commission/carry shadow
  accountants, next-open invariants (D104).
- `scripts/run_convention_sensitivity.py` → `docs/results/convention_sensitivity.md`
  (D105) — the v2 configuration across {close, next-open} × {full-sample, train-window}.
- Conventions pinned by test/record: round-half-even share rounding, current-close carry
  marks, MC block length rationale (D106); written R3 deferrals for the margin lock,
  stop/limit fill menu, FX brick, IS/OOS ratio, and registry artifact policy (D107).

### Added
- Full documentation suite: per-decision ADR records under `docs/decisions/`, standing rules
  in `docs/RULES.md`, this changelog, `AITODO.md`, top-level `README.md`, `.gitignore`.
- `PHILOSOPHY.md` — five guiding pillars extracted from the pattern across the existing 49
  decisions, sitting above `docs/RULES.md` and `docs/decisions/` as the reference point for
  any future decision.
- Local git repository initialized.
- Project scaffolding: `uv`-managed src-layout Python package, pytest + hypothesis test
  stack (D50).
- `backtest_framework.simulator.fills.stop_fill_price` — gap-through-stop fills at the
  bar's open instead of the stop price (D10).
- `backtest_framework.simulator.carry` — `accrue_carry`/`accrue_carry_between_bars`, carry
  cost accrual on the calendar-day gap between bar timestamps rather than bar count (D33),
  using an ACT/365 day-count convention (D51).
- `backtest_framework.registry.trial_registry.TrialRegistry` — SQLite-backed, append-only
  trial log with a deterministic config+snapshot+seed hash (D20).
- Step 1 of `VERIFICATION_SCHEME.md` — gate passed (20/20 tests: golden-master, property,
  unit).
- `backtest_framework.config.factory.FactoryRegistry`/`ConfigError` — generic type-keyed
  declarative-config factory pattern, fails loudly naming the bad key (D35, D52).
- `backtest_framework.config.sim_config.SimConfig` validator/builder, plus two
  demonstration model configs (`carry_model.CarryModel`, `fill_model.FillModel`) wrapping
  Step 1's carry accrual and stop-fill behaviour behind the factory pattern.
- Step 2 of `VERIFICATION_SCHEME.md` — gate passed (35/35 tests total, 15 new), including
  the full reproducibility loop (config → hash → registry → reload → re-run). This closes
  the Phase A milestone in `DEVELOPMENT_TIMETABLE.md`.
- `backtest_framework.instruments` — `Instrument` protocol, `Equity`, `OptionStub` (D12,
  D16). `docs/options_extension.md` added as a stub so `OptionStub`'s
  `NotImplementedError` points at a real path.
- `backtest_framework.costs` — `CostStack` (D1) plus `TradeCostBrick`/`CarryCostBrick`
  protocols (D2) and three toy bricks: `FlatCommission`, `PercentOfNotionalSpread`,
  `FlatRateCarry`.
- `backtest_framework.pipeline.sizing` — `Sizer`, `TargetWeight`, `Order`, `net_orders`,
  `apply_virtual_orders`: the signal → target weight → orders pipeline (D27), with
  cross-strategy netting and per-strategy virtual books (D46).
- Step 3 of `VERIFICATION_SCHEME.md` — gate passed (60/60 tests total, 25 new). The
  "refactor regression" gate was reinterpreted for this project's greenfield conditions
  (D53) and satisfied with a new hand-computed 3-bar golden-master scenario
  (`test_step3_refactor_regression.py`), now the frozen baseline for future refactors of
  CostStack/Instrument/pipeline.
- `backtest_framework.engine.dataview` — `DataView`, `LookAheadError`,
  `build_data_view()`: a structural look-ahead guard (D32) built so future bars are
  never stored in the object at all, not merely access-gated (D56).
- `backtest_framework.engine.risk` — `RiskLimits`, `RiskViolation`, `RiskMonitor`,
  `gross_exposure()`: per-bar portfolio-level risk checks plus a pre-trade gate sharing
  the same limit logic (D30, D57).
- `backtest_framework.engine.allocator` — `Allocator` protocol, `ConstantSplitAllocator`:
  a bare-bones capital-allocation stand-in (D31), wired into `pipeline.sizing.Sizer`'s
  `capital_by_strategy` input (D58).
- Step 4 of `VERIFICATION_SCHEME.md` — gate passed (78/78 tests total, 18 new). **Phase B
  complete** (`DEVELOPMENT_TIMETABLE.md`) — both Step 3 and Step 4 gates pass without
  needing the pre-committed slip rule.
- First production dependencies: `yfinance`, `pandas` (`pyproject.toml` was
  `dependencies = []` until now).
- `backtest_framework.data` — `TimestampedBar` (D60), `DataSource` protocol (D18),
  `EquityDataSource` (a deliberately unhardened yfinance passthrough — no snapshotting
  D24, cleaning D25, or sanity gate D26 yet; see D59).
- `backtest_framework.engine.portfolio.PortfolioState` — broker-facing cash/positions
  and NAV (D43's short-sale accounting falls out naturally from signed notional, no
  special-casing needed).
- `backtest_framework.engine.strategy` — `Strategy` protocol, `ScheduledWeightStrategy`
  (a toy reference strategy, analogous to Step 3's toy cost bricks).
- `backtest_framework.engine.backtest.run_backtest` — the production loop generalizing
  Step 3's test-only `run_mini_backtest`: wires DataView, Strategy, Allocator, Sizer,
  CostStack, PortfolioState, and (optionally) RiskMonitor and TrialRegistry together
  per bar. Capital is reallocated from current NAV every bar (D61). Risk violations are
  recorded, not enforced (D62).
- `pytest` marker `live_fetch`, excluded by default via `addopts` — matches
  `VERIFICATION_SCHEME.md`'s own cross-cutting gate ("CI runs everything offline...
  live-fetch tests are excluded by marker").
- Minimal data-source + engine-loop chunk (not a numbered `VERIFICATION_SCHEME.md`
  step; inserted ahead of Step 5 to unblock it — D59) — gate: a `ScheduledWeightStrategy`
  run through `run_backtest` reproduces Step 3's frozen golden-master NAV curve exactly
  (95/95 tests total, 17 new, offline by default).
- `backtest_framework.data.alignment` — `AlignedBar`, `align_bars()`: inner-join
  multi-instrument bar alignment (D45, D63). A bar missing on one leg drops that
  timestamp for every leg; carry accrues correctly across the resulting gap with no
  special-case code.
- Multi-instrument alignment chunk (D45) — gate: a real long-XLE/short-XOP pair runs
  end-to-end through `run_backtest` (104/104 tests total, 9 new, offline by default;
  the XLE/XOP run is `live_fetch`-marked).
- `backtest_framework.costs.equity_bricks` — the real equity cost bricks (Step 5):
  `IBKRCommission` (Fixed schedule: $0.005/sh, $1 min, 1% cap, cap overrides min —
  D4/D65), `SqrtImpact` (square-root impact law, fraction ∝ √Q / dollars ∝ Q^1.5,
  static per-symbol σ/ADV params, loud errors on missing/zero ADV — D3/D66),
  `MarginInterest` (accrues on max(gross exposure − NAV, 0) — D5/D67). Toy bricks
  remain alongside as simple/sensitivity bricks.
- `CostStack.portfolio_carry_bricks` — a third slot for portfolio-level carry, charged
  once per bar on an engine-computed base, with start-of-bar snapshot semantics in
  `run_backtest` (D67). Additive; existing stacks and the frozen D53 baseline are
  unchanged (re-run and confirmed).
- Step 5 of `VERIFICATION_SCHEME.md` — gate passed (134/134 tests total, 30 new):
  X (13-row IBKR schedule table; live-page anchoring 403-blocked, manual check
  tracked in `AITODO.md`), G (margin interest weekend case tied to D33's arithmetic +
  only-when-positive + engine integration run), U (sqrt impact √2/2√2 scalings +
  loud-error paths).
- `backtest_framework.costs.scaling.scaled_cost_stack` — per-brick cost-multiplier
  scaling across all three CostStack slots (D8, D68).
- `backtest_framework.engine.sweep` — `run_cost_sweep` (strategy-factory API, optional
  per-multiplier TrialRegistry logging), `render_sweep_table`, `max_drawdown` (D68).
- `backtest_framework.strategies.zscore_pairs.ZScorePairsStrategy` — the first
  non-toy strategy: fixed 1:1 log-spread z-score mean reversion with hysteresis,
  previous-bar estimation windows, warm-up/zero-std self-guards (D69).
- `backtest_framework.costs.equity_bricks.BorrowFee` — per-leg carry, shorts pay /
  longs free (D71).
- `backtest_framework.data.csv_fixture` — save/load committed CSV fixtures;
  `data/fixtures/xle_xop_daily_2015_2024.csv` + `.meta.json` committed as the
  pre-Step-7 frozen snapshot (D70). `scripts/fetch_fixture.py` (one-time network),
  `scripts/run_first_result.py` (offline, deterministic).
- **`docs/results/first_real_number.md` — THE FIRST REAL NUMBER (Phase C milestone,
  R1's gate):** XLE/XOP z-score pairs 2015–2024, full real cost stack, sweep
  +13.21% at 0× → −22.70% at 1× → −76.43% at 4×, monotonic; caveats stated.
- Step 6 of `VERIFICATION_SCHEME.md` — gate passed (163/163 tests total, 29 new):
  0× ≡ zero-cost and monotonicity asserted on both a penny-exact synthetic scenario
  and the real fixture, offline and repeatable.
- `backtest_framework.data.snapshot_store.SnapshotStore` — content-addressed frozen
  snapshots (sha256 payload ids), checksum-verified loads, quarantine refusal (D24,
  D72).
- `backtest_framework.data.cleaner` — drop-and-report ruleset `clean-v1` with
  `CleaningReport` attached to snapshot meta (D25, D73).
- `backtest_framework.data.validator` — sanity gate with hard-vs-warning findings,
  observed-data-calibrated move thresholds, frame-robust split awareness (D26, D74).
- `backtest_framework.data.corporate_actions` — dividends/splits tables, two-frame
  conversions (`as_traded_from_adjusted`, `as_declared_dividends`, `split_adjusted`),
  events JSON persistence (D6, D75).
- `EventFlowBrick` protocol + `DividendFlow` brick + `CostStack.event_flow_bricks`
  (4th slot, unscaled by the D8 sweep — flows are transfers, not frictions);
  `run_backtest` gains `splits_by_instrument` (position scaling on ex-dates) and
  `view_bars_by_instrument` (signal/execution series separation) (D75).
- `EquityDataSource.get_raw_history` (additive); committed raw fixture
  `data/fixtures/xle_xop_daily_2015_2024_raw.csv` + events JSON;
  `scripts/fetch_fixture_v2.py`, `scripts/run_first_result_v2.py`.
- **`docs/results/first_real_number_v2.md`** — the first number re-run through the
  hardened path (+21.74% at 0× / −18.56% at 1× / −76.55% at 4×; conclusion
  unchanged); v1 preserved as the historical milestone (D76).
- Step 7 of `VERIFICATION_SCHEME.md` — gate passed (205/205 tests total, 42 new):
  snapshot checksum/restatement/quarantine U-gates, cleaner defect-injection gate,
  validator gate, XLE ex-date dividend G-gate (long credited/short debited, exact),
  pre-split XOP commission G-gate (as-traded vs adjusted differs by hand-computed
  $15.00 on a $32k order), split NAV-continuity, D45 no-fills assertion.

- `BacktestResult.fills` and `.cash_curve` — per-fill and per-bar-cash
  instrumentation (D77, additive).
- **THE golden master** (`tests/golden/test_the_golden_master.py` + `.hand.txt`, D39/
  D77): five-bar short-side scenario asserting every fill, commission, carry accrual,
  the dividend debit, and cash/NAV per bar against an independent calculator.
- Property invariant suite (`tests/property/test_simulator_invariants.py`, D40/D78):
  8 derandomized hypothesis invariants — cash ≥ 0 absent margin, fills within bar
  range, exact fill/position reconciliation, shadow-accountant leak tests,
  fresh-state guarantee, determinism hash.
- Cross-engine reconciliation (`tests/integration/test_cross_engine.py` +
  `docs/verification/cross_engine_reconciliation.md`, D41/D79): our engine vs
  vectorbt 1.1.0 on identical inputs — **penny-exact** (1,370 trades both sides,
  identical final value, 1.3e-12 max relative curve divergence). New dev dependency:
  `vectorbt`.
- Step 8 of `VERIFICATION_SCHEME.md` — gate passed (218/218 tests total, 13 new).
  **The simulator is anchored to references we didn't write** (Phase D milestone,
  `DEVELOPMENT_TIMETABLE.md`).
- `backtest_framework.analytics` — the analytics layer, honest by construction:
  `metrics` (Sharpe/Sortino with REQUIRED rf and periods args, geometric rf, stated
  ±inf conventions; `realised_beta`; `max_drawdown` relocated from `engine.sweep` —
  D80), `tail_risk` (VaR/CVaR gated on ≥30 tail observations, explicit
  insufficient-data results — D36/D81), `monte_carlo` (seeded block bootstrap,
  n=10,000 default, required seed — D34/D81), `tearsheet` (renders the literal
  "insufficient data (n=X, need ≥Y)" string, rf stated in the Sharpe row, D37's ≈0
  beta note).
- Step 9 X-gate: exact agreement with quantstats 0.0.81 on Sharpe (rf=0 and rf=4%),
  Sortino, and max drawdown (D83). New dev dependency: `quantstats`; `numpy`
  promoted to an explicit production dependency.
- D38's label gate reinterpreted (D82): grep-test enforces honest thesis labels on
  the strategies that exist and fails on unregistered strategy modules.
- Step 9 of `VERIFICATION_SCHEME.md` — gate passed (248/248 tests total, 30 new).
- `docs/options_extension.md` rewritten from placeholder to the real scoping decision
  (D16, D84): six hard problems, Lego audit, verification gates if built, trigger
  conditions. Doc-rot grep-test added alongside the existing OptionStub gates.
- Step 11 of `VERIFICATION_SCHEME.md` — gate passed (the stub's U-gate has been green
  since Step 3; the write-up was the remaining deliverable). 249/249 tests.
- `backtest_framework.validation` — the research-integrity layer:
  `walk_forward` (fitters receive DataViews built from training slices only — the
  D22/D28 guarded accessor, D85), `pair_selection` (Gatev-distance top-N with the
  multiplicity count returned for registry logging, D29), `dsr` (PSR/SR0/DSR with N
  and V[{SRn}] pulled from the TrialRegistry, stdlib normal functions, D86),
  `synthetic` (random-walk-spread null pairs, D87).
- `analytics.monte_carlo.block_bootstrap_paths` exposed (additive; seeded output
  byte-identical).
- Step 12 gates: DSR reproduces the Bailey & López de Prado worked example
  (N=100 → 0.9004, N=46 → 0.9505, N=88-normal → the 95% boundary; parameter recovery
  method in D86); inverting-pair walk-forward I-gate; 200-series noise-universe
  multiplicity P-gate (n_pairs_tested = 19,900 logged and read back); zero-edge
  synthetic nulls earn ≈ 0 ("stop everything" not triggered); shuffle-vs-block
  autocorrelation demonstration.
- Step 12 of `VERIFICATION_SCHEME.md` — gate passed (260/260 tests total, 13 new).
  **All in-scope verification-scheme steps are complete. The framework can say
  "no edge" and be believed** (`DEVELOPMENT_TIMETABLE.md` Phase F milestone).
- Transparent `.gz` support in `data.csv_fixture` (D88);
  `data/fixtures/universe_daily_2015_2024_raw.csv.gz` committed — 57 ETFs, 2015–2024
  raw + 2,285 dividends + 14 splits (`scripts/fetch_universe.py`).
- `costs.calibration.calibrate_impact_params` — automated σ/ADV for SqrtImpact
  (full-sample, D66 caveat carried).
- `backtest_framework.research` — the Phase G study package (framework frozen;
  research versions per study): `pairs_study.run_pairs_study` — walk-forward Gatev
  top-N selection, one multi-strategy netted run per (window, multiplier), warm-up
  prefixes, NAV-chained windows, per-trial registry logging, registry-fed DSR
  (D89/D90). `scripts/run_pairs_study.py` produces the artifact offline.
- **`docs/results/pairs_study_v1.md` — THE FIRST PHASE G RESEARCH RESULT**: 57-ETF
  universe, 35 OOS windows, 1,596 pairs scored per window; gross +3.45%, −13.01% at
  real costs, monotone sweep, **DSR = 0.0000** with the multiplicity caveat stated.
  The framework's milestone claim — saying "no edge" believably — exercised on real
  data. (273/273 tests total, 13 new.)
- `docs/TUTORIAL.md` — the start-to-output usage guide; every `# runnable` example
  block is executed verbatim by `tests/integration/test_tutorial.py` (D91), so the
  tutorial breaks CI rather than rotting. Linked from README. (275/275 tests.)
- `research/cointegration.py` — Engle-Granger β + residuals, ADF t-statistic
  (statistic only, rank-don't-threshold per D29; tied to statsmodels at 1e-9 as a
  dev-dep X-anchor, D93), and `CointegrationSelector` (Gatev prefilter → β coherence
  window → ADF rank, D92). `run_pairs_study` gains an optional `selector` (v1
  default preserved). New dev dependency: `statsmodels`.
- **`docs/results/pairs_study_v2.md` — study v2**: selection is the only change from
  v1; gross +3.45% → **+19.03%**, profitable at 0.5× costs (+5.70%), still −6.43%
  at full retail costs, DSR = 0.0000 with the program-level multiplicity note. The
  "edge exists but doesn't clear retail frictions" thesis, measured. (281/281
  tests, 8 new.)
- `research/beta_zscore.py` — `BetaHedgedZScoreStrategy` (D94): trades the
  train-window Engle-Granger β (spread = ln A − β·ln B, legs in the β ratio),
  weights normalized to constant gross (w_A = 2w/(1+β), w_B = 2wβ/(1+β)); β = 1
  reduces exactly to `ZScorePairsStrategy` — tested as a target-level identity AND
  a whole-study equity-curve identity. `run_pairs_study` gains an optional
  `strategy_factory(pair, strategy_id, config, details)` hook (v1/v2 default
  preserved; called per window/multiplier/pair; receives the pair's
  selector-details entry carrying its fitted β).
- **`docs/results/pairs_study_v3.md` — study v3**: trading is the only change from
  v2; the β hedge **hurt** — gross +19.03% → **+6.12%**, 1× costs −6.43% →
  **−16.53%**, DSR = 0.0000. Train-window β carried out-of-sample imports more
  estimation noise than hedge benefit on a selector-coherent (β ≈ 1) universe; the
  1:1 hedge stands. (288/288 tests, 7 new.)
- `research/capacity.py` (D95): recording cost-stack wrappers (D68 delegation
  pattern, accumulate instead of multiply) feeding a `CostLedger` — per-brick
  friction attribution plus per-symbol max |Q| for participation reporting; the
  recorder returns inner values unchanged (transparency is a tested whole-study
  identity). `run_capacity_study` runs the v2 study per AUM level at real
  unscaled costs; `run_pairs_study` gains an optional `base_stack` hook
  (None-default, v1/v2/v3 byte-identical).
- **`docs/results/capacity_analysis.md` — the capacity analysis**: v2's study at
  nine AUM levels, $10k–$100M. **No level clears real costs**: the hump lands as
  predicted (commission minimums small, √-impact large; optimum $300k at
  −5.77%/9yr) but ≈+2.01%/yr of gross edge faces 2.68%/yr of drag at the optimum,
  half of it the scale-invariant floor of a ~200% gross book. Cross-checks: the
  $100k row reproduces v2's −6.43% exactly; $100M gross +19.04% vs v2's +19.03%.
  (295/295 tests, 7 new.)
- `research/gross_sweep.py` (D96): `run_gross_sweep` — one capacity study per
  leg_weight (thin composition), with net-return / margin-drag / total-drag
  matrix renderers; `run_capacity_study` gains `trial_prefix` (default
  "capacity" preserves the D95 artifact's trial ids).
- **`docs/results/gross_exposure_study.md` — the gross exposure study**:
  leg_weight {0.25, 0.5, 0.75, 1.0} × AUM {$100k…$10M}, real unscaled costs.
  The margin threshold collapses as predicted (0.866%/yr at lw 1 → 0 below
  gross ≤ NAV) and **five low-gross cells clear absolute costs** (best lw 0.5 @
  $300k, +0.12%/yr vs +1.03%/yr gross) — **but none clear the 4% risk-free
  hurdle** (best cell Sharpe −1.61; idle-cash-interest caveat stated both
  ways). The two-sided headline: at low gross the edge pays for its own
  implementation, not for the capital it occupies. (299/299 tests, 4 new.)
- **`docs/writeup.md` — the Phase G writeup skeleton (D97)**: the portfolio
  document; methodology-first, ten sections + appendices, all five studies'
  headline numbers final and quoted from committed artifacts, `[TODO prose]`
  markers for narrative polish only. `tests/unit/test_writeup.py` anchors 24
  (number, source-artifact) pairs so a re-run study that moves a headline
  fails CI, asserts required sections, enforces the prose-only-TODO rule, and
  checks the README link. README brought current (stale "pre-implementation"
  status replaced; writeup is the lead link). (326/326 tests, 27 new.)

### Changed
- Bar/event timestamps are normalized to naive exchange-local wall time at the data
  boundary (D75) — daily-bar identity is the exchange-local date, and D33's
  calendar-day carry must not be DST-sensitive.
- `config.carry_model`'s factory now builds `costs.bricks.FlatRateCarry` instead of the
  retired `CarryModel` demonstration class, per that class's own docstring (D54). No
  change to `SimConfig`'s shape or to Step 2's four passing gates.
- **Breaking**: `Strategy.generate_targets` now takes `Mapping[str, DataView]` instead
  of a single `DataView`; `ScheduledWeightStrategy` now takes `weights_by_instrument`
  instead of `instrument_id`/`weight`; `run_backtest` now takes `bars_by_instrument`
  instead of `bars`/`instrument_id`. Single-instrument is the N=1 case throughout
  (D64). The Step 3/D53 golden-master reproduction test was migrated and re-verified
  to produce identical numbers under the new signatures.

<!--
Template for future entries:

## [x.y.z] - YYYY-MM-DD

### Added
- New feature X (see D50)

### Changed
- Behaviour of Y (see D51)

### Fixed
- Bug in Z

### Deprecated / Removed
-->
