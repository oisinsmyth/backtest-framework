# Quant Backtesting Framework

**A backtesting framework where correctness is enforced by structure rather than by care.**
Every friction, instrument and validation check is a swappable, individually-tested component;
the simulator is anchored to ledgers computed by hand; every design call is written down before
it is acted on. The research it has produced is mostly negative — and that is the evidence it
works. A measuring instrument earns trust by returning negatives when negatives are true.

| | |
|---|---|
| **1,839 tests** | hand-computed golden masters · integration · property · unit |
| **741 decision records** | one per design call, D1 → D537, append-only and amended in writing |
| **penny-exact** | the simulator reconciled against vectorbt, an independently written engine |
| **7 defects caught** | by a guard, an assertion or an implausible number — never by inspection |

The seven are enumerated in the final report linked below, with what each one taught. A later
catch is worth its own line: D279's lag audit re-derives the held set from `score[:, t-1]` in a
second implementation that never calls the selection function, and it found that **~93% of that
study's apparent edge was the bug**.

## Five minutes

```bash
uv sync
uv run pytest -q tests/golden     # 91 ledger-anchored tests, 0.58s
```

That runs on a bare clone — the golden masters use synthetic bars and need no market data. The
full suite is `uv run pytest -q`, 6m34s here. **On a clone it is 1,699 passed and 136 skipped in
2m47s** — measured by hiding the panels and running it, not asserted; each of the 136 names the
file it wanted. The panels left git in
[D536](docs/decisions/D536-manifest-only-storage-for-the-bulk-panels.md) at 844 MB;
[`data/data_manifest.json`](data/data_manifest.json) carries the sha256 and git blob id of every
one, so a skipped test names data that is still recoverable.

**Three ways in.** What the framework *guarantees* is in [`tests/`](tests/), four tiers that do
different jobs: `golden/` anchors fills and costs to ledgers worked out by hand, `property/`
quantifies over generated paths rather than chosen ones, `integration/` runs whole studies, and
`unit/` pins the parts. What it has been *used for* is the studies below, which exist to show a
strategy is a swappable brick. Why anything is the way it is, is in
[`docs/decisions/`](docs/decisions/README.md) and [`PHILOSOPHY.md`](PHILOSOPHY.md).

## Where things are

```
src/backtest_framework/   the instrument — 85 modules, engine · costs · instruments · data · analytics
tests/                    the exhibit — golden · property · integration · unit
docs/
  decisions/              741 records, D1 → D537, one per design call     [index](docs/decisions/README.md)
  results/                48 studies, five of them featured               [index](docs/results/README.md)
  internal/               working state: the live queue, the task list, an old self-audit
  RULES.md  FINDINGS.md  BOOK.md  TUTORIAL.md
scripts/                  the research runners — 586 files, one-shot by design
data/                     evidence, committed; the bulk panels are manifested, not committed
CONTRIBUTING.md           how to change any of it: gate before code
```

Two boundaries that are load-bearing rather than tidy: **`src/` never imports from `scripts/`** —
the instrument does not depend on any use of it — and **`data/` holds evidence while
[`data/data_manifest.json`](data/data_manifest.json) holds the checksums of the 118 bulk panels
that are deliberately not in git.

**The final report is [`docs/results/final_report.html`](docs/results/final_report.html)**
— the whole project in one document: what was tested, how each idea died, the seven real
defects the guards caught, and the two properties that survived (neither of which is
signal). Published at
<https://claude.ai/code/artifact/322b8663-8de5-4c75-b798-988d50281d63>.

It is the single source for that summary — deliberately not mirrored as Markdown, because
two copies of the same prose drift apart, which is the most repeated defect in this
project's own history (D176, D183, D186).

**The research output is [`docs/writeup.md`](docs/writeup.md)** — the five-study
measurement of whether ETF pairs trading clears real frictions (draft skeleton; every
headline number final and cross-checked against its source artifact by the test suite).

**The studies are demonstrations, and they are indexed rather than recited here.**
[`docs/results/`](docs/results/README.md) holds all 48 with five featured for what each one proves
about the instrument — that a strategy is a swappable brick, that neutrality engineering can work
while the thesis it serves fails, that a pre-registered stop fires when it should.

The single sharpest fact in the programme is in that index: the MACD ladder's best cell **clears
six of seven hurdles**, including buy-and-hold on Sharpe at half the drawdown, and fails only the
deflated-Sharpe floor — **+0.334 at the fresh count of 42 looks, +0.638 at the verdict count of
45,783**. A result that would have been publishable as a first study and is not publishable as the
45,783rd. The trial registry is what knows the difference.

**Start with [`PHILOSOPHY.md`](PHILOSOPHY.md) if you're new here.** It's the guiding layer
above everything else — the small set of values (trust by structure, honesty over comfort,
anti-self-deception, composability, scope discipline) that generated every decision below,
and the first thing any new decision should be checked against.

**Data providers:** [`docs/alpha_vantage_api.md`](docs/alpha_vantage_api.md) covers the intraday equity provider — read it before adding any
new fetcher, since several load-bearing facts about it are measured rather than documented.

**To USE the framework, read [`docs/TUTORIAL.md`](docs/TUTORIAL.md)** — the full path from
setup to research output, with every example executed verbatim by the test suite so it
cannot rot.

## Doc suite

**Planning (frozen, pre-implementation snapshots — 2026-07-13):**
- [`MASTER_PROJECT_DOC.md`](MASTER_PROJECT_DOC.md) — single-file collation of the three docs below, as they stood before build started
- [`DESIGN_DECISIONS.md`](DESIGN_DECISIONS.md) — original running log, D1–D49 + rules R1–R4 (superseded by the split docs below; kept for history)
- [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md) — the 12 build steps and their test gates. A step is done when its gate passes, not when code exists.
- [`DEVELOPMENT_TIMETABLE.md`](DEVELOPMENT_TIMETABLE.md) — phased schedule (weeks 1–24) and pre-committed kill criteria.

**Live (kept current as implementation proceeds):**
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to change the framework: gate before code, which test tier, adding a brick, recording the decision
- [`PHILOSOPHY.md`](PHILOSOPHY.md) — the guiding design philosophy; changes rarely and deliberately
- [`docs/decisions/`](docs/decisions/README.md) — one file per design decision, 741 of them, D1 → D537. The index is a curated table for D1–D284 and a generated register below it.
- [`docs/results/`](docs/results/README.md) — 48 studies, indexed, with five featured for what each proves about the instrument
- [`docs/RULES.md`](docs/RULES.md) — standing scope/sequencing rules (R1–R16), apply continuously rather than once
- [`CHANGELOG.md`](CHANGELOG.md) — what shipped and when, Keep a Changelog format. Rationale lives in the decision records, not here.
- [`AITODO.md`](docs/internal/AITODO.md) — Claude's current working task list for this project. Not a roadmap; reflects the next few steps only.

## Working conventions

- **A step is done when its [VERIFICATION_SCHEME.md](VERIFICATION_SCHEME.md) gate passes**, not when code exists.
- **Every design decision gets a record** in `docs/decisions/`, formatted as decision + rationale, per R4 in [`docs/RULES.md`](docs/RULES.md). This includes on-the-fly decisions made mid-implementation, not just pre-planned ones.
- **R1 is binding during execution sessions**: no framework scope-creep before the framework produces one real number (the XLE/XOP walk-forward). See [`docs/RULES.md`](docs/RULES.md).
- Version control: local git only, no remote configured yet.

## Status

**The framework is stable; the research programme is still running.** All in-scope
verification-scheme steps (1–9, 11, 12) passed their gates, and the simulator has not needed to
change to carry any study since — which is the claim the gates existed to test.

What has changed is the subject. The ETF pairs studies in [`docs/writeup.md`](docs/writeup.md) and
the crypto work (D108–D217) were the first phase; the programme has since run through **D537**,
into intraday futures microstructure, execution cost measurement at contract minimum size, and a
components ledger for a prop account. Those records live in
[`docs/decisions/`](docs/decisions/README.md) and are not summarised here — **this README documents
the instrument, and the instrument is what has stayed still.**

The studies themselves are in [`docs/results/`](docs/results/README.md), indexed and dated. That
index is the current statement of what has been run; this page is not.
