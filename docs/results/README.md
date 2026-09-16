# Results

Every study this framework has been used for, 62 documents. **The framework is the artifact; these
are what it was pointed at.** Most of them are negatives, and that is the point — an instrument
earns trust by returning negatives when negatives are true.

Reading order matters more than completeness here, so this index has two halves: **five
demonstrations** chosen because each proves a different property of the instrument, and then the
full log.

---

## The five demonstrations

Each is here for what it establishes about the *framework*, not for what it found about the
market. The market findings are mostly "no".

| Study | What it proves about the instrument | Verdict on the market |
|---|---|---|
| [`first_real_number.md`](first_real_number.md) → [`v2`](first_real_number_v2.md), [`pairs_study_v1`](pairs_study_v1.md) / [`v2`](pairs_study_v2.md) / [`v3`](pairs_study_v3.md), [`gross_exposure_study.md`](gross_exposure_study.md) | **The walk-forward harness and cost stack produce a defensible number**, one variable moved per step: selection → cointegration filter → β-hedge → capacity → gross exposure | A real gross edge exists; no configuration of size or gross clears the full cost of capital |
| [`BREAKOUT_RESULTS.md`](BREAKOUT_RESULTS.md) | **A strategy is a swappable brick.** Different asset class, different direction, same engine, cost stack, walk-forward harness and trial registry — unchanged | Fees are not the binding constraint, which is the least interesting true thing about it |
| [`crypto_pairs_btc_eth.md`](crypto_pairs_btc_eth.md) | **An honest negative separates the engineering from the thesis.** Realised β ≈ 0 on all three benchmarks — the neutrality machinery works | At zero fees *and* zero carry it still loses 88.7%: the log spread is stationary in 14% of windows |
| [`MACD_RESULTS.md`](MACD_RESULTS.md) | **Pre-registration and the trial registry, including the stop firing.** The best cell clears six of seven hurdles and fails only the deflated-Sharpe floor — publishable as a first study, not as the 45,783rd look. 0 of 12 cells cleared, so Stage 2 never ran | The signal line adds something; the level rung is dead |
| [`STRUCTURE_RESULTS.md`](STRUCTURE_RESULTS.md) | **A measurement that collapses a story.** Five components mechanised so each could be scored separately — three that cleared the promotion bar turned out to be one quantity under three names | Nothing predicts once leg size relative to ATR is held constant |

All 62 now live here. The last 14 — the ones whose paths were pinned by tests — arrived with their
17 writer scripts and 14 test path expressions repointed in the same commit.

The best single document in the project is not a study at all — it is
[`final_report.html`](final_report.html), *"Nothing Worked"*: what was tested, how each idea died,
and the seven defects the guards caught.

---

## Two naming conventions, and the difference is real

- **`lower_snake_case.md`** — hand-written analysis pages. A human decided what to say.
- **`UPPER_SNAKE_RESULTS.md`** — study ledgers emitted by a runner in `scripts/`. Regenerating the
  study rewrites the document, which is why the numbers in them cannot drift from the artifacts.

Both live here. The names are not being unified: the ALL_CAPS name is the identity these documents
are cited by, in prose, across 102 references in 62 decision records.

---

## The full log

### ETF pairs — the original programme

| | |
|---|---|
| [`first_real_number.md`](first_real_number.md) | XLE/XOP z-score pairs, full cost sweep |
| [`first_real_number_v2.md`](first_real_number_v2.md) | the same through the hardened data layer |
| [`pairs_study_v1.md`](pairs_study_v1.md) | walk-forward Gatev/z-score over 57 ETFs |
| [`pairs_study_v2.md`](pairs_study_v2.md) | cointegration-filtered selection |
| [`pairs_study_v3.md`](pairs_study_v3.md) | β-hedged trading |
| [`capacity_analysis.md`](capacity_analysis.md) | where does the v2 edge clear real costs? |
| [`capacity_portfolio.md`](capacity_portfolio.md) | does the portfolio edge exist at size? |
| [`gross_exposure_study.md`](gross_exposure_study.md) | does lower gross clear the cost floor? |
| [`convention_sensitivity.md`](convention_sensitivity.md) | how much of the v2 result is convention? (D105) |
| [`etf_universe.md`](etf_universe.md) | the cross-sectional portfolio on 57 ETFs |

### Crypto — the contrasting strategy

| | |
|---|---|
| [`crypto_pairs_btc_eth.md`](crypto_pairs_btc_eth.md) | is there a spread to trade at all? |
| [`breakout_intraday.md`](breakout_intraday.md) | the cost–frequency frontier: where do fees eat the edge? |
| [`breakout_monte_carlo.md`](breakout_monte_carlo.md) | serial dependence, or the marginal distribution? |
| [`breakout_universe.md`](breakout_universe.md) | 63 coins including the ones that died |
| [`combined_universe.md`](combined_universe.md) | the combined long+short book on 62 coins |
| [`portfolio_universe.md`](portfolio_universe.md) | a cross-sectional long/short portfolio across 62 coins |
| [`e1_universe.md`](e1_universe.md) | E1 on 62 coins it was never fitted on |
| [`swing_universe.md`](swing_universe.md) | swing_k2 vs trail_10 on unchosen coins |
| [`WEDGE_CRYPTO_RESULTS.md`](WEDGE_CRYPTO_RESULTS.md) | D254 — the wedge breakout on crypto |
| [`BOOK_SHORTS_CRYPTO_RESULTS.md`](BOOK_SHORTS_CRYPTO_RESULTS.md) | D253 — the short sides of S1 and S2, on crypto |

### The book — building, filtering, stopping

| | |
|---|---|
| [`ACTIVATION_THRESHOLD_RESULTS.md`](ACTIVATION_THRESHOLD_RESULTS.md) | D234 — the percentage activation threshold |
| [`BOOTSTRAP_SWEEP_RESULTS.md`](BOOTSTRAP_SWEEP_RESULTS.md) | D230 — the bootstrap sweep |
| [`EXPOSURE_DIAL_RESULTS.md`](EXPOSURE_DIAL_RESULTS.md) | D231 — the exposure dial |
| [`FILTER_SEARCH_RESULTS.md`](FILTER_SEARCH_RESULTS.md) | D228 — the filter search, with the selection bias measured |
| [`JERK_RUNG_RESULTS.md`](JERK_RUNG_RESULTS.md) | D229 — one more rung up the derivative ladder |
| [`SCALE_CORRECTED_RESULTS.md`](SCALE_CORRECTED_RESULTS.md) | D232 — the scale-corrected Impulse MACD |
| [`RISK_CONTROLS_RESULTS.md`](RISK_CONTROLS_RESULTS.md) | D236 — portfolio-level risk controls |
| [`STOPS_TARGETS_RESULTS.md`](STOPS_TARGETS_RESULTS.md) | D235 — stops and targets on the recovery rule |
| [`STOPS_BOOK_RESULTS.md`](STOPS_BOOK_RESULTS.md) | D255 — stops and targets on the book and each arm |
| [`WITHHELD_TEST_RESULTS.md`](WITHHELD_TEST_RESULTS.md) | D237 — the recovery rule on withheld data |
| [`BOOK_WIDE_RESULTS.md`](BOOK_WIDE_RESULTS.md) | D245 — the book on the wide universe |
| [`BOOK_SINGLE_NAMES_RESULTS.md`](BOOK_SINGLE_NAMES_RESULTS.md) | D256 — short arms and the take-profit overlay, single names |
| [`XSEC_TREND_ARM_RESULTS.md`](XSEC_TREND_ARM_RESULTS.md) | D257 — the cross-sectional trend arm, on a name holdout |
| [`CROSS_SECTIONAL_PRESCREEN_RESULTS.md`](CROSS_SECTIONAL_PRESCREEN_RESULTS.md) | D251 — cross-sectional dollar-neutral ranking scores |
| [`BREAKDOWN_RESULTS.md`](BREAKDOWN_RESULTS.md) | does crisis alpha survive borrow? |

### Intraday and overnight

| | |
|---|---|
| [`ETF_INTRADAY_RESULTS.md`](ETF_INTRADAY_RESULTS.md) | D226 — the volume regime gate off its home fixture |
| [`INTRADAY_SHORTS_RESULTS.md`](INTRADAY_SHORTS_RESULTS.md) | D247 — S1 and S2 short at fifteen minutes |
| [`INTRADAY_FILTERED_RESULTS.md`](INTRADAY_FILTERED_RESULTS.md) | D248 — the strength-filtered intraday short |
| [`SINGLE_NAME_INTRADAY_RESULTS.md`](SINGLE_NAME_INTRADAY_RESULTS.md) | D264 — the intraday short on single names |
| [`OVERNIGHT_DECOMPOSITION_RESULTS.md`](OVERNIGHT_DECOMPOSITION_RESULTS.md) | D259 — where the overnight drift accrues |
| [`VOL_TARGETED_HOLD_RESULTS.md`](VOL_TARGETED_HOLD_RESULTS.md) | D260 — the vol-targeted overnight hold, time holdout |
| [`INDEX_SPREAD_RESULTS.md`](INDEX_SPREAD_RESULTS.md) | D261 — the index spread as a prop-track candidate |

### The book's arms and the ladders — the test-pinned ledgers

These fourteen are the documents whose paths the test suite pins, which is why they lived at the
repository root a round longer than the rest.

| | |
|---|---|
| [`MACD_RESULTS.md`](MACD_RESULTS.md) | D217 — the crossover ladder, and the deflated-Sharpe floor that killed it |
| [`BREAKOUT_RESULTS.md`](BREAKOUT_RESULTS.md) | does trend following on BTC/ETH survive exchange fees? |
| [`TERRAIN_RESULTS.md`](TERRAIN_RESULTS.md) | the terrain programme's ledger |
| [`SAMPLING_RESULTS.md`](SAMPLING_RESULTS.md) | D221 — does the indicator care about sampling rate? |
| [`SCALING_RESULTS.md`](SCALING_RESULTS.md) | D222 — does the fine-bar advantage grow with the window? |
| [`ASSEMBLED_RESULTS.md`](ASSEMBLED_RESULTS.md) | D224 — the assembled strategy |
| [`SHORT_MIRROR_RESULTS.md`](SHORT_MIRROR_RESULTS.md) | D238 — the short-side mirror of the recovery rule |
| [`TSMOM_ARM_RESULTS.md`](TSMOM_ARM_RESULTS.md) | D239 — time-series momentum as arm two |
| [`UPTREND_ONSET_RESULTS.md`](UPTREND_ONSET_RESULTS.md) | D240 — the uptrend-onset arm, with stops and targets |
| [`COMBINED_BOOK_RESULTS.md`](COMBINED_BOOK_RESULTS.md) | D241 — the combined book, and first-come-first-served capital |
| [`UPTREND_WITHHELD_RESULTS.md`](UPTREND_WITHHELD_RESULTS.md) | D242 — the uptrend arm and the combined book on withheld data |
| [`BOOK_EXTENDED_RESULTS.md`](BOOK_EXTENDED_RESULTS.md) | D243 — the book on extended history |
| [`BOOK_CRYPTO_RESULTS.md`](BOOK_CRYPTO_RESULTS.md) | D244 — the book on crypto |
| [`WEDGE_INVERSE_RESULTS.md`](WEDGE_INVERSE_RESULTS.md) | D249 — the inverse wedge breakout |

### Price action, and the data underneath

| | |
|---|---|
| [`STRUCTURE_RESULTS.md`](STRUCTURE_RESULTS.md) | the structure programme's ledger, D204–D211 |
| [`structure_trade_examples.html`](structure_trade_examples.html) | seven worked trades, chosen by a rule fixed before any outcome was read — it cross-references `STRUCTURE_RESULTS.md` in its own body |
| [`trade_anatomy.html`](trade_anatomy.html) | one trade, taken apart |
| [`binance_provider_probe.md`](binance_provider_probe.md) | the archive measured before anything was built on it |
| [`vol_estimator_gate.md`](vol_estimator_gate.md) | does finer data give a better estimate? |

### Archive

[`archive/breakout_v1/BREAKOUT_RESULTS.md`](archive/breakout_v1/BREAKOUT_RESULTS.md) — the
superseded first breakout run, kept under `archive/<study>_v<N>/` with its original filename.

> **Two files now share the name `BREAKOUT_RESULTS.md`** — the live study in this directory and
> the superseded v1 run in `archive/breakout_v1/`, two directories apart. Nothing in the repository
> resolves a results document by basename (checked: the only two `rglob` call sites touch `data/`
> and `.git`, and every glob over this directory is non-recursive), so this is a reading hazard
> rather than a tooling one. Link to the full path, not the name.
