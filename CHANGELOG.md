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
