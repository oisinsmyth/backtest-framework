# Design Decision Records

One file per decision (D1–D49), migrated from the original running log in
[`DESIGN_DECISIONS.md`](../../DESIGN_DECISIONS.md) (kept as a historical snapshot).
New decisions are added here going forward — next number is **D50**.

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
