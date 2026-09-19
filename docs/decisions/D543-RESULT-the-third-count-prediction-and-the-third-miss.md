# D543 RESULT — the gate closes, six files were not three, and the third count prediction missed for the second time in the same way

*2026-09-18. Spec committed in `487c12b` BEFORE any config changed (R8). Nothing admitted to
either book. No holdout read: this record touches tooling and declarations, not a strategy.*

**`scripts/` is under the lint gate, the encoding divergence is pinned and ratcheted, and six
tracked files stopped being described as something they are not. Two of five predictions were
wrong, and one of them was wrong for the reason the pre-registration explicitly claimed to have
fixed.**

---

## The predictions, scored

| # | Prediction | Outcome |
|---|---|---|
| **P1** | 4 at the new rule set, **0** after the three sites are resolved | **HOLDS** |
| **P2** | No committed artifact changes; no runner is re-run | **HOLDS** |
| **P3** | `PYTHONUTF8=1` changes nothing, after the edits too | **HOLDS** |
| **P4** | The ratchet's count is within ±10% of the review's 312 | **UNRESOLVABLE AS WRITTEN** |
| **P5** | `+1 test_files`, `+1 scripts`, `raise` +1 or +2 | **FALSIFIED on two of three** |

### P1 and P2 — the gate, and nothing moved

`ruff check src tests scripts` reported **4** before and **0** after. The rule set fires:
a probe carrying an undefined name and a duplicated dict key produced exactly those two
diagnostics and **exit code 1**, while an unused import and an unused local in the same probe
were correctly ignored — so the select is the one intended and not an accident that passes
everything.

Three files changed in `scripts/`, and no artifact was regenerated:

| site | what changed |
|---|---|
| `d361_export_trades.py:372` | `_b=bars` binds the dict at definition instead of closing over a name `del`eted 12 lines later. Same object, same result; a call added below the `del` now works rather than raising. |
| `run_etf_intraday_gate.py:361` | `min(raw.items(), key=lambda kv: (len(kv[1]), kv[0]))[0]` — closes over nothing. The diagnostic was a false positive; the fix is that the line no longer needs a reader to prove it. |
| `d399_draw_construction.py:478` | the duplicate `"h": H` removed. `H = DELTA`, already emitted as `"delta"`, so **nothing was lost and `data/d399_chart_data.json` was already correct**. `H` is still used by branch B at `:522`/`:524`. |

### P3 — the variable that changes nothing, which is why it is worth setting

With `PYTHONUTF8=1`: full suite identical, and `build_readme_counts --check`,
`figures/build_all --check`, `run_golden_master_ledger --check` and `check_doc_links` all
current. Measured before proposing it and again after the edits. **313 runners take their text
encoding from the platform** — UTF-8 on the Linux runner, cp1252 on the machine this is written
on — and the divergence is now declared at workflow level rather than inherited.

### P4 — unresolvable, because the review's number counted a third thing

P4 asked whether the ratchet's count lands within ±10% of "312 runners". It cannot be scored,
and the reason is the finding: **there are three different numbers here and the review reported
one of them without saying which.**

| definition | count |
|---|---|
| files with ≥1 no-`encoding=` text-IO call | 399 |
| files that **never** pass `encoding=` anywhere | 313 |
| call sites, excluding `csv.*` | **1,126** |

The review's 312 is almost certainly the middle row, off by one. The ratchet holds the **call
sites**, because that is the number a single correct fix moves by one; a file count only falls
when the last site in a file is fixed, which makes it a lagging and discouraging indicator.

Two counting corrections are baked into the scan and tested rather than commented:

- **`csv.reader`/`writer`/`DictReader`/`DictWriter` are not counted.** They take a file object,
  not a path, and have no `encoding` parameter. Counting them double-counts the `open()` above
  them and puts the ceiling out of reach of any amount of correct work.
- **`gzip.open`'s default is `"rb"`, where builtin `open`'s is `"r"`.** An unannotated
  `gzip.open(p)` has no encoding to declare. Getting that backwards inflated the count before it
  was caught; as it happens **no runner relies on the default**, so the number is 1,126 either
  way and the guard is there for correctness rather than for its effect.

### P5 — falsified, and for the reason the pre-registration said it had fixed

Predicted `+1 test_files`, `+1 scripts`, `raise` `+1 or +2`. Measured against `487c12b`:

| | predicted | actual |
|---|---|---|
| `test_files` | +1 | **+1** |
| `scripts` | +1 | **+0** |
| non-bare `raise` in `src/` | +1 or +2 | **+0** |

The guard was built as a **test**, not a script, so it added nothing to the runner count; and it
lives in `tests/`, which the `raise` counter — scoped to `src/` — does not read at all.

**This is D542's P6 exactly.** That prediction also missed by naming a guard in a tree the gate
does not count, and this record's pre-registration says, in writing, *"D542's P6 predicted +1 and
got +4 while naming a guard in a tree the gate does not count; this prediction names the tree."*
It then named the wrong tree, in the same sentence that claimed to have learned the lesson.

Three count predictions in this programme: B26 (272 → 284, predicted 278), D542's P6 (+4,
predicted +1), and this one (+0 on two components). **Writing down the rule is not the same as
applying it, and the failure mode is not arithmetic — it is deciding the shape of the fix after
the prediction is written.** The usable version is narrower: *do not predict a count until the
artifact that moves it exists.*

---

## What was found that no prediction covered

### There are six non-UTF-8 tracked files, not three, and one is not what its name says

Verified independently of the census that reported it — 3,042 tracked files decoded, six fail:

| file | bytes | encoding | read by |
|---|---:|---|---|
| `data/D3_french_variable_definitions.html` | 14,236 | cp1252 (`0x92 0x93 0x94`, smart quotes) | nothing |
| `data/d279_run.log` | 3,698 | cp1252 (`0x97`, em dash) | nothing |
| `data/d279_run_corrected.log` | 3,624 | cp1252 | D279, in prose |
| `data/d285_run.log` | 9,881 | cp1252 | nothing |
| `data/ftmo_challenge_terms_2026-08-04.txt` | 73,685 | cp1252/latin-1, **indeterminate** | **D386 + 3 documents** |
| `data/k4_sec_34-81446_2017_ex_date_transition.html` | 133,882 | **not an encoding problem — it is a PDF** (`%PDF-1.5`) | nothing |

`.gitattributes` opened with `* text=auto eol=lf` and named none of them. **`text=auto` is
content detection, not a declaration**, and git's heuristic is "does it contain NUL" — so the
first five were classified text and line-ending-normalised by a tool that cannot read their
bytes. The sixth escaped only because a PDF contains 386 NULs.

All six are now declared `binary`. **The cost is stated rather than glossed:** git will no
longer diff them, so a future change to one becomes invisible in review. For frozen evidence
nobody parses, that is the right trade; it is written into `.gitattributes` beside the rule so
the next reader does not have to rediscover it.

**Two things deliberately not done.** The `ftmo_challenge_terms` file is lossy `pdftotext`
output that has already dropped the Czech diacritics it could not carry (`Purkyňova` →
`Purkyova`, `Nové Město` → `Nové Msto`), and it is cited by D386 — **re-encoding evidence is not
something a tooling lane gets to do**, and its remaining bytes should not go through a second
lossy step. And the PDF-named-`.html` file is left named as it is: renaming a committed artifact
is the principal's call.

### Ruff's encoding rule sees about a ninth of the surface

Beyond being preview-only, `PLW1514` reports **121 sites across 100 files** with `--preview`
against the **1,126** counted here, because it recognises `read_text`/`write_text` only on a
syntactically visible `Path(...)` receiver and does not cover `pandas.read_csv`/`to_csv` or
`gzip.open` at all. So even paying the preview-instability price would have bought 11% of the
gap. That is the second, independent reason the rule lives in the repository.

### The reason the encoding gap has never bitten is structural, and is now asserted

Of 1,180 no-`encoding=` call sites, **zero touch a non-ASCII byte**, and not by luck: 716 of
them read or write `json.dumps` output, and `json.dumps` escapes non-ASCII unless
`ensure_ascii=False`. **No tracked `.json` file contains a non-ASCII byte** — 0 of 14,482.

That argument holds only while nobody passes `ensure_ascii=False`, so the suite now asserts its
absence rather than relying on it being remembered. If that assertion ever fires, the 313 files
become a live divergence rather than a latent one, and the ratchet's ceiling stops being a
formality.

---

## What this record does not settle

Whether any of the 163 `F841` findings is a genuine dropped computation — two were sampled and
both were vestigial, and **two of 163 is not a survey**.

Whether `VERIFICATION.md` and `CONTRIBUTING.md` should be gated against the workflow all three
describe. Both were edited here to match `ruff check src tests scripts`, and **only the workflow
is executable**; the other two are prose that nothing checks. Same for VERIFICATION's *"four jobs
and eight commands"* and *"Six gates that are not the test suite"* — the lint step was extended
rather than duplicated precisely so those counts stayed true, which is a workaround for an
ungated self-count, not a fix. That is A24's class and belongs to Lane 8.

---

## ADDENDUM 2026-09-19 — the 1,126 in this record is a measurement of one worktree

**Every figure above stands as what was measured; the number was measured wrongly and this says
so rather than editing it.**

`1,126` was counted by a scan that listed the index and then filtered to files present on disk.
The principal had two script deletions in flight, unstaged, each carrying exactly one undeclared
call site. **The index holds 1,128.** The author's machine could not see them and neither could
this record.

It was found by the first ever CI run, against a clone, and it is written up in
[D550](D550-what-CI-found-in-its-first-run.md). The gate now reads the index directly, so the
count is the same on any machine at a given commit. No call site was added and no runner was
edited.
