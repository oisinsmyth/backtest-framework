# Design Decision Records

One file per decision (D1–D49), migrated from the original running log in
[`DESIGN_DECISIONS.md`](../../DESIGN_DECISIONS.md) (kept as a historical snapshot).
New decisions are added here going forward — next number is **D177**.

Standing scope/sequencing rules (R1–R4) live separately in [`docs/RULES.md`](../RULES.md);
they aren't chronological decisions, they're constraints that apply throughout.

Format: **Status** — Committed / Deferred / Rule-adjacent. Deferred items have a
written rationale for *why not now*, per R3.

| # | Title | Status | Category |
|---|-------|--------|----------|
| [D01](D01-replace-monolithic-costmodel-with-a-coststack.md) | Replace monolithic CostModel with a CostStack (ordered list of composable cost bricks) | Committed | Cost architecture |
| [D02](D02-split-costs-into-two-interfaces-per.md) | Split costs into two interfaces: per-trade costs (charged on fills) vs carry costs (cha... | Committed | Cost architecture |
| [D03](D03-add-square-root-market-impact-brick.md) | Add square-root market impact brick (cost ∝ σ√(Q/ADV)); demote vol-proportional slippag... | Committed | Cost architecture |
| [D04](D04-model-ibkr-s-actual-commission-schedule.md) | Model IBKR's actual commission schedule (per-share, exchange fees, minimums) instead of... | Committed | Cost architecture |
| [D05](D05-add-margin-interest-carry-brick-daily.md) | Add margin interest carry brick: daily rate on (gross exposure − capital) when positive | Committed | Cost architecture |
| [D06](D06-store-raw-prices-separate-dividends-splits.md) | Store raw prices + separate dividends/splits table; compute returns from adjustments bu... | Committed | Cost architecture |
| [D07](D07-fx-handled-in-two-parts-fxconversioncost.md) | FX handled in two parts: FXConversionCost trade brick now; full multi-currency accounti... | Committed / Deferred | Cost architecture |
| [D08](D08-cost-multiplier-sweep-harness-run-every.md) | Cost-multiplier sweep harness: run every backtest at 0.5×/1×/2×/4× the CostStack, repor... | Committed | Cost architecture |
| [D09](D09-add-limit-trade-through-fill-assumption.md) | Add LIMIT_TRADE_THROUGH fill assumption (fill only if price exceeds limit by ε) alongsi... | Committed | Execution / fill logic |
| [D10](D10-gap-through-stop-fills-at-the.md) | Gap-through-stop fills at the bar open, not the stop price | Committed | Execution / fill logic |
| [D11](D11-rename-vwap-fill-assumption-to-typical.md) | Rename "VWAP" fill assumption to TYPICAL_PRICE_OPTIMISTIC | Committed | Execution / fill logic |
| [D12](D12-introduce-instrument-abstraction-positions-fills-reference.md) | Introduce Instrument abstraction: positions/fills reference instrument objects, not tic... | Committed | Instruments |
| [D13](D13-coststacks-are-per-instrument-class.md) | CostStacks are per-instrument-class | Committed | Instruments |
| [D14](D14-crypto-promoted-above-options-in-build.md) | Crypto promoted above options in build priority; implement fully with a funding-rate ca... | Committed | Instruments |
| [D15](D15-fx-as-plumbing-not-strategy-venue.md) | FX as plumbing, not strategy venue | Committed | Instruments |
| [D16](D16-options-implemented-as-a-well-formed.md) | Options implemented as a well-formed stub: real dataclass fields + contract multiplier ... | Deferred | Instruments |
| [D17](D17-instruments-own-their-trading-calendar-instrument.md) | Instruments own their trading calendar: instrument.periods_per_year(bar_duration); audi... | Committed | Instruments |
| [D18](D18-per-asset-class-data-fetchers-behind.md) | Per-asset-class data fetchers behind one DataSource interface: get_bars(instrument, tim... | Committed | Data & portfolio layers |
| [D19](D19-portfoliostate-converts-all-positions-to-base.md) | PortfolioState converts all positions to base currency for NAV | Committed | Data & portfolio layers |
| [D20](D20-trialregistry-every-backtest-run-appends-config.md) | TrialRegistry: every backtest run appends config hash + params + headline metrics to lo... | Committed (urgent) | Validation & research integrity |
| [D21](D21-deflated-sharpe-ratio-added-as-a.md) | Deflated Sharpe Ratio added as a sibling to the IS/OOS overfitting ratio, not a replace... | Committed | Validation & research integrity |
| [D22](D22-pair-selection-moves-inside-the-walk.md) | Pair selection moves inside the walk-forward training windows, over a broad universe | Committed | Validation & research integrity |
| [D23](D23-synthetic-pair-null-test-generate-cointegrated.md) | Synthetic-pair null test: generate cointegrated-looking series with zero true edge; str... | Committed | Validation & research integrity |
| [D24](D24-immutable-data-snapshots-fetch-once-freeze.md) | Immutable data snapshots: fetch once, freeze with a fetch-date stamp; every trial logs ... | Committed | Data layer |
| [D25](D25-cleaner-returns-data-a-change-report.md) | Cleaner returns data + a change report; cleaning rules are explicit, versioned, and log... | Committed | Data layer |
| [D26](D26-sanity-gate-between-data-source-and.md) | Sanity gate between data source and engine: OHLC consistency (low ≤ open/close ≤ high),... | Committed / Deferred | Data layer |
| [D27](D27-pipeline-boundary-changes-to-signal-target.md) | Pipeline boundary changes to signal → target weight → orders. Strategies output desired... | Committed | Signals & strategy interface |
| [D28](D28-regime-models-obey-the-same-fitting.md) | Regime models obey the same fitting rule as pair selection: fit inside the walk-forward... | Committed | Signals & strategy interface |
| [D29](D29-pair-selection-handles-multiplicity-rank-candidate.md) | Pair selection handles multiplicity: rank candidate pairs and take top-N rather than th... | Committed | Signals & strategy interface |
| [D30](D30-risk-checks-run-per-bar-at.md) | Risk checks run per-bar at portfolio level, not only as pre-trade gates | Committed | Portfolio layer |
| [D31](D31-allocator-is-a-bare-bones-stand.md) | Allocator is a bare-bones stand-in: constant capital split across strategies, behind a ... | Committed | Portfolio layer |
| [D32](D32-structural-look-ahead-guard-strategies-receive.md) | Structural look-ahead guard: strategies receive a `DataView` accessor that physically c... | Committed | Backtest engine |
| [D33](D33-bars-for-sequencing-timestamps-for-accrual.md) | Bars for sequencing, timestamps for accrual and annualisation. All carry costs (borrow,... | Committed | Backtest engine |
| [D34](D34-explicit-rng-seed-policy-every-stochastic.md) | Explicit RNG seed policy: every stochastic component (Monte Carlo shuffle, block bootst... | Committed | Backtest engine |
| [D35](D35-configuration-becomes-declarative-simconfig-and-strategy.md) | Configuration becomes declarative: SimConfig and strategy configs are plain data (dicts... | Committed | Backtest engine |
| [D36](D36-tail-risk-metrics-are-gated-by.md) | Tail-risk metrics are gated by sample size: VaR/CVaR and extreme percentiles only repor... | Committed | Analytics |
| [D37](D37-benchmark-frame-matches-strategy-type-market.md) | Benchmark frame matches strategy type: market-neutral strategies benchmark against the ... | Committed | Analytics |
| [D38](D38-sector-momentum-is-explicitly-labelled-a.md) | Sector momentum is explicitly labelled a learning/reference strategy in the repo (READM... | Committed | Analytics |
| [D39](D39-golden-master-tests-at-least-one.md) | Golden-master tests: at least one hand-computed tiny scenario (≈5 bars, 2 trades, known... | Committed | Testing |
| [D40](D40-property-based-invariant-tests-on-the.md) | Property-based invariant tests on the simulator: cash never negative absent margin, eve... | Committed | Testing |
| [D41](D41-cross-engine-validation-run-one-identical.md) | Cross-engine validation: run one identical strategy on identical data through an establ... | Committed | Testing |
| [D42](D42-intra-bar-ambiguity-convention-when-two.md) | Intra-bar ambiguity convention: when two exits are touchable in the same bar (e.g. stop... | Committed | Backtest engine |
| [D43](D43-short-sale-cash-accounting-made-explicit.md) | Short-sale cash accounting made explicit: short proceeds credit cash but the margin req... | Committed | Portfolio layer |
| [D44](D44-engine-enforces-a-warm-up-period.md) | Engine enforces a warm-up period: no trading until the longest indicator lookback (incl... | Committed | Backtest engine |
| [D45](D45-multi-ticker-bar-alignment-policy-is.md) | Multi-ticker bar alignment policy is explicit: pairs/multi-leg strategies use inner-joi... | Committed | Data layer |
| [D46](D46-per-strategy-p-l-attribution-fills.md) | Per-strategy P&L attribution: fills are already strategy-tagged; add per-strategy virtu... | Committed | Portfolio layer |
| [D47](D47-money-is-float64-with-a-stated.md) | Money is float64 with a stated reconciliation tolerance (default 1e-6), used by every "... | Committed | Testing |
| [D48](D48-no-false-affordances-enum-values-and.md) | No false affordances: enum values and flags for unimplemented behaviour are removed or ... | Committed | Testing |
| [D49](D49-sharpe-sortino-take-an-explicit-risk.md) | Sharpe/Sortino take an explicit risk-free rate input, consistent with the D37 benchmark... | Committed | Analytics |
| [D50](D50-project-scaffolding-uv-src-layout-pytest.md) | Project scaffolding: uv package manager, src-layout, pytest + hypothesis | Committed | Tooling |
| [D51](D51-carry-accrual-day-count-convention-act365.md) | Carry accrual day-count convention: ACT/365 as a single stated default | Committed / Deferred | Backtest engine |
| [D52](D52-declarative-config-type-key-factory-registry.md) | Declarative config shape: `{"type": ..., ...params}` + a generic FactoryRegistry | Committed | Backtest engine |
| [D53](D53-refactor-regression-gate-reinterpreted-greenfield.md) | "Refactor regression" gate reinterpreted for greenfield conditions (no legacy engine to reconcile against) | Committed | Backtest engine |
| [D54](D54-coststack-instrument-interface-design.md) | CostStack + Instrument interface shapes, and toy bricks now vs. real bricks in Step 5 | Committed | Backtest engine |
| [D55](D55-pipeline-sizing-design.md) | Pipeline sizing design: stateless Sizer, capital-by-strategy as an external input | Committed | Signals & strategy interface |
| [D56](D56-dataview-never-stores-future-data.md) | DataView is constructed holding only visible bars, never given future ones | Committed | Backtest engine |
| [D57](D57-risk-monitor-gross-exposure-formula.md) | RiskMonitor's exposure formula and simulate-then-check pre-trade design | Committed | Portfolio layer |
| [D58](D58-allocator-wired-into-sizer.md) | Allocator interface, and wiring ConstantSplitAllocator into Sizer | Committed | Portfolio layer |
| [D59](D59-data-source-engine-loop-chunk-inserted.md) | Insert a minimal data-source + production-engine-loop chunk ahead of Step 5 | Committed | Data & portfolio layers |
| [D60](D60-timestampedbar-wraps-bar.md) | TimestampedBar wraps Bar rather than extending Bar's schema | Committed | Data & portfolio layers |
| [D61](D61-capital-reallocated-every-bar-from-nav.md) | Capital is reallocated every bar from current NAV, not fixed at the start | Committed | Portfolio layer |
| [D62](D62-risk-violations-recorded-not-enforced.md) | RiskMonitor violations are recorded, not enforced, in run_backtest | Committed / Deferred | Portfolio layer |
| [D63](D63-bar-alignment-inner-join-exact-timestamp.md) | Bar alignment: inner join on exact timestamp equality | Committed | Data layer |
| [D64](D64-strategy-run-backtest-multi-instrument.md) | Strategy and run_backtest generalized to multi-instrument, single is the N=1 case | Committed | Backtest engine |
| [D65](D65-ibkr-fixed-schedule-modeled.md) | IBKR Fixed US-equity schedule modeled; cap overrides minimum; pass-throughs deferred | Committed / Deferred | Cost architecture |
| [D66](D66-sqrt-impact-functional-form.md) | Sqrt impact: fraction ∝ √Q, dollars ∝ Q^1.5; static σ/ADV params for now | Committed / Deferred | Cost architecture |
| [D67](D67-portfolio-carry-slot-snapshot-semantics.md) | Portfolio-level carry slot on CostStack; start-of-bar snapshot semantics | Committed | Backtest engine |
| [D68](D68-cost-sweep-harness-design.md) | Cost sweep harness: per-brick scaling wrappers, strategy factories, minimal markdown tearsheet | Committed | Cost architecture |
| [D69](D69-zscore-pairs-first-number-strategy.md) | Z-score pairs as the first-number strategy; "walk-forward" read as trailing-only simulation | Committed | Signals & strategy interface |
| [D70](D70-committed-csv-fixture-as-frozen-snapshot.md) | Committed CSV fixture as the pre-Step-7 frozen snapshot; calibration and adjusted-price caveats | Committed / Deferred | Data layer |
| [D71](D71-borrow-fee-brick.md) | BorrowFee brick: shorts pay, longs free | Committed | Cost architecture |
| [D72](D72-content-addressed-snapshot-store.md) | Content-addressed SnapshotStore; quarantine semantics; meta refreshes on re-freeze | Committed | Data layer |
| [D73](D73-cleaner-ruleset-v1.md) | Cleaner ruleset clean-v1: drop-and-report, never rewrite; permanence discriminates prints from crashes | Committed | Data layer |
| [D74](D74-validator-thresholds-frame-robust.md) | Validator thresholds calibrated to observed data; frame-robust split awareness | Committed | Data layer |
| [D75](D75-corporate-actions-two-frames.md) | Corporate actions: two price frames, event-flow brick slot, split scaling, naive timestamps | Committed | Data layer |
| [D76](D76-v2-result-alongside-v1.md) | v2 first-number published alongside v1; v1 preserved as the milestone | Committed | Data layer |
| [D77](D77-golden-master-scope-instrumentation.md) | THE golden master covers the engine as built; BacktestResult gains fills/cash instrumentation | Committed | Testing |
| [D78](D78-property-test-conventions.md) | Property-test conventions: derandomized hypothesis, shadow accountant, reset-guarantee reinterpretation | Committed | Testing |
| [D79](D79-cross-engine-vectorbt.md) | Cross-engine reconciliation via vectorbt target-percent; precomputed-weights design | Committed | Testing |
| [D80](D80-metrics-conventions.md) | Metrics conventions: required rf/periods args, geometric rf, ±inf on zero variance | Committed | Analytics |
| [D81](D81-tail-gating-monte-carlo.md) | Tail gating: ≥30 tail observations; Monte Carlo: seeded block bootstrap, n=10k | Committed | Analytics |
| [D82](D82-d38-label-reinterpretation.md) | D38 reinterpreted: no sector momentum exists; the label convention is enforced on what does | Committed | Analytics |
| [D83](D83-quantstats-xgate.md) | Step 9's X-gate reference is quantstats; exact ties, one API quirk documented | Committed | Analytics |
| [D84](D84-options-scoping-writeup.md) | The options extension scoping write-up: six hard problems, Lego audit, trigger conditions | Committed / Deferred | Instruments |
| [D85](D85-walk-forward-guarded-fitting.md) | Walk-forward with structurally-guarded fitting; Gatev top-N selection with logged multiplicity | Committed | Validation & research integrity |
| [D86](D86-dsr-implementation.md) | DSR: stdlib normal functions, registry-fed N and V, checkpoint-recovery of the paper's example | Committed | Validation & research integrity |
| [D87](D87-synthetic-null-construction.md) | Synthetic nulls: random-walk spread, not OU; test calibration; block-paths exposure | Committed | Validation & research integrity |
| [D88](D88-universe-fixture.md) | The 57-ETF universe fixture: composition, coverage policy, gzip | Committed | Data layer |
| [D89](D89-pairs-study-runner-design.md) | Study runner design: one multi-strategy run per window, warm-up prefix, chaining, research boundary | Committed | Validation & research integrity |
| [D90](D90-study-dsr-methodology.md) | Study DSR methodology: registry-fed N and V; pair-level multiplicity as an explicit optimism caveat | Committed | Validation & research integrity |
| [D91](D91-executable-tutorial.md) | The tutorial's code is executed by the test suite, not merely written | Committed | Testing |
| [D92](D92-cointegration-selection-v2.md) | Study v2 selection: Gatev prefilter → EG β coherence window → ADF rank; one variable per version | Committed | Validation & research integrity |
| [D93](D93-adf-implementation.md) | Own ADF implementation, statistic only, anchored against statsmodels | Committed | Validation & research integrity |
| [D94](D94-beta-hedged-trading-v3.md) | Study v3 β-hedged trading: constant-gross normalization, factory hook, β=1 equivalence | Committed | Validation & research integrity |
| [D95](D95-capacity-analysis-methodology.md) | Capacity analysis: direct AUM sweep with size-aware bricks, recorder-wrapper attribution | Committed | Validation & research integrity |
| [D96](D96-gross-exposure-study.md) | Gross exposure study: leg_weight as the single variable, the margin threshold as the mechanism | Committed | Validation & research integrity |
| [D97](D97-phase-g-writeup-structure.md) | Phase G writeup: methodology-first structure, skeleton-with-real-numbers, anchor-tested consistency | Committed | Validation & research integrity |
| [D98](D98-dsr-units-and-trial-pool.md) | DSR units contract and trial-pool semantics (audit F1/F8/F9) | Committed | Validation & research integrity |
| [D99](D99-loud-guards-duplicates-empty-runs-event-ordering.md) | Loud guards: duplicate timestamps, empty runs, grid drift, event ordering (audit) | Committed | Data layer |
| [D100](D100-carry-components-consulted.md) | carry_components() is consulted, not decorative (audit F24) | Committed | Instruments |
| [D101](D101-pretrade-enforcement-and-sleeve-instrumentation.md) | Opt-in pre-trade enforcement; sleeve-level fill instrumentation (audit F5/F12) | Committed | Portfolio layer |
| [D102](D102-declarative-stack-config-and-train-window-calibration.md) | Declarative config for the real cost stack; train-window impact calibration (audit F2/F4) | Committed | Backtest engine |
| [D103](D103-fill-timing-next-open.md) | Fill timing: next-bar-open mode alongside same-bar-close (audit F3) | Committed | Execution / fill logic |
| [D104](D104-property-suite-scope-extension.md) | Property-suite scope: signed positions, real OHLC bars, unconditional accountants (audit F14) | Committed | Testing |
| [D105](D105-convention-sensitivity-study.md) | Convention-sensitivity study: fill timing x impact calibration on the v2 configuration | Committed | Validation & research integrity |
| [D106](D106-conventions-pinned.md) | Conventions pinned: share rounding, carry mark timing, bootstrap block length (audit) | Committed | Backtest engine |
| [D107](D107-deferrals-recorded.md) | Deferrals recorded per R3: margin lock, fill menu, FX brick, IS/OOS ratio, registry artifacts | Committed / Deferred | Scope & sequencing |
| [D108](D108-crypto-as-equity-instrument.md) | BTC/ETH modelled as `Equity(quantity_precision=8)`, not a new crypto instrument | Committed | Instruments |
| [D109](D109-breakout-strategy-design.md) | Long-flat breakout: filters and sizing as bricks, hysteresis enforced structurally | Committed | Signals & strategy interface |
| [D110](D110-vol-target-sizing-lives-in-the-weight.md) | Inverse-volatility sizing lives in the signal→target-weight stage, not the portfolio layer | Committed | Signals & strategy interface |
| [D111](D111-volume-filter-blocked-on-bar-schema.md) | Volume-confirmation filter NOT built: `Bar` carries no volume, and neither workaround is acceptable | Superseded by D168 | Signals & strategy interface |
| [D112](D112-trade-episode-diagnostics.md) | A "trade" is a position episode, and the diagnostics say so once | Committed | Analytics |
| [D113](D113-continuous-oos-run-with-parameter-schedule.md) | Walk-forward as one continuous OOS run with a parameter schedule, not chained windows | Committed | Validation & research integrity |
| [D114](D114-crypto-fee-tiers-are-fees-only.md) | Crypto cost tiers model an exchange fee and nothing else, stated loudly | Committed | Cost architecture |
| [D115](D115-buy-and-hold-benchmark-is-a-fixed-quantity.md) | The buy-and-hold benchmark holds a fixed quantity, not a fixed weight | Committed | Analytics |
| [D116](D116-dsr-trial-pool-is-configurations.md) | For a parameter-swept study the DSR trial pool is configurations, not windows | Committed | Validation & research integrity |
| [D117](D117-d38-label-gate-binds-on-the-breakout-strategy.md) | D38's label gate binds for the first time: the breakout strategy is labelled directional | Committed | Analytics |
| [D118](D118-vol-target-swept-not-assumed.md) | The vol target is swept, and it is a risk dial rather than a Sharpe improvement | Committed | Signals & strategy interface |
| [D119](D119-risk-equalised-constant-fraction-benchmark.md) | A constant-fraction benchmark at the strategy's own average exposure | Committed | Analytics |
| [D120](D120-paired-bootstrap-on-sharpe-differences.md) | Sharpe differences get a paired block bootstrap, and the risk-adjusted claim is retracted | Committed | Validation & research integrity |
| [D121](D121-era-decomposition-answers-the-crypto-question.md) | Every crypto backtest reports its era decomposition: annual breakdown + start-date sensitivity | Committed | Validation & research integrity |
| [D122](D122-crypto-pairs-study-is-its-own-harness.md) | The BTC/ETH pairs study gets its own harness; `ZScorePairsStrategy` is reused unmodified | Committed | Validation & research integrity |
| [D123](D123-continuous-stitching-for-the-pairs-book.md) | The pairs study runs continuously too, and the chained seam is priced rather than argued about | Committed | Validation & research integrity |
| [D124](D124-pairs-costs-borrow-is-not-zero.md) | A pairs book pays borrow and margin; the rates are stated, swept, and never silently zero | Committed | Cost architecture |
| [D125](D125-cointegration-is-tested-with-thresholds.md) | Cointegration is a tested premise here, not an assumption; and this is where the ADF gets critical values | Committed | Validation & research integrity |
| [D126](D126-dsr-pool-excludes-convention-and-cost-sensitivities.md) | The DSR pool is strategy configurations; convention and cost sensitivities are re-pricings, not trials | Committed | Validation & research integrity |
| [D127](D127-pair-diagnostics-and-the-d45-truncation.md) | Pair diagnostics are computed locally, and D45's truncation to ETH's inception is reported as the sample definition | Committed | Analytics |
| [D130](D130-bar-shape-resampling-null.md) | The serial-dependence null resamples BAR SHAPES, by segmented permutation, not the block bootstrap | Committed | Validation & research integrity |
| [D131](D131-block-ladder-measures-the-dependence-horizon.md) | The block ladder is a ruler for the dependence horizon, and its sign is inverted from D23 | Committed | Validation & research integrity |
| [D132](D132-d36-honoured-by-parallelism-not-deviation.md) | D36's n ≥ 10,000 honoured by parallelising rather than deviating; every p-value carries its Monte Carlo SE | Committed | Analytics |
| [D133](D133-trade-concentration-and-the-drawdown-sampling-distribution.md) | Trade concentration in two units, and the drawdown claim bootstrapped against BOTH benchmarks | Committed | Analytics |
| [D140](D140-crypto-universe-selection-policy.md) | The crypto-universe fixture: a pre-stated selection policy that deliberately admits assets that died | Committed | Data layer |
| [D141](D141-one-configuration-across-the-cross-section.md) | One fixed configuration across the whole cross-section; the universe is the only variable | Committed | Validation & research integrity |
| [D142](D142-dsr-pool-is-the-cross-section.md) | For a fixed-rule cross-sectional study the DSR trial pool is the symbols | Committed | Validation & research integrity |
| [D143](D143-sanity-gate-overridden-for-crypto-cross-section.md) | The D26/D74 sanity gate is ETF-calibrated; the crypto cross-section overrides it explicitly and reports every violation | Committed / Deferred | Data layer |
| [D144](D144-peg-screen-added-after-first-run.md) | A peg screen was added to the universe policy after its first run, and the amendment is recorded rather than hidden | Committed | Data layer |
| [D160](D160-intraday-data-reality-and-the-1h-study-base.md) | Intraday data reality: 1h is the study base, coarser bars are resampled, and the cleaner is called on prices only | Committed | Data layer |
| [D161](D161-the-resampling-contract.md) | The resampling contract: exact OHLCV on 00:00-UTC buckets, day-level drop policy, and the daily-fixture reconciliation finding | Committed | Data layer |
| [D162](D162-two-designs-calendar-horizon-and-bar-count.md) | Two frequency designs — constant calendar horizon and constant bar count — never conflated | Committed | Validation & research integrity |
| [D163](D163-sub-hourly-is-a-turnover-measurement-not-a-result.md) | 15m/30m are a turnover-and-cost measurement, not a performance result, and the walk-forward is not shrunk to make them one | Committed | Validation & research integrity |
| [D164](D164-dsr-units-for-a-multi-frequency-pool.md) | For a multi-frequency trial pool, D98's shared period is the calendar day, not the bar | Committed | Validation & research integrity |
| [D165](D165-the-crossover-rule-and-the-spliced-gross-edge.md) | The crossover is read three ways, and the load-bearing reading splices a measured cost curve onto a ten-year gross edge | Committed | Analytics |
| [D166](D166-direction-is-omitted-from-config-at-its-default.md) | The breakout brick is sign-parameterized ({long, flat, short} state enum, direction-aware gate) and `direction` is omitted from `config()` at its LONG default so v1 trial hashes survive | Committed | Signals & strategy interface |
| [D167](D167-at-trigger-features-are-logged-on-an-open-map.md) | At-trigger features live on an open F-numbered map, are computed at the trigger bar (not the entry bar), and unavailable never means imputed | Committed | Diagnostics & reporting |
| [D168](D168-volume-rides-inside-the-dataview.md) | Volume reaches strategy code inside `DataView` as an aligned sliced series, in three explicitly different states — absent, gapped, and required-but-unwired (loud) | Committed | Signals & strategy interface |
| [D169](D169-the-short-book-and-its-close-based-stop.md) | The short book ships with a CLOSE-based stop because the engine has no intrabar execution; the gap-through shortfall is measured, tail discipline is enforced at construction, and borrow is charged | Committed | Signals & strategy interface |
| [D170](D170-intrabar-stop-execution.md) | Intrabar stop orders in `run_backtest` via the existing `stop_fill_price`; the engine records which fills a stop caused, and the short book's stop turns out to be present but not binding | Committed | Backtest engine |
| [D171](D171-the-stop-family-sweep.md) | Trailing-channel, ATR and chandelier stops added and swept; stop levels ratchet, and binding more helps BTC (+0.94 rank corr) while hurting ETH (-0.43) | Committed | Signals & strategy interface |
| [D172](D172-the-short-book-deflated.md) | The short book gets a trial registry and a deflated Sharpe; DSR lands at 0.04-0.52 and its best results do not survive the search that produced them | Committed | Validation & research integrity |
| [D173](D173-swing-structure-pre-registration.md) | Swing-structure stop and gate, with a pre-registered prediction that neither beats the incumbent; pivot levels not drawn trend lines, and the k-bar confirmation lag handled explicitly | Committed (H1 falsified) | Validation & research integrity |
| [D174](D174-swing-k2-on-the-universe.md) | `swing_k2` beats `trail_10` on 69% of 62 coins including the ones that died, but the book loses ~50% on the median coin — the stop is real, the strategy is not | Committed | Validation & research integrity |
| [D175](D175-no-margin-call-or-liquidation-model.md) | The engine has no margin call, liquidation or borrow recall; three short accounts passed -100% (worst -1106%) with stops active | Deferred | Backtest engine |
| [D176](D176-phase-2-diagnostic-gaps-closed.md) | Phase 2's squeeze-event and per-window correlation diagnostics built and wired; the dead squeeze function had the adverse direction backwards for shorts | Committed | Diagnostics & reporting |
