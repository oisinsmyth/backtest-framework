# Changelog

All notable changes to the framework's code are logged here, in
[Keep a Changelog](https://keepachangelog.com/) style. This tracks *what shipped and when* —
the *why* behind each change belongs in [`docs/decisions/`](docs/decisions/README.md), not here.

No tagged releases yet. Entries accumulate under **Unreleased** until the first tagged
version (likely at the Phase C "first real number" milestone, see
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)).

## [Unreleased]

### Added (Alpha Vantage intraday provider, 2026-08-27)
- `scripts/fetch_etf_intraday.py` — 15-minute bars for the 57-ETF universe, 2018-01 to
  2026-08, one call per `(symbol, month)`. Resumable, cached, paced at 66/min against a
  75/min tier ceiling. Raw cache is not committed (D191); only the derived fixture is.
- `docs/alpha_vantage_api.md` — the provider reference, with **every claim tagged
  `[DOC]` / `[MEASURED]` / `[INFER]`**, because the documentation is thin on exactly the
  points a study depends on.

### Why (Alpha Vantage)
- yfinance serves **60 days of 15m** (D160). Impulse MACD at `(136, 36)` needs **4,049
  bars of warm-up alone** — short by a factor of three *before* the strategy starts. Alpha
  Vantage's `month=YYYY-MM` slices reach back to 2000-01, which is what makes an intraday
  ETF study possible at all.

### Measured before spending ~5,900 requests
- **Volume is CONSOLIDATED** — SPY median session 66,595,182 shares against a ~70–90M
  consolidated ADV. Undocumented, and the one finding that could have killed the study.
- Timestamps mark the interval's **OPEN**, so a bar stamped `t` is not complete until
  `t+15m` — a look-ahead hazard, now recorded in the fixture meta.
- Errors arrive as **HTTP 200** with an `Error Message` body; success must be decided
  structurally or error bodies land in the fixture.
- `outputsize=full` is **mandatory** with `month`; the default returns 100 bars silently.
- **Fetch extended hours, build regular hours only.** Extended bars exist only where
  something traded (AGG 27–35/session, ragged; RTH exactly 26 every session), so an
  extended-hours fixture would put a **liquidity-correlated** difference in bar counts into
  a **volume** study.

### Fixed
- Corrects an inference that `adjusted=true` dividend-adjusts **volume**. Measured: volume
  is byte-identical either way (ratio 1.000000); only prices adjust. `adjusted=false` is
  still right — adjusted prices are *back-adjusted* and drift with every dividend, which
  breaks D24's immutable-snapshot rule.

### Added (D230 — the bootstrap sweep, 2026-08-27)
- `scripts/run_bootstrap_sweep.py` + `data/bootstrap_sweep_summary.json` +
  `BOOTSTRAP_SWEEP_RESULTS.md` + `tests/unit/test_bootstrap_sweep.py` (18).
- A **reproduction gate**: every point estimate must match its committed artifact to 1e-9
  or the sweep stops and reports that instead.

### Result (D230) — zero of twenty-four clear the hurdle as claimed
- **8 of 24 cleared as the runners scored it. 0 clear as the records claimed it.
  All 24 intervals contain zero.** Reproduction clean.
- **The subtler error runs the other way**: D218's `I2-I3` (-0.016 to -0.032) and `I1-C`
  (~0) were read as evidence of *absence*, on intervals 3-6x and ~±0.3 wide. An interval
  that wide around zero is evidence of nothing.
- 12 of 24 have intervals wider than 5x their point estimate; the extremes are 180.8x
  and 63.6x.

### Fixed (D230)
- **Corrects D229 and the conversation.** D229 called D218's cross-construction argument
  "untouched"; it is not. The `I1-C` leg is what the sweep dissolves, and "independent"
  overstates it — D218's span is a *subset* of D217's on the same 57 ETFs. What survives is
  corroboration, not independent replication. Recorded as an addendum on D229 too, so that
  record does not read as sound standalone.

### Added (D229 — the jerk rung, 2026-08-27)
- `scripts/run_jerk_rung.py` + `data/jerk_rung_summary.json` + `JERK_RUNG_RESULTS.md` +
  `tests/unit/test_jerk_rung.py` (17).
- **A paired block bootstrap**, which the repo did not have. Both rungs recomputed on
  identical resampled dates, block 21, 1,000 replications.

### Result (D229) — the derivative ladder closes at I1
- **Jerk does not beat acceleration.** `I0 - I1 = -0.218`, hurdle A fails in all four cells.
- **P1-P5 all confirmed**, and a clean sweep in a study that predicted its own failure is
  the easy case; only P4 carried information.
- **I0 beats the LEVEL rung** (`+0.310`) while losing to acceleration — both derivative
  rungs beat level, so the ladder is not monotone.
- The pre-registration's free measurements landed exactly: exposure 48.5% (48.53% predicted),
  turnover 16,421 (16,422 predicted).

### Fixed (D229)
- **D217 and D218 both state hurdle A as "above the paired bootstrap's p95" and NEITHER
  RUNNER EVER RAN ONE.** The leg now exists, and **D218's headline fails it in all four
  cells**: `I1 - I2 = +0.628` has a 90% interval of `-0.133` to `+1.325`, containing zero.
  Fairly stated, this attacks the reported *certainty*, not the point estimate, and leaves
  D218's cross-construction replication argument untouched.
- **Third appearance of the `sort_keys` idempotency defect** (D220, D222): `--report-only`
  emitted the same content in a different row order. Pinned by an explicit `CELL_ORDER`.

### Added (D228 — the filter search, 2026-08-27)
- `scripts/run_filter_search.py` + `data/filter_search_summary.json` +
  `FILTER_SEARCH_RESULTS.md` + `tests/unit/test_filter_search.py` (23).
- The **best-of-search null**: the identical eight-candidate search run over rotated filter
  signals, one offset vector per replication reused across all candidates so cross-candidate
  correlation survives. 1,000 replications, 73.5 s.

### Result (D228) — the filter line on the acceleration arm is closed
- **Nothing clears anything.** Best candidate +0.023 excess Sharpe against a measured floor
  of **+0.104**, barely above the null's *median* of +0.014. Not one of eight clears hurdle P.
- **Both gates also fail hurdle E** — 16 and 11 entries per symbol against 30 required.
- **Sizing dominates gating on both matched pairs**: S3 beats G1 by 15.33 pp of money at a
  0.060 Sharpe difference; S4 beats G2 on both metrics.
- **The analytic floor was never the problem.** At matched N the formula (+0.099) and the
  measured floor (+0.104) agree to within 5%. What was wrong was `var_trials` and inherited N.
- **The mechanism, measured**: across candidates spanning 24%–100% exposure, money delta
  against exposure delta gives **r = +0.823**, slope 0.58 pp per pp. Seven studies of "better
  Sharpe, less money" explained rather than repeated.

### Fixed (D228)
- **rf on a long-flat book is charged on the EXPOSED FRACTION**, not the whole book. The arm's
  excess Sharpe is **+0.566**, not the +0.354 quoted in conversation; buy-and-hold is +0.231.
- Recorded that D218's headline **+0.658 is price-only** while the money figures beside it are
  dividend-adjusted — two bases mixed in one sentence. The dividend-adjusted Sharpe is +0.793.

### Added (D226 — the gate on 57 ETFs at 15m, 2026-08-27)
- `scripts/fetch_etf_intraday.py` gains `--actions` (SPLITS + DIVIDENDS) and split
  adjustment; `data/fixtures/etf_intraday_15m_raw*` — a purpose-built 57-ETF 15-minute
  fixture, 3.19M rows, 7.94 live years, zero zero-volume bars.
- `scripts/run_etf_intraday_gate.py` + `data/etf_intraday_gate_summary.json` +
  `ETF_INTRADAY_RESULTS.md` + `tests/unit/test_etf_intraday_fixture.py` (20).

### Result (D226) — the volume regime gate is closed
- **The spike moved.** The gate clears H at **one window of ten (96 bars)**, and D224's
  committed **200-bar window lands at the 45th percentile** here. Two spiky profiles with
  spikes in different places is a fitted parameter, not a discovered one.
- **Three cells cleared the multiplicity floor** — a first — but because 57 instruments
  tighten the null (sd 0.082 vs crypto's 0.24), dropping the floor from +0.88 to +0.35 at a
  *larger* look count. D219's amendment, demonstrated.
- **Nothing survives**: window 96 beats the parent on Sharpe and loses on money.
- **The dividend fetch changed the verdict**: price-only the gate ties its parent (+15.5%
  each); dividend-adjusted it loses by 4.6 points.

### Fixed (D226)
- **Twelve unadjusted splits** in the new fixture, worst appearing as a **+1,772% single
  15-minute bar**. Now back-adjusted in prices *and* volumes (opposite directions —
  `corporate_actions.split_adjusted` does not touch volume, and this is a volume study).
  Five of the twelve existed nowhere in this repo.
- An early runner draft declared `VERDICT_COUNT = 3879`, D225's *crypto* arithmetic applied
  to an ETF study. Corrected to 10 / 78 / 45,819.

### Added (D225 — the gate at 1h, 2026-08-27)
- `scripts/run_gate_1h_replication.py` + `data/gate_1h_summary.json`. Reuses D224's scoring
  path verbatim; only the position builder is local, because `build_positions` hard-reads
  its window constants.

### Result (D225)
- **The volume gate replicates at 1h.** Δ vs parent **+0.635** (BTC) and **+0.558** (ETH)
  against 15m's +0.489 / +0.590, with hurdle H at 99.5/100 and 98.5/98.8. It is **not** an
  artifact of the 15m sampling rate, and it beats the mechanical benefit of trading less by
  about **6×**.
- **Its working window is one point wide.** 50h is the only positive-net window on BTC out
  of ten; both neighbours are negative; and **at 200h the identical construction inverts
  into a significant anti-signal** (0.5th percentile of its own null).
- **Two claims separated:** the *signal* is scale-free in bars (D221); the *gate* is **not**
  scale-free in wall-clock — it is window-critical.
- Nothing clears the verdict floor. ETH clears the fresh-look floor by 0.084 — D214's
  pattern for the second study running.

### Fixed (D225)
- **Recorded after the run**, which departs from this programme's practice and is disclosed
  in the record rather than glossed. The replication was confirmatory of a pre-registered
  claim; the **40-cell window sweep was an unregistered search** and is counted as such.
  The 50-hour window was clean when D224 used it and **is not clean now**.
- Corrects a subagent claim: the window-response curve agreeing across the 15m and 1h grids
  is a *mathematical consequence* of D221's invariance (the 1h series is resampled from the
  same bars), so it validates the implementation and is silent on whether 50h is special.

### Added (D223/D224 — the volume-regime gate and the assembled strategy, 2026-08-27)
- **D223** pre-registers the volume-regime hypothesis and measures its two premises.
  Volume/volatility holds emphatically (top quintile has **4.5x** the mean absolute move);
  the signal-to-noise refinement does **not** — the variance ratio falls from **1.35 to
  0.67** across volume quintiles, so quiet markets trend and loud markets revert.
- **D224** + `scripts/run_assembled_strategy.py` + `data/assembled_strategy_summary.json`
  + `ASSEMBLED_RESULTS.md` + `tests/unit/test_assembled_strategy.py` (14). Run as a
  **2x2 factorial**, not a stack, so each component's contribution and their interaction
  are separable.

### Result (D224)
- **The volume gate is the first thing this programme has produced that beats its own
  matched-count random null** — 96th/96th percentile on BTC, 100th/100th on ETH. It takes
  BTC from -0.284 to **+0.205** net Sharpe and ETH from -0.006 to **+0.584**, deltas above
  the pre-stated MDE of 0.18.
- **It still fails the multiplicity floor** (+0.880 / +0.923 at 3,833 looks). ETH clears the
  *fresh-look* floor and fails the verdict one — D214's pattern exactly.
- The **2-ATR trailing stop is catastrophic**: it stopped out **98%** of trades, cut median
  hold 63 -> 7 bars and cost 2.0-2.9 Sharpe.
- The **interaction is strongly negative** (-2.561, -1.568), exactly as D223's variance-ratio
  census predicted. Running the stack whole would have shown a bad number and taught nothing.

### Fixed (D224)
- **A look-ahead defect, caught by an implausible number.** Zeroing the position on the bar
  the stop triggered let the book escape the entire adverse move, inflating `C_stop` to
  gross **+4.197**. The stop bar is now a held bar earning `log(fill / previous close)`.
- **The fill now uses `simulator.fills.stop_fill_price` (D10)** rather than a restatement —
  the repo already encoded "a gapped stop fills at the open", and reimplementing it was
  D212 again.
- **`var_trials` now comes from the simulated null, not from the study's own cells.** D219's
  amendment predicted the inflation; here it is extreme, with `C_stop`'s -3.17 putting the
  floor at an unusable **+4.944**. Every future study should estimate it from its null.
- Hurdle G was **missing from D224's pre-registered hurdle list** and was added post hoc —
  defensible only because it made the result worse, and disclosed rather than absorbed.

### Added (D222 — the scaling ladder, 2026-08-27)
- `scripts/run_scaling_ladder.py` + `data/scaling_ladder_summary.json` +
  `SCALING_RESULTS.md` + `tests/unit/test_scaling_ladder.py` (12). Reuses D221's arm,
  annualisation and Sharpe by import rather than restating them (D212).
- A **paired block bootstrap** on the shared daily grid — both arms recomputed on the same
  resampled index set, so the pairing survives the resample.

### Result (D222)
- **The fine-bar residual D221 left is noise.** Delta(k) goes up, down, then sideways:
  BTC +0.155 / -0.124 / +0.012 and ETH +0.148 / -0.087 / -0.120 across k = 4 / 32 / 96.
  Negative in 3 of 6 cells, no ordering by k, and **all six bootstrap intervals straddle
  zero** (widths 0.36-0.50 against deltas of 0.01-0.16).
- **The cleanest proof needs no statistics:** the same Delta(4) measures +0.054 on D221's
  8.3 years and +0.155 here on 5.6. A statistic that moves 0.10 when you change the start
  date is not measuring a property of the estimator.
- **Strengthens D221.** At k = 96 the 15m arm decides 96x more often than the daily arm and
  still trades the same 8-9 round trips a year: **turnover is set by the window, not the
  bar rate** — as signal already was.
- The verdict is **"not detectable here"**, not "does not exist": resolving a 0.05 effect
  needs ~19x the independent sample, about 100 symbol-years against the ~11 available.

### Fixed (D222)
- The shared-span gate demanded identical start timestamps across configs, which is
  impossible — a daily bar can only begin at 00:00 UTC and an 8h bar at 00/08/16:00. It
  fired on the first run, **wrong in the safe direction**: it refused to publish rather
  than publishing a misaligned comparison. Rewritten as a bounded spread (all starts agree
  to within one coarse bar) and pinned by a test that checks it still rejects a genuinely
  misaligned ladder.

### Added (D221 — sampling invariance, 2026-08-27)
- `scripts/run_sampling_invariance.py` + `data/sampling_invariance_summary.json` +
  `SAMPLING_RESULTS.md` + `tests/unit/test_sampling_invariance.py` (13). The 1h series is
  exact OHLCV aggregation of the 15m source (D161) on a **shared calendar**, so a gap
  between the two is the sampling rate and nothing else.

### Result (D221)
- **Invariance holds. The window is the variable; the sampling rate is not.** 15m with x4
  parameters matches 1h with defaults on every symbol — deltas +0.054, +0.080, -0.103,
  -0.149 — with hourly return streams correlating at **0.94-0.96**.
- **The control carries it:** the same indicator on the same 15m bars with an *unmatched*
  window correlates at only **0.50** and loses up to 4.183 Sharpe.
- Round trips are set by the window too: ~225/yr matched on either bar rate, ~950
  unmatched. The cost problem and the signal problem had one cause.
- **Nothing is tradeable**, as pre-committed. Every matched config is negative at
  `taker_40bp`; the sole positive net cell is BTG, the least reliable series in the study.

### Fixed (D221)
- **Corrects the earlier 15m screen.** It reported gross -0.400 on BTC and concluded the
  signal was dead at 15m. That ran the default `(34, 9)` on 15m bars — an 8-hour channel
  against the 1h version's 33-hour one — so it compared two indicators and reported it as a
  comparison between two timeframes. Matching the window moves BTC from -0.298 to **+0.735
  on the same bars**. The screen's cost arithmetic stands; its signal conclusion does not.
- Records that `crypto_intraday_1h_raw`, the repo's only **native** 1h crypto fixture, is
  **50.4% zero-volume bars** — the cleaner drops 17,520, leaving an irregular ~2h series
  wearing a 1h label. Unusable for frequency comparison and for volume work.

### Added (D219/D220 — the dual verdict and the volume filter, 2026-08-27)
- **D219** changes the acceptance rule: every arm now carries **two verdicts**, standalone
  (A–G) and in-portfolio (P1–P5), reported side by side with neither allowed to replace the
  other. P4 makes correlation a hurdle rather than a hope; P5 moves the unit of deflation
  from the arm to the book. Amended pre-run with the cross-fixture invariant — comparisons
  are made on `arm − matched buy-and-hold`, never on raw Sharpe.
- **D220** + `scripts/run_volume_filter.py` + `data/volume_filter_summary.json` +
  `tests/unit/test_volume_filter.py` (22). Volume is loaded **separately** rather than by
  changing `load_panel`, so no previously published number can move; a test pins it.
- The **ORACLE bound** and the **matched-count random null** as a reusable pair for any
  selection rule over a fixed trade population, plus the **capture ratio** they define.

### Result (D219/D220)
- **A volume filter selective enough to matter cuts the arm below its own power threshold
  before it can be judged.** All 12 cells remove 39–61% of trades; every one fails the
  pre-registered census gate. At 7.1 round trips per ETF per year the trade population is
  too thin to subset — a fact about the **arm**, not about volume.
- The textbook confirmation rule never clears selectivity. **No cell beats the parent on
  money**; the two that beat it on Sharpe cost 31 and 18 points of return.
- Capture ratios of **0–6%** against an ORACLE reaching **+1.503**: the space was real and
  volume took none of it.
- **Hurdle H in isolation would have promoted a book with Sharpe −0.003.** Only the
  conjunction caught it — D219's dual verdict working on its first outing.

### Fixed (D220)
- `append_section` reintroduced D217's non-reproducible-render defect in a new place: the
  insert and replace paths emitted a different number of blank lines, so `--report-only`
  did not reproduce the page byte-for-byte. Now strips any existing section first so both
  paths run one insertion, pinned by
  `test_report_only_reproduces_the_page_byte_for_byte`.

### Added (D218 — Impulse MACD, 2026-08-24)
- Impulse MACD (LazyBear) in `research/macd.py`: `smma` (Wilder, alpha = 1/n), `zlema`
  (`2*EMA1 - EMA2`, centre of mass exactly zero), `impulse_macd_series` and the three rung
  scores. Deliberately in the same module as the D217 ladder so the two indicator families
  stay pinned together.
- `scripts/run_impulse_macd.py` + `data/impulse_macd_summary.json` + a D218 section in
  `MACD_RESULTS.md`. The runner **imports the D217 runner** rather than restating its cost
  path, portfolio arithmetic, nulls or DSR machinery — D212 is why — and a test asserts by
  identity that it has not defined its own copies.
- `tests/unit/test_impulse_macd.py` (33) and `tests/unit/test_impulse_ladder.py` (16).

### Result (D218)
- **D217's mechanism replicates, and the clean read is stronger than the headline delta.**
  I1−I2 = +0.628 long-short against D217's +0.285, but **I1−C ≈ 0** (−0.038 to +0.008): a
  Wilder channel, a zero-lag mid and a dead zone buy nothing over `EMA(12)−EMA(26)`. Two
  acceleration rules from unrelated arithmetic agree to within 0.04 Sharpe while both level
  counterparts are dead.
- The level rung is **anti-predictive**, not merely dead: −0.265 Sharpe at the 0.0th
  percentile of its own rotation null.
- The dead zone hurts **both** metrics — the indicator's most distinctive feature is its
  most useless one.
- Best cell +0.658 (the highest this project has produced on this fixture) fails A, D and G.
  **0 of 16 clear; the pre-registered stop applies.**
- Verdict floor +1.420 at 45,803 looks, driven by the inherited prior rather than this
  study: **no arm anyone runs on this universe can clear it.** The fixture is exhausted.

### Fixed (D218)
- Hurdle D now names **both** metrics before the run (Sharpe AND dividend-adjusted total
  return, both required), which is the design-time fix for the gap D217 had to disclose in
  an addendum. It bites immediately: the best cell beats buy-and-hold on Sharpe at a third
  of the drawdown and loses 10 points of money.
- Recorded a real defect in the published indicator: an SMA seed matches an EMA's steady
  state only at `alpha = 2/(n+1)`, and Wilder smoothing uses `1/n`, so Impulse MACD starts
  16.5 slopes from its own steady state and needs **926 bars** to forget it — about four
  years of daily data. Pinned by
  `test_the_sma_seed_is_exact_for_the_macd_ema_and_NOT_for_wilder`.

### Added (D217 — the MACD crossover ladder, 2026-08-24)
- `src/backtest_framework/research/macd.py` — the first EMA in this codebase, with the seed
  convention stated rather than assumed (SMA-seeded at `slow-1`, each leg over its own
  window; exact on a linear ramp, which is why that seed and not another) and the burn-in
  derived (166/124/360, slow leg binding, **393** total for 12/26/9). MACD is the first IIR
  estimator in an all-FIR codebase and the module says so out loud.
- `scripts/run_macd_ladder.py` + `data/macd_ladder_summary.json` + `MACD_RESULTS.md` (a new
  append-only ledger). Census, break-even arithmetic, the three-rung nested ladder, the
  declared sweep, rotation and block nulls, a fill-timing bracket, and the deflated Sharpe at
  three multiplicity counts. Offline, deterministic, seed 0.
- `tests/unit/test_macd.py` (36), `tests/property/test_macd_invariants.py` (9),
  `tests/golden/test_macd_golden.py` + its hand-computed twin (12), and
  `tests/unit/test_macd_ladder.py` (15). The golden runs at MACD(3,7,3) so every alpha is a
  power of two and every value in the walk is a dyadic rational — asserted with `==`, not
  `approx` — and its scenario makes the two rungs hold opposite positions, so a ladder that
  collapses into one rule turns the file red.

### Result (D217)
- **The signal line is the only part of MACD that does anything, and the whole thing still
  dies on multiplicity alone.** R1−R2 = +0.285 long-short against a +0.10 hurdle, holding at
  +0.247 under a stricter fill. All eight zero-line sweep cells land between −0.166 and
  +0.080 against a signal-line median of +0.315, so the separation is structural rather than
  a lucky cell.
- The best cell clears **six of seven** hurdles — ladder deltas, rotation null at the 99.25th
  percentile, block null at the 100th, buy-and-hold (+0.496 vs +0.266 at half the drawdown),
  both halves — and fails only the deflated-Sharpe floor: +0.334 at the fresh count of 42,
  +0.638 at the verdict count of 45,783.
- R2−R3 collapses from +0.163 to +0.042 under one more bar of lag: the middle rung's edge is
  a fill-timing artifact, surfaced only because the implemented fill was disclosed as more
  favourable than the pre-registered one and bracketed instead of argued.
- The 200-MA confluence gate is destructive in every cell and both books (−0.09 to −0.21).
- 0 of 12 cells clear every hurdle, so the pre-registered programme stop applies and Stage 2
  (the costed engine verdict) does not run.

### Added (D217 ADDENDUM — dividend-adjusted returns, 2026-08-24)
- `scripts/run_macd_ladder.py` gains a total-return panel: sidecar dividends laid onto the
  bar grid and reinvested on the ex-date (`r_tr[t] = log((close[t] + div[t]) / close[t-1])`),
  2,285 matched and 0 unmatched. Dividends and fixture prices are both in the split-adjusted
  frame (D75), so `as_declared_dividends` is deliberately not called. **The position series
  is untouched** — the signal still reads the price a trader sees.
- Every cell now reports price-only and dividend-adjusted total return and CAGR, and the
  verdict records hurdle D under both a Sharpe and a total-return reading.
- Six tests in `tests/unit/test_macd_ladder.py`, including the sign check that a long
  receives the dividend and a short pays it.

### Changed (D217 ADDENDUM)
- **The best cell loses to buy-and-hold on money, and the adjustment roughly tenfolds the
  margin**: +53.54% against +70.81% dividend-adjusted, a 17.3-point gap (−1.34pp CAGR),
  where price-only it was 1.5 points (−0.13pp). Its Sharpe advantage is a risk-reduction
  result — half the exposure, −13.6% drawdown against −35.1% — not a return result.
- Hurdle D fails under the total-return reading, 0 of 12. The verdict is unchanged because
  every cell already failed G. The ladder deltas are unmoved: both rungs hold the same kind
  of exposure, so the dividend stream largely cancels inside them.

### Fixed (D217)
- D217's own ledger arithmetic: the declared sweep grid admits **8** (fast,slow) pairs, not
  the 6 counted by eye — (12,13) and (24,26) satisfy `fast < slow`. The grid was not widened;
  the count was wrong. Fresh look count corrected from 34 to 42, which is what the deflated
  Sharpe is computed against, and pinned by
  `test_the_sweep_grid_admits_eight_pairs_not_six`.

### Added (D216 — the tail, the frequency and the fill, 2026-08-24)
- `scripts/run_reversion_tail.py` + `data/reversion_tail_summary.json` + a D216 section.
  Adds a spacing-based tail sampler (≥ M bars apart, ~8× the events blind stepping gives at
  the 99th percentile), a maker-fill arm on `FillAssumption.TRADE_THROUGH`, and an
  asymmetric break-even solver — break-even is a fixed point, not a constant, because the
  take-profit can rest and the stop cannot.
- `tests/unit/test_reversion_tail.py` (40), including the mandatory pair, a subset/strictness
  pin on the fill convention, and a regression pin on `_rate` (see Fixed).

### Findings
- **`p` keeps rising all the way into the tail.** 52.33% → **56.66%** (BTC) and 52.89% →
  **61.43%** (ETH) across the 87.5th → 99.5th percentiles of move size, monotone on both.
  D215's one open thread, closed with a yes.
- **It still does not pay.** The maker arm — the only arm whose costs make a 15m entry
  possible at all — reaches 59.27% and 58.60% against break-evens of 63.77% and 60.76%.
  **The gap narrows from roughly 4× to about 4 points and does not reach zero.**
- **Two cells cleared every hurdle, both on the optimistic bound.** `maker in/out` prices the
  stop as a maker fill; you cannot rest a stop, so those passes are real arithmetic on an
  untradeable fee model.
- **At daily the sign flips.** BTC's top bucket reverts 40.00% — big daily moves continue.
  H3 predicted weaker reversion and got reversal of sign, matching the standard stylised
  fact. Weak claim on n = 120 / 100 and recorded as one.
- **Adverse selection is real in direction but half the predicted size**: +1.46% mean against
  a predicted ≥ 3 points, 7 of 10 cells in the predicted direction.

### Fixed
- **`rate()` returned 1.0 for every cell.** `sum(1 for _, ok in rows)` with no `if ok` counts
  every row, so every bucket read 100.00%, every hurdle "cleared", and the reading function
  announced a positive. No test caught it — the halves function sums bools correctly and
  disagreed with the headline, the same tell as D209. Root cause: it was a **closure inside
  `measure`**, so it could not be imported and was never pinned. Now module-level `_rate`,
  pinned against a hand-counted list, with a companion test requiring the headline to equal
  the sample-weighted blend of the halves.
- **The verdict table paired a taker fill with maker costs**, taking `p` from the population
  that crossed the spread and the cost from the population that rested. It produced a
  spurious pass (ETH 99.5th, +0.67%) that reads −2.16% once corrected. Each tier in `FEES`
  now declares the arm it is coherent with, pinned by test.
- **The test fixture could not test what it was written for.** `_bars` padded every synthetic
  bar with a 0.1% wick, so a limit at the previous close always traded through and the maker
  arm filled 434 of 434 events. Default padding is now zero.

### Added (D215 — is it just mean reversion?, 2026-08-24)
- `scripts/run_generic_reversal.py` + `data/generic_reversal_summary.json` + a D215 section.
  Both arms call the *same* `structure_nulls.continue_from` — one function, not two
  implementations — so the comparison is like-for-like by construction.
- `tests/unit/test_generic_reversal.py` (12), including the mandatory pair: the statistic
  must be flat on a random walk and steep on a series built to revert.

### Findings
- **The staircase survives with the structure deleted.** Bucketing every 8th bar by move
  size reproduces the Fibonacci ladder's shape with no change of character, no leg, no level
  and no gap: 37.8% → 50.9% (BTC), 37.6% → 52.6% (ETH). Slopes +0.10288 and +0.10293 — two
  independent assets to four decimal places.
- **Matched on move size, the structure is worse.** −0.033 and −0.030, outside the ±0.02
  band on the negative side. **H2 falsified in the hypothesis's favour**: the components do
  not merely fail to add, they subtract about three percentage points. Conjecture: D173's
  confirmation lag makes the move stale by the time a touch registers.
- **The slope decays two thirds by 20 bars** — reversion's signature, not a level's.
- **It is a slope, not a level**: even the largest-move bucket reverts only ~51%.
- **Matching the target to the horizon converts the tilt into hit rate and gives it back in
  size**: P(target) 4.5% → 42.4% at 1R, gross R unchanged-to-worse, net R worse.
- **And it ends at 15m regardless**: the predicted move is a 0.5 ATR band worth 0.19%/0.26%
  of price against an 80 bp round trip — **0.24× and 0.32× the cost of capturing it**.


### Added (D214 — the terrain map as a confluence gate, 2026-08-24)
- `scripts/run_structure_terrain_gate.py` + `data/structure_terrain_gate_summary.json` + a
  D214 section. Overrides D203's stop by explicit amendment, recorded before the runner
  existed. Field windows calendar-matched to 15m per D194 and asserted by test.
- `tests/unit/test_structure_terrain_gate.py` (19), including the composition look-ahead
  pair — both inputs are individually guarded and neither says anything about reading the
  field at the signal bar rather than the entry bar.

### Findings
- **0 of 12 cells clear the gross-R hurdle, 0 of 12 beat the shuffle control, and 0 of 12
  clear a Sharpe bar — including the lowest.** Best observed Sharpe −2.28. The three-bar
  distinction never arises: not a result history killed, one that was never there.
- **H2 falsified.** `inverted` did not clear +0.10R despite D202's measured anti-signal —
  though the *direction* held: it averages −0.007R against `aligned`'s −0.038R and wins 5 of
  6 paired cells. The prior pointed the right way at a twentieth of the needed size.
- **In 8 of 12 cells the rejected trades beat the kept ones** (D198 repeating).
- **The grid census was first written as a tautology** that returned exactly zero and could
  not have failed — `Grid.bucket` depends only on `ln_min`, the fixture's lowest low falls
  in the first half, so every bucket index was identical by construction. Rebuilt to perturb
  the axis origin by half a bucket, it shows **5.7% / 4.0% of gate decisions flip**, which
  bounds the precision of any gate on this field and is inside every advantage measured.
- D203's stop is restored; the exception was bounded and is spent.

### Added (D213 — mined selection rule on a held-out seven years, 2026-08-24)
- `scripts/run_structure_selection.py` + `data/structure_selection_summary.json` + a D213
  section. Development year picked on counts before any outcome was read; thresholds frozen
  at that year's medians and never recomputed on a holdout year; mining on gross R so the
  search cannot become a search for wide stops.
- A shuffled-outcome control that runs the identical mining procedure on permuted outcomes,
  which is what makes the in-sample and out-of-sample numbers interpretable.

### Findings
- **Two features survived 2018 — wait longer, higher volatility — and inverted out of
  sample**: +0.489R/+0.265R in sample against **−0.128R/−0.016R** on the seven held-out
  years, negative in 7 of 8 years on BTC.
- **54% of shuffled-outcome draws manufacture a surviving feature** from pure noise, yet
  the real in-sample edge cleared that control's 95th percentile — so 2018 was a real
  pattern that did not persist. Regime, not randomness.
- **`trend_align` was pre-registered and never tested**: a median split cannot divide a ±1
  variable, so it vanished from the table without appearing as a failure — D196's H4 again,
  caught by checking which keys the output contained. Amended, tested standalone, and
  falsified out of sample (+0.012R / +0.087R against a +0.10R bar).
- **After costs the filtered arm returns −1.850R and −1.476R a trade.** An entry filter
  changes which trades are taken, not what the wrapper risks.
- Records the control's own weakness: shuffling independently per symbol destroys
  cross-symbol correlation, so the null is narrower than the true selection distribution.

### Added (worked trade examples, 2026-08-24)
- `scripts/run_structure_examples.py` + `data/structure_examples_summary.json` — extracts
  example trades from the full confluence arm under a selection rule fixed in the script
  before any outcome was inspected: per symbol the best, median and worst by net R, plus
  the pooled highest and lowest cost in R.
- `docs/results/structure_trade_examples.html` + `scripts/build_structure_examples_report.py`
  — the report, reusing `final_report.html`'s stylesheet verbatim so the two are the same
  document rather than two that resemble each other.
- `tests/unit/test_structure_examples.py` (13) pins every number the page quotes against
  its source JSON, including that the stylesheet is still byte-identical to the original's.

### Added (candlestick charts on the examples, 2026-08-24)
- `scripts/build_structure_examples_report.py` now draws an inline SVG candle chart per
  trade — the change of character, the impulse leg, the 61.8% touch band drawn to scale,
  the fair value gap, entry, stop, 5R target and exit. Hollow/filled candles rather than
  red/green: the inherited palette has one accent and it is reserved for what the trade
  turned on. Every colour is a custom property, so the charts follow the viewer's theme.
- `run_structure_examples.py` now stores the full bar window per trade (23–88 bars, from
  before the change of character to past the exit) rather than ±4 bars around entry.
- Seven further tests: one candle per bar against the stored window, nothing drawn outside
  its own frame, no hard-coded colours, every chart marking the structure it illustrates,
  and each chart in its own horizontal scroll container.

### Findings — illustrative, not a verdict
- **The eight-slot rule yields seven trades: the highest-cost trade in either book IS
  BTC's worst.** The worst outcome and the most expensive one are the same event.
- **The worst trade is not a bad prediction, it is a fee bill.** Gross −1.00R, an ordinary
  stop-out; the entry sat 0.038% of price from its stop, so the round trip cost **20.891R**.
  ETH's worst is the same shape at 0.039% and 20.443R, five years and one asset apart.
- **The 61.8% level is a band covering 9.6%–28.1% of the leg on each side.** BTC's best
  trade qualifies as a golden-ratio touch at an actual retracement of **37.8%**.
- **Both best trades are genuine, clean 5R winners.** The strategy is not one that never
  works — it needs 40.2%/33.5% of trades to do that and gets 11.0%/15.4%.

### Fixed (the cost convention, 2026-08-24 — D212)
- `structure_setups.friction_in_r` charged `cost_bps` once for a round trip while
  `structure_strategies.r_multiples` charged it per side — **two halves of one study
  pricing the same tier a factor of two apart.** Per-side is correct
  (`CostTier.fee_bps` is a per-fill exchange fee; `StrategyResult.net_returns` doubles it).
- The suite missed it because `test_the_cost_charged_in_r_matches_the_census_arithmetic`
  compared `r_multiples` to a formula retyped from `r_multiples` — a test named for an
  agreement between two components that never called both. The real pin now exists.
- WP2's friction doubles and the conclusion strengthens: the stacked arm's round trip now
  costs **more than the entire risk of the trade** (1.41R / 1.01R), and the required hit
  rate at 5R rises to 32.7%/28.0% (base) and 40.2%/33.5% (stacked). Nothing in D208/D210/D211
  moves — those rest on zero-cost and rank statistics.

### Added (post-close Sharpe/PnL addendum, 2026-08-24 — D212)
- `scripts/run_structure_pnl.py` + `data/structure_pnl_summary.json` + an addendum section.
  Supplies the sizing rule the R-based study never had (constant unit exposure through each
  trade, `PositionResult` path) so the arms can be reported in Sharpe and money against
  buy-and-hold and cash, at three fee tiers.
- **0 of 16 arms make money at 40 bps/side, and 0 of 16 at 10 bps/side.** Buy-and-hold
  returns +460% (BTC, Sharpe +0.32) and +115% (ETH, +0.11) over the same span. The best
  zero-cost arm returns +1,788% and goes to −9,532 of 10,000 at ten basis points a side.
- Admitted to a closed programme as a descriptive restatement under three pre-stated
  conditions, including that a positive would have required its own pre-registration.
  Ledger 86 → **102 looks**.

### Added (the discretion audit and the close, 2026-08-24 — D211)
- `scripts/run_structure_audit.py` + `data/structure_audit_summary.json` + the WP6 section
  and the FINAL REPORT section of `STRUCTURE_RESULTS.md`.
- **The structure programme is closed after 86 looks.** Across all 8 cells of the
  pre-registered grid the largest rank correlation any feature reaches inside any
  stop-width quintile is 0.10–0.15 against a bar of 0.2; stacking the filters helps at zero
  cost in **0 of 8** cells; the base arm's zero-cost mean R never leaves +0.013 to +0.093.
- WP5 never ran — D210 triggered the pre-registered stop.

### Fixed (the stop was on the wrong side of the trade, 2026-08-24 — D209)
- `structure_setups.stop_price` now returns `leg.start_price`, the extreme the impulse came
  FROM. It previously used `leg.end_price`, which for a long sits ABOVE the entry. The
  wrong-side guard in `run_arm` rejected 1,865 of 2,000 setups and kept an adversely
  selected 135 — a wrong answer converted into a missing one, D205's finding for the third
  time. Surfaced by a count that did not match another count, not by a test.
- WP2's friction table recomputed and its section carries a generated correction banner
  naming the superseded figures. One finding reverses: a deeper entry is a TIGHTER stop, so
  the confluence stack raises friction from 0.48R to 0.71R rather than halving it.
- Two tests pin the stop side in both directions and the `(1 - retracement) x |span|` identity.

### Added (the marginal analysis, 2026-08-24 — D210)
- `scripts/run_structure_marginal.py` + `data/structure_marginal_summary.json` + the WP4
  section. Three readings: feature quintiles on an overlapping annotation population,
  the same features conditioned on depth and on stop width, and the 8-arm ablation lattice.
- `structure_strategies`: MFE/MAE moved into **R units** (scale-invariant, asserted by
  test) after the price-fraction form made `stop_atr` a false candidate at rho +0.56 —
  D187's lesson in a new costume. `run_arm` gained `allow_overlap` for annotation
  populations; the one-at-a-time rule was throwing away 93% of the sample for a rank
  statistic. `expectancy` gained `median_r`, `share_untradeable` and `mean_r_tradeable`
  after mean R came back −104 (correct arithmetic for a position size nobody can take).

### Findings — WP4, 48 looks
- **Nothing survives holding leg size constant.** Three features clear the promotion
  criteria unconditionally and are one quantity under three names (pairwise rank
  correlation +0.79 to +0.88). Inside stop-width quintiles the largest correlation any
  feature reaches is **0.13** against a bar of 0.2, with no sign agreement — depth included.
- **Stacking all four filters makes the strategy worse before costs**: −0.038R and −0.102R
  a trade at zero cost, against the base arm's +0.013R and +0.093R.
- **44% and 32% of base-arm trades are untradeable** at 40 bps — the round trip costs at
  least their entire risk.
- **The pre-registered stop condition is triggered. WP5 does not run.**

### Added (component placebos and the frozen wrapper, 2026-08-24 — D207/D208)
- `research/structure_nulls.py` — the continuation statistic (`terrain_nulls`' reversal
  definition, re-oriented by the setup's direction rather than the approach side), four
  matched placebos, a paired bootstrap, and `DepthTable` for the depth-matched re-reading.
- `research/structure_strategies.py` — the frozen wrapper, identical in every arm. Market
  entry at the close (D207), stop at the swing extreme with D10 gap-through fills and D42
  stop-first ordering, 5R target, channel trail after 1R. Direction-signed excursions, so
  `feature_analysis.analyse_feature` can rank a two-sided book.
- `scripts/run_structure_components.py` + `data/structure_components_summary.json` + the
  WP3 section of `STRUCTURE_RESULTS.md`.
- `tests/unit/test_structure_nulls.py` (22), `tests/unit/test_structure_strategies.py` (16).

### Findings — WP3, no costs, 30 looks
- **One variable explains the whole strategy: retracement depth.** The eight-ratio ladder
  is a strictly monotone staircase in depth. 0.618 ranks **4 of 8** on both symbols and
  loses to 0.691 and 0.724 in 97%+ of paired bootstrap draws. The spread between arbitrary
  ratios is ten times the golden ratio's advantage over them.
- **The depth-matched null takes back the study's only clean pass.** The fair value gap
  falls from +0.082 at the 100th percentile to **+0.006 / −0.006**, because real gaps sit
  at retracement 0.626 against the uniform placebo's 0.444.
- **The flipped level is negative either way**, consistent with D196's S5 result.
- **The change of character fails the both-symbols requirement**: BTC +0.133 delta at the
  66th percentile (below the null's p95), ETH −0.057 at the 43.6th.
- **RSI — the control — is the only arm that survives depth matching.** H6 confirmed.
- The depth-matched null was **post-hoc**, is counted as six further looks, and makes every
  verdict harsher rather than kinder. Disclosed rather than folded in.

### Added (the setup census, 2026-08-24 — D206)
- `research/structure_setups.py` — composes the five detectors into `Setup` objects that
  record, per bar of the pullback window, **which conditions held there**. Any subset reads
  its own entry off the same object, so WP4's 16 arms differ in the filters and in nothing
  else. `SetupPopulation` returns the drops explicitly. Plus `friction_in_r` and
  `required_hit_rate`, pinned against D196/D197's published 0.49R/0.12R pair.
- `scripts/run_structure_census.py` + `data/structure_census_summary.json` + the WP2
  section of `STRUCTURE_RESULTS.md`. Counts only — no return, no Sharpe, 0 looks. The
  section's prose is generated from the payload so the two cannot drift (D176/D183/D186).
- `tests/unit/test_structure_setups.py` (26).

### Findings — counts only, no backtest
- **The round-trip cost is roughly the whole distance to the stop.** 40 bps is 0.40% of
  price; the median C1-only stop is 0.41% (BTC) and 0.56% (ETH), so friction is 0.97R and
  0.72R.
- **The course's arithmetic fails once costs exist.** Its 5R target breaks even at 16.7%
  frictionless and at 23.3–32.9% at 40 bps. **A 20% hit rate at 5R loses money in every
  cell measured.** Independent of whether any component carries information.
- **H5 falsified** — the stacked arm is not underpowered (120 and 106 entries against a
  floor of 30). WP3/WP4 proceed.
- **C5 dropped as a stacked filter on counts alone**: RSI 30/70 collapses the stack to 2
  entries on both symbols. Retained as a continuous feature for WP4a.
- **C3 admits 69–70% of setups on its own** — very little work for a filter, before WP3
  asks whether 0.618 differs from the placebo ratios.
- **The stack's one measurable effect is entering deeper** (retracement 0.32 → 0.54, stop
  1.05 → 1.75 ATR), which halves friction and is not evidence of a signal.
- **The discretion gap, measured**: 340 BTC setups had all three conditions somewhere in
  the window and only 120 had them at the same bar.

### Fixed
- Two guard-shaped defects, both caught by tests written before the run. ATR warm-up was
  punching holes in pullback windows, producing non-contiguous windows whose first bar was
  not the bar an entry became possible; those setups are now refused and counted. And ~9%
  of setups were dropped dead-on-arrival by an `if window:` without being counted — found
  because `SetupPopulation`'s drop arithmetic is asserted to add up.

### Added (the structure detectors, 2026-08-24 — D204/D205)
- `New Docs/STRUCTURE_MODEL.md` + `STRUCTURE_RESULTS.md` — a new programme and a new
  ledger, opened at 0 looks, on a genuinely new construction: the five components of a
  discretionary retail price-action strategy. Terrain's 259 looks disclosed adjacent.
  Pre-registered before any code existed (D204).
- `research/structure.py` — five INDEPENDENT detectors, no strategy and no thresholds.
  `market_structure` (the BOS/CHoCH state machine, D173's confirmation lag applied),
  `retracement` + `ratio_price` (continuous depth, never a boolean), `fair_value_gaps`
  (three-bar imbalance, filled on the bar RANGE), `rsi` (Wilder's original smoothing, as
  the study's control). `PLACEBO_RATIOS` fixed here: 0.447/0.553/0.691/0.724, the
  non-canonical ratios 0.618 is measured against.
- `tests/unit/test_structure.py` (45) + `tests/property/test_structure_invariants.py` (10).

### Findings — from a mutation pass run because the suite passed first time
- **Two of six deliberate mutations survived 43 green tests.** Mutation 5 dropped the
  higher-low requirement — the pre-registered definition of a change of character — and
  nothing noticed. Mutation 6 introduced a mirror sign error on the bullish leg's start,
  and the degeneracy guard converted it into *missing* legs rather than wrong ones, which
  the sign-of-every-leg assertion satisfied vacuously.
- Both fixed: a planted pattern that separates the higher-low definition from the naive
  one (and its mirror, reflected through a price axis), and leg-endpoint assertions that
  require **each direction to be populated**.
- The general form, recorded in D205: **an invariant asserted only over the outputs a
  component produces cannot see a component that has stopped producing them.** Same shape
  as D196's H4, reached from the opposite direction.
- 1,098 tests green (55 new), mypy `--strict` clean on the new module.

### Added (the volatility estimator gate, 2026-08-23 — D195)
- `research/vol_estimators.py` — the incumbent (20 close-to-close daily returns, pinned by
  test against `InverseVolatilityWeight.weight()` rather than merely resembling it) and the
  candidate (realized vol from 15m returns), plus MSE-on-log-vol, QLIKE and Mincer-Zarnowitz
  R². Both estimators come from the SAME 15m fixture with the daily series resampled from
  it, so provider, span and calendar are identical and the estimator is the only variable.
- `scripts/run_vol_estimator_gate.py` + `data/vol_estimator_gate_summary.json` +
  `docs/results/vol_estimator_gate.md`. Runs in 11 s.

### Findings — predictions committed first (c27e671), then scored
- **The gate FAILS. Step 2 does not run.** Loss reduction on the majors is +15.8% to
  +29.9%, against a pre-registered floor of 30%. BTC's worst cell is short by 14.2 points,
  ETH's by 8.0.
- **H1 FALSIFIED.** Predicted at high confidence that the candidate would win
  *comfortably*. The direction was right on all eight gate cells and the magnitude was not
  — D195 wrote that case down in advance: the effect being smaller than the literature that
  motivated it IS the finding. A floor calibrated on equity data was applied to 24/7 crypto.
  **The floor was not moved after the fact.**
- **H2 FALSIFIED, and the two-target design is why we know.** Predicted the effect would be
  smaller on thin dying coins. Against the accurate target it is LARGER — XEM +32.8%/+55.7%,
  BTG +36.2%/+51.6%, the only cells anywhere clearing the bar. Against the incumbent's own
  basis it goes NEGATIVE: XEM −0.2%, **BTG −29.6%**, a 65.8-point divergence. On a thin
  instrument the candidate predicts *itself* well and predicts reality worse than a
  20-observation estimator. Scored on one target, BTGUSDT would have been the run's
  strongest result; it is the weakest.
- **H3 untested**, since step 2 did not run. Its argument — that the 70%-of-risk-budget
  defect is structural in the weighting rule rather than an accuracy problem with its input
  — is untouched and remains the more likely explanation.
- Real and unused: forecast R² of 20-day-ahead volatility rises 0.2128 → 0.2710 on BTC and
  0.2145 → 0.2938 on ETH. Better estimate, nothing built on it.

### Verified
- 898 tests green (20 new), mypy clean. Every figure in the result section checked against
  the summary JSON programmatically; one R² was quoted at an ambiguous 3 dp and is now 4.

### Added (S1 re-tested at 15m and closed for good, 2026-08-23 — D194)
- `scripts/run_terrain_s1_intraday.py` — the WP2 re-run on exchange-native 15m volume,
  every window calendar-matched to D189 so bar resolution is the only variable. Appends its
  own dated section to `TERRAIN_RESULTS.md` rather than overwriting it, which the daily
  runner does despite the ledger's append-only header.
- `data/terrain_s1_15m_summary.json` — every figure in the result, machine-readable.
- `rolling_mean_true_range` / `rolling_realized_volatility` in `research/terrain.py`. The
  reaction scan recomputed a 1,920-bar ATR per bar: measured at 173 hours for the grid.
  These are linear, build in 0.08 s, and are pinned by test against the per-call forms.
- A bucket-span census on `PriceDensity` (`spans`, `median_span`, `single_bucket_share`),
  pre-registered in D194 as a diagnostic that can invalidate a pass.
- `ATR_WINDOW`, `HORIZON` and `REBUILD_EVERY` are now parameters rather than constants read
  at import; `run_null` never forwarded `horizon` at all, which is fixed.

### Changed
- `VolumeProfileSensor.lookback_days` → **`lookback_bars`**. The field was applied as a bar
  count and named days — harmless on daily bars, a lie at 15m. `LOOKBACK_BARS` extended to
  `(90, 180, 8_640, 17_280)`, with `DAILY_LOOKBACKS` kept as its own tuple so extending the
  set cannot silently change what D189's runner iterates.

### Findings — predictions committed first (d2cc20e), then scored
- **H1 CONFIRMED. S1 fails all three pre-registered conditions.** Primary configuration:
  BTC 89.6th percentile (p = 0.106), ETH 66.4th (p = 0.337). Deltas +0.0068 and +0.0024
  against a floor of 0.045 — **6.6× and 19× short**. Breadth 3/8 and 0/8.
- **The sign flipped, and that is the honest nuance.** D189's real levels sat BELOW their
  null on both symbols; D194's sit above it on both. Intraday attribution produces a real,
  correctly-signed effect — roughly a fiftieth the size needed to be useful.
- **H3 CONFIRMED, and it is why the run was worth doing.** Three BTC configurations cleared
  p ≤ 0.05, one at **p = 0.0080, the 99.4th percentile, on 30,187 touches**. All were
  4.5–7.1× below the effect-size floor, and none was on ETH. Reported alone that cell would
  have read as "S1 works at 15m". Two independent pre-registered guards killed it.
- **The span-matched daily control rules out the era**: D189's configuration on the
  overlapping years is still indistinguishable from random (BTC 22.4th, ETH 51.2nd). It
  also shows how unstable ~250 touches is — the same configuration moved 41.4th → 22.4th on
  BTC merely by dropping the pre-2018 years.
- **The bucket-span census rules out degeneracy**: median span 4.0 buckets, single-bucket
  share 1.3–3.1%. The map is a genuine volume profile, not a close-price histogram.
- **S1 is closed at any resolution** by D194's permanent stop. WP3–WP8 remain unrun.
  Cumulative multiplicity: **147 looks on one hypothesis**.

### Corrected
- **D194's runtime estimate was wrong by 6×** — 0.5 hours predicted, 10,909 s (3.03 hours)
  measured. The benchmark timed the per-bar scan and omitted the per-touch work, and the
  two numbers it lacked were 23.85 levels per rebuild (D189: 3.88) and 13,782 touches per
  scan (D189: 353). Recorded rather than quietly fixed: a 6× miss on a figure stated in a
  pre-registration is the class of unverified number this project keeps catching.

### Verified
- D189's committed summary reproduces **byte-identically** from the refactored code.
- Both synthetic controls re-run at intraday windows: nothing found in a random walk across
  three seeds, planted level still found.
- Precomputed and per-call reaction paths pinned to agree end to end.
- 878 tests green (16 new), mypy clean.

### Added (BinanceDataSource and the first non-yfinance fixture, 2026-08-23 — D193)
- `data/binance_source.py` — assembles monthly 1m archives into a continuous series behind
  `get_raw_history`, the seam every fetch script uses. Verifies each archive against its
  published SHA256 **on every run including cache hits** and raises on mismatch; calls
  `dedupe_seam` at the monthly joins, which is the caller that function was committed
  without. Caches under `data/raw/` (already gitignored).
- `scripts/fetch_binance_fixture.py` + `data/fixtures/crypto_binance_15m_raw.csv.gz` —
  BTCUSDT/ETHUSDT (matching D189) and XEMUSDT/BTGUSDT (delisted, carrying the empty-bar
  problem), 1m resampled to 15m through D161's existing contract. Refuses to write a
  partial fixture unless `--allow-partial`.
- `data/manifests/binance_1m_majors.json` — D191's committed artifact: 279 archives with
  the provider's own SHA256. The 1m base (486 MB cached) is not committed.
- `save_fixture_csv` gained an optional `extra_columns`, threaded through
  `SnapshotStore.create` to `Snapshot.extras`, so the fixture carries base volume, quote
  volume and taker-buy volume side by side rather than deriving one from another (D187).

### Findings
- **A second provider defect, caught by D161's alignment guard on the first real run.**
  From 2017-12-04 06:00:20.799 to 2017-12-18 10:00:20.799 every `BTCUSDT` 1m bar is
  stamped exactly 20.799 seconds past the minute — a constant clock skew, not jitter.
  `ETHUSDT` carries 20.810s; a second episode at ~14.79s runs into February 2018. 17 days
  and 21,602 bars per symbol. The bars are **dropped, not snapped**: a bar labelled
  00:00:20.799 could describe [00:00, 00:01) or [00:00:20.8, 00:01:20.8) and the archive
  does not say which, so rewriting the timestamp would be inventing the answer (D25).
- **The first fix for it was wrong, and the gate caught that too.** Dropping the off-grid
  days made 2017-12-03 and 2017-12-19 adjacent, so fifteen days of the December 2017 rally
  arrived as one bar and the validator correctly called it +69.0% on BTC / +68.4% on ETH.
  The drop policy manufactured the violation. The series is now TRUNCATED to start after
  the last off-grid day rather than stitched across it, costing BTC and ETH 170 good days
  each. The same artifact is latent in the 1h fixture and has only never fired because its
  holes are one day long.
- **The 15m base needed no gate override.** 0 hard violations, snapshot not quarantined,
  7,334 warnings (6,671 `volume_spike`, 658 `zero_volume`, 5 `unexplained_move`). The
  volume rule would have dropped 658 bars — measured by calling `clean()` twice, not
  assumed. D192's and D143's deferrals both stay unspent.
- **Empty-bar rates at 15m**: BTC/ETH 0.000%, XEM 0.195%, BTG 0.788%, against 25.3% and
  44.7% for the same two dying coins at 1m.
- **Reconciliation against the daily fixture over 2,853 days**: BTC median 8.3 bp
  (p90 63.6, max 371), ETH median 9.4 bp (p90 66.2, max 585). Reported, not asserted —
  a single-venue USDT pair and a multi-venue USD index are different instruments (D161).

### Fixed
- **Gzipped fixtures are now byte-reproducible.** `gzip.open` stamps the current time into
  the header, so re-running any fetch produced a whole-file diff — 25 MB of it here — even
  when not one row had changed. Writes now pin `mtime=0` and omit the embedded filename.
  A diff that always appears is a diff that stops being read, and immutable-by-diff
  (D70/D24) is the reason fixtures are committed rather than re-fetched. Reads untouched;
  snapshot ids unaffected, since `bars.csv` inside a snapshot is uncompressed.
- A units bug in `binance_source`'s first draft: the D192 census was being computed against
  a trade count inferred from volume, which would have made "does zero volume agree with
  zero trades" answer itself. It now uses the provider's own `number_of_trades`, and the
  fetch refuses to build a fixture on a symbol where the two disagree.

### Verified
- Three committed fixtures still freeze to their pre-change snapshot ids, pinned as a test
  — the schema extension is provably inert on the default write path.
- Two consecutive full fetches produce a byte-identical fixture.
- A tampered cached archive is refused by name, identified as stale rather than corrupt.
- 862 tests green (49 new), mypy clean.

### Added (the Binance archive, probed before anything is built on it, 2026-08-22 — D190/D191/D192)
- `data/binance_archive.py` — pure, offline parsing for Binance's public flat-file
  archives. The epoch unit is DETECTED per file, not configured: the archive switched kline
  `open_time` from milliseconds to microseconds at 2025-01, and a reader that assumes
  milliseconds dates a mid-2025 bar to the year 57,400. Base and quote volume are carried
  separately in the provider's own units and neither is derived from the other.
- `scripts/probe_binance_archive.py` — the network probe. Writes no fixture and no
  snapshot; produces `data/binance_probe_summary.json` and a report rendered from it, with
  `--report-only` re-rendering offline. Retention and size come from S3 listings, so only a
  stratified sample of archives is actually downloaded.
- `docs/results/binance_provider_probe.md` — the findings.
- `tests/unit/test_binance_archive.py` — 38 offline tests plus one `live_fetch` smoke test
  that deliberately picks a month AFTER the microsecond switch.

### Findings
- **Retention: 108 monthly archives of 1m bars for BTC and ETH, 2017-08 to 2026-07**,
  against the 730 days of 1h yfinance serves. D163 refused any return claim below 1h
  because 60 days cannot hold a 252-day training window; that constraint does not bind here.
- **Zero-volume rate is 0.000% on every sampled month from 2022 onward**, against D160's
  17,520-of-34,923 on yfinance hourly bars.
- **The zero bars that do exist are TRUE, and the column that proves it is
  `number_of_trades`.** In every sampled month on every symbol, the zero-volume bars and the
  zero-trade bars are the same bars exactly — 25,878 of each on `BTGUSDT` 2022-01. That is
  the market saying nothing traded, not a feed defect, and it is the opposite of D160's case.
- **On dying coins a 1m time grid is majority-empty**: 57.97% on `BTGUSDT` 2022-01, 56.68%
  on `XEMUSDT` 2022-09. Since the failure universe is the only screen in this project that
  ever caught anything (D140/D180), this constrains the bar definition of any intraday
  study, and D192 declines to choose it before a pre-registration does.
- **The units cross-check D187 did not have passes on 100.0000% of bars** in every sampled
  month: quote volume ÷ base volume lands inside the bar's own high–low range.
- **The daily crypto fixture gets its first independent check.** Binance 1m resampled to
  UTC days agrees with it to a median 9.6 bp on BTC and 14.8 bp on ETH over May 2021.
  Volume does not reconcile and should not — global USD notional against single-venue base
  units, which is the same distinction D187 got wrong in the other direction.
- **58 of 63 universe coins are reachable, and the 5 that are not are not random**: `OKB`,
  `HT` and `CRO` are rival exchanges' tokens. A single-venue archive applies a selection
  screen the yfinance roster did not, and that is recorded rather than absorbed.
- **6.34 GB of 1m archives, 952x the largest committed fixture and 367x the whole `.git`.**
  Checksum coverage is 100% across all 58 symbols, which is what makes D191's manifest-only
  policy available rather than merely appealing.

### Fixed
- A local-time bug in the archive parser, caught before it reached a result:
  `datetime.fromtimestamp(x, tz=None)` reads the epoch in the machine's zone, so the same
  archive would have parsed differently in London and New York and the fixture would have
  depended on who ran the fetch.

### Added (Phase 3: the S1 terrain sensor and its null, pre-registered, 2026-08-22 — D189)
- `research/terrain.py` — the terrain sensor interface, frozen for every later sensor, plus
  `VolumeProfileSensor` (S1). `PriceDensity` returns None outside the mapped range rather
  than 0.0; a bar's volume spreads across the buckets its RANGE covers rather than landing
  at its close. Lookback/bucket/volume-units all raise outside the spec's stated sets.
- `research/terrain_nulls.py` — the reusable null-test harness. Touch and reversal
  definitions fixed in the docstring before any run; reuses `MetricSpec`/`summarise_null`
  from D130 so every metric declares its own tail.
- `TERRAIN_RESULTS.md` — the programme's append-only ledger, carrying the multiplicity count.
- Look-ahead guarded HERE rather than inherited: D181 established `DataView` protects
  strategies and not analytics built on their output, and a sensor is analytics.

### Findings — predictions committed first (e2a8b09), then scored
- **S1 FAILS its null on all 16 configurations, all 3 metrics, both symbols.** At the
  primary config (180d, 0.5 ATR, k=0.5): BTC P(reversal|touch) real +0.3768 against a null
  mean of +0.3835 — the **41st percentile**; ETH +0.3529 against +0.3736, the **26th**.
  **On the metric the model rests on, real levels reverse price LESS often than random
  ones.** Traversal and volatility sit mid-null and in the wrong tail.
- **H1 confirmed**, against the spec's own prior that S1 is the lead sensor expected to pass.
- **The terrain programme STOPS at WP2** by its own stated condition. WP3-WP8 do not run:
  S1 was the strongest sensor on the spec's assessment, S2 is marginal and expected to fail,
  and S3 has zero independent validation in the literature.
- **The mandatory false-positive check passed first time** — on a pure random walk across
  three seeds the harness finds nothing.
- **The positive control failed twice and the FIXTURE was wrong both times.** A drift of
  `-0.9*gap` pushes price TOWARD the level, building a magnet rather than a wall; the
  harness correctly reported the planted level as worse than chance. Flipping to `+1.2*gap`
  built a wall price never returned to — one touch in 1,500 bars. The harness caught both.
- `New Docs/` is now complete: every phase either delivered or closed by its own criterion.


### Added (the ETF cross-section, pre-registered, 2026-08-22 — D188)
- `scripts/run_etf_universe.py` — the SAME long baseline, unchanged, on 57 ETFs.
  `periods_per_year=252`, `volume_units="shares"` (D187), dividends PAID on both arms
  (2,285 across 53 symbols + 14 splits), two crypto-specific screens disabled with the
  measurement behind each. Two cost tiers fixed in advance: equity (IBKR + 1bp) and the
  crypto 40bp as a stated handicap. Impact off — this asks whether the effect exists, not
  what it costs at size.
- `actions` threaded through `run_variant`, all three benchmark runners and
  `run_universe_study`, mirroring the volumes pattern; `_context_for` now serves both
  data-dependent bricks. Dividends are not optional: on SPY alone they move the strategy
  from +0.060 to +0.171 Sharpe, and omitting them would flatter the STRATEGY, which is
  flat about half the time and collects fewer than the benchmark.

### Findings — predictions committed first (cac1c45), then scored
- **The portfolio does NOT transfer. H1 confirmed emphatically.**

  | | Sharpe | Return | Max DD |
  |---|---|---|---|
  | Strategy (equity costs) | **-0.273** | +21.6% | **6.1%** |
  | Equal-weight basket | +0.395 | +100.5% | 33.4% |
  | SPY buy & hold | +0.617 | +187.0% | 33.7% |

  **Edge -0.667**, against +0.075 on crypto. At the crypto 40bp tier, -1.190 and the book
  returns -0.5%. Turnover 0.4x/yr: the breakout condition barely fires on an index fund.
- **H2 confirmed** — max DD 6.1% vs 33.4%. The drawdown property has now survived every
  test in this project and is the only claim that has. Read for what it is: a book invested
  a fraction of the time has a small drawdown for the same reason it has a small return.
- **H3 FALSIFIED, and its failure is the finding.** I predicted the diversification lift
  would reproduce, calling it "arithmetic, not a market claim". The portfolio Sharpe
  (-0.273) is BELOW the median single ETF (-0.177) — the lift **reversed**.
  **Sharpe is mean/sigma: averaging shrinks sigma, so it raises the Sharpe when the mean is
  positive and makes it MORE NEGATIVE when the mean is negative.** Diversification is a
  magnifier with the sign of the expectancy, not free arithmetic. D183 called the lift
  guaranteed; it is conditional on a positive mean, which is the entire question.
- **This was the easier test.** All 57 ETFs survived — identical spans, no delistings — the
  opposite property to the crypto universe, which was built to contain the assets that died.
  The strategy lost on the friendlier sample by 0.667 Sharpe.
- **Still untested, and now the deepest assumption in the project:** both samples are
  2015-2024. A different asset class is not a different era, and that cannot be fixed with
  data already on disk.


### Fixed (volume units in the impact model, 2026-08-22 — D187)
- **`SqrtImpact` divides an order QUANTITY by ADV, and `calibrate_impact_params` never
  asked what the volume column counted.** The ETF fixture reports SHARES (SPY 68.1M, x $474
  = $32bn/day); every crypto fixture reports QUOTE-CURRENCY NOTIONAL (BTC 47.5bn, which
  cannot be coins). So every crypto charge was off by sqrt(price): BTC's ADV was 21,970x
  too large (impact understated ~148x), LUNC's 1,585x too small (overstated ~40x). **The
  same run was wrong in both directions at once.**
- `calibrate_impact_params` now takes `volume_units` in `("shares", "quote_notional")` and
  **raises** on anything else — there is no safe default to guess with. `"shares"` stays
  the default, so the pairs study's published trials are untouched. Conversion is bar by
  bar, `mean(volume_t / close_t)`, not mean-notional over mean-price.
- **A second bug, found only because the fix required an alignment assertion.** All three
  benchmark runners were handed a SLICED bar series with a FULL-LENGTH volume series
  (`ADA-USD`: 2,974 volumes against 2,709 bars), introduced the day before when volumes
  were first threaded to them. Without the assertion it would never have raised — ADV would
  have been calibrated over a longer window than the bars it priced, quietly, in the
  direction of understating impact.
- Both study summaries remain byte-identical; `volume_units` is emitted only alongside the
  impact brick.

### Findings — D186 corrected
- **Capacity moves from ~$30M to ~$66M.** Edge: +0.075 at $100k (was +0.067), +0.047 at
  $10M (was +0.014), -0.014 at $100M (was -0.026).
- **"Two long books destroyed by impact" is WITHDRAWN.** `LUNA1-USD` and `LUNC-USD` are
  sub-cent coins whose impact was overstated ~40x. With the units right, **no book is
  destroyed at any size tested**.
- **H1 is now FALSIFIED by 0.001**: Sharpe falls 0.099 against a predicted >0.10. Called as
  written rather than left as yesterday's confirmation.
- **H2 still confirmed, and the concentration mechanism is stronger**: the strategy loses
  10x more Sharpe to impact than the benchmark (0.099 vs 0.010), up from 5.3x.
- **I predicted the correction would move capacity DOWN and it moved up.** BTC and ETH see
  impact rise 148x and 29x — but they are 2 of 62 in an equal-weight book, and most of the
  universe trades below $1 where impact was OVERstated. Same error class as D185: a correct
  mechanism applied to the wrong population.


### Added (capacity, pre-registered, 2026-08-22 — D186)
- `CostTier.impact_coefficient` wires square-root market impact (D66) into the breakout
  cost tiers, reusing `SqrtImpact` and `calibrate_impact_params` from the equities pairs
  study. **The D166 rule, fifth application**: the `sqrt_impact` brick is ABSENT when off,
  not present with coefficient zero, so every config hash in both studies is unchanged.
- `CostTier.build()` takes an optional `StackDataContext` and raises if impact is on
  without one; a new `_context_for` helper is the single place all four build sites ask
  "did anyone pass the volumes".
- `scripts/run_capacity_portfolio.py` sweeps $100k-$100M, per-coin slice AUM/62, at the
  reference tier, with the benchmark charged impact on the same terms.
- `run_universe_study` gains `compute_dsr` (only the capacity sweep passes False).

### Findings — predictions committed first (6a9529e), then scored
- **BOTH CONFIRMED. Capacity is ~$30M of total AUM (~$484k per coin).** Edge over the
  equal-weight universe: **+0.067** at $100k, +0.051 at $1M, +0.014 at $10M, **-0.000 at
  $30M**, **-0.026 at $100M**.
- **H1 confirmed narrowly**: strategy Sharpe falls +1.240 -> +1.124, a loss of 0.116
  against a predicted >0.10.
- **H2 confirmed, and for the predicted reason.** The strategy loses **5.3x more Sharpe to
  impact than the benchmark** (0.116 vs 0.022) despite the benchmark turning over 2.7x
  more. Volatility normalisation did not rescue it — the mechanism the pre-registration
  named — because the strategy's impact CONCENTRATES in the thin coins it trades while the
  benchmark spreads turnover across all 62. **First time a mechanism-first prediction here
  was right about both the mechanism and its consequence.**
- **Two long books destroyed by impact alone** at $30M+: `LUNA1-USD`, `LUNC-USD`. No long
  book dies at zero impact (D183). Also the model's own edge: a sqrt-impact charge large
  enough to bankrupt an account is outside the range D66's form was fitted for.
- **Deflated Sharpe = 0.9996** at $100k (30 trials, V[SRn] read from the long study's
  published inputs, not asserted). **It should not be quoted alone**: DSR deflates against
  a trial pool, not a benchmark. At $30M the strategy and the benchmark both score +1.161
  and the DSR would still be high — it measures crypto beta surviving a multiplicity
  correction, not skill surviving one. Skew +4.76, kurtosis 106.7.
- **All three of D183's debts are now paid**; the honest summary is an equal-weight crypto
  basket with a breakout overlay, at a third of the basket's drawdown, with an edge that is
  small at $1M, marginal at $10M and gone at $30M.

### Fixed
- `run_universe_study` accepted `volumes_by_symbol`, used it for the policy screen and
  **never handed it to the run**. Harmless until a cost tier needed ADV, at which point it
  became a loud failure — which is the only reason it was found. Volumes now passed
  unconditionally to `run_variant` and to both benchmarks; verified byte-identical on the
  existing portfolio study before anything downstream was trusted.
- `dated_returns` tested `a <= 0.0` for account death, which is False for NaN. Impact large
  enough to exceed a position's notional produces exactly that; in the one observed case
  NAV went negative several hundred bars before it went NaN, so the loose guard happened to
  catch it. Now `not (a > 0.0) or not isfinite(b)`.


### Added (rebalancing cost charged, pre-registered, 2026-08-22 — D185)
- `_equal_weight_arm` now returns one-way TURNOVER alongside the gross series, and the
  portfolio study charges it at the project's existing 0/10/25/40bp ladder. **The benchmark
  is charged too** — the equal-weight universe rebalances daily as well, and charging only
  the strategy would rig the comparison. Buy-and-hold pays nothing after its first purchase.
- Break-even solver: the cost at which the strategy's Sharpe edge over the benchmark
  reaches zero, by bisection, reporting "none" rather than interpolating a number that does
  not exist.
- The two D184 artifacts are neutralised in the benchmark only; the strategy is untouched
  by both.

### Findings — predictions committed first (32fd7a2), then scored
- **The cost barely touches the result. Both predictions FALSIFIED.**
- Annual turnover: strategy **1.8x**, equal-weight universe **4.8x**, BTC buy & hold 0x.
- Net Sharpe at 40bp: strategy **+1.252** (from +1.277), benchmark **+1.174** (from
  +1.196), BTC +1.096. **Edge +0.081 -> +0.078.** Break-even **972bp**, about 24x the
  reference tier.
- **H1 falsified**: predicted the strategy would drop below +1.00 at 40bp; it drops 0.025.
  1.8x turnover at 40bp one-way is 0.72%/yr against ~25% vol.
- **H2 falsified as stated**: the edge narrows very slightly rather than widening, and a
  break-even exists. The turnover half of the reasoning was right — the 2.7x asymmetry was
  predicted and observed, for the predicted reason (flat books do not drift).
- **The error is the normalisation, and it is worth keeping.** A cost's damage to a SHARPE
  is `cost / volatility`. The benchmark turns over 2.7x more and pays the same Sharpe
  penalty because it is 3.4x more volatile. Turnover and volatility scale together, so the
  comparison is near cost-invariant. **In RETURN terms the intuition does hold**: the
  strategy gives up 7% of total return at 40bp, the benchmark 17%.
- Drawdown is untouched: 28.8% -> 29.3%.
- **D183's largest stated threat is now paid.** Two debts remain: a deflated Sharpe against
  the 30-configuration pool, and an out-of-sample cross-section. And a turnover charge is
  not a liquidity model — capacity in small-cap alts is the next and harder question.


### Fixed (unrecorded corporate actions, 2026-08-21 — D184)
- **A benchmark returned +102,682,123%, and it came from ONE bar.** `HT-USD` printed
  **+3,398,300%** on 2025-03-12 (close 0.0000150 -> 0.5098, then flat at ~0.50): a
  price-scale defect, not a market move. Neutralising that single bar takes the benchmark
  to +70,139% — a factor of **1,464x** from one day, because daily rebalancing compounds
  it forward.
- **`AAVE-USD` +10,189% on 2020-10-03 is the LEND->AAVE 100:1 token migration** — a genuine
  redenomination that no split adjustment handles. The preceding bar also carries a zero
  open and zero low.
- **The events file is empty.** `crypto_universe_2015_2025_raw_events.json` has `dividends`
  and `splits` for all 63 symbols and every list is `[]`. The machinery is wired and has
  nothing to apply.
- **Four scripts passed an empty corporate-actions object rather than loading it** —
  `run_swing_universe`, `run_e1_universe`, `run_combined_universe`, `run_portfolio_universe`.
  Now fixed. Verified a genuine no-op: every field of the portfolio payload is identical
  after the change, and only the content-addressed snapshot id moves.
- **The strategy results are NOT contaminated.** Long portfolio return on 2025-03-12:
  **+0.0127%**; on 2020-10-03: **+0.0860%**. D103's next-open fill means a one-bar gap
  cannot be entered — the strategy arrives after the jump while buy-and-hold holds through
  it. The defect inflates the BENCHMARK far more than the strategy.
- **D143's validator override is now costed.** Its reasoning stands (the >60% gate deletes
  the failed assets and hands back survivorship bias), but an override with no follow-up
  inspection accepts unknown defects, and the follow-up had never been done.

### Added (benchmarks for D183, appended to that record)
- **Like for like, daily-rebalanced strategy vs daily-rebalanced equal-weight universe, the
  breakout rule is worth +0.084 Sharpe (full span) and +0.194 (>=5 coins live)** — not the
  +0.49 the naive single-coin comparison suggested. Daily rebalancing alone is worth +0.21
  Sharpe on the benchmark (+1.191 daily vs +0.978 monthly), charged nothing.
- Conservative span: strategy +0.927 Sharpe / +316% / **22.9% max DD**, against BTC buy &
  hold +0.786 / +1,087% / 76.6%, equal-weight true buy & hold +0.651 / +438% / 87.7%.
- **The drawdown result is the real one** — a quarter to a third of every benchmark, and
  not explained by diversification, since the equal-weight universe is equally diversified
  and draws down 81%. Being flat about half the time is what does it.
- **The return result is unfavourable**: 15% of buy-and-hold BTC over the full span.
- Correct summary: roughly the return of an equal-weight crypto basket, at a quarter of its
  drawdown, with a small Sharpe edge over that basket rebalanced identically — and the
  +0.084 sits inside the range an un-charged turnover cost could erase.


### Added (cross-sectional portfolio, pre-registered, 2026-08-21 — D183)
- `scripts/run_portfolio_universe.py` — a long/short portfolio ACROSS the 62-coin
  universe. Each date, the long portfolio earns the equal-weighted mean of every live long
  book, likewise the short; the two are combined at D181's expanding inverse-vol weights.
  Return aggregation, not a portfolio backtest. Own registry, no multiplicity added.
- Books that wipe out are truncated at NAV zero. Once NAV is negative `b/a - 1` is not a
  return and averaging it would propagate nonsense across every other coin. Stricter than
  the per-symbol studies, still not a liquidation model (D175).

### Findings — predictions committed first (9dbd2d6), then scored
- **H1 CONFIRMED, narrowly.** Long portfolio Sharpe **+1.278** (total return +2,913%, max
  DD 28.8%) against **+0.437** on the median single coin. But the pre-registered robustness
  check bites: restricted to dates with >=5 coins live, it is **+0.928** — clearing the
  predicted +0.90 bar by 0.028. **A third of the headline was the thin 2015-2017 sample.**
  Still more than double the median single coin, so the diversification claim survives even
  though the headline does not.
- **This is the first thing in this project that has worked.** It is also the least
  surprising, because it is arithmetic: it operates on the return DISTRIBUTION rather than
  on one book's timing, which is what every failed rule tried to do.
- **H2 CONFIRMED, three times more strongly than per symbol.** Adding the short portfolio
  costs **-1.170** Sharpe (D182's per-symbol cost was -0.382) and takes total return from
  +2,913% to +54%. On the breadth-conditioned sample the combined book is NEGATIVE.
  The pre-registered counter-mechanism — that aggregation would fix the short book by
  making it continuously held — is refuted: it is continuously held here and subtracts more.
- **D181's weighting flaw gets WORSE at portfolio level.** Mean long-portfolio weight
  **0.302** — the losing leg carries 70% of the risk budget, against 61% on BTC alone.
  Pooling 62 coins diversifies the short arm's returns, lowering its measured volatility,
  which inverse-vol rewards with MORE weight. **The construction pays a book for being
  diversified and for being absent.**

### Fixed (in this study's own reporting, before publication)
- The weighting paragraph asserted that aggregation would make D181's flaw bite LESS. It
  was written before the run and is the opposite of what happened; it is now derived from
  the payload rather than hardcoded.
- The breadth table was labelled "books with a position open" and actually counts books
  LIVE IN THE SAMPLE — a flat book contributes a 0.0 return and was counted. Label fixed,
  and the exposed gap stated: **position-level breadth is not measured**, which bears
  directly on whether daily equal-weighting is realistic.

### Owed before +0.928 is a result rather than a number
- The rebalancing cost between coins, which this study does not charge and which
  daily-rebalanced equal weight maximises. The largest single threat to the finding.
- A deflated Sharpe: the underlying baseline survived a 30-configuration search.
- Its own out-of-sample test. One crypto cross-section over one bull-dominated decade is
  exactly the sample-shaped problem D180 exists to warn about.


### Added (combined book on the D140 universe, pre-registered, 2026-08-21 — D182)
- `scripts/run_combined_universe.py` — the long+short combined book across 62 coins,
  per-symbol, no rule attached. The baseline that had never been measured. Own registry,
  no multiplicity added; the long arm is `breakout_universe.baseline_variant()` itself.

### Findings — predictions committed first (b75e2e3), then scored
- **H1 CONFIRMED on both clauses.** The combination scores a LOWER Sharpe than the long
  book alone on **57 of 62 coins** (8% win rate, mean Δ -0.382) and a SMALLER max drawdown
  on 68% (mean -4.7pp). On the 19 survivors it is worse on every single one.
- **Absolute P&L is the headline.** Median total return: long **+123.2%**, combined
  **+5.7%**. Profitable symbols 51/62 -> 34/62. Mean Sharpe +0.392 -> **+0.010**.
  Combining destroys ~118pp of median return and 17 profitable symbols to buy 4.7pp of
  drawdown. BTC alone: +4,672% long vs +197% combined.
- **H2 CONFIRMED more strongly than predicted.** Correlation is within +/-0.2 on **62 of
  62** coins, and the largest absolute correlation anywhere is **0.0023** — three orders of
  magnitude inside the brief's ~0.2 target. And combining still costs 0.38 Sharpe on 92% of
  coins. The correlation is MECHANICAL (the short book is flat ~85% of bars, so the legs
  rarely have simultaneous exposure) and **the ~0.2 target is retired as evidence**.
- **The drawdown benefit is real, scales correctly, and inverts in the tail.** By long-book
  drawdown quartile the mean Δ runs +1.0pp (Q1) -> -8.3pp (Q4), monotone. But drawdown got
  WORSE on 20/62, led by `LUNA1-USD` at 21.2% -> **74.5%** (+53.3pp): the long book
  returned +1,298% there and the combination -5%. The hedge smooths ordinary drawdowns and
  amplifies the one that would end the account.
- **D181's weighting flaw, now measured.** Median long-leg weight 0.456; the long leg holds
  a MINORITY of the risk budget on 47/62 coins. corr(long weight, Δ Sharpe) = **+0.604**
  while corr(long weight, short-leg Sharpe) = **-0.043** — the allocator sizes on how often
  a book trades, not on how good it is. On LUNA1 it gave 81% of the budget to the leg about
  to lose more than the account.
- Weighting fell back to 50/50 on **0.8%** of bars, against 75% for the 63-bar trailing
  window D181 rejected.
- Not a portfolio result: per-symbol combination asks whether pairing one coin's two books
  helps, not whether a cross-sectional long/short book works.


### Fixed (ensemble weighting look-ahead, 2026-08-21 — D181)
- **`combine_books`/`combined_series` set their inverse-vol weights from WHOLE-SAMPLE
  volatility and applied them from bar 0.** The calmer leg got exactly the right weight in
  advance. Mild - two scalars, no per-bar leakage, no effect on either leg's trades - but
  every published combined Sharpe was inflated by it, and it was undocumented.
- D44 already required vol to be measured on a window ending at the PREVIOUS bar. The
  structural guard (D32/D56) never applied because the ensemble operates on return series
  rather than a `DataView`: **the guard makes look-ahead impossible for strategies and
  does nothing for analytics built on their output.**
- Now an EXPANDING window with a 252-bar warm-up (`ENSEMBLE_MIN_BARS` = `train_size`),
  using Welford's online variance so it stays O(n) - the naive version is O(n^2) and would
  make the 62-symbol universe run intractable.
- A 63-bar TRAILING window was tried first and rejected by its own diagnostics: the short
  book is flat on 88% of BTC bars, so the window was entirely flat and fell back to 50/50
  on **75%** of bars - an "equal-vol" book that was equal-CAPITAL three times in four.
  That also explains why removing the look-ahead first appeared to RAISE BTC's combined
  Sharpe 0.412 -> 0.685; the fallback was flattering it.
- `combine_books` no longer takes `min(len(a), len(b))` and slices from the end - it
  raises on unequal spans. A no-op today (both books produce identical spans) and a silent
  misalignment the first time that stopped being true.
- All three arms are now scored over the same post-warm-up span; `EnsembleResult` gains
  `short_max_drawdown`, `n_warmup_bars`, `n_fallback_bars` and `mean_long_weight`.
- New test: the weight applied at bar t is unaffected by returns at bar t or later. That
  single property is the definition of the bug and nothing asserted it.

### Findings
- Corrected combined Sharpe: BTC 0.412 -> **0.462**, ETH 0.649 -> **0.570**.
- **D179's conclusion is downgraded** (CORRECTION appended there): BTC's bootstrap
  interval now SPANS ZERO, [-0.008, +0.231]. "Both intervals exclude zero" was that
  record's load-bearing claim; one does.
- **ETH's short leg reads +0.142 over the full span and -0.228 once the first 252 bars are
  dropped.** Its positive Sharpe lived entirely in the 2018 bear market.
- **NOT fixed, now reported instead:** mean weight on the long leg is 0.389 (BTC) / 0.453
  (ETH) - the majority of the risk budget sits on the leg that is flat ~85% of the time
  and loses money, BECAUSE it is flat. Inverse-vol reads a flat book as low-risk when what
  it is, is absent. Surfaced via `mean_long_weight` on every combined result.
- `data/breakout_study_summary.json` byte-identical - the long book has no ensemble, so
  that was the decisive regression check.


### Added (E1 on the D140 universe, pre-registered, 2026-08-21 — D180)
- `scripts/run_e1_universe.py` — E1 vs no-E1 on BOTH books across the 62-coin D140
  cross-section, k=3 fixed, four runs, own registry so no published DSR moves. The long
  control is byte-identical to `breakout_universe.baseline_variant()`.
- Ties counted as ties: E1 is an added brick rather than a swapped one, so win rates are
  over firing symbols only and both denominators are reported. (It fired on all 62, so
  this turned out not to bind.)
- `--report-only` re-renders the report from the saved payload without re-running four
  walk-forwards.

### Findings — predictions committed first (494450e), then scored
- **All three predictions FALSIFIED, one of them reversed.** Long book 39% win rate
  (mean Δ Sharpe -0.065), short book 48% (-0.010). H3 predicted the gain would be LARGER
  among the coins that died; the long book runs monotonically the other way — survived
  -0.022, collapsed -0.081, delisted -0.144.
- **The four published BTC/ETH numbers reproduce exactly** (+0.101/+0.177 long,
  +0.061/+0.101 short), so this is not a measurement difference.
- **Absolute P&L, long book:** median total return +152.4% -> +97.6%, profitable symbols
  52 -> 50, mean Sharpe +0.411 -> +0.346, for 2.1pp less drawdown.
- **The damage is predicted by E1's trade-count growth (-0.72), NOT by volatility
  (+0.06)**, baseline Sharpe (-0.02) or history length (-0.03). Symbols where E1 added
  <=10% trades: mean Δ +0.055. Where it added >=40%: mean Δ -0.220.
- **The firing rate is ~+30% on everything** and is not predicted by any instrument
  property. What varies is the COST per firing: bucketed by baseline trade count, mean Δ
  runs -0.091 (9-17 trades) -> -0.028 (25-42), monotone, while the firing rate stays flat.
- **BTC sits at the 97th percentile of baseline trade count and ETH at the 85th**, median
  21 — the top quartile is the one E1 damages least. They rank 9th and 3rd of 62.
- **E1 is not noise.** Max drawdown improves on 42/62 long and 39/62 short, mean -2.1pp.
  It is a real risk reducer whose price exceeds its payoff outside two instruments.
- **The re-entry attribution is settled against D177.** E1 raised the trade count on 61/62
  long symbols, and that rise correlates -0.72 with the outcome. Re-entry is the mechanism
  of E1's HARM, not its benefit; it looked like a benefit only where re-entry was cheap.
- **D179's arithmetic stands, its interpretation does not.** Both bootstrap intervals
  excluded zero on a sample now shown to be the rule's best case. A confidence interval
  quantifies sampling error within a sample; it cannot detect an unrepresentative one.


### Added (E1 on the combined book, 2026-08-21 — D179)
- A second long leg carrying `failed_breakout` at k=3, so the LONG+SHORT ensemble can be
  measured with E1 on both legs against the same ensemble without it. `COMBINED_E1_K = 3`
  — the stronger k on both books in D178, used on both legs rather than tuned per side.
- `_combined_e1_block` in the breakdown report, and a `combined_e1` entry in
  `data/breakdown_study_summary.json`.

### Findings
- **The first ensemble improvement in this project whose interval excludes zero.** BTC
  combined Sharpe 0.412 -> 0.526 (+0.114, 90% CI [+0.002, +0.219], P=95.4%); ETH 0.649 ->
  0.845 (+0.197, 90% CI [+0.063, +0.362], P=99.5%). Every prior ensemble claim either
  spanned zero or was negative.
- **The gain is not from correlation.** Correlation moves ~0.001 or less on both symbols.
  It comes entirely from improving both legs while leaving their independence intact —
  which is exactly the channel through which the vol-weighted combination could have got
  worse while both components got better.
- **Drawdown improves alongside Sharpe**: combined max DD 34.0% -> 29.5% (BTC) and 29.5%
  -> 24.4% (ETH). The long leg's own max DD falls 43.0% -> 29.2% on BTC.
- **No new multiplicity.** The E1 long leg's config is byte-identical to the long study's
  registered `exit_e1_k3`, and both long legs run outside the short book's registered
  loop. A different reading of trials already paid for.
- Still the same two instruments throughout. The honest next test is unchanged from D178:
  E1 vs no-E1 on the D140 universe, 62 coins.

### Fixed
- The combined-E1 comparison was computed inside the variant loop, where `results_by_key`
  is only partly populated (`exit_e1_k3` is appended last) — the `is not None` guard
  silently skipped the whole section, so the first run produced NO tables rather than
  wrong ones. Moved after both loops and the silent skip replaced with a loud
  `AssertionError`.


### Added (cross-book test, pre-registered, 2026-08-21 — D178)
- `exit_swing_k2` / `exit_swing_k3` on the LONG book, and `exit_e1_k2` / `exit_e1_k3` on
  the SHORT book — each rule on the side it was NOT developed on. Both k tested on both
  sides, because testing only the winning k would repeat D173's actual error. E1 is not a
  stop, so on a short it rides alongside the incumbent channel stop the baseline carries
  and the delta prices E1 alone.

### Findings — predictions committed first (80dab52), then scored
- **H1 holds literally and is misleading if left there.** `swing_k2` fails the long book
  (+0.100 BTC, **-0.075** ETH) as predicted — but `swing_k3` CLEARS it (+0.015 / +0.148).
  The family transfers; the parameter does not.
- **The k FLIPS between books.** Short book: k2 wins, k3 does not (D173). Long book: k3
  wins, k2 does not. The pivot lookback is a property of the BOOK; the rule family is a
  property of the RULE. Carrying the number across is what fails.
- **H2 FALSIFIED.** E1 clears the every-symbol bar on the short book at BOTH k (+0.020 /
  +0.059 at k=2, +0.061 / +0.101 at k=3). H2 rested on attributing E1's long-book benefit
  to RE-ENTRY; trade counts say otherwise (35->39 BTC, 27->28 ETH). **E1's benefit is not
  re-entry, it is not sitting in a failed trade** — a real secondary mechanism mistaken
  for the primary one, the same class of error as D173.
- **E1 is now the strongest rule in this project**: four independent every-symbol passes,
  both books, both k, direction-agnostic by construction. Not adopted — pools grew to 30
  (long) and 27 (short) and both DSRs moved to pay for it. The honest next test is the
  D140 universe, as D174 did for the swing stop.


### Added (Phase 1.5 exit signatures, 2026-08-21 — D177)
- **`FailedBreakoutExit(k)` (E1)** — exits when the close falls back INSIDE the channel
  the entry broke, within k bars. Never built before, despite the doc calling it
  "highest priority" and a predicted survivor. `OpenPosition` gains
  `entry_channel_level`: the boundary that was BROKEN, distinct from `stop_level` (the
  opposite boundary) and `entry_reference` (the trigger close).
- **`TimeStopExit.mfe_atr` (E2)** — at 0.0 the rule is unchanged (the short book's "not
  in profit"); above 0.0 it is E2 as specified, MFE >= mfe_atr x ATR since entry. New
  keys emitted only when non-default, so short-book config hashes are untouched (D166).
- **`mfe_by_bar()`** — E2's stated prerequisite, the baseline's MFE-vs-time distribution,
  which did not exist: `TradeEpisode` carried only a terminal MFE.
- **`TradeEpisode.trajectories` + `impulse_trajectories()` (E3)** — post-entry range and
  volume per trade, logged and gating nothing, per the doc's explicit instruction. A
  sibling field rather than an extension of `features`, which D167 pinned as scalars.

### Findings
- **E1 KEEPS on both symbols** (+0.058/+0.177 at k=2, +0.101/+0.177 at k=3) — the first
  prediction in `BREAKOUT_REVERSAL_FEATURES.md` to hold. Unlike every other trade-touching
  device tested here, it RAISES the trade count (38->44 BTC, 28->30 ETH): it cuts a failed
  trade early and the strategy re-enters on a fresh trigger.
- **E2 DROPS at both n**, and its own prerequisite explains why: only 26% (BTC) / 43%
  (ETH) of trades reach 1 ATR by bar 5, so E2 cuts most of the book including the trends
  that pay. The validation the doc demanded would have predicted this before the run.
- Long-study DSR pool grew 24 -> 28 and every DSR moved; all 5,568 pre-existing variant
  metrics are byte-identical.

### Fixed
- **The MFE-vs-time table printed an impossibility** — ETH at 43% by bar 5 and 39% by bar
  7, when the rate cannot fall as the window grows. Trades closing before bar n were
  excluded from bar n's numerator while sharing bar 5's denominator. Fixed, and the report
  now raises if the rate ever falls again.


### Added (Phase 2's two missing diagnostics, 2026-08-21 — D176)
- **Squeeze events** — adverse excursions beyond 2 ATR against an open short, with share
  of trades, P&L carried, and how many the stop caught. The function existed as DEAD CODE
  from the Phase 2 session and was never called, so the requirement looked satisfied.
- **Per-window long/short correlation** — the brief asks for it per window; the study
  reported the full-sample figure only.

### Fixed
- **The dead squeeze function had the direction backwards.** It used `abs(mae)` as the
  adverse excursion. Excursions are measured in PRICE terms (D112), so a SHORT's adverse
  side is MFE — a short is hurt when price rises. It would have reported the short book's
  profitable moves as squeezes. The code carried a comment reasoning confidently to the
  wrong answer; it was caught only because wiring it up meant reading it again. Dead code
  is unreviewed code wearing the appearance of a delivered requirement.

### Findings
- **6 of 35 BTC trades (17%) ran more than 2 ATR against the position**, worst 3.70 ATR,
  carrying -39,015 of P&L — and **0% ended at the stop**. A direct measurement of what
  D169-D171 kept circling: the stop is present and is not what closes the dangerous trades.
- **Per-window correlation holds**: 15 of 59 windows measurable (the book sat out 44,
  which is the regime gate working), none exceeding ±0.2, median -0.004. The near-zero
  full-sample figure is NOT opposite-signed regimes cancelling out.
- Windows the short book sat out are reported as unmeasurable, not zero — "uncorrelated"
  and "not present" are different claims, and 44 of 59 fall in the second.


### Added (swing_k2 out-of-sample on the D140 universe, 2026-08-21 — D174)
- **`scripts/run_swing_universe.py` + `docs/results/swing_universe.md`** — `swing_k2` and
  `trail_10` run UNCHANGED across 62 screened coins, one configuration each, no
  per-symbol tuning (D141). The single pre-stated question D173 left standing.
- `run_universe_study` gains an optional `variant` parameter so the short book reuses that
  machinery instead of forking it; default unchanged, so the published long-book universe
  study is untouched.

### Findings
- **The stop survives, the strategy does not.** `swing_k2` beats `trail_10` on 43/62
  symbols (69%), above half in EVERY survivorship cohort — collapsed 71%, delisted 2/2,
  survived 63% — and robust to dropping blow-ups (41/59). But median total return is
  -50.5%, profitable on 5/62, and it posts one FEWER profitable symbol than `trail_10`
  while beating it on average.
- **Three accounts lost more than everything** (D175): USTC -1105.7%, LUNC -167.1%,
  LUNA1 -149.5%, with stops active. The engine models no margin call, no liquidation and
  no borrow recall, so NAV goes negative and the book keeps trading. This was the most
  important thing the run found and it is not what the run was looking for.
- Reports lead on the MEDIAN: a mean over a cross-section containing a -1105% row is not
  an average of anything. CAGR emits None rather than nan past -100%, because a nan in a
  results document is a number nobody has thought about — the first cut printed one.


### Added (swing-structure rules, pre-registered, 2026-08-21 — D173)
- **`SwingStructureStop(k)`** — the stop sits at the most recent CONFIRMED swing pivot
  against the trade; **`SwingStructureGate(k)`** — an entry gate requiring the last two
  confirmed swings to agree (higher high AND higher low, or lower high AND lower low),
  with ambiguous structure vetoing rather than guessing. `k in {2,3}`.
- **`last_swings()`** — pivot detection that never considers a bar newer than `index - k`.
  A k-bar pivot is not knowable until k bars after it forms, and an implementation that
  forgets that offset leaks the future INVISIBLY: DataView stops a crude version indexing
  past the present, but not one that computes pivots from visible bars and drops the lag.
  Asserted directly — a pivot must be invisible at t and t+k-1 and visible at t+k.
- Pivot LEVELS, not drawn trend lines. A sloped line through chosen swing points is a fit
  with free parameters, and `TERRAIN_MODEL.md` already rules out discretionary drawing.

### Findings — the pre-registration was committed first (d1f0d6c), then scored
- **H1 FALSIFIED.** `swing_k2` beats `trail_10` on BOTH symbols (+0.100 BTC, +0.093 ETH)
  and is the first stop here to improve both substantially. The prediction that no
  structure stop would clear the every-symbol bar was wrong.
- **Why it was wrong:** the redundancy argument compared swing SPACING to channel
  LOOKBACK and concluded the levels coincide. Spacing ~ lookback does not imply level ~
  level — a swing pivot is a LOCAL extreme and sits far closer to price after a
  favourable move than a rolling N-bar extreme still carrying the pre-move high. The
  prediction did hold for k=3 (+0.008), which is the case its spacing was reasoned from;
  the mechanism was right and generalised to the wrong parameter.
- **H2 holds.** Neither gate improves on the plain baseline across both symbols (k2
  -0.066/-0.006, k3 +0.168/-0.165). Trade counts fall by two thirds — another
  trade-removing device removing good trades with bad.
- **H3 holds.** DSR with the pool at 25: BTC 0.037-0.088, ETH 0.392-0.538, and DSR still
  selects `stop_trail_5` / `short_40_5` as best rather than `swing_k2`. **The
  falsification does not rescue the book:** `swing_k2` is a real improvement over
  `trail_10` and simultaneously the 25th configuration tried on a strategy with no
  demonstrated edge, and the second fact dominates.


### Added (short book: trial registry + deflated Sharpe, 2026-08-21 — D172)
- **Every breakdown trial is now registered** — one variant row per (symbol, variant,
  tier) plus one per walk-forward window, into `data/breakdown_study_registry.sqlite`
  under the `breakdown-v1` prefix. 168 out-of-sample trials, 2,142 per-window rows.
- **Deflated Sharpe per (symbol, tier)**, pool = configurations tried at that cell
  (D116), selected on identity fields and never on the presence of a metric (D98).
- **A paired block bootstrap of (combined - long-only) Sharpe** (D120), so the ensemble
  claim has an interval rather than a point estimate. The brief asked for
  Jobson-Korkie/Memmel; this project's convention for a Sharpe difference is the paired
  bootstrap, which answers the same question without assuming normality — the deviation
  is recorded in D172 rather than left silent.
- `breakout_study.log_trials` / `dsr_for` are now **public**: the breakdown book reuses
  this module's `VariantResult` and `run_variant` wholesale, so it shares these rather
  than becoming a fifth private copy. Every other study keeps its own.
- A **multiplicity sum-guard**, matching the one Phase 1.1 added to the long study after
  its breakdown table failed to add up.

### Findings — the gap was not cosmetic
- **DSR: BTC 0.039-0.096, ETH 0.393-0.515.** The long study sat near 1.0 at every tier;
  not one cell here reaches 0.95.
- **This overturns the report's two strongest positives.** ETH's 96th-percentile null
  result and its clean sweep of the three success criteria were the best of 21
  configurations; priced for that search, the evidence for skill is gone.
- **It lands on the stop sweep too.** DSR selects `stop_trail_5` as BTC's best — the very
  stop D171 found taking BTC from -71.6% to -40.6% — and deflates it to 0.039. D171's
  refusal to adopt it was right, and this is the number that proves it.
- **Ensemble, with an interval:** BTC -0.79 Sharpe, 90% CI [-1.13, -0.44], P(helps) = 0%
  — the whole interval is negative, so the short book measurably hurts. ETH -0.13,
  CI [-0.57, +0.31], P(helps) = 31% — spans zero, which is absence of evidence, not
  neutrality.


### Added (stop family + sweep, 2026-08-21 — D171)
- **`TrailingChannelStop`, `AtrStop`, `ChandelierStop`** alongside the incumbent
  `ChannelStopExit`, all direction-agnostic. `ExitRule` gains an optional
  `stop_level(view, position)`; the strategy keeps the TIGHTEST proposal each bar and
  RATCHETS it, because a level that can loosen is not a stop. The close-based backstop
  moved onto the strategy, applied once against the ratcheted level instead of being
  duplicated into every rule.
- **A seven-family stop sweep on the short book** at fixed entry/exit parameters, with a
  bind-rate column — D170's incumbent stop bound once in 915 armed bars, the trailing
  stops bind 20-60 times, and that is the difference between a stop being tested and a
  stop being decorative.
- **`SHARPE_EPS = 0.01`**, a stated floor below which a Sharpe difference is not called a
  difference. An earlier cut of the scorecard marked `trail_20` KEEP on a delta that
  rounds to +0.00 — it is in fact the incumbent under another name (for a short entering
  on a 20-bar low, a 20-bar trailing high IS the entry channel) and is now correctly
  reported INERT.

### Findings
- Two stops survive the every-symbol rule (`trail_10`, `atr_2`); neither is adopted,
  because the sweep added a fresh trial series to a book with no demonstrated entry edge.
- **Binding more is not uniformly better**: rank correlation between bind frequency and
  improvement is +0.94 on BTC and -0.43 on ETH, where the most-active stops cut winners
  rather than losers — the same failure mode the long study found in its entry filters.
- `trail_5` takes BTC from -71.6% to -40.6% and its drawdown from 72% to 52%, at a Sharpe
  that is still -0.34. Less bad is not good; no stop repairs an entry.
- **Known gap now pressing:** the short book still logs no TrialRegistry rows and computes
  no deflated Sharpe. Every Sharpe in the breakdown report is raw and is an upper bound.


### Added (intrabar stop execution, 2026-08-21 — D170, disposes of D169's limitation)
- **`TargetWeight.stop`** — an optional stop price riding with the target it protects.
  Re-declared every bar, so a trailing stop moves with no extra machinery; optional with
  a default, so all five construction sites and every pre-existing golden master are
  untouched.
- **Stop orders in `run_backtest`** — a live registry keyed (strategy, instrument),
  checked BEFORE the strategy is consulted so a position opened at this bar's open can
  still be stopped on the same bar, and routed through the existing
  `simulator/fills.stop_fill_price` so a gapped stop fills at the open rather than at a
  price the market never traded (D10). D42's adverse-fill-first convention holds by
  construction: the stop is intrabar, every other exit is a close decision.
- **Optional `Strategy.on_stop_filled`** — without it a stateful strategy never learns it
  was stopped and re-enters on the next bar, turning one bounded loss into a repeated
  one. Called via getattr, so every pre-D170 strategy still conforms.
  `ScheduledBreakout` forwards it to its inner strategy.
- **`BacktestResult.stop_fills`** — which fills a stop actually caused, recorded by the
  engine because only the engine knows.

### Fixed
- **D169's stop-gap measurement was wrong, and its headline number is withdrawn.**
  `measure_stop_gaps` inferred stop exits by asking whether an exit price ended beyond
  the stop level, which also counts trailing-channel exits that closed past it. That
  produced the "4 of 4 stop exits gapped, worst 38.5%" claim. Measured properly, the stop
  caused ONE exit across both symbols and did not gap. The real finding: armed for 915
  bars, binding once — the stop sits at the far side of the entry channel, so the
  trailing exit gets there first. Present, not binding.
- The breakdown report's stop section and standing caveat are now **computed from the
  numbers** rather than asserted alongside them — the third instance in this project of
  hardcoded prose drifting from the data beside it.


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
