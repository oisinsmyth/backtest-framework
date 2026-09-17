# What this suite guarantees, and what it does not

**2,070 tests are collected here, and one of them skips on the machine this was written on, for
want of a data panel. This page is about what follows from that, which is less than it sounds and
more specific.**

A test count is not a guarantee. Four tiers do four different jobs here, and the useful question
about any of them is not "does it pass" but "what would have to be broken for it to fail". This
page answers that tier by tier, then says plainly what the suite cannot see.

Three neighbours, so you can tell them apart:

| | |
|---|---|
| [`VERIFICATION_SCHEME.md`](../VERIFICATION_SCHEME.md) | the **frozen** 2026-07 plan: one gate per build step, written before the code. History. |
| [`CONTRIBUTING.md`](../CONTRIBUTING.md) | which tier a **new** test belongs in, and how to write it. For contributors. |
| **this page** | what the suite, as it stands, actually establishes. For a reader deciding whether to believe it. |

Counts are measured with `uv run pytest -q --collect-only tests/<tier>` and are current at
2026-09-17. They are not left to prose discipline:
`tests/unit/test_quoted_counts_are_current.py` re-collects and fails, naming the file and line, if
any document quotes a tier count that has moved. That gate exists because this page was written
with fresh numbers on 2026-09-16 and immediately contradicted four older documents still saying
**91** golden tests when there were 101.

---

## The four tiers

### `tests/golden/` — 101 tests. *The arithmetic is right.*

Every file has a companion `.hand.txt` — 15 of them — containing the arithmetic worked out by
hand, and **the convention is that the ground truth is produced by a calculator that never imports
this codebase.** A `.hand.txt` derived from the implementation would launder the implementation's
assumptions into the thing meant to check them.

What this tier pins: IBKR commission including the $1 minimum and the 1% cap, percent-of-notional
spread, borrow fees on the short leg, margin interest on `max(gross − NAV, 0)`, dividend flow in
both directions, calendar carry accrual, intrabar stop fills and gap-throughs, split handling, and
one whole five-bar backtest end to end — `test_the_golden_master.py`, which reconciles to a final
NAV of 100,149.6537022380 from a 100,000 start.

**What it guarantees:** that on the scenarios worked out by hand, the engine computes to the cent
what a person computed independently. That is a strong guarantee about *arithmetic* and a narrow
one about *coverage*: 15 scenarios, chosen.

**Recently strengthened, and the gap is worth knowing about.** Until 2026-09-16 the golden master
asserted only the *sum* of commission and spread, and asserted borrow, margin interest and the
dividend **nowhere** — 678.82 of the 817.35 this scenario pays in frictions was unchecked. It now
carries a closed-book recomputation of all 19 fields on all 5 bars, and an AST gate forbids that
calculator from importing the package. The engine still publishes no per-brick cost attribution,
so borrow and margin interest remain inseparable from outside it; that residual gap is drawn
rather than hidden in [`docs/figures/`](figures/README.md).

### `tests/property/` — 67 tests across 8 files. *The invariants hold on paths nobody chose.*

Hypothesis generates the inputs. The tier exists for failures with a *shape* you cannot enumerate,
and look-ahead is the archetype: perturbing bars after the decision bar must change nothing
before it, and no finite set of examples covers the shapes that would trigger it.

`test_macd_invariants.py` states the distinction better than a summary can — a unit test checking
an anchoring property at three hand-picked indices "is the right shape for a **gate** and the
wrong shape for a **guarantee**. This file quantifies over the paths and the index."

**What it guarantees:** that across randomised price paths and weight schedules, the named
invariants did not break in the examples drawn *on this run*.

**Read that sentence carefully.** `derandomize=True` fixes hypothesis's seed but **not the values
it draws** — since 6.156.6 the constant pool is harvested from `sys.modules` at test time, so a
full-suite run and a single-file run draw differently from the same seed
([D537](decisions/D537-derandomize-does-not-mean-deterministic.md)). A property failure that does
not reproduce when you run its file alone is **not** thereby a flake.

### `tests/integration/` — 152 tests. *The whole path composes, and one thing is checked against an engine we did not write.*

Whole studies run end to end: the pairs walk-forward, the breakout studies, the capacity and gross
sweeps, the cost sweep, the risk monitor's drift behaviour.

Two carry more weight than the rest:

- **`test_dataview_lookahead_guard.py`** — the structural look-ahead guard. This is the one that
  matters most, because look-ahead is the defect that makes everything else meaningless.
- **`test_cross_engine.py`** — the only **X** test: an identical strategy on identical data through
  `vectorbt`, an engine written by someone else, reconciled at `TOLERANCE = 1e-6` (D47). Measured:
  2,515 bars, **1,370 fills on each side and the same bars**, final value $159,233.023491 both
  ways, maximum divergence 1.30e-12 relative.

  **Its scope is narrow and the figure says so on its face:** one instrument, long-flat,
  proportional fees only. Carry, dividends, splits and margin are ours alone and are anchored by
  the golden masters instead. The README's "penny-exact against an independently written engine"
  is true *of that scope*.

### `tests/unit/` — 1,750 tests. *Each part does its own job.*

The bulk, and the least interesting per test: one behaviour, chosen inputs. This is also where
most of the **structural guard** assertions are proved to fire — `src/` carries **272 `raise`
statements**, spread across 45 of its 85 tracked `.py` files, and a guard nobody has proved will
raise is a guard nobody has checked.

**The counting rule, because a reviewer who checks will otherwise get a different number.** That
figure counts `raise <Exception>` forms only — AST `Raise` nodes with a non-`None` `exc`. A plain
AST walk over the same 85 files finds **two more**: bare `raise` inside an `except`, which re-raise
what they caught. Those are flow control rather than guards, and there is no message for a test to
assert. Both readings are correct arithmetic; only one of them is the thing this paragraph is
about, and `tests/unit/test_quoted_counts_are_current.py` pins the reading as well as the number.

---

## Guards are not tests, and the distinction is the point

The strongest claims here are not made by tests at all. They are made by the code refusing to
proceed. [`ARCHITECTURE.md` §5](ARCHITECTURE.md) grades them honestly into three kinds —
**impossible** (the object was never given the data), **asserted** (raises at a boundary), and
**merely recorded** (the name overpromises) — and it is worth reading before you trust any of
them, because the third category exists.

`DataView` is the important one: a strategy is handed a window that *cannot* contain future bars,
so look-ahead is not prevented by a test but by the absence of the data. The test proves the
absence is real.

## Six gates that are not the test suite

CI runs four jobs and eight commands ([`tests.yml`](../.github/workflows/tests.yml), counting the
`run:` steps and not `uv sync`). **Two** of the eight are `pytest` — `tests/golden` in the `golden`
job and the whole suite in the `suite` job. The other six check committed state, and each has its
own row below rather than sharing one, so that the rows and the commands can be counted against
each other:

| gate | what it establishes |
|---|---|
| `ruff check src tests` | errors, not style (E4/E7/E9/F) |
| `mypy` | types over the library; tests are out of scope by config |
| `check_doc_links.py` | every relative path in every tracked document resolves **in the git index** — 1,031 documents, 0 unresolved |
| `build_readme_counts.py --check` | the README's inventory matches the repository |
| `figures/build_all.py --check` | all twelve SVGs regenerate byte-identically from their artifacts |
| `build_data_manifest.py --verify` | no bulk panel has changed under a published result |

Plus four completeness guards inside the suite, each written after the failure it now prevents:
every decision number appears in its index; every results document is linked from its index; every
*cited* decision number has a record; every figure is registered, indexed and described.

---

## What this suite does not guarantee

The section that matters most.

**It does not guarantee any strategy makes money.** It guarantees the numbers are computed
correctly. Most of the research output is negative, and that is the evidence the instrument works.

**It does not guarantee the cost models are right, only that they are applied right.** The golden
masters pin the arithmetic of a commission schedule; whether that schedule is what you would pay
is a modelling question the suite cannot reach. Corwin-Schultz reads 17–55 bp/side where the quote
is 1–2.

**It does not cover the research code.** `src/backtest_framework/` is 46 modules and is what the
tests pin. `scripts/` is 592 one-shot runners, tested only where a study's headline numbers are
pinned to its artifact.

**On a clone, 53 tests do not run (measured 2026-09-17).** The bulk data panels left the index in
[D536](decisions/D536-manifest-only-storage-for-the-bulk-panels.md); a clone runs **2,017 passed,
53 skipped**.

That figure moved twice in one day and both moves are worth knowing, because they are what a skip
count is *for*. It read 50 while `test_public_cut.py` contained a test that skipped itself in a
clean tree — a test that could not fail, so it was rewritten into one that can, and the count fell
to 49. Then a clone run found **seven failures**, four of them because `--build` cannot author a
commit in a repository with no `user.name` (it is set per-repository here, and `git clone` does not
copy local config). Those four are now honest skips rather than reds, and the count rose to 53.
**A skip count that rises because failures became skips is the suite getting more truthful, not
less.** The split is deliberately not gated: it is a function of what a checkout happens to
carry rather than of the commit, so it stays a dated measurement.

**Every skip that wants a file names it — 49 of the 53 — and
[`data/data_manifest.json`](../data/data_manifest.json) carries the sha256 and git blob id of each.
The other four want a git identity rather than a file** and say so
([D540](decisions/D540-local-config-a-clone-never-receives.md)).

That sentence used to read "each skip names the file it wanted", and **sixteen did**. The other 33
said `fixture not built`, or named a rebuild script instead of the file, or — in four cases — said
nothing at all, while `tests/conftest.py` named that same fixture correctly elsewhere in the same
run. The received explanation was that those 33 wanted data that would have to be re-fetched from a
paid vendor; measured, every one of them is in the manifest with a checksum and a blob, so all 33
were recoverable and simply declined to say so. Six call sites produced all 33 and now route through
`requires_panel`. **A skip is not a pass** — if the count climbs, something stopped being tested.

**It has never run on a machine that is not this one.** Four CI jobs are wired to run on every
push and the repository has no remote, so the workflow has never executed. What *has* been done,
twice, is cloning the repository into an empty directory and running everything there — which
found three tests that passed here and failed on every clone, and five links that resolved only on
the author's disk.

**And it did not catch everything.** Seven real defects were found by a guard, an assertion or an
implausible number — never by inspection — and each one is a test that did not exist at the time:

| | |
|---|---|
| **D181** | the ensemble weighted itself with whole-sample volatility. The structural guard makes this impossible for a *strategy* and does nothing for analytics built on strategy output — a boundary nobody had written down |
| **D187** | crypto volume is quoted in dollars and the impact model read it as coins: understated 148× on BTC and overstated 40× on a sub-cent coin, in the same run |
| **D184** | a benchmark returned +102,682,123% from one bar |
| **D186** | volumes reached the policy screen and never reached the run |
| **D176** | a dead diagnostic had its direction reversed — it would have reported profitable moves as losses |
| **D177** | a cumulative rate that fell as its window grew; the arithmetic could not be true, which is the only reason it was visible |
| **D169** | a headline claim was a measurement artifact — stop exits inferred from price rather than recorded |

A later catch is worth its own line, and it is the largest: **D279's lag audit re-derives the held
set from `score[:, t-1]` in a second implementation that never calls the selection function, and
found that ~93% of that study's apparent edge was the bug.** Six cells moved; the eight the ranking
never selected are bit-identical between the two runs, which is what makes it a finding rather
than a coincidence. It is drawn in
[`docs/figures/lookahead-before-after.svg`](figures/lookahead-before-after.svg).

---

## Running it

```bash
uv sync
uv run pytest -q tests/golden     # 101 ledger-anchored tests, no market data
uv run pytest -q                  # everything
uv run pytest -q -rs              # everything, with every skip named
```

The golden tier runs on a bare clone in under a second: it uses synthetic bars, which is the point
of it.
