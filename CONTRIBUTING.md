# Contributing

This project's claim is that **trust is enforced by structure, not convention**
([`PHILOSOPHY.md`](PHILOSOPHY.md)). That has a practical consequence for anyone adding to it,
including its author: the order of work is not "write the code, then test it."

> **A step is done when its gate passes, not when the code exists.**
> — [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md)

[`docs/TUTORIAL.md`](docs/TUTORIAL.md) is how to *use* the framework — writing a strategy (§4),
composing a cost stack (§3), and the gotchas that bite (§11). This file is how to *change* it.
[`docs/VERIFICATION.md`](docs/VERIFICATION.md) is the other side of this page: where this one
says which tier a new test belongs in, that one says what each tier already establishes — and
what the suite cannot see. Worth reading before adding to a tier.

---

## The order of work

**1. Write the gate before the code.** Name what would have to be true, and in which test type,
before anything exists to satisfy it. The vocabulary is fixed:

| | |
|---|---|
| **U** | unit — pins one part |
| **G** | golden master — hand-computed, exact within D47 tolerance |
| **P** | property / invariant — randomised inputs |
| **I** | integration — the whole path, end to end |
| **X** | cross-validation against a reference you did not write |

**2. For a G gate, write the arithmetic first — by hand, in a `.hand.txt` beside the test.** Every
file in [`tests/golden/`](tests/golden) has one. The convention is stricter than it looks: the
ground truth is produced by a calculator that **never imports this codebase**. From
`test_the_golden_master.py`:

> If this test and the production engine ever disagree, one of them is wrong about what a backtest
> IS — that argument happens here, not at bar 3,000 of a research run.

A `.hand.txt` derived from the implementation is worse than no golden test: it launders the
implementation's assumptions into the thing that is supposed to check them.

**3. Then write the code.** If the gate passes the moment you write it, it was not a gate.

---

## Which tier does a new test belong in?

The sharpest statement of the distinction is in `tests/property/test_macd_invariants.py`, about a
unit test that checked an anchoring property at three hand-picked indices:

> That is the right shape for a **gate** and the wrong shape for a **guarantee**. This file
> quantifies over the paths and the index.

So:

- **`unit/`** — one behaviour, chosen inputs. Most things. Name the gate it discharges in the
  module docstring, the way `test_cost_stack.py` names "VERIFICATION_SCHEME.md Step 3".
- **`golden/`** — anything touching money: fills, commission, borrow, dividends, carry accrual.
  Needs a `.hand.txt`.
- **`property/`** — when the failure you fear has a *shape* you cannot enumerate. Look-ahead is the
  archetype: perturbing bars after the decision bar must change nothing before it, and no finite
  set of examples covers the shapes that would trigger it.
- **`integration/`** — the study runs, the harness composes, the report's numbers come out.

**Property tests are not deterministic in their examples.** `derandomize=True` fixes hypothesis's
seed, not the values it draws — see
[D537](docs/decisions/D537-derandomize-does-not-mean-deterministic.md). A property failure that
does not reproduce when you run its file alone is **not** thereby a flake. Reproduce it with the
whole suite.

---

## Adding a brick

The framework's shape is that frictions, instruments and allocation are independent, swappable
layers ([`PHILOSOPHY.md`](PHILOSOPHY.md) pillar 4). Adding one means implementing a socket, not
editing a blob.

| You want | Implement | Lives in | Gate |
|---|---|---|---|
| a new cost | a cost brick — `cost()` for trade and carry bricks, `flow()` for event bricks, one concern each | `src/backtest_framework/costs/bricks.py` | G, with its scenario in `tests/golden/test_cost_bricks_golden.hand.txt` |
| a new asset class | the `Instrument` protocol | `src/backtest_framework/instruments/` | U for the quantity rules, G for anything that costs money |
| new capital allocation | the allocator protocol | `src/backtest_framework/engine/allocator.py` | U, plus an I test if it changes what the engine holds |
| a new strategy | the `Strategy` protocol | `src/backtest_framework/strategies/` | see [`docs/TUTORIAL.md`](docs/TUTORIAL.md) §4 — it covers this fully |

Two rules apply to all of them:

- **No false affordances.** A knob no code reads, or a method that returns a wrong number instead
  of raising, is a bug (D48). A stub is fine; a stub that looks finished is a liability.
- **The framework is frozen** past Step 12 except for bug fixes. Study code goes in
  `src/backtest_framework/research/`, versioned per study (D89).

---

## Recording the decision

Anything non-obvious gets a record in [`docs/decisions/`](docs/decisions/README.md), in the form
*decision — because rationale* (R4). Design records use:

```markdown
# D<n> — <the decision, as a claim>

**Status:** Committed
**Date:** YYYY-MM-DD
**Category:** Testing | Data layer | Backtest engine | Cost architecture | Signals & strategy interface
**Source:** <what prompted it; which records it extends or amends>

## Decision
## Rationale
## Consequences
```

**To get the next number, ask the directory, not the index:**

```bash
ls docs/decisions | grep -oE '^D[0-9]+' | sort -V | tail -1
```

[`docs/decisions/README.md`](docs/decisions/README.md) is complete and gated — a curated table with
written summaries for D1–D284, and a generated register covering every number after it. Study
records (`PRE-REG` / `RESULT` / `ADDENDUM`) follow a different shape and are governed by R8 and R14
in [`docs/RULES.md`](docs/RULES.md), not by the template above. **Take the next number from the
directory, not from the index** — the command above is the reliable one.

**Records are amended in writing, never silently edited.** When a record stops being true, it
keeps its original text and gains a dated amendment pointing at the record that supersedes it —
see [D78](docs/decisions/D78-property-test-conventions.md) for the pattern. The same rule governs
[`docs/BOOK.md`](docs/BOOK.md), [`docs/BOOK_PROP.md`](docs/BOOK_PROP.md) and
[`docs/COMPONENTS_PROP.md`](docs/COMPONENTS_PROP.md), which are append-only.

---

## Running the gates

```bash
uv sync
uv run pytest -q tests/golden     # 101 ledger-anchored tests, no data needed
uv run pytest -q                  # everything; for runtimes see docs/RUNNING.md
uv run ruff check src tests scripts  # E4/E7/E9/F; scripts/ narrower (D543) — errors, not style
uv run mypy                          # the library only; tests and scripts are out of scope
```

All four are wired into CI ([`.github/workflows/tests.yml`](.github/workflows/tests.yml)) across
four jobs, to run on every push — **though the repository has no remote yet, so the workflow has
never executed.** It runs offline by construction: the five tests marked `live_fetch` are excluded
by default, which is D24's cross-cutting gate rather than a convenience.

**A skip is not a pass.** 53 tests skip on a clone without the bulk data panels (2026-09-17), which left git in
[D536](docs/decisions/D536-manifest-only-storage-for-the-bulk-panels.md). **Every skip that wants a
file names it — 49 of the 53** — and [`data/data_manifest.json`](data/data_manifest.json) carries
its sha256 and the git blob id it had when it was tracked. The other four want a git identity
rather than a file ([D540](docs/decisions/D540-local-config-a-clone-never-receives.md)). **Use
`requires_panel` from `tests/conftest.py` rather than writing your own `pytest.skip`**: it names
the file, and it raises rather than skipping when the manifest does not list it, so a typo'd path
cannot masquerade as absent data. If a skip count rises, something stopped being tested — read
the reasons, do not just read the colour.

---

## When in doubt

[`PHILOSOPHY.md`](PHILOSOPHY.md) is the tie-breaker, and it expects to be argued with: if a change
contradicts a principle there, either the change is wrong or the principle needs amending **in
writing**. It does not get silently overridden.
