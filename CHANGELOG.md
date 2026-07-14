# Changelog

All notable changes to the framework's code are logged here, in
[Keep a Changelog](https://keepachangelog.com/) style. This tracks *what shipped and when* —
the *why* behind each change belongs in [`docs/decisions/`](docs/decisions/README.md), not here.

No tagged releases yet. Entries accumulate under **Unreleased** until the first tagged
version (likely at the Phase C "first real number" milestone, see
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)).

## [Unreleased]

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
