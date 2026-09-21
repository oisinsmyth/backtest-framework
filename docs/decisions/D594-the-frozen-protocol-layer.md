# D594 — The frozen-protocol layer: a model's parameters, code and dates get the same structural guard the DATA already has, and the library picks no seal date

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The six User-Doc-Deposit pre-registrations of 2026-09-21 name a frozen protocol
they have no implementation for: `SETTLEMENT_FLOW_LEDGER_PREREG.md` §13A.4, §13A.7(2),
§13A.8 control 1 and unit tests 34, 60, 64, 65; `OPENING_AGENT_STATE_PREREG.md` §12A control 1
and unit tests 18, 20; `INDEX_REWEIGHT_FLOW_PREREG.md` §11 (`FROZEN_2027.json`). Extends
[D85](D85-walk-forward-guarded-fitting.md) (the look-ahead guard by construction),
[D551](D551-a-snapshot-id-that-depended-on-the-os.md) and
[D550](D550-what-CI-found-in-its-first-run.md) (an identity computed from bytes is a fact about
the writer's newline handling), [D78](D78-property-test-conventions.md) as amended by
[D537](D537-derandomize-does-not-mean-deterministic.md), and R8/R16 in [`../RULES.md`](../RULES.md).
Sibling of [D588](D588-power-analysis-module.md), built the same day for the same
deposit.

## Decision

`src/backtest_framework/validation/frozen.py` — new module, 1 file, no dependency beyond
stdlib + numpy + `registry.trial_registry.canonical_json`. `scripts/freeze.py` is its command
line. Nothing else in the repository is touched: no runner, no `ragged_panel.py`, no README, no
`VERIFICATION.md`, no `CHANGELOG.md`, no `data-available.md`, no `docs/decisions/README.md`.

**1. What it is for.** D85 gives the framework a look-ahead guarantee *by construction*: a
fitter receives training data as `Mapping[str, DataView]` built from the training slice, so the
test window is physically absent from anything it can reach. That guards the **data**. It cannot
guard the three things a researcher carries in their head between one run and the next — the
**parameters** (refitted, nudged, "obviously better" after a look), the **code** (one edited line
in the estimator the result was declared on) and the **dates** (an evaluation window quietly
extended until it pays). This module is the complementary protocol layer for those three, and it
is a *layer*, not a replacement: D85's guarantee is stronger where it applies, because a
construction cannot be forgotten and a protocol can.

**2. The API.**

| | |
|---|---|
| `sha256_bytes(b)` | sha256 of exactly these bytes |
| `sha256_file(path, *, text_normalise=True, chunk_size=CHUNK)` | LF-pinned for text, raw for binary, 1 MiB chunks |
| `normalise_newlines(b)` | CRLF and lone CR to LF |
| `freeze(path, *, name, params, code_paths, fixture_paths=(), evaluation_days=None, spec_commit=None, instruction=None, live_git=False) -> FrozenRecord` | writes `FROZEN_<name>.json`; refuses to overwrite |
| `load_frozen(path) -> FrozenRecord` | re-derives both digests; a hand-edited frozen file raises here |
| `assert_frozen(path, *, params, code_paths, fixture_paths=()) -> None` | names the FIRST drifted item with expected vs found |
| `assert_evaluation_length(path, evaluation_days) -> None` | the length cannot change once evaluation started |
| `SealedWindow(start, end)` · `.contains(day)` · `.as_list()` | explicit ISO dates, **no defaults**, `start <= end` |
| `filter_before(frame, col, reserved_from)` | layer 1 of the reserved guard, at the loader |
| `assert_none_at_or_after(frame, col, reserved_from)` | layer 2, after loading; raises `ReservedSliceError` |
| `window_record(frame, col, reserved_from) -> dict` | layer 3, the artefact's `"windows"` block |
| `open_once(log_path, *, window, model, instruction, frozen_path, params=None, code_paths=(), fixture_paths=()) -> OpenRecord` | one look only, logged as JSON lines |
| `refuse_without_word(word, what, log=print) -> int` | 2 and the D574 message, or 0 |

Errors: `FrozenError` (base) and `FrozenExistsError`, `FrozenDriftError`, `AlreadyOpenedError`,
`VaultGuardError`, `ReservedSliceError`. `ReservedSliceError` also subclasses `AssertionError`,
deliberately, because the seven runners that carry this guard today write
`raise AssertionError(...)` and `expect_raise` (`scripts/stage0_d581_gamma_close.py:39`) catches
`AssertionError` — a runner can adopt the named class without its own self-test quietly ceasing
to catch the raise.

**3. THE MODULE CHOOSES NO SEAL DATE, AND THE OMISSION IS THE DECISION.** The deposit documents
seal 2025-03-01 → 2026-09-18. This repository's futures holdout is 2024-01-01 onward
(`RESERVED_FROM`, defined once at `run_d555:43` and imported by seven runners). Those are two
different windows over two different programmes, and reconciling them is **the principal's open
decision**. So `SealedWindow` takes both dates explicitly and has no defaults, `filter_before`
and its siblings take `reserved_from` as an argument, `scripts/freeze.py` has no default window,
and every test in this record's suite uses a synthetic 2001–2002 span. Importing this module can
never silently change which slice a runner reads.

**4. The identity is content, not machine.** `FrozenRecord.content_sha256` is `canonical_json` of
exactly what was frozen — schema, name, params, each file's **basename** and digest,
`evaluation_days`, `spec` and `instruction` — hashed as UTF-8. It excludes `frozen_utc` (or the
record would have no stable identity at all), the derived `params_sha256` and `content_sha256`
themselves, `git_head` (live and machine-dependent), and each file's **path**. Files are sorted
by basename, so the caller's argument order does not enter the digest, and two files sharing a
basename raise rather than being silently resolved.

**5. The newline rule, stated once:** *code is text and is LF-pinned before hashing; a fixture is
hashed as the bytes on disk; every file this module writes is opened with `newline="\n"` and
`encoding="utf-8"`, never `Path.write_text`.* The golden ledger is the arithmetic: the three
bytes `62 0D 0A` hash to `0263…` as text and `679e…` as binary, and `text_normalise=False` is
asserted bit-identical to a re-implementation of `run_d555:79`'s chunked loop, so every
`fixture_sha256` already published still reproduces.

**6. Provenance stays a committed constant.** `spec_commit` is a `SPEC`-style string the caller
passes (`run_d555:37`, `run_d574:45`). `live_git=True` exists, runs `git rev-parse HEAD`, is off
by default and is never required — exactly one runner in the repository does it live
(`run_d357_holdout_read.py:876`).

**7. Gates.** `tests/golden/test_frozen_ledger.py` + `.hand.txt` (9 tests), `tests/unit/test_frozen.py`
(48), `tests/property/test_frozen_property.py` (9), and `scripts/freeze.py --selftest` (9 proved
raises, on synthetic files in a temp directory). Property settings are
`settings(derandomize=True, max_examples=40, deadline=None)` per D78/D537.

## Rationale

**A digest belongs in the golden tier for the same reason a fill price does.** D551 is the
evidence: `save_events_json` used `Path.write_text`, so one fixture froze to snapshot id
`51756f0d` on Windows and `1bb6fe9c` on Linux, and a snapshot id is the provenance identifier
logged with every trial and printed in results documents. A protocol whose whole value is that
two machines agree on one hexadecimal string has money's failure mode, so it gets money's tier:
ground truth from two calculators that never import this codebase (GNU `sha256sum` fed by
`printf`, and .NET `SHA256` over a literal `[byte[]]`), anchored on the published SHA-256 of the
empty string so a swapped hash function fails on the first assertion.

**The identity had to be keyed on basenames, and that is a cost paid deliberately.** Keying on
paths would have made the digest a fact about one machine's directory layout — D551's defect
arriving from a second direction. Keying on basenames means a collision is possible, so a
collision raises. The property test quantifies the payoff: the same content, kept at two
different depths and listed in two different orders, freezes to the same `content_sha256`.

**The FIRST drifted item is named, in a fixed order — params, then code, then fixtures.** A
message that says "something changed" sends a reader to diff three things. A message that names
`alpha.py` with both digests sends them to one. The order is not arbitrary either: when a
parameter and a file have both moved, the parameter is reported, because the parameter is the
thing a human tuned and the file may have moved for an innocent reason. Ledger unit test 34 asks
only that the code "refuses to run"; the refusal that also says *which* is the deliverable.

**Refusal is a return code from the real entry point.** `run_d574:99` and
`d503_forward_book.do_run` both return 2 rather than calling `sys.exit` inside `__main__`,
precisely so a self-test can call the real function — `run(False, log=lambda *a: None)` — and
assert the 2. A refusal demonstrated by reading the source is not demonstrated. `refuse_without_word`
raises on a non-`bool`, because `refuse_without_word("no", ...)` must not read as the principal's
word.

**Every guard is proved to fire on a break that hits the scalar it compares, and to be silent
otherwise.** A self-test that cannot fail is worse than none; so is one that always fires.
`--selftest` therefore asserts the silent case first, then breaks each guard in turn — one byte
of one code file, one parameter, the evaluation length, a second opening, an absent frozen model,
an unsorted window, a hand-edited frozen file — and checks the message names the right object.
The CRLF-only rewrite is included as a **negative** control: it must NOT be drift, or the pin
would be a nuisance rather than a guard.

**The three-layer reserved guard is consolidated rather than reinvented.** Filter at the loader,
assert after loading, record in the artefact — already the practice in seven runners, now three
named functions whose layer 1 and layer 2 are deliberately not the same code path, since
filtering and checking with one expression proves only that the expression is self-consistent. A
`datetime64` day column is **refused rather than coerced**: `str()` on `datetime64[ns]` yields
`2024-01-01T00:00:00.000000000`, which sorts *after* `"2024-01-01"`, so a silent coercion would
let the first reserved session straight through the guard that exists to stop it. The unit test
demonstrates that inequality rather than asserting the refusal alone.

## Consequences

- A stage can now be frozen and verified from the command line without writing a runner:
  `uv run python scripts/freeze.py --name X --params p.json --code … --fixtures … --out DIR`,
  and `--verify FROZEN_X.json …` returns 1 with the named drift.
- **No runner has been changed to use it.** Adoption is per-runner and is a separate decision
  each time; this record adds a socket, not a migration. The seven runners carrying
  `RESERVED_FROM` continue to work exactly as they did.
- **The seal-date reconciliation is still open.** The deposit's 2025-03-01 → 2026-09-18 vault and
  this repository's 2024-01-01 reserve are not the same object and this module does not pretend
  they are. Whoever reconciles them writes it down; nothing here will have pre-empted it.
- `open_once` is not concurrency-safe against two processes opening the same log in the same
  instant: it reads, then appends. One machine, one researcher, one look — and a damaged log is
  a refusal (`VaultGuardError`), never a fresh start.
- The frozen file is **append-nothing**: `freeze` refuses to overwrite, so a parameter, rule or
  code change restarts the evaluation count under a *new* frozen file, which is ledger §13A.4's
  sentence made mechanical rather than remembered.
- `ReservedSliceError` subclassing `AssertionError` is a compatibility affordance with a shelf
  life: if the repository ever stops catching `AssertionError` in `expect_raise`, the second base
  class should go, and this paragraph is the note that says why it was there.
- No strategy return was computed and no fixture was read for a return. The only fixture bytes
  touched were `data/futures_contract_specs.json`, hashed in a throwaway command-line smoke test
  under `temp/` and deleted.
