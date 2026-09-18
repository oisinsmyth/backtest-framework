# D546 RESULT — both gates are in and prove they fire, and the config fix does not cover the invocation that found the problem

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

*2026-09-18. Spec committed in `8c2b0a5` BEFORE either gate existed (R8). Nothing admitted to
either book. No holdout read. No runner touched and no artifact regenerated.*

**Two gates, both proved live. Two of five predictions falsified — and the one that matters says
the one-line fix does not close the case that produced the bug report.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | No published number moves | **HOLDS** |
| **P2** | Deleting `python_files` reddens the gate by the missing-key assertion, **not** by the floor and **not** by the offender list | **FALSIFIED** — it reddens the missing-key assertion *and* the offender list |
| **P3** | Emptying the pattern list reddens the **floor**, not the offender assertion | **HOLDS** |
| **P4** | Restoring a `D3_wb` file to valid JSON reddens the **allow-list re-derivation** | **HOLDS** |
| **P5** | `pytest data/A4-filing-text/A4_header_test.py` collects 0 items, **writes no file**, makes no network request | **FALSIFIED** — 0 items, and it writes the file anyway |

### P2 — wrong, and wrong in the gate's favour

Deleting the line and running the gate: **2 failed, 4 passed**.

```
FAILED test_python_files_is_configured
FAILED test_nothing_outside_tests_matches_the_collection_patterns
```

The second message names all seven files. I predicted the offender list would stay quiet because
I was thinking of it as a gate on the *tree*, and it is a gate on the *tree under the configured
patterns* — remove the configuration and the patterns revert, so the offenders reappear by
construction. The floor held, as predicted.

The result is better than the prediction: one failure names the cause, the other names the
consequence. But it was not predicted, and a prediction that is wrong in a pleasant direction is
still wrong.

### P3 — holds, and the two failure modes are distinguishable

Setting `python_files = []`: **2 failed, 4 passed**, and the second failure is the **floor**
(`only 0 tracked test file(s) under tests/ match []`), while
`test_nothing_outside_tests_matches_the_collection_patterns` **passes** — an empty pattern list
matches no offenders, which is exactly the shape of the empty-scan defect this programme closed
six times.

So the two ways to break the setting redden two different second assertions: **widened → the
offender list; emptied → the floor.** That was the point of P2 and P3 being separate predictions,
and it survived P2 being wrong.

It only works because `_effective_patterns()` tests `is None` rather than using `or`. The first
draft used `or`, which folds an empty list into a missing one — the floor would then have scanned
with pytest's defaults, found 158 tests, and passed while reporting on a configuration the
repository did not have.

### P4 — holds, exactly

`data/D3_wb_2018.json` replaced with `{"note": "refetched"}`: **1 failed, 3 passed**, and the
failure is `test_the_allow_list_is_still_earned`, naming the file and saying *"parses now, so
remove it from ALLOWED; the exemption is spent"*. Restored byte-exact, verified by SHA-256 rather
than by assumption.

---

## P5 — the finding: pytest imports any file you hand it, whatever the configuration says

**The claim under test was the whole point of the change.** It is false.

Measured on a harmless stand-in — a module that writes a marker file at import through a relative
path, exactly as `A4_header_test.py:97` does — with no network involved:

| invocation | pytest defaults | `python_files = ["test_*.py"]` |
|---|---|---|
| `pytest` (via `testpaths`) | clean | clean |
| `pytest .` (repo-wide) | **imported it** | **clean** |
| `pytest data/A4-filing-text/A4_header_test.py` | **imported it** | **imported it** |

An explicitly-named path is an **initial path**, and pytest skips the `python_files` check for
initial paths — it collects 0 tests from the module and has already imported it to find that out.
Exit code 5, "no tests collected", stray file on disk.

**And no configuration closes it.** Three instruments measured, same stand-in:

| instrument | `pytest .` | `pytest <the file>` |
|---|---|---|
| `python_files = ["test_*.py"]` | clean | **imported** |
| root `conftest.py` with `collect_ignore_glob` | clean | **imported** |
| `addopts = "--ignore-glob=*_test.py"` | clean | **imported** |

**So the residual hazard is a property of the module, not of the configuration**, and the six
other files are immune for a reason that has nothing to do with their names: they are
`__main__`-guarded. `A4_header_test.py` is not.

**This inverts the task chip.** Its implied fix was a rename, and a rename would have closed
neither case: not the six others, and not the explicit-path invocation — which is the one that
actually bit, because passing the file directly to pytest is exactly what I did during Lane 8's
census. The honest fix for the seventh file is the guard the other six already have, and that is
an edit to a file in `data/`, so it is recorded here and not made.

---

## What landed

**`pyproject.toml` — `python_files = ["test_*.py"]`.** Seven tracked `.py` outside `tests/`
matched pytest's defaults, all on the `*_test.py` suffix; all 158 tracked tests use `test_*.py`
and none uses `*_test.py`, so nothing is given up. This closes repo-wide collection, which is
real: `pytest .` no longer imports any of the seven.

**`tests/unit/test_nothing_outside_tests_is_collectable.py`** — six tests. Reads `python_files`
back out of `pyproject.toml` with `tomllib` rather than restating it; asserts the key's presence
separately from its content; floors the scan at 150; and re-derives the reason for the setting, so
that if every offender is one day retired the gate says *"delete the setting and this file"*
instead of standing guard over nothing.

**`tests/unit/test_tracked_json_parses.py`** — four tests, the gate
`D542-RESULT…:201` said should exist and nobody wrote. 813 tracked JSON files, 119 MB, about one
second; `json.loads` on **bytes** so an encoding failure counts as a parse failure through the same
call. The two 429 pages are allow-listed with their reason, and the allow-list is **re-derived**:
each entry must still exist and still fail to parse, so the exemption cannot outlive its subject.

---

## What this record does not settle

**The explicit-path hazard, which is now measured rather than assumed.** Closing it means giving
`data/A4-filing-text/A4_header_test.py` a `__main__` guard or moving it. Both are edits to
evidence, and this repository's rule is that a file a record quotes belongs to the principal —
this one is cited at `docs/research/Scan-100926/R1-04-filing-text-at-scale.md:645`. It stays open,
with a better description than the chip had.

**Whether a gate should assert that tracked scripts are import-safe.** It is the real invariant
underneath both halves of this record — the six safe files are safe because nothing runs at import.
A gate for it would fail today on the seventh file and could not be made green without touching
evidence, so it would have to ship red or ship with the offender exempted, and an exemption for the
only instance is not a gate. It waits on the disposition.

**Whether the JSON gate should extend to `.csv.gz`, `.parquet` and `.jsonl`.** JSON is where the
known failure is and where parsing is free. A parquet census needs the reader and the memory, and
a gate slow enough to be skipped is worse than one that is narrow.

**Five rounds of behaviour predictions, two missed here.** Both misses were about the *tool's*
semantics rather than this repository's: P2 mis-read what the gate's own assertions depend on, and
P5 mis-read pytest's initial-path rule. The count-prediction lesson from D543 was *do not predict
a count until the artifact that moves it exists*. The sibling, earned here: **do not predict what a
tool does under a setting you have not run it under.** P5 was checkable in ninety seconds with a
temporary directory and no network, and it was wrong.
