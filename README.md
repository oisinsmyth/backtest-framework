# Quant Backtesting Framework

**A backtesting framework where correctness is enforced by structure rather than by care.**
Every friction, instrument and validation check is a swappable, individually-tested component;
the simulator is anchored to ledgers computed by hand; every design call is written down before
it is acted on. The research it has produced is mostly negative — and that is the evidence it
works. A measuring instrument earns trust by returning negatives when negatives are true.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/figures/dsr-hurdle-vs-look-count.dark.svg">
  <img src="docs/figures/dsr-hurdle-vs-look-count.svg" width="880"
       alt="A log-scaled chart of trial count against annualised Sharpe. The MACD ladder's best cell sits at a flat 0.4957 while the deflated-Sharpe hurdle rises from below it to 0.6377 at 45,783 looks, crossing the result at 1,086 looks.">
</picture>

**The same result, publishable and not publishable.** The MACD ladder's best cell earns 0.4957 and
clears six of seven hurdles. The seventh is the noise floor a *selected* best result must beat, and
it rises with the number of looks taken: 0.3340 at the 42 this study spent, 0.6377 at the 45,783
the trial registry actually carries. It stops clearing at **1,086** — a fact nobody in this project
knew until the curve was drawn. [Five more figures](docs/figures/README.md), each about the
instrument rather than a strategy.

| | |
|---|---|
| **2,045 tests** | hand-computed golden masters · integration · property · unit |
| **penny-exact** | the simulator reconciled against vectorbt, an independently written engine |
| **7 defects caught** | by a guard, an assertion or an implausible number — never by inspection |
| **MIT licensed** | [`LICENSE`](LICENSE) |

The inventory, measured from the git index rather than typed:

<!-- COUNTS:START -->

| | |
|---|---|
| **743 decision records** | over **500** decision numbers — a pre-registration and its result share one number |
| **46 library modules** | across 11 packages, plus 26 in `research/`, which is study code rather than framework |
| **62 studies** | in [`docs/results/`](docs/results/README.md), five of them featured |
| **146 test files** | golden · property · integration · unit |
| **591 research runners** | in `scripts/`, one-shot by design |
| **8 figure builders** | in `scripts/figures/`, regenerated and checked in CI |

<sub>Generated from the git index by `scripts/build_readme_counts.py`; `tests/unit/test_readme_counts_are_current.py` fails if this block drifts.</sub>

<!-- COUNTS:END -->






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
full suite is `uv run pytest -q`, 3m31s here on a quiet machine and up to 7m26s under load.
**On a clone it is 1,707 passed and 136 skipped in 2m56s** — measured on 2026-09-16 by cloning this repository into an empty directory and running
it, not by reasoning about one from inside the working copy. That distinction earned its keep the
first time: the clone failed three tests the working copy could not, on a line-ending convention
the working copy predates. Each of the 136 skips names the file it wanted. The panels left git in
[D536](docs/decisions/D536-manifest-only-storage-for-the-bulk-panels.md) at 844 MB — which is what
a **checkout** no longer carries; they remain in the history, so a `git clone` is about 1.1 GB, of
which 967 MB is `.git`. [`data/data_manifest.json`](data/data_manifest.json) carries the sha256
and git blob id of every one, so a skipped test names data that is still recoverable.

**Three ways in.** What the framework *guarantees* is in [`tests/`](tests/), four tiers that do
different jobs: `golden/` anchors fills and costs to ledgers worked out by hand, `property/`
quantifies over generated paths rather than chosen ones, `integration/` runs whole studies, and
`unit/` pins the parts. What it has been *used for* is the studies below, which exist to show a
strategy is a swappable brick. Why anything is the way it is, is in
[`docs/decisions/`](docs/decisions/README.md) and [`PHILOSOPHY.md`](PHILOSOPHY.md).

## Where things are

```
src/backtest_framework/   the instrument — engine · costs · data · instruments · validation ·
                          analytics · registry · simulator · pipeline · config · strategies
                          (research/ sits alongside and is study code, not framework surface)
tests/                    the exhibit — golden · property · integration · unit
docs/
  ARCHITECTURE.md         what the framework IS: the loop, the seams, the guards
  figures/                six generated SVGs, one per property   [index](docs/figures/README.md)
  decisions/              one record per design call, D1 → D537   [index](docs/decisions/README.md)
  results/                every study, five featured              [index](docs/results/README.md)
  specs/                  the models and prompts the studies were built from
  research/               scoping and literature for work not yet a study
  internal/               working state: the live queue, the task list, an old self-audit
  verification/           the cross-engine reconciliation
  RULES.md  FINDINGS.md  BOOK.md  STACK.md  TUTORIAL.md  writeup.md
scripts/                  the research runners, one-shot by design
data/                     evidence, committed; the bulk panels are manifested, not committed
CONTRIBUTING.md           how to change any of it: gate before code
```

The counts for each live in the block above, generated rather than typed.
`docs/figures/` holds the six generated figures; they are indexed in
[`docs/figures/README.md`](docs/figures/README.md) and every number on them is pinned to its
source artifact by a test.

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
[`docs/results/`](docs/results/README.md) holds every study, five of them featured for what each proves
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
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — what the framework *is*: the per-bar loop, the five seams with their signatures, the two-book model, and which guards are structural versus merely recorded
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — how to change the framework: gate before code, which test tier, adding a brick, recording the decision
- [`PHILOSOPHY.md`](PHILOSOPHY.md) — the guiding design philosophy; changes rarely and deliberately
- [`docs/decisions/`](docs/decisions/README.md) — one file per design decision, D1 → D537; the file and number counts are in the generated block at the top of this page. The index is a curated table for D1–D284 and a generated register below it, and a test fails if any record is in neither half.
- [`docs/results/`](docs/results/README.md) — every study, indexed, with five featured for what each proves about the instrument; the count is in the block at the top, and a test fails if a document in that directory is listed nowhere
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
