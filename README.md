# Quant Backtesting Framework

A Lego-brick-modular backtesting framework built to run a market-neutral pairs-trading study
(starting with XLE/XOP) as a research portfolio piece. Governing principle: trust is enforced
by structure, not convention — every friction, instrument, and validation check is a swappable,
individually-tested component. Research output is the product; the framework is the instrument.

Implementation has not started yet. This repo currently holds the full planning doc suite.

## Doc suite

**Planning (frozen, pre-implementation snapshots — 2026-07-13):**
- [`MASTER_PROJECT_DOC.md`](MASTER_PROJECT_DOC.md) — single-file collation of the three docs below, as they stood before build started
- [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) — original running log, D1–D49 + rules R1–R4 (superseded by the split docs below; kept for history)
- [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md) — the 12 build steps and their test gates. A step is done when its gate passes, not when code exists.
- [`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md) — phased schedule (weeks 1–24) and pre-committed kill criteria.

**Live (kept current as implementation proceeds):**
- [`docs/decisions/`](docs/decisions/README.md) — one file per design decision, D1–D49 migrated + D50 onward as they're made
- [`docs/RULES.md`](docs/RULES.md) — standing scope/sequencing rules (R1–R5), apply continuously rather than once
- [`CHANGELOG.md`](CHANGELOG.md) — what shipped and when, Keep a Changelog format. Rationale lives in the decision records, not here.
- [`AITODO.md`](AITODO.md) — Claude's current working task list for this project. Not a roadmap; reflects the next few steps only.

## Working conventions

- **A step is done when its [VERIFICATION_SCHEME.md](VERIFICATION_SCHEME.md) gate passes**, not when code exists.
- **Every design decision gets a record** in `docs/decisions/`, formatted as decision + rationale, per R4 in [`docs/RULES.md`](docs/RULES.md). This includes on-the-fly decisions made mid-implementation, not just pre-planned ones.
- **R1 is binding during execution sessions**: no framework scope-creep before the framework produces one real number (the XLE/XOP walk-forward). See [`docs/RULES.md`](docs/RULES.md).
- Version control: local git only, no remote configured yet.

## Status

Pre-implementation. Next up: Step 1 of the verification scheme — TrialRegistry + the two
un-retrofittable bug fixes (D10 gap-through-stop, D33 calendar-day carry accrual). See
[`AITODO.md`](AITODO.md) for the live task list.
