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

### Changed
- `config.carry_model`'s factory now builds `costs.bricks.FlatRateCarry` instead of the
  retired `CarryModel` demonstration class, per that class's own docstring (D54). No
  change to `SimConfig`'s shape or to Step 2's four passing gates.

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
