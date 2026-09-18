# D543 — The lint gate stops at the library door, and two of the review's prescriptions do not work

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Research infrastructure
**Source:** Lane 7 of the two-reviewer audit (`working/REVIEW_REMEDIATION_PLAN.md` §8, items
B11/A27, B12, B18). Predictions below are committed before any code or config changes (R8).

## The problem

`scripts/` is **603 tracked runners — the bulk of the Python in this repository and the source
of every published number — and nothing checks it.** CI runs `ruff check src tests` and `mypy`
over `src` alone. `docs/VERIFICATION.md` tells a reviewer honestly that `tests/` is out of
mypy's scope; it does not mention that lint stops at the library door.

Measured here rather than quoted:

| | |
|---|---|
| `ruff check scripts` | **7,423** |
| of which `E702` (semicolons) | **5,763 — 78%** |
| `mypy scripts --ignore-missing-imports` | **1,048 errors in 262 of 601 files** |
| after ignoring `E4, E7, F401, F541, F841` for `scripts/**` | **exactly 4** |

Full breakdown of the 7,423: `E702` 5763, `F541` 773, `E741` 276, `E731` 220, `F841` 163,
`E401` 84, `F401` 80, `E701` 47, `E402` 10, `F821` 3, `E712` 3, `F601` 1.

## Decision

1. **`scripts/` joins the lint gate at a correctness-only rule set**, via
   `[tool.ruff.lint.per-file-ignores]` for `scripts/**`, and CI's existing step becomes
   `ruff check src tests scripts` rather than gaining a new step — VERIFICATION's "four jobs and
   eight commands" and "Six gates that are not the test suite" are **self-counts that nothing
   gates**, and extending the step keeps both true.
2. **`mypy` does not follow.** 1,048 errors in 262 files, in runners written to be read once and
   frozen. Stated in `VERIFICATION.md` rather than left to be inferred from a passing run.
3. **The encoding gap closes with `PYTHONUTF8=1` in CI plus a repository-owned ratchet**, not
   with a lint rule — see below for why the review's rule does not exist in a usable form.
4. **Nothing in a frozen research runner is edited for style.** The three correctness sites are
   fixed; the 243 `F841`/`F401` findings across 180 of 603 runners are ignored, with the reason
   recorded rather than assumed.

## Two review prescriptions that do not work

**B12's rule cannot fire.** The review said to add ruff's `PLW1514` (unspecified-encoding) to a
scripts select. `PLW1514` is a **preview** rule: selecting it prints
`warning: Selection PLW1514 has no effect because preview is not enabled` and checks nothing.
Enabling preview to reach it would adopt a rule set that changes between ruff versions, which is
exactly the failure `pyproject.toml`'s own comment records for leaving `select` unset —
*"an unpinned-by-omission ruleset is a gate that widens on upgrade without a diff."* So the rule
moves into the repository, where its scope is under this project's control.

**B11's "4 real correctness defects" is 4 diagnostics at 3 sites, and one of them is a false
positive.**

| site | verdict |
|---|---|
| `d361_export_trades.py:372` (2 diagnostics, one lambda) | **Real, latent.** The named lambda `at_bar` closes over `bars`, `del`eted at `:384`. Both calls sit above the `del`, so it cannot misbehave today, and a call added below raises `NameError` loudly rather than reading stale data. Ruff emits two diagnostics for the two `bars` references in one expression. |
| `run_etf_intraday_gate.py:361` | **False positive, and the review named the wrong variable and the wrong mechanism.** The flagged name is `raw`, not `bars`; the lambda is anonymous and consumed synchronously by `min()`; the `del` is 100 lines later at `:461` and `raw` is rebound four times in between. Ruff flags it only because its deferred-scope model resolves lambda free variables against the end-of-scope binding. |
| `d399_draw_construction.py:478/480` | **Real but benign, and the artifact is correct.** A dict literal with `"h"` twice. The discarded value is `H`, and `H = DELTA` — which the same literal already emits as `"delta"`, so nothing is lost. The survivor `a.h` is the right value for the default `branch=E`. `data/d399_chart_data.json` is committed and carries `a.h`; no consumer reads the key. |

The review's stated consequence for the third — "silently discarding `H` from an emitted
diagnostic", with the implication that the artifact is wrong — does not hold.

## Predictions, committed before the config exists

| # | Prediction | Confidence |
|---|---|---|
| **P1** | With `per-file-ignores = ["E4","E7","F401","F541","F841"]` for `scripts/**`, `ruff check src tests scripts` reports **exactly 4**, and **0** after the three sites are resolved. | High |
| **P2** | Resolving the three sites changes **no committed artifact**. `d399`'s emitted `"h"` is already `a.h`, and the other two are a closure binding and a `min()` key. **No runner is re-run under this record.** | High |
| **P3** | `PYTHONUTF8=1` changes **nothing**: full suite identical, and `build_readme_counts --check`, `figures/build_all --check`, `run_golden_master_ledger --check` and `check_doc_links` all report current. Measured before writing this: **already confirmed** — 2,163 passed, 1 skipped, all four gates current. Restated as a prediction because it must hold **after** the edits too, and that has not been measured. | High |
| **P4** | The no-`encoding=` ratchet's count is **within ±10% of the review's 312**. The review counted by one method and the ratchet counts by AST; a large gap means one of the two is counting something else, which is itself the finding. | Medium |
| **P5** | The counts gates move by **+1 `test_files`, +1 `scripts`** and the `raise` count by **+1 or +2** (the ratchet's own guard). D542's P6 predicted +1 and got +4 while naming a guard in a tree the gate does not count; this prediction names the tree. | Medium |

P4 and P5 are the falsifiable ones. P5 in particular is the third attempt in this programme at
predicting a count, after B26 (272 → 284, not 278) and D542's P6 (+4, not +1).

## What this record does not settle

Whether any of the 163 `F841` findings is a genuine dropped computation. Two were sampled —
`d290_summary.py:110`, a comprehension used for its side effects, and
`d285_spread_estimate.py:138`, an abandoned diagnostic — and both are vestigial. **Two of 163 is
not a survey**, and this record claims only that the two looked at were harmless, not that the
other 161 are.

It also does not settle whether `VERIFICATION.md` and `CONTRIBUTING.md` should be gated against
the workflow they both describe. Three documents state one command and **only the workflow is
executable**; that is A24's class and belongs to Lane 8.
