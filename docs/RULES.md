# Standing Rules

Unlike [decisions](decisions/README.md), these aren't one-time calls — they're constraints
that apply continuously across the project's life. Originally logged as R1–R4 in
[`DESIGN_DECISIONS.md`](../DESIGN_DECISIONS.md). Add new rules here as R5, R6, ...

These are specific and binding. For the underlying values that generated them — useful when
a new situation isn't covered by an existing rule — see [`../PHILOSOPHY.md`](../PHILOSOPHY.md).

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

New decisions go in `docs/decisions/` (next number: **D249**), shipped changes go in
[`CHANGELOG.md`](../CHANGELOG.md), current work-in-progress goes in [`AITODO.md`](../AITODO.md).

**Because:** the original four docs (`MASTER_PROJECT_DOC.md`, `DESIGN_DECISIONS.md`,
`VERIFICATION_SCHEME.md`, `DEVELOPMENT_TIMETABLE.md`) were written before implementation
started and are frozen planning artifacts; the doc suite added on 2026-07-13 is what stays
current once code exists.

---

## R6. A hurdle that names a test is not cleared until that test is run

A record claiming a hurdle passed must point at the artifact field holding that test's output.
A runner implementing a multi-leg hurdle must compute **every** leg or fail loudly.

**Because:** D217 and D218 both wrote hurdle A as *"≥ +0.10 Sharpe, above the paired
bootstrap's p95"* and **neither runner ever computed a bootstrap** — `ladder_deltas` compared
the point estimate to +0.10 and stopped. Both records read as though the second leg had passed.
When D229 built the leg and D230 swept all 24 reported deltas through it, **zero cleared the
hurdle as claimed**, against 8 that cleared it as scored.

Prose that is not enforced in code gets skipped, and a hurdle that exists only in prose is
worse than no hurdle: it manufactures confidence nobody earned.

**Scope:** binding on every study. Introduced by [D230](decisions/D230-the-bootstrap-sweep.md).

## R7. Null the overlay, not the book

A study that applies an **overlay** to an existing book — a stop, a target, a partial exit,
anything that modifies positions a base rule already chose — must be controlled against a null
that **keeps the base book and randomises only the overlay's decisions, matched on how many it
makes.**

A rotation null is the wrong control here. Rotation randomises the *whole book's* timing, which
is the right question for an **entry** rule and the wrong one for a rule that modifies an
existing book.

**Because:** D235 tested seven stop and target overlays. All seven beat their baseline and the
pre-registered rotation null cleared — at a p95 of **−0.284**, a bar anything not actively
harmful would clear, because a rotated 17.5%-exposure book scores far below the unrotated 18.9%
baseline by construction. Against the correct null — cutting **the same 146 of 1,124 trades**
short at *random* bars — the best overlay landed at the **63rd percentile**, with the median
random-exit book scoring +0.785 against the real +0.794. **The trigger carried no information at
all**, and the pre-registered hurdle said the opposite.

Corollary, and it is the cheaper half of the rule: **a hurdle that everything clears is not
evidence, it is a broken hurdle.** A clean sweep of positive results is a tell, not a triumph —
the same tell that surfaced D224's look-ahead defect.

**Scope:** binding on every study applying an overlay. Introduced by
[D235](decisions/D235-stops-and-targets-on-the-recovery-rule.md).

## R8. Admission to the book requires a pre-registered out-of-sample test

A strategy enters [`BOOK.md`](BOOK.md) only after a test whose **hurdles were committed before
the withheld data was touched**, and it enters carrying its own **falsification conditions** and
a full statement of what is still wrong with it.

**Because:** D215 committed that a positive needs its own pre-registration and holdout, and
nine studies then produced nothing that reached one. When S1 finally did, the temptation was to
report the pass and not the four things still broken about it — a +0.978-correlated holdout, an
interval containing zero, a failing sample-size hurdle, and a loss to buy-and-hold over the only
forward period tested. **A book entry that records only its evidence is a marketing document.**

**Corollary:** a place in the book is **not** a decision to trade. Sizing, leverage and capital
allocation are separate decisions, recorded separately.

**Scope:** binding. Introduced alongside [S1](BOOK.md#s1--the-recovery-rule).

