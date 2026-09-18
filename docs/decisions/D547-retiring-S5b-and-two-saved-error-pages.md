# D547 — Retiring S5b, 987 lines of apparatus for a question nobody ever asked, and two saved HTTP 429 bodies

*Filename shortened on creation ([D540](D540-local-config-a-clone-never-receives.md)). The H1 above
is the full title.*

**Status:** Pre-registered
**Date:** 2026-09-18
**Category:** Infrastructure
**Source:** The principal's decision on the two items
[D542's RESULT](D542-RESULT-two-predictions-falsified-and-a-verdict-that-flipped.md) handed over
and [D546](D546-a-collectable-script-and-a-json-that-never-parsed.md) carried forward. Committed
before anything is deleted (R8). Nothing admitted to either book; no holdout read.

**`data/` is evidence and `src/` is library, so retirement here is written, not quiet. This record
is the writing.** It is committed before the deletion so that what is being removed, and what was
checked before removing it, exists independently of the commit that removes it.

---

## 1. S5b — `src/backtest_framework/research/terrain_swing_decay.py`

**414 lines of module, 573 lines of test, 48 collected tests.** Imported by nothing except its own
test file; zero references in `scripts/`, and in `docs/` only the four records that flagged it.

### What it is, so that retiring it is a decision and not a tidy-up

S5b is `terrain_swing.SwingSupplyDemandSensor` (S5) **with exactly one rule changed**, deliberately
built as a separate module so S5 stays byte-for-byte what it was, and importing every shared part
(`_is_swing_bars`, `confirmed_pivots`, `_impulse`, `_cluster`, `_rank_scores`, `SwingLevel`,
`SWING_K`, `CLUSTER_ATR`, `MIN_SWINGS`, `SHARPNESS_BARS`, `MIN_LEVELS`) rather than copying it.
Its own docstring gives the reason, and it is the right one: *"A variant that re-implemented the
shared parts would be a second sensor pretending to be a comparison."*

The hypothesis, in its own words:

> *a level that has been probed and rejected is not the same object as a level that has never been
> touched from the wrong side, even though S5 scores them identically.*

The mechanism: a band pierced by a wick that closes back survives at
`strength_multiplier = (1 - decay) ** pierces`, with `DECAY_PER_PIERCE = (0.1, 0.25)`.

### Why retiring it costs less than the line count suggests

**The module already proved the sharpest thing it had to say, and it is a negative.** Its docstring
states — and `test_the_level_set_is_always_identical_to_s5_pierces_or_not` pins — that S5b emits
**the same level set as S5 at every index, always**. S5's kill test reads `close` alone, so a wick
that closes back was already survivable under S5. The entire difference between the two sensors is
the *score* attached to identical levels.

So S5b is a re-weighting test, not a survival test — and **the re-weighting was never measured**.
No runner ever scored S5b against S5 on anything. The apparatus was built, gated by 48 tests, and
the comparison it exists to make was never run. That is what is being retired: not a result, and
not a failed result, but an unasked question with a very well-built instrument beside it.

The surrounding line was closed anyway. The daily channel family (D399–D483) was closed by the
principal on 2026-09-12 without a holdout read, and nothing since has wanted a supply/demand
re-weighting.

### What must survive

**`terrain_swing.py` (S5) is untouched.** It is imported by `research/structure.py`,
`research/terrain_field.py`, `research/terrain_strategies.py`, `scripts/ragged_structure_scores.py`
and `scripts/run_d403_wick_potential.py`. Only the variant goes.

---

## 2. The two saved error pages — and `wb` does not mean what the earlier records assumed

`data/D3_wb_2018.json` and `data/D3_wb_2019.json` are 117 bytes each of
`<html><body><h1>429 Too Many Requests</h1>`. Both earlier records describe them correctly as
saved error bodies. **What none of them establishes is what the request was for, and the answer
changes how much is lost by deleting them.**

`wb` is the **Wayback Machine**, not the World Bank. The 43 other tracked `data/D3_*` files make it
unambiguous: `D3_wb_french_2018.txt`, `D3_wb_french_2019.txt`, `D3_wb_french_20190301.txt` and five
more are **successfully captured archive snapshots of Ken French's data-library pages** at fixed
dates, opening with *"Kenneth R. French - Variable Definitions / 178 captures / 17 Apr 2002 - 17
May 2026 … COLLECTED BY Organization: Alexa Crawls"*.

**So the two 429s are failed index queries whose purpose was served anyway.** They were asking the
archive *which snapshots exist* for 2018 and 2019; the snapshots themselves are on disk, captured,
in the sibling `.txt` files. Nothing downstream of the failed query is missing.

### The mechanism, which is a latent defect and is not being fixed here

`data/D3_fetch.py:22-23` catches `HTTPError` and takes `e.read()` as the body; `:31` then
**writes it to the requested filename unconditionally**, and the status code is reported
afterwards rather than checked. A 429 therefore lands on disk under the name the caller asked
for, looking like the artifact it was meant to be.

That is how these two were created, and it would do it again. **It is not fixed in this record** —
`data/` is evidence, the fetcher is part of the D3 lane's record of how that lane fetched, and
`tests/unit/test_tracked_json_parses.py` now catches the *result* on arrival. Noted for the
principal rather than patched.

---

## Decision

1. **Delete** `src/backtest_framework/research/terrain_swing_decay.py` and
   `tests/unit/test_terrain_swing_decay.py`.
2. **Delete** `data/D3_wb_2018.json` and `data/D3_wb_2019.json`.
3. **Empty `ALLOWED` in `tests/unit/test_tracked_json_parses.py`.** The allow-list is re-derived
   against the files, so leaving the entries in place would redden
   `test_the_allow_list_is_still_earned` with *"no longer present"* — which is the gate working.
   The file's docstring is rewritten to describe a repository where every tracked JSON parses, and
   keeps the two 429 pages as the recorded reason the gate exists.
4. **Amend, do not rewrite, the records that describe these as open.** D542's RESULT, D546 and its
   RESULT all say these are the principal's to decide. They were, and this is the decision; the
   earlier text stays and this record is linked from the plan.

## Predictions

Behaviour, and one piece of arithmetic on an artifact that already exists — which is the only kind
of count this programme has got right.

| # | Prediction | Confidence |
|---|---|---|
| **P1** | Deleting the two JSON files **without** emptying `ALLOWED` reddens exactly one test, `test_the_allow_list_is_still_earned`, naming both paths as *"no longer present"*. Emptying it then turns the file green. Both halves demonstrated, not assumed. | High |
| **P2** | The suite's collected total falls by **exactly 48**, 2,221 → **2,173**, and no test outside `test_terrain_swing_decay.py` fails. 48 is measured today by `--collect-only` on that file, not guessed. | High |
| **P3** | No documentation gate reddens: `check_doc_links.py` stays at 0 unresolved and the D544 citation gate stays green, because every surviving mention of both names is prose in backticks, not a relative link and not a `path:line`. | High |
| **P4** | `terrain_swing.py` and its five dependents are untouched and import cleanly; `ruff` and `mypy` stay green with one fewer `research/` module. | High |

**P2 is the one worth being wrong about.** If the total falls by more than 48, something outside
S5b's test file depended on S5b and the dependency was invisible to a name search — which is
exactly the failure a deletion should be afraid of.

## What this record does not settle

**Whether S5b's question was worth answering.** Retiring the instrument is not a verdict on the
hypothesis; the hypothesis is recorded above precisely so that it survives its apparatus. If a
supply/demand re-weighting is ever wanted again, this record and `terrain_swing.py` are enough to
rebuild it, and git holds the original.

**Whether `D3_fetch.py` should check the status before writing.** It would have prevented both
files. It is evidence in `data/`, the JSON gate now catches the outcome, and the change is the
principal's.

**Whether any other tracked artifact is a saved error body that happens to parse.** This record
removes the two that do not parse. A 200-byte JSON error *object* from an API would parse cleanly
and pass the gate, and nothing here looks for that.
