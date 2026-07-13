# AI TODO

Claude's current working task list for this project — not a roadmap (that's
[`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md)) and not a decision log (that's
[`docs/decisions/`](docs/decisions/README.md)). Kept short: only what's immediately in front of
us. Update this at the start/end of each working session — stale entries here are worse than
none.

## Now

- [x] Set up the full doc suite (ADR records, RULES.md, CHANGELOG.md, this file, README.md)
- [x] Initialize local git repo + `.gitignore`
- [x] First commit of the doc suite
- [x] Write `PHILOSOPHY.md` — the guiding design philosophy, wired into README.md and RULES.md
- [ ] Commit `PHILOSOPHY.md` + the doc-suite cross-links
- [ ] Scaffold the Python project structure (package layout, dependency management, test runner)
- [ ] Start Step 1 of `VERIFICATION_SCHEME.md`: TrialRegistry + stop-gap bug fix (D10) +
      calendar accrual fix (D33) — see Phase A of the timetable

## Next (queued, not started)

- [ ] Declarative config + factories (Step 2 / D35)
- [ ] Decide project scaffolding conventions (test framework, linting, package manager) — not
      yet recorded as a decision anywhere; needs a D50 once chosen

## Watch list (not urgent, don't forget)

- R2: CostStack + Instrument refactor (Phase B) is timeboxed to ~2 weeks once it starts — if the
  refactor regression gate isn't passing by end of week 5, split D27 out per the slip rule.
- R1: no framework scope creep beyond the current build order until the XLE/XOP walk-forward
  produces a first real number (Phase C milestone, week ~8, kill criterion at week 10).

## Log

- **2026-07-13** — Doc suite created (D1–D49 migrated to `docs/decisions/`, R1–R4 moved to
  `docs/RULES.md` + R5 added, `CHANGELOG.md`/`README.md`/`AITODO.md` created, git initialized).
  Old `DESIGN_DECISIONS.md` and `MASTER_PROJECT_DOC.md` marked as frozen historical snapshots.
  Implementation not yet started.
- **2026-07-13** — `PHILOSOPHY.md` added: five pillars (structural trust, honesty over
  comfort, anti-self-deception, composability, scope discipline) extracted from the pattern
  across the existing 49 decisions, not written fresh. Sits above `docs/RULES.md` and
  `docs/decisions/` as the thing new decisions get checked against. Requested explicitly
  before starting Step 1, so it's settled before any code exists.
