# D97 — Phase G writeup: methodology-first structure, skeleton-with-real-numbers, anchor-tested consistency

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Phase G writeup skeleton)

## Decision

`docs/writeup.md` is the portfolio document the timetable pre-specified
("methodology, results (including negative ones), the capacity analysis,
scoping docs as appendices"), structured by five choices:

1. **Methodology before results.** For an audience of senior quant reviewers
   evaluating a well-known strategy, the trustworthiness of the measurement is
   the product — the trust story (golden masters, penny-exact cross-engine
   reconciliation, structural look-ahead prevention, content-addressed
   snapshots, registry-fed DSR, one-variable-per-study) leads, and every
   result section then spends its space on findings rather than defenses.
2. **Skeleton means final numbers, draft prose.** All five studies are
   complete, so every section carries its thesis and its real exhibit;
   `[TODO prose]` markers flag narrative work only. A tested rule enforces the
   boundary: TODO markers that are not prose markers fail the suite — numbers
   are never TODO in this document.
3. **The pre-registration and its correction are in the document.** The
   planning docs predicted "doesn't clear costs at retail scale, clears at £X
   AUM"; the measurement said no size clears at full gross, and low gross
   clears implementation but not the capital hurdle. Stating the corrected
   prediction is the methodology story working in public, not a blemish.
4. **The Kalman cut is recorded as evidence-based.** The original Phase G plan
   listed Gatev → cointegration → Kalman. Study v3 showed a train-window
   static β already imports more estimation error than hedge benefit; a
   dynamic hedge re-estimates exactly that parameter continuously. The writeup
   says the third stage wasn't run because of v3's result, not because time
   ran out.
5. **Anchor-tested number consistency** (`tests/unit/test_writeup.py`): a
   curated list of (headline number, source artifact) pairs asserts each
   number appears in BOTH the writeup and its source, with unicode-minus
   normalization. If a study re-run moves a headline, the writeup fails CI
   instead of silently lying — the D84/D91 doc-rot discipline applied to the
   program's most outward-facing document. The README now leads with the
   writeup link (and its stale "pre-implementation" status was corrected in
   the same pass).

## Rationale

The timetable's kill criterion ("entering week 20 without a started writeup →
freeze all code permanently") makes the skeleton the schedule-critical
deliverable, and the reviewer-outreach plan ("cold emails with the writeup
attached") makes it the document strangers judge the whole project by. A
skeleton whose numbers are final and machine-checked can be sent early and
polished in place; a skeleton of empty headers could not. The structure choices
all serve the same reader: someone who has seen a hundred pairs-trading
backtests and needs a reason to believe this one's negative result within the
first two sections.
