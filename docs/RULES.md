# Standing Rules

Unlike [decisions](decisions/README.md), these aren't one-time calls — they're constraints
that apply continuously across the project's life. Originally logged as R1–R4 in
[`DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md). Add new rules here as R5, R6, ...

---

## R1. No new framework code until the framework has produced one real number

The XLE/XOP walk-forward, run through the *current* imperfect version of the framework.

**Because:** research output, not infrastructure, is what a quant portfolio is judged on,
and observed defects motivate better fixes than theorised ones.

**Scope:** suspended for design-only sessions; binding on execution sessions.

## R2. Timebox the CostStack + Instrument refactor to ~2 weeks of available time

**Because:** satisfying architecture work expands to fill all available time; the framework
earns its existence at the cost-multiplier sweep, not before.

## R3. The deferred list is explicit and written

Options wing ([`docs/options_extension.md`](options_extension.md) — not yet written, see D16),
full multi-currency accounting, live IBKR integration.

**Because:** a reasoned scoping decision is a portfolio asset; silent sprawl is a liability.

## R4. Design decisions get recorded as "decision — because rationale"

**Because:** theorising must converge to commitments, not sprawl into open-ended exploration.
[`docs/decisions/`](decisions/README.md) is the map.

---

## R5. This doc suite is source of truth; keep it in sync as code lands

New decisions go in `docs/decisions/` (next number: **D50**), shipped changes go in
[`CHANGELOG.md`](../CHANGELOG.md), current work-in-progress goes in [`AITODO.md`](../AITODO.md).

**Because:** the original four docs (`MASTER_PROJECT_DOC.md`, `DESIGN_DECISIONS.md`,
`VERIFICATION_SCHEME.md`, `DEVELOPMENT_TIMETABLE.md`) were written before implementation
started and are frozen planning artifacts; the doc suite added on 2026-07-13 is what stays
current once code exists.
