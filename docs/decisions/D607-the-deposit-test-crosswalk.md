# D607 — The crosswalk from the deposit's 146 numbered unit tests to the repository tests that claim them: 28 claimed in three spellings, 118 unclaimed and now a list

**Status:** Committed
**Date:** 2026-09-21
**Category:** Testing
**Source:** The five pre-registrations in `docs/internal/User-Doc-Deposit/` that close with a
numbered **Required unit tests** section — `SETTLEMENT_FLOW_LEDGER_PREREG.md` §12,
`INDEX_REWEIGHT_FLOW_PREREG.md` §13, `OPENING_AGENT_STATE_PREREG.md` §15,
`SHOCK_CLASSIFIER_PREREG.md` §9 and `LETF_CLOSE_FLOW_PREREG.md` §8. **Those five files are
untracked, so this record names them and never links to them**; `scripts/check_doc_links.py`
resolves a relative link against `git ls-files`, and a link to a file no clone receives is a
dead link for every reader but the author. Indexes the claims made by
[D586](D586-FIXTURE-cme-settlement-windows-with-effective-dates.md),
[D587](D587-shared-futures-fill-model.md),
[D588](D588-power-analysis-module.md),
[D592](D592-programme-alpha-registry-trial-counter-and-episode-checks.md),
[D593](D593-look-ahead-defences-and-year-folds.md) and
[D594](D594-the-frozen-protocol-layer.md). Follows D592's JSON-as-truth / page-as-render split
and D588's `validate_*` shape. Governed by [R5](../RULES.md) (this doc suite is the source
of truth) and [R6](../RULES.md) — **a hurdle that names a test is not cleared until that
test is run**, which is the rule this file makes countable.

## Decision

`data/deposit_test_map.json` is the truth: one row per numbered unit test in the five deposit
pre-registrations, **146 rows**, each carrying the item's verbatim text, a ≤ 15-word
paraphrase, a class, a status, and — where one exists — the repository test that claims it as
`file:line` plus a symbol. `docs/results/DEPOSIT_TEST_MAP.md` is rendered from it.

**1. `src/backtest_framework/validation/crosswalk.py`.**

| Object | Signature |
|---|---|
| `Claim` | `Claim(kind, file, line, symbol=None)`; `kind ∈ {function, banner, message, record}`; `.as_page_cell()`, `.to_json()` |
| `CrosswalkRow` | `CrosswalkRow(doc, number, line, text, paraphrase, cls, status, claim=None, covered_via=None, note="")`; `.key`, `.is_claimed`, `.to_json()` |
| `_CROSSWALK_REQUIRED` | the seven fields a row must carry, **cause before symptom** |
| `validate_crosswalk` | `(rows) -> None`; raises `CrosswalkError` naming the FIRST offender |
| `assert_doc_counts` | `(rows, docs_meta) -> None`; every document's rows are exactly `1..count` |
| `load_payload` / `load_map` | `(path=data/deposit_test_map.json)`; validation is not optional on the way in |
| `coverage_by_doc` | `(rows) -> {doc: {count, claimed, covered_via, declined, missing, pct_claimed}}` |
| `coverage_total`, `class_tally`, `claim_kind_tally` | the same six numbers over every document; items per class; claims per spelling |
| `render_md` / `write_md` | `(rows, *, docs_meta) -> str` / writes `DEFAULT_PAGE_PATH`, `newline="\n"` pinned |
| `DEFAULT_MAP_PATH`, `DEFAULT_PAGE_PATH`, `SCHEMA`, `DOC_KEYS`, `CLASSES`, `STATUSES`, `CLAIM_KINDS` | constants |

**2. `scripts/deposit_test_map.py --scan | --render | --check | --selftest`**, and it
**never rewrites the JSON**. `--scan` re-parses the five sections and scans every tracked
`tests/**/test_*.py`, then reports five kinds of difference: a section heading, item line or
item text that has moved under the map; a JSON claim the tree no longer carries; a claim line
that moved; **a claim site in the tree the JSON does not record**; and a number outside any
document's range. `--check` runs `pytest --collect-only -q` on the claimed files and asserts
every `function` claim is a collected node id — 316 node ids across the eight claimed files.

**3. The page names each deposit document by file name in prose and links to none of them**,
for the reason in the Source line above.

**The scan reads the INDEX and reports the worktree separately.** `git ls-files` is the
authority for what a clone receives, so a claim site in an untracked file cannot be a
disagreement — a gate that read the worktree would be green or red depending on whose machine
ran it, which is the failure `tests/unit/test_encoding_is_declared.py` records for a ceiling
measured off the disk. Untracked test files are scanned anyway and printed under their own
heading, because a parallel agent's new test is untracked for exactly as long as it matters.
**It becomes a disagreement the moment the file is staged**, which is the right time.

## The counts, and what a percentage here does not say

| Document | Tests | Claimed | Covered via | Declined | Unclaimed | % claimed |
|---|---:|---:|---:|---:|---:|---:|
| `SETTLEMENT_FLOW_LEDGER_PREREG.md` §12 (705, items 707–777) | 71 | 19 | 0 | 5 | 47 | **26.8%** |
| `INDEX_REWEIGHT_FLOW_PREREG.md` §13 (347, items 349–376) | 28 | 2 | 0 | 0 | 26 | **7.1%** |
| `OPENING_AGENT_STATE_PREREG.md` §15 (334, items 336–360) | 25 | 5 | 4 | 0 | 16 | **20.0%** |
| `SHOCK_CLASSIFIER_PREREG.md` §9 (293, items 295–307) | 13 | 2 | 0 | 0 | 11 | **15.4%** |
| `LETF_CLOSE_FLOW_PREREG.md` §8 (242, items 244–252) | 9 | **0** | 0 | 0 | 9 | **0.0%** |
| **all five** | **146** | **28** | **4** | **5** | **109** | **19.2%** |

`ARCHITECTURE_OVERVIEW.md` has no numbered list — its §9 is a power-class table — and is not
on the map. The six rounds of infrastructure work claim, between them: D586 ledger 13 and
index 12; D587 ledger 10, 11 and shock 9, 10; D588 ledger 51, 52, 53, 59, 62, 63; D592 ledger
66–69; D593 ledger 70, 71, opening 2, 19, 25 and index 9; D594 ledger 34, 60, 64, 65 and
opening 18, 20. **D590 and D591 claim no numbered test**, which is a true statement about two
substantial modules and is on the record here because nothing else says it.

**A percentage above is a COUNT and not a verdict.** "claimed" means one repository test names
that number. It does not say the test is right, that the claimed items are the important ones,
or that the unclaimed ones are not. **LETF is at zero and the shock classifier's two claims
are both incidental** — they fell out of D587's fill model, which was built for the ledger.

## Consequences

### 1. Three spellings, and a grep for one finds six of twenty-eight

The 28 existing claims are made three ways, none of them wrong and none of them searchable
from the others:

| convention | count | example |
|---|---:|---|
| **(i) the function name** | 10 | `def test_ledger_51_design_effect_m10_rho01_gives_n_over_1p9`, `def test_ut34_...` |
| **(ii) a section banner** | 3 | `# ===== ledger test 66`, above a block of functions that name no number |
| **(iii) a docstring or assertion message** | 15 | `Ledger unit test 11 and shock unit test 9, long side.`; `"INDEX_REWEIGHT_FLOW_PREREG.md unit test 9"` |

`grep 'def test_ledger'` returns **six of twenty-eight**. `grep -i 'ledger.*test'` misses the
three that spell the document as a file name, and the regex in the brief that seeded this work
misses `tests/golden/test_episodes_ledger.py:4` entirely, because the number is on the line
*after* the document name. Reading the tree by eye is how the claims were found; it is not how
they should be found again.

**THE CONVENTION THIS RECORD FIXES GOING FORWARD: a test that discharges a numbered deposit
item names the number in its FUNCTION NAME** — `test_<doc>_<number>_<what_it_checks>` — because
that is the one spelling `pytest -k`, a traceback, a test id and a plain grep all see. The
other two remain valid for the tests that already use them and `--scan` reads all three; the
rule is about what the next one does.

### 2. The scan is a tripwire, not a proof, and one claim is not machine-decidable

It cannot see a test that discharges an item without naming it, it cannot see whether a test
naming a number actually checks that number's claim, and **where a docstring names two
documents and one number it cannot decide which document owns it**.
`tests/golden/test_episodes_ledger.py:4` is exactly that: the nearest document name before
"its unit test 69" is `OPENING_AGENT_STATE_PREREG.md`, and the number is the **ledger's**. The
scan therefore emits every candidate document a site could mean and treats the site as
recorded if the JSON claims **any** of them. The JSON is the judgement; the scan is the alarm
that the judgement has gone stale. Stated plainly because D593 had to state the same limits
about its AST forward-index scan, and an unstated limit reads as a guarantee.

### 3. The class tallies the brief carried sum to 153 against 146 items

The seeded tallies were arithmetic 51, statistical 34, leak 32, data_guard 21, execution 12,
rendering 3 — **153**, seven more than there are items. Assigned here from each item's own text
under written definitions (in `crosswalk.py`'s `CLASSES` docstring) the tally is:

| | arithmetic | leak | statistical | data_guard | execution | rendering |
|---|---:|---:|---:|---:|---:|---:|
| **this record** | 40 | 31 | 31 | 25 | 16 | 3 |
| *seeded* | *51* | *32* | *34* | *21* | *12* | *3* |

Only `rendering` agrees, and it agrees exactly — ledger 25 (query lists hashed into
`trials.csv`), 31 (the recorder's no-overwrite file rule) and 63 (`TRACK_MAP.md` validation),
the three items whose subject is a produced artefact. The difference elsewhere is a real
boundary question rather than a miscount: a DST test is `execution` here because it decides
which bars a trade may touch, and a point-in-time rule is `leak` even when its assertion is
arithmetic. **The definitions are written down so the next disagreement is about the
definition and not about the tally.**

### 4. What is not claimed, and the two items that look claimed and are not

* **`declined`, 5 items, on the record:** ledger 54–58 —
  [D588](D588-power-analysis-module.md):152–154 declines the §9A.2 rule-4 marginal-contribution
  regression and the whole §9B toolkit, because both need a regression and a simulator rather
  than planning arithmetic and belong with whichever study runs them.
* **`covered_via`, 4 items:** opening 21–24 are the opening document's restatements of ledger
  66, 67, 68 and 69 (24 also restates ledger 70). **No test names the opening numbers**, so a
  grep for them returns nothing and the work is done; the map says so rather than leaving four
  items looking unwritten.
* **Two items with a note and no test.** **Ledger 61** (the forward consistency test): the only
  trace is the phrase "consistency check" in a docstring at
  `src/backtest_framework/validation/power.py:464`, which is prose about the Track 3 route and
  asserts nothing about a forward estimate against a Track 1 interval. **Index 11**
  (Construction B's per-leg exits): [D586](D586-FIXTURE-cme-settlement-windows-with-effective-dates.md):58
  supplies the data the test needs — the three COMEX metals settle up to three hours before ES
  — and names the test by number, and asserts nothing about legs or entry ordering. Both are
  `missing`, both carry the note, and the note is the point: **a record that mentions a test is
  not a test**, which is [R6](../RULES.md) in miniature.

### 5. The gates, and the one that fires on the next agent

`tests/unit/test_deposit_test_map_is_current.py` asserts the scan reports **zero**
disagreements against the tracked tree. So a parallel agent that writes a test discharging a
numbered item — in any of the three spellings — turns the suite red until the map records it.
That is the intended direction: the cost of the map going stale is paid by whoever makes it
stale, on the same commit, rather than by whoever reads it six months later. The reverse
direction is covered too: a claim whose file, symbol or line has moved is reported by name.

`--selftest` proves 17 validator raises and 5 scan raises, each break aimed at the list the
assertion reads — a symbol that was never written, a file that is gone, a line that moved, a
claim site the JSON stopped recording, a section heading that moved — and then proves the scan
is **silent on the real map**, without which the five breaks prove nothing.

### 6. What a future agent does

Pick an unclaimed row off the page. Its paraphrase is the handle and its verbatim text is the
specification, **and neither needs the deposit document**: the JSON carries the text precisely
so the page renders and the gates run in a clone that has none of the five files. Write the
test with the number in the function name, add the claim to the JSON, re-render, and run
`--scan` and `--check`.

## What this does not do

* **It does not run, read or score anything.** No strategy return is computed; no fixture is
  read; no bar from 2024-01-01 is touched.
* **It does not write any of the 118.** It makes them a list with a class and a paraphrase,
  which is the cheapest thing that stops two agents writing the same one.
* **It does not judge the 28.** `--check` proves a claimed test is *collected*, not that it
  checks what its number says.
* **It does not amend the deposit documents.** They are read-only sources, and the section
  line numbers in the JSON are a snapshot the scan re-checks whenever they are on disk.

## Disagreements between the seeded map and the scan

Recorded rather than silently corrected, because the seeded map is what the next agent will be
handed if this record does not say otherwise.

1. **The class tallies sum to 153 against 146** (consequence 3 above).
2. **Index 12's claim site.** The seed gives `tests/unit/test_settlement_windows.py` lines 93,
   99 and 209. Those are the assertion functions and **none of them names the number**; the
   only line that does is the module docstring at **line 3**. The JSON claims line 3 and the
   note names 93/99/209, because a claim must be something the scan can read.
3. **Ledger 10's claim.** The seed reads `tests/golden/test_futures_fills_ledger.py:200` as the
   fill model's entry test; the function there is
   `test_entry_must_complete_three_minutes_before_the_window`, which is the ledger item's
   three-minute entry constraint. The claim stands; the description did not.
4. **Ledger 54–58's declining lines.** The seed says
   `D588-power-analysis-module.md:152–157`; the bullet runs **152–156** and the numbers are on
   153 (test 54) and 154 (tests 55–58). The JSON cites 152 and 154.
5. **`covered_via` for opening 24** points at ledger 69 alone, because the field takes one
   target; that it also restates **ledger 70** is in the note.
6. **Four pre-existing unresolved links, not mine and not fixed here.**
   `scripts/check_doc_links.py` reports
   `docs/decisions/D592-...md:7` and `:9` and `docs/results/PROGRAMME_REGISTRY.md:5` (twice)
   linking to the untracked deposit documents — *"on disk but NOT in git; a reader gets
   nothing"*. D592 made the same call this record makes about naming those files and then
   linked them anyway. **Flagged for the integrator; editing D592's record or page is outside
   this record's file list.**

## The parallel round's in-flight claims — fourteen more items, NOT in this map

The final `--scan` of this session, over the **untracked** worktree, finds 62 claim sites in
the test files this round's other agents (D608–D606) are writing right now. Between them they
claim **fourteen numbered items the map does not hold**, and the number was eleven forty
minutes earlier — **it will have moved again by the time this is read**:

| document | numbers | files |
|---|---|---|
| ledger | **31, 32, 33** | `tests/unit/test_recorder.py`, `tests/golden/test_recorder_ledger.py`, `tests/property/test_recorder_property.py` |
| ledger | **35, 36** | `tests/golden/test_track3_ledger.py` |
| ledger | **7, 45, 46** | `tests/unit/test_futures_impact.py` |
| ledger | **48, 49** | `tests/golden/test_error_budget_ledger.py`, `tests/unit/test_error_budget.py` |
| index | **19, 20** | `tests/unit/test_error_budget.py`, `tests/golden/test_error_budget_ledger.py` |
| index | **28** | `tests/golden/test_track3_ledger.py`, `tests/unit/test_track3.py` |
| opening | **13** | `tests/golden/test_error_budget_ledger.py` |

**They are deliberately not in `data/deposit_test_map.json`.** Those files are still being
written — three of them appeared during this session — so every line number in them is
provisional, and a map recorded against a moving file is worse than a map that says nothing:
it would go red for the wrong reason and be "fixed" by re-pointing rather than by reading. The
scan lists them under *CLAIM SITES IN UNTRACKED TEST FILES*, so the integrator does not have
to discover them.

**Staging those files turns `tests/unit/test_deposit_test_map_is_current.py` red**, with every
new claim named in the failure text. The fix is to add each one's claim to the JSON and
re-render, and the right moment for it is the integration commit. On the fourteen above the map
would read **42 of 146 claimed (28.8%)** — ledger 29 of 71, index 5 of 28, opening 6 of 25,
shock 2 of 13, LETF still **0 of 9**. **Re-run `--scan` before believing that number**; it is
a snapshot of a worktree in motion, which is exactly the reason the gate reads the index.

**And they vindicate the convention.** Every one of those tests spells its number in the
**function name** — `test_ledger_48_zero_contribution_term_changes_oos_mse_by_exactly_zero`,
`test_index_20_stage_reordering_requires_a_matching_decision_log_entry`,
`test_opening_13_parameter_budget_refuses_twelve_features`. Four agents converged on
convention (i) without being told to, which is the argument for writing it down.

One reading the scan cannot make on its own, left for whoever records them.
`tests/golden/test_error_budget_ledger.py:11` reads *"`OPENING_AGENT_STATE_PREREG.md` §7.3
with unit test 13"*, in a sentence that has already named the settlement ledger two lines
above. The scan therefore offers `opening/index/ledger 13` as candidates and accepts the site
because **ledger** 13 is claimed — and the number means **opening** 13. It happens to be
harmless, because opening 13 is claimed at line 230 of the same file, but it is the second
instance of consequence 2's ambiguity and the reason the JSON is curated rather than derived.

## AMENDMENT, 2026-09-21 — round 3 was staged and its fifteen claims are recorded: 28 → 43

*Appended rather than merged into the text above, because the original's numbers are what the
gate and the page were written against and a reader needs the before as well as the after.
**Everything above — including this record's TITLE, "28 claimed … 118 unclaimed" — stands as
written at the time it was written.** The drafts at the foot are the exception: they are
copy-out text for other documents and carry the amended figures.*

**The section immediately preceding this one predicted fourteen items and one more arrived.**
D608–D606's tests entered the index; the untracked bucket became `CLAIM SITES THE JSON DOES
NOT RECORD` — 70 sites, 15 items — and `tests/unit/test_deposit_test_map_is_current.py` went
red exactly as designed. All fifteen are now recorded, the page is re-rendered, and `--scan`
is back to **zero disagreements** over 204 tracked test files and 140 claim sites.

| record | items claimed | claim site recorded |
|---|---|---|
| **D608** the forward data recorder | ledger **31, 32, 33** | `tests/unit/test_recorder.py:141 / :328 / :476` |
| **D604** futures impact and the depth fixture | ledger **7, 45, 46**, index **18** | `tests/unit/test_futures_impact.py:123 / :219 / :161`; `tests/golden/test_futures_impact_ledger.py:205` |
| **D605** Track 3 logging | ledger **35, 36**, index **28** | `tests/golden/test_track3_ledger.py:102 / :248 / :319` |
| **D606** the error budget and the parameter budget | ledger **48, 49**, index **19, 20**, opening **13** | `tests/golden/test_error_budget_ledger.py:168 / :327 / :230`; `tests/unit/test_error_budget.py:91 / :444` |

**The amended coverage:**

| Document | Tests | Claimed | was | Covered via | Declined | Unclaimed | % claimed |
|---|---:|---:|---:|---:|---:|---:|---:|
| `SETTLEMENT_FLOW_LEDGER_PREREG.md` | 71 | **29** | *19* | 0 | 5 | 37 | **40.8%** |
| `INDEX_REWEIGHT_FLOW_PREREG.md` | 28 | **6** | *2* | 0 | 0 | 22 | **21.4%** |
| `OPENING_AGENT_STATE_PREREG.md` | 25 | **6** | *5* | 4 | 0 | 15 | **24.0%** |
| `SHOCK_CLASSIFIER_PREREG.md` | 13 | 2 | *2* | 0 | 0 | 11 | **15.4%** |
| `LETF_CLOSE_FLOW_PREREG.md` | 9 | **0** | *0* | 0 | 0 | 9 | **0.0%** |
| **all five** | **146** | **43** | *28* | **4** | **5** | **94** | **29.5%** |

**Three things this round settles, and they are not bookkeeping.**

1. **The convention held on its first test.** Thirteen of the fifteen are claimed by a
   **function name** — `test_ledger_48_zero_contribution_term_changes_oos_mse_by_exactly_zero`,
   `test_index_20_stage_reordering_requires_a_matching_decision_log_entry`,
   `test_opening_13_parameter_budget_refuses_twelve_features`. Four agents reached for
   convention (i) with no instruction to. The claimed share went from 10-of-28 spelled that way
   to 23-of-43.
2. **The convention has one seam, and it showed up immediately.**
   `test_ledger_46_and_index_18_i_d_equals_i_when_depth_equals_depth_bar` discharges **two**
   documents' items in one function, and the scan's function-name rule reads only the leading
   number. So index 18 is claimed by the golden's **docstring** at
   `tests/golden/test_futures_impact_ledger.py:205` instead. Index 28 is the same shape from the
   other direction — `tests/golden/test_track3_ledger.py:319` names it in a docstring and no
   function name carries it. **A function name holds one number; an item discharged by a test
   named for a different document still needs the docstring spelling.** That is a limit of the
   convention, not a violation of it, and it is why `--scan` reads all three.
3. **LETF is still at zero, and it is now the only document with nothing.** Four rounds of
   infrastructure have touched the ledger, the index doc, the opening doc and the shock
   classifier. `LETF_CLOSE_FLOW_PREREG.md`'s nine items — four of them one-line arithmetic on
   `rebalance_flow` — are the cheapest unclaimed block on the page and nobody has taken them.

**A fourth thing, and it is a gate checking this record's work for free.**
`tests/unit/test_citation_anchors_resolve.py` reads any `path.py:line` in prose beside a
symbol name and asserts the symbol is defined at that line. The page's **Claim** column is
exactly that shape — `` `tests/unit/test_recorder.py:141` `test_ledger_31_a_second_record_never_overwrites` ``
— so **every one of the 23 function claims is independently re-verified by a gate this record
did not write**, on top of `--scan` and `--check`. It also caught seven notes in which a
secondary site was written as `file:line` beside a *different* symbol; those notes now name
the file without a line, because a line number in prose is an anchor whether or not it was
meant as one. Three anchors of the same kind remain in round 3's own files and are left for
their authors: `src/backtest_framework/data/recorder.py:30` and `:967` cite
`scripts/fetch_release_calendar.py:131` for `RateLimiter` / `attempts`, and
`tests/unit/test_error_budget.py:334` cites `src/backtest_framework/validation/power.py:578`
for `_ERROR_BUDGET_REQUIRED`, which is at module level there.

`tests/unit/test_deposit_test_map_is_current.py` now pins `CLAIMED_PER_DOC` and
`CLAIMED_TOTAL = 43`. **Those constants are meant to be edited**, together with this record,
whenever a claim is added; loosening them to `>=` would delete the gate.

*Verified at the amendment: `--scan` 204 tracked test files, 140 claim sites, zero
disagreements; `--check` 622 collected node ids; `--selftest` 23 checks, 0 failures; 61 tests;
`ruff` and `mypy` clean; `docs/results/DEPOSIT_TEST_MAP.md` re-rendered and byte-equal to the
renderer's output.*

## Integration the integrator must do

1. **Add the index row** for `DEPOSIT_TEST_MAP.md` to `docs/results/README.md`.
   `tests/unit/test_results_index_is_complete.py::test_every_study_document_is_in_the_index`
   is **RED until then** and red for that reason alone.
2. **Stage `data/deposit_test_map.json`.** Until it is tracked, the page's one relative link
   (`../../data/deposit_test_map.json`) is a fifth unresolved link in
   `scripts/check_doc_links.py`.
3. **Add the `docs/decisions/README.md` row** and regenerate the register
   (`scripts/build_decision_register.py`);
   `tests/unit/test_decision_index_is_complete.py` reads `git ls-files`, so it stays green
   while this record is untracked and goes red the moment it is staged without the row.
4. **README / living-document counts** move by four modules-and-tests worth: one new
   `src/` module, one new runner, two new test files.

---

## Draft — `docs/data-available.md` paragraph

> **`data/deposit_test_map.json` — the deposit pre-registrations' 146 numbered unit tests,
> crosswalked to the repository tests that claim them (D607).** One row per numbered item in
> the five `docs/internal/User-Doc-Deposit/*_PREREG.md` **Required unit tests** sections
> (settlement ledger 71, index reweight 28, opening agent state 25, shock classifier 13, LETF
> close flow 9), each with the item's **verbatim text**, a ≤ 15-word paraphrase, a class
> (arithmetic 40, leak 31, statistical 31, data_guard 25, execution 16, rendering 3) and a
> status: **43 claimed, 4 covered via another document's claimed test, 5 declined on the record
> in D588, 94 with nothing.** The thing that bites: **the five deposit documents are
> untracked**, so a clone has none of them — the verbatim text lives in this file for exactly
> that reason, and nothing should link to them by relative path.
> `docs/results/DEPOSIT_TEST_MAP.md` is rendered from this file and is never the source of
> truth; `scripts/deposit_test_map.py --scan` verifies it against the tree and never rewrites
> it.

## Draft — `CHANGELOG.md` bullet

> **D607 — the deposit test crosswalk.** `validation/crosswalk.py`,
> `data/deposit_test_map.json` (146 rows) and the rendered page
> `docs/results/DEPOSIT_TEST_MAP.md` index every numbered unit test in the five deposit
> pre-registrations against the repository test that claims it: **43 claimed (ledger 29/71,
> opening 6/25, index 6/28, shock 2/13, LETF 0/9), 4 covered via another document, 5 declined
> in D588, 94 unwritten and now listed with a class and a paraphrase.** They use **three
> spellings** — function name (23), docstring or assertion message (15), section banner (5) —
> and at the 28 this record opened with, a grep for the first found six of them; going forward
> a test that discharges a numbered item names the number in its **function name**, and round
> 3's fifteen new claims (D608–D606) already do, thirteen of fifteen.
> `scripts/deposit_test_map.py --scan` re-parses the five
> sections and scans every tracked test for all three conventions and reports every
> disagreement, never rewriting the JSON; `--check` collects the claimed files under pytest;
> `--selftest` proves 22 raises. `tests/unit/test_deposit_test_map_is_current.py` holds the
> scan at zero disagreements, so a new claim that is not recorded turns the suite red on the
> commit that makes it. The seeded class tallies summed to 153 against 146 items and are
> re-derived here. No strategy return computed; no fixture read.
